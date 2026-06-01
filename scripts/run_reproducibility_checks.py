from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

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


def run(label: str, command: list[str], cwd: Path = ROOT) -> None:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def powershell_command() -> str:
    for name in ("pwsh", "powershell"):
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("PowerShell was not found; cannot run build_latex.ps1")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the reviewer-facing reproducibility checks for the CBC manuscript package."
    )
    parser.add_argument(
        "--include-latex",
        action="store_true",
        help="Also regenerate the Elsevier LaTeX source, compile the PDF, and rebuild the flat package.",
    )
    args = parser.parse_args()

    run("unit tests", [sys.executable, "-m", "pytest", "-q"])

    for check in PHASE_CHECKS:
        run(f"artifact check {check}", [sys.executable, "src/utils/compare_outputs.py", check])

    run("phase 17 manuscript check", [sys.executable, "scripts/check_phase17_manuscript_brief.py"])
    run(
        "publication figure export check",
        [sys.executable, "scripts/export_phase17_publication_figures.py", "--check"],
    )
    run("snakemake dry run", [sys.executable, "-m", "snakemake", "-n", "--cores", "1"])

    if args.include_latex:
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


if __name__ == "__main__":
    raise SystemExit(main())
