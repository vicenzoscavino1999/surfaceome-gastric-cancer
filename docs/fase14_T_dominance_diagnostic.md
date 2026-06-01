# Fase 14 Post-Hoc Diagnostic: `T` Dominance, Top30 Severity, and Control Direction

Date: 2026-05-31

## Status and scope

This is a **read-only diagnostic** run after Fase 14 stability. It does **not** change scores,
weights, the surfaceome universe, or any frozen ranking. No file under `results/rankings/`,
`config/`, or `data/processed/` was modified. Its only purpose is to interpret three Fase 14
numbers before Fase 15 candidate curation begins:

1. Leave-one-layer-out: removing `T` drops top20 retention to `0.35` (most disruptive layer).
2. Top30 automated false-positive audit: `25/30` rows carry at least one flag.
3. Control recovery direction breakdown (recovered upward vs demoted downward).

The Fase 14 decision (`fase15_allowed_with_coarse_tier_language_and_explicit_stability_limits`,
see `docs/fase14_rank_stability.md` and DD-031) is unchanged. This diagnostic is measurement,
not optimization: no number below was tuned, and the instability metrics are reported as-is.

## Pinned inputs (integrity verified)

- `results/rankings/ranking_v2_frozen.tsv` SHA256 `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631` (matches recorded v2 freeze)
- `results/tables/component_scores_all_candidates.tsv` SHA256 `6e6c6c1034540533fb6aae86f94aeff096fa52abd89cd5f728c4d589f2fc6992`
- `results/validation/leave_one_layer_out.tsv` SHA256 `686beefb49394ce8427669d19f3f935a4c5bf7d88bc1b0b4b07c7ed6e0ea6f0b`
- `results/validation/top30_false_positive_audit.tsv` SHA256 `86b39460c7896d68a03b74d4c0a263d0d9c20b4797fe461fe8b7f52bc6d8569b`
- `results/validation/control_benchmark.tsv` SHA256 `3d1407dbfbb35445e6a0fc95b96cbd0d97d81071d2d2a93e547f81797177ba59`

---

## 1. `T` dominance: biological signal vs transformation artifact

### Question

Leave-one-layer-out removing `T` (topology / extracellular accessibility) gives top20 retention
`0.35` (7/20 retained). The ranking depends critically on `T`. The competing interpretations have
the same statistical signature:

- **Biological (strength):** accessibility of the extracellular domain is genuinely the most
  discriminant layer for antibody/ADC targeting. Removing it correctly lets physically
  poorly-accessible proteins rise. Stated with confidence.
- **Structural (caveat):** `T` carries disproportionate effective leverage because of how it is
  constructed (variance/scale/transformation), independent of biology. Reported as a fragility.

`T` is also the least-audited component (the same transform that placed `MSLN` low), so its
combination of maximum influence and minimum prior audit is exactly where a reviewer probes.

### Test

For `omitted_layer == T` in `leave_one_layer_out.tsv`, identify which baseline top20 genes leave,
which non-top20 genes enter, and cross-tabulate against `accessibility_class` and `T_rank_percentile`
from the frozen v2 ranking.

### Result: baseline top20 under `T` removal

Retained in top20 (7): ITGB4, MPZL1, CDH3, CEACAM5, NECTIN2, ITGB5, BST2.

Dropped (13), split into two mechanistically distinct groups:

**Group A â€” thin-evidence collapse (4 genes, structural):**

| gene | base rank | rank without T | available_weight_sum (no-T) | missing components |
|---|---|---|---|---|
| HLA-DRB3 | 2 | 386 | 0.15 | E;N;R;P |
| HLA-DRB4 | 3 | 387 | 0.15 | E;N;R;P |
| KIR2DL5A | 4 | 388 | 0.15 | E;N;R;P |
| KIR2DS1 | 5 | 389 | 0.15 | E;N;R;P |

