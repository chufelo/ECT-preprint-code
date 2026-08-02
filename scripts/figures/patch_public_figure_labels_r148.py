#!/usr/bin/env python3
"""Create reader-facing R148 successors of figures with internal round labels.

The numerical curves, axes, legends, and status text are inherited byte-for-
byte at the PDF-object level except for one explicitly named text span per
input.  Each input hash is pinned.  The script fails closed if the expected
label is absent, duplicated, or if any forbidden public label survives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz


REPAIRS = (
    {
        "input": "r123/global/panels/fig45_c_dimensional_gate_r123.pdf",
        "output": "fig45_c_dimensional_gate_public_r148.pdf",
        "sha256": "d0280bf8df5b0f6417aff1f16d1f49a0e2c66c010873e9ea750145fbb3d607a4",
        "font_input": "r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf",
        "font_sha256": "18d93f9c182167192b8c67a38a36e606223ecc17adcc066a56b920004a422f49",
        "old": "R114 finite-body scalar gates",
        "new": "Finite-body scalar dimensional gates",
        "font_size": 12.8,
        "color": (0x25 / 255.0, 0x25 / 255.0, 0x25 / 255.0),
        "title": "Finite-body scalar dimensional gates",
        "subject": "Dimensional gate only; not a physical body-sensitivity or full-PPN prediction",
    },
    {
        "input": "r127/rotation_atlas/fig18_a_ddo154_r127.pdf",
        "output": "fig18_a_ddo154_public_r148.pdf",
        "sha256": "cab6b304b472b2635b2053208bd28a054cbdf2b2460a93227f8694bfaac5eb77",
    },
    {
        "input": "r127/rotation_atlas/fig18_b_ngc2403_r127.pdf",
        "output": "fig18_b_ngc2403_public_r148.pdf",
        "sha256": "49759fc651935ba8e8673a5c9b509c856b86492ec4a8aa74a091eb384c5664ca",
    },
    {
        "input": "r127/rotation_atlas/fig18_c_ngc3198_r127.pdf",
        "output": "fig18_c_ngc3198_public_r148.pdf",
        "sha256": "ac866ae189faf404860fe231a81ba8a3fad8c182d99eb0406b1ed9616408af8a",
    },
    {
        "input": "r127/rotation_atlas/fig18_d_ngc6503_r127.pdf",
        "output": "fig18_d_ngc6503_public_r148.pdf",
        "sha256": "219dea37ea8a58820feb660f1b8025ef45293610f842d9105427c19545cdaaf9",
    },
    {
        "input": "r127/rotation_atlas/fig20_a_ugc02953_r127.pdf",
        "output": "fig20_a_ugc02953_public_r148.pdf",
        "sha256": "d5139195c6dde9212dff9eb837ea5735beb9cb6856f81975f9feab181176ebd6",
    },
    {
        "input": "r127/rotation_atlas/fig20_b_ugc09133_r127.pdf",
        "output": "fig20_b_ugc09133_public_r148.pdf",
        "sha256": "c097eb21cea6b09a8f75e11d89fb6e0dfeeca3ef8013fb2b12472dc30cdc39c4",
    },
    {
        "input": "r127/rotation_atlas/fig20_c_ngc6946_r127.pdf",
        "output": "fig20_c_ngc6946_public_r148.pdf",
        "sha256": "d665d0993c638d7f01155eae8ada947d19119b8dd6a1e76e502e404947b0f7d6",
    },
    {
        "input": "r127/rotation_atlas/fig20_d_ngc7331_r127.pdf",
        "output": "fig20_d_ngc7331_public_r148.pdf",
        "sha256": "2c91bf77d868a07d162dfc3fc4852e213a0c9cf1c339653a70337806ec0195c7",
    },
)

ROTATION_OLD = "External comparators: fixed R102 M/L."
ROTATION_NEW = "External comparators: fixed stellar M/L."
FORBIDDEN = ("R114 finite-body scalar gates", "fixed R102 M/L")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_single_span(
    document: fitz.Document,
    old: str,
    new: str,
    font_size: float,
    color: tuple[float, float, float],
    font_buffer: bytes,
) -> dict[str, object]:
    if document.page_count != 1:
        raise RuntimeError(f"expected one-page figure, got {document.page_count}")
    page = document[0]
    matches = page.search_for(old)
    if len(matches) != 1:
        raise RuntimeError(f"expected one occurrence of {old!r}, got {len(matches)}")

    target = matches[0]
    spans = [
        span
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", ())
        for span in line.get("spans", ())
        if old in span.get("text", "")
    ]
    if len(spans) != 1:
        raise RuntimeError(f"expected one containing text span for {old!r}, got {len(spans)}")

    full_span = spans[0]
    full_text = full_span["text"]
    replacement = full_text.replace(old, new)
    if replacement == full_text:
        raise RuntimeError(f"replacement did not modify {full_text!r}")

    full_rect = fitz.Rect(full_span["bbox"])
    erase_rect = fitz.Rect(full_rect.x0 - 1.5, full_rect.y0 - 1.0, full_rect.x1 + 1.5, full_rect.y1 + 1.0)
    page.add_redact_annot(erase_rect, fill=(1, 1, 1))
    page.apply_redactions()

    embedded_font = fitz.Font(fontbuffer=font_buffer)
    missing_glyphs = sorted(
        {character for character in replacement if not embedded_font.has_glyph(ord(character))}
    )
    if missing_glyphs:
        raise RuntimeError(f"embedded font lacks glyphs: {missing_glyphs!r}")
    replacement_width = embedded_font.text_length(replacement, fontsize=font_size)
    available_width = page.rect.width - 16.0
    if replacement_width > available_width:
        raise RuntimeError(
            f"replacement text is wider than the page: "
            f"{replacement_width} > {available_width}"
        )
    insertion_x = (page.rect.width - replacement_width) / 2.0
    insertion_y = float(full_span["origin"][1])
    page.insert_font(fontname="R148Label", fontbuffer=font_buffer)
    inserted_lines = page.insert_text(
        fitz.Point(insertion_x, insertion_y),
        replacement,
        fontname="R148Label",
        fontsize=font_size,
        color=color,
        overlay=True,
    )
    if inserted_lines != 1:
        raise RuntimeError(f"expected one inserted line, got {inserted_lines}")
    return {
        "old": old,
        "new": new,
        "old_bbox": [round(v, 6) for v in target],
        "full_span_bbox": [round(v, 6) for v in full_rect],
        "replacement": replacement,
        "font_size_pt": font_size,
        "replacement_width_pt": round(replacement_width, 6),
        "insertion_point": [round(insertion_x, 6), round(insertion_y, 6)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    for specification in REPAIRS:
        source = input_root / specification["input"]
        if not source.is_file():
            raise FileNotFoundError(source)
        actual_input_hash = sha256(source)
        if actual_input_hash != specification["sha256"]:
            raise RuntimeError(
                f"input hash mismatch for {source}: {actual_input_hash} != {specification['sha256']}"
            )

        font_source = input_root / specification.get(
            "font_input", specification["input"]
        )
        if not font_source.is_file():
            raise FileNotFoundError(font_source)
        expected_font_hash = specification.get(
            "font_sha256", specification["sha256"]
        )
        actual_font_hash = sha256(font_source)
        if actual_font_hash != expected_font_hash:
            raise RuntimeError(
                f"font input hash mismatch for {font_source}: "
                f"{actual_font_hash} != {expected_font_hash}"
            )
        font_document = fitz.open(font_source)
        regular_fonts = [
            font
            for font in font_document[0].get_fonts(full=True)
            if font[3].split("+")[-1] == "DejaVuSans"
        ]
        if len(regular_fonts) != 1:
            raise RuntimeError(
                f"expected one regular DejaVuSans font in {font_source}, "
                f"got {len(regular_fonts)}"
            )
        font_buffer = font_document.extract_font(regular_fonts[0][0])[3]
        font_document.close()
        if not font_buffer:
            raise RuntimeError(f"embedded font extraction failed for {font_source}")

        document = fitz.open(source)
        if "old" in specification:
            old = str(specification["old"])
            new = str(specification["new"])
            font_size = float(specification["font_size"])
            color = tuple(specification["color"])
        else:
            old = ROTATION_OLD
            new = ROTATION_NEW
            font_size = 8.6
            color = (0x22 / 255.0, 0x22 / 255.0, 0x22 / 255.0)

        change = replace_single_span(
            document, old, new, font_size, color, font_buffer
        )
        metadata = document.metadata
        metadata.update(
            {
                "title": str(specification.get("title", "SPARC external-model comparison")),
                "subject": str(
                    specification.get(
                        "subject",
                        "Reader-facing Level-C comparison; fixed stellar M/L protocol",
                    )
                ),
                "author": "Valeriy Blagovidov",
                "creator": "ECT R148 public-label renderer",
                "producer": "PyMuPDF",
                "creationDate": "",
                "modDate": "",
                "keywords": "ECT reader-facing figure public labels",
            }
        )
        document.set_metadata(metadata)

        destination = output_root / specification["output"]
        document.save(
            destination,
            garbage=4,
            clean=True,
            deflate=True,
            no_new_id=True,
            pretty=False,
            preserve_metadata=True,
        )
        document.close()

        check = fitz.open(destination)
        extracted = "\n".join(page.get_text("text") for page in check)
        check.close()
        survivors = [token for token in FORBIDDEN if token in extracted]
        if survivors:
            raise RuntimeError(f"forbidden labels survived in {destination}: {survivors}")
        if new not in extracted:
            raise RuntimeError(f"new label missing from {destination}: {new!r}")

        records.append(
            {
                "input": str(source.relative_to(input_root)),
                "input_sha256": actual_input_hash,
                "font_input": str(font_source.relative_to(input_root)),
                "font_input_sha256": actual_font_hash,
                "output": destination.name,
                "output_sha256": sha256(destination),
                "bytes": destination.stat().st_size,
                "change": change,
            }
        )

    payload = {
        "schema_version": "1.0",
        "owner": "R148_PUBLIC_FIGURE_LABEL_SUCCESSORS_v1",
        "scientific_change": "none; reader-facing labels only",
        "records": records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
