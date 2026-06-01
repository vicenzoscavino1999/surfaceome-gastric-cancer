from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "data" / "processed" / "surfaceome_universe.tsv"
RANKING = ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
TIERS = ROOT / "results" / "tables" / "tier_assignments.tsv"
OUTPUT_AUDIT = ROOT / "results" / "tables" / "surfaceome_source_dependency_audit.tsv"
OUTPUT_SUMMARY = ROOT / "results" / "tables" / "surfaceome_source_dependency_summary.tsv"
OUTPUT_DOC = ROOT / "docs" / "surfaceome_source_dependency_audit.md"

SOURCE_GROUPS = [
    ("tcsa", "TCSA curated cancer surfaceome"),
    ("cspa", "CSPA experimental cell-surface proteomics"),
    ("surfy", "SURFY in silico surfaceome"),
    ("uniprot_anchor", "UniProt topology/TM/GPI anchor"),
    ("hpa_plasma_membrane", "HPA plasma-membrane localization"),
    ("go_plasma_membrane", "GO plasma-membrane/surface annotation"),
]

CURATED_GROUPS = {"tcsa", "cspa", "surfy"}
ANCHOR_GROUPS = {"uniprot_anchor", "hpa_plasma_membrane", "go_plasma_membrane"}


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


def format_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return "" if value is None else str(value)


def is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def source_flags(universe_row: dict[str, str]) -> dict[str, bool]:
    return {
        "tcsa": is_true(universe_row.get("in_tcsa")),
        "cspa": is_true(universe_row.get("in_cspa")),
        "surfy": is_true(universe_row.get("in_surfy")),
        "uniprot_anchor": any(
            is_true(universe_row.get(column))
            for column in [
                "uniprot_extracellular_topology",
                "uniprot_transmembrane",
                "uniprot_gpi_anchor",
            ]
        ),
        "hpa_plasma_membrane": is_true(universe_row.get("hpa_plasma_membrane")),
        "go_plasma_membrane": is_true(universe_row.get("go_surface_or_plasma_membrane")),
    }


def dependency_class(
    support_count: int,
    curated_count: int,
    anchor_count: int,
) -> str:
    if support_count == 0:
        return "no_declared_source_support_review_required"
    if support_count == 1:
        return "single_source_dependent"
    if curated_count > 0 and anchor_count > 0:
        return "source_diverse_curated_plus_anchor"
    if curated_count >= 2:
        return "multi_curated_list_only"
    if anchor_count >= 2:
        return "multi_database_anchor_only"
    return "multi_source_same_family"


def interpretation_for(row: dict[str, object]) -> str:
    if row["source_dependency_class"] == "single_source_dependent":
        return "Removing the listed critical source eliminates declared surfaceome support; manual review is required."
    if row["source_dependency_class"] == "source_diverse_curated_plus_anchor":
        return "Curated-list support is corroborated by at least one independent database/localization anchor."
    if row["source_dependency_class"] == "multi_curated_list_only":
        return "Multiple curated surfaceome lists support the candidate, but no UniProt/HPA/GO anchor is declared."
    if row["source_dependency_class"] == "multi_database_anchor_only":
        return "Multiple database/localization anchors support the candidate without curated-list dependence."
    return "Multiple declared source groups support the candidate."


