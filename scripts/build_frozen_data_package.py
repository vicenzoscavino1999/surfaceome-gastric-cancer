from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "release" / "archive"
FIXED_ZIP_TIME = (2026, 6, 1, 0, 0, 0)
CHUNK_SIZE = 1024 * 1024 * 8

SUPPORT_FILES = [
    "README.md",
    "REPRODUCIBILITY.md",
    "DATA_AVAILABILITY.md",
    "CITATION.cff",
    "LICENSE",
    "config/datasets.yaml",
    "config/release_manifest.yaml",
    "docs/provenance_log.tsv",
    "docs/source_acquisition_policy.md",
    "docs/reproducibility_reviewer_guide.md",
    "release/reproducibility_audit_report.md",
    "release/reproducibility_audit_log.tsv",
]

RAW_ROOTS = [
    "data/raw",
    "data/checksums",
]


def run_git(args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_tag(tag: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", tag)


def planned_release_tag() -> str | None:
    manifest = ROOT / "config" / "release_manifest.yaml"
    if not manifest.exists():
        return None
    pattern = re.compile(r"planned_release_candidate_tag:\s*[\"']?([^\"'\s]+)")
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def resolve_code_tag(tag_arg: str | None) -> tuple[str, str]:
    tag = tag_arg
    if not tag:
        exact = run_git(["describe", "--tags", "--exact-match", "HEAD"], check=False)
        tag = exact or planned_release_tag()
    if not tag:
        raise SystemExit(
            "Could not infer a release tag. Pass --code-tag, or run from an exact tag."
        )
    commit = run_git(["rev-list", "-n", "1", tag])
    return tag, commit


def git_status_text() -> str:
    return run_git(["status", "--porcelain=v1"], check=True)


def collect_files() -> list[Path]:
    paths: set[Path] = set()
    for root_rel in RAW_ROOTS:
        root = ROOT / root_rel
        if not root.exists():
            raise FileNotFoundError(f"Missing required package root: {root_rel}")
        for path in root.rglob("*"):
            if path.is_file():
                paths.add(path)
    for rel in SUPPORT_FILES:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(f"Missing required support file: {rel}")
        paths.add(path)
    return sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix())


def write_bytes_to_zip(
    archive: zipfile.ZipFile,
    arcname: str,
    content: bytes,
    compression: int,
) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = compression
    info.external_attr = 0o644 << 16
    archive.writestr(info, content)


def write_file_to_zip(
    archive: zipfile.ZipFile,
    source: Path,
    arcname: str,
    compression: int,
) -> None:
    info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
    info.compress_type = compression
    info.external_attr = 0o644 << 16
    with source.open("rb") as src, archive.open(info, "w", force_zip64=True) as dst:
        shutil.copyfileobj(src, dst, CHUNK_SIZE)


def zenodo_metadata(code_tag: str, code_commit: str, archive_name: str) -> dict:
    version = code_tag[1:] if code_tag.startswith("v") else code_tag
    release_url = (
        "https://github.com/vicenzoscavino1999/"
        f"surfaceome-gastric-cancer/releases/tag/{code_tag}"
    )
    description = f"""
<p>Frozen reproducibility data package for the gastric cancer surfaceome target-prioritization workflow.</p>
<p>This archive contains the retained <code>data/raw/</code> inputs, checksum manifests,
source-acquisition provenance, release manifest, and reviewer-facing reproducibility documentation
needed to recompute the analysis from frozen raw/source files with the companion code release
<code>{code_tag}</code> ({code_commit}).</p>
<p>The package is intended for reproducibility, not for relicensing upstream resources. Original
source licenses, access terms, and citation requirements remain with TCGA/GDC, UCSC Xena/Toil,
Human Protein Atlas, UniProt, HGNC, cBioPortal, TISCH2/GEO, TCSA/CSPA/SURFY, Wang 2026, and
other upstream providers as documented in <code>DATA_AVAILABILITY.md</code>,
<code>docs/provenance_log.tsv</code>, and <code>docs/source_acquisition_policy.md</code>.</p>
""".strip()
    return {
        "metadata": {
            "title": (
                "Surfaceome-guided target prioritization in gastric adenocarcinoma: "
                f"frozen reproducibility data package {code_tag}"
            ),
            "upload_type": "dataset",
            "description": description,
            "creators": [
                {
                    "name": "Scavino Alfaro, Vicenzo",
                    "affiliation": "Independent Researcher, Lima, Peru",
                    "orcid": "0009-0000-2472-9785",
                }
            ],
            "version": version,
            "access_right": "open",
            "license": "other-open",
            "keywords": [
                "bioinformatics",
                "gastric adenocarcinoma",
                "surfaceome",
                "target prioritization",
                "reproducibility",
                "frozen raw data",
            ],
            "related_identifiers": [
                {
                    "identifier": release_url,
                    "relation": "isSupplementTo",
                    "scheme": "url",
                    "resource_type": "software",
                }
            ],
            "notes": (
                f"Primary file: {archive_name}. This data package should be cited together "
                f"with the companion code release {release_url}."
            ),
        }
    }


def readme_text(
    *,
    package_id: str,
    code_tag: str,
    code_commit: str,
    generator_commit: str,
    generated_at: str,
) -> str:
    return f"""# Frozen Reproducibility Data Package

Package: `{package_id}`

Generated UTC: `{generated_at}`

Companion code release:

- Repository: `https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer`
- Tag: `{code_tag}`
- Commit: `{code_commit}`

Package generated from local checkout commit: `{generator_commit}`

## Contents

This archive contains the frozen raw/source inputs and reproducibility metadata needed to
recompute the analysis from `data/raw/` with the companion code release:

- `data/raw/`
- `data/checksums/`
- `config/release_manifest.yaml`
- `config/datasets.yaml`
- `docs/provenance_log.tsv`
- `docs/source_acquisition_policy.md`
- `docs/reproducibility_reviewer_guide.md`
- `DATA_AVAILABILITY.md`
- `REPRODUCIBILITY.md`
- `release/reproducibility_audit_report.md`
- `SHA256SUMS.txt`
- `package_manifest.json`
- `ZENODO_METADATA.json`

This is a frozen-input package. It does not claim that all external sources can be
redownloaded byte-for-byte from live APIs after release.

## Check The Package

After extracting the ZIP, enter the extracted package directory and verify file hashes:

```powershell
Get-FileHash -Algorithm SHA256 .\\SHA256SUMS.txt
```

For full content verification, compare every path in `SHA256SUMS.txt` against the extracted
files. The companion code repository also includes `scripts/check_release_inputs.py`, which
verifies the expected release inputs when `data/raw/` and `data/checksums/` are restored into
a code checkout.

## Recompute From Frozen Raw

```powershell
git clone https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer.git
cd surfaceome-gastric-cancer
git checkout {code_tag}

# Copy the extracted data/raw and data/checksums directories into this checkout.
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-manuscript.txt
python scripts/check_release_inputs.py --mode full --verify-checksums
python -m snakemake --cores 1
python scripts/run_reproducibility_checks.py
```

## Redistribution Note

The package is provided for reproducibility of a public-data bioinformatics analysis.
Upstream resources retain their original licenses, terms, and citation requirements. See
`DATA_AVAILABILITY.md`, `docs/provenance_log.tsv`, and `docs/source_acquisition_policy.md`.
"""


def build_package(args: argparse.Namespace) -> None:
    status = git_status_text()
    if status and not args.allow_dirty:
        raise SystemExit(
            "Refusing to build from a dirty worktree. Commit/stash changes or pass --allow-dirty."
        )

    code_tag, code_commit = resolve_code_tag(args.code_tag)
    generator_commit = run_git(["rev-parse", "HEAD"])
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    package_id = args.package_id or (
        f"surfaceome_gastric_cancer_{sanitize_tag(code_tag)}_frozen_data_package"
    )
    archive_dir = Path(args.output_dir).resolve()
    archive_dir.mkdir(parents=True, exist_ok=True)
    zip_path = archive_dir / f"{package_id}.zip"
    sha_path = archive_dir / f"{package_id}.zip.sha256"
    metadata_path = archive_dir / f"{package_id}.zenodo_metadata.json"
    manifest_path = archive_dir / f"{package_id}.package_manifest.json"

    compression = zipfile.ZIP_STORED if args.compression == "stored" else zipfile.ZIP_DEFLATED
    files = collect_files()
    entries = []
    for source in files:
        rel = source.relative_to(ROOT).as_posix()
        entries.append(
            {
                "path": rel,
                "size_bytes": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )

    checksum_lines = [
        f"{entry['sha256']}  {entry['path']}" for entry in sorted(entries, key=lambda row: row["path"])
    ]
    checksum_text = "\n".join(checksum_lines) + "\n"
    metadata = zenodo_metadata(code_tag, code_commit, zip_path.name)
    manifest = {
        "package_id": package_id,
        "generated_at_utc": generated_at,
        "companion_code": {
            "repository": "https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer",
            "tag": code_tag,
            "commit": code_commit,
        },
        "generator": {
            "commit": generator_commit,
            "worktree_status": "dirty" if status else "clean",
        },
        "compression": args.compression,
        "file_count": len(entries),
        "total_size_bytes": sum(entry["size_bytes"] for entry in entries),
        "files": entries,
    }
    readme = readme_text(
        package_id=package_id,
        code_tag=code_tag,
        code_commit=code_commit,
        generator_commit=generator_commit,
        generated_at=generated_at,
    )

    if zip_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing archive: {zip_path}")

    with zipfile.ZipFile(zip_path, "w", allowZip64=True) as archive:
        for entry in entries:
            rel = entry["path"]
            write_file_to_zip(
                archive,
                ROOT / rel,
                f"{package_id}/{rel}",
                compression,
            )
        generated_files = {
            "README_DATA_PACKAGE.md": readme,
            "SHA256SUMS.txt": checksum_text,
            "package_manifest.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            "ZENODO_METADATA.json": json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        }
        for rel, text in generated_files.items():
            write_bytes_to_zip(
                archive,
                f"{package_id}/{rel}",
                text.encode("utf-8"),
                compression,
            )

    zip_sha = sha256_file(zip_path)
    sha_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["archive"] = {
        "filename": zip_path.name,
        "size_bytes": zip_path.stat().st_size,
        "sha256": zip_sha,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Built archive: {zip_path}")
    print(f"Archive SHA256: {zip_sha}")
    print(f"Zenodo metadata: {metadata_path}")
    print(f"Package manifest: {manifest_path}")
    print(f"Archive checksum file: {sha_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the frozen raw/source data package for Zenodo deposition."
    )
    parser.add_argument("--code-tag", help="Companion code tag to cite, e.g. v0.1.0-rc3.")
    parser.add_argument("--package-id", help="Override the archive root/package identifier.")
    parser.add_argument(
        "--output-dir",
        default=str(ARCHIVE_DIR),
        help="Directory for generated archive artifacts.",
    )
    parser.add_argument(
        "--compression",
        choices=["stored", "deflated"],
        default="stored",
        help="ZIP compression mode. stored is faster and deterministic.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing archive outputs.")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow building when tracked files are modified or untracked.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    build_package(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
