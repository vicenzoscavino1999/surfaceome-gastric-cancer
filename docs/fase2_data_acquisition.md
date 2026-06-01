# Fase 2 Data Acquisition

Access date: 2026-05-28

This note records the first reproducible raw-data acquisition pass for the MVP tumor-normal workflow. Raw files are immutable inputs; derived tables must be regenerated from scripts rather than by editing raw files.

## Downloaded or Captured Files

| Source | Local raw file | Bytes | SHA-256 |
|---|---:|---:|---|
| gdc_tcga_stad | `data/raw/gdc_tcga_stad/cases_tcga_stad.json` | 444051 | `c0a0fd98e03e15fc16e73c4e270992b21356e9c3e624c3838334b39cdd6f3713` |
| gdc_tcga_stad | `data/raw/gdc_tcga_stad/files_tcga_stad_rnaseq_star_counts.json` | 248100 | `0afada9d15f74292d8c656ecd33e978b231bb67d919678ee0b4d2ff2ff8cd15e` |
| hpa_downloads | `data/raw/hpa/cancer_data.tsv.zip` | 1724018 | `6e771693dc1019a3536d8834175ee97dcfde4f835d5cb3bed7c5a48803668135` |
| hpa_downloads | `data/raw/hpa/normal_ihc_data.tsv.zip` | 5732831 | `de63f1720cbf7fe86da28a3e8463cd0e5a97f7c3add6c5a6ba500ff1518eeaea` |
| hpa_downloads | `data/raw/hpa/rna_tissue_consensus.tsv.zip` | 5293680 | `b001903da23f802c8dfbd1b6b3a8c20b831fedd4932f4bb721b06622d83ae60b` |
| hpa_downloads | `data/raw/hpa/rna_tissue_gtex.tsv.zip` | 5921184 | `8b946d52357a762a79c0395b37ed30d7c56dbba3beba0c4451e1e9d3b52659f7` |
| hpa_downloads | `data/raw/hpa/subcellular_location.tsv.zip` | 252331 | `a9466882bd3328416bcde77c32a6bcb2a17d70183af90e98d032f6f5f781d504` |
| uniprot_reviewed_human | `data/raw/uniprot/uniprot_reviewed_human_topology.tsv.gz` | 1778081 | `b27b89d9785d88fbc5a85c6ef0d13943e9f591abb2bf335c3f3e181c0a8ea257` |
| xena_toil_tcga_gtex | `data/raw/xena_toil/TcgaTargetGTEX_phenotype.txt.gz` | 135753 | `ba4d4461cff0fe5e91cc3e58f793aa47ff3c5d6fbf77d65ccff5a07231aaf2db` |
| xena_toil_tcga_gtex | `data/raw/xena_toil/TcgaTargetGtex_rsem_gene_tpm.gz` | 1323254426 | `a8c36cb16ef82eccb0b6e1e62a2af3ab9d54c1f56735bc59dfac4cbbe2391d4d` |

## Reproducibility Outputs

- Global checksum manifest: `data/checksums/sha256sums.txt`
- Source checksum manifests: `data/checksums/xena_toil_sha256.tsv`, `data/checksums/hpa_sha256.tsv`, `data/checksums/uniprot_sha256.tsv`, `data/checksums/gdc_tcga_stad_sha256.tsv`
- Download manifest: `results/tables/phase2_download_manifest.tsv`
- Provenance log: `docs/provenance_log.tsv`

## Batch Diagnostic Gate

The required Xena/Toil tumor-normal batch diagnostic has been generated:

- `results/figures/pca_batch_diagnostic.svg`
- `results/tables/batch_permanova.tsv`

Interpretation is documented in `docs/fase2_batch_diagnostic.md`. GDC STAR Counts expression files remain a secondary sensitivity layer. The raw GDC metadata captured here identifies eligible files, and Fase 5 must preserve TCGA/GTEx source labels plus adjacent-normal sensitivity before strong tumor-normal selectivity claims.
