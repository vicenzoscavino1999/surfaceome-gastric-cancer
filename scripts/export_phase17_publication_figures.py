from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz
from matplotlib.backends.backend_svg import RendererSVG
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "manuscript" / "figure_table_plan.tsv"
OUTPUT_DIR = ROOT / "manuscript" / "latex" / "figures"
MANIFEST = ROOT / "results" / "tables" / "manuscript_publication_figure_manifest.tsv"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_style(element: ET.Element) -> dict[str, str]:
    declarations: dict[str, str] = {}
    for declaration in element.get("style", "").split(";"):
        if ":" in declaration:
            key, value = declaration.split(":", 1)
            declarations[key.strip()] = value.strip()
    return declarations


def parse_font_size(element: ET.Element) -> float:
    style = parse_style(element)
    raw_size = element.get("font-size") or style.get("font-size")
    if raw_size is None:
        raw_size = "9" if "small" in element.get("class", "").split() else "11"
    return float(raw_size.removesuffix("px"))


def parse_font_weight(element: ET.Element) -> str:
    style = parse_style(element)
    raw_weight = element.get("font-weight") or style.get("font-weight") or "normal"
    return "bold" if raw_weight in {"bold", "600", "700", "800", "900"} else "normal"


def text_to_path_data(element: ET.Element) -> str:
    if list(element):
        raise ValueError("nested SVG text elements are not supported")
    text = element.text or ""
    x = float(element.get("x", "0"))
    y = float(element.get("y", "0"))
    font = FontProperties(family="DejaVu Sans", weight=parse_font_weight(element))
    path = TextPath((0, 0), text, size=parse_font_size(element), prop=font)
    bounds = path.get_extents()
    anchor = element.get("text-anchor", "start")
    if anchor == "middle":
        x_shift = -(bounds.x0 + bounds.x1) / 2
    elif anchor == "end":
        x_shift = -bounds.x1
    else:
        x_shift = 0.0
    transform = Affine2D().translate(x_shift, 0).scale(1, -1).translate(x, y)
    return RendererSVG._convert_path(None, path, transform=transform, clip=False)


def expand_svg_uses(root: ET.Element) -> int:
    expanded_count = 0
    while True:
        uses = list(root.iter(f"{{{SVG_NS}}}use"))
        if not uses:
            return expanded_count
        target_by_id = {element.get("id"): element for element in root.iter() if element.get("id")}
        parent_by_child = {child: parent for parent in root.iter() for child in parent}
        for use_element in uses:
            href = use_element.get(f"{{{XLINK_NS}}}href") or use_element.get("href")
            if not href or not href.startswith("#"):
                raise ValueError("SVG use element must reference a local id")
            target = target_by_id.get(href[1:])
            if target is None or target.tag != f"{{{SVG_NS}}}path":
                raise ValueError(f"unsupported SVG use reference: {href}")
            replacement = copy.deepcopy(target)
            replacement.attrib.pop("id", None)
            target_transform = replacement.attrib.pop("transform", "")
            use_transform = use_element.get("transform", "")
            x = use_element.get("x", "0")
            y = use_element.get("y", "0")
            transforms = [value for value in [use_transform, f"translate({x} {y})", target_transform] if value]
            replacement.set("transform", " ".join(transforms))
            for key, value in use_element.attrib.items():
                if key not in {f"{{{XLINK_NS}}}href", "href", "x", "y", "transform"}:
                    replacement.set(key, value)
            replacement.tail = use_element.tail
            parent = parent_by_child[use_element]
            position = list(parent).index(use_element)
            parent.remove(use_element)
            parent.insert(position, replacement)
            expanded_count += 1


def normalize_image_hrefs(root: ET.Element) -> int:
    normalized_count = 0
    for image in root.iter(f"{{{SVG_NS}}}image"):
        xlink_href = image.attrib.pop(f"{{{XLINK_NS}}}href", None)
        if xlink_href is not None:
            image.set("href", xlink_href)
            normalized_count += 1
    return normalized_count


def normalize_svg(source: Path) -> tuple[bytes, int, int, int]:
    tree = ET.parse(source)
    root = tree.getroot()
    parent_by_child = {child: parent for parent in root.iter() for child in parent}
    text_elements = list(root.iter(f"{{{SVG_NS}}}text"))
    for text_element in text_elements:
        parent = parent_by_child[text_element]
        path_element = ET.Element(f"{{{SVG_NS}}}path")
        path_element.set("d", text_to_path_data(text_element))
        path_element.set("fill", text_element.get("fill", "black"))
        for key in ["fill-opacity", "opacity", "transform"]:
            if key in text_element.attrib:
                path_element.set(key, text_element.attrib[key])
        path_element.tail = text_element.tail
        position = list(parent).index(text_element)
        parent.remove(text_element)
        parent.insert(position, path_element)
    expanded_use_count = expand_svg_uses(root)
    normalized_image_href_count = normalize_image_hrefs(root)
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as handle:
        temporary_path = Path(handle.name)
    try:
        tree.write(temporary_path, encoding="utf-8", xml_declaration=True)
        return temporary_path.read_bytes(), len(text_elements), expanded_use_count, normalized_image_href_count
    finally:
        temporary_path.unlink(missing_ok=True)


