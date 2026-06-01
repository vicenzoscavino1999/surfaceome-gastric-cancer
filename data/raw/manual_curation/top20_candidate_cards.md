# Top 20 Candidate Cards (Fase 15)

Cards for the top 20 of the frozen `Balanced` ranking (`ranking_v2_frozen.tsv`, SHA256 `95040e...`).
Tiers are coarse (Tier 1 / Tier 2 / Watchlist), unordered within a tier (Fase 14 resolution).
`SC` is `not_available` in the MVP; single-cell rows report the bulk TME flag. Structure is annotation
only. Curation informs tier, never score (no score changed; see `manual_curation_notes.tsv`).

Language is hypothesis-generating: these are nominations, not clinically proven or low-risk targets.

---

## Tier 1

### ITGB4 (rank 1)
- **Target form:** integrin beta-4 (single-pass, class A ECD)
- **Modalidad plausible:** ADC, bispecific (preclinical precedent)
- **Prevalence flag:** Broad (median 165 TPM; ~100% samples TPM>1)
- **Por que rankea alto:** very high E (0.97) and N (0.95) percentiles, accessible ECD, full evidence
- **Evidencia RNA:** strong, broad tumor expression
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.54)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected
- **Topologia/ECD:** accessibility class A; isoform multiple-mapped, unresolved
- **Estructura:** annotation pending (not scored)
- **Internalizacion/ADC suitability:** integrins internalize; plausible ADC
- **Riesgos normales:** hematopoietic high_critical; broad normal epithelial (hemidesmosomal) expression
- **Evidencia clinica:** preclinical ITGB4-targeted immunotherapy (breast/HNSCC), no gastric-specific or clinical-stage program
- **Novelty/competition:** moderately novel for gastric; CSC-associated
- **Limitacion principal:** basal/stratified epithelial normal expression (skin keratinocyte/hemidesmosome, laminin-5 anchorage essential for normal keratinocytes) → on-target skin toxicity risk; **skin is not in the organ-risk model so R may under-weight this**; agents preclinical only
- **Experimento wet-lab:** flow cytometry on gastric tumor vs normal epithelium; skin/basal-epithelium cross-reactivity; membranous IHC
- **Tier:** Tier 1 (passes all preregistered criteria; epithelial not compartment-FP, but strengthened skin/basal normal-expression caveat)

### CDH3 (rank 6)
- **Target form:** P-cadherin (single-pass, class A ECD)
- **Modalidad plausible:** ADC (PCA062 precedent), radioimmunotherapy, pCAD×CDH17 bispecific ADC
- **Prevalence flag:** Broad (median 15.6 TPM; 98.6% samples)
- **Por que rankea alto:** strong E/N, accessible ECD, clean evidence, low TME
- **Evidencia RNA:** broad tumor expression
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.64)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected
- **Topologia/ECD:** class A; isoform multiple-mapped
- **Internalizacion/ADC suitability:** validated ADC internalization (PCA062)
- **Riesgos normales:** immune moderate_off_tumor; overexpressed in tumor vs many normal tissues (favorable)
- **Evidencia clinica:** established TAA; ADC clinical activity in solid tumors
- **Novelty/competition:** known TAA, not gastric-validated — non-obvious gastric nomination
- **Limitacion principal:** confirm membranous tumor-cell IHC vs adjacent normal
- **Experimento wet-lab:** IHC membranous pattern; ADC cytotoxicity on gastric lines
- **Tier:** Tier 1 (strong; ADC precedent and favorable window)

### NECTIN2 (rank 9)
- **Target form:** CD112/Nectin-2 (single-pass, Ig V+C2 domains, class A ECD)
- **Modalidad plausible:** naked mAb (ADCC), ADC (ovarian precedent)
- **Prevalence flag:** Broad (median 117 TPM)
- **Por que rankea alto:** high E/N, good Ig ECD, low TME flag
- **Evidencia RNA:** strong tumor expression
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.67)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected (raw ρ=0.027) **but purity-adjusted partial ρ=0.32 with myeloid/macrophage module, p<0.001**
- **Topologia/ECD:** class A; isoform multiple-mapped
- **Internalizacion/ADC suitability:** anti-Nectin-2 ADC shown in ovarian xenografts
- **Riesgos normales:** liver high_critical; expressed on antigen-presenting/dendritic cells
- **Evidencia clinica:** immune-checkpoint ligand (PVRIG/TIGIT axis); anti-Nectin-2 mAb with ADCC; gastric scRNA literature reports LAMP3+ dendritic-cell expression
- **Novelty/competition:** active checkpoint/ADC interest, not gastric-specific
- **Limitacion principal:** partial myeloid/dendritic-cell compartment signal (purity-adjusted ρ=0.32 p<0.001 + DC-checkpoint literature), below the frozen 0.4 TME threshold; HPA shows membranous adenocarcinoma staining but not gastric-cell-resolved — **closest-to-threshold Tier 1 member, first to revisit with single-cell data**
- **Experimento wet-lab:** tumor-epithelial vs dendritic-cell expression by scRNA/flow; ADCC assay
- **Tier:** Tier 1 (user-confirmed 2026-05-31; rule-consistent — partial 0.32 < frozen 0.4 threshold; myeloid/DC caveat documented)

