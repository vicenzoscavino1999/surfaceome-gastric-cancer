# Reviewer Reproducibility Guide

Date: 2026-06-01

This guide gives reviewers a short path through the repository. It does not replace the full provenance records in `docs/provenance_log.tsv`, `config/datasets.yaml`, `config/release_manifest.yaml`, or `REPRODUCIBILITY.md`.

## What a Reviewer Can Verify

- Raw/source files that are retained locally are registered in `config/datasets.yaml` and checksum manifests under `data/checksums/`.
- The active ranking is `results/rankings/ranking_v2_frozen.tsv`; its SHA256 is `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`.
- File-level freeze metadata is stored in `results/rankings/ranking_v2_frozen.metadata.yaml`, not repeated in every ranking row. The literal release commit hash is not embedded in the tracked sidecar; the clean Git commit/tag containing the sidecar is the authoritative file-tree reference.
- The active ranking TSV now contains only ranking/scoring fields. A clean Git commit/tag, not a self-referential in-file commit hash, should define the exact public release file tree.
- Earlier ranking snapshots are preserved as `results/rankings/ranking_v0_frozen.tsv` and `results/rankings/ranking_v1_frozen.tsv`.
- Phase checks validate data inventory, checksums, processed tables, ranking artifacts, stability outputs, tier assignments, manuscript figures/tables, and CBC manuscript constraints.
- Snakemake declares the workflow targets and currently reports nothing to do on the prepared workspace.
- Manuscript figures are checked as nonblank, font-independent PDFs through `scripts/export_phase17_publication_figures.py --check`.

## Reproducibility Levels

The repository separates four reproducibility modes so that reviewers can distinguish validation from recomputation:

1. `audit`: checks the prepared release workspace. It validates file presence, checksums, internal table consistency, ranking freeze hashes, tier/manuscript constraints, publication figure PDFs, and a Snakemake dry-run. It does not claim to recompute every scientific output.
2. `recompute-downstream`: recomputes Fase 13-17 from frozen upstream tables in `data/processed/` plus frozen manual curation inputs. This is the shortest recomputation path for the active ranking, tiering, downstream validation, manuscript tables, and publication figures.
3. `recompute-from-frozen-raw`: starts from retained local raw/source files under `data/raw/`, deletes derived outputs such as `data/processed/`, `data/checksums/`, `results/`, and generated manuscript figure PDFs, then runs the declared Snakemake workflow from Fase 1-17 without live web re-querying.
4. `redownload-from-live-sources`: re-runs acquisition against live APIs or websites. This is best-effort only because GDC, HPA, UniProt, cBioPortal, TISCH2, and other sources can change access behavior, metadata, versions, or availability after the release date.

Frozen raw inputs include the retained source data, `data/raw/frozen_snapshots/phase1_inventory/` for live-endpoint inventory metadata, `data/raw/frozen_snapshots/` for historical ranking snapshots, and `data/raw/manual_curation/` for human-curated tiering artifacts. The active scientific ranking table remains metadata-free; file-level release metadata is in the sidecar.

The frozen-source acquisition policy is documented in `docs/source_acquisition_policy.md`. In particular, cBioPortal clinical/GISTIC JSON files, GDC metadata captures, TISCH2 candidate-context files, Wang 2026 `mmc8.xlsx`, endpoint inventory snapshots, and manual curation files are frozen inputs with checksum/provenance records. The final public DOI must cover these inputs or an equivalent archived data package. Live re-download is not the release reproduction claim.

## One-Command Audit

