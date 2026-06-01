"""Build Fase 16 manuscript-ready figures and tables.

This phase repackages frozen Fase 13-15 outputs for manuscript use. It does
not change scores, weights, universe membership, ranking, or tier assignments.
"""

from __future__ import annotations

import csv
import hashlib
import math
import re
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.patches import FancyArrowPatch, Rectangle


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
VALIDATION_DIR = RESULTS_DIR / "validation"
DOCS_DIR = REPO_ROOT / "docs"

SURFACEOME_UNIVERSE = DATA_DIR / "processed" / "surfaceome_universe.tsv"
TUMOR_EXPRESSION = DATA_DIR / "processed" / "tumor_expression.tsv"
SELECTIVITY_SCORES = DATA_DIR / "processed" / "selectivity_scores.tsv"
OFF_TUMOR_RISK = DATA_DIR / "processed" / "off_tumor_risk.tsv"
COMPONENT_SCORES = TABLES_DIR / "component_scores_all_candidates.tsv"
TIER_ASSIGNMENTS = TABLES_DIR / "tier_assignments.tsv"
DATASET_INVENTORY = TABLES_DIR / "dataset_inventory.tsv"
SURFACEOME_SUMMARY = TABLES_DIR / "surfaceome_confidence_summary.tsv"
PROTEIN_COVERAGE = TABLES_DIR / "protein_coverage.tsv"
WANG_CROSSCHECK = TABLES_DIR / "wang2026_crosscheck.tsv"
WANG_OVERLAP_ENRICHMENT = TABLES_DIR / "wang2026_overlap_enrichment.tsv"
WANG_MATCHED_NULL = TABLES_DIR / "wang2026_matched_null.tsv"
GPI_CORRECTION_IMPACT = TABLES_DIR / "gpi_correction_impact.tsv"
GPI_RANK_DELTA = TABLES_DIR / "gpi_rank_delta_v1_v2.tsv"
EXTERNAL_BASELINE_COMPARISON = TABLES_DIR / "external_surfaceome_baseline_comparison.tsv"
SURFACEOME_SOURCE_DEPENDENCY_AUDIT = TABLES_DIR / "surfaceome_source_dependency_audit.tsv"
SURFACEOME_SOURCE_DEPENDENCY_SUMMARY = TABLES_DIR / "surfaceome_source_dependency_summary.tsv"
CANDIDATE_SCRNA_TISCH2 = TABLES_DIR / "candidate_scrna_tisch2_compartment_check.tsv"
CONTROL_BENCHMARK = VALIDATION_DIR / "control_benchmark.tsv"
CONTROL_RECOVERY = TABLES_DIR / "control_recovery_phase13.tsv"
RANK_STABILITY = VALIDATION_DIR / "rank_stability.tsv"
TOP30_AUDIT = VALIDATION_DIR / "top30_false_positive_audit.tsv"
RANKING_V2 = RESULTS_DIR / "rankings" / "ranking_v2_frozen.tsv"
SCORING_CONFIG = REPO_ROOT / "config" / "scoring_scenarios.yaml"

PHASE16_NOTE = DOCS_DIR / "fase16_figures_tables.md"
PIPELINE_FIGURE = FIGURES_DIR / "phase16_pipeline_overview.svg"
SURFACEOME_FIGURE = FIGURES_DIR / "phase16_surfaceome_evidence_landscape.svg"
SELECTIVITY_FIGURE = FIGURES_DIR / "phase16_tumor_normal_selectivity.svg"
HEATMAP_FIGURE = FIGURES_DIR / "phase16_multilayer_heatmap_top30.svg"
BENCHMARK_FIGURE = FIGURES_DIR / "phase16_benchmark_controls.svg"
TIER1_PANEL_FIGURE = FIGURES_DIR / "phase16_tier1_candidate_panel.svg"
FIGURE_MANIFEST = TABLES_DIR / "manuscript_figure_manifest.tsv"
TABLE1_DATASETS = TABLES_DIR / "manuscript_table1_datasets.tsv"
TABLE2_SCORE_DEFINITIONS = TABLES_DIR / "manuscript_table2_score_definitions.tsv"
TABLE3_TOP_CANDIDATES = TABLES_DIR / "manuscript_table3_top_candidates.tsv"
TABLE4_CONTROLS = TABLES_DIR / "manuscript_table4_controls.tsv"
TABLE5_FLAGS = TABLES_DIR / "manuscript_table5_candidate_flags.tsv"
SUPPLEMENTARY_MANIFEST = TABLES_DIR / "supplementary_table_manifest.tsv"

