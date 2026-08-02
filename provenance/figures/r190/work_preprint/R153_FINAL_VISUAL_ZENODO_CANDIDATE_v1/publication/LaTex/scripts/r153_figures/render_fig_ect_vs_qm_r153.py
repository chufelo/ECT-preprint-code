#!/usr/bin/env python3
"""Render the R153 status-controlled ECT/QM SVG with embedded fonts.

The SVG remains the editable semantic owner.  This renderer deliberately
supports only the small primitive subset used by that source (rect, line and
text/tspan).  Drawing through PyMuPDF avoids host font substitution by librsvg
and makes the publication PDF portable and reproducible.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

import fitz


ROOT = Path(__file__).resolve().parent
PUBLICATION_ROOT = ROOT.parents[1]
FONT_REGULAR = ROOT / "fonts/DejaVuSans.ttf"
FONT_BOLD = ROOT / "fonts/DejaVuSans-Bold.ttf"
FIXED_META = {
    "title": "ECT and standard quantum mechanics: R153 status comparison",
    "author": "ECT reproducibility workflow",
    "subject": "Luminance-first status successor; scientific wording preserved",
    "creator": "render_fig_ect_vs_qm_r153.py",
    "producer": "PyMuPDF with vendored DejaVu Sans",
    "creationDate": "D:20260725120000+02'00'",
    "modDate": "D:20260725120000+02'00'",
}
NS = "{http://www.w3.org/2000/svg}"


def colour(value: str | None, fallback: tuple[float, float, float]) -> tuple[float, float, float]:
    if not value or not value.startswith("#"):
        return fallback
    digits = value[1:]
    if len(digits) == 3:
        digits = "".join(char * 2 for char in digits)
    return tuple(int(digits[index:index + 2], 16) / 255.0 for index in (0, 2, 4))


def attr_number(element: ET.Element, name: str) -> float:
    return float(element.attrib[name])


def render(source: Path, output: Path) -> None:
    root = ET.parse(source).getroot()
    width = float(root.attrib["width"])
    height = float(root.attrib["height"])
    document = fitz.open()
    page = document.new_page(width=width, height=height)
    page.insert_font(fontname="R134DejaVu", fontfile=str(FONT_REGULAR))
    page.insert_font(fontname="R134DejaVuBold", fontfile=str(FONT_BOLD))
    regular = fitz.Font(fontfile=str(FONT_REGULAR))
    bold = fitz.Font(fontfile=str(FONT_BOLD))

    for element in root:
        tag = element.tag.removeprefix(NS)
        if tag in {"style"}:
            continue
        if tag == "rect":
            cls = element.attrib.get("class", "")
            role = element.attrib.get("data-role", "external")
            role_style = {
                "external": ("#F4F4F4", "#888888", None),
                "model": ("#DCECF7", "#0072B2", None),
                "conditional": ("#C7E4D5", "#00805C", "[5 2 1 2] 0"),
                "open": ("#F0C36E", "#B26E00", "[6 3] 0"),
            }[role]
            fill = colour(role_style[0], (0.941, 0.941, 0.941))
            stroke = colour(role_style[1], (0.6, 0.6, 0.6))
            rect = fitz.Rect(
                attr_number(element, "x"), attr_number(element, "y"),
                attr_number(element, "x") + attr_number(element, "width"),
                attr_number(element, "y") + attr_number(element, "height"),
            )
            page.draw_rect(
                rect,
                color=stroke,
                fill=fill,
                width=1.1 if cls == "header" else 0.9,
                dashes=role_style[2],
            )
            continue
        if tag == "line":
            page.draw_line(
                fitz.Point(attr_number(element, "x1"), attr_number(element, "y1")),
                fitz.Point(attr_number(element, "x2"), attr_number(element, "y2")),
                color=colour(element.attrib.get("stroke"), (0.733, 0.733, 0.733)),
                width=float(element.attrib.get("stroke-width", "0.5")),
                dashes="[4 3] 0" if element.attrib.get("stroke-dasharray") else None,
            )
            continue
        if tag != "text":
            raise RuntimeError(f"unsupported SVG primitive: {tag}")

        cls = element.attrib.get("class", "s")
        is_bold = cls in {"b", "hdr", "eq"}
        size = {"hdr": 15.0, "b": 13.5, "s": 12.0, "eq": 12.0}[cls]
        font = bold if is_bold else regular
        fontname = "R134DejaVuBold" if is_bold else "R134DejaVu"
        ink = (0.133, 0.133, 0.133) if cls != "s" else (0.333, 0.333, 0.333)
        text = "".join(element.itertext()).strip()
        x, y = attr_number(element, "x"), attr_number(element, "y")
        if element.attrib.get("text-anchor") == "middle":
            x -= font.text_length(text, fontsize=size) / 2.0
        page.insert_text((x, y), text, fontname=fontname, fontsize=size, color=ink)

    document.set_metadata(FIXED_META)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output, garbage=4, clean=True, deflate=True, no_new_id=True)
    document.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=PUBLICATION_ROOT / "figures/source/svg/r153/fig_ect_vs_qm_r153.svg")
    parser.add_argument("--output", type=Path, default=PUBLICATION_ROOT / "figures/r153/fig_ect_vs_qm_status_palette_r153.pdf")
    args = parser.parse_args()
    render(args.source.resolve(), args.output.resolve())
    print(f"rendered {args.output.resolve()} with vendored embedded fonts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
