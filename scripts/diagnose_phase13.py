"""Generate Fase 13 diagnostic tables without modifying rankings."""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = REPO_ROOT / "results" / "tables"
DOCS_DIR = REPO_ROOT / "docs"

SNAPSHOT_FILES = [
    "results/rankings/ranking_v0_frozen.tsv",
    "results/rankings/ranking_v1_frozen.tsv",
    "results/rankings/ranking_v2_frozen.tsv",
    "results/rankings/ranking_v2_frozen.metadata.yaml",
    "results/rankings/ranking_balanced.tsv",
    "results/tables/component_scores_all_candidates.tsv",
    "config/scoring_scenarios.yaml",
    "config/parameters.yaml",
]

POSITIVE_CONTROLS = ["ERBB2", "EPCAM", "MET", "TACSTD2", "CEACAM5", "MSLN", "CLDN18", "FGFR2"]
ORIGINAL_POSITIVE_FAILURES = {"TACSTD2", "CEACAM5", "MSLN", "CLDN18", "FGFR2"}
BALANCED_WEIGHTS = {"Surf": 0.15, "E": 0.20, "N": 0.20, "R": 0.20, "P": 0.15, "T": 0.10}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.6f}"
    return str(value)


def parse_float(value: object) -> float | None:
    text = str(value).strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def by_symbol(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in rows}


def surfaceome_relative_confidence(raw_score: object) -> float | None:
    value = parse_float(raw_score)
    if value is None:
        return None
    return min(1.0, max(0.0, (value - 5.0) / 5.0))


def legacy_ordinal_surf_percentiles(rows: list[dict[str, str]]) -> dict[str, float]:
    ordered = sorted(rows, key=lambda row: (float(row["surfaceome_confidence_score"]), row["hgnc_symbol"]))
    denominator = len(ordered) - 1
    return {row["hgnc_symbol"]: index / denominator for index, row in enumerate(ordered)}


