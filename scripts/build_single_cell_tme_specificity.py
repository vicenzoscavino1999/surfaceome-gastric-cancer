"""Build Fase 8 scRNA/TME specificity gate outputs.

The current MVP has no admitted processed gastric scRNA matrix, so this script
does not impute SC. It emits SC as not available and computes bulk TME module
correlation flags over TCGA-STAD primary tumors.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import math
import sys
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pyreadr
import yaml
from scipy.stats import pearsonr, rankdata, spearmanr


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.matplotlib_repro import configure_reproducible_svg, save_svg

RAW_DIR = REPO_ROOT / "data" / "raw"
CHECKSUM_DIR = REPO_ROOT / "data" / "checksums"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
DOCS_DIR = REPO_ROOT / "docs"
configure_reproducible_svg()

PHENOTYPE_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGTEX_phenotype.txt.gz"
MATRIX_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
ID_MAP = PROCESSED_DIR / "id_map_master.tsv"
TUMOR_EXPRESSION = PROCESSED_DIR / "tumor_expression.tsv"
CONTROLS_CONFIG = REPO_ROOT / "config" / "controls.yaml"
TME_MARKERS_CONFIG = REPO_ROOT / "config" / "tme_markers.yaml"
PURITY_RAW_DIR = RAW_DIR / "tcga_purity"
TIDYESTIMATE_URL = "https://cran.r-project.org/src/contrib/tidyestimate_1.1.1.tar.gz"
TIDYESTIMATE_TAR = PURITY_RAW_DIR / "tidyestimate_1.1.1.tar.gz"
TIDYESTIMATE_GENE_SETS_RDA = PURITY_RAW_DIR / "tidyestimate" / "data" / "gene_sets.rda"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
XENA_LOG2_PSEUDOCOUNT = 0.001


@dataclass
class TumorSample:
    sample: str
    patient_id: str


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


def ensure_tidyestimate_source() -> None:
    PURITY_RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not TIDYESTIMATE_TAR.exists():
        request = urllib.request.Request(TIDYESTIMATE_URL, headers={"User-Agent": "surfaceome-gastric-cancer-fase8/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            TIDYESTIMATE_TAR.write_bytes(response.read())
    if not TIDYESTIMATE_GENE_SETS_RDA.exists():
        with tarfile.open(TIDYESTIMATE_TAR, "r:gz") as archive:
            member = archive.getmember("tidyestimate/data/gene_sets.rda")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("tidyestimate/data/gene_sets.rda could not be read from the source archive")
            TIDYESTIMATE_GENE_SETS_RDA.parent.mkdir(parents=True, exist_ok=True)
            TIDYESTIMATE_GENE_SETS_RDA.write_bytes(source.read())


def write_purity_checksums() -> None:
    rows: list[dict[str, object]] = []
    global_entries: dict[str, str] = {}
    for path, source_id, note in [
        (
            TIDYESTIMATE_TAR,
            "tidyestimate_cran",
            "CRAN tidyestimate source package used to extract ESTIMATE stromal and immune gene signatures.",
        ),
        (
            TIDYESTIMATE_GENE_SETS_RDA,
            "tidyestimate_gene_sets",
            "Extracted ESTIMATE stromal and immune gene signatures; derived from tidyestimate data/gene_sets.rda.",
        ),
    ]:
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        checksum = sha256_file(path)
        global_entries[rel_path] = checksum
        rows.append(
            {
                "source_id": source_id,
                "action": "downloaded_or_extracted_raw",
                "local_path": rel_path,
                "filename": path.name,
                "url_or_endpoint": TIDYESTIMATE_URL if path == TIDYESTIMATE_TAR else "tidyestimate/data/gene_sets.rda inside source package",
                "retrieval_date": dt.date.today().isoformat(),
                "version_or_release": "tidyestimate 1.1.1; ESTIMATE signatures from Yoshihara et al. 2013",
                "bytes": path.stat().st_size,
                "sha256": checksum,
                "status": "ok",
                "license_or_terms": "GPL-2/GPL-3 expanded from tidyestimate package metadata",
                "notes": note,
            }
        )
    write_tsv(
        CHECKSUM_DIR / "tcga_purity_sha256.tsv",
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
            "license_or_terms",
            "notes",
        ],
    )
    update_global_sha256sums(global_entries)


def load_estimate_gene_sets() -> dict[str, list[str]]:
    ensure_tidyestimate_source()
    write_purity_checksums()
    result = pyreadr.read_r(str(TIDYESTIMATE_GENE_SETS_RDA))
    frame = result["gene_sets"]
    return {
        "stromal_signature": [str(value) for value in frame["stromal_signature"].dropna()],
        "immune_signature": [str(value) for value in frame["immune_signature"].dropna()],
    }


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fmt(value: float | int | str, digits: int = 6) -> str:
    if isinstance(value, str):
        return value
    numeric = float(value)
    if not math.isfinite(numeric):
        return ""
    if abs(numeric) >= 1000:
        return f"{numeric:.3f}"
    return f"{numeric:.{digits}f}"


def candidate_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    rows.sort(key=lambda row: row["hgnc_symbol"])
    return rows


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


def load_symbol_to_ensembl() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in read_tsv(ID_MAP):
        symbol = row.get("hgnc_symbol", "")
        ensembl = row.get("ensembl_gene_id", "")
        if symbol and ensembl:
            mapping[symbol] = ensembl
    return mapping


def load_ensembl_to_symbol() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in read_tsv(ID_MAP):
        symbol = row.get("hgnc_symbol", "")
        ensembl = row.get("ensembl_gene_id", "")
        if symbol and ensembl:
            mapping[ensembl] = symbol
    return mapping


def load_tme_control_symbols() -> set[str]:
    controls = load_yaml(CONTROLS_CONFIG)
    return {str(row["gene"]) for row in controls.get("tme_or_off_tumor_penalty_controls", [])}


def extract_xena_expression(
    wanted_ensembl: set[str],
    selected_samples: dict[str, TumorSample],
) -> tuple[list[TumorSample], dict[str, tuple[str, np.ndarray]], int]:
    with gzip.open(MATRIX_PATH, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        matrix_samples = header[1:]
        sample_to_index = {sample: idx for idx, sample in enumerate(matrix_samples)}
        ordered_samples = [selected_samples[sample] for sample in matrix_samples if sample in selected_samples]
        selected_indices = [sample_to_index[sample.sample] for sample in ordered_samples]
        if not selected_indices:
            raise RuntimeError("No TCGA-STAD primary tumor samples from phenotype were present in the Xena matrix.")

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
            values = np.fromiter((float(parts[idx]) for idx in selected_indices), dtype=np.float64, count=len(selected_indices))
            if np.isfinite(values).all():
                expression[ensembl_base] = (gene_id_full, values)
            if len(expression) == len(wanted_ensembl):
                break
    return ordered_samples, expression, duplicate_rows


def zscore(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.full(values.shape, np.nan, dtype=float)
    sd = float(np.std(finite))
    if sd == 0 or not math.isfinite(sd):
        return np.zeros(values.shape, dtype=float)
    return (values - float(np.mean(finite))) / sd


def safe_spearman(a: np.ndarray, b: np.ndarray, min_samples: int) -> tuple[float, float, int]:
    mask = np.isfinite(a) & np.isfinite(b)
    n = int(np.sum(mask))
    if n < min_samples or np.std(a[mask]) == 0 or np.std(b[mask]) == 0:
        return float("nan"), float("nan"), n
    rho, p_value = spearmanr(a[mask], b[mask])
    return float(rho), float(p_value), n


def safe_partial_spearman(a: np.ndarray, b: np.ndarray, covariate: np.ndarray, min_samples: int) -> tuple[float, float, int]:
    mask = np.isfinite(a) & np.isfinite(b) & np.isfinite(covariate)
    n = int(np.sum(mask))
    if n < min_samples or np.std(a[mask]) == 0 or np.std(b[mask]) == 0 or np.std(covariate[mask]) == 0:
        return float("nan"), float("nan"), n
    ranked_a = rankdata(a[mask], method="average")
    ranked_b = rankdata(b[mask], method="average")
    ranked_c = rankdata(covariate[mask], method="average")
    design = np.column_stack([np.ones(n, dtype=float), ranked_c])
    beta_a = np.linalg.lstsq(design, ranked_a, rcond=None)[0]
    beta_b = np.linalg.lstsq(design, ranked_b, rcond=None)[0]
    residual_a = ranked_a - design @ beta_a
    residual_b = ranked_b - design @ beta_b
    if np.std(residual_a) == 0 or np.std(residual_b) == 0:
        return float("nan"), float("nan"), n
    rho, p_value = pearsonr(residual_a, residual_b)
    return float(rho), float(p_value), n


def ss_gsea_score(ranked_matrix: np.ndarray, symbols: list[str], gene_set: set[str]) -> np.ndarray:
    common_indices = [idx for idx, symbol in enumerate(symbols) if symbol in gene_set]
    if not common_indices:
        return np.full(ranked_matrix.shape[1], np.nan, dtype=float)
    common_index_set = set(common_indices)
    scores = np.full(ranked_matrix.shape[1], np.nan, dtype=float)
    for sample_idx in range(ranked_matrix.shape[1]):
        sample_values = ranked_matrix[:, sample_idx]
        order = np.argsort(sample_values)[::-1]
        ordered_values = sample_values[order] ** 0.25
        hit_ind = np.fromiter((idx in common_index_set for idx in order), dtype=bool, count=order.size)
        no_hit_ind = ~hit_ind
        hit_sum = float(np.sum(ordered_values[hit_ind]))
        no_hit_sum = int(np.sum(no_hit_ind))
        if hit_sum == 0 or no_hit_sum == 0:
            continue
        hit_reward = np.cumsum(hit_ind * ordered_values) / hit_sum
        no_hit_penalty = np.cumsum(no_hit_ind.astype(float) / no_hit_sum)
        scores[sample_idx] = float(np.sum(hit_reward - no_hit_penalty))
    return scores


def build_estimate_purity_scores(
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
    ensembl_to_symbol: dict[str, str],
    estimate_gene_sets: dict[str, list[str]],
) -> tuple[list[dict[str, object]], np.ndarray, dict[str, object]]:
    symbol_values: dict[str, np.ndarray] = {}
    for ensembl, (_, values) in expression_by_ensembl.items():
        symbol = ensembl_to_symbol.get(ensembl, "")
        if not symbol or symbol in symbol_values:
            continue
        symbol_values[symbol] = values.astype(float)
    symbols = sorted(symbol_values)
    matrix = np.vstack([symbol_values[symbol] for symbol in symbols])
    ranked = rankdata(matrix, axis=0, method="average") * 10000.0 / matrix.shape[0]
    stromal = ss_gsea_score(ranked, symbols, set(estimate_gene_sets["stromal_signature"]))
    immune = ss_gsea_score(ranked, symbols, set(estimate_gene_sets["immune_signature"]))
    estimate_score = stromal + immune
    estimate_purity_proxy = np.cos(0.6049872018 + 0.0001467884 * estimate_score)
    estimate_purity_proxy = np.where(estimate_purity_proxy < 0, np.nan, estimate_purity_proxy)
    purity_covariate = estimate_score
    rows: list[dict[str, object]] = []
    for idx in range(matrix.shape[1]):
        rows.append(
            {
                "sample_index": idx,
                "stromal_score": fmt(float(stromal[idx])),
                "immune_score": fmt(float(immune[idx])),
                "estimate_score": fmt(float(estimate_score[idx])),
                "estimate_purity_proxy": fmt(float(estimate_purity_proxy[idx])),
                "purity_covariate": fmt(float(purity_covariate[idx])),
                "purity_source": "ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate",
            }
        )
    metadata = {
        "estimate_expression_gene_n": len(symbols),
        "estimate_stromal_signature_available": len(set(estimate_gene_sets["stromal_signature"]) & set(symbols)),
        "estimate_immune_signature_available": len(set(estimate_gene_sets["immune_signature"]) & set(symbols)),
    }
    return rows, purity_covariate, metadata


def build_module_scores(
    marker_config: dict[str, object],
    symbol_to_ensembl: dict[str, str],
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
) -> tuple[dict[str, np.ndarray], list[dict[str, object]]]:
    module_scores: dict[str, np.ndarray] = {}
    coverage_rows: list[dict[str, object]] = []
    modules: dict[str, dict[str, object]] = marker_config["tme_modules"]
    for module_id, module in modules.items():
        markers = [str(marker) for marker in module.get("markers", [])]
        available_symbols: list[str] = []
        missing_symbols: list[str] = []
        arrays: list[np.ndarray] = []
        for marker in markers:
            ensembl = symbol_to_ensembl.get(marker, "")
            expression_entry = expression_by_ensembl.get(ensembl)
            if ensembl and expression_entry is not None:
                available_symbols.append(marker)
                arrays.append(expression_entry[1])
            else:
                missing_symbols.append(marker)
        if arrays:
            module_scores[module_id] = np.mean(np.vstack(arrays), axis=0)
        coverage_rows.append(
            {
                "module_id": module_id,
                "module_label": module.get("label", module_id),
                "n_markers_declared": len(markers),
                "n_markers_available": len(available_symbols),
                "markers_available": ";".join(available_symbols),
                "markers_missing": ";".join(missing_symbols),
                "module_score_status": "computed" if arrays else "missing_all_markers",
            }
        )
    return module_scores, coverage_rows


def risk_from_correlations(
    symbol: str,
    raw_rho: float,
    partial_rho: float,
    tme_controls: set[str],
    thresholds: dict[str, object],
) -> tuple[str, str, str, str]:
    if symbol in tme_controls:
        return (
            "high_known_tme_marker_control",
            "high_known_tme_marker_control",
            "immune/TME-derived",
            "not_eligible_for_tier1_epithelial_targeting_without_cell_resolved_counterevidence",
        )
    if not math.isfinite(raw_rho):
        return (
            "not_assessable_missing_bulk_expression",
            "not_assessable_missing_bulk_expression",
            "not covered",
            "carry_as_missing_tme_flag",
        )

    if raw_rho >= float(thresholds["high_uncorrected_rho"]):
        raw_risk = "high_uncorrected_tme_correlation"
    elif raw_rho >= float(thresholds["moderate_uncorrected_rho"]):
        raw_risk = "moderate_uncorrected_tme_correlation"
    elif raw_rho >= float(thresholds["watchlist_uncorrected_rho"]):
        raw_risk = "watchlist_uncorrected_tme_correlation"
    else:
        raw_risk = "low_uncorrected_tme_correlation"

    if not math.isfinite(partial_rho):
        return (raw_risk, raw_risk, "ambiguous" if raw_risk != "low_uncorrected_tme_correlation" else "not covered", "purity_adjustment_unavailable")
    if partial_rho > float(thresholds["high_partial_rho"]):
        return (
            raw_risk,
            "high_purity_adjusted_tme_correlation",
            "ambiguous",
            "requires_cell_resolved_or_protein_membranous_tumor_cell_evidence_before_tier1",
        )
    if raw_rho > float(thresholds["moderate_uncorrected_rho"]) and partial_rho < float(thresholds["purity_confounded_partial_rho"]):
        return (
            raw_risk,
            "moderate_purity_confounded",
            "ambiguous",
            "tier1_allowed_with_explicit_purity_confounded_tme_flag",
        )
    if raw_rho >= float(thresholds["moderate_uncorrected_rho"]):
        return (
            raw_risk,
            "moderate_residual_tme_correlation",
            "ambiguous",
            "allowed_only_with_explicit_tme_contamination_flag",
        )
    if raw_rho >= float(thresholds["watchlist_uncorrected_rho"]):
        return (raw_risk, "watchlist_uncorrected_tme_correlation", "ambiguous", "review_in_candidate_card_if_prioritized")
    return (raw_risk, "low_uncorrected_tme_correlation", "not covered", "no_tme_flag_from_bulk_modules")


def build_rows() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, object],
]:
    marker_config = load_yaml(TME_MARKERS_CONFIG)
    estimate_gene_sets = load_estimate_gene_sets()
    thresholds = marker_config["risk_thresholds"]
    candidates = candidate_rows()
    symbol_to_ensembl = load_symbol_to_ensembl()
    ensembl_to_symbol = load_ensembl_to_symbol()
    tme_controls = load_tme_control_symbols()
    candidate_ensembl = {row["ensembl_gene_id"] for row in candidates if row.get("ensembl_gene_id")}
    marker_symbols = {
        str(marker)
        for module in marker_config["tme_modules"].values()
        for marker in module.get("markers", [])
    }
    estimate_symbols = set(estimate_gene_sets["stromal_signature"]) | set(estimate_gene_sets["immune_signature"])
    marker_ensembl = {symbol_to_ensembl[symbol] for symbol in marker_symbols if symbol in symbol_to_ensembl}
    estimate_ensembl = {symbol_to_ensembl[symbol] for symbol in estimate_symbols if symbol in symbol_to_ensembl}
    all_mapped_ensembl = {row.get("ensembl_gene_id", "") for row in read_tsv(ID_MAP) if row.get("ensembl_gene_id")}
    selected_samples = load_primary_tumor_samples()
    ordered_samples, expression_by_ensembl, duplicate_rows = extract_xena_expression(
        all_mapped_ensembl | candidate_ensembl | marker_ensembl | estimate_ensembl,
        selected_samples,
    )
    module_scores, module_coverage_rows = build_module_scores(marker_config, symbol_to_ensembl, expression_by_ensembl)
    estimate_stromal_symbols = set(estimate_gene_sets["stromal_signature"])
    estimate_immune_symbols = set(estimate_gene_sets["immune_signature"])
    estimate_overlap_rows: list[dict[str, object]] = []
    for module_id, module in marker_config["tme_modules"].items():
        markers = {str(marker) for marker in module.get("markers", [])}
        stromal_overlap = sorted(markers & estimate_stromal_symbols)
        immune_overlap = sorted(markers & estimate_immune_symbols)
        estimate_overlap_rows.append(
            {
                "module_id": module_id,
                "module_label": module.get("label", ""),
                "n_module_markers": len(markers),
                "n_estimate_stromal_overlap": len(stromal_overlap),
                "estimate_stromal_overlap_markers": ";".join(stromal_overlap),
                "n_estimate_immune_overlap": len(immune_overlap),
                "estimate_immune_overlap_markers": ";".join(immune_overlap),
                "interpretation_note": "Direct marker overlap is one collinearity diagnostic; ESTIMATE and TME modules also share broader immune/stromal biology.",
            }
        )
    purity_score_rows, purity_covariate, purity_metadata = build_estimate_purity_scores(
        expression_by_ensembl,
        ensembl_to_symbol,
        estimate_gene_sets,
    )
    for idx, row in enumerate(purity_score_rows):
        sample = ordered_samples[idx]
        row["sample"] = sample.sample
        row["patient_id"] = sample.patient_id
    standardized_scores = [zscore(score) for score in module_scores.values()]
    combined_tme = np.mean(np.vstack(standardized_scores), axis=0) if standardized_scores else np.array([], dtype=float)

    specificity_rows: list[dict[str, object]] = []
    flag_rows: list[dict[str, object]] = []
    correlation_rows: list[dict[str, object]] = []
    purity_rows: list[dict[str, object]] = []
    suppression_audit_rows: list[dict[str, object]] = []
    tumor_rows = {row["hgnc_symbol"]: row for row in read_tsv(TUMOR_EXPRESSION)}

    for gene in candidates:
        symbol = gene["hgnc_symbol"]
        ensembl = gene["ensembl_gene_id"]
        expression_entry = expression_by_ensembl.get(ensembl)
        if expression_entry is None:
            candidate_log = np.array([], dtype=float)
        else:
            candidate_log = expression_entry[1]

        module_stats: list[tuple[str, float, float, int]] = []
        module_partial_stats: list[tuple[str, float, float, int]] = []
        for module_id, score in module_scores.items():
            if candidate_log.size == 0:
                rho, p_value, n_samples = float("nan"), float("nan"), 0
                partial_rho, partial_p_value, partial_n_samples = float("nan"), float("nan"), 0
            else:
                rho, p_value, n_samples = safe_spearman(candidate_log, score, int(thresholds["min_samples"]))
                partial_rho, partial_p_value, partial_n_samples = safe_partial_spearman(
                    candidate_log,
                    score,
                    purity_covariate,
                    int(thresholds["min_samples"]),
                )
            module_stats.append((module_id, rho, p_value, n_samples))
            module_partial_stats.append((module_id, partial_rho, partial_p_value, partial_n_samples))
            correlation_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": ensembl,
                    "module_id": module_id,
                    "spearman_rho": fmt(rho),
                    "p_value": fmt(p_value),
                    "n_samples": n_samples,
                    "partial_spearman_rho": fmt(partial_rho),
                    "partial_p_value": fmt(partial_p_value),
                    "partial_n_samples": partial_n_samples,
                    "purity_source": "ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate",
                    "correlation_scope": "TCGA-STAD_primary_tumor_bulk_log2_TPM",
                }
            )

        finite_module_stats = [item for item in module_stats if math.isfinite(item[1])]
        if finite_module_stats:
            max_module, max_rho, max_p, max_n = max(finite_module_stats, key=lambda item: item[1])
        else:
            max_module, max_rho, max_p, max_n = "", float("nan"), float("nan"), 0
        partial_lookup = {item[0]: item for item in module_partial_stats}
        max_partial_row = partial_lookup.get(max_module, ("", float("nan"), float("nan"), 0))
        max_partial_rho = float(max_partial_row[1])
        max_partial_p = float(max_partial_row[2])
        max_partial_n = int(max_partial_row[3])
        combined_rho, combined_p, combined_n = (
            safe_spearman(candidate_log, combined_tme, int(thresholds["min_samples"]))
            if candidate_log.size and combined_tme.size
            else (float("nan"), float("nan"), 0)
        )
        combined_partial_rho, combined_partial_p, combined_partial_n = (
            safe_partial_spearman(candidate_log, combined_tme, purity_covariate, int(thresholds["min_samples"]))
            if candidate_log.size and combined_tme.size
            else (float("nan"), float("nan"), 0)
        )
        raw_risk, risk, label, tiering = risk_from_correlations(symbol, max_rho, max_partial_rho, tme_controls, thresholds)

        flag = {
            "hgnc_symbol": symbol,
            "ensembl_gene_id": ensembl,
            "surfaceome_category": gene.get("surfaceome_category", ""),
            "scRNA_gate_status": marker_config["single_cell_gate"]["status"],
            "SC_status": "not_available",
            "cellular_specificity_label": label,
            "raw_tme_contamination_risk": raw_risk,
            "tme_contamination_risk": risk,
            "max_tme_module": max_module,
            "max_tme_spearman_rho": fmt(max_rho),
            "max_tme_p_value": fmt(max_p),
            "max_tme_n_samples": max_n,
            "max_tme_partial_spearman_rho": fmt(max_partial_rho),
            "max_tme_partial_p_value": fmt(max_partial_p),
            "max_tme_partial_n_samples": max_partial_n,
            "combined_tme_spearman_rho": fmt(combined_rho),
            "combined_tme_p_value": fmt(combined_p),
            "combined_tme_n_samples": combined_n,
            "combined_tme_partial_spearman_rho": fmt(combined_partial_rho),
            "combined_tme_partial_p_value": fmt(combined_partial_p),
            "combined_tme_partial_n_samples": combined_partial_n,
            "known_tme_control": str(symbol in tme_controls).lower(),
            "median_tpm_tumor": tumor_rows.get(symbol, {}).get("median_tpm_tumor", ""),
            "E_rank_percentile": tumor_rows.get(symbol, {}).get("E_rank_percentile", ""),
            "purity_source": "ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate",
            "purity_adjustment_status": "computed_partial_spearman_with_estimate_rnaseq_relative_proxy",
            "tiering_implication": tiering,
        }
        flag_rows.append(flag)
        if raw_risk == "low_uncorrected_tme_correlation" and risk == "high_purity_adjusted_tme_correlation":
            suppression_audit_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": ensembl,
                    "surfaceome_category": gene.get("surfaceome_category", ""),
                    "transition": "low_uncorrected_to_high_purity_adjusted",
                    "max_tme_module": max_module,
                    "raw_spearman_rho": fmt(max_rho),
                    "partial_spearman_rho": fmt(max_partial_rho),
                    "delta_partial_minus_raw": fmt(max_partial_rho - max_rho),
                    "median_tpm_tumor": tumor_rows.get(symbol, {}).get("median_tpm_tumor", ""),
                    "E_rank_percentile": tumor_rows.get(symbol, {}).get("E_rank_percentile", ""),
                    "tiering_implication": tiering,
                    "audit_note": "Potential suppression pattern; high adjusted TME flag is conservative and requires cell-resolved/protein-localization review rather than automatic demotion.",
                }
            )
        specificity_rows.append(
            {
                "hgnc_symbol": symbol,
                "ensembl_gene_id": ensembl,
                "surfaceome_category": gene.get("surfaceome_category", ""),
                "selected_scrna_dataset": "",
                "scRNA_gate_status": marker_config["single_cell_gate"]["status"],
                "scRNA_data_status": "not_available_no_processed_annotated_dataset_admitted",
                "SC_status": "not_available",
                "SC_score": "",
                "SC_rank_percentile": "",
                "pct_malignant_cells_positive": "",
                "mean_expr_malignant_epithelial": "",
                "mean_expr_normal_epithelial": "",
                "max_tme_expr": "",
                "tumor_cell_specificity_index": "",
                "cellular_specificity_label": label,
                "tme_contamination_risk": risk,
                "max_tme_module": max_module,
                "max_tme_spearman_rho": fmt(max_rho),
                "max_tme_partial_spearman_rho": fmt(max_partial_rho),
                "bulk_tme_fallback_status": "computed_uncorrected_bulk_marker_correlations",
                "purity_adjustment_status": "computed_partial_spearman_with_estimate_rnaseq_relative_proxy",
            }
        )
        purity_rows.append(
            {
                "hgnc_symbol": symbol,
                "ensembl_gene_id": ensembl,
                "purity_source": "ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate",
                "purity_n_samples": int(np.sum(np.isfinite(purity_covariate))),
                "partial_correlation_status": "computed_partial_spearman_with_estimate_rnaseq_relative_proxy",
                "max_tme_module": max_module,
                "raw_spearman_rho": fmt(max_rho),
                "partial_spearman_rho": fmt(max_partial_rho),
                "partial_p_value": fmt(max_partial_p),
                "partial_n_samples": max_partial_n,
                "raw_tme_contamination_risk": raw_risk,
                "tme_contamination_risk_after_purity": risk,
                "notes": "ESTIMATE/tidyestimate RNA-seq ESTIMATE score used as a relative purity/admixture covariate; not interpreted as absolute pathologist purity.",
            }
        )

    metadata = {
        "candidate_n": len(candidates),
        "tumor_sample_n": len(ordered_samples),
        "duplicate_xena_rows": duplicate_rows,
        "module_count": len(module_scores),
        "high_or_moderate_flags": sum(
            row["tme_contamination_risk"] in {"high_purity_adjusted_tme_correlation", "moderate_residual_tme_correlation", "high_known_tme_marker_control"}
            for row in flag_rows
        ),
        "moderate_purity_confounded": sum(row["tme_contamination_risk"] == "moderate_purity_confounded" for row in flag_rows),
        "low_to_high_after_purity_adjustment": len(suppression_audit_rows),
        "known_tme_controls": ";".join(sorted(tme_controls)),
        **purity_metadata,
    }
    return (
        specificity_rows,
        flag_rows,
        correlation_rows,
        purity_rows,
        module_coverage_rows,
        purity_score_rows,
        estimate_overlap_rows,
        suppression_audit_rows,
        metadata,
    )


def plot_tme_fallback(flag_rows: list[dict[str, object]], correlation_rows: list[dict[str, object]], output: Path) -> None:
    controls = ["ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN", "PTPRC", "PECAM1"]
    top_by_rho = sorted(
        [row for row in flag_rows if row.get("max_tme_spearman_rho")],
        key=lambda row: float(row["max_tme_spearman_rho"]),
        reverse=True,
    )[:16]
    symbols = []
    for symbol in controls + [str(row["hgnc_symbol"]) for row in top_by_rho]:
        if symbol not in symbols:
            symbols.append(symbol)
    modules = sorted({row["module_id"] for row in correlation_rows})
    rho_by_symbol_module = {
        (row["hgnc_symbol"], row["module_id"]): float(row["spearman_rho"])
        for row in correlation_rows
        if row.get("spearman_rho")
    }
    x_values: list[int] = []
    y_values: list[int] = []
    colors: list[float] = []
    sizes: list[float] = []
    for y_idx, symbol in enumerate(symbols):
        for x_idx, module in enumerate(modules):
            rho = rho_by_symbol_module.get((symbol, module), float("nan"))
            if not math.isfinite(rho):
                continue
            x_values.append(x_idx)
            y_values.append(y_idx)
            colors.append(rho)
            sizes.append(30 + 160 * min(abs(rho), 1.0))

    fig, ax = plt.subplots(figsize=(8.4, max(5.0, 0.28 * len(symbols) + 1.6)))
    scatter = ax.scatter(x_values, y_values, c=colors, s=sizes, cmap="coolwarm", vmin=-1, vmax=1, edgecolor="black", linewidth=0.2)
    ax.set_xticks(range(len(modules)))
    ax.set_xticklabels(modules, rotation=35, ha="right")
    ax.set_yticks(range(len(symbols)))
    ax.set_yticklabels(symbols)
    ax.invert_yaxis()
    ax.set_title("Bulk TME marker fallback (scRNA not integrated)")
    ax.set_xlabel("Bulk TME marker module")
    ax.set_ylabel("Benchmark controls and highest TME-correlated candidates")
    ax.grid(True, linewidth=0.35, alpha=0.25)
    fig.colorbar(scatter, ax=ax, label="Spearman rho")
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    save_svg(fig, output)
    plt.close(fig)


def write_notes(
    flag_rows: list[dict[str, object]],
    module_coverage_rows: list[dict[str, object]],
    estimate_overlap_rows: list[dict[str, object]],
    suppression_audit_rows: list[dict[str, object]],
    metadata: dict[str, object],
) -> None:
    risk_counts: dict[str, int] = {}
    label_counts: dict[str, int] = {}
    for row in flag_rows:
        risk_counts[str(row["tme_contamination_risk"])] = risk_counts.get(str(row["tme_contamination_risk"]), 0) + 1
        label_counts[str(row["cellular_specificity_label"])] = label_counts.get(str(row["cellular_specificity_label"]), 0) + 1
    module_lines = "\n".join(
        f"- {row['module_id']}: {row['n_markers_available']}/{row['n_markers_declared']} markers available ({row['markers_available']})"
        for row in module_coverage_rows
    )
    risk_lines = "\n".join(f"- {risk}: {count}" for risk, count in sorted(risk_counts.items()))
    label_lines = "\n".join(f"- {label}: {count}" for label, count in sorted(label_counts.items()))
    overlap_lines = "\n".join(
        "- {module}: stromal {stromal}/{total} ({stromal_markers}); immune {immune}/{total} ({immune_markers})".format(
            module=row["module_id"],
            stromal=row["n_estimate_stromal_overlap"],
            immune=row["n_estimate_immune_overlap"],
            total=row["n_module_markers"],
            stromal_markers=row["estimate_stromal_overlap_markers"] or "none",
            immune_markers=row["estimate_immune_overlap_markers"] or "none",
        )
        for row in estimate_overlap_rows
    )
    suppression_top_rows = sorted(
        suppression_audit_rows,
        key=lambda row: float(row["partial_spearman_rho"]) if row.get("partial_spearman_rho") else float("-inf"),
        reverse=True,
    )[:10]
    suppression_module_counts: dict[str, int] = {}
    for row in suppression_audit_rows:
        module = str(row.get("max_tme_module", ""))
        suppression_module_counts[module] = suppression_module_counts.get(module, 0) + 1
    suppression_module_lines = "\n".join(
        f"- {module}: {count}" for module, count in sorted(suppression_module_counts.items())
    )
    suppression_lines = "\n".join(
        "- {symbol}: {module}, raw rho={raw}, partial rho={partial}, delta={delta}".format(
            symbol=row["hgnc_symbol"],
            module=row["max_tme_module"],
            raw=row["raw_spearman_rho"],
            partial=row["partial_spearman_rho"],
            delta=row["delta_partial_minus_raw"],
        )
        for row in suppression_top_rows
    )
    suppression_by_symbol = {str(row["hgnc_symbol"]): row for row in suppression_audit_rows}
    sentinel_symbols = ["F11R", "DAG1", "CDH1", "OCLN", "CD46", "ADAM10", "PTK7", "CGN"]
    sentinel_lines = "\n".join(
        "- {symbol}: {module}, raw rho={raw}, partial rho={partial}".format(
            symbol=symbol,
            module=suppression_by_symbol[symbol]["max_tme_module"],
            raw=suppression_by_symbol[symbol]["raw_spearman_rho"],
            partial=suppression_by_symbol[symbol]["partial_spearman_rho"],
        )
        for symbol in sentinel_symbols
        if symbol in suppression_by_symbol
    )
    (DOCS_DIR / "fase8_single_cell_tme_specificity.md").write_text(
        f"""# Fase 8 Single-Cell/TME Specificity

