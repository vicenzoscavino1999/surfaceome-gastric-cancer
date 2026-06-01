"""Build the pre-Fase 14 audit without running stability perturbations."""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
TABLES_DIR = REPO_ROOT / "results" / "tables"

V1_RANKING = REPO_ROOT / "results" / "rankings" / "ranking_v1_frozen.tsv"
V2_RANKING = REPO_ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
V2_RANKING_METADATA = REPO_ROOT / "results" / "rankings" / "ranking_v2_frozen.metadata.yaml"
V0_RANKING = REPO_ROOT / "results" / "rankings" / "ranking_v0_frozen.tsv"
SURFACEOME = REPO_ROOT / "data" / "processed" / "surfaceome_universe.tsv"
COMPONENTS = REPO_ROOT / "results" / "tables" / "component_scores_all_candidates.tsv"
PHASE13_HASHES = REPO_ROOT / "results" / "tables" / "fase13_diagnostic_snapshot_hashes.tsv"
SCORING_CONFIG = REPO_ROOT / "config" / "scoring_scenarios.yaml"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"

NON_GPI_COMMON_SPEARMAN_THRESHOLD = 0.85
PERTURBATION_SPEARMAN_THRESHOLD = 0.90
TOP20_RETENTION_THRESHOLD = 0.80
WEIGHT_PERTURBATIONS = ["plus_minus_10_percent", "plus_minus_20_percent"]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


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
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def by_symbol(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in rows}


def average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for original_index, _ in ordered[start:end]:
            ranks[original_index] = average_rank
        start = end
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    denom_x = math.sqrt(sum(x * x for x in dx))
    denom_y = math.sqrt(sum(y * y for y in dy))
    if denom_x == 0 or denom_y == 0:
        return float("nan")
    return sum(x * y for x, y in zip(dx, dy)) / (denom_x * denom_y)


def spearman(xs: list[float], ys: list[float]) -> float:
    return pearson(average_ranks(xs), average_ranks(ys))


def favorable_count(row: dict[str, str]) -> tuple[int, str]:
    thresholds = {
        "E": ("E_rank_percentile", 0.70, "high"),
        "N": ("N_rank_percentile", 0.70, "high"),
        "P": ("P_rank_percentile", 0.70, "high"),
        "T": ("T_rank_percentile", 0.70, "high"),
        "R": ("R_rank_percentile_high_worse", 0.65, "low_or_moderate"),
    }
    labels: list[str] = []
    count = 0
    for label, (column, threshold, direction) in thresholds.items():
        value = parse_float(row.get(column, ""))
        if value is None:
            continue
        if direction == "high" and value >= threshold:
            count += 1
            labels.append(label)
        elif direction == "low_or_moderate" and value <= threshold:
            count += 1
            labels.append(label)
    return count, ";".join(labels)


