# Reproducibility Audit Report

Generated: 2026-06-01 19:48:22 UTC

## Scope

This report audits the current release-candidate workspace. It does not change scores,
weights, universe membership, rankings, tiers, or manuscript figures.

## Environment

- Python: `3.12.4`
- Platform: `Windows-11-10.0.22621-SP0`
- Docker: `Docker version 27.5.1, build 9f9e405`

### Key Package Versions

- matplotlib: `3.9.0`
- numpy: `2.2.1`
- openpyxl: `3.1.5`
- pandas: `2.2.2`
- pyreadr: `0.5.6`
- PyMuPDF: `1.27.2.3`
- PyYAML: `6.0.3`
- requests: `2.32.3`
- scikit-learn: `1.5.1`
- scipy: `1.15.1`
- pytest: `9.0.3`
- snakemake: `9.21.0`

## Repository State

- Exact release tree: defined by the clean Git commit or tag that contains this report.
- The literal release commit hash is not embedded in this tracked report because doing so would make the report self-referential.
- Verify the release tree after checkout with `git status --short`; it should return no tracked changes.

## Data Footprint

- Retained raw/source files: `41`
- Retained raw/source size: `1408380242` bytes (`1.312` GiB)

## Frozen Ranking

- Active ranking: `results/rankings/ranking_v2_frozen.tsv`
- Active ranking SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`
- Active ranking sidecar: `results/rankings/ranking_v2_frozen.metadata.yaml`
- Active ranking sidecar SHA256: `8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee`
- Sidecar-recorded ranking SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`

## Automated Audit

- `scripts/run_reproducibility_checks.py`: `pass`
- `python -m snakemake --summary`: exit `0`
- `python -m snakemake -n --cores 1`: exit `0`

### Clean/Container Audit Log

| Date | Audit | Status | Key result |
|---|---|---|---|
| 2026-06-01 | `current_workspace_reviewer_audit` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do |
| 2026-06-01 | `current_workspace_workflow_rerun` | `pass` | Downstream Fase 13 diagnostics, Wang overlap, Fase 14, Fase 16, GPI impact, TISCH2 annotation, and external baseline rules completed after release-format sidecar hardening |
| 2026-06-01 | `clean_directory_forced_phase13_to_17` | `pass` | Forced Fase 13 to Fase 17 downstream rerun completed; key hashes matched the main workspace, including ranking_v2_frozen SHA256 95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631 and sidecar SHA256 8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee |
| 2026-06-01 | `clean_directory_reviewer_audit` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do |
| 2026-06-01 | `docker_reviewer_audit` | `pass` | Containerized reviewer audit passed after release-format sidecar hardening with Python 3.12.4 and requirements-lock.txt runtime |
| 2026-06-01 | `clean_directory_frozen_raw_recompute` | `pass` | Clean copy preserved data/raw, deleted derived outputs, and completed the declared Fase 1->17 workflow; Fase 1 used frozen inventory snapshots and raw/source files were treated as inputs rather than disposable outputs |
| 2026-06-01 | `clean_directory_frozen_raw_reviewer_audit` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do |
| 2026-06-01 | `clean_directory_frozen_raw_hash_compare` | `pass` | Frozen-raw outputs matched the main workspace bit-for-bit for ranking_v2_frozen.tsv 95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631, sidecar 8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee, component_scores_all_candidates.tsv, manuscript_table3_top_candidates.tsv, tier_assignments.tsv, supplementary_table_manifest.tsv, and manuscript_publication_figure_manifest.tsv |
| 2026-06-01 | `current_workspace_reviewer_audit_after_frozen_raw_hardening` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do, with historical metadata warnings for five early long-lived rules only |

### Snakemake Dry Run Output

```text
host: LAPTOP-V5GPBKB5
Building DAG of jobs...
Nothing to be done (all requested files are present and up to date).
5 jobs have missing provenance/metadata so that it in part cannot be used to trigger re-runs.
Rules with missing metadata: bootstrap_status phase1_inventory phase2_batch_diagnostic phase2_downloads phase3_identifier_map
```

### Snakemake Summary Output

