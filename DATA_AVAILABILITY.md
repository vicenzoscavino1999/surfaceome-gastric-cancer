# Data Availability

This project uses only public, de-identified, aggregate, or open-access research data. No new patient samples, restricted clinical records, or wet-lab data were generated.

## Current Release Status

The code repository is public at https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer. The final code release tag is `v0.1.1`. The frozen reproducibility data package for release candidate `v0.1.0-rc4` is archived on Zenodo at https://zenodo.org/records/20498705 with DOI `10.5281/zenodo.20498705`.

## Raw and Source Data

Retained raw/source files are stored under `data/raw/` in the local release candidate and are registered in:

- `config/datasets.yaml`
- `config/release_manifest.yaml`
- `results/tables/phase2_download_manifest.tsv`
- `docs/provenance_log.tsv`
- `data/checksums/*.tsv`

The main retained raw/source inputs include:

- UCSC Xena/Toil TCGA/GTEx RNA matrix and phenotype files.
- Human Protein Atlas normal IHC, cancer IHC, tissue RNA, GTEx RNA, and subcellular localization downloads.
- UniProt reviewed-human topology, GO, GPI, and expanded feature files.
- GDC TCGA-STAD metadata.
- HGNC complete set.
- TCSA, CSPA, and SURFY surfaceome workbooks.
- cBioPortal TCGA-STAD clinical and selected GISTIC context.
- tidyestimate source/signature inputs.
- TISCH2 candidate-level gastric scRNA context files.
- Wang 2026 open-access supplementary workbook `mmc8.xlsx` for the drug-target-class overlap and matched-null consistency audit.

Future re-downloads from live APIs may differ. The release therefore prioritizes the frozen local raw/source files, checksum manifests, and exact download provenance rather than live re-querying. It does not claim a 100% automatic live-source re-download from zero.

## Frozen API and Manual Captures

The acquisition policy is documented in `docs/source_acquisition_policy.md`.

cBioPortal TCGA-STAD clinical and selected GISTIC files are treated as frozen archived inputs, not default live-download outputs:

- `data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json`
- `data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json`
- `data/checksums/cbioportal_sha256.tsv`

The Zenodo archival DOI covers the frozen input package with checksums and exact provenance for `v0.1.0-rc4`, which is the archived frozen-data companion to the final `v0.1.1` code release. GDC metadata captures, TISCH2 candidate-level scRNA files, Wang 2026 `mmc8.xlsx`, Phase 1 endpoint snapshots, and manual curation files follow the same frozen-input principle. Live refreshes remain best-effort transparency checks only.

The Wang 2026 `mmc8.xlsx` source is cached at `data/raw/wang2026/mmc8.xlsx` and recorded in `data/checksums/wang2026_mmc8_sha256.tsv` because the older Europe PMC supplementary endpoint was unstable during release audit. The fallback retrieval path uses the PubMed Central OA package location recorded by NCBI/PMC, with checksum validation before any derived table is written.

## Processed Data and Results

Processed analysis outputs are stored under:

- `data/processed/`
- `results/rankings/`
- `results/validation/`
- `results/tables/`
- `results/figures/`
- `manuscript/latex/figures/`

The active frozen ranking is `results/rankings/ranking_v2_frozen.tsv` with SHA256:

`95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`

Its file-level freeze metadata is stored separately in `results/rankings/ranking_v2_frozen.metadata.yaml`.

Earlier preserved ranking snapshots are:

- `results/rankings/ranking_v0_frozen.tsv`: pre-normalization-fix snapshot.
- `results/rankings/ranking_v1_frozen.tsv`: pre-GPI-correction snapshot.
- `results/rankings/ranking_v2_frozen.tsv`: active post-GPI-correction snapshot.

## Reproducibility Commands

Install the local audit dependencies:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-manuscript.txt
```

Run the reviewer-facing audit:

```powershell
python scripts/run_reproducibility_checks.py
```

Build a Docker audit runtime:

```powershell
docker build -f docker/Dockerfile -t surfaceome-gastric-cancer-repro .
docker run --rm -v "${PWD}:/work" surfaceome-gastric-cancer-repro
```

The Docker image is a runtime image. It intentionally expects a mounted release checkout at `/work` so large raw/source files are not copied into the image build context.

## Redistribution Notes

This repository contains code and derived outputs generated from public resources. Upstream datasets retain their original terms, licenses, and citation requirements. Users who redistribute a release archive should verify the redistribution terms for large raw/source files and, where appropriate, archive processed outputs and checksum manifests instead of restricted or third-party raw files.
