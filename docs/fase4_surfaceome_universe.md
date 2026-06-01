# Fase 4 Surfaceome Universe

Access date: 2026-06-01

This phase builds a conservative multi-source surfaceome universe from Cancer Surfaceome Atlas/TCSA, CSPA, SURFY, UniProt topology, UniProt reviewed lipidation/GPI-anchor evidence, UniProt GO cellular component terms, and HPA subcellular localization. The unit remains the HGNC approved protein-coding gene from Fase 3.

Core/Probable membership requires independent surface support plus an anchor/topology/localization signal: UniProt extracellular topology, confirmed UniProt lipidation `GPI-anchor`, UniProt transmembrane annotation, HPA plasma membrane localization, or SURFY surfaceome support. Curated-list or GO-only genes without this anchor are retained as ambiguous rather than used as high-confidence targets.

Confirmed UniProt lipidation `GPI-anchor` is counted as non-experimental strong anchor evidence: score +2, support source +1, `has_anchor=true`, and `has_strong=true`. Subcellular-location-only GPI annotations are flagged but not credited as confirmed direct lipid evidence.

## Category Counts

- Core surfaceome: 2646
- Probable surfaceome: 58
- Core + probable: 2704
- Ambiguous membrane or surface context: 6428
- Excluded: 10163

## Published-List Overlap

| Published list | Published genes | Intersection | Union | Jaccard |
|---|---:|---:|---:|---:|
| tcsa | 3446 | 2685 | 3465 | 0.7749 |
| cspa | 1222 | 880 | 3046 | 0.2889 |
| surfy | 2701 | 2405 | 3000 | 0.8017 |

TCSA and SURFY provide broad published-list agreement with the Core+Probable universe. CSPA overlap is lower because CSPA is an older, experimentally observed and narrower surface proteomics list; CSPA-only absences remain auditable in the false-positive/false-negative table instead of being forced into Core/Probable.

## Exit Criteria

- Negative controls in Core/Probable: 0
- Positive or benchmark controls excluded: 0
- Core + Probable below 500: false
- Core + Probable above 3000: false

Context-dependent or non-canonical surface annotations without membrane anchor/topology support are intentionally retained as ambiguous. This prevents ER/secreted/intracellular negative controls with incidental surface annotations from entering Core/Probable while preserving them for manual review if they later appear as expression-driven top candidates.

The universe is acceptable for the next phase only if negative controls do not enter Core/Probable, positive controls are present or explained, and published-list overlap is interpretable. Genes absent from all published lists and published genes absent from Core/Probable are recorded in `surfaceome_false_positive_false_negative_audit.tsv` for top-candidate review.

## Outputs

- `data/processed/surfaceome_universe.tsv`
- `results/figures/surfaceome_source_overlap.svg`
- `results/figures/surfaceome_jaccard_with_published_lists.svg`
- `results/tables/surfaceome_confidence_summary.tsv`
- `results/tables/surfaceome_jaccard_with_published_lists.tsv`
- `results/tables/surfaceome_false_positive_false_negative_audit.tsv`
