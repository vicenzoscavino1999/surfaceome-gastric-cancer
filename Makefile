.PHONY: help setup phase1-inventory download batch-diagnostic phase2-check phase3-id-map phase3-check phase4-surfaceome phase4-check phase4b-resolution phase4b-check phase5-expression phase5-check phase6-normal-risk phase6-check phase7-protein phase7-check phase8-tme phase8-check phase9-topology phase9-check phase13-scoring phase13-diagnostic phase13-check phase14-preflight phase14-preflight-check phase14-stability phase14-stability-check phase15-check phase16-figures-tables phase16-check phase17-wang-enrichment phase17-gpi-impact phase17-brief-check phase17-figure-export phase17-figure-export-check phase17-latex-handoff smoke-test release-check audit-report all test

help:
	@echo "Targets:"
	@echo "  setup       - verify repository structure"
	@echo "  phase1-inventory - rebuild lightweight dataset inventory tables"
	@echo "  download    - download Fase 2 MVP raw sources with checksums"
	@echo "  batch-diagnostic - build Xena/Toil PCA and PERMANOVA diagnostic"
	@echo "  phase2-check - verify raw checksums and Fase 2 diagnostic outputs"
	@echo "  phase3-id-map - build canonical HGNC/UniProt/HPA/Xena ID map"
	@echo "  phase3-check - verify Fase 3 identifier normalization outputs"
	@echo "  phase4-surfaceome - build multi-source surfaceome universe"
	@echo "  phase4-check - verify Fase 4 surfaceome universe outputs"
	@echo "  phase4b-resolution - run pre-scoring ranking-resolution simulation"
	@echo "  phase4b-check - verify Fase 4B ranking-resolution outputs"
	@echo "  phase5-expression - build TCGA-STAD tumor-expression and subtype tables"
	@echo "  phase5-check - verify Fase 5 tumor-expression outputs"
	@echo "  phase6-normal-risk - build normal-expression, selectivity, and off-tumor risk tables"
	@echo "  phase6-check - verify Fase 6 normal selectivity/risk outputs"
	@echo "  phase7-protein - build HPA protein-evidence and localization tables"
	@echo "  phase7-check - verify Fase 7 protein evidence/localization outputs"
	@echo "  phase8-tme - build scRNA/TME specificity gate outputs"
	@echo "  phase8-check - verify Fase 8 scRNA/TME outputs"
	@echo "  phase9-topology - build topology, isoform, and ECD accessibility outputs"
	@echo "  phase9-check - verify Fase 9 topology/isoform outputs"
	@echo "  phase13-scoring - build preliminary MVP integrated score outputs"
	@echo "  phase13-diagnostic - build Fase 13 v0/v1 diagnostic outputs"
	@echo "  phase13-check - verify Fase 13 MVP scoring outputs"
	@echo "  phase14-preflight - build pre-Fase 14 audit without running Fase 14"
	@echo "  phase14-preflight-check - verify pre-Fase 14 audit outputs"
	@echo "  phase14-stability - build Fase 14 sensitivity/stability outputs"
	@echo "  phase14-stability-check - verify Fase 14 stability outputs"
	@echo "  phase15-check - verify Fase 15 coarse-tier/curation/Wang outputs"
	@echo "  phase16-figures-tables - build Fase 16 manuscript figures/tables"
	@echo "  phase16-check - verify Fase 16 figures/tables"
	@echo "  phase17-wang-enrichment - test Wang 2026 overlap enrichment and matched null"
	@echo "  phase17-gpi-impact - quantify GPI correction impact"
	@echo "  phase17-brief-check - verify Fase 17 CBC manuscript package"
	@echo "  phase17-figure-export - export font-independent manuscript PDFs"
	@echo "  phase17-figure-export-check - verify publication PDF manifest and renders"
	@echo "  phase17-latex-handoff - regenerate CBC/Elsevier LaTeX manuscript source"
	@echo "  smoke-test  - run lightweight bootstrap through Fase 16 checks"
	@echo "  release-check - run reviewer-facing reproducibility audit"
	@echo "  audit-report - write release/reproducibility_audit_report.md"
	@echo "  test        - run unit tests"
	@echo "  all         - run the declared Snakemake workflow"

setup:
	@python src/utils/compare_outputs.py --self-test

phase1-inventory:
	@python scripts/build_dataset_inventory.py

download:
	@python scripts/download_phase2_sources.py

