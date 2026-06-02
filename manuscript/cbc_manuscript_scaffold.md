# SurfPrior-GC: a reproducible framework for uncertainty-aware gastric cancer surface-target prioritization with GPI evidence-routing audit

Draft status: CBC adaptation started 2026-06-01. This is not a submission-ready manuscript.

Target journal: Computational Biology and Chemistry, full-length article, subscription route.

## Abstract

We introduce SurfPrior-GC, a reproducible framework for gastric cancer surface-target prioritization that integrates heterogeneous public evidence while keeping uncertainty explicit rather than collapsing it into a single ranked list. The central methodological finding is a GPI-anchor evidence-routing audit: topology-first routing had excluded 54 confirmed glycosylphosphatidylinositol (GPI)-anchor genes from the ranked universe. Crediting confirmed lipidation evidence at universe construction increased the ranked Core+Probable surfaceome from 2,650 to 2,704 genes, raised confirmed GPI-anchor representation from 65 to 119 genes, moved `CEACAM5` from rank 120 to 12 and `MSLN` from rank 453 to 158, and produced a median improvement of 453 positions among common confirmed GPI-anchor genes. SurfPrior-GC then integrates tumor/normal RNA sequencing, Human Protein Atlas (HPA) protein and localization evidence, UniProt topology and lipidation annotations, curated surfaceome resources, benchmark controls, and stability analysis. The final output was a coarse, unordered set of experimentally testable Tier 1/2 hypotheses, including six Tier 1 candidates, with explicit caveats for bulk RNA, compartment attribution, isoform resolution, HPA immunohistochemistry granularity, and absence of wet-lab validation. Tier 1/2 nominations were consistent with contemporary surface-target resources, but their overlap was not enriched beyond a matched null controlling for surfaceome confidence, expression, protein evidence, topology, component completeness, and accessibility. SurfPrior-GC supports reproducible, transparent hypothesis generation with explicit uncertainty boundaries while making public bulk-data limits part of the result.

## Keywords

gastric cancer; surfaceome; target prioritization; reproducibility; GPI-anchored proteins; proteogenomics

## 1. Introduction

### 1.1 Why surface-target prioritization is hard

Surface-target prioritization from public data is not equivalent to ranking genes by tumor RNA abundance. RNA expression does not establish protein presence, membrane localization, extracellular accessibility, tumor-cell attribution, isoform specificity, or an acceptable normal-tissue profile [13,23,24,31,32]. Bulk tumor RNA can reflect tumor microenvironment (TME) compartments, including endothelial, immune, and stromal cells, rather than malignant epithelial cells [15-18]. Surfaceome resources also differ in how they route non-transmembrane evidence, including glycosylphosphatidylinositol (GPI)-anchored proteins; prior in silico surfaceome work explicitly accounted for annotated GPI-linked proteins, so the open problem here is not whether GPI anchors can be surface evidence but how incomplete evidence routing propagates into an auditable candidate universe and ranking [5].

### 1.2 Clinical context and contribution

In gastric adenocarcinoma, antibody-accessible surface proteins remain a tractable intervention space because they can support antibody-based therapeutics, antibody-drug conjugates (ADCs), cell therapies, receptor blockade, or imaging strategies [1-8,31,37,38]. Established and emerging gastric cancer targets, including ERBB2, CLDN18.2, FGFR2b, TACSTD2/TROP2, EPCAM, CEACAM5, MET, MSLN, CDH17, CD66c, and PVR/CD155, provide useful benchmarks but do not remove the need for systematic prioritization [25-28,33-39].

Recent literature already includes pan-cancer surfaceome resources, pan-cancer ADC target discovery, tumor-specificity modeling, gastric clinical-trial target prioritization, gastric proteogenomic vulnerability atlases, and single-target or subtype-focused gastric/GEJ/GSRCC ADC discovery studies [3,6-8,19,20,31-39]. We therefore introduce SurfPrior-GC, a release-grade, uncertainty-aware framework for auditing how heterogeneous public surfaceome evidence is combined, bounded, and converted into experimentally testable hypotheses in gastric cancer. Its main transferable contribution is a GPI-anchor evidence-routing audit: SurfPrior-GC quantifies how topology-first routing excluded 54 confirmed GPI-anchor genes, corrects this at universe construction before scoring, and preserves the downstream effect on ranking and benchmark behavior. The framework then integrates RNA, protein/localization, topology, normal-risk, TME, benchmark-control, and stability evidence into a coarse experimental queue. External TCSA and Wang comparisons are used as consistency and scope checks, with matched-null behavior reported as an evidential boundary rather than candidate-level experimental evidence.

## 2. Material and methods

### 2.1 Reproducibility design

The analysis was implemented as a staged reproducible workflow rather than as an exploratory notebook. Controls, exclusion criteria, dataset targets, scoring scenarios, random seeds, tissue mappings, and coarse tiering rules were pre-specified in repository configuration and decision files before candidate interpretation; this is an operational repository freeze, not a formal external registry entry. Raw or downloaded inputs were checksum-registered where stored locally, and each major analysis stage produced both machine-readable tables and a short report. The repository preserves design decisions, analytical decisions, provenance records, a release manifest, and stage-specific validation checks, following reproducible-computational-research and findable, accessible, interoperable, reusable data principles where feasible [29,30].

Workflow integrity was assessed with three levels of checks. First, unit tests cover core scripts and stage-specific invariants. Second, a smoke test verifies expected outputs from data inventory through manuscript figure/table packaging, including manual curation artifacts. Third, Snakemake declares the workflow outputs and reports whether any declared artifact is missing or out of date. Some early bootstrap and data-inventory outputs were generated before all rules were formalized and therefore retain missing Snakemake provenance metadata; these steps write source inventories and checksum context rather than scoring outputs, and all later analysis, ranking, and manuscript-package outputs are tracked.

Intermediate ranking snapshots were retained rather than overwritten. The pre-fix snapshot preserves the ordinal surfaceome-confidence transform, the pre-GPI snapshot preserves the state before the GPI-anchor correction, and the final frozen ranking snapshot preserves the active ranking after the universe-wide GPI evidence correction and downstream rerun. This version history was kept to document bug detection and correction, not to select a favorable ranking retrospectively.

### 2.2 Datasets and identifier normalization

The main input sources are summarized in Table 1. TCGA-STAD and GTEx expression data were obtained through the UCSC Xena/Toil RNA-seq recompute and used as the primary tumor-normal RNA matrix [9,10,21]. GDC TCGA-STAD metadata and cBioPortal TCGA-STAD clinical and copy-number fields were used for clinical covariate availability, selected amplification context, and secondary sensitivity planning [11,12]. Human Protein Atlas (HPA) downloadable files supplied normal IHC, cancer IHC, subcellular localization, and tissue RNA context [13,23,24]. UniProtKB reviewed human records supplied protein identifiers, topology, transmembrane annotations, extracellular features, signal peptides, lipidation/GPI-anchor evidence, protein length, and isoform mappings [14]. TCSA, CSPA, SURFY, UniProt GO, UniProt topology/GPI fields, and HPA subcellular localization were integrated to construct the surfaceome universe [3-5].

Identifier normalization used HGNC-approved protein-coding genes as the primary denominator before surfaceome filtering [22]. This choice prevents the candidate denominator from being inflated by noncoding or deprecated matrix rows while preserving alias, Ensembl, UniProt, and HPA mappings for evidence integration. Mapping failures and source coverage are retained as audit outputs rather than silently dropped.

### 2.3 Surfaceome universe construction

