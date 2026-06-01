"""Build the required Xena/Toil Fase 2 PCA and PERMANOVA batch diagnostic."""

from __future__ import annotations

import argparse
import csv
import gzip
import heapq
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[1]
PHENOTYPE_PATH = REPO_ROOT / "data" / "raw" / "xena_toil" / "TcgaTargetGTEX_phenotype.txt.gz"
MATRIX_PATH = REPO_ROOT / "data" / "raw" / "xena_toil" / "TcgaTargetGtex_rsem_gene_tpm.gz"
TABLES_DIR = REPO_ROOT / "results" / "tables"
FIGURES_DIR = REPO_ROOT / "results" / "figures"
DOCS_DIR = REPO_ROOT / "docs"
CONFIG_DATASETS = REPO_ROOT / "config" / "datasets.yaml"

SEED = 20260528


@dataclass(frozen=True)
class SelectedSample:
    sample: str
    study: str
    sample_type: str
    detailed_category: str
    analysis_group: str


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_selected_samples() -> dict[str, SelectedSample]:
    selected: dict[str, SelectedSample] = {}
    with gzip.open(PHENOTYPE_PATH, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            sample = row["sample"]
            study = row["_study"]
            detailed_category = row["detailed_category"]
            sample_type = row["_sample_type"]
            if study == "TCGA" and detailed_category == "Stomach Adenocarcinoma" and sample_type == "Primary Tumor":
                group = "TCGA-STAD primary tumor"
            elif study == "TCGA" and detailed_category == "Stomach Adenocarcinoma" and sample_type == "Solid Tissue Normal":
                group = "TCGA-STAD adjacent normal"
            elif study == "GTEX" and detailed_category == "Stomach" and sample_type == "Normal Tissue":
                group = "GTEx stomach normal"
            else:
                continue
            selected[sample] = SelectedSample(
                sample=sample,
                study=study,
                sample_type=sample_type,
                detailed_category=detailed_category,
                analysis_group=group,
            )
    return selected


def extract_top_variable_matrix(selected: dict[str, SelectedSample], top_n: int) -> tuple[list[str], list[SelectedSample], np.ndarray, np.ndarray]:
    with gzip.open(MATRIX_PATH, "rt", encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        matrix_samples = header[1:]
        sample_to_index = {sample: idx + 1 for idx, sample in enumerate(matrix_samples)}
        ordered_samples = [selected[sample] for sample in matrix_samples if sample in selected]
        selected_indices = [sample_to_index[sample.sample] for sample in ordered_samples]
        if not selected_indices:
            raise RuntimeError("No selected Xena phenotype samples were present in the matrix header.")

        top_genes: list[tuple[float, int, str, np.ndarray]] = []
        rows_seen = 0
        rows_kept = 0
        for raw_line in handle:
            rows_seen += 1
            parts = raw_line.rstrip("\n").split("\t")
            gene_id = parts[0]
            values = np.fromiter((float(parts[idx]) for idx in selected_indices), dtype=np.float32, count=len(selected_indices))
            if not np.isfinite(values).all():
                continue
            variance = float(np.var(values))
            if variance <= 0:
                continue
            rows_kept += 1
            entry = (variance, rows_seen, gene_id, values)
            if len(top_genes) < top_n:
                heapq.heappush(top_genes, entry)
            elif variance > top_genes[0][0]:
                heapq.heapreplace(top_genes, entry)

    top_genes_sorted = sorted(top_genes, reverse=True)
    gene_ids = [entry[2] for entry in top_genes_sorted]
    gene_variances = np.array([entry[0] for entry in top_genes_sorted], dtype=np.float64)
    matrix = np.vstack([entry[3] for entry in top_genes_sorted]).T
    print(f"Scanned {rows_seen} matrix rows; retained {rows_kept}; selected top {len(gene_ids)} variable genes.")
    return gene_ids, ordered_samples, matrix, gene_variances


def permanova(features: np.ndarray, labels: np.ndarray, permutations: int, seed: int) -> dict[str, object]:
    labels = np.asarray(labels)
    unique_labels = np.unique(labels)
    n = features.shape[0]
    k = len(unique_labels)
    if k < 2 or n <= k:
        raise ValueError("PERMANOVA requires at least two groups and more samples than groups.")

    sum_sq = np.sum(features * features, axis=1)
    dist2 = sum_sq[:, None] + sum_sq[None, :] - 2.0 * features.dot(features.T)
    dist2 = np.maximum(dist2, 0.0)
    row_mean = dist2.mean(axis=1, keepdims=True)
    col_mean = dist2.mean(axis=0, keepdims=True)
    grand_mean = dist2.mean()
    centered = -0.5 * (dist2 - row_mean - col_mean + grand_mean)
    total_ss = float(np.trace(centered))

    def between_ss(group_labels: np.ndarray) -> float:
        ss = 0.0
        for label in np.unique(group_labels):
            idx = np.flatnonzero(group_labels == label)
            ss += float(centered[np.ix_(idx, idx)].sum()) / len(idx)
        return ss

    observed_ss = between_ss(labels)
    within_ss = total_ss - observed_ss
    pseudo_f = (observed_ss / (k - 1)) / (within_ss / (n - k))

    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(permutations):
        permuted = rng.permutation(labels)
        perm_ss = between_ss(permuted)
        perm_within = total_ss - perm_ss
        perm_f = (perm_ss / (k - 1)) / (perm_within / (n - k))
        if perm_f >= pseudo_f:
            exceedances += 1

    p_value = (exceedances + 1) / (permutations + 1)
    return {
        "n_samples": n,
        "n_groups": k,
        "df_between": k - 1,
        "df_within": n - k,
        "ss_between": observed_ss,
        "ss_total": total_ss,
        "r2": observed_ss / total_ss if total_ss else np.nan,
        "pseudo_f": pseudo_f,
        "permutations": permutations,
        "p_value": p_value,
    }


def make_plot(scores: np.ndarray, samples: list[SelectedSample], explained: np.ndarray, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    group_order = ["TCGA-STAD primary tumor", "TCGA-STAD adjacent normal", "GTEx stomach normal"]
    colors = {
        "TCGA-STAD primary tumor": "#2563eb",
        "TCGA-STAD adjacent normal": "#059669",
        "GTEx stomach normal": "#dc2626",
    }
    markers = {
        "TCGA-STAD primary tumor": "o",
        "TCGA-STAD adjacent normal": "^",
        "GTEx stomach normal": "s",
    }
    groups = np.array([sample.analysis_group for sample in samples])
    fig, ax = plt.subplots(figsize=(8.0, 6.0))
    for group in group_order:
        idx = groups == group
        if not np.any(idx):
            continue
        ax.scatter(
            scores[idx, 0],
            scores[idx, 1],
            s=24,
            alpha=0.72,
            linewidths=0.25,
            edgecolors="white",
            c=colors[group],
            marker=markers[group],
            label=f"{group} (n={idx.sum()})",
        )
    ax.axhline(0, color="#d1d5db", linewidth=0.8)
    ax.axvline(0, color="#d1d5db", linewidth=0.8)
    ax.set_xlabel(f"PC1 ({explained[0] * 100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({explained[1] * 100:.1f}% variance)")
    ax.set_title("Xena/Toil TCGA-STAD and GTEx stomach PCA diagnostic")
    ax.legend(frameon=False, loc="best", fontsize=9)
    ax.grid(True, linewidth=0.35, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, format="svg")
    plt.close(fig)


def update_config_status() -> None:
    if not CONFIG_DATASETS.exists():
        return
    lines = CONFIG_DATASETS.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    current_id: str | None = None
    for line in lines:
        stripped = line.strip()
        if line.startswith("status: "):
            line = 'status: "fase2_mvp_downloads_and_batch_diagnostic_complete"'
        elif stripped.startswith("- id: "):
            current_id = stripped.split(":", 1)[1].strip().strip('"')
        elif current_id == "xena_toil_tcga_gtex" and line.startswith("    status: "):
            line = '    status: "raw_downloaded_with_checksums_batch_diagnostic_complete"'
        updated.append(line)
    CONFIG_DATASETS.write_text("\n".join(updated) + "\n", encoding="utf-8")


def write_notes(sample_counts: dict[str, int], pca_explained: np.ndarray, permanova_rows: list[dict[str, object]]) -> None:
    formatted = "\n".join(
        "| {test_id} | {grouping_variable} | {n_samples} | {n_groups} | {r2:.4f} | {pseudo_f:.4f} | {p_value:.4f} | {interpretation} |".format(
            **row
        )
        for row in permanova_rows
    )
    counts = "\n".join(f"- {group}: {count}" for group, count in sorted(sample_counts.items()))
    (DOCS_DIR / "fase2_batch_diagnostic.md").write_text(
        f"""# Fase 2 Xena/Toil Batch Diagnostic

Access date: 2026-05-28

This diagnostic uses the downloaded Xena/Toil `TcgaTargetGtex_rsem_gene_tpm.gz` matrix and phenotype file. The matrix was restricted to TCGA-STAD primary tumor, TCGA-STAD adjacent normal, and GTEx stomach normal samples, then PCA and PERMANOVA were run on the top variable genes.

## Sample Counts

{counts}

## PCA

- Output: `results/figures/pca_batch_diagnostic.svg`
- PC1 variance: {pca_explained[0] * 100:.2f}%
- PC2 variance: {pca_explained[1] * 100:.2f}%

## PERMANOVA

| Test | Grouping | Samples | Groups | R2 | pseudo-F | p-value | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|
{formatted}

## Gate Decision

Fase 2 batch diagnostic outputs now exist. The diagnostic is not a permission to ignore source effects: Fase 5 must keep TCGA/GTEx source labels in the analysis notes, and GDC adjacent-normal sensitivity remains required before strong tumor-normal selectivity claims.
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-variable-genes", type=int, default=2000)
    parser.add_argument("--permutations", type=int, default=999)
    args = parser.parse_args(argv)

    selected = load_selected_samples()
    gene_ids, samples, matrix, variances = extract_top_variable_matrix(selected, top_n=args.top_variable_genes)
    sample_rows = [
        {
            "sample": sample.sample,
            "study": sample.study,
            "sample_type": sample.sample_type,
            "detailed_category": sample.detailed_category,
            "analysis_group": sample.analysis_group,
        }
        for sample in samples
    ]
    write_tsv(
        TABLES_DIR / "xena_batch_diagnostic_samples.tsv",
        sample_rows,
        ["sample", "study", "sample_type", "detailed_category", "analysis_group"],
    )
    write_tsv(
        TABLES_DIR / "xena_top_variable_genes.tsv",
        [{"gene_id": gene, "variance": variance} for gene, variance in zip(gene_ids, variances)],
        ["gene_id", "variance"],
    )

    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    pca = PCA(n_components=2, random_state=SEED)
    scores = pca.fit_transform(scaled)
    make_plot(scores, samples, pca.explained_variance_ratio_, FIGURES_DIR / "pca_batch_diagnostic.svg")

    groups = np.array([sample.analysis_group for sample in samples])
    studies = np.array([sample.study for sample in samples])
    normal_mask = np.isin(groups, ["TCGA-STAD adjacent normal", "GTEx stomach normal"])

    tests = [
        (
            "study_all_samples",
            "study",
            studies,
            np.ones(len(samples), dtype=bool),
            "Confounded with tumor/normal biology because GTEx contributes only normal tissue.",
        ),
        (
            "sample_group_all_samples",
            "analysis_group",
            groups,
            np.ones(len(samples), dtype=bool),
            "Describes combined biology and source structure; not a pure batch test.",
        ),
        (
            "normal_source_only",
            "normal_source",
            groups,
            normal_mask,
            "Most relevant source diagnostic: TCGA adjacent normal versus GTEx stomach normal.",
        ),
    ]
    permanova_rows: list[dict[str, object]] = []
    for idx, (test_id, grouping, labels, mask, interpretation) in enumerate(tests):
        result = permanova(scaled[mask], labels[mask], permutations=args.permutations, seed=SEED + idx)
        permanova_rows.append(
            {
                "test_id": test_id,
                "grouping_variable": grouping,
                **result,
                "interpretation": interpretation,
            }
        )
    write_tsv(
        TABLES_DIR / "batch_permanova.tsv",
        permanova_rows,
        [
            "test_id",
            "grouping_variable",
            "n_samples",
            "n_groups",
            "df_between",
            "df_within",
            "ss_between",
            "ss_total",
            "r2",
            "pseudo_f",
            "permutations",
            "p_value",
            "interpretation",
        ],
    )

    counts = {group: int(np.sum(groups == group)) for group in sorted(np.unique(groups))}
    write_notes(counts, pca.explained_variance_ratio_, permanova_rows)
    update_config_status()
    print("Wrote Xena/Toil batch diagnostic PCA and PERMANOVA outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
