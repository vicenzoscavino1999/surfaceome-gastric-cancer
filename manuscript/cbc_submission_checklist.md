# Computational Biology and Chemistry Submission Checklist

Verified against the current ScienceDirect/Elsevier Guide for Authors and open-access information pages on 2026-06-01:

https://www.sciencedirect.com/journal/computational-biology-and-chemistry/publish/guide-for-authors

https://www.sciencedirect.com/journal/computational-biology-and-chemistry/publish/open-access-options

https://submit.elsevier.com/CBAC

## Journal Fit

- [x] Full-length article route selected.
- [x] Manuscript framed as computational life sciences / bioinformatics / functional genomics and proteomics.
- [x] No molecular docking or premature protein-modeling claim is used.
- [x] Candidate outputs are hypothesis-generating, not clinical validation.

## Article Package

- [x] Abstract is standalone, unstructured, contains no reference citations, and is <=250 words.
- [x] Keywords count is within 1-7.
- [x] Highlights are drafted as a separate editable file with 3-5 bullets, each <=85 characters.
- [x] Graphical abstract artwork is exported as a separate TIFF file.
- [x] Graphical abstract export is 3200 x 1280 px, above the Elsevier minimum 1328 x 531 px.
- [x] Figure captions are drafted.
- [x] Main tables are available as editable TSV text.
- [x] Supplementary captions are drafted and mapped to available artifacts.
- [x] Final editorial pass after CBC formatting.

## LaTeX Handoff

- [x] Markdown remains the drafting source; generated `.tex` must not be hand-edited.
- [x] CBC BibTeX library created: `manuscript/cbc_references.bib`.
- [x] Reference list expanded from 20 to 30 entries for CBC full-length article expectations.
- [x] Generate author-year citations for the Elsevier/CBC handoff.
- [x] Use Elsevier `elsarticle` class with a CBC journal declaration.
- [x] Render equations in LaTeX math mode rather than monospace.
- [x] Render candidate gene symbols in italic rather than code font where Markdown backticks identify biological symbols.
- [x] Convert manuscript SVG figures to font-independent publication PDFs with zero residual font resources.
- [x] Recompile and visually inspect the current PDF after metadata and asset completion.
- [x] Prepare a flat Editorial Manager upload package with `.tex`, bibliography/class/style files, tables, and figures at one directory level if LaTeX source upload is required.
- [x] Run current local verification set: Phase 17 manuscript check, publication-figure check, LaTeX log screen, PDF visual render, unit tests, Snakemake dry-run, and manual `smoke-test` equivalent.

## Submission Metadata

- [x] Insert author name and affiliation.
- [x] Insert current corresponding-author email.
- [x] Confirm corresponding-author email is durable and retained permanently by the university.
- [x] Insert phone number for Editorial Manager metadata.
- [ ] Insert full postal address if required by Editorial Manager.
- [x] Finalize CRediT author contributions for current single-author version.
- [x] Finalize funding statement.
- [x] Confirm declaration of interests wording.
- [x] Add Elsevier-style generative-AI disclosure before the reference list.
- [x] Review sex/gender scope statement in the limitations section.
- [x] Draft cover letter for CBC.
- [x] Draft three potential referees with public affiliations/emails; author conflict confirmation still required before upload.

## Publication Route

- [x] Select subscription route as the working plan: no APC/publication fee charged to authors.
- [x] Do not select open access unless funding is available for the USD 3,150 APC excluding taxes.
- [x] Preprint route remains allowed under Elsevier policy.
- [ ] If a preprint is posted, add the final DOI link after publication.

## Release Dependencies

- [ ] Insert public repository URL.
- [ ] Insert archival DOI after release; DOI must cover frozen inputs or an equivalent checksum/provenance data package.
- [ ] Cite or link the deposited dataset/release in the article, consistent with CBC research data Option C.
- [ ] Review whether public inputs should also be represented as formal dataset references.
- [x] Re-run local smoke-test equivalent, unit tests, Snakemake dry-run, and Phase 17 manuscript/figure checks.
- [x] Add reviewer-facing reproducibility guide and aggregate check command.
- [x] Add frozen-source acquisition policy and split GitHub Actions CI/manual release-audit workflow.
- [ ] Re-run clean clone/container audit on the final public tag/DOI package.
- [ ] Reconfirm Guide for Authors requirements immediately before submission.
