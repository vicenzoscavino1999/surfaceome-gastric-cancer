# Changelog

All notable changes to the reproducible analysis package are documented here.

## 0.1.0-rc3 - 2026-06-01

- Supersedes `v0.1.0-rc2` by aligning push/tag GitHub Actions with the documented CI-small boundary.
- Sets `SURFACEOME_CI_SMALL=1` for push/PR pytest and skips full-data pytest files when the frozen raw/derived bundle is absent; local and manual full-data audits still run those tests.

## 0.1.0-rc2 - 2026-06-01

- Supersedes `v0.1.0-rc1` after a public-tag clean clone plus frozen-raw rerun exposed a missing Snakemake dependency edge for the supplementary-manifest status check.
- Declared `results/tables/wang2026_overlap_enrichment.tsv` and `results/tables/wang2026_matched_null.tsv` as explicit inputs to the supplementary-manifest status rule so a Fase 1-17 raw rerun builds Wang tables before validating the manifest.

## 0.1.0-rc1 - 2026-06-01

- Prepared the Computational Biology and Chemistry release-candidate package.
- Added reviewer-facing reproducibility checks through `scripts/run_reproducibility_checks.py`.
- Preserved the ranking correction history: `v0` pre-normalization fix, `v1` pre-GPI correction, and active `v2` post-GPI correction.
- Added the Fase 17 claim-traceability audit, CBC manuscript handoff, cover letter draft, submission checklist, and route-blocker documentation.
- Added external TCSA baseline comparison, Wang simple and matched-null overlap audits, GPI correction-impact tables, and limited TISCH2 candidate-level annotations without changing scores or tiers.
- Added release-engineering files for data availability, citation metadata, Docker runtime, and locked dependency audit.
- Hardened release reproducibility after clean-directory audit: Wang 2026 `mmc8.xlsx` now has a local checksum-validated cache/fallback path, Fase 13 v2 freeze metadata is pinned for bitwise ranking-hash reproduction, Docker audit passes, and a clean directory forced Fase 13->17 rerun reproduced key output hashes.
- Declared cBioPortal/GISTIC and other API/manual captures as frozen checksum inputs rather than default live re-download outputs, added `docs/source_acquisition_policy.md`, and added GitHub Actions small CI plus manual full-data release-audit workflows.
- Published the code repository at https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer and prepared the initial `v0.1.0-rc1` release-candidate tag path. The archival DOI remains pending until the frozen input package or equivalent checksum/provenance package is archived externally.

## Pre-release analysis history

- Fase 1-9 built the dataset inventory, raw/source checksums, identifier normalization, surfaceome universe, tumor expression, normal selectivity/risk, HPA protein evidence, TME fallback flags, and UniProt topology/isoform outputs.
- Fase 13 generated the preliminary six-component MVP rankings with `SC=not_available`.
- Fase 14 established that coarse stability language is justified but fine intra-tier ordering is not.
- Fase 15 assigned coarse unordered Tier 1/Tier 2/Watchlist categories by preregistered rules and frozen manual curation notes.
- Fase 16 packaged manuscript-ready figures and tables from frozen artifacts.
