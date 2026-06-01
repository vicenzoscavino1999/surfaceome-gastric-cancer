# Frozen Source Acquisition Policy

Date: 2026-06-01

This release does not claim that a reviewer can redownload every byte from live web services and obtain a bitwise-identical workspace. The official reviewer paths use retained frozen local raw/source files, checksum manifests, and the clean Git release tree. Live re-downloads are a transparency check only.

## Reviewer Contract

- `audit` validates the prepared release package.
- `recompute-downstream` recomputes Fase 13-17 from frozen upstream tables and frozen manual curation inputs.
- `recompute-from-frozen-raw` recomputes Fase 1-17 from the retained local `data/raw/` bundle without live web re-querying.
- `redownload-from-live-sources` is best-effort only. API payloads, endpoint behavior, versions, and availability can change after the release date.

The final public release must be archived through Zenodo, OSF, Figshare, or an equivalent repository. The archival DOI must cover the code tree and the frozen data inputs needed for the reviewer contract, or a documented data package containing checksum manifests and exact retrieval/provenance records where upstream redistribution terms prevent bundling raw third-party files.

## Frozen API and Manual Inputs

| Source | Frozen local inputs | Checksum manifest | Release policy |
|---|---|---|---|
| cBioPortal TCGA-STAD clinical | `data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json` | `data/checksums/cbioportal_sha256.tsv` | Frozen archived input. The Snakemake path treats this JSON as an input and runs Fase 5 in `--offline` mode. |
| cBioPortal GISTIC ERBB2/FGFR2/MET | `data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json` | `data/checksums/cbioportal_sha256.tsv` | Frozen archived input. Live cBioPortal POST re-fetch is allowed only as an explicit best-effort refresh outside the default reviewer path. |
| GDC TCGA-STAD metadata | `data/raw/gdc_tcga_stad/cases_tcga_stad.json`; `data/raw/gdc_tcga_stad/files_tcga_stad_rnaseq_star_counts.json` | `data/checksums/gdc_tcga_stad_sha256.tsv` | Frozen metadata capture. The workflow validates the retained JSON files rather than silently replacing them. |
| TISCH2 candidate scRNA context | `data/raw/tisch2/STAD_GSE134520/*`; `data/raw/tisch2/STAD_GSE167297/*` | `data/checksums/tisch2_candidate_scrna_sha256.tsv` | Frozen candidate-level annotation inputs. They are context-only and not admitted into the numeric `SC` score. |
| Wang 2026 supplementary workbook | `data/raw/wang2026/mmc8.xlsx` | `data/checksums/wang2026_mmc8_sha256.tsv` | Frozen open-access workbook input used for consistency/context audits only. |
| Manual curation artifacts | `data/raw/manual_curation/*` | Tracked by the release Git tree and phase checks | Frozen human-curation inputs. The workflow materializes them into `results/tables/` but does not regenerate web/manual review. |
| Live endpoint inventory snapshots | `data/raw/frozen_snapshots/phase1_inventory/*` | Tracked by the release Git tree | Frozen inventory metadata for offline Fase 1 materialization. |

## cBioPortal/GISTIC Implementation

`workflow/Snakefile` declares both cBioPortal JSON files as inputs to `phase5_tumor_expression`. The rule runs:

```bash
python scripts/build_tumor_expression.py --offline
```

In this mode, missing cBioPortal/GISTIC JSON files cause an explicit failure. The script still supports live refresh through `--force-download` when run outside the official reviewer path, but that path is not the release reproduction claim.

## CI Boundary

GitHub Actions checks are split by data requirement:

- Push/PR CI runs syntax linting, `pytest`, a CI-safe Snakemake dry-run over tracked small frozen targets, and a Docker image build.
- Full reviewer audit and container audit are manual workflow-dispatch jobs that require the frozen release data bundle to be present.
- The full Fase 1-17 rerun from frozen raw data is also a manual release audit job, not a per-push CI requirement.

This split prevents CI from passing as a false "download from zero" claim while still giving reviewers and maintainers executable audit hooks.
