# Fase 7 Protein Evidence And Localization

Access date: 2026-05-30

Fase 7 separates tumor RNA expression from protein evidence and localization. The MVP uses HPA stomach cancer IHC aggregate counts, HPA normal tissue IHC, and HPA subcellular localization. CPTAC/PDC and literature curation remain downstream/candidate-level layers and are marked `CPTAC_not_assessed` here.

## Coverage

- hpa_stomach_cancer_ihc: 1790/2704 (0.661982)
- hpa_normal_stomach_ihc: 1535/2704 (0.567678)
- hpa_critical_normal_ihc: 1535/2704 (0.567678)
- hpa_subcellular_location: 1302/2704 (0.481509)
- hpa_membrane_or_cell_junction: 734/2704 (0.271450)
- cptac_proteomics: 0/2704 (0.000000)
- protein_evidence_P_score_available: 1790/2704 (0.661982)

## P Score

`P_score` is a component score only. It combines:

- tumor protein presence in HPA stomach cancer;
- membrane/cell-junction localization support from HPA subcellular location;
- normal protein safety support from mapped critical normal IHC;
- HPA reliability support;
- penalties for discordance.

The HPA cancer bulk file does not expose antibody IDs, staining intensity/quantity fields, patient-level membrane pattern, or multi-antibody concordance. Those fields are therefore not imputed and must be revisited during candidate-card manual curation.

## Discordance Summary

- HPA missing stomach cancer IHC: 914
- RNA high but tumor protein absent: 102
- Protein present without membrane/cell-junction support: 410
- Low-confidence HPA evidence: 964

## Rules Preserved

- HPA not detected with low-confidence evidence does not automatically eliminate a target.
- CPTAC total proteomics would support total protein, not surface localization; it is not used in this MVP Fase 7 run.
- IHC plus membrane localization is weighted more directly than total-protein evidence for antibody/ADC-style targeting.

## Outputs

- `data/processed/protein_evidence.tsv`
- `results/tables/protein_coverage.tsv`
- `results/figures/rna_protein_concordance.svg`