These four are ranked at 2-5 on `Surf`+`T` only (`available_weight_sum`=0.25). Removing `T` strips
half their evidence and they crater to ~387. This is not accessibility biology; it is the
`exclude_and_renormalize` thin-evidence inflation that the master plan's Fase 13 sanity check #4
already anticipated, and that the top30 audit independently flags as `thin_evidence_missing_3plus`.

**Group B â€” modest slide of well-evidenced class A genes (9 genes):**

IFNGR1 (11->29), JAG1 (13->30), EPCAM (14->38), PECAM1 (15->39), ALPG (16->34), IL2RG (17->46),
DSC2 (18->27), TNFRSF11A (19->28), ERBB2 (20->32). All `available_weight_sum`=0.90 (full evidence),
all accessibility class A, all with high `T_rank_percentile` (0.79-0.94). They do not crater; they
drift just below the top20 cutoff.

### Result: genes that enter top20 when `T` is removed

| gene | base rank | accessibility_class | T_pct | E_pct | N_pct | P_pct |
|---|---|---|---|---|---|---|
| MYOF | 60 | D | 0.043 | 0.932 | 0.976 | 0.995 |
| ADGRE5 | 89 | B | 0.054 | 0.955 | 0.884 | 0.936 |
| IFITM1 | 82 | D | 0.058 | 0.994 | 0.919 | 0.933 |
| CD44 | 40 | A | 0.080 | 0.989 | 0.989 | 0.841 |
| HLA-E | 95 | A | 0.116 | 0.995 | 0.848 | 0.881 |
| GPR160 | 78 | C | 0.153 | 0.944 | 0.928 | 0.743 |
| SLC7A5 | 61 | C | 0.184 | 0.898 | 0.841 | 0.973 |
| SLC1A5 | 52 | C | 0.221 | 0.964 | 0.930 | 0.939 |
| GPRC5A | 32 | C | 0.225 | 0.950 | 0.997 | 0.954 |
| CLDN4 | 31 | C | 0.443 | 0.948 | 0.996 | 0.988 |
| CD9 | 25 | C | 0.491 | 0.991 | 0.892 | 0.923 |
| CDH1 | 34 | A | 0.500 | 0.934 | 0.979 | 0.983 |
| INSR | 35 | A | 0.500 | 0.855 | 0.872 | 0.915 |

### Interpretation: biological, with one identified structural contaminant

The dominant signature is biological. The genes displaced **out** of the top20 are uniformly
accessibility class A with high `T` percentile; the genes that rise **in** are predominantly
class C/D (tetraspanin CD9; claudin CLDN4; multipass GPCRs GPRC5A, GPR160; transporters SLC1A5,
SLC7A5; class D MYOF, IFITM1) with very low `T` percentile (0.04-0.49) but strong `E`/`N`/`P`
(0.85-0.99). Removing the accessibility layer floods the top20 with proteins that are highly
expressed and selective but physically hard to target by antibody. `T` is therefore doing exactly
the work it should: it gates on extracellular accessibility, the physical determinant of antibody
binding, and within the admitted set the order is set by the other layers.

The single structural contaminant is Group A: four HLA-DRB/KIR genes (ranks 2-5) propped up by
`Surf`+`T` only. They contribute to the `0.35` for a renormalization reason, not an accessibility
reason, and are already flagged hard by the top30 audit. Per the preregistered missing-data tiering
rule (`>=2` missing primary components cannot be Tier 1A; single-layer dependence cannot be Tier 1),
Fase 15 must demote them to Watchlist/Excluded. Applying that rule is preregistered tiering, not an
optimization of the `0.35`.

### Verdict

`T` dominance is **biological (genuine accessibility signal)**, not a transformation artifact. No
third transformation bug was found. The diagnostic does not change any score. Manuscript language:
the ranking is robust to parameterization (weight perturbation Spearman min 0.911) but its
components are not interchangeable, and extracellular accessibility is the most structural layer â€”
a mature characterization, not a weakness. The four thin-evidence HLA-DRB/KIR genes are handled by
the standing tiering rule in Fase 15.

