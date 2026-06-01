# CSBJ Submission Checklist

Verified against the current CSBJ/SPJ Guide for Authors and AAAS-Science Partner Journals LaTeX template on 2026-05-31/2026-06-01:

https://spj.science.org/page/csbj/for-authors

https://www.overleaf.com/latex/templates/computational-and-structural-biotechnology-journal-template/qbyrhgnmngvy

## Article Package

- [x] Research Article framing selected.
- [x] Main-display budget remains within 10 figures and 5 tables.
- [x] Abstract is standalone, unstructured, contains no reference citations, and is kept under the SPJ-template 250-word guidance.
- [x] Maximum of 6 keywords.
- [x] Highlights drafted as a separate file: 3-5 bullets, each <=85 characters.
- [x] Graphical abstract artwork exported as a separate TIFF file.
- [x] Graphical abstract export is 1280 x 3200 px (h x w), above the CSBJ minimum.
- [x] Figure captions drafted separately from artwork.
- [x] Main tables supplied as editable TSV text.
- [x] Supplementary captions drafted and mapped to available artifacts.

## LaTeX Handoff

- [x] Markdown remains the drafting source; the final `.tex` is generated, not edited manually.
- [x] Initial DOI-verified BibTeX library created: `manuscript/csbj_references.bib`.
- [x] Create initial `manuscript/latex/` handoff package from the editorial draft.
- [x] Use current CSBJ/SPJ two-column `article` template structure in the generator.
- [x] Generate numeric bibliography from BibTeX/natbib for local reproducibility.
- [x] Render equations in LaTeX math mode rather than monospace.
- [x] Render candidate gene symbols in italic rather than code font where Markdown backticks identify biological symbols.
- [x] Convert manuscript SVG figures to font-independent publication PDFs with zero residual font resources.
- [x] Compile the SPJ-profile draft PDF.
- [ ] Recompile and visually inspect the final PDF after metadata and asset completion.

## Submission Metadata

- [x] Insert final author name and affiliation.
- [x] Insert current corresponding-author email.
- [ ] Replace student email with a durable email retained after graduation before submission.
- [ ] Insert postal address and phone number if required by the submission system.
- [x] Finalize CRediT author contributions for current single-author version.
- [x] Finalize funding statement.
- [x] Confirm declaration of interests.
- [x] Add generative-AI disclosure draft before the reference list.
- [ ] Review sex/gender scope statement in the limitations section.
- [x] Draft cover letter framing the work as GPI evidence-routing quantification/correction plus honest residual-validation limits.
- [ ] Provide three potential referees with verified current affiliations, emails, and no obvious conflicts.
- [ ] Contact SPJ business office or submission helpdesk about waiver timing before submission.
- [ ] Decide fallback journal path if the waiver is denied or CSBJ scope/APC becomes unsuitable.

## Release Dependencies

- [ ] Insert public repository URL.
- [ ] Insert archival DOI after Fase 18 release.
- [ ] Review whether public inputs should also be represented as formal `[dataset]` references.
- [ ] Re-run clean environment and Docker audit.
- [ ] Reconfirm guide-for-authors requirements immediately before submission.
