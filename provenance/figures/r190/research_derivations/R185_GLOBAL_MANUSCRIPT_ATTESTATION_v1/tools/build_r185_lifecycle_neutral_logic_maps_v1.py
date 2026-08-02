#!/usr/bin/env python3
"""Build lifecycle-neutral R185 successors of the five English logic maps.

The frozen R179 PDFs are the only inputs.  This renderer changes only the
explicit title/focus/footer lifecycle bands listed below.  Scientific nodes,
edges, status codes and topology are inherited.  Inputs are hash guarded and
the rendered pixels outside the declared replacement rectangles must remain
identical at 144 dpi.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageChops, ImageDraw


ROUND_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ROOT = (
    ROUND_ROOT / "candidate" / "R185_GLOBAL_ENGLISH_CORRECTION_CASCADE_V1"
)
INPUT_DIR = CANDIDATE_ROOT / "LaTex" / "figures" / "r179" / "logic_maps"
OUTPUT_DIR = CANDIDATE_ROOT / "LaTex" / "figures" / "r185" / "logic_maps"
QA_DIR = ROUND_ROOT / "figure_governance" / "qa" / "logic_maps_v1"
MANIFEST_PATH = ROUND_ROOT / "figure_governance" / "R185_LOGIC_MAP_MANIFEST_V1.json"
RUNTIME_PATH = ROUND_ROOT / "figure_governance" / "R185_LOGIC_MAP_RUNTIME_V1.json"
RENDER_DPI = 144
MATRIX = fitz.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0)


MAPS = {
    "partI_status_dependency_v15.pdf": {
        "sha256": "0ec82a0740b5bc6f99ec2c4c36e4d34d8a5d042b73e7a942e1548b8db92b01ad",
        "output": "partI_status_dependency.pdf",
        "title": "Selected Part I status and dependency map",
        "replacements": [
            (
                "Selected Part I status and dependency map (R181 candidate)",
                "Selected Part I status and dependency map",
            ),
            (
                "R181 focus: P4 adopted P/B; O(4)->O(3) stabiliser A conditional; c_hat^2=beta/(alpha-beta) A conditional; c_hat=1 B coefficient benchmark; c_char=c B calibration, linked when N_Phi=1 and",
                "Status focus: P4 adopted P/B; O(4)->O(3) stabiliser A conditional; c_hat^2=beta/(alpha-beta) A conditional; c_hat=1 B coefficient benchmark; c_char=c B calibration, linked when N_Phi=1 and",
            ),
            (
                "56 semantic nodes / 63 visible directed edges | R181 successor of frozen source b69742ebb88f32b3 | candidate only",
                "56 semantic nodes / 63 visible directed edges | frozen source b69742ebb88f32b3 | lifecycle-neutral render",
            ),
        ],
    },
    "partII_status_dependency_v15.pdf": {
        "sha256": "cb9fb4b9950429890347fe1ae28f135e9e81b672bf1140ac611c1ed1b96947be",
        "output": "partII_status_dependency.pdf",
        "title": "Selected Part II status and dependency map",
        "replacements": [
            (
                "Selected Part II status and dependency map (V15 candidate)",
                "Selected Part II status and dependency map",
            ),
            (
                "35 semantic nodes / 59 visible directed relations | R177 semantic owner a21756dda12db4d0 | candidate, not live",
                "35 semantic nodes / 59 visible directed relations | frozen source a21756dda12db4d0 | lifecycle-neutral render",
            ),
        ],
    },
    "partIII_status_dependency_v15.pdf": {
        "sha256": "34681946fe212b2b0ec8aa641c005c8cb72e17ea2ae1ec4ca64ddfedd499fba0",
        "output": "partIII_status_dependency.pdf",
        "title": "Selected Part III status and dependency map",
        "replacements": [
            (
                "Selected Part III status and dependency map (R181 candidate)",
                "Selected Part III status and dependency map",
            ),
            (
                "R181 focus: dimensionless iota_0 is not an action; S0 is an action-unit slot; S0=hbar is a Level-B calibration with owner and universality Open.",
                "Status focus: dimensionless iota_0 is not an action; S0 is an action-unit slot; S0=hbar is a Level-B calibration with owner and universality Open.",
            ),
            (
                "95 semantic nodes / 107 visible directed edges | R181 successor of frozen source 5f858a3aa7b78e56 | candidate only",
                "95 semantic nodes / 107 visible directed edges | frozen source 5f858a3aa7b78e56 | lifecycle-neutral render",
            ),
        ],
    },
    "partIV_status_dependency_v15.pdf": {
        "sha256": "8493241dc21be0d2e4ad7c128727b1cd39a2f3ca21477d3e02a0b0807b4fbd77",
        "output": "partIV_status_dependency.pdf",
        "title": "Selected Part IV status and dependency map",
        "replacements": [
            (
                "Selected Part IV status and dependency map (V15 candidate)",
                "Selected Part IV status and dependency map",
            ),
            (
                "28 semantic nodes / 48 visible directed edges | R177 owner a3e4edeeb8136444 | full semantic key accompanies this map",
                "28 semantic nodes / 48 visible directed edges | frozen source a3e4edeeb8136444 | full semantic key accompanies this map",
            ),
        ],
    },
    "whole_status_dependency_v15.pdf": {
        "sha256": "503b8a17bde84d5b07f9ad33b2ee81c58fff13d9a35be9d047852862bd66fbfc",
        "output": "whole_status_dependency.pdf",
        "title": "Selected ECT status and dependency map",
        "replacements": [
            (
                "Selected ECT status and dependency map (R181 candidate)",
                "Selected ECT status and dependency map",
            ),
            (
                "R181 focus: P4 and P7 are adopted Level-B inputs; their stabiliser algebra is conditional; physical QCD, S0 ownership and cross-sector cone universality remain Open.",
                "Status focus: P4 and P7 are adopted Level-B inputs; their stabiliser algebra is conditional; physical QCD, S0 ownership and cross-sector cone universality remain Open.",
            ),
            (
                "64 semantic nodes / 80 visible directed edges | R181 successor of frozen source d711b919f01cd982 | candidate only",
                "64 semantic nodes / 80 visible directed edges | frozen source d711b919f01cd982 | lifecycle-neutral render",
            ),
        ],
    },
}


CVD_MATRICES = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_records(page: fitz.Page) -> list[dict]:
    records = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            records.append(
                {
                    "text": "".join(span["text"] for span in line["spans"]),
                    "bbox": fitz.Rect(line["bbox"]),
                    "size": float(line["spans"][0]["size"]),
                    "origin": fitz.Point(line["spans"][0]["origin"]),
                }
            )
    return records


def render_rgb(page: fitz.Page) -> Image.Image:
    pix = page.get_pixmap(matrix=MATRIX, alpha=False, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def cvd_preview(image: Image.Image, matrix) -> Image.Image:
    return image.convert("RGB").convert(
        "RGB",
        matrix=tuple(value for row in matrix for value in (*row, 0.0)),
    )


def outside_rectangles_identical(before: Image.Image, after: Image.Image, rects: list[fitz.Rect]) -> bool:
    diff = ImageChops.difference(before, after)
    draw = ImageDraw.Draw(diff)
    scale = RENDER_DPI / 72.0
    for rect in rects:
        draw.rectangle(
            (
                int(rect.x0 * scale) - 3,
                int(rect.y0 * scale) - 3,
                int(rect.x1 * scale) + 3,
                int(rect.y1 * scale) + 3,
            ),
            fill=(0, 0, 0),
        )
    return diff.getbbox() is None


def write_contact_sheet(name: str, image: Image.Image) -> list[str]:
    variants = {
        "rgb": image,
        "grayscale": image.convert("L").convert("RGB"),
        **{key: cvd_preview(image, matrix) for key, matrix in CVD_MATRICES.items()},
    }
    width = 540
    height = round(image.height * width / image.width)
    sheet = Image.new("RGB", (width * len(variants), height), "white")
    outputs = []
    for index, (variant, item) in enumerate(variants.items()):
        resized = item.resize((width, height), Image.Resampling.LANCZOS)
        sheet.paste(resized, (index * width, 0))
        target = QA_DIR / f"{name}_{variant}.png"
        resized.save(target, optimize=False, compress_level=9)
        outputs.append(target.relative_to(ROUND_ROOT).as_posix())
    sheet_path = QA_DIR / f"{name}_contact_sheet.png"
    sheet.save(sheet_path, optimize=False, compress_level=9)
    outputs.append(sheet_path.relative_to(ROUND_ROOT).as_posix())
    return outputs


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    entries = []

    for input_name, spec in MAPS.items():
        source = INPUT_DIR / input_name
        if sha256(source) != spec["sha256"]:
            raise RuntimeError(f"input hash mismatch: {source}")
        doc = fitz.open(source)
        if doc.page_count != 1:
            raise RuntimeError(f"expected one-page input: {source}")
        page = doc[0]
        before = render_rgb(page)
        records = line_records(page)
        replaced_rectangles = []
        replacements = []
        for old, new in spec["replacements"]:
            matches = [record for record in records if record["text"] == old]
            if len(matches) != 1:
                raise RuntimeError(
                    f"expected one exact line for {old!r} in {source}; found {len(matches)}"
                )
            record = matches[0]
            rect = fitz.Rect(record["bbox"])
            # PyMuPDF textbox leading is slightly taller than an extracted line
            # bbox.  The lifecycle bands have clear white margins, so retain a
            # small declared pad without touching graph content.
            redact_rect = fitz.Rect(
                rect.x0 - 3.0,
                rect.y0 - 1.0,
                rect.x1 + 3.0,
                rect.y1 + 0.25,
            )
            replaced_rectangles.append(redact_rect)
            page.add_redact_annot(redact_rect, fill=(1.0, 1.0, 1.0))
            replacements.append(
                (redact_rect, record["bbox"], record["origin"], record["size"], old, new)
            )
        page.apply_redactions()
        for rect, original_bbox, origin, fontsize, old, new in replacements:
            fontsize *= 0.96
            width = fitz.get_text_length(new, fontname="helv", fontsize=fontsize)
            x = original_bbox.x0 + (original_bbox.width - width) / 2.0
            written = page.insert_text(
                fitz.Point(x, origin.y),
                new,
                fontsize=fontsize,
                fontname="helv",
                color=(0.0, 0.0, 0.0),
            )
            if written < 1:
                raise RuntimeError(f"replacement could not be written in {source}: {new!r}")

        doc.set_metadata(
            {
                "title": spec["title"],
                "author": "ECT project",
                "subject": (
                    "Lifecycle-neutral title/focus/footer successor; scientific "
                    "nodes, edges, topology and status content inherited unchanged"
                ),
                "keywords": "ECT,status map,dependency map,lifecycle neutral",
                "creator": Path(__file__).name,
                "producer": f"PyMuPDF {fitz.__version__}",
                "creationDate": "D:20260801000000Z",
                "modDate": "D:20260801000000Z",
            }
        )
        target = OUTPUT_DIR / spec["output"]
        doc.save(target, garbage=4, clean=True, deflate=True, no_new_id=True, use_objstms=0)
        doc.close()

        check = fitz.open(target)
        text = check[0].get_text()
        after = render_rgb(check[0])
        page_rect = check[0].rect
        check.close()
        lifecycle_tokens = ("R177", "R181", "V15 candidate", "candidate only", "candidate, not live")
        residual = [token for token in lifecycle_tokens if token in text]
        # The scientifically meaningful node label "Fixed-core candidate" is retained.
        if residual:
            raise RuntimeError(f"residual lifecycle tokens in {target}: {residual}")
        if spec["title"] not in text:
            raise RuntimeError(f"new title missing from {target}")
        outside_ok = outside_rectangles_identical(before, after, replaced_rectangles)
        if not outside_ok:
            raise RuntimeError(f"pixels changed outside replacement rectangles: {target}")
        qa_files = write_contact_sheet(Path(spec["output"]).stem, after)
        entries.append(
            {
                "input": source.relative_to(ROUND_ROOT).as_posix(),
                "input_sha256": spec["sha256"],
                "output": target.relative_to(ROUND_ROOT).as_posix(),
                "output_sha256": sha256(target),
                "page_geometry_pt": [page_rect.width, page_rect.height],
                "replacements": [
                    {"old": old, "new": new}
                    for _, _, _, _, old, new in replacements
                ],
                "outside_replacement_regions_identical_at_144_dpi": outside_ok,
                "scientific_nodes_edges_statuses": "inherited unchanged outside declared lifecycle bands",
                "grayscale_cvd_previews": qa_files,
            }
        )

    runtime = {
        "schema": "R185_LOGIC_MAP_RUNTIME_V1",
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "pymupdf": fitz.__version__,
        "pillow": Image.__version__,
        "render_dpi": RENDER_DPI,
        "render_command": (
            "python3 research/derivations/R185_GLOBAL_MANUSCRIPT_ATTESTATION_v1/"
            "tools/build_r185_lifecycle_neutral_logic_maps_v1.py"
        ),
        "deterministic_environment": {
            "fixed_pdf_dates": "D:20260801000000Z",
            "pdf_no_new_id": True,
            "png_compress_level": 9,
        },
    }
    RUNTIME_PATH.write_text(json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema": "R185_LOGIC_MAP_MANIFEST_V1",
        "status": "CANDIDATE_ONLY_NOT_LIVE_NOT_APPLIED",
        "scope": "English logic-map lifecycle bands only",
        "generator": Path(__file__).relative_to(ROUND_ROOT).as_posix(),
        "generator_sha256": sha256(Path(__file__)),
        "runtime_sidecar": RUNTIME_PATH.relative_to(ROUND_ROOT).as_posix(),
        "runtime_sidecar_sha256": sha256(RUNTIME_PATH),
        "entries": entries,
        "live_manuscript_or_publication_files_edited": False,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for entry in entries:
        print(entry["output"], entry["output_sha256"])


if __name__ == "__main__":
    main()