The surfaceome universe was defined at the HGNC gene level. Core/Probable membership required independent surface support plus an anchor, topology, or localization signal. Qualifying anchor evidence included UniProt extracellular topology, UniProt transmembrane annotation, confirmed UniProt lipidation `GPI-anchor`, HPA plasma membrane localization, or SURFY surfaceome support. Curated-list or GO-only genes lacking such support were retained as ambiguous surface-context genes rather than treated as high-confidence surface targets.

The final Core+Probable universe contains 2,704 genes: 2,646 Core and 58 Probable. Published-list overlap was used as a sanity check, with Jaccard overlap of 0.7749 for TCSA, 0.2889 for CSPA, and 0.8017 for SURFY. Negative controls did not enter Core/Probable, and positive/benchmark controls were present or documented.

Confirmed UniProt lipidation `GPI-anchor` evidence was credited as a non-experimental strong anchor signal at the universe construction stage. Specifically, confirmed GPI evidence contributed score +2, one support source, `has_anchor=true`, and `has_strong=true`. Subcellular-location-only GPI annotations were flagged but not credited as confirmed direct lipidation evidence. This universe-wide correction was applied before final ranking rather than as a target-specific patch.

### 2.4 Tumor expression and heterogeneity

Tumor expression was computed for the Core+Probable universe using TCGA-STAD primary tumor samples from the Xena/Toil matrix. Xena/Toil values were treated as `log2(TPM + 0.001)`, transformed back to TPM as `2^x - 0.001`, and clipped at zero. Of 2,704 Core+Probable genes, 2,696 had measured Xena expression and 8 were missing.

The tumor expression component `E` combines abundance and prevalence. For each measured gene, percentile ranks were computed for median tumor TPM, the fraction of tumor samples with TPM > 1, P75 tumor TPM, and P90 tumor TPM. The raw expression score was:

`E_raw = 0.40 * rank(median_TPM_tumor) + 0.30 * rank(percent_samples_TPM_gt_1) + 0.20 * rank(P75_TPM_tumor) + 0.10 * rank(P90_TPM_tumor)`.

The `E` score is a component score only. It is not by itself a final target ranking.

Molecular subtype, stage, tissue-origin, and selected amplification summaries were computed when fields were available. TCGA molecular subtypes were used for expression and power summaries. Exact Lauren subtype was not available in the current raw sources; histology proxy fields were retained only as audit information and were not treated as quantitative Lauren labels. cBioPortal GISTIC calls were queried for ERBB2, FGFR2, and MET to provide amplification context.

### 2.5 Normal selectivity and off-tumor risk

Normal selectivity and on-target/off-tumor risk were estimated with the same TPM transformation as tumor expression. TCGA-STAD primary tumor, GTEx stomach normal, and TCGA-STAD adjacent normal samples were summarized separately. The primary stomach normal comparator used GTEx stomach because the adjacent-normal set was source-matched but smaller.

The selectivity component `N` combines two tumor-normal contrasts and a statistical rule. `N_stomach` compares tumor median TPM with GTEx stomach median TPM. `N_critical` compares tumor median TPM with the maximum mapped critical normal expression across Xena/HPA-derived normal tissue contexts. The component score was:

`N_score = 0.50 * rank(N_critical_log2fc) + 0.30 * rank(N_stomach_log2fc) + 0.20 * N_stat_gtex`.

The pre-specified positive statistical rule required tumor versus GTEx stomach log2 fold-change >= 1 and BH-FDR < 0.05. The TCGA adjacent-normal comparison was reported as a sensitivity context rather than as a full replacement for GTEx stomach.

The off-tumor risk component `R` used a pre-specified maximum weighted organ penalty. Critical organs and tissue classes were assigned manually chosen expert-prior weights, including heart and brain at 1.00, liver and kidney at 0.90, lung and endothelial contexts at 0.85, hematopoietic at 0.80, immune at 0.75, gastrointestinal epithelial at 0.70, and reproductive/other at 0.60. These weights are not learned, optimized, or inferred from outcome data. `R` is high-worse: higher values indicate greater on-target/off-tumor concern and are subtracted in the integrated score. Alternative `R_max_plus_breadth` and `R_sum_capped` forms were retained for sensitivity analysis.

### 2.6 Protein and localization evidence

Protein/localization evidence was computed from HPA stomach cancer IHC, HPA normal IHC, and HPA subcellular localization. In the 2,704-gene Core+Probable universe, HPA stomach cancer IHC covered 1,790 genes, HPA normal stomach and critical normal IHC covered 1,535 genes, and HPA subcellular localization covered 1,302 genes. Membrane or cell-junction localization support was present for 734 genes. CPTAC/PDC proteomics was not assessed in the primary analysis and was not imputed.

The `P` component combines tumor protein presence, membrane or cell-junction localization support, mapped normal protein safety support, HPA reliability support, and discordance penalties. The HPA bulk cancer file does not expose antibody IDs, staining intensity/quantity fields, patient-level membrane pattern, or multi-antibody concordance. These unavailable fields were not inferred and are marked for candidate-card review where relevant.

Discordance flags include HPA-missing stomach cancer IHC, high RNA but absent tumor protein, protein present without membrane/cell-junction support, and low-confidence HPA evidence. HPA absence does not automatically eliminate a candidate because the protein layer has incomplete coverage and antibody-level detail is unavailable in the bulk files.

### 2.7 Tumor microenvironment specificity

No processed gastric single-cell RNA-seq dataset was admitted into the numeric primary score. The optional `SC` component therefore remains `not_available` and has zero weight in the primary ranking.

As a pre-specified fallback, bulk TCGA-STAD expression was used to flag possible TME-derived signal. Marker modules were computed for CAF/fibroblast, endothelial, myeloid/macrophage, T-cell, and B/plasma compartments. For each candidate gene, Spearman correlations were computed between candidate expression and each module score across 414 TCGA-STAD tumors. ESTIMATE stromal and immune signatures from `tidyestimate` were also computed from the same Xena/Toil matrix and used as relative purity/admixture covariates for partial Spearman correlations [15].

After the ranking and tiers were frozen, processed TISCH2 gastric cancer summaries were used only as candidate-level compartment annotations for the 18 Tier 1/2 genes [16-18]. `STAD_GSE134520` included a malignant-cell class, whereas `STAD_GSE167297` provided epithelial/TME context only. These annotations did not alter `SC`, the integrated score, or tier assignments.

These outputs are flags only. They are not hard ranking filters and are not interpreted as absolute pathology purity estimates. ESTIMATE and the TME marker modules both represent stromal/immune biology, so their partial correlations are biologically collinear rather than clean causal decomposition. A `high_purity_adjusted_tme_correlation` flag therefore triggers conservative review with protein/localization and cell-resolved evidence where available.

### 2.8 Topology, extracellular accessibility, and isoforms

Topology and extracellular accessibility were computed from reviewed UniProt human feature fields for all 2,704 Core+Probable genes. Parsed fields included protein length, topological domains, transmembrane segments, signal peptides, lipid/GPI anchor features, glycosylation, disulfide bonds, chains/domains, subcellular location, PTM comments, and Ensembl isoform mappings.

Each protein was assigned an accessibility class from A to E. Classes A/B indicate clear or inferred extracellular regions suitable for antibody-accessibility review. Class C indicates possible but less straightforward access, often for multipass proteins or shorter extracellular loops. Classes D/E are not automatic exclusions from the universe but block Tier 1 antibody-targeting claims unless later structure, literature, or candidate-card evidence supports an exception.

The topology component `T` combines accessibility class, extracellular length, topology confidence, and isoform confidence, then subtracts conservative cleavage/shedding and soluble-decoy penalties. These penalties are candidate-card flags, not hard exclusions. GPI-anchor features are explicitly captured in this layer; MSLN is the benchmark example where GPI anchoring supports membrane accessibility despite absence of a classical transmembrane segment.