```text
Building DAG of jobs...
output_file	date	rule	log-file(s)	status	plan
results/tables/bootstrap_status.tsv	Sun May 31 19:58:54 2026	bootstrap_status	-	ok	no update
results/tables/dataset_inventory.tsv	Thu May 28 07:47:25 2026	phase1_inventory	-	ok	no update
results/tables/sample_counts.tsv	Thu May 28 07:47:25 2026	phase1_inventory	-	ok	no update
results/tables/coverage_matrix.tsv	Thu May 28 07:47:25 2026	phase1_inventory	-	ok	no update
docs/fase1_data_inventory.md	Thu May 28 07:47:25 2026	phase1_inventory	-	ok	no update
results/tables/phase2_download_manifest.tsv	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
data/checksums/xena_toil_sha256.tsv	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
data/checksums/hpa_sha256.tsv	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
data/checksums/uniprot_sha256.tsv	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
data/checksums/gdc_tcga_stad_sha256.tsv	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
docs/fase2_data_acquisition.md	Thu May 28 08:12:37 2026	phase2_downloads	-	ok	no update
results/figures/pca_batch_diagnostic.svg	Thu May 28 08:11:17 2026	phase2_batch_diagnostic	-	ok	no update
results/tables/batch_permanova.tsv	Thu May 28 08:11:19 2026	phase2_batch_diagnostic	-	ok	no update
results/tables/xena_batch_diagnostic_samples.tsv	Thu May 28 08:11:17 2026	phase2_batch_diagnostic	-	ok	no update
results/tables/xena_top_variable_genes.tsv	Thu May 28 08:11:17 2026	phase2_batch_diagnostic	-	ok	no update
docs/fase2_batch_diagnostic.md	Thu May 28 08:11:19 2026	phase2_batch_diagnostic	-	ok	no update
data/checksums/hgnc_sha256.tsv	Thu May 28 12:46:52 2026	phase3_identifier_map	-	ok	no update
data/processed/id_map_master.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/mapping_failures.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/control_identifier_mapping.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/id_source_coverage.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
docs/fase3_identifier_normalization.md	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
data/checksums/surfaceome_sources_sha256.tsv	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
data/checksums/sha256sums.txt	Mon Jun  1 14:17:43 2026	phase4_surfaceome_universe		ok	no update
data/processed/surfaceome_universe.tsv	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_confidence_summary.tsv	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_jaccard_with_published_lists.tsv	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_false_positive_false_negative_audit.tsv	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/figures/surfaceome_source_overlap.svg	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/figures/surfaceome_jaccard_with_published_lists.svg	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
docs/fase4_surfaceome_universe.md	Mon Jun  1 09:34:22 2026	phase4_surfaceome_universe		ok	no update
results/validation/ranking_resolution_simulation.tsv	Mon Jun  1 09:34:25 2026	phase4b_ranking_resolution		ok	no update
results/validation/ranking_resolution_summary.tsv	Mon Jun  1 09:34:25 2026	phase4b_ranking_resolution		ok	no update
results/figures/rank_ci_by_coverage.svg	Mon Jun  1 09:34:25 2026	phase4b_ranking_resolution		ok	no update
docs/fase4b_ranking_resolution.md	Mon Jun  1 09:34:25 2026	phase4b_ranking_resolution		ok	no update
data/checksums/cbioportal_sha256.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
data/processed/tumor_expression.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/figures/tumor_expression_distribution.svg	Mon Jun  1 14:20:29 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_expression.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_sample_counts.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_power_analysis.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/clinical_covariate_expression.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/clinical_covariate_sample_counts.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/fase5_covariate_availability.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
results/tables/amplified_target_cna_expression.tsv	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
docs/fase5_tumor_expression.md	Mon Jun  1 14:13:48 2026	phase5_tumor_expression		ok	no update
data/processed/normal_expression.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
data/processed/selectivity_scores.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
data/processed/off_tumor_risk.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
data/processed/organ_penalties.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
data/processed/tumor_normal_tests.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
results/tables/tumor_normal_power_analysis.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
results/tables/normal_tissue_sample_counts.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
results/tables/hpa_normal_protein_by_organ.tsv	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
results/figures/tumor_vs_normal_critical.svg	Mon Jun  1 14:20:29 2026	phase6_normal_selectivity		ok	no update
results/figures/tumor_normal_power_curve.svg	Mon Jun  1 14:20:29 2026	phase6_normal_selectivity		ok	no update
docs/fase6_normal_selectivity_risk.md	Mon Jun  1 14:16:32 2026	phase6_normal_selectivity		ok	no update
data/processed/protein_evidence.tsv	Mon Jun  1 14:16:41 2026	phase7_protein_evidence		ok	no update
results/tables/protein_coverage.tsv	Mon Jun  1 14:16:41 2026	phase7_protein_evidence		ok	no update
results/figures/rna_protein_concordance.svg	Mon Jun  1 14:20:29 2026	phase7_protein_evidence		ok	no update
docs/fase7_protein_evidence.md	Mon Jun  1 14:16:41 2026	phase7_protein_evidence		ok	no update
data/checksums/tcga_purity_sha256.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
data/processed/single_cell_specificity.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_contamination_flags.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_contamination_risk_mvp.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_purity_adjusted_correlations.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_purity_suppression_audit.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_module_correlations.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_module_marker_coverage.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_estimate_marker_overlap.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/tables/tumor_purity_estimate_scores.tsv	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
results/figures/top_candidates_scRNA_dotplot.svg	Mon Jun  1 14:20:29 2026	phase8_single_cell_tme		ok	no update
docs/fase8_single_cell_tme_specificity.md	Mon Jun  1 14:15:23 2026	phase8_single_cell_tme		ok	no update
data/checksums/uniprot_phase9_features_sha256.tsv	Mon Jun  1 14:16:46 2026	phase9_topology_isoforms		ok	no update
data/processed/topology_isoforms_ecd.tsv	Mon Jun  1 14:16:46 2026	phase9_topology_isoforms		ok	no update
results/tables/isoform_risk_flags.tsv	Mon Jun  1 14:16:46 2026	phase9_topology_isoforms		ok	no update
results/figures/ecd_length_distribution.svg	Mon Jun  1 14:16:46 2026	phase9_topology_isoforms		ok	no update
docs/fase9_topology_isoforms.md	Mon Jun  1 14:16:46 2026	phase9_topology_isoforms		ok	no update
results/tables/component_scores_all_candidates.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/tables/tiering_annotations_all_candidates.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/tables/control_recovery_phase13.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_balanced.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_safety_first.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_adc_focused.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_novelty.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_protein_first.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_robust_aggregate.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v0_frozen.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v1_frozen.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v2_frozen.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v2_frozen.metadata.yaml	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/validation/functional_form_sensitivity.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
results/validation/phase13_post_scoring_sanity.tsv	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
docs/fase13_mvp_score_integration.md	Mon Jun  1 14:16:49 2026	phase13_mvp_scoring		ok	no update
docs/fase13_diagnostico.md	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_diagnostic_snapshot_hashes.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_component_transform_audit.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_surfaceome_tie_groups.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_gpi_anchor_surf_audit.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_positive_control_component_diagnostic.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_positive_control_causal_gate.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
results/tables/fase13_v0_v1_rank_delta.tsv	Mon Jun  1 14:16:49 2026	phase13_diagnostic		ok	no update
docs/fase13_gpi_membership_route.md	Mon Jun  1 09:36:12 2026	phase13_gpi_membership_route		ok	no update
results/tables/fase13_gpi_membership_route_audit.tsv	Mon Jun  1 09:36:12 2026	phase13_gpi_membership_route		ok	no update
results/tables/fase13_gpi_membership_route_summary.tsv	Mon Jun  1 09:36:12 2026	phase13_gpi_membership_route		ok	no update
docs/fase14_preflight.md	Mon Jun  1 14:16:50 2026	phase14_preflight		ok	no update
results/tables/fase14_preflight_top50_v1_v2_audit.tsv	Mon Jun  1 14:16:50 2026	phase14_preflight		ok	no update
results/tables/fase14_preflight_snapshot_integrity.tsv	Mon Jun  1 14:16:50 2026	phase14_preflight		ok	no update
results/tables/fase14_preflight_universe_stability.tsv	Mon Jun  1 14:16:50 2026	phase14_preflight		ok	no update
docs/fase14_rank_stability.md	Mon Jun  1 14:17:29 2026	phase14_stability		ok	no update
results/validation/rank_stability.tsv	Mon Jun  1 14:17:29 2026	phase14_stability		ok	no update
results/validation/leave_one_layer_out.tsv	Mon Jun  1 14:17:29 2026	phase14_stability		ok	no update
results/validation/weight_perturbation_summary.tsv	Mon Jun  1 14:17:29 2026	phase14_stability		ok	no update
results/validation/risk_threshold_sensitivity.tsv	Mon Jun  1 14:17:29 2026	phase14_stability		ok	no update
results/validation/risk_functiona
```

