# Reproducibility Audit Report

Generated: 2026-06-01 13:40:01 UTC

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

- Retained raw/source files: `28`
- Retained raw/source size: `1405116273` bytes (`1.309` GiB)

## Frozen Ranking

- Active ranking: `results/rankings/ranking_v2_frozen.tsv`
- Active ranking SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`
- Active ranking sidecar: `results/rankings/ranking_v2_frozen.metadata.yaml`
- Active ranking sidecar SHA256: `8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee`
- Sidecar-recorded ranking SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`

## Automated Audit

- `scripts/run_reproducibility_checks.py`: `not_run`
- `python -m snakemake --summary`: exit `0`
- `python -m snakemake -n --cores 1`: exit `0`

### Clean/Container Audit Log

| Date | Audit | Status | Key result |
|---|---|---|---|
|  | `current_workspace_reviewer_audit` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do |
|  | `current_workspace_workflow_rerun` | `pass` | Downstream Fase 13 diagnostics, Wang overlap, Fase 14, Fase 16, GPI impact, TISCH2 annotation, and external baseline rules completed after release-format sidecar hardening |
|  | `clean_directory_forced_phase13_to_17` | `pass` | Forced Fase 13 to Fase 17 downstream rerun completed; key hashes matched the main workspace, including ranking_v2_frozen SHA256 95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631 and sidecar SHA256 8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee |
|  | `clean_directory_reviewer_audit` | `pass` | 13 unit tests passed; all phase checks through Fase 16 passed; CBC manuscript check passed; publication figure check passed; Snakemake dry-run reported nothing to do |
|  | `docker_reviewer_audit` | `pass` | Containerized reviewer audit passed after release-format sidecar hardening with Python 3.12.4 and requirements-lock.txt runtime |

### Snakemake Dry Run Output

