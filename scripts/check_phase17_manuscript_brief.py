from __future__ import annotations

import csv
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/fase17_manuscript_brief.md",
    "docs/fase17_claim_traceability.md",
    "docs/reproducibility_reviewer_guide.md",
    "docs/source_acquisition_policy.md",
    "REPRODUCIBILITY.md",
    "DATA_AVAILABILITY.md",
    "manuscript/cbc_manuscript_scaffold.md",
    "manuscript/cbc_highlights.md",
    "manuscript/graphical_abstract_brief.md",
    "manuscript/figure_table_plan.tsv",
    "manuscript/cbc_references.bib",
    "manuscript/cbc_submission_checklist.md",
    "manuscript/cbc_cover_letter_draft.md",
    "manuscript/cbc_submission_route_blockers.md",
    "manuscript/graphical_abstract.svg",
    "manuscript/graphical_abstract.tiff",
    "manuscript/graphical_abstract_preview.png",
    "manuscript/latex/README.md",
    "manuscript/latex/build_latex.ps1",
    "manuscript/latex/cbc_manuscript.tex",
    "manuscript/latex/cbc_references.bib",
    "manuscript/latex/cbc_manuscript.bbl",
    "manuscript/latex/cbc_manuscript.pdf",
    "manuscript/cbc_editorial_manager_package/PACKAGE_README.md",
    "manuscript/cbc_editorial_manager_package/cbc_manuscript.tex",
    "manuscript/cbc_editorial_manager_package/cbc_manuscript.pdf",
    "manuscript/cbc_editorial_manager_package/cbc_references.bib",
    "manuscript/cbc_editorial_manager_package/cbc_manuscript.bbl",
    "manuscript/cbc_editorial_manager_package/graphical_abstract.tiff",
    "manuscript/cbc_editorial_manager_package/plainnat.bst",
    "scripts/build_phase17_latex_handoff.py",
    "scripts/build_cbc_submission_package.py",
    "scripts/export_phase17_publication_figures.py",
    "scripts/run_reproducibility_checks.py",
    "scripts/check_release_inputs.py",
    ".github/workflows/reproducibility-ci.yml",
    "requirements-manuscript.txt",
    "results/tables/manuscript_publication_figure_manifest.tsv",
    "results/tables/manuscript_table3_top_candidates.tsv",
    "results/tables/manuscript_table5_candidate_flags.tsv",
    "results/tables/wang2026_overlap_enrichment.tsv",
    "results/tables/wang2026_matched_null.tsv",
    "results/tables/gpi_correction_impact.tsv",
    "results/tables/gpi_rank_delta_v1_v2.tsv",
    "results/tables/external_surfaceome_baseline_comparison.tsv",
    "results/tables/external_surfaceome_baseline_gene_ranks.tsv",
    "results/tables/candidate_scrna_tisch2_compartment_check.tsv",
    "results/tables/candidate_scrna_tisch2_summary.tsv",
]

ACTIVE_TEXT_FILES = [
    "docs/fase17_manuscript_brief.md",
    "manuscript/cbc_manuscript_scaffold.md",
    "manuscript/cbc_highlights.md",
    "manuscript/graphical_abstract_brief.md",
    "manuscript/cbc_submission_checklist.md",
    "manuscript/cbc_cover_letter_draft.md",
    "manuscript/cbc_submission_route_blockers.md",
    "docs/reproducibility_reviewer_guide.md",
    "docs/source_acquisition_policy.md",
    "REPRODUCIBILITY.md",
    "DATA_AVAILABILITY.md",
    "manuscript/latex/README.md",
]

FORBIDDEN_OVERCLAIMS = [
    "precision-medicine ready",
    "safe target",
    "clinically validated candidate",
    "validated target",
    "fraction of the cost",
]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG header")
    return struct.unpack(">II", data[16:24])


