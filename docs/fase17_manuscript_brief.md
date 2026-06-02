# Fase 17: Manuscript Brief

Date: 2026-05-31

## Status and scope

Fase 17 is manuscript drafting. This brief freezes the narrative and journal-format assumptions before prose drafting.

This phase does not change scores, weights, universe membership, rankings, coarse tiers, or candidate placement. It only translates frozen Fase 13-16 artifacts into a manuscript and submission package.

## Target journal

Primary target: Computational Biology and Chemistry (CBC), full-length article, subscription route.

Format checked on 2026-06-01 from the current ScienceDirect/Elsevier CBC Guide for Authors, open-access information page, Elsevier article-sharing policy, and LaTeX instructions:

- Full-length articles are original scientific papers in computational life sciences.
- CBC scope includes bioinformatics, functional genomics/proteomics, systems biology, statistical genetics, computational pharmacology, and innovative AI or machine-learning methods for biological data.
- Premature protein-modeling or docking-only submissions without biological insight are not considered; this manuscript does not make docking/modeling claims.
- Abstract should be concise and factual and not exceed 250 words.
- Keywords: 1-7.
- Highlights are required at submission; 3-5 bullets, maximum 85 characters each.
- A graphical abstract is mandatory.
- References should use a consistent style at submission; CBC's guide shows author-year in-text citations and an alphabetical reference list. The generated LaTeX handoff therefore uses author-year citations.
- Full-length articles typically include 30-50 references; the CBC adaptation expands the current reference list from 20 to 30 entries.
- Figures must be supplied as separate files with logical names; tables must be editable text, not images.
- CBC research-data Option C applies: deposit research data in a relevant repository and cite or link the dataset in the article. The DOI must cover frozen inputs or an equivalent checksum/provenance package because live-source re-downloads are best-effort only.
- Publication route: subscription has no publication fee charged to authors. Open access is optional and lists an APC of USD 3,150 excluding taxes.
- Elsevier permits preprints anywhere at any time, but the final published journal article cannot be publicly shared under the subscription route; the accepted manuscript has journal-specific sharing limits and a 24-month embargo for public repository posting.

Sources: https://www.sciencedirect.com/journal/computational-biology-and-chemistry/publish/guide-for-authors ; https://www.sciencedirect.com/journal/computational-biology-and-chemistry/publish/open-access-options ; https://www.elsevier.com/about/policies-and-standards/sharing ; https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions

Fallback targets remain BMC Bioinformatics and PLOS One if CBC scope or subscription-route logistics become unsuitable.

## Authoring format

Markdown remains the editable drafting source during claim review and language polish. The LaTeX handoff must be generated from `scripts/build_phase17_latex_handoff.py`, not edited by hand. The current generator targets an Elsevier `elsarticle` author-year profile for Computational Biology and Chemistry, using the repository-local `elsarticle.cls` and local `plainnat` bibliography style available in TinyTeX. This preserves manuscript reproducibility while aligning the active handoff with the CBC route.

## Frozen central thesis

We developed a reproducible public-data pipeline for gastric cancer surface-target prioritization that is compared against an external pan-cancer surfaceome-score baseline, checked against a contemporary gastric proteogenomic atlas, and quantifies how incomplete routing of confirmed GPI-anchor evidence propagates into candidate-universe construction and ranking.

This wording intentionally avoids an unmeasured cost claim and avoids saying that the nominated targets are clinically validated or safe.

## Contribution order

1. Reproducible public-data method with external consistency benchmarking.
2. Transferable GPI-anchor evidence-routing audit and correction.
3. Gastric cancer Tier 1/2 candidate nominations as hypothesis-generating outputs.

The manuscript should lead with the method and auditability, emphasize the GPI finding as the transferable contribution, and present candidates as the applied output.

## Claim guardrails

Allowed:

- candidate prioritization
- nominate
- coarse tier
- evidence layer
- external concordance
- external baseline behavior versus TCSA final/core GESP
- external consistency with Wang 2026
- limited post-ranking TISCH2 candidate-level compartment annotation
- requires experimental validation
- hypothesis-generating
- quantified GPI-anchor evidence-routing effect
- auditable GPI-anchor universe-stage correction