---

## 2. Top30 false-positive audit: severity distribution of the `25/30`

`25/30` flagged is not "83% problematic." The severity distribution shows granular flags doing
their job, with a small genuinely-hard core.

- **No flag (5):** CDH3, ALPG, DSC2, TNFRSF11A, ULBP2.
- **Hard flag â€” `thin_evidence_missing_3plus` (4):** HLA-DRB3, HLA-DRB4, KIR2DL5A, KIR2DS1. These
  are the same Group A genes from section 1; genuine demotion candidates for Fase 15.
- **Moderate flag â€” `high_TME_flag` (10):** MPZL1, ITGB5, IFNGR1, PECAM1, ERBB2, LRRC15, HLA-DPB1,
  BTN3A3, LSR, TGFBR1. Signal may be partly stromal/immune; needs cell-resolution verification,
  not elimination.
- **Soft / expected â€” `high_normal_risk` (20 total carry it; 10 carry it as their only flag):**
  pervasive by construction. Every epithelial surface antigen has some normal expression, so this
  flag touching most candidates is expected, not disqualifying.
- **Evidence-gap â€” `protein_missing` (5):** HLA-DRB3/4, KIR2DL5A/S1, HLA-A (missing stomach-cancer
  IHC).

No top30 gene carries a hard safety red flag beyond the pervasive on-target/off-tumor `high_normal_risk`
already captured by `N`/`R`, except the 4 thin-evidence genes. Reading: top30 is **healthy-with-caveats**,
not problematic, plus a 4-gene hard core to demote. The `25/30` headline is reported as-is with this
severity breakdown.

---

## 3. Control recovery: both preregistered directions

### Upward (positive-control recovery), from `control_benchmark.tsv` baseline_rank_v2

Recovered into baseline top50 (4/8): EPCAM (14; top20-freq 1.00, top50-freq 1.00),
CEACAM5 (12; 1.00, 1.00), ERBB2 (20; top20-freq 0.34, top50-freq 1.00), MET (45; top50-freq 0.788).

Not recovered, documented biological/isoform/coverage exceptions (4/8): CLDN18 (1474; gene-level
cannot resolve CLDN18.2), FGFR2 (1333; isoform IIIb / amplification), TACSTD2/TROP2 (202; ranked
with normal-risk flag), MSLN (158; documented coverage/shedding). This matches the Fase 13
cause-corrected gate (0/5 pipeline-accusing) recorded under AD-19/DD-028: the aggregate top50 gate
is reported failed, the cause-corrected gate is the relevant diagnostic.

### Downward (negative / TME): MIXED result

The negative-control direction is **mixed, not clean**, and is reported as such:

- Intracellular negative controls (6/6) excluded from the universe entirely:
  ACTB, GAPDH, H3C1, TOMM20, CALR, ALB (`not_in_core_probable_universe`). Clean.
- PTPRC (leukocyte marker): demoted to rank 636 (leave-one-layer range 290-1230). Clean.
- PECAM1 (endothelial marker): **rank 15, identified only by flag (`high_known_tme_marker_control`),
  not by positional demotion.** The two compartment controls that should behave alike diverge by
  ~621 positions (PTPRC 636 vs PECAM1 15). PECAM1 satisfies its preregistered expectation
  (`not_top_100_or_flagged_TME`) only via the flag branch of an OR whose escape branch is a free
  automatic annotation; technically it passes, but on that branch the gate measures nothing.
  PECAM1's high rank is the bulk/TME limitation made explicit: its `E` signal is vascular and bulk
  RNA cannot separate endothelial from epithelial origin without single-cell data (the standing
  Fase 8 limitation, DD-023).

