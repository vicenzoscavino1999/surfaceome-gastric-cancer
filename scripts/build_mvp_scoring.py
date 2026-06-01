"""Build Fase 13 MVP integrated score outputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "results" / "tables"
RANKINGS_DIR = REPO_ROOT / "results" / "rankings"
VALIDATION_DIR = REPO_ROOT / "results" / "validation"
DOCS_DIR = REPO_ROOT / "docs"

SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
TUMOR_EXPRESSION = PROCESSED_DIR / "tumor_expression.tsv"
SELECTIVITY_SCORES = PROCESSED_DIR / "selectivity_scores.tsv"
OFF_TUMOR_RISK = PROCESSED_DIR / "off_tumor_risk.tsv"
PROTEIN_EVIDENCE = PROCESSED_DIR / "protein_evidence.tsv"
SINGLE_CELL_SPECIFICITY = PROCESSED_DIR / "single_cell_specificity.tsv"
TOPOLOGY_ISOFORMS = PROCESSED_DIR / "topology_isoforms_ecd.tsv"

SCORING_CONFIG = REPO_ROOT / "config" / "scoring_scenarios.yaml"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"
CONTROLS_CONFIG = REPO_ROOT / "config" / "controls.yaml"
EXCLUSION_CONFIG = REPO_ROOT / "config" / "exclusion_criteria.yaml"
RELEASE_MANIFEST = REPO_ROOT / "config" / "release_manifest.yaml"

COMPONENT_TABLE = TABLES_DIR / "component_scores_all_candidates.tsv"
TIERING_ANNOTATIONS = TABLES_DIR / "tiering_annotations_all_candidates.tsv"
CONTROL_RECOVERY = TABLES_DIR / "control_recovery_phase13.tsv"
FUNCTIONAL_FORM_SENSITIVITY = VALIDATION_DIR / "functional_form_sensitivity.tsv"
POST_SCORING_SANITY = VALIDATION_DIR / "phase13_post_scoring_sanity.tsv"
PHASE13_NOTE = DOCS_DIR / "fase13_mvp_score_integration.md"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
MVP_COMPONENTS = ["Surf", "E", "N", "R", "P", "T"]
SCENARIO_OUTPUTS = {
    "balanced": RANKINGS_DIR / "ranking_balanced.tsv",
    "safety_first": RANKINGS_DIR / "ranking_safety_first.tsv",
    "adc_focused": RANKINGS_DIR / "ranking_adc_focused.tsv",
    "novelty_focused": RANKINGS_DIR / "ranking_novelty.tsv",
    "protein_first": RANKINGS_DIR / "ranking_protein_first.tsv",
}
ROBUST_AGGREGATE = RANKINGS_DIR / "ranking_robust_aggregate.tsv"
FROZEN_V0_SOURCE = REPO_ROOT / "data" / "raw" / "frozen_snapshots" / "ranking_v0_frozen.tsv"
FROZEN_V1_SOURCE = REPO_ROOT / "data" / "raw" / "frozen_snapshots" / "ranking_v1_frozen.tsv"
FROZEN_V0 = RANKINGS_DIR / "ranking_v0_frozen.tsv"
FROZEN_V1 = RANKINGS_DIR / "ranking_v1_frozen.tsv"
FROZEN_V2 = RANKINGS_DIR / "ranking_v2_frozen.tsv"
FROZEN_V2_METADATA = RANKINGS_DIR / "ranking_v2_frozen.metadata.yaml"
RANKING_STATUS = "preliminary_fase13_mvp_not_final_tiering"
FREEZE_VERSION = "v2"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field, "")) for field in fieldnames})


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def format_value(value: object, digits: int = 6) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.{digits}f}"
    return str(value)


def parse_float(value: object) -> float | None:
    if value is None:
        return None
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


def write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8", newline="\n")


def materialize_archived_ranking_snapshots() -> None:
    """Restore historical v0/v1 snapshots from frozen raw inputs."""
    for source, target in [(FROZEN_V0_SOURCE, FROZEN_V0), (FROZEN_V1_SOURCE, FROZEN_V1)]:
        if not source.exists():
            raise FileNotFoundError(f"Missing archived ranking snapshot source: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.strip()


def git_dirty_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return "dirty" if result.stdout.strip() else "clean"


def frozen_v2_metadata(default_commit: str, default_dirty: str) -> tuple[str, str, str]:
    generated_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    if not RELEASE_MANIFEST.exists():
        return default_commit, default_dirty, generated_date

    manifest = load_yaml(RELEASE_MANIFEST)
    metadata = (
        manifest.get("data_freeze", {})
        .get("score_integration", {})
        .get("frozen_v2_metadata", {})
    )
    commit = str(
        metadata.get("generation_git_commit")
        or metadata.get("git_commit")
        or default_commit
    )
    dirty = str(
        metadata.get("generation_git_worktree_status")
        or metadata.get("git_worktree_status_at_freeze")
        or default_dirty
    )
    freeze_date = str(metadata.get("freeze_date_utc") or generated_date)
    return commit, dirty, freeze_date


def rank_percentiles(rows: list[dict[str, object]], value_key: str) -> dict[str, float]:
    valid: list[tuple[str, float]] = []
    for row in rows:
        value = parse_float(row.get(value_key))
        if value is not None:
            valid.append((str(row["hgnc_symbol"]), value))
    if not valid:
        return {}
    ordered = sorted(enumerate(valid), key=lambda item: item[1][1])
    ranks = [0.0] * len(valid)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1][1] == ordered[start][1][1]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for original_index, _ in ordered[start:end]:
            ranks[original_index] = average_rank
        start = end
    if len(valid) == 1:
        return {valid[0][0]: 1.0}
    denominator = len(valid) - 1
    return {symbol: (rank - 1.0) / denominator for (symbol, _), rank in zip(valid, ranks)}


def surfaceome_relative_confidence(raw_score: object) -> float | None:
    value = parse_float(raw_score)
    if value is None:
        return None
    # After the Fase 4 GPI evidence correction, the theoretical admitted
    # Core+Probable confidence range is [5, 10].
    # Do not use observed min/max; that would make the mapping universe-dependent.
    return min(1.0, max(0.0, (value - 5.0) / 5.0))


def table_by_symbol(path: Path) -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in read_tsv(path)}


def component_value(row: dict[str, object], component: str) -> float | None:
    keys = {
        "Surf": "Surf_relative_confidence",
        "E": "E_rank_percentile",
        "N": "N_rank_percentile",
        "R": "R_rank_percentile_high_worse",
        "P": "P_rank_percentile",
        "SC": "SC_rank_percentile",
        "T": "T_rank_percentile",
    }
    return parse_float(row.get(keys[component]))


def available_mvp_components(row: dict[str, object]) -> list[str]:
    return [component for component in MVP_COMPONENTS if component_value(row, component) is not None]


def compute_scenario_score(
    row: dict[str, object],
    weights: dict[str, float],
) -> tuple[float | None, float, dict[str, float], list[str]]:
    numerator = 0.0
    denominator = 0.0
    contributions: dict[str, float] = {}
    missing: list[str] = []
    for component, raw_weight in weights.items():
        weight = float(raw_weight)
        if weight == 0:
            continue
        value = component_value(row, component)
        if value is None:
            missing.append(component)
            continue
        signed_weight = -weight if component == "R" else weight
        contribution = signed_weight * value
        contributions[component] = contribution
        numerator += contribution
        denominator += abs(weight)
    if denominator == 0:
        return None, 0.0, contributions, missing
    return numerator / denominator, denominator, contributions, missing


def rank_rows(
    rows: list[dict[str, object]],
    score_key: str,
    rank_key: str = "rank",
) -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -(parse_float(row.get(score_key)) if parse_float(row.get(score_key)) is not None else -math.inf),
            str(row.get("hgnc_symbol", "")),
        ),
    )
    for index, row in enumerate(ranked, start=1):
        row[rank_key] = index
    return ranked


def score_rows(
    component_rows: list[dict[str, object]],
    scenarios: dict[str, object],
) -> dict[str, list[dict[str, object]]]:
    scored_by_scenario: dict[str, list[dict[str, object]]] = {}
    for scenario_name, output_path in SCENARIO_OUTPUTS.items():
        scenario = scenarios[scenario_name]
        weights = scenario["weights"]
        scenario_rows: list[dict[str, object]] = []
        for row in component_rows:
            score, available_weight, contributions, missing = compute_scenario_score(row, weights)
            scenario_row = {
                "rank": "",
                "hgnc_symbol": row["hgnc_symbol"],
                "ensembl_gene_id": row.get("ensembl_gene_id", ""),
                "uniprot_accession": row.get("uniprot_accession", ""),
                "surfaceome_category": row.get("surfaceome_category", ""),
                "scenario": scenario_name,
                "scenario_score": score,
                "available_weight_sum": available_weight,
                "missing_weighted_components": ";".join(missing),
                "n_missing_mvp_score_components": row.get("n_missing_mvp_score_components", ""),
                "missing_mvp_score_components": row.get("missing_mvp_score_components", ""),
                "Surf_relative_confidence": row.get("Surf_relative_confidence", ""),
                "E_rank_percentile": row.get("E_rank_percentile", ""),
                "N_rank_percentile": row.get("N_rank_percentile", ""),
                "R_rank_percentile_high_worse": row.get("R_rank_percentile_high_worse", ""),
                "P_rank_percentile": row.get("P_rank_percentile", ""),
                "SC_status": row.get("SC_status", ""),
                "SC_rank_percentile": row.get("SC_rank_percentile", ""),
                "T_rank_percentile": row.get("T_rank_percentile", ""),
                "Surf_contribution": contributions.get("Surf"),
                "E_contribution": contributions.get("E"),
                "N_contribution": contributions.get("N"),
                "R_contribution_subtracted": contributions.get("R"),
                "P_contribution": contributions.get("P"),
                "SC_contribution": contributions.get("SC"),
                "T_contribution": contributions.get("T"),
                "E_score": row.get("E_score", ""),
                "N_score": row.get("N_score", ""),
                "R_score": row.get("R_score", ""),
                "P_score": row.get("P_score", ""),
                "T_score": row.get("T_score", ""),
                "tme_contamination_risk": row.get("tme_contamination_risk", ""),
                "accessibility_class": row.get("accessibility_class", ""),
                "isoform_resolution_status": row.get("isoform_resolution_status", ""),
                "hpa_evidence_status": row.get("hpa_evidence_status", ""),
                "discordance_flags": row.get("discordance_flags", ""),
                "max_risk_organ": row.get("max_risk_organ", ""),
                "risk_interpretation": row.get("risk_interpretation", ""),
            }
            scenario_rows.append(scenario_row)
        ranked_rows = rank_rows(scenario_rows, "scenario_score")
        scored_by_scenario[scenario_name] = ranked_rows
        write_tsv(output_path, ranked_rows, RANKING_FIELDNAMES)
    return scored_by_scenario


def geometric_mean_scores(component_rows: list[dict[str, object]], weights: dict[str, float]) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []
    for row in component_rows:
        weighted_logs = []
        weight_sum = 0.0
        for component, raw_weight in weights.items():
            weight = float(raw_weight)
            if weight == 0:
                continue
            value = component_value(row, component)
            if value is None:
                continue
            positive_value = 1.0 - value if component == "R" else value
            positive_value = min(1.0, max(1.0e-6, positive_value))
            weighted_logs.append(abs(weight) * math.log(positive_value))
            weight_sum += abs(weight)
        score = math.exp(sum(weighted_logs) / weight_sum) if weight_sum else None
        scored.append({"hgnc_symbol": row["hgnc_symbol"], "scenario_score": score})
    return rank_rows(scored, "scenario_score")


def veto_rank_scores(component_rows: list[dict[str, object]], balanced_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    balanced_score_by_symbol = {row["hgnc_symbol"]: row["scenario_score"] for row in balanced_rows}
    scored: list[dict[str, object]] = []
    for row in component_rows:
        values: list[float] = []
        for component in MVP_COMPONENTS:
            value = component_value(row, component)
            if value is None:
                continue
            values.append(1.0 - value if component == "R" else value)
        vetoed = any(value < 0.20 for value in values)
        scored.append(
            {
                "hgnc_symbol": row["hgnc_symbol"],
                "scenario_score": balanced_score_by_symbol.get(row["hgnc_symbol"]),
                "vetoed": vetoed,
            }
        )
    ranked = sorted(
        scored,
        key=lambda row: (
            bool(row["vetoed"]),
            -(parse_float(row.get("scenario_score")) if parse_float(row.get("scenario_score")) is not None else -math.inf),
            str(row.get("hgnc_symbol", "")),
        ),
    )
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def rank_map(rows: list[dict[str, object]]) -> dict[str, int]:
    return {str(row["hgnc_symbol"]): int(row["rank"]) for row in rows}


def spearman_between(primary: dict[str, int], other: dict[str, int]) -> float:
    symbols = sorted(set(primary) & set(other))
    if len(symbols) < 2:
        return float("nan")
    x = np.array([primary[symbol] for symbol in symbols], dtype=float)
    y = np.array([other[symbol] for symbol in symbols], dtype=float)
    correlation = np.corrcoef(x, y)[0, 1]
    return float(correlation)


def jaccard_top_k(primary: dict[str, int], other: dict[str, int], k: int) -> float:
    top_primary = {symbol for symbol, rank in primary.items() if rank <= k}
    top_other = {symbol for symbol, rank in other.items() if rank <= k}
    union = top_primary | top_other
    if not union:
        return float("nan")
    return len(top_primary & top_other) / len(union)


def write_functional_form_sensitivity(
    component_rows: list[dict[str, object]],
    balanced_rows: list[dict[str, object]],
    balanced_weights: dict[str, float],
) -> list[dict[str, object]]:
    primary = rank_map(balanced_rows)
    geometric = rank_map(geometric_mean_scores(component_rows, balanced_weights))
    veto_rows = veto_rank_scores(component_rows, balanced_rows)
    veto = rank_map(veto_rows)
    balanced_top20 = {row["hgnc_symbol"] for row in balanced_rows if int(row["rank"]) <= 20}
    vetoed_top20 = sorted(row["hgnc_symbol"] for row in veto_rows if row["hgnc_symbol"] in balanced_top20 and row["vetoed"])
    rows = [
        {
            "method": "weighted_rank_sum",
            "comparison_basis": "primary_balanced",
            "spearman_vs_weighted_rank_sum": 1.0,
            "top10_jaccard_vs_weighted_rank_sum": 1.0,
            "top20_jaccard_vs_weighted_rank_sum": 1.0,
            "top50_jaccard_vs_weighted_rank_sum": 1.0,
            "n_balanced_top20_vetoed": 0,
            "balanced_top20_vetoed_symbols": "",
            "interpretation": "primary_compensatory_model",
        },
        {
            "method": "geometric_mean_percentile",
            "comparison_basis": "R converted to 1-R for multiplicative positive scale",
            "spearman_vs_weighted_rank_sum": spearman_between(primary, geometric),
            "top10_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, geometric, 10),
            "top20_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, geometric, 20),
            "top50_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, geometric, 50),
            "n_balanced_top20_vetoed": "",
            "balanced_top20_vetoed_symbols": "",
            "interpretation": "less_compensatory_functional_form",
        },
        {
            "method": "weighted_rank_sum_with_veto_p20",
            "comparison_basis": "any available positive component below p20, or R safety below p20, sorted after non-vetoed genes",
            "spearman_vs_weighted_rank_sum": spearman_between(primary, veto),
            "top10_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, veto, 10),
            "top20_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, veto, 20),
            "top50_jaccard_vs_weighted_rank_sum": jaccard_top_k(primary, veto, 50),
            "n_balanced_top20_vetoed": len(vetoed_top20),
            "balanced_top20_vetoed_symbols": ";".join(vetoed_top20),
            "interpretation": "semi_veto_sensitivity_not_final_tiering",
        },
    ]
    write_tsv(FUNCTIONAL_FORM_SENSITIVITY, rows, FUNCTIONAL_FORM_FIELDNAMES)
    return rows


def write_robust_aggregate(scored_by_scenario: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    symbols = sorted({row["hgnc_symbol"] for rows in scored_by_scenario.values() for row in rows})
    scenario_rank_maps = {scenario: rank_map(rows) for scenario, rows in scored_by_scenario.items()}
    scenario_score_maps = {
        scenario: {row["hgnc_symbol"]: parse_float(row.get("scenario_score")) for row in rows}
        for scenario, rows in scored_by_scenario.items()
    }
    aggregate_rows: list[dict[str, object]] = []
    for symbol in symbols:
        ranks = [scenario_rank_maps[scenario][symbol] for scenario in SCENARIO_OUTPUTS]
        scores = [scenario_score_maps[scenario][symbol] for scenario in SCENARIO_OUTPUTS]
        non_missing_scores = [score for score in scores if score is not None]
        aggregate_rows.append(
            {
                "robust_aggregate_rank": "",
                "hgnc_symbol": symbol,
                "aggregation_method": "borda_mean_rank_across_preregistered_mvp_scenarios",
                "mean_scenario_rank": float(np.mean(ranks)),
                "median_scenario_rank": float(np.median(ranks)),
                "rank_spread": max(ranks) - min(ranks),
                "scenario_top20_count": sum(rank <= 20 for rank in ranks),
                "scenario_top50_count": sum(rank <= 50 for rank in ranks),
                "balanced_rank": scenario_rank_maps["balanced"][symbol],
                "safety_first_rank": scenario_rank_maps["safety_first"][symbol],
                "adc_focused_rank": scenario_rank_maps["adc_focused"][symbol],
                "novelty_rank": scenario_rank_maps["novelty_focused"][symbol],
                "protein_first_rank": scenario_rank_maps["protein_first"][symbol],
                "mean_scenario_score": float(np.mean(non_missing_scores)) if non_missing_scores else None,
                "ranking_status": RANKING_STATUS,
            }
        )
    aggregate_rows = sorted(
        aggregate_rows,
        key=lambda row: (float(row["mean_scenario_rank"]), int(row["balanced_rank"]), str(row["hgnc_symbol"])),
    )
    for index, row in enumerate(aggregate_rows, start=1):
        row["robust_aggregate_rank"] = index
    write_tsv(ROBUST_AGGREGATE, aggregate_rows, ROBUST_FIELDNAMES)
    return aggregate_rows


def build_component_rows() -> list[dict[str, object]]:
    universe = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    universe = sorted(universe, key=lambda row: row["hgnc_symbol"])
    tumor_by_symbol = table_by_symbol(TUMOR_EXPRESSION)
    selectivity_by_symbol = table_by_symbol(SELECTIVITY_SCORES)
    risk_by_symbol = table_by_symbol(OFF_TUMOR_RISK)
    protein_by_symbol = table_by_symbol(PROTEIN_EVIDENCE)
    sc_by_symbol = table_by_symbol(SINGLE_CELL_SPECIFICITY)
    topology_by_symbol = table_by_symbol(TOPOLOGY_ISOFORMS)
    risk_percentiles = rank_percentiles(
        [{"hgnc_symbol": symbol, "value": row.get("R_score", "")} for symbol, row in risk_by_symbol.items()],
        "value",
    )

    component_rows: list[dict[str, object]] = []
    for surface_row in universe:
        symbol = surface_row["hgnc_symbol"]
        tumor = tumor_by_symbol.get(symbol, {})
        selectivity = selectivity_by_symbol.get(symbol, {})
        risk = risk_by_symbol.get(symbol, {})
        protein = protein_by_symbol.get(symbol, {})
        sc = sc_by_symbol.get(symbol, {})
        topology = topology_by_symbol.get(symbol, {})
        row: dict[str, object] = {
            "hgnc_symbol": symbol,
            "ensembl_gene_id": surface_row.get("ensembl_gene_id", ""),
            "uniprot_accession": surface_row.get("uniprot_accession", ""),
            "protein_name": surface_row.get("protein_name", topology.get("protein_name", "")),
            "surfaceome_category": surface_row.get("surfaceome_category", ""),
            "Surf_raw_score": surface_row.get("surfaceome_confidence_score", ""),
            "Surf_relative_confidence": surfaceome_relative_confidence(surface_row.get("surfaceome_confidence_score", "")),
            "Surf_scaling_method": "theoretical_minmax_5_10_after_fase4_gpi",
            "E_score": tumor.get("E_score", ""),
            "E_rank_percentile": tumor.get("E_rank_percentile", ""),
            "E_data_status": tumor.get("expression_data_status", "missing_tumor_expression_row"),
            "N_score": selectivity.get("N_score", ""),
            "N_rank_percentile": selectivity.get("N_rank_percentile", ""),
            "N_interpretation": selectivity.get("selectivity_interpretation", ""),
            "R_score": risk.get("R_score", ""),
            "R_rank_percentile_high_worse": risk_percentiles.get(symbol),
            "R_score_direction": "higher_worse_subtracted",
            "R_max": risk.get("R_max", ""),
            "R_max_plus_breadth": risk.get("R_max_plus_breadth", ""),
            "R_sum_capped": risk.get("R_sum_capped", ""),
            "max_risk_organ": risk.get("max_risk_organ", ""),
            "risk_interpretation": risk.get("risk_interpretation", ""),
            "P_score": protein.get("P_score", ""),
            "P_rank_percentile": protein.get("P_rank_percentile", ""),
            "hpa_evidence_status": protein.get("hpa_evidence_status", "missing_protein_row"),
            "discordance_flags": protein.get("discordance_flags", ""),
            "SC_status": sc.get("SC_status", "not_available"),
            "SC_score": sc.get("SC_score", ""),
            "SC_rank_percentile": sc.get("SC_rank_percentile", ""),
            "SC_component_status": "not_available_not_counted_in_mvp_missingness",
            "tme_contamination_risk": sc.get("tme_contamination_risk", ""),
            "max_tme_module": sc.get("max_tme_module", ""),
            "max_tme_spearman_rho": sc.get("max_tme_spearman_rho", ""),
            "max_tme_partial_spearman_rho": sc.get("max_tme_partial_spearman_rho", ""),
            "T_score": topology.get("T_score", ""),
            "T_rank_percentile": topology.get("T_rank_percentile", ""),
            "accessibility_class": topology.get("accessibility_class", ""),
            "tm_helix_count": topology.get("tm_helix_count", ""),
            "largest_extracellular_loop_aa": topology.get("largest_extracellular_loop_aa", ""),
            "gpi_anchor_present": topology.get("gpi_anchor_present", ""),
            "isoform_resolution_status": topology.get("isoform_resolution_status", ""),
        }
        missing = [component for component in MVP_COMPONENTS if component_value(row, component) is None]
        row["missing_mvp_score_components"] = ";".join(missing)
        row["n_missing_mvp_score_components"] = len(missing)
        row["n_available_mvp_score_components"] = len(MVP_COMPONENTS) - len(missing)
        row["score_data_status"] = "complete_mvp_components" if not missing else "exclude_and_renormalize"
        component_rows.append(row)
    write_tsv(COMPONENT_TABLE, component_rows, COMPONENT_FIELDNAMES)
    return component_rows


def write_tiering_annotations(
    component_rows: list[dict[str, object]],
    balanced_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    balanced_by_symbol = {row["hgnc_symbol"]: row for row in balanced_rows}
    annotation_rows: list[dict[str, object]] = []
    for row in component_rows:
        balanced = balanced_by_symbol[row["hgnc_symbol"]]
        missing_n = int(row["n_missing_mvp_score_components"])
        if missing_n <= 1:
            missing_flag = "eligible_for_tier1A_missingness_only_not_assignment"
        elif missing_n == 2:
            missing_flag = "not_tier1A_missingness_only"
        else:
            missing_flag = "tier2_watchlist_missingness_only"
        manual_flags = []
        if row.get("SC_status") == "not_available":
            manual_flags.append("SC_not_available")
        if row.get("P_score", "") == "":
            manual_flags.append("protein_evidence_missing")
        if "isoform_unresolved" in str(row.get("isoform_resolution_status", "")):
            manual_flags.append("isoform_unresolved")
        if str(row.get("tme_contamination_risk", "")).startswith("high"):
            manual_flags.append("high_TME_flag")
        if str(row.get("accessibility_class", "")) in {"D", "E"}:
            manual_flags.append("low_or_ambiguous_accessibility")
        annotation_rows.append(
            {
                "hgnc_symbol": row["hgnc_symbol"],
                "balanced_rank": balanced["rank"],
                "balanced_score": balanced["scenario_score"],
                "missing_mvp_score_components": row["missing_mvp_score_components"],
                "n_missing_mvp_score_components": row["n_missing_mvp_score_components"],
                "missing_data_tiering_precheck": missing_flag,
                "manual_curation_required_flags": ";".join(manual_flags) if manual_flags else "none",
                "SC_status": row.get("SC_status", ""),
                "tme_contamination_risk": row.get("tme_contamination_risk", ""),
                "accessibility_class": row.get("accessibility_class", ""),
                "isoform_resolution_status": row.get("isoform_resolution_status", ""),
                "hpa_evidence_status": row.get("hpa_evidence_status", ""),
                "discordance_flags": row.get("discordance_flags", ""),
                "max_risk_organ": row.get("max_risk_organ", ""),
                "risk_interpretation": row.get("risk_interpretation", ""),
                "annotation_status": "pre_tiering_annotation_not_final_tier",
            }
        )
    annotation_rows = sorted(annotation_rows, key=lambda row: int(row["balanced_rank"]))
    write_tsv(TIERING_ANNOTATIONS, annotation_rows, TIERING_FIELDNAMES)
    return annotation_rows


def write_control_recovery(
    component_rows: list[dict[str, object]],
    balanced_rows: list[dict[str, object]],
    controls_config: dict[str, object],
) -> list[dict[str, object]]:
    component_by_symbol = {row["hgnc_symbol"]: row for row in component_rows}
    balanced_by_symbol = {row["hgnc_symbol"]: row for row in balanced_rows}
    groups = [
        ("positive_control", controls_config.get("positive_controls", [])),
        ("secondary_benchmark", controls_config.get("secondary_benchmark_targets", [])),
        ("negative_control", controls_config.get("negative_controls_intracellular_or_secreted", [])),
        ("tme_or_off_tumor_penalty_control", controls_config.get("tme_or_off_tumor_penalty_controls", [])),
    ]
    rows: list[dict[str, object]] = []
    for control_set, entries in groups:
        for entry in entries:
            symbol = entry["gene"]
            balanced = balanced_by_symbol.get(symbol)
            component = component_by_symbol.get(symbol, {})
            if balanced:
                rank = int(balanced["rank"])
                presence = "ranked_in_core_probable_universe"
            else:
                rank = ""
                presence = "not_in_core_probable_universe"
            rows.append(
                {
                    "control_set": control_set,
                    "hgnc_symbol": symbol,
                    "alias": entry.get("alias", ""),
                    "expected": entry.get("expected", ""),
                    "balanced_rank": rank,
                    "in_top50_balanced": bool(rank != "" and rank <= 50),
                    "in_top100_balanced": bool(rank != "" and rank <= 100),
                    "presence_status": presence,
                    "balanced_score": balanced.get("scenario_score", "") if balanced else "",
                    "missing_mvp_score_components": component.get("missing_mvp_score_components", ""),
                    "tme_contamination_risk": component.get("tme_contamination_risk", ""),
                    "accessibility_class": component.get("accessibility_class", ""),
                    "isoform_resolution_status": component.get("isoform_resolution_status", ""),
                    "risk_interpretation": component.get("risk_interpretation", ""),
                    "control_interpretation": "diagnostic_only_no_weight_tuning",
                }
            )
    write_tsv(CONTROL_RECOVERY, rows, CONTROL_FIELDNAMES)
    return rows


def write_post_scoring_sanity(
    balanced_rows: list[dict[str, object]],
    control_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    top20 = balanced_rows[:20]
    top100 = balanced_rows[:100]
    positive_top50 = [
        row["hgnc_symbol"]
        for row in control_rows
        if row["control_set"] == "positive_control" and (row["in_top50_balanced"] is True or row["in_top50_balanced"] == "true")
    ]
    negative_top100 = [
        row["hgnc_symbol"]
        for row in control_rows
        if row["control_set"] == "negative_control" and (row["in_top100_balanced"] is True or row["in_top100_balanced"] == "true")
    ]
    tme_controls_top100 = [
        row["hgnc_symbol"]
        for row in control_rows
        if row["control_set"] == "tme_or_off_tumor_penalty_control"
        and (row["in_top100_balanced"] is True or row["in_top100_balanced"] == "true")
    ]
    top20_missing_p = [row["hgnc_symbol"] for row in top20 if str(row.get("P_score", "")) == ""]
    top20_three_plus_missing = [
        row["hgnc_symbol"]
        for row in top20
        if int(str(row.get("n_missing_mvp_score_components", "0") or "0")) >= 3
    ]
    positive_controls = {row["hgnc_symbol"] for row in control_rows if row["control_set"] == "positive_control"}
    top10_non_positive = [row["hgnc_symbol"] for row in balanced_rows[:10] if row["hgnc_symbol"] not in positive_controls]
    rows = [
        {
            "check": "positive_controls_top50",
            "criterion": "at_least_5_of_8",
            "observed": f"{len(positive_top50)}/8",
            "status": "diagnostic_required_before_fase14" if len(positive_top50) < 5 else "pass",
            "symbols": ";".join(positive_top50),
            "interpretation": "Do not tune weights; document whether misses are biological/design limitations or technical issues.",
        },
        {
            "check": "negative_controls_top100",
            "criterion": "zero_negative_controls_in_top100",
            "observed": str(len(negative_top100)),
            "status": "pass" if not negative_top100 else "fail_investigate_as_bug_or_universe_issue",
            "symbols": ";".join(negative_top100),
            "interpretation": "Negative controls absent from Core+Probable universe remain expected.",
        },
        {
            "check": "non_obvious_top10_presence",
            "criterion": "at_least_one_top10_not_positive_control",
            "observed": str(len(top10_non_positive)),
            "status": "pass" if top10_non_positive else "diagnostic_required",
            "symbols": ";".join(top10_non_positive[:10]),
            "interpretation": "Top 10 is not composed only of preregistered positive controls.",
        },
        {
            "check": "top20_missing_protein",
            "criterion": "review_any_P_missing_top20",
            "observed": str(len(top20_missing_p)),
            "status": "diagnostic_required_before_fase14" if top20_missing_p else "pass",
            "symbols": ";".join(top20_missing_p),
            "interpretation": "Verify exclude-and-renormalize is not being read as protein support.",
        },
        {
            "check": "top20_three_or_more_missing_components",
            "criterion": "three_or_more_missing_requires_tier2_watchlist",
            "observed": str(len(top20_three_plus_missing)),
            "status": "documented_tiering_restriction_required" if top20_three_plus_missing else "pass",
            "symbols": ";".join(top20_three_plus_missing),
            "interpretation": "These genes can remain in the audit ranking but cannot be Tier 1A/1B without manual justification.",
        },
        {
            "check": "tme_penalty_controls_top100",
            "criterion": "TME controls may rank but cannot be epithelial Tier 1 without evidence",
            "observed": str(len(tme_controls_top100)),
            "status": "documented_tiering_demotion_required" if tme_controls_top100 else "pass",
            "symbols": ";".join(tme_controls_top100),
            "interpretation": "TME flags are not numeric filters in Fase 13; Fase 15 must demote known TME/off-tumor controls for epithelial targeting.",
        },
    ]
    write_tsv(POST_SCORING_SANITY, rows, SANITY_FIELDNAMES)
    return rows


def write_frozen_v2(
    balanced_rows: list[dict[str, object]],
    config_hash: str,
    commit: str,
    dirty: str,
    freeze_date: str,
) -> None:
    frozen_rows = [dict(row) for row in balanced_rows]
    write_tsv(FROZEN_V2, frozen_rows, RANKING_FIELDNAMES)
    ranking_hash = sha256_file(FROZEN_V2)
    write_yaml(
        FROZEN_V2_METADATA,
        {
            "format_version": "release-format-v1",
            "ranking_file": FROZEN_V2.relative_to(REPO_ROOT).as_posix(),
            "ranking_sha256": ranking_hash,
            "row_count": len(frozen_rows),
            "freeze_version": FREEZE_VERSION,
            "freeze_date_utc": freeze_date,
            "ranking_status": RANKING_STATUS,
            "score_config_sha256": config_hash,
            "release_git_commit": "defined_by_containing_clean_git_commit_or_tag",
            "release_git_worktree_status": "clean_at_release_commit_required",
            "generation_git_commit": commit,
            "generation_git_worktree_status": dirty,
            "git_commit_policy": (
                "The release commit hash is intentionally not embedded literally "
                "in this tracked sidecar, because doing so would make the commit "
                "hash self-referential. The clean Git commit or tag that contains "
                "this file is authoritative for the exact release tree."
            ),
            "metadata_policy": (
                "File-level provenance is stored in this sidecar so the ranking "
                "table contains only ranking/scoring fields."
            ),
        },
    )


def write_phase13_note(
    component_rows: list[dict[str, object]],
    scored_by_scenario: dict[str, list[dict[str, object]]],
    aggregate_rows: list[dict[str, object]],
    functional_rows: list[dict[str, object]],
    control_rows: list[dict[str, object]],
    sanity_rows: list[dict[str, object]],
    config_hash: str,
    commit: str,
    dirty: str,
) -> None:
    balanced_rows = scored_by_scenario["balanced"]
    top20 = [row["hgnc_symbol"] for row in balanced_rows[:20]]
    top20_p_missing = [
        row["hgnc_symbol"]
        for row in balanced_rows[:20]
        if str(row.get("P_score", "")) == ""
    ]
    positive_rows = [row for row in control_rows if row["control_set"] == "positive_control"]
    positives_top50 = [
        row["hgnc_symbol"]
        for row in positive_rows
        if row["in_top50_balanced"] == "true" or row["in_top50_balanced"] is True
    ]
    negative_top100 = [
        row["hgnc_symbol"]
        for row in control_rows
        if row["control_set"] == "negative_control" and (row["in_top100_balanced"] == "true" or row["in_top100_balanced"] is True)
    ]
    scenario_top20_sets = {
        scenario: {row["hgnc_symbol"] for row in rows[:20]}
        for scenario, rows in scored_by_scenario.items()
    }
    balanced_top20 = scenario_top20_sets["balanced"]
    overlap_lines = []
    for scenario in ["safety_first", "adc_focused", "novelty_focused", "protein_first"]:
        overlap = len(balanced_top20 & scenario_top20_sets[scenario])
        overlap_lines.append(f"- `{scenario}` top20 overlap with Balanced: {overlap}/20")

    missing_counts: dict[str, int] = {}
    for row in component_rows:
        key = str(row.get("missing_mvp_score_components", ""))
        key = key if key else "none"
        missing_counts[key] = missing_counts.get(key, 0) + 1
    missing_lines = [f"- `{key}`: {count}" for key, count in sorted(missing_counts.items())]

    function_lines = [
        f"- `{row['method']}`: Spearman={format_value(row['spearman_vs_weighted_rank_sum'])}, top20 Jaccard={format_value(row['top20_jaccard_vs_weighted_rank_sum'])}"
        for row in functional_rows
    ]
    control_lines = [
        f"- `{row['hgnc_symbol']}`: rank {row['balanced_rank'] if row['balanced_rank'] != '' else 'not in Core+Probable'}; {row['control_set']}"
        for row in control_rows
        if row["control_set"] in {"positive_control", "tme_or_off_tumor_penalty_control"}
    ]
    sanity_lines = [
        f"- `{row['check']}`: {row['status']} (observed {row['observed']}; `{row['symbols'] if row['symbols'] else 'none'}`)"
        for row in sanity_rows
    ]

    text = f"""# Fase 13 MVP Score Integration

