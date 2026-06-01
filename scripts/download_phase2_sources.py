"""Download Fase 2 MVP raw sources with checksums and provenance.

The script intentionally downloads only the sources needed before first
tumor-normal scoring:

- UCSC Xena/Toil expression matrix and phenotype
- HPA normal/pathology/subcellular/RNA tissue files
- UniProt reviewed human TSV with topology-relevant fields
- GDC TCGA-STAD metadata responses for clinical/biospecimen and STAR counts
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
CHECKSUM_DIR = REPO_ROOT / "data" / "checksums"
RESULTS_DIR = REPO_ROOT / "results" / "tables"
DOCS_DIR = REPO_ROOT / "docs"
CONFIG_DATASETS = REPO_ROOT / "config" / "datasets.yaml"
PROVENANCE_LOG = DOCS_DIR / "provenance_log.tsv"

USER_AGENT = "surfaceome-gastric-cancer-phase2/0.1"

PHASE2_SOURCE_STATUS = {
    "xena_toil_tcga_gtex": "raw_downloaded_with_checksums_batch_diagnostic_pending",
    "hpa_downloads": "raw_downloaded_with_checksums",
    "uniprot_reviewed_human": "raw_downloaded_with_checksums",
    "gdc_tcga_stad": "metadata_raw_downloaded_with_checksums_expression_files_pending",
}


@dataclass(frozen=True)
class UrlDownload:
    source_id: str
    url: str
    local_dir: str
    filename: str
    version_or_release: str
    license_or_terms: str
    notes: str
    large: bool = False

    @property
    def target(self) -> Path:
        return RAW_DIR / self.local_dir / self.filename


URL_DOWNLOADS = [
    UrlDownload(
        source_id="xena_toil_tcga_gtex",
        url="https://toil.xenahubs.net/download/TcgaTargetGTEX_phenotype.txt.gz",
        local_dir="xena_toil",
        filename="TcgaTargetGTEX_phenotype.txt.gz",
        version_or_release="Toil recompute; phenotype Last-Modified Fri, 09 Apr 2021 20:01:15 GMT",
        license_or_terms="UCSC Xena public hub terms",
        notes="Phenotype table used to select TCGA-STAD tumor, TCGA adjacent normal, and GTEx stomach normal samples.",
    ),
    UrlDownload(
        source_id="xena_toil_tcga_gtex",
        url="https://toil.xenahubs.net/download/TcgaTargetGtex_rsem_gene_tpm.gz",
        local_dir="xena_toil",
        filename="TcgaTargetGtex_rsem_gene_tpm.gz",
        version_or_release="Toil recompute; matrix Last-Modified Fri, 09 Apr 2021 20:01:53 GMT",
        license_or_terms="UCSC Xena public hub terms",
        notes="Primary log2(TPM+0.001) matrix for TCGA-STAD vs GTEx stomach analysis.",
        large=True,
    ),
    UrlDownload(
        source_id="hpa_downloads",
        url="https://www.proteinatlas.org/download/tsv/normal_ihc_data.tsv.zip",
        local_dir="hpa",
        filename="normal_ihc_data.tsv.zip",
        version_or_release="HPA 25.1; Ensembl 109",
        license_or_terms="Creative Commons Attribution 4.0 International, with third-party caveats",
        notes="Normal tissue IHC evidence; stomach rows drive normal protein evidence.",
    ),
    UrlDownload(
        source_id="hpa_downloads",
        url="https://www.proteinatlas.org/download/tsv/cancer_data.tsv.zip",
        local_dir="hpa",
        filename="cancer_data.tsv.zip",
        version_or_release="HPA 25.1; Ensembl 109",
        license_or_terms="Creative Commons Attribution 4.0 International, with third-party caveats",
        notes="Cancer pathology IHC evidence; stomach cancer rows drive tumor protein evidence.",
    ),
    UrlDownload(
        source_id="hpa_downloads",
        url="https://www.proteinatlas.org/download/tsv/subcellular_location.tsv.zip",
        local_dir="hpa",
        filename="subcellular_location.tsv.zip",
        version_or_release="HPA 25.1; Ensembl 109",
        license_or_terms="Creative Commons Attribution 4.0 International, with third-party caveats",
        notes="Subcellular localization evidence used to audit surface/plasma membrane support.",
    ),
    UrlDownload(
        source_id="hpa_downloads",
        url="https://www.proteinatlas.org/download/tsv/rna_tissue_consensus.tsv.zip",
        local_dir="hpa",
        filename="rna_tissue_consensus.tsv.zip",
        version_or_release="HPA 25.1; Ensembl 109",
        license_or_terms="Creative Commons Attribution 4.0 International, with third-party caveats",
        notes="HPA consensus RNA tissue expression, including stomach.",
    ),
    UrlDownload(
        source_id="hpa_downloads",
        url="https://www.proteinatlas.org/download/tsv/rna_tissue_gtex.tsv.zip",
        local_dir="hpa",
        filename="rna_tissue_gtex.tsv.zip",
        version_or_release="HPA 25.1; Ensembl 109",
        license_or_terms="Creative Commons Attribution 4.0 International, with third-party caveats",
        notes="HPA GTEx-derived RNA tissue expression, including stomach.",
    ),
    UrlDownload(
        source_id="uniprot_reviewed_human",
        url=(
            "https://rest.uniprot.org/uniprotkb/stream?"
            "compressed=true&format=tsv&"
            "fields=accession,id,gene_names,protein_name,ft_topo_dom,ft_transmem,ft_signal,xref_ensembl&"
            "query=(reviewed:true)%20AND%20(organism_id:9606)"
        ),
        local_dir="uniprot",
        filename="uniprot_reviewed_human_topology.tsv.gz",
        version_or_release="UniProt release 2026_01 observed in Fase 1 metadata query",
        license_or_terms="UniProt terms",
        notes="Reviewed human proteins with topology, transmembrane, signal peptide, and Ensembl mapping fields.",
    ),
]


def request(url: str, method: str = "GET", timeout: int = 120) -> urllib.request.addinfourl:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers, method=method), timeout=timeout)


def fetch_head(url: str, timeout: int) -> dict[str, str]:
    try:
        with request(url, method="HEAD", timeout=timeout) as response:
            return {key.lower(): value for key, value in response.headers.items()}
    except Exception:
        return {}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024 * 8) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def download_url(spec: UrlDownload, force: bool, timeout: int, chunk_size: int) -> dict[str, object]:
    target = spec.target
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = fetch_head(spec.url, timeout=timeout)
    action = "verified_existing_raw"

    if force or not target.exists():
        action = "downloaded_raw"
        part = target.with_name(target.name + ".part")
        if part.exists():
            part.unlink()
        print(f"Downloading {spec.source_id}: {spec.filename}", flush=True)
        started = time.monotonic()
        bytes_written = 0
        digest = hashlib.sha256()
        with request(spec.url, timeout=timeout) as response, part.open("wb") as handle:
            if not headers:
                headers = {key.lower(): value for key, value in response.headers.items()}
            for chunk in iter(lambda: response.read(chunk_size), b""):
                if not chunk:
                    break
                handle.write(chunk)
                digest.update(chunk)
                bytes_written += len(chunk)
                if spec.large and bytes_written and bytes_written % (1024 * 1024 * 256) < chunk_size:
                    elapsed = max(time.monotonic() - started, 0.1)
                    mib = bytes_written / (1024 * 1024)
                    print(f"  {mib:,.0f} MiB downloaded ({mib / elapsed:,.1f} MiB/s)", flush=True)
        os.replace(part, target)
        checksum = digest.hexdigest()
    else:
        checksum = sha256_file(target, chunk_size=chunk_size)

    return {
        "source_id": spec.source_id,
        "action": action,
        "local_path": relative(target),
        "filename": spec.filename,
        "url_or_endpoint": spec.url,
        "retrieval_date": dt.date.today().isoformat(),
        "version_or_release": spec.version_or_release,
        "bytes": target.stat().st_size,
        "sha256": checksum,
        "status": "ok",
        "last_modified": headers.get("last-modified", ""),
        "content_length": headers.get("content-length", ""),
        "license_or_terms": spec.license_or_terms,
        "notes": spec.notes,
    }


def gdc_query(endpoint: str, params: dict[str, object], timeout: int) -> tuple[str, bytes]:
    url = f"https://api.gdc.cancer.gov/{endpoint}?{urllib.parse.urlencode(params)}"
    with request(url, timeout=timeout) as response:
        return url, response.read()


def write_gdc_metadata(force: bool, timeout: int) -> list[dict[str, object]]:
    project_filter = {"op": "=", "content": {"field": "project.project_id", "value": "TCGA-STAD"}}
    case_fields = ",".join(
        [
            "case_id",
            "submitter_id",
            "samples.submitter_id",
            "samples.sample_type",
            "diagnoses.ajcc_pathologic_stage",
            "diagnoses.tumor_grade",
            "diagnoses.tissue_or_organ_of_origin",
            "diagnoses.site_of_resection_or_biopsy",
            "diagnoses.prior_treatment",
            "diagnoses.treatments.treatment_type",
            "diagnoses.treatments.treatment_or_therapy",
            "diagnoses.classification_of_tumor",
            "diagnoses.primary_diagnosis",
        ]
    )
    file_filters = {
        "op": "and",
        "content": [
            {"op": "=", "content": {"field": "cases.project.project_id", "value": "TCGA-STAD"}},
            {"op": "=", "content": {"field": "data_category", "value": "Transcriptome Profiling"}},
            {"op": "=", "content": {"field": "data_type", "value": "Gene Expression Quantification"}},
            {"op": "=", "content": {"field": "experimental_strategy", "value": "RNA-Seq"}},
            {"op": "=", "content": {"field": "analysis.workflow_type", "value": "STAR - Counts"}},
        ],
    }
    file_fields = ",".join(
        [
            "file_id",
            "file_name",
            "md5sum",
            "file_size",
            "data_format",
            "analysis.workflow_type",
            "cases.submitter_id",
            "cases.samples.submitter_id",
            "cases.samples.sample_type",
            "cases.samples.portions.analytes.aliquots.submitter_id",
        ]
    )
    outputs = [
        (
            "cases_tcga_stad.json",
            "cases",
            {
                "filters": json.dumps(project_filter, separators=(",", ":")),
                "fields": case_fields,
                "format": "JSON",
                "size": "2000",
            },
            "GDC TCGA-STAD case, sample, clinical, and treatment metadata response.",
        ),
        (
            "files_tcga_stad_rnaseq_star_counts.json",
            "files",
            {
                "filters": json.dumps(file_filters, separators=(",", ":")),
                "fields": file_fields,
                "format": "JSON",
                "size": "2000",
            },
            "GDC TCGA-STAD RNA-seq STAR Counts file metadata for secondary sensitivity planning.",
        ),
    ]

    records: list[dict[str, object]] = []
    out_dir = RAW_DIR / "gdc_tcga_stad"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, endpoint, params, notes in outputs:
        target = out_dir / filename
        action = "verified_existing_raw_metadata"
        url = f"https://api.gdc.cancer.gov/{endpoint}?{urllib.parse.urlencode(params)}"
        if force or not target.exists():
            action = "downloaded_raw_metadata"
            print(f"Downloading gdc_tcga_stad: {filename}", flush=True)
            url, raw = gdc_query(endpoint, params, timeout=timeout)
            target.write_bytes(raw)
        records.append(
            {
                "source_id": "gdc_tcga_stad",
                "action": action,
                "local_path": relative(target),
                "filename": filename,
                "url_or_endpoint": url,
                "retrieval_date": dt.date.today().isoformat(),
                "version_or_release": "GDC API live query",
                "bytes": target.stat().st_size,
                "sha256": sha256_file(target),
                "status": "ok",
                "last_modified": "",
                "content_length": "",
                "license_or_terms": "GDC data use terms; open-access metadata queried",
                "notes": notes,
            }
        )
    return records


def write_checksum_manifests(records: list[dict[str, object]]) -> None:
    fields = [
        "source_id",
        "action",
        "local_path",
        "filename",
        "url_or_endpoint",
        "retrieval_date",
        "version_or_release",
        "bytes",
        "sha256",
        "status",
        "last_modified",
        "content_length",
        "license_or_terms",
        "notes",
    ]
    by_source: dict[str, list[dict[str, object]]] = {}
    for record in records:
        by_source.setdefault(str(record["source_id"]), []).append(record)

    source_manifest_names = {
        "xena_toil_tcga_gtex": "xena_toil_sha256.tsv",
        "hpa_downloads": "hpa_sha256.tsv",
        "uniprot_reviewed_human": "uniprot_sha256.tsv",
        "gdc_tcga_stad": "gdc_tcga_stad_sha256.tsv",
    }
    for source_id, rows in sorted(by_source.items()):
        manifest_name = source_manifest_names.get(source_id, f"{source_id}_sha256.tsv")
        write_tsv(CHECKSUM_DIR / manifest_name, sorted(rows, key=lambda row: str(row["local_path"])), fields)

    write_tsv(RESULTS_DIR / "phase2_download_manifest.tsv", sorted(records, key=lambda row: str(row["local_path"])), fields)
    global_rows = sorted(records, key=lambda row: str(row["local_path"]))
    CHECKSUM_DIR.mkdir(parents=True, exist_ok=True)
    with (CHECKSUM_DIR / "sha256sums.txt").open("w", encoding="utf-8", newline="") as handle:
        for row in global_rows:
            handle.write(f"{row['sha256']}  {row['local_path']}\n")


def append_provenance(records: list[dict[str, object]]) -> None:
    fieldnames = [
        "date",
        "source_id",
        "action",
        "file_or_endpoint",
        "version_or_release",
        "checksum_or_hash",
        "notes",
    ]
    existing_keys: set[tuple[str, str, str]] = set()
    existing_rows: list[dict[str, str]] = []
    if PROVENANCE_LOG.exists():
        with PROVENANCE_LOG.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            existing_rows = list(reader)
            for row in existing_rows:
                existing_keys.add((row.get("source_id", ""), row.get("file_or_endpoint", ""), row.get("checksum_or_hash", "")))

    new_rows = []
    for record in records:
        key = (str(record["source_id"]), str(record["url_or_endpoint"]), str(record["sha256"]))
        if key in existing_keys:
            continue
        new_rows.append(
            {
                "date": str(record["retrieval_date"]),
                "source_id": str(record["source_id"]),
                "action": str(record["action"]),
                "file_or_endpoint": str(record["url_or_endpoint"]),
                "version_or_release": str(record["version_or_release"]),
                "checksum_or_hash": str(record["sha256"]),
                "notes": f"{record['local_path']}; {record['notes']}",
            }
        )

    if not new_rows:
        return
    PROVENANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    write_header = not PROVENANCE_LOG.exists() or PROVENANCE_LOG.stat().st_size == 0
    with PROVENANCE_LOG.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)


def update_datasets_config(downloaded_sources: Iterable[str], all_xena_files_present: bool) -> None:
    if not CONFIG_DATASETS.exists():
        return
    status_updates = {
        source_id: PHASE2_SOURCE_STATUS[source_id]
        for source_id in downloaded_sources
        if source_id in PHASE2_SOURCE_STATUS
    }
    if "xena_toil_tcga_gtex" in status_updates and not all_xena_files_present:
        status_updates["xena_toil_tcga_gtex"] = "partial_raw_downloaded_with_checksums_matrix_pending"

    lines = CONFIG_DATASETS.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    current_id: str | None = None
    for line in lines:
        stripped = line.strip()
        if line.startswith("status: "):
            line = 'status: "fase2_mvp_raw_downloads_complete_batch_diagnostic_pending"'
        elif stripped.startswith("- id: "):
            current_id = stripped.split(":", 1)[1].strip().strip('"')
        elif current_id in status_updates and line.startswith("    status: "):
            line = f'    status: "{status_updates[current_id]}"'
        updated_lines.append(line)
    CONFIG_DATASETS.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def write_fase2_notes(records: list[dict[str, object]], skipped_large: bool) -> None:
    rows = "\n".join(
        "| {source_id} | `{local_path}` | {bytes} | `{sha256}` |".format(**record)
        for record in sorted(records, key=lambda row: str(row["local_path"]))
    )
    skipped = (
        "\n\nLarge Xena matrix download was skipped by CLI option; Fase 2A is not complete."
        if skipped_large
        else ""
    )
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "fase2_data_acquisition.md").write_text(
        f"""# Fase 2 Data Acquisition