ACTIVE_COMPONENTS = ["Surf", "E", "N", "R", "P", "T"]
COMPONENT_COLUMNS = {
    "Surf": "Surf_relative_confidence",
    "E": "E_rank_percentile",
    "N": "N_rank_percentile",
    "R": "R_rank_percentile_high_worse",
    "P": "P_rank_percentile",
    "T": "T_rank_percentile",
}
TIER_COLORS = {
    "Tier 1": "#2f7d4f",
    "Tier 2": "#2f6f9f",
    "Watchlist": "#c57b2a",
    "Excluded": "#7a7a7a",
    "not_in_top30": "#bbbbbb",
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
            writer.writerow({field: format_value(row.get(field, "")) for field in fieldnames})


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def format_value(value: object, digits: int = 6) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.{digits}f}"
    return str(value)


def float_or_nan(value: str) -> float:
    if value in {"", "NA", "nan", "None", None}:  # type: ignore[comparison-overlap]
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def int_or_none(value: str) -> int | None:
    if value in {"", "NA", None}:  # type: ignore[comparison-overlap]
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def publication_stage_text(value: str) -> str:
    replacements = {
        "Fase 1": "inventory",
        "Fase 2": "source acquisition",
        "Fase 3": "identifier normalization",
        "Fase 4B": "ranking-resolution simulation",
        "Fase 4": "surfaceome universe",
        "Fase 5": "tumor expression",
        "Fase 6": "normal selectivity and risk",
        "Fase 7": "protein evidence",
        "Fase 8": "TME specificity fallback",
        "Fase 9": "topology and isoforms",
        "Fase 10": "structure annotation",
        "Fase 11": "functional annotation",
        "Fase 12": "clinical/druggability annotation",
        "Fase 13": "integrated scoring",
        "Fase 14": "stability analysis",
        "Fase 15": "tiering and curation",
        "Fase 16": "figure/table packaging",
        "MVP": "primary",
        "mvp": "primary",
        "v2": "final",
        "v1": "pre-GPI",
        "v0": "pre-fix",
    }
    clean = value
    for old, new in replacements.items():
        clean = clean.replace(old, new)
    return clean


def shorten(text: str, width: int = 85) -> str:
    text = " ".join((text or "").split())
    return textwrap.shorten(text, width=width, placeholder="...")


def tier_counts(tier_rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {"Tier 1": 0, "Tier 2": 0, "Watchlist": 0}
    for row in tier_rows:
        if row.get("tier") in counts:
            counts[row["tier"]] += 1
    return counts


def source_overlap_from_note(note: str) -> int:
    match = re.search(r"(\d+)\s+overlap", note or "")
    return int(match.group(1)) if match else 0


def build_pipeline_overview(
    surfaceome_rows: list[dict[str, str]],
    protein_rows: list[dict[str, str]],
    ranking_rows: list[dict[str, str]],
    rank_stability_rows: list[dict[str, str]],
    tier_rows: list[dict[str, str]],
) -> None:
    categories = {
        row["label"]: int(float(row["n_genes"]))
        for row in surfaceome_rows
        if row.get("summary_type") == "category"
    }
    candidate_denominator = sum(categories.values())
    core_probable = categories.get("core_surfaceome", 0) + categories.get("probable_surfaceome", 0)
    hpa_rows = {row["evidence_layer"]: row for row in protein_rows}
    hpa_covered = int(float(hpa_rows["hpa_stomach_cancer_ihc"]["n_covered"]))
    top20_passing = sum(
        1
        for row in rank_stability_rows
        if int_or_none(row.get("baseline_rank_v2", "")) is not None
        and int(row["baseline_rank_v2"]) <= 20
        and row.get("tier1_stability_precheck_not_final_tier") == "passes_top20_frequency_only"
    )
    counts = tier_counts(tier_rows)
    steps = [
        ("HGNC protein-coding\ncandidate space", candidate_denominator),
        ("Core+Probable\nsurfaceome", core_probable),
        ("Scored\nfinal ranking", len(ranking_rows)),
        ("HPA stomach IHC\ncovered", hpa_covered),
        ("Stability analysis\n(top20 pass)", top20_passing),
        ("Coarse tiers\nT1/T2/W", f"{counts['Tier 1']}/{counts['Tier 2']}/{counts['Watchlist']}"),
    ]

    fig, ax = plt.subplots(figsize=(12.8, 3.5))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 3.5)
    ax.axis("off")
    for index, (label, count) in enumerate(steps):
        x = 0.25 + index * 2.05
        rect = Rectangle((x, 1.25), 1.65, 1.1, facecolor="#eef4f8", edgecolor="#2a4b5f", linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + 0.825, 1.96, label, ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(x + 0.825, 1.48, str(count), ha="center", va="center", fontsize=13, color="#16384b")
        if index < len(steps) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + 1.68, 1.8),
                    (x + 2.02, 1.8),
                    arrowstyle="-|>",
                    mutation_scale=12,
                    linewidth=1.2,
                    color="#4a4a4a",
                )
            )
    ax.text(
        0.25,
        0.55,
        "Manuscript package uses frozen outputs only: no score, weight, universe, ranking, or tier changes.",
        fontsize=9,
        color="#555555",
    )
    fig.savefig(PIPELINE_FIGURE, bbox_inches="tight")
    plt.close(fig)


