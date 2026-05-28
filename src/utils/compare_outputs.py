"""Minimal reproducibility helper for the bootstrap stage."""

from __future__ import annotations

import argparse
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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_bootstrap(root: Path) -> list[str]:
    return [path for path in REQUIRED_BOOTSTRAP_FILES if not (root / path).exists()]


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

    if args.write_bootstrap_status:
        write_bootstrap_status(Path(args.write_bootstrap_status), root)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
