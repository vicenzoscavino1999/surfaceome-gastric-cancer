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

To write a local release audit report:

```powershell
python scripts/build_release_audit_report.py
```

The current release candidate has been checked both in Docker and in a clean directory copy. In the clean copy, `python -m snakemake --cores 1 --forcerun phase13_mvp_scoring` completed through the downstream Fase 13->17 rules, and key outputs matched the main workspace bit-for-bit, including the active ranking hash.

## Manual Traceability Checks

- Central claim map: `docs/fase17_claim_traceability.md`.
- Analysis decisions: `docs/analytical_decisions_registry.md`.
- Reviewer-risk register: `docs/reviewer_attack_surface.md`.
- Non-determinism inventory: `docs/nondeterminism_inventory.md`.
- Data/code availability wording: `manuscript/cbc_manuscript_scaffold.md`, section `Data and code availability`.
- Submission blockers: `manuscript/cbc_submission_route_blockers.md`.

## Current Limitations

- A public repository URL and archival DOI are still pending; those must be inserted before formal submission.
- A Dockerfile, full transitive environment lockfile, Docker audit, and clean-directory audit are present for the current release candidate. The clean clone/container audit must still be repeated after the public release tag and DOI are frozen.
- Some historical Snakemake metadata are missing for early files generated before all rules were formalized; the dry-run is still clean for the current declared outputs.
- Manual curation artifacts are validated as frozen files; web curation is not automatically regenerated.
- Future re-downloads from live APIs may differ, so the release should prioritize frozen local raw files and checksum manifests over live re-querying.

## Bottom Line

The current package is reviewable and locally auditable. It is not yet formally release-grade 10/10 until the public repository URL, archival DOI, and final tagged-release clean-clone/container audit are completed.
