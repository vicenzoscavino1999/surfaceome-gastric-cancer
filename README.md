# Surfaceome-Guided Target Prioritization in Gastric Adenocarcinoma

This repository is the execution workspace for a reproducible computational paper that prioritizes cell-surface targets in gastric adenocarcinoma.

Current stage: Fase 17 has a Computational Biology and Chemistry manuscript handoff, PDF, graphical abstract, flat Editorial Manager package, and reviewer-facing reproducibility checks. Coarse tiers are assigned and packaged for manuscript use, but no fine intra-tier order, clinical efficacy/safety claim, or wet-lab validation claim has been generated.

## First Gates

1. Freeze controls, scoring scenarios, dataset targets, seeds, and decision logs before looking at rankings.
2. Complete `docs/literature_landscape_and_differentiation.md` with at least five real close references.
3. Decide `go`, `go_with_narrower_claim`, or `pivot`.
4. Download expression data only after the novelty gate and dataset inventory are documented.

Current Fase 0B status: closed for execution as `go_with_narrower_claim`; direct manual Google Scholar verification remains a pre-submission check.

Current Fase 1 status: metadata inventory complete in `results/tables/dataset_inventory.tsv`, `results/tables/sample_counts.tsv`, `results/tables/coverage_matrix.tsv`, and `docs/fase1_data_inventory.md`.

Current Fase 2 status: reproducible download/checksum tooling exists in `scripts/download_phase2_sources.py`; Xena/Toil PCA/PERMANOVA outputs exist in `results/figures/pca_batch_diagnostic.svg` and `results/tables/batch_permanova.tsv`.

Current Fase 4 status: multi-source surfaceome universe complete in `data/processed/surfaceome_universe.tsv`, with source-overlap figures, Jaccard table, and control/false-positive/false-negative audit. Confirmed UniProt lipidation `GPI-anchor` evidence is now counted universe-wide as non-experimental strong anchor evidence.

Current Fase 4B status: pre-scoring synthetic rank-resolution simulation complete in `results/validation/ranking_resolution_simulation.tsv`. Under neutral layer uncertainty, fine five-level tiering is not yet justified without a stricter Tier 1 stability threshold or later Fase 14 confirmation with real scores.

Current Fase 5 status: TCGA-STAD tumor-expression component table, subtype expression, subtype sample counts, subtype power analysis, clinical covariate expression summaries, and amplified-target CNA context are complete. `E_score` is a component score only.

Current Fase 6 status: normal-expression, tumor-normal tests, `N_score`, organ-specific `R_score`, tumor-normal power analysis, HPA normal protein summary, and risk figures are complete. `N_score` and `R_score` are components only.

Current Fase 7 status: HPA stomach cancer IHC, HPA normal IHC, HPA subcellular localization, protein discordance flags, `P_score`, and RNA-protein concordance figure are complete. `P_score` is a component only; CPTAC is explicitly not assessed in this MVP pass.

Current Fase 8 status: no processed gastric scRNA dataset was admitted into the score; `SC` is `not_available`. The MVP TME fallback is complete with bulk marker-module correlations and ESTIMATE/tidyestimate purity-adjusted partial correlations; both emit contamination flags only, not ranking filters.

Current Fase 9 status: reviewed UniProt feature fields support `T_score`, accessibility classes A-E, GPI-anchor capture, and explicit isoform-unresolved flags for `CLDN18.2` and `FGFR2b`. `T_score` is a component only, not a final target ranking.

