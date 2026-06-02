"""Build Fase 7 HPA protein evidence and localization tables."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import sys
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml


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

HPA_CANCER = RAW_DIR / "hpa" / "cancer_data.tsv.zip"
HPA_NORMAL_IHC = RAW_DIR / "hpa" / "normal_ihc_data.tsv.zip"
HPA_SUBCELLULAR = RAW_DIR / "hpa" / "subcellular_location.tsv.zip"
SURFACEOME_UNIVERSE = PROCESSED_DIR / "surfaceome_universe.tsv"
TUMOR_EXPRESSION = PROCESSED_DIR / "tumor_expression.tsv"
OFF_TUMOR_RISK = PROCESSED_DIR / "off_tumor_risk.tsv"
PARAMETERS_CONFIG = REPO_ROOT / "config" / "parameters.yaml"
TISSUE_MAPPINGS_CONFIG = REPO_ROOT / "config" / "tissue_mappings.yaml"

CORE_SURFACEOME_CATEGORIES = {"core_surfaceome", "probable_surfaceome"}
HPA_STOMACH_CANCER = "stomach cancer"
MEMBRANE_TERMS = {"Plasma membrane", "Cell Junctions"}
INTRACELLULAR_ONLY_TERMS = {
    "Nucleoplasm",
    "Nucleoli",
    "Nucleoli fibrillar center",
    "Cytosol",
    "Mitochondria",
    "Endoplasmic reticulum",
    "Golgi apparatus",
    "Peroxisomes",
    "Centrosome",
    "Actin filaments",
    "Microtubules",
    "Intermediate filaments",
    "Aggresome",
    "Lipid droplets",
}


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


def candidate_rows() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_tsv(SURFACEOME_UNIVERSE)
        if row.get("surfaceome_category") in CORE_SURFACEOME_CATEGORIES
    ]
    rows.sort(key=lambda row: row["hgnc_symbol"])
    return rows


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
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    if finite_values.size == 1:
        percentiles = np.ones(1, dtype=float)
    else:
        percentiles = (ranks - 1.0) / (finite_values.size - 1.0)
    return {symbol: float(value) for symbol, value in zip(finite_symbols, percentiles)}


def max_level_label(counts: dict[str, int]) -> str:
    for label in ["High", "Medium", "Low", "Not detected"]:
        if counts.get(label, 0) > 0:
            return label
    return ""


def dominant_level_label(counts: dict[str, int]) -> str:
    if not counts:
        return ""
    labels = ["High", "Medium", "Low", "Not detected"]
    return max(labels, key=lambda label: (counts.get(label, 0), -labels.index(label)))


def parse_hpa_cancer(universe: list[dict[str, str]], level_scores: dict[str, float]) -> dict[str, dict[str, object]]:
    wanted = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    rows: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(HPA_CANCER) as archive:
        with archive.open(archive.namelist()[0]) as raw:
            reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
            for row in reader:
                ensembl = row["Gene"].split(".", 1)[0]
                if ensembl not in wanted or row.get("Cancer") != HPA_STOMACH_CANCER:
                    continue
                counts = {
                    "High": int(row.get("High", "0") or 0),
                    "Medium": int(row.get("Medium", "0") or 0),
                    "Low": int(row.get("Low", "0") or 0),
                    "Not detected": int(row.get("Not detected", "0") or 0),
                }
                total = sum(counts.values())
                if total:
                    weighted = sum(level_scores[label] * count for label, count in counts.items()) / (3.0 * total)
                    present_pct = (counts["High"] + counts["Medium"] + counts["Low"]) / total
                    high_medium_pct = (counts["High"] + counts["Medium"]) / total
                else:
                    weighted = present_pct = high_medium_pct = float("nan")
                rows[ensembl] = {
                    "counts": counts,
                    "total": total,
                    "protein_tumor_presence": weighted,
                    "tumor_protein_present_pct": present_pct,
                    "tumor_high_medium_pct": high_medium_pct,
                    "max_staining_level": max_level_label(counts),
                    "dominant_staining_level": dominant_level_label(counts),
                }
    return rows


def best_reliability(current: str, candidate: str, reliability_scores: dict[str, float]) -> str:
    if not current:
        return candidate
    if reliability_scores.get(candidate, 0.0) > reliability_scores.get(current, 0.0):
        return candidate
    return current


def parse_hpa_normal(
    universe: list[dict[str, str]],
    mappings: dict[str, object],
    level_scores: dict[str, float],
    reliability_scores: dict[str, float],
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, dict[str, object]]]]:
    wanted = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    tissue_to_organs: dict[str, list[str]] = {}
    for organ, config in mappings["critical_organs"].items():
        for tissue in config.get("hpa_ihc_tissues", []):
            tissue_to_organs.setdefault(str(tissue).lower(), []).append(str(organ))

    stomach: dict[str, dict[str, object]] = {}
    critical: dict[str, dict[str, dict[str, object]]] = {row["ensembl_gene_id"]: {} for row in universe}
    with zipfile.ZipFile(HPA_NORMAL_IHC) as archive:
        with archive.open(archive.namelist()[0]) as raw:
            reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
            for row in reader:
                ensembl = row["Gene"].split(".", 1)[0]
                if ensembl not in wanted:
                    continue
                level = row.get("Level", "")
                level_score = level_scores.get(level)
                if level_score is None:
                    continue
                reliability = row.get("Reliability", "")
                if row.get("Tissue") == "Stomach":
                    current = stomach.setdefault(
                        ensembl,
                        {
                            "max_level_score": -1.0,
                            "max_level": "",
                            "best_reliability": "",
                            "cell_type_evidence": [],
                        },
                    )
                    if level_score > float(current["max_level_score"]):
                        current["max_level_score"] = level_score
                        current["max_level"] = level
                    current["best_reliability"] = best_reliability(str(current["best_reliability"]), reliability, reliability_scores)
                    if level_score >= 2:
                        current["cell_type_evidence"].append(f"{row['IHC tissue name']}:{row['Cell type']}:{level}:{reliability}")

                for organ in tissue_to_organs.get(row.get("Tissue", "").lower(), []):
                    organ_row = critical.setdefault(ensembl, {}).setdefault(
                        organ,
                        {
                            "max_level_score": -1.0,
                            "max_level": "",
                            "best_reliability": "",
                            "cell_type_evidence": [],
                        },
                    )
                    if level_score > float(organ_row["max_level_score"]):
                        organ_row["max_level_score"] = level_score
                        organ_row["max_level"] = level
                    organ_row["best_reliability"] = best_reliability(str(organ_row["best_reliability"]), reliability, reliability_scores)
                    if level_score >= 2:
                        organ_row["cell_type_evidence"].append(f"{row['Tissue']}:{row['Cell type']}:{level}:{reliability}")
    return stomach, critical


def split_locations(*values: str) -> set[str]:
    locations: set[str] = set()
    for value in values:
        for part in str(value or "").split(";"):
            part = part.strip()
            if part:
                locations.add(part)
    return locations


def parse_hpa_subcellular(
    universe: list[dict[str, str]],
    reliability_scores: dict[str, float],
) -> dict[str, dict[str, object]]:
    wanted = {row["ensembl_gene_id"] for row in universe if row.get("ensembl_gene_id")}
    rows: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(HPA_SUBCELLULAR) as archive:
        with archive.open(archive.namelist()[0]) as raw:
            reader = csv.DictReader((line.decode("utf-8", "replace") for line in raw), delimiter="\t")
            for row in reader:
                ensembl = row["Gene"].split(".", 1)[0]
                if ensembl not in wanted:
                    continue
                locations = split_locations(row.get("Main location", ""), row.get("Additional location", ""))
                extracellular_location = row.get("Extracellular location", "")
                if "Plasma membrane" in locations:
                    membrane_support = 1.0
                    membrane_class = "plasma_membrane"
                elif "Cell Junctions" in locations:
                    membrane_support = 0.70
                    membrane_class = "cell_junctions"
                elif extracellular_location:
                    membrane_support = 0.30
                    membrane_class = "predicted_secreted_only"
                else:
                    membrane_support = 0.0
                    membrane_class = "no_membrane_support"
                intracellular_only = bool(locations) and not locations.intersection(MEMBRANE_TERMS) and not extracellular_location
                rows[ensembl] = {
                    "hpa_subcellular_reliability": row.get("Reliability", ""),
                    "hpa_subcellular_reliability_score": reliability_scores.get(row.get("Reliability", ""), 0.0),
                    "hpa_main_location": row.get("Main location", ""),
                    "hpa_additional_location": row.get("Additional location", ""),
                    "hpa_extracellular_location": extracellular_location,
                    "membrane_localization_support": membrane_support,
                    "membrane_support_class": membrane_class,
                    "intracellular_only_hpa": intracellular_only,
                }
    return rows


def normal_critical_summary(critical: dict[str, dict[str, object]]) -> dict[str, object]:
    if not critical:
        return {
            "max_level_score": float("nan"),
            "max_level": "",
            "max_organ": "",
            "best_reliability": "",
            "cell_type_evidence": [],
        }
    max_organ = max(critical, key=lambda organ: float(critical[organ].get("max_level_score", -1.0)))
    max_row = critical[max_organ]
    evidence: list[str] = []
    for organ, row in critical.items():
        evidence.extend(str(item) for item in row.get("cell_type_evidence", [])[:4])
    return {
        "max_level_score": max_row.get("max_level_score", float("nan")),
        "max_level": max_row.get("max_level", ""),
        "max_organ": max_organ,
        "best_reliability": max_row.get("best_reliability", ""),
        "cell_type_evidence": evidence,
    }


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    params = load_yaml(PARAMETERS_CONFIG)
    mappings = load_yaml(TISSUE_MAPPINGS_CONFIG)
    protein_params = params["protein_evidence"]
    level_scores = {str(k): float(v) for k, v in protein_params["hpa_level_scores"].items()}
    reliability_scores = {str(k): float(v) for k, v in protein_params["hpa_reliability_scores"].items()}
    weights = {str(k): float(v) for k, v in protein_params["p_score_weights"].items()}
    penalties = {str(k): float(v) for k, v in protein_params["discordance_penalties"].items()}

    universe = candidate_rows()
    tumor_by_symbol = {row["hgnc_symbol"]: row for row in read_tsv(TUMOR_EXPRESSION)}
    risk_by_symbol = {row["hgnc_symbol"]: row for row in read_tsv(OFF_TUMOR_RISK)}
    cancer = parse_hpa_cancer(universe, level_scores)
    normal_stomach, normal_critical = parse_hpa_normal(universe, mappings, level_scores, reliability_scores)
    subcellular = parse_hpa_subcellular(universe, reliability_scores)

    p_raw_by_symbol: dict[str, float] = {}
    rows: list[dict[str, object]] = []
    for gene in universe:
        symbol = gene["hgnc_symbol"]
        ensembl = gene["ensembl_gene_id"]
        tumor = tumor_by_symbol.get(symbol, {})
        risk = risk_by_symbol.get(symbol, {})
        cancer_row = cancer.get(ensembl)
        normal_stomach_row = normal_stomach.get(ensembl, {})
        critical_summary = normal_critical_summary(normal_critical.get(ensembl, {}))
        subcell = subcellular.get(ensembl, {})

        hpa_tumor_missing = cancer_row is None
        if cancer_row is None:
            counts = {"High": 0, "Medium": 0, "Low": 0, "Not detected": 0}
            total = 0
            protein_tumor_presence = float("nan")
            present_pct = float("nan")
            high_medium_pct = float("nan")
            max_staining = ""
            dominant_staining = ""
        else:
            counts = cancer_row["counts"]
            total = int(cancer_row["total"])
            protein_tumor_presence = float(cancer_row["protein_tumor_presence"])
            present_pct = float(cancer_row["tumor_protein_present_pct"])
            high_medium_pct = float(cancer_row["tumor_high_medium_pct"])
            max_staining = str(cancer_row["max_staining_level"])
            dominant_staining = str(cancer_row["dominant_staining_level"])

        membrane_support = float(subcell.get("membrane_localization_support", 0.0))
        validation_candidates = [
            float(subcell.get("hpa_subcellular_reliability_score", 0.0)),
            reliability_scores.get(str(normal_stomach_row.get("best_reliability", "")), 0.0),
            reliability_scores.get(str(critical_summary.get("best_reliability", "")), 0.0),
        ]
        antibody_validation_support = max(validation_candidates)

        critical_level_score = critical_summary.get("max_level_score", float("nan"))
        if isinstance(critical_level_score, str) or not math.isfinite(float(critical_level_score)):
            normal_protein_safety_support = 0.5
        else:
            normal_protein_safety_support = 1.0 - min(max(float(critical_level_score), 0.0), 3.0) / 3.0

        median_tpm = float(tumor.get("median_tpm_tumor", "nan") or "nan")
        e_rank = float(tumor.get("E_rank_percentile", "nan") or "nan")
        rna_high = (
            math.isfinite(median_tpm)
            and median_tpm >= float(protein_params["rna_high_for_discordance"]["min_median_tpm"])
        ) or (
            math.isfinite(e_rank)
            and e_rank >= float(protein_params["rna_high_for_discordance"]["min_E_rank_percentile"])
        )
        rna_low = math.isfinite(median_tpm) and median_tpm <= float(protein_params["rna_low_for_discordance"]["max_median_tpm"])
        protein_present = math.isfinite(protein_tumor_presence) and protein_tumor_presence >= float(protein_params["protein_present_threshold"])
        protein_absent = cancer_row is not None and total > 0 and counts["High"] + counts["Medium"] + counts["Low"] == 0

        flags: list[str] = []
        penalty = 0.0
        if hpa_tumor_missing:
            flags.append("HPA_missing")
            penalty += penalties["HPA_missing"]
        if rna_high and protein_absent:
            flags.append("RNA_high_protein_absent")
            penalty += penalties["RNA_high_protein_absent"]
        if rna_low and protein_present:
            flags.append("RNA_low_protein_present")
        if protein_present and membrane_support < 0.70:
            flags.append("protein_present_no_membrane")
            penalty += penalties["protein_present_no_membrane"]
        if antibody_validation_support < 0.50:
            flags.append("antibody_low_confidence")
            penalty += penalties["antibody_low_confidence"]
        flags.append("CPTAC_not_assessed")

        if math.isfinite(protein_tumor_presence):
            positive_components = (
                weights["protein_tumor_presence"] * protein_tumor_presence
                + weights["membrane_localization_support"] * membrane_support
                + weights["normal_protein_safety_support"] * normal_protein_safety_support
                + weights["antibody_validation_support"] * antibody_validation_support
            )
            p_score = min(max(positive_components - penalty, 0.0), 1.0)
            p_raw_by_symbol[symbol] = p_score
        else:
            p_score = float("nan")

        rows.append(
            {
                "hgnc_symbol": symbol,
                "ensembl_gene_id": ensembl,
                "uniprot_accession": gene.get("uniprot_accession", ""),
                "surfaceome_category": gene.get("surfaceome_category", ""),
                "hpa_stomach_cancer_total_patients": total,
                "hpa_stomach_cancer_high": counts["High"],
                "hpa_stomach_cancer_medium": counts["Medium"],
                "hpa_stomach_cancer_low": counts["Low"],
                "hpa_stomach_cancer_not_detected": counts["Not detected"],
                "hpa_stomach_cancer_present_pct": fmt(present_pct),
                "hpa_stomach_cancer_high_medium_pct": fmt(high_medium_pct),
                "hpa_stomach_cancer_weighted_presence": fmt(protein_tumor_presence),
                "hpa_stomach_cancer_max_staining": max_staining,
                "hpa_stomach_cancer_dominant_staining": dominant_staining,
                "normal_stomach_protein_level_score": fmt(float(normal_stomach_row.get("max_level_score", float("nan")))),
                "normal_stomach_protein_level": normal_stomach_row.get("max_level", ""),
                "normal_stomach_reliability": normal_stomach_row.get("best_reliability", ""),
                "normal_critical_protein_level_score": fmt(float(critical_summary.get("max_level_score", float("nan")))),
                "normal_critical_protein_level": critical_summary.get("max_level", ""),
                "normal_critical_protein_organ": critical_summary.get("max_organ", ""),
                "hpa_subcellular_reliability": subcell.get("hpa_subcellular_reliability", ""),
                "hpa_main_location": subcell.get("hpa_main_location", ""),
                "hpa_additional_location": subcell.get("hpa_additional_location", ""),
                "hpa_extracellular_location": subcell.get("hpa_extracellular_location", ""),
                "membrane_support_class": subcell.get("membrane_support_class", "missing"),
                "protein_tumor_presence": fmt(protein_tumor_presence),
                "membrane_localization_support": fmt(membrane_support),
                "normal_protein_safety_support": fmt(normal_protein_safety_support),
                "antibody_validation_support": fmt(antibody_validation_support),
                "discordance_penalty": fmt(penalty),
                "P_score": fmt(p_score),
                "P_rank_percentile": "",
                "median_tpm_tumor": tumor.get("median_tpm_tumor", ""),
                "E_rank_percentile": tumor.get("E_rank_percentile", ""),
                "R_score": risk.get("R_score", ""),
                "discordance_flags": ";".join(flags),
                "cptac_status": "CPTAC_not_assessed",
                "hpa_evidence_status": "missing_stomach_cancer_ihc" if hpa_tumor_missing else "stomach_cancer_ihc_available",
                "bulk_limitations": "HPA_cancer_bulk_has_no_antibody_id_intensity_quantity_or_patient_level_membrane_pattern",
            }
        )

    p_ranks = rank_percentiles(p_raw_by_symbol)
    for row in rows:
        symbol = str(row["hgnc_symbol"])
        if symbol in p_ranks:
            row["P_rank_percentile"] = fmt(p_ranks[symbol])
    rows.sort(key=lambda item: str(item["hgnc_symbol"]))

    coverage_rows = build_coverage_rows(rows)
    metadata = {
        "candidate_n": len(universe),
        "hpa_stomach_cancer_covered_n": sum(row["hpa_evidence_status"] == "stomach_cancer_ihc_available" for row in rows),
        "hpa_subcellular_covered_n": sum(bool(row["hpa_main_location"] or row["hpa_additional_location"] or row["hpa_extracellular_location"]) for row in rows),
    }
    return rows, coverage_rows, metadata


def build_coverage_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    total = len(rows)

    def count(predicate) -> int:
        return sum(1 for row in rows if predicate(row))

    coverage = [
        ("hpa_stomach_cancer_ihc", count(lambda row: row["hpa_evidence_status"] == "stomach_cancer_ihc_available"), "HPA cancer_data stomach cancer aggregate patient counts"),
        ("hpa_normal_stomach_ihc", count(lambda row: bool(row["normal_stomach_protein_level"])), "HPA normal_ihc stomach protein level"),
        ("hpa_critical_normal_ihc", count(lambda row: bool(row["normal_critical_protein_level"])), "HPA normal_ihc mapped critical organ protein level"),
        ("hpa_subcellular_location", count(lambda row: bool(row["hpa_main_location"] or row["hpa_additional_location"] or row["hpa_extracellular_location"])), "HPA subcellular_location localization record"),
        ("hpa_membrane_or_cell_junction", count(lambda row: row["membrane_support_class"] in {"plasma_membrane", "cell_junctions"}), "HPA plasma membrane or cell junction support"),
        ("cptac_proteomics", 0, "Not assessed in Fase 7 MVP; retained as explicit flag"),
        ("protein_evidence_P_score_available", count(lambda row: bool(row["P_score"])), "Rows with computable P_score"),
    ]
    return [
        {
            "evidence_layer": layer,
            "n_candidates": total,
            "n_covered": covered,
            "pct_covered": fmt(covered / total if total else float("nan")),
            "notes": notes,
        }
        for layer, covered, notes in coverage
    ]


def plot_rna_protein(rows: list[dict[str, object]], output: Path) -> None:
    measured = [
        row
        for row in rows
        if row.get("median_tpm_tumor") and row.get("hpa_stomach_cancer_weighted_presence") and row.get("P_score")
    ]
    x = np.array([math.log10(float(row["median_tpm_tumor"]) + 0.1) for row in measured], dtype=float)
    y = np.array([float(row["hpa_stomach_cancer_weighted_presence"]) for row in measured], dtype=float)
    color = np.array([float(row["P_score"]) for row in measured], dtype=float)
    symbols = [str(row["hgnc_symbol"]) for row in measured]
    fig, ax = plt.subplots(figsize=(7.6, 5.8))
    scatter = ax.scatter(x, y, c=color, cmap="viridis", s=18, alpha=0.78, linewidths=0)
    ax.set_xlabel("log10(TCGA-STAD median TPM + 0.1)")
    ax.set_ylabel("HPA stomach cancer weighted protein presence")
    ax.set_title("Fase 7 RNA-protein concordance")
    ax.grid(True, linewidth=0.35, alpha=0.25)
    fig.colorbar(scatter, ax=ax, label="P score")
    for symbol in ["ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN", "PTPRC", "PECAM1"]:
        if symbol not in symbols:
            continue
        idx = symbols.index(symbol)
        ax.annotate(symbol, (x[idx], y[idx]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    save_svg(fig, output)
    plt.close(fig)


def write_notes(rows: list[dict[str, object]], coverage_rows: list[dict[str, object]], metadata: dict[str, object]) -> None:
    hpa_missing = sum("HPA_missing" in str(row["discordance_flags"]).split(";") for row in rows)
    rna_high_absent = sum("RNA_high_protein_absent" in str(row["discordance_flags"]).split(";") for row in rows)
    protein_no_membrane = sum("protein_present_no_membrane" in str(row["discordance_flags"]).split(";") for row in rows)
    low_conf = sum("antibody_low_confidence" in str(row["discordance_flags"]).split(";") for row in rows)
    coverage_lines = "\n".join(
        f"- {row['evidence_layer']}: {row['n_covered']}/{row['n_candidates']} ({row['pct_covered']})"
        for row in coverage_rows
    )
    (DOCS_DIR / "fase7_protein_evidence.md").write_text(
        f"""# Fase 7 Protein Evidence And Localization

