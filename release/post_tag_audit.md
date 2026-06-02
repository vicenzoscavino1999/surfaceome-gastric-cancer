# Post-Tag Reproducibility Audit

Audit date: 2026-06-02. Auditor: pre-submission self-audit (single operator, no third party yet).

This artifact records the reproducibility state **after** the public release tag and archival DOI
were created, because that audit is necessarily generated after the commit tree is frozen. It is the
record requested by the open item in `release/release_checklist.md`.

## Release identity verified

- Public code release tag `v0.1.1` resolves to commit `19f30fa09b8161071ca4aca67ee2dcb9246337fe`.
- GitHub repository is public: https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer
  (tag `v0.1.1` is the latest release; LICENSE present).
- Zenodo archival DOI `10.5281/zenodo.20498705` resolves to the frozen reproducibility data package
  for `v0.1.0-rc4` (~1.4 GB zip + SHA256 sidecar). Confirmed live on the audit date.
- Active frozen ranking `results/rankings/ranking_v2_frozen.tsv` SHA256 recomputed as
  `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`, matching the value stated in
  `DATA_AVAILABILITY.md` and the manuscript.

## What passed

- Full reviewer audit `python scripts/run_reproducibility_checks.py` passes on the populated
  reference workspace (Windows / win32, CPython 3.12.4): unit tests, all Fase 1-16 artifact checks,
  the CBC manuscript check, the publication-figure check, and the Snakemake dry-run (`Nothing to be
  done`).

## Clean-checkout finding for tag v0.1.1

A clean checkout of tag `v0.1.1` (via `git worktree add --detach <dir> v0.1.1`, equivalent to a fresh
`git clone` of the tag) was tested with no external data downloaded. Result:

- The checkout contains code, configuration, the 71 tracked `results/` tables, and tracked
  `data/processed/` tables, with a clean `git status`.
- `python scripts/run_reproducibility_checks.py` **aborts at `--check-phase2-downloads`** with a
  non-zero exit, because `data/raw/*` is gitignored and therefore absent from the repository
  (missing Xena/Toil TPM + phenotype, HPA zips, UniProt topology, GDC metadata, etc.).

**Implication:** the documented "shortest reviewer path" does not run end-to-end from a bare clone.
A reviewer must first download the Zenodo data package and populate `data/raw/`. This is now stated
up front in `README.md`.

## Post-tag main mitigation

On post-tag `main`, `scripts/run_reproducibility_checks.py` now has `auto`, `full`, and `smoke`
modes. A bare clone without `data/raw/` runs a no-raw smoke audit that verifies the frozen ranking
hash, release-input wiring, no-data unit tests, and tracked phase artifacts, then explicitly lists
the full-data checks that require the Zenodo bundle. With `data/raw/` populated, the same command
runs the full audit. This improves reviewer ergonomics on `main`; it does not change the already
published `v0.1.1` tag or Zenodo DOI.

## Still open (honest residual)

- [ ] Run the full audit from a fresh clone of `v0.1.1` **plus** the Zenodo `data/raw/` bundle on a
      **Linux/container** runtime, and record the result + the `ranking_v2_frozen.tsv` hash there.
      Bit-for-bit reproduction is so far demonstrated only on the author's win32 reference machine;
      `docs/nondeterminism_inventory.md` notes BLAS/LAPACK and cross-architecture floating-point
      differences may perturb tolerance-validated numeric outputs (PCA/PERMANOVA/power sims).
- [ ] Independent third-party reproduction (any operator other than the author).
- [x] Post-tag `main` makes `scripts/run_reproducibility_checks.py` degrade gracefully without
      `data/raw/` by running a no-raw smoke audit and listing skipped full-data checks.

## Note on repository state at audit time

The published artifacts (`v0.1.1` tag and the `10.5281/zenodo.20498705` DOI) are frozen and stable.
The local `main` branch has advanced past the tag with post-release commits; those do not change the
published release or DOI. If the no-raw smoke-audit mitigation should become a tagged release
feature, create a later code tag from the updated `main`.