def build_surfaceome_landscape(surfaceome_rows: list[dict[str, str]]) -> None:
    source_rows = [row for row in surfaceome_rows if row.get("summary_type") == "source"]
    source_rows.sort(key=lambda row: int(float(row["n_genes"])))
    labels = [row["label"] for row in source_rows]
    totals = np.array([float(row["n_genes"]) for row in source_rows])
    overlaps = np.array([source_overlap_from_note(row.get("notes", "")) for row in source_rows])
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.barh(y, totals, color="#d9e1e8", label="Source genes")
    ax.barh(y, overlaps, color="#3179a6", label="Overlap with Core+Probable")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Gene count")
    ax.set_title("Surfaceome Evidence Landscape")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", color="#eeeeee", linewidth=0.8)
    for yi, total, overlap in zip(y, totals, overlaps):
        ax.text(total + max(totals) * 0.01, yi, f"{int(overlap)}/{int(total)}", va="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(SURFACEOME_FIGURE)
    plt.close(fig)


def build_selectivity_map(
    tumor_rows: list[dict[str, str]],
    selectivity_rows: list[dict[str, str]],
    component_rows: list[dict[str, str]],
    tier_rows: list[dict[str, str]],
) -> None:
    selectivity_by_gene = by_key(selectivity_rows, "hgnc_symbol")
    component_by_gene = by_key(component_rows, "hgnc_symbol")
    tier_by_gene = by_key(tier_rows, "gene")

    background_x: list[float] = []
    background_y: list[float] = []
    highlighted: list[tuple[float, float, str, str]] = []
    for row in tumor_rows:
        gene = row.get("hgnc_symbol", "")
        selectivity = selectivity_by_gene.get(gene, {})
        median_tpm = float_or_nan(row.get("median_tpm_tumor", ""))
        log2fc = float_or_nan(selectivity.get("N_critical_log2fc", ""))
        if math.isnan(median_tpm) or math.isnan(log2fc):
            continue
        critical_tpm = median_tpm / (2.0**log2fc)
        x = math.log10(median_tpm + 0.1)
        y = math.log10(max(critical_tpm, 0.0) + 0.1)
        tier = tier_by_gene.get(gene, {}).get("tier", "not_in_top30")
        if tier == "not_in_top30":
            background_x.append(x)
            background_y.append(y)
        else:
            highlighted.append((x, y, gene, tier))

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.scatter(background_x, background_y, s=8, color="#d2d2d2", alpha=0.5, linewidth=0)
    for tier in ["Watchlist", "Tier 2", "Tier 1"]:
        points = [(x, y, gene) for x, y, gene, row_tier in highlighted if row_tier == tier]
        if not points:
            continue
        xs, ys, genes = zip(*points)
        ax.scatter(xs, ys, s=36 if tier == "Tier 1" else 24, color=TIER_COLORS[tier], label=tier, alpha=0.9)
        for x, y, gene in points:
            if tier == "Tier 1" or gene in {"ERBB2", "PECAM1", "LRRC15"}:
                ax.text(x + 0.025, y + 0.025, gene, fontsize=7)

    lim_min = min(ax.get_xlim()[0], ax.get_ylim()[0])
    lim_max = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([lim_min, lim_max], [lim_min, lim_max], color="#777777", linestyle="--", linewidth=1)
    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)
    ax.set_xlabel("Tumor median expression log10(TPM + 0.1)")
    ax.set_ylabel("Estimated max critical normal log10(TPM + 0.1)")
    ax.set_title("Tumor-Normal Selectivity Map")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(color="#eeeeee", linewidth=0.7)

    high_p = sum(1 for row in component_by_gene.values() if row.get("hpa_evidence_status") == "stomach_cancer_ihc_available")
    ax.text(0.02, 0.02, f"HPA stomach IHC available: {high_p} genes", transform=ax.transAxes, fontsize=8, color="#555555")
    fig.tight_layout()
    fig.savefig(SELECTIVITY_FIGURE)
    plt.close(fig)


