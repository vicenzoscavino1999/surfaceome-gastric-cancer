# Fase 15: Coarse Tiering and Manual Curation

Date: 2026-05-31

## Status and scope

Fase 15 executes the preregistered protocol (`docs/manual_curation_protocol.md`,
`config/tiering_rules.yaml`; DD-033, AD-25) on the frozen `Balanced` ranking
(`results/rankings/ranking_v2_frozen.tsv`, SHA256 `95040e...`). Tiers are coarse (Tier 1 / Tier 2 /
Watchlist) with no intra-tier order (Fase 14 resolution: 1/20). Curation informs tier, never score;
no score, weight, universe, or frozen ranking was changed.

- Pass 1: web curation of top 30 (UniProt/HPA/PubMed/ClinicalTrials) -> `results/tables/manual_curation_notes.tsv` (30/30).
- Pass 2: detailed candidate cards for top 20 -> `results/tables/top20_candidate_cards.md` (20/20).
- Tier assignment by rule -> `results/tables/tier_assignments.tsv` (30/30, each with rule clause + caveat).
- Hard exclusions documented -> `results/tables/excluded_with_reason.tsv`.

## Coarse tier distribution (top 30)

- **Tier 1 (6):** ITGB4, CDH3, NECTIN2, CEACAM5, JAG1, EPCAM.
- **Tier 2 (12):** MPZL1, ITGB5, BST2, IFNGR1, ALPG, DSC2, TNFRSF11A, ERBB2, CD9, LSR, CDH17, TGFBR1.
- **Watchlist (12):** HLA-DRB3, HLA-DRB4, KIR2DL5A, KIR2DS1, PECAM1, IL2RG, HLA-A, LRRC15, HLA-DPB1, BTN3A3, ULBP2, CD47.

## Rule-driven results that the discipline produced (not tuned)

- **ERBB2 -> Tier 2.** The validated HER2 benchmark has balanced top20-frequency 0.34 < 0.40 and
  fails the preregistered Tier-1 stability criterion. It was **not** forced to Tier 1. It is robustly
  top50 (freq 1.0); the top20-boundary instability is consistent with known HER2 heterogeneity. A
  ranking that does not gerrymander HER2 into the top tier is more credible.
- **CDH17 -> Tier 2.** A GI-restricted surface-antigen program with clinical-stage CAR-T/ADC context
  (CHM-2101 phase 1/2) ranks 28 in the bulk surfaceome and fails the stability criterion; the bulk
  ranking is conservative relative to external evidence.
- **PECAM1 -> Watchlist (a-priori expectation confirmed).** The 2026-05-31 registered prediction held:
  HPA shows PECAM1 staining in endothelial/vascular cells, not tumor epithelium ("cancer tissues
  mainly negative"). Demotion is by the preregistered TME rule, registered before the HPA check.
- **LRRC15 -> Watchlist.** Curation identified it as a TGFÎ²-induced CAF/stromal marker (ABBV-085
  targets it on stroma, not tumor epithelium). It is a second bulk/TME compartment false positive
  alongside PECAM1, illustrating the known single-cell-absent limitation.
- **ALPG -> Tier 2.** The most favorable biology in the set (oncofetal antigen virtually absent from
  normal adult tissue except placenta; active ADC/bispecific programs), but `single_layer_dependency`
  blocks Tier 1: its high rank leans on one layer. Flagged for priority re-evaluation if a second
  layer corroborates.
- **Four thin-evidence genes (HLA-DRB3/DRB4, KIR2DL5A/2DS1) -> Watchlist** by the missing-data rule
  (>=3 missing primary components, non-assessable expression), as Fase 14 anticipated.

## Sanity checks

- Non-obvious Tier-1 nominations present (CDH3, NECTIN2 â€” genuine ADC targets not gastric-validated),
  satisfying the "top should include non-control non-obvious genes" check.
- Negative controls behave correctly: intracellular controls excluded from the universe (6/6); the
  endothelial compartment control PECAM1 is Watchlist via the TME rule.
- Positive controls: EPCAM/CEACAM5 -> Tier 1, ERBB2 -> Tier 2 (stability), all with documented
  rationale; isoform benchmarks (CLDN18/FGFR2) remain Watchlist outside the top30 with isoform flags.

## Limitations (carried to manuscript)

- Single-evaluator curation (RA-04): no inter-rater reliability; curation notes published for audit.
- `SC` not available: tumor-vs-TME separation rests on bulk flags; PECAM1 and LRRC15 are the explicit
  evidence of this limit.
- Coarse tiers only: no fine intra-tier order is claimed (Fase 14 resolution).
- Curation findings did not trigger any score change (no reproducible bug found); `changes_score=no`
  for all 30.

## Outputs

- `results/tables/tier_assignments.tsv`
- `results/tables/top20_candidate_cards.md`
- `results/tables/manual_curation_notes.tsv`
- `results/tables/excluded_with_reason.tsv`

## Decision

Fase 15 complete. Coarse tiers assigned by preregistered rule; nothing hand-tuned. Next phase is
Fase 16 (figures and tables) / Fase 17 (manuscript), using coarse-tier language and the explicit
stability/TME/single-cell limitations throughout.