Isoform-specific benchmarks were handled conservatively. `CLDN18` and `FGFR2` remain gene-level in the current expression layers, so `CLDN18.2` and `FGFR2b/IIIb` claims are marked `isoform_unresolved` and are not used as evidence that the pipeline resolves isoform-specific expression.

### 2.9 Integrated scoring and sensitivity

The integrated score used the pre-specified components listed in Table 2. The primary scenario used manually chosen expert-prior weights `Surf=0.15`, `E=0.20`, `N=0.20`, `R=0.20`, `P=0.15`, `SC=0.00`, and `T=0.10`. These weights are transparent design choices, not learned coefficients or optimal estimates. `SC` remained unavailable and was not imputed. Sensitivity scenarios included safety-prioritized, ADC-focused, novelty-focused, and protein-evidence-focused weighting; these were reported as sensitivity contexts, not alternative primary rankings.

`Surf` is the relative surfaceome confidence within the admitted Core+Probable universe. After the GPI correction, it is scaled as:

`Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`

over the theoretical admitted confidence range 5 to 10, not over the observed min/max of the current dataset. This means that zero indicates the lowest admitted confidence level, not absence from the surfaceome universe.

Let `x_gj` denote the scaled component value for gene `g` and component `j`, `w_j` the primary weight, and `A_g` the available nonzero-weight components for that gene. The integrated score was:

`S_g = (sum_{j in A_g, j != R} w_j * x_gj - w_R * x_gR) / sum_{j in A_g} abs(w_j)`

For score computation, missing principal components were handled with exclude-and-renormalize: the weighted score was computed over available nonzero-weight components and divided by the available absolute weight sum. Missingness was then carried into tiering restrictions and sensitivity analyses rather than mean-imputed. `R` is the only high-worse primary component and is subtracted from the total score. Rank percentiles used average-rank tie handling so tied raw component values received identical percentile values rather than HGNC-order-dependent ranks.

The stability analysis evaluated weight perturbation, leave-one-layer-out sensitivity, missing-data sensitivity, risk-threshold sensitivity, organ-weight perturbation, scenario stability, and post-scoring rank resolution. These analyses supported coarse tier language but not fine intra-tier ordering.

### 2.10 Tiering and manual curation

Tiering was performed only after stability analysis. The original fine tiering plan was collapsed to unordered coarse categories because post-scoring rank resolution supported coarse interpretation but not fine rank distinctions. The tiering rule file was frozen before candidate assignment. Tier 1 required stability, no unexplained critical normal risk, no unsupported TME-marker status, acceptable accessibility class, protein evidence or documented absence, no more than two missing primary components, and absence of single-layer dependence. Tier 2 captured candidates failing one Tier 1 criterion or showing scenario/subtype dependence. Watchlist captured candidates with major missingness, TME-marker behavior, unresolved benchmark isoforms, or other non-nominable but biologically relevant signals.

Manual curation informed tiers and caveats but did not change scores. The top 30 candidates were reviewed against UniProt, HPA, literature, clinical/druggability context, Wang 2026 concordance, and analysis-stage flags. Candidate notes explicitly record whether curation changed the score; all current entries preserve `changes_score=no`.

External baseline behavior was assessed in two ways. First, final scores were compared with the Cancer Surfaceome Atlas final and core GESP scores [3] over overlapping genes by Spearman correlation and top-k overlap. This is a pan-cancer surfaceome-prioritization baseline, not a gastric-specific validation label. Second, external consistency was assessed against Wang 2026 gastric proteogenomic surface-target resources [19]. Two null models were retained for the Wang comparison. The first was a one-sided hypergeometric test against random draws from the frozen Core+Probable surfaceome universe. The second was a deterministic matched-null sensitivity analysis with 20,000 permutations and seed 20260531, sampling nearest-neighbor Core+Probable controls matched on surfaceome confidence, tumor expression percentile, protein-evidence percentile and missingness, topology percentile, available component count, and accessibility class. This cross-check is used as benchmark concordance and compartment-framework support, not as clinical-efficacy evidence or as per-gene single-cell support for genes absent from the Wang Figure 7H panel.

## 3. Results

### 3.1 SurfPrior-GC workflow and GPI-routing audit

SurfPrior-GC integrates public transcriptomic, protein, localization, topology, and curated surfaceome resources into a staged candidate-prioritization pipeline (Fig. 1; Table 1). The current execution covers dataset inventory, raw/source checksum capture, batch diagnostics, identifier normalization, surfaceome universe construction, tumor expression, normal selectivity and off-tumor risk, HPA protein/localization evidence, TME specificity flags, topology/isoform annotation, integrated scoring, stability analysis, coarse tiering, external baseline comparison, candidate-level scRNA compartment annotation, and manuscript figure/table packaging. Unit tests, smoke tests through the figure/table package, the manuscript brief check, and Snakemake dry-run checks pass for declared current outputs.

The final surfaceome universe contains 2,704 Core+Probable genes, comprising 2,646 Core and 58 Probable candidates (Fig. 2). The construction rule balanced published surfaceome support with direct anchor, topology, or localization evidence. This conservative rule excluded all intracellular/secreted negative controls from Core+Probable while retaining benchmark surface-target genes for downstream scoring.

During scoring diagnostics, confirmed GPI-anchored candidates exposed a source-integration problem. Treating GPI evidence only as a downstream topology note under-credited confirmed GPI-anchored surface proteins at the surfaceome universe layer. Prior surfaceome work already recognized annotated GPI-linked proteins [5]; the issue quantified here is local evidence routing in a gastric cancer prioritization workflow. Confirmed lipidation evidence was therefore credited universe-wide as non-experimental strong anchor evidence before rerunning downstream analyses, while subcellular-location-only GPI annotations remained flagged but uncredited as direct lipidation evidence.

After correction, the active final ranking uses the fixed theoretical `Surf_relative_confidence` scale over the admitted confidence range 5 to 10. This means that low `Surf` values represent lower relative confidence within an admitted surfaceome universe, not absence from the surfaceome. The GPI finding is therefore interpreted as a transferable under-crediting issue in resource integration, not as evidence that all GPI-anchored proteins are strong therapeutic candidates.

The impact of the correction was quantified against the preserved pre-GPI snapshot. The ranked universe increased from 2,650 to 2,704 genes; all 54 newly ranked genes were confirmed UniProt GPI-anchor genes. Confirmed GPI anchors increased from 65 to 119 ranked genes. None were in the pre-GPI top 50, whereas five confirmed GPI anchors entered the final top 50 (`BST2`, `CEACAM5`, `ALPG`, `ULBP2`, and `NT5E`), with zero classified as suspicious Surf-dominant entrants by the pre-stability audit. Among common GPI genes, the median rank improvement was 453 positions. The correction also changed benchmark behavior: `CEACAM5` moved from rank 120 to 12, and `MSLN` moved from rank 453 to 158. Because tiering was performed after the correction, no pre/post tier-change claim is made; instead, the current Tier 1/2 set contains three confirmed GPI candidates (`CEACAM5`, `BST2`, and `ALPG`).

### 3.2 External consistency and scope boundary

The primary behavior of SurfPrior-GC is transparent hypothesis generation with explicit uncertainty. Against the TCSA final GESP baseline, final scores showed moderate concordance across 2,685 overlapping genes (Spearman rho=0.389861, p=3.5e-98), with low top20 identity (1/20: `NECTIN2`) and 6 of 18 Tier 1/2 genes in the TCSA final-score top100. The TCSA core GESP baseline gave similar moderate concordance (rho=0.329466, p=5.3e-69), 2/20 top20 overlap (`ERBB2` and `ITGB4`), and 8 of 18 Tier 1/2 genes in the baseline top100. This supports external surfaceome consistency while showing that the final ranking is not a clone of a pan-cancer surfaceome score.

