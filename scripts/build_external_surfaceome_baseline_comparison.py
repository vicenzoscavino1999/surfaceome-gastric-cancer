from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "data" / "processed" / "surfaceome_universe.tsv"
RANKING = ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
TIER_TABLE = ROOT / "results" / "tables" / "manuscript_table3_top_candidates.tsv"
OUTPUT_SUMMARY = ROOT / "results" / "tables" / "external_surfaceome_baseline_comparison.tsv"
OUTPUT_GENE_RANKS = ROOT / "results" / "tables" / "external_surfaceome_baseline_gene_ranks.tsv"
OUTPUT_DOC = ROOT / "docs" / "external_surfaceome_baseline_comparison.md"


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fmt(value: float, digits: int = 6) -> str:
    return f"{float(value):.{digits}g}"


def compare_baseline(
    merged: pd.DataFrame,
    score_column: str,
    baseline_id: str,
    baseline_name: str,
    tier18: set[str],
) -> tuple[dict[str, object], pd.DataFrame]:
    sub = merged.dropna(subset=[score_column, "scenario_score"]).copy()
    sub["baseline_score"] = sub[score_column].astype(float)
    sub["final_score"] = sub["scenario_score"].astype(float)
    sub["rank"] = sub["rank"].astype(int)
    sub = sub.sort_values(["baseline_score", "hgnc_symbol"], ascending=[False, True])
    sub["baseline_rank"] = range(1, len(sub) + 1)
    rho, p_value = spearmanr(sub["final_score"], sub["baseline_score"])

    our_top20 = set(merged.sort_values("rank").head(20)["hgnc_symbol"])
    our_top50 = set(merged.sort_values("rank").head(50)["hgnc_symbol"])
    baseline_top20 = set(sub.head(20)["hgnc_symbol"])
    baseline_top50 = set(sub.head(50)["hgnc_symbol"])
    baseline_top100 = set(sub.head(100)["hgnc_symbol"])
    tier18_in_top100 = sorted(tier18 & baseline_top100)
    top20_overlap = sorted(our_top20 & baseline_top20)
    top50_overlap = sorted(our_top50 & baseline_top50)

    row = {
        "baseline_id": baseline_id,
        "baseline_name": baseline_name,
        "n_overlap_genes": len(sub),
        "spearman_rho_final_score_vs_baseline": fmt(rho),
        "spearman_p_value": fmt(p_value),
        "top20_overlap_n": len(top20_overlap),
        "top20_jaccard": fmt(len(top20_overlap) / len(our_top20 | baseline_top20)),
        "top20_overlap_genes": ";".join(top20_overlap),
        "top50_overlap_n": len(top50_overlap),
        "top50_jaccard": fmt(len(top50_overlap) / len(our_top50 | baseline_top50)),
        "top50_overlap_genes": ";".join(top50_overlap),
        "tier1_2_in_baseline_top100_n": len(tier18_in_top100),
        "tier1_2_in_baseline_top100_genes": ";".join(tier18_in_top100),
        "interpretation": "moderate concordance with a pan-cancer external surfaceome score; low top-k identity indicates the final ranking is not a clone of the external baseline",
    }
    sub["baseline_id"] = baseline_id
    sub["baseline_name"] = baseline_name
    return row, sub


def write_doc(summary_rows: list[dict[str, object]]) -> None:
    final_row = next(row for row in summary_rows if row["baseline_id"] == "tcsa_final_gesp_score")
    core_row = next(row for row in summary_rows if row["baseline_id"] == "tcsa_core_gesp_score")
    lines = [
        "# External Surfaceome Baseline Comparison",
        "",
        "This analysis compares the final frozen gastric ranking against the Cancer Surfaceome Atlas",
        "(TCSA) pan-cancer GESP scores carried in `surfaceome_universe.tsv`. TCSA is used as an",
        "external surfaceome-prioritization baseline, not as a gastric-specific validation label.",
        "",
        "## Results",
        "",
        f"- TCSA final GESP score: Spearman rho={final_row['spearman_rho_final_score_vs_baseline']}, "
        f"n={final_row['n_overlap_genes']}, top20 overlap={final_row['top20_overlap_n']} "
        f"({final_row['top20_overlap_genes'] or 'none'}).",
        f"- TCSA core GESP score: Spearman rho={core_row['spearman_rho_final_score_vs_baseline']}, "
        f"n={core_row['n_overlap_genes']}, top20 overlap={core_row['top20_overlap_n']} "
        f"({core_row['top20_overlap_genes'] or 'none'}).",
        "",
        "Interpretation: the ranking is related to an external published surfaceome score, but the modest",
        "correlation and low top-k identity show that tumor expression, normal selectivity, risk, protein",
        "evidence, topology, stability, and curation materially change candidate prioritization.",
        "",
        "## Outputs",
        "",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT).as_posix()}`",
        f"- `{OUTPUT_GENE_RANKS.relative_to(ROOT).as_posix()}`",
    ]
    OUTPUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    universe = pd.read_csv(UNIVERSE, sep="\t", dtype=str)
    ranking = pd.read_csv(RANKING, sep="\t", dtype=str)
    tier18 = set(pd.read_csv(TIER_TABLE, sep="\t", dtype=str)["gene"])
    merged = ranking.merge(
        universe[["hgnc_symbol", "tcsa_core_gesp_score", "tcsa_final_gesp_score"]],
        on="hgnc_symbol",
        how="left",
    )
    for column in ["rank", "scenario_score", "tcsa_core_gesp_score", "tcsa_final_gesp_score"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")

    summary_rows: list[dict[str, object]] = []
    gene_rank_frames: list[pd.DataFrame] = []
    for column, label in [
        ("tcsa_final_gesp_score", "Cancer Surfaceome Atlas final GESP score"),
        ("tcsa_core_gesp_score", "Cancer Surfaceome Atlas core GESP score"),
    ]:
        row, frame = compare_baseline(merged, column, column, label, tier18)
        summary_rows.append(row)
        gene_rank_frames.append(
            frame[
                [
                    "baseline_id",
                    "baseline_name",
                    "hgnc_symbol",
                    "rank",
                    "final_score",
                    "baseline_score",
                    "baseline_rank",
                ]
            ]
        )

    write_tsv(OUTPUT_SUMMARY, summary_rows, list(summary_rows[0]))
    gene_ranks = pd.concat(gene_rank_frames, ignore_index=True)
    gene_ranks.to_csv(OUTPUT_GENE_RANKS, sep="\t", index=False, lineterminator="\n")
    write_doc(summary_rows)
    print(f"Wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_GENE_RANKS.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