def publication_rows() -> list[dict[str, str]]:
    with PLAN.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return [row for row in rows if row["type"] == "figure" and row["keep_in_main"] == "yes"]


def output_pdf_path(display_id: str, source: Path) -> Path:
    safe_id = display_id.lower().replace(" ", "_")
    return OUTPUT_DIR / f"{safe_id}_{source.stem}.pdf"


def nonwhite_fraction(page: fitz.Page) -> float:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(0.75, 0.75), alpha=False)
    samples = pixmap.samples
    colored_pixels = sum(
        1
        for index in range(0, len(samples), pixmap.n)
        if any(channel < 250 for channel in samples[index : index + 3])
    )
    return colored_pixels / (pixmap.width * pixmap.height)


def validate_pdf(path: Path) -> dict[str, str]:
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty publication PDF: {path.relative_to(ROOT)}")
    document = fitz.open(path)
    if document.page_count != 1:
        raise ValueError(f"expected one-page publication PDF: {path.relative_to(ROOT)}")
    page = document[0]
    fonts = page.get_fonts(full=True)
    if fonts:
        raise ValueError(f"publication PDF still contains font resources: {path.relative_to(ROOT)}")
    drawings = len(page.get_drawings())
    images = len(page.get_images(full=True))
    ink_fraction = nonwhite_fraction(page)
    if drawings == 0 and images == 0:
        raise ValueError(f"publication PDF contains no visible vector or image resources: {path.relative_to(ROOT)}")
    if ink_fraction < 0.001:
        raise ValueError(f"publication PDF renders as blank: {path.relative_to(ROOT)}")
    return {
        "width_pt": f"{page.rect.width:.2f}",
        "height_pt": f"{page.rect.height:.2f}",
        "drawings": str(drawings),
        "embedded_images": str(images),
        "font_resources": str(len(fonts)),
        "nonwhite_fraction": f"{ink_fraction:.6f}",
        "pdf_sha256": sha256(path),
    }


def export_figures(review_dir: Path | None) -> list[dict[str, str]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if review_dir is not None:
        review_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, str]] = []
    for row in publication_rows():
        source = ROOT / row["source_path_or_paths"]
        output = output_pdf_path(row["display_id"], source)
        normalized_svg, outlined_text_count, expanded_use_count, normalized_image_href_count = normalize_svg(source)
        svg_document = fitz.open("svg", normalized_svg)
        output.write_bytes(svg_document.convert_to_pdf())
        metrics = validate_pdf(output)
        if review_dir is not None:
            pdf = fitz.open(output)
            pixmap = pdf[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pixmap.save(review_dir / f"{output.stem}.png")
        manifest_rows.append(
            {
                "figure_id": row["display_id"],
                "title": row["title"],
                "source_svg": source.relative_to(ROOT).as_posix(),
                "publication_pdf": output.relative_to(ROOT).as_posix(),
                "outlined_text_count": str(outlined_text_count),
                "expanded_use_count": str(expanded_use_count),
                "normalized_image_href_count": str(normalized_image_href_count),
                **metrics,
            }
        )
    return manifest_rows


def write_manifest(rows: list[dict[str, str]]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def check_existing() -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected_rows = publication_rows()
    if len(rows) != len(expected_rows):
        raise ValueError(f"expected {len(expected_rows)} publication figures, found {len(rows)}")
    for row in rows:
        metrics = validate_pdf(ROOT / row["publication_pdf"])
        for key, value in metrics.items():
            if row[key] != value:
                raise ValueError(f"publication manifest mismatch for {row['figure_id']} field {key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate existing publication PDFs and manifest")
    parser.add_argument("--review-dir", type=Path, help="optional temporary directory for rendered PNG review files")
    args = parser.parse_args()
    if args.check:
        check_existing()
        print("Phase 17 publication figure export check passed.")
        return 0
    review_dir = args.review_dir
    if review_dir is not None and not review_dir.is_absolute():
        review_dir = ROOT / review_dir
    rows = export_figures(review_dir)
    write_manifest(rows)
    print(f"Exported {len(rows)} Phase 17 publication PDFs.")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
