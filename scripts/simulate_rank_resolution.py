"""Run the Fase 4B pre-scoring ranking-resolution simulation."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
RESULTS_DIR = REPO_ROOT / "results"
VALIDATION_DIR = RESULTS_DIR / "validation"
FIGURES_DIR = RESULTS_DIR / "figures"
DOCS_DIR = REPO_ROOT / "docs"
FROZEN_ACCESS_DATE = "2026-06-01"

SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
ID_MAP = PROCESSED_DIR / "id_map_master.tsv"
SCORING_CONFIG = REPO_ROOT / "config" / "scoring_scenarios.yaml"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"

COMPONENTS = ["Surf", "E", "N", "R", "P", "T"]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def bool_value(value: str) -> bool:
    return str(value).strip().lower() == "true"


def load_configs() -> tuple[dict[str, float], dict[str, object]]:
    scoring = yaml.safe_load(SCORING_CONFIG.read_text(encoding="utf-8"))
    params = yaml.safe_load(PARAMETERS_CONFIG.read_text(encoding="utf-8"))
    weights = scoring["scenarios"]["balanced"]["weights"]
    return {component: float(weights[component]) for component in COMPONENTS}, params


def candidate_rows() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    universe = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"}
    ]
    universe.sort(key=lambda row: row["hgnc_symbol"])
    id_map = {row["hgnc_symbol"]: row for row in read_tsv(ID_MAP)}
    return universe, id_map


def component_availability(universe: list[dict[str, str]], id_map: dict[str, dict[str, str]]) -> dict[str, np.ndarray]:
    symbols = [row["hgnc_symbol"] for row in universe]
    arrays: dict[str, list[bool]] = {component: [] for component in COMPONENTS}
    for row in universe:
        id_row = id_map[row["hgnc_symbol"]]
        arrays["Surf"].append(True)
        arrays["E"].append(bool_value(id_row.get("in_xena_expression", "")))
        arrays["N"].append(bool_value(id_row.get("in_xena_expression", "")))
        arrays["R"].append(bool_value(id_row.get("in_hpa", "")))
        arrays["P"].append(bool_value(id_row.get("in_hpa", "")))
        arrays["T"].append(bool_value(id_row.get("in_uniprot_reviewed", "")))
    if len(symbols) != len(set(symbols)):
        raise ValueError("surfaceome candidate universe contains duplicate HGNC symbols")
    return {key: np.array(value, dtype=bool) for key, value in arrays.items()}


def normalize_surfaceome_scores(universe: list[dict[str, str]]) -> np.ndarray:
    raw = np.array([float(row["surfaceome_confidence_score"]) for row in universe], dtype=float)
    min_value = float(raw.min())
    max_value = float(raw.max())
    if max_value == min_value:
        return np.ones_like(raw)
    return (raw - min_value) / (max_value - min_value)


def rank_scores(scores: np.ndarray) -> np.ndarray:
    # Rank 1 is best. Stable mergesort makes ties deterministic.
    order = np.argsort(-scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def run_simulation(
    universe: list[dict[str, str]],
    availability: dict[str, np.ndarray],
    weights: dict[str, float],
    params: dict[str, object],
) -> tuple[np.ndarray, dict[str, float]]:
    ranking_params = params.get("ranking_resolution", {})
    n_simulations = int(ranking_params.get("n_simulations", 500))
    latent_weight = float(ranking_params.get("latent_weight_neutral_layers", 0.70))
    noise_sd = float(ranking_params.get("component_noise_sd", 0.08))
    seed = int(params["random"]["rank_resolution_seed"])

    rng = np.random.default_rng(seed)
    n_genes = len(universe)
    ranks = np.zeros((n_simulations, n_genes), dtype=float)
    surfaceome_component = normalize_surfaceome_scores(universe)
    latent_quality = np.clip(0.50 * surfaceome_component + 0.50 * rng.beta(2.0, 2.0, size=n_genes), 0.0, 1.0)

    active_weight_sum = sum(weights.values())
    if active_weight_sum <= 0:
        raise ValueError("balanced weights for Fase 4B sum to zero")

    for simulation_idx in range(n_simulations):
        numerator = np.zeros(n_genes, dtype=float)
        denominator = np.zeros(n_genes, dtype=float)
        for component in COMPONENTS:
            component_weight = weights[component]
            if component_weight <= 0:
                continue
            observed = availability[component]
            if component == "Surf":
                values = np.clip(surfaceome_component + rng.normal(0.0, noise_sd / 2.0, size=n_genes), 0.0, 1.0)
            else:
                neutral_draw = rng.beta(2.0, 2.0, size=n_genes)
                values = np.clip(latent_weight * latent_quality + (1.0 - latent_weight) * neutral_draw, 0.0, 1.0)
                values = np.clip(values + rng.normal(0.0, noise_sd, size=n_genes), 0.0, 1.0)
            numerator[observed] += component_weight * values[observed]
            denominator[observed] += component_weight
        scores = np.divide(numerator, denominator, out=np.full(n_genes, -np.inf), where=denominator > 0)
        ranks[simulation_idx, :] = rank_scores(scores)
    metadata = {
        "n_simulations": n_simulations,
        "latent_weight_neutral_layers": latent_weight,
        "component_noise_sd": noise_sd,
        "seed": seed,
    }
    return ranks, metadata


def summarize_gene_ranks(universe: list[dict[str, str]], ranks: np.ndarray) -> list[dict[str, object]]:
    p2 = np.percentile(ranks, 2.5, axis=0)
    p50 = np.percentile(ranks, 50.0, axis=0)
    p97 = np.percentile(ranks, 97.5, axis=0)
    mean = ranks.mean(axis=0)
    sd = ranks.std(axis=0, ddof=1)
    top20_frequency = (ranks <= 20).mean(axis=0)
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(universe):
        ci_width = float(p97[idx] - p2[idx])
        rows.append(
            {
                "hgnc_symbol": row["hgnc_symbol"],
                "surfaceome_category": row["surfaceome_category"],
                "surfaceome_confidence_score": row["surfaceome_confidence_score"],
                "mean_rank": f"{mean[idx]:.3f}",
                "sd_rank": f"{sd[idx]:.3f}",
                "rank_p2_5": f"{p2[idx]:.3f}",
                "rank_p50": f"{p50[idx]:.3f}",
                "rank_p97_5": f"{p97[idx]:.3f}",
                "rank_ci_width": f"{ci_width:.3f}",
                "rank_ci_half_width": f"{ci_width / 2.0:.3f}",
                "ci_within_plusminus_10": str(ci_width <= 20.0).lower(),
                "ci_exceeds_plusminus_50": str(ci_width > 100.0).lower(),
                "ci_contained_in_top40": str(p97[idx] <= 40.0).lower(),
                "top20_frequency": f"{top20_frequency[idx]:.4f}",
            }
        )
    rows.sort(key=lambda item: (float(item["rank_p50"]), float(item["rank_p97_5"]), item["hgnc_symbol"]))
    return rows


def summarize_resolution(
    gene_rows: list[dict[str, object]],
    universe: list[dict[str, str]],
    availability: dict[str, np.ndarray],
    metadata: dict[str, float],
) -> list[dict[str, object]]:
    top20 = gene_rows[:20]
    top20_ci_top40 = [row for row in top20 if row["ci_contained_in_top40"] == "true"]
    tight = [row for row in gene_rows if row["ci_within_plusminus_10"] == "true"]
    wide = [row for row in gene_rows if row["ci_exceeds_plusminus_50"] == "true"]
    decision = "five_tier_starting_point_supported" if len(top20_ci_top40) >= 10 else "reduce_to_three_tiers_or_raise_tier1_stability_threshold"

    summary: list[dict[str, object]] = [
        {"metric": "candidate_universe_n", "value": len(universe), "notes": "Core+Probable surfaceome genes from Fase 4"},
        {"metric": "n_simulations", "value": int(metadata["n_simulations"]), "notes": "K synthetic rankings"},
        {"metric": "rank_resolution_seed", "value": int(metadata["seed"]), "notes": "config/parameters.yaml random.rank_resolution_seed"},
        {"metric": "genes_ci_within_plusminus_10", "value": len(tight), "notes": "95% rank CI width <=20 positions"},
        {"metric": "genes_ci_exceeds_plusminus_50", "value": len(wide), "notes": "95% rank CI width >100 positions"},
        {"metric": "top20_median_rank_genes", "value": len(top20), "notes": "Twenty genes with the best simulated median ranks"},
        {"metric": "top20_with_ci_contained_in_top40", "value": len(top20_ci_top40), "notes": "Exit criterion threshold is >=10"},
        {"metric": "tiering_resolution_decision", "value": decision, "notes": "Pre-scoring calibration only; repeat with real score distributions in Fase 14"},
    ]
    for component in COMPONENTS:
        coverage = float(availability[component].mean())
        summary.append(
            {
                "metric": f"coverage_{component}",
                "value": f"{coverage:.4f}",
                "notes": "Observed source availability among Core+Probable candidates",
            }
        )
    return summary


def plot_rank_ci(gene_rows: list[dict[str, object]], summary_rows: list[dict[str, object]], output: Path) -> None:
    ordered = gene_rows[:120]
    x = np.arange(1, len(ordered) + 1)
    p2 = np.array([float(row["rank_p2_5"]) for row in ordered])
    p50 = np.array([float(row["rank_p50"]) for row in ordered])
    p97 = np.array([float(row["rank_p97_5"]) for row in ordered])
    lower = p50 - p2
    upper = p97 - p50

    fig, (ax_rank, ax_cov) = plt.subplots(
        2,
        1,
        figsize=(9.2, 7.2),
        gridspec_kw={"height_ratios": [3.0, 1.0]},
    )
    ax_rank.errorbar(x, p50, yerr=[lower, upper], fmt=".", markersize=3, linewidth=0.6, color="#1f4e79", ecolor="#8aa6c1")
    ax_rank.axhline(20, color="#166534", linestyle="--", linewidth=0.9, label="Top 20")
    ax_rank.axhline(40, color="#b45309", linestyle="--", linewidth=0.9, label="Top 40")
    ax_rank.invert_yaxis()
    ax_rank.set_ylabel("Synthetic rank")
    ax_rank.set_title("Fase 4B ranking-resolution simulation")
    ax_rank.legend(frameon=False, loc="upper right")
    ax_rank.grid(axis="y", linewidth=0.35, alpha=0.3)

    cov_rows = [row for row in summary_rows if str(row["metric"]).startswith("coverage_")]
    labels = [str(row["metric"]).replace("coverage_", "") for row in cov_rows]
    values = [float(row["value"]) for row in cov_rows]
    ax_cov.bar(labels, values, color="#64748b")
    ax_cov.set_ylim(0, 1.05)
    ax_cov.set_ylabel("Coverage")
    ax_cov.set_xlabel("Balanced-score component")
    ax_cov.grid(axis="y", linewidth=0.35, alpha=0.3)

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="svg")
    plt.close(fig)


def write_notes(summary_rows: list[dict[str, object]], metadata: dict[str, float]) -> None:
    values = {str(row["metric"]): row["value"] for row in summary_rows}
    coverage_lines = "\n".join(
        f"- {row['metric'].replace('coverage_', '')}: {row['value']}"
        for row in summary_rows
        if str(row["metric"]).startswith("coverage_")
    )
    (DOCS_DIR / "fase4b_ranking_resolution.md").write_text(
        f"""# Fase 4B Ranking-Resolution Simulation