## Status

Fase 13 generated preliminary MVP integrated score version `v2` after the Fase 4 GPI evidence correction, not final biological tiers. The primary score uses six quantitative components: `Surf`, `E`, `N`, `R`, `P`, and `T`. `SC` remains `not_available` from Fase 8 and is not imputed.

Fase 10 structure and Fase 11 functional evidence remain deferred candidate-card layers. Fase 12 clinical/druggability curation is deferred to top preliminary candidates before final tiering. This scope is registered in `docs/limitations_register.md`.

## Inputs

- Candidate universe: {len(component_rows)} Core+Probable genes.
- Scoring config SHA256: `{config_hash}`.
- Git commit at scoring: `{commit}`.
- Worktree status at scoring: `{dirty}`.
- Missing-data policy: `exclude_and_renormalize`.
- Risk direction: `R` is higher-worse and is subtracted from the score.
- `Surf` scaling: `Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`, using the theoretical admitted Fase 4 confidence range `[5,10]` after confirmed UniProt GPI-anchor evidence was added.
- Fase 13 internal percentile ranks use average-rank ties; this prevents HGNC lexicographic order from changing tied `R` values.

## Missing Data

{chr(10).join(missing_lines)}

`SC` is not counted as missing for MVP tiering prechecks because it is outside the six-component strict MVP score.

