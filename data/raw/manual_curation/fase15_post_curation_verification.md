# Fase 15 Post-Curation Desk Verification

Date opened: 2026-05-31

Three desk-curation items raised after the Fase 15 tier assignment. All are reading/literature
checks; none is wet-lab and none changes scores, weights, the universe, or the frozen ranking.
Wet-lab validation is downstream work for another group and is explicitly NOT a step here.

---

## 1. NECTIN2 compartment verification [RESOLVED - remains Tier 1 with caveat]

Concern: gastric single-cell literature (Cancer Cell 2023 atlas; Wang lineage) reports NECTIN2/CD112
as a checkpoint gene enriched on LAMP3+ dendritic cells, not as an epithelial antigen. NECTIN2 is
currently Tier 1. It is a suspect third compartment false positive after PECAM1 (endothelial) and
LRRC15 (CAF/stromal).

### A-priori expectation (registered 2026-05-31, BEFORE the HPA gastric review)

This expectation is committed now and the HPA/Fase-8 evidence is examined in a later step, so the
decision provably precedes the look (same protocol as the PECAM1 demotion).

> NECTIN2 differs from PECAM1 in a way that matters: it is a broadly-expressed nectin adhesion
> molecule present on epithelial cells AND on antigen-presenting/dendritic cells (it is a TIGIT/PVRIG
> checkpoint ligand). Critically, in MY Fase 8 bulk data NECTIN2 carries a **low** TME flag
> (`low_uncorrected_tme_correlation`), unlike the high-TME compartment false positives PECAM1 and
> LRRC15 (and unlike MPZL1/ITGB5). On that basis I **expect HPA to show genuine epithelial/membranous
> staining** in gastric tumor and I **expect NECTIN2 to REMAIN Tier 1** — i.e., I expect it is NOT a
> pure compartment FP.
>
> The falsifiable risk is real and explicit: IF HPA shows predominantly immune/myeloid/dendritic-cell
> staining with weak or absent tumor-epithelial membranous staining, THEN NECTIN2 joins PECAM1/LRRC15
> as a compartment false positive → **Watchlist by the preregistered TME rule**, and Tier 1 drops from
> 6 to 5. The decision follows the rule whichever way the evidence falls; if the result contradicts
> this expectation it is recorded as a rule-relevant surprise, not bent to keep NECTIN2 in Tier 1.

### Evidence (examined 2026-05-31, after the a-priori was committed)

- **HPA:** general statement "most adenocarcinomas showed moderate **membranous** immunoreactivity,
  often combined with cytoplasmic staining" (antibodies HPA012759, CAB026138). Supports
  membranous-epithelial expression in adenocarcinoma, but the summary is NOT stomach-specific and is
  NOT cell-type-resolved (tumor-epithelial vs immune not disaggregated). Suggestive-positive for
  epithelial, not definitive.
- **Fase 8 (`tme_contamination_flags.tsv`):** raw TME correlation LOW and non-significant
  (max_tme_spearman_rho = 0.027, p = 0.58); **but purity-adjusted partial = 0.320 with the
  `myeloid_macrophage` module (p < 0.001)**, combined partial = 0.355 (p < 0.001). Final bulk flag:
  `low_uncorrected_tme_correlation` -> `no_tme_flag_from_bulk_modules` (the flag keys on the raw
  correlation, which is low). known_tme_control = false; median TPM 116.7; E percentile 0.98.
- **Threshold context:** the preregistered high-TME flag fires at purity-adjusted rho > 0.4
  (high-TME genes MPZL1/ITGB5 exceed it). NECTIN2 = 0.32 < 0.4, so it does NOT meet the frozen
  high-TME threshold.

### Result vs a-priori expectation

Mixed, and a rule-relevant note. The a-priori (stay Tier 1, bulk flag low) holds on the bulk flag,
and HPA gives genuine membranous-epithelial evidence (unlike PECAM1) -> NECTIN2 is NOT a clean
compartment FP. BUT curation surfaced a real, significant purity-adjusted **myeloid/dendritic-cell
partial signal (0.32, p<0.001)** that the bulk flag under-detected, corroborated by the LAMP3+ DC
checkpoint literature. The signal sits BELOW the frozen 0.4 high-TME threshold.

### Decision (by preregistered rule)

