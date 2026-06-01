"""Build Fase 5 TCGA-STAD tumor-expression and heterogeneity tables."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.special import erfc


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
RAW_CBIO_DIR = RAW_DIR / "cbioportal"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CHECKSUM_DIR = REPO_ROOT / "data" / "checksums"
TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
DOCS_DIR = REPO_ROOT / "docs"

PHENOTYPE_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGTEX_phenotype.txt.gz"
MATRIX_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
ID_MAP = PROCESSED_DIR / "id_map_master.tsv"
GDC_CASES = RAW_DIR / "gdc_tcga_stad" / "cases_tcga_stad.json"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"

CBIO_STUDY_ID = "stad_tcga_pan_can_atlas_2018"
CBIO_BASE = "https://www.cbioportal.org/api"
CBIO_PATIENT_CLINICAL_URL = (
    f"{CBIO_BASE}/studies/{CBIO_STUDY_ID}/clinical-data"
    "?clinicalDataType=PATIENT&projection=DETAILED"
)
CBIO_GISTIC_URL = (
    f"{CBIO_BASE}/molecular-profiles/{CBIO_STUDY_ID}_gistic"
    "/molecular-data/fetch?projection=SUMMARY"
)
CBIO_PATIENT_CLINICAL_RAW = RAW_CBIO_DIR / f"{CBIO_STUDY_ID}_patient_clinical_data.json"
CBIO_GISTIC_RAW = RAW_CBIO_DIR / f"{CBIO_STUDY_ID}_gistic_erbb2_fgfr2_met.json"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
SUBTYPE_ORDER = ["STAD_EBV", "STAD_MSI", "STAD_GS", "STAD_CIN", "STAD_POLE", "unassigned"]
AMPLIFICATION_TARGETS = ["ERBB2", "FGFR2", "MET"]
XENA_LOG2_PSEUDOCOUNT = 0.001


@dataclass
class TumorSample:
    sample: str
    patient_id: str
    subtype: str = "unassigned"
    stage_group: str = "unavailable"
    tissue_origin: str = "unavailable"
    histology_proxy: str = "unavailable"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 8), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_global_sha256sums(entries: dict[str, str]) -> None:
    path = CHECKSUM_DIR / "sha256sums.txt"
    current: dict[str, str] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                checksum, rel_path = stripped.split(maxsplit=1)
                current[rel_path.strip()] = checksum
    current.update(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for rel_path in sorted(current):
            handle.write(f"{current[rel_path]}  {rel_path}\n")


def load_parameters() -> dict[str, object]:
    return yaml.safe_load(PARAMETERS_CONFIG.read_text(encoding="utf-8"))


def fetch_json_raw(
    url: str,
    output: Path,
    payload: dict[str, object] | None = None,
    force: bool = False,
    offline: bool = False,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    output.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "Accept": "application/json",
        "User-Agent": "surfaceome-gastric-cancer-fase5/0.1",
    }
    if output.exists() and not force:
        raw = output.read_bytes()
        return json.loads(raw.decode("utf-8")), {"source": "cache"}
    if offline:
        rel_path = output.relative_to(REPO_ROOT).as_posix()
        raise FileNotFoundError(
            f"Frozen cBioPortal input is missing: {rel_path}. "
            "Restore the archived data/raw bundle or rerun live acquisition explicitly outside the reviewer path."
        )

    data: bytes | None = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
        meta = {
            "source": "download",
            "last_modified": response.headers.get("Last-Modified", ""),
            "content_length": response.headers.get("Content-Length", ""),
        }
    output.write_bytes(raw)
    return json.loads(raw.decode("utf-8")), meta


def write_cbioportal_checksums(download_meta: dict[str, dict[str, str]]) -> None:
    rows: list[dict[str, object]] = []
    global_entries: dict[str, str] = {}
    for path, url, action, note in [
        (
            CBIO_PATIENT_CLINICAL_RAW,
            CBIO_PATIENT_CLINICAL_URL,
            "downloaded_raw_metadata",
            "cBioPortal patient-level clinical attributes, including TCGA molecular subtype and AJCC stage.",
        ),
        (
            CBIO_GISTIC_RAW,
            CBIO_GISTIC_URL,
            "downloaded_raw_molecular_data",
            "cBioPortal GISTIC discrete CNA calls for ERBB2, FGFR2, and MET amplification context.",
        ),
    ]:
        if not path.exists():
            continue
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        checksum = sha256_file(path)
        global_entries[rel_path] = checksum
        meta = download_meta.get(rel_path, {})
        rows.append(
            {
                "source_id": "cbioportal_stad_tcga",
                "action": action,
                "local_path": rel_path,
                "filename": path.name,
                "url_or_endpoint": url,
                "retrieval_date": dt.date.today().isoformat(),
                "version_or_release": f"{CBIO_STUDY_ID} API live query",
                "bytes": path.stat().st_size,
                "sha256": checksum,
                "status": "ok",
                "last_modified": meta.get("last_modified", ""),
                "content_length": meta.get("content_length", ""),
                "license_or_terms": "cBioPortal public API terms",
                "notes": note,
            }
        )
    write_tsv(
        CHECKSUM_DIR / "cbioportal_sha256.tsv",
        rows,
        [
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
        ],
    )
    update_global_sha256sums(global_entries)


def load_primary_tumor_samples() -> dict[str, TumorSample]:
    selected: dict[str, TumorSample] = {}
    with gzip.open(PHENOTYPE_PATH, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if (
                row.get("_study") == "TCGA"
                and row.get("detailed_category") == "Stomach Adenocarcinoma"
                and row.get("_sample_type") == "Primary Tumor"
            ):
                sample = row["sample"]
                selected[sample] = TumorSample(sample=sample, patient_id=sample[:12])
    return selected


def clinical_records_by_patient(records: list[dict[str, object]]) -> dict[str, dict[str, str]]:
    by_patient: dict[str, dict[str, str]] = {}
    for record in records:
        patient_id = str(record.get("patientId", ""))
        attr = str(record.get("clinicalAttributeId", ""))
        value = str(record.get("value", "")).strip()
        if not patient_id or not attr:
            continue
        by_patient.setdefault(patient_id, {})[attr] = value
    return by_patient


def collapse_stage(value: str) -> str:
    cleaned = value.strip()
    upper = cleaned.upper()
    if not cleaned or upper in {"NA", "NAN", "NOT REPORTED", "UNKNOWN"}:
        return "unavailable"
    if "STAGE IV" in upper:
        return "Stage IV"
    if "STAGE III" in upper:
        return "Stage III"
    if "STAGE II" in upper:
        return "Stage II"
    if "STAGE I" in upper:
        return "Stage I"
    return cleaned


def load_gdc_covariates() -> dict[str, dict[str, str]]:
    data = json.loads(GDC_CASES.read_text(encoding="utf-8"))
    covariates: dict[str, dict[str, str]] = {}
    for case in data.get("data", {}).get("hits", []):
        patient_id = case.get("submitter_id", "")
        diagnoses = case.get("diagnoses") or []
        primary = next(
            (
                diagnosis
                for diagnosis in diagnoses
                if str(diagnosis.get("classification_of_tumor", "")).lower() == "primary"
            ),
            diagnoses[0] if diagnoses else {},
        )
        origin = str(primary.get("tissue_or_organ_of_origin", "") or "").strip() or "unavailable"
        diagnosis = str(primary.get("primary_diagnosis", "") or "").strip() or "unavailable"
        covariates[patient_id] = {
            "tissue_origin": origin,
            "histology_proxy": classify_histology_proxy(diagnosis),
            "primary_diagnosis": diagnosis,
        }
    return covariates


def classify_histology_proxy(primary_diagnosis: str) -> str:
    lower = primary_diagnosis.lower()
    if "intestinal" in lower or "tubular" in lower or "papillary" in lower:
        return "intestinal_like_proxy"
    if "diffuse" in lower or "signet" in lower:
        return "diffuse_or_signet_like_proxy"
    if "mixed" in lower:
        return "mixed_proxy"
    if primary_diagnosis and primary_diagnosis.lower() not in {"not reported", "unknown", "unavailable"}:
        return "adenocarcinoma_nos_or_other_proxy"
    return "unavailable"


def annotate_samples(samples: dict[str, TumorSample], patient_clinical: dict[str, dict[str, str]], gdc_covariates: dict[str, dict[str, str]]) -> None:
    for sample in samples.values():
        clinical = patient_clinical.get(sample.patient_id, {})
        sample.subtype = clinical.get("SUBTYPE", "").strip() or "unassigned"
        sample.stage_group = collapse_stage(clinical.get("AJCC_PATHOLOGIC_TUMOR_STAGE", ""))
        gdc_row = gdc_covariates.get(sample.patient_id, {})
        sample.tissue_origin = gdc_row.get("tissue_origin", "unavailable") or "unavailable"
        sample.histology_proxy = gdc_row.get("histology_proxy", "unavailable") or "unavailable"


def candidate_universe() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    rows.sort(key=lambda row: row["hgnc_symbol"])
    return rows


def load_expression_rows(wanted_ensembl: set[str], selected_samples: dict[str, TumorSample]) -> tuple[list[TumorSample], dict[str, tuple[str, np.ndarray]], int]:
    with gzip.open(MATRIX_PATH, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        matrix_samples = header[1:]
        sample_to_index = {sample: idx for idx, sample in enumerate(matrix_samples)}
        ordered_samples = [selected_samples[sample] for sample in matrix_samples if sample in selected_samples]
        selected_indices = [sample_to_index[sample.sample] for sample in ordered_samples]
        if not selected_indices:
            raise RuntimeError("No TCGA-STAD primary tumor samples from the phenotype file were present in the Xena matrix.")

        expression: dict[str, tuple[str, np.ndarray]] = {}
        duplicate_rows = 0
        for raw_line in handle:
            gene_id_full, values_text = raw_line.rstrip("\n").split("\t", 1)
            ensembl_base = gene_id_full.split(".", 1)[0]
            if ensembl_base not in wanted_ensembl:
                continue
            if ensembl_base in expression:
                duplicate_rows += 1
                continue
            parts = values_text.split("\t")
            values = np.fromiter((float(parts[idx]) for idx in selected_indices), dtype=np.float32, count=len(selected_indices))
            if not np.isfinite(values).all():
                continue
            expression[ensembl_base] = (gene_id_full, values)
            if len(expression) == len(wanted_ensembl):
                break
    return ordered_samples, expression, duplicate_rows


def log2_to_tpm(values: np.ndarray) -> np.ndarray:
    return np.maximum(np.exp2(values.astype(np.float64)) - XENA_LOG2_PSEUDOCOUNT, 0.0)


def trimmed_mean(values: np.ndarray, trim_fraction: float = 0.10) -> float:
    finite = np.sort(values[np.isfinite(values)])
    if finite.size == 0:
        return float("nan")
    trim = int(math.floor(finite.size * trim_fraction))
    if trim > 0 and finite.size > trim * 2:
        finite = finite[trim:-trim]
    return float(np.mean(finite))


def expression_metrics(values_tpm: np.ndarray) -> dict[str, float]:
    finite = values_tpm[np.isfinite(values_tpm)]
    if finite.size == 0:
        return {
            "n": 0,
            "median": float("nan"),
            "robust_mean": float("nan"),
            "p75": float("nan"),
            "p90": float("nan"),
            "pct_gt_1": float("nan"),
            "pct_gt_5": float("nan"),
        }
    return {
        "n": float(finite.size),
        "median": float(np.median(finite)),
        "robust_mean": trimmed_mean(finite),
        "p75": float(np.percentile(finite, 75.0)),
        "p90": float(np.percentile(finite, 90.0)),
        "pct_gt_1": float(np.mean(finite > 1.0)),
        "pct_gt_5": float(np.mean(finite > 5.0)),
    }


def rank_percentiles(values_by_symbol: dict[str, float]) -> dict[str, float]:
    symbols = sorted(values_by_symbol)
    values = np.array([values_by_symbol[symbol] for symbol in symbols], dtype=float)
    finite_mask = np.isfinite(values)
    finite_symbols = [symbol for symbol, is_finite in zip(symbols, finite_mask) if is_finite]
    finite_values = values[finite_mask]
    if finite_values.size == 0:
        return {}
    order = np.argsort(finite_values, kind="mergesort")
    ranks = np.zeros(finite_values.size, dtype=float)
    start = 0
    while start < finite_values.size:
        end = start + 1
        while end < finite_values.size and finite_values[order[end]] == finite_values[order[start]]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    if finite_values.size == 1:
        percentiles = np.ones(1, dtype=float)
    else:
        percentiles = (ranks - 1.0) / (finite_values.size - 1.0)
    return {symbol: float(value) for symbol, value in zip(finite_symbols, percentiles)}


def fmt(value: float | int | str, digits: int = 6) -> str:
    if isinstance(value, str):
        return value
    numeric = float(value)
    if not math.isfinite(numeric):
        return ""
    if abs(numeric) >= 1000:
        return f"{numeric:.3f}"
    return f"{numeric:.{digits}f}"


def build_tumor_expression(
    universe: list[dict[str, str]],
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
) -> tuple[list[dict[str, object]], dict[str, np.ndarray], dict[str, str]]:
    raw_rows: list[dict[str, object]] = []
    log_values_by_symbol: dict[str, np.ndarray] = {}
    symbol_to_xena_gene_id: dict[str, str] = {}
    metric_values: dict[str, dict[str, float]] = {
        "median": {},
        "pct_gt_1": {},
        "p75": {},
        "p90": {},
    }
    for row in universe:
        symbol = row["hgnc_symbol"]
        ensembl = row["ensembl_gene_id"]
        expression_entry = expression_by_ensembl.get(ensembl)
        base = {
            "hgnc_symbol": symbol,
            "ensembl_gene_id": ensembl,
            "uniprot_accession": row.get("uniprot_accession", ""),
            "surfaceome_category": row.get("surfaceome_category", ""),
            "tumor_sample_source": "Xena/Toil TCGA-STAD Primary Tumor",
        }
        if expression_entry is None:
            raw_rows.append(
                {
                    **base,
                    "n_tumor_samples": "",
                    "median_tpm_tumor": "",
                    "robust_mean_tpm_tumor": "",
                    "p75_tpm_tumor": "",
                    "p90_tpm_tumor": "",
                    "pct_samples_tpm_gt_1": "",
                    "pct_samples_tpm_gt_5": "",
                    "median_tpm_rank_percentile": "",
                    "pct_gt_1_rank_percentile": "",
                    "p75_tpm_rank_percentile": "",
                    "p90_tpm_rank_percentile": "",
                    "E_score": "",
                    "E_rank_percentile": "",
                    "expression_data_status": "missing_xena_expression",
                    "xena_gene_id": "",
                }
            )
            continue
        xena_gene_id, log_values = expression_entry
        tpm_values = log2_to_tpm(log_values)
        metrics = expression_metrics(tpm_values)
        log_values_by_symbol[symbol] = log_values
        symbol_to_xena_gene_id[symbol] = xena_gene_id
        for metric_name, output_name in [
            ("median", "median"),
            ("pct_gt_1", "pct_gt_1"),
            ("p75", "p75"),
            ("p90", "p90"),
        ]:
            metric_values[metric_name][symbol] = metrics[output_name]
        raw_rows.append(
            {
                **base,
                "n_tumor_samples": int(metrics["n"]),
                "median_tpm_tumor": metrics["median"],
                "robust_mean_tpm_tumor": metrics["robust_mean"],
                "p75_tpm_tumor": metrics["p75"],
                "p90_tpm_tumor": metrics["p90"],
                "pct_samples_tpm_gt_1": metrics["pct_gt_1"],
                "pct_samples_tpm_gt_5": metrics["pct_gt_5"],
                "median_tpm_rank_percentile": "",
                "pct_gt_1_rank_percentile": "",
                "p75_tpm_rank_percentile": "",
                "p90_tpm_rank_percentile": "",
                "E_score": "",
                "E_rank_percentile": "",
                "expression_data_status": "measured",
                "xena_gene_id": xena_gene_id,
            }
        )

    metric_ranks = {name: rank_percentiles(values) for name, values in metric_values.items()}
    e_scores: dict[str, float] = {}
    for symbol in metric_ranks["median"]:
        e_scores[symbol] = (
            0.40 * metric_ranks["median"][symbol]
            + 0.30 * metric_ranks["pct_gt_1"][symbol]
            + 0.20 * metric_ranks["p75"][symbol]
            + 0.10 * metric_ranks["p90"][symbol]
        )
    e_rank_percentiles = rank_percentiles(e_scores)
    for row in raw_rows:
        symbol = str(row["hgnc_symbol"])
        if symbol not in e_scores:
            continue
        row["median_tpm_rank_percentile"] = metric_ranks["median"][symbol]
        row["pct_gt_1_rank_percentile"] = metric_ranks["pct_gt_1"][symbol]
        row["p75_tpm_rank_percentile"] = metric_ranks["p75"][symbol]
        row["p90_tpm_rank_percentile"] = metric_ranks["p90"][symbol]
        row["E_score"] = e_scores[symbol]
        row["E_rank_percentile"] = e_rank_percentiles[symbol]

    formatted_rows = []
    for row in raw_rows:
        formatted_rows.append(
            {
                key: fmt(value)
                if key
                in {
                    "median_tpm_tumor",
                    "robust_mean_tpm_tumor",
                    "p75_tpm_tumor",
                    "p90_tpm_tumor",
                    "pct_samples_tpm_gt_1",
                    "pct_samples_tpm_gt_5",
                    "median_tpm_rank_percentile",
                    "pct_gt_1_rank_percentile",
                    "p75_tpm_rank_percentile",
                    "p90_tpm_rank_percentile",
                    "E_score",
                    "E_rank_percentile",
                }
                else value
                for key, value in row.items()
            }
        )
    formatted_rows.sort(key=lambda item: str(item["hgnc_symbol"]))
    return formatted_rows, log_values_by_symbol, symbol_to_xena_gene_id


def claim_scope(n: int, params: dict[str, object], extra_note: str = "", allow_tier1_context: bool = True) -> str:
    subtype_params = params["subtype_analysis"]
    if allow_tier1_context and n >= int(subtype_params["min_n_for_tier_1_subtype_only"]):
        base = "quantitative_and_tier1_subtype_context_allowed"
    elif n >= int(subtype_params["min_n_for_quantitative_claim"]):
        base = "quantitative_claim_allowed"
    elif n >= int(subtype_params["min_n_for_descriptive_report"]):
        base = "descriptive_only"
    else:
        base = "insufficient_n"
    return f"{base};{extra_note}" if extra_note else base


def subtype_sort_key(value: str) -> tuple[int, str]:
    if value in SUBTYPE_ORDER:
        return (SUBTYPE_ORDER.index(value), value)
    return (len(SUBTYPE_ORDER), value)


def build_sample_count_rows(
    samples: list[TumorSample],
    patient_clinical: dict[str, dict[str, str]],
    params: dict[str, object],
) -> list[dict[str, object]]:
    sample_counts: dict[str, int] = {}
    for sample in samples:
        sample_counts[sample.subtype] = sample_counts.get(sample.subtype, 0) + 1
    patient_counts: dict[str, int] = {}
    for clinical in patient_clinical.values():
        subtype = clinical.get("SUBTYPE", "").strip() or "unassigned"
        patient_counts[subtype] = patient_counts.get(subtype, 0) + 1
    rows: list[dict[str, object]] = []
    all_subtypes = sorted(set(sample_counts) | set(patient_counts), key=subtype_sort_key)
    thresholds = params["subtype_analysis"]
    for subtype in all_subtypes:
        n_samples = sample_counts.get(subtype, 0)
        rows.append(
            {
                "subtype": subtype,
                "n_primary_tumor_samples": n_samples,
                "n_cbioportal_patients": patient_counts.get(subtype, 0),
                "n_cbioportal_patients_without_xena_primary": max(patient_counts.get(subtype, 0) - n_samples, 0),
                "descriptive_report_allowed": str(n_samples >= int(thresholds["min_n_for_descriptive_report"])).lower(),
                "quantitative_claim_allowed": str(n_samples >= int(thresholds["min_n_for_quantitative_claim"])).lower(),
                "tier1_subtype_only_allowed": str(n_samples >= int(thresholds["min_n_for_tier_1_subtype_only"])).lower(),
                "claim_scope": claim_scope(n_samples, params),
            }
        )
    return rows


def grouped_expression_rows(
    universe: list[dict[str, str]],
    log_values_by_symbol: dict[str, np.ndarray],
    samples: list[TumorSample],
    group_values: dict[str, list[int]],
    group_type: str,
    params: dict[str, object],
    extra_note: str = "",
    allow_tier1_context: bool = True,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    all_indices = np.arange(len(samples))
    for gene in universe:
        symbol = gene["hgnc_symbol"]
        log_values = log_values_by_symbol.get(symbol)
        if log_values is None:
            continue
        tpm_values = log2_to_tpm(log_values)
        for level in sorted(group_values):
            indices = np.array(group_values[level], dtype=int)
            if indices.size == 0:
                continue
            other = np.setdiff1d(all_indices, indices, assume_unique=False)
            group_metrics = expression_metrics(tpm_values[indices])
            other_metrics = expression_metrics(tpm_values[other]) if other.size else {}
            subtype_log_median = float(np.median(log_values[indices]))
            other_log_median = float(np.median(log_values[other])) if other.size else float("nan")
            rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": gene["ensembl_gene_id"],
                    "group_type": group_type,
                    "group_level": level,
                    "n_group_samples": int(group_metrics["n"]),
                    "n_other_primary_tumor_samples": int(other.size),
                    "median_tpm_group": fmt(group_metrics["median"]),
                    "p75_tpm_group": fmt(group_metrics["p75"]),
                    "p90_tpm_group": fmt(group_metrics["p90"]),
                    "pct_samples_tpm_gt_1_group": fmt(group_metrics["pct_gt_1"]),
                    "pct_samples_tpm_gt_5_group": fmt(group_metrics["pct_gt_5"]),
                    "median_tpm_other_tumors": fmt(other_metrics.get("median", float("nan"))),
                    "median_log2_tpm_plus_001_group": fmt(subtype_log_median),
                    "median_log2_tpm_plus_001_other_tumors": fmt(other_log_median),
                    "median_log2_tpm_delta_vs_other_tumors": fmt(subtype_log_median - other_log_median),
                    "claim_scope": claim_scope(int(group_metrics["n"]), params, extra_note, allow_tier1_context),
                }
            )
    rows.sort(key=lambda item: (str(item["hgnc_symbol"]), str(item["group_type"]), str(item["group_level"])))
    return rows


def build_group_index(samples: list[TumorSample], attribute: str, minimum_n: int = 1) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for idx, sample in enumerate(samples):
        value = str(getattr(sample, attribute)).strip() or "unavailable"
        groups.setdefault(value, []).append(idx)
    return {level: indices for level, indices in groups.items() if len(indices) >= minimum_n}


def build_clinical_count_rows(samples: list[TumorSample], params: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    covariates = [
        ("ajcc_pathologic_stage_collapsed", "stage_group", ""),
        ("tissue_or_organ_of_origin", "tissue_origin", ""),
        ("histology_proxy_not_lauren", "histology_proxy", "proxy_only_not_lauren_claim"),
    ]
    for covariate_type, attribute, note in covariates:
        groups = build_group_index(samples, attribute)
        for level in sorted(groups):
            n = len(groups[level])
            rows.append(
                {
                    "covariate_type": covariate_type,
                    "covariate_level": level,
                    "n_primary_tumor_samples": n,
                    "descriptive_report_allowed": str(n >= int(params["subtype_analysis"]["min_n_for_descriptive_report"])).lower(),
                    "quantitative_claim_allowed": str(n >= int(params["subtype_analysis"]["min_n_for_quantitative_claim"])).lower(),
                    "claim_scope": claim_scope(n, params, note, allow_tier1_context=False),
                }
            )
    return rows


def bh_rejections(p_values: np.ndarray, q: float) -> np.ndarray:
    order = np.argsort(p_values, kind="mergesort")
    sorted_p = p_values[order]
    thresholds = q * np.arange(1, sorted_p.size + 1) / sorted_p.size
    passed = sorted_p <= thresholds
    rejected = np.zeros_like(p_values, dtype=bool)
    if not np.any(passed):
        return rejected
    max_idx = int(np.max(np.flatnonzero(passed)))
    rejected[order[: max_idx + 1]] = True
    return rejected


def simulate_power(
    n_group: int,
    n_other: int,
    n_tests: int,
    seed: int,
    simulations: int = 200,
    alternative_fraction: float = 0.10,
    q: float = 0.05,
    target_power: float = 0.80,
) -> dict[str, object]:
    if n_group < 2 or n_other < 2:
        return {
            "min_detectable_standardized_shift": "",
            "achieved_power": "",
            "achieved_fdr": "",
            "status": "insufficient_n_for_power_simulation",
        }
    deltas = np.arange(0.25, 3.0001, 0.25)
    rng = np.random.default_rng(seed)
    n_alt = max(1, int(round(n_tests * alternative_fraction)))
    se = math.sqrt(1.0 / n_group + 1.0 / n_other)
    best: dict[str, object] | None = None
    for delta in deltas:
        powers: list[float] = []
        fdrs: list[float] = []
        effect_z_mean = delta / se
        for _ in range(simulations):
            z = rng.normal(0.0, 1.0, size=n_tests)
            z[:n_alt] += effect_z_mean
            p_values = erfc(np.abs(z) / math.sqrt(2.0))
            rejected = bh_rejections(p_values, q=q)
            true_positives = int(np.sum(rejected[:n_alt]))
            false_positives = int(np.sum(rejected[n_alt:]))
            total_rejected = true_positives + false_positives
            powers.append(true_positives / n_alt)
            fdrs.append(false_positives / total_rejected if total_rejected else 0.0)
        mean_power = float(np.mean(powers))
        mean_fdr = float(np.mean(fdrs))
        if mean_power >= target_power:
            best = {
                "min_detectable_standardized_shift": float(delta),
                "achieved_power": mean_power,
                "achieved_fdr": mean_fdr,
                "status": "target_power_reached",
            }
            break
    if best is None:
        best = {
            "min_detectable_standardized_shift": f">{float(deltas[-1]):.2f}",
            "achieved_power": float(mean_power),
            "achieved_fdr": float(mean_fdr),
            "status": "target_power_not_reached_at_max_grid",
        }
    return best


def build_power_rows(samples: list[TumorSample], log_values_by_symbol: dict[str, np.ndarray], params: dict[str, object]) -> list[dict[str, object]]:
    subtype_groups = build_group_index(samples, "subtype")
    n_tests = len(log_values_by_symbol)
    stacked = np.vstack(list(log_values_by_symbol.values()))
    empirical_sds = np.std(stacked, axis=1, ddof=1)
    median_empirical_sd = float(np.median(empirical_sds[np.isfinite(empirical_sds)]))
    seed_base = int(params["random"].get("subtype_power_seed", params["random"]["global_seed"]))
    rows: list[dict[str, object]] = []
    for idx, subtype in enumerate(sorted(subtype_groups, key=subtype_sort_key)):
        n_group = len(subtype_groups[subtype])
        n_other = len(samples) - n_group
        result = simulate_power(n_group=n_group, n_other=n_other, n_tests=n_tests, seed=seed_base + idx)
        standardized = result["min_detectable_standardized_shift"]
        if isinstance(standardized, float):
            log2_shift = standardized * median_empirical_sd
        else:
            log2_shift = ""
        rows.append(
            {
                "subtype": subtype,
                "n_subtype_samples": n_group,
                "n_other_primary_tumor_samples": n_other,
                "n_tests": n_tests,
                "alternative_fraction": "0.10",
                "simulations_per_delta": 200,
                "bh_fdr": "0.05",
                "target_power": "0.80",
                "median_empirical_log2_sd": fmt(median_empirical_sd),
                "min_detectable_standardized_shift": fmt(standardized) if isinstance(standardized, float) else standardized,
                "approx_min_detectable_log2_tpm_shift": fmt(log2_shift) if isinstance(log2_shift, float) else "",
                "achieved_power": fmt(result["achieved_power"]) if result["achieved_power"] != "" else "",
                "achieved_fdr": fmt(result["achieved_fdr"]) if result["achieved_fdr"] != "" else "",
                "status": result["status"],
                "power_model": "normal-approximation two-group log2(TPM+0.001) shift; 10% non-null genes; BH-FDR 0.05",
            }
        )
    return rows


def fetch_cna_data(
    id_map: dict[str, dict[str, str]],
    force: bool = False,
    offline: bool = False,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    entrez_ids = []
    for symbol in AMPLIFICATION_TARGETS:
        row = id_map.get(symbol, {})
        entrez = row.get("entrez_id", "")
        if entrez:
            entrez_ids.append(int(entrez))
    payload = {
        "entrezGeneIds": entrez_ids,
        "sampleListId": f"{CBIO_STUDY_ID}_cna",
    }
    data, meta = fetch_json_raw(
        CBIO_GISTIC_URL,
        CBIO_GISTIC_RAW,
        payload=payload,
        force=force,
        offline=offline,
    )
    return data, meta


def build_cna_expression_rows(
    cna_records: list[dict[str, object]],
    id_map: dict[str, dict[str, str]],
    log_values_by_symbol: dict[str, np.ndarray],
    samples: list[TumorSample],
) -> list[dict[str, object]]:
    entrez_to_symbol = {
        int(row["entrez_id"]): symbol
        for symbol, row in id_map.items()
        if symbol in AMPLIFICATION_TARGETS and row.get("entrez_id")
    }
    patient_to_index = {sample.patient_id: idx for idx, sample in enumerate(samples)}
    grouped: dict[str, list[tuple[int, int]]] = {symbol: [] for symbol in AMPLIFICATION_TARGETS}
    for record in cna_records:
        symbol = entrez_to_symbol.get(int(record.get("entrezGeneId", -1)))
        if symbol is None:
            continue
        patient_id = str(record.get("patientId", ""))
        if patient_id not in patient_to_index:
            continue
        grouped.setdefault(symbol, []).append((patient_to_index[patient_id], int(record.get("value", 0))))
    rows: list[dict[str, object]] = []
    for symbol in AMPLIFICATION_TARGETS:
        records = grouped.get(symbol, [])
        log_values = log_values_by_symbol.get(symbol)
        if log_values is None:
            rows.append(
                {
                    "hgnc_symbol": symbol,
                    "n_cna_samples_matched_to_xena": len(records),
                    "n_high_amplification": "",
                    "pct_high_amplification": "",
                    "n_gain_or_amplification": "",
                    "pct_gain_or_amplification": "",
                    "median_tpm_high_amp": "",
                    "median_tpm_non_high_amp": "",
                    "median_log2_delta_high_amp_vs_non_amp": "",
                    "status": "target_missing_xena_expression",
                }
            )
            continue
        amp_indices = np.array([idx for idx, value in records if value == 2], dtype=int)
        gain_indices = np.array([idx for idx, value in records if value >= 1], dtype=int)
        non_amp_indices = np.array([idx for idx, value in records if value != 2], dtype=int)
        tpm = log2_to_tpm(log_values)
        amp_median = float(np.median(tpm[amp_indices])) if amp_indices.size else float("nan")
        non_amp_median = float(np.median(tpm[non_amp_indices])) if non_amp_indices.size else float("nan")
        amp_log = float(np.median(log_values[amp_indices])) if amp_indices.size else float("nan")
        non_amp_log = float(np.median(log_values[non_amp_indices])) if non_amp_indices.size else float("nan")
        n_records = len(records)
        rows.append(
            {
                "hgnc_symbol": symbol,
                "n_cna_samples_matched_to_xena": n_records,
                "n_high_amplification": int(amp_indices.size),
                "pct_high_amplification": fmt(amp_indices.size / n_records if n_records else float("nan")),
                "n_gain_or_amplification": int(gain_indices.size),
                "pct_gain_or_amplification": fmt(gain_indices.size / n_records if n_records else float("nan")),
                "median_tpm_high_amp": fmt(amp_median),
                "median_tpm_non_high_amp": fmt(non_amp_median),
                "median_log2_delta_high_amp_vs_non_amp": fmt(amp_log - non_amp_log),
                "status": "computed" if amp_indices.size else "no_high_amplification_in_matched_samples",
            }
        )
    return rows


def build_covariate_availability_rows(
    samples: list[TumorSample],
    cna_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    n = len(samples)
    available_subtype = sum(1 for sample in samples if sample.subtype != "unassigned")
    available_stage = sum(1 for sample in samples if sample.stage_group != "unavailable")
    available_site = sum(1 for sample in samples if sample.tissue_origin != "unavailable")
    histology_proxy = sum(1 for sample in samples if sample.histology_proxy != "unavailable")
    cna_ok = sum(1 for row in cna_rows if row.get("status") == "computed")
    return [
        {
            "covariate": "TCGA molecular subtype",
            "availability": "available",
            "n_primary_tumor_samples_with_value": available_subtype,
            "n_primary_tumor_samples_total": n,
            "action": "used_for_subtype_expression_and_power_analysis",
            "notes": "cBioPortal patient-level SUBTYPE mapped by TCGA patient barcode.",
        },
        {
            "covariate": "Lauren subtype",
            "availability": "not_available_as_exact_field",
            "n_primary_tumor_samples_with_value": "",
            "n_primary_tumor_samples_total": n,
            "action": "not_used_for_quantitative_lauren_claims",
            "notes": "GDC primary diagnosis can provide only a flagged histology proxy; exact Lauren claims remain blocked.",
        },
        {
            "covariate": "Histology proxy",
            "availability": "available_proxy_only",
            "n_primary_tumor_samples_with_value": histology_proxy,
            "n_primary_tumor_samples_total": n,
            "action": "counted_but_not_treated_as_lauren",
            "notes": "Proxy labels are descriptive and explicitly not equivalent to Lauren subtype.",
        },
        {
            "covariate": "AJCC pathologic stage",
            "availability": "available",
            "n_primary_tumor_samples_with_value": available_stage,
            "n_primary_tumor_samples_total": n,
            "action": "included_in_clinical_covariate_expression_table",
            "notes": "cBioPortal AJCC stage collapsed to Stage I-IV for sample-size stability.",
        },
        {
            "covariate": "Anatomic tissue origin",
            "availability": "available",
            "n_primary_tumor_samples_with_value": available_site,
            "n_primary_tumor_samples_total": n,
            "action": "included_in_clinical_covariate_expression_table",
            "notes": "GDC tissue_or_organ_of_origin mapped by TCGA patient barcode.",
        },
        {
            "covariate": "Tumor purity",
            "availability": "not_available_in_current_raw_sources",
            "n_primary_tumor_samples_with_value": "",
            "n_primary_tumor_samples_total": n,
            "action": "not_purity_adjusted_in_fase5",
            "notes": "No purity/stromal/immune estimate field was present in queried cBioPortal patient or sample clinical attributes.",
        },
        {
            "covariate": "Copy-number amplification",
            "availability": "available_for_selected_targets",
            "n_primary_tumor_samples_with_value": "",
            "n_primary_tumor_samples_total": n,
            "action": "computed_for_ERBB2_FGFR2_MET",
            "notes": f"{cna_ok}/{len(cna_rows)} selected amplified targets had high-amplification expression contrast rows.",
        },
    ]


def plot_expression_distribution(tumor_rows: list[dict[str, object]], output: Path) -> None:
    measured = [row for row in tumor_rows if row.get("expression_data_status") == "measured"]
    medians = np.array([float(row["median_tpm_tumor"]) for row in measured], dtype=float)
    pct_gt_1 = np.array([float(row["pct_samples_tpm_gt_1"]) for row in measured], dtype=float)
    e_scores = np.array([float(row["E_score"]) for row in measured], dtype=float)
    symbols = [str(row["hgnc_symbol"]) for row in measured]
    log_median = np.log10(medians + 0.01)

    fig, (ax_hist, ax_scatter) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    ax_hist.hist(log_median, bins=45, color="#4b5563", edgecolor="white", linewidth=0.4)
    ax_hist.set_xlabel("log10(median TPM + 0.01)")
    ax_hist.set_ylabel("Core+Probable genes")
    ax_hist.set_title("Tumor expression distribution")
    ax_hist.grid(axis="y", linewidth=0.35, alpha=0.25)

    scatter = ax_scatter.scatter(log_median, pct_gt_1, c=e_scores, cmap="viridis", s=16, alpha=0.78, linewidths=0)
    ax_scatter.set_xlabel("log10(median TPM + 0.01)")
    ax_scatter.set_ylabel("Fraction TPM > 1")
    ax_scatter.set_title("Fase 5 E component inputs")
    ax_scatter.grid(True, linewidth=0.35, alpha=0.25)
    fig.colorbar(scatter, ax=ax_scatter, label="E score")

    highlight = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN"}
    for symbol in highlight:
        if symbol not in symbols:
            continue
        idx = symbols.index(symbol)
        ax_scatter.annotate(
            symbol,
            (log_median[idx], pct_gt_1[idx]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
        )

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="svg")
    plt.close(fig)


def write_notes(
    tumor_rows: list[dict[str, object]],
    subtype_counts: list[dict[str, object]],
    power_rows: list[dict[str, object]],
    cna_rows: list[dict[str, object]],
    covariate_availability: list[dict[str, object]],
    duplicate_xena_rows: int,
) -> None:
    measured = [row for row in tumor_rows if row.get("expression_data_status") == "measured"]
    missing = [row for row in tumor_rows if row.get("expression_data_status") != "measured"]
    subtype_lines = "\n".join(
        f"- {row['subtype']}: n={row['n_primary_tumor_samples']} ({row['claim_scope']})"
        for row in subtype_counts
    )
    power_lines = "\n".join(
        f"- {row['subtype']}: min standardized shift {row['min_detectable_standardized_shift']} ({row['status']})"
        for row in power_rows
    )
    cna_lines = "\n".join(
        f"- {row['hgnc_symbol']}: high amp {row['n_high_amplification']}/{row['n_cna_samples_matched_to_xena']}, status={row['status']}"
        for row in cna_rows
    )
    availability_lines = "\n".join(
        f"- {row['covariate']}: {row['availability']} -> {row['action']}"
        for row in covariate_availability
    )
    (DOCS_DIR / "fase5_tumor_expression.md").write_text(
        f"""# Fase 5 Tumor Expression