Current Fase 13 status: preliminary MVP rankings are generated in `results/rankings/` using `Surf`, `E`, `N`, `R`, `P`, and `T`; `SC` remains `not_available`. `ranking_v0_frozen.tsv` is preserved as the pre-normalization-fix snapshot, `ranking_v1_frozen.tsv` is preserved as the pre-GPI snapshot, and `ranking_v2_frozen.tsv` is the active preliminary ranking after the Fase 4 GPI evidence correction and full downstream rerun. `Surf_relative_confidence` now uses the fixed theoretical Fase 4 scale `[5,10]`. The aggregate preregistered positive-control gate still fails at 4/8 top 50, but the cause-corrected diagnostic finds 0/5 original misses that still accuse the pipeline; the Fase 13 gate is `eligible_for_fase14`. Fase 17B quantifies the GPI correction impact in `results/tables/gpi_correction_impact.tsv` and `results/tables/gpi_rank_delta_v1_v2.tsv`.

Current pre-Fase 14 status: `docs/fase14_preflight.md` preregistered Fase 14 stability thresholds before running Fase 14, verified v0/v1/v2 snapshot integrity, audited v1-to-v2 top50 GPI movement, and checked common non-GPI universe/evidence-rule stability. The preflight decision was `eligible_for_fase14`.

Current Fase 14 status: `docs/fase14_rank_stability.md` reports weight perturbation, leave-one-layer-out, control benchmark, missing-data, risk-form, organ-weight, and post-scoring resolution sensitivity. The decision was `fase15_allowed_with_coarse_tier_language_and_explicit_stability_limits`: candidate-level curation could proceed, but only with coarse stability language and no fine intra-tier ranking.

