"""Check whether the frozen release data bundle is present."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import compare_outputs as gates

FROZEN_SMALL_INPUTS = [
    "data/raw/frozen_snapshots/phase1_inventory/coverage_matrix.tsv",
    "data/raw/frozen_snapshots/phase1_inventory/dataset_inventory.tsv",
    "data/raw/frozen_snapshots/phase1_inventory/fase1_data_inventory.md",
    "data/raw/frozen_snapshots/phase1_inventory/sample_counts.tsv",
    "data/raw/frozen_snapshots/ranking_v0_frozen.tsv",
    "data/raw/frozen_snapshots/ranking_v1_frozen.tsv",
    "data/raw/manual_curation/excluded_with_reason.tsv",
    "data/raw/manual_curation/fase15_post_curation_verification.md",
    "data/raw/manual_curation/fase15_tiering_and_curation.md",
    "data/raw/manual_curation/manual_curation_notes.tsv",
    "data/raw/manual_curation/tier_assignments.tsv",
    "data/raw/manual_curation/top20_candidate_cards.md",
    "data/raw/manual_curation/wang2026_crosscheck.tsv",
]

API_OR_MANUAL_RAW_INPUTS = [
    "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json",
    "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json",
    "data/raw/gdc_tcga_stad/cases_tcga_stad.json",
    "data/raw/gdc_tcga_stad/files_tcga_stad_rnaseq_star_counts.json",
    "data/raw/tisch2/STAD_GSE134520/STAD_GSE134520_Expression.zip",
    "data/raw/tisch2/STAD_GSE134520/STAD_GSE134520_CellMetainfo_table.tsv",
    "data/raw/tisch2/STAD_GSE167297/STAD_GSE167297_Expression.zip",
    "data/raw/tisch2/STAD_GSE167297/STAD_GSE167297_CellMetainfo_table.tsv",
    "data/raw/wang2026/mmc8.xlsx",
]

OTHER_FULL_RAW_INPUTS = [
    "data/raw/hgnc/hgnc_complete_set.txt",
    "data/raw/tcga_purity/tidyestimate_1.1.1.tar.gz",
    "data/raw/tcga_purity/tidyestimate/data/gene_sets.rda",
    "data/raw/uniprot/uniprot_reviewed_human_features.tsv.gz",
]

CHECKSUM_MANIFESTS = [
    "data/checksums/cbioportal_sha256.tsv",
    "data/checksums/gdc_tcga_stad_sha256.tsv",
    "data/checksums/hgnc_sha256.tsv",
    "data/checksums/hpa_sha256.tsv",
    "data/checksums/sha256sums.txt",
    "data/checksums/surfaceome_sources_sha256.tsv",
    "data/checksums/tcga_purity_sha256.tsv",
    "data/checksums/tisch2_candidate_scrna_sha256.tsv",
    "data/checksums/uniprot_phase9_features_sha256.tsv",
    "data/checksums/uniprot_sha256.tsv",
    "data/checksums/wang2026_mmc8_sha256.tsv",
    "data/checksums/xena_toil_sha256.tsv",
]

CI_SMALL_FILES = sorted(
    set(gates.REQUIRED_BOOTSTRAP_FILES + gates.REQUIRED_PHASE1_FILES + FROZEN_SMALL_INPUTS)
)

FULL_RELEASE_FILES = sorted(
    set(
        gates.REQUIRED_PHASE2_RAW_FILES
        + gates.REQUIRED_PHASE4_RAW_FILES
        + API_OR_MANUAL_RAW_INPUTS
        + OTHER_FULL_RAW_INPUTS
        + FROZEN_SMALL_INPUTS
        + CHECKSUM_MANIFESTS
    )
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 8), b""):
            digest.update(chunk)
    return digest.hexdigest()


def missing_files(paths: list[str]) -> list[str]:
    return [path for path in paths if not (ROOT / path).exists()]


def checksum_entries(manifest: Path) -> list[tuple[str, str]]:
    if manifest.name == "sha256sums.txt":
        entries: list[tuple[str, str]] = []
        with manifest.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                checksum, rel_path = stripped.split(maxsplit=1)
                entries.append((rel_path.strip(), checksum.strip()))
        return entries

    with manifest.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "local_path" not in reader.fieldnames or "sha256" not in reader.fieldnames:
            return []
        return [
            (row["local_path"], row["sha256"])
            for row in reader
            if row.get("local_path") and row.get("sha256")
        ]


def verify_checksums(manifests: list[str]) -> list[str]:
    failures: list[str] = []
    for rel_manifest in manifests:
        manifest = ROOT / rel_manifest
        if not manifest.exists():
            failures.append(f"missing checksum manifest: {rel_manifest}")
            continue
        for rel_path, expected in checksum_entries(manifest):
            path = ROOT / rel_path
            if not path.exists():
                failures.append(f"{rel_manifest} references missing file: {rel_path}")
                continue
            actual = sha256_file(path)
            if actual != expected:
                failures.append(f"checksum mismatch in {rel_manifest}: {rel_path}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["ci-small", "full"], default="ci-small")
    parser.add_argument("--verify-checksums", action="store_true")
    args = parser.parse_args()

    required = CI_SMALL_FILES if args.mode == "ci-small" else FULL_RELEASE_FILES
    failures = missing_files(required)
    if args.verify_checksums:
        failures.extend(verify_checksums(CHECKSUM_MANIFESTS))

    if failures:
        print(f"Release input check failed for mode={args.mode}:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Release input check passed for mode={args.mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