By the frozen rule, NECTIN2 **stays Tier 1**: it has membranous-epithelial HPA evidence and its
purity-adjusted TME partial (0.32) is below the preregistered 0.4 high-TME threshold. Demoting it
would require lowering that frozen threshold for this one gene -- a post-hoc adjustment symmetric to
forcing ERBB2 up, and therefore disallowed. The myeloid/DC partial signal + DC-checkpoint literature
are recorded as an explicit caveat: **NECTIN2 is the Tier 1 member closest to the compartment
threshold and the first to demote if single-cell data confirm dendritic-cell origin.**

**User confirmed (2026-05-31): keep NECTIN2 in Tier 1 with the documented myeloid/DC caveat.** Tier 1
remains 6 members. The discipline is symmetric: just as the 0.40 stability bar was not raised to keep
ERBB2 in Tier 1, the 0.40 TME bar is not lowered to push NECTIN2 out. Single-cell data are the first
thing to revisit for NECTIN2.

---

## 2. ITGB4 and JAG1 - Tier 1 curation [RESOLVED]

Both are Tier 1 but were not given detailed curation in Pass 1. Tier 1 cannot have uncharacterised
members. Web desk-curation, classify each as: validated target / plausible non-established nomination
/ compartment-or-ubiquity false positive. If problematic, apply the tiering rule (may drop).

**ITGB4 (integrin beta-4 / CD104)** — classification: plausible non-established nomination; NOT a
compartment FP (it is epithelial), but with a strengthened normal-tissue caveat.
- Expression: basal/stratified epithelium (skin keratinocytes, hemidesmosomes anchoring epithelium to
  basement membrane via laminin-5), also endothelial cells, immature thymocytes, Schwann cells. Broad
  in normal basal epithelium, not tumor-restricted.
- Targetability: surface integrin; preclinical only (ITGB4-pulsed DC vaccine, anti-CD3/anti-ITGB4
  bispecific BiAb). No clinical-stage agent.
- Documented risk: α6β4-mediated keratinocyte attachment to basement membrane is essential in normal
  skin -> on-target/off-tumor skin toxicity risk. The organ-risk model does not include skin/basal
  epithelium, so this risk may be under-weighted by R.
- Decision: remains Tier 1 by rule (epithelial, not a compartment marker), with an explicit caveat
  that basal-epithelial/skin normal expression is a real toxicity concern possibly under-captured.

**JAG1 (Jagged1 / Notch ligand)** — classification: plausible nomination, surface-targetable, but
dual-compartment expression.
- Targetability: transmembrane Notch ligand with an accessible ECD; neutralizing mAbs developed. It is
  surface-targetable, NOT purely intracellular signaling.
- Compartment: expressed on BOTH tumor epithelial cells AND endothelial/vascular cells (angiocrine
  function, strong in tumor-associated blood vessels). Partial compartment confounding — not a pure
  compartment marker like PECAM1, but a substantial non-tumoral (endothelial) fraction.
- Decision: remains Tier 1 by rule (bulk TME flag low_uncorrected; genuinely tumor-epithelial and
  surface-targetable), but flagged as the **most compartment-exposed Tier 1 member**; tumor-epithelial
  vs endothelial fraction requires single-cell resolution before strong nomination.

---

## 3. Cross-check vs Wang 2026 [RESOLVED via open access]

Initial concern: Wang et al. 2026 (Cell Reports Medicine) appeared inaccessible because ScienceDirect
returned 403. This was later resolved as bot-blocking, not a paywall. Identifiers verified:
DOI 10.1016/j.xcrm.2026.102756; ScienceDirect pii S2666379126001734; AACR abstract
10.1158/1538-7445.AM2026-7647.

Goal: extract the supplementary surface-target gene list and cross it against our Tier 1 (6) + Tier 2
(12). Interpretation is a distinct claim either way:
- Our nominations NOT in Wang -> "independent nomination not prioritised by the contemporary atlas."
- Our nominations IN Wang -> "concordance with Wang using only public data and a reproducible method."

Access routes: UPC institutional access; ScienceDirect "request full text"; contact Bing Zhang / CPTAC.

- Access status: **RESOLVED (2026-05-31).** The ScienceDirect 403 was bot-blocking, not a paywall —
  Cell Reports Medicine is gold open access. Retrieved full text + supplementary via Europe PMC REST
  (PMC13198309): fullTextXML and supplementaryFiles zip (108 MB, CC BY-NC-ND). The surface/drug-target
  nomination table is mmc8 "Drug_target_classes" (3,090 unique genes parsed in the current audit;
  1,228 membrane-protein-flagged genes; drug-class framework
  PMID 38917788 + ADC/Antibody/T-cell annotation) and the glycoprotein-outlier tables (figures 7B/7D).
  Cross-check saved to `results/tables/wang2026_crosscheck.tsv`; enrichment against the Core+Probable
  universe is saved to `results/tables/wang2026_overlap_enrichment.tsv`.