def read_tiff_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    byte_order = data[:2]
    endian = {"II": "<", "MM": ">"}.get(byte_order.decode("ascii", errors="ignore"))
    if endian is None or len(data) < 8:
        raise ValueError("invalid TIFF header")
    magic, ifd_offset = struct.unpack(f"{endian}HI", data[2:8])
    if magic != 42:
        raise ValueError("invalid TIFF magic")
    entry_count = struct.unpack(f"{endian}H", data[ifd_offset : ifd_offset + 2])[0]
    dimensions: dict[int, int] = {}
    for index in range(entry_count):
        start = ifd_offset + 2 + index * 12
        tag, field_type, count, value = struct.unpack(f"{endian}HHI4s", data[start : start + 12])
        if tag not in {256, 257} or count != 1:
            continue
        if field_type == 3:
            dimensions[tag] = struct.unpack(f"{endian}H", value[:2])[0]
        elif field_type == 4:
            dimensions[tag] = struct.unpack(f"{endian}I", value)[0]
    if 256 not in dimensions or 257 not in dimensions:
        raise ValueError("TIFF dimensions missing")
    return dimensions[256], dimensions[257]


def main() -> int:
    failures: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            failures.append(f"missing required file: {rel}")

    if failures:
        print("Fase 17 CBC manuscript check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    brief = read_text("docs/fase17_manuscript_brief.md")
    claim_traceability = read_text("docs/fase17_claim_traceability.md")
    scaffold = read_text("manuscript/cbc_manuscript_scaffold.md")
    highlights = read_text("manuscript/cbc_highlights.md")
    bibliography = read_text("manuscript/cbc_references.bib")
    latex_manuscript = read_text("manuscript/latex/cbc_manuscript.tex")
    latex_bibliography = read_text("manuscript/latex/cbc_references.bib")
    cover_letter = read_text("manuscript/cbc_cover_letter_draft.md")
    submission_blockers = read_text("manuscript/cbc_submission_route_blockers.md")
    reproducibility = read_text("REPRODUCIBILITY.md")
    data_availability = read_text("DATA_AVAILABILITY.md")
    reviewer_guide = read_text("docs/reproducibility_reviewer_guide.md")
    source_policy = read_text("docs/source_acquisition_policy.md")

    for needle in [
        "Computational Biology and Chemistry",
        "subscription route",
        "no publication fee charged to authors",
        "USD 3,150",
        "preprints anywhere at any time",
        "author-year citations",
        "research-data Option C",
    ]:
        if needle not in brief:
            failures.append(f"brief missing CBC route phrase: {needle}")

    for rel in ACTIVE_TEXT_FILES:
        text = read_text(rel)
        for forbidden in ["Computational and Structural Biotechnology Journal", "CSBJ/SPJ", "CSBJ requires"]:
            if forbidden in text:
                failures.append(f"active CBC file still contains obsolete journal phrase in {rel}: {forbidden}")

    for needle in [
        "A reproducible framework for uncertainty-aware gastric cancer surface-target prioritization with GPI evidence-routing audit",
        "Target journal: Computational Biology and Chemistry",
        "subscription route",
        "integrates heterogeneous public evidence while keeping uncertainty explicit",
        "not enriched beyond a matched null controlling for surfaceome confidence",
        "transparent hypothesis generation and uncertainty delimitation, not independent validation",
        "excluded 54 confirmed glycosylphosphatidylinositol (GPI)-anchor genes",
        "including six Tier 1 candidates",
        "## Glossary",
        "## Acknowledgements",
        "Telephone: +51 962 559 391",
        "Computational Biology and Chemistry research-data route",
    ]:
        if needle not in scaffold:
            failures.append(f"scaffold missing required CBC/science phrase: {needle}")

    for needle in [
        "95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631",
        "ranking_v2_frozen.metadata.yaml",
        "Tier 1 = 6; Tier 2 = 12; Watchlist = 12",
        "hypergeometric p=0.0013",
        "matched-null mean 15.18, p=0.436",
        "v1 2,650 -> v2 2,704",
        "CEACAM5 120->12; MSLN 453->158",
    ]:
        if needle not in claim_traceability:
            failures.append(f"claim traceability audit missing required phrase: {needle}")

    if bibliography.count("@article{") != 30:
        failures.append("expected 30 BibTeX article entries for CBC")
    if latex_bibliography != bibliography:
        failures.append("LaTeX handoff BibTeX library differs from manuscript/cbc_references.bib")
    dois = re.findall(r"^\s*doi\s*=\s*\{([^}]+)\}", bibliography, flags=re.MULTILINE | re.IGNORECASE)
    if len(dois) != 30 or len(set(dois)) != 30:
        failures.append("expected 30 unique DOI fields in CBC BibTeX library")
    for doi in ["10.1126/science.aaz1776", "10.1016/S0140-6736(10)61121-X", "10.1371/journal.pcbi.1003285"]:
        if doi not in bibliography:
            failures.append(f"CBC BibTeX library missing added DOI: {doi}")

    manuscript_body, references = scaffold.split("## References", 1)
    cited_references: set[int] = set()
    for group in re.findall(r"\[([0-9, -]+)\]", manuscript_body):
        for part in group.split(","):
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-", 1))
                cited_references.update(range(start, end + 1))
            elif part:
                cited_references.add(int(part))
    listed_references = {int(value) for value in re.findall(r"^\s*(\d+)\.", references, flags=re.MULTILINE)}
    if cited_references != listed_references:
        failures.append(
            "numbered scaffold references are inconsistent before LaTeX conversion: "
            f"uncited={sorted(listed_references - cited_references)}, "
            f"missing={sorted(cited_references - listed_references)}"
        )

    abstract = scaffold.split("## Abstract", 1)[1].split("## Keywords", 1)[0]
    abstract_words = re.findall(r"\b[\w.-]+\b", abstract)
    if len(abstract_words) > 250:
        failures.append(f"abstract exceeds CBC guidance: {len(abstract_words)} > 250 words")
    keywords = [item.strip() for item in scaffold.split("## Keywords", 1)[1].split("## 1. Introduction", 1)[0].split(";") if item.strip()]
    if not 1 <= len(keywords) <= 7:
        failures.append(f"keyword count outside CBC range 1-7: {len(keywords)}")

    highlight_lines = [line[2:].strip() for line in highlights.splitlines() if line.startswith("- ")]
    if not 3 <= len(highlight_lines) <= 5:
        failures.append(f"expected 3-5 highlights, found {len(highlight_lines)}")
    for line in highlight_lines:
        if len(line) > 85:
            failures.append(f"highlight exceeds 85 characters ({len(line)}): {line}")

    try:
        svg_root = ET.parse(ROOT / "manuscript/graphical_abstract.svg").getroot()
        if svg_root.get("width") != "1600" or svg_root.get("height") != "640":
            failures.append("graphical abstract SVG dimensions changed from expected 1600 x 640")
    except ET.ParseError as exc:
        failures.append(f"graphical abstract SVG is not valid XML: {exc}")
    for path, dimension_reader in [
        ("manuscript/graphical_abstract.tiff", read_tiff_dimensions),
        ("manuscript/graphical_abstract_preview.png", read_png_dimensions),
    ]:
        try:
            width, height = dimension_reader(ROOT / path)
            if width < 1328 or height < 531:
                failures.append(f"graphical abstract raster below Elsevier minimum: {path} is {width} x {height}")
        except (OSError, UnicodeDecodeError, ValueError, struct.error) as exc:
            failures.append(f"unable to validate graphical abstract raster {path}: {exc}")

    for needle in [
        r"\documentclass[preprint,12pt,authoryear]{elsarticle}",
        r"\journal{Computational Biology and Chemistry}",
        r"\bibliographystyle{plainnat}",
        r"\bibliography{cbc_references}",
        r"\citep{",
        "Vicenzo Scavino Alfaro",
        "u201919346@upc.edu.pe",
        r"+\allowbreak{}51 962 559 391",
        "0009-0000-2472-9785",
        r"\begin{equation}",
        r"\textit{CDH3}",
    ]:
        if needle not in latex_manuscript:
            failures.append(f"CBC LaTeX handoff missing required phrase: {needle}")
    for forbidden in [
        r"\documentclass[twocolumn]{article}",
        r"\bibliographystyle{unsrtnat}",
        r"\bibliography{csbj_references}",
    ]:
        if forbidden in latex_manuscript:
            failures.append(f"CBC LaTeX handoff contains obsolete formatting phrase: {forbidden}")
    if r"\section{Graphical abstract caption}" in latex_manuscript:
        failures.append("graphical abstract caption should remain separate from the rendered manuscript body")
    if r"\title{\#" in latex_manuscript or "\\title{\ufeff\\#" in latex_manuscript:
        failures.append("CBC LaTeX handoff title contains a literal Markdown heading marker")
    if (ROOT / "manuscript/latex/cbc_manuscript.pdf").stat().st_size == 0:
        failures.append("CBC LaTeX handoff PDF preview is empty")

    for needle in [
        "subscription route",
        "not independent validation",
        "https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer",
        "archival DOI",
        "10.5281/zenodo.20498705",
    ]:
        if needle not in cover_letter:
            failures.append(f"CBC cover letter draft missing required phrase: {needle}")
    for needle in ["subscription route", "no APC", "Do not hand-edit `manuscript/latex/cbc_manuscript.tex`", "research-data Option C"]:
        if needle not in submission_blockers:
            failures.append(f"CBC submission blockers missing required phrase: {needle}")

    for needle in [
        "python scripts/run_reproducibility_checks.py",
        "Current Limitations",
        "https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer",
        "archival DOI",
        "10.5281/zenodo.20498705",
        "full transitive environment lockfile",
        "GitHub Actions",
        "docs/source_acquisition_policy.md",
    ]:
        if needle not in reviewer_guide:
            failures.append(f"reviewer reproducibility guide missing required phrase: {needle}")
    for needle in [
        "python scripts/run_reproducibility_checks.py",
        "Snakemake dry-run",
        "Public repository URL inserted",
        "Archival DOI inserted",
        "GitHub Actions",
    ]:
        if needle not in reproducibility:
            failures.append(f"reproducibility plan missing required phrase: {needle}")
    for needle in [
        "This release does not claim",
        "cBioPortal TCGA-STAD clinical",
        "Frozen archived input",
        "GitHub Actions checks are split",
        "The archival DOI covers",
        "10.5281/zenodo.20498705",
    ]:
        if needle not in source_policy:
            failures.append(f"source acquisition policy missing required phrase: {needle}")

    for needle in [
        "10.5281/zenodo.20498705",
        "https://zenodo.org/records/20498705",
    ]:
        for label, text in [
            ("CBC manuscript scaffold", scaffold),
            ("data availability", data_availability),
            ("reproducibility plan", reproducibility),
        ]:
            if needle not in text:
                failures.append(f"{label} missing archival dataset DOI phrase: {needle}")

    manuscript_tables = "\n".join(
        read_text(path)
        for path in [
            "results/tables/manuscript_table3_top_candidates.tsv",
            "results/tables/manuscript_table5_candidate_flags.tsv",
        ]
    )
    combined = "\n".join([scaffold, highlights, manuscript_tables]).lower()
    for phrase in FORBIDDEN_OVERCLAIMS:
        if phrase in combined:
            failures.append(f"forbidden overclaim phrase present: {phrase}")

    with (ROOT / "manuscript/figure_table_plan.tsv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in rows:
        for path in row["source_path_or_paths"].split(";"):
            path = path.strip()
            if path and not (ROOT / path).exists():
                failures.append(f"planned display source missing: {path}")

    with (ROOT / "results/tables/manuscript_publication_figure_manifest.tsv").open(
        newline="", encoding="utf-8"
    ) as handle:
        publication_rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in publication_rows:
        pdf_path = ROOT / row["publication_pdf"]
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            failures.append(f"publication PDF missing or empty: {row['publication_pdf']}")
        if row.get("font_resources") != "0":
            failures.append(f"publication PDF manifest records residual fonts: {row['figure_id']}")
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("pdf_sha256", "")):
            failures.append(f"publication PDF manifest has invalid SHA256: {row['figure_id']}")

    if failures:
        print("Fase 17 CBC manuscript check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Fase 17 CBC manuscript check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
