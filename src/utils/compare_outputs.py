"""Minimal reproducibility helpers for early execution gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import yaml


REQUIRED_BOOTSTRAP_FILES = [
    "README.md",
    "REPRODUCIBILITY.md",
    "Makefile",
    "config/controls.yaml",
    "config/scoring_scenarios.yaml",
    "config/datasets.yaml",
    "config/parameters.yaml",
    "config/surfaceome_universe_definition.yaml",
    "config/tissue_mappings.yaml",
    "config/tme_markers.yaml",
    "config/topology_isoforms.yaml",
    "config/exclusion_criteria.yaml",
    "docs/design_decisions.md",
    "docs/time_tracking.tsv",
    "docs/resource_requirements.md",
    "docs/literature_landscape_and_differentiation.md",
    "docs/deep_research_report_assessment.md",
    "docs/analytical_decisions_registry.md",
    "docs/notebook_to_pipeline_protocol.md",
    "docs/nondeterminism_inventory.md",
    "docs/reviewer_attack_surface.md",
    "docs/provenance_log.tsv",
    "workflow/Snakefile",
    "scripts/smoke_test.ps1",
]

REQUIRED_PHASE1_FILES = [
    "docs/fase1_data_inventory.md",
    "results/tables/dataset_inventory.tsv",
    "results/tables/sample_counts.tsv",
    "results/tables/coverage_matrix.tsv",
]

REQUIRED_PHASE2_FILES = [
    "config/release_manifest.yaml",
    "docs/fase2_data_acquisition.md",
    "results/tables/phase2_download_manifest.tsv",
    "data/checksums/sha256sums.txt",
    "data/checksums/xena_toil_sha256.tsv",
    "data/checksums/hpa_sha256.tsv",
    "data/checksums/uniprot_sha256.tsv",
    "data/checksums/gdc_tcga_stad_sha256.tsv",
]

REQUIRED_PHASE2_RAW_FILES = [
    "data/raw/xena_toil/TcgaTargetGTEX_phenotype.txt.gz",
    "data/raw/xena_toil/TcgaTargetGtex_rsem_gene_tpm.gz",
    "data/raw/hpa/normal_ihc_data.tsv.zip",
    "data/raw/hpa/cancer_data.tsv.zip",
    "data/raw/hpa/subcellular_location.tsv.zip",
    "data/raw/hpa/rna_tissue_consensus.tsv.zip",
    "data/raw/hpa/rna_tissue_gtex.tsv.zip",
    "data/raw/uniprot/uniprot_reviewed_human_topology.tsv.gz",
    "data/raw/gdc_tcga_stad/cases_tcga_stad.json",
    "data/raw/gdc_tcga_stad/files_tcga_stad_rnaseq_star_counts.json",
]

REQUIRED_PHASE2_DIAGNOSTIC_FILES = [
    "docs/fase2_batch_diagnostic.md",
    "results/figures/pca_batch_diagnostic.svg",
    "results/tables/batch_permanova.tsv",
    "results/tables/xena_batch_diagnostic_samples.tsv",
    "results/tables/xena_top_variable_genes.tsv",
]

REQUIRED_PHASE3_FILES = [
    "docs/fase3_identifier_normalization.md",
    "data/processed/id_map_master.tsv",
    "results/tables/mapping_failures.tsv",
    "results/tables/control_identifier_mapping.tsv",
    "results/tables/id_source_coverage.tsv",
    "data/checksums/hgnc_sha256.tsv",
]

REQUIRED_PHASE4_FILES = [
    "docs/fase4_surfaceome_universe.md",
    "data/processed/surfaceome_universe.tsv",
    "results/figures/surfaceome_source_overlap.svg",
    "results/figures/surfaceome_jaccard_with_published_lists.svg",
    "results/tables/surfaceome_confidence_summary.tsv",
    "results/tables/surfaceome_jaccard_with_published_lists.tsv",
    "results/tables/surfaceome_false_positive_false_negative_audit.tsv",
    "data/checksums/surfaceome_sources_sha256.tsv",
]

REQUIRED_PHASE4_RAW_FILES = [
    "data/raw/surfaceome/tcsa_supplementary_tables_1_40.xlsx",
    "data/raw/surfaceome/cspa_pone_0121314_s003.xlsx",
    "data/raw/surfaceome/surfy_table_s3_surfaceome.xlsx",
    "data/raw/uniprot/uniprot_reviewed_human_go.tsv.gz",
    "data/raw/uniprot/uniprot_reviewed_human_gpi.tsv.gz",
]

REQUIRED_PHASE4B_FILES = [
    "docs/fase4b_ranking_resolution.md",
    "results/validation/ranking_resolution_simulation.tsv",
    "results/validation/ranking_resolution_summary.tsv",
    "results/figures/rank_ci_by_coverage.svg",
]

REQUIRED_PHASE5_FILES = [
    "docs/fase5_tumor_expression.md",
    "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json",
    "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json",
    "data/checksums/cbioportal_sha256.tsv",
    "data/processed/tumor_expression.tsv",
    "results/figures/tumor_expression_distribution.svg",
    "results/tables/subtype_expression.tsv",
    "results/tables/subtype_sample_counts.tsv",
    "results/tables/subtype_power_analysis.tsv",
    "results/tables/clinical_covariate_expression.tsv",
    "results/tables/clinical_covariate_sample_counts.tsv",
    "results/tables/fase5_covariate_availability.tsv",
    "results/tables/amplified_target_cna_expression.tsv",
]

REQUIRED_PHASE6_FILES = [
    "config/tissue_mappings.yaml",
    "docs/fase6_normal_selectivity_risk.md",
    "data/processed/normal_expression.tsv",
    "data/processed/selectivity_scores.tsv",
    "data/processed/off_tumor_risk.tsv",
    "data/processed/organ_penalties.tsv",
    "data/processed/tumor_normal_tests.tsv",
    "results/tables/tumor_normal_power_analysis.tsv",
    "results/tables/normal_tissue_sample_counts.tsv",
    "results/tables/hpa_normal_protein_by_organ.tsv",
    "results/figures/tumor_vs_normal_critical.svg",
    "results/figures/tumor_normal_power_curve.svg",
]

REQUIRED_PHASE7_FILES = [
    "docs/fase7_protein_evidence.md",
    "data/processed/protein_evidence.tsv",
    "results/tables/protein_coverage.tsv",
    "results/figures/rna_protein_concordance.svg",
]

REQUIRED_PHASE8_FILES = [
    "config/tme_markers.yaml",
    "docs/fase8_single_cell_tme_specificity.md",
    "data/raw/tcga_purity/tidyestimate_1.1.1.tar.gz",
    "data/raw/tcga_purity/tidyestimate/data/gene_sets.rda",
    "data/checksums/tcga_purity_sha256.tsv",
    "data/processed/single_cell_specificity.tsv",
    "results/tables/tme_contamination_flags.tsv",
    "results/tables/tme_contamination_risk_mvp.tsv",
    "results/tables/tme_purity_adjusted_correlations.tsv",
    "results/tables/tme_purity_suppression_audit.tsv",
    "results/tables/tme_module_correlations.tsv",
    "results/tables/tme_module_marker_coverage.tsv",
    "results/tables/tme_estimate_marker_overlap.tsv",
    "results/tables/tumor_purity_estimate_scores.tsv",
    "results/figures/top_candidates_scRNA_dotplot.svg",
]

REQUIRED_PHASE9_FILES = [
    "config/topology_isoforms.yaml",
    "docs/fase9_topology_isoforms.md",
    "data/raw/uniprot/uniprot_reviewed_human_features.tsv.gz",
    "data/checksums/uniprot_phase9_features_sha256.tsv",
    "data/processed/topology_isoforms_ecd.tsv",
    "results/tables/isoform_risk_flags.tsv",
    "results/figures/ecd_length_distribution.svg",
]

REQUIRED_PHASE13_FILES = [
    "docs/limitations_register.md",
    "docs/fase13_mvp_score_integration.md",
    "docs/fase13_diagnostico.md",
    "results/tables/component_scores_all_candidates.tsv",
    "results/tables/tiering_annotations_all_candidates.tsv",
    "results/tables/control_recovery_phase13.tsv",
    "results/tables/fase13_diagnostic_snapshot_hashes.tsv",
    "results/tables/fase13_component_transform_audit.tsv",
    "results/tables/fase13_surfaceome_tie_groups.tsv",
    "results/tables/fase13_gpi_anchor_surf_audit.tsv",
    "results/tables/fase13_positive_control_component_diagnostic.tsv",
    "results/tables/fase13_positive_control_causal_gate.tsv",
    "results/tables/fase13_v0_v1_rank_delta.tsv",
    "results/rankings/ranking_balanced.tsv",
    "results/rankings/ranking_safety_first.tsv",
    "results/rankings/ranking_adc_focused.tsv",
    "results/rankings/ranking_novelty.tsv",
    "results/rankings/ranking_protein_first.tsv",
    "results/rankings/ranking_robust_aggregate.tsv",
    "results/rankings/ranking_v0_frozen.tsv",
    "results/rankings/ranking_v1_frozen.tsv",
    "results/rankings/ranking_v2_frozen.tsv",
    "results/rankings/ranking_v2_frozen.metadata.yaml",
    "results/validation/functional_form_sensitivity.tsv",
    "results/validation/phase13_post_scoring_sanity.tsv",
]

REQUIRED_PHASE14_PREFLIGHT_FILES = [
    "docs/fase14_preflight.md",
    "results/tables/fase14_preflight_top50_v1_v2_audit.tsv",
    "results/tables/fase14_preflight_snapshot_integrity.tsv",
    "results/tables/fase14_preflight_universe_stability.tsv",
]

REQUIRED_PHASE14_STABILITY_FILES = [
    "docs/fase14_rank_stability.md",
    "results/validation/rank_stability.tsv",
    "results/validation/leave_one_layer_out.tsv",
    "results/validation/weight_perturbation_summary.tsv",
    "results/validation/risk_threshold_sensitivity.tsv",
    "results/validation/risk_functional_form_sensitivity.tsv",
    "results/validation/organ_weight_perturbation.tsv",
    "results/validation/ranking_resolution_post_scoring.tsv",
    "results/validation/ranking_resolution_post_scoring_summary.tsv",
    "results/validation/missing_data_sensitivity.tsv",
    "results/validation/control_benchmark.tsv",
    "results/validation/top30_false_positive_audit.tsv",
    "results/figures/rank_stability_heatmap.svg",
    "results/figures/bumpchart_scenarios.svg",
]

REQUIRED_PHASE15_FILES = [
    "config/tiering_rules.yaml",
    "docs/manual_curation_protocol.md",
    "docs/fase15_tiering_and_curation.md",
    "docs/fase15_post_curation_verification.md",
    "docs/code_audit_four_claims_verification.md",
    "results/tables/tier_assignments.tsv",
    "results/tables/manual_curation_notes.tsv",
    "results/tables/top20_candidate_cards.md",
    "results/tables/excluded_with_reason.tsv",
    "results/tables/wang2026_crosscheck.tsv",
]

REQUIRED_PHASE16_FILES = [
    "docs/fase16_figures_tables.md",
    "results/figures/phase16_pipeline_overview.svg",
    "results/figures/phase16_surfaceome_evidence_landscape.svg",
    "results/figures/phase16_tumor_normal_selectivity.svg",
    "results/figures/phase16_multilayer_heatmap_top30.svg",
    "results/figures/phase16_benchmark_controls.svg",
    "results/figures/phase16_tier1_candidate_panel.svg",
    "results/tables/manuscript_figure_manifest.tsv",
    "results/tables/manuscript_table1_datasets.tsv",
    "results/tables/manuscript_table2_score_definitions.tsv",
    "results/tables/manuscript_table3_top_candidates.tsv",
    "results/tables/manuscript_table4_controls.tsv",
    "results/tables/manuscript_table5_candidate_flags.tsv",
    "results/tables/supplementary_table_manifest.tsv",
]

REQUIRED_RANK_RESOLUTION_COLUMNS = {
    "hgnc_symbol",
    "surfaceome_category",
    "surfaceome_confidence_score",
    "mean_rank",
    "sd_rank",
    "rank_p2_5",
    "rank_p50",
    "rank_p97_5",
    "rank_ci_width",
    "rank_ci_half_width",
    "ci_within_plusminus_10",
    "ci_exceeds_plusminus_50",
    "ci_contained_in_top40",
    "top20_frequency",
}

REQUIRED_RANK_RESOLUTION_SUMMARY_METRICS = {
    "candidate_universe_n",
    "n_simulations",
    "rank_resolution_seed",
    "genes_ci_within_plusminus_10",
    "genes_ci_exceeds_plusminus_50",
    "top20_median_rank_genes",
    "top20_with_ci_contained_in_top40",
    "tiering_resolution_decision",
    "coverage_Surf",
    "coverage_E",
    "coverage_N",
    "coverage_R",
    "coverage_P",
    "coverage_T",
}

REQUIRED_TUMOR_EXPRESSION_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "surfaceome_category",
    "n_tumor_samples",
    "median_tpm_tumor",
    "robust_mean_tpm_tumor",
    "p75_tpm_tumor",
    "p90_tpm_tumor",
    "pct_samples_tpm_gt_1",
    "pct_samples_tpm_gt_5",
    "median_tpm_rank_percentile",
    "pct_gt_1_rank_percentile",
    "p75_tpm_rank_percentile",
    "p90_tpm_rank_percentile",
    "E_score",
    "E_rank_percentile",
    "expression_data_status",
    "xena_gene_id",
}

REQUIRED_SUBTYPE_COUNT_COLUMNS = {
    "subtype",
    "n_primary_tumor_samples",
    "n_cbioportal_patients",
    "descriptive_report_allowed",
    "quantitative_claim_allowed",
    "tier1_subtype_only_allowed",
    "claim_scope",
}

REQUIRED_GROUPED_EXPRESSION_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "group_type",
    "group_level",
    "n_group_samples",
    "n_other_primary_tumor_samples",
    "median_tpm_group",
    "p75_tpm_group",
    "p90_tpm_group",
    "pct_samples_tpm_gt_1_group",
    "pct_samples_tpm_gt_5_group",
    "median_log2_tpm_delta_vs_other_tumors",
    "claim_scope",
}

REQUIRED_NORMAL_EXPRESSION_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "n_tumor",
    "n_gtex_stomach_normal",
    "n_tcga_adjacent_normal",
    "median_tpm_tumor",
    "median_tpm_gtex_stomach",
    "median_tpm_tcga_adjacent_normal",
    "normal_xena_p90_tpm",
    "normal_xena_p95_tpm",
    "max_critical_normal_tpm",
    "max_critical_normal_organ",
    "gi_normal_max_tpm",
    "immune_blood_max_tpm",
    "hpa_stomach_rna_ntpm",
    "hpa_max_critical_rna_ntpm",
    "hpa_normal_protein_max_level_score",
    "normal_expression_data_status",
    "gastric_lineage_flag",
}

REQUIRED_SELECTIVITY_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "N_stomach_log2fc",
    "N_critical_log2fc",
    "N_tcga_adjacent_log2fc",
    "N_stat_gtex",
    "N_score",
    "N_rank_percentile",
    "positive_N_stat_rule_gtex",
    "gtex_fdr_bh",
    "tcga_adjacent_fdr_bh",
    "selectivity_interpretation",
}

REQUIRED_OFF_TUMOR_RISK_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "R_score",
    "R_max",
    "R_max_plus_breadth",
    "R_sum_capped",
    "max_risk_organ",
    "critical_organs",
    "risk_interpretation",
}

REQUIRED_ORGAN_PENALTY_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "organ",
    "normal_expr_tpm_or_ntpm",
    "normal_expression_source",
    "organ_rank_percentile",
    "caution_threshold_tpm",
    "critical_threshold_tpm",
    "organ_penalty",
    "organ_weight",
    "weighted_organ_penalty",
    "risk_category",
    "hpa_normal_protein_level_score",
}

REQUIRED_PROTEIN_EVIDENCE_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "surfaceome_category",
    "hpa_stomach_cancer_total_patients",
    "hpa_stomach_cancer_high",
    "hpa_stomach_cancer_medium",
    "hpa_stomach_cancer_low",
    "hpa_stomach_cancer_not_detected",
    "hpa_stomach_cancer_present_pct",
    "hpa_stomach_cancer_high_medium_pct",
    "hpa_stomach_cancer_weighted_presence",
    "hpa_stomach_cancer_max_staining",
    "hpa_stomach_cancer_dominant_staining",
    "normal_stomach_protein_level_score",
    "normal_stomach_protein_level",
    "normal_stomach_reliability",
    "normal_critical_protein_level_score",
    "normal_critical_protein_level",
    "normal_critical_protein_organ",
    "hpa_subcellular_reliability",
    "hpa_main_location",
    "hpa_additional_location",
    "hpa_extracellular_location",
    "membrane_support_class",
    "protein_tumor_presence",
    "membrane_localization_support",
    "normal_protein_safety_support",
    "antibody_validation_support",
    "discordance_penalty",
    "P_score",
    "P_rank_percentile",
    "median_tpm_tumor",
    "E_rank_percentile",
    "R_score",
    "discordance_flags",
    "cptac_status",
    "hpa_evidence_status",
    "bulk_limitations",
}

REQUIRED_PROTEIN_COVERAGE_LAYERS = {
    "hpa_stomach_cancer_ihc",
    "hpa_normal_stomach_ihc",
    "hpa_critical_normal_ihc",
    "hpa_subcellular_location",
    "hpa_membrane_or_cell_junction",
    "cptac_proteomics",
    "protein_evidence_P_score_available",
}

REQUIRED_PROTEIN_DISCORDANCE_FLAGS = {
    "HPA_missing",
    "RNA_high_protein_absent",
    "RNA_low_protein_present",
    "protein_present_no_membrane",
    "antibody_low_confidence",
    "CPTAC_not_assessed",
}

REQUIRED_SINGLE_CELL_SPECIFICITY_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "surfaceome_category",
    "selected_scrna_dataset",
    "scRNA_gate_status",
    "scRNA_data_status",
    "SC_status",
    "SC_score",
    "SC_rank_percentile",
    "pct_malignant_cells_positive",
    "mean_expr_malignant_epithelial",
    "mean_expr_normal_epithelial",
    "max_tme_expr",
    "tumor_cell_specificity_index",
    "cellular_specificity_label",
    "tme_contamination_risk",
    "max_tme_module",
    "max_tme_spearman_rho",
    "max_tme_partial_spearman_rho",
    "bulk_tme_fallback_status",
    "purity_adjustment_status",
}

REQUIRED_TME_FLAG_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "surfaceome_category",
    "scRNA_gate_status",
    "SC_status",
    "cellular_specificity_label",
    "raw_tme_contamination_risk",
    "tme_contamination_risk",
    "max_tme_module",
    "max_tme_spearman_rho",
    "max_tme_p_value",
    "max_tme_n_samples",
    "max_tme_partial_spearman_rho",
    "max_tme_partial_p_value",
    "max_tme_partial_n_samples",
    "combined_tme_spearman_rho",
    "combined_tme_p_value",
    "combined_tme_n_samples",
    "combined_tme_partial_spearman_rho",
    "combined_tme_partial_p_value",
    "combined_tme_partial_n_samples",
    "known_tme_control",
    "median_tpm_tumor",
    "E_rank_percentile",
    "purity_source",
    "purity_adjustment_status",
    "tiering_implication",
}

REQUIRED_TME_PURITY_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "purity_source",
    "purity_n_samples",
    "partial_correlation_status",
    "max_tme_module",
    "raw_spearman_rho",
    "partial_spearman_rho",
    "partial_p_value",
    "partial_n_samples",
    "raw_tme_contamination_risk",
    "tme_contamination_risk_after_purity",
    "notes",
}

REQUIRED_TUMOR_PURITY_SCORE_COLUMNS = {
    "sample",
    "patient_id",
    "sample_index",
    "stromal_score",
    "immune_score",
    "estimate_score",
    "estimate_purity_proxy",
    "purity_covariate",
    "purity_source",
}

REQUIRED_TME_SUPPRESSION_AUDIT_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "surfaceome_category",
    "transition",
    "max_tme_module",
    "raw_spearman_rho",
    "partial_spearman_rho",
    "delta_partial_minus_raw",
    "median_tpm_tumor",
    "E_rank_percentile",
    "tiering_implication",
    "audit_note",
}

REQUIRED_TME_ESTIMATE_OVERLAP_COLUMNS = {
    "module_id",
    "module_label",
    "n_module_markers",
    "n_estimate_stromal_overlap",
    "estimate_stromal_overlap_markers",
    "n_estimate_immune_overlap",
    "estimate_immune_overlap_markers",
    "interpretation_note",
}

REQUIRED_TME_MODULES = {
    "caf_fibroblast",
    "endothelial",
    "myeloid_macrophage",
    "t_cell",
    "b_plasma",
}

ALLOWED_CELLULAR_SPECIFICITY_LABELS = {
    "tumor epithelial enriched",
    "tumor + normal epithelial",
    "immune/TME-derived",
    "ambiguous",
    "not covered",
}

REQUIRED_TOPOLOGY_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "protein_name",
    "surfaceome_category",
    "uniprot_feature_status",
    "protein_length_aa",
    "tm_helix_count",
    "signal_peptide_present",
    "gpi_anchor_present",
    "n_terminal_orientation",
    "c_terminal_orientation",
    "extracellular_segment_count",
    "extracellular_segments",
    "total_extracellular_aa",
    "largest_extracellular_loop_aa",
    "topology_confidence",
    "topology_evidence_class",
    "accessibility_class",
    "accessibility_interpretation",
    "domain_architecture_flags",
    "glycosylation_site_count",
    "disulfide_bond_count",
    "cleavage_or_shedding_flag",
    "soluble_isoform_or_secreted_flag",
    "internalization_status",
    "isoform_count",
    "mapped_uniprot_isoforms",
    "isoform_confidence",
    "isoform_resolution_status",
    "accessibility_class_score",
    "extracellular_length_score",
    "shedding_penalty",
    "soluble_decoy_penalty",
    "T_score",
    "T_rank_percentile",
    "topology_notes",
}

REQUIRED_ISOFORM_FLAG_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "isoform_or_topology_issue",
    "isoform_resolution_status",
    "mapped_transcripts_or_isoforms",
    "clinical_target_context",
    "tiering_implication",
    "evidence_basis",
    "required_followup",
}

REQUIRED_COMPONENT_SCORE_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "surfaceome_category",
    "Surf_relative_confidence",
    "Surf_scaling_method",
    "E_rank_percentile",
    "N_rank_percentile",
    "R_rank_percentile_high_worse",
    "R_score_direction",
    "P_rank_percentile",
    "SC_status",
    "SC_component_status",
    "T_rank_percentile",
    "missing_mvp_score_components",
    "n_missing_mvp_score_components",
    "n_available_mvp_score_components",
    "score_data_status",
}

REQUIRED_RANKING_COLUMNS = {
    "rank",
    "hgnc_symbol",
    "scenario",
    "scenario_score",
    "available_weight_sum",
    "Surf_relative_confidence",
    "E_rank_percentile",
    "N_rank_percentile",
    "R_rank_percentile_high_worse",
    "P_rank_percentile",
    "SC_status",
    "T_rank_percentile",
    "R_contribution_subtracted",
    "tme_contamination_risk",
    "accessibility_class",
    "isoform_resolution_status",
}

RANKING_SIDECAR_COLUMNS = {
    "ranking_status",
    "score_config_sha256",
    "git_commit",
    "freeze_version",
    "freeze_date_utc",
    "git_worktree_status_at_freeze",
}

REQUIRED_TIERING_ANNOTATION_COLUMNS = {
    "hgnc_symbol",
    "balanced_rank",
    "balanced_score",
    "missing_data_tiering_precheck",
    "manual_curation_required_flags",
    "annotation_status",
}

REQUIRED_CONTROL_RECOVERY_COLUMNS = {
    "control_set",
    "hgnc_symbol",
    "expected",
    "balanced_rank",
    "in_top50_balanced",
    "in_top100_balanced",
    "presence_status",
    "control_interpretation",
}

REQUIRED_FUNCTIONAL_FORM_METHODS = {
    "weighted_rank_sum",
    "geometric_mean_percentile",
    "weighted_rank_sum_with_veto_p20",
}

REQUIRED_PHASE13_SANITY_CHECKS = {
    "positive_controls_top50",
    "negative_controls_top100",
    "non_obvious_top10_presence",
    "top20_missing_protein",
    "top20_three_or_more_missing_components",
    "tme_penalty_controls_top100",
}

ALLOWED_ACCESSIBILITY_CLASSES = {"A", "B", "C", "D", "E"}

REQUIRED_CRITICAL_ORGANS = {
    "heart",
    "brain",
    "liver",
    "kidney",
    "lung",
    "hematopoietic",
    "endothelial",
    "immune",
    "gi_epithelial",
    "reproductive_other",
}

REQUIRED_SURFACEOME_COLUMNS = {
    "hgnc_symbol",
    "ensembl_gene_id",
    "uniprot_accession",
    "surfaceome_confidence_score",
    "surfaceome_category",
    "surface_support_source_count",
    "surface_support_sources",
    "in_tcsa",
    "in_cspa",
    "in_surfy",
    "uniprot_extracellular_topology",
    "uniprot_gpi_anchor",
    "uniprot_gpi_evidence_class",
    "uniprot_gpi_subcellular_only",
    "go_surface_or_plasma_membrane",
    "hpa_plasma_membrane",
    "control_role",
    "interpretation_flags",
}

SURFACEOME_NEGATIVE_CONTROLS = {"ACTB", "GAPDH", "H3C1", "TOMM20", "CALR", "ALB"}
SURFACEOME_POSITIVE_CONTROLS = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "CEACAM5", "MET", "MSLN"}
SURFACEOME_PUBLISHED_LISTS = {"tcsa", "cspa", "surfy"}

REQUIRED_ID_MAP_COLUMNS = {
    "source_gene_symbol",
    "hgnc_symbol",
    "alias_symbols",
    "ensembl_gene_id",
    "ensembl_transcript_id",
    "entrez_id",
    "uniprot_accession",
    "uniprot_isoform_id",
    "protein_name",
    "mapping_status",
    "isoform_handling_flag",
    "target_context_flag",
}

REQUIRED_CONTROL_SYMBOLS = {
    "ERBB2",
    "CLDN18",
    "FGFR2",
    "TACSTD2",
    "EPCAM",
    "CEACAM5",
    "MET",
    "MSLN",
    "CEACAM6",
    "ERBB3",
    "GUCY2C",
    "SLC44A4",
    "NECTIN4",
    "ACTB",
    "GAPDH",
    "H3C1",
    "TOMM20",
    "CALR",
    "ALB",
    "PTPRC",
    "PECAM1",
}

REQUIRED_COVERAGE_LAYERS = {
    "RNA tumor",
    "RNA normal",
    "HPA normal",
    "HPA pathology",
    "UniProt topology",
    "PDB/AlphaFold",
    "DepMap",
    "scRNA",
    "external cohort",
    "clinical/druggability",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_bootstrap(root: Path) -> list[str]:
    return [path for path in REQUIRED_BOOTSTRAP_FILES if not (root / path).exists()]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 8), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_phase1_inventory(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE1_FILES if not (root / path).exists()]
    if failures:
        return failures

    coverage_rows = read_tsv(root / "results/tables/coverage_matrix.tsv")
    layers = {row["layer"] for row in coverage_rows}
    missing_layers = sorted(REQUIRED_COVERAGE_LAYERS - layers)
    if missing_layers:
        failures.append("coverage_matrix missing layers: " + ",".join(missing_layers))

    sample_rows = read_tsv(root / "results/tables/sample_counts.tsv")
    uniprot_reviewed = [
        row
        for row in sample_rows
        if row.get("source_id") == "uniprot_reviewed_human"
        and row.get("category") == "human_reviewed"
    ]
    if not uniprot_reviewed or int(uniprot_reviewed[0].get("n", "0")) <= 0:
        failures.append("sample_counts has invalid UniProt reviewed human count")

    xena_primary = [
        row
        for row in sample_rows
        if row.get("source_id") == "xena_toil_tcga_gtex"
        and row.get("cohort_or_dataset") == "TCGA-STAD"
        and row.get("category") == "Primary Tumor"
    ]
    if not xena_primary or int(xena_primary[0].get("n", "0")) <= 0:
        failures.append("sample_counts has invalid Xena TCGA-STAD primary tumor count")

    return failures


def read_sha256sums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            checksum, rel_path = stripped.split(maxsplit=1)
            checksums[rel_path.strip()] = checksum
    return checksums


def check_phase2_downloads(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE2_FILES if not (root / path).exists()]
    failures.extend(path for path in REQUIRED_PHASE2_RAW_FILES if not (root / path).exists())
    checksum_path = root / "data/checksums/sha256sums.txt"
    if failures or not checksum_path.exists():
        return failures

    checksums = read_sha256sums(checksum_path)
    for rel_path in REQUIRED_PHASE2_RAW_FILES:
        path = root / rel_path
        expected = checksums.get(rel_path)
        if expected is None:
            failures.append(f"sha256sums.txt missing {rel_path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            failures.append(f"checksum mismatch for {rel_path}")

    manifest_rows = read_tsv(root / "results/tables/phase2_download_manifest.tsv")
    manifest_sources = {row.get("source_id", "") for row in manifest_rows}
    for source_id in ["xena_toil_tcga_gtex", "hpa_downloads", "uniprot_reviewed_human", "gdc_tcga_stad"]:
        if source_id not in manifest_sources:
            failures.append(f"phase2_download_manifest missing source {source_id}")

    return failures


def check_phase2_batch_diagnostic(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE2_DIAGNOSTIC_FILES if not (root / path).exists()]
    if failures:
        return failures

    samples = read_tsv(root / "results/tables/xena_batch_diagnostic_samples.tsv")
    group_counts: dict[str, int] = {}
    for row in samples:
        group_counts[row["analysis_group"]] = group_counts.get(row["analysis_group"], 0) + 1
    expected_minimums = {
        "TCGA-STAD primary tumor": 400,
        "TCGA-STAD adjacent normal": 30,
        "GTEx stomach normal": 150,
    }
    for group, minimum in expected_minimums.items():
        if group_counts.get(group, 0) < minimum:
            failures.append(f"xena_batch_diagnostic_samples has too few {group} samples")

    permanova = read_tsv(root / "results/tables/batch_permanova.tsv")
    tests = {row.get("test_id", "") for row in permanova}
    for test_id in ["study_all_samples", "sample_group_all_samples", "normal_source_only"]:
        if test_id not in tests:
            failures.append(f"batch_permanova missing {test_id}")

    pca_svg = (root / "results/figures/pca_batch_diagnostic.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in pca_svg:
        failures.append("pca_batch_diagnostic.svg is not a valid SVG")

    return failures


def check_phase3_identifier_map(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE3_FILES if not (root / path).exists()]
    if failures:
        return failures

    id_map = read_tsv(root / "data/processed/id_map_master.tsv")
    if not id_map:
        return ["id_map_master.tsv has no rows"]
    missing_columns = REQUIRED_ID_MAP_COLUMNS - set(id_map[0])
    if missing_columns:
        failures.append("id_map_master missing columns: " + ",".join(sorted(missing_columns)))

    unresolved = [row for row in id_map if row.get("mapping_status") != "resolved_primary"]
    unresolved_pct = len(unresolved) / len(id_map) * 100
    if unresolved_pct >= 2.0:
        failures.append(f"id_map_master unresolved primary identifiers >=2%: {unresolved_pct:.2f}%")

    rows_by_symbol = {row.get("hgnc_symbol", ""): row for row in id_map}
    for symbol in ["CLDN18", "FGFR2", "ERBB2", "MUC1", "MUC16"]:
        if symbol not in rows_by_symbol:
            failures.append(f"id_map_master missing required special/control symbol {symbol}")
    if "CLDN18.2" not in rows_by_symbol.get("CLDN18", {}).get("isoform_handling_flag", ""):
        failures.append("CLDN18 lacks CLDN18.2 isoform flag")
    if "FGFR2b" not in rows_by_symbol.get("FGFR2", {}).get("isoform_handling_flag", ""):
        failures.append("FGFR2 lacks FGFR2b isoform flag")
    if not rows_by_symbol.get("ERBB2", {}).get("target_context_flag", ""):
        failures.append("ERBB2 lacks amplification/protein downstream flag")
    hla_rows = [row for row in id_map if row.get("hgnc_symbol", "").startswith("HLA-")]
    if not hla_rows or not all(row.get("target_context_flag") for row in hla_rows):
        failures.append("HLA genes are not consistently flagged")

    control_rows = read_tsv(root / "results/tables/control_identifier_mapping.tsv")
    resolved_controls = {row.get("source_gene_symbol", "") for row in control_rows if row.get("gene_mapping_status") in {"mapped", "mapped_manual_alias"}}
    missing_controls = REQUIRED_CONTROL_SYMBOLS - resolved_controls
    if missing_controls:
        failures.append("control_identifier_mapping missing resolved controls: " + ",".join(sorted(missing_controls)))
    control_errors = [
        row
        for row in read_tsv(root / "results/tables/mapping_failures.tsv")
        if row.get("source_id") == "controls" and row.get("severity") == "error"
    ]
    if control_errors:
        failures.append("mapping_failures contains control error rows")

    coverage_rows = read_tsv(root / "results/tables/id_source_coverage.tsv")
    candidate_rows = [row for row in coverage_rows if row.get("source_id") == "id_map_master_candidates"]
    if not candidate_rows or candidate_rows[0].get("pct_mapped_to_hgnc_protein_coding") != "100.00":
        failures.append("id_source_coverage missing 100% candidate coverage row")

    return failures


def check_phase4_surfaceome_universe(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE4_FILES if not (root / path).exists()]
    failures.extend(path for path in REQUIRED_PHASE4_RAW_FILES if not (root / path).exists())
    if failures:
        return failures

    checksum_path = root / "data/checksums/sha256sums.txt"
    if not checksum_path.exists():
        failures.append("data/checksums/sha256sums.txt")
        return failures
    checksums = read_sha256sums(checksum_path)
    for rel_path in REQUIRED_PHASE4_RAW_FILES:
        path = root / rel_path
        expected = checksums.get(rel_path)
        if expected is None:
            failures.append(f"sha256sums.txt missing {rel_path}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            failures.append(f"checksum mismatch for {rel_path}")

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    if not universe:
        return failures + ["surfaceome_universe.tsv has no rows"]
    missing_columns = REQUIRED_SURFACEOME_COLUMNS - set(universe[0])
    if missing_columns:
        failures.append("surfaceome_universe missing columns: " + ",".join(sorted(missing_columns)))

    rows_by_symbol = {row.get("hgnc_symbol", ""): row for row in universe}
    gpi_direct_rows = [row for row in universe if row.get("uniprot_gpi_anchor", "").lower() == "true"]
    if len(gpi_direct_rows) < 100:
        failures.append(f"too few confirmed UniProt GPI anchors captured in surfaceome universe: {len(gpi_direct_rows)}")
    for symbol in ["CEACAM5", "MSLN"]:
        if rows_by_symbol.get(symbol, {}).get("uniprot_gpi_anchor", "").lower() != "true":
            failures.append(f"{symbol} confirmed GPI anchor was not credited in Fase 4")
    category_counts: dict[str, int] = {}
    for row in universe:
        category = row.get("surfaceome_category", "")
        category_counts[category] = category_counts.get(category, 0) + 1
    core_probable = category_counts.get("core_surfaceome", 0) + category_counts.get("probable_surfaceome", 0)
    if core_probable < 500 or core_probable > 3000:
        failures.append(f"core+probable surfaceome size outside 500-3000 review range: {core_probable}")

    for symbol in sorted(SURFACEOME_NEGATIVE_CONTROLS):
        row = rows_by_symbol.get(symbol)
        if not row:
            failures.append(f"surfaceome_universe missing negative control {symbol}")
            continue
        if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"}:
            failures.append(f"negative control {symbol} entered {row.get('surfaceome_category')}")

    for symbol in sorted(SURFACEOME_POSITIVE_CONTROLS):
        row = rows_by_symbol.get(symbol)
        if not row:
            failures.append(f"surfaceome_universe missing positive control {symbol}")
            continue
        if row.get("surfaceome_category") == "excluded":
            failures.append(f"positive control {symbol} is excluded from the surfaceome universe")

    audit_rows = read_tsv(root / "results/tables/surfaceome_false_positive_false_negative_audit.tsv")
    control_reviews = [
        row
        for row in audit_rows
        if row.get("audit_type") == "control" and row.get("status") == "review_required"
    ]
    if control_reviews:
        failures.append(
            "surfaceome control audit has review_required rows: "
            + ",".join(sorted(row.get("hgnc_symbol", "") for row in control_reviews))
        )

    jaccard_rows = read_tsv(root / "results/tables/surfaceome_jaccard_with_published_lists.tsv")
    published_lists = {row.get("published_list", "") for row in jaccard_rows}
    missing_published = SURFACEOME_PUBLISHED_LISTS - published_lists
    if missing_published:
        failures.append("surfaceome jaccard table missing published lists: " + ",".join(sorted(missing_published)))
    valid_jaccard_values: list[float] = []
    for row in jaccard_rows:
        try:
            value = float(row.get("jaccard", "0") or "0")
        except ValueError:
            failures.append(f"invalid jaccard value for {row.get('published_list', '')}")
            continue
        if not 0 <= value <= 1:
            failures.append(f"jaccard outside [0,1] for {row.get('published_list', '')}: {value}")
        valid_jaccard_values.append(value)
    if valid_jaccard_values and max(valid_jaccard_values) < 0.60:
        note = (root / "docs/fase4_surfaceome_universe.md").read_text(encoding="utf-8", errors="replace").lower()
        if "jaccard" not in note or "review" not in note:
            failures.append("all published-list Jaccard values are <0.60 without documented review note")

    note_text = (root / "docs/fase4_surfaceome_universe.md").read_text(encoding="utf-8", errors="replace")
    for required_text in ["GPI-anchor", "score +2", "Subcellular-location-only"]:
        if required_text not in note_text:
            failures.append(f"fase4_surfaceome_universe.md missing '{required_text}'")

    for rel_path in [
        "results/figures/surfaceome_source_overlap.svg",
        "results/figures/surfaceome_jaccard_with_published_lists.svg",
    ]:
        text = (root / rel_path).read_text(encoding="utf-8", errors="replace")
        if "<svg" not in text:
            failures.append(f"{rel_path} is not a valid SVG")

    return failures


def check_phase4b_ranking_resolution(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE4B_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    simulation_rows = read_tsv(root / "results/validation/ranking_resolution_simulation.tsv")
    if not simulation_rows:
        return ["ranking_resolution_simulation.tsv has no rows"]
    missing_columns = REQUIRED_RANK_RESOLUTION_COLUMNS - set(simulation_rows[0])
    if missing_columns:
        failures.append("ranking_resolution_simulation missing columns: " + ",".join(sorted(missing_columns)))
    if len(simulation_rows) != expected_n:
        failures.append(f"ranking_resolution_simulation row count {len(simulation_rows)} does not match Core+Probable universe {expected_n}")

    seen_symbols: set[str] = set()
    for row in simulation_rows:
        symbol = row.get("hgnc_symbol", "")
        if symbol in seen_symbols:
            failures.append(f"ranking_resolution_simulation duplicate symbol {symbol}")
            break
        seen_symbols.add(symbol)
        for field in ["mean_rank", "sd_rank", "rank_p2_5", "rank_p50", "rank_p97_5", "rank_ci_width", "top20_frequency"]:
            try:
                value = float(row.get(field, "nan"))
            except ValueError:
                failures.append(f"ranking_resolution_simulation invalid numeric {field} for {symbol}")
                continue
            if field == "top20_frequency":
                if not 0 <= value <= 1:
                    failures.append(f"top20_frequency outside [0,1] for {symbol}: {value}")
            elif value < 0:
                failures.append(f"{field} is negative for {symbol}: {value}")
        try:
            p2 = float(row.get("rank_p2_5", "0"))
            p50 = float(row.get("rank_p50", "0"))
            p97 = float(row.get("rank_p97_5", "0"))
        except ValueError:
            continue
        if not p2 <= p50 <= p97:
            failures.append(f"rank percentiles are not ordered for {symbol}")

    summary_rows = read_tsv(root / "results/validation/ranking_resolution_summary.tsv")
    summary = {row.get("metric", ""): row for row in summary_rows}
    missing_metrics = REQUIRED_RANK_RESOLUTION_SUMMARY_METRICS - set(summary)
    if missing_metrics:
        failures.append("ranking_resolution_summary missing metrics: " + ",".join(sorted(missing_metrics)))
    if int(float(summary.get("candidate_universe_n", {}).get("value", "-1"))) != expected_n:
        failures.append("ranking_resolution_summary candidate_universe_n does not match Core+Probable universe")
    if int(float(summary.get("n_simulations", {}).get("value", "0"))) < 100:
        failures.append("ranking_resolution_summary n_simulations is below 100")
    decision = summary.get("tiering_resolution_decision", {}).get("value", "")
    if decision not in {"five_tier_starting_point_supported", "reduce_to_three_tiers_or_raise_tier1_stability_threshold"}:
        failures.append("ranking_resolution_summary has invalid tiering_resolution_decision")
    for metric in ["coverage_Surf", "coverage_E", "coverage_N", "coverage_R", "coverage_P", "coverage_T"]:
        try:
            value = float(summary.get(metric, {}).get("value", "nan"))
        except ValueError:
            failures.append(f"invalid coverage metric {metric}")
            continue
        if not 0 <= value <= 1:
            failures.append(f"coverage metric {metric} outside [0,1]: {value}")

    svg = (root / "results/figures/rank_ci_by_coverage.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in svg:
        failures.append("rank_ci_by_coverage.svg is not a valid SVG")

    note = (root / "docs/fase4b_ranking_resolution.md").read_text(encoding="utf-8", errors="replace")
    for required_text in ["Fase 4B", "Core+Probable", "Fase 14"]:
        if required_text not in note:
            failures.append(f"fase4b_ranking_resolution.md missing '{required_text}'")

    return failures


def check_phase5_tumor_expression(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE5_FILES if not (root / path).exists()]
    if failures:
        return failures

    checksum_path = root / "data/checksums/sha256sums.txt"
    if not checksum_path.exists():
        failures.append("data/checksums/sha256sums.txt")
        return failures
    checksums = read_sha256sums(checksum_path)
    for rel_path in [
        "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_patient_clinical_data.json",
        "data/raw/cbioportal/stad_tcga_pan_can_atlas_2018_gistic_erbb2_fgfr2_met.json",
    ]:
        expected = checksums.get(rel_path)
        if expected is None:
            failures.append(f"sha256sums.txt missing {rel_path}")
            continue
        actual = sha256_file(root / rel_path)
        if actual != expected:
            failures.append(f"checksum mismatch for {rel_path}")

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    tumor_rows = read_tsv(root / "data/processed/tumor_expression.tsv")
    if not tumor_rows:
        return failures + ["tumor_expression.tsv has no rows"]
    missing_columns = REQUIRED_TUMOR_EXPRESSION_COLUMNS - set(tumor_rows[0])
    if missing_columns:
        failures.append("tumor_expression missing columns: " + ",".join(sorted(missing_columns)))
    if len(tumor_rows) != expected_n:
        failures.append(f"tumor_expression row count {len(tumor_rows)} does not match Core+Probable universe {expected_n}")
    seen_symbols: set[str] = set()
    measured_count = 0
    for row in tumor_rows:
        symbol = row.get("hgnc_symbol", "")
        if symbol in seen_symbols:
            failures.append(f"tumor_expression duplicate symbol {symbol}")
            break
        seen_symbols.add(symbol)
        if row.get("expression_data_status") != "measured":
            continue
        measured_count += 1
        try:
            n_tumor = int(row.get("n_tumor_samples", "0"))
        except ValueError:
            failures.append(f"invalid n_tumor_samples for {symbol}")
            continue
        if n_tumor < 400:
            failures.append(f"too few tumor samples for {symbol}: {n_tumor}")
        for field in [
            "median_tpm_tumor",
            "robust_mean_tpm_tumor",
            "p75_tpm_tumor",
            "p90_tpm_tumor",
            "pct_samples_tpm_gt_1",
            "pct_samples_tpm_gt_5",
            "E_score",
            "E_rank_percentile",
        ]:
            try:
                value = float(row.get(field, "nan"))
            except ValueError:
                failures.append(f"invalid numeric {field} for {symbol}")
                continue
            if field.startswith("pct_") or field in {"E_score", "E_rank_percentile"}:
                if not 0 <= value <= 1:
                    failures.append(f"{field} outside [0,1] for {symbol}: {value}")
            elif value < 0:
                failures.append(f"{field} is negative for {symbol}: {value}")
    if measured_count < int(expected_n * 0.95):
        failures.append(f"measured tumor-expression coverage below 95%: {measured_count}/{expected_n}")

    subtype_counts = read_tsv(root / "results/tables/subtype_sample_counts.tsv")
    if not subtype_counts:
        failures.append("subtype_sample_counts.tsv has no rows")
    else:
        missing_columns = REQUIRED_SUBTYPE_COUNT_COLUMNS - set(subtype_counts[0])
        if missing_columns:
            failures.append("subtype_sample_counts missing columns: " + ",".join(sorted(missing_columns)))
        counts_by_subtype = {row.get("subtype", ""): row for row in subtype_counts}
        for subtype in ["STAD_EBV", "STAD_MSI", "STAD_GS", "STAD_CIN"]:
            if subtype not in counts_by_subtype:
                failures.append(f"subtype_sample_counts missing {subtype}")
                continue
            if int(counts_by_subtype[subtype].get("n_primary_tumor_samples", "0")) < 15:
                failures.append(f"subtype_sample_counts has too few {subtype} samples")

    subtype_rows = read_tsv(root / "results/tables/subtype_expression.tsv")
    if not subtype_rows:
        failures.append("subtype_expression.tsv has no rows")
    else:
        missing_columns = REQUIRED_GROUPED_EXPRESSION_COLUMNS - set(subtype_rows[0])
        if missing_columns:
            failures.append("subtype_expression missing columns: " + ",".join(sorted(missing_columns)))
        subtype_levels = {row.get("group_level", "") for row in subtype_rows}
        for subtype in ["STAD_EBV", "STAD_MSI", "STAD_GS", "STAD_CIN"]:
            if subtype not in subtype_levels:
                failures.append(f"subtype_expression missing {subtype}")

    clinical_rows = read_tsv(root / "results/tables/clinical_covariate_expression.tsv")
    if not clinical_rows:
        failures.append("clinical_covariate_expression.tsv has no rows")
    else:
        missing_columns = REQUIRED_GROUPED_EXPRESSION_COLUMNS - set(clinical_rows[0])
        if missing_columns:
            failures.append("clinical_covariate_expression missing columns: " + ",".join(sorted(missing_columns)))
        group_types = {row.get("group_type", "") for row in clinical_rows}
        for group_type in ["ajcc_pathologic_stage_collapsed", "tissue_or_organ_of_origin"]:
            if group_type not in group_types:
                failures.append(f"clinical_covariate_expression missing {group_type}")

    power_rows = read_tsv(root / "results/tables/subtype_power_analysis.tsv")
    if not power_rows:
        failures.append("subtype_power_analysis.tsv has no rows")
    else:
        power_subtypes = {row.get("subtype", "") for row in power_rows}
        for subtype in ["STAD_EBV", "STAD_MSI", "STAD_GS", "STAD_CIN"]:
            if subtype not in power_subtypes:
                failures.append(f"subtype_power_analysis missing {subtype}")
        for row in power_rows:
            try:
                n_tests = int(row.get("n_tests", "0"))
            except ValueError:
                failures.append(f"invalid n_tests for subtype {row.get('subtype', '')}")
                continue
            if n_tests < int(expected_n * 0.95):
                failures.append(f"subtype_power_analysis n_tests too low for {row.get('subtype', '')}: {n_tests}")

    cna_rows = read_tsv(root / "results/tables/amplified_target_cna_expression.tsv")
    if not cna_rows:
        failures.append("amplified_target_cna_expression.tsv has no rows")
    else:
        cna_symbols = {row.get("hgnc_symbol", "") for row in cna_rows}
        for symbol in ["ERBB2", "FGFR2", "MET"]:
            if symbol not in cna_symbols:
                failures.append(f"amplified_target_cna_expression missing {symbol}")

    availability_rows = read_tsv(root / "results/tables/fase5_covariate_availability.tsv")
    availability = {row.get("covariate", ""): row for row in availability_rows}
    if availability.get("Lauren subtype", {}).get("action") != "not_used_for_quantitative_lauren_claims":
        failures.append("fase5_covariate_availability does not block quantitative Lauren claims")
    if availability.get("Tumor purity", {}).get("action") != "not_purity_adjusted_in_fase5":
        failures.append("fase5_covariate_availability does not document missing tumor purity")

    svg = (root / "results/figures/tumor_expression_distribution.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in svg:
        failures.append("tumor_expression_distribution.svg is not a valid SVG")

    note = (root / "docs/fase5_tumor_expression.md").read_text(encoding="utf-8", errors="replace")
    for required_text in ["Fase 5", "E_score", "Lauren", "purity", "cBioPortal GISTIC"]:
        if required_text not in note:
            failures.append(f"fase5_tumor_expression.md missing '{required_text}'")

    return failures


def check_phase6_normal_selectivity(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE6_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})
    tumor_expression = read_tsv(root / "data/processed/tumor_expression.tsv")
    expected_measured = sum(1 for row in tumor_expression if row.get("expression_data_status") == "measured")

    normal_rows = read_tsv(root / "data/processed/normal_expression.tsv")
    if not normal_rows:
        return failures + ["normal_expression.tsv has no rows"]
    missing_columns = REQUIRED_NORMAL_EXPRESSION_COLUMNS - set(normal_rows[0])
    if missing_columns:
        failures.append("normal_expression missing columns: " + ",".join(sorted(missing_columns)))
    if len(normal_rows) != expected_n:
        failures.append(f"normal_expression row count {len(normal_rows)} does not match Core+Probable universe {expected_n}")
    measured_normal = [row for row in normal_rows if row.get("normal_expression_data_status") == "measured"]
    if len(measured_normal) != expected_measured:
        failures.append(f"normal_expression measured count {len(measured_normal)} does not match tumor measured count {expected_measured}")
    seen_symbols: set[str] = set()
    for row in measured_normal:
        symbol = row.get("hgnc_symbol", "")
        if symbol in seen_symbols:
            failures.append(f"normal_expression duplicate symbol {symbol}")
            break
        seen_symbols.add(symbol)
        for field in [
            "n_tumor",
            "n_gtex_stomach_normal",
            "n_tcga_adjacent_normal",
        ]:
            try:
                value = int(row.get(field, "0"))
            except ValueError:
                failures.append(f"invalid {field} for {symbol}")
                continue
            expected = {"n_tumor": 414, "n_gtex_stomach_normal": 175, "n_tcga_adjacent_normal": 36}[field]
            if value != expected:
                failures.append(f"{field} for {symbol} is {value}, expected {expected}")
        for field in [
            "median_tpm_tumor",
            "median_tpm_gtex_stomach",
            "median_tpm_tcga_adjacent_normal",
            "normal_xena_p90_tpm",
            "normal_xena_p95_tpm",
            "max_critical_normal_tpm",
            "gi_normal_max_tpm",
        ]:
            try:
                value = float(row.get(field, "nan"))
            except ValueError:
                failures.append(f"invalid numeric {field} for {symbol}")
                continue
            if value < 0:
                failures.append(f"{field} is negative for {symbol}: {value}")
    cldn18 = next((row for row in normal_rows if row.get("hgnc_symbol") == "CLDN18"), {})
    if "CLDN18_gene_level_isoform_unresolved" not in cldn18.get("gastric_lineage_flag", ""):
        failures.append("CLDN18 lacks Fase 6 gene-level isoform/normal gastric risk flag")

    selectivity_rows = read_tsv(root / "data/processed/selectivity_scores.tsv")
    if not selectivity_rows:
        failures.append("selectivity_scores.tsv has no rows")
    else:
        missing_columns = REQUIRED_SELECTIVITY_COLUMNS - set(selectivity_rows[0])
        if missing_columns:
            failures.append("selectivity_scores missing columns: " + ",".join(sorted(missing_columns)))
        if len(selectivity_rows) != expected_n:
            failures.append(f"selectivity_scores row count {len(selectivity_rows)} does not match Core+Probable universe {expected_n}")
        positive_n_count = 0
        for row in selectivity_rows:
            if row.get("positive_N_stat_rule_gtex") == "true":
                positive_n_count += 1
            if not row.get("N_score"):
                continue
            for field in ["N_score", "N_rank_percentile"]:
                try:
                    value = float(row.get(field, "nan"))
                except ValueError:
                    failures.append(f"invalid {field} for {row.get('hgnc_symbol', '')}")
                    continue
                if not 0 <= value <= 1:
                    failures.append(f"{field} outside [0,1] for {row.get('hgnc_symbol', '')}: {value}")
        if positive_n_count < 100:
            failures.append(f"too few genes meet positive GTEx N rule: {positive_n_count}")

    risk_rows = read_tsv(root / "data/processed/off_tumor_risk.tsv")
    if not risk_rows:
        failures.append("off_tumor_risk.tsv has no rows")
    else:
        missing_columns = REQUIRED_OFF_TUMOR_RISK_COLUMNS - set(risk_rows[0])
        if missing_columns:
            failures.append("off_tumor_risk missing columns: " + ",".join(sorted(missing_columns)))
        if len(risk_rows) != expected_n:
            failures.append(f"off_tumor_risk row count {len(risk_rows)} does not match Core+Probable universe {expected_n}")
        for row in risk_rows:
            if not row.get("R_score"):
                continue
            for field in ["R_score", "R_max", "R_max_plus_breadth", "R_sum_capped"]:
                try:
                    value = float(row.get(field, "nan"))
                except ValueError:
                    failures.append(f"invalid {field} for {row.get('hgnc_symbol', '')}")
                    continue
                if not 0 <= value <= 1:
                    failures.append(f"{field} outside [0,1] for {row.get('hgnc_symbol', '')}: {value}")

    organ_rows = read_tsv(root / "data/processed/organ_penalties.tsv")
    if not organ_rows:
        failures.append("organ_penalties.tsv has no rows")
    else:
        missing_columns = REQUIRED_ORGAN_PENALTY_COLUMNS - set(organ_rows[0])
        if missing_columns:
            failures.append("organ_penalties missing columns: " + ",".join(sorted(missing_columns)))
        if len(organ_rows) != expected_n * len(REQUIRED_CRITICAL_ORGANS):
            failures.append(
                f"organ_penalties row count {len(organ_rows)} does not equal genes x organs {expected_n * len(REQUIRED_CRITICAL_ORGANS)}"
            )
        organs = {row.get("organ", "") for row in organ_rows}
        missing_organs = REQUIRED_CRITICAL_ORGANS - organs
        if missing_organs:
            failures.append("organ_penalties missing organs: " + ",".join(sorted(missing_organs)))
        invalid_categories = {row.get("risk_category", "") for row in organ_rows} - {"critical", "caution", "low", "missing"}
        if invalid_categories:
            failures.append("organ_penalties invalid risk categories: " + ",".join(sorted(invalid_categories)))

    test_rows = read_tsv(root / "data/processed/tumor_normal_tests.tsv")
    if not test_rows:
        failures.append("tumor_normal_tests.tsv has no rows")
    else:
        comparisons = {row.get("comparison", "") for row in test_rows}
        for comparison in ["tumor_vs_gtex_stomach", "tumor_vs_tcga_adjacent"]:
            if comparison not in comparisons:
                failures.append(f"tumor_normal_tests missing {comparison}")
        if len(test_rows) != expected_measured * 2:
            failures.append(f"tumor_normal_tests row count {len(test_rows)} does not equal measured genes x 2 comparisons")
        for row in test_rows:
            for field in ["p_value", "fdr_bh"]:
                try:
                    value = float(row.get(field, "nan"))
                except ValueError:
                    failures.append(f"invalid {field} for {row.get('hgnc_symbol', '')} {row.get('comparison', '')}")
                    continue
                if not 0 <= value <= 1:
                    failures.append(f"{field} outside [0,1] for {row.get('hgnc_symbol', '')}: {value}")

    power_rows = read_tsv(root / "results/tables/tumor_normal_power_analysis.tsv")
    if not power_rows:
        failures.append("tumor_normal_power_analysis.tsv has no rows")
    else:
        comparisons = {row.get("comparison", "") for row in power_rows}
        for comparison in ["tumor_vs_gtex_stomach", "tumor_vs_tcga_adjacent"]:
            rows = [row for row in power_rows if row.get("comparison") == comparison]
            if not rows:
                failures.append(f"tumor_normal_power_analysis missing {comparison}")
                continue
            if not any(row.get("is_min_detectable") == "true" for row in rows):
                failures.append(f"tumor_normal_power_analysis lacks min-detectable row for {comparison}")
            for row in rows:
                if int(row.get("n_tests", "0")) != expected_measured:
                    failures.append(f"tumor_normal_power_analysis n_tests mismatch for {comparison}")
                    break

    sample_counts = read_tsv(root / "results/tables/normal_tissue_sample_counts.tsv")
    counts = {row.get("group_id", ""): int(row.get("n_samples", "0")) for row in sample_counts}
    for group, expected in {
        "tcga_stad_primary_tumor": 414,
        "gtex_stomach_normal": 175,
        "tcga_stad_adjacent_normal": 36,
    }.items():
        if counts.get(group) != expected:
            failures.append(f"normal_tissue_sample_counts {group} is {counts.get(group)}, expected {expected}")

    hpa_rows = read_tsv(root / "results/tables/hpa_normal_protein_by_organ.tsv")
    if not hpa_rows:
        failures.append("hpa_normal_protein_by_organ.tsv has no rows")

    for rel_path in ["results/figures/tumor_vs_normal_critical.svg", "results/figures/tumor_normal_power_curve.svg"]:
        svg = (root / rel_path).read_text(encoding="utf-8", errors="replace")
        if "<svg" not in svg:
            failures.append(f"{rel_path} is not a valid SVG")

    note = (root / "docs/fase6_normal_selectivity_risk.md").read_text(encoding="utf-8", errors="replace")
    for required_text in ["Fase 6", "N_score", "R_score", "CLDN18", "TCGA/GTEx"]:
        if required_text not in note:
            failures.append(f"fase6_normal_selectivity_risk.md missing '{required_text}'")

    return failures


def check_phase7_protein_evidence(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE7_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    protein_rows = read_tsv(root / "data/processed/protein_evidence.tsv")
    if not protein_rows:
        return failures + ["protein_evidence.tsv has no rows"]
    missing_columns = REQUIRED_PROTEIN_EVIDENCE_COLUMNS - set(protein_rows[0])
    if missing_columns:
        failures.append("protein_evidence missing columns: " + ",".join(sorted(missing_columns)))
    if len(protein_rows) != expected_n:
        failures.append(f"protein_evidence row count {len(protein_rows)} does not match Core+Probable universe {expected_n}")

    seen_symbols: set[str] = set()
    computable_p_scores = 0
    flag_counts: dict[str, int] = {}
    for row in protein_rows:
        symbol = row.get("hgnc_symbol", "")
        if symbol in seen_symbols:
            failures.append(f"protein_evidence duplicate symbol {symbol}")
            break
        seen_symbols.add(symbol)

        for field in [
            "hpa_stomach_cancer_present_pct",
            "hpa_stomach_cancer_high_medium_pct",
            "hpa_stomach_cancer_weighted_presence",
            "protein_tumor_presence",
            "membrane_localization_support",
            "normal_protein_safety_support",
            "antibody_validation_support",
            "P_score",
            "P_rank_percentile",
        ]:
            value_text = row.get(field, "")
            if not value_text:
                continue
            try:
                value = float(value_text)
            except ValueError:
                failures.append(f"invalid {field} for {symbol}")
                continue
            if not 0 <= value <= 1:
                failures.append(f"{field} outside [0,1] for {symbol}: {value}")
        if row.get("P_score"):
            computable_p_scores += 1

        if row.get("cptac_status") != "CPTAC_not_assessed":
            failures.append(f"unexpected cptac_status for {symbol}: {row.get('cptac_status')}")
        for flag in [flag for flag in row.get("discordance_flags", "").split(";") if flag]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    if computable_p_scores < 1500:
        failures.append(f"too few computable P_score rows: {computable_p_scores}")
    if flag_counts.get("CPTAC_not_assessed", 0) != len(protein_rows):
        failures.append("CPTAC_not_assessed is not present on every protein_evidence row")
    for flag in sorted(REQUIRED_PROTEIN_DISCORDANCE_FLAGS - {"CPTAC_not_assessed"}):
        if flag_counts.get(flag, 0) == 0:
            failures.append(f"protein_evidence lacks required discordance flag {flag}")

    coverage_rows = read_tsv(root / "results/tables/protein_coverage.tsv")
    if not coverage_rows:
        failures.append("protein_coverage.tsv has no rows")
    else:
        coverage_layers = {row.get("evidence_layer", "") for row in coverage_rows}
        missing_layers = REQUIRED_PROTEIN_COVERAGE_LAYERS - coverage_layers
        if missing_layers:
            failures.append("protein_coverage missing layers: " + ",".join(sorted(missing_layers)))
        coverage_by_layer = {row.get("evidence_layer", ""): row for row in coverage_rows}
        for layer in ["hpa_stomach_cancer_ihc", "protein_evidence_P_score_available"]:
            try:
                covered = int(coverage_by_layer.get(layer, {}).get("n_covered", "0"))
            except ValueError:
                failures.append(f"protein_coverage invalid n_covered for {layer}")
                continue
            if covered < 1500:
                failures.append(f"protein_coverage {layer} below expected MVP coverage: {covered}")
        if coverage_by_layer.get("cptac_proteomics", {}).get("n_covered") != "0":
            failures.append("protein_coverage CPTAC layer should remain explicitly not assessed in Fase 7 MVP")

    svg = (root / "results/figures/rna_protein_concordance.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in svg:
        failures.append("rna_protein_concordance.svg is not a valid SVG")

    note = (root / "docs/fase7_protein_evidence.md").read_text(encoding="utf-8", errors="replace")
    for required_text in ["Fase 7", "P_score", "CPTAC_not_assessed", "antibody IDs"]:
        if required_text not in note:
            failures.append(f"fase7_protein_evidence.md missing '{required_text}'")

    return failures


def check_phase8_single_cell_tme(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE8_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    specificity_rows = read_tsv(root / "data/processed/single_cell_specificity.tsv")
    if not specificity_rows:
        return failures + ["single_cell_specificity.tsv has no rows"]
    missing_columns = REQUIRED_SINGLE_CELL_SPECIFICITY_COLUMNS - set(specificity_rows[0])
    if missing_columns:
        failures.append("single_cell_specificity missing columns: " + ",".join(sorted(missing_columns)))
    if len(specificity_rows) != expected_n:
        failures.append(f"single_cell_specificity row count {len(specificity_rows)} does not match Core+Probable universe {expected_n}")
    labels = {row.get("cellular_specificity_label", "") for row in specificity_rows}
    invalid_labels = labels - ALLOWED_CELLULAR_SPECIFICITY_LABELS
    if invalid_labels:
        failures.append("single_cell_specificity invalid labels: " + ",".join(sorted(invalid_labels)))
    if {row.get("SC_status", "") for row in specificity_rows} != {"not_available"}:
        failures.append("single_cell_specificity should keep SC_status as not_available in MVP fallback")
    if any(row.get("SC_score") for row in specificity_rows):
        failures.append("single_cell_specificity should not impute SC_score in MVP fallback")
    specificity_statuses = {row.get("purity_adjustment_status", "") for row in specificity_rows}
    if specificity_statuses != {"computed_partial_spearman_with_estimate_rnaseq_relative_proxy"}:
        failures.append("single_cell_specificity purity status is not the ESTIMATE partial-correlation status")

    flag_rows = read_tsv(root / "results/tables/tme_contamination_flags.tsv")
    if not flag_rows:
        failures.append("tme_contamination_flags.tsv has no rows")
    else:
        missing_columns = REQUIRED_TME_FLAG_COLUMNS - set(flag_rows[0])
        if missing_columns:
            failures.append("tme_contamination_flags missing columns: " + ",".join(sorted(missing_columns)))
        if len(flag_rows) != expected_n:
            failures.append(f"tme_contamination_flags row count {len(flag_rows)} does not match Core+Probable universe {expected_n}")
        rows_by_symbol = {row.get("hgnc_symbol", ""): row for row in flag_rows}
        for symbol in ["PTPRC", "PECAM1"]:
            row = rows_by_symbol.get(symbol, {})
            if row.get("cellular_specificity_label") != "immune/TME-derived":
                failures.append(f"{symbol} is not labeled immune/TME-derived in Fase 8")
            if row.get("known_tme_control") != "true":
                failures.append(f"{symbol} is not retained as known TME control in Fase 8")
        for symbol in ["ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "MET", "MSLN"]:
            if symbol not in rows_by_symbol:
                failures.append(f"tme_contamination_flags missing benchmark {symbol}")
        for row in flag_rows:
            for field in [
                "max_tme_spearman_rho",
                "combined_tme_spearman_rho",
                "max_tme_partial_spearman_rho",
                "combined_tme_partial_spearman_rho",
            ]:
                value_text = row.get(field, "")
                if not value_text:
                    continue
                try:
                    value = float(value_text)
                except ValueError:
                    failures.append(f"invalid {field} for {row.get('hgnc_symbol', '')}")
                    continue
                if not -1 <= value <= 1:
                    failures.append(f"{field} outside [-1,1] for {row.get('hgnc_symbol', '')}: {value}")
        flag_statuses = {row.get("purity_adjustment_status", "") for row in flag_rows}
        if flag_statuses != {"computed_partial_spearman_with_estimate_rnaseq_relative_proxy"}:
            failures.append("tme_contamination_flags purity status is not the ESTIMATE partial-correlation status")
        flag_sources = {row.get("purity_source", "") for row in flag_rows}
        if flag_sources != {"ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate"}:
            failures.append("tme_contamination_flags purity source is not ESTIMATE/tidyestimate")

    risk_rows = read_tsv(root / "results/tables/tme_contamination_risk_mvp.tsv")
    if len(risk_rows) != len(flag_rows):
        failures.append("tme_contamination_risk_mvp row count does not match tme_contamination_flags")

    correlation_rows = read_tsv(root / "results/tables/tme_module_correlations.tsv")
    if not correlation_rows:
        failures.append("tme_module_correlations.tsv has no rows")
    else:
        modules = {row.get("module_id", "") for row in correlation_rows}
        missing_modules = REQUIRED_TME_MODULES - modules
        if missing_modules:
            failures.append("tme_module_correlations missing modules: " + ",".join(sorted(missing_modules)))
        expected_min_rows = expected_n * len(REQUIRED_TME_MODULES)
        if len(correlation_rows) < expected_min_rows:
            failures.append(f"tme_module_correlations has too few rows: {len(correlation_rows)}")

    coverage_rows = read_tsv(root / "results/tables/tme_module_marker_coverage.tsv")
    if not coverage_rows:
        failures.append("tme_module_marker_coverage.tsv has no rows")
    else:
        modules = {row.get("module_id", "") for row in coverage_rows}
        missing_modules = REQUIRED_TME_MODULES - modules
        if missing_modules:
            failures.append("tme_module_marker_coverage missing modules: " + ",".join(sorted(missing_modules)))
        for row in coverage_rows:
            try:
                available = int(row.get("n_markers_available", "0"))
            except ValueError:
                failures.append(f"invalid marker coverage for {row.get('module_id', '')}")
                continue
            if available < 3:
                failures.append(f"too few available markers for {row.get('module_id', '')}: {available}")

    overlap_rows = read_tsv(root / "results/tables/tme_estimate_marker_overlap.tsv")
    if not overlap_rows:
        failures.append("tme_estimate_marker_overlap.tsv has no rows")
    else:
        missing_columns = REQUIRED_TME_ESTIMATE_OVERLAP_COLUMNS - set(overlap_rows[0])
        if missing_columns:
            failures.append("tme_estimate_marker_overlap missing columns: " + ",".join(sorted(missing_columns)))
        modules = {row.get("module_id", "") for row in overlap_rows}
        missing_modules = REQUIRED_TME_MODULES - modules
        if missing_modules:
            failures.append("tme_estimate_marker_overlap missing modules: " + ",".join(sorted(missing_modules)))
        total_direct_overlap = 0
        for row in overlap_rows:
            try:
                stromal_overlap = int(row.get("n_estimate_stromal_overlap", "0"))
                immune_overlap = int(row.get("n_estimate_immune_overlap", "0"))
                module_markers = int(row.get("n_module_markers", "0"))
            except ValueError:
                failures.append(f"invalid ESTIMATE overlap counts for {row.get('module_id', '')}")
                continue
            if stromal_overlap + immune_overlap > module_markers:
                failures.append(f"ESTIMATE overlap exceeds marker count for {row.get('module_id', '')}")
            total_direct_overlap += stromal_overlap + immune_overlap
            if "collinearity" not in row.get("interpretation_note", ""):
                failures.append(f"ESTIMATE overlap row lacks collinearity note for {row.get('module_id', '')}")
        if total_direct_overlap == 0:
            failures.append("tme_estimate_marker_overlap did not record any direct ESTIMATE/TME marker overlap")

    purity_rows = read_tsv(root / "results/tables/tme_purity_adjusted_correlations.tsv")
    if not purity_rows:
        failures.append("tme_purity_adjusted_correlations.tsv has no rows")
    else:
        missing_columns = REQUIRED_TME_PURITY_COLUMNS - set(purity_rows[0])
        if missing_columns:
            failures.append("tme_purity_adjusted_correlations missing columns: " + ",".join(sorted(missing_columns)))
        if len(purity_rows) != expected_n:
            failures.append(f"tme_purity_adjusted_correlations row count {len(purity_rows)} does not match Core+Probable universe {expected_n}")
        statuses = {row.get("partial_correlation_status", "") for row in purity_rows}
        if statuses != {"computed_partial_spearman_with_estimate_rnaseq_relative_proxy"}:
            failures.append("unexpected Fase 8 purity-adjustment status: " + ",".join(sorted(statuses)))
        purity_sources = {row.get("purity_source", "") for row in purity_rows}
        if purity_sources != {"ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate"}:
            failures.append("unexpected Fase 8 purity source: " + ",".join(sorted(purity_sources)))
        if not any(row.get("tme_contamination_risk_after_purity") == "moderate_purity_confounded" for row in purity_rows):
            failures.append("Fase 8 purity adjustment did not produce any moderate_purity_confounded rescue flags")
        for row in purity_rows:
            for field in ["raw_spearman_rho", "partial_spearman_rho"]:
                value_text = row.get(field, "")
                if not value_text:
                    continue
                try:
                    value = float(value_text)
                except ValueError:
                    failures.append(f"invalid {field} for {row.get('hgnc_symbol', '')}")
                    continue
                if not -1 <= value <= 1:
                    failures.append(f"{field} outside [-1,1] for {row.get('hgnc_symbol', '')}: {value}")
            try:
                purity_n = int(row.get("purity_n_samples", "0"))
            except ValueError:
                failures.append(f"invalid purity_n_samples for {row.get('hgnc_symbol', '')}")
                continue
            if purity_n < 400:
                failures.append(f"too few purity samples for {row.get('hgnc_symbol', '')}: {purity_n}")

    suppression_rows = read_tsv(root / "results/tables/tme_purity_suppression_audit.tsv")
    if not suppression_rows:
        failures.append("tme_purity_suppression_audit.tsv has no rows")
    else:
        missing_columns = REQUIRED_TME_SUPPRESSION_AUDIT_COLUMNS - set(suppression_rows[0])
        if missing_columns:
            failures.append("tme_purity_suppression_audit missing columns: " + ",".join(sorted(missing_columns)))
        expected_suppression = [
            row
            for row in flag_rows
            if row.get("raw_tme_contamination_risk") == "low_uncorrected_tme_correlation"
            and row.get("tme_contamination_risk") == "high_purity_adjusted_tme_correlation"
        ]
        if len(suppression_rows) != len(expected_suppression):
            failures.append(
                f"tme_purity_suppression_audit row count {len(suppression_rows)} does not match low-to-high transitions {len(expected_suppression)}"
            )
        expected_symbols = {row.get("hgnc_symbol", "") for row in expected_suppression}
        audit_symbols = {row.get("hgnc_symbol", "") for row in suppression_rows}
        missing_symbols = expected_symbols - audit_symbols
        extra_symbols = audit_symbols - expected_symbols
        if missing_symbols:
            failures.append("tme_purity_suppression_audit missing symbols: " + ",".join(sorted(missing_symbols)[:20]))
        if extra_symbols:
            failures.append("tme_purity_suppression_audit unexpected symbols: " + ",".join(sorted(extra_symbols)[:20]))
        for row in suppression_rows:
            if row.get("transition") != "low_uncorrected_to_high_purity_adjusted":
                failures.append(f"unexpected suppression transition for {row.get('hgnc_symbol', '')}")
            try:
                raw_value = float(row.get("raw_spearman_rho", "nan"))
                partial_value = float(row.get("partial_spearman_rho", "nan"))
                delta_value = float(row.get("delta_partial_minus_raw", "nan"))
            except ValueError:
                failures.append(f"invalid suppression audit numeric value for {row.get('hgnc_symbol', '')}")
                continue
            if raw_value >= 0.35 or partial_value <= 0.40 or delta_value <= 0:
                failures.append(f"suppression audit thresholds do not match low-to-high transition for {row.get('hgnc_symbol', '')}")
            if "conservative" not in row.get("audit_note", ""):
                failures.append(f"suppression audit row lacks conservative-flag note for {row.get('hgnc_symbol', '')}")

    purity_score_rows = read_tsv(root / "results/tables/tumor_purity_estimate_scores.tsv")
    if not purity_score_rows:
        failures.append("tumor_purity_estimate_scores.tsv has no rows")
    else:
        missing_columns = REQUIRED_TUMOR_PURITY_SCORE_COLUMNS - set(purity_score_rows[0])
        if missing_columns:
            failures.append("tumor_purity_estimate_scores missing columns: " + ",".join(sorted(missing_columns)))
        if len(purity_score_rows) != 414:
            failures.append(f"tumor_purity_estimate_scores row count {len(purity_score_rows)} does not match TCGA-STAD primary tumors 414")
        purity_score_sources = {row.get("purity_source", "") for row in purity_score_rows}
        if purity_score_sources != {"ESTIMATE_tidyestimate_gene_sets_RNAseq_relative_covariate"}:
            failures.append("tumor_purity_estimate_scores purity source is not ESTIMATE/tidyestimate")
        finite_proxy_count = 0
        for row in purity_score_rows:
            if not row.get("sample") or not row.get("patient_id"):
                failures.append("tumor_purity_estimate_scores has blank sample or patient_id")
            for field in ["stromal_score", "immune_score", "estimate_score", "purity_covariate"]:
                value_text = row.get(field, "")
                try:
                    float(value_text)
                except ValueError:
                    failures.append(f"invalid {field} for purity sample {row.get('sample', '')}")
            proxy_text = row.get("estimate_purity_proxy", "")
            if proxy_text:
                try:
                    proxy_value = float(proxy_text)
                except ValueError:
                    failures.append(f"invalid estimate_purity_proxy for purity sample {row.get('sample', '')}")
                else:
                    if not 0 <= proxy_value <= 1:
                        failures.append(f"estimate_purity_proxy outside [0,1] for {row.get('sample', '')}: {proxy_value}")
                    finite_proxy_count += 1
        if finite_proxy_count < 300:
            failures.append(f"too few finite ESTIMATE purity proxy values: {finite_proxy_count}")

    purity_checksum_rows = read_tsv(root / "data/checksums/tcga_purity_sha256.tsv")
    if not purity_checksum_rows:
        failures.append("tcga_purity_sha256.tsv has no rows")
    else:
        rows_by_source = {row.get("source_id", ""): row for row in purity_checksum_rows}
        for source_id in ["tidyestimate_cran", "tidyestimate_gene_sets"]:
            row = rows_by_source.get(source_id)
            if not row:
                failures.append(f"tcga_purity_sha256.tsv missing {source_id}")
                continue
            local_path = root / row.get("local_path", "")
            if not local_path.exists():
                failures.append(f"tcga_purity checksum path missing: {local_path}")
                continue
            expected_sha = row.get("sha256", "")
            if len(expected_sha) != 64:
                failures.append(f"tcga_purity checksum for {source_id} is not SHA-256 length")
            elif sha256_file(local_path) != expected_sha:
                failures.append(f"tcga_purity checksum mismatch for {source_id}")
            if row.get("status") != "ok":
                failures.append(f"tcga_purity checksum row {source_id} status is not ok")

    svg = (root / "results/figures/top_candidates_scRNA_dotplot.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in svg:
        failures.append("top_candidates_scRNA_dotplot.svg is not a valid SVG")

    note = (root / "docs/fase8_single_cell_tme_specificity.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 8",
        "SC",
        "not_available",
        "TME",
        "purity",
        "ESTIMATE",
        "partial Spearman",
        "Collinearity",
        "tme_purity_suppression_audit.tsv",
    ]:
        if required_text not in note:
            failures.append(f"fase8_single_cell_tme_specificity.md missing '{required_text}'")

    return failures


def check_phase9_topology_isoforms(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE9_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    topology_rows = read_tsv(root / "data/processed/topology_isoforms_ecd.tsv")
    if not topology_rows:
        return failures + ["topology_isoforms_ecd.tsv has no rows"]
    missing_columns = REQUIRED_TOPOLOGY_COLUMNS - set(topology_rows[0])
    if missing_columns:
        failures.append("topology_isoforms_ecd missing columns: " + ",".join(sorted(missing_columns)))
    if len(topology_rows) != expected_n:
        failures.append(f"topology_isoforms_ecd row count {len(topology_rows)} does not match Core+Probable universe {expected_n}")

    rows_by_symbol = {row.get("hgnc_symbol", ""): row for row in topology_rows}
    classes = {row.get("accessibility_class", "") for row in topology_rows}
    invalid_classes = classes - ALLOWED_ACCESSIBILITY_CLASSES
    if invalid_classes:
        failures.append("invalid accessibility classes: " + ",".join(sorted(invalid_classes)))
    if not {"A", "B", "C", "D", "E"}.issubset(classes):
        failures.append("Fase 9 accessibility classes do not include A/B/C/D/E coverage")

    for row in topology_rows:
        symbol = row.get("hgnc_symbol", "")
        if row.get("uniprot_feature_status") != "reviewed_human_features_found":
            failures.append(f"{symbol} lacks reviewed UniProt feature coverage")
        for field in [
            "topology_confidence",
            "accessibility_class_score",
            "extracellular_length_score",
            "isoform_confidence",
            "shedding_penalty",
            "soluble_decoy_penalty",
            "T_score",
            "T_rank_percentile",
        ]:
            value_text = row.get(field, "")
            try:
                value = float(value_text)
            except ValueError:
                failures.append(f"invalid {field} for {symbol}")
                continue
            if field in {"shedding_penalty", "soluble_decoy_penalty"}:
                if value < 0:
                    failures.append(f"{field} below 0 for {symbol}")
            elif not 0 <= value <= 1:
                failures.append(f"{field} outside [0,1] for {symbol}: {value}")
        for integer_field in [
            "protein_length_aa",
            "tm_helix_count",
            "extracellular_segment_count",
            "total_extracellular_aa",
            "largest_extracellular_loop_aa",
            "glycosylation_site_count",
            "disulfide_bond_count",
            "isoform_count",
        ]:
            value_text = row.get(integer_field, "")
            if value_text == "" and integer_field == "protein_length_aa":
                failures.append(f"blank protein length for {symbol}")
                continue
            try:
                value = int(value_text or "0")
            except ValueError:
                failures.append(f"invalid integer {integer_field} for {symbol}")
                continue
            if value < 0:
                failures.append(f"negative {integer_field} for {symbol}")

    expected_controls = {
        "ERBB2": "A",
        "TACSTD2": "A",
        "EPCAM": "A",
        "MET": "A",
        "CLDN18": "C",
        "FGFR2": "A",
        "MSLN": "A",
    }
    for symbol, expected_class in expected_controls.items():
        row = rows_by_symbol.get(symbol, {})
        if not row:
            failures.append(f"{symbol} missing from Fase 9 topology table")
            continue
        if row.get("accessibility_class") != expected_class:
            failures.append(f"{symbol} accessibility class {row.get('accessibility_class')} != expected {expected_class}")
    if rows_by_symbol.get("MSLN", {}).get("gpi_anchor_present") != "true":
        failures.append("MSLN GPI anchor was not captured in Fase 9")
    if "CLDN18.2_isoform_unresolved_gene_level_only" not in rows_by_symbol.get("CLDN18", {}).get("isoform_resolution_status", ""):
        failures.append("CLDN18 lacks CLDN18.2 unresolved isoform status in Fase 9")
    if "FGFR2b_isoform_unresolved_gene_level_only" not in rows_by_symbol.get("FGFR2", {}).get("isoform_resolution_status", ""):
        failures.append("FGFR2 lacks FGFR2b unresolved isoform status in Fase 9")

    flag_rows = read_tsv(root / "results/tables/isoform_risk_flags.tsv")
    if not flag_rows:
        failures.append("isoform_risk_flags.tsv has no rows")
    else:
        missing_columns = REQUIRED_ISOFORM_FLAG_COLUMNS - set(flag_rows[0])
        if missing_columns:
            failures.append("isoform_risk_flags missing columns: " + ",".join(sorted(missing_columns)))
        issues_by_symbol = {}
        for row in flag_rows:
            issues_by_symbol.setdefault(row.get("hgnc_symbol", ""), set()).add(row.get("isoform_or_topology_issue", ""))
        if "CLDN18.2_isoform_unresolved_gene_level_only" not in issues_by_symbol.get("CLDN18", set()):
            failures.append("isoform_risk_flags missing CLDN18.2 unresolved flag")
        if "FGFR2b_isoform_unresolved_gene_level_only" not in issues_by_symbol.get("FGFR2", set()):
            failures.append("isoform_risk_flags missing FGFR2b unresolved flag")
        if not any(issue.startswith("accessibility_class_E") for issues in issues_by_symbol.values() for issue in issues):
            failures.append("isoform_risk_flags has no accessibility_class_E flags")

    checksum_rows = read_tsv(root / "data/checksums/uniprot_phase9_features_sha256.tsv")
    if not checksum_rows:
        failures.append("uniprot_phase9_features_sha256.tsv has no rows")
    else:
        row = checksum_rows[0]
        local_path = root / row.get("local_path", "")
        if not local_path.exists():
            failures.append(f"UniProt Fase 9 checksum path missing: {local_path}")
        elif sha256_file(local_path) != row.get("sha256", ""):
            failures.append("UniProt Fase 9 feature checksum mismatch")
        if row.get("status") != "ok":
            failures.append("UniProt Fase 9 checksum status is not ok")

    svg = (root / "results/figures/ecd_length_distribution.svg").read_text(encoding="utf-8", errors="replace")
    if "<svg" not in svg:
        failures.append("ecd_length_distribution.svg is not a valid SVG")

    note = (root / "docs/fase9_topology_isoforms.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 9",
        "T_score",
        "CLDN18.2",
        "FGFR2b",
        "isoform_unresolved",
        "MSLN",
        "GPI-anchor",
        "not a final biological ranking",
    ]:
        if required_text not in note:
            failures.append(f"fase9_topology_isoforms.md missing '{required_text}'")

    return failures


def check_phase13_mvp_scoring(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE13_FILES if not (root / path).exists()]
    if failures:
        return failures

    universe = read_tsv(root / "data/processed/surfaceome_universe.tsv")
    expected_n = sum(1 for row in universe if row.get("surfaceome_category") in {"core_surfaceome", "probable_surfaceome"})

    components = read_tsv(root / "results/tables/component_scores_all_candidates.tsv")
    if not components:
        return failures + ["component_scores_all_candidates.tsv has no rows"]
    missing_columns = REQUIRED_COMPONENT_SCORE_COLUMNS - set(components[0])
    if missing_columns:
        failures.append("component_scores_all_candidates missing columns: " + ",".join(sorted(missing_columns)))
    if len(components) != expected_n:
        failures.append(f"component score row count {len(components)} does not match Core+Probable universe {expected_n}")

    for row in components:
        symbol = row.get("hgnc_symbol", "")
        if row.get("SC_status") != "not_available":
            failures.append(f"{symbol} SC_status is not not_available")
        if row.get("SC_rank_percentile", ""):
            failures.append(f"{symbol} has SC_rank_percentile despite MVP SC not_available")
        if row.get("SC_component_status") != "not_available_not_counted_in_mvp_missingness":
            failures.append(f"{symbol} has unexpected SC_component_status")
        if row.get("Surf_scaling_method") != "theoretical_minmax_5_10_after_fase4_gpi":
            failures.append(f"{symbol} has unexpected Surf_scaling_method")
        for field in [
            "Surf_relative_confidence",
            "E_rank_percentile",
            "N_rank_percentile",
            "R_rank_percentile_high_worse",
            "P_rank_percentile",
            "T_rank_percentile",
        ]:
            value_text = row.get(field, "")
            if value_text == "":
                continue
            try:
                value = float(value_text)
            except ValueError:
                failures.append(f"invalid {field} for {symbol}")
                continue
            if not 0 <= value <= 1:
                failures.append(f"{field} outside [0,1] for {symbol}: {value}")
        try:
            missing_n = int(row.get("n_missing_mvp_score_components", ""))
            available_n = int(row.get("n_available_mvp_score_components", ""))
        except ValueError:
            failures.append(f"invalid missing/available component counts for {symbol}")
            continue
        if missing_n + available_n != 6:
            failures.append(f"{symbol} missing+available MVP component count != 6")

    config_hash = sha256_file(root / "config/scoring_scenarios.yaml")
    ranking_files = {
        "balanced": "results/rankings/ranking_balanced.tsv",
        "safety_first": "results/rankings/ranking_safety_first.tsv",
        "adc_focused": "results/rankings/ranking_adc_focused.tsv",
        "novelty_focused": "results/rankings/ranking_novelty.tsv",
        "protein_first": "results/rankings/ranking_protein_first.tsv",
    }
    balanced_rows: list[dict[str, str]] = []
    for scenario, rel_path in ranking_files.items():
        rows = read_tsv(root / rel_path)
        if not rows:
            failures.append(f"{rel_path} has no rows")
            continue
        if scenario == "balanced":
            balanced_rows = rows
        missing_columns = REQUIRED_RANKING_COLUMNS - set(rows[0])
        if missing_columns:
            failures.append(f"{rel_path} missing columns: " + ",".join(sorted(missing_columns)))
        sidecar_columns = RANKING_SIDECAR_COLUMNS & set(rows[0])
        if sidecar_columns:
            failures.append(
                f"{rel_path} contains file-level metadata columns that should live in a sidecar: "
                + ",".join(sorted(sidecar_columns))
            )
        if len(rows) != expected_n:
            failures.append(f"{rel_path} row count {len(rows)} does not match Core+Probable universe {expected_n}")
        ranks = []
        for row in rows:
            if row.get("scenario") != scenario:
                failures.append(f"{rel_path} contains scenario {row.get('scenario')} instead of {scenario}")
            if row.get("SC_status") != "not_available":
                failures.append(f"{rel_path} SC_status not not_available for {row.get('hgnc_symbol')}")
            try:
                score = float(row.get("scenario_score", ""))
            except ValueError:
                failures.append(f"{rel_path} invalid scenario score for {row.get('hgnc_symbol')}")
                continue
            if not -1 <= score <= 1:
                failures.append(f"{rel_path} scenario score outside [-1,1] for {row.get('hgnc_symbol')}: {score}")
            if row.get("R_contribution_subtracted", ""):
                try:
                    r_contribution = float(row["R_contribution_subtracted"])
                except ValueError:
                    failures.append(f"{rel_path} invalid R contribution for {row.get('hgnc_symbol')}")
                else:
                    if r_contribution > 0:
                        failures.append(f"{rel_path} R contribution is positive for {row.get('hgnc_symbol')}")
            try:
                ranks.append(int(row.get("rank", "")))
            except ValueError:
                failures.append(f"{rel_path} invalid rank for {row.get('hgnc_symbol')}")
        if ranks and sorted(ranks) != list(range(1, expected_n + 1)):
            failures.append(f"{rel_path} ranks are not 1..{expected_n}")

    frozen_v0_rows = read_tsv(root / "results/rankings/ranking_v0_frozen.tsv")
    if not frozen_v0_rows:
        failures.append("ranking_v0_frozen has no rows")
    for row in frozen_v0_rows[:10]:
        if row.get("freeze_version") != "v0":
            failures.append("ranking_v0_frozen has non-v0 freeze_version")
        if row.get("ranking_status") != "preliminary_fase13_mvp_not_final_tiering":
            failures.append("ranking_v0_frozen has non-preliminary ranking_status")

    frozen_v1_rows = read_tsv(root / "results/rankings/ranking_v1_frozen.tsv")
    if not frozen_v1_rows:
        failures.append("ranking_v1_frozen has no rows")
    for row in frozen_v1_rows[:10]:
        if row.get("freeze_version") != "v1":
            failures.append("ranking_v1_frozen has non-v1 freeze_version")
        if row.get("ranking_status") != "preliminary_fase13_mvp_not_final_tiering":
            failures.append("ranking_v1_frozen has non-preliminary ranking_status")
        if "Surf_relative_confidence" not in row:
            failures.append("ranking_v1_frozen missing Surf_relative_confidence")

    frozen_v2_rows = read_tsv(root / "results/rankings/ranking_v2_frozen.tsv")
    if len(frozen_v2_rows) != expected_n:
        failures.append("ranking_v2_frozen row count does not match current Core+Probable universe")
    if frozen_v2_rows:
        sidecar_columns = RANKING_SIDECAR_COLUMNS & set(frozen_v2_rows[0])
        if sidecar_columns:
            failures.append(
                "ranking_v2_frozen.tsv still contains sidecar metadata columns: "
                + ",".join(sorted(sidecar_columns))
            )
        for row in frozen_v2_rows[:10]:
            if "Surf_relative_confidence" not in row:
                failures.append("ranking_v2_frozen missing Surf_relative_confidence")
    metadata_path = root / "results/rankings/ranking_v2_frozen.metadata.yaml"
    metadata = read_yaml(metadata_path) if metadata_path.exists() else {}
    if not metadata:
        failures.append("ranking_v2_frozen.metadata.yaml is missing or empty")
    else:
        ranking_hash = sha256_file(root / "results/rankings/ranking_v2_frozen.tsv")
        if metadata.get("ranking_sha256") != ranking_hash:
            failures.append("ranking_v2_frozen metadata hash does not match ranking TSV")
        if metadata.get("row_count") != expected_n:
            failures.append("ranking_v2_frozen metadata row_count does not match Core+Probable universe")
        if metadata.get("freeze_version") != "v2":
            failures.append("ranking_v2_frozen metadata has non-v2 freeze_version")
        if metadata.get("ranking_status") != "preliminary_fase13_mvp_not_final_tiering":
            failures.append("ranking_v2_frozen metadata has non-preliminary ranking_status")
        if metadata.get("score_config_sha256") != config_hash:
            failures.append("ranking_v2_frozen metadata config hash mismatch")

    robust_rows = read_tsv(root / "results/rankings/ranking_robust_aggregate.tsv")
    if len(robust_rows) != expected_n:
        failures.append("ranking_robust_aggregate row count does not match Core+Probable universe")
    elif "robust_aggregate_rank" not in robust_rows[0]:
        failures.append("ranking_robust_aggregate missing robust_aggregate_rank")

    tiering_rows = read_tsv(root / "results/tables/tiering_annotations_all_candidates.tsv")
    if not tiering_rows:
        failures.append("tiering_annotations_all_candidates.tsv has no rows")
    else:
        missing_columns = REQUIRED_TIERING_ANNOTATION_COLUMNS - set(tiering_rows[0])
        if missing_columns:
            failures.append("tiering annotations missing columns: " + ",".join(sorted(missing_columns)))
        invalid_final = [
            row.get("hgnc_symbol", "")
            for row in tiering_rows
            if row.get("annotation_status") != "pre_tiering_annotation_not_final_tier"
        ]
        if invalid_final:
            failures.append("tiering annotations contain final-tier-like statuses")

    control_rows = read_tsv(root / "results/tables/control_recovery_phase13.tsv")
    if not control_rows:
        failures.append("control_recovery_phase13.tsv has no rows")
    else:
        missing_columns = REQUIRED_CONTROL_RECOVERY_COLUMNS - set(control_rows[0])
        if missing_columns:
            failures.append("control recovery missing columns: " + ",".join(sorted(missing_columns)))
        expected_controls = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "CEACAM5", "MET", "MSLN", "PTPRC", "PECAM1"}
        observed_controls = {row.get("hgnc_symbol", "") for row in control_rows}
        missing_controls = expected_controls - observed_controls
        if missing_controls:
            failures.append("control recovery missing controls: " + ",".join(sorted(missing_controls)))

    functional_rows = read_tsv(root / "results/validation/functional_form_sensitivity.tsv")
    methods = {row.get("method", "") for row in functional_rows}
    missing_methods = REQUIRED_FUNCTIONAL_FORM_METHODS - methods
    if missing_methods:
        failures.append("functional_form_sensitivity missing methods: " + ",".join(sorted(missing_methods)))

    sanity_rows = read_tsv(root / "results/validation/phase13_post_scoring_sanity.tsv")
    sanity_checks = {row.get("check", "") for row in sanity_rows}
    missing_checks = REQUIRED_PHASE13_SANITY_CHECKS - sanity_checks
    if missing_checks:
        failures.append("phase13_post_scoring_sanity missing checks: " + ",".join(sorted(missing_checks)))
    sanity_by_check = {row.get("check", ""): row for row in sanity_rows}
    if sanity_by_check.get("negative_controls_top100", {}).get("status") != "pass":
        failures.append("negative_controls_top100 sanity check did not pass")
    if sanity_by_check.get("positive_controls_top50", {}).get("status") not in {"pass", "diagnostic_required_before_fase14"}:
        failures.append("positive_controls_top50 sanity check has unexpected status")

    note = (root / "docs/fase13_mvp_score_integration.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 13",
        "preliminary MVP integrated score",
        "SC` remains `not_available",
        "Surf_relative_confidence",
        "ranking_v2_frozen.tsv",
        "not final biological tiers",
        "diagnostic_required_before_fase14",
        "docs/limitations_register.md",
    ]:
        if required_text not in note:
            failures.append(f"fase13_mvp_score_integration.md missing '{required_text}'")

    limitations = (root / "docs/limitations_register.md").read_text(encoding="utf-8", errors="replace")
    limitations_lower = limitations.lower()
    for required_text in ["Fase 10", "Fase 11", "Fase 12", "deferred", "SC=not_available"]:
        haystack = limitations_lower if required_text == "deferred" else limitations
        if required_text not in haystack:
            failures.append(f"limitations_register.md missing '{required_text}'")

    if balanced_rows:
        top20_missing_p = [row.get("hgnc_symbol", "") for row in balanced_rows[:20] if row.get("P_score", "") == ""]
        if top20_missing_p and "Top 20 Balanced with missing `P`" not in note:
            failures.append("Fase 13 note does not document top20 missing P diagnostic")

    diagnostic_note = (root / "docs/fase13_diagnostico.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Surf_relative_confidence",
        "ranking_v1_frozen.tsv",
        "ranking_v2_frozen.tsv",
        "eligible_for_fase14",
        "fase13_positive_control_causal_gate.tsv",
        "v0",
        "v1",
        "GPI",
        "average-rank",
        "fase13_component_transform_audit.tsv",
        "Correccion de labels causales",
    ]:
        if required_text not in diagnostic_note:
            failures.append(f"fase13_diagnostico.md missing '{required_text}'")

    transform_rows = read_tsv(root / "results/tables/fase13_component_transform_audit.tsv")
    transform_components = {row.get("component", "") for row in transform_rows}
    expected_transform_components = {"Surf", "E", "N", "R", "P", "T", "SC"}
    if transform_components != expected_transform_components:
        failures.append(
            "fase13_component_transform_audit components mismatch: "
            + ",".join(sorted(expected_transform_components - transform_components))
        )
    for row in transform_rows:
        if row.get("component") == "Surf" and row.get("v1_action") != "replace_v0_ordinal_percentile_with_theoretical_scale_5_10_after_gpi":
            failures.append("fase13 transform audit does not record Surf theoretical-scale fix after GPI")
        if row.get("component") == "R" and row.get("v1_action") != "average_rank_ties":
            failures.append("fase13 transform audit does not record R average-rank tie handling")

    diagnostic_rows = read_tsv(root / "results/tables/fase13_positive_control_component_diagnostic.tsv")
    if not diagnostic_rows:
        failures.append("fase13_positive_control_component_diagnostic.tsv has no rows")
    else:
        observed = {row.get("hgnc_symbol", "") for row in diagnostic_rows}
        expected = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "CEACAM5", "MET", "MSLN"}
        missing = expected - observed
        if missing:
            failures.append("fase13 positive diagnostic missing controls: " + ",".join(sorted(missing)))
        if "Surf_relative_confidence_v1" not in diagnostic_rows[0]:
            failures.append("fase13 positive diagnostic missing Surf_relative_confidence_v1")

    causal_rows = read_tsv(root / "results/tables/fase13_positive_control_causal_gate.tsv")
    if not causal_rows:
        failures.append("fase13_positive_control_causal_gate.tsv has no rows")
    else:
        observed = {row.get("hgnc_symbol", "") for row in causal_rows}
        expected = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "CEACAM5", "MET", "MSLN"}
        missing = expected - observed
        if missing:
            failures.append("fase13 causal gate missing controls: " + ",".join(sorted(missing)))
        pipeline_failures = [
            row.get("hgnc_symbol", "")
            for row in causal_rows
            if row.get("pipeline_accusing_failure", "").lower() == "true"
        ]
        if pipeline_failures:
            failures.append("fase13 causal gate has pipeline-accusing failures: " + ",".join(sorted(pipeline_failures)))
        if not any(row.get("causal_class_v1") == "expected_mid_surface_confidence_and_weaker_protein_support" for row in causal_rows):
            failures.append("fase13 causal gate does not classify TACSTD2 mid surface/protein-support cause")

    gpi_route_note = (root / "docs/fase13_gpi_membership_route.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 13 GPI Membership Route Audit",
        "Confirmed GPI",
        "Route Decision",
        "fase13_gpi_membership_route_audit.tsv",
        "does not change Fase 4",
    ]:
        if required_text not in gpi_route_note:
            failures.append(f"fase13_gpi_membership_route.md missing '{required_text}'")

    gpi_route_rows = read_tsv(root / "results/tables/fase13_gpi_membership_route_summary.tsv")
    if not gpi_route_rows:
        failures.append("fase13_gpi_membership_route_summary.tsv has no rows")
    else:
        metrics = {row.get("metric", "") for row in gpi_route_rows}
        required_metrics = {
            "confirmed_uniprot_lipid_gpi_anchor_symbols",
            "subcellular_gpi_without_lipid_feature_symbols",
            "confirmed_current_core_probable",
            "confirmed_outside_core_probable",
            "confirmed_gpi_already_integrated_in_fase4",
            "confirmed_outside_enter_plus1_anchor_support",
            "confirmed_outside_enter_plus2_strong_anchor",
            "route_decision",
        }
        missing_metrics = required_metrics - metrics
        if missing_metrics:
            failures.append("fase13 GPI membership summary missing metrics: " + ",".join(sorted(missing_metrics)))
        route_values = {row.get("route_decision", "") for row in gpi_route_rows}
        allowed_routes = {
            "reopen_fase4_required_before_gpi_credit",
            "fase13_gpi_scoring_correction_membership_invariant_available",
            "fase4_gpi_evidence_correction_applied",
        }
        if not route_values <= allowed_routes:
            failures.append("fase13 GPI membership summary has unexpected route decisions")

    gpi_route_audit = read_tsv(root / "results/tables/fase13_gpi_membership_route_audit.tsv")
    if not gpi_route_audit:
        failures.append("fase13_gpi_membership_route_audit.tsv has no rows")
    else:
        required_columns = {
            "hgnc_symbol",
            "gpi_evidence_class",
            "current_category",
            "plus1_anchor_category",
            "plus2_strong_category",
            "counted_in_confirmed_membership_gate",
            "gpi_credit_already_integrated_in_fase4",
            "route_note",
        }
        missing_columns = required_columns - set(gpi_route_audit[0])
        if missing_columns:
            failures.append("fase13 GPI membership audit missing columns: " + ",".join(sorted(missing_columns)))

    delta_rows = read_tsv(root / "results/tables/fase13_v0_v1_rank_delta.tsv")
    if not delta_rows:
        failures.append("fase13_v0_v1_rank_delta.tsv has no rows")

    return failures


def check_phase14_preflight(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE14_PREFLIGHT_FILES if not (root / path).exists()]
    if failures:
        return failures

    top50_rows = read_tsv(root / "results/tables/fase14_preflight_top50_v1_v2_audit.tsv")
    if len(top50_rows) != 50:
        failures.append(f"fase14 preflight top50 audit has {len(top50_rows)} rows instead of 50")
    elif "preflight_classification" not in top50_rows[0]:
        failures.append("fase14 preflight top50 audit missing preflight_classification")
    else:
        suspicious = [
            row.get("hgnc_symbol", "")
            for row in top50_rows
            if row.get("preflight_classification") == "new_suspicious_surf_dominant"
        ]
        if suspicious:
            failures.append("fase14 preflight top50 audit has suspicious Surf-dominant new entries: " + ",".join(suspicious))
        new_rows = [row for row in top50_rows if row.get("new_in_v2_top50_vs_v1") == "true"]
        if not new_rows:
            failures.append("fase14 preflight top50 audit should record v2 top50 movement versus v1")
        for row in new_rows:
            try:
                support_n = int(row.get("non_surf_support_count", ""))
            except ValueError:
                failures.append(f"invalid non_surf_support_count for {row.get('hgnc_symbol', '')}")
                continue
            if support_n < 3:
                failures.append(f"{row.get('hgnc_symbol', '')} entered v2 top50 with weak non-Surf support")

    snapshot_rows = read_tsv(root / "results/tables/fase14_preflight_snapshot_integrity.tsv")
    if not snapshot_rows:
        failures.append("fase14 preflight snapshot integrity table has no rows")
    else:
        expected_paths = {
            "results/rankings/ranking_v0_frozen.tsv",
            "results/rankings/ranking_v1_frozen.tsv",
            "results/rankings/ranking_v2_frozen.tsv",
            "config/scoring_scenarios.yaml",
            "config/parameters.yaml",
        }
        observed_paths = {row.get("path", "") for row in snapshot_rows}
        missing_paths = expected_paths - observed_paths
        if missing_paths:
            failures.append("fase14 preflight snapshot table missing paths: " + ",".join(sorted(missing_paths)))
        bad_status = [
            row.get("path", "")
            for row in snapshot_rows
            if row.get("status") != "pass" or row.get("sha256_matches_phase13_snapshot") != "true"
        ]
        if bad_status:
            failures.append("fase14 preflight snapshot integrity did not pass for: " + ",".join(bad_status))

    stability_rows = read_tsv(root / "results/tables/fase14_preflight_universe_stability.tsv")
    groups = {row.get("comparison_group", ""): row for row in stability_rows}
    expected_groups = {"common_non_gpi", "common_gpi", "common_all"}
    if set(groups) != expected_groups:
        failures.append("fase14 preflight universe stability groups mismatch")
    else:
        non_gpi = groups["common_non_gpi"]
        try:
            spearman_value = float(non_gpi.get("rank_spearman_v1_v2", ""))
        except ValueError:
            failures.append("fase14 preflight common non-GPI Spearman is not numeric")
        else:
            if spearman_value < 0.85:
                failures.append(f"common non-GPI v1/v2 Spearman below preregistered threshold: {spearman_value}")
        if non_gpi.get("threshold_status") != "pass":
            failures.append("common non-GPI universe/evidence-rule stability gate did not pass")
        if groups["common_gpi"].get("threshold_status") != "descriptive_not_gated":
            failures.append("common GPI stability should remain descriptive_not_gated")

    note = (root / "docs/fase14_preflight.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 14 Preflight",
        "does not run perturbation",
        "A Priori Fase 14 Thresholds",
        "ranking_v2_frozen.tsv",
        "common non-GPI",
        "0.85",
        "eligible_for_fase14",
        "universe/evidence-rule stability",
        "not final biological tiers",
    ]:
        if required_text not in note:
            failures.append(f"fase14_preflight.md missing '{required_text}'")

    return failures


def check_phase14_stability(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE14_STABILITY_FILES if not (root / path).exists()]
    if failures:
        return failures

    baseline_rows = read_tsv(root / "results/rankings/ranking_v2_frozen.tsv")
    expected_n = len(baseline_rows)

    rank_rows = read_tsv(root / "results/validation/rank_stability.tsv")
    if len(rank_rows) != expected_n:
        failures.append(f"rank_stability row count {len(rank_rows)} does not match ranking_v2 {expected_n}")
    else:
        required_columns = {
            "hgnc_symbol",
            "baseline_rank_v2",
            "balanced_weight_perturb_top20_frequency",
            "leave_one_layer_max_abs_delta",
            "post_scoring_resolution_top20_frequency",
            "tier1_stability_precheck_not_final_tier",
            "analysis_status",
        }
        missing_columns = required_columns - set(rank_rows[0])
        if missing_columns:
            failures.append("rank_stability missing columns: " + ",".join(sorted(missing_columns)))
        invalid_status = [
            row.get("hgnc_symbol", "")
            for row in rank_rows[:100]
            if row.get("analysis_status") != "stability_precheck_not_final_tiering"
        ]
        if invalid_status:
            failures.append("rank_stability contains final-tier-like status")
        top20 = [row for row in rank_rows if int(row.get("baseline_rank_v2", "999999")) <= 20]
        if len(top20) != 20:
            failures.append("rank_stability does not identify exactly 20 baseline top20 rows")
        else:
            passing = [
                row
                for row in top20
                if row.get("tier1_stability_precheck_not_final_tier") == "passes_top20_frequency_only"
            ]
            if len(passing) < 10:
                failures.append("fewer than 10 baseline top20 genes pass the preregistered top20-frequency precheck")

    loo_rows = read_tsv(root / "results/validation/leave_one_layer_out.tsv")
    if len(loo_rows) != expected_n * 6:
        failures.append("leave_one_layer_out row count should equal ranking_v2 rows x six MVP components")
    else:
        observed_layers = {row.get("omitted_layer", "") for row in loo_rows}
        if observed_layers != {"Surf", "E", "N", "R", "P", "T"}:
            failures.append("leave_one_layer_out omitted layer set mismatch")

    weight_rows = read_tsv(root / "results/validation/weight_perturbation_summary.tsv")
    if len(weight_rows) != 250:
        failures.append(f"weight_perturbation_summary expected 250 MVP perturbations, observed {len(weight_rows)}")
    elif not all(row.get("spearman_gate") == "pass" for row in weight_rows):
        failures.append("at least one weight perturbation fell below the preregistered Spearman gate")

    organ_rows = read_tsv(root / "results/validation/organ_weight_perturbation.tsv")
    if len(organ_rows) != 50:
        failures.append(f"organ_weight_perturbation expected 50 MVP perturbations, observed {len(organ_rows)}")

    missing_rows = read_tsv(root / "results/validation/missing_data_sensitivity.tsv")
    scenarios = {row.get("missing_data_scenario", "") for row in missing_rows}
    if scenarios != {"exclude_and_renormalize", "p25", "p50", "p75"}:
        failures.append("missing_data_sensitivity scenarios mismatch")
    if len(missing_rows) != expected_n * 4:
        failures.append("missing_data_sensitivity row count should equal ranking_v2 rows x four scenarios")

    risk_form_rows = read_tsv(root / "results/validation/risk_functional_form_sensitivity.tsv")
    risk_forms = {row.get("risk_form", "") for row in risk_form_rows}
    if risk_forms != {"R_max", "R_max_plus_breadth", "R_sum_capped"}:
        failures.append("risk_functional_form_sensitivity risk forms mismatch")

    risk_threshold_rows = read_tsv(root / "results/validation/risk_threshold_sensitivity.tsv")
    threshold_scenarios = {row.get("risk_threshold_scenario", "") for row in risk_threshold_rows}
    if threshold_scenarios != {"p50_p75", "p60_p80", "absolute_tpm_1_5"}:
        failures.append("risk_threshold_sensitivity scenarios mismatch")

    resolution_rows = read_tsv(root / "results/validation/ranking_resolution_post_scoring.tsv")
    if len(resolution_rows) != expected_n:
        failures.append("ranking_resolution_post_scoring row count does not match ranking_v2")
    summary_rows = read_tsv(root / "results/validation/ranking_resolution_post_scoring_summary.tsv")
    summary_by_metric = {row.get("metric", ""): row for row in summary_rows}
    if summary_by_metric.get("top20_with_ci_contained_in_top40", {}).get("status") != "coarse_tiering_recommended":
        failures.append("Fase 14 post-scoring resolution should document coarse_tiering_recommended")

    control_rows = read_tsv(root / "results/validation/control_benchmark.tsv")
    expected_controls = {"ERBB2", "CLDN18", "FGFR2", "TACSTD2", "EPCAM", "CEACAM5", "MET", "MSLN", "PTPRC", "PECAM1"}
    observed_controls = {row.get("hgnc_symbol", "") for row in control_rows}
    missing_controls = expected_controls - observed_controls
    if missing_controls:
        failures.append("control_benchmark missing controls: " + ",".join(sorted(missing_controls)))

    audit_rows = read_tsv(root / "results/validation/top30_false_positive_audit.tsv")
    if len(audit_rows) != 30:
        failures.append("top30_false_positive_audit should have 30 rows")
    elif not all(row.get("manual_review_status") == "not_manual_reviewed_fase14_auto_flag_only" for row in audit_rows):
        failures.append("top30_false_positive_audit should remain automated-only before Fase 15")

    for rel_path in ["results/figures/rank_stability_heatmap.svg", "results/figures/bumpchart_scenarios.svg"]:
        svg = (root / rel_path).read_text(encoding="utf-8", errors="replace")
        if "<svg" not in svg:
            failures.append(f"{rel_path} is not a valid SVG")

    note = (root / "docs/fase14_rank_stability.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 14 Rank Stability",
        "ranking_v2_frozen.tsv",
        "does not create final biological tiers",
        "Weight perturbations passing",
        "Leave-One-Layer-Out",
        "coarse_tiering_recommended",
        "fase15_allowed_with_coarse_tier_language_and_explicit_stability_limits",
        "not a final target ranking claim",
    ]:
        if required_text not in note:
            failures.append(f"fase14_rank_stability.md missing '{required_text}'")

    return failures


def check_phase15_tiering(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE15_FILES if not (root / path).exists()]
    if failures:
        return failures

    tier_rows = read_tsv(root / "results/tables/tier_assignments.tsv")
    if len(tier_rows) != 30:
        failures.append(f"tier_assignments.tsv should have 30 rows, observed {len(tier_rows)}")
    else:
        required_columns = {
            "rank_v2",
            "gene",
            "tier",
            "balanced_top20_freq",
            "single_layer_dependent",
            "tme_flag",
            "rule_clause",
            "principal_caveat",
        }
        missing_columns = required_columns - set(tier_rows[0])
        if missing_columns:
            failures.append("tier_assignments.tsv missing columns: " + ",".join(sorted(missing_columns)))

        counts: dict[str, int] = {}
        for row in tier_rows:
            counts[row.get("tier", "")] = counts.get(row.get("tier", ""), 0) + 1
        if counts != {"Tier 1": 6, "Tier 2": 12, "Watchlist": 12}:
            failures.append(f"unexpected Fase 15 tier distribution: {counts}")

        tier1 = {row.get("gene", "") for row in tier_rows if row.get("tier") == "Tier 1"}
        expected_tier1 = {"ITGB4", "CDH3", "NECTIN2", "CEACAM5", "JAG1", "EPCAM"}
        if tier1 != expected_tier1:
            failures.append("Tier 1 set mismatch: " + ",".join(sorted(tier1)))

        watchlist = {row.get("gene", "") for row in tier_rows if row.get("tier") == "Watchlist"}
        required_watchlist = {"PECAM1", "LRRC15", "HLA-DPB1", "CD47", "HLA-DRB3", "KIR2DS1"}
        missing_watchlist = required_watchlist - watchlist
        if missing_watchlist:
            failures.append("Watchlist missing expected genes: " + ",".join(sorted(missing_watchlist)))

    notes = read_tsv(root / "results/tables/manual_curation_notes.tsv")
    if len(notes) != 30:
        failures.append(f"manual_curation_notes.tsv should have 30 rows, observed {len(notes)}")
    elif any(row.get("changes_score") != "no" for row in notes):
        failures.append("manual_curation_notes.tsv contains a score-changing curation row")

    excluded_rows = read_tsv(root / "results/tables/excluded_with_reason.tsv")
    excluded_genes = {row.get("gene", "") for row in excluded_rows}
    for gene in {"ACTB", "GAPDH", "H3C1", "TOMM20", "CALR", "ALB", "NOTE_top30"}:
        if gene not in excluded_genes:
            failures.append(f"excluded_with_reason.tsv missing {gene}")

    wang_rows = read_tsv(root / "results/tables/wang2026_crosscheck.tsv")
    tier12_rows = [row for row in wang_rows if row.get("our_tier") in {"Tier 1", "Tier 2"}]
    if len(tier12_rows) != 18:
        failures.append(f"wang2026_crosscheck.tsv should include 18 Tier 1+Tier 2 rows, observed {len(tier12_rows)}")
    else:
        overlap = [row for row in tier12_rows if row.get("in_wang_drug_target_table") == "yes"]
        absent = {row.get("our_gene", "") for row in tier12_rows if row.get("in_wang_drug_target_table") != "yes"}
        if len(overlap) != 16 or absent != {"CD9", "LSR"}:
            failures.append("Wang cross-check expected 16/18 overlap with CD9 and LSR absent")
        tier1_overlap = [
            row
            for row in tier12_rows
            if row.get("our_tier") == "Tier 1" and row.get("in_wang_drug_target_table") == "yes"
        ]
        if len(tier1_overlap) != 6:
            failures.append("Wang cross-check should have Tier 1 6/6 overlap")

    cards = (root / "results/tables/top20_candidate_cards.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Top 20 Candidate Cards",
        "Language is hypothesis-generating",
        "## Tier 1",
        "## Watchlist",
        "### ITGB4",
        "### ERBB2",
    ]:
        if required_text not in cards:
            failures.append(f"top20_candidate_cards.md missing '{required_text}'")

    note = (root / "docs/fase15_tiering_and_curation.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 15 complete",
        "Tier 1 (6)",
        "Tier 2 (12)",
        "Watchlist (12)",
        "no score, weight, universe, or frozen ranking was changed",
    ]:
        if required_text not in note:
            failures.append(f"fase15_tiering_and_curation.md missing '{required_text}'")

    post_note = (root / "docs/fase15_post_curation_verification.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "RESOLVED (2026-05-31)",
        "16/18 of our Tier 1+Tier 2",
        "Wang Figure 7H",
        "CLOSED as partially resolved",
        "NECTIN2 is the Tier 1 member closest to the compartment",
    ]:
        if required_text not in post_note:
            failures.append(f"fase15_post_curation_verification.md missing '{required_text}'")

    return failures


def check_phase16_figures_tables(root: Path) -> list[str]:
    failures = [path for path in REQUIRED_PHASE16_FILES if not (root / path).exists()]
    if failures:
        return failures

    for rel_path in [
        "results/figures/phase16_pipeline_overview.svg",
        "results/figures/phase16_surfaceome_evidence_landscape.svg",
        "results/figures/phase16_tumor_normal_selectivity.svg",
        "results/figures/phase16_multilayer_heatmap_top30.svg",
        "results/figures/phase16_benchmark_controls.svg",
        "results/figures/phase16_tier1_candidate_panel.svg",
    ]:
        svg = (root / rel_path).read_text(encoding="utf-8", errors="replace")
        if "<svg" not in svg:
            failures.append(f"{rel_path} is not a valid SVG")

    figure_rows = read_tsv(root / "results/tables/manuscript_figure_manifest.tsv")
    if len(figure_rows) != 9:
        failures.append(f"manuscript_figure_manifest.tsv should have 9 rows, observed {len(figure_rows)}")
    elif any(row.get("exists") != "true" for row in figure_rows):
        failures.append("manuscript_figure_manifest.tsv contains missing figure paths")

    dataset_rows = read_tsv(root / "results/tables/manuscript_table1_datasets.tsv")
    if len(dataset_rows) < 8:
        failures.append("manuscript_table1_datasets.tsv has too few dataset rows")

    score_rows = read_tsv(root / "results/tables/manuscript_table2_score_definitions.tsv")
    score_by_component = {row.get("component", ""): row for row in score_rows}
    if set(score_by_component) != {"Surf", "E", "N", "R", "P", "SC", "T"}:
        failures.append("manuscript_table2_score_definitions.tsv component set mismatch")
    else:
        if score_by_component["SC"].get("primary_weight") != "0.000000":
            failures.append("SC should remain zero-weight/not available in Fase 16 score definitions")
        if score_by_component["R"].get("direction") != "higher_worse_subtracted":
            failures.append("R direction should be documented as higher_worse_subtracted")

    top_rows = read_tsv(root / "results/tables/manuscript_table3_top_candidates.tsv")
    tier_counts: dict[str, int] = {}
    for row in top_rows:
        tier_counts[row.get("tier", "")] = tier_counts.get(row.get("tier", ""), 0) + 1
    if tier_counts != {"Tier 1": 6, "Tier 2": 12}:
        failures.append(f"manuscript_table3_top_candidates.tsv tier distribution mismatch: {tier_counts}")
    tier1 = {row.get("gene", "") for row in top_rows if row.get("tier") == "Tier 1"}
    if tier1 != {"ITGB4", "CDH3", "NECTIN2", "CEACAM5", "JAG1", "EPCAM"}:
        failures.append("manuscript_table3_top_candidates.tsv Tier 1 set mismatch")

    control_rows = read_tsv(root / "results/tables/manuscript_table4_controls.tsv")
    controls = {row.get("gene", "") for row in control_rows}
    for gene in {"ERBB2", "CLDN18", "FGFR2", "PTPRC", "PECAM1", "ACTB"}:
        if gene not in controls:
            failures.append(f"manuscript_table4_controls.tsv missing {gene}")

    flag_rows = read_tsv(root / "results/tables/manuscript_table5_candidate_flags.tsv")
    if len(flag_rows) != 30:
        failures.append(f"manuscript_table5_candidate_flags.tsv should have 30 rows, observed {len(flag_rows)}")
    elif not any(row.get("gene") == "NECTIN2" and "myeloid/DC" in row.get("principal_caveat", "") for row in flag_rows):
        failures.append("manuscript_table5_candidate_flags.tsv should carry the NECTIN2 myeloid/DC caveat")

    supplement_rows = read_tsv(root / "results/tables/supplementary_table_manifest.tsv")
    if len(supplement_rows) < 16:
        failures.append("supplementary_table_manifest.tsv should list at least S1-S16")
    elif any(row.get("exists") != "true" for row in supplement_rows):
        failures.append("supplementary_table_manifest.tsv contains missing paths")

    note = (root / "docs/fase16_figures_tables.md").read_text(encoding="utf-8", errors="replace")
    for required_text in [
        "Fase 16: Figures and Tables",
        "It does not change scores",
        "Coarse tier distribution: Tier 1=6, Tier 2=12, Watchlist=12",
        "Wang 2026 concordance carried forward: 16/18",
        "Fase 16 complete",
    ]:
        if required_text not in note:
            failures.append(f"fase16_figures_tables.md missing '{required_text}'")

    return failures


def write_bootstrap_status(path: Path, root: Path) -> None:
    missing = check_bootstrap(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("check\tstatus\tmessage\n")
        if missing:
            handle.write("bootstrap\tfail\tmissing files: " + ",".join(missing) + "\n")
        else:
            handle.write("bootstrap\tpass\tall required bootstrap files exist\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-phase1-inventory", action="store_true")
    parser.add_argument("--check-phase2-downloads", action="store_true")
    parser.add_argument("--check-phase2-batch-diagnostic", action="store_true")
    parser.add_argument("--check-phase3-identifier-map", action="store_true")
    parser.add_argument("--check-phase4-surfaceome-universe", action="store_true")
    parser.add_argument("--check-phase4b-ranking-resolution", action="store_true")
    parser.add_argument("--check-phase5-tumor-expression", action="store_true")
    parser.add_argument("--check-phase6-normal-selectivity", action="store_true")
    parser.add_argument("--check-phase7-protein-evidence", action="store_true")
    parser.add_argument("--check-phase8-single-cell-tme", action="store_true")
    parser.add_argument("--check-phase9-topology-isoforms", action="store_true")
    parser.add_argument("--check-phase13-mvp-scoring", action="store_true")
    parser.add_argument("--check-phase14-preflight", action="store_true")
    parser.add_argument("--check-phase14-stability", action="store_true")
    parser.add_argument("--check-phase15-tiering", action="store_true")
    parser.add_argument("--check-phase16-figures-tables", action="store_true")
    parser.add_argument("--write-bootstrap-status")
    args = parser.parse_args()

    root = repo_root()

    if args.self_test:
        missing = check_bootstrap(root)
        if missing:
            print("Bootstrap check failed. Missing files:")
            for path in missing:
                print(f"- {path}")
            return 1
        print("Bootstrap check passed.")
        return 0

    if args.check_phase1_inventory:
        failures = check_phase1_inventory(root)
        if failures:
            print("Fase 1 inventory check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 1 inventory check passed.")
        return 0

    if args.check_phase2_downloads:
        failures = check_phase2_downloads(root)
        if failures:
            print("Fase 2 download check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 2 download check passed.")
        return 0

    if args.check_phase2_batch_diagnostic:
        failures = check_phase2_batch_diagnostic(root)
        if failures:
            print("Fase 2 batch diagnostic check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 2 batch diagnostic check passed.")
        return 0

    if args.check_phase3_identifier_map:
        failures = check_phase3_identifier_map(root)
        if failures:
            print("Fase 3 identifier map check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 3 identifier map check passed.")
        return 0

    if args.check_phase4_surfaceome_universe:
        failures = check_phase4_surfaceome_universe(root)
        if failures:
            print("Fase 4 surfaceome universe check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 4 surfaceome universe check passed.")
        return 0

    if args.check_phase4b_ranking_resolution:
        failures = check_phase4b_ranking_resolution(root)
        if failures:
            print("Fase 4B ranking-resolution check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 4B ranking-resolution check passed.")
        return 0

    if args.check_phase5_tumor_expression:
        failures = check_phase5_tumor_expression(root)
        if failures:
            print("Fase 5 tumor-expression check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 5 tumor-expression check passed.")
        return 0

    if args.check_phase6_normal_selectivity:
        failures = check_phase6_normal_selectivity(root)
        if failures:
            print("Fase 6 normal-selectivity check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 6 normal-selectivity check passed.")
        return 0

    if args.check_phase7_protein_evidence:
        failures = check_phase7_protein_evidence(root)
        if failures:
            print("Fase 7 protein-evidence check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 7 protein-evidence check passed.")
        return 0

    if args.check_phase8_single_cell_tme:
        failures = check_phase8_single_cell_tme(root)
        if failures:
            print("Fase 8 single-cell/TME check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 8 single-cell/TME check passed.")
        return 0

    if args.check_phase9_topology_isoforms:
        failures = check_phase9_topology_isoforms(root)
        if failures:
            print("Fase 9 topology/isoforms check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 9 topology/isoforms check passed.")
        return 0

    if args.check_phase13_mvp_scoring:
        failures = check_phase13_mvp_scoring(root)
        if failures:
            print("Fase 13 MVP scoring check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 13 MVP scoring check passed.")
        return 0

    if args.check_phase14_preflight:
        failures = check_phase14_preflight(root)
        if failures:
            print("Fase 14 preflight check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 14 preflight check passed.")
        return 0

    if args.check_phase14_stability:
        failures = check_phase14_stability(root)
        if failures:
            print("Fase 14 stability check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 14 stability check passed.")
        return 0

    if args.check_phase15_tiering:
        failures = check_phase15_tiering(root)
        if failures:
            print("Fase 15 tiering check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 15 tiering check passed.")
        return 0

    if args.check_phase16_figures_tables:
        failures = check_phase16_figures_tables(root)
        if failures:
            print("Fase 16 figures/tables check failed:")
            for path in failures:
                print(f"- {path}")
            return 1
        print("Fase 16 figures/tables check passed.")
        return 0

    if args.write_bootstrap_status:
        write_bootstrap_status(Path(args.write_bootstrap_status), root)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