Access date: {dt.date.today().isoformat()}

Fase 7 separates tumor RNA expression from protein evidence and localization. The MVP uses HPA stomach cancer IHC aggregate counts, HPA normal tissue IHC, and HPA subcellular localization. CPTAC/PDC and literature curation remain downstream/candidate-level layers and are marked `CPTAC_not_assessed` here.

## Coverage

{coverage_lines}

## P Score

`P_score` is a component score only. It combines:

- tumor protein presence in HPA stomach cancer;
- membrane/cell-junction localization support from HPA subcellular location;
- normal protein safety support from mapped critical normal IHC;
- HPA reliability support;
- penalties for discordance.

The HPA cancer bulk file does not expose antibody IDs, staining intensity/quantity fields, patient-level membrane pattern, or multi-antibody concordance. Those fields are therefore not imputed and must be revisited during candidate-card manual curation.

## Discordance Summary

- HPA missing stomach cancer IHC: {hpa_missing}
- RNA high but tumor protein absent: {rna_high_absent}
- Protein present without membrane/cell-junction support: {protein_no_membrane}
- Low-confidence HPA evidence: {low_conf}

## Rules Preserved

- HPA not detected with low-confidence evidence does not automatically eliminate a target.
- CPTAC total proteomics would support total protein, not surface localization; it is not used in this MVP Fase 7 run.
- IHC plus membrane localization is weighted more directly than total-protein evidence for antibody/ADC-style targeting.