Access date: {dt.date.today().isoformat()}

Fase 8 was executed as the preregistered MVP fallback. No processed gastric scRNA dataset with reliable malignant epithelial versus TME annotations was admitted into the quantitative score, so `SC` is `not_available` and was not imputed.

TISCH2/GEO remain candidate sources for a later incremental scRNA layer. This run only uses TCGA-STAD primary tumor bulk RNA to flag possible TME-derived signal.

## Bulk TME Fallback

TCGA-STAD primary tumors: {metadata['tumor_sample_n']}.

Candidate genes assessed: {metadata['candidate_n']}.

TME marker modules:

{module_lines}

For each Core+Probable candidate, Spearman correlation was computed between its bulk tumor expression and each TME module score. These are flags only, not filters and not final ranking components.

## ESTIMATE-Based Purity Adjustment

Control B is implemented with the ESTIMATE stromal and immune signatures from `tidyestimate` 1.1.1. The Xena/Toil TCGA-STAD RNA-seq matrix is used to compute sample-level stromal, immune, and ESTIMATE scores. The ESTIMATE-derived value is used as a relative purity covariate for partial Spearman correlations; it is not interpreted as an absolute pathologist purity measurement.

Expression genes used for ESTIMATE scoring: {metadata['estimate_expression_gene_n']}.

