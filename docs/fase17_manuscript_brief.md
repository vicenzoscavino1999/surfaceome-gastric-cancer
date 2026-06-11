# Fase 17: Manuscript Brief

Date: 2026-05-31

## Status and scope

Fase 17 is manuscript drafting. This brief freezes the narrative and journal-format assumptions before prose drafting.

This phase does not change scores, weights, universe membership, rankings, coarse tiers, or candidate placement. It only translates frozen Fase 13-16 artifacts into a manuscript and submission package.

## Target journal

Primary target: Computational Biology and Chemistry (CBC), full-length article, subscription route.

Format rechecked on 2026-06-10 from the current ScienceDirect/Elsevier CBC Guide for Authors, Elsevier article-sharing policy, graphical-abstract guidance, artwork checklist, and LaTeX instructions:

- Full-length articles are original scientific papers in computational life sciences.
- CBC scope includes bioinformatics, functional genomics/proteomics, systems biology, statistical genetics, computational pharmacology, and innovative AI or machine-learning methods for biological data.
- Premature protein-modeling or docking-only submissions without biological insight are not considered; this manuscript does not make docking/modeling claims.
- Abstract should be concise and factual and not exceed 250 words; the current abstract has 225 words.
- Keywords: 1-7.
- Highlights are required at submission; 3-5 bullets, maximum 85 characters each. The current separate highlights file has 4 bullets, all <=85 characters.
- A graphical abstract is mandatory.
- References should use a consistent style at submission; CBC's guide shows author-year in-text citations and an alphabetical reference list. The generated LaTeX handoff therefore uses author-year citations.
- Full-length articles typically include 30-50 references; the CBC adaptation now uses 39 references after the pre-submission novelty/literature audit.
- Figures must be supplied as separate files with logical names; tables must be editable text, not images. The generated review PDF embeds the main figures and main-table previews near their first manuscript mention while retaining separate figure PDFs and editable TSV tables for upload.
- Elsevier LaTeX submissions must be flat in Editorial Manager: source, bibliography, class/style files, figures, and tables should be at the same folder level, not in subdirectories.
- CBC research-data Option C applies: deposit research data in a relevant repository and cite or link the dataset in the article. The DOI must cover frozen inputs or an equivalent checksum/provenance package because live-source re-downloads are best-effort only.
- Publication route: subscription has no publication fee charged to authors. Open access is optional and lists an APC of USD 3,150 excluding taxes.
- Elsevier permits preprints anywhere at any time, but preprints should not be enhanced to substitute for the final published article. Under the subscription route, the public shareable item after publication should be the article DOI/share link rather than a public copy of the published journal article.

Sources: https://www.sciencedirect.com/journal/computational-biology-and-chemistry/publish/guide-for-authors ; https://www.elsevier.com/about/policies-and-standards/sharing ; https://www.elsevier.com/researcher/author/tools-and-resources/graphical-abstract ; https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist ; https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions

Fallback targets remain BMC Bioinformatics and PLOS One if CBC scope or subscription-route logistics become unsuitable.

## Authoring format

Markdown remains the editable drafting source during claim review and language polish. The LaTeX handoff must be generated from `scripts/build_phase17_latex_handoff.py`, not edited by hand. The current generator targets an Elsevier `elsarticle` review-profile author-year manuscript for Computational Biology and Chemistry, using the repository-local `elsarticle.cls` and local `plainnat` bibliography style available in TinyTeX. This preserves manuscript reproducibility while aligning the active handoff with the CBC route.

## Frozen central thesis

We developed SurfPrior-GC, a reproducible public-data pipeline for gastric cancer surface-target prioritization that leads with a transferable GPI-anchor evidence-routing audit, then integrates heterogeneous public evidence into a coarse experimental queue with explicit uncertainty boundaries.

This wording intentionally avoids an unmeasured cost claim and avoids saying that the nominated targets are clinically validated or safe.

## Contribution order

1. Named framework: SurfPrior-GC.
2. Transferable GPI-anchor evidence-routing audit and correction, including the 54-gene universe effect and benchmark-rank shifts.
3. Integrated uncertainty-aware scoring across RNA, protein/localization, topology, normal-risk, TME, benchmark-control, and stability evidence.
4. Gastric cancer Tier 1/2 candidate nominations as hypothesis-generating outputs.
5. Scope boundary: matched-null overlap is not enriched and no wet-lab validation is claimed.

