# Resource Requirements

Initial estimates are now anchored by the Fase 2 MVP download and batch diagnostic. Later phases can still increase storage and runtime.

```yaml
resource_estimates:
  raw_data_storage: "~1.38 GB for Fase 2-4 MVP raw files including HGNC and surfaceome workbooks; optional PDC/raw proteomics can be much larger and is not part of MVP download"
  processed_data_storage: "Fase 13 processed tables/rankings remain TSV scale; no scRNA count matrix has been admitted or stored; tidyestimate source adds <1 MB raw purity-signature input; expanded UniProt Fase 9 feature raw adds ~4.3 MB; Fase 4 UniProt GPI raw stream is TSV-gzip scale"
  peak_ram: "Fase 2 batch diagnostic completed with top 2000 genes on reference machine; exact peak not profiled"
  full_pipeline_time: "Current Fase 1-13 workflow dry-run is up to date; Fase 8 bulk TME fallback plus ESTIMATE/tidyestimate partial correlations reads the Xena matrix and takes about 1.5 minutes on the reference machine; Fase 9 topology parsing is sub-minute after UniProt feature download; Fase 13 v2 scoring and diagnostic are seconds-scale"
  smoke_test_time: "<10 min"
  docker_build_time: "TBD"
  requires_gpu: false
  requires_internet: "download phase only"
  rate_limited_apis: ["HPA", "UniProt", "ClinicalTrials.gov", "Open Targets", "GDC", "cBioPortal", "DepMap", "PDC"]
  known_large_files:
    xena_toil_gene_tpm_gz: "1323254426 bytes by HEAD on 2026-05-28"
    total_fase2_mvp_raw_files: "1340344456 bytes across 10 files on 2026-05-28"
    hgnc_complete_set_txt: "16737155 bytes by HEAD on 2026-05-28"
    total_fase4_surfaceome_raw_files: "15395627 bytes across 4 files on 2026-05-28"
    tidyestimate_source_tar_gz: "936616 bytes on 2026-05-28"
    uniprot_phase9_features_tsv_gz: "4338475 bytes on 2026-05-28"
```

```yaml
reference_machine:
  os: "Microsoft Windows 11 Home Single Language 10.0.22621"
  cpu: "Intel(R) Core(TM) i5-10300H CPU @ 2.50GHz"
  architecture: "x86_64 / 64-bit Windows"
  cores: 4
  logical_processors: 8
  ram_gb: 15.84
  storage_free_gb_on_d: 865.62
```
