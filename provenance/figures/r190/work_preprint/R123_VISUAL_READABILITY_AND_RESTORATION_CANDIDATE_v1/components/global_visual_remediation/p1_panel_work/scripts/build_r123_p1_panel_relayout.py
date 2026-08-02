#!/usr/bin/env python3
"""Build proposal-only readable vector relayouts for overloaded ECT figures.

Scientific curves, arrays and status text are either copied as vector content
from the frozen publication PDFs or replayed from the named frozen JSON owners.
No live manuscript or publication asset is modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parents[1]
ECT_ROOT = SCRIPT.parents[8]
LATEX_ROOT = ECT_ROOT / "LaTex"
R123_ROOT = LATEX_ROOT / "work" / "preprint" / "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"

# Keep Matplotlib's font cache inside the owned proposal component.
os.environ.setdefault("MPLCONFIGDIR", str(COMPONENT / "qa" / "mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(COMPONENT / "qa" / "cache"))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")

import fitz  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch  # noqa: E402
import PIL  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


FIXED_DT = datetime(2026, 7, 21, 0, 0, 0, tzinfo=timezone.utc)
FIXED_PDF_DATE = "D:20260721000000Z"
PAGE_WIDTH_PT = 468.0
MARGIN_PT = 7.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_palette():
    path = R123_ROOT / "scripts" / "r123_palette.py"
    spec = importlib.util.spec_from_file_location("r123_palette", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path


PAL, PALETTE_PATH = load_palette()


FAMILY_POLICY = {
    10: {
        "supplement": "one page: a+b stacked at 0.82 text width",
        "widths": {"a": 0.82, "b": 0.82},
        "supplement_pages": 1,
        "main_panels": ("a", "b"),
        "main": "one page: a+b stacked at 0.82 text width",
        "main_pages": 1,
        "texture": "none",
        "caption_delta": "preserve caption; no texture claim",
    },
    11: {
        "supplement": "two pages: a and b separately at full text width",
        "widths": {"a": 1.00, "b": 1.00},
        "supplement_pages": 2,
        "main_panels": ("a",),
        "main": "one owner page: timescale mismatch a; point to full supplement for ballistic-distance panel b",
        "main_pages": 1,
        "texture": "retained",
        "caption_delta": "state that hatch encodes the 70--100 kpc target interval, not decoration",
    },
    15: {
        "supplement": "one page: a+b stacked at 0.83 text width",
        "widths": {"a": 0.83, "b": 0.83},
        "supplement_pages": 1,
        "main_panels": ("a", "b"),
        "main": "one page: a+b stacked at 0.83 text width",
        "main_pages": 1,
        "texture": "removed",
        "caption_delta": "replace 'line style and hatching' by 'line style, fill luminance and direct labels; no hatch'",
    },
    16: {
        "supplement": "two pages: a+b stacked at 0.67 text width; c at 0.83 text width",
        "widths": {"a": 0.67, "b": 0.67, "c": 0.83},
        "supplement_pages": 2,
        "main_panels": ("c",),
        "main": "one owner page: nuisance-summary panel c at 0.83 text width; point to supplement for a+b",
        "main_pages": 1,
        "texture": "removed",
        "caption_delta": "panel c uses fill luminance plus dashed/solid borders; no hatch",
    },
    17: {
        "supplement": "one page: a+b stacked at 0.83 text width",
        "widths": {"a": 0.83, "b": 0.83},
        "supplement_pages": 1,
        "main_panels": ("a", "b"),
        "main": "one page: a+b stacked at 0.83 text width",
        "main_pages": 1,
        "texture": "removed",
        "caption_delta": "replace hatch promise by fill luminance and dashed/solid borders; no hatch",
    },
    18: {
        "supplement": "two pages: a+b and c+d, each pair stacked at 0.86 text width",
        "widths": {"a": 0.86, "b": 0.86, "c": 0.86, "d": 0.86},
        "supplement_pages": 2,
        "main_panels": (),
        "main": "no insertion from this component; sibling external-comparator replacement owns the main rotation-example block",
        "main_pages": 0,
        "texture": "none",
        "caption_delta": "preserve held-out status and common key; link the sibling main block to the complete supplement",
    },
    19: {
        "supplement": "four pages: a,b,c,d separately at full text width; four galaxies per page",
        "widths": {"a": 1.00, "b": 1.00, "c": 1.00, "d": 1.00},
        "supplement_pages": 4,
        "main_panels": ("a", "c"),
        "main": "two representative owner pages: low-acceleration a and high-acceleration c; point to supplement for b+d",
        "main_pages": 2,
        "texture": "none",
        "caption_delta": "preserve frozen selection and fitted-scale warning; explicitly identify omitted gallery pages as supplement-only, not deleted",
    },
    20: {
        "supplement": "two pages: a+b and c+d, each pair stacked at 0.86 text width",
        "widths": {"a": 0.86, "b": 0.86, "c": 0.86, "d": 0.86},
        "supplement_pages": 2,
        "main_panels": ("a", "b", "c", "d"),
        "main": "two pages: a+b and c+d, each pair stacked at 0.86 text width",
        "main_pages": 2,
        "texture": "none",
        "caption_delta": "preserve post-hoc red-team status",
    },
    35: {
        "supplement": "two pages: a+b stacked at 0.70 text width; c at 0.70 text width",
        "widths": {"a": 0.70, "b": 0.70, "c": 0.70},
        "supplement_pages": 2,
        "main_panels": ("a", "b", "c"),
        "main": "two pages: a+b stacked at 0.70 text width; c at 0.70 text width",
        "main_pages": 2,
        "texture": "retained",
        "caption_delta": "hatch denotes the scientifically distinct Open admissible entropy region, not a curve",
    },
    41: {
        "supplement": "two pages: a and b separately at full text width",
        "widths": {"a": 1.00, "b": 1.00},
        "supplement_pages": 2,
        "main_panels": ("b",),
        "main": "one owner page: tensor-normalisation Open-bridge panel b; point to supplement for upstream panel a",
        "main_pages": 1,
        "texture": "removed",
        "caption_delta": "replace hatch promise by luminance, border style, arrow style and literal status",
    },
    42: {
        "supplement": "three pages: a+b, c+d and e+f, each pair stacked at 0.70 text width",
        "widths": {"a": 0.70, "b": 0.70, "c": 0.70, "d": 0.70, "e": 0.70, "f": 0.70},
        "supplement_pages": 3,
        "main_panels": ("a", "b", "c", "f"),
        "main": "two pages: a+b and c+f, each pair stacked at 0.70 text width; point to supplement for d+e",
        "main_pages": 2,
        "texture": "none",
        "caption_delta": "preserve supplied-action and missing-likelihood scope",
    },
    43: {
        "supplement": "three pages: a,b,c separately at full text width",
        "widths": {"a": 1.00, "b": 1.00, "c": 1.00},
        "supplement_pages": 3,
        "main_panels": ("a", "c"),
        "main": "two owner pages: expansion panel a and inverse-F proxy c; point to supplement for w panel b",
        "main_pages": 2,
        "texture": "none",
        "caption_delta": "preserve no-common-epsilon and conditional-state scope",
    },
    44: {
        "supplement": "one page: a+b stacked at 0.80 text width",
        "widths": {"a": 0.80, "b": 0.80},
        "supplement_pages": 1,
        "main_panels": ("a", "b"),
        "main": "one page: a+b stacked at 0.80 text width",
        "main_pages": 1,
        "texture": "none",
        "caption_delta": "preserve prescribed-row / not-posterior guard",
    },
    45: {
        "supplement": "three pages: a,b,c separately at full text width",
        "widths": {"a": 1.00, "b": 1.00, "c": 1.00},
        "supplement_pages": 3,
        "main_panels": ("a", "c"),
        "main": "two owner pages: fixed-metric BVP a and dimensional gate c; point to supplement for estimator panel b",
        "main_pages": 2,
        "texture": "none",
        "caption_delta": "remove stale word 'hatching'; retain marker, line, luminance and direct-label redundancy",
    },
    46: {
        "supplement": "one page: full text width",
        "widths": {"a": 1.00},
        "supplement_pages": 1,
        "main_panels": ("a",),
        "main": "one page: full text width",
        "main_pages": 1,
        "texture": "none",
        "caption_delta": "preserve Level-C proxy-only scope",
    },
    47: {
        "supplement": "one page: a+b stacked at 0.86 text width",
        "widths": {"a": 0.86, "b": 0.86},
        "supplement_pages": 1,
        "main_panels": ("a", "b"),
        "main": "one page: a+b stacked at 0.86 text width",
        "main_pages": 1,
        "texture": "retained",
        "caption_delta": "texture marks finite-window/bin data region; protocol caveats unchanged",
    },
}

# Final R123 integration architecture has two explicit options.  FULL keeps
# every panel in the main manuscript at full text width.  BOUNDED keeps the
# minimum owner panels listed below at full text width and sends every other
# panel to the complete vector supplement.  Figure 18 is owned in the main
# manuscript by the sibling external-comparator replacement.
BOUNDED_MAIN_SELECTION = {
    10: ("a",),
    11: ("a",),
    15: ("a", "b"),
    16: ("c",),
    17: ("a",),
    18: (),
    19: ("a", "c"),
    20: ("a", "c"),
    35: ("b",),
    41: ("b",),
    42: ("b",),
    43: ("a", "c"),
    44: ("a", "b"),
    45: ("a", "c"),
    46: ("a",),
    47: ("a", "b"),
}

for _figure, _policy in FAMILY_POLICY.items():
    _all_panels = tuple(_policy["widths"])
    _selected = BOUNDED_MAIN_SELECTION[_figure]
    _policy["widths"] = {panel: 1.0 for panel in _all_panels}
    _policy["supplement"] = f"{len(_all_panels)} full-width pages; one vector panel per page"
    _policy["supplement_pages"] = len(_all_panels)
    _policy["main_panels"] = _selected
    _policy["main_pages"] = len(_selected)
    _policy["main"] = (
        "no main insertion from this component; sibling external-comparator replacement owns Figure 18"
        if not _selected
        else "bounded owner selection, one full-width vector panel per page: " + ",".join(_selected)
    )


SOURCE_FILES = {
    10: LATEX_ROOT / "figures/r103/r103_ect_acoustic_ppn_tradeoff.pdf",
    11: LATEX_ROOT / "figures/r114/r114_one_real_pole_cluster_scale_no_go.pdf",
    15: LATEX_ROOT / "figures/hrc/R97_HRC_BTFR_AND_SCALE.pdf",
    16: LATEX_ROOT / "figures/hrc/R97_HRC_ML_SENSITIVITY.pdf",
    17: LATEX_ROOT / "figures/hrc/R97_HRC_RESPONSE_AND_REGIMES.pdf",
    18: LATEX_ROOT / "figures/hrc/R97_HRC_ROTATION_EXAMPLES.pdf",
    19: LATEX_ROOT / "figures/hrc/R97_HRC_ROTATION_GALLERY.pdf",
    20: LATEX_ROOT / "figures/hrc/R97_HRC_RESIDUAL_STRESS.pdf",
    35: LATEX_ROOT / "figures/fig_bh_information.pdf",
    41: LATEX_ROOT / "figures/r103/r103_Cn_scalechain_corrected.pdf",
    42: LATEX_ROOT / "figures/r103/r103_ect_background_clocks.pdf",
    43: LATEX_ROOT / "figures/r103/r103_two_slope_HwG_conditional.pdf",
    44: LATEX_ROOT / "figures/r114/r114_early_response_growth_collapse_envelope.pdf",
    45: LATEX_ROOT / "figures/r114/r114_finitebody_scalar_gates.pdf",
    46: LATEX_ROOT / "figures/r103/r103_ect_restricted_perturbation_proxies.pdf",
    47: LATEX_ROOT / "figures/r114/r114_pes_m1_same_channel_fdt_protocol.pdf",
}


@dataclass(frozen=True)
class PanelSpec:
    figure: int
    suffix: str
    slug: str
    clip: tuple[float, float, float, float]
    header: str = ""
    key: str = ""
    footer: str = ""
    status: str = ""
    method: str = "vector crop from frozen publication PDF"

    @property
    def stem(self) -> str:
        return f"fig{self.figure}_{self.suffix}_{self.slug}_r123"


SPECS = [
    PanelSpec(10, "a", "acoustic_gate", (45, 15, 410, 306), status="Level C diagnostic; not a CMB likelihood"),
    PanelSpec(10, "b", "fixed_angle_proxy", (420, 15, 772, 306), status="Level C diagnostic; not a CMB likelihood"),
    PanelSpec(11, "a", "timescale_mismatch", (35, 25, 395, 313), header="One-real-pole cluster-scale test", status="conditional no-go within the named one-pole model"),
    PanelSpec(11, "b", "ballistic_distance_mismatch", (420, 25, 778, 313), header="One-real-pole cluster-scale test", status="conditional no-go within the named one-pole model"),
    PanelSpec(15, "a", "btfr_tail_proxy", (35, 25, 418, 315), header="HRC-only BTFR and fitted-scale diagnostics", status="Level C algebraic diagnostic"),
    PanelSpec(16, "a", "hrc0_ml_coupling", (42, 25, 292, 285), header="HRC-only stellar-M/L sensitivity", status="Level C nuisance diagnostic"),
    PanelSpec(16, "b", "hrc3_ml_coupling", (327, 25, 578, 285), header="HRC-only stellar-M/L sensitivity", status="Level C nuisance diagnostic"),
    PanelSpec(17, "a", "response_laws", (35, 25, 410, 294), header="HRC-only response and regime diagnostics", status="algebraic response laws"),
    PanelSpec(18, "a", "ddo154", (40, 90, 375, 298), header="Held-out HRC rotation-curve examples", key="HRC-0: dashed blue; HRC-3: solid orange; SPARC: black points", status="mean over five whole-galaxy splits"),
    PanelSpec(18, "b", "ngc2403", (410, 90, 746, 298), header="Held-out HRC rotation-curve examples", key="HRC-0: dashed blue; HRC-3: solid orange; SPARC: black points", status="mean over five whole-galaxy splits"),
    PanelSpec(18, "c", "ngc3198", (40, 315, 375, 538), header="Held-out HRC rotation-curve examples", key="HRC-0: dashed blue; HRC-3: solid orange; SPARC: black points", status="mean over five whole-galaxy splits"),
    PanelSpec(18, "d", "ngc6503", (410, 315, 746, 538), header="Held-out HRC rotation-curve examples", key="HRC-0: dashed blue; HRC-3: solid orange; SPARC: black points", status="mean over five whole-galaxy splits"),
    PanelSpec(19, "a", "gallery_lowacc_1", (35, 65, 435, 405), header="HRC-only frozen acceleration-stratified gallery -- page 1/4", key="SPARC points; baryons dotted; HRC-0 dashed; HRC-3 solid", status="selection and curves unchanged"),
    PanelSpec(19, "b", "gallery_lowacc_2", (440, 65, 850, 405), header="HRC-only frozen acceleration-stratified gallery -- page 2/4", key="SPARC points; baryons dotted; HRC-0 dashed; HRC-3 solid", status="selection and curves unchanged"),
    PanelSpec(19, "c", "gallery_highacc_1", (35, 390, 435, 780), header="HRC-only frozen acceleration-stratified gallery -- page 3/4", key="SPARC points; baryons dotted; HRC-0 dashed; HRC-3 solid", status="selection and curves unchanged"),
    PanelSpec(19, "d", "gallery_highacc_2", (440, 390, 850, 780), header="HRC-only frozen acceleration-stratified gallery -- page 4/4", key="SPARC points; baryons dotted; HRC-0 dashed; HRC-3 solid", status="selection and curves unchanged"),
    PanelSpec(20, "a", "ugc02953", (40, 90, 375, 300), header="Post-hoc HRC residual-stress examples", key="HRC-0 dashed; HRC-3 solid; SPARC black points", status="post-hoc stress example; not held-out prediction"),
    PanelSpec(20, "b", "ugc09133", (410, 90, 746, 300), header="Post-hoc HRC residual-stress examples", key="HRC-0 dashed; HRC-3 solid; SPARC black points", status="post-hoc stress example; not held-out prediction"),
    PanelSpec(20, "c", "ngc6946", (40, 315, 375, 539), header="Post-hoc HRC residual-stress examples", key="HRC-0 dashed; HRC-3 solid; SPARC black points", status="post-hoc stress example; not held-out prediction"),
    PanelSpec(20, "d", "ngc7331", (410, 315, 746, 539), header="Post-hoc HRC residual-stress examples", key="HRC-0 dashed; HRC-3 solid; SPARC black points", status="post-hoc stress example; not held-out prediction"),
    PanelSpec(35, "a", "tolman_kinematics", (20, 20, 315, 305), status="external kinematics"),
    PanelSpec(35, "b", "page_curve_benchmark", (330, 20, 630, 305), status="semiclassical benchmark; ECT curve Open"),
    PanelSpec(35, "c", "hawking_benchmark", (665, 20, 950, 305), status="external Hawking benchmark; ECT shell depth not identified"),
    PanelSpec(42, "a", "named_expansion", (55, 5, 325, 270), header="Conditional supplied-action background diagnostics", status="not a unique P1-P6 cosmology"),
    PanelSpec(42, "b", "clock_budget", (340, 5, 620, 270), header="Conditional supplied-action background diagnostics", status="not a unique P1-P6 cosmology"),
    PanelSpec(42, "c", "comoving_distance", (650, 5, 935, 270), header="Conditional supplied-action background diagnostics", status="photon/perturbation likelihood owners remain Open"),
    PanelSpec(42, "d", "background_w", (55, 270, 325, 535), header="Conditional supplied-action background diagnostics", status="total kinematic w_eff, not w_DE"),
    PanelSpec(42, "e", "calibrated_family", (340, 270, 620, 535), header="Conditional supplied-action background diagnostics", status="declared state/unit calibration; Level C"),
    PanelSpec(42, "f", "scope_statement", (650, 270, 950, 535), header="Conditional supplied-action background diagnostics", status="scope and missing-owner statement"),
    PanelSpec(43, "a", "two_slope_expansion", (55, 0, 270, 315), header="Conditional two-slope state; no common-epsilon law", status="Level C observable diagnostic inside supplied state"),
    PanelSpec(43, "b", "two_slope_w", (290, 0, 505, 315), header="Conditional two-slope state; no common-epsilon law", status="total kinematic w_eff"),
    PanelSpec(43, "c", "inverse_f_proxy", (530, 0, 743, 315), header="Conditional two-slope state; no common-epsilon law", status="not local G_N; finite-body/PPN map Open"),
    PanelSpec(44, "a", "growth_equality", (35, 25, 405, 314), header="Owner-specific early-response envelope", status="conditional owner response"),
    PanelSpec(44, "b", "rare_tail", (410, 25, 779, 314), header="Owner-specific early-response envelope", status="Level C rare-tail sensitivity; not posterior/JWST prediction"),
    PanelSpec(45, "a", "fixed_metric_bvp", (40, 35, 360, 315), header="R114 finite-body scalar gates", footer="Fixed-metric scalar BVP only; not body sensitivity, coupled metric, Cassini, WEP or full PPN.", status="conditional fixed-metric diagnostic"),
    PanelSpec(45, "b", "tail_estimators", (385, 35, 710, 315), header="R114 finite-body scalar gates", footer="Three tail estimators are shown separately and are not averaged.", status="conditional fixed-metric diagnostic"),
    PanelSpec(45, "c", "dimensional_gate", (735, 35, 1051, 315), header="R114 finite-body scalar gates", footer="Dimensional gate only; not physical body sensitivity or full PPN.", status="named-object dimensional obstruction"),
    PanelSpec(47, "a", "single_kms_channel", (45, 40, 390, 275), header="M1 same-channel FDT protocol", footer="Synthetic source model; conditional Level-A algebra inside a Level-B protocol.", status="diagnostic only"),
    PanelSpec(47, "b", "counterexamples", (425, 40, 777, 275), header="M1 same-channel FDT protocol", footer="Ordinary non-KMS/protocol counterexamples; mismatch is not by itself ECT evidence.", status="diagnostic only"),
]


def fitz_metadata(title: str) -> dict[str, str]:
    return {
        "title": title,
        "author": "ECT reproducibility workflow",
        "subject": "Proposal-only vector readability relayout; scientific payload unchanged",
        "keywords": "ECT R123 vector relayout proposal",
        "creator": SCRIPT.name,
        "producer": f"PyMuPDF {fitz.VersionBind}",
        "creationDate": FIXED_PDF_DATE,
        "modDate": FIXED_PDF_DATE,
    }


def insert_centered_text(page: fitz.Page, y: float, text: str, size: float, color=(0.13, 0.13, 0.13), bold=False) -> float:
    if not text:
        return y
    font = "hebo" if bold else "helv"
    rect = fitz.Rect(MARGIN_PT, y, PAGE_WIDTH_PT - MARGIN_PT, y + size * 2.5)
    rc = page.insert_textbox(rect, text, fontsize=size, fontname=font, color=color, align=fitz.TEXT_ALIGN_CENTER)
    if rc < 0:
        raise RuntimeError(f"Text did not fit: {text!r}")
    return y + size * 1.55


def compose_crop(spec: PanelSpec, output: Path) -> dict:
    source = SOURCE_FILES[spec.figure]
    src = fitz.open(source)
    page0 = src[0]
    clip = fitz.Rect(*spec.clip) & page0.rect
    if clip.is_empty or clip.width < 50 or clip.height < 50:
        raise ValueError(f"Bad crop for {spec.stem}: {clip}")

    header_height = 0.0
    if spec.header:
        header_height += 19.0
    if spec.key:
        header_height += 14.0
    footer_height = 0.0
    if spec.footer:
        footer_height = 27.0

    target_width = PAGE_WIDTH_PT - 2 * MARGIN_PT
    scale = target_width / clip.width
    target_height = clip.height * scale
    page_height = MARGIN_PT + header_height + target_height + footer_height + MARGIN_PT

    out = fitz.open()
    page = out.new_page(width=PAGE_WIDTH_PT, height=page_height)
    y = MARGIN_PT
    if spec.header:
        y = insert_centered_text(page, y, spec.header, 10.5, bold=True)
    if spec.key:
        y = insert_centered_text(page, y, spec.key, 8.2, color=(0.36, 0.36, 0.36))
    dst = fitz.Rect(MARGIN_PT, y, PAGE_WIDTH_PT - MARGIN_PT, y + target_height)
    page.show_pdf_page(dst, src, 0, clip=clip, keep_proportion=True)
    y = dst.y1 + 3.0
    if spec.footer:
        insert_centered_text(page, y, spec.footer, 8.2, color=(0.28, 0.28, 0.28))
    out.set_metadata(fitz_metadata(spec.stem))
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output, garbage=4, deflate=True, clean=True, no_new_id=True)
    out.close()
    src.close()
    return {
        "clip": [round(v, 3) for v in spec.clip],
        "scale_to_468pt": scale,
        "page_width_pt": PAGE_WIDTH_PT,
        "page_height_pt": page_height,
    }


def configure_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.titlesize": 11.0,
            "axes.labelsize": 9.5,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "r123-p1-panel-relayout-v1",
            "savefig.facecolor": PAL.PAPER,
            "axes.facecolor": PAL.PAPER,
            "text.color": PAL.INK,
            "axes.labelcolor": PAL.INK,
            "axes.edgecolor": PAL.GRAPHITE,
            "xtick.color": PAL.INK,
            "ytick.color": PAL.INK,
        }
    )


PDF_METADATA = {
    "Title": "R123 P1 readable panel relayout",
    "Author": "ECT reproducibility workflow",
    "Subject": "Proposal-only readability relayout from frozen scientific owners",
    "Keywords": "ECT R123 grayscale safe vector panel",
    "Creator": SCRIPT.name,
    "CreationDate": FIXED_DT,
    "ModDate": FIXED_DT,
}


def save_mpl(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf", bbox_inches="tight", metadata=PDF_METADATA)
    plt.close(fig)


def add_box(ax, xy, width, height, title, body, face, edge, linestyle="-", linewidth=1.7):
    p = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.07",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        linestyle=linestyle,
    )
    ax.add_patch(p)
    x, y = xy
    ax.text(x + width / 2, y + height * 0.66, title, ha="center", va="center", fontsize=10.5, weight="bold")
    ax.text(x + width / 2, y + height * 0.28, body, ha="center", va="center", fontsize=10.2, linespacing=1.12)


def add_arrow(ax, start, end, color, linestyle="-", label="", label_xy=None):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.7, color=color, linestyle=linestyle))
    if label:
        lx, ly = label_xy or ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.1)
        ax.text(lx, ly, label, ha="center", va="bottom", fontsize=10.2, color=PAL.INK)


def render_fig41(out_dir: Path) -> list[tuple[str, str]]:
    """Re-layout the exact owner chain into two readable semantic panels."""
    configure_matplotlib()
    outputs = []

    fig, ax = plt.subplots(figsize=(6.5, 6.25))
    ax.set(xlim=(0, 10), ylim=(0, 6.4))
    ax.axis("off")
    ax.text(5, 6.10, "Orientation stiffness: established and conditional upstream chain", ha="center", fontsize=12, weight="bold")
    ax.text(5, 5.72, "Every status is literal; colour is redundant with border style and wording.", ha="center", fontsize=9.0, color=PAL.GRAPHITE)
    add_box(ax, (0.75, 4.15), 8.5, 1.05, "Ordered variables", "$\\partial_A\\Phi=u n_A$; P4 kinematics -- Level A", PAL.LEVEL_A_FILL, PAL.LEVEL_A_EDGE)
    add_box(ax, (0.75, 2.55), 8.5, 1.05, "Heavy-radial determinant", "$\\frac{1}{2}\\,\\mathrm{Tr}\\ln\\mathcal{O}_\\sigma$; NLO -- CONDITIONAL declared closure", PAL.LEVEL_B_FILL, PAL.LEVEL_B_EDGE, "--")
    add_box(ax, (0.75, 0.95), 8.5, 1.05, "Orientation coefficient $\\mathcal{C}_n$", "$\\mathcal{C}_n=\\hat a_{\\rm eff}/(16\\pi^2m_\\sigma^2)$ -- CONDITIONAL; matching Open", PAL.LEVEL_B_FILL, PAL.LEVEL_B_EDGE, "--")
    add_arrow(ax, (5, 4.15), (5, 3.60), PAL.LEVEL_A_EDGE, label="background reduction", label_xy=(6.45, 3.73))
    add_arrow(ax, (5, 2.55), (5, 2.00), PAL.LEVEL_B_EDGE, label="operator basis", label_xy=(6.02, 2.13))
    handles = [
        Patch(facecolor=PAL.LEVEL_A_FILL, edgecolor=PAL.LEVEL_A_EDGE, label="Level A definition / kinematics"),
        Patch(facecolor=PAL.LEVEL_B_FILL, edgecolor=PAL.LEVEL_B_EDGE, linestyle="--", label="conditional under declared assumptions"),
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=8.2, bbox_to_anchor=(0.5, -0.01))
    p = out_dir / "fig41_a_orientation_stiffness_upstream_r123.pdf"
    save_mpl(fig, p)
    outputs.append((p.name, "scientific-equivalent relayout from frozen Fig. 41 owner text"))

    fig, ax = plt.subplots(figsize=(6.5, 7.5))
    ax.set(xlim=(0, 10), ylim=(0, 8.0))
    ax.axis("off")
    ax.text(5, 7.70, "Tensor-normalisation bridge remains Open", ha="center", fontsize=12, weight="bold")
    ax.text(5, 7.33, "The established owner chain ends at $\\kappa_n$; dimensional equality creates neither helicity-2 dynamics nor a static-density vertex.", ha="center", fontsize=10.2, color=PAL.GRAPHITE)
    add_box(ax, (0.75, 5.70), 8.5, 1.0, "Orientation coefficient $\\mathcal{C}_n$", "CONDITIONAL; matching Open", PAL.LEVEL_B_FILL, PAL.LEVEL_B_EDGE, "--")
    add_box(ax, (0.75, 4.15), 8.5, 1.0, "Orientation stiffness $\\kappa_n$", "$\\kappa_n\\equiv\\mathcal{C}_nu_0^2$ -- exact EFT definition, Level A", PAL.LEVEL_A_FILL, PAL.LEVEL_A_EDGE)
    add_box(ax, (0.75, 2.60), 8.5, 1.0, "Physical tensor scale $M_G$", "$M_G^2\\;?=\\;c_M\\kappa_n$ -- OPEN: TT owner/source missing", PAL.OPEN_FILL, PAL.OPEN_EDGE, "--")
    add_box(ax, (0.75, 1.05), 8.5, 1.0, "Newton constant $G_N$", "$G_N=c_{\\rm char}^4/(8\\pi M_G^2)$ -- external supplied completion", PAL.EXTERNAL_FILL, PAL.EXTERNAL_EDGE)
    add_arrow(ax, (5, 5.70), (5, 5.15), PAL.LEVEL_A_EDGE, label="definition", label_xy=(5.78, 5.27))
    add_arrow(ax, (5, 4.15), (5, 3.60), PAL.OPEN_EDGE, "--", label="OPEN: $c_M$ + tensor owner", label_xy=(6.40, 3.72))
    add_arrow(ax, (5, 2.60), (5, 2.05), PAL.EXTERNAL_EDGE, label="standard weak-field matching", label_xy=(6.55, 2.17))
    handles = [
        Patch(facecolor=PAL.LEVEL_A_FILL, edgecolor=PAL.LEVEL_A_EDGE, label="exact EFT definition"),
        Patch(facecolor=PAL.LEVEL_B_FILL, edgecolor=PAL.LEVEL_B_EDGE, linestyle="--", label="conditional input"),
        Patch(facecolor=PAL.OPEN_FILL, edgecolor=PAL.OPEN_EDGE, linestyle="--", label="Open / missing owner"),
        Patch(facecolor=PAL.EXTERNAL_FILL, edgecolor=PAL.EXTERNAL_EDGE, label="external supplied completion"),
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=8.0, bbox_to_anchor=(0.5, 0.005))
    p = out_dir / "fig41_b_tensor_normalisation_open_bridge_r123.pdf"
    save_mpl(fig, p)
    outputs.append((p.name, "scientific-equivalent relayout from frozen Fig. 41 owner text"))
    return outputs


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_fig46(out_dir: Path) -> list[tuple[str, str]]:
    """Re-render the same frozen proxy arrays with larger type and R123 colours."""
    configure_matplotlib()
    data_dir = LATEX_ROOT / "data" / "cosmology_r103"
    background_path = data_dir / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json"
    isw_path = data_dir / "R103_RESTRICTED_ISW_LENSING_PROXY_v1.json"
    flow_path = data_dir / "R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json"
    background = load_json(background_path)
    isw = load_json(isw_path)
    flow = load_json(flow_path)
    brow = {float(r["z"]): r for r in background["rows"]}
    rows = isw["rows_primary"]
    z = np.array([r["z"] for r in rows])
    dz = np.array([brow[float(v)]["delta_D_percent"] for v in z])
    q = np.array([r["delta_Q_W_percent"] for r in rows])
    s = np.array([r["delta_S_ISW_proxy_percent"] for r in rows])
    frow = {float(r["z"]): r for r in flow["rows"]}
    v = np.array([frow[float(vv)]["delta_velocity_carrier_percent"] for vv in z])
    vp = np.array([frow[float(vv)]["delta_velocity_power_carrier_percent"] for vv in z])

    fig, ax = plt.subplots(figsize=(6.5, 5.35), constrained_layout=True)
    ax.plot(z, dz, color=PAL.HRC0, marker="o", ls="-", lw=1.9, label=r"growth amplitude $D$")
    ax.plot(z, q, color=PAL.HRC3, marker="s", ls="--", lw=1.9, label=r"Weyl carrier $Q_W$")
    ax.plot(z, s, color=PAL.LEVEL_C_EDGE, marker="^", ls="-.", lw=1.9, label=r"derivative carrier $S_{\mathrm{ISW}}^{\mathrm{proxy}}$")
    ax.plot(z, v, color=PAL.GRAPHITE, marker="D", markerfacecolor=PAL.PAPER, ls=":", lw=1.9, label=r"velocity carrier $aHfD$")
    ax.plot(z, vp, color=PAL.TENSION_EDGE, marker="v", ls=(0, (5, 2, 1, 2)), lw=1.9, label="velocity-power carrier")
    ax.axhline(0, color=PAL.INK, lw=0.9)
    ax.grid(True, color=PAL.GRID, linewidth=0.7, alpha=0.8)
    ax.set(xlabel="redshift $z$", ylabel=r"model/control difference [\%]", title="Restricted near-GR perturbation carriers")
    ax.legend(frameon=False, fontsize=10.2, ncol=2, loc="upper left")
    ax.text(0.01, 0.02, "Level C: same metric, zero slip, sub-horizon; not projected spectra", transform=ax.transAxes, fontsize=8.5, bbox=dict(facecolor=PAL.EXTERNAL_FILL, edgecolor=PAL.EXTERNAL_EDGE, boxstyle="round,pad=0.25"))
    p = out_dir / "fig46_restricted_perturbation_proxies_readable_r123.pdf"
    save_mpl(fig, p)
    return [(p.name, "exact replay of frozen R103 JSON arrays; only palette/type/layout changed")]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def render_hatchfree_hrc_panels(out_dir: Path) -> list[dict]:
    """Replay three HRC panels without decorative model-identity hatching."""
    configure_matplotlib()
    fits_path = LATEX_ROOT / "data/hrc_r97/R97_HRC_PER_GALAXY_FITS.csv"
    regimes_path = LATEX_ROOT / "data/hrc_r97/R97_HRC_SOURCE_REGIMES.csv"
    fits = read_csv(fits_path)
    regimes = [r for r in read_csv(regimes_path) if r["bin_kind"] == "coarse"]
    results = []

    ratios0 = np.asarray([float(r["aM_HRC0_over_match"]) for r in fits])
    ratios3 = np.asarray([float(r["aM_HRC3_over_match"]) for r in fits])
    fig, ax = plt.subplots(figsize=(6.5, 4.8), constrained_layout=True)
    bins = np.logspace(-2, 2, 31)
    ax.hist(ratios0, bins=bins, histtype="step", lw=2.2, ls="--", color=PAL.HRC0, label="HRC-0")
    ax.hist(
        ratios3,
        bins=bins,
        histtype="stepfilled",
        facecolor=PAL.LEVEL_B_FILL,
        edgecolor=PAL.HRC3,
        linewidth=1.8,
        alpha=1.0,
        label="HRC-3",
    )
    ax.axvline(1.0, color=PAL.INK, lw=1.5, ls=":", label="matched scale")
    ax.set_xscale("log")
    ax.set_xlabel(r"per-galaxy fitted $a_M/a_{M0}$")
    ax.set_ylabel("galaxies")
    ax.set_title("Algebraic scale dispersion -- Level C diagnostic")
    ax.grid(True, which="both", color=PAL.GRID, linewidth=0.7)
    ax.legend(frameon=False, fontsize=9.0)
    p = out_dir / "fig15_b_scale_dispersion_r123.pdf"
    save_mpl(fig, p)
    results.append({"figure": 15, "panel": "b", "path": p, "inputs": [fits_path], "status": "Level C algebraic diagnostic", "method": "exact histogram replay; decorative hatch removed"})

    ml0 = np.asarray([float(r["ups_disk_HRC0_freeML"]) for r in fits])
    ml3 = np.asarray([float(r["ups_disk_HRC3_freeML"]) for r in fits])
    fig, ax = plt.subplots(figsize=(6.5, 4.8), constrained_layout=True)
    bins = np.linspace(0.1, 2.5, 25)
    ax.hist(ml0, bins=bins, histtype="step", color=PAL.HRC0, lw=2.2, ls="--", label="HRC-0")
    ax.hist(
        ml3,
        bins=bins,
        histtype="stepfilled",
        facecolor=PAL.LEVEL_B_FILL,
        edgecolor=PAL.HRC3,
        linewidth=1.8,
        alpha=1.0,
        label="HRC-3",
    )
    ax.axvline(0.5, color=PAL.INK, lw=1.5, ls=":", label="fixed value")
    ax.set_xlabel(r"fitted disk $\Upsilon_{\mathrm{d}}$")
    ax.set_ylabel("galaxies")
    ax.set_title(r"Two-parameter stellar-$M/L$ nuisance test -- Level C")
    ax.grid(True, color=PAL.GRID, linewidth=0.7)
    ax.legend(frameon=False, fontsize=9.0)
    p = out_dir / "fig16_c_two_parameter_nuisance_r123.pdf"
    save_mpl(fig, p)
    results.append({"figure": 16, "panel": "c", "path": p, "inputs": [fits_path], "status": "Level C nuisance diagnostic", "method": "exact histogram replay; decorative hatch removed"})

    order = ["deep_yN_lt_0p1", "crossover_0p1_to_10", "newtonian_yN_gt_10"]
    names = {r["bin"]: r for r in regimes}
    h0 = [float(names[key]["chi2_HRC0_per_point"]) for key in order]
    h3 = [float(names[key]["chi2_HRC3_per_point"]) for key in order]
    fig, ax = plt.subplots(figsize=(6.5, 4.8), constrained_layout=True)
    idx = np.arange(3)
    width = 0.34
    ax.bar(
        idx - width / 2,
        h0,
        width,
        facecolor=PAL.LEVEL_A_FILL,
        edgecolor=PAL.HRC0,
        linewidth=1.8,
        linestyle="--",
        label="HRC-0",
    )
    ax.bar(
        idx + width / 2,
        h3,
        width,
        facecolor=PAL.LEVEL_B_FILL,
        edgecolor=PAL.HRC3,
        linewidth=1.8,
        linestyle="-",
        label="HRC-3",
    )
    ax.set_xticks(idx, ["deep", "crossover", "Newtonian"])
    ax.set_ylabel(r"held-out $\chi^2$ per point")
    ax.set_title("Frozen algebraic SPARC diagnostic -- Level C")
    ax.grid(True, axis="y", color=PAL.GRID, linewidth=0.7)
    ax.legend(frameon=False, fontsize=9.0)
    p = out_dir / "fig17_b_sparc_regime_diagnostic_r123.pdf"
    save_mpl(fig, p)
    results.append({"figure": 17, "panel": "b", "path": p, "inputs": [regimes_path], "status": "frozen Level C SPARC diagnostic", "method": "exact bar replay; decorative hatch removed"})
    return results


def text_metrics(path: Path) -> dict:
    doc = fitz.open(path)
    all_spans = []
    primary_spans = []
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                visible = [s for s in line.get("spans", []) if s.get("text", "").strip()]
                line_max = max((float(s["size"]) for s in visible), default=0.0)
                for span in visible:
                    text = span.get("text", "").strip()
                    size = float(span["size"])
                    all_spans.append((size, text))
                    # Mathtext encodes subscripts/superscripts as reduced-size
                    # spans on the same line.  They are reported in the all-text
                    # metric but do not define the primary label/tick/legend
                    # gate.  This is a typographic distinction, not deletion.
                    is_math_script = line_max > 0 and size < 0.78 * line_max
                    if not is_math_script:
                        primary_spans.append((size, text))
    doc.close()
    return {
        "span_count": len(all_spans),
        "minimum_all_text_pt": min((s for s, _ in all_spans), default=None),
        "minimum_primary_text_pt": min((s for s, _ in primary_spans), default=None),
        "smallest_spans": [
            {"size_pt": round(s, 3), "text": t}
            for s, t in sorted(all_spans, key=lambda x: (x[0], x[1]))[:8]
        ],
    }


def render_png(pdf: Path, output: Path, dpi: int = 120) -> None:
    doc = fitz.open(pdf)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False, colorspace=fitz.csRGB)
    output.parent.mkdir(parents=True, exist_ok=True)
    pix.save(output)
    doc.close()


def cvd_image(image: Image.Image, mode: str) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    if mode == "gray":
        lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
        out = np.repeat(lum[..., None], 3, axis=2)
    else:
        matrices = {
            "protan": np.array([[0.567, 0.433, 0.000], [0.558, 0.442, 0.000], [0.000, 0.242, 0.758]]),
            "deutan": np.array([[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]]),
            "tritan": np.array([[0.950, 0.050, 0.000], [0.000, 0.433, 0.567], [0.000, 0.475, 0.525]]),
        }
        out = arr @ matrices[mode].T
    return Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255.0), mode="RGB")


def build_contact(images: list[tuple[str, Path]], output: Path, mode: str) -> None:
    thumb_w, thumb_h = 320, 260
    columns = 3
    rows = math.ceil(len(images) / columns)
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + 26)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, (name, path) in enumerate(images):
        im = Image.open(path).convert("RGB")
        if mode != "color":
            im = cvd_image(im, mode)
        im.thumbnail((thumb_w - 12, thumb_h - 12), Image.Resampling.LANCZOS)
        x = (i % columns) * thumb_w + (thumb_w - im.width) // 2
        y0 = (i // columns) * (thumb_h + 26)
        y = y0 + 22 + (thumb_h - im.height) // 2
        canvas.paste(im, (x, y))
        draw.text((i % columns * thumb_w + 6, y0 + 4), name, fill="black", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", compress_level=9, optimize=False)


def build(output_root: Path) -> dict:
    assets = output_root / "assets"
    color_dir = output_root / "previews" / "color"
    qa_dir = output_root / "qa"
    manifests = output_root / "manifests"
    for d in (assets, color_dir, qa_dir, manifests):
        d.mkdir(parents=True, exist_ok=True)

    records = []
    for spec in SPECS:
        output = assets / f"{spec.stem}.pdf"
        placement = compose_crop(spec, output)
        records.append(
            {
                "figure": spec.figure,
                "panel": spec.suffix,
                "slug": spec.slug,
                "source": str(SOURCE_FILES[spec.figure].relative_to(ECT_ROOT)),
                "source_sha256": sha256(SOURCE_FILES[spec.figure]),
                "output": f"assets/{output.name}",
                "output_sha256": sha256(output),
                "method": spec.method,
                "status": spec.status,
                "placement": placement,
                "text_metrics": text_metrics(output),
            }
        )

    for name, method in render_fig41(assets):
        output = assets / name
        records.append(
            {
                "figure": 41,
                "panel": "a" if "_a_" in name else "b",
                "slug": output.stem,
                "source": str(SOURCE_FILES[41].relative_to(ECT_ROOT)),
                "source_sha256": sha256(SOURCE_FILES[41]),
                "owner_generator": "LaTex/scripts/figures/make_r103_restored_visuals.py",
                "owner_generator_sha256": sha256(LATEX_ROOT / "scripts/figures/make_r103_restored_visuals.py"),
                "output": f"assets/{name}",
                "output_sha256": sha256(output),
                "method": method,
                "status": "owner chain exact through kappa_n; tensor bridge Open",
                "text_metrics": text_metrics(output),
            }
        )

    for name, method in render_fig46(assets):
        output = assets / name
        data_dir = LATEX_ROOT / "data" / "cosmology_r103"
        inputs = [
            data_dir / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json",
            data_dir / "R103_RESTRICTED_ISW_LENSING_PROXY_v1.json",
            data_dir / "R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json",
        ]
        records.append(
            {
                "figure": 46,
                "panel": "a",
                "slug": output.stem,
                "source": str(SOURCE_FILES[46].relative_to(ECT_ROOT)),
                "source_sha256": sha256(SOURCE_FILES[46]),
                "owner_generator": "LaTex/scripts/cosmology/make_r103_corrected_cosmology_figures.py",
                "owner_generator_sha256": sha256(LATEX_ROOT / "scripts/cosmology/make_r103_corrected_cosmology_figures.py"),
                "input_files": [str(p.relative_to(ECT_ROOT)) for p in inputs],
                "input_sha256": {str(p.relative_to(ECT_ROOT)): sha256(p) for p in inputs},
                "output": f"assets/{name}",
                "output_sha256": sha256(output),
                "method": method,
                "status": "Level C same-metric, zero-slip, sub-horizon proxies; not projected spectra",
                "text_metrics": text_metrics(output),
            }
        )

    for item in render_hatchfree_hrc_panels(assets):
        output = item["path"]
        inputs = item["inputs"]
        records.append(
            {
                "figure": item["figure"],
                "panel": item["panel"],
                "slug": output.stem,
                "source": str(SOURCE_FILES[item["figure"]].relative_to(ECT_ROOT)),
                "source_sha256": sha256(SOURCE_FILES[item["figure"]]),
                "owner_generator": (
                    "LaTex/scripts/hrc/make_r97_hrc_only_figures.py"
                    if item["figure"] == 17
                    else "LaTex/scripts/hrc/make_r97_hrc_completion_figures.py"
                ),
                "owner_generator_sha256": sha256(
                    LATEX_ROOT
                    / (
                        "scripts/hrc/make_r97_hrc_only_figures.py"
                        if item["figure"] == 17
                        else "scripts/hrc/make_r97_hrc_completion_figures.py"
                    )
                ),
                "input_files": [str(p.relative_to(ECT_ROOT)) for p in inputs],
                "input_sha256": {str(p.relative_to(ECT_ROOT)): sha256(p) for p in inputs},
                "output": f"assets/{output.name}",
                "output_sha256": sha256(output),
                "method": item["method"],
                "status": item["status"],
                "decorative_texture_removed": True,
                "text_metrics": text_metrics(output),
            }
        )

    records.sort(key=lambda r: (r["figure"], r["panel"], r["output"]))
    color_images = []
    for rec in records:
        pdf = output_root / rec["output"]
        png = color_dir / (pdf.stem + ".png")
        render_png(pdf, png)
        rec["color_preview"] = str(png.relative_to(output_root))
        rec["color_preview_sha256"] = sha256(png)
        color_images.append((pdf.stem, png))

    for mode in ("color", "gray", "protan", "deutan", "tritan"):
        build_contact(color_images, output_root / "previews" / f"R123_P1_PANEL_CONTACT_{mode}.png", mode)

    for record in records:
        width = FAMILY_POLICY[record["figure"]]["widths"][record["panel"]]
        minimum = record["text_metrics"]["minimum_primary_text_pt"]
        record["recommended_width_fraction"] = width
        record["effective_minimum_primary_text_pt"] = None if minimum is None else minimum * width
        record["selected_for_bounded_main"] = record["panel"] in FAMILY_POLICY[record["figure"]]["main_panels"]

    hard_fail = [
        r["output"]
        for r in records
        if r["effective_minimum_primary_text_pt"] is not None
        and r["effective_minimum_primary_text_pt"] < 7.0 - 1e-6
    ]
    preferred_fail = [
        r["output"]
        for r in records
        if r["effective_minimum_primary_text_pt"] is not None
        and r["effective_minimum_primary_text_pt"] < 8.0 - 1e-6
    ]
    by_figure: dict[int, list[dict]] = {}
    for record in records:
        by_figure.setdefault(record["figure"], []).append(record)
    ledger_path = manifests / "R123_P1_PANEL_COMPLETION_LEDGER_v1.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "figure",
            "source",
            "source_sha256",
            "output_count",
            "outputs",
            "recommended_main_preprint_placement",
            "main_owner_outputs",
            "main_page_estimate",
            "main_omissions_disposition",
            "full_supplement_placement",
            "full_supplement_page_estimate",
            "recommended_width_fractions_by_panel",
            "minimum_primary_text_pt",
            "effective_minimum_at_recommended_width_pt",
            "preferred_8pt_all",
            "hard_7pt_pass",
            "texture_action",
            "caption_delta",
            "scientific_arrays_changed",
            "scientific_status_changed",
            "rotation_comparators_added",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for figure, group in sorted(by_figure.items()):
            policy = FAMILY_POLICY[figure]
            minimum = min(r["text_metrics"]["minimum_primary_text_pt"] for r in group)
            effective_minimum = min(r["effective_minimum_primary_text_pt"] for r in group)
            selected = [Path(r["output"]).name for r in group if r["selected_for_bounded_main"]]
            omitted = [Path(r["output"]).name for r in group if not r["selected_for_bounded_main"]]
            width_string = ";".join(
                f"{r['panel']}={r['recommended_width_fraction']:.2f}" for r in sorted(group, key=lambda item: item["panel"])
            )
            writer.writerow(
                {
                    "figure": figure,
                    "source": str(SOURCE_FILES[figure].relative_to(ECT_ROOT)),
                    "source_sha256": sha256(SOURCE_FILES[figure]),
                    "output_count": len(group),
                    "outputs": ";".join(Path(r["output"]).name for r in group),
                    "recommended_main_preprint_placement": policy["main"],
                    "main_owner_outputs": ";".join(selected) if selected else "NONE_IN_THIS_COMPONENT",
                    "main_page_estimate": policy["main_pages"],
                    "main_omissions_disposition": (
                        "all outputs selected for main"
                        if not omitted
                        else "full-resolution reproducibility supplement: " + ";".join(omitted)
                    ),
                    "full_supplement_placement": policy["supplement"],
                    "full_supplement_page_estimate": policy["supplement_pages"],
                    "recommended_width_fractions_by_panel": width_string,
                    "minimum_primary_text_pt": f"{minimum:.3f}",
                    "effective_minimum_at_recommended_width_pt": f"{effective_minimum:.3f}",
                    "preferred_8pt_all": str(effective_minimum >= 8.0).upper(),
                    "hard_7pt_pass": str(effective_minimum >= 7.0).upper(),
                    "texture_action": policy["texture"],
                    "caption_delta": policy["caption_delta"],
                    "scientific_arrays_changed": "FALSE",
                    "scientific_status_changed": "FALSE",
                    "rotation_comparators_added": "FALSE",
                }
            )

    manifest = {
        "schema": "ECT_R123_P1_PANEL_RELAYOUT_v1",
        "status": "PROPOSAL_ONLY_NO_LIVE_EDIT",
        "fixed_build_date": "2026-07-21T00:00:00Z",
        "generator": str(SCRIPT.relative_to(ECT_ROOT)),
        "generator_sha256": sha256(SCRIPT),
        "palette": str(PALETTE_PATH.relative_to(ECT_ROOT)),
        "palette_sha256": sha256(PALETTE_PATH),
        "render_environment": {
            "python": platform.python_version(),
            "pymupdf": fitz.VersionBind,
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pillow": PIL.__version__,
            "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        },
        "render_command": "python3 scripts/build_r123_p1_panel_relayout.py --output-root <owned-output-root>",
        "policy": {
            "target_primary_text_pt": 8.0,
            "hard_floor_primary_text_pt": 7.0,
            "hard_floor_is_evaluated_after_recommended_tex_scaling": True,
            "bounded_main_page_estimate_excluding_sibling_figure_18_replacement": sum(
                policy["main_pages"] for policy in FAMILY_POLICY.values()
            ),
            "full_reproducibility_supplement_page_estimate": sum(
                policy["supplement_pages"] for policy in FAMILY_POLICY.values()
            ),
            "full_readability_main_page_estimate": len(records),
            "full_readability_page_delta_vs_16_original_compounds": len(records) - len(FAMILY_POLICY),
            "bounded_main_panel_count": sum(len(panels) for panels in BOUNDED_MAIN_SELECTION.values()),
            "bounded_main_page_delta_vs_15_non_figure18_compounds": (
                sum(policy["main_pages"] for policy in FAMILY_POLICY.values()) - (len(FAMILY_POLICY) - 1)
            ),
            "original_composite_count_in_this_component": len(FAMILY_POLICY),
            "reduced_one-character_math_scripts_reported_separately": True,
            "colour_only_semantics": False,
            "hatch_is_primary_channel": False,
            "scientific_arrays_changed": False,
            "scientific_status_changed": False,
            "rotation_comparators_added": False,
        },
        "hard_floor_failures": hard_fail,
        "preferred_target_exceptions": preferred_fail,
        "family_completion_ledger": str(ledger_path.relative_to(output_root)),
        "family_completion_ledger_sha256": sha256(ledger_path),
        "outputs": records,
    }
    (manifests / "R123_P1_PANEL_RELAYOUT_MANIFEST_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(args.output_root.resolve())
    print(
        json.dumps(
            {
                "outputs": len(manifest["outputs"]),
                "hard_floor_failures": manifest["hard_floor_failures"],
                "preferred_target_exceptions": len(manifest["preferred_target_exceptions"]),
                "manifest": str(args.output_root / "manifests/R123_P1_PANEL_RELAYOUT_MANIFEST_v1.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