### CEACAM5 (rank 12) — positive control
- **Target form:** CEA (GPI-anchored, class A ECD)
- **Modalidad plausible:** ADC (tusamitamab ravtansine, labetuzumab govitecan)
- **Prevalence flag:** Broad (median 200 TPM; 95% samples)
- **Por que rankea alto:** high E/N/P, accessible ECD, low TME
- **Evidencia RNA:** strong tumor expression
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.70, the highest in Tier 1)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected
- **Topologia/ECD:** class A; isoform multiple-mapped
- **Internalizacion/ADC suitability:** clinical ADC programs
- **Riesgos normales:** lung high_critical; apical/normal GI epithelial expression
- **Evidencia clinica:** classical tumor antigen; multiple ADC trials
- **Novelty/competition:** positive control; well-trodden, useful benchmark
- **Limitacion principal:** normal GI epithelial expression; apical localization specificity review
- **Experimento wet-lab:** membranous vs apical IHC; tumor-normal specificity
- **Tier:** Tier 1 (positive control recovered; specificity caveat)

### JAG1 (rank 13)
- **Target form:** Jagged1 Notch ligand (single-pass, class A ECD)
- **Modalidad plausible:** naked neutralizing mAb
- **Prevalence flag:** Broad (median 28 TPM)
- **Por que rankea alto:** good E, accessible ECD, low TME flag
- **Evidencia RNA:** tumor overexpression (miR-142 axis)
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.72)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected
- **Topologia/ECD:** class A
- **Internalizacion/ADC suitability:** ligand; neutralizing antibody rationale rather than ADC
- **Riesgos normales:** endothelial high_critical; broad developmental Notch-ligand expression
- **Evidencia clinica:** oncogenic Notch ligand; neutralizing mAbs developed; surface-targetable (transmembrane ligand, not intracellular-only)
- **Novelty/competition:** mechanism-driven; broad expression tempers selectivity
- **Limitacion principal:** **dual tumor-epithelial + endothelial/vascular (angiocrine) expression** — most compartment-exposed Tier 1 member; partial vascular confound not captured by the low bulk TME flag; needs single-cell resolution of the tumor-epithelial fraction
- **Experimento wet-lab:** tumor-epithelial vs endothelial expression by scRNA/flow; Notch-blockade functional assay
- **Tier:** Tier 1 (rule-pass: low bulk TME, surface-targetable, genuinely epithelial; dual-compartment caveat)

### EPCAM (rank 14) — positive control
- **Target form:** epithelial cell adhesion molecule (single-pass, class A ECD)
- **Modalidad plausible:** naked mAb (catumaxomab history), ADC, bispecific
- **Prevalence flag:** Broad (median 404 TPM; 99.8% samples — highest prevalence in set)
- **Por que rankea alto:** very high E/N, accessible ECD, low TME
- **Evidencia RNA:** very strong, near-universal tumor expression
- **Evidencia proteica:** HPA stomach-cancer IHC available (P 0.51)
- **Evidencia single-cell:** SC not_available; bulk TME flag low_uncorrected
- **Topologia/ECD:** class A
- **Internalizacion/ADC suitability:** internalizes; ADC feasible
- **Riesgos normales:** kidney high_critical; **high normal epithelial expression** (preregistered penalty)
- **Evidencia clinica:** pan-epithelial antigen; historical toxicity concerns
- **Novelty/competition:** positive control; well-known, toxicity-limited
- **Limitacion principal:** high normal epithelial expression → on-target/off-tumor toxicity
- **Experimento wet-lab:** therapeutic-window modeling; normal epithelium cross-reactivity
- **Tier:** Tier 1 (positive control; loud normal-expression safety caveat)

---

## Tier 2 (within top 20)

