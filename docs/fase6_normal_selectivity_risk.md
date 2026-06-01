# Fase 6 Normal Selectivity And Off-Tumor Risk

Access date: 2026-06-01

Fase 6 estimates tumor-normal selectivity (`N`) and organ-specific on-target/off-tumor risk (`R`) for the Fase 4 Core+Probable surfaceome universe. Xena/Toil values are transformed from `log2(TPM+0.001)` back to TPM before summary statistics. HPA RNA `nTPM` is used conservatively where mapped by `config/tissue_mappings.yaml`, especially for tissue classes not directly represented in Xena.

## Sample Counts

- gtex_stomach_normal: n=175
- tcga_stad_adjacent_normal: n=36
- tcga_stad_primary_tumor: n=414

## Scope

- Candidate universe: 2704 Core+Probable genes.
- Genes with measured tumor/normal Xena expression: 2696.
- Genes meeting the preregistered GTEx stomach statistical rule (`log2FC >= 1` and BH-FDR < 0.05): 757.
- Genes with high critical off-tumor risk by current `R_max`: 1825.

## Selectivity

`N_stomach` compares TCGA-STAD primary tumor median TPM against GTEx stomach median TPM. `N_critical` compares tumor median TPM against the maximum mapped critical normal expression across Xena/HPA sources. `N_score` is a component score only:

`0.50*rank(N_critical_log2fc) + 0.30*rank(N_stomach_log2fc) + 0.20*N_stat_gtex`

The intra-TCGA adjacent-normal comparison is reported as a sensitivity test. It is not treated as a full replacement for GTEx stomach because adjacent normals have smaller sample size.

## Power

- tumor_vs_gtex_stomach: standardized shift 0.500000 (approx log2 shift 0.939496)
- tumor_vs_tcga_adjacent: standardized shift 0.750000 (approx log2 shift 1.284625)

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
