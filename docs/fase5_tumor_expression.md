# Fase 5 Tumor Expression

Access date: 2026-06-01

Fase 5 computes the tumor-expression component for the Fase 4 Core+Probable surfaceome universe using Xena/Toil TCGA-STAD primary tumor RNA. Xena values are stored as `log2(TPM + 0.001)`; they were transformed back to TPM as `2^x - 0.001` and clipped at zero.

## Scope

- Candidate universe: 2704 Core+Probable genes.
- Genes with measured Xena expression: 2696.
- Genes missing Xena expression: 8.
- Duplicate Xena Ensembl-base rows skipped after first match: 0.

## E Score

The preregistered tumor-expression score is:

`E_raw = 0.40 * rank(median_TPM_tumor) + 0.30 * rank(percent_samples_TPM_gt_1) + 0.20 * rank(P75_TPM_tumor) + 0.10 * rank(P90_TPM_tumor)`

Ranks are percentile ranks among measured Core+Probable genes; higher expression and prevalence produce higher values. `E_score` is a component score only, not a final target ranking.

## Subtype Counts

- STAD_EBV: n=30 (quantitative_claim_allowed)
- STAD_MSI: n=73 (quantitative_and_tier1_subtype_context_allowed)
- STAD_GS: n=50 (quantitative_and_tier1_subtype_context_allowed)
- STAD_CIN: n=221 (quantitative_and_tier1_subtype_context_allowed)
- STAD_POLE: n=7 (insufficient_n)
- unassigned: n=33 (quantitative_claim_allowed)

## Subtype Power

The subtype power simulation is an approximate two-group log2-expression model with 10% non-null genes and BH-FDR 0.05 across the measured Core+Probable universe.

- STAD_EBV: min standardized shift 0.750000 (target_power_reached)
- STAD_MSI: min standardized shift 0.500000 (target_power_reached)
- STAD_GS: min standardized shift 0.750000 (target_power_reached)
- STAD_CIN: min standardized shift 0.500000 (target_power_reached)
- STAD_POLE: min standardized shift 1.500000 (target_power_reached)
- unassigned: min standardized shift 0.750000 (target_power_reached)

## Covariate Availability

- TCGA molecular subtype: available -> used_for_subtype_expression_and_power_analysis
- Lauren subtype: not_available_as_exact_field -> not_used_for_quantitative_lauren_claims
- Histology proxy: available_proxy_only -> counted_but_not_treated_as_lauren
- AJCC pathologic stage: available -> included_in_clinical_covariate_expression_table
- Anatomic tissue origin: available -> included_in_clinical_covariate_expression_table
- Tumor purity: not_available_in_current_raw_sources -> not_purity_adjusted_in_fase5
- Copy-number amplification: available_for_selected_targets -> computed_for_ERBB2_FGFR2_MET

Stage and anatomic-origin expression summaries are included because the fields were available. Exact Lauren subtype and tumor purity were not available in the current raw sources and are not silently imputed. Histology proxy counts are retained only as a limitation/audit item and must not be described as Lauren subtype.

## Amplification Context

cBioPortal GISTIC calls were queried for ERBB2, FGFR2, and MET to support amplified-target context.

- ERBB2: high amp 54/409, status=computed
- FGFR2: high amp 18/409, status=computed
- MET: high amp 12/409, status=computed

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
