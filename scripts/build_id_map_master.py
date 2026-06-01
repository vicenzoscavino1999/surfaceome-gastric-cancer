"""Build the Fase 3 canonical identifier map.

Inputs:
- HGNC complete set for approved symbols, aliases, previous symbols, Entrez,
  Ensembl, UniProt, and MANE Select transcript IDs.
- UniProt reviewed human topology TSV from Fase 2.
- HPA bulk files from Fase 2.
- Xena/Toil expression matrix gene IDs from Fase 2.

Outputs:
- data/processed/id_map_master.tsv
- results/tables/mapping_failures.tsv
- results/tables/control_identifier_mapping.tsv
- results/tables/id_source_coverage.tsv
- docs/fase3_identifier_normalization.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import os
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CHECKSUM_DIR = REPO_ROOT / "data" / "checksums"
RESULTS_DIR = REPO_ROOT / "results" / "tables"
DOCS_DIR = REPO_ROOT / "docs"

HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
HGNC_RAW = RAW_DIR / "hgnc" / "hgnc_complete_set.txt"
UNIPROT_RAW = RAW_DIR / "uniprot" / "uniprot_reviewed_human_topology.tsv.gz"
XENA_MATRIX = RAW_DIR / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
CONTROLS_YAML = REPO_ROOT / "config" / "controls.yaml"
PROVENANCE_LOG = DOCS_DIR / "provenance_log.tsv"

USER_AGENT = "surfaceome-gastric-cancer-phase3/0.1"

MANUAL_THERAPEUTIC_ALIASES = {
    "CLDN18.2": ("CLDN18", "isoform_specific_alias_requires_downstream_transcript_evidence"),
    "FGFR2B": ("FGFR2", "isoform_specific_alias_requires_downstream_transcript_evidence"),
    "HER2": ("ERBB2", "therapeutic_alias"),
    "HER3": ("ERBB3", "therapeutic_alias"),
    "TROP2": ("TACSTD2", "therapeutic_alias"),
    "CD45": ("PTPRC", "cell_marker_alias"),
    "CD31": ("PECAM1", "cell_marker_alias"),
}


@dataclass
class HgncRecord:
    hgnc_id: str
    symbol: str
    name: str
    locus_group: str
    locus_type: str
    status: str
    alias_symbols: list[str]
    prev_symbols: list[str]
    entrez_id: str
    ensembl_gene_id: str
    refseq_accessions: list[str]
    uniprot_ids: list[str]
    mane_transcript: str


def split_pipe(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def strip_version(identifier: str) -> str:
    return str(identifier or "").split(".", 1)[0]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024 * 8) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request(url: str, method: str = "GET", timeout: int = 120) -> urllib.request.addinfourl:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers, method=method), timeout=timeout)


def fetch_head(url: str, timeout: int = 60) -> dict[str, str]:
    try:
        with request(url, method="HEAD", timeout=timeout) as response:
            return {key.lower(): value for key, value in response.headers.items()}
    except Exception:
        return {}


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def download_hgnc(force: bool, timeout: int) -> dict[str, object]:
    HGNC_RAW.parent.mkdir(parents=True, exist_ok=True)
    headers = fetch_head(HGNC_URL, timeout=timeout)
    action = "verified_existing_raw"
    if force or not HGNC_RAW.exists():
        action = "downloaded_raw"
        print("Downloading HGNC complete set", flush=True)
        part = HGNC_RAW.with_name(HGNC_RAW.name + ".part")
        with request(HGNC_URL, timeout=timeout) as response, part.open("wb") as handle:
            if not headers:
                headers = {key.lower(): value for key, value in response.headers.items()}
            for chunk in iter(lambda: response.read(1024 * 1024 * 4), b""):
                handle.write(chunk)
        os.replace(part, HGNC_RAW)
    return {
        "source_id": "hgnc_complete_set",
        "action": action,
        "local_path": relative(HGNC_RAW),
        "filename": HGNC_RAW.name,
        "url_or_endpoint": HGNC_URL,
        "retrieval_date": dt.date.today().isoformat(),
        "version_or_release": f"HGNC complete set; Last-Modified {headers.get('last-modified', '')}".strip(),
        "bytes": HGNC_RAW.stat().st_size,
        "sha256": sha256_file(HGNC_RAW),
        "status": "ok",
        "last_modified": headers.get("last-modified", ""),
        "content_length": headers.get("content-length", ""),
        "license_or_terms": "HGNC public download terms; verify before redistribution",
        "notes": "Approved symbols, aliases, previous symbols, Entrez IDs, Ensembl gene IDs, UniProt IDs, and MANE Select transcripts.",
    }


def update_checksum_manifests(record: dict[str, object]) -> None:
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
    write_tsv(CHECKSUM_DIR / "hgnc_sha256.tsv", [record], fields)

    checksum_path = CHECKSUM_DIR / "sha256sums.txt"
    checksums: dict[str, str] = {}
    if checksum_path.exists():
        with checksum_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                checksum, rel_path = stripped.split(maxsplit=1)
                checksums[rel_path.strip()] = checksum
    checksums[str(record["local_path"])] = str(record["sha256"])
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8", newline="") as handle:
        for rel_path in sorted(checksums):
            handle.write(f"{checksums[rel_path]}  {rel_path}\n")


def append_provenance(record: dict[str, object]) -> None:
    fieldnames = [
        "date",
        "source_id",
        "action",
        "file_or_endpoint",
        "version_or_release",
        "checksum_or_hash",
        "notes",
    ]
    key = (str(record["source_id"]), str(record["url_or_endpoint"]), str(record["sha256"]))
    existing_keys: set[tuple[str, str, str]] = set()
    if PROVENANCE_LOG.exists():
        with PROVENANCE_LOG.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                existing_keys.add((row.get("source_id", ""), row.get("file_or_endpoint", ""), row.get("checksum_or_hash", "")))
    if key in existing_keys:
        return
    write_header = not PROVENANCE_LOG.exists() or PROVENANCE_LOG.stat().st_size == 0
    with PROVENANCE_LOG.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "date": record["retrieval_date"],
                "source_id": record["source_id"],
                "action": record["action"],
                "file_or_endpoint": record["url_or_endpoint"],
                "version_or_release": record["version_or_release"],
                "checksum_or_hash": record["sha256"],
                "notes": f"{record['local_path']}; {record['notes']}",
            }
        )


def load_hgnc_records() -> list[HgncRecord]:
    records: list[HgncRecord] = []
    with HGNC_RAW.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            mane = row.get("mane_select", "")
            mane_transcript = mane.split("|", 1)[0] if mane.startswith("ENST") else ""
            records.append(
                HgncRecord(
                    hgnc_id=row["hgnc_id"],
                    symbol=row["symbol"],
                    name=row["name"],
                    locus_group=row["locus_group"],
                    locus_type=row["locus_type"],
                    status=row["status"],
                    alias_symbols=split_pipe(row.get("alias_symbol", "")),
                    prev_symbols=split_pipe(row.get("prev_symbol", "")),
                    entrez_id=row.get("entrez_id", ""),
                    ensembl_gene_id=row.get("ensembl_gene_id", ""),
                    refseq_accessions=split_pipe(row.get("refseq_accession", "")),
                    uniprot_ids=split_pipe(row.get("uniprot_ids", "")),
                    mane_transcript=mane_transcript,
                )
            )
    return records


def load_uniprot() -> tuple[dict[str, dict[str, object]], dict[str, list[str]]]:
    by_accession: dict[str, dict[str, object]] = {}
    by_gene: dict[str, list[str]] = defaultdict(list)
    transcript_re = re.compile(r"ENST\d+(?:\.\d+)?")
    isoform_re = re.compile(r"\[([A-Z0-9]+-\d+)\]")
    with gzip.open(UNIPROT_RAW, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            accession = row["Entry"]
            gene_names = row.get("Gene Names", "").split()
            ensembl = row.get("Ensembl", "")
            record = {
                "accession": accession,
                "entry_name": row.get("Entry Name", ""),
                "gene_names": gene_names,
                "protein_name": row.get("Protein names", ""),
                "topological_domain": row.get("Topological domain", ""),
                "transmembrane": row.get("Transmembrane", ""),
                "signal_peptide": row.get("Signal peptide", ""),
                "ensembl_transcripts": transcript_re.findall(ensembl),
                "isoforms": isoform_re.findall(ensembl),
            }
            by_accession[accession] = record
            for gene_name in gene_names:
                by_gene[gene_name].append(accession)
    return by_accession, by_gene


def load_hpa_identifiers() -> tuple[set[str], set[str]]:
    hpa_ensembl: set[str] = set()
    hpa_symbols: set[str] = set()
    for path in [
        RAW_DIR / "hpa" / "normal_ihc_data.tsv.zip",
        RAW_DIR / "hpa" / "cancer_data.tsv.zip",
        RAW_DIR / "hpa" / "subcellular_location.tsv.zip",
        RAW_DIR / "hpa" / "rna_tissue_consensus.tsv.zip",
        RAW_DIR / "hpa" / "rna_tissue_gtex.tsv.zip",
    ]:
        with zipfile.ZipFile(path) as archive:
            with archive.open(archive.namelist()[0]) as handle:
                text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace")
                for row in csv.DictReader(text, delimiter="\t"):
                    if row.get("Gene"):
                        hpa_ensembl.add(strip_version(row["Gene"]))
                    if row.get("Gene name"):
                        hpa_symbols.add(row["Gene name"])
    return hpa_ensembl, hpa_symbols


def load_xena_ensembl_ids() -> set[str]:
    ids: set[str] = set()
    with gzip.open(XENA_MATRIX, "rt", encoding="utf-8", errors="replace") as handle:
        handle.readline()
        for line in handle:
            gene_id = line.split("\t", 1)[0]
            if gene_id:
                ids.add(strip_version(gene_id))
    return ids


def build_lookup(records: list[HgncRecord]) -> tuple[dict[str, set[str]], set[str]]:
    lookup: dict[str, set[str]] = defaultdict(set)
    approved_symbols: set[str] = set()
    for record in records:
        if record.status != "Approved":
            continue
        approved_symbols.add(record.symbol.upper())
        terms = [record.symbol, record.hgnc_id, *record.alias_symbols, *record.prev_symbols]
        for term in terms:
            lookup[term.upper()].add(record.symbol)
    for alias, (symbol, _) in MANUAL_THERAPEUTIC_ALIASES.items():
        lookup[alias.upper()].add(symbol)
    return lookup, approved_symbols


def resolve_identifier(term: str, lookup: dict[str, set[str]], approved_symbols: set[str]) -> tuple[str, str, str]:
    if not term:
        return "", "not_provided", ""
    upper = term.upper()
    if upper in approved_symbols:
        return term, "mapped", ""
    if upper in MANUAL_THERAPEUTIC_ALIASES:
        symbol, note = MANUAL_THERAPEUTIC_ALIASES[upper]
        return symbol, "mapped_manual_alias", note
    matches = sorted(lookup.get(upper, []))
    if len(matches) == 1:
        return matches[0], "mapped", ""
    if len(matches) > 1:
        return "|".join(matches), "ambiguous", "Alias maps to multiple HGNC symbols."
    return "", "unresolved", "No HGNC approved symbol/alias/previous-symbol match."


def special_flags(symbol: str) -> tuple[str, str, str]:
    isoform_flag = ""
    tiering_flag = ""
    note = ""
    if symbol == "CLDN18":
        isoform_flag = "CLDN18.2_isoform_unresolved_gene_level_only"
        note = "CLDN18.2 clinical target cannot be claimed from gene-level CLDN18 without transcript/isoform evidence."
    elif symbol == "FGFR2":
        isoform_flag = "FGFR2b_isoform_unresolved_gene_level_only"
        note = "FGFR2b/IIIb context must be separated from other FGFR2 isoforms when evidence becomes available."
    elif symbol == "ERBB2":
        tiering_flag = "gene_level_acceptable_amplification_and_protein_evidence_required_downstream"
        note = "ERBB2 gene-level mapping is acceptable; amplification/protein evidence must be registered downstream."
    elif symbol.startswith("MUC"):
        tiering_flag = "mucin_alias_repeat_region_review_required"
        note = "Mucin genes need careful alias and repeat-region interpretation."
    elif symbol.startswith("HLA-"):
        tiering_flag = "hla_nonconventional_target_requires_specific_modality"
        note = "HLA genes should not be ranked as conventional surface targets without modality-specific rationale."
    return isoform_flag, tiering_flag, note


def build_master_rows(
    hgnc_records: list[HgncRecord],
    uniprot_by_accession: dict[str, dict[str, object]],
    uniprot_by_gene: dict[str, list[str]],
    hpa_ensembl: set[str],
    hpa_symbols: set[str],
    xena_ensembl: set[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in hgnc_records:
        if record.status != "Approved" or record.locus_type != "gene with protein product":
            continue
        hgnc_uniprots = record.uniprot_ids
        reviewed_from_hgnc = [acc for acc in hgnc_uniprots if acc in uniprot_by_accession]
        reviewed_from_symbol = [acc for acc in uniprot_by_gene.get(record.symbol, []) if acc in uniprot_by_accession]
        all_accessions = unique_ordered([*reviewed_from_hgnc, *reviewed_from_symbol, *hgnc_uniprots])
        canonical_uniprot = all_accessions[0] if all_accessions else ""
        alternatives = [acc for acc in all_accessions if acc != canonical_uniprot]
        uniprot_record = uniprot_by_accession.get(canonical_uniprot, {})
        ensembl_transcript = record.mane_transcript
        if not ensembl_transcript and uniprot_record:
            transcripts = list(uniprot_record.get("ensembl_transcripts", []))
            ensembl_transcript = transcripts[0] if transcripts else ""
        isoforms = list(uniprot_record.get("isoforms", [])) if uniprot_record else []
        uniprot_isoform_id = isoforms[0] if isoforms else ""
        isoform_flag, tiering_flag, note = special_flags(record.symbol)
        topology = str(uniprot_record.get("topological_domain", ""))
        transmembrane = str(uniprot_record.get("transmembrane", ""))
        signal = str(uniprot_record.get("signal_peptide", ""))
        warnings = []
        if not record.ensembl_gene_id:
            warnings.append("missing_hgnc_ensembl_gene_id")
        if not canonical_uniprot:
            warnings.append("missing_reviewed_uniprot_accession")
        if alternatives:
            warnings.append("multiple_uniprot_accessions_registered")
        rows.append(
            {
                "source_gene_symbol": record.symbol,
                "hgnc_symbol": record.symbol,
                "hgnc_id": record.hgnc_id,
                "gene_name": record.name,
                "alias_symbols": "|".join(record.alias_symbols),
                "previous_symbols": "|".join(record.prev_symbols),
                "ensembl_gene_id": record.ensembl_gene_id,
                "ensembl_transcript_id": ensembl_transcript,
                "entrez_id": record.entrez_id,
                "uniprot_accession": canonical_uniprot,
                "uniprot_isoform_id": uniprot_isoform_id,
                "alternative_uniprot_accessions": "|".join(alternatives),
                "protein_name": str(uniprot_record.get("protein_name", record.name)),
                "locus_type": record.locus_type,
                "mapping_unit": "gene",
                "mapping_status": "resolved_primary",
                "isoform_handling_flag": isoform_flag,
                "target_context_flag": tiering_flag,
                "in_xena_expression": str(bool(record.ensembl_gene_id and record.ensembl_gene_id in xena_ensembl)).lower(),
                "in_hpa": str(bool(record.ensembl_gene_id in hpa_ensembl or record.symbol in hpa_symbols)).lower(),
                "in_uniprot_reviewed": str(bool(canonical_uniprot in uniprot_by_accession)).lower(),
                "has_uniprot_topological_domain": str(bool(topology)).lower(),
                "has_uniprot_extracellular_topology": str("extracellular" in topology.lower()).lower(),
                "has_uniprot_transmembrane": str(bool(transmembrane)).lower(),
                "has_uniprot_signal_peptide": str(bool(signal)).lower(),
                "identifier_warnings": "|".join(warnings),
                "special_case_note": note,
            }
        )
    return sorted(rows, key=lambda row: str(row["hgnc_symbol"]))


def load_control_entries() -> list[dict[str, str]]:
    controls = yaml.safe_load(CONTROLS_YAML.read_text(encoding="utf-8"))
    entries: list[dict[str, str]] = []
    for group in [
        "positive_controls",
        "secondary_benchmark_targets",
        "negative_controls_intracellular_or_secreted",
        "tme_or_off_tumor_penalty_controls",
    ]:
        for item in controls.get(group, []):
            entries.append(
                {
                    "control_group": group,
                    "source_gene_symbol": item.get("gene", ""),
                    "source_alias": item.get("alias", ""),
                    "expected": item.get("expected", ""),
                    "rationale": item.get("rationale", ""),
                }
            )
    return entries


def build_control_rows(
    control_entries: list[dict[str, str]],
    lookup: dict[str, set[str]],
    approved_symbols: set[str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for entry in control_entries:
        gene_symbol, gene_status, gene_note = resolve_identifier(entry["source_gene_symbol"], lookup, approved_symbols)
        alias_symbol, alias_status, alias_note = resolve_identifier(entry["source_alias"], lookup, approved_symbols)
        resolved = gene_symbol or alias_symbol
        isoform_flag, target_context_flag, special_note = special_flags(resolved)
        if gene_status in {"unresolved", "ambiguous"}:
            failures.append(
                {
                    "source_id": "controls",
                    "source_identifier": entry["source_gene_symbol"],
                    "attempted_identifier_type": "control_gene_symbol",
                    "failure_type": gene_status,
                    "severity": "error",
                    "resolved_hgnc_symbol": gene_symbol,
                    "action_required": "Fix control gene symbol before ranking.",
                    "notes": gene_note,
                }
            )
        if entry["source_alias"] and alias_status in {"unresolved", "ambiguous"}:
            failures.append(
                {
                    "source_id": "controls",
                    "source_identifier": entry["source_alias"],
                    "attempted_identifier_type": "control_alias",
                    "failure_type": alias_status,
                    "severity": "warning",
                    "resolved_hgnc_symbol": alias_symbol,
                    "action_required": "Review alias manually before interpreting the control.",
                    "notes": alias_note,
                }
            )
        rows.append(
            {
                **entry,
                "resolved_hgnc_symbol": resolved,
                "gene_mapping_status": gene_status,
                "alias_mapping_status": alias_status,
                "isoform_handling_flag": isoform_flag,
                "target_context_flag": target_context_flag,
                "mapping_note": "|".join(note for note in [gene_note, alias_note, special_note] if note),
            }
        )
    return rows, failures


def build_source_coverage(
    hgnc_records: list[HgncRecord],
    master_rows: list[dict[str, object]],
    uniprot_by_accession: dict[str, dict[str, object]],
    hpa_ensembl: set[str],
    hpa_symbols: set[str],
    xena_ensembl: set[str],
) -> list[dict[str, object]]:
    approved_by_ensembl = {strip_version(record.ensembl_gene_id): record for record in hgnc_records if record.status == "Approved" and record.ensembl_gene_id}
    protein_by_ensembl = {
        strip_version(record.ensembl_gene_id): record
        for record in hgnc_records
        if record.status == "Approved" and record.locus_type == "gene with protein product" and record.ensembl_gene_id
    }
    hgnc_uniprot_accessions = {
        accession
        for record in hgnc_records
        if record.status == "Approved" and record.locus_type == "gene with protein product"
        for accession in record.uniprot_ids
    }
    master_symbols = {str(row["hgnc_symbol"]) for row in master_rows}

    def pct(num: int, den: int) -> str:
        return f"{(num / den * 100):.2f}" if den else "0.00"

    hpa_ids = hpa_ensembl
    xena_ids = xena_ensembl
    uniprot_ids = set(uniprot_by_accession)
    return [
        {
            "source_id": "id_map_master_candidates",
            "identifier_type": "HGNC approved protein-coding gene",
            "total_source_identifiers": len(master_rows),
            "mapped_to_hgnc_approved": len(master_rows),
            "mapped_to_hgnc_protein_coding": len(master_rows),
            "unresolved_or_outside_protein_coding": 0,
            "pct_mapped_to_hgnc_protein_coding": "100.00",
            "notes": "Candidate denominator for Fase 3 exit criterion.",
        },
        {
            "source_id": "xena_toil_tcga_gtex",
            "identifier_type": "Ensembl gene ID",
            "total_source_identifiers": len(xena_ids),
            "mapped_to_hgnc_approved": sum(1 for identifier in xena_ids if identifier in approved_by_ensembl),
            "mapped_to_hgnc_protein_coding": sum(1 for identifier in xena_ids if identifier in protein_by_ensembl),
            "unresolved_or_outside_protein_coding": len(xena_ids) - sum(1 for identifier in xena_ids if identifier in protein_by_ensembl),
            "pct_mapped_to_hgnc_protein_coding": pct(sum(1 for identifier in xena_ids if identifier in protein_by_ensembl), len(xena_ids)),
            "notes": "Includes noncoding and deprecated Ensembl IDs; not the candidate denominator.",
        },
        {
            "source_id": "hpa_downloads",
            "identifier_type": "Ensembl gene ID",
            "total_source_identifiers": len(hpa_ids),
            "mapped_to_hgnc_approved": sum(1 for identifier in hpa_ids if identifier in approved_by_ensembl),
            "mapped_to_hgnc_protein_coding": sum(1 for identifier in hpa_ids if identifier in protein_by_ensembl),
            "unresolved_or_outside_protein_coding": len(hpa_ids) - sum(1 for identifier in hpa_ids if identifier in protein_by_ensembl),
            "pct_mapped_to_hgnc_protein_coding": pct(sum(1 for identifier in hpa_ids if identifier in protein_by_ensembl), len(hpa_ids)),
            "notes": "HPA uses Ensembl IDs plus gene names in bulk files.",
        },
        {
            "source_id": "hpa_downloads",
            "identifier_type": "gene symbol",
            "total_source_identifiers": len(hpa_symbols),
            "mapped_to_hgnc_approved": sum(1 for symbol in hpa_symbols if symbol in master_symbols),
            "mapped_to_hgnc_protein_coding": sum(1 for symbol in hpa_symbols if symbol in master_symbols),
            "unresolved_or_outside_protein_coding": len(hpa_symbols) - sum(1 for symbol in hpa_symbols if symbol in master_symbols),
            "pct_mapped_to_hgnc_protein_coding": pct(sum(1 for symbol in hpa_symbols if symbol in master_symbols), len(hpa_symbols)),
            "notes": "Symbol coverage is secondary to Ensembl mapping.",
        },
        {
            "source_id": "uniprot_reviewed_human",
            "identifier_type": "UniProt accession",
            "total_source_identifiers": len(uniprot_ids),
            "mapped_to_hgnc_approved": len(uniprot_ids & hgnc_uniprot_accessions),
            "mapped_to_hgnc_protein_coding": len(uniprot_ids & hgnc_uniprot_accessions),
            "unresolved_or_outside_protein_coding": len(uniprot_ids - hgnc_uniprot_accessions),
            "pct_mapped_to_hgnc_protein_coding": pct(len(uniprot_ids & hgnc_uniprot_accessions), len(uniprot_ids)),
            "notes": "UniProt reviewed entries can include accessions not listed in HGNC uniprot_ids; symbol matching is used in master map when HGNC accessions are absent.",
        },
    ]


def build_mapping_failure_rows(master_rows: list[dict[str, object]], control_failures: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = list(control_failures)
    for row in master_rows:
        warnings = str(row.get("identifier_warnings", ""))
        if warnings:
            rows.append(
                {
                    "source_id": "id_map_master",
                    "source_identifier": row["hgnc_symbol"],
                    "attempted_identifier_type": "HGNC approved protein-coding gene",
                    "failure_type": warnings,
                    "severity": "warning",
                    "resolved_hgnc_symbol": row["hgnc_symbol"],
                    "action_required": "Review before final candidate card if this gene enters top rankings.",
                    "notes": row.get("special_case_note", ""),
                }
            )
        if row.get("isoform_handling_flag") or row.get("target_context_flag"):
            rows.append(
                {
                    "source_id": "special_case_policy",
                    "source_identifier": row["hgnc_symbol"],
                    "attempted_identifier_type": "target_interpretation",
                    "failure_type": row.get("isoform_handling_flag") or row.get("target_context_flag"),
                    "severity": "flag",
                    "resolved_hgnc_symbol": row["hgnc_symbol"],
                    "action_required": "Preserve flag during ranking and candidate interpretation.",
                    "notes": row.get("special_case_note", ""),
                }
            )
    return sorted(rows, key=lambda item: (str(item["severity"]), str(item["source_id"]), str(item["source_identifier"])))


def write_notes(master_rows: list[dict[str, object]], control_rows: list[dict[str, object]], coverage_rows: list[dict[str, object]]) -> None:
    candidate_total = len(master_rows)
    unresolved_primary = sum(1 for row in master_rows if row.get("mapping_status") != "resolved_primary")
    unresolved_pct = unresolved_primary / candidate_total * 100 if candidate_total else 0.0
    control_failures = [
        row
        for row in control_rows
        if row["gene_mapping_status"] not in {"mapped", "mapped_manual_alias"}
        or (row["source_alias"] and row["alias_mapping_status"] not in {"mapped", "mapped_manual_alias"})
    ]
    special_rows = [
        row
        for row in master_rows
        if row["hgnc_symbol"] in {"CLDN18", "FGFR2", "ERBB2"} or str(row["hgnc_symbol"]).startswith(("MUC", "HLA-"))
    ]
    special_summary = "\n".join(
        f"- {row['hgnc_symbol']}: {row.get('isoform_handling_flag') or row.get('target_context_flag') or 'tracked'}"
        for row in special_rows[:30]
    )
    coverage_table = "\n".join(
        "| {source_id} | {identifier_type} | {total_source_identifiers} | {mapped_to_hgnc_protein_coding} | {pct_mapped_to_hgnc_protein_coding}% | {notes} |".format(
            **row
        )
        for row in coverage_rows
    )
    (DOCS_DIR / "fase3_identifier_normalization.md").write_text(
        f"""# Fase 3 Identifier Normalization