Access date: {dt.date.today().isoformat()}

Fase 5 computes the tumor-expression component for the Fase 4 Core+Probable surfaceome universe using Xena/Toil TCGA-STAD primary tumor RNA. Xena values are stored as `log2(TPM + {XENA_LOG2_PSEUDOCOUNT})`; they were transformed back to TPM as `2^x - {XENA_LOG2_PSEUDOCOUNT}` and clipped at zero.

## Scope

- Candidate universe: {len(tumor_rows)} Core+Probable genes.
- Genes with measured Xena expression: {len(measured)}.
- Genes missing Xena expression: {len(missing)}.
- Duplicate Xena Ensembl-base rows skipped after first match: {duplicate_xena_rows}.

## E Score

The preregistered tumor-expression score is:

`E_raw = 0.40 * rank(median_TPM_tumor) + 0.30 * rank(percent_samples_TPM_gt_1) + 0.20 * rank(P75_TPM_tumor) + 0.10 * rank(P90_TPM_tumor)`

Ranks are percentile ranks among measured Core+Probable genes; higher expression and prevalence produce higher values. `E_score` is a component score only, not a final target ranking.

## Subtype Counts

{subtype_lines}

## Subtype Power

The subtype power simulation is an approximate two-group log2-expression model with 10% non-null genes and BH-FDR 0.05 across the measured Core+Probable universe.

