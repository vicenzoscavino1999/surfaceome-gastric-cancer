"""Minimal reproducibility helpers for early execution gates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


REQUIRED_BOOTSTRAP_FILES = [
    "README.md",
    "REPRODUCIBILITY.md",
    "Makefile",
    "config/controls.yaml",
    "config/scoring_scenarios.yaml",
    "config/datasets.yaml",
    "config/parameters.yaml",
    "config/surfaceome_universe_definition.yaml",
    "config/exclusion_criteria.yaml",
    "docs/design_decisions.md",
    "docs/time_tracking.tsv",
    "docs/resource_requirements.md",
    "docs/literature_landscape_and_differentiation.md",
    "docs/deep_research_report_assessment.md",
    "docs/analytical_decisions_registry.md",
    "docs/notebook_to_pipeline_protocol.md",
    "docs/reviewer_attack_surface.md",
    "docs/provenance_log.tsv",
    "workflow/Snakefile",
    "scripts/smoke_test.ps1",
]

REQUIRED_PHASE1_FILES = [
    "docs/fase1_data_inventory.md",
    "results/tables/dataset_inventory.tsv",
    "results/tables/sample_counts.tsv",
    "results/tables/coverage_matrix.tsv",
]

REQUIRED_COVERAGE_LAYERS = {
    "RNA tumor",
    "RNA normal",
    "HPA normal",
    "HPA pathology",
    "UniProt topology",
    "PDB/AlphaFold",
    "DepMap",
    "scRNA",
    "external cohort",
    "clinical/druggability",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_bootstrap(root: Path) -> list[str]:
    return [path for path in REQUIRED_BOOTSTRAP_FILES if not (root / path).exists()]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def check_phase1_inventory(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE1_FILES if not (root / path).exists()]
    if failures:
        return failures

    coverage_rows = read_tsv(root / "results/tables/coverage_matrix.tsv")
    layers = {row["layer"] for row in coverage_rows}
    missing_layers = sorted(REQUIRED_COVERAGE_LAYERS - layers)
    if missing_layers:
        failures.append("coverage_matrix missing layers: " + ",".join(missing_layers))

    sample_rows = read_tsv(root / "results/tables/sample_counts.tsv")
    uniprot_reviewed = [
        row
        for row in sample_rows
        if row.get("source_id") == "uniprot_reviewed_human"
        and row.get("category") == "human_reviewed"
    ]
    if not uniprot_reviewed or int(uniprot_reviewed[0].get("n", "0")) <= 0:
        failures.append("sample_counts has invalid UniProt reviewed human count")

    xena_primary = [
        row
        for row in sample_rows
        if row.get("source_id") == "xena_toil_tcga_gtex"
        and row.get("cohort_or_dataset") == "TCGA-STAD"
        and row.get("category") == "Primary Tumor"
    ]
    if not xena_primary or int(xena_primary[0].get("n", "0")) <= 0:
        failures.append("sample_counts has invalid Xena TCGA-STAD primary tumor count")

    return failures


def write_bootstrap_status(path: Path, root: Path) -> None:
    missing = check_bootstrap(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("check\tstatus\tmessage\n")
        if missing:
            handle.write("bootstrap\tfail\tmissing files: " + ",".join(missing) + "\n")
        else:
            handle.write("bootstrap\tpass\tall required bootstrap files exist\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-phase1-inventory", action="store_true")
    parser.add_argument("--write-bootstrap-status")
    args = parser.parse_args()

    root = repo_root()

    if args.self_test:
        missing = check_bootstrap(root)
        if missing:
            print("Bootstrap check failed. Missing files:")
            for path in missing:
                print(f"- {path}")
            return 1
        print("Bootstrap check passed.")
        return 0

    if args.check_phase1_inventory:
        failures = check_phase1_inventory(root)
        if failures:
            print("Fase 1 inventory check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 1 inventory check passed.")
        return 0

    if args.write_bootstrap_status:
        write_bootstrap_status(Path(args.write_bootstrap_status), root)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
