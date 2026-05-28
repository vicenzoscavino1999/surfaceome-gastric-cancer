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
  os: "Windows"
  cpu: "TBD"
  architecture: "TBD"
  ram_gb: 0
  storage_free_gb: 0
```