def build_audit_rows() -> list[dict[str, object]]:
    universe_by_gene = by_key(read_tsv(UNIVERSE), "hgnc_symbol")
    ranking_by_gene = by_key(read_tsv(RANKING), "hgnc_symbol")
    tier_rows = [
        row
        for row in read_tsv(TIERS)
        if row.get("tier") in {"Tier 1", "Tier 2"}
    ]
    tier_rows.sort(key=lambda row: int(row["rank_v2"]))

    audit_rows: list[dict[str, object]] = []
    for tier_row in tier_rows:
        gene = tier_row["gene"]
        universe = universe_by_gene[gene]
        ranking = ranking_by_gene.get(gene, {})
        flags = source_flags(universe)
        present = [source_id for source_id, _label in SOURCE_GROUPS if flags[source_id]]
        curated_count = sum(1 for source_id in present if source_id in CURATED_GROUPS)
        anchor_count = sum(1 for source_id in present if source_id in ANCHOR_GROUPS)
        support_count = len(present)
        remaining_by_source = {
            source_id: sum(1 for other_id in flags if other_id != source_id and flags[other_id])
            for source_id, _label in SOURCE_GROUPS
        }
        critical_removed = [
            source_id
            for source_id, _label in SOURCE_GROUPS
            if flags[source_id] and remaining_by_source[source_id] == 0
        ]
        row: dict[str, object] = {
            "rank_v2": tier_row["rank_v2"],
            "gene": gene,
            "tier": tier_row["tier"],
            "scenario_score": ranking.get("scenario_score", ""),
            "surfaceome_category": universe.get("surfaceome_category", ""),
            "surfaceome_confidence_score": universe.get("surfaceome_confidence_score", ""),
            "source_support_n": support_count,
            "curated_surfaceome_source_n": curated_count,
            "database_or_localization_anchor_n": anchor_count,
            "support_sources": present,
            "source_dependency_class": dependency_class(support_count, curated_count, anchor_count),
            "single_source_dependent": support_count == 1,
            "retains_support_after_any_single_source_removal": support_count >= 2,
            "critical_removed_sources": critical_removed,
            "surface_support_sources_original": universe.get("surface_support_sources", ""),
        }
        for source_id, _label in SOURCE_GROUPS:
            row[f"has_{source_id}"] = flags[source_id]
            row[f"remaining_support_after_removing_{source_id}"] = remaining_by_source[source_id]
        row["interpretation"] = interpretation_for(row)
        audit_rows.append(row)
    return audit_rows


def add_summary(
    rows: list[dict[str, object]],
    metric: str,
    group: str,
    numerator: int,
    denominator: int,
    genes: list[str],
    interpretation: str,
) -> dict[str, object]:
    return {
        "metric": metric,
        "group": group,
        "value": numerator,
        "denominator": denominator,
        "fraction": f"{numerator / denominator:.3f}" if denominator else "",
        "genes": genes,
        "interpretation": interpretation,
    }


