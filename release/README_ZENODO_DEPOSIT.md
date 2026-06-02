# Zenodo Frozen Data Deposit

This workflow archives the frozen raw/source data package separately from the GitHub code
release. Use it for the DOI that backs the manuscript's data-availability statement.

Current production record: https://zenodo.org/records/20498705, DOI `10.5281/zenodo.20498705`.
It contains the `v0.1.0-rc4` frozen data package ZIP and `.sha256` checksum.

## 1. Build The Local Package

```powershell
python scripts/build_frozen_data_package.py --code-tag v0.1.0-rc4
```

Outputs are written under `release/archive/`, which is intentionally ignored by Git:

- `surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip`
- `surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip.sha256`
- `surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zenodo_metadata.json`
- `surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.package_manifest.json`

The ZIP includes `data/raw/`, `data/checksums/`, release/provenance documentation,
`SHA256SUMS.txt`, `package_manifest.json`, and `ZENODO_METADATA.json`.

## 2. Create A Zenodo Token

In Zenodo, create a personal access token with deposit permissions. Keep it local and do not
commit it.

```powershell
$env:ZENODO_ACCESS_TOKEN = "paste-token-here"
```

For a trial run, use a Sandbox token from `https://sandbox.zenodo.org`.

## 3. Test The Upload Plan Locally

```powershell
python scripts/zenodo_upload_frozen_data_package.py `
  release/archive/surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip `
  --dry-run
```

## 4. Optional Sandbox Draft

```powershell
python scripts/zenodo_upload_frozen_data_package.py `
  release/archive/surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip `
  --sandbox
```

This creates an unpublished Zenodo Sandbox draft, uploads the ZIP and checksum file, and prints
the draft URL and reserved DOI.

## 5. Production Draft

```powershell
python scripts/zenodo_upload_frozen_data_package.py `
  release/archive/surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip
```

The script does not publish by default. Review the draft in Zenodo first, especially:

- title
- creator and ORCID
- resource type: dataset
- license: Other (Open)
- related GitHub release
- archive ZIP and `.sha256` checksum file
- reserved DOI

## 6. Publish Only After Review

Publishing is permanent enough that the script requires an explicit confirmation string:

```powershell
python scripts/zenodo_upload_frozen_data_package.py `
  release/archive/surfaceome_gastric_cancer_v0.1.0-rc4_frozen_data_package.zip `
  --deposition-id ZENODO_DRAFT_ID `
  --skip-upload `
  --publish `
  --confirm-publish PUBLISH_ZENODO_RECORD
```

After publication, insert the DOI into:

- `DATA_AVAILABILITY.md`
- `REPRODUCIBILITY.md`
- `README.md`
- `config/release_manifest.yaml`
- `manuscript/cbc_manuscript_scaffold.md`
- `manuscript/cbc_cover_letter_draft.md`
- `manuscript/cbc_submission_route_blockers.md`

Then cut the final clean release tag.
