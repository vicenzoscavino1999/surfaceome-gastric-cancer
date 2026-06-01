# Fase 1 Data Inventory Notes

Access date: 2026-05-28

This file answers the mandatory Fase 1 questions using lightweight metadata/API queries only. Large matrices are not saved yet.

## Mandatory Questions

1. TCGA-STAD expression matrix: primary matrix will be UCSC Xena/Toil `TcgaTargetGtex_rsem_gene_tpm.gz`, with phenotype `TcgaTargetGTEX_phenotype.txt.gz`. The matrix is recorded as log2(TPM+0.001); verify unit again at Fase 2 download.
2. GTEx matrix: same Xena/Toil matrix, filtered to GTEx stomach normal tissue.
3. Same pipeline or batch correction: TCGA, TARGET, and GTEx in Xena/Toil are recomputed uniformly, but batch diagnostic remains mandatory before any tumor-normal selectivity score. GDC STAR counts are secondary TCGA-only sensitivity.
4. Primary tumor, adjacent normal, metastasis: Xena phenotype has TCGA-STAD Primary Tumor=414, Solid Tissue Normal=36, Metastatic=0; GTEx stomach Normal Tissue=175. GDC STAR-count RNA-seq has Primary Tumor=412, Solid Tissue Normal=36.
5. TCGA subtype counts: cBioPortal PanCanAtlas patient SUBTYPE counts are STAD_CIN=223, STAD_EBV=30, STAD_GS=50, STAD_MSI=73, STAD_POLE=7.
6. Lauren/stage/grade/anatomic site/treatment data: exact Lauren subtype was not exposed in the queried GDC/cBioPortal fields. Legacy cBioPortal histological diagnosis is available for 440 patients and has 276 Lauren-like terms requiring curation. GDC AJCC stage=416, GDC grade=443, GDC tissue origin=443, GDC site of resection/biopsy=443, GDC treatment records=409.
7. HPA version/files: HPA downloadable files are version 25.1 with Ensembl 109. Use `normal_ihc_data.tsv.zip`, `cancer_data.tsv.zip`, `subcellular_location.tsv.zip`, `rna_tissue_consensus.tsv.zip`, and `rna_tissue_gtex.tsv.zip`. The older plan names `normal_tissue.tsv` and `pathology.tsv` are superseded by current HPA file names.
8. UniProt reviewed coverage: UniProt release 2026_01 has reviewed_human=20431, transmembrane=5230, topological_domain=4037. Universe-specific coverage waits for ID mapping.
9. HPA pathology stomach cancer coverage: `cancer_data.tsv.zip` has stomach cancer rows for 15312 genes.
10. CPTAC/PDC gastric proteomics coverage: PDC has gastric/STAD studies including CPTAC STAD proteome `PDC000614` with 193 cases and 234 aliquots. Candidate gene coverage is TBD until Protein Assembly reports are downloaded and mapped.
11. DepMap gastric line count: DepMap Context Explorer STOMACH has 104 Esophagus/Stomach models, including EGC=74 and ESCC=30. Modality coverage includes CRISPR=69 and RNASeq=78.
12. scRNA gastric datasets: candidate sources include TISCH2 and GEO datasets GSE112302, GSE134520, GSE150290, GSE163558, plus recent gastric cancer scRNA atlases. They are not yet admitted to the main score; Fase 8 must verify processed matrix access and malignant epithelial vs TME annotations.

## Fase 1 Exit Status

The required files now exist:

- `results/tables/dataset_inventory.tsv`
- `results/tables/sample_counts.tsv`
- `results/tables/coverage_matrix.tsv`

Fase 1 is sufficient to proceed to Fase 2 data acquisition, with two explicit caveats:

- exact Lauren subtype is not directly available from the queried TCGA metadata and must be curated from histology or an external clinical table;
- PDC/DepMap/scRNA/structure/druggability remain incremental or candidate-level layers, not prerequisites for first scoring.
