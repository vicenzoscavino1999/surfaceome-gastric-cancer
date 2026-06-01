# Fase 4B Ranking-Resolution Simulation

Access date: 2026-05-30

This pre-scoring simulation estimates whether the current surfaceome universe and observed layer coverage can support fine-grained tiering before biological expression/selectivity results are inspected.

The simulation uses the Core+Probable Fase 4 universe (`N=2704`), `K=500` synthetic rankings, the preregistered Balanced weights, and `exclude_and_renormalize` missing-data handling. `Surf` uses the observed Fase 4 surfaceome confidence score. `E`, `N`, `R`, `P`, and `T` use neutral synthetic score distributions because their real score distributions are not available before Fase 5+. `R` is simulated as favorable low-risk contribution for rank-resolution purposes only.

## Coverage Used

- Surf: 1.0000
- E: 0.9970
- N: 0.9970
- R: 0.9963
- P: 0.9963
- T: 1.0000

## Resolution Summary

- Genes with 95% rank CI within +/-10 positions: 0
- Genes with 95% rank CI exceeding +/-50 positions: 2693
- Median-rank top 20 genes with 95% CI contained in top 40: 0
- Decision: `reduce_to_three_tiers_or_raise_tier1_stability_threshold`

## Interpretation

Fase 4B is not a statistical power test and does not assign biological priority. It calibrates how much rank movement is expected from missingness and neutral layer uncertainty. The simulation must be repeated in Fase 14 with real component-score distributions and perturbation/leave-one-layer-out sensitivity before interpreting final rank positions.

## Parameters

- Seed: 20260531
- Latent weight for neutral layers: 0.7
- Component noise SD: 0.08

## Outputs

- `results/validation/ranking_resolution_simulation.tsv`
- `results/validation/ranking_resolution_summary.tsv`
- `results/figures/rank_ci_by_coverage.svg`
