# Fase 13 MVP Score Integration

## Status

Fase 13 generated preliminary MVP integrated score version `v2` after the Fase 4 GPI evidence correction, not final biological tiers. The primary score uses six quantitative components: `Surf`, `E`, `N`, `R`, `P`, and `T`. `SC` remains `not_available` from Fase 8 and is not imputed.

Fase 10 structure and Fase 11 functional evidence remain deferred candidate-card layers. Fase 12 clinical/druggability curation is deferred to top preliminary candidates before final tiering. This scope is registered in `docs/limitations_register.md`.

## Inputs

- Candidate universe: 2704 Core+Probable genes.
- Scoring config SHA256: `227d95ac3448af4b00edffbe8281c5c6b481dbd16eaaa92576f3633b21905560`.
- Git commit at scoring: `6b4346e850b08f041c8e6c46b97a7396a3bba25d`.
- Worktree status at scoring: `dirty`.
- Missing-data policy: `exclude_and_renormalize`.
- Risk direction: `R` is higher-worse and is subtracted from the score.
- `Surf` scaling: `Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`, using the theoretical admitted Fase 4 confidence range `[5,10]` after confirmed UniProt GPI-anchor evidence was added.
- Fase 13 internal percentile ranks use average-rank ties; this prevents HGNC lexicographic order from changing tied `R` values.

## Missing Data

- `E;N;R;P`: 8
- `P`: 906
- `none`: 1790

`SC` is not counted as missing for MVP tiering prechecks because it is outside the six-component strict MVP score.

## Scenario Rule

`Balanced` is the primary preliminary ranking. `Safety-first`, `ADC-focused`, `Novelty-focused`, and `Protein-first` are sensitivity rankings and must not be cherry-picked as alternative final answers.

- `safety_first` top20 overlap with Balanced: 16/20
- `adc_focused` top20 overlap with Balanced: 18/20
- `novelty_focused` top20 overlap with Balanced: 19/20
- `protein_first` top20 overlap with Balanced: 16/20

Top 20 `Balanced` symbols:

`ITGB4;HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1;CDH3;MPZL1;ITGB5;NECTIN2;BST2;IFNGR1;CEACAM5;JAG1;EPCAM;PECAM1;ALPG;IL2RG;DSC2;TNFRSF11A;ERBB2`

## Functional Form Sensitivity

- `weighted_rank_sum`: Spearman=1.000000, top20 Jaccard=1.000000
- `geometric_mean_percentile`: Spearman=0.898705, top20 Jaccard=0.600000
- `weighted_rank_sum_with_veto_p20`: Spearman=0.927228, top20 Jaccard=1.000000

## Sanity Checks

- Positive controls in top 50 Balanced: 4/8 (`ERBB2;EPCAM;CEACAM5;MET`).
- Negative controls in top 100 Balanced: 0 (`none`).
- Top 20 Balanced with missing `P`: 4 (`HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1`).

Post-scoring gate table:

- `positive_controls_top50`: diagnostic_required_before_fase14 (observed 4/8; `ERBB2;EPCAM;CEACAM5;MET`)
- `negative_controls_top100`: pass (observed 0; `none`)
- `non_obvious_top10_presence`: pass (observed 10; `ITGB4;HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1;CDH3;MPZL1;ITGB5;NECTIN2;BST2`)
- `top20_missing_protein`: diagnostic_required_before_fase14 (observed 4; `HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1`)
- `top20_three_or_more_missing_components`: documented_tiering_restriction_required (observed 4; `HLA-DRB3;HLA-DRB4;KIR2DL5A;KIR2DS1`)
- `tme_penalty_controls_top100`: documented_tiering_demotion_required (observed 1; `PECAM1`)

Control ranks:

- `ERBB2`: rank 20; positive_control
- `CLDN18`: rank 1474; positive_control
- `FGFR2`: rank 1333; positive_control
- `TACSTD2`: rank 202; positive_control
- `EPCAM`: rank 14; positive_control
- `CEACAM5`: rank 12; positive_control
- `MET`: rank 45; positive_control
- `MSLN`: rank 158; positive_control
- `PTPRC`: rank 636; tme_or_off_tumor_penalty_control
- `PECAM1`: rank 15; tme_or_off_tumor_penalty_control

These checks are diagnostic only. A control failure triggers investigation, not score-weight tuning.

## Outputs

- `results/tables/component_scores_all_candidates.tsv`
- `results/tables/tiering_annotations_all_candidates.tsv`
- `results/tables/control_recovery_phase13.tsv`
- `results/rankings/ranking_balanced.tsv`
- `results/rankings/ranking_safety_first.tsv`
- `results/rankings/ranking_adc_focused.tsv`
- `results/rankings/ranking_novelty.tsv`
- `results/rankings/ranking_protein_first.tsv`
- `results/rankings/ranking_robust_aggregate.tsv`
- `results/rankings/ranking_v2_frozen.tsv`
- `results/validation/functional_form_sensitivity.tsv`
- `results/validation/phase13_post_scoring_sanity.tsv`

## Interpretation Boundary

This output is the active v2 preliminary integrated score freeze for auditability; `ranking_v0_frozen.tsv` remains archived as the pre-normalization-fix snapshot and `ranking_v1_frozen.tsv` remains archived as the pre-GPI evidence snapshot. It does not assign Tier 1/2/3 labels and does not support final target claims until Fase 14 stability, control recovery, manual false-positive audit, and candidate-card review are complete.