def build_top50_audit(
    v1_rows: list[dict[str, str]],
    v2_rows: list[dict[str, str]],
    components: dict[str, dict[str, str]],
    surfaceome: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    v1_top50 = {row["hgnc_symbol"] for row in v1_rows if int(row["rank"]) <= 50}
    rows: list[dict[str, object]] = []
    new_rows: list[dict[str, object]] = []
    suspicious_new = 0
    plausible_new = 0
    for row in [r for r in v2_rows if int(r["rank"]) <= 50]:
        symbol = row["hgnc_symbol"]
        component = components.get(symbol, {})
        surface = surfaceome.get(symbol, {})
        is_new = symbol not in v1_top50
        support_n, support_labels = favorable_count(row)
        is_gpi = surface.get("uniprot_gpi_anchor", "").lower() == "true"
        suspicious = is_new and is_gpi and support_n < 3
        classification = (
            "new_plausible_multi_component_support"
            if is_new and not suspicious
            else "new_suspicious_surf_dominant"
            if suspicious
            else "retained_v1_top50"
        )
        audit_row = {
            "hgnc_symbol": symbol,
            "rank_v2": int(row["rank"]),
            "rank_v1": next((int(v1_row["rank"]) for v1_row in v1_rows if v1_row["hgnc_symbol"] == symbol), ""),
            "new_in_v2_top50_vs_v1": is_new,
            "scenario_score_v2": row.get("scenario_score", ""),
            "Surf_raw_score_v2": component.get("Surf_raw_score", ""),
            "Surf_relative_confidence_v2": row.get("Surf_relative_confidence", ""),
            "uniprot_gpi_anchor": is_gpi,
            "E_rank_percentile_v2": row.get("E_rank_percentile", ""),
            "N_rank_percentile_v2": row.get("N_rank_percentile", ""),
            "R_rank_percentile_high_worse_v2": row.get("R_rank_percentile_high_worse", ""),
            "P_rank_percentile_v2": row.get("P_rank_percentile", ""),
            "T_rank_percentile_v2": row.get("T_rank_percentile", ""),
            "non_surf_support_count": support_n,
            "non_surf_support_labels": support_labels,
            "missing_mvp_score_components": row.get("missing_mvp_score_components", ""),
            "surface_support_sources": surface.get("surface_support_sources", ""),
            "preflight_classification": classification,
        }
        rows.append(audit_row)
        if is_new:
            new_rows.append(audit_row)
            if suspicious:
                suspicious_new += 1
            else:
                plausible_new += 1
    summary = {
        "v2_top50_n": 50,
        "new_v2_top50_vs_v1_n": len(new_rows),
        "new_v2_top50_gpi_n": sum(1 for row in new_rows if row["uniprot_gpi_anchor"] is True),
        "new_v2_top50_plausible_n": plausible_new,
        "new_v2_top50_suspicious_n": suspicious_new,
        "top50_contamination_gate": "pass" if suspicious_new == 0 else "fail",
    }
    return rows, summary


def build_snapshot_audit() -> tuple[list[dict[str, object]], dict[str, object]]:
    expected_hashes = {row["path"]: row["sha256"] for row in read_tsv(PHASE13_HASHES)} if PHASE13_HASHES.exists() else {}
    rows: list[dict[str, object]] = []
    for path, role, expected_rows, expected_freeze in [
        (V0_RANKING, "pre_normalization_fix_snapshot", 2650, "v0"),
        (V1_RANKING, "post_normalization_fix_pre_gpi_snapshot", 2650, "v1"),
        (V2_RANKING, "active_post_gpi_snapshot", 2704, "v2"),
    ]:
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        ranking_rows = read_tsv(path)
        if path == V2_RANKING:
            metadata = read_yaml(V2_RANKING_METADATA) if V2_RANKING_METADATA.exists() else {}
            freeze_versions = str(metadata.get("freeze_version", ""))
        else:
            freeze_versions = ";".join(sorted({row.get("freeze_version", "") for row in ranking_rows}))
        actual_hash = sha256_file(path)
        expected_hash = expected_hashes.get(rel_path, "")
        rows.append(
            {
                "path": rel_path,
                "role": role,
                "exists": path.exists(),
                "row_count": len(ranking_rows),
                "expected_row_count": expected_rows,
                "freeze_versions": freeze_versions,
                "expected_freeze_version": expected_freeze,
                "sha256": actual_hash,
                "sha256_matches_phase13_snapshot": actual_hash == expected_hash,
                "status": "pass"
                if len(ranking_rows) == expected_rows and freeze_versions == expected_freeze and actual_hash == expected_hash
                else "review_required",
            }
        )
    for path, role in [
        (V2_RANKING_METADATA, "active_post_gpi_snapshot_metadata"),
        (SCORING_CONFIG, "scoring_config"),
        (PARAMETERS_CONFIG, "parameters_config"),
    ]:
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        actual_hash = sha256_file(path)
        expected_hash = expected_hashes.get(rel_path, "")
        rows.append(
            {
                "path": rel_path,
                "role": role,
                "exists": path.exists(),
                "row_count": "",
                "expected_row_count": "",
                "freeze_versions": "",
                "expected_freeze_version": "",
                "sha256": actual_hash,
                "sha256_matches_phase13_snapshot": actual_hash == expected_hash,
                "status": "pass" if actual_hash == expected_hash else "review_required",
            }
        )
    summary = {
        "snapshot_integrity_gate": "pass" if all(row["status"] == "pass" for row in rows) else "fail",
        "snapshot_rows": len(rows),
    }
    return rows, summary


def build_universe_stability(
    v1_rows: list[dict[str, str]],
    v2_rows: list[dict[str, str]],
    surfaceome: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    v1 = by_symbol(v1_rows)
    v2 = by_symbol(v2_rows)
    common_symbols = sorted(set(v1) & set(v2))
    groups = {
        "common_non_gpi": [symbol for symbol in common_symbols if surfaceome.get(symbol, {}).get("uniprot_gpi_anchor", "").lower() != "true"],
        "common_gpi": [symbol for symbol in common_symbols if surfaceome.get(symbol, {}).get("uniprot_gpi_anchor", "").lower() == "true"],
        "common_all": common_symbols,
    }
    rows: list[dict[str, object]] = []
    for group, symbols in groups.items():
        rank_v1 = [float(v1[symbol]["rank"]) for symbol in symbols]
        rank_v2 = [float(v2[symbol]["rank"]) for symbol in symbols]
        score_v1 = [float(v1[symbol]["scenario_score"]) for symbol in symbols]
        score_v2 = [float(v2[symbol]["scenario_score"]) for symbol in symbols]
        rank_delta = [abs(int(v2[symbol]["rank"]) - int(v1[symbol]["rank"])) for symbol in symbols]
        median_delta = sorted(rank_delta)[len(rank_delta) // 2] if rank_delta else ""
        top50_v1 = {symbol for symbol in symbols if int(v1[symbol]["rank"]) <= 50}
        top50_v2 = {symbol for symbol in symbols if int(v2[symbol]["rank"]) <= 50}
        top100_v1 = {symbol for symbol in symbols if int(v1[symbol]["rank"]) <= 100}
        top100_v2 = {symbol for symbol in symbols if int(v2[symbol]["rank"]) <= 100}
        row = {
            "comparison_group": group,
            "n_common_genes": len(symbols),
            "rank_spearman_v1_v2": spearman(rank_v1, rank_v2),
            "score_spearman_v1_v2": spearman(score_v1, score_v2),
            "median_abs_rank_delta": median_delta,
            "max_abs_rank_delta": max(rank_delta) if rank_delta else "",
            "top50_v1_n": len(top50_v1),
            "top50_v2_n": len(top50_v2),
            "top50_retention_fraction": (len(top50_v1 & top50_v2) / len(top50_v1)) if top50_v1 else "",
            "top100_retention_fraction": (len(top100_v1 & top100_v2) / len(top100_v1)) if top100_v1 else "",
            "a_priori_spearman_threshold": NON_GPI_COMMON_SPEARMAN_THRESHOLD if group == "common_non_gpi" else "descriptive_only",
            "threshold_status": "",
        }
        if group == "common_non_gpi":
            row["threshold_status"] = (
                "pass" if parse_float(row["rank_spearman_v1_v2"]) is not None and row["rank_spearman_v1_v2"] >= NON_GPI_COMMON_SPEARMAN_THRESHOLD else "fail"
            )
        else:
            row["threshold_status"] = "descriptive_not_gated"
        rows.append(row)
    non_gpi = next(row for row in rows if row["comparison_group"] == "common_non_gpi")
    summary = {
        "non_gpi_common_spearman": non_gpi["rank_spearman_v1_v2"],
        "universe_evidence_rule_stability_gate": non_gpi["threshold_status"],
    }
    return rows, summary


def main() -> int:
    v1_rows = read_tsv(V1_RANKING)
    v2_rows = read_tsv(V2_RANKING)
    components = by_symbol(read_tsv(COMPONENTS))
    surfaceome = by_symbol(read_tsv(SURFACEOME))

    top50_rows, top50_summary = build_top50_audit(v1_rows, v2_rows, components, surfaceome)
    snapshot_rows, snapshot_summary = build_snapshot_audit()
    stability_rows, stability_summary = build_universe_stability(v1_rows, v2_rows, surfaceome)

    write_tsv(
        TABLES_DIR / "fase14_preflight_top50_v1_v2_audit.tsv",
        top50_rows,
        [
            "hgnc_symbol",
            "rank_v2",
            "rank_v1",
            "new_in_v2_top50_vs_v1",
            "scenario_score_v2",
            "Surf_raw_score_v2",
            "Surf_relative_confidence_v2",
            "uniprot_gpi_anchor",
            "E_rank_percentile_v2",
            "N_rank_percentile_v2",
            "R_rank_percentile_high_worse_v2",
            "P_rank_percentile_v2",
            "T_rank_percentile_v2",
            "non_surf_support_count",
            "non_surf_support_labels",
            "missing_mvp_score_components",
            "surface_support_sources",
            "preflight_classification",
        ],
    )
    write_tsv(
        TABLES_DIR / "fase14_preflight_snapshot_integrity.tsv",
        snapshot_rows,
        [
            "path",
            "role",
            "exists",
            "row_count",
            "expected_row_count",
            "freeze_versions",
            "expected_freeze_version",
            "sha256",
            "sha256_matches_phase13_snapshot",
            "status",
        ],
    )
    write_tsv(
        TABLES_DIR / "fase14_preflight_universe_stability.tsv",
        stability_rows,
        [
            "comparison_group",
            "n_common_genes",
            "rank_spearman_v1_v2",
            "score_spearman_v1_v2",
            "median_abs_rank_delta",
            "max_abs_rank_delta",
            "top50_v1_n",
            "top50_v2_n",
            "top50_retention_fraction",
            "top100_retention_fraction",
            "a_priori_spearman_threshold",
            "threshold_status",
        ],
    )

    new_top50 = [
        row["hgnc_symbol"]
        for row in top50_rows
        if row["new_in_v2_top50_vs_v1"] is True
    ]
    suspicious = [
        row["hgnc_symbol"]
        for row in top50_rows
        if row["preflight_classification"] == "new_suspicious_surf_dominant"
    ]
    non_gpi_stability = next(row for row in stability_rows if row["comparison_group"] == "common_non_gpi")
    gpi_stability = next(row for row in stability_rows if row["comparison_group"] == "common_gpi")

    doc = f"""# Fase 14 Preflight

Date: 2026-05-31

This preflight is executed before Fase 14 stability analyses. It does not run perturbation, leave-one-layer-out, missing-data sensitivity, or final tiering. Its outputs are not final biological tiers.

## A Priori Fase 14 Thresholds

These thresholds are fixed before running Fase 14:

- Weight perturbations: `{';'.join(WEIGHT_PERTURBATIONS)}` around the active v2 Balanced weights.
- Perturbed-rank global stability: Spearman rank correlation versus `ranking_v2_frozen.tsv` must be `>={PERTURBATION_SPEARMAN_THRESHOLD}` for the main perturbation summaries to be called stable.
- Top-20 retention under perturbation: at least `{TOP20_RETENTION_THRESHOLD:.0%}` of v2 top-20 genes should remain in top 20 under reasonable perturbations.
- Control expectation: recovered controls (`ERBB2`, `EPCAM`, `MET`, `CEACAM5`) should remain high-priority; biologically demoted controls (`CLDN18`, `FGFR2`, `MSLN`) should not become top-20 under small perturbations.
- Universe/evidence-rule stability: common non-GPI genes between v1 and v2 should have Spearman rank correlation `>={NON_GPI_COMMON_SPEARMAN_THRESHOLD}`. GPI common genes are descriptive only because GPI movement is expected by design.

## Preflight Gates

### 1. Top50 v1/v2 Contamination Audit

- New v2 top50 genes versus v1: {top50_summary['new_v2_top50_vs_v1_n']} (`{';'.join(new_top50)}`)
- New v2 top50 GPI genes: {top50_summary['new_v2_top50_gpi_n']}
- New v2 top50 plausible multi-component entries: {top50_summary['new_v2_top50_plausible_n']}
- New v2 top50 suspicious Surf-dominant entries: {top50_summary['new_v2_top50_suspicious_n']} (`{';'.join(suspicious) if suspicious else 'none'}`)
- Gate: `{top50_summary['top50_contamination_gate']}`

Criterion: a few GPI entrants are acceptable if they have non-Surf support. Any suspicious Surf-dominant new top50 GPI entry blocks Fase 14.

### 2. Snapshot Integrity

- Snapshot rows checked: {snapshot_summary['snapshot_rows']}
- Gate: `{snapshot_summary['snapshot_integrity_gate']}`

Interpretation: v0 is the pre-normalization-fix snapshot, v1 is post-normalization-fix/pre-GPI, and v2 is active post-GPI. The only new methodological decision from v1 to v2 is the Fase 4 GPI evidence correction; changes in E/N/R/P/T percentiles are deterministic consequences of rerunning downstream over the expanded universe.

### 3. Universe/Evidence-Rule Stability

- Common non-GPI genes: {non_gpi_stability['n_common_genes']}
- Common non-GPI rank Spearman v1 vs v2: `{fmt(non_gpi_stability['rank_spearman_v1_v2'])}`
- Common non-GPI top50 retention: `{fmt(non_gpi_stability['top50_retention_fraction'])}`
- Gate: `{non_gpi_stability['threshold_status']}`

GPI common genes are reported separately:

- Common GPI genes: {gpi_stability['n_common_genes']}
- Common GPI rank Spearman v1 vs v2: `{fmt(gpi_stability['rank_spearman_v1_v2'])}`
- Common GPI top50 retention: `{fmt(gpi_stability['top50_retention_fraction']) or 'not_applicable'}`

This is named universe/evidence-rule stability rather than pure composition stability because v1 to v2 changed both universe membership and the Fase 4 GPI evidence rule. The primary gated subset is common non-GPI genes to avoid penalizing intended GPI movement.

## Decision

Fase 14 is allowed to start only if the top50 contamination gate, snapshot integrity gate, and common non-GPI universe/evidence-rule stability gate are all `pass`.

Current preflight decision: `{'eligible_for_fase14' if top50_summary['top50_contamination_gate'] == 'pass' and snapshot_summary['snapshot_integrity_gate'] == 'pass' and non_gpi_stability['threshold_status'] == 'pass' else 'blocked_before_fase14'}`

## Outputs

- `results/tables/fase14_preflight_top50_v1_v2_audit.tsv`
- `results/tables/fase14_preflight_snapshot_integrity.tsv`
- `results/tables/fase14_preflight_universe_stability.tsv`
"""
    (DOCS_DIR / "fase14_preflight.md").write_text(doc, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
