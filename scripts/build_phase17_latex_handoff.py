from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "cbc_manuscript_scaffold.md"
BIBLIOGRAPHY = ROOT / "manuscript" / "cbc_references.bib"
OUTPUT_DIR = ROOT / "manuscript" / "latex"
OUTPUT_TEX = OUTPUT_DIR / "cbc_manuscript.tex"
OUTPUT_BIB = OUTPUT_DIR / "cbc_references.bib"
TABLE_DIR = ROOT / "results" / "tables"
AUTHOR_NAME = "Vicenzo Scavino Alfaro"
AUTHOR_EMAIL = "u201919346@upc.edu.pe"
AUTHOR_PHONE = "+51 962 559 391"
AUTHOR_ORCID = "0009-0000-2472-9785"
AUTHOR_AFFILIATION = "Independent Researcher"
AUTHOR_CITY = "Lima"
AUTHOR_COUNTRY = "Peru"

GENE_SYMBOLS = {
    "ALPG",
    "BST2",
    "CD47",
    "CD9",
    "CDH17",
    "CDH3",
    "CEACAM5",
    "CLDN18",
    "DSC2",
    "EPCAM",
    "ERBB2",
    "FGFR2",
    "HLA-DPB1",
    "IFNGR1",
    "IL2RG",
    "ITGB4",
    "ITGB5",
    "JAG1",
    "LRRC15",
    "LSR",
    "MET",
    "MPZL1",
    "MSLN",
    "NECTIN2",
    "NT5E",
    "PECAM1",
    "PTPRC",
    "TACSTD2",
    "TGFBR1",
    "TNFRSF11A",
    "ULBP2",
}

MATH_TOKENS = {
    "2^x - 0.001": r"$2^{x} - 0.001$",
    "E": r"$E$",
    "N": r"$N$",
    "R": r"$R$",
    "P": r"$P$",
    "SC": r"$SC$",
    "T": r"$T$",
    "Surf": r"$Surf$",
    "E=0.20": r"$E=0.20$",
    "N=0.20": r"$N=0.20$",
    "R=0.20": r"$R=0.20$",
    "P=0.15": r"$P=0.15$",
    "SC=0.00": r"$SC=0.00$",
    "Surf=0.15": r"$Surf=0.15$",
    "T=0.10": r"$T=0.10$",
    "N_critical": r"$N_{\mathrm{critical}}$",
    "N_stomach": r"$N_{\mathrm{stomach}}$",
    "R_max_plus_breadth": r"$R_{\mathrm{max+breadth}}$",
    "R_sum_capped": r"$R_{\mathrm{sum,capped}}$",
    "Surf_relative_confidence": r"$Surf_{\mathrm{relative\ confidence}}$",
    "x_gj": r"$x_{gj}$",
    "w_j": r"$w_j$",
    "A_g": r"$A_g$",
    "log2(TPM + 0.001)": r"$\log_2(\mathrm{TPM}+0.001)$",
    "log2FC >= 1": r"$\log_2\mathrm{FC}\geq 1$",
}

TEXT_TOKENS = {
    "GPI-anchor": "GPI-anchor",
    "Malignant cells": "Malignant cells",
    "CLDN18.2": "CLDN18.2",
    "FGFR2b/IIIb": "FGFR2b/IIIb",
}

EQUATIONS = {
    "E_raw = 0.40 * rank(median_TPM_tumor) + 0.30 * rank(percent_samples_TPM_gt_1) + 0.20 * rank(P75_TPM_tumor) + 0.10 * rank(P90_TPM_tumor)": r"""\begin{equation}
\begin{split}
E_{\mathrm{raw}} ={}& 0.40\,r_{\mathrm{median}}
 + 0.30\,r_{\mathrm{prev>1}} \\
& + 0.20\,r_{\mathrm{P75}}
 + 0.10\,r_{\mathrm{P90}}.
\end{split}
\end{equation}""",
    "N_score = 0.50 * rank(N_critical_log2fc) + 0.30 * rank(N_stomach_log2fc) + 0.20 * N_stat_gtex": r"""\begin{equation}
\begin{split}
N_{\mathrm{score}} ={}& 0.50\,r_{\mathrm{critical}}
 + 0.30\,r_{\mathrm{stomach}} \\
& + 0.20\,N_{\mathrm{stat,GTEx}}.
\end{split}
\end{equation}""",
    "Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5": r"""\begin{equation}
\operatorname{Surf}_{\mathrm{relative}} = \frac{S_{\mathrm{conf}} - 5}{5}.
\end{equation}""",
    "S_g = (sum_{j in A_g, j != R} w_j * x_gj - w_R * x_gR) / sum_{j in A_g} abs(w_j)": r"""\begin{equation}
S_g =
\frac{
\sum_{j\in A_g,\ j\neq R} w_j x_{gj}
- w_R x_{gR}
}{
\sum_{j\in A_g} |w_j|
}.
\end{equation}""",
}