Current Fase 15 status: `docs/fase15_tiering_and_curation.md` assigns coarse unordered tiers by the preregistered rule in `config/tiering_rules.yaml`: Tier 1 = 6 (`ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, `EPCAM`), Tier 2 = 12, Watchlist = 12. Post-curation verification in `docs/fase15_post_curation_verification.md` keeps `NECTIN2`, `ITGB4`, and `JAG1` in Tier 1 with explicit caveats, resolves the Wang 2026 cross-check as 16/18 Tier 1+Tier 2 concordance, and closes the Figure 7H single-cell follow-up as framework-validating but only partially gene-resolved. Fase 17B later shows Wang is enriched under a simple Core+Probable random-draw null but not under a matched null, so it is framed as consistency/context only. No score, weight, universe, or frozen ranking changed.

Current Fase 16 status: `docs/fase16_figures_tables.md` packages manuscript-ready figures, main tables, a figure manifest, and a supplementary table manifest from frozen Fase 13-15 artifacts. New figures are `results/figures/phase16_*.svg`; main tables are `results/tables/manuscript_table1_*` through `manuscript_table5_*`. No score, weight, universe, ranking, or tier changed.

Current Fase 17 status: `docs/fase17_manuscript_brief.md` now records Computational Biology and Chemistry (CBC) as the active target journal, using the subscription route to avoid APC. `docs/fase17_claim_traceability.md` maps the central quantitative claims to frozen repository artifacts; `docs/reproducibility_reviewer_guide.md` gives a reviewer-facing audit path; `manuscript/cbc_manuscript_scaffold.md`, `manuscript/cbc_highlights.md`, `manuscript/graphical_abstract_brief.md`, and `manuscript/figure_table_plan.tsv` are the active CBC manuscript package. The main body (Abstract, Materials and methods, Results, Discussion, Conclusions, Glossary, Data/code availability, Declarations, and Acknowledgements) has editorially hardened prose, figure/table captions, supplementary captions, data/code availability wording, declarations, graphical-abstract submission caption text, and an expanded 30-entry reference list. `manuscript/cbc_references.bib`, `manuscript/cbc_submission_checklist.md`, `manuscript/cbc_cover_letter_draft.md`, `manuscript/cbc_suggested_referees_draft.md`, and `manuscript/cbc_submission_route_blockers.md` prepare the CBC journal handoff. The graphical abstract draft is exported as `manuscript/graphical_abstract.tiff`, with editable `manuscript/graphical_abstract.svg` source and `manuscript/graphical_abstract_preview.png` for review. Markdown remains the editable drafting source; `scripts/build_phase17_latex_handoff.py` generates the `manuscript/latex/` handoff with an Elsevier `elsarticle` author-year profile for CBC and no manual `.tex` editing. The current author metadata has been inserted from user-supplied details: Vicenzo Scavino Alfaro, Independent Researcher, Lima, Peru, ORCID 0009-0000-2472-9785, durable correspondence u201919346@upc.edu.pe, and telephone +51 962 559 391. `scripts/export_phase17_publication_figures.py` generates nine font-independent publication PDFs in `manuscript/latex/figures/`, with hashes and render metrics in `results/tables/manuscript_publication_figure_manifest.tsv`. Reviewer-hardening now explicitly centers the matched-null result, reframes GPI as quantification/correction of evidence routing, compresses TISCH2 to context-only status, and removes residual internal process labels from public-facing text and artwork. Local validation passes; remaining external work includes final graphical-abstract/PDF approval, public repository URL, archival DOI, author conflict confirmation for suggested referees if requested, optional postal address metadata, and submission-system upload.

Next planned phase: release and submission handoff, including repository archival, DOI insertion, final approval, and submission-system upload.

## Reviewer Reproducibility Audit

The shortest reviewer-facing path is documented in `docs/reproducibility_reviewer_guide.md`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-manuscript.txt
python scripts/run_reproducibility_checks.py
```

The optional manuscript rebuild also regenerates the CBC LaTeX handoff, compiles the PDF, and rebuilds the flat package:

```powershell
python scripts/run_reproducibility_checks.py --include-latex
```

Current local result: unit tests pass, phase artifact checks pass through Fase 16, the CBC manuscript check passes, the publication-figure check passes, and Snakemake dry-run reports all declared outputs up to date.

## Commands

```bash
make help
make smoke-test
make batch-diagnostic
make phase3-id-map
make phase4-surfaceome
make phase4b-resolution
make phase5-expression
make phase6-normal-risk
make phase7-protein
make phase8-tme
make phase9-topology
make phase13-scoring
make phase13-diagnostic
make phase14-preflight
make phase14-preflight-check
make phase14-stability
make phase14-stability-check
make phase15-check
make phase16-figures-tables
make phase16-check
make phase17-wang-enrichment
make phase17-brief-check
make phase17-figure-export
make phase17-figure-export-check
make phase17-latex-handoff
python -m pytest -q
```

On Windows without `make`:

```powershell
.\scripts\smoke_test.ps1
python scripts\check_phase17_manuscript_brief.py
```

Development checks require the pinned packages in `requirements-dev.txt`:

```powershell
python -m pip install -r requirements-dev.txt
snakemake --summary
```

Manuscript figure export uses the separate pinned packages in `requirements-manuscript.txt`.

The release-candidate Docker runtime uses the locked dependency closure in `requirements-lock.txt`:

```powershell
docker build -f docker/Dockerfile -t surfaceome-gastric-cancer-repro .
docker run --rm -v "${PWD}:/work" surfaceome-gastric-cancer-repro
```

The Docker image expects the release checkout to be mounted at `/work`; large raw/source files are not copied into the image during build.

The current `smoke-test` validates repository wiring, Fase 1 inventory files, Fase 2 raw-download checksums and batch diagnostic, Fase 3 identifier normalization, Fase 4 surfaceome universe outputs, Fase 4B ranking-resolution outputs, Fase 5 tumor-expression outputs, Fase 6 normal selectivity/risk outputs, Fase 7 protein evidence/localization outputs, Fase 8 scRNA/TME MVP fallback outputs, Fase 9 topology/isoform outputs, Fase 13 preliminary MVP scoring outputs, the pre-Fase 14 audit, Fase 14 stability outputs, Fase 15 coarse-tier/curation/Wang artifacts, and Fase 16 manuscript figure/table packaging. Fase 15 curation is validated as frozen artifacts; Fase 16 tables/figures are regenerated by `scripts/build_phase16_figures_tables.py`.