Access date: {FROZEN_ACCESS_DATE}

This pre-scoring simulation estimates whether the current surfaceome universe and observed layer coverage can support fine-grained tiering before biological expression/selectivity results are inspected.

The simulation uses the Core+Probable Fase 4 universe (`N={values['candidate_universe_n']}`), `K={values['n_simulations']}` synthetic rankings, the preregistered Balanced weights, and `exclude_and_renormalize` missing-data handling. `Surf` uses the observed Fase 4 surfaceome confidence score. `E`, `N`, `R`, `P`, and `T` use neutral synthetic score distributions because their real score distributions are not available before Fase 5+. `R` is simulated as favorable low-risk contribution for rank-resolution purposes only.

## Coverage Used

{coverage_lines}

## Resolution Summary

- Genes with 95% rank CI within +/-10 positions: {values['genes_ci_within_plusminus_10']}
- Genes with 95% rank CI exceeding +/-50 positions: {values['genes_ci_exceeds_plusminus_50']}
- Median-rank top 20 genes with 95% CI contained in top 40: {values['top20_with_ci_contained_in_top40']}
- Decision: `{values['tiering_resolution_decision']}`

## Interpretation

Fase 4B is not a statistical power test and does not assign biological priority. It calibrates how much rank movement is expected from missingness and neutral layer uncertainty. The simulation must be repeated in Fase 14 with real component-score distributions and perturbation/leave-one-layer-out sensitivity before interpreting final rank positions.