FIGURE_PLATES = [
    ("1", ["f1_phase16_pipeline_overview.pdf"]),
    ("2", ["f2_phase16_surfaceome_evidence_landscape.pdf"]),
    ("3", ["f3_phase16_tumor_normal_selectivity.pdf"]),
    ("4", ["f4_phase16_multilayer_heatmap_top30.pdf"]),
    ("5", ["f5_top_candidates_scRNA_dotplot.pdf"]),
    ("6", ["f6a_rank_stability_heatmap.pdf", "f6b_bumpchart_scenarios.pdf"]),
    ("7", ["f7_phase16_benchmark_controls.pdf"]),
    ("8", ["f8_phase16_tier1_candidate_panel.pdf"]),
]

TABLE_PLATES = [
    ("1", TABLE_DIR / "manuscript_table1_datasets.tsv"),
    ("2", TABLE_DIR / "manuscript_table2_score_definitions.tsv"),
    ("3", TABLE_DIR / "manuscript_table3_top_candidates.tsv"),
    ("4", TABLE_DIR / "manuscript_table4_controls.tsv"),
]

TABLE_COLUMN_WIDTHS = {
    "1": [0.10, 0.13, 0.14, 0.13, 0.11, 0.09, 0.12, 0.19],
    "2": [0.08, 0.20, 0.08, 0.10, 0.15, 0.14, 0.23],
    "3": [0.03, 0.05, 0.05, 0.055, 0.055, 0.055, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.07, 0.055, 0.30],
    "4": [0.10, 0.06, 0.20, 0.13, 0.07, 0.07, 0.07, 0.13, 0.19],
    "5": [0.03, 0.05, 0.05, 0.10, 0.10, 0.09, 0.06, 0.04, 0.08, 0.08, 0.06, 0.09, 0.19],
}


def escape_tex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "<": r"\ensuremath{<}",
        ">": r"\ensuremath{>}",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    output: list[str] = []
    for character in text:
        output.append(replacements.get(character, character))
        if character in {"/", "+", "_", ";"}:
            output.append(r"\allowbreak{}")
    return "".join(output)


def bibliography_keys() -> list[str]:
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")
    keys = re.findall(r"@\w+\{([^,]+),", bibliography)
    if len(keys) != 39:
        raise ValueError(f"expected 39 BibTeX entries, found {len(keys)}")
    return keys


def expand_citation_group(group: str, keys: list[str]) -> str:
    numbers: list[int] = []
    for part in group.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-", 1))
            numbers.extend(range(start, end + 1))
        else:
            numbers.append(int(part))
    for number in numbers:
        if number < 1 or number > len(keys):
            raise ValueError(f"citation [{group}] refers to missing reference {number}")
    return ",".join(keys[number - 1] for number in numbers)


def format_monospace(code: str) -> str:
    if re.fullmatch(r"[0-9a-f]{40,}", code):
        chunks = [code[index : index + 4] for index in range(0, len(code), 4)]
        return r"\texttt{" + r"\allowbreak{}".join(chunks) + "}"
    escaped = escape_tex(code)
    return r"\texttt{" + escaped + "}"


def format_code_token(code: str) -> str:
    if code in EQUATIONS:
        return EQUATIONS[code]
    if code in GENE_SYMBOLS:
        return r"\textit{" + escape_tex(code) + "}"
    if code in MATH_TOKENS:
        return MATH_TOKENS[code]
    if code in TEXT_TOKENS:
        return escape_tex(TEXT_TOKENS[code])
    if "/" in code or code.endswith("/") or code in {"config/", "scripts/", "src/"}:
        return r"\path{" + code + "}"
    return format_monospace(code)


def format_inline(text: str, keys: list[str]) -> str:
    output: list[str] = []
    cursor = 0
    token_pattern = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|\[([0-9, -]+)\]")
    for match in token_pattern.finditer(text):
        output.append(escape_tex(text[cursor : match.start()]))
        code, bold, bracket_group = match.groups()
        if code is not None:
            output.append(format_code_token(code))
        elif bold is not None:
            output.append(r"\textbf{" + escape_tex(bold) + "}")
        elif bracket_group is not None:
            output.append(r"\citep{" + expand_citation_group(bracket_group, keys) + "}")
        cursor = match.end()
    output.append(escape_tex(text[cursor:]))
    return "".join(output)


