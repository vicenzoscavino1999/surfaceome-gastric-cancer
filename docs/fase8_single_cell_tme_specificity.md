# Fase 8 Single-Cell/TME Specificity

Access date: 2026-06-01

Fase 8 was executed as the preregistered MVP fallback. No processed gastric scRNA dataset with reliable malignant epithelial versus TME annotations was admitted into the quantitative score, so `SC` is `not_available` and was not imputed.

TISCH2/GEO remain candidate sources for a later incremental scRNA layer. This run only uses TCGA-STAD primary tumor bulk RNA to flag possible TME-derived signal.

## Bulk TME Fallback

TCGA-STAD primary tumors: 414.

Candidate genes assessed: 2704.

TME marker modules:

- caf_fibroblast: 6/6 markers available (FAP;ACTA2;COL1A1;COL1A2;DCN;LUM)
- endothelial: 5/5 markers available (PECAM1;VWF;CDH5;ENG;ERG)
- myeloid_macrophage: 5/5 markers available (CD68;CD163;CSF1R;ITGAM;LYZ)
- t_cell: 4/5 markers available (CD3D;CD3E;CD8A;CD4)
- b_plasma: 5/5 markers available (CD19;MS4A1;SDC1;MZB1;JCHAIN)

For each Core+Probable candidate, Spearman correlation was computed between its bulk tumor expression and each TME module score. These are flags only, not filters and not final ranking components.

## ESTIMATE-Based Purity Adjustment

Control B is implemented with the ESTIMATE stromal and immune signatures from `tidyestimate` 1.1.1. The Xena/Toil TCGA-STAD RNA-seq matrix is used to compute sample-level stromal, immune, and ESTIMATE scores. The ESTIMATE-derived value is used as a relative purity covariate for partial Spearman correlations; it is not interpreted as an absolute pathologist purity measurement.

Expression genes used for ESTIMATE scoring: 19080.

Available ESTIMATE stromal signature genes: 141/141.

Available ESTIMATE immune signature genes: 141/141.

## ESTIMATE/TME Collinearity

ESTIMATE and the TME modules are not independent measurements. ESTIMATE is built from stromal and immune signatures, while the module scores also represent stromal, endothelial, myeloid, T-cell, and B/plasma biology. Partial Spearman correlations are therefore module-dependent flags; they should not be interpreted as a clean causal decomposition of epithelial versus TME expression.

Direct marker overlap with ESTIMATE signatures:

- caf_fibroblast: stromal 4/6 (COL1A2;DCN;FAP;LUM); immune 0/6 (none)
- endothelial: stromal 2/5 (CDH5;ERG); immune 0/5 (none)
- myeloid_macrophage: stromal 3/5 (CD163;CSF1R;ITGAM); immune 1/5 (LYZ)
- t_cell: stromal 0/5 (none); immune 1/5 (CD3D)
- b_plasma: stromal 0/5 (none); immune 0/5 (none)

This overlap is an audit item, not an exclusion criterion. Low direct marker overlap does not remove broader biological collinearity, and high direct overlap does not make the module unusable; it changes how conservatively the adjusted flag should be interpreted.

## Risk Summary

- high_known_tme_marker_control: 2
- high_purity_adjusted_tme_correlation: 744
- low_uncorrected_tme_correlation: 1549
- moderate_purity_confounded: 8
- moderate_residual_tme_correlation: 152
- not_assessable_missing_bulk_expression: 8
- watchlist_uncorrected_tme_correlation: 241

Cellular labels:

- ambiguous: 1145
- immune/TME-derived: 2
- not covered: 1557

Known TME/off-tumor controls carried from preregistered controls: PECAM1;PTPRC.

## Purity Adjustment

The file `results/tables/tme_purity_adjusted_correlations.tsv` stores the raw module correlation, partial Spearman correlation, and final TME flag after controlling for the ESTIMATE RNA-seq relative purity/admixture covariate. `moderate_purity_confounded` means `rho_raw > 0.5` but `rho_partial < 0.2`.

The file `results/tables/tme_purity_suppression_audit.tsv` stores genes that moved from `low_uncorrected_tme_correlation` to `high_purity_adjusted_tme_correlation`. These are potential suppression patterns where purity/admixture adjustment increased the TME correlation. Count in this run: 92.

Distribution of low-to-high transitions by strongest adjusted module:

- b_plasma: 2
- caf_fibroblast: 4
- endothelial: 17
- myeloid_macrophage: 69

Top low-to-high adjusted examples by partial rho:

- F11R: myeloid_macrophage, raw rho=0.215818, partial rho=0.563956, delta=0.348137
- LRRC8B: myeloid_macrophage, raw rho=0.318032, partial rho=0.544440, delta=0.226408
- TMEM63B: myeloid_macrophage, raw rho=0.097831, partial rho=0.541412, delta=0.443581
- DAG1: myeloid_macrophage, raw rho=0.325960, partial rho=0.528973, delta=0.203013
- CDH1: myeloid_macrophage, raw rho=0.055369, partial rho=0.509083, delta=0.453713
- SLC31A1: myeloid_macrophage, raw rho=0.229285, partial rho=0.507835, delta=0.278550
- OCLN: myeloid_macrophage, raw rho=0.094119, partial rho=0.504968, delta=0.410850
- ZDHHC5: myeloid_macrophage, raw rho=0.234109, partial rho=0.496196, delta=0.262086
- ADAM10: myeloid_macrophage, raw rho=0.346853, partial rho=0.493795, delta=0.146942
- SERINC3: myeloid_macrophage, raw rho=0.302100, partial rho=0.493397, delta=0.191297

Sentinel low-to-high examples for manual review:

- F11R: myeloid_macrophage, raw rho=0.215818, partial rho=0.563956
- DAG1: myeloid_macrophage, raw rho=0.325960, partial rho=0.528973
- CDH1: myeloid_macrophage, raw rho=0.055369, partial rho=0.509083
- OCLN: myeloid_macrophage, raw rho=0.094119, partial rho=0.504968
- CD46: myeloid_macrophage, raw rho=0.127648, partial rho=0.483974
- ADAM10: myeloid_macrophage, raw rho=0.346853, partial rho=0.493795
- PTK7: caf_fibroblast, raw rho=0.261817, partial rho=0.479038
- CGN: myeloid_macrophage, raw rho=0.041391, partial rho=0.481274

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