## Outputs

- `data/processed/protein_evidence.tsv`
- `results/tables/protein_coverage.tsv`
- `results/figures/rna_protein_concordance.svg`
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args(argv)
    rows, coverage_rows, metadata = build_rows()
    write_tsv(
        PROCESSED_DIR / "protein_evidence.tsv",
        rows,
        [
            "hgnc_symbol",
            "ensembl_gene_id",
            "uniprot_accession",
            "surfaceome_category",
            "hpa_stomach_cancer_total_patients",
            "hpa_stomach_cancer_high",
            "hpa_stomach_cancer_medium",
            "hpa_stomach_cancer_low",
            "hpa_stomach_cancer_not_detected",
            "hpa_stomach_cancer_present_pct",
            "hpa_stomach_cancer_high_medium_pct",
            "hpa_stomach_cancer_weighted_presence",
            "hpa_stomach_cancer_max_staining",
            "hpa_stomach_cancer_dominant_staining",
            "normal_stomach_protein_level_score",
            "normal_stomach_protein_level",
            "normal_stomach_reliability",
            "normal_critical_protein_level_score",
            "normal_critical_protein_level",
            "normal_critical_protein_organ",
            "hpa_subcellular_reliability",
            "hpa_main_location",
            "hpa_additional_location",
            "hpa_extracellular_location",
            "membrane_support_class",
            "protein_tumor_presence",
            "membrane_localization_support",
            "normal_protein_safety_support",
            "antibody_validation_support",
            "discordance_penalty",
            "P_score",
            "P_rank_percentile",
            "median_tpm_tumor",
            "E_rank_percentile",
            "R_score",
            "discordance_flags",
            "cptac_status",
            "hpa_evidence_status",
            "bulk_limitations",
        ],
    )
    write_tsv(
        TABLES_DIR / "protein_coverage.tsv",
        coverage_rows,
        ["evidence_layer", "n_candidates", "n_covered", "pct_covered", "notes"],
    )
    plot_rna_protein(rows, FIGURES_DIR / "rna_protein_concordance.svg")
    write_notes(rows, coverage_rows, metadata)
    print("Wrote Fase 7 protein evidence and localization outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