Available ESTIMATE stromal signature genes: {metadata['estimate_stromal_signature_available']}/141.

Available ESTIMATE immune signature genes: {metadata['estimate_immune_signature_available']}/141.

## ESTIMATE/TME Collinearity

ESTIMATE and the TME modules are not independent measurements. ESTIMATE is built from stromal and immune signatures, while the module scores also represent stromal, endothelial, myeloid, T-cell, and B/plasma biology. Partial Spearman correlations are therefore module-dependent flags; they should not be interpreted as a clean causal decomposition of epithelial versus TME expression.

Direct marker overlap with ESTIMATE signatures:

{overlap_lines}

This overlap is an audit item, not an exclusion criterion. Low direct marker overlap does not remove broader biological collinearity, and high direct overlap does not make the module unusable; it changes how conservatively the adjusted flag should be interpreted.

## Risk Summary

{risk_lines}

Cellular labels:

{label_lines}

Known TME/off-tumor controls carried from preregistered controls: {metadata['known_tme_controls']}.

## Purity Adjustment

The file `results/tables/tme_purity_adjusted_correlations.tsv` stores the raw module correlation, partial Spearman correlation, and final TME flag after controlling for the ESTIMATE RNA-seq relative purity/admixture covariate. `moderate_purity_confounded` means `rho_raw > 0.5` but `rho_partial < 0.2`.