Avoid:

- validated target
- safe target
- precision-medicine ready
- first discovery
- cost advantage unless quantified
- clinical efficacy or safety claims
- fine intra-tier order

## Main-display budget

CBC does not list a fixed figure/table count for full-length articles, but every display item must be necessary and cited. The current package keeps the previous conservative budget as an internal readability target.

Current Fase 16 plan:

- Figures: 9 main-display entries if F6a and F6b remain separate.
- Tables: 5 main tables.

If space becomes tight after the CBC PDF is regenerated, the lowest-damage compression levers are: move Table 5 or Table 4 to Supplementary Materials, shorten declarations/availability boilerplate, and combine F6a/F6b if needed. Scientific caveats should be consolidated, not removed.

## Manuscript guardrails from prior phases

- Coarse tiers are unordered within tier.
- `SC` remains not available in the primary score.
- TME inference uses bulk marker-module and ESTIMATE/tidyestimate partial correlations, not cell-resolved proof.
- The limited TISCH2 check annotates the 18 Tier 1/2 candidates only; it does not resolve cell-of-origin for the full ranked universe and must not change scores or tiers.
- Only `STAD_GSE134520` contributes a TISCH2 malignant-cell class (880 malignant-class cells; premalignant/early-cancer study); `STAD_GSE167297` is context-only. Discordant calls lower candidate-specific confidence but must not silently change frozen scores or tiers.
- TCSA final/core GESP is an external surfaceome-prioritization baseline, not a gastric-specific validation label.
- Wang 2026 is an external consistency check, not proof of first discovery, independent ranking validation, or per-gene single-cell validation for genes absent from Figure 7H.
- `CLDN18.2` and `FGFR2b` remain isoform unresolved from gene-level expression.
- HPA IHC supports protein/localization evidence but lacks antibody-level and patient-level membrane details.
- Fase 14 supports coarse stability language but not fine rank interpretation.
- No wet-lab validation has been generated.

## Fase 17 deliverables started

- `manuscript/cbc_manuscript_scaffold.md`
- `manuscript/cbc_highlights.md`
- `manuscript/graphical_abstract_brief.md`
- `manuscript/figure_table_plan.tsv`

Current manuscript body status: Abstract, Materials and methods, Results, Discussion, Conclusions, Glossary, Data/code availability, Declarations, and Acknowledgements have editorially hardened prose. Initial DOI-verified references, declarations, figure/table captions, supplementary captions, and graphical-abstract submission caption text are drafted. The graphical abstract is exported as a separate TIFF with editable SVG source and a PNG visual-review raster. The `manuscript/latex/` handoff is generated from Markdown through the CBC Elsevier profile, and `manuscript/cbc_editorial_manager_package/` contains a flat package for Editorial Manager. The user-supplied author name, affiliation, ORCID, durable corresponding-author email, and telephone are inserted into the manuscript source and LaTeX handoff. Reviewer-hardening audits verified that active `Surf` scaling is the post-GPI `[5,10]` formula, clarified the six-active-layer/`SC` wording, centered Wang 2026 simple and matched-null overlap testing, quantified the GPI correction impact, downgraded Wang language to consistency-check framing, added TCSA external-baseline comparison, compressed limited TISCH2 candidate-level scRNA annotation to context-only status, reframed GPI as quantification/correction rather than first discovery, declared API/manual captures as frozen checksum inputs rather than live-redownload claims, added GitHub Actions small CI/manual release-audit hooks, and removed residual internal scenario/stage labels from public-facing text and artwork. The public repository URL is https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer, and the frozen data package DOI is `10.5281/zenodo.20498705`. The manuscript is not submission-ready; final graphical-abstract approval, final PDF approval after any further edits, optional postal address, and referee suggestions if requested remain pending. APC/waiver is no longer a blocker if the subscription route is selected.

## Decision

Fase 17 may proceed to sustained manuscript drafting from this brief and the Fase 16 figure/table package. The first full prose section should be Methods or Abstract, but all prose must preserve the claim guardrails above.