## Parameters

- Seed: {int(metadata['seed'])}
- Latent weight for neutral layers: {metadata['latent_weight_neutral_layers']}
- Component noise SD: {metadata['component_noise_sd']}

## Outputs

- `results/validation/ranking_resolution_simulation.tsv`
- `results/validation/ranking_resolution_summary.tsv`
- `results/figures/rank_ci_by_coverage.svg`
""",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)

    weights, params = load_configs()
    universe, id_map = candidate_rows()
    availability = component_availability(universe, id_map)
    ranks, metadata = run_simulation(universe, availability, weights, params)
    gene_rows = summarize_gene_ranks(universe, ranks)
    summary_rows = summarize_resolution(gene_rows, universe, availability, metadata)

    write_tsv(
        VALIDATION_DIR / "ranking_resolution_simulation.tsv",
        gene_rows,
        [
            "hgnc_symbol",
            "surfaceome_category",
            "surfaceome_confidence_score",
            "mean_rank",
            "sd_rank",
            "rank_p2_5",
            "rank_p50",
            "rank_p97_5",
            "rank_ci_width",
            "rank_ci_half_width",
            "ci_within_plusminus_10",
            "ci_exceeds_plusminus_50",
            "ci_contained_in_top40",
            "top20_frequency",
        ],
    )
    write_tsv(
        VALIDATION_DIR / "ranking_resolution_summary.tsv",
        summary_rows,
        ["metric", "value", "notes"],
    )
    plot_rank_ci(gene_rows, summary_rows, FIGURES_DIR / "rank_ci_by_coverage.svg")
    write_notes(summary_rows, metadata)
    print("Wrote Fase 4B ranking-resolution simulation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
