# Fase 2 Xena/Toil Batch Diagnostic

Access date: 2026-05-28

This diagnostic uses the downloaded Xena/Toil `TcgaTargetGtex_rsem_gene_tpm.gz` matrix and phenotype file. The matrix was restricted to TCGA-STAD primary tumor, TCGA-STAD adjacent normal, and GTEx stomach normal samples, then PCA and PERMANOVA were run on the top variable genes.

## Sample Counts

- GTEx stomach normal: 175
- TCGA-STAD adjacent normal: 36
- TCGA-STAD primary tumor: 414

## PCA

- Output: `results/figures/pca_batch_diagnostic.svg`
- PC1 variance: 17.86%
- PC2 variance: 5.02%

## PERMANOVA

| Test | Grouping | Samples | Groups | R2 | pseudo-F | p-value | Interpretation |
|---|---|---:|---:|---:|---:|---:|---|
| study_all_samples | study | 625 | 2 | 0.1613 | 119.8422 | 0.0010 | Confounded with tumor/normal biology because GTEx contributes only normal tissue. |
| sample_group_all_samples | analysis_group | 625 | 3 | 0.1750 | 65.9595 | 0.0010 | Describes combined biology and source structure; not a pure batch test. |
| normal_source_only | normal_source | 211 | 2 | 0.0896 | 20.5816 | 0.0010 | Most relevant source diagnostic: TCGA adjacent normal versus GTEx stomach normal. |

## Gate Decision

Fase 2 batch diagnostic outputs now exist. The diagnostic is not a permission to ignore source effects: Fase 5 must keep TCGA/GTEx source labels in the analysis notes, and GDC adjacent-normal sensitivity remains required before strong tumor-normal selectivity claims.