## Scenario Rule

`Balanced` is the primary preliminary ranking. `Safety-first`, `ADC-focused`, `Novelty-focused`, and `Protein-first` are sensitivity rankings and must not be cherry-picked as alternative final answers.

{chr(10).join(overlap_lines)}

Top 20 `Balanced` symbols:

`{';'.join(top20)}`

## Functional Form Sensitivity

{chr(10).join(function_lines)}

## Sanity Checks

- Positive controls in top 50 Balanced: {len(positives_top50)}/8 (`{';'.join(positives_top50)}`).
- Negative controls in top 100 Balanced: {len(negative_top100)} (`{';'.join(negative_top100) if negative_top100 else 'none'}`).
- Top 20 Balanced with missing `P`: {len(top20_p_missing)} (`{';'.join(top20_p_missing) if top20_p_missing else 'none'}`).

Post-scoring gate table:

{chr(10).join(sanity_lines)}

Control ranks:

{chr(10).join(control_lines)}

These checks are diagnostic only. A control failure triggers investigation, not score-weight tuning.

## Outputs

- `results/tables/component_scores_all_candidates.tsv`
- `results/tables/tiering_annotations_all_candidates.tsv`
- `results/tables/control_recovery_phase13.tsv`
- `results/rankings/ranking_balanced.tsv`
- `results/rankings/ranking_safety_first.tsv`
- `results/rankings/ranking_adc_focused.tsv`
- `results/rankings/ranking_novelty.tsv`
- `results/rankings/ranking_protein_first.tsv`
- `results/rankings/ranking_robust_aggregate.tsv`
- `results/rankings/ranking_v0_frozen.tsv` (archived snapshot materialized from `data/raw/frozen_snapshots/`)
- `results/rankings/ranking_v1_frozen.tsv` (archived snapshot materialized from `data/raw/frozen_snapshots/`)
- `results/rankings/ranking_v2_frozen.tsv`
- `results/rankings/ranking_v2_frozen.metadata.yaml`
- `results/validation/functional_form_sensitivity.tsv`
- `results/validation/phase13_post_scoring_sanity.tsv`

