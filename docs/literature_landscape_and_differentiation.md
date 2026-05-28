# Literature Landscape and Differentiation

Status: Fase 0B closed for execution on 2026-05-28.

Decision: `go_with_narrower_claim`.

This project should not claim to be the first gastric cancer target discovery or the first use of surfaceome concepts in gastric/GEJ cancer. The defensible claim is narrower: an auditable, surfaceome-guided MCDA prioritization framework for STAD/GAC with preregistered controls, isoform-aware handling, TCGA/GTEx batch diagnostics, normal-tissue risk scoring, missing-data policy, ranking stability analysis, and reproducible release.

## Search Protocol

Required plan queries:

1. `"surfaceome" AND "gastric cancer"`
2. `"surface target" AND "gastric" AND "prioritization"`
3. `"antibody target" AND "gastric adenocarcinoma" AND "computational"`
4. `"multi-omic" AND "surface" AND "cancer" AND "ranking"`
5. `"ADC target" AND "gastric cancer" AND "bioinformatics"`

Executed on 2026-05-28 using web search over PubMed, PMC, publisher pages, Sciety/Research Square, and open-access article pages. Direct automated Google Scholar review was not available in this environment. A Scholar-equivalent broad search pass using the same query language plus "Google Scholar" terms was performed on 2026-05-28 and did not identify a pivot-triggering equivalent study. Before manuscript submission, do a direct browser/manual Google Scholar check and append any additional close papers here.

## Search Log

| Date | Query | Search surface | Result of pass |
|---|---|---|---|
| 2026-05-28 | `"surfaceome" AND "gastric cancer"` | Web/PubMed/publisher index | Found pan-cancer surfaceome atlas, gastric/GEJ ADC target papers, and gastric antigen prioritization preprint. |
| 2026-05-28 | `"surface target" AND "gastric" AND "prioritization"` | Web/PubMed/publisher index | Found gastric trial target prioritization and GEJ/GSRCC ADC target discovery papers. |
| 2026-05-28 | `"antibody target" AND "gastric adenocarcinoma" AND "computational"` | Web/PubMed/publisher index | Found general ADC target discovery and gastric subtype-specific ADC work. |
| 2026-05-28 | `"multi-omic" AND "surface" AND "cancer" AND "ranking"` | Web/PubMed/publisher index | Found Cancer Surfaceome Atlas and Multiomics2Targets framework. |
| 2026-05-28 | `"ADC target" AND "gastric cancer" AND "bioinformatics"` | Web/PubMed/publisher index | Found HPA-based ADC target prioritization and gastric/GEJ ADC target examples. |
| 2026-05-28 | `Google Scholar "surfaceome" "gastric cancer" "prioritization"` and related variants | Broad web/academic index | Recovered already documented close papers: BMC Cancer 2026, CD66c GEJ, PVR GSRCC, Kathad 2024, Li 2022, TCSA, and ADC target discovery papers. No pivot-triggering equivalent found. |

## Differentiation Table