phase2-check:
	@python src/utils/compare_outputs.py --check-phase2-downloads
	@python src/utils/compare_outputs.py --check-phase2-batch-diagnostic

batch-diagnostic:
	@python scripts/build_xena_batch_diagnostic.py

phase3-id-map:
	@python scripts/build_id_map_master.py

phase3-check:
	@python src/utils/compare_outputs.py --check-phase3-identifier-map

phase4-surfaceome:
	@python scripts/build_surfaceome_universe.py

phase4-check:
	@python src/utils/compare_outputs.py --check-phase4-surfaceome-universe

phase4b-resolution:
	@python scripts/simulate_rank_resolution.py

phase4b-check:
	@python src/utils/compare_outputs.py --check-phase4b-ranking-resolution

phase5-expression:
	@python scripts/build_tumor_expression.py

phase5-check:
	@python src/utils/compare_outputs.py --check-phase5-tumor-expression

phase6-normal-risk:
	@python scripts/build_normal_selectivity.py

phase6-check:
	@python src/utils/compare_outputs.py --check-phase6-normal-selectivity

phase7-protein:
	@python scripts/build_protein_evidence.py

phase7-check:
	@python src/utils/compare_outputs.py --check-phase7-protein-evidence

phase8-tme:
	@python scripts/build_single_cell_tme_specificity.py

phase8-check:
	@python src/utils/compare_outputs.py --check-phase8-single-cell-tme

phase9-topology:
	@python scripts/build_topology_isoforms.py

phase9-check:
	@python src/utils/compare_outputs.py --check-phase9-topology-isoforms

phase13-scoring:
	@python scripts/build_mvp_scoring.py

phase13-diagnostic:
	@python scripts/diagnose_phase13.py
	@python scripts/diagnose_gpi_membership_route.py

phase13-check:
	@python src/utils/compare_outputs.py --check-phase13-mvp-scoring

phase14-preflight:
	@python scripts/build_phase14_preflight.py

phase14-preflight-check:
	@python src/utils/compare_outputs.py --check-phase14-preflight

phase14-stability:
	@python scripts/build_phase14_stability.py

phase14-stability-check:
	@python src/utils/compare_outputs.py --check-phase14-stability

phase15-check:
	@python src/utils/compare_outputs.py --check-phase15-tiering

phase16-figures-tables:
	@python scripts/build_phase16_figures_tables.py

phase16-check:
	@python src/utils/compare_outputs.py --check-phase16-figures-tables

phase17-wang-enrichment:
	@python scripts/build_wang2026_overlap_enrichment.py

phase17-gpi-impact:
	@python scripts/build_gpi_correction_impact.py

phase17-brief-check:
	@python scripts/check_phase17_manuscript_brief.py

phase17-figure-export:
	@python scripts/export_phase17_publication_figures.py

phase17-figure-export-check:
	@python scripts/export_phase17_publication_figures.py --check

phase17-latex-handoff:
	@python scripts/build_phase17_latex_handoff.py

smoke-test: setup
	@python src/utils/compare_outputs.py --self-test
	@python src/utils/compare_outputs.py --check-phase1-inventory
	@python src/utils/compare_outputs.py --check-phase2-downloads
	@python src/utils/compare_outputs.py --check-phase2-batch-diagnostic
	@python src/utils/compare_outputs.py --check-phase3-identifier-map
	@python src/utils/compare_outputs.py --check-phase4-surfaceome-universe
	@python src/utils/compare_outputs.py --check-phase4b-ranking-resolution
	@python src/utils/compare_outputs.py --check-phase5-tumor-expression
	@python src/utils/compare_outputs.py --check-phase6-normal-selectivity
	@python src/utils/compare_outputs.py --check-phase7-protein-evidence
	@python src/utils/compare_outputs.py --check-phase8-single-cell-tme
	@python src/utils/compare_outputs.py --check-phase9-topology-isoforms
	@python src/utils/compare_outputs.py --check-phase13-mvp-scoring
	@python src/utils/compare_outputs.py --check-phase14-preflight
	@python src/utils/compare_outputs.py --check-phase14-stability
	@python src/utils/compare_outputs.py --check-phase15-tiering
	@python src/utils/compare_outputs.py --check-phase16-figures-tables

test:
	@python -m pytest -q

release-check:
	@python scripts/run_reproducibility_checks.py

audit-report:
	@python scripts/build_release_audit_report.py --skip-checks

all:
	@python -m snakemake --cores 1
