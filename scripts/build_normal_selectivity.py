"""Build Fase 6 normal-expression, selectivity, and off-tumor risk tables."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import math
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.special import erfc
from scipy.stats import mannwhitneyu


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.matplotlib_repro import configure_reproducible_svg, save_svg

RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
DOCS_DIR = REPO_ROOT / "docs"
configure_reproducible_svg()

PHENOTYPE_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGTEX_phenotype.txt.gz"
MATRIX_PATH = RAW_DIR / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
HPA_RNA_CONSENSUS = RAW_DIR / "hpa" / "rna_tissue_consensus.tsv.zip"
HPA_NORMAL_IHC = RAW_DIR / "hpa" / "normal_ihc_data.tsv.zip"
SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
TUMOR_EXPRESSION = PROCESSED_DIR / "tumor_expression.tsv"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"
TISSUE_MAPPINGS_CONFIG = REPO_ROOT / "config" / "tissue_mappings.yaml"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
XENA_LOG2_PSEUDOCOUNT = 0.001
HPA_LEVEL_SCORE = {"Not detected": 0, "Low": 1, "Medium": 2, "High": 3}
HPA_LEVEL_LABEL = {0: "Not detected", 1: "Low", 2: "Medium", 3: "High"}


@dataclass
class SelectedSample:
    sample: str
    comparison_groups: set[str] = field(default_factory=set)
    xena_tissue: str = ""


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


def bool_text(value: bool) -> str:
    return str(value).lower()


def log2_to_tpm(values: np.ndarray) -> np.ndarray:
    return np.maximum(np.exp2(values.astype(np.float64)) - XENA_LOG2_PSEUDOCOUNT, 0.0)


def finite_median(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    return float(np.median(finite))


def finite_percentile(values: np.ndarray, percentile: float) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    return float(np.percentile(finite, percentile))


def rank_percentiles(values_by_symbol: dict[str, float]) -> dict[str, float]:
    symbols = sorted(values_by_symbol)
    values = np.array([values_by_symbol[symbol] for symbol in symbols], dtype=float)
    finite_mask = np.isfinite(values)
    finite_symbols = [symbol for symbol, ok in zip(symbols, finite_mask) if ok]
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


def bh_fdr(p_values: list[float]) -> list[float]:
    p = np.array(p_values, dtype=float)
    fdr = np.full(p.size, np.nan, dtype=float)
    finite = np.isfinite(p)
    if not np.any(finite):
        return fdr.tolist()
    finite_indices = np.flatnonzero(finite)
    finite_p = p[finite]
    order = np.argsort(finite_p, kind="mergesort")
    ranked_p = finite_p[order]
    m = ranked_p.size
    adjusted = ranked_p * m / np.arange(1, m + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    fdr[finite_indices[order]] = adjusted
    return fdr.tolist()


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


def candidate_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    rows.sort(key=lambda row: row["hgnc_symbol"])
    return rows


def tumor_expression_by_symbol() -> dict[str, dict[str, str]]:
    return {row["hgnc_symbol"]: row for row in read_tsv(TUMOR_EXPRESSION)}


def load_selected_samples(mappings: dict[str, object]) -> tuple[dict[str, SelectedSample], dict[str, list[str]]]:
    critical_organs: dict[str, dict[str, object]] = mappings["critical_organs"]
    xena_category_to_organs: dict[str, list[str]] = {}
    for organ, config in critical_organs.items():
        for category in config.get("xena_detailed_categories", []):
            xena_category_to_organs.setdefault(str(category), []).append(str(organ))

    selected: dict[str, SelectedSample] = {}
    sample_counts_by_group: dict[str, list[str]] = {}
    with gzip.open(PHENOTYPE_PATH, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sample = row["sample"]
            study = row["_study"]
            category = row["detailed_category"]
            sample_type = row["_sample_type"]
            entry = SelectedSample(sample=sample)
            if study == "TCGA" and category == "Stomach Adenocarcinoma" and sample_type == "Primary Tumor":
                entry.comparison_groups.add("tcga_stad_primary_tumor")
            elif study == "TCGA" and category == "Stomach Adenocarcinoma" and sample_type == "Solid Tissue Normal":
                entry.comparison_groups.add("tcga_stad_adjacent_normal")
            elif study == "GTEX" and category == "Stomach" and sample_type == "Normal Tissue":
                entry.comparison_groups.add("gtex_stomach_normal")
                entry.xena_tissue = category
            elif study == "GTEX" and sample_type == "Normal Tissue" and category in xena_category_to_organs:
                entry.xena_tissue = category
            else:
                continue

            if entry.comparison_groups or entry.xena_tissue:
                selected[sample] = entry
                for group in entry.comparison_groups:
                    sample_counts_by_group.setdefault(group, []).append(sample)
                if entry.xena_tissue:
                    sample_counts_by_group.setdefault(f"xena_tissue::{entry.xena_tissue}", []).append(sample)
                    for organ in xena_category_to_organs.get(entry.xena_tissue, []):
                        sample_counts_by_group.setdefault(f"organ::{organ}", []).append(sample)
    return selected, sample_counts_by_group


def extract_xena_expression(
    wanted_ensembl: set[str],
    selected_samples: dict[str, SelectedSample],
) -> tuple[list[SelectedSample], dict[str, tuple[str, np.ndarray]], dict[str, list[int]], dict[str, list[int]]]:
    with gzip.open(MATRIX_PATH, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        matrix_samples = header[1:]
        sample_to_matrix_idx = {sample: idx for idx, sample in enumerate(matrix_samples)}
        ordered_samples = [selected_samples[sample] for sample in matrix_samples if sample in selected_samples]
        selected_indices = [sample_to_matrix_idx[sample.sample] for sample in ordered_samples]
        if not selected_indices:
            raise RuntimeError("No selected normal/tumor Xena samples were present in the matrix header.")

        comparison_indices: dict[str, list[int]] = {
            "tcga_stad_primary_tumor": [],
            "gtex_stomach_normal": [],
            "tcga_stad_adjacent_normal": [],
        }
        tissue_indices: dict[str, list[int]] = {}
        for selected_pos, sample in enumerate(ordered_samples):
            for group in sample.comparison_groups:
                comparison_indices.setdefault(group, []).append(selected_pos)
            if sample.xena_tissue:
                tissue_indices.setdefault(sample.xena_tissue, []).append(selected_pos)

        expression: dict[str, tuple[str, np.ndarray]] = {}
        for raw_line in handle:
            gene_id_full, values_text = raw_line.rstrip("\n").split("\t", 1)
            ensembl_base = gene_id_full.split(".", 1)[0]
            if ensembl_base not in wanted_ensembl:
                continue
            if ensembl_base in expression:
                continue
            parts = values_text.split("\t")
            values = np.fromiter((float(parts[idx]) for idx in selected_indices), dtype=np.float32, count=len(selected_indices))
            if not np.isfinite(values).all():
                continue
            expression[ensembl_base] = (gene_id_full, values)
            if len(expression) == len(wanted_ensembl):
                break
    return ordered_samples, expression, comparison_indices, tissue_indices


def load_hpa_rna_by_organ(universe: list[dict[str, str]], mappings: dict[str, object]) -> dict[str, dict[str, float]]:
    wanted = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    tissue_to_organs: dict[str, list[str]] = {}
    for organ, config in mappings["critical_organs"].items():
        for tissue in config.get("hpa_rna_tissues", []):
            tissue_to_organs.setdefault(str(tissue).lower(), []).append(str(organ))
    values: dict[str, dict[str, float]] = {row["ensembl_gene_id"]: {} for row in universe}
    with zipfile.ZipFile(HPA_RNA_CONSENSUS) as archive:
        with archive.open(archive.namelist()[0]) as raw:
            reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
            for row in reader:
                ensembl = row["Gene"].split(".", 1)[0]
                if ensembl not in wanted:
                    continue
                organs = tissue_to_organs.get(row["Tissue"].lower(), [])
                if not organs:
                    continue
                try:
                    ntpm = float(row["nTPM"])
                except ValueError:
                    continue
                if row["Tissue"].lower() == "stomach":
                    current_stomach = values.setdefault(ensembl, {}).get("_stomach", float("nan"))
                    if not math.isfinite(current_stomach) or ntpm > current_stomach:
                        values[ensembl]["_stomach"] = ntpm
                for organ in organs:
                    current = values.setdefault(ensembl, {}).get(organ, float("nan"))
                    if not math.isfinite(current) or ntpm > current:
                        values[ensembl][organ] = ntpm
    return values


def load_hpa_ihc_by_organ(universe: list[dict[str, str]], mappings: dict[str, object]) -> tuple[dict[str, dict[str, int]], list[dict[str, object]]]:
    wanted = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    tissue_to_organs: dict[str, list[str]] = {}
    for organ, config in mappings["critical_organs"].items():
        for tissue in config.get("hpa_ihc_tissues", []):
            tissue_to_organs.setdefault(str(tissue).lower(), []).append(str(organ))
    scores: dict[str, dict[str, int]] = {row["ensembl_gene_id"]: {} for row in universe}
    details: dict[tuple[str, str], list[str]] = {}
    with zipfile.ZipFile(HPA_NORMAL_IHC) as archive:
        with archive.open(archive.namelist()[0]) as raw:
            reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
            for row in reader:
                ensembl = row["Gene"].split(".", 1)[0]
                if ensembl not in wanted:
                    continue
                organs = tissue_to_organs.get(row["Tissue"].lower(), [])
                if not organs:
                    continue
                level = HPA_LEVEL_SCORE.get(row["Level"])
                if level is None:
                    continue
                for organ in organs:
                    current = scores.setdefault(ensembl, {}).get(organ, -1)
                    if level > current:
                        scores[ensembl][organ] = level
                    if level >= 2:
                        details.setdefault((ensembl, organ), []).append(
                            f"{row['Tissue']}:{row['Cell type']}:{row['Level']}:{row['Reliability']}"
                        )
    rows: list[dict[str, object]] = []
    ensembl_to_symbol = {row["ensembl_gene_id"]: row["hgnc_symbol"] for row in universe}
    for ensembl, organ_scores in scores.items():
        for organ, score in sorted(organ_scores.items()):
            rows.append(
                {
                    "hgnc_symbol": ensembl_to_symbol.get(ensembl, ""),
                    "ensembl_gene_id": ensembl,
                    "organ": organ,
                    "hpa_normal_protein_max_level_score": score,
                    "hpa_normal_protein_max_level": HPA_LEVEL_LABEL.get(score, ""),
                    "medium_high_cell_type_evidence": ";".join(sorted(set(details.get((ensembl, organ), [])))[:8]),
                }
            )
    rows.sort(key=lambda item: (str(item["hgnc_symbol"]), str(item["organ"])))
    return scores, rows


def max_finite(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    return float(max(finite))


def organ_expression_for_gene(
    log_values: np.ndarray,
    tissue_indices: dict[str, list[int]],
    organ_config: dict[str, object],
    hpa_rna_values: dict[str, float],
) -> tuple[dict[str, float], dict[str, str]]:
    organ_values: dict[str, float] = {}
    organ_sources: dict[str, str] = {}
    for organ, config in organ_config.items():
        xena_tissue_medians: list[float] = []
        for tissue in config.get("xena_detailed_categories", []):
            indices = tissue_indices.get(str(tissue), [])
            if not indices:
                continue
            tpm = log2_to_tpm(log_values[np.array(indices, dtype=int)])
            xena_tissue_medians.append(finite_median(tpm))
        xena_max = max_finite(xena_tissue_medians)
        hpa_value = hpa_rna_values.get(organ, float("nan"))
        combined = max_finite([xena_max, hpa_value])
        organ_values[organ] = combined
        if math.isfinite(xena_max) and math.isfinite(hpa_value):
            organ_sources[organ] = "xena_tissue_median+hpa_rna_ntpm_max" if hpa_value > xena_max else "xena_tissue_median_max+hpa_rna_ntpm"
        elif math.isfinite(xena_max):
            organ_sources[organ] = "xena_tissue_median_max"
        elif math.isfinite(hpa_value):
            organ_sources[organ] = "hpa_rna_ntpm"
        else:
            organ_sources[organ] = "missing"
    return organ_values, organ_sources


def run_tumor_normal_tests(
    universe: list[dict[str, str]],
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
    comparison_indices: dict[str, list[int]],
    pseudocount: float,
    positive_rule: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, dict[str, dict[str, float]]]]:
    comparisons = [
        ("tumor_vs_gtex_stomach", "tcga_stad_primary_tumor", "gtex_stomach_normal"),
        ("tumor_vs_tcga_adjacent", "tcga_stad_primary_tumor", "tcga_stad_adjacent_normal"),
    ]
    raw_rows: list[dict[str, object]] = []
    stats_by_symbol: dict[str, dict[str, dict[str, float]]] = {}
    for gene in universe:
        symbol = gene["hgnc_symbol"]
        ensembl = gene["ensembl_gene_id"]
        expression_entry = expression_by_ensembl.get(ensembl)
        if expression_entry is None:
            continue
        _, log_values = expression_entry
        for comparison, tumor_group, normal_group in comparisons:
            tumor_indices = np.array(comparison_indices[tumor_group], dtype=int)
            normal_indices = np.array(comparison_indices[normal_group], dtype=int)
            tumor_tpm = log2_to_tpm(log_values[tumor_indices])
            normal_tpm = log2_to_tpm(log_values[normal_indices])
            if tumor_tpm.size < 2 or normal_tpm.size < 2:
                continue
            tumor_median = finite_median(tumor_tpm)
            normal_median = finite_median(normal_tpm)
            log2fc = math.log2((tumor_median + pseudocount) / (normal_median + pseudocount))
            try:
                test = mannwhitneyu(tumor_tpm, normal_tpm, alternative="two-sided", method="asymptotic")
                u_value = float(test.statistic)
                p_value = float(test.pvalue)
            except ValueError:
                u_value = float("nan")
                p_value = float("nan")
            rank_biserial = (2.0 * u_value / (tumor_tpm.size * normal_tpm.size) - 1.0) if math.isfinite(u_value) else float("nan")
            raw_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": ensembl,
                    "comparison": comparison,
                    "n_tumor": tumor_tpm.size,
                    "n_normal": normal_tpm.size,
                    "median_tpm_tumor": tumor_median,
                    "median_tpm_normal": normal_median,
                    "log2fc_tumor_vs_normal": log2fc,
                    "mannwhitney_u": u_value,
                    "p_value": p_value,
                    "fdr_bh": "",
                    "rank_biserial_correlation": rank_biserial,
                    "positive_N_stat_rule": "",
                }
            )

    for comparison in [item[0] for item in comparisons]:
        indices = [idx for idx, row in enumerate(raw_rows) if row["comparison"] == comparison]
        fdr_values = bh_fdr([float(raw_rows[idx]["p_value"]) for idx in indices])
        for idx, fdr in zip(indices, fdr_values):
            row = raw_rows[idx]
            row["fdr_bh"] = fdr
            is_positive_rule = (
                comparison == positive_rule.get("comparison")
                and float(row["log2fc_tumor_vs_normal"]) >= float(positive_rule.get("min_log2fc", 1.0))
                and math.isfinite(fdr)
                and fdr < float(positive_rule.get("max_fdr_bh", 0.05))
            )
            row["positive_N_stat_rule"] = bool_text(is_positive_rule)
            stats_by_symbol.setdefault(str(row["hgnc_symbol"]), {})[comparison] = {
                "log2fc": float(row["log2fc_tumor_vs_normal"]),
                "fdr_bh": float(fdr) if math.isfinite(fdr) else float("nan"),
                "rank_biserial": float(row["rank_biserial_correlation"]),
                "positive_rule": 1.0 if is_positive_rule else 0.0,
            }

    formatted_rows: list[dict[str, object]] = []
    for row in raw_rows:
        formatted_rows.append(
            {
                key: fmt(value)
                if key
                in {
                    "median_tpm_tumor",
                    "median_tpm_normal",
                    "log2fc_tumor_vs_normal",
                    "mannwhitney_u",
                    "p_value",
                    "fdr_bh",
                    "rank_biserial_correlation",
                }
                else value
                for key, value in row.items()
            }
        )
    formatted_rows.sort(key=lambda item: (str(item["comparison"]), str(item["hgnc_symbol"])))
    return formatted_rows, stats_by_symbol


def build_normal_and_selectivity_rows(
    universe: list[dict[str, str]],
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
    comparison_indices: dict[str, list[int]],
    tissue_indices: dict[str, list[int]],
    mappings: dict[str, object],
    params: dict[str, object],
    hpa_rna: dict[str, dict[str, float]],
    hpa_ihc_scores: dict[str, dict[str, int]],
    test_stats: dict[str, dict[str, dict[str, float]]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, dict[str, float]], dict[str, dict[str, str]]]:
    pseudocount = float(params["normal_selectivity"]["pseudocount_tpm"])
    organ_config = mappings["critical_organs"]
    lineage_watchlist = set(mappings.get("gastric_lineage_marker_watchlist", []))
    tumor_rows = tumor_expression_by_symbol()

    normal_rows: list[dict[str, object]] = []
    raw_selectivity_rows: list[dict[str, object]] = []
    organ_values_by_symbol: dict[str, dict[str, float]] = {}
    organ_sources_by_symbol: dict[str, dict[str, str]] = {}

    n_critical_values: dict[str, float] = {}
    n_stomach_values: dict[str, float] = {}
    n_stat_values: dict[str, float] = {}
    log2fc_values = {
        symbol: stats.get("tumor_vs_gtex_stomach", {}).get("log2fc", float("nan"))
        for symbol, stats in test_stats.items()
    }
    fdr_values = {
        symbol: -math.log10(max(stats.get("tumor_vs_gtex_stomach", {}).get("fdr_bh", 1.0), 1.0e-300))
        for symbol, stats in test_stats.items()
    }
    log2fc_ranks = rank_percentiles(log2fc_values)
    fdr_ranks = rank_percentiles(fdr_values)
    for symbol in set(log2fc_ranks) & set(fdr_ranks):
        n_stat_values[symbol] = 0.5 * log2fc_ranks[symbol] + 0.5 * fdr_ranks[symbol]

    for gene in universe:
        symbol = gene["hgnc_symbol"]
        ensembl = gene["ensembl_gene_id"]
        expression_entry = expression_by_ensembl.get(ensembl)
        base = {
            "hgnc_symbol": symbol,
            "ensembl_gene_id": ensembl,
            "surfaceome_category": gene.get("surfaceome_category", ""),
        }
        tumor_row = tumor_rows.get(symbol, {})
        if expression_entry is None:
            normal_rows.append(
                {
                    **base,
                    "n_tumor": "",
                    "n_gtex_stomach_normal": "",
                    "n_tcga_adjacent_normal": "",
                    "median_tpm_tumor": tumor_row.get("median_tpm_tumor", ""),
                    "median_tpm_gtex_stomach": "",
                    "median_tpm_tcga_adjacent_normal": "",
                    "normal_xena_p90_tpm": "",
                    "normal_xena_p95_tpm": "",
                    "max_critical_normal_tpm": "",
                    "max_critical_normal_organ": "",
                    "max_non_gi_critical_normal_tpm": "",
                    "gi_normal_max_tpm": "",
                    "immune_blood_max_tpm": "",
                    "hpa_stomach_rna_ntpm": "",
                    "hpa_max_critical_rna_ntpm": "",
                    "hpa_normal_protein_max_level_score": "",
                    "hpa_normal_protein_max_organ": "",
                    "normal_expression_data_status": "missing_xena_expression",
                    "gastric_lineage_flag": "",
                }
            )
            raw_selectivity_rows.append(
                {
                    **base,
                    "N_stomach_log2fc": "",
                    "N_critical_log2fc": "",
                    "N_tcga_adjacent_log2fc": "",
                    "N_stat_gtex": "",
                    "N_score": "",
                    "N_rank_percentile": "",
                    "positive_N_stat_rule_gtex": "",
                    "gastric_lineage_flag": "",
                    "selectivity_interpretation": "missing_xena_expression",
                }
            )
            continue

        _, log_values = expression_entry
        tumor_indices = np.array(comparison_indices["tcga_stad_primary_tumor"], dtype=int)
        gtex_indices = np.array(comparison_indices["gtex_stomach_normal"], dtype=int)
        adjacent_indices = np.array(comparison_indices["tcga_stad_adjacent_normal"], dtype=int)
        all_normal_indices = sorted(set(gtex_indices.tolist()) | set(adjacent_indices.tolist()) | {idx for indices in tissue_indices.values() for idx in indices})

        tumor_tpm = log2_to_tpm(log_values[tumor_indices])
        gtex_tpm = log2_to_tpm(log_values[gtex_indices])
        adjacent_tpm = log2_to_tpm(log_values[adjacent_indices])
        all_normal_tpm = log2_to_tpm(log_values[np.array(all_normal_indices, dtype=int)])

        hpa_gene_values = hpa_rna.get(ensembl, {})
        organ_values, organ_sources = organ_expression_for_gene(log_values, tissue_indices, organ_config, hpa_gene_values)
        organ_values_by_symbol[symbol] = organ_values
        organ_sources_by_symbol[symbol] = organ_sources

        max_critical_organ = max(organ_values, key=lambda organ: organ_values[organ] if math.isfinite(organ_values[organ]) else -math.inf)
        max_critical = organ_values[max_critical_organ]
        non_gi_values = [value for organ, value in organ_values.items() if organ != "gi_epithelial"]
        max_non_gi = max_finite(non_gi_values)
        gi_normal = organ_values.get("gi_epithelial", float("nan"))
        immune_blood = max_finite([organ_values.get("hematopoietic", float("nan")), organ_values.get("immune", float("nan"))])
        hpa_max = max_finite([value for key, value in hpa_gene_values.items() if not key.startswith("_")])
        hpa_protein_scores = hpa_ihc_scores.get(ensembl, {})
        max_hpa_protein_organ = max(
            hpa_protein_scores,
            key=lambda organ: hpa_protein_scores[organ],
        ) if hpa_protein_scores else ""
        max_hpa_protein_score = hpa_protein_scores.get(max_hpa_protein_organ, float("nan")) if max_hpa_protein_organ else float("nan")

        tumor_median = finite_median(tumor_tpm)
        gtex_median = finite_median(gtex_tpm)
        adjacent_median = finite_median(adjacent_tpm)
        n_stomach = math.log2((tumor_median + pseudocount) / (gtex_median + pseudocount))
        n_critical = math.log2((tumor_median + pseudocount) / (max_critical + pseudocount)) if math.isfinite(max_critical) else float("nan")
        n_adjacent = math.log2((tumor_median + pseudocount) / (adjacent_median + pseudocount))
        n_stomach_values[symbol] = n_stomach
        n_critical_values[symbol] = n_critical

        lineage_flag = ""
        if symbol in lineage_watchlist:
            if n_stomach < 0:
                lineage_flag = "gastric_lineage_lost_or_lower_in_tumor"
            else:
                lineage_flag = "gastric_lineage_retained"
        if symbol == "CLDN18":
            lineage_flag = (lineage_flag + ";" if lineage_flag else "") + "CLDN18_gene_level_isoform_unresolved;normal_gastric_penalty_required;accessibility_context_required"

        normal_rows.append(
            {
                **base,
                "n_tumor": tumor_tpm.size,
                "n_gtex_stomach_normal": gtex_tpm.size,
                "n_tcga_adjacent_normal": adjacent_tpm.size,
                "median_tpm_tumor": fmt(tumor_median),
                "median_tpm_gtex_stomach": fmt(gtex_median),
                "median_tpm_tcga_adjacent_normal": fmt(adjacent_median),
                "normal_xena_p90_tpm": fmt(finite_percentile(all_normal_tpm, 90.0)),
                "normal_xena_p95_tpm": fmt(finite_percentile(all_normal_tpm, 95.0)),
                "max_critical_normal_tpm": fmt(max_critical),
                "max_critical_normal_organ": max_critical_organ,
                "max_non_gi_critical_normal_tpm": fmt(max_non_gi),
                "gi_normal_max_tpm": fmt(gi_normal),
                "immune_blood_max_tpm": fmt(immune_blood),
                "hpa_stomach_rna_ntpm": fmt(hpa_gene_values.get("_stomach", float("nan"))),
                "hpa_max_critical_rna_ntpm": fmt(hpa_max),
                "hpa_normal_protein_max_level_score": fmt(max_hpa_protein_score, digits=0),
                "hpa_normal_protein_max_organ": max_hpa_protein_organ,
                "normal_expression_data_status": "measured",
                "gastric_lineage_flag": lineage_flag,
            }
        )
        gtex_stats = test_stats.get(symbol, {}).get("tumor_vs_gtex_stomach", {})
        adjacent_stats = test_stats.get(symbol, {}).get("tumor_vs_tcga_adjacent", {})
        raw_selectivity_rows.append(
            {
                **base,
                "N_stomach_log2fc": n_stomach,
                "N_critical_log2fc": n_critical,
                "N_tcga_adjacent_log2fc": n_adjacent,
                "N_stat_gtex": n_stat_values.get(symbol, float("nan")),
                "N_score": "",
                "N_rank_percentile": "",
                "positive_N_stat_rule_gtex": bool_text(bool(gtex_stats.get("positive_rule", 0.0))),
                "gtex_fdr_bh": gtex_stats.get("fdr_bh", float("nan")),
                "tcga_adjacent_fdr_bh": adjacent_stats.get("fdr_bh", float("nan")),
                "gastric_lineage_flag": lineage_flag,
                "selectivity_interpretation": "",
            }
        )

    critical_ranks = rank_percentiles(n_critical_values)
    stomach_ranks = rank_percentiles(n_stomach_values)
    n_stat_ranks = rank_percentiles(n_stat_values)
    n_scores: dict[str, float] = {}
    for symbol in set(critical_ranks) & set(stomach_ranks) & set(n_stat_ranks):
        n_scores[symbol] = 0.50 * critical_ranks[symbol] + 0.30 * stomach_ranks[symbol] + 0.20 * n_stat_ranks[symbol]
    n_score_ranks = rank_percentiles(n_scores)

    selectivity_rows: list[dict[str, object]] = []
    for row in raw_selectivity_rows:
        symbol = str(row["hgnc_symbol"])
        if symbol in n_scores:
            row["N_score"] = n_scores[symbol]
            row["N_rank_percentile"] = n_score_ranks[symbol]
            n_critical = float(row["N_critical_log2fc"])
            gtex_positive = str(row["positive_N_stat_rule_gtex"]) == "true"
            if n_critical >= 1.0 and gtex_positive:
                row["selectivity_interpretation"] = "selective_by_critical_and_gtex_stat"
            elif n_critical < 0:
                row["selectivity_interpretation"] = "higher_or_equal_in_critical_normal"
            else:
                row["selectivity_interpretation"] = "intermediate_or_context_dependent"
        formatted = {
            key: fmt(value)
            if key
            in {
                "N_stomach_log2fc",
                "N_critical_log2fc",
                "N_tcga_adjacent_log2fc",
                "N_stat_gtex",
                "N_score",
                "N_rank_percentile",
                "gtex_fdr_bh",
                "tcga_adjacent_fdr_bh",
            }
            else value
            for key, value in row.items()
        }
        selectivity_rows.append(formatted)

    normal_rows.sort(key=lambda item: str(item["hgnc_symbol"]))
    selectivity_rows.sort(key=lambda item: str(item["hgnc_symbol"]))
    return normal_rows, selectivity_rows, organ_values_by_symbol, organ_sources_by_symbol


def build_risk_rows(
    universe: list[dict[str, str]],
    organ_values_by_symbol: dict[str, dict[str, float]],
    organ_sources_by_symbol: dict[str, dict[str, str]],
    hpa_ihc_scores: dict[str, dict[str, int]],
    mappings: dict[str, object],
    params: dict[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    organ_config = mappings["critical_organs"]
    organs = sorted(organ_config)
    values_for_rank: dict[str, dict[str, float]] = {organ: {} for organ in organs}
    for gene in universe:
        symbol = gene["hgnc_symbol"]
        for organ in organs:
            values_for_rank[organ][symbol] = organ_values_by_symbol.get(symbol, {}).get(organ, float("nan"))
    organ_ranks = {organ: rank_percentiles(values) for organ, values in values_for_rank.items()}

    organ_penalty_rows: list[dict[str, object]] = []
    risk_rows: list[dict[str, object]] = []
    floors = params["normal_risk"]["thresholds"]
    caution_floor = float(floors["caution_tpm_floor"])
    critical_floor = float(floors["critical_tpm_floor"])

    for gene in universe:
        symbol = gene["hgnc_symbol"]
        ensembl = gene["ensembl_gene_id"]
        organ_values = organ_values_by_symbol.get(symbol, {})
        finite_values = np.array([value for value in organ_values.values() if math.isfinite(float(value))], dtype=float)
        if finite_values.size:
            gene_p50 = float(np.percentile(finite_values, 50.0))
            gene_p75 = float(np.percentile(finite_values, 75.0))
        else:
            gene_p50 = float("nan")
            gene_p75 = float("nan")
        caution_threshold = max(gene_p50, caution_floor) if math.isfinite(gene_p50) else caution_floor
        critical_threshold = max(gene_p75, critical_floor) if math.isfinite(gene_p75) else critical_floor
        weighted_penalties: list[tuple[str, float, float]] = []
        critical_organs: list[str] = []
        caution_organs: list[str] = []

        for organ in organs:
            normal_expr = organ_values.get(organ, float("nan"))
            weight = float(organ_config[organ]["base_weight"])
            rank_pct = organ_ranks.get(organ, {}).get(symbol, float("nan"))
            if not math.isfinite(normal_expr):
                penalty = float("nan")
                category = "missing"
            elif normal_expr >= critical_threshold:
                penalty = 1.0
                category = "critical"
                critical_organs.append(organ)
            elif normal_expr >= caution_threshold:
                penalty = 0.5 * rank_pct if math.isfinite(rank_pct) else 0.5
                category = "caution"
                caution_organs.append(organ)
            else:
                penalty = 0.0
                category = "low"
            weighted = penalty * weight if math.isfinite(penalty) else float("nan")
            if math.isfinite(weighted):
                weighted_penalties.append((organ, weighted, penalty))
            hpa_score = hpa_ihc_scores.get(ensembl, {}).get(organ, "")
            organ_penalty_rows.append(
                {
                    "hgnc_symbol": symbol,
                    "ensembl_gene_id": ensembl,
                    "organ": organ,
                    "normal_expr_tpm_or_ntpm": fmt(normal_expr),
                    "normal_expression_source": organ_sources_by_symbol.get(symbol, {}).get(organ, "missing"),
                    "organ_rank_percentile": fmt(rank_pct),
                    "caution_threshold_tpm": fmt(caution_threshold),
                    "critical_threshold_tpm": fmt(critical_threshold),
                    "organ_penalty": fmt(penalty),
                    "organ_weight": fmt(weight),
                    "weighted_organ_penalty": fmt(weighted),
                    "risk_category": category,
                    "hpa_normal_protein_level_score": hpa_score,
                    "hpa_normal_protein_level": HPA_LEVEL_LABEL.get(hpa_score, "") if isinstance(hpa_score, int) else "",
                }
            )

        weighted_values = [item[1] for item in weighted_penalties]
        if weighted_values:
            sorted_weighted = sorted(weighted_penalties, key=lambda item: item[1], reverse=True)
            r_max = sorted_weighted[0][1]
            max_organ = sorted_weighted[0][0]
            top3 = [item[1] for item in sorted_weighted[:3]]
            r_max_plus_breadth = 0.7 * r_max + 0.3 * float(np.mean(top3))
            r_sum_capped = min(1.0, float(np.sum(weighted_values)) / 3.0)
        else:
            r_max = r_max_plus_breadth = r_sum_capped = float("nan")
            max_organ = ""
        if math.isfinite(r_max) and r_max >= 0.80:
            interpretation = "high_critical_off_tumor_risk"
        elif math.isfinite(r_max) and r_max >= 0.50:
            interpretation = "moderate_off_tumor_risk"
        elif math.isfinite(r_max):
            interpretation = "lower_risk_by_current_normal_expression"
        else:
            interpretation = "missing_normal_expression"
        risk_rows.append(
            {
                "hgnc_symbol": symbol,
                "ensembl_gene_id": ensembl,
                "R_score": fmt(r_max),
                "R_max": fmt(r_max),
                "R_max_plus_breadth": fmt(r_max_plus_breadth),
                "R_sum_capped": fmt(r_sum_capped),
                "max_risk_organ": max_organ,
                "critical_organs": ";".join(sorted(critical_organs)),
                "caution_organs": ";".join(sorted(caution_organs)),
                "n_critical_organs": len(critical_organs),
                "n_caution_organs": len(caution_organs),
                "risk_interpretation": interpretation,
            }
        )

    organ_penalty_rows.sort(key=lambda item: (str(item["hgnc_symbol"]), str(item["organ"])))
    risk_rows.sort(key=lambda item: str(item["hgnc_symbol"]))
    return organ_penalty_rows, risk_rows


def simulate_power_curve(
    comparison: str,
    n_tumor: int,
    n_normal: int,
    n_tests: int,
    median_empirical_sd: float,
    params: dict[str, object],
    seed: int,
) -> list[dict[str, object]]:
    power_params = params["tumor_normal_power"]
    simulations = int(power_params["simulations_per_delta"])
    alternative_fraction = float(power_params["alternative_fraction"])
    q = float(power_params["bh_fdr"])
    target_power = float(power_params["target_power"])
    grid = power_params["effect_grid_standardized"]
    deltas = np.arange(float(grid["start"]), float(grid["stop"]) + 1.0e-9, float(grid["step"]))
    rng = np.random.default_rng(seed)
    n_alt = max(1, int(round(n_tests * alternative_fraction)))
    se = math.sqrt(1.0 / n_tumor + 1.0 / n_normal)
    rows: list[dict[str, object]] = []
    min_detectable = ""
    for delta in deltas:
        powers: list[float] = []
        fdrs: list[float] = []
        effect_z_mean = float(delta) / se
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
        if min_detectable == "" and mean_power >= target_power:
            min_detectable = float(delta)
        rows.append(
            {
                "comparison": comparison,
                "n_tumor": n_tumor,
                "n_normal": n_normal,
                "n_tests": n_tests,
                "standardized_log2_shift": fmt(float(delta)),
                "approx_log2_tpm_shift": fmt(float(delta) * median_empirical_sd),
                "power": fmt(mean_power),
                "mean_fdr": fmt(mean_fdr),
                "simulations": simulations,
                "alternative_fraction": fmt(alternative_fraction),
                "bh_fdr": fmt(q),
                "target_power": fmt(target_power),
                "is_min_detectable": "",
            }
        )
    if min_detectable != "":
        for row in rows:
            if float(row["standardized_log2_shift"]) == float(min_detectable):
                row["is_min_detectable"] = "true"
            else:
                row["is_min_detectable"] = "false"
    else:
        for row in rows:
            row["is_min_detectable"] = "not_reached"
    return rows


def build_power_rows(
    expression_by_ensembl: dict[str, tuple[str, np.ndarray]],
    comparison_indices: dict[str, list[int]],
    params: dict[str, object],
) -> list[dict[str, object]]:
    n_tests = len(expression_by_ensembl)
    seed_base = int(params["random"]["tumor_normal_power_seed"])
    rows: list[dict[str, object]] = []
    comparisons = [
        ("tumor_vs_gtex_stomach", "tcga_stad_primary_tumor", "gtex_stomach_normal"),
        ("tumor_vs_tcga_adjacent", "tcga_stad_primary_tumor", "tcga_stad_adjacent_normal"),
    ]
    for idx, (comparison, tumor_group, normal_group) in enumerate(comparisons):
        combined_indices = np.array(comparison_indices[tumor_group] + comparison_indices[normal_group], dtype=int)
        gene_sds: list[float] = []
        for _, log_values in expression_by_ensembl.values():
            values = log_values[combined_indices]
            if values.size > 2:
                gene_sds.append(float(np.std(values, ddof=1)))
        median_sd = float(np.median(gene_sds))
        rows.extend(
            simulate_power_curve(
                comparison=comparison,
                n_tumor=len(comparison_indices[tumor_group]),
                n_normal=len(comparison_indices[normal_group]),
                n_tests=n_tests,
                median_empirical_sd=median_sd,
                params=params,
                seed=seed_base + idx,
            )
        )
    return rows


def build_sample_counts_rows(
    mappings: dict[str, object],
    comparison_indices: dict[str, list[int]],
    tissue_indices: dict[str, list[int]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "group_type": "comparison",
            "group_id": group,
            "n_samples": len(indices),
            "mapped_organs": "",
        }
        for group, indices in sorted(comparison_indices.items())
    ]
    category_to_organs: dict[str, list[str]] = {}
    for organ, config in mappings["critical_organs"].items():
        for category in config.get("xena_detailed_categories", []):
            category_to_organs.setdefault(str(category), []).append(str(organ))
    for tissue, indices in sorted(tissue_indices.items()):
        rows.append(
            {
                "group_type": "xena_tissue",
                "group_id": tissue,
                "n_samples": len(indices),
                "mapped_organs": ";".join(sorted(category_to_organs.get(tissue, []))),
            }
        )
    return rows


def plot_tumor_vs_normal(normal_rows: list[dict[str, object]], risk_rows: list[dict[str, object]], output: Path) -> None:
    risk_by_symbol = {row["hgnc_symbol"]: row for row in risk_rows}
    measured = [row for row in normal_rows if row.get("normal_expression_data_status") == "measured"]
    tumor = np.array([float(row["median_tpm_tumor"]) for row in measured], dtype=float)
    normal = np.array([float(row["max_critical_normal_tpm"]) for row in measured], dtype=float)
    risk = np.array([float(risk_by_symbol[row["hgnc_symbol"]]["R_score"]) for row in measured], dtype=float)
    symbols = [str(row["hgnc_symbol"]) for row in measured]

    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    scatter = ax.scatter(
        np.log10(normal + 0.1),
        np.log10(tumor + 0.1),
        c=risk,
        cmap="magma_r",
        s=18,
        alpha=0.78,
        linewidths=0,
    )
    lim_min = min(float(np.min(np.log10(normal + 0.1))), float(np.min(np.log10(tumor + 0.1))))
    lim_max = max(float(np.max(np.log10(normal + 0.1))), float(np.max(np.log10(tumor + 0.1))))
    ax.plot([lim_min, lim_max], [lim_min, lim_max], color="#6b7280", linestyle="--", linewidth=0.8)
    ax.set_xlabel("log10(max critical normal TPM/nTPM + 0.1)")
    ax.set_ylabel("log10(TCGA-STAD tumor median TPM + 0.1)")
    ax.set_title("Fase 6 tumor vs critical normal expression")
    ax.grid(True, linewidth=0.35, alpha=0.25)
    fig.colorbar(scatter, ax=ax, label="R score")
    for symbol in ["ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN", "PTPRC", "PECAM1"]:
        if symbol not in symbols:
            continue
        idx = symbols.index(symbol)
        ax.annotate(symbol, (np.log10(normal[idx] + 0.1), np.log10(tumor[idx] + 0.1)), xytext=(4, 4), textcoords="offset points", fontsize=7)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    save_svg(fig, output)
    plt.close(fig)


def plot_power_curve(power_rows: list[dict[str, object]], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    for comparison, color in [("tumor_vs_gtex_stomach", "#2563eb"), ("tumor_vs_tcga_adjacent", "#dc2626")]:
        rows = [row for row in power_rows if row["comparison"] == comparison]
        x = [float(row["standardized_log2_shift"]) for row in rows]
        y = [float(row["power"]) for row in rows]
        ax.plot(x, y, marker="o", markersize=3.5, linewidth=1.2, color=color, label=comparison)
    ax.axhline(0.80, color="#111827", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Standardized log2 expression shift")
    ax.set_ylabel("Power at BH-FDR 0.05")
    ax.set_ylim(0, 1.03)
    ax.set_title("Tumor-normal power simulation")
    ax.grid(True, linewidth=0.35, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    save_svg(fig, output)
    plt.close(fig)


def write_notes(
    normal_rows: list[dict[str, object]],
    selectivity_rows: list[dict[str, object]],
    risk_rows: list[dict[str, object]],
    test_rows: list[dict[str, object]],
    power_rows: list[dict[str, object]],
    sample_counts: list[dict[str, object]],
) -> None:
    measured = [row for row in normal_rows if row.get("normal_expression_data_status") == "measured"]
    positive_n = [row for row in selectivity_rows if row.get("positive_N_stat_rule_gtex") == "true"]
    high_risk = [row for row in risk_rows if row.get("risk_interpretation") == "high_critical_off_tumor_risk"]
    comparison_counts = "\n".join(
        f"- {row['group_id']}: n={row['n_samples']}"
        for row in sample_counts
        if row["group_type"] == "comparison"
    )
    min_power_lines: list[str] = []
    for comparison in sorted({row["comparison"] for row in power_rows}):
        min_rows = [row for row in power_rows if row["comparison"] == comparison and row["is_min_detectable"] == "true"]
        if min_rows:
            row = min_rows[0]
            min_power_lines.append(
                f"- {comparison}: standardized shift {row['standardized_log2_shift']} (approx log2 shift {row['approx_log2_tpm_shift']})"
            )
        else:
            min_power_lines.append(f"- {comparison}: target power not reached on the tested grid")
    (DOCS_DIR / "fase6_normal_selectivity_risk.md").write_text(
        f"""# Fase 6 Normal Selectivity And Off-Tumor Risk

