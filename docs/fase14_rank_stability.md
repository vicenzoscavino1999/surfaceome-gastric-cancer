# Fase 14 Rank Stability

Date: 2026-05-31

Fase 14 was run on the frozen Fase 13 v2 preliminary ranking, `results/rankings/ranking_v2_frozen.tsv`. It does not create final biological tiers and does not change Fase 13 scores or weights.

## Inputs

- Ranking SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`
- Component table SHA256: `6e6c6c1034540533fb6aae86f94aeff096fa52abd89cd5f728c4d589f2fc6992`
- Scoring config SHA256: `227d95ac3448af4b00edffbe8281c5c6b481dbd16eaaa92576f3633b21905560`
- Preflight: `docs/fase14_preflight.md`
- Baseline top20: `ITGB4;HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1;CDH3;MPZL1;ITGB5;NECTIN2;BST2;IFNGR1;CEACAM5;JAG1;EPCAM;PECAM1;ALPG;IL2RG;DSC2;TNFRSF11A;ERBB2`

## Summary

- Weight perturbations passing both preregistered gates: 231/250.
- Minimum / median perturbation Spearman vs v2: `0.910703` / `0.983898`.
- Minimum top20 retention under weight perturbation: `0.600000`.
- Most disruptive leave-one-layer-out by top20 retention: `leave_one_T` with retention `0.350000`.
- Baseline top20 genes passing the predeclared >=40% Balanced-perturbation top20-frequency precheck: 19/20.
- Post-scoring resolution top20 genes with 95% rank interval contained in top40: 1/20 (`coarse_tiering_recommended`).
- Top30 automated false-positive audit rows with at least one flag: 25/30.

## Scenario Stability

- `scenario_balanced`: Spearman `1.000000`, top20 retention `1.000000`
- `scenario_safety_first`: Spearman `0.949569`, top20 retention `0.800000`
- `scenario_adc_focused`: Spearman `0.983944`, top20 retention `0.900000`
- `scenario_novelty_focused`: Spearman `0.995443`, top20 retention `0.950000`
- `scenario_protein_first`: Spearman `0.976419`, top20 retention `0.800000`

## Leave-One-Layer-Out

- `Surf` omitted: Spearman `0.986108`, top20 retention `0.800000`
- `E` omitted: Spearman `0.844554`, top20 retention `0.550000`
- `N` omitted: Spearman `0.870636`, top20 retention `0.750000`
- `R` omitted: Spearman `0.882534`, top20 retention `0.450000`
- `P` omitted: Spearman `0.947432`, top20 retention `0.650000`
- `T` omitted: Spearman `0.968739`, top20 retention `0.350000`

## Risk Sensitivity

- `R_max`: risk_functional_form, Spearman `1.000000`, top20 retention `1.000000`
- `R_max_plus_breadth`: risk_functional_form, Spearman `0.987858`, top20 retention `0.950000`
- `R_sum_capped`: risk_functional_form, Spearman `0.943298`, top20 retention `0.550000`
- `p50_p75`: risk_threshold, Spearman `1.000000`, top20 retention `1.000000`
- `p60_p80`: risk_threshold, Spearman `0.988308`, top20 retention `0.600000`
- `absolute_tpm_1_5`: risk_threshold, Spearman `0.978242`, top20 retention `0.550000`

## Missing Data Sensitivity

- `exclude_and_renormalize`: Spearman `1.000000`, top20 retention `1.000000`
- `p25`: Spearman `0.993180`, top20 retention `0.800000`
- `p50`: Spearman `0.984845`, top20 retention `0.800000`
- `p75`: Spearman `0.945973`, top20 retention `0.800000`

## Control Benchmark

Controls are audited in `results/validation/control_benchmark.tsv`. The Fase 13 aggregate positive-control top50 gate remains reported as failed, while the cause-corrected gate remains the relevant technical-failure diagnostic.

## False-Positive Audit

`results/validation/top30_false_positive_audit.tsv` is an automated flag audit for the top30. It is not manual biological curation; Fase 15 must review these candidates before final tier assignment.

## Decision

Current Fase 14 decision: `fase15_allowed_with_coarse_tier_language_and_explicit_stability_limits`.

This decision only authorizes candidate-level curation/tiering work. It is not a final target ranking claim.

## Outputs

- `results/validation/rank_stability.tsv`
- `results/validation/leave_one_layer_out.tsv`
- `results/validation/weight_perturbation_summary.tsv`
- `results/validation/risk_threshold_sensitivity.tsv`
- `results/validation/risk_functional_form_sensitivity.tsv`
- `results/validation/organ_weight_perturbation.tsv`
- `results/validation/ranking_resolution_post_scoring.tsv`
- `results/validation/ranking_resolution_post_scoring_summary.tsv`
- `results/validation/missing_data_sensitivity.tsv`
- `results/validation/control_benchmark.tsv`
- `results/validation/top30_false_positive_audit.tsv`
- `results/figures/rank_stability_heatmap.svg`
- `results/figures/bumpchart_scenarios.svg`
