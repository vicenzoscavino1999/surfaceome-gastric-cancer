# Fase 16: Figures and Tables

Date: 2026-05-31

## Status and scope

Fase 16 packages manuscript-ready figures and tables from frozen Fase 13-15 artifacts.
It does not change scores, weights, universe membership, ranking, or tier assignments.

Inputs remain anchored on `results/rankings/ranking_v2_frozen.tsv` (SHA256 `95040edef1b2...`) and Fase 15 coarse tiers.

## Main results packaged

- Ranking rows packaged: 2704.
- Coarse tier distribution: Tier 1=6, Tier 2=12, Watchlist=12.
- Tier 1 set: ITGB4, CDH3, NECTIN2, CEACAM5, JAG1, EPCAM.
- Wang 2026 concordance carried forward: 16/18 Tier 1+Tier 2 in Wang drug-target table; Fase 17 adds simple enrichment and matched-null sensitivity audits.

## New Fase 16 figures

- `results/figures/phase16_pipeline_overview.svg`
- `results/figures/phase16_surfaceome_evidence_landscape.svg`
- `results/figures/phase16_tumor_normal_selectivity.svg`
- `results/figures/phase16_multilayer_heatmap_top30.svg`
- `results/figures/phase16_benchmark_controls.svg`
- `results/figures/phase16_tier1_candidate_panel.svg`

Existing Fase 8/Fase 14 figures remain part of the manuscript figure manifest where appropriate.

## Main manuscript tables

- Table 1: `results/tables/manuscript_table1_datasets.tsv`
- Table 2: `results/tables/manuscript_table2_score_definitions.tsv`
- Table 3: `results/tables/manuscript_table3_top_candidates.tsv`
- Table 4: `results/tables/manuscript_table4_controls.tsv`
- Table 5: `results/tables/manuscript_table5_candidate_flags.tsv`

## Manifests

- Figure manifest: `results/tables/manuscript_figure_manifest.tsv`
- Supplementary table manifest: `results/tables/supplementary_table_manifest.tsv`

## Interpretation guardrails

- Tiers are coarse and unordered within tier.
- `SC` remains not available in the primary score; TME interpretation relies on bulk marker/purity diagnostics plus curation.
- Wang 2026 is used as external consistency and compartment-framework context, not as proof of first discovery or independent ranking validation.
- Figure 7H does not directly resolve NECTIN2/PECAM1/LRRC15 per-gene compartments.
- Candidate outputs remain hypothesis-generating and require experimental validation.

## Decision

Fase 16 complete. Proceed to Fase 17 manuscript drafting with these packaged figures/tables and the stated limitations.
