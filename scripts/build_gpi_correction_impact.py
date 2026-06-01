from __future__ import annotations

import csv
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "data" / "processed" / "surfaceome_universe.tsv"
RANKING_V1 = ROOT / "results" / "rankings" / "ranking_v1_frozen.tsv"
RANKING_V2 = ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
TIER_ASSIGNMENTS = ROOT / "results" / "tables" / "tier_assignments.tsv"
PREFLIGHT_TOP50_AUDIT = ROOT / "results" / "tables" / "fase14_preflight_top50_v1_v2_audit.tsv"
OUTPUT_SUMMARY = ROOT / "results" / "tables" / "gpi_correction_impact.tsv"
OUTPUT_RANK_DELTA = ROOT / "results" / "tables" / "gpi_rank_delta_v1_v2.tsv"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_int(value: str) -> int:
    return int(float(value))


def as_float(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def fmt_float(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def metric_row(metric: str, value: object, genes: list[str] | None, source: str, interpretation: str) -> dict[str, object]:
    return {
        "metric": metric,
        "value": value,
        "genes": ";".join(genes or []),
        "source": source,
        "interpretation": interpretation,
    }


def rank_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in rows}


def main() -> int:
    universe_rows = read_tsv(UNIVERSE)
    ranking_v1_rows = read_tsv(RANKING_V1)
    ranking_v2_rows = read_tsv(RANKING_V2)
    tier_rows = read_tsv(TIER_ASSIGNMENTS)
    preflight_rows = read_tsv(PREFLIGHT_TOP50_AUDIT)

    ranking_v1 = rank_map(ranking_v1_rows)
    ranking_v2 = rank_map(ranking_v2_rows)
    tier_by_gene = {row["gene"]: row["tier"] for row in tier_rows}

    confirmed_gpi = {
        row["hgnc_symbol"]
        for row in universe_rows
        if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"}
        and row.get("uniprot_gpi_anchor") == "true"
    }
    v1_genes = set(ranking_v1)
    v2_genes = set(ranking_v2)
    v1_top50 = {gene for gene, row in ranking_v1.items() if as_int(row["rank"]) <= 50}
    v2_top50 = {gene for gene, row in ranking_v2.items() if as_int(row["rank"]) <= 50}

    new_v2_genes = sorted(v2_genes - v1_genes)
    new_v2_gpi = sorted(set(new_v2_genes) & confirmed_gpi)
    new_top50_gpi = sorted((v2_top50 - v1_top50) & confirmed_gpi, key=lambda gene: as_int(ranking_v2[gene]["rank"]))
    suspicious_new_top50_gpi = sorted(
        row["hgnc_symbol"]
        for row in preflight_rows
        if row.get("hgnc_symbol") in new_top50_gpi and row.get("preflight_classification") == "new_v2_top50_suspicious"
    )
    current_tier12_gpi = sorted(
        [row["gene"] for row in tier_rows if row["tier"] in {"Tier 1", "Tier 2"} and row["gene"] in confirmed_gpi],
        key=lambda gene: as_int(ranking_v2[gene]["rank"]),
    )

    common_gpi = sorted(confirmed_gpi & v1_genes & v2_genes)
    rank_improvements = [as_int(ranking_v1[gene]["rank"]) - as_int(ranking_v2[gene]["rank"]) for gene in common_gpi]

    summary_rows = [
        metric_row(
            "pre_gpi_ranking_v1_gene_count",
            len(ranking_v1_rows),
            None,
            "results/rankings/ranking_v1_frozen.tsv",
            "Preserved pre-GPI snapshot used only for diagnostic comparison.",
        ),
        metric_row(
            "post_gpi_ranking_v2_gene_count",
            len(ranking_v2_rows),
            None,
            "results/rankings/ranking_v2_frozen.tsv",
            "Active frozen ranking after universe-wide GPI evidence correction.",
        ),
        metric_row(
            "ranked_universe_delta_v2_minus_v1",
            len(ranking_v2_rows) - len(ranking_v1_rows),
            new_v2_genes,
            "results/rankings/ranking_v1_frozen.tsv;results/rankings/ranking_v2_frozen.tsv",
            "Increase in ranked Core+Probable candidates after the GPI correction.",
        ),
        metric_row(
            "confirmed_gpi_in_current_core_probable_universe",
            len(confirmed_gpi),
            sorted(confirmed_gpi),
            "data/processed/surfaceome_universe.tsv",
            "Confirmed UniProt lipidation GPI-anchor genes currently admitted as Core+Probable.",
        ),
        metric_row(
            "confirmed_gpi_ranked_v1",
            len(confirmed_gpi & v1_genes),
            sorted(confirmed_gpi & v1_genes),
            "results/rankings/ranking_v1_frozen.tsv",
            "Confirmed GPI genes already ranked before the Fase 4 GPI evidence correction.",
        ),
        metric_row(
            "confirmed_gpi_ranked_v2",
            len(confirmed_gpi & v2_genes),
            sorted(confirmed_gpi & v2_genes),
            "results/rankings/ranking_v2_frozen.tsv",
            "Confirmed GPI genes ranked after the Fase 4 GPI evidence correction.",
        ),
        metric_row(
            "newly_ranked_v2_not_v1_confirmed_gpi",
            len(new_v2_gpi),
            new_v2_gpi,
            "results/rankings/ranking_v1_frozen.tsv;results/rankings/ranking_v2_frozen.tsv;data/processed/surfaceome_universe.tsv",
            "Newly ranked candidates in v2 that are confirmed GPI-anchor genes.",
        ),
        metric_row(
            "confirmed_gpi_top50_v1",
            len(confirmed_gpi & v1_top50),
            sorted(confirmed_gpi & v1_top50),
            "results/rankings/ranking_v1_frozen.tsv",
            "No confirmed GPI anchors were in the pre-GPI top 50.",
        ),
        metric_row(
            "confirmed_gpi_top50_v2",
            len(confirmed_gpi & v2_top50),
            sorted(confirmed_gpi & v2_top50, key=lambda gene: as_int(ranking_v2[gene]["rank"])),
            "results/rankings/ranking_v2_frozen.tsv",
            "Confirmed GPI anchors in the active post-GPI top 50.",
        ),
        metric_row(
            "new_confirmed_gpi_top50_v2_not_v1_top50",
            len(new_top50_gpi),
            new_top50_gpi,
            "results/tables/fase14_preflight_top50_v1_v2_audit.tsv",
            "GPI anchors entering the top 50 after the correction.",
        ),
        metric_row(
            "suspicious_new_confirmed_gpi_top50_preflight",
            len(suspicious_new_top50_gpi),
            suspicious_new_top50_gpi,
            "results/tables/fase14_preflight_top50_v1_v2_audit.tsv",
            "Preflight count of new top50 GPI entrants classified as suspicious Surf-dominant artifacts.",
        ),
        metric_row(
            "current_tier1_2_confirmed_gpi",
            len(current_tier12_gpi),
            current_tier12_gpi,
            "results/tables/tier_assignments.tsv",
            "Current Tier 1/2 GPI candidates after v2 tiering; no pre-GPI tier-delta claim is made.",
        ),
        metric_row(
            "common_gpi_median_rank_improvement_v1_minus_v2",
            f"{statistics.median(rank_improvements):.0f}" if rank_improvements else "NA",
            None,
            "results/rankings/ranking_v1_frozen.tsv;results/rankings/ranking_v2_frozen.tsv",
            "Positive values mean improved rank in v2 among confirmed GPI genes present in both snapshots.",
        ),
    ]

    for gene in ["CEACAM5", "MSLN", "BST2", "ALPG", "ULBP2", "NT5E"]:
        if gene not in ranking_v2:
            continue
        rank_v1 = ranking_v1.get(gene, {}).get("rank", "")
        rank_v2 = ranking_v2[gene]["rank"]
        value = f"{rank_v1 or 'not_ranked'}->{rank_v2}"
        summary_rows.append(
            metric_row(
                f"{gene}_rank_v1_to_v2",
                value,
                [gene],
                "results/rankings/ranking_v1_frozen.tsv;results/rankings/ranking_v2_frozen.tsv",
                "Rank movement for a named GPI/benchmark gene after universe-wide GPI correction.",
            )
        )

    summary_rows.append(
        metric_row(
            "pre_gpi_tier_delta_available",
            "false",
            None,
            "results/tables/tier_assignments.tsv",
            "Tiering was performed after v2; the audit quantifies rank/universe impact and current GPI tier presence, not pre/post tier changes.",
        )
    )

    detail_rows: list[dict[str, object]] = []
    for gene in sorted(confirmed_gpi, key=lambda item: as_int(ranking_v2[item]["rank"]) if item in ranking_v2 else 999999):
        row_v1 = ranking_v1.get(gene)
        row_v2 = ranking_v2.get(gene)
        if row_v2 is None:
            continue
        rank_v1 = as_int(row_v1["rank"]) if row_v1 else None
        rank_v2 = as_int(row_v2["rank"])
        score_v1 = as_float(row_v1["scenario_score"]) if row_v1 else None
        score_v2 = as_float(row_v2["scenario_score"])
        detail_rows.append(
            {
                "hgnc_symbol": gene,
                "rank_v1": "" if rank_v1 is None else rank_v1,
                "rank_v2": rank_v2,
                "rank_improvement_v1_minus_v2": "" if rank_v1 is None else rank_v1 - rank_v2,
                "score_v1": fmt_float(score_v1),
                "score_v2": fmt_float(score_v2),
                "score_delta_v2_minus_v1": "" if score_v1 is None or score_v2 is None else fmt_float(score_v2 - score_v1),
                "Surf_relative_confidence_v1": "" if row_v1 is None else row_v1.get("Surf_relative_confidence", ""),
                "Surf_relative_confidence_v2": row_v2.get("Surf_relative_confidence", ""),
                "tier_v2": tier_by_gene.get(gene, "not_tiered_or_watchlist_absent"),
                "top50_v1": "true" if gene in v1_top50 else "false",
                "top50_v2": "true" if gene in v2_top50 else "false",
                "newly_ranked_post_gpi": "true" if gene in new_v2_gpi else "false",
            }
        )

    write_tsv(OUTPUT_SUMMARY, summary_rows)
    write_tsv(OUTPUT_RANK_DELTA, detail_rows)
    print(f"Wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_RANK_DELTA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
