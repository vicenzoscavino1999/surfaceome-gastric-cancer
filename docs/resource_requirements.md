# Resource Requirements

Initial estimates are placeholders until Fase 2 downloads and the first full smoke workflow.

```yaml
resource_estimates:
  raw_data_storage: "TBD after Fase 2"
  processed_data_storage: "TBD after Fase 5"
  peak_ram: "TBD after first full run"
  full_pipeline_time: "TBD on reference machine"
  smoke_test_time: "<10 min"
  docker_build_time: "TBD"
  requires_gpu: false
  requires_internet: "download phase only"
  rate_limited_apis: ["HPA", "UniProt", "ClinicalTrials.gov", "Open Targets"]
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
