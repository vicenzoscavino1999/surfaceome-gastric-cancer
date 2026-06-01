from __future__ import annotations

import argparse
import csv
import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "release" / "reproducibility_audit_report.md"
AUDIT_LOG = ROOT / "release" / "reproducibility_audit_log.tsv"
KEY_PACKAGES = [
    "matplotlib",
    "numpy",
    "openpyxl",
    "pandas",
    "pyreadr",
    "PyMuPDF",
    "PyYAML",
    "requests",
    "scikit-learn",
    "scipy",
    "pytest",
    "snakemake",
]


def run_capture(command: list[str], check: bool = False) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed with exit code {result.returncode}\n{result.stdout}")
    return result.returncode, result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_versions() -> list[str]:
    rows = []
    for package in KEY_PACKAGES:
        try:
            rows.append(f"- {package}: `{metadata.version(package)}`")
        except metadata.PackageNotFoundError:
            rows.append(f"- {package}: `not installed`")
    return rows


def raw_data_summary() -> tuple[int, int]:
    raw_root = ROOT / "data" / "raw"
    files = [p for p in raw_root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def read_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def audit_log_rows() -> list[str]:
    if not AUDIT_LOG.exists():
        return ["No manual clean-directory/container audit log is present."]
    with AUDIT_LOG.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        return ["Audit log is present but empty."]
    lines = [
        "| Date | Audit | Status | Key result |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {date} | `{audit}` | `{status}` | {result} |".format(
                date=row.get("date_utc", ""),
                audit=row.get("audit_id", ""),
                status=row.get("status", ""),
                result=row.get("key_result", "").replace("|", "\\|"),
            )
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the release-candidate reproducibility audit report.")
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Only summarize the current environment and repository state; do not rerun checks.",
    )
    args = parser.parse_args()

    audit_status = "not_run"
    audit_output = ""
    if not args.skip_checks:
        code, audit_output = run_capture([sys.executable, "scripts/run_reproducibility_checks.py"])
        audit_status = "pass" if code == 0 else f"fail_exit_{code}"

    summary_code, summary_output = run_capture([sys.executable, "-m", "snakemake", "--summary"])
    dry_run_code, dry_run_output = run_capture([sys.executable, "-m", "snakemake", "-n", "--cores", "1"])
    docker_code, docker_version = run_capture(["docker", "--version"])

    ranking = ROOT / "results" / "rankings" / "ranking_v2_frozen.tsv"
    ranking_metadata = ROOT / "results" / "rankings" / "ranking_v2_frozen.metadata.yaml"
    ranking_hash = sha256(ranking) if ranking.exists() else "missing"
    ranking_metadata_hash = sha256(ranking_metadata) if ranking_metadata.exists() else "missing"
    ranking_metadata_payload = read_yaml(ranking_metadata) if ranking_metadata.exists() else {}
    raw_count, raw_bytes = raw_data_summary()
    raw_gb = raw_bytes / (1024**3)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Reproducibility Audit Report",
        "",
        f"Generated: {now}",
        "",
        "## Scope",
        "",
        "This report audits the current release-candidate workspace. It does not change scores,",
        "weights, universe membership, rankings, tiers, or manuscript figures.",
        "",
        "## Environment",
        "",
        f"- Python: `{sys.version.split()[0]}`",
        f"- Platform: `{platform.platform()}`",
        f"- Docker: `{docker_version if docker_code == 0 else 'not available'}`",
        "",
        "### Key Package Versions",
        "",
        *package_versions(),
        "",
        "## Repository State",
        "",
        "- Exact release tree: defined by the clean Git commit or tag that contains this report.",
        "- The literal release commit hash is not embedded in this tracked report because doing so would make the report self-referential.",
        "- Verify the release tree after checkout with `git status --short`; it should return no tracked changes.",
        "",
        "## Data Footprint",
        "",
        f"- Retained raw/source files: `{raw_count}`",
        f"- Retained raw/source size: `{raw_bytes}` bytes (`{raw_gb:.3f}` GiB)",
        "",
        "## Frozen Ranking",
        "",
        "- Active ranking: `results/rankings/ranking_v2_frozen.tsv`",
        f"- Active ranking SHA256: `{ranking_hash}`",
        "- Active ranking sidecar: `results/rankings/ranking_v2_frozen.metadata.yaml`",
        f"- Active ranking sidecar SHA256: `{ranking_metadata_hash}`",
        f"- Sidecar-recorded ranking SHA256: `{ranking_metadata_payload.get('ranking_sha256', 'missing')}`",
        "",
        "## Automated Audit",
        "",
        f"- `scripts/run_reproducibility_checks.py`: `{audit_status}`",
        f"- `python -m snakemake --summary`: exit `{summary_code}`",
        f"- `python -m snakemake -n --cores 1`: exit `{dry_run_code}`",
        "",
        "### Clean/Container Audit Log",
        "",
        *audit_log_rows(),
        "",
        "### Snakemake Dry Run Output",
        "",
        "```text",
        dry_run_output,
        "```",
        "",
        "### Snakemake Summary Output",
        "",
        "```text",
        summary_output[:12000],
        "```",
        "",
        "## Remaining Release Blockers",
        "",
        "- Public repository URL is still required.",
        "- Archival DOI is still required and must cover frozen inputs or an equivalent checksum/provenance data package.",
        "- A clean clone or clean directory audit should be repeated after the release candidate is frozen.",
        "- Docker build/run should be repeated on the final public release package.",
        "- Manual GitHub Actions release-audit jobs should be repeated when the final frozen data bundle is available to the runner.",
        "- Manuscript and cover letter still need the final repository URL and archival DOI.",
    ]

    if audit_output:
        lines.extend(
            [
                "",
                "### Reproducibility Check Output",
                "",
                "```text",
                audit_output[-12000:],
                "```",
            ]
        )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")
    if audit_status.startswith("fail") or summary_code != 0 or dry_run_code != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
