"""Build Phase 1 dataset inventory tables.

This script queries lightweight metadata endpoints only. It does not download
large expression or proteomics matrices into data/raw.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import io
import json
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "results" / "tables"
DOCS_DIR = REPO_ROOT / "docs"
FROZEN_PHASE1_DIR = REPO_ROOT / "data" / "raw" / "frozen_snapshots" / "phase1_inventory"
FROZEN_PHASE1_FILES = {
    "dataset_inventory.tsv": RESULTS_DIR / "dataset_inventory.tsv",
    "sample_counts.tsv": RESULTS_DIR / "sample_counts.tsv",
    "coverage_matrix.tsv": RESULTS_DIR / "coverage_matrix.tsv",
    "fase1_data_inventory.md": DOCS_DIR / "fase1_data_inventory.md",
}

USER_AGENT = "surfaceome-gastric-cancer-inventory/0.1"

MISSING_VALUES = {
    "",
    "--",
    "na",
    "n/a",
    "not available",
    "not reported",
    "unknown",
    "none",
    "[not available]",
    "not allowed to collect",
}


def known(value: object) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() not in MISSING_VALUES


def request_url(url: str, timeout: int = 120) -> urllib.request.addinfourl:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json,*/*", "User-Agent": USER_AGENT},
    )
    return urllib.request.urlopen(request, timeout=timeout)


def fetch_json(url: str, params: dict[str, object] | None = None, timeout: int = 120) -> tuple[dict, dict]:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with request_url(url, timeout=timeout) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        data = json.load(response)
    return data, headers


def fetch_text(url: str, timeout: int = 120) -> tuple[str, dict]:
    with request_url(url, timeout=timeout) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        text = response.read().decode("utf-8", errors="replace")
    return text, headers


def fetch_head(url: str, timeout: int = 60) -> dict:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return dict(response.headers.items())


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def materialize_offline_inventory() -> None:
    missing = [name for name in FROZEN_PHASE1_FILES if not (FROZEN_PHASE1_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Offline frozen-raw mode requires Phase 1 inventory snapshots: " + ", ".join(missing)
    )
    for name, target in FROZEN_PHASE1_FILES.items():
        source = FROZEN_PHASE1_DIR / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() in {".md", ".tsv"}:
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        else:
            shutil.copy2(source, target)


def format_counts(mapping: dict[str, object]) -> str:
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def gdc_query(endpoint: str, filters: dict, fields: str, size: int = 1000) -> dict:
    params = {
        "filters": json.dumps(filters),
        "fields": fields,
        "format": "JSON",
        "size": str(size),
    }
    data, _ = fetch_json(f"https://api.gdc.cancer.gov/{endpoint}", params=params)
    return data


def collect_gdc_counts(sample_counts: list[dict[str, object]]) -> dict[str, object]:
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
    case_data = gdc_query("cases", project_filter, case_fields)
    cases = case_data["data"]["hits"]

    sample_type_to_ids: dict[str, set[str]] = collections.defaultdict(set)
    clinical_counts: collections.Counter[str] = collections.Counter()
    for case in cases:
        for sample in case.get("samples", []):
            sample_type_to_ids[sample.get("sample_type", "")].add(sample.get("submitter_id", ""))

        primary_diagnoses = [
            diagnosis
            for diagnosis in case.get("diagnoses", [])
            if str(diagnosis.get("classification_of_tumor", "")).lower() == "primary"
        ]
        diagnosis = (primary_diagnoses or case.get("diagnoses", [])[:1] or [{}])[0]
        checks = {
            "primary_diagnosis": diagnosis.get("primary_diagnosis"),
            "ajcc_pathologic_stage": diagnosis.get("ajcc_pathologic_stage"),
            "tumor_grade": diagnosis.get("tumor_grade"),
            "tissue_or_organ_of_origin": diagnosis.get("tissue_or_organ_of_origin"),
            "site_of_resection_or_biopsy": diagnosis.get("site_of_resection_or_biopsy"),
            "prior_treatment": diagnosis.get("prior_treatment"),
        }
        for key, value in checks.items():
            if known(value):
                clinical_counts[key] += 1
        if any(
            known(treatment.get("treatment_type")) or known(treatment.get("treatment_or_therapy"))
            for treatment in diagnosis.get("treatments", [])
        ):
            clinical_counts["treatment_records"] += 1

    sample_counts.append(
        {
            "source_id": "gdc_tcga_stad",
            "cohort_or_dataset": "TCGA-STAD",
            "count_type": "cases",
            "category": "all_cases",
            "n": len(cases),
            "unit": "case",
            "method": "GDC cases endpoint filtered by project.project_id=TCGA-STAD",
            "status": "queried",
            "endpoint_or_file": "https://api.gdc.cancer.gov/cases",
            "notes": "Case-level project membership, not necessarily RNA-seq availability.",
        }
    )
    for sample_type, ids in sorted(sample_type_to_ids.items()):
        sample_counts.append(
            {
                "source_id": "gdc_tcga_stad",
                "cohort_or_dataset": "TCGA-STAD biospecimen",
                "count_type": "biospecimen_sample_type",
                "category": sample_type or "missing",
                "n": len(ids),
                "unit": "sample_submitter_id",
                "method": "Unique samples from GDC cases endpoint",
                "status": "queried",
                "endpoint_or_file": "https://api.gdc.cancer.gov/cases",
                "notes": "Includes non-RNA samples such as slides and blood-derived normal.",
            }
        )
    for field, count in sorted(clinical_counts.items()):
        sample_counts.append(
            {
                "source_id": "gdc_tcga_stad",
                "cohort_or_dataset": "TCGA-STAD",
                "count_type": "clinical_field_available",
                "category": field,
                "n": count,
                "unit": "case",
                "method": "Known values in primary diagnosis records from GDC cases endpoint",
                "status": "queried",
                "endpoint_or_file": "https://api.gdc.cancer.gov/cases",
                "notes": "Counts fields that are present and not unknown/not reported.",
            }
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
            "analysis.workflow_type",
            "cases.submitter_id",
            "cases.samples.submitter_id",
            "cases.samples.sample_type",
            "cases.samples.portions.analytes.aliquots.submitter_id",
        ]
    )
    file_data = gdc_query("files", file_filters, file_fields, size=2000)
    files = file_data["data"]["hits"]
    files_by_sample_type: collections.Counter[str] = collections.Counter()
    samples_by_type: dict[str, set[str]] = collections.defaultdict(set)
    aliquots_by_type: dict[str, set[str]] = collections.defaultdict(set)
    for file_record in files:
        for case in file_record.get("cases", []):
            for sample in case.get("samples", []):
                sample_type = sample.get("sample_type", "")
                files_by_sample_type[sample_type] += 1
                samples_by_type[sample_type].add(sample.get("submitter_id", ""))
                for portion in sample.get("portions", []):
                    for analyte in portion.get("analytes", []):
                        for aliquot in analyte.get("aliquots", []):
                            aliquots_by_type[sample_type].add(aliquot.get("submitter_id", ""))

    for sample_type in sorted(samples_by_type):
        sample_counts.append(
            {
                "source_id": "gdc_tcga_stad",
                "cohort_or_dataset": "TCGA-STAD RNA-seq STAR - Counts",
                "count_type": "rna_seq_sample_type",
                "category": sample_type,
                "n": len(samples_by_type[sample_type]),
                "unit": "sample_submitter_id",
                "method": "GDC files endpoint, RNA-Seq Gene Expression Quantification, STAR - Counts",
                "status": "queried",
                "endpoint_or_file": "https://api.gdc.cancer.gov/files",
                "notes": f"{files_by_sample_type[sample_type]} files; {len(aliquots_by_type[sample_type])} aliquots.",
            }
        )
    if "Metastatic" not in samples_by_type:
        sample_counts.append(
            {
                "source_id": "gdc_tcga_stad",
                "cohort_or_dataset": "TCGA-STAD RNA-seq STAR - Counts",
                "count_type": "rna_seq_sample_type",
                "category": "Metastatic",
                "n": 0,
                "unit": "sample_submitter_id",
                "method": "GDC files endpoint, RNA-Seq Gene Expression Quantification, STAR - Counts",
                "status": "queried",
                "endpoint_or_file": "https://api.gdc.cancer.gov/files",
                "notes": "No metastatic RNA-seq STAR count samples were returned.",
            }
        )

    return {
        "gdc_cases": len(cases),
        "gdc_rna_total_files": len(files),
        "gdc_rna_counts_by_type": {key: len(value) for key, value in samples_by_type.items()},
        "gdc_clinical_counts": dict(clinical_counts),
    }


def collect_xena_counts(sample_counts: list[dict[str, object]]) -> dict[str, object]:
    phenotype_url = "https://toil.xenahubs.net/download/TcgaTargetGTEX_phenotype.txt.gz"
    matrix_url = "https://toil.xenahubs.net/download/TcgaTargetGtex_rsem_gene_tpm.gz"
    phenotype_head = fetch_head(phenotype_url)
    matrix_head = fetch_head(matrix_url)

    raw = request_url(phenotype_url).read()
    text = gzip.decompress(raw).decode("utf-8", errors="replace")
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))

    tcga_stad = [
        row
        for row in rows
        if row.get("_study") == "TCGA"
        and row.get("detailed_category") == "Stomach Adenocarcinoma"
    ]
    gtex_stomach = [
        row
        for row in rows
        if row.get("_study") == "GTEX" and row.get("detailed_category") == "Stomach"
    ]
    for label, subset in [("TCGA-STAD", tcga_stad), ("GTEx stomach", gtex_stomach)]:
        counter = collections.Counter(row.get("_sample_type", "missing") for row in subset)
        for sample_type, count in sorted(counter.items()):
            sample_counts.append(
                {
                    "source_id": "xena_toil_tcga_gtex",
                    "cohort_or_dataset": label,
                    "count_type": "xena_phenotype_sample_type",
                    "category": sample_type,
                    "n": count,
                    "unit": "sample",
                    "method": "Counted rows in TcgaTargetGTEX_phenotype.txt.gz",
                    "status": "queried",
                    "endpoint_or_file": phenotype_url,
                    "notes": "Primary expression matrix will be TcgaTargetGtex_rsem_gene_tpm.gz.",
                }
            )
    return {
        "phenotype_url": phenotype_url,
        "matrix_url": matrix_url,
        "phenotype_last_modified": phenotype_head.get("Last-Modified", ""),
        "matrix_last_modified": matrix_head.get("Last-Modified", ""),
        "matrix_content_length": matrix_head.get("Content-Length", ""),
        "tcga_stad_counts": dict(collections.Counter(row.get("_sample_type", "missing") for row in tcga_stad)),
        "gtex_stomach_counts": dict(collections.Counter(row.get("_sample_type", "missing") for row in gtex_stomach)),
    }


def collect_cbioportal_counts(sample_counts: list[dict[str, object]]) -> dict[str, object]:
    pancan_url = "https://www.cbioportal.org/api/studies/stad_tcga_pan_can_atlas_2018/clinical-data"
    pancan, _ = fetch_json(
        pancan_url,
        params={"clinicalDataType": "PATIENT", "projection": "SUMMARY"},
    )
    subtype_counter = collections.Counter(
        record["value"] for record in pancan if record.get("clinicalAttributeId") == "SUBTYPE"
    )
    for subtype, count in sorted(subtype_counter.items()):
        sample_counts.append(
            {
                "source_id": "cbioportal_stad_tcga_pan_can_atlas_2018",
                "cohort_or_dataset": "TCGA-STAD PanCanAtlas 2018",
                "count_type": "tcga_molecular_subtype",
                "category": subtype,
                "n": count,
                "unit": "patient",
                "method": "cBioPortal clinical-data endpoint, PATIENT SUBTYPE",
                "status": "queried",
                "endpoint_or_file": pancan_url,
                "notes": "PanCanAtlas clinical attribute SUBTYPE; includes STAD_POLE as annotated by cBioPortal.",
            }
        )

    classic_url = "https://www.cbioportal.org/api/studies/stad_tcga/clinical-data"
    classic, _ = fetch_json(classic_url, params={"clinicalDataType": "PATIENT", "projection": "SUMMARY"})
    by_attribute: dict[str, list[str]] = collections.defaultdict(list)
    for record in classic:
        by_attribute[record.get("clinicalAttributeId", "")].append(record.get("value", ""))

    attribute_map = {
        "AJCC_PATHOLOGIC_TUMOR_STAGE": "cbioportal_ajcc_pathologic_stage",
        "GRADE": "cbioportal_grade",
        "HISTOLOGICAL_DIAGNOSIS": "cbioportal_histological_diagnosis",
        "PRIMARY_SITE_PATIENT": "cbioportal_primary_site_patient",
        "SITE_OF_TUMOR_TISSUE": "cbioportal_site_of_tumor_tissue",
        "HISTORY_NEOADJUVANT_TRTYN": "cbioportal_neoadjuvant_history",
        "TREATMENT": "cbioportal_treatment",
        "TREATMENT_TYPE": "cbioportal_treatment_type",
    }
    clinical_counts = {}
    for attribute, label in attribute_map.items():
        count = sum(1 for value in by_attribute.get(attribute, []) if known(value))
        clinical_counts[label] = count
        sample_counts.append(
            {
                "source_id": "cbioportal_stad_tcga",
                "cohort_or_dataset": "TCGA-STAD legacy cBioPortal",
                "count_type": "clinical_field_available",
                "category": label,
                "n": count,
                "unit": "patient",
                "method": f"cBioPortal clinical-data endpoint, PATIENT {attribute}",
                "status": "queried",
                "endpoint_or_file": classic_url,
                "notes": "Legacy cBioPortal TCGA clinical table.",
            }
        )

    histology_values = by_attribute.get("HISTOLOGICAL_DIAGNOSIS", [])
    lauren_like = sum(
        1
        for value in histology_values
        if any(term in value.lower() for term in ["intestinal", "diffuse", "signet ring"])
    )
    sample_counts.append(
        {
            "source_id": "cbioportal_stad_tcga",
            "cohort_or_dataset": "TCGA-STAD legacy cBioPortal",
            "count_type": "clinical_field_available",
            "category": "exact_lauren_subtype",
            "n": 0,
            "unit": "patient",
            "method": "Searched exposed cBioPortal clinical attributes for a Lauren-specific field",
            "status": "not_found",
            "endpoint_or_file": "https://www.cbioportal.org/api/studies/stad_tcga/clinical-attributes",
            "notes": "Exact Lauren subtype field was not exposed; histological diagnosis can be curated as a proxy.",
        }
    )
    sample_counts.append(
        {
            "source_id": "cbioportal_stad_tcga",
            "cohort_or_dataset": "TCGA-STAD legacy cBioPortal",
            "count_type": "clinical_field_available",
            "category": "lauren_like_histology_terms",
            "n": lauren_like,
            "unit": "patient",
            "method": "Counted histological diagnosis values containing intestinal, diffuse, or signet ring",
            "status": "proxy_requires_curation",
            "endpoint_or_file": classic_url,
            "notes": "Do not label as exact Lauren subtype without manual curation.",
        }
    )
    return {
        "tcga_subtypes": dict(subtype_counter),
        "legacy_clinical_counts": clinical_counts,
        "lauren_like_histology_terms": lauren_like,
    }


def hpa_zip_summary(file_name: str, tissue_column: str | None = None, tissue_value: str | None = None) -> dict[str, object]:
    url = f"https://www.proteinatlas.org/download/tsv/{file_name}"
    headers = fetch_head(url)
    raw = request_url(url, timeout=180).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", errors="replace")
            reader = csv.DictReader(text, delimiter="\t")
            genes: set[str] = set()
            matched_genes: set[str] = set()
            rows = 0
            matched_rows = 0
            for row in reader:
                rows += 1
                gene = row.get("Gene") or row.get("Ensembl") or row.get("Gene name") or ""
                if gene:
                    genes.add(gene)
                if tissue_column and tissue_value:
                    value = str(row.get(tissue_column, ""))
                    if value.lower() == tissue_value.lower():
                        matched_rows += 1
                        if gene:
                            matched_genes.add(gene)
    return {
        "url": url,
        "last_modified": headers.get("Last-Modified", ""),
        "content_length": headers.get("Content-Length", ""),
        "rows": rows,
        "genes": len(genes),
        "matched_rows": matched_rows,
        "matched_genes": len(matched_genes),
    }


def collect_hpa_counts(sample_counts: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    summaries = {
        "normal_ihc_data.tsv.zip": hpa_zip_summary("normal_ihc_data.tsv.zip", "Tissue", "Stomach"),
        "cancer_data.tsv.zip": hpa_zip_summary("cancer_data.tsv.zip", "Cancer", "stomach cancer"),
        "subcellular_location.tsv.zip": hpa_zip_summary("subcellular_location.tsv.zip"),
        "rna_tissue_consensus.tsv.zip": hpa_zip_summary("rna_tissue_consensus.tsv.zip", "Tissue", "stomach"),
        "rna_tissue_gtex.tsv.zip": hpa_zip_summary("rna_tissue_gtex.tsv.zip", "Tissue", "stomach"),
        "cancer_cptac.tsv.zip": hpa_zip_summary("cancer_cptac.tsv.zip", "Cancer", "Stomach cancer"),
    }
    for file_name, summary in summaries.items():
        if summary["matched_genes"]:
            category = f"{file_name}:stomach"
            n = summary["matched_genes"]
            notes = f"{summary['matched_rows']} stomach rows; total genes in file={summary['genes']}."
        else:
            category = file_name
            n = summary["genes"]
            notes = f"Total rows={summary['rows']}; no stomach-specific rows counted for this file."
        sample_counts.append(
            {
                "source_id": "hpa_downloads",
                "cohort_or_dataset": "Human Protein Atlas v25.1",
                "count_type": "gene_coverage",
                "category": category,
                "n": n,
                "unit": "Ensembl gene",
                "method": "Counted unique Gene values from HPA downloadable TSV zip",
                "status": "queried",
                "endpoint_or_file": summary["url"],
                "notes": notes,
            }
        )
    return summaries


def collect_uniprot_counts(sample_counts: list[dict[str, object]]) -> dict[str, object]:
    queries = {
        "human_reviewed": "organism_id:9606 AND reviewed:true",
        "human_reviewed_transmembrane": "organism_id:9606 AND reviewed:true AND ft_transmem:*",
        "human_reviewed_topological_domain": "organism_id:9606 AND reviewed:true AND ft_topo_dom:*",
        "human_reviewed_signal_peptide": "organism_id:9606 AND reviewed:true AND ft_signal:*",
    }
    counts = {}
    release = ""
    for label, query in queries.items():
        _, headers = fetch_json(
            "https://rest.uniprot.org/uniprotkb/search",
            params={"query": query, "format": "json", "size": "0"},
        )
        count = int(headers.get("x-total-results", 0))
        release = headers.get("x-uniprot-release", release)
        counts[label] = count
        sample_counts.append(
            {
                "source_id": "uniprot_reviewed_human",
                "cohort_or_dataset": "UniProtKB reviewed human",
                "count_type": "entry_coverage",
                "category": label,
                "n": count,
                "unit": "UniProtKB entry",
                "method": f"UniProt REST query: {query}",
                "status": "queried",
                "endpoint_or_file": "https://rest.uniprot.org/uniprotkb/search",
                "notes": f"Release header: {release}. Universe-specific coverage waits for ID mapping.",
            }
        )
    return {"release": release, "counts": counts}


def collect_depmap_counts(sample_counts: list[dict[str, object]]) -> dict[str, object]:
    context_url = "https://depmap.org/portal/api/context_explorer/context_info"
    data, _ = fetch_json(context_url, params={"level_0_subtype_code": "STOMACH"})
    rows = data["table_data"]
    tree = data["tree"]
    modality_keys = ["crispr", "rnai", "wgs", "wes", "rna_seq", "repurposing"]
    modality_counts = {key: sum(1 for row in rows if row.get(key) is True) for key in modality_keys}
    child_counts = {child["name"]: len(child.get("model_ids", [])) for child in tree.get("children", [])}

    sample_counts.append(
        {
            "source_id": "depmap",
            "cohort_or_dataset": "DepMap context STOMACH",
            "count_type": "lineage_models",
            "category": "Esophagus/Stomach",
            "n": len(tree.get("model_ids", [])),
            "unit": "model",
            "method": "DepMap Context Explorer API, level_0_subtype_code=STOMACH",
            "status": "queried",
            "endpoint_or_file": context_url,
            "notes": "Includes esophageal and esophagogastric models; child subtype counts separate ESCC and EGC.",
        }
    )
    for subtype, count in sorted(child_counts.items()):
        sample_counts.append(
            {
                "source_id": "depmap",
                "cohort_or_dataset": "DepMap context STOMACH",
                "count_type": "lineage_child_models",
                "category": subtype,
                "n": count,
                "unit": "model",
                "method": "DepMap Context Explorer API child nodes",
                "status": "queried",
                "endpoint_or_file": context_url,
                "notes": "EGC is the most relevant gastric/GEJ adenocarcinoma subset.",
            }
        )
    for modality, count in sorted(modality_counts.items()):
        sample_counts.append(
            {
                "source_id": "depmap",
                "cohort_or_dataset": "DepMap context STOMACH",
                "count_type": "data_modality_models",
                "category": modality,
                "n": count,
                "unit": "model",
                "method": "Counted true values in DepMap Context Explorer table_data",
                "status": "queried",
                "endpoint_or_file": context_url,
                "notes": "Modality coverage across Esophagus/Stomach lineage models.",
            }
        )
    return {"total_models": len(tree.get("model_ids", [])), "child_counts": child_counts, "modality_counts": modality_counts}


def pdc_study(study_id: str) -> dict[str, object]:
    query = (
        "{ study (pdc_study_id: \"%s\") { pdc_study_id study_name disease_type primary_site "
        "analytical_fraction experiment_type cases_count aliquots_count "
        "filesCount { data_category file_type files_count } } }"
    ) % study_id
    data, _ = fetch_json("https://pdc.cancer.gov/graphql", params={"query": query}, timeout=180)
    studies = data.get("data", {}).get("study", [])
    return studies[0] if studies else {}


def collect_pdc_counts(sample_counts: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    study_ids = [
        "PDC000614",
        "PDC000615",
        "PDC000616",
        "PDC000617",
        "PDC000621",
        "PDC000622",
        "PDC000626",
        "PDC000214",
        "PDC000215",
        "PDC000216",
        "PDC000645",
        "PDC000649",
    ]
    summaries = {}
    for study_id in study_ids:
        study = pdc_study(study_id)
        if not study:
            continue
        summaries[study_id] = study
        protein_assembly_files = sum(
            int(item.get("files_count", 0))
            for item in study.get("filesCount", [])
            if item.get("data_category") == "Protein Assembly"
        )
        sample_counts.append(
            {
                "source_id": "pdc_cptac_gastric",
                "cohort_or_dataset": study.get("study_name", study_id),
                "count_type": "pdc_study_cases",
                "category": study.get("analytical_fraction", ""),
                "n": study.get("cases_count", ""),
                "unit": "case",
                "method": "PDC GraphQL study(pdc_study_id)",
                "status": "queried",
                "endpoint_or_file": f"https://pdc.cancer.gov/pdc/study/{study_id}",
                "notes": f"Aliquots={study.get('aliquots_count')}; Protein Assembly files={protein_assembly_files}; experiment={study.get('experiment_type')}.",
            }
        )
    return summaries


def build_inventory_rows(access_date: str, summaries: dict[str, object]) -> list[dict[str, object]]:
    hpa = summaries["hpa"]
    uniprot = summaries["uniprot"]
    depmap = summaries["depmap"]
    xena = summaries["xena"]
    pdc = summaries["pdc"]
    pdc_ids = ", ".join(sorted(pdc))
    return [
        {
            "source_id": "xena_toil_tcga_gtex",
            "source_name": "UCSC Xena / Toil RNA-seq recompute",
            "role": "Primary TCGA-STAD vs GTEx stomach RNA matrix",
            "phase": "Fase 2 download; Fase 1 metadata complete",
            "status": "metadata_verified_no_matrix_downloaded",
            "version_or_release": "Toil recompute; matrix Last-Modified " + str(xena.get("matrix_last_modified", "")),
            "access_date": access_date,
            "url": "https://toil.xenahubs.net",
            "endpoint_or_file": "TcgaTargetGtex_rsem_gene_tpm.gz; TcgaTargetGTEX_phenotype.txt.gz",
            "local_raw_dir": "data/raw/xena_toil",
            "exact_files_or_queries": "https://toil.xenahubs.net/download/TcgaTargetGtex_rsem_gene_tpm.gz; https://toil.xenahubs.net/download/TcgaTargetGTEX_phenotype.txt.gz",
            "license_or_terms": "UCSC Xena public hub terms; verify at Fase 2 download",
            "checksum_manifest": "data/checksums/xena_toil_sha256.tsv",
            "notes": "Expression unit to register as log2(TPM+0.001); phenotype counted without downloading matrix.",
        },
        {
            "source_id": "gdc_tcga_stad",
            "source_name": "GDC TCGA-STAD API",
            "role": "TCGA clinical, biospecimen, STAR-count RNA-seq sensitivity",
            "phase": "Fase 1 metadata complete; Fase 2 selected downloads",
            "status": "metadata_verified_no_raw_downloaded",
            "version_or_release": "GDC API live query",
            "access_date": access_date,
            "url": "https://api.gdc.cancer.gov",
            "endpoint_or_file": "/cases and /files",
            "local_raw_dir": "data/raw/gdc_tcga_stad",
            "exact_files_or_queries": "project.project_id=TCGA-STAD; RNA-Seq Gene Expression Quantification; STAR - Counts",
            "license_or_terms": "GDC data use terms; open-access metadata queried",
            "checksum_manifest": "data/checksums/gdc_tcga_stad_sha256.tsv",
            "notes": "GDC STAR counts are secondary sensitivity, not the primary TCGA-GTEx matrix.",
        },
        {
            "source_id": "cbioportal_stad_tcga",
            "source_name": "cBioPortal TCGA-STAD clinical",
            "role": "TCGA subtype and legacy clinical field availability",
            "phase": "Fase 1 metadata complete",
            "status": "metadata_verified",
            "version_or_release": "stad_tcga and stad_tcga_pan_can_atlas_2018 API studies",
            "access_date": access_date,
            "url": "https://www.cbioportal.org",
            "endpoint_or_file": "/api/studies/stad_tcga*/clinical-data",
            "local_raw_dir": "data/raw/cbioportal",
            "exact_files_or_queries": "PATIENT clinical-data; SUBTYPE from stad_tcga_pan_can_atlas_2018",
            "license_or_terms": "cBioPortal public API terms; verify before redistribution",
            "checksum_manifest": "data/checksums/cbioportal_sha256.tsv",
            "notes": "Used for TCGA molecular subtype counts and legacy histology fields.",
        },
        {
            "source_id": "hpa_downloads",
            "source_name": "Human Protein Atlas downloadable TSV",
            "role": "Normal IHC, cancer IHC, subcellular location, tissue RNA cross-checks",
            "phase": "Fase 1 metadata complete; Fase 2 downloads",
            "status": "metadata_verified_no_raw_saved",
            "version_or_release": "HPA 25.1; Ensembl 109",
            "access_date": access_date,
            "url": "https://www.proteinatlas.org/about/download",
            "endpoint_or_file": "normal_ihc_data.tsv.zip; cancer_data.tsv.zip; subcellular_location.tsv.zip; rna_tissue_consensus.tsv.zip; rna_tissue_gtex.tsv.zip",
            "local_raw_dir": "data/raw/hpa",
            "exact_files_or_queries": "; ".join(sorted(summary["url"] for summary in hpa.values())),
            "license_or_terms": "Creative Commons Attribution 4.0 International, with third-party caveats",
            "checksum_manifest": "data/checksums/hpa_sha256.tsv",
            "notes": "HPA v25.1 replaces older plan filenames normal_tissue.tsv/pathology.tsv with current normal_ihc_data.tsv/cancer_data.tsv.",
        },
        {
            "source_id": "uniprot_reviewed_human",
            "source_name": "UniProtKB reviewed human",
            "role": "Protein identifiers, topology, TM, extracellular domains, signal peptides",
            "phase": "Fase 1 metadata complete; Fase 4 ID mapping/topology",
            "status": "metadata_verified",
            "version_or_release": uniprot.get("release", ""),
            "access_date": access_date,
            "url": "https://rest.uniprot.org/uniprotkb/search",
            "endpoint_or_file": "UniProt REST search",
            "local_raw_dir": "data/raw/uniprot",
            "exact_files_or_queries": "organism_id:9606 AND reviewed:true plus feature-specific queries",
            "license_or_terms": "UniProt terms; verify at Fase 2 download",
            "checksum_manifest": "data/checksums/uniprot_sha256.tsv",
            "notes": "Universe-specific reviewed coverage waits for HGNC/Ensembl/UniProt mapping.",
        },
        {
            "source_id": "depmap",
            "source_name": "DepMap Portal Context Explorer",
            "role": "Gastric/GEJ cell-line expression and CRISPR dependency evidence",
            "phase": "Fase 1 metadata complete; Fase 11 optional annotation",
            "status": "metadata_verified",
            "version_or_release": "DepMap Portal current release; 26Q1 label observed on portal",
            "access_date": access_date,
            "url": "https://depmap.org/portal/context_explorer/?context=STOMACH",
            "endpoint_or_file": "/portal/api/context_explorer/context_info?level_0_subtype_code=STOMACH",
            "local_raw_dir": "data/raw/depmap",
            "exact_files_or_queries": "Context Explorer STOMACH; model and modality coverage from table_data",
            "license_or_terms": "DepMap portal terms; verify at file download",
            "checksum_manifest": "data/checksums/depmap_sha256.tsv",
            "notes": f"{depmap['total_models']} Esophagus/Stomach models; EGC subset is the closest adenocarcinoma set.",
        },
        {
            "source_id": "pdc_cptac_gastric",
            "source_name": "NCI Proteomic Data Commons gastric/STAD studies",
            "role": "Incremental proteomics, phosphoproteomics, glycoproteomics, and related omics",
            "phase": "Fase 1 metadata complete; optional after HPA/scRNA/external RNA",
            "status": "metadata_verified_no_raw_downloaded",
            "version_or_release": "PDC GraphQL live query",
            "access_date": access_date,
            "url": "https://pdc.cancer.gov",
            "endpoint_or_file": "PDC GraphQL study(pdc_study_id)",
            "local_raw_dir": "data/raw/pdc_cptac",
            "exact_files_or_queries": pdc_ids,
            "license_or_terms": "PDC open access and study-specific terms; verify before download",
            "checksum_manifest": "data/checksums/pdc_cptac_sha256.tsv",
            "notes": "Candidate gene protein coverage remains TBD until Protein Assembly reports are downloaded and mapped.",
        },
        {
            "source_id": "scrna_gastric_candidates",
            "source_name": "TISCH2/GEO gastric cancer scRNA candidates",
            "role": "Malignant epithelial vs TME specificity layer",
            "phase": "Fase 1 candidate inventory; Fase 8 quality gate",
            "status": "candidate_sources_identified_not_downloaded",
            "version_or_release": "GEO/TISCH2 current at access date",
            "access_date": access_date,
            "url": "https://tisch.compbio.cn/home/",
            "endpoint_or_file": "GSE112302; GSE134520; GSE150290; GSE163558 and recent GC scRNA atlases",
            "local_raw_dir": "data/raw/scrna",
            "exact_files_or_queries": "Select datasets with malignant epithelial and TME annotations only",
            "license_or_terms": "Per GEO/TISCH2/source publication",
            "checksum_manifest": "data/checksums/scrna_sha256.tsv",
            "notes": "Do not include in main score until annotation quality and processed matrix availability pass gate.",
        },
        {
            "source_id": "external_bulk_rna_cohorts",
            "source_name": "GEO/ACRG external gastric expression cohorts",
            "role": "External RNA validation cohort",
            "phase": "Fase 1 candidate inventory; Fase 5-7 optional validation",
            "status": "candidate_sources_identified_not_downloaded",
            "version_or_release": "GEO current at access date",
            "access_date": access_date,
            "url": "https://www.ncbi.nlm.nih.gov/geo/",
            "endpoint_or_file": "GSE62254, GSE15459, GSE57303, GSE66229, GSE84437 candidates",
            "local_raw_dir": "data/raw/external_bulk_rna",
            "exact_files_or_queries": "Prioritize GSE62254/ACRG n=300 and GSE15459 n~200 if processed matrices map cleanly",
            "license_or_terms": "Per GEO/source publication",
            "checksum_manifest": "data/checksums/external_bulk_rna_sha256.tsv",
            "notes": "Layer is incremental; avoid delaying MVP if batch/platform harmonization becomes expensive.",
        },
        {
            "source_id": "structure_sources",
            "source_name": "RCSB PDB and AlphaFold DB",
            "role": "Candidate-level ECD/structure annotations",
            "phase": "Fase 10 candidate-level optional layer",
            "status": "source_declared_not_assessed",
            "version_or_release": "Current APIs at candidate query date",
            "access_date": access_date,
            "url": "https://search.rcsb.org/ ; https://alphafold.ebi.ac.uk/",
            "endpoint_or_file": "RCSB Search API; AlphaFold DB by UniProt accession",
            "local_raw_dir": "data/raw/pdb; data/raw/alphafold",
            "exact_files_or_queries": "Query only after final candidate list or top N candidates",
            "license_or_terms": "Per PDB/AlphaFold source terms",
            "checksum_manifest": "data/checksums/structures_sha256.tsv",
            "notes": "Not needed before scoring; used for candidate cards and modality discussion.",
        },
        {
            "source_id": "clinical_druggability_sources",
            "source_name": "Open Targets, ChEMBL, DGIdb, ClinicalTrials.gov",
            "role": "Clinical/druggability annotations",
            "phase": "Fase 12 candidate-level annotation",
            "status": "source_declared_not_assessed",
            "version_or_release": "Current APIs at candidate query date",
            "access_date": access_date,
            "url": "https://platform.opentargets.org/ ; https://www.ebi.ac.uk/chembl/ ; https://www.clinicaltrials.gov/",
            "endpoint_or_file": "Open Targets GraphQL/downloads; ChEMBL API; DGIdb; ClinicalTrials.gov API v2",
            "local_raw_dir": "data/raw/clinical_druggability",
            "exact_files_or_queries": "Candidate-level target/drug/trial queries after ranking",
            "license_or_terms": "Per source",
            "checksum_manifest": "data/checksums/clinical_druggability_sha256.tsv",
            "notes": "Used for candidate cards and tiering context, not to inflate discovery score.",
        },
    ]


def build_coverage_rows(summaries: dict[str, object]) -> list[dict[str, object]]:
    xena = summaries["xena"]
    gdc = summaries["gdc"]
    hpa = summaries["hpa"]
    uniprot = summaries["uniprot"]
    depmap = summaries["depmap"]
    pdc = summaries["pdc"]
    pdc_proteome = pdc.get("PDC000614", {})
    return [
        {
            "layer": "RNA tumor",
            "primary_source": "UCSC Xena / Toil TCGA-STAD",
            "status": "available_metadata_verified",
            "current_coverage": xena["tcga_stad_counts"].get("Primary Tumor", 0),
            "unit": "TCGA-STAD primary tumor samples",
            "required_before_scoring": "yes",
            "decision": "use_as_primary_expression_matrix",
            "next_action": "Download matrix and phenotype with checksums in Fase 2.",
            "notes": "GDC STAR counts provide 412 primary tumors as secondary sensitivity.",
        },
        {
            "layer": "RNA normal",
            "primary_source": "UCSC Xena / Toil GTEx stomach plus TCGA adjacent normal sensitivity",
            "status": "available_metadata_verified",
            "current_coverage": f"GTEx_stomach={xena['gtex_stomach_counts'].get('Normal Tissue', 0)}; TCGA_solid_tissue_normal={xena['tcga_stad_counts'].get('Solid Tissue Normal', 0)}",
            "unit": "samples",
            "required_before_scoring": "yes",
            "decision": "use_xena_toil_for_primary_tumor_normal; use_tcga_adjacent_normal_as_sensitivity",
            "next_action": "Download Xena matrix and run batch diagnostic before N/R scores.",
            "notes": "Do not compare independent TCGA and GTEx pipelines naively.",
        },
        {
            "layer": "HPA normal",
            "primary_source": "HPA normal_ihc_data.tsv.zip",
            "status": "available_metadata_verified",
            "current_coverage": hpa["normal_ihc_data.tsv.zip"]["matched_genes"],
            "unit": "genes with stomach normal IHC rows",
            "required_before_scoring": "yes",
            "decision": "include_in_mvp",
            "next_action": "Download HPA files and build protein_evidence.tsv.",
            "notes": "Current HPA v25.1 file name differs from older plan placeholder normal_tissue.tsv.",
        },
        {
            "layer": "HPA pathology",
            "primary_source": "HPA cancer_data.tsv.zip",
            "status": "available_metadata_verified",
            "current_coverage": hpa["cancer_data.tsv.zip"]["matched_genes"],
            "unit": "genes with stomach cancer IHC rows",
            "required_before_scoring": "yes",
            "decision": "include_in_mvp",
            "next_action": "Download HPA files and model antibody/staining reliability flags.",
            "notes": "Current HPA v25.1 file name differs from older plan placeholder pathology.tsv.",
        },
        {
            "layer": "UniProt topology",
            "primary_source": "UniProtKB reviewed human",
            "status": "available_metadata_verified_universe_specific_coverage_tbd",
            "current_coverage": f"reviewed_human={uniprot['counts']['human_reviewed']}; topological_domain={uniprot['counts']['human_reviewed_topological_domain']}; transmembrane={uniprot['counts']['human_reviewed_transmembrane']}",
            "unit": "UniProtKB entries",
            "required_before_scoring": "yes",
            "decision": "use_reviewed_human_as_topology_backbone",
            "next_action": "Map surfaceome universe genes to reviewed UniProt accessions.",
            "notes": "Universe-specific percent coverage cannot be known before ID map and universe build.",
        },
        {
            "layer": "PDB/AlphaFold",
            "primary_source": "RCSB PDB / AlphaFold DB",
            "status": "candidate_level_not_assessed",
            "current_coverage": "TBD_after_candidate_mapping",
            "unit": "candidate proteins",
            "required_before_scoring": "no",
            "decision": "candidate_card_layer_only",
            "next_action": "Query by UniProt accession after top candidates are frozen.",
            "notes": "Do not block MVP scoring on structural coverage.",
        },
        {
            "layer": "DepMap",
            "primary_source": "DepMap Context Explorer STOMACH",
            "status": "available_metadata_verified",
            "current_coverage": f"models={depmap['total_models']}; EGC={depmap['child_counts'].get('Esophagogastric Adenocarcinoma', 0)}; CRISPR={depmap['modality_counts'].get('crispr', 0)}; RNASeq={depmap['modality_counts'].get('rna_seq', 0)}",
            "unit": "models",
            "required_before_scoring": "no",
            "decision": "functional_annotation_not_hard_filter",
            "next_action": "Download selected DepMap release files only if >=5 useful gastric/EGC models remain after mapping.",
            "notes": "Lineage mixes esophagus/stomach; EGC subset is closest to gastric/GEJ adenocarcinoma.",
        },
        {
            "layer": "scRNA",
            "primary_source": "TISCH2/GEO gastric cancer candidates",
            "status": "candidate_sources_identified_quality_gate_pending",
            "current_coverage": "GSE112302; GSE134520; GSE150290; GSE163558; recent atlases",
            "unit": "datasets",
            "required_before_scoring": "no_for_mvp_yes_if_SC_component_enabled",
            "decision": "optional_SC_component_only_after_annotation_gate",
            "next_action": "Select one processed dataset with malignant epithelial vs TME labels in Fase 8.",
            "notes": "If not available, use TME marker correlation fallback and mark SC as missing/not_used.",
        },
        {
            "layer": "external cohort",
            "primary_source": "GEO/ACRG external bulk RNA",
            "status": "candidate_sources_identified",
            "current_coverage": "GSE62254 n=300; GSE15459 n~200 candidates",
            "unit": "bulk expression cohorts",
            "required_before_scoring": "no",
            "decision": "incremental_validation_layer",
            "next_action": "Assess processed matrices and platform mapping after primary pipeline works.",
            "notes": "Avoid merging platforms into the primary score without a clear validation design.",
        },
        {
            "layer": "clinical/druggability",
            "primary_source": "Open Targets, ChEMBL, DGIdb, ClinicalTrials.gov",
            "status": "candidate_level_not_assessed",
            "current_coverage": "TBD_after_candidate_list",
            "unit": "candidate genes",
            "required_before_scoring": "no",
            "decision": "candidate_card_and_tiering_context",
            "next_action": "Run candidate-level queries after ranking is frozen.",
            "notes": "Do not use druggability databases to create circular discovery claims.",
        },
        {
            "layer": "PDC/CPTAC proteomics",
            "primary_source": "NCI PDC gastric/STAD studies",
            "status": "available_metadata_verified_incremental",
            "current_coverage": f"CPTAC_STAD_proteome_cases={pdc_proteome.get('cases_count', 'TBD')}; gastric_study_ids={len(pdc)}",
            "unit": "studies/cases",
            "required_before_scoring": "no",
            "decision": "incremental_not_surface_specific",
            "next_action": "Only download Protein Assembly reports if HPA/scRNA/external RNA gates are already handled.",
            "notes": "Proteomics supports protein abundance, not cell-surface localization by itself.",
        },
    ]


def build_phase1_notes(access_date: str, summaries: dict[str, object]) -> str:
    xena = summaries["xena"]
    gdc = summaries["gdc"]
    cbio = summaries["cbioportal"]
    hpa = summaries["hpa"]
    uniprot = summaries["uniprot"]
    depmap = summaries["depmap"]
    pdc = summaries["pdc"]
    pdc_proteome = pdc.get("PDC000614", {})
    subtype_counts = format_counts(cbio["tcga_subtypes"])
    gdc_rna_counts = format_counts(gdc["gdc_rna_counts_by_type"])
    return f"""# Fase 1 Data Inventory Notes