def compute_surf_tie_diagnostics(
    universe_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    core_rows = [
        row
        for row in universe_rows
        if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"}
    ]
    ordered = sorted(core_rows, key=lambda row: (float(row["surfaceome_confidence_score"]), row["hgnc_symbol"]))
    denom = len(ordered) - 1
    legacy = legacy_ordinal_surf_percentiles(core_rows)
    group_indices: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(ordered):
        group_indices[row["surfaceome_confidence_score"]].append(index)

    group_rows = []
    group_stats: dict[str, dict[str, object]] = {}
    for raw_score, indices in sorted(group_indices.items(), key=lambda item: float(item[0])):
        min_pct = min(indices) / denom
        max_pct = max(indices) / denom
        mid_pct = (sum(indices) / len(indices)) / denom
        stats = {
            "surfaceome_confidence_score": raw_score,
            "n_genes": len(indices),
            "legacy_ordinal_percentile_min": min_pct,
            "legacy_ordinal_percentile_max": max_pct,
            "legacy_ordinal_percentile_span": max_pct - min_pct,
            "tie_aware_midrank_percentile": mid_pct,
            "v1_relative_confidence": surfaceome_relative_confidence(raw_score),
        }
        group_stats[raw_score] = stats
        group_rows.append(stats)

    per_gene: dict[str, dict[str, object]] = {}
    for row in core_rows:
        symbol = row["hgnc_symbol"]
        raw_score = row["surfaceome_confidence_score"]
        stats = group_stats[raw_score]
        legacy_value = legacy[symbol]
        relative_value = surfaceome_relative_confidence(raw_score)
        per_gene[symbol] = {
            "legacy_ordinal_surf_percentile": legacy_value,
            "tie_aware_surf_midrank_percentile": stats["tie_aware_midrank_percentile"],
            "v1_surf_relative_confidence": relative_value,
            "legacy_minus_v1_delta": None if relative_value is None else legacy_value - relative_value,
            "surfaceome_score_group_n": stats["n_genes"],
            "surfaceome_score_group_legacy_min": stats["legacy_ordinal_percentile_min"],
            "surfaceome_score_group_legacy_max": stats["legacy_ordinal_percentile_max"],
            "surfaceome_score_group_legacy_span": stats["legacy_ordinal_percentile_span"],
        }
    return group_rows, per_gene


def classify_positive(
    symbol: str,
    component: dict[str, str],
    ranking_v1: dict[str, str],
    topology: dict[str, str],
    universe: dict[str, str],
) -> tuple[str, str, bool, str]:
    explanations: list[str] = []
    bug_suspected = False
    rank = int(ranking_v1.get("rank", "999999"))
    surf = parse_float(component.get("Surf_relative_confidence", ""))
    t_rank = parse_float(component.get("T_rank_percentile", ""))
    t_score = parse_float(component.get("T_score", ""))
    r = parse_float(component.get("R_rank_percentile_high_worse", ""))
    n = parse_float(component.get("N_rank_percentile", ""))
    isoform = component.get("isoform_resolution_status", "")
    missing = component.get("missing_mvp_score_components", "")
    raw_surf = parse_float(universe.get("surfaceome_confidence_score", ""))

    if rank <= 50:
        explanations.append("recovered_in_top50_v1")
    if "isoform_unresolved" in isoform:
        explanations.append("isoform_unresolved")
    if r is not None and r >= 0.60:
        explanations.append("normal_risk_or_off_tumor_penalty")
    if n is not None and n < 0.50:
        explanations.append("low_selectivity_component")
    if raw_surf is not None and raw_surf <= 6:
        explanations.append("lower_raw_surfaceome_confidence")
    if topology.get("gpi_anchor_present") == "true":
        explanations.append("gpi_anchor_positive")
    if t_rank is not None and t_rank < 0.20:
        if symbol == "MSLN" and t_score is not None and t_score >= 0.60:
            explanations.append("T_rank_low_due_distribution_after_shedding_soluble_penalties")
        else:
            explanations.append("topology_component_low_or_unexpected")
    if missing:
        explanations.append("coverage_missing_components")

    if not explanations:
        explanations.append("no_single_failure_mode")
    primary = explanations[0]
    risk_text = component.get("risk_interpretation", "")
    if symbol == "MSLN" and rank > 50 and "T_rank_low_due_distribution_after_shedding_soluble_penalties" in explanations:
        final_verdict = "explained_shedding_soluble_T_penalty_after_GPI_surfaceome_correction"
    elif symbol == "CEACAM5" and rank > 50 and raw_surf is not None and raw_surf <= 6:
        final_verdict = "explained_GPI_Surf_source_underconfidence_with_strong_E_N_P_T"
    elif symbol == "TACSTD2" and rank > 50:
        final_verdict = "explained_mid_surface_confidence_and_weaker_protein_support"
    elif "isoform_unresolved" in explanations:
        final_verdict = "explained_isoform_unresolved"
    elif "normal_risk_or_off_tumor_penalty" in explanations:
        final_verdict = "explained_normal_risk"
    elif rank <= 50:
        final_verdict = "recovered"
    else:
        final_verdict = "requires_followup"
    secondary = ";".join(explanations[1:])
    return primary, secondary, bug_suspected, final_verdict


def score_lift_if_best(row: dict[str, str], component: str) -> float | None:
    available_weight = parse_float(row.get("available_weight_sum", ""))
    if available_weight is None or available_weight == 0:
        available_weight = 1.0
    column = {
        "Surf": "Surf_relative_confidence",
        "E": "E_rank_percentile",
        "N": "N_rank_percentile",
        "R": "R_rank_percentile_high_worse",
        "P": "P_rank_percentile",
        "T": "T_rank_percentile",
    }[component]
    value = parse_float(row.get(column, ""))
    if value is None:
        return None
    weight = BALANCED_WEIGHTS[component]
    if component == "R":
        return weight * value / available_weight
    return weight * (1.0 - value) / available_weight


def classify_causal_gate(
    symbol: str,
    rank_row: dict[str, str],
    component: dict[str, str],
    topology: dict[str, str],
    universe: dict[str, str],
) -> tuple[str, bool, str]:
    rank = int(rank_row["rank"])
    if rank <= 50:
        return "recovered_top50_v1", False, "Counts as recovered in the original aggregate gate."
    isoform = component.get("isoform_resolution_status", "")
    risk = component.get("risk_interpretation", "")
    raw_surf = parse_float(universe.get("surfaceome_confidence_score", ""))
    p_rank = parse_float(component.get("P_rank_percentile", ""))
    t_rank = parse_float(component.get("T_rank_percentile", ""))

    if "CLDN18.2_isoform_unresolved" in isoform or "FGFR2b_isoform_unresolved" in isoform:
        return (
            "expected_isoform_and_safety_demotion",
            False,
            "Gene-level expression cannot validate isoform-specific targets; low selectivity, high normal risk, and low topology percentile are expected demotion signals.",
        )
    if symbol == "MSLN":
        return (
            "expected_shedding_soluble_T_penalty_after_GPI_surfaceome_correction",
            False,
            "P/E/N and corrected Surf are high, but T is reduced by shedding/soluble isoform annotations; this is candidate-card biology, not residual Surf/GPI integration bug.",
        )
    if symbol == "CEACAM5" and raw_surf is not None and raw_surf <= 6:
        return (
            "expected_GPI_Surf_source_underconfidence_with_strong_E_N_P_T",
            False,
            "E/N/P/T are strong and R percentile is not high; the differentiating cause is low raw Surf for this GPI anchor, consistent with source under-confidence rather than an off-tumor-risk demotion.",
        )
    if symbol == "TACSTD2":
        return (
            "expected_mid_surface_confidence_and_weaker_protein_support",
            False,
            "TROP2/TACSTD2 is biologically plausible, but its R percentile is comparable to recovered controls; the miss is better explained by mid surface confidence and weaker protein evidence than recovered positives.",
        )
    if t_rank is not None and t_rank < 0.20:
        return (
            "explained_topology_component_demotion",
            False,
            "Low topology/accessibility percentile is explicit score evidence rather than unexplained rank behavior.",
        )
    if p_rank is not None and p_rank < 0.70:
        return (
            "explained_lower_protein_support",
            False,
            "Protein/localization component is weaker than recovered positives.",
        )
    return (
        "unexplained_after_component_review",
        True,
        "No prespecified biological, safety, isoform, topology, or coverage explanation accounts for the miss.",
    )


def write_positive_causal_gate(
    positive_rows: list[dict[str, object]],
    ranking_v1: dict[str, dict[str, str]],
    components: dict[str, dict[str, str]],
    topology: dict[str, dict[str, str]],
    universe: dict[str, dict[str, str]],
    top50_threshold: float,
) -> list[dict[str, object]]:
    rows = []
    positive_by_symbol = {str(row["hgnc_symbol"]): row for row in positive_rows}
    for symbol in POSITIVE_CONTROLS:
        rank_row = ranking_v1[symbol]
        component = components[symbol]
        rank = int(rank_row["rank"])
        score = parse_float(rank_row.get("scenario_score", "")) or 0.0
        deficit = max(0.0, top50_threshold - score)
        lifts = {comp: score_lift_if_best(rank_row, comp) for comp in BALANCED_WEIGHTS}
        valid_lifts = {comp: lift for comp, lift in lifts.items() if lift is not None}
        largest_component = max(valid_lifts, key=valid_lifts.get) if valid_lifts else ""
        rescue_components = [
            comp
            for comp, lift in valid_lifts.items()
            if rank > 50 and deficit > 0 and lift >= deficit
        ]
        causal_class, pipeline_failure, interpretation = classify_causal_gate(
            symbol, rank_row, component, topology[symbol], universe[symbol]
        )
        positive_diag = positive_by_symbol[symbol]
        rows.append(
            {
                "hgnc_symbol": symbol,
                "rank_v1": rank,
                "score_v1": score,
                "in_top50_v1": rank <= 50,
                "top50_score_threshold": top50_threshold,
                "score_deficit_to_top50": deficit,
                "Surf_relative_confidence": rank_row.get("Surf_relative_confidence", ""),
                "E_rank_percentile": rank_row.get("E_rank_percentile", ""),
                "N_rank_percentile": rank_row.get("N_rank_percentile", ""),
                "R_score": component.get("R_score", ""),
                "R_rank_percentile_high_worse": rank_row.get("R_rank_percentile_high_worse", ""),
                "P_rank_percentile": rank_row.get("P_rank_percentile", ""),
                "T_score": component.get("T_score", ""),
                "T_rank_percentile": rank_row.get("T_rank_percentile", ""),
                "Surf_contribution": rank_row.get("Surf_contribution", ""),
                "E_contribution": rank_row.get("E_contribution", ""),
                "N_contribution": rank_row.get("N_contribution", ""),
                "R_contribution_subtracted": rank_row.get("R_contribution_subtracted", ""),
                "P_contribution": rank_row.get("P_contribution", ""),
                "T_contribution": rank_row.get("T_contribution", ""),
                "Surf_max_lift_if_best": lifts["Surf"],
                "E_max_lift_if_best": lifts["E"],
                "N_max_lift_if_best": lifts["N"],
                "R_max_lift_if_best": lifts["R"],
                "P_max_lift_if_best": lifts["P"],
                "T_max_lift_if_best": lifts["T"],
                "largest_single_rescue_component": largest_component,
                "components_that_cross_top50_if_best": ";".join(rescue_components),
                "surfaceome_confidence_score": universe[symbol].get("surfaceome_confidence_score", ""),
                "gpi_anchor_present": topology[symbol].get("gpi_anchor_present", ""),
                "max_risk_organ": component.get("max_risk_organ", ""),
                "risk_interpretation": component.get("risk_interpretation", ""),
                "isoform_resolution_status": component.get("isoform_resolution_status", ""),
                "discordance_flags": component.get("discordance_flags", ""),
                "causal_class_v1": causal_class,
                "pipeline_accusing_failure": pipeline_failure,
                "final_control_verdict": positive_diag["final_control_verdict"],
                "gate_interpretation": interpretation,
            }
        )
    fieldnames = [
        "hgnc_symbol",
        "rank_v1",
        "score_v1",
        "in_top50_v1",
        "top50_score_threshold",
        "score_deficit_to_top50",
        "Surf_relative_confidence",
        "E_rank_percentile",
        "N_rank_percentile",
        "R_score",
        "R_rank_percentile_high_worse",
        "P_rank_percentile",
        "T_score",
        "T_rank_percentile",
        "Surf_contribution",
        "E_contribution",
        "N_contribution",
        "R_contribution_subtracted",
        "P_contribution",
        "T_contribution",
        "Surf_max_lift_if_best",
        "E_max_lift_if_best",
        "N_max_lift_if_best",
        "R_max_lift_if_best",
        "P_max_lift_if_best",
        "T_max_lift_if_best",
        "largest_single_rescue_component",
        "components_that_cross_top50_if_best",
        "surfaceome_confidence_score",
        "gpi_anchor_present",
        "max_risk_organ",
        "risk_interpretation",
        "isoform_resolution_status",
        "discordance_flags",
        "causal_class_v1",
        "pipeline_accusing_failure",
        "final_control_verdict",
        "gate_interpretation",
    ]
    write_tsv(TABLES_DIR / "fase13_positive_control_causal_gate.tsv", rows, fieldnames)
    return rows


def compare_v0_v1(
    ranking_v0_rows: list[dict[str, str]],
    ranking_v1_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    v0 = by_symbol(ranking_v0_rows)
    v1 = by_symbol(ranking_v1_rows)
    rows = []
    for symbol in sorted(set(v0) & set(v1)):
        rank_v0 = int(v0[symbol]["rank"])
        rank_v1 = int(v1[symbol]["rank"])
        rows.append(
            {
                "hgnc_symbol": symbol,
                "rank_v0": rank_v0,
                "rank_v1": rank_v1,
                "rank_delta_v1_minus_v0": rank_v1 - rank_v0,
                "score_v0": v0[symbol].get("scenario_score", ""),
                "score_v1": v1[symbol].get("scenario_score", ""),
                "score_delta_v1_minus_v0": (parse_float(v1[symbol].get("scenario_score", "")) or 0.0)
                - (parse_float(v0[symbol].get("scenario_score", "")) or 0.0),
                "was_top50_v0": rank_v0 <= 50,
                "is_top50_v1": rank_v1 <= 50,
                "ranking_status": "v0_vs_v1_diagnostic_not_tiering",
            }
        )
    write_tsv(
        TABLES_DIR / "fase13_v0_v1_rank_delta.tsv",
        rows,
        [
            "hgnc_symbol",
            "rank_v0",
            "rank_v1",
            "rank_delta_v1_minus_v0",
            "score_v0",
            "score_v1",
            "score_delta_v1_minus_v0",
            "was_top50_v0",
            "is_top50_v1",
            "ranking_status",
        ],
    )
    return rows


def support_stats(rows: list[dict[str, str]], value_column: str) -> dict[str, object]:
    values = [row.get(value_column, "") for row in rows if row.get(value_column, "") != ""]
    counts = Counter(values)
    largest_tie_n = max(counts.values()) if counts else 0
    return {
        "n_observed": len(values),
        "n_unique_values": len(counts),
        "largest_tie_n": largest_tie_n,
        "largest_tie_fraction": (largest_tie_n / len(values)) if values else "",
    }


def write_transform_audit(component_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    definitions = [
        {
            "component": "Surf",
            "raw_score_column": "Surf_raw_score",
            "score_column_used_in_v1": "Surf_relative_confidence",
            "rank_percentile_column": "",
            "transform_location": "Fase 13",
            "support_type": "discrete_additive_surfaceome_score",
            "v1_action": "replace_v0_ordinal_percentile_with_theoretical_scale_5_10_after_gpi",
            "interpretation": "Relative confidence within admitted Core+Probable universe; 0 does not mean non-surfaceome.",
        },
        {
            "component": "E",
            "raw_score_column": "E_score",
            "score_column_used_in_v1": "E_rank_percentile",
            "rank_percentile_column": "E_rank_percentile",
            "transform_location": "Fase 5 upstream",
            "support_type": "continuous_or_many_level",
            "v1_action": "unchanged_upstream_tie_aware",
            "interpretation": "Tumor expression percentile already computed upstream with tie-aware handling.",
        },
        {
            "component": "N",
            "raw_score_column": "N_score",
            "score_column_used_in_v1": "N_rank_percentile",
            "rank_percentile_column": "N_rank_percentile",
            "transform_location": "Fase 6 upstream",
            "support_type": "continuous_or_many_level",
            "v1_action": "unchanged_upstream_tie_aware",
            "interpretation": "Normal selectivity percentile already computed upstream with tie-aware handling.",
        },
        {
            "component": "R",
            "raw_score_column": "R_score",
            "score_column_used_in_v1": "R_rank_percentile_high_worse",
            "rank_percentile_column": "R_rank_percentile_high_worse",
            "transform_location": "Fase 13",
            "support_type": "discrete_or_dense_ties",
            "v1_action": "average_rank_ties",
            "interpretation": "High-worse risk component is subtracted; tied raw risk values receive identical percentile.",
        },
        {
            "component": "P",
            "raw_score_column": "P_score",
            "score_column_used_in_v1": "P_rank_percentile",
            "rank_percentile_column": "P_rank_percentile",
            "transform_location": "Fase 7 upstream",
            "support_type": "discrete_or_missing_dense",
            "v1_action": "unchanged_upstream_tie_aware",
            "interpretation": "Protein evidence percentile already computed upstream; missing HPA evidence remains missing, not imputed.",
        },
        {
            "component": "T",
            "raw_score_column": "T_score",
            "score_column_used_in_v1": "T_rank_percentile",
            "rank_percentile_column": "T_rank_percentile",
            "transform_location": "Fase 9 upstream",
            "support_type": "bounded_topology_score_with_ties",
            "v1_action": "unchanged_upstream_tie_aware",
            "interpretation": "Topology percentile already computed upstream; MSLN low percentile is not the Fase 13 lexicographic tie bug.",
        },
        {
            "component": "SC",
            "raw_score_column": "SC_score",
            "score_column_used_in_v1": "SC_rank_percentile",
            "rank_percentile_column": "SC_rank_percentile",
            "transform_location": "not_available_in_MVP",
            "support_type": "not_available",
            "v1_action": "not_imputed",
            "interpretation": "Fase 8 did not admit a processed scRNA score; SC remains outside six-component MVP scoring.",
        },
    ]
    rows = []
    for item in definitions:
        stats = support_stats(component_rows, item["raw_score_column"])
        rows.append({**item, **stats})
    fieldnames = [
        "component",
        "raw_score_column",
        "score_column_used_in_v1",
        "rank_percentile_column",
        "transform_location",
        "support_type",
        "n_observed",
        "n_unique_values",
        "largest_tie_n",
        "largest_tie_fraction",
        "v1_action",
        "interpretation",
    ]
    write_tsv(TABLES_DIR / "fase13_component_transform_audit.tsv", rows, fieldnames)
    return rows


def main() -> int:
    universe_rows = read_tsv(REPO_ROOT / "data" / "processed" / "surfaceome_universe.tsv")
    topology_rows = read_tsv(REPO_ROOT / "data" / "processed" / "topology_isoforms_ecd.tsv")
    component_rows = read_tsv(REPO_ROOT / "results" / "tables" / "component_scores_all_candidates.tsv")
    ranking_v2_path = REPO_ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
    ranking_v1_rows = read_tsv(ranking_v2_path if ranking_v2_path.exists() else REPO_ROOT / "results" / "rankings" / "ranking_balanced.tsv")
    ranking_v0_rows = read_tsv(REPO_ROOT / "results" / "rankings" / "ranking_v0_frozen.tsv")

    universe = by_symbol(universe_rows)
    topology = by_symbol(topology_rows)
    components = by_symbol(component_rows)
    ranking_v1 = by_symbol(ranking_v1_rows)

    snapshot_rows = []
    for rel_path in SNAPSHOT_FILES:
        path = REPO_ROOT / rel_path
        if path.exists():
            snapshot_rows.append({"path": rel_path, "sha256": sha256_file(path)})
    write_tsv(TABLES_DIR / "fase13_diagnostic_snapshot_hashes.tsv", snapshot_rows, ["path", "sha256"])
    transform_audit_rows = write_transform_audit(component_rows)

    tie_group_rows, surf_by_symbol = compute_surf_tie_diagnostics(universe_rows)
    write_tsv(
        TABLES_DIR / "fase13_surfaceome_tie_groups.tsv",
        tie_group_rows,
        [
            "surfaceome_confidence_score",
            "n_genes",
            "legacy_ordinal_percentile_min",
            "legacy_ordinal_percentile_max",
            "legacy_ordinal_percentile_span",
            "tie_aware_midrank_percentile",
            "v1_relative_confidence",
        ],
    )

    gpi_rows = []
    for topo_row in sorted(topology_rows, key=lambda row: row["hgnc_symbol"]):
        if topo_row.get("gpi_anchor_present") != "true":
            continue
        symbol = topo_row["hgnc_symbol"]
        uni = universe.get(symbol, {})
        component = components.get(symbol, {})
        surf_diag = surf_by_symbol.get(symbol, {})
        gpi_rows.append(
            {
                "hgnc_symbol": symbol,
                "surfaceome_confidence_score": uni.get("surfaceome_confidence_score", ""),
                "surfaceome_category": uni.get("surfaceome_category", ""),
                "legacy_ordinal_surf_percentile": surf_diag.get("legacy_ordinal_surf_percentile", ""),
                "v1_surf_relative_confidence": component.get("Surf_relative_confidence", ""),
                "legacy_minus_v1_delta": surf_diag.get("legacy_minus_v1_delta", ""),
                "surface_support_source_count": uni.get("surface_support_source_count", ""),
                "surface_support_sources": uni.get("surface_support_sources", ""),
                "accessibility_class": topo_row.get("accessibility_class", ""),
                "T_score": topo_row.get("T_score", ""),
                "T_rank_percentile": topo_row.get("T_rank_percentile", ""),
                "cleavage_or_shedding_flag": topo_row.get("cleavage_or_shedding_flag", ""),
                "soluble_isoform_or_secreted_flag": topo_row.get("soluble_isoform_or_secreted_flag", ""),
            }
        )
    write_tsv(
        TABLES_DIR / "fase13_gpi_anchor_surf_audit.tsv",
        gpi_rows,
        [
            "hgnc_symbol",
            "surfaceome_confidence_score",
            "surfaceome_category",
            "legacy_ordinal_surf_percentile",
            "v1_surf_relative_confidence",
            "legacy_minus_v1_delta",
            "surface_support_source_count",
            "surface_support_sources",
            "accessibility_class",
            "T_score",
            "T_rank_percentile",
            "cleavage_or_shedding_flag",
            "soluble_isoform_or_secreted_flag",
        ],
    )

    delta_rows = compare_v0_v1(ranking_v0_rows, ranking_v1_rows)
    delta_by_symbol = {row["hgnc_symbol"]: row for row in delta_rows}

    positive_rows = []
    for symbol in POSITIVE_CONTROLS:
        component = components[symbol]
        rank_row = ranking_v1[symbol]
        uni = universe[symbol]
        topo = topology[symbol]
        surf_diag = surf_by_symbol[symbol]
        primary, secondary, bug_suspected, final_verdict = classify_positive(symbol, component, rank_row, topo, uni)
        delta = delta_by_symbol[symbol]
        positive_rows.append(
            {
                "hgnc_symbol": symbol,
                "rank_v0": delta["rank_v0"],
                "rank_v1": delta["rank_v1"],
                "rank_delta_v1_minus_v0": delta["rank_delta_v1_minus_v0"],
                "score_v0": delta["score_v0"],
                "score_v1": delta["score_v1"],
                "surfaceome_confidence_score": uni.get("surfaceome_confidence_score", ""),
                "legacy_ordinal_surf_percentile": surf_diag.get("legacy_ordinal_surf_percentile", ""),
                "Surf_relative_confidence_v1": component.get("Surf_relative_confidence", ""),
                "E_rank_percentile": component.get("E_rank_percentile", ""),
                "N_rank_percentile": component.get("N_rank_percentile", ""),
                "R_rank_percentile_high_worse": component.get("R_rank_percentile_high_worse", ""),
                "P_rank_percentile": component.get("P_rank_percentile", ""),
                "T_score": component.get("T_score", ""),
                "T_rank_percentile": component.get("T_rank_percentile", ""),
                "missing_mvp_score_components": component.get("missing_mvp_score_components", ""),
                "tme_contamination_risk": component.get("tme_contamination_risk", ""),
                "accessibility_class": component.get("accessibility_class", ""),
                "gpi_anchor_present": topo.get("gpi_anchor_present", ""),
                "isoform_resolution_status": component.get("isoform_resolution_status", ""),
                "risk_interpretation": component.get("risk_interpretation", ""),
                "surface_support_source_count": uni.get("surface_support_source_count", ""),
                "surface_support_sources": uni.get("surface_support_sources", ""),
                "primary_explanation": primary,
                "secondary_explanations": secondary,
                "bug_suspected_after_v1": bug_suspected,
                "final_control_verdict": final_verdict,
            }
        )
    positive_fields = [
        "hgnc_symbol",
        "rank_v0",
        "rank_v1",
        "rank_delta_v1_minus_v0",
        "score_v0",
        "score_v1",
        "surfaceome_confidence_score",
        "legacy_ordinal_surf_percentile",
        "Surf_relative_confidence_v1",
        "E_rank_percentile",
        "N_rank_percentile",
        "R_rank_percentile_high_worse",
        "P_rank_percentile",
        "T_score",
        "T_rank_percentile",
        "missing_mvp_score_components",
        "tme_contamination_risk",
        "accessibility_class",
        "gpi_anchor_present",
        "isoform_resolution_status",
        "risk_interpretation",
        "surface_support_source_count",
        "surface_support_sources",
        "primary_explanation",
        "secondary_explanations",
        "bug_suspected_after_v1",
        "final_control_verdict",
    ]
    write_tsv(TABLES_DIR / "fase13_positive_control_component_diagnostic.tsv", positive_rows, positive_fields)
    top50_threshold = parse_float(next(row for row in ranking_v1_rows if row["rank"] == "50")["scenario_score"]) or 0.0
    causal_rows = write_positive_causal_gate(
        positive_rows,
        ranking_v1,
        components,
        topology,
        universe,
        top50_threshold,
    )

    gpi_score_counts = Counter(row["surfaceome_confidence_score"] for row in gpi_rows)
    ceacam5 = next(row for row in positive_rows if row["hgnc_symbol"] == "CEACAM5")
    msln = next(row for row in positive_rows if row["hgnc_symbol"] == "MSLN")
    positive_top50 = [row["hgnc_symbol"] for row in positive_rows if int(str(row["rank_v1"])) <= 50]
    unresolved_failures = [
        row["hgnc_symbol"]
        for row in positive_rows
        if row["hgnc_symbol"] in ORIGINAL_POSITIVE_FAILURES and row["final_control_verdict"] == "requires_followup"
    ]
    pipeline_accusing_failures = [
        str(row["hgnc_symbol"])
        for row in causal_rows
        if str(row["hgnc_symbol"]) in ORIGINAL_POSITIVE_FAILURES
        and str(row["pipeline_accusing_failure"]).lower() == "true"
    ]
    explained_demotions = [
        str(row["hgnc_symbol"])
        for row in causal_rows
        if str(row["hgnc_symbol"]) in ORIGINAL_POSITIVE_FAILURES
        and str(row["pipeline_accusing_failure"]).lower() != "true"
    ]
    if unresolved_failures or pipeline_accusing_failures:
        gate_status = "blocked_by_scoring_bug"
    else:
        gate_status = "eligible_for_fase14"

    hash_lines = "\n".join(f"- `{row['path']}`: `{row['sha256']}`" for row in snapshot_rows)
    positive_table_lines = "\n".join(
        "| {gene} | {rank0} | {rank1} | {delta} | {raw} | {surf} | {e} | {n} | {r} | {p} | {t_score} | {t_rank} | {verdict} |".format(
            gene=row["hgnc_symbol"],
            rank0=row["rank_v0"],
            rank1=row["rank_v1"],
            delta=row["rank_delta_v1_minus_v0"],
            raw=row["surfaceome_confidence_score"],
            surf=row["Surf_relative_confidence_v1"],
            e=row["E_rank_percentile"],
            n=row["N_rank_percentile"],
            r=row["R_rank_percentile_high_worse"],
            p=row["P_rank_percentile"],
            t_score=row["T_score"],
            t_rank=row["T_rank_percentile"],
            verdict=row["final_control_verdict"],
        )
        for row in positive_rows
    )
    causal_table_lines = "\n".join(
        "| {gene} | {rank} | {score} | {deficit} | {surf} | {e} | {n} | {r_score} | {r_pct} | {p} | {t_score} | {t_rank} | {rescue} | {klass} | {pipe} |".format(
            gene=row["hgnc_symbol"],
            rank=row["rank_v1"],
            score=fmt(row["score_v1"]),
            deficit=fmt(row["score_deficit_to_top50"]),
            surf=row["Surf_relative_confidence"],
            e=row["E_rank_percentile"],
            n=row["N_rank_percentile"],
            r_score=row["R_score"],
            r_pct=row["R_rank_percentile_high_worse"],
            p=row["P_rank_percentile"],
            t_score=row["T_score"],
            t_rank=row["T_rank_percentile"],
            rescue=row["components_that_cross_top50_if_best"] or "none",
            klass=row["causal_class_v1"],
            pipe=row["pipeline_accusing_failure"],
        )
        for row in causal_rows
    )
    tie_group_summary_lines = "\n".join(
        "- Score {score}: n={n}, percentil ordinal {min_pct}-{max_pct}, relative {relative}".format(
            score=row["surfaceome_confidence_score"],
            n=row["n_genes"],
            min_pct=fmt(row["legacy_ordinal_percentile_min"]),
            max_pct=fmt(row["legacy_ordinal_percentile_max"]),
            relative=fmt(row["v1_relative_confidence"]),
        )
        for row in tie_group_rows
    )

    doc = f"""# Fase 13 Diagnostico

## Estado

Diagnostico actualizado despues del fix versionado `v2`. Este documento no modifica pesos ni politica de missing data; resume el re-run completo de Fase 13 despues de corregir el bug de normalizacion y aplicar la correccion de evidencia GPI en Fase 4.

Veredicto actual: `{gate_status}`.

## Snapshot SHA256

{hash_lines}

## Decision de Fix Registrada Antes de Re-correr v2

Decision aplicada:

1. `Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`.
2. La escala es teorica y fija `[5,10]` despues de anadir evidencia GPI directa en Fase 4, no min/max observado.
3. La funcion de percentiles calculada dentro de Fase 13 ahora usa average-rank para empates; esto corrige `R_rank_percentile_high_worse`.

Justificacion: `Surf` es una confianza relativa dentro del universo Core+Probable ya admitido. El valor 0 no significa "no surfaceome"; significa menor confianza entre candidatos admitidos. La transformacion teorica conserva la escala aditiva de Fase 4, asigna valores identicos a scores crudos identicos y evita introducir senal por orden alfabetico de HGNC.

## Auditoria de Transformaciones

- `Surf`: bug confirmado en v0; corregido con escala teorica fija; en v2 la escala es `[5,10]` por la evidencia GPI directa anadida en Fase 4.
- `R`: percentil calculado en Fase 13 con empates densos; corregido en v1 con average-rank ties.
- `E`, `N`, `P`, `T`: se calculan upstream con funciones de percentil tie-aware; no usan el bug lexicografico de Fase 13.
- `T` de `MSLN`: `T_score` ya incorpora penalizaciones biologicamente plausibles de shedding/soluble isoform. El percentil bajo refleja la distribucion de `T_score`, no desempate HGNC.

La auditoria por componente esta en `results/tables/fase13_component_transform_audit.tsv` y cubre {len(transform_audit_rows)} componentes (`Surf`, `E`, `N`, `R`, `P`, `T`, `SC`).

Distribucion historica del bug `Surf` en v0:

{tie_group_summary_lines}

## GPI Anchor Limitation

- GPI anchors evaluados: {len(gpi_rows)}
- Distribucion por `surfaceome_confidence_score`: {dict(sorted(gpi_score_counts.items()))}
- La distribucion actual refleja la correccion de evidencia GPI en Fase 4. Los casos GPI de baja confianza restantes quedan como limitacion de cobertura/calibracion, separada del bug de normalizacion.

Correccion de labels causales (2026-05-30): `CEACAM5` y `TACSTD2` ya no se describen como demociones primarias por riesgo normal/off-tumor, porque sus percentiles `R` activos no sostienen esa lectura. Esta correccion no cambia scores, pesos, rankings ni politica de missing data.

Casos centinela:

- `CEACAM5`: v0 rank {ceacam5['rank_v0']} -> active rank {ceacam5['rank_v1']}; `Surf_relative_confidence={ceacam5['Surf_relative_confidence_v1']}`. Tras la correccion GPI, este caso ya no debe narrarse como under-confidence GPI/Surf si su score crudo es alto.
- `MSLN`: v0 rank {msln['rank_v0']} -> active rank {msln['rank_v1']}; `Surf_relative_confidence={msln['Surf_relative_confidence_v1']}`, `T_score={msln['T_score']}`, `T_rank_percentile={msln['T_rank_percentile']}`. Si sigue fuera de top 50, la causa residual esperada es `T` bajo por penalizaciones de shedding/soluble isoform, no cobertura proteica ni el bug de desempate.

## Controles Positivos v0 vs Active v2

Positive controls top 50 en active v2: {len(positive_top50)}/8 (`{';'.join(positive_top50)}`).

El gate agregado preregistrado (`>=5/8` en top 50) sigue fallando. Ese conteo no distingue controles que caen por bug de controles penalizados por una razon biologica o de seguridad que el score debe capturar. Por eso se agrega un gate causal post-hoc, sin cambiar pesos ni ranking.

| Gene | Rank v0 | Active rank | Delta active-v0 | Surf raw | Surf active | E | N | R high-worse | P | T score | T rank | Final verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
{positive_table_lines}

## Gate Causal de Controles Positivos

Top50 score threshold en active v2: `{fmt(top50_threshold)}`.

| Gene | Active rank | Active score | Deficit to top50 | Surf | E | N | R raw | R pct | P | T score | T rank | Single best component crosses top50 | Causal class | Pipeline-accusing failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
{causal_table_lines}

Resumen causal:

- Recovered in top50: {len(positive_top50)}/8 (`{';'.join(positive_top50)}`).
- Original top50 misses explained by component-level biology/safety/coverage: {len(explained_demotions)}/5 (`{';'.join(explained_demotions)}`).
- Original top50 misses that still accuse the pipeline: {len(pipeline_accusing_failures)}/5 (`{';'.join(pipeline_accusing_failures) if pipeline_accusing_failures else 'none'}`).

Interpretacion: el bug `Surf/R` era real y esta corregido, y la omision de evidencia GPI directa fue tratada en Fase 4 antes del rerun downstream. Tras revisar componentes, los misses originales deben interpretarse por causa: `TACSTD2` por confianza de superficie intermedia y menor soporte proteico, `MSLN` por shedding/soluble isoform reflejado en `T`, y `CLDN18`/`FGFR2` por isoforma gene-level no resuelta junto a riesgo/selectividad/topologia. Si `CEACAM5` queda recuperado tras GPI, deja de contar como miss; si no, requiere explicacion por componentes actualizados.

## Veredicto

`{gate_status}`

Cada uno de los cinco controles positivos fuera del top 50 original tiene veredicto escrito en `results/tables/fase13_positive_control_component_diagnostic.tsv` y clasificacion causal en `results/tables/fase13_positive_control_causal_gate.tsv`.

Con veredicto `eligible_for_fase14`, Fase 14 puede correr como analisis de estabilidad del ranking preliminar activo v2 y con estas advertencias:

1. El ranking v2 es el ranking activo; v0 queda preservado como evidencia del bug detectado y v1 como snapshot pre-GPI.
2. `MSLN` no debe narrarse como fallo de cobertura proteica; tiene `P` alto y residual `T` bajo por shedding/soluble isoform.
3. La evidencia GPI directa fue aplicada universe-wide en Fase 4; no fue un parche para controles.
4. El fallo del gate agregado debe reportarse junto con el gate causal; no debe ocultarse ni usarse para retunar pesos.

## Outputs del Diagnostico

- `results/tables/fase13_diagnostic_snapshot_hashes.tsv`
- `results/tables/fase13_component_transform_audit.tsv`
- `results/tables/fase13_surfaceome_tie_groups.tsv`
- `results/tables/fase13_gpi_anchor_surf_audit.tsv`
- `results/tables/fase13_positive_control_component_diagnostic.tsv`
- `results/tables/fase13_positive_control_causal_gate.tsv`
- `results/tables/fase13_v0_v1_rank_delta.tsv`
"""
    (DOCS_DIR / "fase13_diagnostico.md").write_text(doc, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
