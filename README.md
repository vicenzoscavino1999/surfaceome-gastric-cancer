# Surfaceome-Guided Target Prioritization in Gastric Adenocarcinoma

This repository is the execution workspace for a reproducible computational paper that prioritizes cell-surface targets in gastric adenocarcinoma.

Current stage: Fase 1 dataset inventory complete. No data-derived results should be interpreted until Fase 2 downloads and batch diagnostics are complete.

## First Gates

1. Freeze controls, scoring scenarios, dataset targets, seeds, and decision logs before looking at rankings.
2. Complete `docs/literature_landscape_and_differentiation.md` with at least five real close references.
3. Decide `go`, `go_with_narrower_claim`, or `pivot`.
4. Download expression data only after the novelty gate and dataset inventory are documented.

Current Fase 0B status: closed for execution as `go_with_narrower_claim`; direct manual Google Scholar verification remains a pre-submission check.

Current Fase 1 status: metadata inventory complete in `results/tables/dataset_inventory.tsv`, `results/tables/sample_counts.tsv`, `results/tables/coverage_matrix.tsv`, and `docs/fase1_data_inventory.md`.

## Commands

```bash
make help
make smoke-test
```

On Windows without `make`:

```powershell
.\scripts\smoke_test.ps1
```

The current `smoke-test` is a placeholder gate for repository wiring. It does not validate scientific results yet.