def build_multilayer_heatmap(component_rows: list[dict[str, str]], tier_rows: list[dict[str, str]]) -> None:
    component_by_gene = by_key(component_rows, "hgnc_symbol")
    sorted_tiers = sorted(tier_rows, key=lambda row: int(row["rank_v2"]))
    matrix: list[list[float]] = []
    labels: list[str] = []
    for row in sorted_tiers:
        gene = row["gene"]
        comp = component_by_gene.get(gene, {})
        values = [float_or_nan(comp.get(COMPONENT_COLUMNS[component], "")) for component in ACTIVE_COMPONENTS]
        matrix.append(values)
        tier_short = {"Tier 1": "T1", "Tier 2": "T2", "Watchlist": "W"}.get(row["tier"], row["tier"])
        labels.append(f"{row['rank_v2']} {gene} ({tier_short})")

    data = np.array(matrix, dtype=float)
    masked = np.ma.masked_invalid(data)
    cmap = plt.cm.viridis.copy()
    cmap.set_bad("#eeeeee")
    fig, ax = plt.subplots(figsize=(7.6, 9.2))
    im = ax.imshow(masked, aspect="auto", vmin=0, vmax=1, cmap=cmap)
    ax.set_xticks(np.arange(len(ACTIVE_COMPONENTS)))
    ax.set_xticklabels(["Surf", "E", "N", "R\nhigh=worse", "P", "T"], fontsize=8)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_title("Top 30 Multi-Layer Component Landscape")
    for y_index, row in enumerate(sorted_tiers):
        ax.add_patch(
            Rectangle(
                (-0.75, y_index - 0.48),
                0.18,
                0.96,
                facecolor=TIER_COLORS[row["tier"]],
                edgecolor="none",
                clip_on=False,
            )
        )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    cbar.set_label("Rank percentile / scaled confidence", fontsize=8)
    fig.tight_layout()
    fig.savefig(HEATMAP_FIGURE)
    plt.close(fig)


def build_benchmark_controls(control_rows: list[dict[str, str]]) -> None:
    rows = [
        row
        for row in control_rows
        if row.get("control_set")
        in {"positive_control", "negative_control", "tme_or_off_tumor_penalty_control"}
    ]
    y = np.arange(len(rows))
    x_values = []
    colors = []
    labels = []
    for row in rows:
        rank = int_or_none(row.get("baseline_rank_v2", ""))
        x_values.append(rank if rank is not None else 2800)
        labels.append(row["hgnc_symbol"])
        control_set = row["control_set"]
        colors.append(
            {
                "positive_control": "#2f6f9f",
                "negative_control": "#777777",
                "tme_or_off_tumor_penalty_control": "#c57b2a",
            }.get(control_set, "#999999")
        )

    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    ax.scatter(x_values, y, s=42, c=colors)
    ax.axvspan(1, 50, color="#e8f3ea", alpha=0.8, label="top 50")
    ax.axvline(100, color="#999999", linestyle="--", linewidth=1, label="top 100")
    ax.set_xscale("log")
    ax.set_xlim(1, 3000)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Primary rank (log scale; lower is better)")
    ax.set_title("Benchmark and Control Behavior")
    ax.grid(axis="x", color="#eeeeee")
    for row_index, row in enumerate(rows):
        if not row.get("baseline_rank_v2"):
            ax.text(2820, row_index, "not in Core+Probable", va="center", fontsize=7, ha="right")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(BENCHMARK_FIGURE)
    plt.close(fig)


def build_tier1_panel(
    tier_rows: list[dict[str, str]],
    ranking_rows: list[dict[str, str]],
    wang_rows: list[dict[str, str]],
) -> None:
    ranking_by_gene = by_key(ranking_rows, "hgnc_symbol")
    wang_by_gene = by_key(wang_rows, "our_gene")
    tier1 = [row for row in tier_rows if row.get("tier") == "Tier 1"]
    tier1.sort(key=lambda row: int(row["rank_v2"]))
    table = []
    for row in tier1:
        gene = row["gene"]
        rank = ranking_by_gene.get(gene, {})
        wang = wang_by_gene.get(gene, {})
        table.append(
            [
                gene,
                row["rank_v2"],
                rank.get("scenario_score", ""),
                row.get("balanced_top20_freq", ""),
                wang.get("wang_class", "NA"),
                textwrap.fill(shorten(row.get("principal_caveat", ""), 72), width=36),
            ]
        )
    fig, ax = plt.subplots(figsize=(12.8, 4.8))
    ax.axis("off")
    ax.set_title("Tier 1 Candidate Summary (unordered within tier)", loc="left", fontsize=12, fontweight="bold")
    columns = ["Gene", "Rank", "Score", "Stability freq", "Wang class", "Main caveat"]
    mpl_table = ax.table(
        cellText=table,
        colLabels=columns,
        colWidths=[0.09, 0.06, 0.09, 0.10, 0.18, 0.48],
        loc="center",
        cellLoc="left",
        colLoc="left",
    )
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(8)
    mpl_table.scale(1, 2.1)
    for (row_index, col_index), cell in mpl_table.get_celld().items():
        cell.set_edgecolor("#dddddd")
        if row_index == 0:
            cell.set_facecolor("#e8f3ea")
            cell.set_text_props(weight="bold")
        elif col_index == 0:
            cell.set_text_props(weight="bold", color="#2f7d4f")
    fig.text(
        0.01,
        0.02,
        "Curation informs tier only; no score/rank/tier recalibration.",
        fontsize=8,
        color="#555555",
    )
    fig.savefig(TIER1_PANEL_FIGURE, bbox_inches="tight")
    plt.close(fig)