| Paper | Year | Scope | Data layers | Reproducible repo? | What it does | Gap this project can fill | Decision impact |
|---|---:|---|---|---|---|---|---|
| TCGA Research Network, "Comprehensive molecular characterization of gastric adenocarcinoma" (Nature, doi:10.1038/nature13480; https://pmc.ncbi.nlm.nih.gov/articles/PMC4170219/) | 2014 | Gastric adenocarcinoma molecular subtypes | Genomics, methylation, mRNA, miRNA, RPPA | Public TCGA data; not a target-prioritization repo | Defines EBV, MSI, GS, and CIN subtypes and establishes key molecular context for STAD. | Does not create a surfaceome target ranking, antibody/ADC target workflow, isoform-aware scoring, or reproducibility package. | Background foundation; does not block novelty. |
| Hu et al., "The Cancer Surfaceome Atlas integrates genomic, functional and drug response data to identify actionable targets" (Nature Cancer, doi:10.1038/s43018-021-00282-w; https://pmc.ncbi.nlm.nih.gov/articles/PMC9940627/) | 2021 | Pan-cancer surfaceome atlas | Bulk genomics, single-cell, functional screens, drug/actionability annotations | Public portal; article has public data, not project-specific STAD workflow | Defines and annotates genes encoding cell-surface proteins across cancers; identifies cancer-specific GESPs and therapeutic potential. | Not STAD/GAC-focused MCDA with preregistered controls, TCGA/GTEx batch diagnostics, isoform-specific CLDN18.2/FGFR2b handling, and ranking stability. | Strong prior art; project must position as gastric-specific auditable prioritization, not "first surfaceome atlas". |
| Mahboobnia et al., "Data-Driven Discovery of Molecular Targets for Antibody-Drug Conjugates in Cancer Treatment" (HPA/IHC-based ADC target discovery; https://pmc.ncbi.nlm.nih.gov/articles/PMC7801065/) | 2021 | Pan-cancer ADC target discovery | HPA IHC/protein, membrane protein filters, normal tissue exclusion | No project repo identified in search pass | Prioritizes ADC candidate targets across 20 tumor types using protein-level evidence and normal tissue filters. | Not gastric-specific surfaceome MCDA; limited explicit handling of STAD batch, isoforms, TME, perturbation, missing data, and reproducibility release. | Strong methodological comparator for HPA/protein evidence; does not block if differentiation is explicit. |
| Montero/Molina et al., "Surfaceome analyses uncover CD98hc as an antibody drug-conjugate target in triple negative breast cancer" (J Exp Clin Cancer Res, doi:10.1186/s13046-022-02330-4; https://pubmed.ncbi.nlm.nih.gov/35317825/) | 2022 | TNBC surfaceome ADC target discovery | Tumor/normal genomics, membrane proteomics, experimental validation | No project repo identified in search pass | Uses surfaceome analysis to nominate and experimentally validate CD98hc as an ADC target in TNBC. | Different tumor type and wet-lab validation focus; not a reproducible STAD/GAC computational ranking. | Useful methodological comparator for surfaceome-to-ADC logic. |
| Li et al., "Pan-Cancer Analysis Identifies Tumor Cell Surface Targets for CAR-T Cell Therapies and Antibody Drug Conjugates" (Cancers, doi:10.3390/cancers14225674; https://pmc.ncbi.nlm.nih.gov/articles/PMC9688665/) | 2022 | Pan-cancer CAR-T/ADC surface target discovery | TCGA, GTEx v8, membrane-protein databases, survival/risk analyses | No project repo identified in search pass | Screens tumor-specific cell membrane genes across 17 cancer types and proposes targets for CAR-T/ADC development. | Pan-cancer and transcriptome-heavy; not STAD-specific with HPA/topology/isoform/batch/reproducibility gates. | Important comparator; supports avoiding generic "surface target discovery" novelty claims. |
| Deng et al., "Multiomics2Targets identifies targets from cancer cohorts profiled with transcriptomics, proteomics, and phosphoproteomics" (Cell Reports Methods, doi:10.1016/j.crmeth.2024.100839; https://pmc.ncbi.nlm.nih.gov/articles/PMC11384097/) | 2024 | General multi-omics target-prioritization platform | Transcriptomics, proteomics, phosphoproteomics, knowledge-base tools | Web platform available; not a gastric paper-specific repo | Provides a reusable platform that ranks targets from multi-omics cancer cohorts and generates reports. | Not focused on STAD surfaceome/antibody targets; does not solve gastric-specific CLDN18.2/FGFR2b, TCGA/GTEx batch, preregistered controls, or surfaceome-specific candidate cards. | Important framework competitor; project should compare conceptually and avoid claiming a generic multi-omics target-prioritization invention. |
| Kathad et al., "Expanding the repertoire of Antibody Drug Conjugate targets with improved tumor selectivity and range of potent payloads through in-silico analysis" (PLOS One, doi:10.1371/journal.pone.0308604; https://pubmed.ncbi.nlm.nih.gov/39186767/) | 2024 | Pan-cancer/in-silico ADC target expansion | Surfaceome filters, tumor selectivity, IHC/protein annotations, payload matching | No project repo identified in search pass | Identifies 82 prioritized ADC targets and many target-indication combinations. | Not gastric-specific, and not built around CLDN18.2/FGFR2b isoform handling, STAD batch diagnostics, TME flags, and reproducibility gates. | Very close computational ADC comparator; must be cited and differentiated directly. |
| Zhang et al., "Identification of CD66c as a potential target in gastroesophageal junction cancer for antibody-drug conjugate development" (Gastric Cancer, doi:10.1007/s10120-025-01584-z; https://pubmed.ncbi.nlm.nih.gov/39918687/) | 2025 | GEJ cancer ADC target discovery | Transcriptomics, proteomics, phosphoproteomics, Cancer Surfaceome Atlas, IHC, cell/xenograft experiments | No repo identified in search pass | Uses multi-omics and surfaceome filtering to nominate CD66c and validates CD66c-DXd preclinically. | Single GEJ target, not broad STAD/GAC ranking; stronger wet-lab validation but narrower scope. | Raises novelty bar for GEJ/ADC claims; project should avoid claiming novelty for ADC target discovery alone. |
| Yin et al., "Navigating the future of gastric cancer treatment: a review on the impact of antibody-drug conjugates" (Cell Death Discovery, doi:10.1038/s41420-025-02429-5) | 2025 | Gastric cancer ADC review | Clinical and translational review | Not applicable | Reviews gastric cancer ADC landscape including HER2, CLDN18.2, TROP2 and emerging ADC directions. | Review only; does not prioritize new surfaceome targets computationally. | Useful clinical framing and benchmark-target context. |
| Xu et al., "Identification and prioritization of high-frequency biomarkers and therapeutic targets in gastric cancer trials" (BMC Cancer, doi:10.1186/s12885-025-15484-z; https://pubmed.ncbi.nlm.nih.gov/41454296/) | 2026 | Gastric cancer clinical trial target/biomarker prioritization | Trialtrove, GTEx RNA, HPA RNA/protein, CPTAC | No repo identified in search pass | Analyzes GC trial target landscape and evaluates target safety/specificity, highlighting candidates such as FGFR2, CTLA4, and TROP. | Does not appear to build a full surfaceome universe with MCDA ranking stability, preregistered controls, batch diagnostics, CLDN18.2/FGFR2b isoform policy, or Docker-level reproducibility. | Closest gastric target-prioritization competitor; forces narrower claim. |
| Hu, "TANK: A Variance-Based Framework for Identifying Heterogeneous Therapeutic Targets in Gastric Cancer" (Research Square/Sciety preprint; https://sciety.org/articles/activity/10.21203/rs.3.rs-9183044/v1) | 2026 | Gastric cancer antigen prioritization | TCGA-STAD raw counts, GSE26942 validation, survival analysis | No repo identified in search pass | Uses expression variance to recover CLDN18.2 as a high-ranking heterogeneous antigen/companion diagnostic target. | Single statistical principle, not surfaceome-specific multi-layer ranking; limited normal tissue, protein, topology, TME, missing data, and reproducibility controls. | Close because it is gastric antigen prioritization; project must emphasize multi-layer surfaceome/risk/stability rather than variance alone. |
| "A 15-layer multi-omics analysis of gastric cancer ecotypes provides therapeutic insights" (Cell Reports Medicine, doi:10.1016/j.xcrm.2026.102756; https://www.sciencedirect.com/science/article/pii/S2666379126001734) | 2026 | Gastric cancer ecotypes and therapeutic insights | 15 omics layers including genomics, epigenomics, transcriptomics, proteomics, PTMs, PPI, metabolomics, microbiome, TME deconvolution | Not assessed in this pass | Defines gastric cancer ecotypes and prioritizes ecotype-, subtype-, and cell-type-specific targetable proteins. | Broader and deeper multi-omics resource, but not specifically an auditable surfaceome/antibody target MCDA workflow with preregistered controls and release-grade reproducibility. | Major novelty pressure; project should become a focused, reproducible surfaceome-prioritization framework rather than a broad multi-omics atlas. |
| Chang et al., "Integrative proteogenomics maps multifactorial aetiology, progression and therapeutic vulnerabilities in gastric cancer" (Gut, doi:10.1136/gutjnl-2025-337247; https://pubmed.ncbi.nlm.nih.gov/41617485/) | 2026 | Gastric cancer proteogenomic vulnerabilities | WES, RNA-seq, proteome, phosphoproteome, microbial/environmental context | Not assessed in this pass | Builds a gastric cancer proteogenomic atlas and identifies therapeutic vulnerabilities/subtypes. | Not surfaceome/antibody-target specific; does not replace a reproducible surfaceome MCDA ranking. | Strong gastric multi-omics comparator; raises bar for biological interpretation. |
| "Poliovirus Receptor as a Potential Target in Gastric Signet-Ring Cell Carcinoma for Antibody-Drug Conjugate Development" (Cancers/PMC; https://pmc.ncbi.nlm.nih.gov/articles/PMC12838934/) | 2026 | Gastric signet-ring cell carcinoma ADC target discovery | Transcriptomics, proteomics, target validation, ADC synthesis, xenograft | No repo identified in search pass | Identifies PVR/CD155 as a GSRCC ADC target and validates PVR-DXd preclinically. | Single subtype/single target with wet-lab validation; not a broad reproducible STAD/GAC surfaceome prioritization pipeline. | Raises bar for subtype-specific ADC novelty; project can still proceed as broader ranking/methodology. |

## Go/No-Go Decision

Decision: `go_with_narrower_claim`

Rationale:

- There is no clear evidence from this pass of a gastric adenocarcinoma paper that simultaneously covers a broad surfaceome universe, auditable multi-layer scoring, preregistered controls, CLDN18.2/FGFR2b isoform handling, TCGA/GTEx batch diagnostics, explicit missing-data policy, ranking perturbation/leave-one-layer-out, and Docker-style reproducibility.
- However, the field is not open. Recent gastric/GEJ/GSRCC target papers and pan-cancer surfaceome/ADC frameworks overlap heavily with the original broad idea.
- Therefore the project should proceed only with a narrowed, methodology-forward claim.

## Revised Differentiation Claim

Primary claim to test:

> We present a reproducible, surfaceome-guided multi-criteria prioritization framework for gastric adenocarcinoma targets that integrates tumor expression, tumor-normal selectivity, organ-specific off-tumor risk, protein/localization evidence, topology/isoform confidence, and optional tumor-cell specificity, with preregistered controls, explicit TCGA/GTEx batch diagnostics, missing-data policy, ranking stability analysis, and release-grade provenance.

Claims to avoid:

- "First surfaceome analysis in gastric cancer."
- "First computational target discovery in gastric cancer."
- "Clinically validated new targets."
- "Safe targets" without qualifying that risk is proxy-based.
- "CLDN18.2 expression is resolved" if only gene-level CLDN18 RNA is available.

## Immediate Consequences for the Plan

1. Keep direct manual Google Scholar as a pre-submission check, not a blocker for Fase 1 inventory.
2. Proceed to Fase 1 only under `go_with_narrower_claim`.
3. In the manuscript, compare directly against TCSA, BMC Cancer 2026 target prioritization, TANK, CD66c-DXd GEJ, PVR-DXd GSRCC, and the 15-layer gastric ecotype atlas.
4. Add at least one figure or supplement explicitly benchmarking what this project adds over existing target-prioritization papers.
5. Include Kathad 2024, Li 2022, Molina/Montero 2022, Yin 2025, and Chang 2026 as additional comparators from the deep-research report.