Access date: {access_date}

This file answers the mandatory Fase 1 questions using lightweight metadata/API queries only. Large matrices are not saved yet.

## Mandatory Questions

1. TCGA-STAD expression matrix: primary matrix will be UCSC Xena/Toil `TcgaTargetGtex_rsem_gene_tpm.gz`, with phenotype `TcgaTargetGTEX_phenotype.txt.gz`. The matrix is recorded as log2(TPM+0.001); verify unit again at Fase 2 download.
2. GTEx matrix: same Xena/Toil matrix, filtered to GTEx stomach normal tissue.
3. Same pipeline or batch correction: TCGA, TARGET, and GTEx in Xena/Toil are recomputed uniformly, but batch diagnostic remains mandatory before any tumor-normal selectivity score. GDC STAR counts are secondary TCGA-only sensitivity.
4. Primary tumor, adjacent normal, metastasis: Xena phenotype has TCGA-STAD Primary Tumor={xena['tcga_stad_counts'].get('Primary Tumor', 0)}, Solid Tissue Normal={xena['tcga_stad_counts'].get('Solid Tissue Normal', 0)}, Metastatic=0; GTEx stomach Normal Tissue={xena['gtex_stomach_counts'].get('Normal Tissue', 0)}. GDC STAR-count RNA-seq has {gdc_rna_counts}.
5. TCGA subtype counts: cBioPortal PanCanAtlas patient SUBTYPE counts are {subtype_counts}.
6. Lauren/stage/grade/anatomic site/treatment data: exact Lauren subtype was not exposed in the queried GDC/cBioPortal fields. Legacy cBioPortal histological diagnosis is available for {cbio['legacy_clinical_counts'].get('cbioportal_histological_diagnosis', 0)} patients and has {cbio['lauren_like_histology_terms']} Lauren-like terms requiring curation. GDC AJCC stage={gdc['gdc_clinical_counts'].get('ajcc_pathologic_stage', 0)}, GDC grade={gdc['gdc_clinical_counts'].get('tumor_grade', 0)}, GDC tissue origin={gdc['gdc_clinical_counts'].get('tissue_or_organ_of_origin', 0)}, GDC site of resection/biopsy={gdc['gdc_clinical_counts'].get('site_of_resection_or_biopsy', 0)}, GDC treatment records={gdc['gdc_clinical_counts'].get('treatment_records', 0)}.
7. HPA version/files: HPA downloadable files are version 25.1 with Ensembl 109. Use `normal_ihc_data.tsv.zip`, `cancer_data.tsv.zip`, `subcellular_location.tsv.zip`, `rna_tissue_consensus.tsv.zip`, and `rna_tissue_gtex.tsv.zip`. The older plan names `normal_tissue.tsv` and `pathology.tsv` are superseded by current HPA file names.
8. UniProt reviewed coverage: UniProt release {uniprot['release']} has reviewed_human={uniprot['counts']['human_reviewed']}, transmembrane={uniprot['counts']['human_reviewed_transmembrane']}, topological_domain={uniprot['counts']['human_reviewed_topological_domain']}. Universe-specific coverage waits for ID mapping.
9. HPA pathology stomach cancer coverage: `cancer_data.tsv.zip` has stomach cancer rows for {hpa['cancer_data.tsv.zip']['matched_genes']} genes.
10. CPTAC/PDC gastric proteomics coverage: PDC has gastric/STAD studies including CPTAC STAD proteome `{pdc_proteome.get('pdc_study_id', 'PDC000614')}` with {pdc_proteome.get('cases_count', 'TBD')} cases and {pdc_proteome.get('aliquots_count', 'TBD')} aliquots. Candidate gene coverage is TBD until Protein Assembly reports are downloaded and mapped.
11. DepMap gastric line count: DepMap Context Explorer STOMACH has {depmap['total_models']} Esophagus/Stomach models, including EGC={depmap['child_counts'].get('Esophagogastric Adenocarcinoma', 0)} and ESCC={depmap['child_counts'].get('Esophageal Squamous Cell Carcinoma', 0)}. Modality coverage includes CRISPR={depmap['modality_counts'].get('crispr', 0)} and RNASeq={depmap['modality_counts'].get('rna_seq', 0)}.
12. scRNA gastric datasets: candidate sources include TISCH2 and GEO datasets GSE112302, GSE134520, GSE150290, GSE163558, plus recent gastric cancer scRNA atlases. They are not yet admitted to the main score; Fase 8 must verify processed matrix access and malignant epithelial vs TME annotations.