### MPZL1 (rank 7)
- **Target form:** MPZL1/PZR (single-pass, class A ECD); **Modalidad:** ADC/mAb (preclinical)
- **Prevalence:** Broad (90 TPM). **RNA:** strong. **Protein:** HPA IHC available (P 0.66).
- **Single-cell:** SC not_available; **bulk TME flag high_purity_adjusted (high)**
- **Riesgos:** endothelial high_critical. **Clinica:** oncogenic in gastric cancer (poor survival).
- **Limitacion principal:** high TME flag — signal may be partly non-epithelial; needs cell-resolution
- **Wet-lab:** scRNA/flow tumor vs stroma; **Tier:** Tier 2 (fails Tier-1 TME criterion)

### ITGB5 (rank 8)
- **Target form:** integrin beta-5 (class A ECD); **Modalidad:** ADC/mAb
- **Prevalence:** Broad (61 TPM). **RNA:** strong. **Protein:** HPA IHC available (P 0.63).
- **Single-cell:** bulk TME flag high_purity_adjusted (high). **Riesgos:** endothelial high_critical.
- **Clinica:** promotes TGFβ-driven EMT/metastasis; correlates with immune infiltrates.
- **Limitacion principal:** high TME flag + broad expression. **Wet-lab:** tumor vs stroma resolution.
- **Tier:** Tier 2 (fails Tier-1 TME criterion)

### BST2 (rank 10)
- **Target form:** tetherin/CD317 (class A ECD); **Modalidad:** naked mAb (ADCC)
- **Prevalence:** Broad (132 TPM). **RNA:** strong. **Protein:** P 0.25 — **protein_present_no_membrane discordance**.
- **Single-cell:** bulk TME flag watchlist_uncorrected. **Riesgos:** hematopoietic high_critical.
- **Clinica:** overexpressed gastric vs adjacent normal; anti-BST2 mAb ADCC (myeloma).
- **Limitacion principal:** membrane-localization discordance weakens antibody-accessibility claim.
- **Wet-lab:** confirm membranous surface localization; **Tier:** Tier 2 (fails membrane-evidence criterion)

### IFNGR1 (rank 11)
- **Target form:** IFN-γ receptor 1 (class A ECD); **Modalidad:** uncertain (signaling receptor)
- **Prevalence:** Broad (54 TPM). **RNA:** strong. **Protein:** HPA IHC available (P 0.61).
- **Single-cell:** bulk TME flag high_purity_adjusted (high). **Riesgos:** lung high_critical; **ubiquitous on all nucleated cells**.
- **Clinica:** cytokine receptor; gastric risk polymorphism. **Limitacion principal:** ubiquitous expression, no tumor selectivity.
- **Wet-lab:** tumor vs normal quantitative surface density; **Tier:** Tier 2 (fails TME criterion; ubiquity caveat)

### ALPG (rank 16)
- **Target form:** placental alkaline phosphatase ALPG/ALPPL2 (GPI-anchored, class A ECD)
- **Modalidad plausible:** ADC, CD3 bispecific (ATG-112), CAR
- **Prevalence:** Moderate (median 0.4 TPM; 36% samples — restricted/tail)
- **Por que rankea alto:** very high N (selectivity) — but ranking is single-layer dependent
- **RNA:** restricted/tail expression. **Protein:** HPA IHC available (P 0.45).
- **Single-cell:** bulk TME flag low_uncorrected. **Riesgos:** **low (brain max; lower_risk_by_current_normal_expression)** — favorable window
- **Clinica:** oncofetal antigen, virtually absent from normal adult tissue except placenta; active ADC/bispecific programs
- **Novelty/competition:** strong, relatively novel oncofetal target with excellent window
- **Limitacion principal:** `single_layer_dependency` — high rank leans on one layer (selectivity); restricted prevalence
- **Wet-lab:** confirm tumor prevalence and surface density; ADC/bispecific cytotoxicity
- **Tier:** Tier 2 (fails not-single-layer criterion; **most promising biology in Tier 2** — flagged for priority re-evaluation if a second layer corroborates)

### IL2RG (rank 17) — see Watchlist note; ranked in top20
- Placed Watchlist (immune/lymphoid lineage); card retained for completeness. See Watchlist section.

### DSC2 (rank 18)
- **Target form:** desmocollin-2 (class A ECD); **Modalidad:** mAb/ADC
- **Prevalence:** Broad (12 TPM). **RNA:** present. **Protein:** HPA IHC available (P 0.67).
- **Single-cell:** bulk TME flag low_uncorrected. **Riesgos:** immune moderate_off_tumor.
- **Clinica:** literature reports **DOWNregulation in gastric cancer with progression** (tumor-suppressor-like).
- **Limitacion principal:** poor tumor-normal window (downregulated in tumor); single_layer_dependent.
- **Wet-lab:** tumor vs normal protein quantitation; **Tier:** Tier 2 (single-layer; negative-window caveat)

