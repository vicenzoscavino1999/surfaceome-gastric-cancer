# Release Checklist

Status date: 2026-06-01

## Data

- [x] Active-analysis dataset registry is documented in `config/datasets.yaml`.
- [x] Release manifest is documented in `config/release_manifest.yaml`.
- [x] Retained active raw/source files have checksum manifests under `data/checksums/`.
- [x] API/manual captures are declared as frozen inputs in `docs/source_acquisition_policy.md`; cBioPortal/GISTIC are not treated as default live-download outputs.
- [x] Data availability limitations are documented in the manuscript, reproducibility guide, and route-blocker file.
- [x] Public repository URL inserted after release: https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer.
- [x] Archival DOI inserted after release and covering the frozen input package or equivalent checksum/provenance data package: `10.5281/zenodo.20498705`.

## Code

- [x] `workflow/` dry-run works with `python -m snakemake -n --cores 1`.
- [x] Windows/no-`make` smoke-test equivalent passes through `scripts/smoke_test.ps1` and `scripts/run_reproducibility_checks.py`.
- [x] Unit tests pass with `python -m pytest -q`.
- [x] Scoring and artifact specification checks pass through `src/utils/compare_outputs.py`.
- [x] Phase 17 manuscript and figure-export checks pass.
- [x] Release-candidate Dockerfile and dependency lockfile are present.
- [x] GitHub Actions workflow added for push/PR small CI, manual reviewer audit, Docker audit, and manual frozen-raw rerun.
- [x] Current release-candidate container audit passes with `docker run --rm -v "${PWD}:/work" surfaceome-gastric-cancer-repro`.
- [x] Current release-candidate clean-directory audit passes after forced Fase 13->17 rerun and hash comparison.
- [x] Current release-candidate clean-directory recompute from frozen `data/raw/` passes Fase 1->17 and reviewer audit.
- [ ] Clean clone/container audit repeated after public release tag; post-tag result should be recorded in release notes or an external audit artifact because it is generated after the commit tree is frozen.
- [ ] Full transitive environment lockfile or container verified on the frozen public release tag.
- [ ] Manual GitHub Actions release-audit workflow repeated on the final public release package if the frozen data bundle is available to the runner.

## Results

- [x] Active ranking includes a frozen SHA256 recorded in the manuscript and reproducibility documentation.
- [x] Active ranking file-level provenance is stored in `results/rankings/ranking_v2_frozen.metadata.yaml` rather than repeated per row.
- [x] Preserved ranking snapshots exist for pre-normalization and pre-GPI states.
- [x] Sensitivity outputs are generated and checked.
- [x] Candidate cards and tier files are generated/validated as frozen artifacts.
- [x] Manuscript figures are exported and checked as publication PDFs.
- [x] Forced downstream Fase 13->17 workflow rerun and key-output hash comparison completed on a clean directory copy.
- [x] Full declared workflow rerun from frozen local raw/source files completed on a clean directory copy, with key-output hash comparison.
- [ ] Live-source redownload smoke test after public release tag and DOI archive, best-effort only.

## Documentation

- [x] `README.md`
- [x] `REPRODUCIBILITY.md`
- [x] `docs/reproducibility_reviewer_guide.md`
- [x] `docs/source_acquisition_policy.md`
- [x] `docs/design_decisions.md`
- [x] `docs/analytical_decisions_registry.md`
- [x] `docs/reviewer_attack_surface.md`
- [x] `docs/nondeterminism_inventory.md`
- [x] `manuscript/cbc_submission_checklist.md`
- [x] `manuscript/cbc_submission_route_blockers.md`
- [x] `DATA_AVAILABILITY.md`
- [x] `CITATION.cff`
- [x] `CHANGELOG.md`

## Publication

- [ ] Final PDF/graphical abstract approved by author.
- [x] GitHub or equivalent public repository release.
- [x] Zenodo, OSF, Figshare, or equivalent archival DOI.
- [x] Public repository URL added to manuscript.
- [x] Public repository URL added to cover letter.
- [x] DOI added to manuscript.
- [x] DOI added to cover letter.
- [ ] Editorial Manager upload completed.