def build_table1_datasets(dataset_rows: list[dict[str, str]]) -> None:
    rows = []
    for row in dataset_rows:
        rows.append(
            {
                "source_id": row.get("source_id", ""),
                "source_name": row.get("source_name", ""),
                "primary_use": publication_stage_text(row.get("role", "")),
                "analysis_stage": publication_stage_text(row.get("phase", "")),
                "version_or_release": row.get("version_or_release", ""),
                "status": row.get("status", ""),
                "checksum_manifest": row.get("checksum_manifest", ""),
                "limitation_or_note": publication_stage_text(row.get("notes", "")),
            }
        )
    write_tsv(
        TABLE1_DATASETS,
        rows,
        [
            "source_id",
            "source_name",
            "primary_use",
            "analysis_stage",
            "version_or_release",
            "status",
            "checksum_manifest",
            "limitation_or_note",
        ],
    )


def build_table2_score_definitions(config: dict[str, object]) -> None:
    components = config["score_components"]  # type: ignore[index]
    weights = config["scenarios"]["balanced"]["weights"]  # type: ignore[index]
    sources = {
        "Surf": "surfaceome_universe.tsv",
        "E": "TCGA-STAD tumor_expression.tsv",
        "N": "selectivity_scores.tsv",
        "R": "off_tumor_risk.tsv",
        "P": "protein_evidence.tsv",
        "SC": "single_cell_specificity.tsv (not_available in primary score)",
        "T": "topology_isoforms_ecd.tsv",
    }
    limitations = {
        "Surf": "Membership confidence within admitted Core+Probable universe; not direct antigen density.",
        "E": "Bulk RNA; no malignant epithelial isolation.",
        "N": "TCGA/GTEx source effects remain explicit.",
        "R": "High-worse off-tumor risk is subtracted; risk form is sensitivity-tested.",
        "P": "HPA bulk IHC lacks antibody-level and patient-level membrane fields.",
        "SC": "No processed annotated gastric scRNA matrix admitted into the score; not counted in the primary score.",
        "T": "Topology/gene-level isoform annotations do not resolve CLDN18.2 or FGFR2b expression.",
    }
    rows = []
    for component in ["Surf", "E", "N", "R", "P", "SC", "T"]:
        rows.append(
            {
                "component": component,
                "definition": publication_stage_text(str(components[component])),  # type: ignore[index]
                "primary_weight": weights[component],  # type: ignore[index]
                "direction": "higher_worse_subtracted" if component == "R" else "higher_better",
                "primary_source": sources[component],
                "normalization": "rank_percentile_or_fixed_scale",
                "main_limitation": limitations[component],
            }
        )
    write_tsv(
        TABLE2_SCORE_DEFINITIONS,
        rows,
        ["component", "definition", "primary_weight", "direction", "primary_source", "normalization", "main_limitation"],
    )