## Interpretation Boundary

This output is the active v2 preliminary integrated score freeze for auditability; `ranking_v0_frozen.tsv` remains archived as the pre-normalization-fix snapshot and `ranking_v1_frozen.tsv` remains archived as the pre-GPI evidence snapshot. It does not assign Tier 1/2/3 labels and does not support final target claims until Fase 14 stability, control recovery, manual false-positive audit, and candidate-card review are complete.
"""
    PHASE13_NOTE.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    scoring_config = load_yaml(SCORING_CONFIG)
    load_yaml(PARAMETERS_CONFIG)
    controls_config = load_yaml(CONTROLS_CONFIG)
    load_yaml(EXCLUSION_CONFIG)
    config_hash = sha256_file(SCORING_CONFIG)
    commit, dirty, freeze_date = frozen_v2_metadata(git_commit(), git_dirty_status())

    materialize_archived_ranking_snapshots()
    component_rows = build_component_rows()
    scored_by_scenario = score_rows(component_rows, scoring_config["scenarios"])
    aggregate_rows = write_robust_aggregate(scored_by_scenario)
    functional_rows = write_functional_form_sensitivity(
        component_rows,
        scored_by_scenario["balanced"],
        scoring_config["scenarios"]["balanced"]["weights"],
    )
    write_frozen_v2(scored_by_scenario["balanced"], config_hash, commit, dirty, freeze_date)
    write_tiering_annotations(component_rows, scored_by_scenario["balanced"])
    control_rows = write_control_recovery(component_rows, scored_by_scenario["balanced"], controls_config)
    sanity_rows = write_post_scoring_sanity(scored_by_scenario["balanced"], control_rows)
    write_phase13_note(
        component_rows,
        scored_by_scenario,
        aggregate_rows,
        functional_rows,
        control_rows,
        sanity_rows,
        config_hash,
        commit,
        dirty,
    )
    return 0


COMPONENT_FIELDNAMES = [
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "protein_name",
    "surfaceome_category",
    "Surf_raw_score",
    "Surf_relative_confidence",
    "Surf_scaling_method",
    "E_score",
    "E_rank_percentile",
    "E_data_status",
    "N_score",
    "N_rank_percentile",
    "N_interpretation",
    "R_score",
    "R_rank_percentile_high_worse",
    "R_score_direction",
    "R_max",
    "R_max_plus_breadth",
    "R_sum_capped",
    "max_risk_organ",
    "risk_interpretation",
    "P_score",
    "P_rank_percentile",
    "hpa_evidence_status",
    "discordance_flags",
    "SC_status",
    "SC_score",
    "SC_rank_percentile",
    "SC_component_status",
    "tme_contamination_risk",
    "max_tme_module",
    "max_tme_spearman_rho",
    "max_tme_partial_spearman_rho",
    "T_score",
    "T_rank_percentile",
    "accessibility_class",
    "tm_helix_count",
    "largest_extracellular_loop_aa",
    "gpi_anchor_present",
    "isoform_resolution_status",
    "missing_mvp_score_components",
    "n_missing_mvp_score_components",
    "n_available_mvp_score_components",
    "score_data_status",
]

RANKING_FIELDNAMES = [
    "rank",
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "surfaceome_category",
    "scenario",
    "scenario_score",
    "available_weight_sum",
    "missing_weighted_components",
    "n_missing_mvp_score_components",
    "missing_mvp_score_components",
    "Surf_relative_confidence",
    "E_rank_percentile",
    "N_rank_percentile",
    "R_rank_percentile_high_worse",
    "P_rank_percentile",
    "SC_status",
    "SC_rank_percentile",
    "T_rank_percentile",
    "Surf_contribution",
    "E_contribution",
    "N_contribution",
    "R_contribution_subtracted",
    "P_contribution",
    "SC_contribution",
    "T_contribution",
    "E_score",
    "N_score",
    "R_score",
    "P_score",
    "T_score",
    "tme_contamination_risk",
    "accessibility_class",
    "isoform_resolution_status",
    "hpa_evidence_status",
    "discordance_flags",
    "max_risk_organ",
    "risk_interpretation",
]

ROBUST_FIELDNAMES = [
    "robust_aggregate_rank",
    "hgnc_symbol",
    "aggregation_method",
    "mean_scenario_rank",
    "median_scenario_rank",
    "rank_spread",
    "scenario_top20_count",
    "scenario_top50_count",
    "balanced_rank",
    "safety_first_rank",
    "adc_focused_rank",
    "novelty_rank",
    "protein_first_rank",
    "mean_scenario_score",
    "ranking_status",
]

FUNCTIONAL_FORM_FIELDNAMES = [
    "method",
    "comparison_basis",
    "spearman_vs_weighted_rank_sum",
    "top10_jaccard_vs_weighted_rank_sum",
    "top20_jaccard_vs_weighted_rank_sum",
    "top50_jaccard_vs_weighted_rank_sum",
    "n_balanced_top20_vetoed",
    "balanced_top20_vetoed_symbols",
    "interpretation",
]

TIERING_FIELDNAMES = [
    "hgnc_symbol",
    "balanced_rank",
    "balanced_score",
    "missing_mvp_score_components",
    "n_missing_mvp_score_components",
    "missing_data_tiering_precheck",
    "manual_curation_required_flags",
    "SC_status",
    "tme_contamination_risk",
    "accessibility_class",
    "isoform_resolution_status",
    "hpa_evidence_status",
    "discordance_flags",
    "max_risk_organ",
    "risk_interpretation",
    "annotation_status",
]

CONTROL_FIELDNAMES = [
    "control_set",
    "hgnc_symbol",
    "alias",
    "expected",
    "balanced_rank",
    "in_top50_balanced",
    "in_top100_balanced",
    "presence_status",
    "balanced_score",
    "missing_mvp_score_components",
    "tme_contamination_risk",
    "accessibility_class",
    "isoform_resolution_status",
    "risk_interpretation",
    "control_interpretation",
]

SANITY_FIELDNAMES = [
    "check",
    "criterion",
    "observed",
    "status",
    "symbols",
    "interpretation",
]


if __name__ == "__main__":
    raise SystemExit(main())
