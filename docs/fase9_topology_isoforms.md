# Fase 9 Topology, Isoforms, and Extracellular Accessibility

Access date: 2026-06-01

Fase 9 builds the topology component `T` for the Core+Probable surfaceome universe. The component is not a final biological ranking. It uses reviewed UniProt human feature fields for protein length, topological domains, transmembrane segments, signal peptide, lipid/GPI anchor, glycosylation, disulfide bonds, chains, domains, subcellular location, PTM comments, and Ensembl isoform mappings.

## Scope

Candidate genes assessed: 2704.

UniProt feature coverage: 2704/2704.

GPI-anchor annotations: 121.

Genes with D/E accessibility class: 158.

Genes with cleavage, shedding, soluble, or secreted-isoform annotation: 370.

## Accessibility Classes

- A: 1103
- B: 355
- C: 1088
- D: 66
- E: 92

Class A/B means a clear or inferred extracellular region supports antibody-accessibility review. Class C is possible but harder, usually for multipass proteins or shorter loops. Class D/E is not an automatic exclusion from the table, but it blocks Tier 1 antibody-targeting claims unless later structure/literature/candidate-card evidence provides a strong counterargument.

## Mandatory Isoform Handling

- CLDN18: CLDN18.2_isoform_unresolved_gene_level_only; implication=isoform-specific claims blocked from gene-level data
- FGFR2: FGFR2b_isoform_unresolved_gene_level_only; implication=isoform-specific claims blocked from gene-level data

`CLDN18` and `FGFR2` remain gene-level in the current expression layers. `CLDN18.2` and `FGFR2b/IIIb` claims are therefore marked `isoform_unresolved` and cannot be used as proof that the pipeline resolved isoform-specific targets.

## Benchmark Controls

- ERBB2: class=A, ECD=630, TM=1, GPI=false, isoform=multiple_uniprot_isoforms_mapped_not_resolved, T_score=0.932500
- CLDN18: class=C, ECD=53, TM=4, GPI=false, isoform=CLDN18.2_isoform_unresolved_gene_level_only, T_score=0.614010
- FGFR2: class=A, ECD=356, TM=1, GPI=false, isoform=FGFR2b_isoform_unresolved_gene_level_only, T_score=0.712500
- TACSTD2: class=A, ECD=248, TM=1, GPI=false, isoform=not_isoform_critical_or_single_canonical_mapping, T_score=0.962500
- EPCAM: class=A, ECD=242, TM=1, GPI=false, isoform=not_isoform_critical_or_single_canonical_mapping, T_score=0.962500
- MET: class=A, ECD=908, TM=1, GPI=false, isoform=multiple_uniprot_isoforms_mapped_not_resolved, T_score=0.832500
- MSLN: class=A, ECD=569, TM=0, GPI=true, isoform=multiple_uniprot_isoforms_mapped_not_resolved, T_score=0.670000

`MSLN` illustrates why Fase 9 uses the expanded UniProt feature file: its GPI-anchor supports membrane accessibility even though the earlier Fase 2 topology-only raw file did not expose a transmembrane or topological-domain feature.

## Score Definition

`T_score` combines accessibility class, extracellular length, topology confidence, and isoform confidence, then subtracts conservative cleavage/shedding and soluble-decoy penalties. These penalties are candidate-card flags, not hard filters.

## Outputs

- `data/processed/topology_isoforms_ecd.tsv`
- `results/tables/isoform_risk_flags.tsv`
- `results/figures/ecd_length_distribution.svg`