External consistency was also assessed against Wang 2026. Sixteen of eighteen Tier 1/2 nominations were present in Wang's drug-target table, including all six Tier 1 genes. Against the 2,704-gene Core+Probable universe, this exceeded a simple random draw (one-sided hypergeometric p=0.0013; odds ratio 7.27). However, a matched-null sensitivity analysis showed that the observed Wang overlap was not above matched expectation after controlling for surfaceome confidence, expression, protein-evidence availability, topology, component completeness, and accessibility class. For the all-table background, the matched-null mean overlap was 15.18 of 18 (upper-tail p=0.436); for the Wang membrane-protein flag, the matched-null mean was 13.99 of 18 (p=0.817). The external checks therefore support plausibility and benchmark consistency while leaving candidate-level experimental evidence to follow-up studies.

### 3.3 Tumor expression, normal selectivity, and risk landscape

Tumor expression was measured for 2,696 of 2,704 Core+Probable genes. The `E` component captured both expression magnitude and prevalence in TCGA-STAD primary tumors. The normal selectivity component `N` combined tumor versus GTEx stomach contrast, tumor versus mapped critical-normal contrast, and a pre-specified statistical rule. Under the GTEx stomach statistical selectivity rule, 757 genes met `log2FC >= 1` and BH-FDR < 0.05.

The off-tumor risk component `R` provided an opposing high-worse layer (Fig. 3). In the current conservative maximum-risk model, 1,825 Core+Probable genes had high critical off-tumor risk. This high count is expected because many cell-surface proteins are shared across normal epithelial, endothelial, hematopoietic, immune, or organ-specific compartments. `E`, `N`, and `R` therefore need to be interpreted together: tumor abundance without normal-context review can over-rank broadly expressed targets, while a high normal-risk flag does not automatically exclude gastric-lineage or clinically benchmarked antigens.

### 3.4 Integrated evidence across candidates