The file `results/tables/tme_purity_suppression_audit.tsv` stores genes that moved from `low_uncorrected_tme_correlation` to `high_purity_adjusted_tme_correlation`. These are potential suppression patterns where purity/admixture adjustment increased the TME correlation. Count in this run: {metadata['low_to_high_after_purity_adjustment']}.

Distribution of low-to-high transitions by strongest adjusted module:

{suppression_module_lines}

Top low-to-high adjusted examples by partial rho:

{suppression_lines}

Sentinel low-to-high examples for manual review:

{sentinel_lines}

Interpretation: this set mixes plausible adhesion/surface or dual-compartment biology with epithelial-lineage genes such as `CDH1`, `OCLN`, and `CGN`. A `high_purity_adjusted_tme_correlation` flag must therefore be treated as a conservative review flag, not as an automatic demotion of an epithelial candidate. Candidate interpretation must use protein/localization evidence and, if later available, cell-resolved scRNA evidence.

## Rules Preserved

- `SC` is `not_available`, not imputed.
- Bulk TME correlations and purity-adjusted correlations generate flags, not hard exclusions.
- Genes with high purity-adjusted TME correlation require cell-resolved or protein-localized counterevidence before being treated as Tier 1 epithelial tumor-cell targets.
- If a target is intentionally stromal/vascular, it must be separated into a different modality rather than mixed with epithelial tumor-cell targets.