Install the project check dependencies:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-manuscript.txt
```

Run the reviewer audit:

```powershell
python scripts/run_reproducibility_checks.py
```

This command runs unit tests, all phase artifact checks through Fase 16, the CBC manuscript check, the publication-figure check, and a Snakemake dry-run.

Expected current result:

- `python -m pytest -q`: 13 tests pass.
- Phase artifact checks: all pass from bootstrap through Fase 16.
- `scripts/check_phase17_manuscript_brief.py`: passes.
- `scripts/export_phase17_publication_figures.py --check`: passes.
- `python -m snakemake -n --cores 1`: reports that all requested files are present and up to date.

## Recompute Downstream

From a prepared release workspace that already contains `data/processed/` and frozen raw/manual inputs:

```powershell
python -m snakemake --cores 1 --forcerun phase13_mvp_scoring
python scripts/run_reproducibility_checks.py
```

This recomputes the active scoring layer and downstream declared outputs: Fase 13 rankings/diagnostics, Fase 14 stability, Fase 15 materialized tiering/curation artifacts, Fase 16 manuscript tables/figures, and Fase 17 reviewer-hardening/publication-figure exports.

## Recompute From Frozen Raw

For the stricter no-live-download path, make a clean copy of the release workspace, preserve `data/raw/`, and delete derived outputs:

```powershell
Remove-Item data\processed,data\interim,data\checksums,results,.snakemake -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item manuscript\latex\figures -Recurse -Force -ErrorAction SilentlyContinue
python -m snakemake --cores 1
python scripts/run_reproducibility_checks.py
```

In this mode the workflow uses the frozen raw files already present under `data/raw/`. Raw/source files are Snakemake inputs, not disposable outputs, so a missing retained raw file causes an explicit missing-input failure instead of a silent re-download or deletion. The current release candidate completed this path in a clean directory copy and the reviewer audit passed afterward.

## Redownload From Live Sources

Live-source acquisition is not the default reviewer path. It can be attempted by running the acquisition scripts without offline mode, but any mismatch must be interpreted as a source-version/access change unless the frozen raw checksums also change. This path is useful for transparency, not for bitwise release reproduction.

## Optional Manuscript Rebuild

LaTeX compilation requires a working TeX installation with `latexmk`, `pdflatex`, and `bibtex`.

```powershell
python scripts/run_reproducibility_checks.py --include-latex
```

The optional LaTeX pass regenerates `manuscript/latex/cbc_manuscript.tex`, compiles `manuscript/latex/cbc_manuscript.pdf`, and rebuilds `manuscript/cbc_editorial_manager_package/`.

## Docker Runtime

The release-candidate Docker runtime installs the locked dependency closure from `requirements-lock.txt` and runs the same reviewer audit against a mounted checkout. This file is intended as the current full transitive environment lockfile for the Python audit/runtime stack.

```powershell
docker build -f docker/Dockerfile -t surfaceome-gastric-cancer-repro .
docker run --rm -v "${PWD}:/work" surfaceome-gastric-cancer-repro
```

The image does not copy large raw/source data during build. It expects the release checkout, including `data/`, `results/`, and `manuscript/`, to be mounted at `/work`.

## GitHub Actions

`.github/workflows/reproducibility-ci.yml` defines three CI levels:

1. Push/PR `ci-smoke`: syntax lint through `compileall`, `pytest`, a Snakemake dry-run over tracked small frozen targets, and Docker image build. Data-dependent pytest checks are skipped automatically when the frozen release data bundle is not present.
2. Manual `reviewer-audit`: verifies the full frozen data bundle, runs `python scripts/run_reproducibility_checks.py`, runs a full Snakemake dry-run, and runs the Docker audit. It can optionally force Fase 13-17 recomputation.
3. Manual `frozen-raw-rerun`: verifies frozen raw/source inputs, deletes derived outputs, recomputes Fase 1-17 from `data/raw/`, and reruns the reviewer audit.

The manual jobs require the frozen data package to be present in the workflow workspace. They are release-audit hooks, not a claim that GitHub can redownload all live sources on every push.

To write a local release audit report:

```powershell
python scripts/build_release_audit_report.py
```

The current release candidate has been checked in Docker and in clean directory copies. The downstream clean copy completed `python -m snakemake --cores 1 --forcerun phase13_mvp_scoring`. A stricter frozen-raw clean copy then deleted derived outputs, preserved `data/raw/`, ran `python -m snakemake --cores 1` through Fase 1-17, and passed `python scripts/run_reproducibility_checks.py`. Key outputs matched the main workspace bit-for-bit, including the active ranking hash.

## Manual Traceability Checks

- Central claim map: `docs/fase17_claim_traceability.md`.
- Analysis decisions: `docs/analytical_decisions_registry.md`.
- Reviewer-risk register: `docs/reviewer_attack_surface.md`.
- Non-determinism inventory: `docs/nondeterminism_inventory.md`.
- Data/code availability wording: `manuscript/cbc_manuscript_scaffold.md`, section `Data and code availability`.
- Submission blockers: `manuscript/cbc_submission_route_blockers.md`.

## Current Limitations

- A public repository URL and archival DOI are still pending; those must be inserted before formal submission.
- A Dockerfile, full transitive environment lockfile, Docker audit, downstream clean-directory audit, and frozen-raw clean-directory audit are present for the current release candidate. The clean clone/container audit must still be repeated after the public release tag and DOI are frozen.
- GitHub Actions are present for small CI and manual full-data release audits, but the full raw bundle is intentionally not assumed to exist on every push.
- Some historical Snakemake metadata are missing in the long-lived prepared workspace for early files generated before all rules were formalized; a clean frozen-raw run produces current metadata and a clean dry-run for declared outputs.
- Manual curation artifacts are validated as frozen files; web curation is not automatically regenerated.
- Future re-downloads from live APIs may differ, so the release should prioritize frozen local raw files and checksum manifests over live re-querying.

## Bottom Line

The current package is reviewable and locally auditable. It is not yet formally release-grade 10/10 until the public repository URL, archival DOI, and final tagged-release clean-clone/container audit are completed.
