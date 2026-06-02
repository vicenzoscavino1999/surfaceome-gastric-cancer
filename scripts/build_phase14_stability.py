"""Build Fase 14 rank sensitivity and stability outputs.

This phase audits the frozen Fase 13 v2 preliminary ranking. It does not
create final tiers and it does not retune weights after observing results.
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results"
VALIDATION_DIR = RESULTS_DIR / "validation"
FIGURES_DIR = RESULTS_DIR / "figures"
DOCS_DIR = REPO_ROOT / "docs"

COMPONENT_TABLE = RESULTS_DIR / "tables" / "component_scores_all_candidates.tsv"
RANKING_V2 = RESULTS_DIR / "rankings" / "ranking_v2_frozen.tsv"
TIERING_ANNOTATIONS = RESULTS_DIR / "tables" / "tiering_annotations_all_candidates.tsv"
CONTROL_RECOVERY = RESULTS_DIR / "tables" / "control_recovery_phase13.tsv"
PRE_FLIGHT = DOCS_DIR / "fase14_preflight.md"
FUNCTIONAL_FORM_SENSITIVITY = VALIDATION_DIR / "functional_form_sensitivity.tsv"
ORGAN_PENALTIES = REPO_ROOT / "data" / "processed" / "organ_penalties.tsv"

SCORING_CONFIG = REPO_ROOT / "config" / "scoring_scenarios.yaml"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"
CONTROLS_CONFIG = REPO_ROOT / "config" / "controls.yaml"

RANK_STABILITY = VALIDATION_DIR / "rank_stability.tsv"
LEAVE_ONE_LAYER_OUT = VALIDATION_DIR / "leave_one_layer_out.tsv"
WEIGHT_PERTURBATION_SUMMARY = VALIDATION_DIR / "weight_perturbation_summary.tsv"
RISK_THRESHOLD_SENSITIVITY = VALIDATION_DIR / "risk_threshold_sensitivity.tsv"
RISK_FUNCTIONAL_FORM_SENSITIVITY = VALIDATION_DIR / "risk_functional_form_sensitivity.tsv"
ORGAN_WEIGHT_PERTURBATION = VALIDATION_DIR / "organ_weight_perturbation.tsv"
RANKING_RESOLUTION_POST_SCORING = VALIDATION_DIR / "ranking_resolution_post_scoring.tsv"
RANKING_RESOLUTION_POST_SCORING_SUMMARY = VALIDATION_DIR / "ranking_resolution_post_scoring_summary.tsv"
MISSING_DATA_SENSITIVITY = VALIDATION_DIR / "missing_data_sensitivity.tsv"
CONTROL_BENCHMARK = VALIDATION_DIR / "control_benchmark.tsv"
TOP30_FALSE_POSITIVE_AUDIT = VALIDATION_DIR / "top30_false_positive_audit.tsv"
PHASE14_NOTE = DOCS_DIR / "fase14_rank_stability.md"
RANK_STABILITY_HEATMAP = FIGURES_DIR / "rank_stability_heatmap.svg"
BUMCHART_SCENARIOS = FIGURES_DIR / "bumpchart_scenarios.svg"

MVP_COMPONENTS = ["Surf", "E", "N", "R", "P", "T"]
COMPONENT_VALUE_COLUMNS = {
    "Surf": "Surf_relative_confidence",
    "E": "E_rank_percentile",
    "N": "N_rank_percentile",
    "R": "R_rank_percentile_high_worse",
    "P": "P_rank_percentile",
    "T": "T_rank_percentile",
}
COMPONENT_INDEX = {component: index for index, component in enumerate(MVP_COMPONENTS)}
PRIMARY_SCENARIOS = ["balanced", "safety_first", "adc_focused", "novelty_focused", "protein_first"]
WEIGHT_PERTURBATION_WIDTHS = [0.10, 0.20]
N_WEIGHT_PERTURBATIONS_PER_ANCHOR = 25
N_ORGAN_WEIGHT_PERTURBATIONS = 50
PERTURBATION_SPEARMAN_THRESHOLD = 0.90
TOP20_RETENTION_THRESHOLD = 0.80
TIER1_TOP20_PERTURBATION_THRESHOLD = 0.40


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


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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


def spearman_from_maps(primary: dict[str, int], other: dict[str, int]) -> float:
    symbols = sorted(set(primary) & set(other))
    return pearson(
        average_ranks([float(primary[symbol]) for symbol in symbols]),
        average_ranks([float(other[symbol]) for symbol in symbols]),
    )


def rank_percentiles(values: dict[str, float | None]) -> dict[str, float]:
    valid = [(symbol, value) for symbol, value in values.items() if value is not None and math.isfinite(value)]
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


def rank_rows(rows: list[dict[str, object]], score_key: str = "scenario_score") -> list[dict[str, object]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -(parse_float(row.get(score_key)) if parse_float(row.get(score_key)) is not None else -math.inf),
            str(row.get("hgnc_symbol", "")),
        ),
    )
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked


def rank_map(rows: list[dict[str, object]]) -> dict[str, int]:
    return {str(row["hgnc_symbol"]): int(row["rank"]) for row in rows}


def jaccard_top_k(primary: dict[str, int], other: dict[str, int], k: int) -> float:
    top_primary = {symbol for symbol, rank in primary.items() if rank <= k}
    top_other = {symbol for symbol, rank in other.items() if rank <= k}
    union = top_primary | top_other
    if not union:
        return float("nan")
    return len(top_primary & top_other) / len(union)


def top_retention(primary: dict[str, int], other: dict[str, int], k: int) -> float:
    top_primary = {symbol for symbol, rank in primary.items() if rank <= k}
    if not top_primary:
        return float("nan")
    top_other = {symbol for symbol, rank in other.items() if rank <= k}
    return len(top_primary & top_other) / len(top_primary)


def component_value(
    row: dict[str, object],
    component: str,
    overrides: dict[str, dict[str, float]] | None = None,
) -> float | None:
    symbol = str(row["hgnc_symbol"])
    if overrides and component in overrides and symbol in overrides[component]:
        return overrides[component][symbol]
    return parse_float(row.get(COMPONENT_VALUE_COLUMNS[component], ""))


def compute_score(
    row: dict[str, object],
    weights: dict[str, float],
    *,
    omitted: set[str] | None = None,
    overrides: dict[str, dict[str, float]] | None = None,
    impute_values: dict[str, float] | None = None,
) -> tuple[float | None, float, str]:
    omitted = omitted or set()
    numerator = 0.0
    denominator = 0.0
    missing: list[str] = []
    for component in MVP_COMPONENTS:
        if component in omitted:
            continue
        weight = float(weights.get(component, 0.0))
        if weight == 0:
            continue
        value = component_value(row, component, overrides)
        if value is None and impute_values and component in impute_values:
            value = impute_values[component]
        if value is None:
            missing.append(component)
            continue
        signed_weight = -weight if component == "R" else weight
        numerator += signed_weight * value
        denominator += abs(weight)
    if denominator == 0:
        return None, 0.0, ";".join(missing)
    return numerator / denominator, denominator, ";".join(missing)


def build_ranking(
    component_rows: list[dict[str, object]],
    weights: dict[str, float],
    *,
    label: str,
    omitted: set[str] | None = None,
    overrides: dict[str, dict[str, float]] | None = None,
    impute_values: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in component_rows:
        score, available_weight_sum, missing = compute_score(
            row,
            weights,
            omitted=omitted,
            overrides=overrides,
            impute_values=impute_values,
        )
        rows.append(
            {
                "hgnc_symbol": row["hgnc_symbol"],
                "scenario_score": score,
                "available_weight_sum": available_weight_sum,
                "missing_weighted_components": missing,
                "sensitivity_label": label,
            }
        )
    return rank_rows(rows)


def component_matrix(component_rows: list[dict[str, object]]) -> np.ndarray:
    matrix = np.full((len(component_rows), len(MVP_COMPONENTS)), np.nan, dtype=float)
    for row_index, row in enumerate(component_rows):
        for component, column in COMPONENT_VALUE_COLUMNS.items():
            value = parse_float(row.get(column, ""))
            if value is not None:
                matrix[row_index, COMPONENT_INDEX[component]] = value
    return matrix


def weights_array(weights: dict[str, float]) -> np.ndarray:
    return np.array([float(weights.get(component, 0.0)) for component in MVP_COMPONENTS], dtype=float)


def score_array(
    values: np.ndarray,
    weights: np.ndarray,
    *,
    omitted: set[str] | None = None,
    impute: dict[str, float] | None = None,
) -> np.ndarray:
    active = weights != 0
    if omitted:
        for component in omitted:
            active[COMPONENT_INDEX[component]] = False
    working = values.copy()
    if impute:
        for component, value in impute.items():
            column = COMPONENT_INDEX[component]
            if active[column] and math.isfinite(value):
                missing = ~np.isfinite(working[:, column])
                working[missing, column] = value
    signed_weights = weights.copy()
    signed_weights[COMPONENT_INDEX["R"]] *= -1.0
    active_values = working[:, active]
    finite = np.isfinite(active_values)
    active_signed = signed_weights[active]
    active_abs = np.abs(weights[active])
    numerator = np.sum(np.where(finite, active_values * active_signed, 0.0), axis=1)
    denominator = np.sum(np.where(finite, active_abs, 0.0), axis=1)
    scores = np.full(values.shape[0], np.nan, dtype=float)
    np.divide(numerator, denominator, out=scores, where=denominator > 0)
    return scores


def rank_array(scores: np.ndarray, tie_breaker_array: np.ndarray) -> np.ndarray:
    sortable_scores = np.where(np.isfinite(scores), scores, -np.inf)
    order = np.lexsort((tie_breaker_array, -sortable_scores))
    ranks = np.empty(scores.shape[0], dtype=int)
    ranks[order] = np.arange(1, scores.shape[0] + 1)
    return ranks


def rank_dict_from_array(symbols: list[str], ranks: np.ndarray) -> dict[str, int]:
    return {symbol: int(rank) for symbol, rank in zip(symbols, ranks)}


def summarize_rank_array(
    baseline_ranks: np.ndarray,
    ranks: np.ndarray,
    symbols: list[str],
    label: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    baseline = rank_dict_from_array(symbols, baseline_ranks)
    other = rank_dict_from_array(symbols, ranks)
    return summarize_ranking(baseline, other, label, extra)


def pearson_np(xs: np.ndarray, ys: np.ndarray) -> float:
    if xs.size != ys.size or xs.size < 2:
        return float("nan")
    x = xs.astype(float)
    y = ys.astype(float)
    x = x - float(np.mean(x))
    y = y - float(np.mean(y))
    denom = float(np.sqrt(np.sum(x * x)) * np.sqrt(np.sum(y * y)))
    if denom == 0:
        return float("nan")
    return float(np.sum(x * y) / denom)


def summarize_rank_arrays_fast(
    baseline_ranks: np.ndarray,
    ranks: np.ndarray,
    label: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    row = {
        "sensitivity_label": label,
        "spearman_vs_v2": pearson_np(baseline_ranks, ranks),
        "top10_jaccard_vs_v2": jaccard_masks(baseline_ranks <= 10, ranks <= 10),
        "top20_jaccard_vs_v2": jaccard_masks(baseline_ranks <= 20, ranks <= 20),
        "top50_jaccard_vs_v2": jaccard_masks(baseline_ranks <= 50, ranks <= 50),
        "top20_retention_vs_v2": retention_masks(baseline_ranks <= 20, ranks <= 20),
        "top50_retention_vs_v2": retention_masks(baseline_ranks <= 50, ranks <= 50),
    }
    row["spearman_gate"] = "pass" if row["spearman_vs_v2"] >= PERTURBATION_SPEARMAN_THRESHOLD else "review"
    row["top20_retention_gate"] = "pass" if row["top20_retention_vs_v2"] >= TOP20_RETENTION_THRESHOLD else "review"
    if extra:
        row.update(extra)
    return row


def jaccard_masks(primary: np.ndarray, other: np.ndarray) -> float:
    union = np.logical_or(primary, other)
    if not np.any(union):
        return float("nan")
    return float(np.sum(np.logical_and(primary, other)) / np.sum(union))


def retention_masks(primary: np.ndarray, other: np.ndarray) -> float:
    if not np.any(primary):
        return float("nan")
    return float(np.sum(np.logical_and(primary, other)) / np.sum(primary))


def summarize_ranking(
    baseline: dict[str, int],
    other: dict[str, int],
    label: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    row = {
        "sensitivity_label": label,
        "spearman_vs_v2": spearman_from_maps(baseline, other),
        "top10_jaccard_vs_v2": jaccard_top_k(baseline, other, 10),
        "top20_jaccard_vs_v2": jaccard_top_k(baseline, other, 20),
        "top50_jaccard_vs_v2": jaccard_top_k(baseline, other, 50),
        "top20_retention_vs_v2": top_retention(baseline, other, 20),
        "top50_retention_vs_v2": top_retention(baseline, other, 50),
        "spearman_gate": "pass" if spearman_from_maps(baseline, other) >= PERTURBATION_SPEARMAN_THRESHOLD else "review",
        "top20_retention_gate": "pass" if top_retention(baseline, other, 20) >= TOP20_RETENTION_THRESHOLD else "review",
    }
    if extra:
        row.update(extra)
    return row


def quantile(values: list[int | float], q: float) -> float:
    if not values:
        return float("nan")
    return float(np.percentile(np.array(values, dtype=float), q))


def imputation_values(component_rows: list[dict[str, object]], quantile_name: str) -> dict[str, float]:
    q_map = {"p25": 25.0, "p50": 50.0, "p75": 75.0}
    q = q_map[quantile_name]
    output: dict[str, float] = {}
    for component in MVP_COMPONENTS:
        observed = [
            component_value(row, component)
            for row in component_rows
            if component_value(row, component) is not None
        ]
        output[component] = float(np.percentile(np.array(observed, dtype=float), q)) if observed else float("nan")
    return output


def perturbed_weights(base: dict[str, float], width: float, rng: np.random.Generator) -> dict[str, float]:
    weights: dict[str, float] = {}
    for component in MVP_COMPONENTS:
        value = float(base.get(component, 0.0))
        if value == 0:
            weights[component] = 0.0
        else:
            weights[component] = value * float(rng.uniform(1.0 - width, 1.0 + width))
    return weights


def risk_rank_percentiles_from_column(component_rows: list[dict[str, object]], column: str) -> dict[str, float]:
    raw = {str(row["hgnc_symbol"]): parse_float(row.get(column, "")) for row in component_rows}
    return rank_percentiles(raw)


def recompute_risk_from_organ_rows(
    organ_rows: list[dict[str, str]],
    mode: str,
    *,
    organ_factors: dict[str, float] | None = None,
) -> dict[str, float]:
    by_gene: dict[str, list[dict[str, str]]] = {}
    for row in organ_rows:
        by_gene.setdefault(row["hgnc_symbol"], []).append(row)
    output: dict[str, float] = {}
    for symbol, rows in by_gene.items():
        values = [parse_float(row.get("normal_expr_tpm_or_ntpm", "")) for row in rows]
        finite_values = [value for value in values if value is not None]
        if not finite_values:
            output[symbol] = float("nan")
            continue
        if mode == "p60_p80":
            caution_threshold = max(float(np.percentile(finite_values, 60.0)), 1.0)
            critical_threshold = max(float(np.percentile(finite_values, 80.0)), 5.0)
        elif mode == "absolute_tpm_1_5":
            caution_threshold = 1.0
            critical_threshold = 5.0
        else:
            caution_threshold = max(float(np.percentile(finite_values, 50.0)), 1.0)
            critical_threshold = max(float(np.percentile(finite_values, 75.0)), 5.0)
        weighted_values: list[float] = []
        for row in rows:
            expr = parse_float(row.get("normal_expr_tpm_or_ntpm", ""))
            rank_pct = parse_float(row.get("organ_rank_percentile", ""))
            weight = parse_float(row.get("organ_weight", "")) or 0.0
            factor = organ_factors.get(row.get("organ", ""), 1.0) if organ_factors else 1.0
            if expr is None:
                continue
            if expr >= critical_threshold:
                penalty = 1.0
            elif expr >= caution_threshold:
                penalty = 0.5 * (rank_pct if rank_pct is not None else 1.0)
            else:
                penalty = 0.0
            weighted_values.append(penalty * weight * factor)
        output[symbol] = max(weighted_values) if weighted_values else float("nan")
    return output


def write_rank_stability_heatmap(top_symbols: list[str], rank_sources: dict[str, dict[str, int]]) -> None:
    cell_w = 25
    cell_h = 13
    left = 95
    top = 42
    labels = list(rank_sources)
    width = left + len(labels) * cell_w + 24
    height = top + len(top_symbols) * cell_h + 28

    def color(rank: int) -> str:
        if rank <= 10:
            return "#1b9e77"
        if rank <= 20:
            return "#66c2a5"
        if rank <= 50:
            return "#ffd166"
        if rank <= 100:
            return "#f4a261"
        return "#d9d9d9"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;font-size:10px}.small{font-size:8px}</style>',
        '<text x="12" y="20" font-size="14" font-weight="700">Rank stability heatmap</text>',
    ]
    for col, label in enumerate(labels):
        x = left + col * cell_w + 12
        parts.append(f'<text class="small" font-size="8" x="{x}" y="36" text-anchor="middle" transform="rotate(-45 {x} 36)">{label}</text>')
    for row_idx, symbol in enumerate(top_symbols):
        y = top + row_idx * cell_h
        parts.append(f'<text font-size="9" x="8" y="{y + 9.5:.1f}">{symbol}</text>')
        for col, label in enumerate(labels):
            rank = rank_sources[label].get(symbol, 9999)
            x = left + col * cell_w
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 1}" height="{cell_h - 1}" fill="{color(rank)}"/>')
            text = str(rank) if rank <= 999 else ">999"
            parts.append(f'<text class="small" font-size="7" x="{x + cell_w / 2:.1f}" y="{y + 9.5:.1f}" text-anchor="middle">{text}</text>')
    parts.append("</svg>")
    RANK_STABILITY_HEATMAP.write_text("\n".join(parts), encoding="utf-8", newline="\n")


def write_bumpchart_scenarios(scenario_ranks: dict[str, dict[str, int]], baseline_top20: list[str]) -> None:
    scenarios = list(scenario_ranks)
    display_labels = {
        "balanced": "primary",
        "safety_first": "safety",
        "adc_focused": "ADC",
        "novelty_focused": "novelty",
        "protein_first": "protein",
    }
    left = 78
    top = 62
    col_w = 112
    row_h = 9.6
    max_rank = 30
    right_label_x = left + (len(scenarios) - 1) * col_w + 14
    width = right_label_x + 112
    height = top + max_rank * row_h + 36
    palette = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#1f78b4"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;font-size:11px}.small{font-size:9px}</style>',
        '<text x="12" y="20" font-size="14" font-weight="700">Top-20 weighting-sensitivity bumpchart</text>',
    ]
    for col, scenario in enumerate(scenarios):
        x = left + col * col_w
        parts.append(f'<text x="{x}" y="{top - 15}" text-anchor="middle" font-weight="700">{display_labels.get(scenario, scenario)}</text>')
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + max_rank * row_h}" stroke="#cccccc"/>')
        for rank in [1, 10, 20, 30]:
            y = top + (rank - 1) * row_h
            if col == 0:
                parts.append(f'<text class="small" font-size="8" x="{x - 28}" y="{y + 3.2:.1f}">{rank}</text>')
    raw_end_labels: list[tuple[float, str]] = []
    for symbol in baseline_top20:
        end_rank = scenario_ranks[scenarios[-1]].get(symbol, max_rank + 1)
        end_y = top + (min(end_rank, max_rank) - 1) * row_h
        raw_end_labels.append((end_y + 3.2, symbol))
    end_label_y: dict[str, float] = {}
    min_gap = 8.4
    sorted_labels = sorted(raw_end_labels)
    previous = top + 2
    for requested_y, symbol in sorted_labels:
        label_y = max(requested_y, previous + min_gap)
        end_label_y[symbol] = label_y
        previous = label_y
    overflow = previous - (top + (max_rank - 1) * row_h + 8)
    if overflow > 0:
        for _, symbol in sorted_labels:
            end_label_y[symbol] -= overflow
    for idx, symbol in enumerate(baseline_top20):
        points: list[tuple[float, float]] = []
        for col, scenario in enumerate(scenarios):
            rank = scenario_ranks[scenario].get(symbol, max_rank + 1)
            y_rank = min(rank, max_rank)
            points.append((left + col * col_w, top + (y_rank - 1) * row_h))
        color = palette[idx % len(palette)]
        path = " ".join([("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(points)])
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.7" opacity="0.85"/>')
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{color}"/>')
        parts.append(
            f'<line x1="{points[-1][0] + 3:.1f}" y1="{points[-1][1]:.1f}" '
            f'x2="{right_label_x - 3:.1f}" y2="{end_label_y[symbol] - 3:.1f}" '
            f'stroke="{color}" stroke-width="0.6" opacity="0.45"/>'
        )
        parts.append(f'<text class="small" font-size="8" x="{right_label_x:.1f}" y="{end_label_y[symbol]:.1f}">{symbol}</text>')
    parts.append("</svg>")
    BUMCHART_SCENARIOS.write_text("\n".join(parts), encoding="utf-8", newline="\n")


def main() -> int:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    scoring_config = load_yaml(SCORING_CONFIG)
    params = load_yaml(PARAMETERS_CONFIG)
    controls_config = load_yaml(CONTROLS_CONFIG)
    component_rows = [dict(row) for row in read_tsv(COMPONENT_TABLE)]
    baseline_rows = [dict(row) for row in read_tsv(RANKING_V2)]
    baseline = rank_map(baseline_rows)
    baseline_top20 = [row["hgnc_symbol"] for row in baseline_rows if int(row["rank"]) <= 20]
    baseline_top50 = {row["hgnc_symbol"] for row in baseline_rows if int(row["rank"]) <= 50}
    component_by_symbol = by_symbol(component_rows)
    symbols = [row["hgnc_symbol"] for row in component_rows]
    lex_order = {symbol: index for index, symbol in enumerate(sorted(symbols))}
    symbol_tie_array = np.array([lex_order[symbol] for symbol in symbols], dtype=int)
    components = component_matrix(component_rows)
    baseline_rank_array = np.array([baseline[symbol] for symbol in symbols], dtype=int)
    balanced_weights = {
        component: float(scoring_config["scenarios"]["balanced"]["weights"].get(component, 0.0))
        for component in MVP_COMPONENTS
    }
    balanced_weight_array = weights_array(balanced_weights)
    rng = np.random.default_rng(int(params["random"]["weight_perturbation_seed"]))

    scenario_ranks: dict[str, dict[str, int]] = {}
    scenario_summary: list[dict[str, object]] = []
    for scenario in PRIMARY_SCENARIOS:
        weights = {
            component: float(scoring_config["scenarios"][scenario]["weights"].get(component, 0.0))
            for component in MVP_COMPONENTS
        }
        rows = build_ranking(component_rows, weights, label=f"scenario_{scenario}")
        ranks = rank_map(rows)
        scenario_ranks[scenario] = ranks
        scenario_summary.append(summarize_ranking(baseline, ranks, f"scenario_{scenario}", {"analysis_type": "preregistered_scenario"}))

    leave_rows: list[dict[str, object]] = []
    leave_summary: list[dict[str, object]] = []
    leave_rank_maps: dict[str, dict[str, int]] = {}
    for omitted in MVP_COMPONENTS:
        rows = build_ranking(component_rows, balanced_weights, label=f"leave_one_{omitted}", omitted={omitted})
        ranks = rank_map(rows)
        leave_rank_maps[omitted] = ranks
        leave_summary.append(summarize_ranking(baseline, ranks, f"leave_one_{omitted}", {"analysis_type": "leave_one_layer_out", "omitted_layer": omitted}))
        for row in rows:
            symbol = row["hgnc_symbol"]
            leave_rows.append(
                {
                    "omitted_layer": omitted,
                    "hgnc_symbol": symbol,
                    "baseline_rank_v2": baseline[symbol],
                    "leave_one_rank": row["rank"],
                    "rank_delta_vs_v2": int(row["rank"]) - baseline[symbol],
                    "leave_one_score": row["scenario_score"],
                    "available_weight_sum": row["available_weight_sum"],
                    "missing_weighted_components": row["missing_weighted_components"],
                    "analysis_status": "sensitivity_not_final_tiering",
                }
            )
    write_tsv(
        LEAVE_ONE_LAYER_OUT,
        leave_rows,
        [
            "omitted_layer",
            "hgnc_symbol",
            "baseline_rank_v2",
            "leave_one_rank",
            "rank_delta_vs_v2",
            "leave_one_score",
            "available_weight_sum",
            "missing_weighted_components",
            "analysis_status",
        ],
    )

    perturb_rank_lists_all: dict[str, list[int]] = {row["hgnc_symbol"]: [] for row in baseline_rows}
    perturb_rank_lists_balanced: dict[str, list[int]] = {row["hgnc_symbol"]: [] for row in baseline_rows}
    weight_rows: list[dict[str, object]] = []
    perturbation_index = 0
    for anchor in PRIMARY_SCENARIOS:
        anchor_weights = {
            component: float(scoring_config["scenarios"][anchor]["weights"].get(component, 0.0))
            for component in MVP_COMPONENTS
        }
        for width in WEIGHT_PERTURBATION_WIDTHS:
            for replicate in range(1, N_WEIGHT_PERTURBATIONS_PER_ANCHOR + 1):
                perturbation_index += 1
                weights = perturbed_weights(anchor_weights, width, rng)
                scores = score_array(components, weights_array(weights))
                ranks_array = rank_array(scores, symbol_tie_array)
                for symbol, rank in zip(symbols, ranks_array):
                    perturb_rank_lists_all[symbol].append(int(rank))
                    if anchor == "balanced":
                        perturb_rank_lists_balanced[symbol].append(int(rank))
                summary = summarize_rank_arrays_fast(
                    baseline_rank_array,
                    ranks_array,
                    f"{anchor}_pm{int(width * 100)}_{replicate}",
                    {
                        "analysis_type": "weight_perturbation",
                        "anchor_scenario": anchor,
                        "perturbation_width": width,
                        "perturbation_id": perturbation_index,
                    },
                )
                top20_other = {symbol for symbol, rank in zip(symbols, ranks_array) if int(rank) <= 20}
                summary["top20_exits_vs_v2"] = ";".join(sorted(set(baseline_top20) - top20_other))
                summary["top20_entries_vs_v2"] = ";".join(sorted(top20_other - set(baseline_top20)))
                weight_rows.append(summary)
    write_tsv(
        WEIGHT_PERTURBATION_SUMMARY,
        weight_rows,
        [
            "perturbation_id",
            "analysis_type",
            "anchor_scenario",
            "perturbation_width",
            "sensitivity_label",
            "spearman_vs_v2",
            "top10_jaccard_vs_v2",
            "top20_jaccard_vs_v2",
            "top50_jaccard_vs_v2",
            "top20_retention_vs_v2",
            "top50_retention_vs_v2",
            "spearman_gate",
            "top20_retention_gate",
            "top20_exits_vs_v2",
            "top20_entries_vs_v2",
        ],
    )

    risk_form_rows: list[dict[str, object]] = []
    risk_form_rank_maps: dict[str, dict[str, int]] = {}
    for form in ["R_max", "R_max_plus_breadth", "R_sum_capped"]:
        r_percentiles = risk_rank_percentiles_from_column(component_rows, form)
        rows = build_ranking(component_rows, balanced_weights, label=f"risk_form_{form}", overrides={"R": r_percentiles})
        ranks = rank_map(rows)
        risk_form_rank_maps[form] = ranks
        for row in rows:
            symbol = row["hgnc_symbol"]
            risk_form_rows.append(
                {
                    "risk_form": form,
                    "hgnc_symbol": symbol,
                    "baseline_rank_v2": baseline[symbol],
                    "risk_form_rank": row["rank"],
                    "rank_delta_vs_v2": int(row["rank"]) - baseline[symbol],
                    "risk_form_score": row["scenario_score"],
                    "R_rank_percentile_high_worse": r_percentiles.get(symbol),
                    "analysis_status": "risk_form_sensitivity_not_final_tiering",
                }
            )
    write_tsv(
        RISK_FUNCTIONAL_FORM_SENSITIVITY,
        risk_form_rows,
        [
            "risk_form",
            "hgnc_symbol",
            "baseline_rank_v2",
            "risk_form_rank",
            "rank_delta_vs_v2",
            "risk_form_score",
            "R_rank_percentile_high_worse",
            "analysis_status",
        ],
    )

    organ_rows = read_tsv(ORGAN_PENALTIES)
    threshold_rank_maps: dict[str, dict[str, int]] = {}
    threshold_rows: list[dict[str, object]] = []
    for mode in ["p50_p75", "p60_p80", "absolute_tpm_1_5"]:
        r_raw = recompute_risk_from_organ_rows(organ_rows, mode)
        r_percentiles = rank_percentiles(r_raw)
        rows = build_ranking(component_rows, balanced_weights, label=f"risk_threshold_{mode}", overrides={"R": r_percentiles})
        ranks = rank_map(rows)
        threshold_rank_maps[mode] = ranks
        for row in rows:
            symbol = row["hgnc_symbol"]
            threshold_rows.append(
                {
                    "risk_threshold_scenario": mode,
                    "hgnc_symbol": symbol,
                    "baseline_rank_v2": baseline[symbol],
                    "risk_threshold_rank": row["rank"],
                    "rank_delta_vs_v2": int(row["rank"]) - baseline[symbol],
                    "risk_threshold_score": row["scenario_score"],
                    "R_raw_score": r_raw.get(symbol),
                    "R_rank_percentile_high_worse": r_percentiles.get(symbol),
                    "analysis_status": "risk_threshold_sensitivity_not_final_tiering",
                }
            )
    write_tsv(
        RISK_THRESHOLD_SENSITIVITY,
        threshold_rows,
        [
            "risk_threshold_scenario",
            "hgnc_symbol",
            "baseline_rank_v2",
            "risk_threshold_rank",
            "rank_delta_vs_v2",
            "risk_threshold_score",
            "R_raw_score",
            "R_rank_percentile_high_worse",
            "analysis_status",
        ],
    )

    organ_rng = np.random.default_rng(int(params["random"]["perturbation_seed"]))
    organs = sorted({row["organ"] for row in organ_rows})
    organ_weight_rows: list[dict[str, object]] = []
    organ_rank_lists: dict[str, list[int]] = {row["hgnc_symbol"]: [] for row in baseline_rows}
    for perturbation_id in range(1, N_ORGAN_WEIGHT_PERTURBATIONS + 1):
        factors = {organ: float(organ_rng.uniform(0.80, 1.20)) for organ in organs}
        r_raw = recompute_risk_from_organ_rows(organ_rows, "p50_p75", organ_factors=factors)
        r_percentiles = rank_percentiles(r_raw)
        organ_components = components.copy()
        for idx, symbol in enumerate(symbols):
            organ_components[idx, COMPONENT_INDEX["R"]] = r_percentiles.get(symbol, np.nan)
        scores = score_array(organ_components, balanced_weight_array)
        ranks_array = rank_array(scores, symbol_tie_array)
        for symbol, rank in zip(symbols, ranks_array):
            organ_rank_lists[symbol].append(int(rank))
        summary = summarize_rank_arrays_fast(
            baseline_rank_array,
            ranks_array,
            f"organ_weight_pm20_{perturbation_id}",
            {
                "analysis_type": "organ_weight_perturbation",
                "perturbation_id": perturbation_id,
                "organ_weight_range": "uniform_0.80_1.20",
            },
        )
        top20_other = {symbol for symbol, rank in zip(symbols, ranks_array) if int(rank) <= 20}
        summary["top20_exits_vs_v2"] = ";".join(sorted(set(baseline_top20) - top20_other))
        summary["top20_entries_vs_v2"] = ";".join(sorted(top20_other - set(baseline_top20)))
        organ_weight_rows.append(summary)
    write_tsv(
        ORGAN_WEIGHT_PERTURBATION,
        organ_weight_rows,
        [
            "perturbation_id",
            "analysis_type",
            "organ_weight_range",
            "sensitivity_label",
            "spearman_vs_v2",
            "top10_jaccard_vs_v2",
            "top20_jaccard_vs_v2",
            "top50_jaccard_vs_v2",
            "top20_retention_vs_v2",
            "top50_retention_vs_v2",
            "spearman_gate",
            "top20_retention_gate",
            "top20_exits_vs_v2",
            "top20_entries_vs_v2",
        ],
    )

    missing_rank_maps: dict[str, dict[str, int]] = {}
    missing_rows: list[dict[str, object]] = []
    for scenario in ["exclude_and_renormalize", "p25", "p50", "p75"]:
        impute = None if scenario == "exclude_and_renormalize" else imputation_values(component_rows, scenario)
        rows = build_ranking(component_rows, balanced_weights, label=f"missing_{scenario}", impute_values=impute)
        ranks = rank_map(rows)
        missing_rank_maps[scenario] = ranks
        for row in rows:
            symbol = row["hgnc_symbol"]
            missing_rows.append(
                {
                    "missing_data_scenario": scenario,
                    "hgnc_symbol": symbol,
                    "baseline_rank_v2": baseline[symbol],
                    "sensitivity_rank": row["rank"],
                    "rank_delta_vs_v2": int(row["rank"]) - baseline[symbol],
                    "sensitivity_score": row["scenario_score"],
                    "available_weight_sum": row["available_weight_sum"],
                    "missing_weighted_components_after_policy": row["missing_weighted_components"],
                    "analysis_status": "missing_data_sensitivity_not_final_tiering",
                }
            )
    write_tsv(
        MISSING_DATA_SENSITIVITY,
        missing_rows,
        [
            "missing_data_scenario",
            "hgnc_symbol",
            "baseline_rank_v2",
            "sensitivity_rank",
            "rank_delta_vs_v2",
            "sensitivity_score",
            "available_weight_sum",
            "missing_weighted_components_after_policy",
            "analysis_status",
        ],
    )

    resolution_seed = int(params["random"]["rank_resolution_seed"])
    resolution_rng = np.random.default_rng(resolution_seed)
    n_resolution = int(params["ranking_resolution"]["n_simulations"])
    noise_sd = float(params["ranking_resolution"]["component_noise_sd"])
    resolution_rank_lists: dict[str, list[int]] = {row["hgnc_symbol"]: [] for row in baseline_rows}
    for sim in range(n_resolution):
        noise = resolution_rng.normal(0.0, noise_sd, size=components.shape)
        simulated = np.where(np.isfinite(components), np.clip(components + noise, 0.0, 1.0), np.nan)
        scores = score_array(simulated, balanced_weight_array)
        ranks_array = rank_array(scores, symbol_tie_array)
        for symbol, rank in zip(symbols, ranks_array):
            resolution_rank_lists[symbol].append(int(rank))

    resolution_rows: list[dict[str, object]] = []
    for row in baseline_rows:
        symbol = row["hgnc_symbol"]
        ranks = resolution_rank_lists[symbol]
        resolution_rows.append(
            {
                "hgnc_symbol": symbol,
                "baseline_rank_v2": baseline[symbol],
                "mean_rank": float(np.mean(ranks)),
                "sd_rank": float(np.std(ranks, ddof=1)) if len(ranks) > 1 else 0.0,
                "rank_p2_5": quantile(ranks, 2.5),
                "rank_p50": quantile(ranks, 50.0),
                "rank_p97_5": quantile(ranks, 97.5),
                "rank_ci_width": quantile(ranks, 97.5) - quantile(ranks, 2.5),
                "ci_contained_in_top40": quantile(ranks, 97.5) <= 40.0,
                "top20_frequency": sum(rank <= 20 for rank in ranks) / len(ranks),
                "n_simulations": len(ranks),
                "simulation_seed": resolution_seed,
                "component_noise_sd": noise_sd,
            }
        )
    resolution_rows.sort(key=lambda item: (float(item["rank_p50"]), float(item["mean_rank"]), str(item["hgnc_symbol"])))
    resolution_by_symbol = {row["hgnc_symbol"]: row for row in resolution_rows}
    write_tsv(
        RANKING_RESOLUTION_POST_SCORING,
        resolution_rows,
        [
            "hgnc_symbol",
            "baseline_rank_v2",
            "mean_rank",
            "sd_rank",
            "rank_p2_5",
            "rank_p50",
            "rank_p97_5",
            "rank_ci_width",
            "ci_contained_in_top40",
            "top20_frequency",
            "n_simulations",
            "simulation_seed",
            "component_noise_sd",
        ],
    )
    top20_resolution = [row for row in resolution_rows if int(row["baseline_rank_v2"]) <= 20]
    resolution_summary_rows = [
        {
            "metric": "top20_with_ci_contained_in_top40",
            "value": sum(str(row["ci_contained_in_top40"]).lower() == "true" or row["ci_contained_in_top40"] is True for row in top20_resolution),
            "threshold": int(params["ranking_resolution"]["top20_ci_contained_in_top40_min_genes"]),
            "status": "pass"
            if sum(str(row["ci_contained_in_top40"]).lower() == "true" or row["ci_contained_in_top40"] is True for row in top20_resolution)
            >= int(params["ranking_resolution"]["top20_ci_contained_in_top40_min_genes"])
            else "coarse_tiering_recommended",
        },
        {
            "metric": "median_top20_top20_frequency",
            "value": float(np.median([row["top20_frequency"] for row in top20_resolution])) if top20_resolution else float("nan"),
            "threshold": TIER1_TOP20_PERTURBATION_THRESHOLD,
            "status": "descriptive",
        },
        {
            "metric": "n_simulations",
            "value": n_resolution,
            "threshold": "",
            "status": "recorded",
        },
    ]
    write_tsv(RANKING_RESOLUTION_POST_SCORING_SUMMARY, resolution_summary_rows, ["metric", "value", "threshold", "status"])

    rank_stability_rows: list[dict[str, object]] = []
    for row in baseline_rows:
        symbol = row["hgnc_symbol"]
        all_perturb = perturb_rank_lists_all[symbol]
        balanced_perturb = perturb_rank_lists_balanced[symbol]
        leave_values = [rank_map_[symbol] for rank_map_ in leave_rank_maps.values()]
        missing_values = [rank_map_[symbol] for rank_map_ in missing_rank_maps.values()]
        risk_values = [rank_map_[symbol] for rank_map_ in risk_form_rank_maps.values()]
        organ_values = organ_rank_lists[symbol]
        rank_stability_rows.append(
            {
                "hgnc_symbol": symbol,
                "baseline_rank_v2": baseline[symbol],
                "baseline_score_v2": row.get("scenario_score", ""),
                "balanced_weight_perturb_top20_frequency": sum(rank <= 20 for rank in balanced_perturb) / len(balanced_perturb),
                "all_weight_perturb_top20_frequency": sum(rank <= 20 for rank in all_perturb) / len(all_perturb),
                "all_weight_perturb_top50_frequency": sum(rank <= 50 for rank in all_perturb) / len(all_perturb),
                "all_weight_perturb_mean_rank": float(np.mean(all_perturb)),
                "all_weight_perturb_rank_p2_5": quantile(all_perturb, 2.5),
                "all_weight_perturb_rank_p50": quantile(all_perturb, 50.0),
                "all_weight_perturb_rank_p97_5": quantile(all_perturb, 97.5),
                "leave_one_layer_min_rank": min(leave_values),
                "leave_one_layer_max_rank": max(leave_values),
                "leave_one_layer_max_abs_delta": max(abs(rank - baseline[symbol]) for rank in leave_values),
                "missing_data_min_rank": min(missing_values),
                "missing_data_max_rank": max(missing_values),
                "risk_form_min_rank": min(risk_values),
                "risk_form_max_rank": max(risk_values),
                "organ_weight_perturb_top20_frequency": sum(rank <= 20 for rank in organ_values) / len(organ_values),
                "post_scoring_resolution_top20_frequency": resolution_by_symbol[symbol]["top20_frequency"],
                "single_layer_dependency_flag": bool(baseline[symbol] <= 20 and max(leave_values) > 50),
                "tier1_stability_precheck_not_final_tier": "passes_top20_frequency_only"
                if sum(rank <= 20 for rank in balanced_perturb) / len(balanced_perturb) >= TIER1_TOP20_PERTURBATION_THRESHOLD
                else "fails_top20_frequency_only",
                "analysis_status": "stability_precheck_not_final_tiering",
            }
        )
    rank_stability_rows.sort(key=lambda item: int(item["baseline_rank_v2"]))
    write_tsv(
        RANK_STABILITY,
        rank_stability_rows,
        [
            "hgnc_symbol",
            "baseline_rank_v2",
            "baseline_score_v2",
            "balanced_weight_perturb_top20_frequency",
            "all_weight_perturb_top20_frequency",
            "all_weight_perturb_top50_frequency",
            "all_weight_perturb_mean_rank",
            "all_weight_perturb_rank_p2_5",
            "all_weight_perturb_rank_p50",
            "all_weight_perturb_rank_p97_5",
            "leave_one_layer_min_rank",
            "leave_one_layer_max_rank",
            "leave_one_layer_max_abs_delta",
            "missing_data_min_rank",
            "missing_data_max_rank",
            "risk_form_min_rank",
            "risk_form_max_rank",
            "organ_weight_perturb_top20_frequency",
            "post_scoring_resolution_top20_frequency",
            "single_layer_dependency_flag",
            "tier1_stability_precheck_not_final_tier",
            "analysis_status",
        ],
    )

    control_symbols: list[tuple[str, str, str]] = []
    for label, entries in [
        ("positive_control", controls_config.get("positive_controls", [])),
        ("secondary_benchmark", controls_config.get("secondary_benchmark_targets", [])),
        ("negative_control", controls_config.get("negative_controls_intracellular_or_secreted", [])),
        ("tme_or_off_tumor_penalty_control", controls_config.get("tme_or_off_tumor_penalty_controls", [])),
    ]:
        for entry in entries:
            control_symbols.append((label, entry["gene"], entry.get("expected", "")))
    control_rows: list[dict[str, object]] = []
    stability_by_symbol = {row["hgnc_symbol"]: row for row in rank_stability_rows}
    for control_set, symbol, expected in control_symbols:
        stability = stability_by_symbol.get(symbol)
        control_rows.append(
            {
                "control_set": control_set,
                "hgnc_symbol": symbol,
                "expected": expected,
                "presence_status": "ranked_in_core_probable_universe" if stability else "not_in_core_probable_universe",
                "baseline_rank_v2": stability.get("baseline_rank_v2", "") if stability else "",
                "balanced_weight_perturb_top20_frequency": stability.get("balanced_weight_perturb_top20_frequency", "") if stability else "",
                "all_weight_perturb_top50_frequency": stability.get("all_weight_perturb_top50_frequency", "") if stability else "",
                "leave_one_layer_rank_range": f"{stability.get('leave_one_layer_min_rank')}-{stability.get('leave_one_layer_max_rank')}" if stability else "",
                "missing_data_rank_range": f"{stability.get('missing_data_min_rank')}-{stability.get('missing_data_max_rank')}" if stability else "",
                "risk_form_rank_range": f"{stability.get('risk_form_min_rank')}-{stability.get('risk_form_max_rank')}" if stability else "",
                "analysis_status": "benchmark_diagnostic_not_weight_tuning",
            }
        )
    write_tsv(
        CONTROL_BENCHMARK,
        control_rows,
        [
            "control_set",
            "hgnc_symbol",
            "expected",
            "presence_status",
            "baseline_rank_v2",
            "balanced_weight_perturb_top20_frequency",
            "all_weight_perturb_top50_frequency",
            "leave_one_layer_rank_range",
            "missing_data_rank_range",
            "risk_form_rank_range",
            "analysis_status",
        ],
    )

    tiering_by_symbol = by_symbol(read_tsv(TIERING_ANNOTATIONS))
    audit_rows: list[dict[str, object]] = []
    for row in baseline_rows[:30]:
        symbol = row["hgnc_symbol"]
        component = component_by_symbol.get(symbol, {})
        annotation = tiering_by_symbol.get(symbol, {})
        flags: list[str] = []
        if str(component.get("tme_contamination_risk", "")).startswith("high"):
            flags.append("high_TME_flag")
        if str(component.get("risk_interpretation", "")).startswith("high"):
            flags.append("high_normal_risk")
        if "isoform_unresolved" in str(component.get("isoform_resolution_status", "")):
            flags.append("isoform_unresolved")
        if str(component.get("hpa_evidence_status", "")).startswith("missing"):
            flags.append("protein_missing")
        if str(component.get("accessibility_class", "")) in {"D", "E"}:
            flags.append("low_or_ambiguous_accessibility")
        if int(str(component.get("n_missing_mvp_score_components", "0") or "0")) >= 3:
            flags.append("thin_evidence_missing_3plus")
        audit_rows.append(
            {
                "rank_v2": row["rank"],
                "hgnc_symbol": symbol,
                "scenario_score_v2": row["scenario_score"],
                "automatic_audit_flags": ";".join(flags) if flags else "none",
                "manual_curation_required_flags": annotation.get("manual_curation_required_flags", ""),
                "manual_review_status": "not_manual_reviewed_fase14_auto_flag_only",
                "tme_contamination_risk": component.get("tme_contamination_risk", ""),
                "risk_interpretation": component.get("risk_interpretation", ""),
                "max_risk_organ": component.get("max_risk_organ", ""),
                "isoform_resolution_status": component.get("isoform_resolution_status", ""),
                "accessibility_class": component.get("accessibility_class", ""),
                "hpa_evidence_status": component.get("hpa_evidence_status", ""),
                "missing_mvp_score_components": component.get("missing_mvp_score_components", ""),
                "analysis_status": "false_positive_audit_requires_fase15_manual_curation",
            }
        )
    write_tsv(
        TOP30_FALSE_POSITIVE_AUDIT,
        audit_rows,
        [
            "rank_v2",
            "hgnc_symbol",
            "scenario_score_v2",
            "automatic_audit_flags",
            "manual_curation_required_flags",
            "manual_review_status",
            "tme_contamination_risk",
            "risk_interpretation",
            "max_risk_organ",
            "isoform_resolution_status",
            "accessibility_class",
            "hpa_evidence_status",
            "missing_mvp_score_components",
            "analysis_status",
        ],
    )

    heatmap_sources: dict[str, dict[str, int]] = {
        "primary": baseline,
        "safety": scenario_ranks["safety_first"],
        "adc": scenario_ranks["adc_focused"],
        "novelty": scenario_ranks["novelty_focused"],
        "protein": scenario_ranks["protein_first"],
        "noSurf": leave_rank_maps["Surf"],
        "noE": leave_rank_maps["E"],
        "noN": leave_rank_maps["N"],
        "noR": leave_rank_maps["R"],
        "noP": leave_rank_maps["P"],
        "noT": leave_rank_maps["T"],
        "Rbreadth": risk_form_rank_maps["R_max_plus_breadth"],
        "Rsum": risk_form_rank_maps["R_sum_capped"],
        "missP50": missing_rank_maps["p50"],
    }
    write_rank_stability_heatmap([row["hgnc_symbol"] for row in baseline_rows[:30]], heatmap_sources)
    write_bumpchart_scenarios(scenario_ranks, baseline_top20)

    all_summary_rows = scenario_summary + leave_summary
    risk_form_summary = [
        summarize_ranking(baseline, ranks, f"risk_form_{form}", {"analysis_type": "risk_functional_form", "risk_form": form})
        for form, ranks in risk_form_rank_maps.items()
    ]
    threshold_summary = [
        summarize_ranking(baseline, ranks, f"risk_threshold_{mode}", {"analysis_type": "risk_threshold", "risk_threshold_scenario": mode})
        for mode, ranks in threshold_rank_maps.items()
    ]
    missing_summary = [
        summarize_ranking(baseline, ranks, f"missing_{scenario}", {"analysis_type": "missing_data", "missing_data_scenario": scenario})
        for scenario, ranks in missing_rank_maps.items()
    ]

    min_weight_spearman = min(float(row["spearman_vs_v2"]) for row in weight_rows)
    median_weight_spearman = float(np.median([float(row["spearman_vs_v2"]) for row in weight_rows]))
    min_weight_top20_retention = min(float(row["top20_retention_vs_v2"]) for row in weight_rows)
    perturbations_passing = sum(
        float(row["spearman_vs_v2"]) >= PERTURBATION_SPEARMAN_THRESHOLD
        and float(row["top20_retention_vs_v2"]) >= TOP20_RETENTION_THRESHOLD
        for row in weight_rows
    )
    worst_leave = min(leave_summary, key=lambda row: float(row["top20_retention_vs_v2"]))
    top20_stable_count = sum(
        float(row["balanced_weight_perturb_top20_frequency"]) >= TIER1_TOP20_PERTURBATION_THRESHOLD
        for row in rank_stability_rows
        if int(row["baseline_rank_v2"]) <= 20
    )
    post_scoring_contained = int(resolution_summary_rows[0]["value"])
    top30_flagged = sum(row["automatic_audit_flags"] != "none" for row in audit_rows)

    summary_lines = [
        f"- Weight perturbations passing both preregistered gates: {perturbations_passing}/{len(weight_rows)}.",
        f"- Minimum / median perturbation Spearman vs v2: `{fmt(min_weight_spearman)}` / `{fmt(median_weight_spearman)}`.",
        f"- Minimum top20 retention under weight perturbation: `{fmt(min_weight_top20_retention)}`.",
        f"- Most disruptive leave-one-layer-out by top20 retention: `{worst_leave['sensitivity_label']}` with retention `{fmt(worst_leave['top20_retention_vs_v2'])}`.",
        f"- Baseline top20 genes passing the predeclared >=40% Balanced-perturbation top20-frequency precheck: {top20_stable_count}/20.",
        f"- Post-scoring resolution top20 genes with 95% rank interval contained in top40: {post_scoring_contained}/20 (`{resolution_summary_rows[0]['status']}`).",
        f"- Top30 automated false-positive audit rows with at least one flag: {top30_flagged}/30.",
    ]
    scenario_lines = [
        f"- `{row['sensitivity_label']}`: Spearman `{fmt(row['spearman_vs_v2'])}`, top20 retention `{fmt(row['top20_retention_vs_v2'])}`"
        for row in scenario_summary
    ]
    leave_lines = [
        f"- `{row['omitted_layer']}` omitted: Spearman `{fmt(row['spearman_vs_v2'])}`, top20 retention `{fmt(row['top20_retention_vs_v2'])}`"
        for row in leave_summary
    ]
    risk_lines = [
        f"- `{row.get('risk_form', row.get('risk_threshold_scenario', ''))}`: {row['analysis_type']}, Spearman `{fmt(row['spearman_vs_v2'])}`, top20 retention `{fmt(row['top20_retention_vs_v2'])}`"
        for row in risk_form_summary + threshold_summary
    ]
    missing_lines = [
        f"- `{row['missing_data_scenario']}`: Spearman `{fmt(row['spearman_vs_v2'])}`, top20 retention `{fmt(row['top20_retention_vs_v2'])}`"
        for row in missing_summary
    ]

    decision = (
        "eligible_for_fase15_candidate_curation_not_final_tiering"
        if perturbations_passing == len(weight_rows)
        and top20_stable_count >= 10
        and post_scoring_contained >= int(params["ranking_resolution"]["top20_ci_contained_in_top40_min_genes"])
        else "fase15_allowed_with_coarse_tier_language_and_explicit_stability_limits"
    )

    note = f"""# Fase 14 Rank Stability

