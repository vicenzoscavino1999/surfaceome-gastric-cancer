# Release Checklist

Status date: 2026-06-01

## Data

- [x] Active-analysis dataset registry is documented in `config/datasets.yaml`.
- [x] Release manifest is documented in `config/release_manifest.yaml`.
- [x] Retained active raw/source files have checksum manifests under `data/checksums/`.
- [x] Data availability limitations are documented in the manuscript, reproducibility guide, and route-blocker file.
- [ ] Public repository URL inserted after release.
- [ ] Archival DOI inserted after release.

## Code

- [x] `workflow/` dry-run works with `python -m snakemake -n --cores 1`.
- [x] Windows/no-`make` smoke-test equivalent passes through `scripts/smoke_test.ps1` and `scripts/run_reproducibility_checks.py`.
- [x] Unit tests pass with `python -m pytest -q`.
- [x] Scoring and artifact specification checks pass through `src/utils/compare_outputs.py`.
- [x] Phase 17 manuscript and figure-export checks pass.
- [x] Release-candidate Dockerfile and dependency lockfile are present.
- [x] Current release-candidate container audit passes with `docker run --rm -v "${PWD}:/work" surfaceome-gastric-cancer-repro`.
- [x] Current release-candidate clean-directory audit passes after forced Fase 13->17 rerun and hash comparison.
- [ ] Clean clone/container audit repeated after public release tag/DOI freeze.
- [ ] Full transitive environment lockfile or container verified on the frozen public release.

## Results

- [x] Active ranking includes a frozen SHA256 recorded in the manuscript and reproducibility documentation.
- [x] Active ranking file-level provenance is stored in `results/rankings/ranking_v2_frozen.metadata.yaml` rather than repeated per row.
- [x] Preserved ranking snapshots exist for pre-normalization and pre-GPI states.
- [x] Sensitivity outputs are generated and checked.
- [x] Candidate cards and tier files are generated/validated as frozen artifacts.
- [x] Manuscript figures are exported and checked as publication PDFs.
- [x] Forced downstream Fase 13->17 workflow rerun and key-output hash comparison completed on a clean directory copy.
- [ ] Full all-rules rerun from raw acquisition repeated after public release tag/DOI freeze, if live-source access remains available.

## Documentation

- [x] `README.md`
- [x] `REPRODUCIBILITY.md`
- [x] `docs/reproducibility_reviewer_guide.md`
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
- [ ] GitHub or equivalent public repository release.
- [ ] Zenodo, OSF, Figshare, or equivalent archival DOI.
- [ ] DOI and public repository URL added to manuscript.
- [ ] DOI and public repository URL added to cover letter.
- [ ] Editorial Manager upload completed.
