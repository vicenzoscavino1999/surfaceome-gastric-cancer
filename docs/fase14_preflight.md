# Fase 14 Preflight

Date: 2026-05-31

This preflight is executed before Fase 14 stability analyses. It does not run perturbation, leave-one-layer-out, missing-data sensitivity, or final tiering. Its outputs are not final biological tiers.

## A Priori Fase 14 Thresholds

These thresholds are fixed before running Fase 14:

- Weight perturbations: `plus_minus_10_percent;plus_minus_20_percent` around the active v2 Balanced weights.
- Perturbed-rank global stability: Spearman rank correlation versus `ranking_v2_frozen.tsv` must be `>=0.9` for the main perturbation summaries to be called stable.
- Top-20 retention under perturbation: at least `80%` of v2 top-20 genes should remain in top 20 under reasonable perturbations.
- Control expectation: recovered controls (`ERBB2`, `EPCAM`, `MET`, `CEACAM5`) should remain high-priority; biologically demoted controls (`CLDN18`, `FGFR2`, `MSLN`) should not become top-20 under small perturbations.
- Universe/evidence-rule stability: common non-GPI genes between v1 and v2 should have Spearman rank correlation `>=0.85`. GPI common genes are descriptive only because GPI movement is expected by design.

## Preflight Gates

### 1. Top50 v1/v2 Contamination Audit

- New v2 top50 genes versus v1: 7 (`BST2;CEACAM5;ALPG;ULBP2;MMP14;HLA-B;NT5E`)
- New v2 top50 GPI genes: 5
- New v2 top50 plausible multi-component entries: 7
- New v2 top50 suspicious Surf-dominant entries: 0 (`none`)
- Gate: `pass`

Criterion: a few GPI entrants are acceptable if they have non-Surf support. Any suspicious Surf-dominant new top50 GPI entry blocks Fase 14.

### 2. Snapshot Integrity

- Snapshot rows checked: 6
- Gate: `pass`

Interpretation: v0 is the pre-normalization-fix snapshot, v1 is post-normalization-fix/pre-GPI, and v2 is active post-GPI. The only new methodological decision from v1 to v2 is the Fase 4 GPI evidence correction; changes in E/N/R/P/T percentiles are deterministic consequences of rerunning downstream over the expanded universe.

### 3. Universe/Evidence-Rule Stability

- Common non-GPI genes: 2585
- Common non-GPI rank Spearman v1 vs v2: `0.993215`
- Common non-GPI top50 retention: `0.860000`
- Gate: `pass`

GPI common genes are reported separately:

- Common GPI genes: 65
- Common GPI rank Spearman v1 vs v2: `0.992657`
- Common GPI top50 retention: `not_applicable`

This is named universe/evidence-rule stability rather than pure composition stability because v1 to v2 changed both universe membership and the Fase 4 GPI evidence rule. The primary gated subset is common non-GPI genes to avoid penalizing intended GPI movement.

## Decision

Fase 14 is allowed to start only if the top50 contamination gate, snapshot integrity gate, and common non-GPI universe/evidence-rule stability gate are all `pass`.

Current preflight decision: `eligible_for_fase14`

## Outputs

- `results/tables/fase14_preflight_top50_v1_v2_audit.tsv`
- `results/tables/fase14_preflight_snapshot_integrity.tsv`
- `results/tables/fase14_preflight_universe_stability.tsv`
