# Reviewer Attack Surface

| ID | Attack | Severity | Current defense | Gap | Remediation |
|---|---|---|---|---|---|
| RA-01 | Surfaceome universe is arbitrary. | High | Multi-source universe planned. | No downloaded/versioned source yet. | Implement `surfaceome_universe_definition.yaml`, Jaccard overlap, and strict/broad sensitivity. |
| RA-02 | Weights are arbitrary. | High | Weights preregistered in `config/scoring_scenarios.yaml`. | No perturbation results yet. | Run perturbation, leave-one-layer-out, and functional-form sensitivity. |
| RA-03 | TCGA/GTEx batch invalidates selectivity. | High | Fase 1 chose Xena/Toil as primary and GDC STAR counts/adjacent normal as secondary sensitivity. | No PCA/PERMANOVA yet. | Generate PCA/PERMANOVA before freezing `N`. |
| RA-04 | No wet-lab validation. | High | Hypothesis-generating scope. | Must avoid clinical efficacy/safety claims. | Candidate cards must propose experimental follow-up and state limitations. |
| RA-05 | Bulk RNA signal may be TME. | High | scRNA optional; TME marker correlation planned for MVP. | No scRNA selected yet. | Add TME flags and purity-adjusted correlations if scRNA is unavailable. |
| RA-06 | CLDN18.2 and FGFR2b are not resolved at isoform level. | High | Isoform flags preregistered. | Data may be gene-level only. | Keep `isoform_unresolved` flag and avoid isoform-specific claims when unresolved. |
| RA-07 | Controls are cherry-picked or adjusted post hoc. | Medium | Controls preregistered in `config/controls.yaml`. | Revision process needed. | Use `config/controls_revision_log.tsv`; no ad-hoc tuning. |
| RA-08 | Results do not reproduce. | Medium | Reproducibility plan exists. | Workflow and tests still minimal. | Implement Snakemake, checksums, smoke test, Docker audit. |
| RA-09 | Lauren subtype claims are overcalled. | Medium | Fase 1 found no exact Lauren field in queried GDC/cBioPortal metadata and flags histology as proxy only. | Lauren mapping not curated. | Do not make Lauren-specific quantitative claims until a curated mapping/table is documented. |