Manuscript wording (not "negative controls passed"): intracellular negative controls were excluded
from the universe (6/6) and the leukocyte marker PTPRC was strongly demoted (rank 636), confirming
the pipeline excludes non-surface and leukocyte signal; however, the endothelial marker PECAM1
remains at rank 15, identified only by a TME flag and not by positional demotion, reflecting the
known limitation of the bulk approach for separating endothelial from epithelial signal in the
absence of single-cell data.

### PECAM1 as the floor-calibration case (a-priori expectation registered 2026-05-31)

PECAM1 is the floor-calibration case for the **preregistered** TME tiering rule (master plan:
`tme_contamination_risk=high` -> no Tier 1A without tumor-cell membranous protein evidence;
`moderate_purity_confounded` -> Tier 1 allowed with flag). Fase 15 applies this rule; it does not
redesign it. Treating "how strict" as an open Fase 15 choice would itself reintroduce a post-hoc
degree of freedom, which the project's discipline exists to prevent.

To close the last "decided with the result in view" gap on the gene that is precisely a negative
control, the expected curation outcome is registered **now, before the HPA-web review**:

> **A-priori prediction (2026-05-31, before curation):** PECAM1 HPA stomach-cancer IHC is expected
> to show **vascular** staining, i.e. **not** tumor-cell membranous. Under the preregistered rule
> (high TME without tumor-cell membranous evidence -> not Tier 1A), the expected result is
> **PECAM1 -> Watchlist by the pre-existing rule**, not by a decision taken after seeing the rank.
> If, against expectation, the IHC shows genuine tumor-epithelial membranous staining, that must be
> recorded as a rule-relevant surprise, not silently used to keep PECAM1 in Tier 1.

This pre-writing makes the eventual demotion incontestable rather than merely defensible. By
contrast, ERBB2 (also `high` TME via `high_purity_adjusted_tme_correlation`, a categorically softer
label than PECAM1's `high_known_tme_marker_control`) is expected to survive via the same rule's
rescue clause because it has validated tumor-epithelial membranous IHC. The TME severity gradient is
already encoded in the data, so the rule demotes the known marker without collateral damage to
validated epithelial targets.

### Verdict

Positives recovered upward (EPCAM/CEACAM5/ERBB2/MET) with documented isoform/coverage exceptions:
that direction passes. The negative direction is **mixed**: intracellular controls and PTPRC are
clean, PECAM1 passes only via the TME-flag branch and sits in the coarse Tier 1 band. This means the
coarse Tier 1 contains at least one known compartment false positive, which reinforces (does not
contradict) the coarse-tiering decision and makes the preregistered compartment rule mandatory in
Fase 15. PECAM1 calibrates the floor; the real curation effort is the ambiguous candidate middle
(MPZL1, ITGB5, LSR, TGFBR1, BTN3A3, ...), not PECAM1.

---

## Consequences for Fase 15

1. Report coarse tiers only (Tier 1 / Tier 2 / Watchlist), no fine intra-tier order â€” post-scoring
   resolution supports nothing finer (1/20 with 95% rank interval inside top40).
2. Demote the four thin-evidence genes (HLA-DRB3, HLA-DRB4, KIR2DL5A, KIR2DS1) to Watchlist/Excluded
   under the standing missing-data tiering rule.
3. Manual-curate the 10 `high_TME_flag` genes for stromal/immune origin before any Tier 1 placement,
   applying the preregistered TME rule (severity-graded label + tumor-cell membranous rescue) without
   recalibrating it. Put the effort on the ambiguous middle, not on PECAM1.
4. Report the negative-control result as **mixed** (intracellular + PTPRC clean; PECAM1 via flag at
   rank 15) and carry the `T`-is-most-structural framing into the manuscript. Apply the registered
   2026-05-31 a-priori expectation that PECAM1 -> Watchlist after vascular-staining confirmation.

Nothing in this diagnostic authorizes re-touching `T`, re-tuning weights, or recalibrating flags.
The Fase 14 numbers stand as reported.
