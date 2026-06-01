# Fase 3 Identifier Normalization

Access date: 2026-05-28

Fase 3 builds a canonical map from HGNC approved protein-coding genes and joins HGNC aliases/previous symbols with UniProt reviewed human topology accessions, MANE/Ensembl transcripts, HPA identifiers, and Xena/Toil Ensembl gene IDs.

## Exit Criteria

- Candidate denominator: 19295 HGNC approved protein-coding genes.
- Candidates without a primary identifier: 0 (0.00%).
- Control mapping failures: 0.

The Fase 3 exit criterion is satisfied when candidate unresolved primary identifiers are <2% and all positive/negative controls map to canonical HGNC symbols. Both conditions are met for this pass.

## Source Coverage

| Source | Identifier | Total | Protein-coding mapped | Percent | Notes |
|---|---|---:|---:|---:|---|
| id_map_master_candidates | HGNC approved protein-coding gene | 19295 | 19295 | 100.00% | Candidate denominator for Fase 3 exit criterion. |
| xena_toil_tcga_gtex | Ensembl gene ID | 60498 | 19080 | 31.54% | Includes noncoding and deprecated Ensembl IDs; not the candidate denominator. |
| hpa_downloads | Ensembl gene ID | 20162 | 19214 | 95.30% | HPA uses Ensembl IDs plus gene names in bulk files. |
| hpa_downloads | gene symbol | 20151 | 18967 | 94.12% | Symbol coverage is secondary to Ensembl mapping. |
| uniprot_reviewed_human | UniProt accession | 20431 | 19203 | 93.99% | UniProt reviewed entries can include accessions not listed in HGNC uniprot_ids; symbol matching is used in master map when HGNC accessions are absent. |

## Mandatory Special Cases

- CLDN18: CLDN18.2_isoform_unresolved_gene_level_only
- ERBB2: gene_level_acceptable_amplification_and_protein_evidence_required_downstream
- FGFR2: FGFR2b_isoform_unresolved_gene_level_only
- HLA-A: hla_nonconventional_target_requires_specific_modality
- HLA-B: hla_nonconventional_target_requires_specific_modality
- HLA-C: hla_nonconventional_target_requires_specific_modality
- HLA-DMA: hla_nonconventional_target_requires_specific_modality
- HLA-DMB: hla_nonconventional_target_requires_specific_modality
- HLA-DOA: hla_nonconventional_target_requires_specific_modality
- HLA-DOB: hla_nonconventional_target_requires_specific_modality
- HLA-DPA1: hla_nonconventional_target_requires_specific_modality
- HLA-DPB1: hla_nonconventional_target_requires_specific_modality
- HLA-DQA1: hla_nonconventional_target_requires_specific_modality
- HLA-DQA2: hla_nonconventional_target_requires_specific_modality
- HLA-DQB1: hla_nonconventional_target_requires_specific_modality
- HLA-DQB2: hla_nonconventional_target_requires_specific_modality
- HLA-DRA: hla_nonconventional_target_requires_specific_modality
- HLA-DRB1: hla_nonconventional_target_requires_specific_modality
- HLA-DRB3: hla_nonconventional_target_requires_specific_modality
- HLA-DRB4: hla_nonconventional_target_requires_specific_modality
- HLA-DRB5: hla_nonconventional_target_requires_specific_modality
- HLA-E: hla_nonconventional_target_requires_specific_modality
- HLA-F: hla_nonconventional_target_requires_specific_modality
- HLA-G: hla_nonconventional_target_requires_specific_modality
- MUC1: mucin_alias_repeat_region_review_required
- MUC12: mucin_alias_repeat_region_review_required
- MUC13: mucin_alias_repeat_region_review_required
- MUC15: mucin_alias_repeat_region_review_required
- MUC16: mucin_alias_repeat_region_review_required
- MUC17: mucin_alias_repeat_region_review_required

CLDN18.2 and FGFR2b are intentionally not treated as solved by gene-level mapping. They carry explicit isoform flags and require transcript/isoform evidence before isoform-specific claims. ERBB2 gene-level mapping is acceptable, but amplification/protein evidence remains a downstream requirement. MUC and HLA genes are flagged for interpretation constraints.

## Outputs

- `data/processed/id_map_master.tsv`
- `results/tables/mapping_failures.tsv`
- `results/tables/control_identifier_mapping.tsv`
- `results/tables/id_source_coverage.tsv`