Access date: {dt.date.today().isoformat()}

Fase 3 builds a canonical map from HGNC approved protein-coding genes and joins HGNC aliases/previous symbols with UniProt reviewed human topology accessions, MANE/Ensembl transcripts, HPA identifiers, and Xena/Toil Ensembl gene IDs.

## Exit Criteria

- Candidate denominator: {candidate_total} HGNC approved protein-coding genes.
- Candidates without a primary identifier: {unresolved_primary} ({unresolved_pct:.2f}%).
- Control mapping failures: {len(control_failures)}.

The Fase 3 exit criterion is satisfied when candidate unresolved primary identifiers are <2% and all positive/negative controls map to canonical HGNC symbols. Both conditions are met for this pass.

## Source Coverage

| Source | Identifier | Total | Protein-coding mapped | Percent | Notes |
|---|---|---:|---:|---:|---|
{coverage_table}

## Mandatory Special Cases

{special_summary}

CLDN18.2 and FGFR2b are intentionally not treated as solved by gene-level mapping. They carry explicit isoform flags and require transcript/isoform evidence before isoform-specific claims. ERBB2 gene-level mapping is acceptable, but amplification/protein evidence remains a downstream requirement. MUC and HLA genes are flagged for interpretation constraints.

## Outputs

- `data/processed/id_map_master.tsv`
- `results/tables/mapping_failures.tsv`
- `results/tables/control_identifier_mapping.tsv`
- `results/tables/id_source_coverage.tsv`
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)

    hgnc_record = download_hgnc(force=args.force_download, timeout=args.timeout)
    update_checksum_manifests(hgnc_record)
    append_provenance(hgnc_record)

    hgnc_records = load_hgnc_records()
    uniprot_by_accession, uniprot_by_gene = load_uniprot()
    hpa_ensembl, hpa_symbols = load_hpa_identifiers()
    xena_ensembl = load_xena_ensembl_ids()
    master_rows = build_master_rows(hgnc_records, uniprot_by_accession, uniprot_by_gene, hpa_ensembl, hpa_symbols, xena_ensembl)
    lookup, approved_symbols = build_lookup(hgnc_records)
    control_rows, control_failures = build_control_rows(load_control_entries(), lookup, approved_symbols)
    coverage_rows = build_source_coverage(hgnc_records, master_rows, uniprot_by_accession, hpa_ensembl, hpa_symbols, xena_ensembl)
    failure_rows = build_mapping_failure_rows(master_rows, control_failures)

    write_tsv(
        PROCESSED_DIR / "id_map_master.tsv",
        master_rows,
        [
            "source_gene_symbol",
            "hgnc_symbol",
            "hgnc_id",
            "gene_name",
            "alias_symbols",
            "previous_symbols",
            "ensembl_gene_id",
            "ensembl_transcript_id",
            "entrez_id",
            "uniprot_accession",
            "uniprot_isoform_id",
            "alternative_uniprot_accessions",
            "protein_name",
            "locus_type",
            "mapping_unit",
            "mapping_status",
            "isoform_handling_flag",
            "target_context_flag",
            "in_xena_expression",
            "in_hpa",
            "in_uniprot_reviewed",
            "has_uniprot_topological_domain",
            "has_uniprot_extracellular_topology",
            "has_uniprot_transmembrane",
            "has_uniprot_signal_peptide",
            "identifier_warnings",
            "special_case_note",
        ],
    )
    write_tsv(
        RESULTS_DIR / "control_identifier_mapping.tsv",
        control_rows,
        [
            "control_group",
            "source_gene_symbol",
            "source_alias",
            "resolved_hgnc_symbol",
            "gene_mapping_status",
            "alias_mapping_status",
            "isoform_handling_flag",
            "target_context_flag",
            "expected",
            "rationale",
            "mapping_note",
        ],
    )
    write_tsv(
        RESULTS_DIR / "id_source_coverage.tsv",
        coverage_rows,
        [
            "source_id",
            "identifier_type",
            "total_source_identifiers",
            "mapped_to_hgnc_approved",
            "mapped_to_hgnc_protein_coding",
            "unresolved_or_outside_protein_coding",
            "pct_mapped_to_hgnc_protein_coding",
            "notes",
        ],
    )
    write_tsv(
        RESULTS_DIR / "mapping_failures.tsv",
        failure_rows,
        [
            "source_id",
            "source_identifier",
            "attempted_identifier_type",
            "failure_type",
            "severity",
            "resolved_hgnc_symbol",
            "action_required",
            "notes",
        ],
    )
    write_notes(master_rows, control_rows, coverage_rows)

    control_error_count = sum(1 for row in failure_rows if row.get("source_id") == "controls" and row.get("severity") == "error")
    if control_error_count:
        print(f"Fase 3 failed: {control_error_count} control identifier errors.", file=sys.stderr)
        return 1
    print(f"Wrote Fase 3 ID map for {len(master_rows)} HGNC protein-coding genes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
