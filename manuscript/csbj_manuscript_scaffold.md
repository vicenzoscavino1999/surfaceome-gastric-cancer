# A reproducible framework for gastric cancer surface-target prioritization and GPI-anchor auditing

Draft status: scaffold started 2026-05-31. This is not a submission-ready manuscript.

Target journal: Computational and Structural Biotechnology Journal, Research Article.

## Abstract

Gastric adenocarcinoma remains a therapeutic challenge, and antibody-accessible surface proteins provide a tractable route for experimental target nomination. Computational prioritization, however, is sensitive to identifier mapping, RNA/protein discordance, normal-tissue expression, tumor microenvironment signal, isoform ambiguity, and surfaceome resource bias. We built a reproducible public-data pipeline integrating tumor/normal RNA sequencing, Human Protein Atlas protein/localization evidence, UniProt topology and lipidation annotations, curated surfaceome resources, benchmark controls, and stability analysis. The final ranking used six active quantitative evidence layers; single-cell specificity was not imputed, and a post-ranking TISCH2 check was used only for compartment caveats. The pipeline nominated six unordered Tier 1 hypotheses (`ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, and `EPCAM`) and twelve Tier 2 candidates. Scores showed moderate concordance with the Cancer Surfaceome Atlas final GESP baseline (Spearman rho=0.390, n=2,685) but low top20 identity. Sixteen of eighteen Tier 1/2 nominations overlapped a contemporary gastric proteogenomic surface-target atlas; this exceeded a simple Core+Probable random-draw null (p=0.0013) but not a surfaceome-evidence-matched null. These external checks support plausibility and benchmark consistency, not independent validation. A diagnostic audit quantified how incomplete routing of confirmed GPI-anchor evidence affects universe construction and ranking: the correction expanded the ranked universe from 2,650 to 2,704 genes, admitted 54 additional confirmed GPI-anchor genes, moved `CEACAM5` from rank 120 to 12 and `MSLN` from rank 453 to 158, and placed five confirmed GPI anchors in the active top 50. The result is a transparent, hypothesis-generating framework and an auditable GPI-anchor handling lesson.

## Keywords

gastric cancer; surfaceome; target prioritization; reproducibility; GPI-anchored proteins; proteogenomics

## 1. Introduction

### 1.1 Clinical and biological motivation

Gastric adenocarcinoma is molecularly heterogeneous and continues to have limited broadly effective targeted options [1,2]. Cell-surface proteins offer a tractable intervention space because they can support antibody-based therapeutics, antibody-drug conjugates (ADCs), cell therapies, receptor blockade, or imaging strategies [3-8]. Established and emerging gastric cancer targets, including ERBB2, CLDN18.2, FGFR2b, TACSTD2/TROP2, EPCAM, CEACAM5, MET, and MSLN, provide useful benchmarks but do not remove the need for systematic prioritization.

### 1.2 Why surface-target prioritization is hard

Surface-target prioritization is not equivalent to ranking genes by tumor RNA abundance. RNA expression does not establish protein presence, membrane localization, extracellular accessibility, or an acceptable normal-tissue profile. Bulk tumor RNA can also reflect tumor microenvironment (TME) compartments, including endothelial, immune, and stromal cells, rather than malignant epithelial cells. In addition, gene-level measurements do not resolve isoform-specific antigens. Surfaceome resources also differ in how they route non-transmembrane evidence, including glycosylphosphatidylinositol (GPI)-anchored proteins; prior in silico surfaceome work explicitly accounted for annotated GPI-linked proteins, so the open problem here is not whether GPI anchors can be surface evidence but how incomplete evidence routing propagates into an auditable candidate universe and ranking [5].

### 1.3 Contribution

Here, we developed a reproducible public-data pipeline for gastric cancer surface-target prioritization. The workflow quantifies the ranking impact of a GPI-anchor evidence-routing gap and implements a source-wide correction at universe construction before scoring. It also produces coarse Tier 1/2 nominations framed as experimentally testable hypotheses. The contribution is methods-forward: candidate lists are an applied output of a transparent evidence-integration framework rather than claims of clinical readiness.

## 2. Material and methods

### 2.1 Reproducibility design

The analysis was implemented as a staged reproducible workflow rather than as an exploratory notebook. Controls, exclusion criteria, dataset targets, scoring scenarios, random seeds, tissue mappings, and coarse tiering rules were recorded before candidate interpretation. Raw or downloaded inputs were checksum-registered where stored locally, and each major analysis stage produced both machine-readable tables and a short report. The repository preserves design decisions, analytical decisions, provenance records, a release manifest, and stage-specific validation checks.

Workflow integrity was assessed with three levels of checks. First, unit tests cover core scripts and stage-specific invariants. Second, a smoke test verifies expected outputs from data inventory through manuscript figure/table packaging, including manual curation artifacts. Third, Snakemake declares the workflow outputs and reports whether any declared artifact is missing or out of date. Some early bootstrap and data-inventory outputs were generated before all rules were formalized and therefore retain missing Snakemake provenance metadata; this limitation is documented and does not apply to the current figure/table package.

Intermediate ranking snapshots were retained rather than overwritten. The pre-fix snapshot preserves the ordinal surfaceome-confidence transform, the pre-GPI snapshot preserves the state before the GPI-anchor correction, and the final frozen ranking snapshot preserves the active ranking after the universe-wide GPI evidence correction and downstream rerun. This version history was kept to document bug detection and correction, not to select a favorable ranking retrospectively.

### 2.2 Datasets and identifier normalization

The main input sources are summarized in Table 1. TCGA-STAD and GTEx expression data were obtained through the UCSC Xena/Toil RNA-seq recompute and used as the primary tumor-normal RNA matrix [9,10]. GDC TCGA-STAD metadata and cBioPortal TCGA-STAD clinical and copy-number fields were used for clinical covariate availability, selected amplification context, and secondary sensitivity planning [11,12]. Human Protein Atlas (HPA) downloadable files supplied normal IHC, cancer IHC, subcellular localization, and tissue RNA context [13]. UniProtKB reviewed human records supplied protein identifiers, topology, transmembrane annotations, extracellular features, signal peptides, lipidation/GPI-anchor evidence, protein length, and isoform mappings [14]. TCSA, CSPA, SURFY, UniProt GO, UniProt topology/GPI fields, and HPA subcellular localization were integrated to construct the surfaceome universe [3-5].

Identifier normalization used HGNC-approved protein-coding genes as the primary denominator before surfaceome filtering. This choice prevents the candidate denominator from being inflated by noncoding or deprecated matrix rows while preserving alias, Ensembl, UniProt, and HPA mappings for evidence integration. Mapping failures and source coverage are retained as audit outputs rather than silently dropped.

### 2.3 Surfaceome universe construction

The surfaceome universe was defined at the HGNC gene level. Core/Probable membership required independent surface support plus an anchor, topology, or localization signal. Qualifying anchor evidence included UniProt extracellular topology, UniProt transmembrane annotation, confirmed UniProt lipidation `GPI-anchor`, HPA plasma membrane localization, or SURFY surfaceome support. Curated-list or GO-only genes lacking such support were retained as ambiguous surface-context genes rather than treated as high-confidence surface targets.

The final Core+Probable universe contains 2,704 genes: 2,646 Core and 58 Probable. Published-list overlap was used as a sanity check, with Jaccard overlap of 0.7749 for TCSA, 0.2889 for CSPA, and 0.8017 for SURFY. Negative controls did not enter Core/Probable, and positive/benchmark controls were present or documented.

Confirmed UniProt lipidation `GPI-anchor` evidence was credited as a non-experimental strong anchor signal at the universe construction stage. Specifically, confirmed GPI evidence contributed score +2, one support source, `has_anchor=true`, and `has_strong=true`. Subcellular-location-only GPI annotations were flagged but not credited as confirmed direct lipidation evidence. This correction was applied universe-wide before final ranking, not as a target-specific patch, and is best interpreted as an auditable evidence-routing correction rather than a new biological discovery.

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

The preregistered positive statistical rule required tumor versus GTEx stomach log2 fold-change >= 1 and BH-FDR < 0.05. The TCGA adjacent-normal comparison was reported as a sensitivity context rather than as a full replacement for GTEx stomach.

The off-tumor risk component `R` used the preregistered maximum weighted organ penalty. Critical organs and tissue classes were assigned weights, including heart and brain at 1.00, liver and kidney at 0.90, lung and endothelial contexts at 0.85, hematopoietic at 0.80, immune at 0.75, gastrointestinal epithelial at 0.70, and reproductive/other at 0.60. `R` is high-worse: higher values indicate greater on-target/off-tumor concern and are subtracted in the integrated score. Alternative `R_max_plus_breadth` and `R_sum_capped` forms were retained for sensitivity analysis.

### 2.6 Protein and localization evidence

Protein/localization evidence was computed from HPA stomach cancer IHC, HPA normal IHC, and HPA subcellular localization. In the 2,704-gene Core+Probable universe, HPA stomach cancer IHC covered 1,790 genes, HPA normal stomach and critical normal IHC covered 1,535 genes, and HPA subcellular localization covered 1,302 genes. Membrane or cell-junction localization support was present for 734 genes. CPTAC/PDC proteomics was not assessed in the primary analysis and was not imputed.

The `P` component combines tumor protein presence, membrane or cell-junction localization support, mapped normal protein safety support, HPA reliability support, and discordance penalties. The HPA bulk cancer file does not expose antibody IDs, staining intensity/quantity fields, patient-level membrane pattern, or multi-antibody concordance. These unavailable fields were not inferred and are marked for candidate-card review where relevant.

Discordance flags include HPA-missing stomach cancer IHC, high RNA but absent tumor protein, protein present without membrane/cell-junction support, and low-confidence HPA evidence. HPA absence does not automatically eliminate a candidate because the protein layer has incomplete coverage and antibody-level detail is unavailable in the bulk files.

### 2.7 Tumor microenvironment specificity

No processed gastric single-cell RNA-seq dataset was admitted into the numeric primary score. The optional `SC` component therefore remains `not_available` and has zero weight in the primary ranking.

As a preregistered fallback, bulk TCGA-STAD expression was used to flag possible TME-derived signal. Marker modules were computed for CAF/fibroblast, endothelial, myeloid/macrophage, T-cell, and B/plasma compartments. For each candidate gene, Spearman correlations were computed between candidate expression and each module score across 414 TCGA-STAD tumors. ESTIMATE stromal and immune signatures from `tidyestimate` were also computed from the same Xena/Toil matrix and used as relative purity/admixture covariates for partial Spearman correlations [15].

After the ranking and tiers were frozen, a limited candidate-level scRNA cross-check was added with processed TISCH2 gastric cancer datasets [16-18]. TISCH2 `STAD_GSE134520` provides average expression for 41,554 cells across 13 samples and includes a `Malignant cells` class, while `STAD_GSE167297` provides average expression for 22,464 cells across 14 diffuse-type gastric cancer samples but no TISCH2 malignant-cell class. These data were used only to annotate the 18 Tier 1/2 candidates as malignant-cell supported, mixed, non-malignant dominant, or context-only. They did not alter `SC`, the integrated score, or tier assignments.

These outputs are flags only. They are not hard ranking filters and are not interpreted as absolute pathology purity estimates. ESTIMATE and the TME marker modules both represent stromal/immune biology, so their partial correlations are biologically collinear rather than clean causal decomposition. A `high_purity_adjusted_tme_correlation` flag therefore triggers conservative review with protein/localization and cell-resolved evidence where available.

### 2.8 Topology, extracellular accessibility, and isoforms

Topology and extracellular accessibility were computed from reviewed UniProt human feature fields for all 2,704 Core+Probable genes. Parsed fields included protein length, topological domains, transmembrane segments, signal peptides, lipid/GPI anchor features, glycosylation, disulfide bonds, chains/domains, subcellular location, PTM comments, and Ensembl isoform mappings.

Each protein was assigned an accessibility class from A to E. Classes A/B indicate clear or inferred extracellular regions suitable for antibody-accessibility review. Class C indicates possible but less straightforward access, often for multipass proteins or shorter extracellular loops. Classes D/E are not automatic exclusions from the universe but block Tier 1 antibody-targeting claims unless later structure, literature, or candidate-card evidence supports an exception.

The topology component `T` combines accessibility class, extracellular length, topology confidence, and isoform confidence, then subtracts conservative cleavage/shedding and soluble-decoy penalties. These penalties are candidate-card flags, not hard exclusions. GPI-anchor features are explicitly captured in this layer; MSLN is the benchmark example where GPI anchoring supports membrane accessibility despite absence of a classical transmembrane segment.

Isoform-specific benchmarks were handled conservatively. `CLDN18` and `FGFR2` remain gene-level in the current expression layers, so `CLDN18.2` and `FGFR2b/IIIb` claims are marked `isoform_unresolved` and are not used as evidence that the pipeline resolves isoform-specific expression.

### 2.9 Integrated scoring and sensitivity

The integrated score used the preregistered components listed in Table 2. The primary preregistered scenario used weights `Surf=0.15`, `E=0.20`, `N=0.20`, `R=0.20`, `P=0.15`, `SC=0.00`, and `T=0.10`. `SC` remained unavailable and was not imputed. Sensitivity scenarios included safety-prioritized, ADC-focused, novelty-focused, and protein-evidence-focused weighting; these were reported as sensitivity contexts, not alternative primary rankings.

`Surf` is the relative surfaceome confidence within the admitted Core+Probable universe. After the GPI correction, it is scaled as:

`Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`

over the theoretical admitted confidence range [5,10], not over the observed min/max of the current dataset. This means that zero indicates the lowest admitted confidence level, not absence from the surfaceome universe.

For score computation, missing principal components were handled with exclude-and-renormalize: the weighted score was computed over available nonzero-weight components and divided by the available absolute weight sum. Missingness was then carried into tiering restrictions and sensitivity analyses rather than mean-imputed. `R` is the only high-worse primary component and is subtracted from the total score.

The stability analysis evaluated weight perturbation, leave-one-layer-out sensitivity, missing-data sensitivity, risk-threshold sensitivity, organ-weight perturbation, scenario stability, and post-scoring rank resolution. These analyses supported coarse tier language but not fine intra-tier ordering.

### 2.10 Tiering and manual curation

Tiering was performed only after stability analysis. The original fine tiering plan was collapsed to unordered coarse categories because post-scoring rank resolution supported coarse interpretation but not fine rank distinctions. The tiering rule file was frozen before candidate assignment. Tier 1 required stability, no unexplained critical normal risk, no unsupported TME-marker status, acceptable accessibility class, protein evidence or documented absence, no more than two missing primary components, and absence of single-layer dependence. Tier 2 captured candidates failing one Tier 1 criterion or showing scenario/subtype dependence. Watchlist captured candidates with major missingness, TME-marker behavior, unresolved benchmark isoforms, or other non-nominable but biologically relevant signals.

Manual curation informed tiers and caveats but did not change scores. The top 30 candidates were reviewed against UniProt, HPA, literature, clinical/druggability context, Wang 2026 concordance, and analysis-stage flags. Candidate notes explicitly record whether curation changed the score; all current entries preserve `changes_score=no`.

External baseline behavior was assessed in two ways. First, final scores were compared with the Cancer Surfaceome Atlas final and core GESP scores [3] over overlapping genes by Spearman correlation and top-k overlap. This is a pan-cancer surfaceome-prioritization baseline, not a gastric-specific validation label. Second, external consistency was assessed against Wang 2026 gastric proteogenomic surface-target resources [19]. Two null models were retained for the Wang comparison. The first was a one-sided hypergeometric test against random draws from the frozen Core+Probable surfaceome universe. The second was a deterministic matched-null sensitivity analysis with 20,000 permutations and seed 20260531, sampling nearest-neighbor Core+Probable controls matched on surfaceome confidence, tumor expression percentile, protein-evidence percentile and missingness, topology percentile, available component count, and accessibility class. This cross-check is used as benchmark concordance and compartment-framework support, not as proof of clinical validity or as per-gene single-cell validation for genes absent from the Wang Figure 7H panel.

## 3. Results

### 3.1 Dataset coverage and reproducible workflow

The workflow integrates public transcriptomic, protein, localization, topology, and curated surfaceome resources into a staged candidate-prioritization pipeline (Fig. 1; Table 1). The current execution covers dataset inventory, raw/source checksum capture, batch diagnostics, identifier normalization, surfaceome universe construction, tumor expression, normal selectivity and off-tumor risk, HPA protein/localization evidence, TME specificity flags, topology/isoform annotation, integrated scoring, stability analysis, coarse tiering, external baseline comparison, candidate-level scRNA compartment annotation, and manuscript figure/table packaging.

All current smoke-test checks through the figure/table package pass, and the manuscript brief check passes. Unit tests pass for the implemented analysis utilities. Snakemake dry-run reports that all declared workflow targets are present and up to date. The remaining Snakemake metadata warnings are limited to bootstrap and early data-inventory rules that were first generated before complete workflow formalization; the later manuscript-package outputs are tracked as workflow outputs.

### 3.2 Surfaceome universe and GPI-anchor diagnostic

The final surfaceome universe contains 2,704 Core+Probable genes, comprising 2,646 Core and 58 Probable candidates (Fig. 2). The construction rule balanced published surfaceome support with direct anchor, topology, or localization evidence. This conservative rule excluded all intracellular/secreted negative controls from Core+Probable while retaining benchmark surface-target genes for downstream scoring.

During scoring diagnostics, confirmed GPI-anchored candidates exposed a source-integration problem. Treating GPI evidence only as a downstream topology note under-credited confirmed GPI-anchored surface proteins at the surfaceome universe layer. This is not a claim that GPI-linked proteins were absent from prior surfaceome resources: SURFY explicitly incorporated annotated GPI-linked proteins in its in silico surfaceome construction [5]. The contribution here is to quantify how incomplete routing of confirmed GPI evidence affects a gastric cancer prioritization workflow and to correct that routing before final scoring. Because confirmed lipidation evidence can affect both membership and confidence, the correction was applied universe-wide during surfaceome-universe construction before rerunning downstream analyses. Confirmed UniProt lipidation `GPI-anchor` evidence was credited as non-experimental strong anchor evidence; subcellular-location-only GPI annotations were flagged but not credited as direct lipidation evidence.

After correction, the active final ranking uses the fixed theoretical `Surf_relative_confidence` scale over the admitted confidence range [5,10]. This means that low `Surf` values represent lower relative confidence within an admitted surfaceome universe, not absence from the surfaceome. The GPI finding is therefore interpreted as a transferable under-crediting issue in resource integration, not as evidence that all GPI-anchored proteins are strong therapeutic candidates.

The impact of the correction was quantified against the preserved pre-GPI snapshot. The ranked universe increased from 2,650 to 2,704 genes; all 54 newly ranked genes were confirmed UniProt GPI-anchor genes. Confirmed GPI anchors increased from 65 to 119 ranked genes. None were in the pre-GPI top 50, whereas five confirmed GPI anchors entered the final top 50 (`BST2`, `CEACAM5`, `ALPG`, `ULBP2`, and `NT5E`), with zero classified as suspicious Surf-dominant entrants by the pre-stability audit. Among common GPI genes, the median rank improvement was 453 positions. The correction also changed benchmark behavior: `CEACAM5` moved from rank 120 to 12, and `MSLN` moved from rank 453 to 158. Because tiering was performed after the correction, no pre/post tier-change claim is made; instead, the current Tier 1/2 set contains three confirmed GPI candidates (`CEACAM5`, `BST2`, and `ALPG`).

### 3.3 Tumor expression, normal selectivity, and risk landscape

Tumor expression was measured for 2,696 of 2,704 Core+Probable genes. The `E` component captured both expression magnitude and prevalence in TCGA-STAD primary tumors. The normal selectivity component `N` combined tumor versus GTEx stomach contrast, tumor versus mapped critical-normal contrast, and a preregistered statistical rule. Under the GTEx stomach statistical selectivity rule, 757 genes met `log2FC >= 1` and BH-FDR < 0.05.

The off-tumor risk component `R` provided an opposing high-worse layer (Fig. 3). In the current conservative maximum-risk model, 1,825 Core+Probable genes had high critical off-tumor risk. This high count is expected because many cell-surface proteins are shared across normal epithelial, endothelial, hematopoietic, immune, or organ-specific compartments. `E`, `N`, and `R` therefore need to be interpreted together: tumor abundance without normal-context review can over-rank broadly expressed targets, while a high normal-risk flag does not automatically exclude gastric-lineage or clinically benchmarked antigens.

### 3.4 Integrated evidence across candidates

The primary frozen ranking was converted into coarse tiers only after stability analysis and manual curation (Fig. 4; Table 3). Tier 1 contains six unordered surface-target hypotheses: `ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, and `EPCAM`. Tier 2 contains twelve additional candidates: `MPZL1`, `ITGB5`, `BST2`, `IFNGR1`, `ALPG`, `DSC2`, `TNFRSF11A`, `ERBB2`, `CD9`, `LSR`, `CDH17`, and `TGFBR1`.

The Tier 1 set is intentionally not presented as a fine rank order. Its members combine high tumor expression/selectivity, protein/localization support, and accessible topology, but each carries interpretation caveats. For example, `ITGB4` has basal/stratified epithelial expression not fully captured by the organ-risk model, `NECTIN2` has a purity-adjusted myeloid/DC signal below the frozen high-TME threshold, `CEACAM5` and `EPCAM` retain normal epithelial expression concerns, and `JAG1` has dual epithelial/endothelial biology. These caveats are part of the prioritization output rather than post-hoc exclusions.

Tier 2 captures candidates with strong but less stable or more caveated evidence. `ERBB2`, an established HER2 benchmark, remains Tier 2 because its primary-scenario top-20 stability frequency (0.34) does not meet the preregistered Tier 1 stability threshold of 0.40, although it is robustly recovered within the top 50. `CDH17` is likewise retained as Tier 2: its external clinical and biological relevance is noted, but the bulk ranking and stability criteria do not support Tier 1 placement in this pipeline.

### 3.5 TME specificity and compartment caveats

Because no processed gastric single-cell matrix was admitted into the primary score, compartment specificity was handled through flags rather than a numeric `SC` layer (Fig. 5; Table 5). The TME fallback identified known immune, endothelial, and stromal markers as high-risk cases for epithelial tumor-target interpretation. `PECAM1` remained high in the bulk ranking but was assigned to Watchlist by the preregistered TME rule after curation confirmed vascular/endothelial rather than tumor-epithelial staining. `LRRC15` was also assigned to Watchlist because curation supported a CAF/stromal interpretation rather than a primary malignant-epithelial target claim.

The same compartment discipline applies to immune genes and thin-evidence high-rank artifacts. HLA and KIR genes with missing primary expression/protein/risk components were Watchlist by the missing-data rule, not by subjective demotion. `HLA-DPB1`, `IL2RG`, and related immune-context candidates are retained as biologically relevant but not nominated as epithelial tumor-cell surface targets.

The candidate-level TISCH2 cross-check strengthened, but did not eliminate, these caveats. In `STAD_GSE134520`, all 18 Tier 1/2 genes were present, 8 were malignant-class supported, 1 had mixed malignant and non-malignant signal, 7 had low malignant signal in that early-cancer/premalignant dataset, and 2 were non-malignant dominant. `NECTIN2`, `JAG1`, `MPZL1`, `ITGB5`, `BST2`, `IFNGR1`, `CD9`, and `TGFBR1` were malignant-class supported; `ITGB4` was mixed; `CDH3`, `CEACAM5`, `ALPG`, `DSC2`, `TNFRSF11A`, `ERBB2`, and `CDH17` had low malignant-class signal; and `EPCAM` and `LSR` were non-malignant dominant in that dataset. In `STAD_GSE167297`, TISCH2 provided epithelial/TME context only because no malignant-cell class was present. These results are candidate annotations, not score components.

These single-cell calls are not symmetric evidence for or against tier placement. `STAD_GSE134520` contains only 880 malignant-class cells and was designed around premalignant lesions and early gastric cancer. For the established epithelial benchmarks `EPCAM` and `CEACAM5`, discordance is treated as a dataset-scope warning rather than a reason to override the frozen multi-layer evidence. For `CDH3`, the low malignant-class signal explicitly lowers confidence in tumor-cell attribution: it remains Tier 1 under the frozen bulk-expression, protein/localization, topology, and stability rules, but tumor-cell membrane confirmation is required before experimental prioritization. `ALPG` is more strongly caveated: its low signal reinforces its existing Tier 2 placement and single-layer-dependence warning rather than supporting promotion.

Two Tier 1 genes carry compartment-specific caveats rather than demotion. `NECTIN2` remains Tier 1 because the frozen high-TME threshold was not met, HPA curation supports membranous epithelial expression, and the limited TISCH2 check provides malignant-class support in `STAD_GSE134520`; it remains the Tier 1 member closest to the compartment threshold. `JAG1` remains Tier 1 because it has surface-accessibility and tumor-epithelial evidence, but its endothelial/angiocrine biology makes it the most compartment-exposed Tier 1 member.

### 3.6 Stability, controls, and external consistency

Stability analysis supported coarse candidate interpretation but not fine within-tier ordering (Fig. 6a-b). Weight perturbations were generally stable: 231 of 250 perturbations passed both preregistered gates, with minimum and median Spearman correlations of 0.910703 and 0.983898 relative to the final ranking. However, leave-one-layer-out analyses showed important layer dependence, especially for `T`, `R`, and `E`, and post-scoring rank resolution found only 1 of 20 baseline top20 genes with a 95% rank interval contained within the top 40. These results justify coarse tiers rather than fine rank claims.

Control behavior was used as a diagnostic rather than for weight tuning (Fig. 7; Table 4). Positive-control top50 recovery remained imperfect at 4 of 8 (`ERBB2`, `EPCAM`, `MET`, and `CEACAM5`). The aggregate preregistered top50 gate therefore remains reported as failed. A component-level causal review showed that the original misses were explained by expected biology or design limits rather than residual pipeline-accusing failures: `CLDN18` and `FGFR2` are isoform unresolved at gene level, `MSLN` retains a topology/shedding penalty despite high protein support and corrected GPI evidence, and `TACSTD2` has intermediate surface confidence and weaker protein support. Negative intracellular controls were excluded from Core/Probable; `PTPRC` was cleanly low-ranked for epithelial targeting; `PECAM1` remained the documented vascular/TME exception and was handled by Watchlist tiering.

Against the TCSA final GESP baseline, final scores showed moderate concordance across 2,685 overlapping genes (Spearman rho=0.389861, p=3.5e-98), with low top20 identity (1/20: `NECTIN2`) and 6 of 18 Tier 1/2 genes in the TCSA final-score top100. The TCSA core GESP baseline gave similar moderate concordance (rho=0.329466, p=5.3e-69), 2/20 top20 overlap (`ERBB2` and `ITGB4`), and 8 of 18 Tier 1/2 genes in the baseline top100. This supports external surfaceome consistency while showing that the final ranking is not a clone of a pan-cancer surfaceome score.

External consistency was also assessed against Wang 2026. Sixteen of eighteen Tier 1/2 nominations were present in Wang's drug-target table, including all six Tier 1 genes. Against the 2,704-gene Core+Probable universe, 1,423 genes overlapped the Wang drug-target table; random sampling of 18 Core+Probable genes would therefore be expected to recover 9.47 Wang genes, whereas the observed overlap was 16 (one-sided hypergeometric p=0.0013; odds ratio 7.27). A stricter Wang membrane-protein subset gave 13 of 18 observed versus 5.79 expected (p=5.6e-4). However, a matched-null sensitivity analysis showed that the observed Wang overlap was not above matched expectation after controlling for surfaceome confidence, expression, protein-evidence availability, topology, component completeness, and accessibility class. For the all-table background, the matched-null mean overlap was 15.18 of 18 (upper-tail p=0.436); for the Wang membrane-protein flag, the matched-null mean was 13.99 of 18 (p=0.817). Taken together, the external checks support plausibility and benchmark consistency, but not independent validation of the ranking or of any individual nomination. The two absent Tier 2 genes, `CD9` and `LSR`, remain divergent nominations. Wang also provided selective glyco-outlier support for `CEACAM5`, `CDH17`, `EPCAM`, `ITGB5`, and `DSC2`. Figure 7H from Wang provided compartment-framework support: plotted genes confirmed `EPCAM` as epithelial, `HLA-DPB1` as immune, and `CD47` as broad, while fibroblast and immune target blocks supported the PECAM1/LRRC15/HLA compartment-caveat framework. Most specific nominees, including `NECTIN2`, `PECAM1`, `LRRC15`, `CDH3`, `CDH17`, and `CEACAM5`, were not in Wang's curated Figure 7H panel and therefore are not individually resolved by that figure.

### 3.7 Candidate interpretation

The candidate panel summarizes the final applied output of the pipeline (Fig. 8; Tables 3 and 5). The Tier 1 set should be read as a compact, experimentally testable hypothesis set rather than as a list of proven therapeutic targets. `CDH3` is the cleanest Tier 1 example of a non-benchmark nomination, with P-cadherin biology and ADC-development precedent in curation. Its limited TISCH2 result lowers confidence in malignant-cell attribution and makes tumor-cell membrane confirmation mandatory before experimental prioritization. `ITGB4`, `NECTIN2`, and `JAG1` are Wang-concordant membrane-class nominations with distinct compartment or normal-tissue caveats. `CEACAM5` and `EPCAM` are established surface-antigen benchmarks with stronger external concordance but persistent normal epithelial expression concerns.

Tier 2 expands the hypothesis space and preserves informative edge cases. Some Tier 2 genes are biologically attractive but fail one frozen criterion (`ALPG`, `CDH17`); for `ALPG`, low TISCH2 malignant-class signal reinforces the existing single-layer-dependence caution. Some are broad or compartment-exposed (`MPZL1`, `ITGB5`, `IFNGR1`, `TGFBR1`), and some are divergent from Wang or topologically constrained (`CD9`, `LSR`). Watchlist genes are not discarded; they document why bulk surfaceome prioritization can over-rank immune, stromal, endothelial, ubiquitous, or thin-evidence candidates when cell-resolved data are unavailable.

## 4. Discussion

### 4.1 What the pipeline adds

This study presents a reproducible public-data workflow for prioritizing gastric cancer surface-target hypotheses while preserving the uncertainty that usually gets compressed into a single ranked list. The pipeline integrates surfaceome membership, tumor expression, tumor-normal selectivity, normal-tissue risk, protein/localization evidence, and topology/accessibility, while keeping single-cell specificity unavailable rather than imputed. Its main contribution is not a claim that any individual candidate is ready for translation, but a transparent method for combining heterogeneous evidence layers and showing where that evidence is strong, weak, or confounded. This positioning is deliberately narrower than pan-cancer target-discovery frameworks and general multi-omics prioritization platforms [6-8,20].

The TCSA and Wang comparisons address different external-reference questions. TCSA provides a pan-cancer surfaceome-score baseline: the moderate rank correlation and low top20 identity show that the workflow is aligned with established surfaceome evidence but not reducible to it. Wang 2026 is best interpreted as a gastric-specific consistency check rather than an independent validation claim. The overlap with Wang exceeds a simple random draw but not a matched null, which matters because both resources enrich for highly expressed and well-annotated surface proteins. Taken together, the external checks support plausibility and benchmark consistency, but not independent validation of the ranking or any individual nomination. CD9 and LSR remain divergent nominations, glyco-outlier corroboration is selective, and the curated Wang Figure 7H single-cell panel does not directly plot most of the specific nominees.

The workflow also makes uncertainty visible. ERBB2 remaining Tier 2 rather than being forced into Tier 1 shows that benchmark recovery was not used to override frozen stability rules. PECAM1 and LRRC15 moving to Watchlist shows that bulk RNA surfaceome ranking can produce compartment-derived false positives when cell-resolved data are unavailable. CLDN18 and FGFR2 remaining isoform unresolved shows that gene-level expression is insufficient for isoform-specific claims. These are not failures to be hidden; they are the evidence boundaries that make the prioritization interpretable.

### 4.2 Transferable GPI-anchor lesson

The GPI-anchor audit is the most transferable methods insight from this work. Confirmed GPI-anchored proteins are biologically membrane-associated and can be relevant to antibody-accessible targeting, and prior surfaceome work already recognized this class explicitly [5]. The issue quantified here is narrower: when a local integration workflow gives direct topology/list overlap more routing weight than confirmed lipidation evidence, GPI-anchored candidates can be under-credited at universe construction and ranking.

The key point is where the correction was applied. A downstream score-only patch would have benefited already admitted GPI genes while leaving potential GPI-supported candidates outside the universe. The final rule instead credited confirmed UniProt lipidation `GPI-anchor` evidence across the full universe construction step. This keeps the correction source-wide and auditable. It does not imply that GPI anchoring alone makes a good target; it means that confirmed GPI evidence should be handled as direct surface-anchor evidence when defining a surfaceome candidate universe.

The effect was not limited to a single benchmark rescue. The correction admitted 54 additional confirmed GPI-anchor genes into the ranked universe, increased confirmed GPI representation from 65 to 119 ranked genes, created five confirmed GPI top50 entries, and shifted `CEACAM5`, `MSLN`, `ALPG`, `ULBP2`, and `NT5E` upward by 108, 295, 130, 164, and 204 rank positions, respectively. These numbers are the reason the GPI finding is framed as quantification and correction of an evidence-routing issue rather than a claim of first discovery.

### 4.3 Candidate implications

The Tier 1 group contains a mixture of benchmark-like and less-established hypotheses. CEACAM5 and EPCAM are established surface-antigen benchmarks with strong external concordance, but both carry normal epithelial expression caveats. CDH3 is highlighted because it combines P-cadherin biology, strong component evidence, low TME concern in the primary analysis, and ADC-development precedent. Its low malignant-class signal in the limited TISCH2 check lowers confidence in tumor-cell attribution and makes tumor-cell membrane confirmation mandatory before experimental prioritization or any translational claim. NECTIN2, ITGB4, and JAG1 make the applied candidate output more interesting than simple benchmark recovery, but their interpretation remains candidate-specific: ITGB4 has basal/skin epithelial risk that may be under-weighted by the current organ model, NECTIN2 needs cell-resolved review of the myeloid/DC signal, and JAG1 requires separation of tumor-epithelial from endothelial/angiocrine expression.

Tier 2 provides additional hypotheses and boundary cases. ERBB2 and CDH17 demonstrate that established or clinically active biology does not automatically become Tier 1 under frozen stability rules. ALPG is biologically attractive but currently single-layer dependent; its low TISCH2 malignant-class signal reinforces Tier 2 caution. CD9 and LSR are divergent from Wang and require stronger independent support before they can be treated as robust nominations. MPZL1, ITGB5, IFNGR1, and TGFBR1 illustrate how high expression and surface accessibility can coexist with TME, normal-expression, or broad-signaling concerns.

The Watchlist is also informative. It captures candidates that a naive score could over-promote: immune HLA/KIR genes with thin evidence, endothelial PECAM1, CAF/stromal LRRC15, immune IL2RG/HLA-DPB1/BTN3A3, and ubiquitous or toxicity-prone CD47. Keeping these cases visible helps reviewers and future users see where the pipeline is cautious rather than silently discarding inconvenient outputs.

### 4.4 Limitations

Several limitations are central to interpretation. First, the expression layers are based on bulk RNA rather than isolated malignant epithelial cells. Bulk signal can reflect tumor cells, stromal cells, immune cells, endothelial cells, or mixtures of these compartments. Bulk TME correlations, ESTIMATE-adjusted partial correlations, and the limited TISCH2 candidate-level check provide conservative review flags, but they do not replace single-cell or spatial validation.

Second, tumor-normal selectivity is constrained by source and sample-size limitations. TCGA-STAD primary tumors and GTEx stomach normals were processed through the Xena/Toil recompute, but TCGA/GTEx source effects remain explicit. TCGA adjacent normal samples provide a source-matched sensitivity context but are lower-powered than GTEx stomach. The risk model is intentionally conservative, yet some normal compartments such as skin/basal epithelium are incompletely represented and must be revisited in candidate-specific review.

Third, HPA bulk IHC provides useful protein and localization evidence but lacks antibody-level and patient-level membrane detail in the downloadable cancer file. A candidate with HPA tumor staining and subcellular membrane support still requires antibody-specific review, tumor-cell membrane quantification, and normal-tissue cross-reactivity assessment before experimental prioritization.

Fourth, the primary score did not admit a processed gastric scRNA dataset. `SC` is therefore unavailable rather than imputed. The limited TISCH2 analysis annotates compartment caveats for the 18 Tier 1/2 candidates, but it does not solve cell-of-origin for the full ranked universe, does not provide patient-level malignant-cell prevalence for every candidate, and does not alter scores or tiers. Only `STAD_GSE134520` contributes a TISCH2 malignant-cell class, and it contains 880 malignant-class cells from a premalignant/early-cancer study; `STAD_GSE167297` is context-only. The current single-cell check is therefore deliberately limited and cannot be treated as a multi-cohort malignant-cell validation layer. This is especially important for CDH3, ALPG, NECTIN2, JAG1, PECAM1, LRRC15, HLA/immune genes, and other compartment-exposed candidates.

Fifth, gene-level expression cannot resolve isoform-specific targets. CLDN18.2 and FGFR2b remain explicitly `isoform_unresolved`; their positions in the ranking cannot be used as evidence that the pipeline resolves isoform-specific abundance. Similarly, topology/accessibility annotations do not establish antigen density, epitope exposure in native tumor tissue, internalization, shedding behavior, or therapeutic index.

Finally, this is a computational, hypothesis-generating study without wet-lab validation. Wang 2026 consistency checks and HPA/UniProt support strengthen candidate context, but they do not establish clinical efficacy or safety for any nominated target.

Sex-stratified and gender-related analyses were outside the scope of the current analysis. These dimensions should be assessed where relevant in future candidate-specific validation and translational study design.

### 4.5 Experimental follow-up

The highest-priority follow-up is experimental confirmation of tumor-cell surface abundance. Flow cytometry, cell-surface capture proteomics, or orthogonal surface-enrichment methods should be applied to gastric cancer cell models, organoids, and patient-derived samples. Tumor and normal tissue IHC should be repeated with validated antibodies and scored for membrane pattern, tumor-cell specificity, and normal compartment expression.

Compartment resolution is especially important for the most exposed candidates. NECTIN2 should be evaluated in cell-resolved data to distinguish tumor-epithelial expression from dendritic/myeloid checkpoint-ligand biology. JAG1 requires separation of tumor epithelial and endothelial/vascular expression. PECAM1 and LRRC15 provide useful negative examples for epithelial targeting but may be relevant to vascular or stromal strategies if framed as different modalities.

Modality-specific assays should follow confirmation of tumor-cell surface abundance. ADC-relevant candidates require internalization and payload-sensitivity testing. CAR or bispecific candidates require antigen-density and normal cross-reactivity assessment. GPI-anchored candidates require attention to shedding, soluble isoforms, and surface-retention behavior. The output of this pipeline is therefore a prioritized experimental queue, not a substitute for target validation.

## 5. Conclusions

We developed a reproducible public-data pipeline for gastric cancer surface-target prioritization and used it to generate coarse, caveat-aware candidate tiers from the final frozen ranking. The workflow integrates surfaceome confidence, tumor expression, normal selectivity, off-tumor risk, protein/localization evidence, topology/accessibility, stability analysis, and manual curation while keeping single-cell specificity unavailable rather than imputed.

The resulting Tier 1 and Tier 2 sets show moderate concordance with an external pan-cancer surfaceome-score baseline and are consistent with a contemporary gastric proteogenomic surface-target atlas, but the gastric-atlas agreement is not enriched beyond a surfaceome-evidence-matched null and should not be read as independent validation. The pipeline exposes important uncertainty: TME compartments can drive bulk surfaceome signals, limited TISCH2 cross-checks can flag but not resolve compartment origin, isoform-specific targets remain unresolved from gene-level data, HPA bulk IHC has antibody-detail limits, and coarse tiers are more defensible than fine rank claims.

The most transferable methodological finding is that confirmed GPI-anchored proteins can be under-credited unless lipidation evidence is routed into surfaceome universe construction. Correcting this issue before final scoring strengthened the reproducibility and interpretability of the prioritization. The nominated candidates should now be treated as experimentally testable hypotheses for gastric cancer surface-target follow-up.

## Figure captions

**Figure 1. Reproducible public-data workflow for gastric cancer surface-target prioritization.** The workflow begins with frozen public inputs, identifier normalization, and construction of a Core+Probable surfaceome universe, then computes tumor expression (`E`), normal selectivity (`N`), high-worse off-tumor risk (`R`), HPA protein/localization evidence (`P`), topology/accessibility (`T`), TME flags, stability checks, and coarse tiering. The figure reports stage-level counts and separates quantitative evidence layers from review flags and downstream hypothesis generation.

**Figure 2. Surfaceome evidence landscape and GPI-anchor correction.** Source overlap and confidence summaries show how curated surfaceome resources, UniProt topology/GPI evidence, HPA localization, GO annotations, and SURFY support contribute to the 2,704-gene Core+Probable universe. Confirmed UniProt lipidation `GPI-anchor` evidence is credited as a source-wide non-experimental strong anchor during universe construction. Low `Surf` values in the final ranking indicate lower relative confidence within the admitted universe, not absence from the surfaceome.

**Figure 3. Tumor-normal selectivity and off-tumor risk landscape.** Candidate genes are positioned by TCGA-STAD tumor expression, stomach and critical-normal selectivity, and conservative organ-risk context. `R` is a high-worse component and is subtracted in the integrated score. The display illustrates why tumor abundance, normal selectivity, and off-tumor risk must be interpreted jointly rather than as independent target-readiness claims.

**Figure 4. Multi-layer evidence heatmap for the top 30 ranked candidates.** The heatmap summarizes `Surf`, `E`, `N`, `R`, `P`, `T`, missingness, TME flags, topology/accessibility, and coarse tiers for the top-ranked candidates from the final frozen ranking. Tiers are unordered within Tier 1, Tier 2, and Watchlist. Watchlist entries document immune, stromal, endothelial, ubiquitous, or thin-evidence cases that would be overinterpreted by a score-only view.

**Figure 5. Tumor microenvironment specificity fallback.** Bulk TCGA-STAD marker-module and ESTIMATE-adjusted partial-correlation outputs flag likely CAF/fibroblast, endothelial, myeloid/macrophage, T-cell, and B/plasma compartment signals among top candidates. These outputs are flags only and do not replace cell-resolved single-cell or spatial validation. `SC` remains `not_available` and is not imputed in the primary score.

**Figure 6. Rank stability and weighting sensitivity.** (a) Rank-stability heatmap from weight perturbation, leave-one-layer-out, missing-data, risk-form, organ-weight, and post-scoring resolution analyses. (b) Weighting-sensitivity bumpchart comparing the primary preregistered ranking with safety-prioritized, ADC-focused, novelty-focused, protein-evidence-focused, and robust-aggregate contexts. Stability supports coarse tiers and explicit caveats, but not fine within-tier ordering.

**Figure 7. Benchmark-control behavior.** Positive, secondary, negative, and TME/off-tumor controls are shown as diagnostics of pipeline behavior rather than as tuning targets. Positive-control top50 recovery is reported as imperfect, isoform-specific benchmarks remain unresolved where expression is gene-level, intracellular negative controls are excluded from Core+Probable, and `PECAM1` is retained as the documented vascular/TME exception handled by Watchlist tiering.

**Figure 8. Tier 1 candidate panel.** The six unordered Tier 1 hypotheses are `ITGB4`, `CDH3`, `NECTIN2`, `CEACAM5`, `JAG1`, and `EPCAM`. The panel summarizes component evidence, Wang 2026 concordance, and candidate-specific caveats. These nominations are experimentally testable hypotheses and do not imply clinical efficacy, clinical safety, antigen density, internalization, or wet-lab validation.

## Table captions

**Table 1. Public datasets, versions, uses, and limitations.** Primary and secondary sources used for the workflow, including Xena/Toil TCGA-STAD/GTEx RNA, GDC and cBioPortal metadata, HPA IHC/localization/RNA files, UniProt reviewed-human topology/GPI features, curated surfaceome resources, TISCH2 candidate-level scRNA context, and optional resources not admitted into the numeric primary score. The table records source versions, checksum manifests where applicable, and interpretation limits.

**Table 2. Score components and primary weights.** Definitions, directions, weights, primary sources, normalization conventions, and principal limitations for `Surf`, `E`, `N`, `R`, `P`, `SC`, and `T`. `R` is high-worse and subtracted; `SC` remains unavailable with zero weight; missing components are handled by exclude-and-renormalize during scoring and by tier restrictions during interpretation.

**Table 3. Tier 1 and Tier 2 candidates.** Coarse unordered Tier 1 and Tier 2 nominations from the final frozen ranking, stability outputs, and manual curation. Columns report rank, score, prevalence flag, stability frequency, component values, Wang 2026 class/glyco-outlier context, and the principal caveat. The table is a hypothesis list, not a clinical target list.

**Table 4. Benchmark-control diagnostics.** Positive controls, secondary benchmarks, intracellular negative controls, and TME/off-tumor controls used to assess whether the pipeline behaves plausibly. Control behavior is reported honestly, including the failed aggregate positive-control top50 gate and the cause-level interpretation of misses. Controls were not used to retune weights or rescue individual candidates.

**Table 5. Candidate flags and interpretation guardrails for the top 30.** Automatic audit flags, TME risk, normal-risk interpretation, maximum-risk organ, accessibility class, HPA status, discordance flags, missing primary components, isoform-resolution status, and candidate-specific caveats. These flags define the review burden before any experimental prioritization.

## Supplementary information captions

**Supplementary Table S1. Full surfaceome universe.** Complete Core, Probable, Ambiguous, and excluded surfaceome evidence table used to define the candidate universe.

**Supplementary Table S2. All component scores.** Universe-wide component scores, missingness indicators, and integrated primary-score inputs for all Core+Probable genes.

**Supplementary Table S3. Scenario rankings.** Preregistered primary, safety-prioritized, ADC-focused, novelty-focused, protein-evidence-focused, and robust-aggregate ranking outputs.

**Supplementary Table S4. Complete stability and sensitivity outputs.** Rank stability, perturbation, leave-one-layer-out, missing-data, risk-threshold, organ-weight, and post-scoring resolution outputs.

**Supplementary Table S5. Tissue mapping.** Organ and tissue mappings used to aggregate normal expression and off-tumor risk contexts.

**Supplementary Table S6. Manual curation notes.** Frozen candidate-curation records for the top 30, including evidence notes and `changes_score=no` status.

**Supplementary Table S7. Excluded candidates with reason.** Candidate-level exclusions and non-nominable cases documented after tiering.

**Supplementary Table S8. PCA/PERMANOVA batch diagnostic.** TCGA/GTEx source-effect diagnostic output used to keep tumor-normal selectivity claims explicitly source-aware.

**Supplementary Table S9. Surfaceome overlap and Jaccard analysis.** Published-list overlap and Jaccard comparisons for TCSA, CSPA, and SURFY.

**Supplementary Table S10. Tumor-normal power analysis.** Feasibility and sample-size context for tumor versus GTEx stomach and TCGA adjacent-normal comparisons.

**Supplementary Table S11. Score functional-form sensitivity.** Alternative score-transform outputs used to assess whether component functional forms drive ranking conclusions.

**Supplementary Table S12. TME marker-correlation flags.** Bulk marker-module and purity-adjusted TME correlation flags used as the fallback for absent score-level single-cell specificity.

**Supplementary Table S13. Subtype feasibility and power.** TCGA-STAD molecular subtype sample-size and power context for exploratory subtype summaries.

**Supplementary Table S14. Rank resolution simulation.** Pre-scoring simulation used to warn against fine rank interpretation before real-score stability analysis.

**Supplementary Table S15. Risk functional-form sensitivity.** Alternative `R` forms used to test whether risk aggregation changes candidate interpretation.

**Supplementary Table S16. Wang 2026 cross-check.** Tier 1/2 and benchmark overlap with the Wang 2026 gastric proteogenomic surface-target resources, including drug-target class and glyco-outlier context.

**Supplementary Table S17. Wang 2026 overlap enrichment.** Hypergeometric enrichment tests comparing Tier 1/2 overlap with Wang 2026 target backgrounds against random draws from the Core+Probable surfaceome universe.

**Supplementary Table S18. Wang 2026 matched-null sensitivity.** Matched-null permutation analysis comparing Tier 1/2 Wang overlap against nearest-neighbor Core+Probable controls matched on surfaceome confidence, expression, protein evidence and missingness, topology, component completeness, and accessibility class.

**Supplementary Table S19. GPI correction impact summary.** Summary metrics quantifying the effect of the universe-wide GPI evidence correction on ranked-universe size, confirmed GPI representation, top50 entry, named benchmark movement, and current Tier 1/2 GPI candidates.

**Supplementary Table S20. GPI rank delta.** Gene-level rank and score changes for confirmed GPI-anchor genes between the preserved pre-GPI snapshot and the active post-GPI ranking.

**Supplementary Table S21. External surfaceome baseline comparison.** Spearman rank correlation, top-k overlap, and Tier 1/2 overlap between the final ranking and TCSA final/core GESP baseline scores.

**Supplementary Table S22. Candidate-level TISCH2 scRNA compartment check.** Processed TISCH2 gastric single-cell expression summaries for the 18 Tier 1/2 candidates, including malignant-class support, mixed signal, non-malignant dominance, low malignant signal, and context-only calls.

## Data and code availability

All inputs used in the current analysis are public resources. Downloaded or captured raw/source files are listed in the release manifest, dataset registry, download manifest, and provenance log, with checksums in `data/checksums/` where files are stored locally. Primary local data paths include `data/raw/xena_toil/`, `data/raw/hpa/`, `data/raw/uniprot/`, `data/raw/gdc_tcga_stad/`, `data/raw/hgnc/`, `data/raw/surfaceome/`, `data/raw/cbioportal/`, `data/raw/tcga_purity/`, and `data/raw/tisch2/`.

Processed tables, rankings, validation outputs, figures, and manuscript display tables are available in `data/processed/`, `results/rankings/`, `results/validation/`, `results/figures/`, and `results/tables/`. The active frozen ranking table has SHA256 `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`. File-level ranking metadata are stored in `results/rankings/ranking_v2_frozen.metadata.yaml`. Earlier ranking snapshots are retained for reproducibility and diagnostic history.

Analysis code is in `scripts/`, `src/`, `workflow/Snakefile`, and the configuration files in `config/`. The repository includes smoke tests, unit tests, manuscript checks, and Snakemake dry-run checks documented in the README and reproducibility guide. The submission version will include a public repository URL and archival DOI after the release package is archived; those items remain pre-submission blockers in this draft.

No new patient samples, wet-lab data, or restricted-access clinical data were generated for this study. The Wang 2026 supplementary cross-check was performed from open-access materials and summarized into the Wang cross-check, overlap-enrichment, and matched-null tables; temporary article/supplement parsing files were not retained in the repository. The external baseline comparison is summarized in the external surfaceome baseline comparison tables. The limited TISCH2 candidate-level scRNA check is summarized in the candidate-level TISCH2 compartment tables. The GPI impact audit is summarized in the GPI correction-impact and rank-delta tables.

## Declarations

**Ethics approval and consent to participate.** Not applicable. This study uses publicly available, de-identified, aggregate, or open-access research data and does not generate new human-subject samples.

**Consent for publication.** Not applicable.

**Author information.** Vicenzo Scavino Alfaro, Independent Researcher, Lima, Peru. ORCID: 0009-0000-2472-9785. Correspondence: u201919346@upc.edu.pe.

**Declaration of interests.** The author declares no competing interests.

**Funding.** The author received no funding for this research.

**Author contributions.** Vicenzo Scavino Alfaro is the sole author and was responsible for conceptualization, data curation, formal analysis, methodology, software, validation, visualization, writing-original draft, writing-review and editing, and final manuscript approval.

**Acknowledgements.** The author acknowledges the developers, maintainers, data generators, and participants behind TCGA, GTEx, GDC, UCSC Xena/Toil, HPA, UniProt, HGNC, cBioPortal, TCSA, CSPA, SURFY, ESTIMATE/tidyestimate, TISCH2, the underlying public gastric single-cell datasets, and the Wang 2026 open-access gastric proteogenomic atlas. No endorsement by those projects is implied.

**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process.** During the preparation of this work, the author used OpenAI Codex to support manuscript organization, language editing, and repository-oriented consistency checks. The author reviewed, revised, verified, and approved the final manuscript and accepts full responsibility for its content.

## Graphical abstract caption

Public TCGA/GTEx RNA, HPA protein/localization, UniProt topology/GPI features, curated surfaceome resources, TME marker modules, and limited TISCH2 candidate annotations are integrated through a reproducible pipeline for gastric cancer surface-target prioritization. A universe-wide GPI-anchor evidence-routing correction is applied before ranking. Outputs are coarse, hypothesis-generating Tier 1/2 nominations with external TCSA/Wang consistency checks and explicit limits from bulk RNA, compartment flags, isoform ambiguity, HPA IHC granularity, and absence of wet-lab validation.

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