def build_table3_top_candidates(
    tier_rows: list[dict[str, str]],
    ranking_rows: list[dict[str, str]],
    component_rows: list[dict[str, str]],
    wang_rows: list[dict[str, str]],
) -> None:
    ranking_by_gene = by_key(ranking_rows, "hgnc_symbol")
    component_by_gene = by_key(component_rows, "hgnc_symbol")
    wang_by_gene = by_key(wang_rows, "our_gene")
    rows = []
    for tier in ["Tier 1", "Tier 2"]:
        for tier_row in sorted([row for row in tier_rows if row.get("tier") == tier], key=lambda row: int(row["rank_v2"])):
            gene = tier_row["gene"]
            rank = ranking_by_gene.get(gene, {})
            comp = component_by_gene.get(gene, {})
            wang = wang_by_gene.get(gene, {})
            rows.append(
                {
                    "rank": tier_row.get("rank_v2", ""),
                    "gene": gene,
                    "tier": tier,
                    "primary_score": rank.get("scenario_score", ""),
                    "prevalence_flag": tier_row.get("prevalence_flag", ""),
                    "primary_top20_freq": tier_row.get("balanced_top20_freq", ""),
                    "Surf": comp.get("Surf_relative_confidence", ""),
                    "E": comp.get("E_rank_percentile", ""),
                    "N": comp.get("N_rank_percentile", ""),
                    "R_high_worse": comp.get("R_rank_percentile_high_worse", ""),
                    "P": comp.get("P_rank_percentile", ""),
                    "T": comp.get("T_rank_percentile", ""),
                    "wang_class": wang.get("wang_class", "NA"),
                    "wang_glyco_outlier_rank": wang.get("wang_glyco_outlier_rank", "NA"),
                    "principal_caveat": tier_row.get("principal_caveat", ""),
                }
            )
    write_tsv(
        TABLE3_TOP_CANDIDATES,
        rows,
        [
            "rank",
            "gene",
            "tier",
            "primary_score",
            "prevalence_flag",
            "primary_top20_freq",
            "Surf",
            "E",
            "N",
            "R_high_worse",
            "P",
            "T",
            "wang_class",
            "wang_glyco_outlier_rank",
            "principal_caveat",
        ],
    )


def build_table4_controls(control_rows: list[dict[str, str]]) -> None:
    rows = []
    for row in control_rows:
        rows.append(
            {
                "control_set": row.get("control_set", ""),
                "gene": row.get("hgnc_symbol", ""),
                "expected": row.get("expected", ""),
                "presence_status": row.get("presence_status", ""),
                "baseline_rank": row.get("baseline_rank_v2", ""),
                "top20_frequency": row.get("balanced_weight_perturb_top20_frequency", ""),
                "top50_frequency": row.get("all_weight_perturb_top50_frequency", ""),
                "leave_one_layer_rank_range": row.get("leave_one_layer_rank_range", ""),
                "interpretation": row.get("analysis_status", ""),
            }
        )
    write_tsv(
        TABLE4_CONTROLS,
        rows,
        [
            "control_set",
            "gene",
            "expected",
            "presence_status",
            "baseline_rank",
            "top20_frequency",
            "top50_frequency",
            "leave_one_layer_rank_range",
            "interpretation",
        ],
    )


def build_table5_flags(
    tier_rows: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
    component_rows: list[dict[str, str]],
) -> None:
    audit_by_gene = by_key(audit_rows, "hgnc_symbol")
    component_by_gene = by_key(component_rows, "hgnc_symbol")
    rows = []
    for tier_row in sorted(tier_rows, key=lambda row: int(row["rank_v2"])):
        gene = tier_row["gene"]
        audit = audit_by_gene.get(gene, {})
        comp = component_by_gene.get(gene, {})
        rows.append(
            {
                "rank": tier_row.get("rank_v2", ""),
                "gene": gene,
                "tier": tier_row.get("tier", ""),
                "automatic_audit_flags": audit.get("automatic_audit_flags", ""),
                "tme_contamination_risk": comp.get("tme_contamination_risk", ""),
                "risk_interpretation": comp.get("risk_interpretation", ""),
                "max_risk_organ": comp.get("max_risk_organ", ""),
                "accessibility_class": comp.get("accessibility_class", ""),
                "hpa_evidence_status": comp.get("hpa_evidence_status", ""),
                "discordance_flags": comp.get("discordance_flags", ""),
                "missing_primary_score_components": comp.get("missing_mvp_score_components", ""),
                "isoform_resolution_status": comp.get("isoform_resolution_status", ""),
                "principal_caveat": tier_row.get("principal_caveat", ""),
            }
        )
    write_tsv(
        TABLE5_FLAGS,
        rows,
        [
            "rank",
            "gene",
            "tier",
            "automatic_audit_flags",
            "tme_contamination_risk",
            "risk_interpretation",
            "max_risk_organ",
            "accessibility_class",
            "hpa_evidence_status",
            "discordance_flags",
            "missing_primary_score_components",
            "isoform_resolution_status",
            "principal_caveat",
        ],
    )