### TNFRSF11A (rank 19)
- **Target form:** RANK (class A ECD); **Modalidad:** mAb
- **Prevalence:** Broad (6.9 TPM). **RNA:** present. **Protein:** HPA IHC available (P 0.51).
- **Single-cell:** bulk TME flag low_uncorrected. **Riesgos:** GI epithelial moderate.
- **Clinica:** bone-metabolism receptor; **denosumab targets the ligand (RANKL), not RANK**.
- **Limitacion principal:** weak gastric-specific antibody rationale; single_layer_dependent.
- **Wet-lab:** gastric tumor surface expression confirmation; **Tier:** Tier 2 (single-layer)

### ERBB2 (rank 20) — positive control
- **Target form:** HER2 (single-pass, class A ECD); **Modalidad:** mAb, ADC (trastuzumab deruxtecan), bispecific
- **Prevalence:** Broad (64 TPM). **RNA:** strong. **Protein:** HPA IHC available (P 0.56).
- **Single-cell:** bulk TME flag high_purity_adjusted. **Riesgos:** kidney high_critical.
- **Clinica:** **validated gastric/GEJ target** (trastuzumab ToGA; T-DXd approved 2L); membranous companion-Dx IHC.
- **Por que aparece aqui pero en Tier 2:** balanced top20-frequency **0.34 < 0.40** → fails the preregistered Tier-1 stability criterion. Robustly top50 (freq 1.0). **Not forced to Tier 1.**
- **Limitacion principal:** top20-boundary instability consistent with known HER2 heterogeneity.
- **Wet-lab:** standard HER2 IHC/ISH; **Tier:** Tier 2 (established benchmark, stability-limited — honest non-gamed placement)

---

## Watchlist (within top 20)

### HLA-DRB3 (rank 2), HLA-DRB4 (rank 3), KIR2DL5A (rank 4), KIR2DS1 (rank 5)
- **Target form:** MHC class II beta chains (HLA-DRB3/4) and NK killer-Ig-like receptors (KIR2DL5A/2DS1)
- **Prevalence:** Restricted/non-assessable (median TPM 0 in TCGA-STAD)
- **Por que rankean alto:** artifact — ranked on `Surf`+`T` only (E, N, R, P all missing; available_weight_sum 0.25)
- **Evidencia RNA:** non-assessable (missing bulk expression). **Protein:** missing stomach-cancer IHC.
- **Single-cell:** SC not_available; **immune/NK-cell restricted biology**
- **Limitacion principal:** thin-evidence renormalization inflation (Fase 13 sanity-check #4); immune genes, not epithelial tumor targets
- **Wet-lab:** none recommended (not a tumor-cell target)
- **Tier:** Watchlist (rule: ≥3 missing primary components AND non-assessable core expression)

### PECAM1 (rank 15) — TME control
- **Target form:** CD31 endothelial adhesion molecule (class A ECD)
- **Prevalence:** Broad in bulk (44 TPM) — **but vascular, not tumor-epithelial**
- **Por que rankea alto:** high bulk E from tumor vasculature; bulk RNA cannot separate compartments
- **Evidencia proteica:** **HPA confirmed: cancer tissues mainly negative; expression in endothelial cells and smooth muscle, not tumor epithelium** (a-priori expectation registered 2026-05-31, confirmed)
- **Single-cell:** bulk TME flag high_known_tme_marker_control
- **Limitacion principal:** endothelial compartment marker; high rank is the bulk/TME limitation made explicit
- **Wet-lab:** none for epithelial targeting (negative control behaving as a compartment FP)
- **Tier:** Watchlist (tme_marker control; preregistered not-Tier-1; HPA-confirmed vascular)

### IL2RG (rank 17)
- **Target form:** common gamma chain (class A ECD)
- **Prevalence:** Broad in bulk (75 TPM) — lymphoid/hematopoietic origin
- **Evidencia proteica:** P 0.25 — **RNA_high_protein_absent discordance**
- **Single-cell:** bulk TME flag moderate_residual. **Riesgos:** hematopoietic high_critical.
- **Limitacion principal:** immune/lymphoid lineage receptor, not an epithelial tumor target; RNA-protein discordance
- **Wet-lab:** none recommended for epithelial targeting
- **Tier:** Watchlist (immune lineage + discordance)