Access date: {dt.date.today().isoformat()}

Fase 6 estimates tumor-normal selectivity (`N`) and organ-specific on-target/off-tumor risk (`R`) for the Fase 4 Core+Probable surfaceome universe. Xena/Toil values are transformed from `log2(TPM+0.001)` back to TPM before summary statistics. HPA RNA `nTPM` is used conservatively where mapped by `config/tissue_mappings.yaml`, especially for tissue classes not directly represented in Xena.

## Sample Counts

{comparison_counts}

## Scope

- Candidate universe: {len(normal_rows)} Core+Probable genes.
- Genes with measured tumor/normal Xena expression: {len(measured)}.
- Genes meeting the preregistered GTEx stomach statistical rule (`log2FC >= 1` and BH-FDR < 0.05): {len(positive_n)}.
- Genes with high critical off-tumor risk by current `R_max`: {len(high_risk)}.

## Selectivity

`N_stomach` compares TCGA-STAD primary tumor median TPM against GTEx stomach median TPM. `N_critical` compares tumor median TPM against the maximum mapped critical normal expression across Xena/HPA sources. `N_score` is a component score only:

`0.50*rank(N_critical_log2fc) + 0.30*rank(N_stomach_log2fc) + 0.20*N_stat_gtex`

The intra-TCGA adjacent-normal comparison is reported as a sensitivity test. It is not treated as a full replacement for GTEx stomach because adjacent normals have smaller sample size.

