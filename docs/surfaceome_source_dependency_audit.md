# Surfaceome Source-Dependency Audit

Date: 2026-06-01

## Scope

This post-ranking robustness audit checks whether the 18 Tier 1/2 candidates depend
on a single declared surfaceome source. It does not change scores, weights, universe
membership, rankings, or tier assignments.

Source groups tested:

- TCSA curated cancer surfaceome
- CSPA experimental cell-surface proteomics
- SURFY in silico surfaceome
- UniProt extracellular topology, transmembrane, or confirmed GPI-anchor evidence
- HPA plasma-membrane localization
- GO plasma-membrane or cell-surface annotation

## Results

- Multi-source supported Tier 1/2 candidates: 18/18 (1.000).
- Curated-list plus independent anchor support: 18/18 (1.000).
- Retain support after any single-source removal: 18/18 (1.000).
- Single-source dependent Tier 1/2 candidates: 0/18 (0.000); genes: none.

Dependency classes:

- `source_diverse_curated_plus_anchor`: 18

## Interpretation

The Tier 1/2 set is not driven by a single surfaceome resource. This supports the
claim that the nominated hypotheses are not simple artifacts of one curated list or
one database/localization source. The audit is still a source-dependency check, not
experimental validation of membrane abundance, malignant-cell origin, safety, or
clinical actionability.

## Outputs

- `results/tables/surfaceome_source_dependency_audit.tsv`
- `results/tables/surfaceome_source_dependency_summary.tsv`