```text
host: LAPTOP-V5GPBKB5
Building DAG of jobs...
Nothing to be done (all requested files are present and up to date).
6 jobs have missing provenance/metadata so that it in part cannot be used to trigger re-runs.
Rules with missing metadata: bootstrap_status phase1_inventory phase2_batch_diagnostic phase2_downloads phase3_identifier_map phase4_surfaceome_universe
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
data/raw/xena_toil/TcgaTargetGTEX_phenotype.txt.gz	Thu May 28 08:02:02 2026	phase2_downloads	-	ok	no update
data/raw/xena_toil/TcgaTargetGtex_rsem_gene_tpm.gz	Thu May 28 08:06:01 2026	phase2_downloads	-	ok	no update
data/raw/hpa/normal_ihc_data.tsv.zip	Thu May 28 08:06:04 2026	phase2_downloads	-	ok	no update
data/raw/hpa/cancer_data.tsv.zip	Thu May 28 08:06:07 2026	phase2_downloads	-	ok	no update
data/raw/hpa/subcellular_location.tsv.zip	Thu May 28 08:06:09 2026	phase2_downloads	-	ok	no update
data/raw/hpa/rna_tissue_consensus.tsv.zip	Thu May 28 08:06:12 2026	phase2_downloads	-	ok	no update
data/raw/hpa/rna_tissue_gtex.tsv.zip	Thu May 28 08:06:15 2026	phase2_downloads	-	ok	no update
data/raw/uniprot/uniprot_reviewed_human_topology.tsv.gz	Thu May 28 08:06:36 2026	phase2_downloads	-	ok	no update
data/raw/gdc_tcga_stad/cases_tcga_stad.json	Thu May 28 08:06:40 2026	phase2_downloads	-	ok	no update
data/raw/gdc_tcga_stad/files_tcga_stad_rnaseq_star_counts.json	Thu May 28 08:06:41 2026	phase2_downloads	-	ok	no update
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
data/raw/hgnc/hgnc_complete_set.txt	Thu May 28 12:45:03 2026	phase3_identifier_map	-	ok	no update
data/checksums/hgnc_sha256.tsv	Thu May 28 12:46:52 2026	phase3_identifier_map	-	ok	no update
data/processed/id_map_master.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/mapping_failures.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/control_identifier_mapping.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
results/tables/id_source_coverage.tsv	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
docs/fase3_identifier_normalization.md	Thu May 28 12:47:37 2026	phase3_identifier_map	-	ok	no update
data/raw/surfaceome/tcsa_supplementary_tables_1_40.xlsx	Thu May 28 13:12:24 2026	phase4_surfaceome_universe		ok	no update
data/raw/surfaceome/cspa_pone_0121314_s003.xlsx	Thu May 28 13:12:24 2026	phase4_surfaceome_universe		ok	no update
data/raw/surfaceome/surfy_table_s3_surfaceome.xlsx	Thu May 28 13:12:24 2026	phase4_surfaceome_universe		ok	no update
data/raw/uniprot/uniprot_reviewed_human_go.tsv.gz	Thu May 28 13:12:24 2026	phase4_surfaceome_universe		ok	no update
data/raw/uniprot/uniprot_reviewed_human_gpi.tsv.gz	Sat May 30 20:14:14 2026	phase4_surfaceome_universe	-	ok	no update
data/checksums/surfaceome_sources_sha256.tsv	Sat May 30 20:17:55 2026	phase4_surfaceome_universe		ok	no update
data/checksums/sha256sums.txt	Mon Jun  1 08:39:43 2026	phase4_surfaceome_universe		ok	no update
data/processed/surfaceome_universe.tsv	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_confidence_summary.tsv	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_jaccard_with_published_lists.tsv	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/tables/surfaceome_false_positive_false_negative_audit.tsv	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/figures/surfaceome_source_overlap.svg	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/figures/surfaceome_jaccard_with_published_lists.svg	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
docs/fase4_surfaceome_universe.md	Sat May 30 20:18:05 2026	phase4_surfaceome_universe		ok	no update
results/validation/ranking_resolution_simulation.tsv	Sat May 30 20:30:09 2026	phase4b_ranking_resolution		ok	no update
results/validation/ranking_resolution_summary.tsv	Sat May 30 20:30:09 2026	phase4b_ranking_resolution		ok	no update
results/figures/rank_ci_by_coverage.svg	Sat May 30 20:30:09 2026	phase4b_ranking_resolution		ok	no update
docs/fase4b_ranking_resolution.md	Sat May 30 20:30:09 2026	phase4b_ranking_resolution		ok	no update
data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
data/checksums/cbioportal_sha256.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
data/processed/tumor_expression.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/figures/tumor_expression_distribution.svg	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_expression.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_sample_counts.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/subtype_power_analysis.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/clinical_covariate_expression.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/clinical_covariate_sample_counts.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/fase5_covariate_availability.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
results/tables/amplified_target_cna_expression.tsv	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
docs/fase5_tumor_expression.md	Sat May 30 20:26:45 2026	phase5_tumor_expression		ok	no update
data/processed/normal_expression.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
data/processed/selectivity_scores.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
data/processed/off_tumor_risk.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
data/processed/organ_penalties.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
data/processed/tumor_normal_tests.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
results/tables/tumor_normal_power_analysis.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
results/tables/normal_tissue_sample_counts.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
results/tables/hpa_normal_protein_by_organ.tsv	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
results/figures/tumor_vs_normal_critical.svg	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
results/figures/tumor_normal_power_curve.svg	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
docs/fase6_normal_selectivity_risk.md	Sat May 30 20:30:03 2026	phase6_normal_selectivity		ok	no update
data/processed/protein_evidence.tsv	Sat May 30 20:30:22 2026	phase7_protein_evidence		ok	no update
results/tables/protein_coverage.tsv	Sat May 30 20:30:22 2026	phase7_protein_evidence		ok	no update
results/figures/rna_protein_concordance.svg	Sat May 30 20:30:22 2026	phase7_protein_evidence		ok	no update
docs/fase7_protein_evidence.md	Sat May 30 20:30:22 2026	phase7_protein_evidence		ok	no update
data/raw/tcga_purity/tidyestimate_1.1.1.tar.gz	Sat May 30 20:28:40 2026	phase8_single_cell_tme		ok	no update
data/raw/tcga_purity/tidyestimate/data/gene_sets.rda	Sat May 30 20:28:40 2026	phase8_single_cell_tme		ok	no update
data/checksums/tcga_purity_sha256.tsv	Sun May 31 19:49:47 2026	phase8_single_cell_tme		ok	no update
data/processed/single_cell_specificity.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_contamination_flags.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_contamination_risk_mvp.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_purity_adjusted_correlations.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_purity_suppression_audit.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_module_correlations.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_module_marker_coverage.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tme_estimate_marker_overlap.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/tables/tumor_purity_estimate_scores.tsv	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
results/figures/top_candidates_scRNA_dotplot.svg	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
docs/fase8_single_cell_tme_specificity.md	Sun May 31 19:51:45 2026	phase8_single_cell_tme		ok	no update
data/raw/uniprot/uniprot_reviewed_human_features.tsv.gz	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
data/checksums/uniprot_phase9_features_sha256.tsv	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
data/processed/topology_isoforms_ecd.tsv	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
results/tables/isoform_risk_flags.tsv	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
results/figures/ecd_length_distribution.svg	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
docs/fase9_topology_isoforms.md	Sat May 30 20:30:42 2026	phase9_topology_isoforms		ok	no update
results/tables/component_scores_all_candidates.tsv	Mon Jun  1 08:35:15 2026	phase13_mvp_scoring		ok	no update
results/tables/tiering_annotations_all_candidates.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/tables/control_recovery_phase13.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_balanced.tsv	Mon Jun  1 08:35:15 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_safety_first.tsv	Mon Jun  1 08:35:15 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_adc_focused.tsv	Mon Jun  1 08:35:15 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_novelty.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_protein_first.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_robust_aggregate.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v2_frozen.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/rankings/ranking_v2_frozen.metadata.yaml	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/validation/functional_form_sensitivity.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
results/validation/phase13_post_scoring_sanity.tsv	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
docs/fase13_mvp_score_integration.md	Mon Jun  1 08:35:16 2026	phase13_mvp_scoring		ok	no update
docs/fase13
```

## Remaining Release Blockers

- Public repository URL is still required.
- Archival DOI is still required.
- A clean clone or clean directory audit should be repeated after the release candidate is frozen.
- Docker build/run should be repeated on the final public release package.
- Manuscript and cover letter still need the final repository URL and archival DOI.
