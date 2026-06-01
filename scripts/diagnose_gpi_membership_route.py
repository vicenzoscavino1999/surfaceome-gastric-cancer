"""Audit whether confirmed GPI evidence changes Phase 4 surfaceome membership."""

from __future__ import annotations

import csv
import gzip
import math
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = REPO_ROOT / "results" / "tables"
DOCS_DIR = REPO_ROOT / "docs"

CORE_PROBABLE = {"core_surfaceome", "probable_surfaceome"}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_tsv_gz(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
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


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def as_int(value: str) -> int:
    text = str(value).strip()
    if not text:
        return 0
    return int(float(text))


def category_for(
    score: int,
    support_count: int,
    has_strong: bool,
    has_anchor: bool,
    secreted_only: bool,
    intracellular_only: bool,
    has_any_support: bool,
    has_tm_or_signal: bool,
) -> str:
    if score >= 6 and support_count >= 3 and has_strong and has_anchor and not secreted_only and not intracellular_only:
        return "core_surfaceome"
    if score >= 5 and support_count >= 4 and has_strong and has_anchor and not secreted_only and not intracellular_only:
        return "probable_surfaceome"
    if has_any_support or has_tm_or_signal:
        return "ambiguous_membrane_or_surface_context"
    return "excluded"


def split_aliases(text: str) -> list[str]:
    if not text:
        return []
    parts: list[str] = []
    for chunk in text.replace(";", "|").split("|"):
        token = chunk.strip()
        if token:
            parts.append(token)
    return parts


def build_symbol_maps(id_rows: list[dict[str, str]]) -> tuple[set[str], dict[str, str], dict[str, str]]:
    symbols = {row["hgnc_symbol"] for row in id_rows if row.get("hgnc_symbol")}
    uniprot_to_symbol: dict[str, str] = {}
    alias_to_symbol: dict[str, str] = {}
    for row in id_rows:
        symbol = row.get("hgnc_symbol", "")
        if not symbol:
            continue
        alias_to_symbol[symbol] = symbol
        for column in ["source_gene_symbol", "alias_symbols", "previous_symbols"]:
            for alias in split_aliases(row.get(column, "")):
                alias_to_symbol.setdefault(alias, symbol)
        primary_accession = row.get("uniprot_accession", "").split("-", 1)[0]
        if primary_accession:
            uniprot_to_symbol[primary_accession] = symbol
        for column in ["uniprot_isoform_id", "alternative_uniprot_accessions"]:
            for accession in split_aliases(row.get(column, "")):
                primary = accession.split("-", 1)[0]
                if primary:
                    uniprot_to_symbol.setdefault(primary, symbol)
    return symbols, uniprot_to_symbol, alias_to_symbol


def resolve_symbols(
    row: dict[str, str],
    symbols: set[str],
    uniprot_to_symbol: dict[str, str],
    alias_to_symbol: dict[str, str],
) -> set[str]:
    entry = row.get("Entry", "").strip()
    if entry in uniprot_to_symbol:
        return {uniprot_to_symbol[entry]}
    gene_names = [token.strip() for token in row.get("Gene Names", "").replace(";", " ").split() if token.strip()]
    for gene_name in gene_names:
        if gene_name in symbols:
            return {gene_name}
        if gene_name in alias_to_symbol:
            return {alias_to_symbol[gene_name]}
    return set()


def gpi_class_from_uniprot(row: dict[str, str]) -> tuple[bool, bool]:
    lipid = row.get("Lipidation", "").lower()
    subcellular = row.get("Subcellular location [CC]", "").lower()
    direct_lipid = "gpi-anchor" in lipid or "gpi anchor" in lipid
    subcellular_only = ("gpi-anchor" in subcellular or "gpi anchor" in subcellular) and not direct_lipid
    return direct_lipid, subcellular_only


def row_state(row: dict[str, str]) -> dict[str, object]:
    in_tcsa = as_bool(row.get("in_tcsa", ""))
    in_cspa = as_bool(row.get("in_cspa", ""))
    in_surfy = as_bool(row.get("in_surfy", ""))
    has_uniprot_ext = as_bool(row.get("uniprot_extracellular_topology", ""))
    has_uniprot_tm = as_bool(row.get("uniprot_transmembrane", ""))
    has_signal = as_bool(row.get("uniprot_signal_peptide", ""))
    has_hpa = as_bool(row.get("hpa_plasma_membrane", ""))
    secreted_only = as_bool(row.get("secreted_only_flag", ""))
    intracellular_only = as_bool(row.get("hpa_intracellular_only_flag", ""))
    support_count = as_int(row.get("surface_support_source_count", "0"))
    score = as_int(row.get("surfaceome_confidence_score", "0"))
    has_anchor = has_uniprot_ext or has_uniprot_tm or has_hpa or in_surfy
    has_strong = in_tcsa or in_cspa or has_uniprot_ext
    return {
        "score": score,
        "support_count": support_count,
        "has_strong": has_strong,
        "has_anchor": has_anchor,
        "secreted_only": secreted_only,
        "intracellular_only": intracellular_only,
        "has_any_support": support_count > 0,
        "has_tm_or_signal": has_uniprot_tm or has_signal,
    }


def simulate_category(row: dict[str, str], gpi_credit: int, gpi_is_strong: bool) -> tuple[int, int, str]:
    state = row_state(row)
    score = int(state["score"]) + gpi_credit
    support_count = int(state["support_count"]) + 1
    has_strong = bool(state["has_strong"]) or gpi_is_strong
    category = category_for(
        score=score,
        support_count=support_count,
        has_strong=has_strong,
        has_anchor=True,
        secreted_only=bool(state["secreted_only"]),
        intracellular_only=bool(state["intracellular_only"]),
        has_any_support=True,
        has_tm_or_signal=bool(state["has_tm_or_signal"]),
    )
    return score, support_count, category


def main() -> int:
    surfaceome_rows = read_tsv(REPO_ROOT / "data" / "processed" / "surfaceome_universe.tsv")
    id_rows = read_tsv(REPO_ROOT / "data" / "processed" / "id_map_master.tsv")
    uniprot_rows = read_tsv_gz(REPO_ROOT / "data" / "raw" / "uniprot" / "uniprot_reviewed_human_features.tsv.gz")

    surfaceome_by_symbol = {row["hgnc_symbol"]: row for row in surfaceome_rows}
    symbols, uniprot_to_symbols, alias_to_symbol = build_symbol_maps(id_rows)

    gpi_by_symbol: dict[str, dict[str, object]] = {}
    for uniprot_row in uniprot_rows:
        direct_lipid, subcellular_only = gpi_class_from_uniprot(uniprot_row)
        if not direct_lipid and not subcellular_only:
            continue
        resolved_symbols = resolve_symbols(uniprot_row, symbols, uniprot_to_symbols, alias_to_symbol)
        for symbol in resolved_symbols:
            evidence = gpi_by_symbol.setdefault(
                symbol,
                {
                    "hgnc_symbol": symbol,
                    "uniprot_accessions": set(),
                    "direct_lipid": False,
                    "subcellular_only": False,
                    "lipidation_examples": [],
                    "subcellular_examples": [],
                },
            )
            evidence["uniprot_accessions"].add(uniprot_row.get("Entry", ""))
            if direct_lipid:
                evidence["direct_lipid"] = True
                if len(evidence["lipidation_examples"]) < 2:
                    evidence["lipidation_examples"].append(uniprot_row.get("Lipidation", ""))
            if subcellular_only:
                evidence["subcellular_only"] = True
                if len(evidence["subcellular_examples"]) < 2:
                    evidence["subcellular_examples"].append(uniprot_row.get("Subcellular location [CC]", ""))

    audit_rows: list[dict[str, object]] = []
    for symbol in sorted(gpi_by_symbol):
        evidence = gpi_by_symbol[symbol]
        row = surfaceome_by_symbol.get(symbol)
        if row is None:
            audit_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "gpi_evidence_class": "confirmed_uniprot_lipid_gpi_anchor"
                    if evidence["direct_lipid"]
                    else "subcellular_gpi_without_lipid_feature",
                    "uniprot_accessions": ";".join(sorted(evidence["uniprot_accessions"])),
                    "in_surfaceome_universe_table": False,
                    "current_category": "not_in_surfaceome_universe_table",
                    "current_core_probable": False,
                    "current_score": "",
                    "current_support_count": "",
                    "current_sources": "",
                    "secreted_only_flag": "",
                    "hpa_intracellular_only_flag": "",
                    "plus1_anchor_score": "",
                    "plus1_anchor_support_count": "",
                    "plus1_anchor_category": "",
                    "plus1_changes_membership": False,
                    "plus2_strong_score": "",
                    "plus2_strong_support_count": "",
                    "plus2_strong_category": "",
                    "plus2_changes_membership": False,
                    "counted_in_confirmed_membership_gate": bool(evidence["direct_lipid"]),
                    "gpi_credit_already_integrated_in_fase4": False,
                    "route_note": "missing_from_surfaceome_universe_table",
                }
            )
            continue

        evidence_class = (
            "confirmed_uniprot_lipid_gpi_anchor"
            if evidence["direct_lipid"]
            else "subcellular_gpi_without_lipid_feature"
        )
        current_category = row.get("surfaceome_category", "")
        current_core_probable = current_category in CORE_PROBABLE
        gpi_already_integrated = evidence["direct_lipid"] and row.get("uniprot_gpi_anchor", "").lower() == "true"
        if gpi_already_integrated:
            plus1_score = plus2_score = row.get("surfaceome_confidence_score", "")
            plus1_support = plus2_support = row.get("surface_support_source_count", "")
            plus1_category = plus2_category = current_category
            plus1_changes = plus2_changes = False
            route_note = (
                "gpi_integrated_current_core_probable"
                if current_core_probable
                else "gpi_integrated_still_outside_core_probable"
            )
        elif evidence["direct_lipid"]:
            plus1_score, plus1_support, plus1_category = simulate_category(row, gpi_credit=1, gpi_is_strong=False)
            plus2_score, plus2_support, plus2_category = simulate_category(row, gpi_credit=2, gpi_is_strong=True)
            plus1_changes = not current_core_probable and plus1_category in CORE_PROBABLE
            plus2_changes = not current_core_probable and plus2_category in CORE_PROBABLE
            route_note = (
                "current_core_probable"
                if current_core_probable
                else "would_enter_with_plus1_anchor"
                if plus1_changes
                else "would_enter_with_plus2_strong_anchor"
                if plus2_changes
                else "membership_invariant_under_tested_gpi_terms"
            )
        else:
            plus1_score = plus1_support = plus2_score = plus2_support = ""
            plus1_category = plus2_category = ""
            plus1_changes = plus2_changes = False
            route_note = "not_counted_in_confirmed_direct_lipid_gate"

        audit_rows.append(
            {
                "hgnc_symbol": symbol,
                "gpi_evidence_class": evidence_class,
                "uniprot_accessions": ";".join(sorted(evidence["uniprot_accessions"])),
                "in_surfaceome_universe_table": True,
                "current_category": current_category,
                "current_core_probable": current_core_probable,
                "current_score": row.get("surfaceome_confidence_score", ""),
                "current_support_count": row.get("surface_support_source_count", ""),
                "current_sources": row.get("surface_support_sources", ""),
                "secreted_only_flag": row.get("secreted_only_flag", ""),
                "hpa_intracellular_only_flag": row.get("hpa_intracellular_only_flag", ""),
                "plus1_anchor_score": plus1_score,
                "plus1_anchor_support_count": plus1_support,
                "plus1_anchor_category": plus1_category,
                "plus1_changes_membership": plus1_changes,
                "plus2_strong_score": plus2_score,
                "plus2_strong_support_count": plus2_support,
                "plus2_strong_category": plus2_category,
                "plus2_changes_membership": plus2_changes,
                "counted_in_confirmed_membership_gate": bool(evidence["direct_lipid"]),
                "gpi_credit_already_integrated_in_fase4": gpi_already_integrated,
                "route_note": route_note,
            }
        )

    audit_fields = [
        "hgnc_symbol",
        "gpi_evidence_class",
        "uniprot_accessions",
        "in_surfaceome_universe_table",
        "current_category",
        "current_core_probable",
        "current_score",
        "current_support_count",
        "current_sources",
        "secreted_only_flag",
        "hpa_intracellular_only_flag",
        "plus1_anchor_score",
        "plus1_anchor_support_count",
        "plus1_anchor_category",
        "plus1_changes_membership",
        "plus2_strong_score",
        "plus2_strong_support_count",
        "plus2_strong_category",
        "plus2_changes_membership",
        "counted_in_confirmed_membership_gate",
        "gpi_credit_already_integrated_in_fase4",
        "route_note",
    ]
    write_tsv(TABLES_DIR / "fase13_gpi_membership_route_audit.tsv", audit_rows, audit_fields)

    confirmed_rows = [row for row in audit_rows if row["gpi_evidence_class"] == "confirmed_uniprot_lipid_gpi_anchor"]
    subcellular_only_rows = [
        row for row in audit_rows if row["gpi_evidence_class"] == "subcellular_gpi_without_lipid_feature"
    ]
    confirmed_current_core = [row for row in confirmed_rows if row["current_core_probable"] is True]
    confirmed_outside = [row for row in confirmed_rows if row["current_core_probable"] is not True]
    confirmed_integrated = [row for row in confirmed_rows if row["gpi_credit_already_integrated_in_fase4"] is True]
    plus1_changers = [row for row in confirmed_rows if row["plus1_changes_membership"] is True]
    plus2_changers = [row for row in confirmed_rows if row["plus2_changes_membership"] is True]
    category_counts = Counter(row["current_category"] for row in confirmed_rows)

    if confirmed_integrated:
        route_decision = "fase4_gpi_evidence_correction_applied"
        route_reason = (
            "Confirmed UniProt lipid GPI anchors are already integrated in the current Fase 4 universe; "
            "this audit is now an idempotence check rather than a pre-correction route simulation."
        )
    elif plus1_changers or plus2_changers:
        route_decision = "reopen_fase4_required_before_gpi_credit"
        route_reason = (
            "At least one confirmed UniProt lipid GPI anchor outside Core+Probable would enter under a tested "
            "additive GPI term; applying GPI only inside Fase 13 would be membership-biased."
        )
    else:
        route_decision = "fase13_gpi_scoring_correction_membership_invariant_available"
        route_reason = (
            "No confirmed UniProt lipid GPI anchor outside Core+Probable enters under either tested additive "
            "GPI term; a Fase 13-only scoring correction would be membership-invariant."
        )

    summary_rows = [
        {
            "metric": "confirmed_uniprot_lipid_gpi_anchor_symbols",
            "value": len(confirmed_rows),
            "route_decision": route_decision,
            "note": "Direct UniProt Lipidation field contains GPI-anchor.",
        },
        {
            "metric": "subcellular_gpi_without_lipid_feature_symbols",
            "value": len(subcellular_only_rows),
            "route_decision": route_decision,
            "note": "Tracked separately and not counted as confirmed direct lipid evidence for the gate.",
        },
        {
            "metric": "confirmed_current_core_probable",
            "value": len(confirmed_current_core),
            "route_decision": route_decision,
            "note": "Confirmed direct GPI genes already admitted to Core+Probable.",
        },
        {
            "metric": "confirmed_outside_core_probable",
            "value": len(confirmed_outside),
            "route_decision": route_decision,
            "note": "Confirmed direct GPI genes not currently in Core+Probable.",
        },
        {
            "metric": "confirmed_gpi_already_integrated_in_fase4",
            "value": len(confirmed_integrated),
            "route_decision": route_decision,
            "note": "Confirmed direct GPI genes whose current surfaceome row already carries uniprot_gpi_anchor=true.",
        },
        {
            "metric": "confirmed_outside_enter_plus1_anchor_support",
            "value": len(plus1_changers),
            "route_decision": route_decision,
            "note": "Simulation: score +1, support +1, anchor true, strong-evidence flag unchanged.",
        },
        {
            "metric": "confirmed_outside_enter_plus2_strong_anchor",
            "value": len(plus2_changers),
            "route_decision": route_decision,
            "note": "Simulation: score +2, support +1, anchor true, strong-evidence flag true.",
        },
        {
            "metric": "route_decision",
            "value": route_decision,
            "route_decision": route_decision,
            "note": route_reason,
        },
    ]
    write_tsv(
        TABLES_DIR / "fase13_gpi_membership_route_summary.tsv",
        summary_rows,
        ["metric", "value", "route_decision", "note"],
    )

    def md_gene_list(rows: list[dict[str, object]], max_rows: int = 25) -> str:
        if not rows:
            return "none"
        ordered = sorted(rows, key=lambda row: str(row["hgnc_symbol"]))
        shown = ordered[:max_rows]
        names = ";".join(str(row["hgnc_symbol"]) for row in shown)
        if len(ordered) > max_rows:
            names += f";...(+{len(ordered) - max_rows} more)"
        return names

    category_summary = ", ".join(f"{category}:{count}" for category, count in sorted(category_counts.items()))
    doc = f"""# Fase 13 GPI Membership Route Audit

## Scope

This diagnostic implements Paso 0.5 of `docs/fase13_gpi_evidence_membership_plan.md`. It does not change Fase 4, component scores, weights, missing-data policy, `ranking_v1_frozen.tsv`, or any downstream ranking.

Confirmed GPI means the UniProt reviewed human `Lipidation` field contains `GPI-anchor`. Subcellular-location-only GPI annotations are tracked separately and are not counted as confirmed direct lipid evidence for the route gate.

## Tested Terms

Two non-final additive simulations were evaluated only to decide membership routing:

1. `plus1_anchor_support`: score +1, support source +1, anchor true, strong-evidence flag unchanged.
2. `plus2_strong_anchor`: score +2, support source +1, anchor true, strong-evidence flag true.

These are route tests, not a selected scoring rule. If either test changes Core+Probable membership for confirmed direct GPI genes, GPI cannot be patched only inside Fase 13.
If the current Fase 4 universe already contains `uniprot_gpi_anchor=true`, the audit does not add another simulated credit and reports an idempotence status instead.

## Counts

- Confirmed UniProt lipid GPI symbols: {len(confirmed_rows)}
- Subcellular-only GPI symbols: {len(subcellular_only_rows)}
- Confirmed GPI already Core+Probable: {len(confirmed_current_core)}
- Confirmed GPI outside Core+Probable: {len(confirmed_outside)}
- Confirmed GPI already integrated in current Fase 4: {len(confirmed_integrated)}
- Confirmed outside entering under plus1 anchor/support: {len(plus1_changers)}
- Confirmed outside entering under plus2 strong-anchor: {len(plus2_changers)}
- Current category distribution among confirmed GPI: {category_summary}

## Route Decision

`{route_decision}`

Reason: {route_reason}

## Membership Changers

- plus1 anchor/support changers: `{md_gene_list(plus1_changers)}`
- plus2 strong-anchor changers: `{md_gene_list(plus2_changers)}`

## Outputs

- `results/tables/fase13_gpi_membership_route_audit.tsv`
- `results/tables/fase13_gpi_membership_route_summary.tsv`
"""
    (DOCS_DIR / "fase13_gpi_membership_route.md").write_text(doc, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