def heading_title(markdown_heading: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", markdown_heading).strip()


def section_command(markdown_heading: str, level: int, keys: list[str]) -> str:
    title = format_inline(heading_title(markdown_heading), keys)
    command = "section" if level == 2 else "subsection"
    return rf"\{command}{{{title}}}"


def extract_between(source: str, start: str, end: str) -> str:
    return source.split(start, 1)[1].split(end, 1)[0].strip()


def render_body(source: str, keys: list[str]) -> str:
    body_end_marker = "## Graphical abstract caption" if "## Graphical abstract caption" in source else "## References"
    body = source.split("## 1. Introduction", 1)[1].split(body_end_marker, 1)[0]
    lines = ["\\section{Introduction}"]
    for line in body.splitlines()[1:]:
        stripped = line.strip()
        equation_match = re.fullmatch(r"`([^`]+)`\.?", stripped)
        if line.startswith("## "):
            lines.append(section_command(line[3:], level=2, keys=keys))
        elif line.startswith("### "):
            lines.append(section_command(line[4:], level=3, keys=keys))
        elif equation_match and equation_match.group(1) in EQUATIONS:
            lines.append(EQUATIONS[equation_match.group(1)])
        elif line:
            lines.append(format_inline(line, keys))
        else:
            lines.append("")
    return "\n".join(lines).strip()


def extract_display_caption(source: str, display_type: str, display_id: str, keys: list[str]) -> str:
    pattern = re.compile(
        rf"\*\*{display_type} {re.escape(display_id)}\. ([^*]+?)\.\*\*\s+(.*?)(?=\n\n)",
        flags=re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        raise ValueError(f"missing {display_type.lower()} caption for {display_id}")
    title, description = match.groups()
    caption = f"{title.strip()}. {' '.join(description.split())}"
    return format_inline(caption, keys)


def column_spec(widths: list[float]) -> str:
    return "@{}" + "".join(
        rf">{{\raggedright\arraybackslash}}p{{{width:.3f}\linewidth}}" for width in widths
    ) + "@{}"


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def format_table_cell(value: str) -> str:
    cleaned = " ".join(str(value).split())
    if cleaned == "":
        return r"\textemdash{}"
    return escape_tex(cleaned)


def render_table_plate(table_id: str, path: Path, source: str, keys: list[str]) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    columns, rows = read_tsv(path)
    widths = TABLE_COLUMN_WIDTHS[table_id]
    if len(columns) != len(widths):
        raise ValueError(
            f"table {table_id} has {len(columns)} columns but {len(widths)} widths are configured"
        )
    caption = extract_display_caption(source, "Table", table_id, keys)
    header = " & ".join(r"\textbf{" + escape_tex(column.replace("_", " ")) + "}" for column in columns)
    body_rows = [
        " & ".join(format_table_cell(row.get(column, "")) for column in columns) + r" \\"
        for row in rows
    ]
    return "\n".join(
        [
            r"\clearpage",
            r"\begin{landscape}",
            r"\begingroup",
            r"\tiny",
            r"\setlength{\tabcolsep}{2pt}",
            r"\renewcommand{\arraystretch}{1.13}",
            rf"\begin{{longtable}}{{{column_spec(widths)}}}",
            rf"\caption{{{caption}}}\label{{tab:review-{table_id}}}\\",
            r"\toprule",
            header + r" \\",
            r"\midrule",
            r"\endfirsthead",
            rf"\caption[]{{{caption} (continued)}}\\",
            r"\toprule",
            header + r" \\",
            r"\midrule",
            r"\endhead",
            *body_rows,
            r"\bottomrule",
            r"\end{longtable}",
            r"\endgroup",
            r"\end{landscape}",
        ]
    )


def render_figure_plate(display_id: str, files: list[str], source: str, keys: list[str]) -> str:
    caption = extract_display_caption(source, "Figure", display_id, keys)
    if display_id == "6" and len(files) == 2:
        graphics = [
            r"\textbf{a.}",
            rf"\includegraphics[width=\linewidth,height=0.34\textheight,keepaspectratio]{{{files[0]}}}",
            r"\par\vspace{0.5em}",
            r"\textbf{b.}",
            rf"\includegraphics[width=\linewidth,height=0.42\textheight,keepaspectratio]{{{files[1]}}}",
            r"\par\vspace{0.5em}",
        ]
        return "\n".join(
            [
                r"\clearpage",
                r"\begin{figure}[p]",
                r"\centering",
                *graphics,
                rf"\caption{{{caption}}}\label{{fig:review-{display_id}}}",
                r"\end{figure}",
            ]
        )
    graphics: list[str] = []
    if len(files) == 1:
        graphics.append(
            rf"\includegraphics[width=\linewidth,height=0.82\textheight,keepaspectratio]{{{files[0]}}}"
        )
    else:
        for index, file_name in enumerate(files):
            panel = chr(ord("a") + index)
            graphics.extend(
                [
                    rf"\textbf{{{panel}.}}",
                    rf"\includegraphics[width=\linewidth,height=0.38\textheight,keepaspectratio]{{{file_name}}}",
                    r"\par\vspace{0.5em}",
                ]
            )
    return "\n".join(
        [
            r"\clearpage",
            r"\begin{figure}[p]",
            r"\centering",
            *graphics,
            rf"\caption{{{caption}}}\label{{fig:review-{display_id}}}",
            r"\end{figure}",
        ]
    )


def render_review_displays(source: str, keys: list[str]) -> str:
    figure_blocks = [
        render_figure_plate(display_id, files, source, keys) for display_id, files in FIGURE_PLATES
    ]
    table_blocks = [
        render_table_plate(table_id, path, source, keys) for table_id, path in TABLE_PLATES
    ]
    return "\n\n".join(
        [
            r"\clearpage",
            r"\section*{Review figures and main tables}",
            (
                "The following pages embed the main display items for the review PDF. "
                "The same figures and editable table files are also supplied separately "
                "in the Editorial Manager package."
            ),
            *figure_blocks,
            *table_blocks,
        ]
    )


def build_cbc_tex(source: str, keys: list[str]) -> str:
    title = source.splitlines()[0].lstrip("\ufeff").removeprefix("# ").strip()
    abstract = extract_between(source, "## Abstract", "## Keywords")
    keywords = [
        keyword.strip()
        for keyword in extract_between(source, "## Keywords", "## 1. Introduction").split(";")
        if keyword.strip()
    ]
    body = render_body(source, keys)
    review_displays = render_review_displays(source, keys)

    return rf"""\documentclass[preprint,12pt,authoryear]{{elsarticle}}

\IfFileExists{{cmap.sty}}{{\usepackage{{cmap}}}}{{}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{lmodern}}
\usepackage{{amsmath}}
\usepackage{{array}}
\usepackage{{booktabs}}
\usepackage{{graphicx}}
\graphicspath{{{{./figures/}}{{./}}}}
\usepackage{{longtable}}
\IfFileExists{{pdflscape.sty}}{{\usepackage{{pdflscape}}}}{{\usepackage{{lscape}}}}
\usepackage{{url}}
\usepackage[hidelinks]{{hyperref}}

\journal{{Computational Biology and Chemistry}}
\bibliographystyle{{plainnat}}
\setlength{{\emergencystretch}}{{3em}}

\begin{{document}}

\begin{{frontmatter}}

\title{{{escape_tex(title)}}}
\author[aff1]{{{escape_tex(AUTHOR_NAME)}\corref{{cor1}}}}
\ead{{{escape_tex(AUTHOR_EMAIL)}}}
\cortext[cor1]{{Corresponding author. ORCID: {escape_tex(AUTHOR_ORCID)}. Telephone: {escape_tex(AUTHOR_PHONE)}.}}
\affiliation[aff1]{{organization={{{escape_tex(AUTHOR_AFFILIATION)}}}, city={{{escape_tex(AUTHOR_CITY)}}}, country={{{escape_tex(AUTHOR_COUNTRY)}}}}}

\begin{{abstract}}
{format_inline(abstract, keys)}
\end{{abstract}}

\begin{{keyword}}
{" \\sep ".join(escape_tex(keyword) for keyword in keywords)}
\end{{keyword}}

\end{{frontmatter}}

{body}

\bibliography{{cbc_references}}

{review_displays}

\end{{document}}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template",
        choices=["cbc"],
        default="cbc",
        help="LaTeX target profile. The default follows the Elsevier/CBC author-year route.",
    )
    parser.parse_args()

    source = SOURCE.read_text(encoding="utf-8-sig")
    keys = bibliography_keys()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BIBLIOGRAPHY, OUTPUT_BIB)

    tex = build_cbc_tex(source, keys)
    OUTPUT_TEX.write_text(tex, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT_TEX.relative_to(ROOT)} using Elsevier/CBC author-year profile")
    print(f"Copied {OUTPUT_BIB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
