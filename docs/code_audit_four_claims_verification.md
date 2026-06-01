# Code Audit Verification: Four Claimed Scoring Biases

Date: 2026-05-31

An external review raised four claimed algorithmic biases ("silent bugs") in Fase 7, 8, and 13. Each
was verified against the actual source and its impact on the frozen rankings / Fase 15 tiering was
quantified. **No code, score, weight, universe, or ranking was changed by this verification.**

Bottom line: all four claims are **factually accurate about the code** — they describe real
inconsistencies, and the author did use the better technique elsewhere (`geometric_mean_scores`,
`combined_tme`, `rank_percentiles`), so they are genuine oversights, not deliberate design. **However,
quantified, none of the four changes the Tier 1 / Tier 2 / Watchlist nominations.** A v3 re-run is not
warranted to fix them for the results; they are logged as known code-level limitations to correct if a
v3 is ever run for another reason, and the manuscript Methods must describe the current behavior.

## Claim 1 — Risk penalty / denominator (build_mvp_scoring.py:216-220)

True: `R` is subtracted in the numerator while `abs(weight)` is added to the denominator.

Impact: **zero on nominations.** For a fully-measured gene the proposed fix (`1-R`) equals
`current_score + wR/D`, a constant identical for all fully-measured genes (same D = sum of all six
weights), so it does **not** reorder them. Algebra: `numerator_fixed - numerator_current = wR`. Every
Tier 1 (6) and Tier 2 (12) gene has `available_weight_sum = 1.0` (fully measured), so their relative
order is invariant under the fix. Only missing-component genes (the thin-evidence HLA/KIR, already
Watchlist) shift, and the fix would push them down — the desired direction already achieved by rule.
Also: subtracted `R` is the documented design (DD-027, master plan); `geometric_mean`'s `1-R` is
mathematically required there (log of non-negative), not an obviously portable "correct" technique.

## Claim 2 — TME module without z-score (build_single_cell_tme_specificity.py:404 vs 541)

True: per-module scores average raw log2(TPM) (line 404) while `combined_tme` z-scores (line 541).
Modules are level-dominated in raw TPM (CD68 = 81% of myeloid mass, FAP = 100% of CAF mass, SDC1 = 97%
of B/plasma).

Impact: **zero on flags, quantified by read-only recompute.** Re-deriving every TME module both ways
(raw mean vs marker-level z-scored mean of the log2 vectors) over the 414 TCGA-STAD primary tumors and
re-computing the purity-adjusted partial Spearman for all top30 candidates:

- Validation: NECTIN2 myeloid raw-mean partial reproduced exactly at 0.320 (pipeline stored 0.320).
- The z-scored partials differ from raw-mean by < 0.05 for every gene.
- **Flag flips at the 0.40 high-TME threshold: NONE.** NECTIN2 0.320 -> 0.329 (stays < 0.40, Tier 1
  holds); MPZL1 0.535 -> 0.548, ITGB5 0.536 -> 0.535, IFNGR1 0.401 -> 0.446, ERBB2 0.456 -> 0.466,
  LSR 0.422 -> 0.418, TGFBR1 0.460 -> 0.460, PECAM1 0.880 -> 0.864, LRRC15 0.564 -> 0.566 — all keep
  their flag side. No Tier 1 gene crosses above; no Tier 2/Watchlist gene crosses below.

Why level-dominance does not propagate: Spearman correlation is rank/variance-driven in log2 space, not
level-driven in raw TPM. The level-dominant marker does not dominate the rank-variance, so raw-mean and
z-mean modules correlate near-identically with candidates. **The NECTIN2 Tier-1 decision is robust to
this fix.**

## Claim 3 — Lexicographic Borda (build_mvp_scoring.py:231-240 vs 159)

True: `rank_rows` assigns sequential ranks with HGNC alphabetical tie-break, while `rank_percentiles`
uses average-rank ties.

Impact: **zero on nominations.** (a) Lexicographic tie-break is the preregistered reproducibility
convention (`parameters.yaml` reproducibility_tolerances.rank_order). (b) It only affects tied-score
genes; the one real tie group is the thin-evidence HLA-DRB3/4 + KIR2DL5A/2DS1 (identical score
0.614473), already Watchlist. (c) `ranking_robust_aggregate` is supplementary, not the tiering basis
(Fase 15 used `ranking_v2_frozen` = balanced). (d) Coarse tiers carry no intra-tier order. The
methodological point (averaging sequential ranks in Borda) is valid for the supplementary aggregate
only.

## Claim 4 — P-score imputation asymmetry (build_protein_evidence.py:364 vs 372-376)

True: missing membrane localization -> 0.0 (line 364); missing normal-safety IHC -> 0.5 (lines
372-376). Asymmetric.

Impact: **near-zero on nominations, quantified from `protein_evidence.tsv`.** All 26 measured top30
genes have real HPA subcellular data (`hpa_subcellular_reliability` Supported/Approved/Enhanced) and
resolve to `plasma_membrane` or `cell_junctions`. The only `no_membrane_support` in the top30 is BST2,
which is a genuine HPA result (data present, no membrane support), not the missing-data 0.0 default.
The four "missing" rows are the thin-evidence genes with no protein data (already Watchlist). So no
nominated gene is hit by the asymmetry; it suppresses P only for obscure low-coverage genes that never
reach the top. The single second-order effect — suppressing P for ~half the universe could inflate the
P-percentile of well-covered top genes — is modest given P's weight and the top genes' multi-layer
robustness.

## Decision

All four are real code-level inconsistencies but have negligible impact on the frozen rankings and the
Fase 15 nominations (claim 2 quantified by recompute, claim 4 by data inspection, claims 1 and 3 by
construction). **No v3 re-run is warranted on their account.** Recommended handling:

1. Log claims 1-4 as known code-level limitations / technical debt (this document).
2. If a v3 is ever run for another reason, apply the four consistency fixes then and report the diff.
3. Manuscript Methods must describe the current (frozen) behavior accurately: subtracted `R` with
   abs-weight renormalization, raw-mean TME modules with z-scored combined index, lexicographic
   rank tie-break, and the membrane/safety imputation defaults.
