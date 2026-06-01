# Non-Determinism Inventory

Status: active after preliminary Fase 13 scoring and before final tiering.

This inventory documents outputs that may vary across platforms, dependency versions, BLAS/LAPACK implementations, API changes, or stochastic simulations. Scientific outputs must be validated with declared tolerances rather than by assuming binary-identical files across all environments.

| Source | Affected outputs | Mitigation | Residual risk |
|---|---|---|---|
| Floating-point differences across architectures | PCA coordinates, PERMANOVA distances, simulated rank summaries, future scores | Numeric tolerances in `config/parameters.yaml`; deterministic seeds where applicable | Small low-order numeric differences can remain across OS/CPU/runtime |
| Stochastic simulations | Fase 4B rank-resolution simulation, Fase 5 subtype power simulation, Fase 6 tumor-normal power simulation, future perturbation/bootstrap/missing-data sensitivity | Seeds declared in `config/parameters.yaml`; seed and simulation counts reported in output notes/tables | Results are reproducible only with same code, seed, input data, and compatible dependency versions |
| Ranking ties | Future score rankings and tier assignments | Component percentile transforms use average-rank ties where tied values are biologically identical; final ranking sorts use stable deterministic HGNC tie-break only after numeric scores are computed | None if tie handling is implemented consistently |
| Fase 13 freeze metadata | `results/rankings/ranking_v0_frozen.tsv`; `results/rankings/ranking_v1_frozen.tsv`; `results/rankings/ranking_v2_frozen.tsv`; `results/rankings/ranking_v2_frozen.metadata.yaml` | Scientific rank values are deterministic over frozen inputs/config; v0 is preserved as the pre-fix bug snapshot, v1 as the pre-GPI snapshot, and active v2 file-level metadata is stored in a sidecar rather than repeated per ranking row | Active v2 ranking-table reruns should be bitwise-identical for ranking/scoring content; the sidecar records generation metadata and the release-commit policy, while the containing clean Git commit/tag defines the exact release file tree |
| Python dict/set iteration order | Any output built from unordered collections | Use sorted iteration for outputs where order matters | None for outputs already sorted before writing |
| BLAS/LAPACK implementation | PCA and future linear algebra operations | Treat PCA numeric outputs as tolerance-validated; final release should pin runtime in lockfile/Docker | Small coordinate sign or low-order differences can occur |
| Snakemake parallel execution order | Logs and timestamps | Scientific outputs are per-rule deterministic; logs are not compared as scientific outputs | Log ordering may differ and is not interpreted biologically |
| API response format changes | Download scripts and metadata capture | Raw files are frozen locally with checksums; `config/datasets.yaml` records URL/version/date; `docs/source_acquisition_policy.md` declares cBioPortal/GISTIC, GDC metadata, TISCH2, Wang, endpoint snapshots, and manual curation as frozen inputs | Future re-download can fail or differ if APIs change, but frozen raw analysis remains reproducible |
| Workbook parser warnings | Surfaceome Excel supplementary parsing | Fase 4 outputs are validated by control audits and output checks | Parser/library upgrades may alter warning text, not expected biological output |

## Current Deterministic Outputs

- Fase 4B uses `random.rank_resolution_seed=20260531` and `ranking_resolution.n_simulations=500`.
- Fase 5 subtype power analysis uses `random.subtype_power_seed=20260602` and 200 simulations per effect-size grid point.
- Fase 6 tumor-normal power analysis uses `random.tumor_normal_power_seed=20260603` and 200 simulations per effect-size grid point.
- Fase 8 TME marker-module fallback uses deterministic Spearman correlations and ESTIMATE/tidyestimate partial Spearman correlations over frozen Xena/Toil TCGA-STAD primary tumor samples; `SC` is not imputed.
- Fase 9 topology/isoform outputs are deterministic over the frozen UniProt Fase 9 feature TSV checksum; future re-downloads can differ if UniProt updates entries or feature formatting.
- Fase 13 preliminary score rankings are deterministic over frozen Fase 4-9 component tables and `config/scoring_scenarios.yaml`; active v2 `Surf_relative_confidence` uses the fixed theoretical Fase 4 scale `[5,10]` after confirmed UniProt GPI-anchor evidence correction, internal Fase 13 percentiles use average-rank ties, and final exact score ties use HGNC symbol ordering.
- Raw-file integrity is checked by `data/checksums/sha256sums.txt`.
- Fase checks are implemented in `src/utils/compare_outputs.py`.
- Current release-candidate clean-directory audit forced Fase 13->17 rerun and reproduced key output hashes bit-for-bit, including `ranking_v2_frozen.tsv`.
- GitHub Actions push/PR CI covers syntax lint, `pytest`, a small frozen-target Snakemake dry-run, and Docker image build; full reviewer/container/frozen-raw audits are manual jobs requiring the frozen data bundle.

## Pending Before Final Release

- Repeat the clean clone/container audit after the final public tag and archival DOI are frozen.
- Ensure the archival DOI covers the frozen inputs or an equivalent checksum/provenance data package.
- Treat any full all-rules live-source redownload after public release freeze as best-effort only.
