from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_CURATION = ROOT / "data" / "raw" / "manual_curation"
TABLES = ROOT / "results" / "tables"
DOCS = ROOT / "docs"
RANKING = ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"

CURATED_TABLES = {
    "tier_assignments.tsv": TABLES / "tier_assignments.tsv",
    "manual_curation_notes.tsv": TABLES / "manual_curation_notes.tsv",
    "top20_candidate_cards.md": TABLES / "top20_candidate_cards.md",
    "excluded_with_reason.tsv": TABLES / "excluded_with_reason.tsv",
    "wang2026_crosscheck.tsv": TABLES / "wang2026_crosscheck.tsv",
}

CURATED_DOCS = {
    "fase15_tiering_and_curation.md": DOCS / "fase15_tiering_and_curation.md",
    "fase15_post_curation_verification.md": DOCS / "fase15_post_curation_verification.md",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def copy_curated_inputs() -> None:
    for source_name, target in {**CURATED_TABLES, **CURATED_DOCS}.items():
        source = RAW_CURATION / source_name
        if not source.exists():
            raise FileNotFoundError(f"Missing frozen Fase 15 input: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def validate_tier_assignments() -> None:
    ranking_rows = read_tsv(RANKING)
    tier_rows = read_tsv(TABLES / "tier_assignments.tsv")
    if len(tier_rows) != 30:
        raise ValueError(f"Expected 30 tier-assignment rows, observed {len(tier_rows)}")

    top30_by_gene = {
        row["hgnc_symbol"]: row
        for row in ranking_rows[:30]
    }
    missing_from_top30 = sorted(row["gene"] for row in tier_rows if row["gene"] not in top30_by_gene)
    if missing_from_top30:
        raise ValueError("Fase 15 curation freeze no longer matches ranking top30: " + ",".join(missing_from_top30))

    rank_mismatches = []
    for row in tier_rows:
        expected_rank = top30_by_gene[row["gene"]]["rank"]
        if row["rank_v2"] != expected_rank:
            rank_mismatches.append(f"{row['gene']} expected {expected_rank} observed {row['rank_v2']}")
    if rank_mismatches:
        raise ValueError("Fase 15 rank mismatch: " + "; ".join(rank_mismatches[:10]))

    counts: dict[str, int] = {}
    for row in tier_rows:
        counts[row["tier"]] = counts.get(row["tier"], 0) + 1
    if counts != {"Tier 1": 6, "Tier 2": 12, "Watchlist": 12}:
        raise ValueError(f"Unexpected tier distribution: {counts}")

    tier1 = {row["gene"] for row in tier_rows if row["tier"] == "Tier 1"}
    expected_tier1 = {"ITGB4", "CDH3", "NECTIN2", "CEACAM5", "JAG1", "EPCAM"}
    if tier1 != expected_tier1:
        raise ValueError("Tier 1 set mismatch: " + ",".join(sorted(tier1)))


def validate_manual_curation() -> None:
    notes = read_tsv(TABLES / "manual_curation_notes.tsv")
    if len(notes) != 30:
        raise ValueError(f"Expected 30 manual-curation rows, observed {len(notes)}")
    score_changes = [row["gene"] for row in notes if row.get("changes_score") != "no"]
    if score_changes:
        raise ValueError("Manual curation must not change scores: " + ",".join(score_changes))

    wang_rows = read_tsv(TABLES / "wang2026_crosscheck.tsv")
    tier12_rows = [row for row in wang_rows if row.get("our_tier") in {"Tier 1", "Tier 2"}]
    absent = {row["our_gene"] for row in tier12_rows if row.get("in_wang_drug_target_table") != "yes"}
    overlap = [row for row in tier12_rows if row.get("in_wang_drug_target_table") == "yes"]
    if len(tier12_rows) != 18 or len(overlap) != 16 or absent != {"CD9", "LSR"}:
        raise ValueError("Unexpected Wang 2026 cross-check summary")


def validate_docs() -> None:
    tier_note = (DOCS / "fase15_tiering_and_curation.md").read_text(encoding="utf-8", errors="replace")
    post_note = (DOCS / "fase15_post_curation_verification.md").read_text(encoding="utf-8", errors="replace")
    required_tier_text = [
        "Fase 15 complete",
        "Tier 1 (6)",
        "Tier 2 (12)",
        "Watchlist (12)",
        "no score, weight, universe, or frozen ranking was changed",
    ]
    required_post_text = [
        "RESOLVED (2026-05-31)",
        "16/18 of our Tier 1+Tier 2",
        "Wang Figure 7H",
        "CLOSED as partially resolved",
        "NECTIN2 is the Tier 1 member closest to the compartment",
    ]
    for text in required_tier_text:
        if text not in tier_note:
            raise ValueError(f"Fase 15 tiering note missing: {text}")
    for text in required_post_text:
        if text not in post_note:
            raise ValueError(f"Fase 15 post-curation note missing: {text}")


def main() -> int:
    copy_curated_inputs()
    validate_tier_assignments()
    validate_manual_curation()
    validate_docs()
    print("Materialized frozen Fase 15 curation and tiering artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