The primary frozen ranking was converted into coarse tiers only after stability analysis and manual curation (Fig. 4; Table 3). Tier 1 contains six unordered surface-target hypotheses: `ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, and `EPCAM`. Tier 2 contains twelve additional candidates: `MPZL1`, `ITGB5`, `BST2`, `IFNGR1`, `ALPG`, `DSC2`, `TNFRSF11A`, `ERBB2`, `CD9`, `LSR`, `CDH17`, and `TGFBR1`.

The Tier 1 set is intentionally not presented as a fine rank order. Its members combine high tumor expression/selectivity, protein/localization support, and accessible topology, but each carries interpretation caveats. For example, `ITGB4` has basal/stratified epithelial expression not fully captured by the organ-risk model, `NECTIN2` has a purity-adjusted myeloid/DC signal below the frozen high-TME threshold, `CEACAM5` and `EPCAM` retain normal epithelial expression concerns, and `JAG1` has dual epithelial/endothelial biology. These caveats are part of the prioritization output rather than post-hoc exclusions.

Tier 2 captures candidates with strong but less stable or more caveated evidence. `ERBB2`, an established HER2 benchmark, remains Tier 2 because its primary-scenario top-20 stability frequency (0.34) does not meet the pre-specified Tier 1 stability threshold of 0.40, although it is robustly recovered within the top 50. `CDH17` is likewise retained as Tier 2: its external clinical and biological relevance is noted, but the bulk ranking and stability criteria do not support Tier 1 placement in this pipeline.

### 3.5 TME specificity and compartment caveats

Because no processed gastric single-cell matrix was admitted into the primary score, compartment specificity was handled through flags rather than a numeric `SC` layer (Fig. 5; Supplementary File 2). The TME fallback identified known immune, endothelial, and stromal markers as high-risk cases for epithelial tumor-target interpretation. `PECAM1` remained high in the bulk ranking but was assigned to Watchlist by the pre-specified TME rule after curation confirmed vascular/endothelial rather than tumor-epithelial staining. `LRRC15` was also assigned to Watchlist because curation supported a CAF/stromal interpretation rather than a primary malignant-epithelial target claim.

The same compartment discipline applies to immune genes and thin-evidence high-rank artifacts. HLA and KIR genes with missing primary expression/protein/risk components were Watchlist by the missing-data rule, not by subjective demotion. `HLA-DPB1`, `IL2RG`, and related immune-context candidates are retained as biologically relevant but not nominated as epithelial tumor-cell surface targets.

The candidate-level TISCH2 cross-check is deliberately context-only. In `STAD_GSE134520`, all 18 Tier 1/2 genes were present: 8 were malignant-class supported, 1 was mixed, 7 had low malignant signal, and 2 were non-malignant dominant. `STAD_GSE167297` provided epithelial/TME context only because no malignant-cell class was present. These results are candidate annotations, not score components.

These single-cell calls are not symmetric evidence for or against tier placement. `STAD_GSE134520` contains only 880 malignant-class cells and was designed around premalignant lesions and early gastric cancer. Low or non-malignant calls for `CDH3`, `ALPG`, `CEACAM5`, and `EPCAM` therefore lower confidence in tumor-cell attribution and make tumor-cell membrane confirmation mandatory before experimental prioritization, but they do not override the frozen multi-layer score or tiers.

`NECTIN2` and `JAG1` illustrate the same rule in the opposite direction: supportive annotations can reduce concern but do not eliminate compartment caveats. Both remain Tier 1 under frozen criteria, but `NECTIN2` remains closest to the TME threshold and `JAG1` remains exposed to endothelial/angiocrine interpretation.

### 3.6 Stability and control diagnostics

Stability analysis supported coarse candidate interpretation but not fine within-tier ordering (Fig. 6a-b). Weight perturbations were generally stable: 231 of 250 perturbations passed both pre-specified gates, with minimum and median Spearman correlations of 0.910703 and 0.983898 relative to the final ranking. However, leave-one-layer-out analyses showed important layer dependence, especially for `T`, `R`, and `E`, and post-scoring rank resolution found only 1 of 20 baseline top20 genes with a 95% rank interval contained within the top 40. These results justify coarse tiers rather than fine rank claims.

Control behavior was used as a diagnostic rather than for weight tuning (Fig. 7; Table 4). Positive-control top50 recovery remained imperfect at 4 of 8 (`ERBB2`, `EPCAM`, `MET`, and `CEACAM5`). The aggregate pre-specified top50 gate therefore remains reported as failed. The cause review was added after the aggregate miss and is reported as an explanatory diagnostic, not as a replacement success criterion: `CLDN18` and `FGFR2` are isoform unresolved at gene level, `MSLN` retains a topology/shedding penalty despite high protein support and corrected GPI evidence, and `TACSTD2` has intermediate surface confidence and weaker protein support. Negative intracellular controls were excluded from Core/Probable; `PTPRC` was cleanly low-ranked for epithelial targeting; `PECAM1` remained the documented vascular/TME exception and was handled by Watchlist tiering.

### 3.7 Candidate interpretation

The candidate panel summarizes the final applied output of the pipeline (Fig. 8; Table 3; Supplementary File 2). The Tier 1 set should be read as a compact, experimentally testable hypothesis set rather than as a list of proven therapeutic targets. Candidate behavior is most useful where it reveals the framework's boundaries: `ERBB2` remaining Tier 2 shows that benchmark status did not override frozen stability rules, and Watchlist placement for `PECAM1` and `LRRC15` shows how bulk surfaceome ranking can over-rank endothelial or stromal signals when cell-resolved data are unavailable.

Tier 1/2 candidates therefore function as a prioritized experimental queue with explicit caveats. Their value in this manuscript is not stand-alone translational validity, but the fact that each nomination carries the evidence layers, missingness, compartment warnings, normal-risk context, and stability limits needed to decide what validation would be required next.

## 4. Discussion

### 4.1 What the pipeline adds

This study presents SurfPrior-GC, a reproducible public-data workflow for prioritizing gastric cancer surface-target hypotheses while preserving the uncertainty that usually gets compressed into a single ranked list. Its main positive methods contribution is the GPI-routing audit: 54 confirmed GPI-anchor genes were absent from the ranked universe under topology-first routing, and universe-stage correction changed both candidate-space membership and benchmark ranks before final scoring. The broader pipeline integrates surfaceome membership, tumor expression, tumor-normal selectivity, normal-tissue risk, protein/localization evidence, and topology/accessibility, while keeping single-cell specificity unavailable rather than imputed. Its contribution is not a claim that any individual candidate is ready for translation, but a transparent method for combining heterogeneous evidence layers and showing where that evidence is strong, weak, or confounded. This positioning is deliberately narrower than pan-cancer target-discovery frameworks, tumor-specificity models, general multi-omics prioritization platforms, and recent gastric target-prioritization or proteogenomic resources [6-8,20,31-34].

The TCSA and Wang comparisons address different external-reference questions. TCSA provides a pan-cancer surfaceome-score baseline: the moderate rank correlation and low top20 identity show that the workflow is aligned with established surfaceome evidence but not reducible to it. Wang 2026 is best interpreted as a gastric-specific consistency check. Other contemporary gastric proteogenomic work provides therapeutic-vulnerability context but is not treated here as a candidate label [34]. The overlap with Wang exceeds a simple random draw but not a matched null, which matters because both resources enrich for highly expressed and well-annotated surface proteins. Taken together, the external checks support plausibility and benchmark consistency, while CD9 and LSR remain divergent nominations, glyco-outlier corroboration is selective, and the curated Wang Figure 7H single-cell panel does not directly plot most of the specific nominees.

Recent gastric/GEJ/GSRCC ADC studies show why the present work should not be framed as first target discovery. CD66c and PVR/CD155 have already been prioritized and tested in subtype- or site-focused ADC workflows, and CDH17-targeted ADC work illustrates continued target-specific development in gastrointestinal cancers [35,36,39]. The value of the present framework is complementary: it makes the broad public-data prioritization process, evidence routing, stability limits, and candidate caveats auditable before any wet-lab or modality-specific validation is claimed.

The workflow also makes uncertainty visible. ERBB2 remaining Tier 2 rather than being forced into Tier 1 shows that benchmark recovery was not used to override frozen stability rules. PECAM1 and LRRC15 moving to Watchlist shows that bulk RNA surfaceome ranking can produce compartment-derived false positives when cell-resolved data are unavailable. CLDN18 and FGFR2 remaining isoform unresolved shows that gene-level expression is insufficient for isoform-specific claims. These are not failures to be hidden; they are the evidence boundaries that make the prioritization interpretable.

### 4.2 Transferable GPI-anchor lesson

The GPI-anchor audit is the most transferable concrete methods artifact from this work. Confirmed GPI-anchored proteins are biologically membrane-associated and can be relevant to antibody-accessible targeting, and prior surfaceome work already recognized this class explicitly [5]. The narrower lesson is that a pipeline can under-credit GPI-anchored candidates when list overlap or classical transmembrane topology is weighted above confirmed lipidation evidence during universe construction.

The correction is therefore a routing-design precaution for workflows that build candidate universes from heterogeneous surfaceome lists and topology fields. It does not generalize to resources that already handle GPI evidence appropriately, such as SURFY, and it does not imply that GPI anchoring alone makes a good target. The discussion-level consequence is compact: evidence routing changed which 54 confirmed GPI-anchor genes the framework was allowed to evaluate before scoring began.

### 4.3 Candidate tiers as method diagnostics

The candidate tiers are useful because they show how the framework behaves under pressure. Established biology does not automatically override frozen criteria: ERBB2 remains Tier 2 because it misses the Tier 1 stability threshold. High bulk expression does not automatically imply malignant epithelial targeting: PECAM1 and LRRC15 are retained as Watchlist examples of endothelial and stromal signal. External concordance does not erase normal-tissue or compartment caveats: CEACAM5, EPCAM, NECTIN2, ITGB4, JAG1, and CDH3 still require candidate-specific validation before any translational claim.

This candidate behavior is the point of a methods-forward paper. The output is an experimental queue with evidence boundaries, not a ranked claim that the top genes are intrinsically superior therapeutic targets. Cases such as ERBB2, PECAM1, LRRC15, CLDN18, FGFR2, and the GPI-anchored candidates show where the framework refuses to simplify away benchmark expectations, compartment risk, isoform ambiguity, or routing artifacts.

The Watchlist is therefore not a discard bin. It is a visible record of the cases that a score-only view could over-promote, including immune HLA/KIR genes with thin evidence, endothelial PECAM1, CAF/stromal LRRC15, immune IL2RG/HLA-DPB1/BTN3A3, and ubiquitous or toxicity-prone CD47.

### 4.4 Limitations

Several limitations are central to interpretation. First, the Tier 1/2 set is externally consistent, but its Wang overlap exceeds a simple random-draw null and not the matched null that controls for surfaceome confidence, expression, protein evidence, topology, component completeness, and accessibility. This is a boundary made visible by the framework, not a secondary apology for the result.

Second, the expression layers are based on bulk RNA rather than isolated malignant epithelial cells. Bulk signal can reflect tumor cells, stromal cells, immune cells, endothelial cells, or mixtures of these compartments [15-18]. Bulk TME correlations, ESTIMATE-adjusted partial correlations, and the limited TISCH2 candidate-level check provide conservative review flags, but they do not replace single-cell or spatial validation.

Third, tumor-normal selectivity is constrained by source and sample-size limitations. TCGA-STAD primary tumors and GTEx stomach normals were processed through the Xena/Toil recompute, but TCGA/GTEx source effects remain explicit. TCGA adjacent normal samples provide a source-matched sensitivity context but are lower-powered than GTEx stomach. The risk model is intentionally conservative, yet some normal compartments such as skin/basal epithelium are incompletely represented and must be revisited in candidate-specific review.

Fourth, HPA bulk IHC provides useful protein and localization evidence but lacks antibody-level and patient-level membrane detail in the downloadable cancer file [13,23,24]. A candidate with HPA tumor staining and subcellular membrane support still requires antibody-specific review, tumor-cell membrane quantification, and normal-tissue cross-reactivity assessment before experimental prioritization.

Fifth, the primary score did not admit a processed gastric scRNA dataset. `SC` is therefore unavailable rather than imputed. The limited TISCH2 analysis annotates compartment caveats for the 18 Tier 1/2 candidates, but it does not solve cell-of-origin for the full ranked universe, provide patient-level malignant-cell prevalence for every candidate, or alter scores or tiers [16-18]. Only `STAD_GSE134520` contributes a TISCH2 malignant-cell class, and `STAD_GSE167297` is context-only.

Sixth, gene-level expression cannot resolve isoform-specific targets. CLDN18.2 and FGFR2b remain explicitly `isoform_unresolved`; their positions in the ranking cannot be used as evidence that the pipeline resolves isoform-specific abundance. Similarly, topology/accessibility annotations do not establish antigen density, epitope exposure in native tumor tissue, internalization, shedding behavior, or therapeutic index.

Finally, this is a computational, hypothesis-generating study without wet-lab validation. Wang 2026 consistency checks and HPA/UniProt support strengthen candidate context, but they do not establish clinical efficacy or safety for any nominated target.

Sex-stratified and gender-related analyses were outside the scope of the current analysis. These dimensions should be assessed where relevant in future candidate-specific validation and translational study design.

### 4.5 Experimental follow-up

The highest-priority follow-up is experimental confirmation of tumor-cell surface abundance. Flow cytometry, cell-surface capture proteomics, or orthogonal surface-enrichment methods would directly test the surface-accessibility assumptions that public RNA, HPA, and topology annotations cannot resolve alone [4,13,24]. Tumor and normal tissue IHC should be repeated with validated antibodies and scored for membrane pattern, tumor-cell specificity, and normal compartment expression.

Compartment resolution is especially important for the most exposed candidates. NECTIN2 should be evaluated in cell-resolved data to distinguish tumor-epithelial expression from dendritic/myeloid checkpoint-ligand biology. JAG1 requires separation of tumor epithelial and endothelial/vascular expression. PECAM1 and LRRC15 provide useful negative examples for epithelial targeting but may be relevant to vascular or stromal strategies if framed as different modalities.

Modality-specific assays should follow confirmation of tumor-cell surface abundance. ADC-relevant candidates require internalization and payload-sensitivity testing. CAR or bispecific candidates require antigen-density and normal cross-reactivity assessment. GPI-anchored candidates require attention to shedding, soluble isoforms, and surface-retention behavior. The output of this pipeline is therefore a prioritized experimental queue, not a substitute for target validation.

## 5. Conclusions

This study provides SurfPrior-GC, a reproducible framework for uncertainty-aware gastric cancer surface-target prioritization from public evidence. Its concrete transferable contribution is the GPI audit: confirmed lipidation evidence should be handled at universe construction when defining surfaceome candidates, because incomplete routing excluded 54 confirmed GPI-anchor genes and changed benchmark-relevant ranks.

The resulting Tier 1 and Tier 2 hypotheses are a coarse experimental queue, not a target list alone. They preserve a transparent record of what heterogeneous bulk RNA, protein/localization, topology, normal-risk, surfaceome, and benchmark data can and cannot establish.

The matched-null result defines the scope of the evidence: gastric-atlas agreement is not enriched beyond a surfaceome-evidence-matched null, and no wet-lab validation is provided here. The nominated genes should therefore be treated as experimentally testable hypotheses with explicit validation requirements, not as established therapeutic targets.

## Glossary

**ADC.** Antibody-drug conjugate.

**CSPA.** Cell Surface Protein Atlas.

**GPI.** Glycosylphosphatidylinositol, a lipid anchor that can attach proteins to the cell surface.

**GTEx.** Genotype-Tissue Expression project.

**HPA.** Human Protein Atlas.

**IHC.** Immunohistochemistry.

**SC.** Single-cell specificity score component; unavailable and not imputed in the primary score.

**SURFY.** Published in silico human surfaceome resource.

**TCSA.** The Cancer Surfaceome Atlas.

**TISCH2.** Tumor Immune Single-cell Hub 2.

**TME.** Tumor microenvironment.

## Figure captions

**Figure 1. SurfPrior-GC reproducible public-data workflow for gastric cancer surface-target prioritization.** The workflow begins with frozen public inputs, identifier normalization, and construction of a Core+Probable surfaceome universe, then computes tumor expression (`E`), normal selectivity (`N`), high-worse off-tumor risk (`R`), HPA protein/localization evidence (`P`), topology/accessibility (`T`), TME flags, stability checks, and coarse tiering. The figure reports stage-level counts and separates quantitative evidence layers from review flags and downstream hypothesis generation.

**Figure 2. SurfPrior-GC surfaceome evidence landscape and GPI-anchor correction.** Source overlap and confidence summaries show how curated surfaceome resources, UniProt topology/GPI evidence, HPA localization, GO annotations, and SURFY support contribute to the 2,704-gene Core+Probable universe. Confirmed UniProt lipidation `GPI-anchor` evidence is credited as a source-wide non-experimental strong anchor during universe construction. Low `Surf` values in the final ranking indicate lower relative confidence within the admitted universe, not absence from the surfaceome.

**Figure 3. Tumor-normal selectivity and off-tumor risk landscape.** Candidate genes are positioned by TCGA-STAD tumor expression, stomach and critical-normal selectivity, and conservative organ-risk context. `R` is a high-worse component and is subtracted in the integrated score. The display illustrates why tumor abundance, normal selectivity, and off-tumor risk must be interpreted jointly rather than as independent target-readiness claims.

**Figure 4. Multi-layer evidence heatmap for the top 30 ranked candidates.** The heatmap summarizes `Surf`, `E`, `N`, `R`, `P`, `T`, missingness, TME flags, topology/accessibility, and coarse tiers for the top-ranked candidates from the final frozen ranking. Tiers are unordered within Tier 1, Tier 2, and Watchlist. Watchlist entries document immune, stromal, endothelial, ubiquitous, or thin-evidence cases that would be overinterpreted by a score-only view.

**Figure 5. Tumor microenvironment specificity fallback.** Bulk TCGA-STAD marker-module and ESTIMATE-adjusted partial-correlation outputs flag likely CAF/fibroblast, endothelial, myeloid/macrophage, T-cell, and B/plasma compartment signals among top candidates. These outputs are flags only and do not replace cell-resolved single-cell or spatial validation. `SC` remains `not_available` and is not imputed in the primary score.

**Figure 6. Rank stability and weighting sensitivity.** (a) Rank-stability heatmap from weight perturbation, leave-one-layer-out, missing-data, risk-form, organ-weight, and post-scoring resolution analyses. (b) Weighting-sensitivity bumpchart comparing the primary pre-specified ranking with safety-prioritized, ADC-focused, novelty-focused, protein-evidence-focused, and robust-aggregate contexts. Stability supports coarse tiers and explicit caveats, but not fine within-tier ordering.

**Figure 7. Benchmark-control behavior.** Positive, secondary, negative, and TME/off-tumor controls are shown as diagnostics of pipeline behavior rather than as tuning targets. Positive-control top50 recovery is reported as imperfect, isoform-specific benchmarks remain unresolved where expression is gene-level, intracellular negative controls are excluded from Core+Probable, and `PECAM1` is retained as the documented vascular/TME exception handled by Watchlist tiering.

**Figure 8. Tier 1 candidate panel.** The six unordered Tier 1 hypotheses are `ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, and `EPCAM`. The panel summarizes component evidence, Wang 2026 concordance, and candidate-specific caveats. These nominations are experimentally testable hypotheses and do not imply clinical efficacy, clinical safety, antigen density, internalization, or wet-lab validation.