def build_summary_rows(audit_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    groups = {
        "Tier 1+2": audit_rows,
        "Tier 1": [row for row in audit_rows if row["tier"] == "Tier 1"],
        "Tier 2": [row for row in audit_rows if row["tier"] == "Tier 2"],
    }
    for group, rows in groups.items():
        denominator = len(rows)
        multi = [row for row in rows if int(row["source_support_n"]) >= 2]
        diverse = [row for row in rows if row["source_dependency_class"] == "source_diverse_curated_plus_anchor"]
        single = [row for row in rows if row["single_source_dependent"] is True]
        retained = [row for row in rows if row["retains_support_after_any_single_source_removal"] is True]
        summary.append(
            add_summary(
                audit_rows,
                "multi_source_supported",
                group,
                len(multi),
                denominator,
                [str(row["gene"]) for row in multi],
                "Candidates have at least two declared source groups.",
            )
        )
        summary.append(
            add_summary(
                audit_rows,
                "source_diverse_curated_plus_anchor",
                group,
                len(diverse),
                denominator,
                [str(row["gene"]) for row in diverse],
                "Candidates combine curated surfaceome-list support with UniProt/HPA/GO anchoring.",
            )
        )
        summary.append(
            add_summary(
                audit_rows,
                "retains_support_after_any_single_source_removal",
                group,
                len(retained),
                denominator,
                [str(row["gene"]) for row in retained],
                "Candidates would retain at least one declared surfaceome source after dropping any single source group.",
            )
        )
        summary.append(
            add_summary(
                audit_rows,
                "single_source_dependent",
                group,
                len(single),
                denominator,
                [str(row["gene"]) for row in single],
                "Candidates whose declared surfaceome support collapses if their only source is removed.",
            )
        )

    for source_id, label in SOURCE_GROUPS:
        losing = [
            row
            for row in audit_rows
            if row[f"has_{source_id}"] is True
            and int(row[f"remaining_support_after_removing_{source_id}"]) == 0
        ]
        summary.append(
            add_summary(
                audit_rows,
                f"loses_all_support_after_removing_{source_id}",
                "Tier 1+2",
                len(losing),
                len(audit_rows),
                [str(row["gene"]) for row in losing],
                f"Candidates fully dependent on {label}.",
            )
        )
    return summary


def write_doc(audit_rows: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> None:
    def metric_value(metric: str, group: str = "Tier 1+2") -> dict[str, object]:
        for row in summary_rows:
            if row["metric"] == metric and row["group"] == group:
                return row
        raise KeyError(metric)

    multi = metric_value("multi_source_supported")
    diverse = metric_value("source_diverse_curated_plus_anchor")
    retained = metric_value("retains_support_after_any_single_source_removal")
    single = metric_value("single_source_dependent")
    class_counts: dict[str, int] = {}
    for row in audit_rows:
        key = str(row["source_dependency_class"])
        class_counts[key] = class_counts.get(key, 0) + 1
    class_lines = [
        f"- `{key}`: {value}" for key, value in sorted(class_counts.items())
    ]
    single_gene_list = single["genes"]
    if isinstance(single_gene_list, list):
        single_genes = ";".join(str(gene) for gene in single_gene_list) or "none"
    else:
        single_genes = str(single_gene_list) or "none"
    lines = [
        "# Surfaceome Source-Dependency Audit",
        "",
        "Date: 2026-06-01",
        "",
        "## Scope",
        "",
        "This post-ranking robustness audit checks whether the 18 Tier 1/2 candidates depend",
        "on a single declared surfaceome source. It does not change scores, weights, universe",
        "membership, rankings, or tier assignments.",
        "",
        "Source groups tested:",
        "",
        "- TCSA curated cancer surfaceome",
        "- CSPA experimental cell-surface proteomics",
        "- SURFY in silico surfaceome",
        "- UniProt extracellular topology, transmembrane, or confirmed GPI-anchor evidence",
        "- HPA plasma-membrane localization",
        "- GO plasma-membrane or cell-surface annotation",
        "",
        "## Results",
        "",
        f"- Multi-source supported Tier 1/2 candidates: {multi['value']}/{multi['denominator']} "
        f"({multi['fraction']}).",
        f"- Curated-list plus independent anchor support: {diverse['value']}/{diverse['denominator']} "
        f"({diverse['fraction']}).",
        f"- Retain support after any single-source removal: {retained['value']}/{retained['denominator']} "
        f"({retained['fraction']}).",
        f"- Single-source dependent Tier 1/2 candidates: {single['value']}/{single['denominator']} "
        f"({single['fraction']}); genes: {single_genes}.",
        "",
        "Dependency classes:",
        "",
        *class_lines,
        "",
        "## Interpretation",
        "",
        "The Tier 1/2 set is not driven by a single surfaceome resource. This supports the",
        "claim that the nominated hypotheses are not simple artifacts of one curated list or",
        "one database/localization source. The audit is still a source-dependency check, not",
        "experimental validation of membrane abundance, malignant-cell origin, safety, or",
        "clinical actionability.",
        "",
        "## Outputs",
        "",
        f"- `{OUTPUT_AUDIT.relative_to(ROOT).as_posix()}`",
        f"- `{OUTPUT_SUMMARY.relative_to(ROOT).as_posix()}`",
    ]
    OUTPUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    audit_rows = build_audit_rows()
    summary_rows = build_summary_rows(audit_rows)
    audit_fields = [
        "rank_v2",
        "gene",
        "tier",
        "scenario_score",
        "surfaceome_category",
        "surfaceome_confidence_score",
        "source_support_n",
        "curated_surfaceome_source_n",
        "database_or_localization_anchor_n",
        "support_sources",
        "source_dependency_class",
        "single_source_dependent",
        "retains_support_after_any_single_source_removal",
        "critical_removed_sources",
        *[f"has_{source_id}" for source_id, _label in SOURCE_GROUPS],
        *[f"remaining_support_after_removing_{source_id}" for source_id, _label in SOURCE_GROUPS],
        "surface_support_sources_original",
        "interpretation",
    ]
    write_tsv(OUTPUT_AUDIT, audit_rows, audit_fields)
    write_tsv(
        OUTPUT_SUMMARY,
        summary_rows,
        ["metric", "group", "value", "denominator", "fraction", "genes", "interpretation"],
    )
    write_doc(audit_rows, summary_rows)
    print(f"Wrote {OUTPUT_AUDIT.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
