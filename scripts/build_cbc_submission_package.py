from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LATEX_DIR = ROOT / "manuscript" / "latex"
PACKAGE_DIR = ROOT / "manuscript" / "cbc_editorial_manager_package"

ROOT_FILES = [
    LATEX_DIR / "cbc_manuscript.tex",
    LATEX_DIR / "cbc_references.bib",
    LATEX_DIR / "cbc_manuscript.bbl",
    LATEX_DIR / "cbc_manuscript.pdf",
    LATEX_DIR / "elsarticle.cls",
    LATEX_DIR / "elsarticle-num.bst",
    ROOT / "manuscript" / "cbc_highlights.md",
    ROOT / "manuscript" / "cbc_cover_letter_draft.md",
    ROOT / "manuscript" / "cbc_suggested_referees_draft.md",
    ROOT / "manuscript" / "graphical_abstract.tiff",
]

TABLE_FILES = [
    ROOT / "results" / "tables" / "manuscript_table1_datasets.tsv",
    ROOT / "results" / "tables" / "manuscript_table2_score_definitions.tsv",
    ROOT / "results" / "tables" / "manuscript_table3_top_candidates.tsv",
    ROOT / "results" / "tables" / "manuscript_table4_controls.tsv",
    ROOT / "results" / "tables" / "manuscript_table5_candidate_flags.tsv",
]


def copy_file(source: Path, target_name: str | None = None) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    target = PACKAGE_DIR / (target_name or source.name)
    shutil.copy2(source, target)
    return target.name


def resolve_plainnat() -> Path | None:
    try:
        result = subprocess.run(
            ["kpsewhich", "plainnat.bst"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    return path if path.exists() else None


def main() -> int:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)

    manifest: list[str] = []
    manifest.append("# CBC Editorial Manager flat package")
    manifest.append("")
    manifest.append("Generated from repository sources. Do not edit these packaged files directly.")
    manifest.append("")
    manifest.append("## Core files")

    for source in ROOT_FILES:
        manifest.append(f"- {copy_file(source)}")
    plainnat = resolve_plainnat()
    if plainnat is not None:
        manifest.append(f"- {copy_file(plainnat, 'plainnat.bst')}")
    else:
        manifest.append("- plainnat.bst not copied; available from standard natbib TeX distribution")

    manifest.append("")
    manifest.append("## Figure PDFs")
    for source in sorted((LATEX_DIR / "figures").glob("*.pdf")):
        manifest.append(f"- {copy_file(source)}")

    manifest.append("")
    manifest.append("## Editable table TSV files")
    for source in TABLE_FILES:
        manifest.append(f"- {copy_file(source)}")

    manifest.append("")
    manifest.append("## External blockers")
    manifest.append(
        "- Public repository URL is https://github.com/vicenzoscavino1999/surfaceome-gastric-cancer; "
        "final code release tag is v0.1.2; archival DOI is 10.5281/zenodo.20498705."
    )
    manifest.append("- Add full postal address in Editorial Manager if required.")
    manifest.append("- Suggested referees remain optional unless the submission system requests them; a draft shortlist is included for author conflict confirmation.")

    (PACKAGE_DIR / "PACKAGE_README.md").write_text("\n".join(manifest) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote flat CBC submission package: {PACKAGE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