## Table captions

**Table 1. Public datasets, versions, uses, and limitations.** Primary and secondary sources used for the workflow, including Xena/Toil TCGA-STAD/GTEx RNA, GDC and cBioPortal metadata, HPA IHC/localization/RNA files, UniProt reviewed-human topology/GPI features, curated surfaceome resources, TISCH2 candidate-level scRNA context, and optional resources not admitted into the numeric primary score. The table records source versions, checksum manifests where applicable, and interpretation limits.

**Table 2. Score components and primary weights.** Definitions, directions, weights, primary sources, normalization conventions, and principal limitations for `Surf`, `E`, `N`, `R`, `P`, `SC`, and `T`. `R` is high-worse and subtracted; `SC` remains unavailable with zero weight; missing components are handled by exclude-and-renormalize during scoring and by tier restrictions during interpretation.

**Table 3. Tier 1 and Tier 2 candidates.** Coarse unordered Tier 1 and Tier 2 nominations from the final frozen ranking, stability outputs, and manual curation. Columns report rank, score, prevalence flag, stability frequency, component values, Wang 2026 class/glyco-outlier context, and the principal caveat. The table is a hypothesis list, not a clinical target list.

**Table 4. Benchmark-control diagnostics.** Positive controls, secondary benchmarks, intracellular negative controls, and TME/off-tumor controls used to assess whether the pipeline behaves plausibly. Control behavior is reported honestly, including the failed aggregate positive-control top50 gate and the cause-level interpretation of misses. Controls were not used to retune weights or rescue individual candidates.