## Remaining Release Blockers

- Public repository URL: https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer.
- Archival DOI is still required and must cover frozen inputs or an equivalent checksum/provenance data package.
- A clean clone/container audit should be repeated after the public release-candidate tag is created.
- Docker build/run should be repeated on the frozen public release tag.
- Manual GitHub Actions release-audit jobs should be repeated when the final frozen data bundle is available to the runner.
- Manuscript and cover letter include the public repository URL; they still need the final archival DOI.

### Reproducibility Check Output

```text
== unit tests ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe -m pytest -q
.............                                                            [100%]
13 passed in 5.68s

== artifact check --self-test ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --self-test
Bootstrap check passed.

== artifact check --check-phase1-inventory ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase1-inventory
Fase 1 inventory check passed.

== artifact check --check-phase2-downloads ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase2-downloads
Fase 2 download check passed.

== artifact check --check-phase2-batch-diagnostic ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase2-batch-diagnostic
Fase 2 batch diagnostic check passed.

== artifact check --check-phase3-identifier-map ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase3-identifier-map
Fase 3 identifier map check passed.

== artifact check --check-phase4-surfaceome-universe ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase4-surfaceome-universe
Fase 4 surfaceome universe check passed.

== artifact check --check-phase4b-ranking-resolution ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase4b-ranking-resolution
Fase 4B ranking-resolution check passed.

== artifact check --check-phase5-tumor-expression ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase5-tumor-expression
Fase 5 tumor-expression check passed.

== artifact check --check-phase6-normal-selectivity ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase6-normal-selectivity
Fase 6 normal-selectivity check passed.

== artifact check --check-phase7-protein-evidence ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase7-protein-evidence
Fase 7 protein-evidence check passed.

== artifact check --check-phase8-single-cell-tme ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase8-single-cell-tme
Fase 8 single-cell/TME check passed.

== artifact check --check-phase9-topology-isoforms ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase9-topology-isoforms
Fase 9 topology/isoforms check passed.

== artifact check --check-phase13-mvp-scoring ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase13-mvp-scoring
Fase 13 MVP scoring check passed.

== artifact check --check-phase14-preflight ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase14-preflight
Fase 14 preflight check passed.

== artifact check --check-phase14-stability ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase14-stability
Fase 14 stability check passed.

== artifact check --check-phase15-tiering ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase15-tiering
Fase 15 tiering check passed.

== artifact check --check-phase16-figures-tables ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe src/utils/compare_outputs.py --check-phase16-figures-tables
Fase 16 figures/tables check passed.

== phase 17 manuscript check ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe scripts/check_phase17_manuscript_brief.py
Fase 17 CBC manuscript check passed.

== publication figure export check ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe scripts/export_phase17_publication_figures.py --check
Phase 17 publication figure export check passed.

== snakemake dry run ==
C:\Users\Vicenzo\AppData\Local\Programs\Python\Python312\python.exe -m snakemake -n --cores 1
host: LAPTOP-V5GPBKB5
Building DAG of jobs...
Nothing to be done (all requested files are present and up to date).
5 jobs have missing provenance/metadata so that it in part cannot be used to trigger re-runs.
Rules with missing metadata: bootstrap_status phase1_inventory phase2_batch_diagnostic phase2_downloads phase3_identifier_map

All requested reproducibility checks passed.
```
