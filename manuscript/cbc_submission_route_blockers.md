# Computational Biology and Chemistry Submission Route Blockers

Date: 2026-06-01

These items must be resolved before submitting the CBC package. They do not alter scores, rankings, tiers, or analysis artifacts.

## Route-Critical

- Publication route: use the subscription route to avoid APC; operationally, this is the no APC route. Do not choose open access unless funding is available for the listed USD 3,150 APC excluding taxes.
- Article access tradeoff: the final Elsevier published PDF will not be freely shareable if the subscription route is selected. A preprint can remain public, and the public repository/data release can remain public.
- Durable correspondence: resolved for this draft. The author confirmed that `u201919346@upc.edu.pe` is retained permanently by the university. Telephone metadata is `+51 962 559 391`.
- Public repository and DOI: resolved for this draft. The public repository URL is https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer. The frozen reproducibility data package is archived on Zenodo at https://zenodo.org/records/20498705 with DOI `10.5281/zenodo.20498705`, covering the frozen input bundle and checksum/provenance data package.
- Research data route: Computational Biology and Chemistry applies Elsevier research-data Option C, so the deposited data/release must be cited or linked in the article.

## Formatting

- LaTeX source must remain generated from `manuscript/cbc_manuscript_scaffold.md` through `scripts/build_phase17_latex_handoff.py`.
- The current generated profile follows an Elsevier `elsarticle` author-year profile for Computational Biology and Chemistry. Do not hand-edit `manuscript/latex/cbc_manuscript.tex`.
- Re-run the final PDF and visual checks after all source edits and metadata are frozen.
- Editorial Manager may require LaTeX submissions to keep source, bibliography, class/style files, figures, and tables at the same folder level. Prepare a flat upload package before submission if using the LaTeX route.
- Reviewer reproducibility is locally auditable through `docs/reproducibility_reviewer_guide.md` and `python scripts/run_reproducibility_checks.py`. `docs/source_acquisition_policy.md` records that API/manual captures are frozen inputs rather than a live-redownload claim. Clean-clone/container audit remains pending until the final public tag is frozen; DOI-bound data-package archival is complete for `v0.1.0-rc4`.

## Editorial Package

- Cover letter: use `manuscript/cbc_cover_letter_draft.md` as the starting point.
- Referees: draft shortlist prepared in `manuscript/cbc_suggested_referees_draft.md`; author conflict confirmation is still required before upload if the submission system requests suggested reviewers.
- Graphical abstract: final user approval still required after any wording changes.
- Data/code availability: DOI wording inserted; re-check after any final tag or manuscript-title edits.
- Preprint: optional and allowed under Elsevier policy; if posted, link it to the final DOI after publication.
- Postal address: insert in Editorial Manager only if the submission system requires it.