### Cross-check result (concordance, not novel discovery)

- **16/18 of our Tier 1+Tier 2 are in Wang's drug-target table.** Tier 1 6/6; Tier 2 10/12 (absent:
  CD9, LSR — independent/divergent nominations). Our positive controls map to Wang's clinically-drugged
  tiers (ERBB2/FGFR2/MET/TACSTD2 T1+ADC/Ab; CLDN18 T3+ADC/Ab; MSLN ADC/Ab), so the table tracks
  clinical reality.
- **The 16/18 overlap is enriched, not only a raw count.** Against the 2,704-gene Core+Probable
  universe, Wang drug-target-table overlap expected by random draw is 9.47/18; observed is 16/18
  (one-sided hypergeometric p=0.0013). Against Wang's stricter membrane-protein flag, expected is
  5.79/18 and observed is 13/18 (p=5.6e-4).
- **Our novel Tier 1 (CDH3, NECTIN2, ITGB4, JAG1) are Wang "Membrane" but undrugged (ADC=0/Ab=0)** —
  concordant yet still novel.
  2026-05-31 manuscript correction: CDH3 is no longer described as "undrugged" in the manuscript
  because P-cadherin ADC-development precedent was captured during curation; the precise claim is
  Wang membrane-class concordance plus external ADC-development precedent outside Wang's ADC flag.
- **Orthogonal proteomic (glyco-outlier) corroboration, selective:** CEACAM5 #4, CDH17 #19, EPCAM #22,
  ITGB5 #40, DSC2 #49 are top surface glyco-outliers in Wang's proteomics (evidence we did not have,
  RNA/HPA only). CDH3/NECTIN2/JAG1 are NOT top glyco-outliers — corroboration is partial, reported
  honestly.
- **Compartment thesis independently validated:** Wang concludes vulnerabilities "extend beyond
  epithelial tumor cells to stromal and immune compartments" and confirms EPCAM epithelial-predominant
  (C4) plus a fibroblast-predominant surface-target set — exactly our PECAM1/LRRC15 compartment-FP
  narrative and bulk/TME limitation.

Manuscript framing after the Fase 17B matched-null audit: consistency with a contemporary 15-layer
proteogenomic atlas using only public RNA/HPA/UniProt data and a reproducible method, plus independent
compartment-discipline and stability framework. This is benchmark/context support, not independent
method validation; CD9/LSR are own divergent nominations.

### Single-cell compartment cross-check (Wang Figure 7H, rendered from the open-access main PDF)

Wang Figure 7H is a single-cell dot plot of cell type (Epithelial/Fibroblasts/Endothelial/B/CD4.T/
CD8.T/Dendritic/Mast/Mono-Mac/NK/PCs/PMNs) x ~75 surface-target outliers. It is a curated outlier
subset, not all targets. Of our genes, only a few appear, but those confirm our calls:

- **EPCAM -> Epithelial row** (strong dot): confirms our Tier 1 epithelial assignment.
- **HLA-DPB1 -> immune rows (Dendritic/Mono-Mac)**: confirms our Watchlist immune assignment.
- **CD47 -> broad/multiple rows**: consistent with our ubiquitous-target Watchlist.
- **ERBB2 -> epithelial + fibroblast** (per Wang text, Figure 7H): benchmark.

Framework validation: Figure 7H shows a clear **fibroblast-target block** (ASPN, FAP, DCN, MFAP4,
VCAN, COL3A1/5A1, LTBP1) and a clear **immune-target block** (PTPRC, CD68, CD74, HLA-DOA1/DPB1, CD3E,
MPO, FCGR3A), independently validating our LRRC15-CAF and PECAM1/IL2RG/HLA compartment-FP reasoning.

Honest limit: most of our specific nominations (NECTIN2, PECAM1, LRRC15, CDH3, CDH17, CEACAM5) are NOT
in Wang's curated single-cell panel, so no direct per-gene comparison for them. In particular, the
NECTIN2 dendritic-cell question cannot be resolved from Wang's figure; it remains supported only by our
Fase 8 purity-adjusted myeloid partial (0.32) plus DC-checkpoint literature. The figure-extraction
follow-up is therefore CLOSED as partially resolved: framework + EPCAM/HLA-DPB1 confirmed; NECTIN2/
PECAM1/LRRC15 not individually testable against Wang.