{power_lines}

## Covariate Availability

{availability_lines}

Stage and anatomic-origin expression summaries are included because the fields were available. Exact Lauren subtype and tumor purity were not available in the current raw sources and are not silently imputed. Histology proxy counts are retained only as a limitation/audit item and must not be described as Lauren subtype.

## Amplification Context

Frozen cBioPortal GISTIC JSON calls were used for ERBB2, FGFR2, and MET to support amplified-target context.

{cna_lines}

## Outputs

- `data/processed/tumor_expression.tsv`
- `results/figures/tumor_expression_distribution.svg`
- `results/tables/subtype_expression.tsv`
- `results/tables/subtype_sample_counts.tsv`
- `results/tables/subtype_power_analysis.tsv`
- `results/tables/clinical_covariate_expression.tsv`
- `results/tables/clinical_covariate_sample_counts.tsv`
- `results/tables/fase5_covariate_availability.tsv`
- `results/tables/amplified_target_cna_expression.tsv`
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use frozen local cBioPortal/GISTIC JSON inputs only; fail if they are absent.",
    )
    args = parser.parse_args(argv)

    params = load_parameters()
    universe = candidate_universe()
    id_map = {row["hgnc_symbol"]: row for row in read_tsv(ID_MAP)}
    selected_samples = load_primary_tumor_samples()

    download_meta: dict[str, dict[str, str]] = {}
    clinical_records, clinical_meta = fetch_json_raw(
        CBIO_PATIENT_CLINICAL_URL,
        CBIO_PATIENT_CLINICAL_RAW,
        force=args.force_download,
        offline=args.offline,
    )
    download_meta[CBIO_PATIENT_CLINICAL_RAW.relative_to(REPO_ROOT).as_posix()] = clinical_meta
    patient_clinical = clinical_records_by_patient(clinical_records)
    annotate_samples(selected_samples, patient_clinical, load_gdc_covariates())

    wanted_ensembl = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    ordered_samples, expression_by_ensembl, duplicate_xena_rows = load_expression_rows(wanted_ensembl, selected_samples)
    tumor_rows, log_values_by_symbol, _ = build_tumor_expression(universe, expression_by_ensembl)

    subtype_count_rows = build_sample_count_rows(ordered_samples, patient_clinical, params)
    subtype_groups = build_group_index(ordered_samples, "subtype")
    subtype_rows = grouped_expression_rows(
        universe,
        log_values_by_symbol,
        ordered_samples,
        subtype_groups,
        "TCGA_molecular_subtype",
        params,
        "subtype_annotation_only",
    )
    clinical_count_rows = build_clinical_count_rows(ordered_samples, params)
    stage_rows = grouped_expression_rows(
        universe,
        log_values_by_symbol,
        ordered_samples,
        build_group_index(ordered_samples, "stage_group", minimum_n=1),
        "ajcc_pathologic_stage_collapsed",
        params,
        allow_tier1_context=False,
    )
    site_rows = grouped_expression_rows(
        universe,
        log_values_by_symbol,
        ordered_samples,
        build_group_index(ordered_samples, "tissue_origin", minimum_n=1),
        "tissue_or_organ_of_origin",
        params,
        allow_tier1_context=False,
    )
    power_rows = build_power_rows(ordered_samples, log_values_by_symbol, params)
    cna_records, cna_meta = fetch_cna_data(id_map, force=args.force_download, offline=args.offline)
    download_meta[CBIO_GISTIC_RAW.relative_to(REPO_ROOT).as_posix()] = cna_meta
    cna_rows = build_cna_expression_rows(cna_records, id_map, log_values_by_symbol, ordered_samples)
    covariate_availability = build_covariate_availability_rows(ordered_samples, cna_rows)

    write_tsv(
        PROCESSED_DIR / "tumor_expression.tsv",
        tumor_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "uniprot_accession",
            "surfaceome_category",
            "tumor_sample_source",
            "n_tumor_samples",
            "median_tpm_tumor",
            "robust_mean_tpm_tumor",
            "p75_tpm_tumor",
            "p90_tpm_tumor",
            "pct_samples_tpm_gt_1",
            "pct_samples_tpm_gt_5",
            "median_tpm_rank_percentile",
            "pct_gt_1_rank_percentile",
            "p75_tpm_rank_percentile",
            "p90_tpm_rank_percentile",
            "E_score",
            "E_rank_percentile",
            "expression_data_status",
            "xena_gene_id",
        ],
    )
    write_tsv(
        TABLES_DIR / "subtype_sample_counts.tsv",
        subtype_count_rows,
        [
            "subtype",
            "n_primary_tumor_samples",
            "n_cbioportal_patients",
            "n_cbioportal_patients_without_xena_primary",
            "descriptive_report_allowed",
            "quantitative_claim_allowed",
            "tier1_subtype_only_allowed",
            "claim_scope",
        ],
    )
    grouped_fieldnames = [
        "hgnc_symbol",
        "ensembl_gene_id",
        "group_type",
        "group_level",
        "n_group_samples",
        "n_other_primary_tumor_samples",
        "median_tpm_group",
        "p75_tpm_group",
        "p90_tpm_group",
        "pct_samples_tpm_gt_1_group",
        "pct_samples_tpm_gt_5_group",
        "median_tpm_other_tumors",
        "median_log2_tpm_plus_001_group",
        "median_log2_tpm_plus_001_other_tumors",
        "median_log2_tpm_delta_vs_other_tumors",
        "claim_scope",
    ]
    write_tsv(TABLES_DIR / "subtype_expression.tsv", subtype_rows, grouped_fieldnames)
    write_tsv(TABLES_DIR / "clinical_covariate_expression.tsv", stage_rows + site_rows, grouped_fieldnames)
    write_tsv(
        TABLES_DIR / "clinical_covariate_sample_counts.tsv",
        clinical_count_rows,
        [
            "covariate_type",
            "covariate_level",
            "n_primary_tumor_samples",
            "descriptive_report_allowed",
            "quantitative_claim_allowed",
            "claim_scope",
        ],
    )
    write_tsv(
        TABLES_DIR / "subtype_power_analysis.tsv",
        power_rows,
        [
            "subtype",
            "n_subtype_samples",
            "n_other_primary_tumor_samples",
            "n_tests",
            "alternative_fraction",
            "simulations_per_delta",
            "bh_fdr",
            "target_power",
            "median_empirical_log2_sd",
            "min_detectable_standardized_shift",
            "approx_min_detectable_log2_tpm_shift",
            "achieved_power",
            "achieved_fdr",
            "status",
            "power_model",
        ],
    )
    write_tsv(
        TABLES_DIR / "amplified_target_cna_expression.tsv",
        cna_rows,
        [
            "hgnc_symbol",
            "n_cna_samples_matched_to_xena",
            "n_high_amplification",
            "pct_high_amplification",
            "n_gain_or_amplification",
            "pct_gain_or_amplification",
            "median_tpm_high_amp",
            "median_tpm_non_high_amp",
            "median_log2_delta_high_amp_vs_non_amp",
            "status",
        ],
    )
    write_tsv(
        TABLES_DIR / "fase5_covariate_availability.tsv",
        covariate_availability,
        [
            "covariate",
            "availability",
            "n_primary_tumor_samples_with_value",
            "n_primary_tumor_samples_total",
            "action",
            "notes",
        ],
    )
    plot_expression_distribution(tumor_rows, FIGURES_DIR / "tumor_expression_distribution.svg")
    write_cbioportal_checksums(download_meta)
    write_notes(
        tumor_rows,
        subtype_count_rows,
        power_rows,
        cna_rows,
        covariate_availability,
        duplicate_xena_rows,
    )
    print("Wrote Fase 5 tumor-expression, subtype, covariate, and amplified-target outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