## Supplementary material

Supplementary material is supplied separately for Editorial Manager. Supplementary File 1 contains the table manifest for Supplementary Tables S1-S24, including titles, repository paths, availability status, and archived-data-package coverage. Supplementary File 2 contains candidate flags and interpretation guardrails for the top 30 ranked candidates, including TME risk, normal-risk interpretation, accessibility class, HPA status, discordance flags, missing primary components, isoform-resolution status, and candidate-specific caveats.

## Data and code availability

All inputs used in the current analysis are public resources. Downloaded or captured raw/source files are listed in the release manifest, dataset registry, download manifest, and provenance log, with checksums where files are stored locally. Mutable API captures, including cBioPortal clinical/GISTIC JSON files, are treated as frozen archived inputs for release reproduction; live re-downloads are best-effort transparency checks rather than the default reproducibility claim.

Analysis code is available at https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer under final code release tag `v0.1.3`. The frozen reproducibility data package for release candidate `v0.1.0-rc4` is archived on Zenodo at https://zenodo.org/records/20498705 with DOI `10.5281/zenodo.20498705`. The active frozen ranking table has SHA256 `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`, with file-level metadata in `results/rankings/ranking_v2_frozen.metadata.yaml`.

The repository includes smoke tests, unit tests, manuscript checks, Snakemake dry-run checks, GitHub Actions small CI, and manual full-data release-audit hooks documented in the README and reproducibility guide. No new patient samples, wet-lab data, or restricted-access clinical data were generated for this study.

## Declarations

**Ethics approval and consent to participate.** Not applicable. This study uses publicly available, de-identified, aggregate, or open-access research data and does not generate new human-subject samples.

**Consent for publication.** Not applicable.

**Author information.** Vicenzo Scavino Alfaro, Independent Researcher, Lima, Peru. ORCID: 0009-0000-2472-9785. Correspondence: u201919346@upc.edu.pe. Telephone: +51 962 559 391. The author has confirmed that the correspondence email is retained permanently by the university.

**Declaration of interests.** The author declares no competing interests.

**Funding.** The author received no funding for this research.

**Author contributions.** Vicenzo Scavino Alfaro is the sole author and was responsible for conceptualization, data curation, formal analysis, methodology, software, validation, visualization, writing-original draft, writing-review and editing, and final manuscript approval.

**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.** During the preparation of this work, the author used OpenAI Codex to support manuscript organization, language editing, and repository-oriented consistency checks. The author reviewed, revised, verified, and approved the final manuscript and accepts full responsibility for its content.

## Acknowledgements

The author acknowledges the developers, maintainers, data generators, and participants behind TCGA, GTEx, GDC, UCSC Xena/Toil, HPA, UniProt, HGNC, cBioPortal, TCSA, CSPA, SURFY, ESTIMATE/tidyestimate, TISCH2, the underlying public gastric single-cell datasets, and the Wang 2026 open-access gastric proteogenomic atlas. No endorsement by those projects is implied.

## Graphical abstract caption

SurfPrior-GC integrates public TCGA/GTEx RNA, HPA protein/localization, UniProt topology/GPI features, curated surfaceome resources, TME marker modules, and limited TISCH2 candidate annotations for gastric cancer surface-target prioritization. A universe-wide GPI-anchor evidence-routing audit restores 54 confirmed GPI-anchor genes before ranking. Outputs are coarse, hypothesis-generating Tier 1/2 nominations with external TCSA/Wang consistency checks and explicit limits from bulk RNA, compartment flags, isoform ambiguity, HPA IHC granularity, and absence of wet-lab validation.

## References

