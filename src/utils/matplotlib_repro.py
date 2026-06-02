"""Small helpers for byte-stable Matplotlib SVG exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib


SVG_HASH_SALT = "surfaceome_gastric_cancer_release"
SVG_DATE = "2026-05-28T00:00:00"


def configure_reproducible_svg() -> None:
    """Pin Matplotlib's generated SVG IDs across reruns."""
    matplotlib.rcParams["svg.hashsalt"] = SVG_HASH_SALT


def save_svg(fig: Any, output: Path, **kwargs: Any) -> None:
    """Save an SVG with stable metadata and generated element IDs."""
    output.parent.mkdir(parents=True, exist_ok=True)
    configure_reproducible_svg()
    metadata = {"Date": SVG_DATE}
    metadata.update(kwargs.pop("metadata", {}) or {})
    fig.savefig(output, format="svg", metadata=metadata, **kwargs)
    normalize_svg(output)


def normalize_svg(path: Path) -> None:
    """Remove renderer whitespace drift and force LF line endings."""
    text = path.read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(normalized)
