from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]

# Full reviewer audit: every phase artifact check, run when the frozen raw bundle
# and the regenerated intermediates are present (author workspace, or a clone with
# the Zenodo data package extracted into data/raw/ after a pipeline run).
PHASE_CHECKS = [
    "--self-test",
    "--check-phase1-inventory",
    "--check-phase2-downloads",
    "--check-phase2-batch-diagnostic",
    "--check-phase3-identifier-map",
    "--check-phase4-surfaceome-universe",
    "--check-phase4b-ranking-resolution",
    "--check-phase5-tumor-expression",
    "--check-phase6-normal-selectivity",
    "--check-phase7-protein-evidence",
    "--check-phase8-single-cell-tme",
    "--check-phase9-topology-isoforms",
    "--check-phase13-mvp-scoring",
    "--check-phase14-preflight",
    "--check-phase14-stability",
    "--check-phase15-tiering",
    "--check-phase16-figures-tables",
]

# Subset that validates only artifacts shipped in a bare git clone (no data/raw/,
# no regenerated data/processed or results/figures, which are gitignored by design).
# Determined empirically; keep in sync if tracked artifacts change.
SMOKE_PHASE_CHECKS = [
    "--self-test",
    "--check-phase1-inventory",
    "--check-phase2-batch-diagnostic",
    "--check-phase3-identifier-map",
    "--check-phase6-normal-selectivity",
    "--check-phase7-protein-evidence",
]

ZENODO_DOI = "10.5281/zenodo.20498705"


def run(label: str, command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(command), flush=True)
    merged_env = None
    if env:
        merged_env = os.environ.copy()
        merged_env.update(env)
    subprocess.run(command, cwd=cwd, check=True, env=merged_env)


def powershell_command() -> str:
    for name in ("pwsh", "powershell"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("PowerShell was not found; cannot run build_latex.ps1")


def frozen_raw_present() -> bool:
    """True when the full frozen release bundle (including the large data/raw inputs) is present."""
    result = subprocess.run(
        [sys.executable, "scripts/check_release_inputs.py", "--mode", "full"],
        cwd=ROOT,
        capture_output=True,
    )
    return result.returncode == 0


def verify_frozen_ranking_hash() -> None:
    """Verify the headline frozen ranking matches its declared SHA256 (works from a bare clone)."""
    print("\n== frozen ranking hash ==", flush=True)
    sidecar = ROOT / "results/rankings/ranking_v2_frozen.metadata.yaml"
    meta = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    ranking = ROOT / meta["ranking_file"]
    expected = str(meta["ranking_sha256"])
    actual = hashlib.sha256(ranking.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(
            f"Frozen ranking hash mismatch for {meta['ranking_file']}: {actual} != {expected}"
        )
    print(f"{meta['ranking_file']} sha256={expected} OK", flush=True)


def run_smoke_audit() -> int:
    print("=" * 78)
    print("NO-RAW SMOKE AUDIT")
    print(
        "The large data/raw/ inputs are not present, so this runs the bare-clone subset\n"
        "only. It validates repository wiring, the frozen ranking hash, the no-data unit\n"
        "tests, and the phase checks whose artifacts ship in the repository.\n"
        "\n"
        "For the FULL reviewer audit, reproduce the data first:\n"
        f"  1. Download the frozen data package (DOI {ZENODO_DOI}) and extract it so that\n"
        "     data/raw/ is populated.\n"
        "  2. python -m snakemake --cores 1        # regenerate processed/results from raw\n"
        "  3. python scripts/run_reproducibility_checks.py   # now runs the full audit"
    )
    print("=" * 78)

    verify_frozen_ranking_hash()
    run("release input wiring (ci-small)", [sys.executable, "scripts/check_release_inputs.py", "--mode", "ci-small"])
    run("unit tests (no-data subset)", [sys.executable, "-m", "pytest", "-q"], env={"SURFACEOME_CI_SMALL": "1"})

    for check in SMOKE_PHASE_CHECKS:
        run(f"artifact check {check}", [sys.executable, "src/utils/compare_outputs.py", check])

    skipped = [c for c in PHASE_CHECKS if c not in SMOKE_PHASE_CHECKS]
    skipped += ["phase 17 manuscript check", "publication figure export check", "snakemake dry run"]
    print("\n== skipped (require frozen raw data and/or a pipeline run) ==")
    for item in skipped:
        print(f"  SKIPPED {item}")

    print("\nNo-raw smoke audit passed. Download the Zenodo data package for the full audit.")
    return 0


def run_full_audit(include_latex: bool) -> int:
    verify_frozen_ranking_hash()
    run("unit tests", [sys.executable, "-m", "pytest", "-q"])

    for check in PHASE_CHECKS:
        run(f"artifact check {check}", [sys.executable, "src/utils/compare_outputs.py", check])

    run("phase 17 manuscript check", [sys.executable, "scripts/check_phase17_manuscript_brief.py"])
    run(
        "publication figure export check",
        [sys.executable, "scripts/export_phase17_publication_figures.py", "--check"],
    )
    run("snakemake dry run", [sys.executable, "-m", "snakemake", "-n", "--cores", "1"])

    if include_latex:
        run("generate CBC LaTeX handoff", [sys.executable, "scripts/build_phase17_latex_handoff.py"])
        run(
            "compile CBC LaTeX PDF",
            [
                powershell_command(),
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ROOT / "manuscript" / "latex" / "build_latex.ps1"),
            ],
        )
        run("rebuild flat CBC package", [sys.executable, "scripts/build_cbc_submission_package.py"])

    print("\nAll requested reproducibility checks passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the reviewer-facing reproducibility checks for the CBC manuscript package."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "full", "smoke"],
        default="auto",
        help=(
            "auto (default) runs the full audit when the frozen raw bundle is present and "
            "otherwise a no-raw smoke audit; full and smoke force either path."
        ),
    )
    parser.add_argument(
        "--include-latex",
        action="store_true",
        help="Also regenerate the Elsevier LaTeX source, compile the PDF, and rebuild the flat package.",
    )
    args = parser.parse_args()

    mode = args.mode
    if mode == "auto":
        mode = "full" if frozen_raw_present() else "smoke"

    if mode == "smoke":
        if args.include_latex:
            print("note: --include-latex is ignored in the no-raw smoke audit.", flush=True)
        return run_smoke_audit()
    return run_full_audit(args.include_latex)


if __name__ == "__main__":
    raise SystemExit(main())