1. Bray F, Laversanne M, Sung H, Ferlay J, Siegel RL, Soerjomataram I, et al. Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries. CA Cancer J Clin. 2024;74:229-263. doi:10.3322/caac.21834.
2. Cancer Genome Atlas Research Network. Comprehensive molecular characterization of gastric adenocarcinoma. Nature. 2014;513:202-209. doi:10.1038/nature13480.
3. Hu Z, Yuan J, Long M, Jiang J, Zhang Y, Zhang T, et al. The Cancer Surfaceome Atlas integrates genomic, functional and drug response data to identify actionable targets. Nat Cancer. 2021;2:1406-1422. doi:10.1038/s43018-021-00282-w.
4. Bausch-Fluck D, Hofmann A, Bock T, Frei AP, Cerciello F, Jacobs A, et al. A mass spectrometric-derived cell surface protein atlas. PLoS One. 2015;10:e0121314. doi:10.1371/journal.pone.0121314.
5. Bausch-Fluck D, Goldmann U, Muller S, van Oostrum M, Muller M, Schubert OT, et al. The in silico human surfaceome. Proc Natl Acad Sci U S A. 2018;115:E10988-E10997. doi:10.1073/pnas.1808790115.
6. Li X, Zhou J, Zhang W, You W, Wang J, Zhou L, et al. Pan-cancer analysis identifies tumor cell surface targets for CAR-T cell therapies and antibody drug conjugates. Cancers (Basel). 2022;14:5674. doi:10.3390/cancers14225674.
7. Razzaghdoust A, Rahmatizadeh S, Mofid B, Muhammadnejad S, Parvin M, Mohammadi Torbati P, et al. Data-driven discovery of molecular targets for antibody-drug conjugates in cancer treatment. BioMed Res Int. 2021;2021:2670573. doi:10.1155/2021/2670573.
8. Kathad U, Biyani N, Peru Y Colon De Portugal RL, Zhou J, Kochat V, et al. Expanding the repertoire of antibody drug conjugate targets with improved tumor selectivity and range of potent payloads through in-silico analysis. PLoS One. 2024;19:e0308604. doi:10.1371/journal.pone.0308604.
9. Goldman MJ, Craft B, Hastie M, Repecka K, McDade F, Kamath A, et al. Visualizing and interpreting cancer genomics data via the Xena platform. Nat Biotechnol. 2020;38:675-678. doi:10.1038/s41587-020-0546-8.
10. Vivian J, Rao AA, Nothaft FA, Ketchum C, Armstrong J, Novak A, et al. Toil enables reproducible, open source, big biomedical data analyses. Nat Biotechnol. 2017;35:314-316. doi:10.1038/nbt.3772.
11. Grossman RL, Heath AP, Ferretti V, Varmus HE, Lowy DR, Kibbe WA, et al. Toward a shared vision for cancer genomic data. N Engl J Med. 2016;375:1109-1112. doi:10.1056/NEJMp1607591.
12. Cerami E, Gao J, Dogrusoz U, Gross BE, Sumer SO, Aksoy BA, et al. The cBio Cancer Genomics Portal: an open platform for exploring multidimensional cancer genomics data. Cancer Discov. 2012;2:401-404. doi:10.1158/2159-8290.CD-12-0095.
13. Uhlen M, Fagerberg L, Hallstrom BM, Lindskog C, Oksvold P, Mardinoglu A, et al. Tissue-based map of the human proteome. Science. 2015;347:1260419. doi:10.1126/science.1260419.
14. UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2025. Nucleic Acids Res. 2025;53:D609-D617. doi:10.1093/nar/gkae1010.
15. Yoshihara K, Shahmoradgoli M, Martinez E, Vegesna R, Kim H, Torres-Garcia W, et al. Inferring tumour purity and stromal and immune cell admixture from expression data. Nat Commun. 2013;4:2612. doi:10.1038/ncomms3612.
16. Han Y, Wang Y, Dong X, Sun D, Liu Z, et al. TISCH2: expanded datasets and new tools for single-cell transcriptome analyses of the tumor microenvironment. Nucleic Acids Res. 2023;51:D1425-D1431. doi:10.1093/nar/gkac959.
17. Zhang P, Yang M, Zhang Y, Xiao S, Lai X, et al. Dissecting the single-cell transcriptome network underlying gastric premalignant lesions and early gastric cancer. Cell Rep. 2019;27:1934-1947.e5. doi:10.1016/j.celrep.2019.04.052.
18. Jeong HY, Ham IH, Lee SH, Ryu D, Son SY, et al. Spatially distinct reprogramming of the tumor microenvironment based on tumor invasion in diffuse-type gastric cancers. Clin Cancer Res. 2021;27:6529-6542. doi:10.1158/1078-0432.CCR-21-0792.
19. Wang Y, Olsen LK, Jiao F, Wang C, Jiang KX, Dou Y, et al.; Clinical Proteomic Tumor Analysis Consortium. A 15-layer multi-omics analysis of gastric cancer ecotypes provides therapeutic insights. Cell Rep Med. 2026;7:102756. doi:10.1016/j.xcrm.2026.102756.
20. Deng EZ, Marino GB, Clarke DJB, Diamant I, Resnick AC, Ma W, et al. Multiomics2Targets identifies targets from cancer cohorts profiled with transcriptomics, proteomics, and phosphoproteomics. Cell Rep Methods. 2024;4:100839. doi:10.1016/j.crmeth.2024.100839.
21. GTEx Consortium. The GTEx Consortium atlas of genetic regulatory effects across human tissues. Science. 2020;369:1318-1330. doi:10.1126/science.aaz1776.
22. Tweedie S, Braschi B, Gray K, Jones TEM, Seal RL, Yates B, et al. Genenames.org: the HGNC and VGNC resources in 2021. Nucleic Acids Res. 2021;49:D939-D946. doi:10.1093/nar/gkaa980.
23. Uhlen M, Zhang C, Lee S, Sjostedt E, Fagerberg L, Bidkhori G, et al. A pathology atlas of the human cancer transcriptome. Science. 2017;357:eaan2507. doi:10.1126/science.aan2507.
24. Thul PJ, Akesson L, Wiking M, Mahdessian D, Geladaki A, Ait Blal H, et al. A subcellular map of the human proteome. Science. 2017;356:eaal3321. doi:10.1126/science.aal3321.
25. Bang YJ, Van Cutsem E, Feyereislova A, Chung HC, Shen L, Sawaki A, et al. Trastuzumab in combination with chemotherapy versus chemotherapy alone for treatment of HER2-positive advanced gastric or gastro-oesophageal junction cancer (ToGA): a phase 3, open-label, randomised controlled trial. Lancet. 2010;376:687-697. doi:10.1016/S0140-6736(10)61121-X.
26. Shah MA, Shitara K, Ajani JA, Bang YJ, Enzinger P, Ilson D, et al. Zolbetuximab plus mFOLFOX6 in patients with CLDN18.2-positive, HER2-negative, untreated, locally advanced unresectable or metastatic gastric or gastro-oesophageal junction adenocarcinoma (SPOTLIGHT): a multicentre, randomised, double-blind, phase 3 trial. Lancet. 2023;401:1655-1668. doi:10.1016/S0140-6736(23)00620-7.
27. Shitara K, Lordick F, Bang YJ, Enzinger P, Ilson D, Shah MA, et al. Zolbetuximab plus CAPOX in CLDN18.2-positive gastric or gastroesophageal junction adenocarcinoma: the randomized, phase 3 GLOW trial. Nat Med. 2023;29:2133-2141. doi:10.1038/s41591-023-02465-7.
28. Wainberg ZA, Enzinger PC, Kang YK, Qin S, Yamaguchi K, Kim IH, et al. Bemarituzumab in patients with FGFR2b-selected gastric or gastro-oesophageal junction adenocarcinoma (FIGHT): a randomised, double-blind, placebo-controlled, phase 2 study. Lancet Oncol. 2022;23:1430-1440. doi:10.1016/S1470-2045(22)00603-9.
29. Sandve GK, Nekrutenko A, Taylor J, Hovig E. Ten simple rules for reproducible computational research. PLoS Comput Biol. 2013;9:e1003285. doi:10.1371/journal.pcbi.1003285.
30. Wilkinson MD, Dumontier M, Aalbersberg IJ, Appleton G, Axton M, Baak A, et al. The FAIR Guiding Principles for scientific data management and stewardship. Sci Data. 2016;3:160018. doi:10.1038/sdata.2016.18.
31. Moek KL, de Groot DJA, de Vries EGE, Fehrmann RSN. The antibody-drug conjugate target landscape across a broad range of tumour types. Ann Oncol. 2017;28:3083-3091. doi:10.1093/annonc/mdx541.
32. Li G, Schnell D, Bhattacharjee A, Yarmarkovich M, Salomonis N. Quantifying tumor specificity using Bayesian probabilistic modeling for drug and immunotherapeutic target discovery. Cell Rep Methods. 2024;4:100900. doi:10.1016/j.crmeth.2024.100900.
33. Xu Y, Wei Z, Li M, Yang W, Chen Z, Shi R, et al. Identification and prioritization of high-frequency biomarkers and therapeutic targets in gastric cancer trials. BMC Cancer. 2025;26:148. doi:10.1186/s12885-025-15484-z.
34. Chang YH, Hong TC, Lin KT, Hsiao YJ, Hsu HE, Waniwan JT, et al. Integrative proteogenomics maps multifactorial aetiology, progression and therapeutic vulnerabilities in gastric cancer. Gut. 2026;75:886-904. doi:10.1136/gutjnl-2025-337247.
35. Zhang P, Tao C, Xie H, Yang L, Lu Y, Xi Y, et al. Identification of CD66c as a potential target in gastroesophageal junction cancer for antibody-drug conjugate development. Gastric Cancer. 2025;28:422-441. doi:10.1007/s10120-025-01584-z.
36. Zhao Y, Xie H, Tian X, Yuan L, Hu C, Dai Y, et al. Poliovirus receptor as a potential target in gastric signet-ring cell carcinoma for antibody-drug conjugate development. Cancers (Basel). 2026;18:270. doi:10.3390/cancers18020270.
37. Li W, Cheng M, Han H, Xu M, Luo Y, Bi F, et al. Antibody-drug conjugates in gastric cancer: clinical advances and resistance mechanisms. Gastric Cancer. 2026;29:300-320. doi:10.1007/s10120-025-01703-w.
38. Katoh M, Loriot Y, Nakayama I, Hamada A, Shitara K, Katoh M. Antibody-drug conjugates targeting the cadherin, claudin and nectin families of adhesion molecules. Front Mol Med. 2025;5:1661016. doi:10.3389/fmmed.2025.1661016.
39. Wang R, Fang P, Chen X, Ji J, Yu D, Mei F, et al. Overcoming multidrug resistance in gastrointestinal cancers with a CDH17-targeted ADC conjugated to a DNA topoisomerase inhibitor. Cell Rep Med. 2025;6:102213. doi:10.1016/j.xcrm.2025.102213.