The manuscript should lead with the named framework and GPI audit, present the integrated evidence model and candidate tiers as the applied output, and place the matched-null negative result in limitations/scope rather than as the headline.

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
- Tables: 4 main tables, with the extended top-30 candidate-flag table supplied as Supplementary File 2.

If space becomes tight after the CBC PDF is regenerated, the lowest-damage compression levers are: keep supplementary-table detail in the separate supplementary files, shorten declarations/availability boilerplate, and combine F6a/F6b if needed. Scientific caveats should be consolidated, not removed.

## Manuscript guardrails from prior phases

- Coarse tiers are unordered within tier.
- `SC` remains not available in the primary score.
- TME inference uses bulk marker-module and ESTIMATE/tidyestimate partial correlations, not cell-resolved proof.
- The limited TISCH2 check annotates the 18 Tier 1/2 candidates only; it does not resolve cell-of-origin for the full ranked universe and must not change scores or tiers.
- Only `STAD_GSE134520` contributes a TISCH2 malignant-cell class (880 malignant-class cells; premalignant/early-cancer study); `STAD_GSE167297` is context-only. Discordant calls lower candidate-specific confidence but must not silently change frozen scores or tiers.
- TCSA final/core GESP is an external surfaceome-prioritization baseline, not a gastric-specific validation label.
- Wang 2026 is an external consistency check, not proof of first discovery, candidate-level proof, or per-gene single-cell support for genes absent from Figure 7H.
- `CLDN18.2` and `FGFR2b` remain isoform unresolved from gene-level expression.
- HPA IHC supports protein/localization evidence but lacks antibody-level and patient-level membrane details.
- Fase 14 supports coarse stability language but not fine rank interpretation.
- No wet-lab validation has been generated.

## Fase 17 deliverables started

- `manuscript/cbc_manuscript_scaffold.md`
- `manuscript/cbc_highlights.md`
- `manuscript/graphical_abstract_brief.md`
- `manuscript/figure_table_plan.tsv`

Current manuscript body status: Abstract, Materials and methods, Results, Discussion, Conclusions, Glossary, Data/code availability, Declarations, and Acknowledgements have editorially hardened prose. DOI-verified references, declarations, figure/table captions, a separate supplementary manifest caption file, and graphical-abstract submission caption text are drafted. The graphical abstract is exported as a separate TIFF with editable SVG source and a PNG visual-review raster. The `manuscript/latex/` handoff is generated from Markdown through the CBC Elsevier review profile, and `manuscript/cbc_editorial_manager_package/` contains a flat package for Editorial Manager. The generated review PDF embeds the main figures and main-table previews near their first manuscript mention while retaining separate figure PDFs, editable TSV tables, and a separate supplementary-table manifest for upload. The user-supplied author name, affiliation, ORCID, durable corresponding-author email, and telephone are inserted into the manuscript source and LaTeX handoff. Reviewer-hardening audits verified that active `Surf` scaling is the post-GPI `[5,10]` formula, clarified the six-active-layer/`SC` wording, centered Wang 2026 simple and matched-null overlap testing, quantified the GPI correction impact, downgraded Wang language to consistency-check framing, added TCSA external-baseline comparison, compressed limited TISCH2 candidate-level scRNA annotation to context-only status, reframed GPI as quantification/correction rather than first discovery, declared API/manual captures as frozen checksum inputs rather than live-redownload claims, added GitHub Actions small CI/manual release-audit hooks, and removed residual internal scenario/stage labels from public-facing text and artwork. The public repository URL is https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer, and the frozen data package DOI is `10.5281/zenodo.20498705`. The package is CBC-submission-ready at the repository-artifact level; remaining human upload items are final graphical-abstract/PDF approval, author conflict confirmation if suggested referees are entered, and full postal address only if Editorial Manager requires it. APC/waiver is not a blocker if the subscription route is selected.

## Decision

Fase 17 may proceed to sustained manuscript drafting from this brief and the Fase 16 figure/table package. The first full prose section should be Methods or Abstract, but all prose must preserve the claim guardrails above.
