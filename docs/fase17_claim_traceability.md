# Fase 17 Claim Traceability Audit

Date: 2026-05-31; pre-submission literature/novelty status updated 2026-06-02.

## Scope

This audit maps the main quantitative manuscript claims to frozen repository artifacts before final language polish and LaTeX migration. It does not recalculate scores, weights, universe membership, rankings, or tiers.

Active ranking: `results/rankings/ranking_v2_frozen.tsv`

SHA256: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`

Sidecar metadata: `results/rankings/ranking_v2_frozen.metadata.yaml`

## Verified Quantitative Claims

| Manuscript claim | Frozen source | Verified value | Status |
|---|---|---:|---|
| Core+Probable surfaceome universe size | `results/tables/surfaceome_confidence_summary.tsv` | 2,704 genes: 2,646 Core + 58 Probable | verified |
| Published-list Jaccard overlap | `results/tables/surfaceome_jaccard_with_published_lists.tsv` | TCSA 0.7749; CSPA 0.2889; SURFY 0.8017 | verified |
| Tumor-expression coverage | `data/processed/tumor_expression.tsv` | 2,696 measured of 2,704; 8 missing | verified |
| TCGA-STAD tumors used for MVP TME fallback | `results/tables/tme_contamination_flags.tsv` | 414 tumors | verified |
| GTEx stomach selectivity rule | `data/processed/selectivity_scores.tsv` | 757 genes with `positive_N_stat_rule_gtex=true` | verified |
| Conservative high critical off-tumor risk | `data/processed/off_tumor_risk.tsv` | 1,825 genes with `high_critical_off_tumor_risk` | verified |
| HPA stomach cancer IHC coverage | `results/tables/protein_coverage.tsv` | 1,790 genes | verified |
| HPA normal stomach/critical IHC coverage | `results/tables/protein_coverage.tsv` | 1,535 genes | verified |
| HPA subcellular-location coverage | `results/tables/protein_coverage.tsv` | 1,302 genes | verified |
| HPA membrane or cell-junction support | `results/tables/protein_coverage.tsv` | 734 genes | verified |
| Coarse unordered tier distribution | `results/tables/tier_assignments.tsv` | Tier 1 = 6; Tier 2 = 12; Watchlist = 12 | verified |
| Weight perturbations passing both preregistered gates | `results/validation/weight_perturbation_summary.tsv`; `docs/fase14_rank_stability.md` | 231/250 | verified |
| Minimum and median perturbation Spearman vs v2 | `results/validation/weight_perturbation_summary.tsv`; `docs/fase14_rank_stability.md` | 0.910703 / 0.983898 | verified |
| Post-scoring top20 genes with 95% rank interval contained in top40 | `results/validation/ranking_resolution_post_scoring_summary.tsv` | 1/20 | verified |
| Positive-control top50 recovery | `results/tables/control_recovery_phase13.tsv`; `results/validation/phase13_post_scoring_sanity.tsv` | 4/8: ERBB2, EPCAM, CEACAM5, MET | verified |
| Wang 2026 Tier 1/2 concordance | `results/tables/wang2026_crosscheck.tsv` | 16/18; Tier 1 = 6/6; Tier 2 = 10/12 | verified |
| Wang 2026 simple random-draw overlap versus Core+Probable universe | `results/tables/wang2026_overlap_enrichment.tsv` | all drug-target table: 16/18 observed vs 9.47 expected, hypergeometric p=0.0013; membrane-protein flag: 13/18 observed vs 5.79 expected, p=5.6e-4 | verified |
| Wang 2026 matched-null sensitivity | `results/tables/wang2026_matched_null.tsv` | all drug-target table: observed 16/18 vs matched-null mean 15.18, p=0.436; membrane-protein flag: observed 13/18 vs matched-null mean 13.99, p=0.817 | verified |
| TCSA final GESP external baseline | `results/tables/external_surfaceome_baseline_comparison.tsv` | n=2,685; Spearman rho=0.389861, p=3.5e-98; top20 overlap 1/20 (`NECTIN2`); Tier 1/2 in baseline top100 = 6/18 | verified |
| TCSA core GESP external baseline | `results/tables/external_surfaceome_baseline_comparison.tsv` | n=2,685; Spearman rho=0.329466, p=5.3e-69; top20 overlap 2/20 (`ERBB2`; `ITGB4`); Tier 1/2 in baseline top100 = 8/18 | verified |
| Surfaceome source-dependency audit | `results/tables/surfaceome_source_dependency_summary.tsv`; `results/tables/surfaceome_source_dependency_audit.tsv` | 18/18 Tier 1/2 candidates are multi-source supported; 18/18 combine curated-list plus independent anchor support; 18/18 retain support after any single-source removal; 0/18 are single-source dependent | verified |
| Limited TISCH2 candidate-level scRNA check | `results/tables/candidate_scrna_tisch2_summary.tsv`; `results/tables/candidate_scrna_tisch2_compartment_check.tsv` | `STAD_GSE134520`: 18/18 present, 8 malignant-class supported, 1 mixed, 7 low malignant signal, 2 non-malignant dominant; `STAD_GSE167297`: context-only, no malignant-cell class | verified |
| GPI correction ranked-universe impact | `results/tables/gpi_correction_impact.tsv` | v1 2,650 -> v2 2,704; +54 newly ranked confirmed GPI genes; confirmed GPI top50 0 -> 5; current Tier 1/2 GPI = 3 | verified |
| GPI benchmark rank movement | `results/tables/gpi_correction_impact.tsv`; `results/tables/gpi_rank_delta_v1_v2.tsv` | CEACAM5 120->12; MSLN 453->158; BST2 82->10; ALPG 146->16; ULBP2 191->27; NT5E 254->50 | verified |

## Verified Interpretation Guardrails

| Guardrail | Frozen source | Verified state |
|---|---|---|
| `SC` is unavailable and is not imputed | `results/tables/tme_contamination_flags.tsv`; `config/scoring_scenarios.yaml` | `SC_status=not_available` for all 2,704 genes |
| TME bulk/ESTIMATE outputs are review flags, not hard filters | `docs/fase8_single_cell_tme_specificity.md`; `config/tiering_rules.yaml` | preserved |
| Limited TISCH2 scRNA output is candidate annotation only, not a score or tier-changing layer | `docs/candidate_scrna_compartment_check.md`; `results/tables/candidate_scrna_tisch2_compartment_check.tsv` | preserved |
| TCSA is an external surfaceome-score baseline, not a gastric-specific validation label | `docs/external_surfaceome_baseline_comparison.md`; `results/tables/external_surfaceome_baseline_comparison.tsv` | preserved |
| Surfaceome source-dependency audit is source-support robustness, not experimental validation | `docs/surfaceome_source_dependency_audit.md`; `results/tables/surfaceome_source_dependency_audit.tsv` | preserved |
| `CLDN18.2` is unresolved from gene-level expression | `data/processed/topology_isoforms_ecd.tsv` | `CLDN18.2_isoform_unresolved_gene_level_only` |
| `FGFR2b` is unresolved from gene-level expression | `data/processed/topology_isoforms_ecd.tsv` | `FGFR2b_isoform_unresolved_gene_level_only` |
| HPA bulk IHC does not provide antibody-level or patient-level membrane detail | `docs/fase7_protein_evidence.md`; `REPRODUCIBILITY.md` | preserved as an explicit limitation |
| Wang 2026 is an external consistency check, not clinical validation, independent enrichment-based validation, or per-gene scRNA proof | `docs/fase15_post_curation_verification.md`; `results/tables/wang2026_crosscheck.tsv`; `results/tables/wang2026_matched_null.tsv` | preserved |

## Remaining Pre-Submission Checks

- Direct PubMed/Google Scholar novelty check: DONE on 2026-06-02; see `docs/literature_landscape_and_differentiation.md` and DD-065. This did not require stronger manuscript novelty claims or changes to scores, tiers, DOI, or release artifacts.
- Verify every external bibliographic record and DOI during any final reference-manager / `.bib` pass if new citations are added after this audit. The current CBC 30-reference library remains unchanged by the novelty check.
- Reconfirm the Computational Biology and Chemistry Guide for Authors and Editorial Manager file requirements immediately before final upload.
- Public repository URL inserted: https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer.
- Archival DOI inserted: `10.5281/zenodo.20498705`.
- Reconfirm author, funding, competing-interest, and acknowledgement wording immediately before final submission; current author name, affiliation, ORCID, and corrected corresponding-author email are inserted but the PDF remains non-final.
- Migrate the frozen editorial text to LaTeX only after the remaining language review is complete.
