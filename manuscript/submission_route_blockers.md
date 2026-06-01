# Submission Route Blockers

Date: 2026-06-01

These items must be resolved before submitting the CSBJ package. They do not alter scores, rankings, tiers, or analysis artifacts.

## Route-Critical

- CSBJ APC: official CSBJ/SPJ APC is USD 3,450 plus applicable taxes. Waivers can be requested from pre-submission through acceptance, but they are not granted until acceptance. Action: contact the SPJ program business office before submission and document the waiver route.
- Fallback venue: keep BMC Bioinformatics and PLOS One as practical fallback paths if CSBJ scope, page budget, or APC/waiver risk becomes unacceptable.
- Durable correspondence: replace the student email with a durable email retained after graduation before formal submission and proofs.
- Public repository and DOI: publish the repository/release package and archive it with Zenodo, OSF, or Figshare before submission. Insert both URL and DOI in the manuscript and cover letter.

## Formatting

- LaTeX source must remain generated from `manuscript/csbj_manuscript_scaffold.md` through `scripts/build_phase17_latex_handoff.py`.
- The current generated profile follows the CSBJ/SPJ two-column article template structure with local BibTeX/natbib numeric citations. Do not hand-edit `manuscript/latex/csbj_manuscript.tex`.
- Re-run the final PDF and visual checks after all source edits and metadata are frozen.
- Confirm whether CSBJ enforces the 25 printed pages, 15,000 words, or both at initial submission. If compression is needed, first move Table 5 or Table 4 to supplement and shorten declarations/availability boilerplate.

## Editorial Package

- Cover letter: use `manuscript/csbj_cover_letter_draft.md` as the starting point.
- Referees: prepare three suggested reviewers with verified current affiliation, email, ORCID if available, and a conflict-of-interest screen.
- Graphical abstract: final user approval still required after any wording changes.
- Data/code availability: remove draft wording once the public repository URL and archival DOI are available.
