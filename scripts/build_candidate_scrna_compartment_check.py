from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import math
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "tisch2"
CHECKSUM_DIR = ROOT / "data" / "checksums"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"
DOCS_DIR = ROOT / "docs"
FROZEN_ACCESS_DATE = "2026-06-01"

CANDIDATE_TABLE = TABLES_DIR / "manuscript_table3_top_candidates.tsv"
OUTPUT_TABLE = TABLES_DIR / "candidate_scrna_tisch2_compartment_check.tsv"
OUTPUT_SUMMARY = TABLES_DIR / "candidate_scrna_tisch2_summary.tsv"
OUTPUT_FIGURE = FIGURES_DIR / "candidate_scrna_tisch2_compartment_heatmap.svg"
OUTPUT_DOC = DOCS_DIR / "candidate_scrna_compartment_check.md"
CHECKSUM_TABLE = CHECKSUM_DIR / "tisch2_candidate_scrna_sha256.tsv"

TISCH2_BASE = "https://tisch.compbio.cn/static/data"
DATASETS = {
    "STAD_GSE134520": {
        "pmid": "31067475",
        "citation": "Zhang et al., Cell Reports 2019",
        "scope": "gastric premalignant lesions and early gastric cancer; TISCH2 includes Malignant cells",
    },
    "STAD_GSE167297": {
        "pmid": "34385296",
        "citation": "Jeong et al., Clinical Cancer Research 2021",
        "scope": "diffuse-type gastric cancer TME; TISCH2 has no malignant-cell class",
    },
}

MALIGNANCY_COLUMNS = ["Malignant cells", "Immune cells", "Stromal cells"]
MAJOR_COLUMNS = [
    "Malignant",
    "Epithelial",
    "Pit mucous",
    "Gland mucous",
    "Fibroblasts",
    "Myofibroblasts",
    "Endothelial",
    "DC",
    "Mono/Macro",
    "B",
    "Plasma",
    "CD8T",
    "Mast",
]
DETECTABLE_MEAN = 0.05


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