## Fase 1 Exit Status

The required files now exist:

- `results/tables/dataset_inventory.tsv`
- `results/tables/sample_counts.tsv`
- `results/tables/coverage_matrix.tsv`

Fase 1 is sufficient to proceed to Fase 2 data acquisition, with two explicit caveats:

- exact Lauren subtype is not directly available from the queried TCGA metadata and must be curated from histology or an external clinical table;
- PDC/DepMap/scRNA/structure/druggability remain incremental or candidate-level layers, not prerequisites for first scoring.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-date", default=dt.date.today().isoformat())
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Materialize the frozen Phase 1 inventory snapshot instead of querying live metadata endpoints.",
    )
    args = parser.parse_args(argv)

    if args.offline:
        materialize_offline_inventory()
        print("Materialized frozen Fase 1 inventory snapshot.")
        return 0

    sample_counts: list[dict[str, object]] = []
    summaries: dict[str, object] = {}
    summaries["gdc"] = collect_gdc_counts(sample_counts)
    summaries["xena"] = collect_xena_counts(sample_counts)
    summaries["cbioportal"] = collect_cbioportal_counts(sample_counts)
    summaries["hpa"] = collect_hpa_counts(sample_counts)
    summaries["uniprot"] = collect_uniprot_counts(sample_counts)
    summaries["depmap"] = collect_depmap_counts(sample_counts)
    summaries["pdc"] = collect_pdc_counts(sample_counts)

    inventory_rows = build_inventory_rows(args.access_date, summaries)
    coverage_rows = build_coverage_rows(summaries)

    write_tsv(
        RESULTS_DIR / "dataset_inventory.tsv",
        inventory_rows,
        [
            "source_id",
            "source_name",
            "role",
            "phase",
            "status",
            "version_or_release",
            "access_date",
            "url",
            "endpoint_or_file",
            "local_raw_dir",
            "exact_files_or_queries",
            "license_or_terms",
            "checksum_manifest",
            "notes",
        ],
    )
    write_tsv(
        RESULTS_DIR / "sample_counts.tsv",
        sample_counts,
        [
            "source_id",
            "cohort_or_dataset",
            "count_type",
            "category",
            "n",
            "unit",
            "method",
            "status",
            "endpoint_or_file",
            "notes",
        ],
    )
    write_tsv(
        RESULTS_DIR / "coverage_matrix.tsv",
        coverage_rows,
        [
            "layer",
            "primary_source",
            "status",
            "current_coverage",
            "unit",
            "required_before_scoring",
            "decision",
            "next_action",
            "notes",
        ],
    )
    (DOCS_DIR / "fase1_data_inventory.md").write_text(
        build_phase1_notes(args.access_date, summaries),
        encoding="utf-8",
        newline="\n",
    )
    print("Wrote Fase 1 inventory tables and notes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