Date: 2026-05-31

Fase 14 was run on the frozen Fase 13 v2 preliminary ranking, `results/rankings/ranking_v2_frozen.tsv`. It does not create final biological tiers and does not change Fase 13 scores or weights.

## Inputs

- Ranking SHA256: `{sha256_file(RANKING_V2)}`
- Component table SHA256: `{sha256_file(COMPONENT_TABLE)}`
- Scoring config SHA256: `{sha256_file(SCORING_CONFIG)}`
- Preflight: `docs/fase14_preflight.md`
- Baseline top20: `{';'.join(baseline_top20)}`

## Summary

{chr(10).join(summary_lines)}

## Scenario Stability

{chr(10).join(scenario_lines)}

## Leave-One-Layer-Out

{chr(10).join(leave_lines)}

## Risk Sensitivity

{chr(10).join(risk_lines)}

## Missing Data Sensitivity

{chr(10).join(missing_lines)}

## Control Benchmark

Controls are audited in `results/validation/control_benchmark.tsv`. The Fase 13 aggregate positive-control top50 gate remains reported as failed, while the cause-corrected gate remains the relevant technical-failure diagnostic.

## False-Positive Audit

`results/validation/top30_false_positive_audit.tsv` is an automated flag audit for the top30. It is not manual biological curation; Fase 15 must review these candidates before final tier assignment.

## Decision

Current Fase 14 decision: `{decision}`.

This decision only authorizes candidate-level curation/tiering work. It is not a final target ranking claim.

## Outputs

- `results/validation/rank_stability.tsv`
- `results/validation/leave_one_layer_out.tsv`
- `results/validation/weight_perturbation_summary.tsv`
- `results/validation/risk_threshold_sensitivity.tsv`
- `results/validation/risk_functional_form_sensitivity.tsv`
- `results/validation/organ_weight_perturbation.tsv`
- `results/validation/ranking_resolution_post_scoring.tsv`
- `results/validation/ranking_resolution_post_scoring_summary.tsv`
- `results/validation/missing_data_sensitivity.tsv`
- `results/validation/control_benchmark.tsv`
- `results/validation/top30_false_positive_audit.tsv`
- `results/figures/rank_stability_heatmap.svg`
- `results/figures/bumpchart_scenarios.svg`
"""
    PHASE14_NOTE.write_text(note, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
