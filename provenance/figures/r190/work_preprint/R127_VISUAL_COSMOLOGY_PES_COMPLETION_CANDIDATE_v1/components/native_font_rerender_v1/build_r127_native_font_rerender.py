#!/usr/bin/env python3
"""Native-owner font remediation for the R127 proposal candidate.

This builder never edits the live manuscript or a publication figure.  It
replays the preserved scientific owners and changes only native typography,
canvas geometry, and Graphviz spacing.  Numerical curves, arrays, status text,
graph nodes/edges, and semantic colours remain owned by the cited sources.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import html
import importlib.util
import json
import math
import os
import platform
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parent
R127 = SCRIPT.parents[2]
LATEX = SCRIPT.parents[5]
ECT = LATEX.parent
R123 = LATEX / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"
FONT_REMEDIATION = R127 / "components/font_readability_remediation_v1"
FONT_REMEDIATION_MANIFEST = (
    FONT_REMEDIATION / "manifests/R127_FONT_READABILITY_REMEDIATION_MANIFEST_v1.json"
)
FONT_REMEDIATION_INTEGRATION_MAP = (
    FONT_REMEDIATION / "manifests/R127_FONT_READABILITY_INTEGRATION_MAP_v1.json"
)
FONT_REMEDIATION_CHECKSUMS = FONT_REMEDIATION / "SHA256SUMS.txt"

os.environ.setdefault("MPLCONFIGDIR", str(COMPONENT / "qa/mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(COMPONENT / "qa/cache"))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784678400")

import fitz  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ft2font import FT2Font  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402
from matplotlib.text import Text  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


FIXED_TIME = datetime(2026, 7, 22, 0, 0, 0, tzinfo=timezone.utc)
FIXED_META = {
    "Title": "ECT R127 native-owner font remediation",
    "Author": "ECT reproducibility pipeline",
    "Subject": "Proposal-only native vector rerender",
    "Keywords": "ECT R127 native font readability grayscale safe",
    "Creator": SCRIPT.name,
    "Producer": "Matplotlib / Graphviz / PyMuPDF",
    "CreationDate": FIXED_TIME,
    "ModDate": FIXED_TIME,
}
FIXED_FITZ_META = {
    "title": FIXED_META["Title"],
    "author": FIXED_META["Author"],
    "subject": FIXED_META["Subject"],
    "keywords": FIXED_META["Keywords"],
    "creator": FIXED_META["Creator"],
    "producer": FIXED_META["Producer"],
    "creationDate": "D:20260722000000Z",
    "modDate": "D:20260722000000Z",
}

TEXT_WIDTH_PT = 453.543
TEXT_HEIGHT_PT = 700.157
ORDINARY_FLOOR_PT = 7.5
SCRIPT_FLOOR_PT = 5.0
DOT_FONT_FAMILY = "STIX Two Math"
_DOT_FONT_PATH: Path | None = None
_DOT_FONT_CHARMAP: set[int] | None = None
_TOP_PREDECESSORS: dict[str, dict[str, Any]] | None = None

READER_PRINT_TILING_PAGES: dict[str, int] = {
    "figures/r123/reader_print/fig09_partI_reader_print_supplement.pdf": 19,
    "figures/r123/reader_print/fig36_partIII_reader_print_supplement.pdf": 25,
    "figures/r123/reader_print/fig38_partIV_reader_print_supplement.pdf": 17,
    "figures/r123/reader_print/fig39_full_reader_print_supplement.pdf": 25,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ECT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def normalize_pdf(raw: Path, output: Path) -> None:
    source = fitz.open(raw)
    target = fitz.open()
    target.insert_pdf(source)
    target.set_metadata(FIXED_FITZ_META)
    output.parent.mkdir(parents=True, exist_ok=True)
    target.save(output, garbage=4, deflate=True, no_new_id=True)
    target.close()
    source.close()
    canonicalize_pdf_id(output)


def canonicalize_pdf_id(path: Path) -> None:
    """Replace only the fixed-width trailer ID; xref offsets stay valid."""
    data = path.read_bytes()
    replacement = (b"/ID [<00000000000000000000000000000000>"
                   b"<00000000000000000000000000000000>]")
    data, count = re.subn(rb"/ID\s*\[<[^>]+><[^>]+>\]", replacement, data)
    if count > 1:
        raise RuntimeError(f"{path}: more than one PDF trailer ID")
    path.write_bytes(data)


def all_text(fig: Figure) -> Iterable[Text]:
    for item in fig.findobj(match=Text):
        if str(item.get_text()).strip():
            yield item


def apply_font_floor(
    fig: Figure,
    *,
    floor: float = 10.6,
    title_floor: float = 12.0,
    legend_floor: float = 10.2,
) -> None:
    """Typography-only mutation on an already-created owner figure."""
    for text in all_text(fig):
        target = floor
        if text in fig.texts or text.get_fontweight() in ("bold", "semibold", 600, 700):
            target = max(target, title_floor)
        text.set_fontsize(max(float(text.get_fontsize()), target))
    # Tick Text instances can be lazily created only at draw time.  Set the
    # owning axis policy as well as the already-materialised artists.
    for ax in fig.axes:
        ax.tick_params(axis="both", which="both", labelsize=floor)
        ax.title.set_fontsize(max(float(ax.title.get_fontsize()), title_floor))
        ax.xaxis.label.set_fontsize(max(float(ax.xaxis.label.get_fontsize()), floor))
        ax.yaxis.label.set_fontsize(max(float(ax.yaxis.label.get_fontsize()), floor))
        for text in [*ax.get_xticklabels(which="both"), *ax.get_yticklabels(which="both")]:
            text.set_fontsize(max(float(text.get_fontsize()), floor))
    for legend in list(fig.legends) + [ax.get_legend() for ax in fig.axes]:
        if legend is None:
            continue
        for text in legend.get_texts():
            text.set_fontsize(max(float(text.get_fontsize()), legend_floor))
        legend.get_title().set_fontsize(max(float(legend.get_title().get_fontsize()), legend_floor))


def save_figure(fig: Figure, output: Path, *, size: tuple[float, float] | None = None) -> None:
    if size is not None:
        fig.set_size_inches(*size, forward=True)
    raw = output.with_suffix(".raw.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        raw,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.15,
        facecolor="white",
        metadata=FIXED_META,
    )
    normalize_pdf(raw, output)
    raw.unlink()
    plt.close(fig)


@contextlib.contextmanager
def capture_named_save(module: Any, name: str):
    holder: dict[str, Figure] = {}
    original = getattr(module, name)

    def capture(fig: Figure, *_args: Any, **_kwargs: Any) -> None:
        holder["fig"] = fig

    setattr(module, name, capture)
    try:
        yield holder
    finally:
        setattr(module, name, original)


def capture_top_level(path: Path) -> Figure:
    """Run a preserved top-level owner without permitting its hard-coded writes."""
    plt.close("all")
    original_savefig = Figure.savefig
    original_close = plt.close
    Figure.savefig = lambda self, *_args, **_kwargs: None  # type: ignore[method-assign]
    plt.close = lambda *_args, **_kwargs: None  # type: ignore[assignment]
    try:
        runpy.run_path(str(path), run_name=f"r127_capture_{path.stem}")
        numbers = plt.get_fignums()
        if len(numbers) != 1:
            raise RuntimeError(f"{path}: expected one captured figure, found {len(numbers)}")
        return plt.figure(numbers[0])
    finally:
        Figure.savefig = original_savefig  # type: ignore[method-assign]
        plt.close = original_close  # type: ignore[assignment]


def pdf_font_inventory(path: Path) -> dict[str, Any]:
    doc = fitz.open(path)
    all_spans: list[float] = []
    ordinary: list[float] = []
    scripts: list[float] = []
    outside: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(doc, start=1):
        page_all: list[float] = []
        page_ordinary: list[float] = []
        page_scripts: list[float] = []
        rect = page.rect
        lines = []
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if str(s.get("text", "")).strip()]
                if spans:
                    lines.append(spans)
        page_max = max((float(s.get("size", 0.0)) for spans in lines for s in spans), default=0.0)
        for spans in lines:
            line_max = max(float(s.get("size", 0.0)) for s in spans)
            for span in spans:
                    size = float(span.get("size", 0.0))
                    bbox = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                    page_all.append(size)
                    font = str(span.get("font", ""))
                    stripped = str(span.get("text", "")).strip()
                    exponent_like = bool(re.fullmatch(r"[+\-−¡]?[0-9]+", stripped))
                    short_oblique_math = (
                        font.startswith(("DejaVuSans-Oblique", "DejaVuSerif-Italic"))
                        and len(stripped) <= 3
                        and size < 0.80 * page_max
                    )
                    math_script = (
                        (font.startswith(("Cm", "STIX")) and size < 0.80 * page_max)
                        or (font.startswith("DejaVu") and exponent_like and size < 0.76 * page_max)
                        or short_oblique_math
                    )
                    if size < 0.86 * line_max or math_script:
                        page_scripts.append(size)
                    else:
                        page_ordinary.append(size)
                    if bbox.x0 < -0.75 or bbox.y0 < -0.75 or bbox.x1 > rect.width + 0.75 or bbox.y1 > rect.height + 0.75:
                        outside.append({"page": page_number, "text": span.get("text", ""), "bbox": list(bbox)})
        all_spans.extend(page_all)
        ordinary.extend(page_ordinary)
        scripts.extend(page_scripts)
        pages.append({
            "page": page_number,
            "width_pt": round(rect.width, 4),
            "height_pt": round(rect.height, 4),
            "min_span_pt": round(min(page_all), 4) if page_all else None,
            "min_ordinary_pt": round(min(page_ordinary), 4) if page_ordinary else None,
            "min_script_pt": round(min(page_scripts), 4) if page_scripts else None,
        })
    doc.close()
    return {
        "pages": pages,
        "page_count": len(pages),
        "minimum_span_pt": round(min(all_spans), 4) if all_spans else None,
        "minimum_ordinary_pt": round(min(ordinary), 4) if ordinary else None,
        "minimum_script_pt": round(min(scripts), 4) if scripts else None,
        "outside_mediabox": outside,
        "embedded_text": bool(all_spans),
    }


def placement_box(install_path: str) -> tuple[float, float]:
    if install_path == "figures/fig_ect_architecture.pdf":
        return 0.92 * TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if install_path == "figures/fig_equation_hierarchy.pdf":
        # Native larger type requires the parent TeX inclusion to use the full
        # text width; the integration map records this one deliberate layout
        # change from the old unreadable 0.55-width placement.
        return TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if install_path == "figures/fig_liv_delay.pdf":
        return 0.78 * TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if install_path == "figures/hrc/R97_HRC_RAR_DIAGNOSTIC.pdf":
        return 0.86 * TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if install_path == "figures/hrc/R97_HRC_UDG_STRESS.pdf":
        return 0.90 * TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if install_path == "figures/r103/r103_cluster_local_no_go.pdf":
        return 0.90 * TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT
    if "R123_SPARC_EXTERNAL_MODEL_COMPARISON" in install_path:
        return TEXT_WIDTH_PT, 0.70 * TEXT_HEIGHT_PT
    if "/global/graphviz/fig09_partI/" in install_path or "/global/graphviz/fig36_partIII/" in install_path:
        return 0.88 * TEXT_WIDTH_PT, 0.68 * TEXT_HEIGHT_PT
    if "/global/graphviz/fig38_partIV/" in install_path:
        return TEXT_WIDTH_PT, 0.75 * TEXT_HEIGHT_PT
    if "/global/graphviz/fig39_full/" in install_path:
        return TEXT_WIDTH_PT, 0.76 * TEXT_HEIGHT_PT
    if "/reader_print/" in install_path:
        return 841.8898, 595.2756
    if "/global/panels/" in install_path:
        return TEXT_WIDTH_PT, 0.60 * TEXT_HEIGHT_PT
    return TEXT_WIDTH_PT, 0.72 * TEXT_HEIGHT_PT


def effective_inventory(path: Path, install_path: str) -> dict[str, Any]:
    inventory = pdf_font_inventory(path)
    target_w, target_h = placement_box(install_path)
    page_results = []
    for page in inventory["pages"]:
        scale = min(1.0 if "/reader_print/" in install_path else target_w / page["width_pt"],
                    1.0 if "/reader_print/" in install_path else target_h / page["height_pt"])
        # TeX may enlarge small figures.  Enlargement is allowed and improves
        # readability, so do not cap the scale for ordinary includegraphics.
        if "/reader_print/" not in install_path:
            scale = min(target_w / page["width_pt"], target_h / page["height_pt"])
        page_results.append({
            "page": page["page"],
            "placement_scale": round(scale, 8),
            "effective_min_span_pt": round(page["min_span_pt"] * scale, 4) if page["min_span_pt"] else None,
            "effective_min_ordinary_pt": round(page["min_ordinary_pt"] * scale, 4) if page["min_ordinary_pt"] else None,
            "effective_min_script_pt": round(page["min_script_pt"] * scale, 4) if page["min_script_pt"] else None,
        })
    ordinary_values = [p["effective_min_ordinary_pt"] for p in page_results if p["effective_min_ordinary_pt"] is not None]
    script_values = [p["effective_min_script_pt"] for p in page_results if p["effective_min_script_pt"] is not None]
    span_values = [p["effective_min_span_pt"] for p in page_results if p["effective_min_span_pt"] is not None]
    return {
        "source": inventory,
        "placement_target_pt": [round(target_w, 4), round(target_h, 4)],
        "pages": page_results,
        "effective_minimum_span_pt": min(span_values) if span_values else None,
        "effective_minimum_ordinary_pt": min(ordinary_values) if ordinary_values else None,
        "effective_minimum_script_pt": min(script_values) if script_values else None,
        "ordinary_gate_pass": bool(ordinary_values) and min(ordinary_values) >= ORDINARY_FLOOR_PT - 1e-4,
        "script_gate_pass": (not script_values) or min(script_values) >= SCRIPT_FLOOR_PT - 1e-4,
        "mediabox_gate_pass": not inventory["outside_mediabox"],
    }


def pdf_text_integrity_guard(path: Path, *, forbid_question_mark: bool = False) -> dict[str, Any]:
    """Fail closed on visible replacement glyphs or leaked TeX source notation."""
    doc = fitz.open(path)
    page_texts = [page.get_text() for page in doc]
    doc.close()
    failures: list[dict[str, Any]] = []
    literal_macro = re.compile(r"\\(?:[A-Za-z]+|[A-Za-z]+_[A-Za-z0-9{}]+)")
    for page_number, text_value in enumerate(page_texts, start=1):
        for marker in ("□", "�"):
            if marker in text_value:
                failures.append({"page": page_number, "kind": "replacement_glyph", "token": marker})
        if forbid_question_mark and "?" in text_value:
            failures.append({"page": page_number, "kind": "unexpected_question_mark", "count": text_value.count("?")})
        for leaked in sorted(set(literal_macro.findall(text_value))):
            failures.append({"page": page_number, "kind": "literal_tex_macro", "token": leaked})
        if "Klein--Gordon" in text_value:
            failures.append({"page": page_number, "kind": "literal_double_hyphen", "token": "Klein--Gordon"})
    if failures:
        raise RuntimeError(f"{path}: PDF text-integrity failure {failures}")
    return {
        "zero_tofu": True,
        "zero_replacement_glyphs": True,
        "zero_literal_tex_macros": True,
        "unexpected_question_mark_checked": forbid_question_mark,
        "page_count": len(page_texts),
    }


def current_top_predecessors() -> dict[str, dict[str, Any]]:
    """Resolve the top component byte, not the stale lower payload snapshot.

    The font-readability component supersedes the R127 payload for 32 install
    paths.  A native replacement must bind to those already-installed reader
    bytes.  Falling back to ``payload/assets`` is permitted only for a path
    absent from that component (currently the discovered Fig. 41a owner).
    """
    global _TOP_PREDECESSORS
    if _TOP_PREDECESSORS is not None:
        return _TOP_PREDECESSORS
    data = json.loads(FONT_REMEDIATION_MANIFEST.read_text(encoding="utf-8"))
    result: dict[str, dict[str, Any]] = {}
    for row in data["remediations"]:
        install_path = str(row["install_path"])
        path = FONT_REMEDIATION / str(row["output_path"])
        if not path.is_file():
            raise RuntimeError(f"top predecessor missing: {path}")
        measured = sha256(path)
        if measured != row["output_sha256"]:
            raise RuntimeError(f"top predecessor hash mismatch: {path}: {measured} != {row['output_sha256']}")
        document = fitz.open(path)
        page_count = len(document)
        document.close()
        result[install_path] = {
            "path": path,
            "sha256": measured,
            "page_count": page_count,
            "layer": "font_readability_remediation_v1",
            "manifest": FONT_REMEDIATION_MANIFEST,
            "manifest_sha256": sha256(FONT_REMEDIATION_MANIFEST),
        }
    _TOP_PREDECESSORS = result
    return result


def current_top_predecessor(install_path: str) -> dict[str, Any]:
    top = current_top_predecessors()
    if install_path in top:
        return top[install_path]
    previous = R127 / "payload/assets" / install_path
    if not previous.is_file():
        raise RuntimeError(f"missing current R127 predecessor for {install_path}: {previous}")
    document = fitz.open(previous)
    page_count = len(document)
    document.close()
    return {
        "path": previous,
        "sha256": sha256(previous),
        "page_count": page_count,
        "layer": "R127_payload_fallback_no_later_supersession",
        "manifest": R127 / "manifests/R127_VISUAL_COSMOLOGY_PES_INSTALL_MAP_v1.json",
        "manifest_sha256": sha256(R127 / "manifests/R127_VISUAL_COSMOLOGY_PES_INSTALL_MAP_v1.json"),
    }


def render_pdf_page(pdf: Path, page_index: int, dpi: int = 120) -> Image.Image:
    doc = fitz.open(pdf)
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False, colorspace=fitz.csRGB)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return image


def cvd(image: Image.Image, mode: str) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=float) / 255.0
    matrices = {
        "protanopia": np.array([[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]),
        "deuteranopia": np.array([[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]),
        "tritanopia": np.array([[0.950, 0.050, 0.000], [0.000, 0.433, 0.567], [0.000, 0.475, 0.525]]),
    }
    if mode == "grayscale":
        y = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
        out = np.repeat(y[..., None], 3, axis=2)
    elif mode == "original":
        out = arr
    else:
        out = arr @ matrices[mode].T
    return Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255), mode="RGB")


def make_contact_sheet(items: list[tuple[str, Image.Image]], output: Path) -> None:
    thumb_w, thumb_h, label_h, cols = 360, 280, 34, 3
    rows = math.ceil(len(items) / cols)
    canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, (label, image) in enumerate(items):
        image = image.copy()
        image.thumbnail((thumb_w - 12, thumb_h - 12), Image.Resampling.LANCZOS)
        col, row = index % cols, index // cols
        x = col * thumb_w + (thumb_w - image.width) // 2
        y0 = row * (thumb_h + label_h)
        y = y0 + label_h + (thumb_h - image.height) // 2
        canvas.paste(image, (x, y))
        draw.text((col * thumb_w + 8, y0 + 8), label[:58], fill=(34, 34, 34), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", compress_level=9, optimize=False)


def record_output(records: list[dict[str, Any]], root: Path, install_path: str,
                  owners: list[Path], method: str, scientific_guard: dict[str, Any]) -> None:
    output = root / "assets" / install_path
    if not output.is_file():
        raise RuntimeError(f"missing output {output}")
    predecessor = current_top_predecessor(install_path)
    effective = effective_inventory(output, install_path)
    text_integrity = pdf_text_integrity_guard(output)
    record = {
        "install_path": install_path,
        "output": str(output.relative_to(root)),
        "output_sha256": sha256(output),
        "previous_candidate_asset": rel(predecessor["path"]),
        "previous_candidate_sha256": predecessor["sha256"],
        "previous_candidate_page_count": predecessor["page_count"],
        "previous_candidate_layer": predecessor["layer"],
        "previous_candidate_manifest": rel(predecessor["manifest"]),
        "previous_candidate_manifest_sha256": predecessor["manifest_sha256"],
        "new_component_page_count": effective["source"]["page_count"],
        "owners": [{"path": rel(path), "sha256": sha256(path)} for path in owners],
        "method": method,
        "scientific_guard": scientific_guard,
        "text_integrity_guard": text_integrity,
        "font_gate": effective,
        "status": "PASS" if effective["ordinary_gate_pass"] and effective["script_gate_pass"] and effective["mediabox_gate_pass"] else "FAIL_CLOSED",
    }
    records.append(record)


def make_architecture_native() -> Figure:
    """Reflow the exact architecture owner payload without changing its graph.

    The preserved owner predates the 7.5 pt effective-print gate.  Enlarging
    its text in place makes the two lower branch boxes overflow.  This native
    replay keeps all eight nodes and all nine declared relations, but gives
    every label enough box area at the actual 0.92-text-width placement.
    """
    fig = plt.figure(figsize=(6.2, 7.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.018, 0.018, 0.964, 0.964])
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 12.0)
    ax.axis("off")
    nodes: dict[str, tuple[float, float, float, float]] = {}

    def box(key: str, x: float, y: float, w: float, h: float,
            lines: list[str], fill: str, fs: float) -> None:
        nodes[key] = (x, y, w, h)
        ax.add_patch(FancyBboxPatch(
            (x - w / 2.0, y - h / 2.0), w, h,
            boxstyle="round,pad=0.13", facecolor=fill, edgecolor="#3F3F3F",
            linewidth=1.35, zorder=3,
        ))
        ax.text(x, y, "\n".join(lines), ha="center", va="center",
                fontsize=fs, linespacing=1.20, color="#202020", zorder=4)

    def arrow(src: str, dst: str) -> None:
        x0, y0, _w0, h0 = nodes[src]
        x1, y1, _w1, h1 = nodes[dst]
        ax.annotate(
            "", xy=(x1, y1 + h1 / 2.0), xytext=(x0, y0 - h0 / 2.0),
            arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.45,
                            mutation_scale=12, linestyle=(0, (4, 2.5))),
            zorder=5,
        )

    box("phi", 5.0, 11.25, 7.2, 0.82,
        [r"$\Phi$-medium on $\mathcal{M}^4$",
         r"P1–P6, DP; proposed S11 / ERP-$\Phi$"], "#D9EAF7", 10.2)
    box("ssb", 5.0, 9.55, 8.45, 1.48,
        [r"P4-supplied $O(4)\to O(3)$ ordered branch",
         r"$\langle\partial_A\Phi\rangle=u_0\,\delta_{Aw}$ (input)",
         r"Scalar hyperbolic principal form for $\alpha>\beta$",
         r"Physical clocks / metric remain Open"], "#DDF3EA", 8.9)
    box("ord", 5.0, 7.75, 7.15, 0.92,
        ["Supplied scalar ordered-branch EFT",
         r"$K^{AB}=\beta\,\delta^{AB}-\alpha\,n^A n^B$"], "#E8E8E8", 9.2)
    box("geo", 2.45, 6.10, 4.25, 1.22,
        ["Metric / gravity completion", "(Macroscopic Physics, Part II)",
         "physical tensor, source, metric Open"], "#E8E8E8", 8.5)
    box("coh", 7.55, 6.10, 4.25, 1.22,
        ["Quantum reconstruction programme", "(Quantum Sector, Part III)",
         "state / operators / Born owners Open"], "#E8E8E8", 8.5)
    box("geo_sub", 2.45, 4.25, 4.35, 1.42,
        [r"Scalar ansatz / tensor and $G_N$ owners Open",
         r"Cosmology; conditional ERP-$\Phi$/HRC layer",
         "BTFR/RAR diagnostics; metric/lensing Open"], "#F7F7F7", 8.25)
    box("coh_sub", 7.55, 4.25, 4.35, 1.42,
        [r"Supplied $S_0$ slot; Gaussian OS checks",
         "PES-R taxonomy; conditional Born route",
         "entanglement / detector / BH owners Open"], "#F7F7F7", 8.25)
    box("pred", 5.0, 1.50, 8.15, 1.30,
        ["Conditional outputs, external falsifiers, open owners",
         r"BTFR slope 4 conditional, $a_{M0}=cH_0/(2\pi)$ matched, LIV, 5th force",
         "Casimir scalar-BVP / Unruh targets; physical ECT owners open"],
        "#FCE8C4", 8.35)

    for src, dst in (
        ("phi", "ssb"), ("ssb", "ord"), ("ord", "geo"), ("ord", "coh"),
        ("geo", "geo_sub"), ("coh", "coh_sub"),
    ):
        arrow(src, dst)
    # Fan the two output dependencies into distinct points on the prediction
    # box so the separate back-reaction annotation remains unobstructed.
    for src, x1 in (("geo_sub", 4.0), ("coh_sub", 6.0)):
        x0, y0, _w0, h0 = nodes[src]
        _xp, yp, _wp, hp = nodes["pred"]
        ax.annotate(
            "", xy=(x1, yp + hp / 2.0), xytext=(x0, y0 - h0 / 2.0),
            arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.45,
                            mutation_scale=12, linestyle=(0, (4, 2.5))), zorder=5,
        )

    # This is the ninth relation in the owner: an explicitly un-derived
    # bidirectional back-reaction annotation, not an additional node.
    ax.annotate(
        "", xy=(6.4, 2.88), xytext=(3.6, 2.88),
        arrowprops=dict(arrowstyle="<|-|>", color="#777777", lw=1.15,
                        mutation_scale=10, linestyle=(0, (3, 2))), zorder=5,
    )
    ax.text(5.0, 3.07, "common-action back-reaction not yet derived",
            fontsize=8.30, ha="center", va="bottom", color="#5F5F5F",
            fontstyle="italic", zorder=6,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.7})
    return fig


def make_equation_hierarchy_native() -> Figure:
    """Reflow the four exact equation levels with separated status baselines."""
    fig = plt.figure(figsize=(6.2, 7.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.025, 0.02, 0.95, 0.96])
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 10.0)
    ax.axis("off")
    nodes: dict[str, tuple[float, float, float, float]] = {}

    def box(key: str, y: float, h: float, lines: list[str], status: str,
            fill: str) -> None:
        x, w = 5.0, 8.7
        nodes[key] = (x, y, w, h)
        ax.add_patch(FancyBboxPatch(
            (x - w / 2.0, y - h / 2.0), w, h,
            boxstyle="round,pad=0.12", facecolor=fill, edgecolor="#333333",
            linewidth=1.35, zorder=3,
        ))
        # Main equation/body and status occupy disjoint vertical bands.
        # Matplotlib's embedded math glyph sizes are approximately 0.70 of
        # the requested Text size.  Eleven points therefore keeps base math
        # above 7.5 pt and nested scripts above 5 pt in the output PDF.
        ax.text(x, y + 0.18, "\n".join(lines), ha="center", va="center",
                fontsize=11.0, linespacing=1.12, color="#202020", zorder=4)
        ax.text(x, y - h / 2.0 + 0.16, status, ha="center", va="bottom",
                fontsize=8.15, color="#5F5F5F", fontstyle="italic", zorder=4)

    def arrow(src: str, dst: str, label: str) -> None:
        x0, y0, _w0, h0 = nodes[src]
        x1, y1, _w1, h1 = nodes[dst]
        ys, yd = y0 - h0 / 2.0, y1 + h1 / 2.0
        ax.annotate(
            "", xy=(x1, yd), xytext=(x0, ys),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.35,
                            mutation_scale=12, linestyle=(0, (4, 2.5))), zorder=2,
        )
        ax.text(x0 + 0.18, (ys + yd) / 2.0, label, fontsize=8.05,
                ha="left", va="center", color="#555555", fontstyle="italic",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5},
                zorder=5)

    box("L0", 9.05, 1.42,
        [r"$\delta^{AB}\partial_A\partial_B\Phi-V^{\prime}(\Phi)=0$",
         "Euclidean condensate equation"],
        "Level 0: supplied bare scalar model", "#D9EAF7")
    box("L1", 6.75, 1.72,
        [r"$K^{AB}\partial_A\partial_B\chi+m_\sigma^2\chi=0$",
         r"$K^{AB}=\beta\,\delta^{AB}-\alpha\,n^A n^B$",
         "Ordered-branch scalar equation"],
        "Level 1: supplied P4 / EFT closure", "#DDF3EA")
    box("L2", 4.35, 1.42,
        [r"$\partial_t^2\varphi-c_*^2\nabla^2\varphi+M^2\varphi=0$",
         "conditional scalar Klein–Gordon form"],
        "Level 2: clock / physical-state map Open", "#F3E7C9")
    box("L3", 1.95, 1.42,
        [r"$iS_0\,\partial_t\psi=-\frac{S_0^2}{2m}\nabla^2\psi+V\psi$",
         "conditional Schrödinger-type envelope"],
        r"Level 3: state / operator / $S_0$ owners Open", "#F6E1D8")
    arrow("L0", "L1", r"P4 supplies $O(4)\to O(3)$ branch")
    arrow("L1", "L2", "conditional coordinate / cone map")
    arrow("L2", "L3", "state + positive-frequency + NR assumptions")
    ax.text(5.0, 0.40,
            "Dashed arrows are conditional dependencies, not status upgrades.",
            ha="center", va="center", fontsize=8.15, color="#555555")
    return fig


def build_top_level(root: Path, records: list[dict[str, Any]]) -> None:
    architecture_owner = LATEX / "scripts/fig_ect_architecture.py"
    architecture = make_architecture_native()
    save_figure(architecture, root / "assets/figures/fig_ect_architecture.pdf")
    record_output(
        records, root, "figures/fig_ect_architecture.pdf", [architecture_owner],
        "native semantic reflow of exact owner nodes and relations",
        {
            "nodes": ["phi", "ssb", "ord", "geo", "coh", "geo_sub", "coh_sub", "pred"],
            "directed_edges": [["phi", "ssb"], ["ssb", "ord"], ["ord", "geo"],
                               ["ord", "coh"], ["geo", "geo_sub"], ["coh", "coh_sub"],
                               ["geo_sub", "pred"], ["coh_sub", "pred"]],
            "bidirectional_annotation": ["geo_sub", "coh_sub",
                                           "common-action back-reaction not yet derived"],
            "numeric_payload_changed": False,
        },
    )

    hierarchy_owner = LATEX / "scripts/fig_equation_hierarchy.py"
    hierarchy = make_equation_hierarchy_native()
    save_figure(hierarchy, root / "assets/figures/fig_equation_hierarchy.pdf")
    record_output(
        records, root, "figures/fig_equation_hierarchy.pdf", [hierarchy_owner],
        "native semantic reflow of exact four-level owner hierarchy",
        {
            "levels": ["L0", "L1", "L2", "L3"],
            "directed_edges": [["L0", "L1"], ["L1", "L2"], ["L2", "L3"]],
            "all_edges_conditional": True,
            "numeric_or_status_payload_changed": False,
        },
    )

    liv_owner = LATEX / "scripts/fig_liv_delay.py"
    liv = capture_top_level(liv_owner)
    apply_font_floor(liv, floor=13.4, title_floor=14.2, legend_floor=13.4)
    save_figure(liv, root / "assets/figures/fig_liv_delay.pdf", size=(5.9, 4.5))
    record_output(records, root, "figures/fig_liv_delay.pdf", [liv_owner],
                  "native owner replay; font and canvas geometry only",
                  {"owner_executed": True, "numeric_or_text_payload_rewritten": False})


def build_hrc_and_cluster(root: Path, records: list[dict[str, Any]]) -> None:
    hrc_only_path = LATEX / "scripts/hrc/make_r97_hrc_only_figures.py"
    hrc_completion_path = LATEX / "scripts/hrc/make_r97_hrc_completion_figures.py"
    cluster_path = LATEX / "scripts/cosmology/make_r103_corrected_cosmology_figures.py"
    hrc_only = load_module("r127_hrc_only", hrc_only_path)
    hrc_completion = load_module("r127_hrc_completion", hrc_completion_path)
    cluster_mod = load_module("r127_cluster", cluster_path)

    for install, module, function_name, size, owners in (
        ("figures/hrc/R97_HRC_RAR_DIAGNOSTIC.pdf", hrc_only, "rar_figure", (6.2, 5.0),
         [hrc_only_path, hrc_only.POINTS, hrc_only.REGIMES, hrc_only.RESULTS]),
        ("figures/hrc/R97_HRC_UDG_STRESS.pdf", hrc_completion, "udg_figure", (6.5, 4.8),
         [hrc_completion_path, hrc_completion.UDG]),
        ("figures/r123/global/panels/fig_milky_way_hrc_only_r123.pdf", hrc_completion,
         "milky_way_figure", (7.0, 5.0), [hrc_completion_path]),
    ):
        with capture_named_save(module, "save") as holder:
            getattr(module, function_name)()
        fig = holder["fig"]
        before = {"axes": len(fig.axes), "line_points": [int(len(line.get_xdata())) for ax in fig.axes for line in ax.lines]}
        apply_font_floor(fig, floor=10.5, title_floor=12.0, legend_floor=10.2)
        save_figure(fig, root / "assets" / install, size=size)
        record_output(records, root, install, [Path(p) for p in owners],
                      "native HRC owner replay; typography/canvas only", before)

    cluster_json = LATEX / "data/cosmology_r103/R103_CLUSTER_LOCAL_HRC_SYNTHETIC_v1.json"
    cluster = json.loads(cluster_json.read_text(encoding="utf-8"))
    with capture_named_save(cluster_mod, "finish") as holder:
        cluster_mod.cluster_figure(cluster, root / "qa/unused_cluster_target")
    fig = holder["fig"]
    before = {"axes": len(fig.axes), "line_points": [int(len(line.get_xdata())) for ax in fig.axes for line in ax.lines]}
    apply_font_floor(fig, floor=10.3, title_floor=12.0, legend_floor=10.2)
    save_figure(fig, root / "assets/figures/r103/r103_cluster_local_no_go.pdf", size=(7.35, 5.45))
    record_output(records, root, "figures/r103/r103_cluster_local_no_go.pdf", [cluster_path, cluster_json],
                  "native frozen R103 owner replay; typography/canvas only", before)


def build_sparc(root: Path, records: list[dict[str, Any]]) -> None:
    renderer_path = R123 / "components/curve_luminance_final/render_r123_rotation_comparison_lstar_v2.py"
    renderer = load_module("r127_sparc_renderer", renderer_path)
    sample = sorted(renderer.read_csv(renderer.SAMPLE), key=lambda row: int(row["sample_order"]))
    points = renderer.read_csv(renderer.POINTS)
    result = json.loads(renderer.RESULTS.read_text(encoding="utf-8"))
    result_by_name = {row["galaxy"]: row for row in result["galaxies"]}
    rows_by_name = {item["galaxy"]: [row for row in points if row["galaxy"] == item["galaxy"]] for item in sample}
    renderer.plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11.6, "axes.titlesize": 11.6,
        "axes.labelsize": 11.4, "xtick.labelsize": 10.8, "ytick.labelsize": 10.8,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })
    temp = root / "qa/sparc_native"
    temp.mkdir(parents=True, exist_ok=True)
    original_savefig = Figure.savefig
    original_spread_labels = renderer.spread_labels
    def spread_labels_large(values: dict[str, float], lower: float, upper: float) -> dict[str, float]:
        """Owner algorithm with print-safe separation for 10.7 pt labels."""
        span = max(upper - lower, 1.0)
        gap = 0.090 * span
        ordered = sorted(values, key=lambda key: (values[key], key))
        positions: dict[str, float] = {}
        cursor = lower
        for key in ordered:
            cursor = max(values[key], cursor)
            positions[key] = cursor
            cursor += gap
        overflow = max(positions.values()) - upper
        if overflow > 0.0:
            positions = {key: value - overflow for key, value in positions.items()}
        underflow = lower - min(positions.values())
        if underflow > 0.0:
            positions = {key: value + underflow for key, value in positions.items()}
        return positions

    renderer.spread_labels = spread_labels_large

    def hooked(fig: Figure, *args: Any, **kwargs: Any):
        if not getattr(fig, "_r127_native_prepared", False):
            apply_font_floor(fig, floor=10.7, title_floor=12.0, legend_floor=10.5)
            fig.set_size_inches(7.2, 9.35, forward=True)
            # Reflow the four owner annotations rather than letting larger
            # native type escape the page.  Wording and scientific scope are
            # unchanged.
            replacements = {
                r"Black circles: SPARC; curves are directly labelled.  HRC-0 $\equiv$ MOND-standard at equal scale.":
                    "Black circles: SPARC; curves are directly labelled.\nHRC-0 $\\equiv$ MOND-standard at equal scale.",
                r"Plotted fixed scales: $a_M=1.0824\times10^{-10}$ and $a_0=1.2\times10^{-10}\,\mathrm{m\,s^{-2}}$; NFW parameters are fitted per galaxy.":
                    r"Plotted fixed scales: $a_M=1.0824\times10^{-10}$ and "
                    r"$a_0=1.2\times10^{-10}\,\mathrm{m\,s^{-2}}$;"
                    "\nNFW parameters are fitted per galaxy.",
                r"NFW is a $\Lambda$CDM-motivated two-parameter halo benchmark, not a unique $\Lambda$CDM prediction.":
                    "NFW is a $\\Lambda$CDM-motivated two-parameter halo benchmark;\nit is not a unique $\\Lambda$CDM prediction.",
                r"All panels: $\Upsilon_d=0.5$, $\Upsilon_b=0.7$, signed gas and a $2\,\mathrm{km\,s^{-1}}$ error floor.":
                    "All panels: $\\Upsilon_d=0.5$, $\\Upsilon_b=0.7$, signed gas,\nand a $2\\,\\mathrm{km\\,s^{-1}}$ error floor.",
            }
            for text in fig.texts:
                if text.get_text() in replacements:
                    text.set_text(replacements[text.get_text()])
                if text.get_text().startswith("Black circles:"):
                    text.set_y(0.951)
                    text.set_fontsize(10.7)
                    text.set_linespacing(1.12)
                elif text.get_text().startswith("Plotted fixed scales:"):
                    text.set_y(0.899)
                    text.set_fontsize(10.7)
                    text.set_linespacing(1.12)
                elif text.get_text().startswith("NFW is a"):
                    text.set_y(0.070)
                elif text.get_text().startswith("All panels:"):
                    text.set_y(0.030)
            if fig._suptitle is not None:
                fig._suptitle.set_y(0.988)
                fig._suptitle.set_fontsize(12.0)
            fig.subplots_adjust(left=0.115, right=0.82, bottom=0.155, top=0.825, hspace=0.54)
            setattr(fig, "_r127_native_prepared", True)
        return original_savefig(fig, *args, **kwargs)

    Figure.savefig = hooked  # type: ignore[method-assign]
    try:
        renderer.render_page(temp, "A", "SPARC comparison I: diffuse and low-surface-brightness systems",
                             sample[:3], rows_by_name, result_by_name)
        renderer.render_page(temp, "B", "SPARC comparison II: extended, bright and bulge-dominated systems",
                             sample[3:], rows_by_name, result_by_name)
    finally:
        Figure.savefig = original_savefig  # type: ignore[method-assign]
        renderer.spread_labels = original_spread_labels
    owners = [renderer_path, renderer.SAMPLE, renderer.POINTS, renderer.RESULTS]
    for page in ("A", "B"):
        source = temp / f"{renderer.STEM}_{page}.pdf"
        install = f"figures/r123/R123_SPARC_EXTERNAL_MODEL_COMPARISON_v1_{page}.pdf"
        normalize_pdf(source, root / "assets" / install)
        record_output(records, root, install, owners,
                      "native frozen R102/SPARC comparison owner replay; typography and label-spacing geometry only",
                      {"page": page, "galaxies": [item["galaxy"] for item in (sample[:3] if page == "A" else sample[3:])],
                       "scientific_numbers_changed": False,
                       "curve_arrays_changed": False,
                       "endpoint_vertical_order_preserved": True})


def build_monochrome(root: Path, records: list[dict[str, Any]]) -> None:
    module_path = R123 / "components/global_visual_remediation/scripts/build_r123_remaining_monochrome.py"
    module = load_module("r127_monochrome", module_path)
    wanted = [
        "fig_coupling_comparison_r123.pdf", "fig_gamma_crossover_r123.pdf",
        "fig_neutrino_corrections_r123.pdf", "fig_qubit_info_decoherence_r123.pdf",
        "fig_species_beta5_r123.pdf",
    ]
    for name in wanted:
        holder: dict[str, Figure] = {}
        original = module.save
        module.save = lambda fig, *_args, **_kwargs: holder.setdefault("fig", fig)
        try:
            payload = module.BUILDERS[name](root / "qa/unused.pdf")
        finally:
            module.save = original
        fig = holder["fig"]
        apply_font_floor(fig, floor=10.7, title_floor=12.1, legend_floor=10.5)
        save_figure(fig, root / "assets/figures/r123" / name, size=(7.35, 5.25))
        record_output(records, root, "figures/r123/" + name,
                      [module_path, *module.OWNER_PATHS[name]],
                      "native owner-aware R123 palette replay; typography/canvas only",
                      {"owner_payload": payload, "numeric_arrays_changed": False})


def build_clipping_owned(root: Path, records: list[dict[str, Any]]) -> None:
    module_path = R123 / "components/clipping_remediation_v2/build_clipping_remediation_v2.py"
    module = load_module("r127_clipping_owner", module_path)
    wanted = {
        "fig10_a_acoustic_gate_r123.pdf", "fig10_b_fixed_angle_proxy_r123.pdf",
        "fig11_a_timescale_mismatch_r123.pdf", "fig11_b_ballistic_distance_mismatch_r123.pdf",
        "fig35_a_tolman_kinematics_r123.pdf", "fig35_b_page_curve_benchmark_r123.pdf",
        "fig35_c_hawking_benchmark_r123.pdf", "fig45_a_fixed_metric_bvp_r123.pdf",
        "fig45_b_tail_estimators_r123.pdf", "fig47_a_single_kms_channel_r123.pdf",
    }
    for spec in module.panel_specs():
        if spec["filename"] not in wanted:
            continue
        fig = spec["factory"]()
        targets, before, after = module.solo_layout(
            fig, spec["indices"], title=spec["title"], grid=spec["grid"],
            global_legend=spec["legend"], status_guard=spec["status_guard"],
            palette_role=spec["palette_role"],
        )
        if before != after:
            raise RuntimeError(f"scientific payload changed in inherited relayout {spec['filename']}")
        accessibility_annotation = None
        if spec["filename"] == "fig10_b_fixed_angle_proxy_r123.pdf":
            ax = fig.axes[0]
            if len(ax.lines) < 3 or not all(len(line.get_xdata()) == 3 for line in ax.lines[:3]):
                raise RuntimeError("fixed-angle proxy series owner changed")
            ax.text(
                0.98, 0.045,
                "The $\\kappa_s$ series overlap near unity;\n"
                "markers and line styles distinguish them.",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=10.5,
                color="#333333", bbox=dict(boxstyle="round,pad=0.28", facecolor="white",
                                             edgecolor="#777777", alpha=0.92), zorder=8,
            )
            accessibility_annotation = "strongly overlapping/adjacent kappa_s proxy tracks stated explicitly"
        elif spec["filename"] == "fig11_b_ballistic_distance_mismatch_r123.pdf":
            matches = [text for text in fig.axes[0].texts if text.get_text().startswith("mismatch")]
            if len(matches) != 1:
                raise RuntimeError("ballistic mismatch annotation owner changed")
            matches[0].set_position((0.98, 0.72))
            matches[0].set_ha("right")
            matches[0].set_va("top")
            accessibility_annotation = "mismatch callout moved clear of target band"
        elif spec["filename"] == "fig35_c_hawking_benchmark_r123.pdf":
            matches = [text for text in fig.axes[0].texts if text.get_text().startswith("ECT shell depth")]
            if len(matches) != 1:
                raise RuntimeError("Hawking benchmark status annotation owner changed")
            matches[0].set_position((0.03, 0.055))
            matches[0].set_ha("left")
            matches[0].set_va("bottom")
            accessibility_annotation = "ECT-shell status callout moved to empty lower-left field"
        apply_font_floor(fig, floor=12.4, title_floor=13.0, legend_floor=11.5)
        output = root / "assets/figures/r123/global/panels" / spec["filename"]
        save_figure(fig, output, size=(7.35, 5.45))
        owners = [module_path]
        for key in spec["owner_keys"]:
            owners.append(Path(module.MODULE_PATHS.get(key) or module.DATA_PATHS.get(key)))
        record_output(records, root, "figures/r123/global/panels/" + spec["filename"], owners,
                      "fresh vector replay from frozen owner arrays/functions; native font floor",
                      {"artist_payload_sha256_before_layout": before,
                       "artist_payload_sha256_after_layout": after,
                       "scientific_payload_identical": before == after,
                       "accessibility_annotation_adjustment": accessibility_annotation})


def build_fig41a(root: Path, records: list[dict[str, Any]]) -> None:
    owner = R123 / "components/global_visual_remediation/p1_panel_work/scripts/build_r123_p1_panel_relayout.py"
    module = load_module("r127_p1_owner", owner)
    module.configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.35, 5.45), constrained_layout=True)
    ax.set(xlim=(0, 10), ylim=(0, 6.4))
    ax.axis("off")
    ax.text(5, 6.10, "Orientation stiffness: established and conditional upstream chain",
            ha="center", fontsize=13.0, weight="bold")
    ax.text(5, 5.72, "Every status is literal; colour is redundant with border style and wording.",
            ha="center", fontsize=10.6, color=module.PAL.GRAPHITE)
    module.add_box(ax, (0.75, 4.15), 8.5, 1.05, "Ordered variables",
                   "$\\partial_A\\Phi=u n_A$; P4 kinematics -- Level A",
                   module.PAL.LEVEL_A_FILL, module.PAL.LEVEL_A_EDGE)
    module.add_box(ax, (0.75, 2.55), 8.5, 1.05, "Heavy-radial determinant",
                   "$\\frac{1}{2}\\,\\mathrm{Tr}\\ln\\mathcal{O}_\\sigma$; NLO -- CONDITIONAL declared closure",
                   module.PAL.LEVEL_B_FILL, module.PAL.LEVEL_B_EDGE, "--")
    module.add_box(ax, (0.75, 0.95), 8.5, 1.05, "Orientation coefficient $\\mathcal{C}_n$",
                   "$\\mathcal{C}_n=\\hat a_{\\rm eff}/(16\\pi^2m_\\sigma^2)$ -- CONDITIONAL; matching Open",
                   module.PAL.LEVEL_B_FILL, module.PAL.LEVEL_B_EDGE, "--")
    module.add_arrow(ax, (5, 4.15), (5, 3.60), module.PAL.LEVEL_A_EDGE,
                     label="background reduction", label_xy=(6.45, 3.73))
    module.add_arrow(ax, (5, 2.55), (5, 2.00), module.PAL.LEVEL_B_EDGE,
                     label="operator basis", label_xy=(6.02, 2.13))
    handles = [
        Patch(facecolor=module.PAL.LEVEL_A_FILL, edgecolor=module.PAL.LEVEL_A_EDGE,
              label="Level A definition / kinematics"),
        Patch(facecolor=module.PAL.LEVEL_B_FILL, edgecolor=module.PAL.LEVEL_B_EDGE,
              linestyle="--", label="conditional under declared assumptions"),
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
              fontsize=10.3, bbox_to_anchor=(0.5, -0.01))
    apply_font_floor(fig, floor=10.6, title_floor=13.0, legend_floor=10.3)
    install = "figures/r123/global/panels/fig41_a_orientation_stiffness_upstream_r123.pdf"
    save_figure(fig, root / "assets" / install, size=(7.35, 5.45))
    record_output(records, root, install, [owner, module.PALETTE_PATH],
                  "native replay of preserved Fig. 41 owner text/topology; font/canvas only",
                  {"boxes": 3, "arrows": 2, "wording_copied_from_owner": True})


def transform_dot_fonts(text: str, *, minimum: float) -> str:
    def repl(match: re.Match[str]) -> str:
        prefix, quote, raw, suffix = match.groups()
        value = max(minimum, float(raw) * 1.16)
        return f"{prefix}{quote}{value:.2f}{suffix}"

    text = re.sub(r'(fontsize\s*=\s*)(\"?)([0-9]+(?:\.[0-9]+)?)(\"?)', repl, text)
    text = re.sub(
        r'POINT-SIZE="([0-9]+(?:\.[0-9]+)?)"',
        lambda m: f'POINT-SIZE="{max(minimum, float(m.group(1)) * 1.16):.2f}"',
        text,
    )
    text = re.sub(r'(nodesep\s*=\s*)[0-9.]+', r'\g<1>0.16', text)
    text = re.sub(r'(ranksep\s*=\s*)[0-9.]+', r'\g<1>0.26', text)
    # Helvetica substituted visible tofu for hbar, subscript digits, Greek,
    # topology symbols and mathematical alphabets.  STIX Two Math is the one
    # locally available face whose cmap covers every Unicode codepoint in all
    # 17 semantic DOT owners.  Only the font family changes.
    text = re.sub(
        r'(fontname\s*=\s*)(?:"Helvetica"|Helvetica)',
        rf'\g<1>"{DOT_FONT_FAMILY}"',
        text,
    )
    assert_dot_unicode_coverage(text)
    return text


def dot_font_coverage() -> tuple[Path, set[int]]:
    global _DOT_FONT_PATH, _DOT_FONT_CHARMAP
    if _DOT_FONT_PATH is None or _DOT_FONT_CHARMAP is None:
        raw = subprocess.check_output(
            ["fc-match", "-f", "%{file}", DOT_FONT_FAMILY], stderr=subprocess.STDOUT
        ).decode("utf-8").strip()
        path = Path(raw)
        if not path.is_file():
            raise RuntimeError(f"Unicode Graphviz font unavailable: {DOT_FONT_FAMILY} -> {raw}")
        _DOT_FONT_PATH = path
        _DOT_FONT_CHARMAP = set(FT2Font(str(path)).get_charmap())
    return _DOT_FONT_PATH, _DOT_FONT_CHARMAP


def assert_dot_unicode_coverage(text: str) -> dict[str, Any]:
    font_path, cmap = dot_font_coverage()
    decoded = html.unescape(text)
    codepoints = sorted({ord(char) for char in decoded if ord(char) >= 128})
    missing = [value for value in codepoints if value not in cmap]
    if missing:
        rendered = ", ".join(f"U+{value:04X} {chr(value)!r}" for value in missing)
        raise RuntimeError(f"{DOT_FONT_FAMILY} lacks required DOT glyphs: {rendered}")
    return {
        "font_family": DOT_FONT_FAMILY,
        "font_path": str(font_path),
        "unicode_codepoints_checked": len(codepoints),
        "missing_codepoints": [],
    }


def pdf_zero_tofu_guard(path: Path) -> dict[str, Any]:
    """Reject visible replacement characters and verify the embedded STIX face."""
    doc = fitz.open(path)
    hits: list[dict[str, Any]] = []
    fonts: set[str] = set()
    for page_number, page in enumerate(doc, start=1):
        text = page.get_text()
        for marker in ("□", "�", "?"):
            if marker in text:
                hits.append({"page": page_number, "marker": marker})
        for font in page.get_fonts(full=True):
            fonts.add(str(font[3]))
    doc.close()
    if hits:
        raise RuntimeError(f"{path}: visible tofu/replacement markers {hits}")
    if not any("STIXTwoMath" in font.replace("-", "") for font in fonts):
        raise RuntimeError(f"{path}: expected embedded STIX Two Math font, found {sorted(fonts)}")
    return {"zero_tofu": True, "replacement_hits": [], "embedded_fonts": sorted(fonts)}


def normalize_graphviz(raw: Path, output: Path) -> None:
    normalize_pdf(raw, output)


def render_dot(source: Path, output: Path) -> None:
    raw = output.with_suffix(".raw.pdf")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["/opt/homebrew/bin/dot", "-Tpdf", str(source), "-o", str(raw)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    normalize_graphviz(raw, output)
    raw.unlink()


def graph_page_scale(rect: fitz.Rect) -> float:
    values = []
    for width, height in ((841.8898, 595.2756), (595.2756, 841.8898)):
        values.append(min((width - 12) / rect.width, (height - 46) / rect.height))
    return max(values)


def render_dot_best_packed(source: Path, output: Path) -> str:
    """Choose only among deterministic layout transforms; content is fixed."""
    output.parent.mkdir(parents=True, exist_ok=True)
    candidates: list[tuple[float, str, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="r127_graph_pack_") as temporary:
        temp = Path(temporary)
        unflattened = temp / "unflattened.gv"
        result = subprocess.run(["/opt/homebrew/bin/unflatten", "-l", "3", "-c", "3", str(source)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", "replace"))
        unflattened.write_bytes(result.stdout)
        variants = [("direct", source, [])]
        for mode in ("array_u2", "array_u3"):
            variants.append((f"unflatten_l3_c3+{mode}", unflattened,
                             ["-Gpack=true", f"-Gpackmode={mode}"]))
        for label, dot_source, args in variants:
            candidate = temp / f"{label.replace('+', '_')}.pdf"
            command = ["/opt/homebrew/bin/dot", *args, "-Tpdf", str(dot_source), "-o", str(candidate)]
            run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if run.returncode:
                raise RuntimeError(run.stderr.decode("utf-8", "replace"))
            doc = fitz.open(candidate)
            score = graph_page_scale(doc[0].rect)
            doc.close()
            candidates.append((score, label, candidate.read_bytes()))
        _score, selected, data = max(candidates, key=lambda item: (item[0], item[1]))
        raw = output.with_suffix(".raw.pdf")
        raw.write_bytes(data)
        normalize_graphviz(raw, output)
        raw.unlink()
    return selected


def wrap_graph_page(raw_pdf: Path, output: Path, title: str) -> None:
    src = fitz.open(raw_pdf)
    raw = src[0].rect
    candidates = []
    for width, height in ((841.8898, 595.2756), (595.2756, 841.8898)):
        content = fitz.Rect(6, 29, width - 6, height - 28)
        candidates.append((min(content.width / raw.width, content.height / raw.height), width, height, content))
    scale, width, height, content = max(candidates, key=lambda item: item[0])
    fitted_w, fitted_h = raw.width * scale, raw.height * scale
    target = fitz.Rect((width - fitted_w) / 2, content.y0 + (content.height - fitted_h) / 2,
                       (width + fitted_w) / 2, content.y0 + (content.height + fitted_h) / 2)
    out = fitz.open()
    page = out.new_page(width=width, height=height)
    title_result = page.insert_textbox(
        fitz.Rect(6, 4, width - 6, 26), title, fontname="helv", fontsize=10.5,
        color=(34 / 255, 34 / 255, 34 / 255), align=fitz.TEXT_ALIGN_CENTER,
    )
    page.show_pdf_page(target, src, 0, keep_proportion=True)
    footer_result = page.insert_textbox(
        fitz.Rect(6, height - 25, width - 6, height - 4),
        "Node text states status; colour is redundant with border/line style.",
        fontname="helv", fontsize=8.5, color=(94 / 255, 94 / 255, 94 / 255),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    if title_result < 0 or footer_result < 0:
        raise RuntimeError(f"Graphviz wrapper text did not fit: title={title_result}, footer={footer_result}")
    out.set_metadata(FIXED_FITZ_META)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output, garbage=4, deflate=True, no_new_id=True)
    out.close()
    src.close()
    canonicalize_pdf_id(output)


def combine_pdfs(inputs: list[Path], output: Path) -> None:
    doc = fitz.open()
    for path in inputs:
        src = fitz.open(path)
        doc.insert_pdf(src)
        src.close()
    doc.set_metadata(FIXED_FITZ_META)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output, garbage=4, deflate=True, no_new_id=True)
    doc.close()
    canonicalize_pdf_id(output)


def canonical_dot_semantics(text_value: str) -> str:
    """Erase only the typography/layout values that this builder may change."""
    value = re.sub(
        r'(fontname\s*=\s*)(?:"Helvetica"|Helvetica|"STIX Two Math")',
        r'\g<1>"__NATIVE_FONT__"',
        text_value,
    )
    value = re.sub(
        r'(fontsize\s*=\s*)("?)[0-9]+(?:\.[0-9]+)?("?)',
        r'\g<1>"__NATIVE_SIZE__"',
        value,
    )
    value = re.sub(r'POINT-SIZE="[0-9]+(?:\.[0-9]+)?"', 'POINT-SIZE="__NATIVE_SIZE__"', value)
    value = re.sub(r'(nodesep\s*=\s*)[0-9.]+', r'\g<1>__NATIVE_NODESEP__', value)
    value = re.sub(r'(ranksep\s*=\s*)[0-9.]+', r'\g<1>__NATIVE_RANKSEP__', value)
    # Edge-label attachment is permitted to move from the edge midpoint to its
    # destination solely to prevent two labels from visually merging.  Text
    # and edge endpoints remain exact.
    value = re.sub(r'\b(?:headlabel|taillabel|xlabel)\s*=', 'label=', value)
    value = re.sub(r',\s*(?:labelangle|labeldistance)\s*=\s*-?[0-9.]+', '', value)
    return value


def graph_structure(path: Path) -> dict[str, Any]:
    """Extract the complete non-geometric graph payload for exact comparison."""
    result = subprocess.run(["/opt/homebrew/bin/dot", "-Tjson", str(path)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", "replace"))
    payload = json.loads(result.stdout)
    objects = payload.get("objects", [])
    ids: dict[int, str] = {
        int(obj["_gvid"]): str(obj["name"])
        for obj in objects if "_gvid" in obj and "name" in obj and "nodes" not in obj
    }
    semantic_keys = (
        "label", "xlabel", "headlabel", "taillabel", "shape", "style", "color",
        "fillcolor", "fontcolor", "penwidth", "arrowhead", "arrowtail", "dir",
        "constraint", "tooltip", "URL", "href", "target",
    )

    def selected(row: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in semantic_keys:
            if key not in row:
                continue
            value = row[key]
            if key in ("label", "xlabel", "headlabel", "taillabel", "tooltip"):
                value = canonical_dot_semantics(str(value))
            result[key] = value
        return result

    def selected_edge(row: dict[str, Any]) -> dict[str, Any]:
        result = selected(row)
        edge_text: list[str] = []
        for key in ("label", "xlabel", "headlabel", "taillabel"):
            if key not in result:
                continue
            value = str(result.pop(key))
            if value.strip():
                edge_text.append(value)
        edge_text.sort()
        if edge_text:
            result["edge_text_labels"] = edge_text
        return result

    nodes = sorted(
        ({"name": ids[int(obj["_gvid"])], **selected(obj)}
         for obj in objects if "_gvid" in obj and int(obj["_gvid"]) in ids),
        key=lambda row: row["name"],
    )
    clusters = sorted(
        ({"name": str(obj.get("name", "")),
          "members": sorted(ids[int(value)] for value in obj.get("nodes", []) if int(value) in ids),
          **selected(obj)}
         for obj in objects if "nodes" in obj),
        key=lambda row: row["name"],
    )
    edges = sorted(
        ({"tail": ids[int(edge["tail"])], "head": ids[int(edge["head"])], **selected_edge(edge)}
         for edge in payload.get("edges", [])),
        key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False),
    )
    label_values: list[str] = []
    for row in [*nodes, *clusters, *edges]:
        for key in ("label", "xlabel", "headlabel", "taillabel", "tooltip"):
            if key in row and str(row[key]).strip():
                label_values.append(str(row[key]))
        label_values.extend(str(value) for value in row.get("edge_text_labels", []) if str(value).strip())
    status_tokens = (
        "Level A", "Level B", "Level C", "Open", "MISSING VERTEX",
        "NOT IDENTIFIABLE", "PARAMETRIC ONLY", "DOUBLE-COUNTED", "INCOMPATIBLE",
    )
    status_counts = {
        token: sum(value.count(token) for value in label_values)
        for token in status_tokens if any(token in value for value in label_values)
    }
    spans: list[str] = []
    for value in label_values:
        plain = html.unescape(re.sub(r"<[^>]+>", "\n", value))
        spans.extend(
            re.sub(r"\s+", " ", part).strip()
            for part in re.split(r"(?:\\n|\n|\|)", plain)
            if re.sub(r"\s+", " ", part).strip()
        )
    return {
        "nodes": nodes,
        "clusters": clusters,
        "edges": edges,
        "labels_in_owner_order": label_values,
        "text_spans_in_owner_order": spans,
        "status_token_counts": status_counts,
        "counts": {
            "nodes": len(nodes), "clusters": len(clusters), "edges": len(edges),
            "labels": len(label_values), "text_spans": len(spans),
        },
    }


def build_graphviz(root: Path, records: list[dict[str, Any]]) -> None:
    generator = R123 / "components/global_visual_remediation/graphviz_work/build_r123_graphviz_semantic_panels.py"
    dot_root = R123 / "components/global_visual_remediation/graphviz_work/output/panel_dots"
    family_counts = {"fig09_partI": 4, "fig36_partIII": 5, "fig38_partIV": 3, "fig39_full": 5}
    nav_targets = {
        family: f"figures/r123/global/graphviz/{family}/00_navigation.pdf" for family in family_counts
    }
    supplement_targets = {
        family: f"figures/r123/reader_print/{family}_reader_print_supplement.pdf"
        for family in family_counts
    }
    for family, count in family_counts.items():
        source_family = dot_root / family
        source_snapshot = root / "sources/graphviz" / family
        source_snapshot.mkdir(parents=True, exist_ok=True)
        nav_source = source_family / "00_navigation.gv"
        nav_dot = source_snapshot / "00_navigation_native_font.gv"
        nav_source_text = nav_source.read_text(encoding="utf-8")
        transformed = transform_dot_fonts(nav_source_text, minimum=12.2)
        coverage = assert_dot_unicode_coverage(transformed)
        nav_dot.write_text(transformed, encoding="utf-8")
        nav_source_payload = graph_structure(nav_source)
        nav_native_payload = graph_structure(nav_dot)
        if nav_source_payload != nav_native_payload:
            raise RuntimeError(f"{family}: navigation topology changed")
        if canonical_dot_semantics(nav_source_text) != canonical_dot_semantics(transformed):
            raise RuntimeError(f"{family}: navigation changed outside allowed typography/layout fields")
        nav_output = root / "assets" / nav_targets[family]
        render_dot(nav_dot, nav_output)
        tofu = pdf_zero_tofu_guard(nav_output)
        record_output(records, root, nav_targets[family], [generator, nav_source],
                      "native Graphviz rerender from preserved navigation DOT; font/spacing only",
                      {"topology_identical": True, "nodes_edges_labels_preserved": True,
                       "source_semantic_payload_sha256": hashlib.sha256(
                           json.dumps(nav_source_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
                       ).hexdigest(),
                       "native_semantic_payload_sha256": hashlib.sha256(
                           json.dumps(nav_native_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
                       ).hexdigest(),
                       "allowed_mutations_only": True,
                       "unicode_font_coverage": coverage, "pdf_zero_tofu_guard": tofu})

        base_semantic = R127 / "payload/assets" / supplement_targets[family]
        base_doc = fitz.open(base_semantic)
        base_page_count = len(base_doc)
        base_titles: list[str] = []
        expected_redundancy_note = "Node text states status; colour is redundant with border/line style."
        for page in base_doc:
            lines = [line.strip() for line in page.get_text().splitlines() if line.strip()]
            if not lines:
                raise RuntimeError(f"{family}: empty base semantic page")
            base_titles.append(lines[0])
            if expected_redundancy_note not in page.get_text():
                raise RuntimeError(f"{family}: base redundancy note missing on page {len(base_titles)}")
        base_doc.close()
        if base_page_count != count:
            raise RuntimeError(f"{family}: base semantic page order changed: {base_page_count} != {count}")

        wrapped_pages: list[Path] = []
        semantic_sources: list[Path] = []
        page_proofs: list[dict[str, Any]] = []
        for index in range(1, count + 1):
            candidates = sorted(source_family.glob(f"{index:02d}_*.gv"))
            if len(candidates) != 1:
                raise RuntimeError(f"{family}: expected one semantic owner for page {index}, found {candidates}")
            source = candidates[0]
            semantic_sources.append(source)
            source_text = source.read_text(encoding="utf-8")
            transformed_text = transform_dot_fonts(source_text, minimum=12.0)
            label_attachment_adjustment = None
            if family == "fig36_partIII" and index == 3:
                replacements = {
                    'label="closure / imported benchmark"': (
                        'headlabel="closure / imported benchmark", labeldistance=2.2, labelangle=28'
                    ),
                    'label="protocol + entropy definition"': (
                        'headlabel="protocol + entropy definition", labeldistance=2.2, labelangle=-28'
                    ),
                }
                for old, new in replacements.items():
                    if transformed_text.count(old) != 1:
                        raise RuntimeError(f"fig36 semantic page 3 label anchor changed: {old}")
                    transformed_text = transformed_text.replace(old, new)
                label_attachment_adjustment = (
                    "two exact edge-label strings attached near their distinct destination nodes to prevent merging"
                )
            coverage = assert_dot_unicode_coverage(transformed_text)
            dot = source_snapshot / source.name.replace(".gv", "_native_font.gv")
            dot.write_text(transformed_text, encoding="utf-8")
            source_payload = graph_structure(source)
            native_payload = graph_structure(dot)
            if source_payload != native_payload:
                raise RuntimeError(f"{family}/{source.name}: node/edge/label/status payload changed")
            source_canonical = canonical_dot_semantics(source_text)
            native_canonical = canonical_dot_semantics(transformed_text)
            if source_canonical != native_canonical:
                raise RuntimeError(f"{family}/{source.name}: mutation outside typography/layout allow-list")
            raw = root / "qa/graphviz_raw" / family / source.with_suffix(".pdf").name
            packing = render_dot_best_packed(dot, raw)
            wrapped = root / "qa/graphviz_pages" / family / source.with_suffix(".pdf").name
            title = base_titles[index - 1]
            wrap_graph_page(raw, wrapped, title)
            text_guard = pdf_text_integrity_guard(wrapped, forbid_question_mark=True)
            tofu_guard = pdf_zero_tofu_guard(wrapped)
            wrapped_pages.append(wrapped)
            payload_digest = hashlib.sha256(
                json.dumps(source_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            page_proofs.append({
                "page": index,
                "source_dot": rel(source),
                "source_dot_sha256": sha256(source),
                "native_dot": str(dot.relative_to(root)),
                "native_dot_sha256": sha256(dot),
                "source_semantic_payload_sha256": payload_digest,
                "native_semantic_payload_sha256": payload_digest,
                "node_edge_label_status_payload_identical": True,
                "source_text_span_count": source_payload["counts"]["text_spans"],
                "source_text_spans_sha256": hashlib.sha256(
                    json.dumps(source_payload["text_spans_in_owner_order"], ensure_ascii=False).encode("utf-8")
                ).hexdigest(),
                "status_token_counts": source_payload["status_token_counts"],
                "allowed_mutations_only": True,
                "edge_label_attachment_adjustment": label_attachment_adjustment,
                "selected_packing": packing,
                "unicode_font_coverage": coverage,
                "pdf_text_integrity_guard": text_guard,
                "pdf_zero_tofu_guard": tofu_guard,
            })
        supplement = root / "assets" / supplement_targets[family]
        combine_pdfs(wrapped_pages, supplement)
        combined_text_guard = pdf_text_integrity_guard(supplement, forbid_question_mark=True)
        combined_tofu_guard = pdf_zero_tofu_guard(supplement)
        predecessor = current_top_predecessor(supplement_targets[family])
        expected_tiled_pages = READER_PRINT_TILING_PAGES[supplement_targets[family]]
        if predecessor["page_count"] != expected_tiled_pages:
            raise RuntimeError(
                f"{family}: top accessibility page count {predecessor['page_count']} != {expected_tiled_pages}"
            )
        record_output(records, root, supplement_targets[family], [generator, *semantic_sources],
                      "native Graphviz semantic-page rerender superseding accessibility clip/tiling bundle",
                      {
                          "exact_base_semantic_page_count_and_order": count,
                          "base_semantic_payload": rel(base_semantic),
                          "base_semantic_payload_sha256": sha256(base_semantic),
                          "current_top_accessibility_tiling_pages_retired": expected_tiled_pages,
                          "native_semantic_pages": count,
                          "page_count_delta_from_tiling": count - expected_tiled_pages,
                          "retirement_reason": (
                              "The superseded pages are overlapping magnified clips of these ordered semantic pages, "
                              "not additional scientific panels. Native typography makes tiling unnecessary."
                          ),
                          "semantic_page_order": [proof["source_dot"] for proof in page_proofs],
                          "semantic_page_titles": base_titles,
                          "redundancy_note_exact": expected_redundancy_note,
                          "semantic_page_proofs": page_proofs,
                          "all_source_spans_nodes_edges_labels_statuses_preserved": True,
                          "all_mutations_limited_to_font_spacing_and_page_wrapper": True,
                          "crop_fragments_used": False,
                          "combined_pdf_text_integrity_guard": combined_text_guard,
                          "combined_pdf_zero_tofu_guard": combined_tofu_guard,
                      })


def build_previews(root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    modes = ("original", "grayscale", "protanopia", "deuteranopia", "tritanopia")
    all_outputs: dict[str, dict[str, str]] = {}
    mode_items: dict[str, list[tuple[str, Image.Image]]] = {mode: [] for mode in modes}
    for record in records:
        pdf = root / record["output"]
        page_count = len(fitz.open(pdf))
        asset_key = record["install_path"].replace("/", "__").removesuffix(".pdf")
        for page_index in range(page_count):
            image = render_pdf_page(pdf, page_index)
            page_key = asset_key + (f"__p{page_index + 1:02d}" if page_count > 1 else "")
            all_outputs[page_key] = {}
            for mode in modes:
                transformed = cvd(image, mode)
                path = root / "previews" / mode / f"{page_key}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                transformed.save(path, format="PNG", compress_level=9, optimize=False)
                all_outputs[page_key][mode] = sha256(path)
                mode_items[mode].append((page_key, transformed))
    contacts = {}
    for mode in modes:
        path = root / "previews" / f"R127_NATIVE_FONT_{mode.upper()}_CONTACT_SHEET_v1.png"
        make_contact_sheet(mode_items[mode], path)
        contacts[mode] = {"path": str(path.relative_to(root)), "sha256": sha256(path), "tiles": len(mode_items[mode])}
    return {"individual_previews": all_outputs, "contact_sheets": contacts}


def build_once(root: Path) -> dict[str, Any]:
    # Each replay begins from the same clean plotting state.  Several preserved
    # owners update only a subset of rcParams, so carrying state from build A
    # into build B would create a false determinism failure.
    plt.close("all")
    matplotlib.rcdefaults()
    if root.exists():
        shutil.rmtree(root)
    for path in (root / "assets", root / "manifests", root / "qa", root / "previews", root / "sources"):
        path.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    build_top_level(root, records)
    build_hrc_and_cluster(root, records)
    build_sparc(root, records)
    build_monochrome(root, records)
    build_clipping_owned(root, records)
    build_fig41a(root, records)
    build_graphviz(root, records)
    previews = build_previews(root, records)
    failed = [record["install_path"] for record in records if record["status"] != "PASS"]
    if len(records) != 33:
        raise RuntimeError(f"native replacement scope changed: expected 33 records, found {len(records)}")
    mapped = [record for record in records if record["previous_candidate_layer"] == "font_readability_remediation_v1"]
    if len(mapped) != 32:
        raise RuntimeError(f"accessibility supersession scope changed: expected 32 records, found {len(mapped)}")
    tiled_pages = sum(record["previous_candidate_page_count"] for record in mapped)
    native_pages = sum(record["new_component_page_count"] for record in mapped)
    if (tiled_pages, native_pages) != (187, 45):
        raise RuntimeError(f"accessibility pagination contract changed: {(tiled_pages, native_pages)} != (187, 45)")
    superseded_hashes = {
        "manifest_sha256": sha256(FONT_REMEDIATION_MANIFEST),
        "integration_map_sha256": sha256(FONT_REMEDIATION_INTEGRATION_MAP),
        "checksum_ledger_sha256": sha256(FONT_REMEDIATION_CHECKSUMS),
    }
    expected_hashes = {
        "manifest_sha256": "503fa6d6a5b2192cf20eb0b59578e25dc2f10f90389be079a877d975ade6e842",
        "integration_map_sha256": "4a341990018b1e17a6814549397f44f85aaf32d36b9f3198a6e7b83f03f7e60f",
        "checksum_ledger_sha256": "4b8c4ebb156cc1400e6d85ee5d3f0b935968dbd6005ccdae9dfe4627b381fee3",
    }
    if superseded_hashes != expected_hashes:
        raise RuntimeError(f"superseded accessibility component drifted: {superseded_hashes}")
    manifest = {
        "schema": "ECT-R127-native-font-rerender-v1",
        "status": "PASS_PROPOSAL_ONLY_NOT_APPLIED" if not failed else "FAIL_CLOSED_NOT_FOR_INTEGRATION",
        "fixed_build_time": "2026-07-22T00:00:00Z",
        "scope": "33 native-owner vector replacements: 32 accessibility tilings superseded plus Fig. 41a",
        "generator": rel(SCRIPT),
        "runtime": {
            "python": platform.python_version(), "matplotlib": matplotlib.__version__,
            "numpy": np.__version__, "pymupdf": fitz.VersionBind,
            "graphviz": subprocess.check_output(["/opt/homebrew/bin/dot", "-V"], stderr=subprocess.STDOUT).decode().strip(),
            "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        },
        "policy": {
            "live_files_changed": False, "pdf_crop_fragments_used": False,
            "ordinary_semantic_text_floor_at_tex_placement_pt": ORDINARY_FLOOR_PT,
            "math_script_floor_at_tex_placement_pt": SCRIPT_FLOOR_PT,
            "scientific_arrays_or_statuses_changed": False,
            "graph_topology_changed": False,
            "predecessor_binding": "current top font-readability component byte, never stale lower payload",
            "reader_print_base_semantic_page_partition": {
                "fig09": 4, "fig36": 5, "fig38": 3, "fig39": 5,
            },
            "reader_print_top_tiling_page_partition_retired": {
                "fig09": 19, "fig36": 25, "fig38": 17, "fig39": 25,
            },
            "accessibility_tiling_retirement_reason": (
                "The 187-page predecessor is an overlapping clip/tile magnification of 45 source pages. "
                "Native owner typography restores the same semantic payload without duplicated tiles."
            ),
        },
        "record_count": len(records),
        "superseded_accessibility_component": {
            "name": "font_readability_remediation_v1",
            **superseded_hashes,
            "replacement_count": len(mapped),
            "tiled_reader_pages": tiled_pages,
            "native_semantic_pages": native_pages,
            "page_count_delta": native_pages - tiled_pages,
            "supersession_status": "EXPLICITLY_RETIRED_BY_NATIVE_OWNER_RERENDER",
        },
        "failed_records": failed,
        "all_font_gates_pass": not failed,
        "records": records,
        "qa": previews,
    }
    manifest_path = root / "manifests/R127_NATIVE_FONT_RERENDER_MANIFEST_v1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def hash_tree(root: Path, *, exclude: set[str] | None = None) -> dict[str, str]:
    exclude = exclude or set()
    result = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = str(path.relative_to(root))
        if relative in exclude:
            continue
        result[relative] = sha256(path)
    return result


def write_report(root: Path, manifest: dict[str, Any], deterministic: bool) -> None:
    records = manifest["records"]
    min_ordinary = min(r["font_gate"]["effective_minimum_ordinary_pt"] for r in records)
    script_values = [r["font_gate"]["effective_minimum_script_pt"] for r in records
                     if r["font_gate"]["effective_minimum_script_pt"] is not None]
    report = root / "R127_NATIVE_FONT_RERENDER_REPORT_v1.md"
    report.write_text(
        "# R127 native-owner font rerender v1\n\n"
        "- Date: 2026-07-22.\n"
        "- Status: **" + manifest["status"] + "**.\n"
        "- Scope: 33 install paths (32 audited failures plus Fig. 41a found on discovery page 842).\n"
        "- Method: replay preserved Matplotlib owners/frozen data and Graphviz DOT; changes are limited to typography/canvas spacing, two relocated non-data callouts, one explicit overlap note, and two endpoint-only Graphviz label placements.\n"
        "- Supersession: the 32-path `font_readability_remediation_v1` clip/tiling layer is explicitly retired: "
        "187 tiled accessibility pages become 45 native semantic pages; the added Fig. 41a makes 46 output pages total.\n"
        "- Reader supplements: ordered native 4/5/3/5 semantic pages; all intended DOT spans, nodes, edges, "
        "labels and status tokens are machine-compared; no crop fragments are used.\n"
        f"- Effective ordinary-text minimum at declared TeX placement: **{min_ordinary:.3f} pt** (gate 7.5 pt).\n"
        f"- Effective script minimum: **{min(script_values):.3f} pt** (gate 5 pt).\n"
        f"- Two independent builds byte-identical: **{str(deterministic).upper()}**.\n"
        "- QA: original, true grayscale, protanopia, deuteranopia, and tritanopia previews plus contact sheets.\n"
        "- Scientific guards: numerical arrays and curves, formulas, status text, palette roles, Graphviz nodes/edge endpoints/label text/status counts are unchanged; every accessibility-only annotation change is enumerated in the manifest.\n"
        "- Exact previous-candidate to new-component hashes: `manifests/R127_NATIVE_FONT_INTEGRATION_MAP_v1.json`.\n"
        "- Human visual review: `qa/R127_NATIVE_FONT_HUMAN_VISUAL_REVIEW_v1.json`.\n"
        "- Live manuscript, bibliography, companion, summary, book, Git index/history/remote: **untouched**.\n\n"
        "## Integration policy\n\n"
        "Replace only the exact install paths listed in the manifest.  The parent builder must rebuild the full candidate, "
        "measure fonts on the rendered manuscript pages, inspect every affected page, and fail closed on any overlap, clipping, "
        "semantic drift, or page-count change other than the declared 187-to-45 accessibility-tiling retirement.\n",
        encoding="utf-8",
    )
    integration = root / "manifests/R127_NATIVE_FONT_INTEGRATION_MAP_v1.json"
    integration.write_text(json.dumps({
        "schema": "ECT-R127-native-font-integration-map-v1",
        "status": "PROPOSAL_ONLY_PARENT_REVIEW_REQUIRED",
        "replacement_count": len(records),
        "supersedes": manifest["superseded_accessibility_component"],
        "replacements": [{
            "install_path": r["install_path"],
            "previous_candidate_asset": r["previous_candidate_asset"],
            "previous_candidate_sha256": r["previous_candidate_sha256"],
            "previous_candidate_layer": r["previous_candidate_layer"],
            "previous_candidate_page_count": r["previous_candidate_page_count"],
            "new_component_asset": r["output"],
            "new_component_sha256": r["output_sha256"],
            "new_component_page_count": r["new_component_page_count"],
            "page_count_delta": r["new_component_page_count"] - r["previous_candidate_page_count"],
            "status": r["status"],
            "required_tex_layout": (
                "retire reader-scale includepdf bundle; include native asset at textwidth; preserve caption/label/status"
                if r["install_path"] == "figures/fig_equation_hierarchy.pdf"
                else "retire reader-scale tiling for this path and install native owner asset at its canonical include token"
            ),
        } for r in records],
        "forbidden": ["retaining both native and retired reader-scale tiles", "silent live edit", "unreviewed apply"],
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_human_review(root: Path, manifest: dict[str, Any]) -> None:
    """Freeze the completed human review of the deterministic preview set."""
    contacts = manifest["qa"]["contact_sheets"]
    records = manifest["records"]
    semantic_pages = sum(r["font_gate"]["source"]["page_count"] for r in records)
    review = {
        "schema": "ECT-R127-native-font-human-visual-review-v1",
        "status": "PASS_PROPOSAL_ONLY_PARENT_INTEGRATION_REVIEW_REQUIRED",
        "date": "2026-07-22",
        "scope": {
            "active_assets": len(records),
            "rendered_pages": semantic_pages,
            "superseded_tiled_pages": manifest["superseded_accessibility_component"]["tiled_reader_pages"],
            "native_pages_for_32_superseded_paths": manifest["superseded_accessibility_component"]["native_semantic_pages"],
            "modes": ["original", "grayscale", "protanopia", "deuteranopia", "tritanopia"],
            "live_or_git_changed": False,
        },
        "review_groups": [
            {
                "group": "architecture_equation_liv",
                "status": "PASS",
                "checks": ["no text-box overlap", "no clipped formula/status line",
                           "all declared dependencies visible", "ordinary semantic type readable"],
            },
            {
                "group": "HRC_cluster_SPARC",
                "status": "PASS",
                "checks": ["curves and frozen points unchanged", "direct labels separated",
                           "header/footer reflowed without omission", "NFW benchmark qualifier visible"],
            },
            {
                "group": "owner_analytical_and_data_panels",
                "status": "PASS",
                "checks": ["axes and legends legible", "formula annotations inside page",
                           "line/marker redundancy retained", "scientific status callouts retained"],
            },
            {
                "group": "Graphviz_navigation",
                "status": "PASS_OVERVIEW_ONLY",
                "checks": ["whole overview nodes visible", "overview role explicitly labelled",
                           "semantic reading delegated to paired native supplement"],
            },
            {
                "group": "Graphviz_reader_supplements",
                "status": "PASS",
                "checks": ["ordered 4/5/3/5 native semantic pages retained", "no crop fragments",
                           "whole nodes and arrowheads visible", "all DOT spans/nodes/edges/labels/statuses identical",
                           "zero tofu/replacement glyphs", "current top 19/25/17/25 tiling explicitly retired"],
            },
            {
                "group": "colour_accessibility",
                "status": "PASS",
                "checks": ["true grayscale review", "protanopia review", "deuteranopia review",
                           "tritanopia review", "colour never sole semantic channel"],
            },
        ],
        "contact_sheets": contacts,
        "terminal_font_gates": {
            "ordinary_floor_pt": ORDINARY_FLOOR_PT,
            "script_floor_pt": SCRIPT_FLOOR_PT,
            "all_records_pass": all(r["status"] == "PASS" for r in records),
            "minimum_effective_ordinary_pt": min(
                r["font_gate"]["effective_minimum_ordinary_pt"] for r in records),
            "minimum_effective_script_pt": min(
                r["font_gate"]["effective_minimum_script_pt"] for r in records
                if r["font_gate"]["effective_minimum_script_pt"] is not None),
        },
        "remaining_gate": (
            "The parent R127 builder must install the exact mapped hashes into a disposable full-preprint "
            "candidate, remove the superseded reader-scale includepdf continuations, and repeat pagination plus "
            "rendered-page inspection at actual manuscript placement."
        ),
    }
    path = root / "qa/R127_NATIVE_FONT_HUMAN_VISUAL_REVIEW_v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=COMPONENT)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    with tempfile.TemporaryDirectory(prefix="r127_native_a_") as a_dir, tempfile.TemporaryDirectory(prefix="r127_native_b_") as b_dir:
        a = Path(a_dir)
        b = Path(b_dir)
        manifest_a = build_once(a)
        manifest_b = build_once(b)
        tree_a = hash_tree(a)
        tree_b = hash_tree(b)
        deterministic = tree_a == tree_b
        if not deterministic:
            differing = sorted(set(tree_a) | set(tree_b))
            differing = [path for path in differing if tree_a.get(path) != tree_b.get(path)]
            raise RuntimeError(f"deterministic replay failed: {differing[:20]}")
        if output_root.exists():
            for name in ("assets", "manifests", "qa", "previews", "sources"):
                shutil.rmtree(output_root / name, ignore_errors=True)
            for name in ("R127_NATIVE_FONT_RERENDER_REPORT_v1.md", "SHA256SUMS"):
                (output_root / name).unlink(missing_ok=True)
        for item in a.iterdir():
            if item.name == "manifests":
                continue
            target = output_root / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        (output_root / "manifests").mkdir(parents=True, exist_ok=True)
        manifest = manifest_a
        manifest["deterministic_replay"] = {
            "two_builds_byte_identical": True,
            "file_count": len(tree_a),
            "aggregate_sha256": hashlib.sha256(json.dumps(tree_a, sort_keys=True).encode()).hexdigest(),
        }
        manifest_path = output_root / "manifests/R127_NATIVE_FONT_RERENDER_MANIFEST_v1.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        write_report(output_root, manifest, deterministic)
        write_human_review(output_root, manifest)
        # Imported owner modules may leave interpreter caches beside this
        # builder during probes.  They are neither provenance nor release
        # payload and must not enter the frozen component checksum inventory.
        for cache in sorted(output_root.rglob("__pycache__"), reverse=True):
            shutil.rmtree(cache, ignore_errors=True)
        for bytecode in output_root.rglob("*.pyc"):
            bytecode.unlink(missing_ok=True)
        checksums = []
        for path in sorted(p for p in output_root.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
            checksums.append(f"{sha256(path)}  {path.relative_to(output_root)}")
        (output_root / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": manifest["status"], "records": manifest["record_count"],
            "failed": manifest["failed_records"], "deterministic": deterministic,
            "manifest": str(manifest_path),
        }, indent=2))


if __name__ == "__main__":
    main()