Access date: {dt.date.today().isoformat()}

This note records the first reproducible raw-data acquisition pass for the MVP tumor-normal workflow. Raw files are immutable inputs; derived tables must be regenerated from scripts rather than by editing raw files.

## Downloaded or Captured Files

| Source | Local raw file | Bytes | SHA-256 |
|---|---:|---:|---|
{rows}

## Reproducibility Outputs

- Global checksum manifest: `data/checksums/sha256sums.txt`
- Source checksum manifests: `data/checksums/xena_toil_sha256.tsv`, `data/checksums/hpa_sha256.tsv`, `data/checksums/uniprot_sha256.tsv`, `data/checksums/gdc_tcga_stad_sha256.tsv`
- Download manifest: `results/tables/phase2_download_manifest.tsv`
- Provenance log: `docs/provenance_log.tsv`

## Remaining Fase 2 Gate

The next required Fase 2 output is the Xena/Toil tumor-normal batch diagnostic:

- `results/figures/pca_batch_diagnostic.svg`
- `results/tables/batch_permanova.tsv`

GDC STAR Counts expression files remain a secondary sensitivity layer. The raw GDC metadata captured here identifies eligible files, but the primary tumor-normal score should not start until the Xena/Toil PCA/PERMANOVA diagnostic is generated and interpreted.{skipped}
""",
        encoding="utf-8",
    )


def selected_url_downloads(sources: set[str], skip_large: bool) -> list[UrlDownload]:
    selected = []
    for spec in URL_DOWNLOADS:
        if spec.source_id not in sources:
            continue
        if skip_large and spec.large:
            continue
        selected.append(spec)
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["xena_toil_tcga_gtex", "hpa_downloads", "uniprot_reviewed_human", "gdc_tcga_stad"],
        help="Source IDs to download. Defaults to the Fase 2A MVP sources.",
    )
    parser.add_argument("--skip-large", action="store_true", help="Skip large files such as the Xena expression matrix.")
    parser.add_argument("--force", action="store_true", help="Redownload files even if local copies exist.")
    parser.add_argument("--no-update-config", action="store_true", help="Do not update status fields in config/datasets.yaml.")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--chunk-size-mib", type=int, default=8)
    args = parser.parse_args(argv)

    CHECKSUM_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sources = set(args.sources)
    records: list[dict[str, object]] = []
    chunk_size = args.chunk_size_mib * 1024 * 1024
    for spec in selected_url_downloads(sources, skip_large=args.skip_large):
        records.append(download_url(spec, force=args.force, timeout=args.timeout, chunk_size=chunk_size))

    if "gdc_tcga_stad" in sources:
        records.extend(write_gdc_metadata(force=args.force, timeout=args.timeout))

    if not records:
        print("No records were downloaded or verified.", file=sys.stderr)
        return 1

    write_checksum_manifests(records)
    append_provenance(records)
    xena_matrix = RAW_DIR / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
    xena_phenotype = RAW_DIR / "xena_toil" / "TcgaTargetGTEX_phenotype.txt.gz"
    if not args.no_update_config:
        update_datasets_config({str(record["source_id"]) for record in records}, xena_matrix.exists() and xena_phenotype.exists())
    write_fase2_notes(records, skipped_large=args.skip_large)

    print(f"Wrote {len(records)} Fase 2 raw records and checksum manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
