# External Surfaceome Baseline Comparison

This analysis compares the final frozen gastric ranking against the Cancer Surfaceome Atlas
(TCSA) pan-cancer GESP scores carried in `surfaceome_universe.tsv`. TCSA is used as an
external surfaceome-prioritization baseline, not as a gastric-specific validation label.

## Results

- TCSA final GESP score: Spearman rho=0.389861, n=2685, top20 overlap=1 (NECTIN2).
- TCSA core GESP score: Spearman rho=0.329466, n=2685, top20 overlap=2 (ERBB2;ITGB4).

Interpretation: the ranking is related to an external published surfaceome score, but the modest
correlation and low top-k identity show that tumor expression, normal selectivity, risk, protein
evidence, topology, stability, and curation materially change candidate prioritization.

## Outputs

- `results/tables/external_surfaceome_baseline_comparison.tsv`
- `results/tables/external_surfaceome_baseline_gene_ranks.tsv`
