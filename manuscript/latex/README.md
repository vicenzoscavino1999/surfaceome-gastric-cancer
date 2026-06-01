# Computational Biology and Chemistry LaTeX handoff

This directory is the generated Elsevier/CBC LaTeX handoff for the full-length article draft.

## Build

From the repository root:

```powershell
python scripts\build_phase17_latex_handoff.py
.\manuscript\latex\build_latex.ps1
```

The generated manuscript source is `cbc_manuscript.tex`. Edit `manuscript/cbc_manuscript_scaffold.md`, not the generated `.tex`, then regenerate.

The current `cbc_manuscript.pdf` is a draft preview with current author name, affiliation, ORCID, durable corresponding-author email, and phone metadata inserted. It is not submission-ready because the public repository URL, archival DOI, optional postal-address metadata, optional referee suggestions, and final user approval remain pending.

Publication figure PDFs are generated separately:

```powershell
python scripts\export_phase17_publication_figures.py
python scripts\export_phase17_publication_figures.py --check
```

The nine files in `figures/` are font-independent PDFs: text and Matplotlib SVG symbols are converted to explicit paths, while the expected raster heatmap/colorbar resources remain embedded. Hashes and render metrics are recorded in `results/tables/manuscript_publication_figure_manifest.tsv`.

## Template Profile

The generator follows the Elsevier `elsarticle` preprint profile with author-year citations for Computational Biology and Chemistry. The bibliography uses local `plainnat` because CBC accepts consistent reference formatting at submission and applies journal style after acceptance if needed.

Elsevier's LaTeX instructions warn that Editorial Manager may not process source files in subfolders. This local directory may keep `figures/` for reproducible compilation, but a final upload package should flatten `.tex`, `.bib`/`.bbl`, class/style files, figures, and editable tables into one directory if the submission system requires LaTeX sources.

The older `csbj_manuscript.*` files may remain as historical generated artifacts from the previous CSBJ route; the active CBC handoff is `cbc_manuscript.*`.

## Pending before submission

- Add postal-address metadata if required by Editorial Manager.
- Reconfirm funding, declaration of interests, and CRediT roles immediately before submission.
- Add public repository URL and archival DOI after release.
- Select the subscription route unless open-access funding is available.
- Recompile and visually inspect the final submission PDF.