def build_manifests() -> None:
    figure_rows = [
        ("F1", "Pipeline overview with counts", PIPELINE_FIGURE, "new_phase16"),
        ("F2", "Surfaceome evidence landscape", SURFACEOME_FIGURE, "new_phase16"),
        ("F3", "Tumor-normal selectivity map", SELECTIVITY_FIGURE, "new_phase16"),
        ("F4", "Top30 multi-layer heatmap", HEATMAP_FIGURE, "new_phase16"),
        ("F5", "TME specificity fallback dotplot", FIGURES_DIR / "top_candidates_scRNA_dotplot.svg", "existing_tme_fallback"),
        ("F6a", "Rank stability heatmap", FIGURES_DIR / "rank_stability_heatmap.svg", "existing_stability_analysis"),
        ("F6b", "Weighting-sensitivity bumpchart", FIGURES_DIR / "bumpchart_scenarios.svg", "existing_stability_analysis"),
        ("F7", "Benchmark controls", BENCHMARK_FIGURE, "new_phase16"),
        ("F8", "Tier 1 candidate panel", TIER1_PANEL_FIGURE, "new_phase16"),
    ]
    write_tsv(
        FIGURE_MANIFEST,
        [
            {
                "figure_id": figure_id,
                "title": title,
                "path": rel(path),
                "status": status,
                "exists": path.exists(),
            }
            for figure_id, title, path, status in figure_rows
        ],
        ["figure_id", "title", "path", "status", "exists"],
    )

    supplements = [
        ("S1", "Full surfaceome universe", SURFACEOME_UNIVERSE, "available"),
        ("S2", "All component scores", COMPONENT_SCORES, "available"),
        ("S3", "Scenario rankings", RESULTS_DIR / "rankings", "available_directory"),
        ("S4", "Complete stability and sensitivity outputs", VALIDATION_DIR / "rank_stability.tsv", "available"),
        ("S5", "Tissue mapping", REPO_ROOT / "config" / "tissue_mappings.yaml", "available"),
        ("S6", "Manual curation notes", TABLES_DIR / "manual_curation_notes.tsv", "available"),
        ("S7", "Excluded candidates with reason", TABLES_DIR / "excluded_with_reason.tsv", "available"),
        ("S8", "PCA/PERMANOVA batch diagnostic", TABLES_DIR / "batch_permanova.tsv", "available"),
        ("S9", "Surfaceome overlap/Jaccard", TABLES_DIR / "surfaceome_jaccard_with_published_lists.tsv", "available"),
        ("S10", "Tumor-normal power analysis", TABLES_DIR / "tumor_normal_power_analysis.tsv", "available"),
        ("S11", "Score functional-form sensitivity", VALIDATION_DIR / "functional_form_sensitivity.tsv", "available"),
        ("S12", "TME marker-correlation flags", TABLES_DIR / "tme_contamination_flags.tsv", "available"),
        ("S13", "Subtype feasibility and power", TABLES_DIR / "subtype_power_analysis.tsv", "available"),
        ("S14", "Rank resolution simulation", VALIDATION_DIR / "ranking_resolution_simulation.tsv", "available"),
        ("S15", "Risk functional-form sensitivity", VALIDATION_DIR / "risk_functional_form_sensitivity.tsv", "available"),
        ("S16", "Wang 2026 cross-check", WANG_CROSSCHECK, "available"),
        ("S17", "Wang 2026 overlap enrichment", WANG_OVERLAP_ENRICHMENT, "available"),
        ("S18", "Wang 2026 matched-null sensitivity", WANG_MATCHED_NULL, "available"),
        ("S19", "GPI correction impact summary", GPI_CORRECTION_IMPACT, "available"),
        ("S20", "GPI rank delta", GPI_RANK_DELTA, "available"),
        ("S21", "External surfaceome baseline comparison", EXTERNAL_BASELINE_COMPARISON, "available"),
        ("S22", "Candidate-level TISCH2 scRNA compartment check", CANDIDATE_SCRNA_TISCH2, "available"),
        ("S23", "Surfaceome source-dependency audit", SURFACEOME_SOURCE_DEPENDENCY_AUDIT, "available"),
        ("S24", "Surfaceome source-dependency summary", SURFACEOME_SOURCE_DEPENDENCY_SUMMARY, "available"),
    ]
    write_tsv(
        SUPPLEMENTARY_MANIFEST,
        [
            {
                "supplement_id": supplement_id,
                "title": title,
                "path": rel(path) if path.is_file() or path.is_dir() else rel(path),
                "status": status,
                "exists": path.exists(),
            }
            for supplement_id, title, path, status in supplements
        ],
        ["supplement_id", "title", "path", "status", "exists"],
    )