def download_file(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "surfaceome-gastric-cancer-scrna/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:
        path.write_bytes(response.read())


def download_dataset(dataset: str) -> dict[str, Path]:
    dataset_dir = RAW_DIR / dataset
    expression_zip = dataset_dir / f"{dataset}_Expression.zip"
    meta_table = dataset_dir / f"{dataset}_CellMetainfo_table.tsv"
    download_file(f"{TISCH2_BASE}/{dataset}/{dataset}_Expression.zip", expression_zip)
    download_file(f"{TISCH2_BASE}/{dataset}/{dataset}_CellMetainfo_table.tsv", meta_table)
    return {"expression_zip": expression_zip, "meta_table": meta_table}


def read_expression(zip_path: Path, suffix: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if suffix in name and name.endswith(".txt")]
        if len(names) != 1:
            raise RuntimeError(f"expected exactly one {suffix} file in {zip_path}, found {names}")
        with archive.open(names[0]) as handle:
            return pd.read_csv(handle, sep="\t", index_col=0)


def fmt(value: object, digits: int = 5) -> str:
    if value is None:
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(numeric):
        return ""
    return f"{numeric:.{digits}f}"


def column_value(frame: pd.DataFrame, gene: str, column: str) -> float | None:
    if column not in frame.columns or gene not in frame.index:
        return None
    value = frame.at[gene, column]
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def top_column(values: dict[str, float | None]) -> tuple[str, float]:
    finite = {key: value for key, value in values.items() if value is not None and math.isfinite(value)}
    if not finite:
        return "", float("nan")
    return max(finite.items(), key=lambda item: (item[1], item[0]))


def classify_gene(has_malignant: bool, malignancy_values: dict[str, float | None]) -> str:
    if not has_malignant:
        return "context_only_no_malignant_class"
    malignant = malignancy_values.get("Malignant cells")
    nonmalignant = [
        value
        for key, value in malignancy_values.items()
        if key != "Malignant cells" and value is not None and math.isfinite(value)
    ]
    if malignant is None or not math.isfinite(malignant):
        return "missing_gene"
    if malignant < DETECTABLE_MEAN:
        return "low_malignant_signal_in_dataset"
    max_nonmalignant = max(nonmalignant) if nonmalignant else 0.0
    if malignant >= max_nonmalignant:
        return "malignant_class_supported"
    if malignant >= 0.5 * max_nonmalignant:
        return "mixed_malignant_and_nonmalignant_signal"
    return "nonmalignant_dominant_signal"


def interpretation(call: str, top_major: str) -> str:
    if call == "malignant_class_supported":
        return "candidate has direct malignant-cell expression support in this TISCH2 dataset"
    if call == "mixed_malignant_and_nonmalignant_signal":
        return "candidate is expressed in malignant cells but also has substantial non-malignant/TME signal"
    if call == "low_malignant_signal_in_dataset":
        return "candidate is not supported as malignant-cell expressed in this dataset"
    if call == "nonmalignant_dominant_signal":
        return "candidate is more strongly expressed in non-malignant compartments in this dataset"
    if call == "context_only_no_malignant_class" and top_major:
        return f"dataset provides compartment context only; top major lineage is {top_major}"
    return "candidate-level scRNA context only"


def meta_counts(meta_path: Path) -> tuple[Counter[str], Counter[str], int, int]:
    rows = read_tsv(meta_path)
    malignancy = Counter(row.get("Celltype (malignancy)", "") for row in rows)
    major = Counter(row.get("Celltype (major-lineage)", "") for row in rows)
    sample_field = "Sample" if rows and "Sample" in rows[0] else ""
    samples = len({row.get(sample_field, "") for row in rows if sample_field and row.get(sample_field, "")})
    return malignancy, major, len(rows), samples


def build_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    candidates = read_tsv(CANDIDATE_TABLE)
    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    checksum_rows: list[dict[str, object]] = []
    checksum_entries: dict[str, str] = {}

    for dataset, info in DATASETS.items():
        paths = download_dataset(dataset)
        for label, path in paths.items():
            rel_path = path.relative_to(ROOT).as_posix()
            checksum = sha256_file(path)
            checksum_entries[rel_path] = checksum
            checksum_rows.append(
                {
                    "dataset": dataset,
                    "artifact": label,
                    "local_path": rel_path,
                    "url": f"{TISCH2_BASE}/{dataset}/{path.name}",
                    "retrieval_date": FROZEN_ACCESS_DATE,
                    "bytes": path.stat().st_size,
                    "sha256": checksum,
                    "license_or_terms": "TISCH2 public download; source studies remain under their original terms",
                }
            )

        malignancy_expr = read_expression(paths["expression_zip"], "Celltype_malignancy")
        major_expr = read_expression(paths["expression_zip"], "Celltype_majorlineage")
        malignancy_counts, major_counts, total_cells, sample_count = meta_counts(paths["meta_table"])
        has_malignant = "Malignant cells" in malignancy_expr.columns

        dataset_rows: list[dict[str, object]] = []
        for candidate in candidates:
            gene = candidate["gene"]
            malignancy_values = {column: column_value(malignancy_expr, gene, column) for column in MALIGNANCY_COLUMNS}
            major_values = {column: column_value(major_expr, gene, column) for column in MAJOR_COLUMNS}
            top_malignancy, top_malignancy_mean = top_column(malignancy_values)
            top_major, top_major_mean = top_column(major_values)
            malignant = malignancy_values.get("Malignant cells")
            nonmalignant_values = [
                value
                for key, value in malignancy_values.items()
                if key != "Malignant cells" and value is not None and math.isfinite(value)
            ]
            max_nonmalignant = max(nonmalignant_values) if nonmalignant_values else None
            delta = None if malignant is None or max_nonmalignant is None else malignant - max_nonmalignant
            ratio = (
                None
                if malignant is None or max_nonmalignant is None
                else (malignant + 1e-6) / (max_nonmalignant + 1e-6)
            )
            call = classify_gene(has_malignant, malignancy_values)
            row = {
                "gene": gene,
                "tier": candidate["tier"],
                "dataset": dataset,
                "pmid": info["pmid"],
                "citation": info["citation"],
                "dataset_scope": info["scope"],
                "n_cells_total": total_cells,
                "n_samples": sample_count,
                "n_malignant_cells": malignancy_counts.get("Malignant cells", 0),
                "has_malignant_class": str(has_malignant).lower(),
                "mean_malignant_cells": fmt(malignant),
                "mean_immune_cells": fmt(malignancy_values.get("Immune cells")),
                "mean_stromal_cells": fmt(malignancy_values.get("Stromal cells")),
                "mean_epithelial": fmt(major_values.get("Epithelial")),
                "mean_pit_mucous": fmt(major_values.get("Pit mucous")),
                "mean_gland_mucous": fmt(major_values.get("Gland mucous")),
                "mean_fibroblasts": fmt(major_values.get("Fibroblasts")),
                "mean_myofibroblasts": fmt(major_values.get("Myofibroblasts")),
                "mean_endothelial": fmt(major_values.get("Endothelial")),
                "mean_dc": fmt(major_values.get("DC")),
                "mean_mono_macro": fmt(major_values.get("Mono/Macro")),
                "mean_b": fmt(major_values.get("B")),
                "mean_plasma": fmt(major_values.get("Plasma")),
                "mean_cd8t": fmt(major_values.get("CD8T")),
                "mean_mast": fmt(major_values.get("Mast")),
                "top_malignancy_class": top_malignancy,
                "top_malignancy_mean": fmt(top_malignancy_mean),
                "top_major_lineage": top_major,
                "top_major_lineage_mean": fmt(top_major_mean),
                "malignant_minus_max_nonmalignant": fmt(delta),
                "malignant_to_max_nonmalignant_ratio": fmt(ratio),
                "candidate_scrna_call": call,
                "manuscript_interpretation": interpretation(call, top_major),
                "score_usage": "candidate_annotation_only_not_numeric_SC_score",
            }
            rows.append(row)
            dataset_rows.append(row)

        summary.append(
            {
                "dataset": dataset,
                "pmid": info["pmid"],
                "citation": info["citation"],
                "n_cells_total": total_cells,
                "n_samples": sample_count,
                "n_malignant_cells": malignancy_counts.get("Malignant cells", 0),
                "has_malignant_class": str(has_malignant).lower(),
                "genes_assessed": len(candidates),
                "genes_present_in_expression_matrix": sum(
                    1 for candidate in candidates if candidate["gene"] in malignancy_expr.index
                ),
                "genes_with_malignant_class_supported": sum(
                    1 for row in dataset_rows if row["candidate_scrna_call"] == "malignant_class_supported"
                ),
                "genes_with_mixed_malignant_signal": sum(
                    1 for row in dataset_rows if row["candidate_scrna_call"] == "mixed_malignant_and_nonmalignant_signal"
                ),
                "genes_with_low_malignant_signal": sum(
                    1 for row in dataset_rows if row["candidate_scrna_call"] == "low_malignant_signal_in_dataset"
                ),
                "genes_context_only": sum(
                    1 for row in dataset_rows if row["candidate_scrna_call"] == "context_only_no_malignant_class"
                ),
                "malignancy_cell_counts": ";".join(f"{key}:{value}" for key, value in sorted(malignancy_counts.items())),
                "major_lineage_cell_counts": ";".join(f"{key}:{value}" for key, value in sorted(major_counts.items())),
            }
        )

    write_tsv(CHECKSUM_TABLE, checksum_rows, list(checksum_rows[0]))
    update_global_sha256sums(checksum_entries)
    return rows, summary


def write_figure(rows: list[dict[str, object]]) -> None:
    selected_dataset = "STAD_GSE134520"
    genes = [row["gene"] for row in rows if row["dataset"] == selected_dataset]
    columns = [
        "mean_malignant_cells",
        "mean_stromal_cells",
        "mean_immune_cells",
        "mean_pit_mucous",
        "mean_gland_mucous",
        "mean_fibroblasts",
        "mean_endothelial",
        "mean_dc",
    ]
    labels = [
        "Malignant",
        "Stromal",
        "Immune",
        "Pit mucous",
        "Gland mucous",
        "Fibroblasts",
        "Endothelial",
        "DC",
    ]
    matrix: list[list[float]] = []
    for gene in genes:
        row = next(item for item in rows if item["dataset"] == selected_dataset and item["gene"] == gene)
        matrix.append([float(row.get(column) or 0.0) for column in columns])

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.2, 6.0))
    image = ax.imshow(matrix, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
    ax.set_yticks(range(len(genes)), labels=genes)
    ax.set_title("TISCH2 STAD_GSE134520 candidate-level scRNA compartment check", fontsize=10)
    ax.set_xlabel("TISCH2 cell type")
    ax.set_ylabel("Tier 1/2 candidate")
    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Mean normalized expression")
    fig.tight_layout()
    fig.savefig(OUTPUT_FIGURE, format="svg")
    plt.close(fig)


def write_doc(rows: list[dict[str, object]], summary: list[dict[str, object]]) -> None:
    by_call = Counter(row["candidate_scrna_call"] for row in rows if row["dataset"] == "STAD_GSE134520")
    malignant_supported = [
        row["gene"]
        for row in rows
        if row["dataset"] == "STAD_GSE134520" and row["candidate_scrna_call"] == "malignant_class_supported"
    ]
    mixed = [
        row["gene"]
        for row in rows
        if row["dataset"] == "STAD_GSE134520" and row["candidate_scrna_call"] == "mixed_malignant_and_nonmalignant_signal"
    ]
    low = [
        row["gene"]
        for row in rows
        if row["dataset"] == "STAD_GSE134520" and row["candidate_scrna_call"] == "low_malignant_signal_in_dataset"
    ]
    nonmalignant_dominant = [
        row["gene"]
        for row in rows
        if row["dataset"] == "STAD_GSE134520" and row["candidate_scrna_call"] == "nonmalignant_dominant_signal"
    ]
    lines = [
        "# Candidate-Level scRNA Compartment Check",
        "",
        f"Access date: {FROZEN_ACCESS_DATE}",
        "",
        "This is a post-ranking candidate-level cross-check. It does not change the numeric `SC` component,",
        "the frozen ranking, or the Tier 1/Tier 2 assignments. Its purpose is to reduce overclaiming by",
        "annotating whether the 18 nominated candidates show malignant-cell, epithelial, stromal, endothelial,",
        "or immune/TME expression in public processed gastric scRNA resources.",
        "",
        "## Sources",
        "",
    ]
    for item in summary:
        lines.append(
            f"- `{item['dataset']}` ({item['citation']}, PMID {item['pmid']}): "
            f"{item['n_cells_total']} cells, {item['n_samples']} samples, "
            f"malignant cells annotated: {item['n_malignant_cells']}."
        )
    lines.extend(
        [
            "",
            "TISCH2 average cell-type expression matrices and cell metadata were downloaded from the public",
            "TISCH2 dataset pages. Expression values are used as TISCH2-normalized mean expression summaries,",
            "not as raw UMI counts.",
            "",
            "## STAD_GSE134520 Summary",
            "",
            f"- Candidate calls: {dict(sorted(by_call.items()))}",
            f"- Malignant-class supported: {';'.join(malignant_supported) if malignant_supported else 'none'}",
            f"- Mixed malignant and non-malignant signal: {';'.join(mixed) if mixed else 'none'}",
            f"- Low malignant signal in this dataset: {';'.join(low) if low else 'none'}",
            f"- Non-malignant dominant signal: {';'.join(nonmalignant_dominant) if nonmalignant_dominant else 'none'}",
            "",
            "Interpretation: the limited scRNA cross-check strengthens compartment caveats. It provides direct",
            "malignant-cell support for a subset of candidates but does not resolve cell-of-origin for all Tier 1/2",
            "genes. Some clinically or biologically plausible epithelial antigens are low in the early-cancer",
            "TISCH2 malignant-cell class, so absence of support here is not treated as an exclusion.",
            "",
            "## Outputs",
            "",
            f"- `{OUTPUT_TABLE.relative_to(ROOT).as_posix()}`",
            f"- `{OUTPUT_SUMMARY.relative_to(ROOT).as_posix()}`",
            f"- `{OUTPUT_FIGURE.relative_to(ROOT).as_posix()}`",
            f"- `{CHECKSUM_TABLE.relative_to(ROOT).as_posix()}`",
        ]
    )
    OUTPUT_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rows, summary = build_rows()
    fieldnames = [
        "gene",
        "tier",
        "dataset",
        "pmid",
        "citation",
        "dataset_scope",
        "n_cells_total",
        "n_samples",
        "n_malignant_cells",
        "has_malignant_class",
        "mean_malignant_cells",
        "mean_immune_cells",
        "mean_stromal_cells",
        "mean_epithelial",
        "mean_pit_mucous",
        "mean_gland_mucous",
        "mean_fibroblasts",
        "mean_myofibroblasts",
        "mean_endothelial",
        "mean_dc",
        "mean_mono_macro",
        "mean_b",
        "mean_plasma",
        "mean_cd8t",
        "mean_mast",
        "top_malignancy_class",
        "top_malignancy_mean",
        "top_major_lineage",
        "top_major_lineage_mean",
        "malignant_minus_max_nonmalignant",
        "malignant_to_max_nonmalignant_ratio",
        "candidate_scrna_call",
        "manuscript_interpretation",
        "score_usage",
    ]
    write_tsv(OUTPUT_TABLE, rows, fieldnames)
    write_tsv(OUTPUT_SUMMARY, summary, list(summary[0]))
    write_figure(rows)
    write_doc(rows, summary)
    print(f"Wrote {OUTPUT_TABLE.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_FIGURE.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_DOC.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
