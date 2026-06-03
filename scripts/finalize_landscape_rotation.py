"""Post-process a compiled LaTeX PDF so lscape (landscape) table pages display rotated.

TinyTeX here lacks pdflscape, so the build falls back to lscape, which rotates the
table *content* 90 degrees but leaves the page in portrait orientation. The result is
readable text but sideways pages. This step detects those pages by their dominant text
writing direction and sets the page /Rotate so viewers show them as upright landscape.
The text layer is untouched, so copy/extract still works.

Usage: python scripts/finalize_landscape_rotation.py <pdf> [<pdf> ...]
"""
from __future__ import annotations

import sys
from collections import Counter

import fitz


def dominant_dir(page: "fitz.Page") -> tuple[int, int]:
    counts: Counter[tuple[int, int]] = Counter()
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            counts[tuple(round(c) for c in line.get("dir", (1, 0)))] += 1
    return counts.most_common(1)[0][0] if counts else (1, 0)


def rotate_landscape_pages(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    changed = 0
    for page in doc:
        if page.rotation != 0:
            continue  # already rotated; keep idempotent
        direction = dominant_dir(page)
        if direction == (0, -1):
            page.set_rotation(90)
            changed += 1
        elif direction == (0, 1):
            page.set_rotation(270)
            changed += 1
    if changed:
        doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    print(f"{pdf_path}: rotated {changed} landscape page(s)")
    return changed


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: finalize_landscape_rotation.py <pdf> [<pdf> ...]", file=sys.stderr)
        return 2
    for path in argv:
        rotate_landscape_pages(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