## Power

{chr(10).join(min_power_lines)}

## Risk

`R_score` uses the preregistered maximum weighted organ penalty. `R_max_plus_breadth` and `R_sum_capped` are already computed for later Fase 14 sensitivity, but `R_max` remains the primary conservative risk component.

## Interpretation Constraints

- `N` and `R` are components, not final ranking decisions.
- High GI/stomach normal expression does not automatically exclude gastric-lineage targets, but it must be carried into candidate cards.
- `CLDN18` keeps the gene-level isoform and normal gastric penalty flags; CLDN18.2-specific claims remain blocked until isoform/topology review.
- TCGA/GTEx source effects remain a limitation from Fase 2; GDC adjacent-normal sensitivity is reported but lower-powered.

## Outputs

- `data/processed/normal_expression.tsv`
- `data/processed/selectivity_scores.tsv`
- `data/processed/off_tumor_risk.tsv`
- `data/processed/organ_penalties.tsv`
- `data/processed/tumor_normal_tests.tsv`
- `results/tables/tumor_normal_power_analysis.tsv`
- `results/tables/normal_tissue_sample_counts.tsv`
- `results/tables/hpa_normal_protein_by_organ.tsv`
- `results/figures/tumor_vs_normal_critical.svg`
- `results/figures/tumor_normal_power_curve.svg`
""",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)

    params = load_yaml(PARAMETERS_CONFIG)
    mappings = load_yaml(TISSUE_MAPPINGS_CONFIG)
    universe = candidate_rows()
    wanted_ensembl = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    selected_samples, _ = load_selected_samples(mappings)
    ordered_samples, expression_by_ensembl, comparison_indices, tissue_indices = extract_xena_expression(wanted_ensembl, selected_samples)
    hpa_rna = load_hpa_rna_by_organ(universe, mappings)
    hpa_ihc_scores, hpa_ihc_rows = load_hpa_ihc_by_organ(universe, mappings)

    test_rows, test_stats = run_tumor_normal_tests(
        universe,
        expression_by_ensembl,
        comparison_indices,
        pseudocount=float(params["normal_selectivity"]["pseudocount_tpm"]),
        positive_rule=params["normal_selectivity"]["positive_rule"],
    )
    normal_rows, selectivity_rows, organ_values_by_symbol, organ_sources_by_symbol = build_normal_and_selectivity_rows(
        universe,
        expression_by_ensembl,
        comparison_indices,
        tissue_indices,
        mappings,
        params,
        hpa_rna,
        hpa_ihc_scores,
        test_stats,
    )
    organ_penalty_rows, risk_rows = build_risk_rows(
        universe,
        organ_values_by_symbol,
        organ_sources_by_symbol,
        hpa_ihc_scores,
        mappings,
        params,
    )
    power_rows = build_power_rows(expression_by_ensembl, comparison_indices, params)
    sample_count_rows = build_sample_counts_rows(mappings, comparison_indices, tissue_indices)

    write_tsv(
        PROCESSED_DIR / "normal_expression.tsv",
        normal_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "surfaceome_category",
            "n_tumor",
            "n_gtex_stomach_normal",
            "n_tcga_adjacent_normal",
            "median_tpm_tumor",
            "median_tpm_gtex_stomach",
            "median_tpm_tcga_adjacent_normal",
            "normal_xena_p90_tpm",
            "normal_xena_p95_tpm",
            "max_critical_normal_tpm",
            "max_critical_normal_organ",
            "max_non_gi_critical_normal_tpm",
            "gi_normal_max_tpm",
            "immune_blood_max_tpm",
            "hpa_stomach_rna_ntpm",
            "hpa_max_critical_rna_ntpm",
            "hpa_normal_protein_max_level_score",
            "hpa_normal_protein_max_organ",
            "normal_expression_data_status",
            "gastric_lineage_flag",
        ],
    )
    write_tsv(
        PROCESSED_DIR / "selectivity_scores.tsv",
        selectivity_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "surfaceome_category",
            "N_stomach_log2fc",
            "N_critical_log2fc",
            "N_tcga_adjacent_log2fc",
            "N_stat_gtex",
            "N_score",
            "N_rank_percentile",
            "positive_N_stat_rule_gtex",
            "gtex_fdr_bh",
            "tcga_adjacent_fdr_bh",
            "gastric_lineage_flag",
            "selectivity_interpretation",
        ],
    )
    write_tsv(
        PROCESSED_DIR / "off_tumor_risk.tsv",
        risk_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "R_score",
            "R_max",
            "R_max_plus_breadth",
            "R_sum_capped",
            "max_risk_organ",
            "critical_organs",
            "caution_organs",
            "n_critical_organs",
            "n_caution_organs",
            "risk_interpretation",
        ],
    )
    write_tsv(
        PROCESSED_DIR / "organ_penalties.tsv",
        organ_penalty_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "organ",
            "normal_expr_tpm_or_ntpm",
            "normal_expression_source",
            "organ_rank_percentile",
            "caution_threshold_tpm",
            "critical_threshold_tpm",
            "organ_penalty",
            "organ_weight",
            "weighted_organ_penalty",
            "risk_category",
            "hpa_normal_protein_level_score",
            "hpa_normal_protein_level",
        ],
    )
    write_tsv(
        PROCESSED_DIR / "tumor_normal_tests.tsv",
        test_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "comparison",
            "n_tumor",
            "n_normal",
            "median_tpm_tumor",
            "median_tpm_normal",
            "log2fc_tumor_vs_normal",
            "mannwhitney_u",
            "p_value",
            "fdr_bh",
            "rank_biserial_correlation",
            "positive_N_stat_rule",
        ],
    )
    write_tsv(
        TABLES_DIR / "tumor_normal_power_analysis.tsv",
        power_rows,
        [
            "comparison",
            "n_tumor",
            "n_normal",
            "n_tests",
            "standardized_log2_shift",
            "approx_log2_tpm_shift",
            "power",
            "mean_fdr",
            "simulations",
            "alternative_fraction",
            "bh_fdr",
            "target_power",
            "is_min_detectable",
        ],
    )
    write_tsv(TABLES_DIR / "normal_tissue_sample_counts.tsv", sample_count_rows, ["group_type", "group_id", "n_samples", "mapped_organs"])
    write_tsv(
        TABLES_DIR / "hpa_normal_protein_by_organ.tsv",
        hpa_ihc_rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "organ",
            "hpa_normal_protein_max_level_score",
            "hpa_normal_protein_max_level",
            "medium_high_cell_type_evidence",
        ],
    )
    plot_tumor_vs_normal(normal_rows, risk_rows, FIGURES_DIR / "tumor_vs_normal_critical.svg")
    plot_power_curve(power_rows, FIGURES_DIR / "tumor_normal_power_curve.svg")
    write_notes(normal_rows, selectivity_rows, risk_rows, test_rows, power_rows, sample_count_rows)
    print("Wrote Fase 6 normal-expression, selectivity, and off-tumor risk outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
