# Candidate-Level scRNA Compartment Check

Access date: 2026-06-01

This is a post-ranking candidate-level cross-check. It does not change the numeric `SC` component,
the frozen ranking, or the Tier 1/Tier 2 assignments. Its purpose is to reduce overclaiming by
annotating whether the 18 nominated candidates show malignant-cell, epithelial, stromal, endothelial,
or immune/TME expression in public processed gastric scRNA resources.

## Sources

- `STAD_GSE134520` (Zhang et al., Cell Reports 2019, PMID 31067475): 41554 cells, 13 samples, malignant cells annotated: 880.
- `STAD_GSE167297` (Jeong et al., Clinical Cancer Research 2021, PMID 34385296): 22464 cells, 14 samples, malignant cells annotated: 0.

TISCH2 average cell-type expression matrices and cell metadata were downloaded from the public
TISCH2 dataset pages. Expression values are used as TISCH2-normalized mean expression summaries,
not as raw UMI counts.

## STAD_GSE134520 Summary

- Candidate calls: {'low_malignant_signal_in_dataset': 7, 'malignant_class_supported': 8, 'mixed_malignant_and_nonmalignant_signal': 1, 'nonmalignant_dominant_signal': 2}
- Malignant-class supported: NECTIN2;JAG1;MPZL1;ITGB5;BST2;IFNGR1;CD9;TGFBR1
- Mixed malignant and non-malignant signal: ITGB4
- Low malignant signal in this dataset: CDH3;CEACAM5;ALPG;DSC2;TNFRSF11A;ERBB2;CDH17
- Non-malignant dominant signal: EPCAM;LSR

Interpretation: the limited scRNA cross-check strengthens compartment caveats. It provides direct
malignant-cell support for a subset of candidates but does not resolve cell-of-origin for all Tier 1/2
genes. Some clinically or biologically plausible epithelial antigens are low in the early-cancer
TISCH2 malignant-cell class, so absence of support here is not treated as an exclusion.

## Outputs

- `results/tables/candidate_scrna_tisch2_compartment_check.tsv`
- `results/tables/candidate_scrna_tisch2_summary.tsv`
- `results/figures/candidate_scrna_tisch2_compartment_heatmap.svg`
- `data/checksums/tisch2_candidate_scrna_sha256.tsv`