## Outputs

- `data/processed/single_cell_specificity.tsv`
- `results/tables/tme_contamination_flags.tsv`
- `results/tables/tme_contamination_risk_mvp.tsv`
- `results/tables/tme_purity_adjusted_correlations.tsv`
- `results/tables/tme_purity_suppression_audit.tsv`
- `results/tables/tme_module_correlations.tsv`
- `results/tables/tme_estimate_marker_overlap.tsv`
- `results/tables/tumor_purity_estimate_scores.tsv`
- `results/figures/top_candidates_scRNA_dotplot.svg`
""",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    (
        specificity_rows,
        flag_rows,
        correlation_rows,
        purity_rows,
        module_coverage_rows,
        purity_score_rows,
        estimate_overlap_rows,
        suppression_audit_rows,
        metadata,
    ) = build_rows()

    specificity_fields = [
        "hgnc_symbol",
        "ensembl_gene_id",
        "surfaceome_category",
        "selected_scrna_dataset",
        "scRNA_gate_status",
        "scRNA_data_status",
        "SC_status",
        "SC_score",
        "SC_rank_percentile",
        "pct_malignant_cells_positive",
        "mean_expr_malignant_epithelial",
        "mean_expr_normal_epithelial",
        "max_tme_expr",
        "tumor_cell_specificity_index",
        "cellular_specificity_label",
        "tme_contamination_risk",
        "max_tme_module",
        "max_tme_spearman_rho",
        "max_tme_partial_spearman_rho",
        "bulk_tme_fallback_status",
        "purity_adjustment_status",
    ]
    flag_fields = [
        "hgnc_symbol",
        "ensembl_gene_id",
        "surfaceome_category",
        "scRNA_gate_status",
        "SC_status",
        "cellular_specificity_label",
        "raw_tme_contamination_risk",
        "tme_contamination_risk",
        "max_tme_module",
        "max_tme_spearman_rho",
        "max_tme_p_value",
        "max_tme_n_samples",
        "max_tme_partial_spearman_rho",
        "max_tme_partial_p_value",
        "max_tme_partial_n_samples",
        "combined_tme_spearman_rho",
        "combined_tme_p_value",
        "combined_tme_n_samples",
        "combined_tme_partial_spearman_rho",
        "combined_tme_partial_p_value",
        "combined_tme_partial_n_samples",
        "known_tme_control",
        "median_tpm_tumor",
        "E_rank_percentile",
        "purity_source",
        "purity_adjustment_status",
        "tiering_implication",
    ]
    write_tsv(PROCESSED_DIR / "single_cell_specificity.tsv", specificity_rows, specificity_fields)
    write_tsv(TABLES_DIR / "tme_contamination_flags.tsv", flag_rows, flag_fields)
    write_tsv(TABLES_DIR / "tme_contamination_risk_mvp.tsv", flag_rows, flag_fields)
    write_tsv(
        TABLES_DIR / "tme_module_correlations.tsv",
        correlation_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "module_id",
            "spearman_rho",
            "p_value",
            "n_samples",
            "partial_spearman_rho",
            "partial_p_value",
            "partial_n_samples",
            "purity_source",
            "correlation_scope",
        ],
    )
    write_tsv(
        TABLES_DIR / "tme_purity_adjusted_correlations.tsv",
        purity_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "purity_source",
            "purity_n_samples",
            "partial_correlation_status",
            "max_tme_module",
            "raw_spearman_rho",
            "partial_spearman_rho",
            "partial_p_value",
            "partial_n_samples",
            "raw_tme_contamination_risk",
            "tme_contamination_risk_after_purity",
            "notes",
        ],
    )
    write_tsv(
        TABLES_DIR / "tumor_purity_estimate_scores.tsv",
        purity_score_rows,
        [
            "sample",
            "patient_id",
            "sample_index",
            "stromal_score",
            "immune_score",
            "estimate_score",
            "estimate_purity_proxy",
            "purity_covariate",
            "purity_source",
        ],
    )
    write_tsv(
        TABLES_DIR / "tme_estimate_marker_overlap.tsv",
        estimate_overlap_rows,
        [
            "module_id",
            "module_label",
            "n_module_markers",
            "n_estimate_stromal_overlap",
            "estimate_stromal_overlap_markers",
            "n_estimate_immune_overlap",
            "estimate_immune_overlap_markers",
            "interpretation_note",
        ],
    )
    write_tsv(
        TABLES_DIR / "tme_purity_suppression_audit.tsv",
        suppression_audit_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "surfaceome_category",
            "transition",
            "max_tme_module",
            "raw_spearman_rho",
            "partial_spearman_rho",
            "delta_partial_minus_raw",
            "median_tpm_tumor",
            "E_rank_percentile",
            "tiering_implication",
            "audit_note",
        ],
    )
    write_tsv(
        TABLES_DIR / "tme_module_marker_coverage.tsv",
        module_coverage_rows,
        [
            "module_id",
            "module_label",
            "n_markers_declared",
            "n_markers_available",
            "markers_available",
            "markers_missing",
            "module_score_status",
        ],
    )
    plot_tme_fallback(flag_rows, correlation_rows, FIGURES_DIR / "top_candidates_scRNA_dotplot.svg")
    write_notes(flag_rows, module_coverage_rows, estimate_overlap_rows, suppression_audit_rows, metadata)
    print("Wrote Fase 8 single-cell/TME specificity MVP fallback outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