def build_note(
    ranking_rows: list[dict[str, str]],
    tier_rows: list[dict[str, str]],
    wang_rows: list[dict[str, str]],
) -> None:
    counts = tier_counts(tier_rows)
    tier12_wang = [row for row in wang_rows if row.get("our_tier") in {"Tier 1", "Tier 2"}]
    wang_overlap = sum(1 for row in tier12_wang if row.get("in_wang_drug_target_table") == "yes")
    tier1_genes = ", ".join(row["gene"] for row in tier_rows if row.get("tier") == "Tier 1")
    lines = [
        "# Fase 16: Figures and Tables",
        "",
        "Date: 2026-05-31",
        "",
        "## Status and scope",
        "",
        "Fase 16 packages manuscript-ready figures and tables from frozen Fase 13-15 artifacts.",
        "It does not change scores, weights, universe membership, ranking, or tier assignments.",
        "",
        "Inputs remain anchored on `results/rankings/ranking_v2_frozen.tsv` "
        f"(SHA256 `{sha256_file(RANKING_V2)[:12]}...`) and Fase 15 coarse tiers.",
        "",
        "## Main results packaged",
        "",
        f"- Ranking rows packaged: {len(ranking_rows)}.",
        f"- Coarse tier distribution: Tier 1={counts['Tier 1']}, Tier 2={counts['Tier 2']}, Watchlist={counts['Watchlist']}.",
        f"- Tier 1 set: {tier1_genes}.",
        f"- Wang 2026 concordance carried forward: {wang_overlap}/{len(tier12_wang)} Tier 1+Tier 2 in Wang drug-target table; Fase 17 adds simple enrichment and matched-null sensitivity audits.",
        "",
        "## New Fase 16 figures",
        "",
        f"- `{rel(PIPELINE_FIGURE)}`",
        f"- `{rel(SURFACEOME_FIGURE)}`",
        f"- `{rel(SELECTIVITY_FIGURE)}`",
        f"- `{rel(HEATMAP_FIGURE)}`",
        f"- `{rel(BENCHMARK_FIGURE)}`",
        f"- `{rel(TIER1_PANEL_FIGURE)}`",
        "",
        "Existing Fase 8/Fase 14 figures remain part of the manuscript figure manifest where appropriate.",
        "",
        "## Main manuscript tables",
        "",
        f"- Table 1: `{rel(TABLE1_DATASETS)}`",
        f"- Table 2: `{rel(TABLE2_SCORE_DEFINITIONS)}`",
        f"- Table 3: `{rel(TABLE3_TOP_CANDIDATES)}`",
        f"- Table 4: `{rel(TABLE4_CONTROLS)}`",
        f"- Table 5: `{rel(TABLE5_FLAGS)}`",
        "",
        "## Manifests",
        "",
        f"- Figure manifest: `{rel(FIGURE_MANIFEST)}`",
        f"- Supplementary table manifest: `{rel(SUPPLEMENTARY_MANIFEST)}`",
        "",
        "## Interpretation guardrails",
        "",
        "- Tiers are coarse and unordered within tier.",
        "- `SC` remains not available in the primary score; TME interpretation relies on bulk marker/purity diagnostics plus curation.",
        "- Wang 2026 is used as external consistency and compartment-framework context, not as proof of first discovery or independent ranking validation.",
        "- Figure 7H does not directly resolve NECTIN2/PECAM1/LRRC15 per-gene compartments.",
        "- Candidate outputs remain hypothesis-generating and require experimental validation.",
        "",
        "## Decision",
        "",
        "Fase 16 complete. Proceed to Fase 17 manuscript drafting with these packaged figures/tables and the stated limitations.",
        "",
    ]
    PHASE16_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    surfaceome_rows = read_tsv(SURFACEOME_SUMMARY)
    protein_rows = read_tsv(PROTEIN_COVERAGE)
    ranking_rows = read_tsv(RANKING_V2)
    component_rows = read_tsv(COMPONENT_SCORES)
    tier_rows = read_tsv(TIER_ASSIGNMENTS)
    rank_stability_rows = read_tsv(RANK_STABILITY)
    tumor_rows = read_tsv(TUMOR_EXPRESSION)
    selectivity_rows = read_tsv(SELECTIVITY_SCORES)
    dataset_rows = read_tsv(DATASET_INVENTORY)
    control_rows = read_tsv(CONTROL_BENCHMARK)
    audit_rows = read_tsv(TOP30_AUDIT)
    wang_rows = read_tsv(WANG_CROSSCHECK)
    scoring_config = load_yaml(SCORING_CONFIG)

    build_pipeline_overview(surfaceome_rows, protein_rows, ranking_rows, rank_stability_rows, tier_rows)
    build_surfaceome_landscape(surfaceome_rows)
    build_selectivity_map(tumor_rows, selectivity_rows, component_rows, tier_rows)
    build_multilayer_heatmap(component_rows, tier_rows)
    build_benchmark_controls(control_rows)
    build_tier1_panel(tier_rows, ranking_rows, wang_rows)

    build_table1_datasets(dataset_rows)
    build_table2_score_definitions(scoring_config)
    build_table3_top_candidates(tier_rows, ranking_rows, component_rows, wang_rows)
    build_table4_controls(control_rows)
    build_table5_flags(tier_rows, audit_rows, component_rows)
    build_manifests()
    build_note(ranking_rows, tier_rows, wang_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
