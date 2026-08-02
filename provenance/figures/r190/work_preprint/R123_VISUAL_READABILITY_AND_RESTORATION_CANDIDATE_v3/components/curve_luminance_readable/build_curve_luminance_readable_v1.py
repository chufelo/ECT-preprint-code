#!/usr/bin/env python3
"""Build the proposal-only R123 luminance/readability curve overlay.

The builder replays the frozen HRC/cosmology/evolution producers, changes only
the publication palette and typography, and creates 16 active single-panel
PDFs plus two restored evolution PDFs.  Twelve inherited multi-panel crops for
Figures 18--20 are retained only as WITHDRAWN_NOT_FOR_INSTALL provenance; a
separate direct-render rotation-atlas component owns their replacements.  This
builder never writes the live manuscript, live figure tree, Git index, or
remote.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")

SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parent


def find_root() -> Path:
    for parent in SCRIPT.parents:
        if (parent / "LaTex/ECT_preprint.tex").is_file():
            return parent
    raise RuntimeError("ECT workspace root not found")


ROOT = find_root()
LATEX = ROOT / "LaTex"
V1 = LATEX / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"
V2 = LATEX / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v2"
FULL_V3 = V1 / "components/curve_luminance_full_v3"
PANEL_BUILDER = V1 / "components/global_visual_remediation/p1_panel_work/scripts/build_r123_p1_panel_relayout.py"
EVOLUTION_WORDING = V1 / "components/evolution_wording_v2/scripts/build_evolution_wording_v2.py"

EXPECTED_FULL_BUILDER = "df15a100560de67365cfcf6b2dde4f253a200be054067e2f84d909ce0932ba92"
EXPECTED_PANEL_BUILDER = "8f6f4da993d8fafd94ddf887c8ddf94f718b880a8a2c71e1edb1f0b0dbcb9ba4"
EXPECTED_EVOLUTION_WORDING = "7bfc81219e0ee9c5b49cf8177dc12368185ca129e78393d52cb6fa8a789800e4"

# Ordered luminance ramp inherited from curve_luminance_full_v3.  D65 CIELAB
# L*: 6.319, 17.533, 28.444, 39.523, 50.643, 61.412.
DATA = "#141414"
BARYON = "#2B2B2B"
NFW = "#762A22"
MOND = "#6E4E96"
HRC0 = "#267EBC"
HRC3 = "#51A56B"
PALETTE = [DATA, BARYON, NFW, MOND, HRC0, HRC3]
MIN_SOURCE_TEXT_PT = 11.0
MIN_DIRECT_PANEL_TEXT_PT = 14.0
PDF_SAFE_PAD_PT = 18.0
# The evolution figures carry substantially more prose than the compact curve
# panels.  A 13.5-pt blanket floor made the scientifically correct labels
# overlap.  Eleven-point primary type on a larger canvas is both readable at the
# manuscript width and preserves the intended information hierarchy.
MIN_EVOLUTION_TEXT_PT = 11.0

EVOLUTION_LAYOUT_REPLACEMENTS = (
    (
        "fig, axes = plt.subplots(2, 2, figsize=(7.0, 6.3))",
        "fig, axes = plt.subplots(2, 2, figsize=(9.4, 8.4))",
    ),
    (
        "fig.subplots_adjust(left=0.085, right=0.91, bottom=0.12, top=0.89, wspace=0.30, hspace=0.36)",
        "fig.subplots_adjust(left=0.080, right=0.905, bottom=0.135, top=0.900, wspace=0.34, hspace=0.43)",
    ),
    (
        "        figsize=(7.0, 5.9),",
        "        figsize=(9.4, 7.5),",
    ),
    (
        "fig.subplots_adjust(left=0.075, right=0.975, bottom=0.14, top=0.88, hspace=0.43)",
        "fig.subplots_adjust(left=0.090, right=0.975, bottom=0.165, top=0.810, hspace=0.62)",
    ),
    (
        "        1.08,\n        \"Formation/front selection: Open\\nsolver enters an already ordered regular branch\",",
        "        1.04,\n        \"Formation/front selection: Open\\nsolver enters an already ordered regular branch\",",
    ),
)

TARGET_PREFIXES = (
    "fig15_", "fig16_", "fig17_", "fig18_", "fig19_", "fig20_",
    "fig42_", "fig43_a", "fig43_b", "fig44_a",
)
EVOLUTION_TARGETS = (
    "r123_conditional_post_ordering_evolution.pdf",
    "r123_conditional_chronology.pdf",
)
WITHDRAWN_PREFIXES = ("fig18_", "fig19_", "fig20_")
EXPECTED_ACTIVE_OVERLAYS = 18
EXPECTED_WITHDRAWN_CROPS = 12

# The crop owner deliberately left little room around some secondary axes.
# These bounded source-coordinate changes recover the whole label while never
# reaching the neighbouring panel.  Data coordinates and plotted artists are
# unchanged.
SAFE_CLIPS = {
    "fig15_a_btfr_tail_proxy_r123": (30, 20, 436, 320),
    # The original middle-panel crop began at the plotting spine and therefore
    # cut the y tick labels and axis title.  The source gutter is empty to x=282.
    "fig16_b_hrc3_ml_coupling_r123": (282, 25, 585, 285),
    "fig17_a_response_laws_r123": (30, 20, 428, 300),
    # Rotation-sheet gutters lie at x~=370.  Include the complete y labels on
    # both columns rather than starting each crop at the plotting spine.
    "fig18_a_ddo154_r123": (0, 84, 370, 310),
    "fig18_b_ngc2403_r123": (370, 84, 745.574, 310),
    "fig18_c_ngc3198_r123": (0, 309, 370, 538.464),
    "fig18_d_ngc6503_r123": (370, 309, 745.574, 538.464),
    # Each gallery overlay owns two source columns.  The wider bounds retain
    # the first-column velocity ticks and the second-row radial ticks.
    "fig19_a_gallery_lowacc_1_r123": (0, 55, 430, 420),
    "fig19_b_gallery_lowacc_2_r123": (430, 55, 853.534, 420),
    "fig19_c_gallery_highacc_1_r123": (0, 390, 430, 780.538),
    "fig19_d_gallery_highacc_2_r123": (430, 390, 853.534, 780.538),
    "fig20_a_ugc02953_r123": (0, 84, 370, 312),
    "fig20_b_ugc09133_r123": (370, 84, 745.484, 312),
    "fig20_c_ngc6946_r123": (0, 309, 370, 539.004),
    "fig20_d_ngc7331_r123": (370, 309, 745.484, 539.004),
    "fig42_a_named_expansion_r123": (47, 0, 335, 270),
    "fig42_b_clock_budget_r123": (315, 0, 630, 270),
    "fig42_c_comoving_distance_r123": (642, 0, 943, 270),
    "fig42_d_background_w_r123": (47, 264, 335, 541),
    "fig42_e_calibrated_family_r123": (330, 264, 630, 541),
    "fig42_f_scope_statement_r123": (642, 264, 958, 541),
    # The component supplies its own concise shared header.  Starting at y=22
    # removes the duplicate full-sheet title while preserving each panel title.
    "fig43_a_two_slope_expansion_r123": (40, 22, 279, 330),
    "fig43_b_two_slope_w_r123": (275, 22, 522, 330),
}

INSTALL_ROOT = "figures/r123/global/panels"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def assert_frozen_sources() -> None:
    expected = {
        FULL_V3 / "build_full_curve_luminance_v3.py": EXPECTED_FULL_BUILDER,
        PANEL_BUILDER: EXPECTED_PANEL_BUILDER,
        EVOLUTION_WORDING: EXPECTED_EVOLUTION_WORDING,
    }
    failures = []
    for path, digest in expected.items():
        actual = sha(path)
        if actual != digest:
            failures.append(f"{path}: expected {digest}, got {actual}")
    if failures:
        raise RuntimeError("Frozen producer guard failed:\n" + "\n".join(failures))


@contextlib.contextmanager
def minimum_matplotlib_text(size_pt: float, *, skip_png: bool = True):
    """Raise only typography; arrays, axes and artists remain untouched."""
    from matplotlib.figure import Figure
    from matplotlib.text import Text

    original = Figure.savefig

    def guarded(self, *args, **kwargs):
        destination = args[0] if args else kwargs.get("fname")
        if skip_png and destination is not None and Path(destination).suffix.lower() == ".png":
            return None
        # Tick/offset Text artists are instantiated lazily.  Draw first so the
        # floor applies to them as well as titles, legends and annotations.
        self.canvas.draw()
        for text in self.findobj(match=Text):
            content = text.get_text()
            if content and float(text.get_fontsize()) < size_pt:
                text.set_fontsize(size_pt)
        return original(self, *args, **kwargs)

    Figure.savefig = guarded
    try:
        yield
    finally:
        Figure.savefig = original


@contextlib.contextmanager
def suppress_matplotlib_hatch():
    """Discard decorative hatch at render time while preserving patch geometry.

    Some frozen two-panel source PDFs put a hatch pattern in a neighbouring
    panel.  A vector crop then imports that unused resource even when the
    visible target panel contains no hatch.  Suppressing the hatch on the
    frozen replay removes both visible texture and the hidden PDF pattern
    resource; patch extents, bins, bar heights and line geometry are untouched.
    """
    from matplotlib.patches import Patch

    original = Patch.set_hatch

    def no_hatch(self, hatch):
        return original(self, None)

    Patch.set_hatch = no_hatch
    try:
        yield
    finally:
        Patch.set_hatch = original


def set_panel_palette(p) -> None:
    p.PAL.HRC0 = HRC0
    p.PAL.HRC3 = HRC3
    p.PAL.LEVEL_C_EDGE = MOND
    p.PAL.GRAPHITE = BARYON
    p.PAL.TENSION_EDGE = NFW
    # Pale fills remain secondary; no hatch/pattern is introduced.


def rebuild_font_sensitive_sources(full, sources: Path) -> None:
    """Re-render only the two source sheets whose math spans were <7.5 pt."""
    hrc = full.load("r97_completion_readable_v1", LATEX / "scripts/hrc/make_r97_hrc_completion_figures.py")
    hrc.OUT = sources / "hrc"
    full.set_hrc_palette(hrc)
    rows = full.numeric_rows(LATEX / "data/hrc_r97/R97_HRC_PER_GALAXY_FITS.csv")
    with suppress_matplotlib_hatch(), minimum_matplotlib_text(MIN_SOURCE_TEXT_PT):
        hrc.btfr_and_scale_figure(rows)
        hrc.ml_sensitivity_figure(rows)

    r114 = full.load("r114_closure_readable_v1", LATEX / "scripts/figures/make_r114_closure_figures.py")
    r114.BLUE, r114.GREEN, r114.ORANGE, r114.PURPLE = HRC0, HRC3, MOND, NFW
    r114.VERMILION, r114.BLACK, r114.GRAY = NFW, DATA, BARYON
    r114.configure()
    early_csv = LATEX / "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv"
    rows = r114.read_early_rows(early_csv)
    with minimum_matplotlib_text(MIN_SOURCE_TEXT_PT):
        r114.early_response_figure(rows, sources / "cosmology/r114_early_response_growth_collapse_envelope")


def safe_compose_crop(p, spec, source, output: Path) -> dict:
    """Compose a bounded source crop while keeping all original vectors."""
    import fitz

    src = fitz.open(source)
    page0 = src[0]
    coordinates = SAFE_CLIPS.get(spec.stem, spec.clip)
    clip = fitz.Rect(*coordinates) & page0.rect
    if clip.is_empty or clip.width < 50 or clip.height < 50:
        raise RuntimeError(f"invalid crop for {spec.stem}: {clip}")
    header_height = (19.0 if spec.header else 0.0) + (14.0 if spec.key else 0.0)
    footer_height = 27.0 if spec.footer else 0.0
    target_width = p.PAGE_WIDTH_PT - 2 * p.MARGIN_PT
    scale = target_width / clip.width
    target_height = clip.height * scale
    page_height = p.MARGIN_PT + header_height + target_height + footer_height + p.MARGIN_PT
    out = fitz.open()
    page = out.new_page(width=p.PAGE_WIDTH_PT, height=page_height)
    y = p.MARGIN_PT
    if spec.header:
        y = p.insert_centered_text(page, y, spec.header, 10.5, bold=True)
    if spec.key:
        y = p.insert_centered_text(page, y, spec.key, 8.2, color=(0.28, 0.28, 0.28))
    dst = fitz.Rect(p.MARGIN_PT, y, p.PAGE_WIDTH_PT - p.MARGIN_PT, y + target_height)
    page.show_pdf_page(dst, src, 0, clip=clip, keep_proportion=True)
    if spec.footer:
        p.insert_centered_text(page, dst.y1 + 3.0, spec.footer, 8.2, color=(0.28, 0.28, 0.28))
    out.set_metadata(p.fitz_metadata(spec.stem))
    output.parent.mkdir(parents=True, exist_ok=True)
    out.save(output, garbage=4, deflate=True, clean=True, no_new_id=True)
    out.close()
    src.close()
    return {
        "source_clip": [round(float(v), 3) for v in coordinates],
        "scale": scale,
        "source_sha256": sha(source),
    }


def render_fig43b_direct(p, source_csv: Path, output: Path) -> dict:
    """Replay the central two-slope w panel without clipping global text.

    The old crop necessarily intersected a full-sheet title and footer.  This
    bounded replay uses the same frozen columns and artists as the owner, but
    lays out the central panel as a self-contained publication figure.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    x = np.log1p(np.asarray([float(row["z"]) for row in rows]))
    reference = np.asarray([float(row["w_eff_reference"]) for row in rows])
    two_slope = np.asarray([float(row["w_eff_two_slope"]) for row in rows])
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(6.6, 4.9))
        ax.plot(x, reference, color=DATA, marker="s", ls="--", lw=1.7, label="matched control")
        ax.plot(
            x,
            two_slope,
            color=HRC3,
            marker="^",
            markerfacecolor="white",
            markeredgewidth=1.5,
            ls="-.",
            lw=2.0,
            label="two-slope",
        )
        ax.set_xlabel(r"$\ln(1+z)$")
        ax.set_ylabel(r"$w_{\rm eff}=-1-2H'/(3H)$")
        ax.set_title(r"Conditional two-slope state: total kinematic $w_{\rm eff}$")
        ax.grid(True, color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="lower right")
        ax.text(0.03, 0.93, "curves overlap at this scale", transform=ax.transAxes, va="top")
        fig.text(
            0.5,
            0.018,
            "Supplied action/state; Level C observable diagnostic; not a unique P1--P6 cosmology.",
            ha="center",
            va="bottom",
            color=BARYON,
            fontsize=MIN_SOURCE_TEXT_PT,
        )
        fig.tight_layout(rect=(0.0, 0.075, 1.0, 1.0))
        p.save_mpl(fig, output)
    return {
        "method": "direct frozen-column replay replacing an intrinsically clipped sheet crop",
        "input": str(source_csv.relative_to(ROOT)),
        "input_sha256": sha(source_csv),
        "numeric_payload": numeric_signature(source_csv),
        "row_count": len(rows),
    }


def render_fig16_coupling_direct(p, source_csv: Path, model: str, output: Path) -> dict:
    """Replay one scale--M/L coupling panel from the frozen per-galaxy table."""
    import matplotlib.pyplot as plt
    import numpy as np

    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    fixed = np.asarray([float(row[f"aM_{model}_over_match"]) for row in rows])
    free = np.asarray([float(row[f"aM_{model}_freeML_over_match"]) for row in rows])
    colour = HRC0 if model == "HRC0" else HRC3
    marker = "o" if model == "HRC0" else "s"
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(6.3, 5.1))
        ax.scatter(
            fixed,
            free,
            s=28,
            marker=marker,
            facecolor="white",
            edgecolor=colour,
            linewidth=1.2,
            alpha=1.0,
            label=f"{model.replace('HRC', 'HRC-')} galaxy fits",
        )
        limits = (1.0e-2, 1.0e2)
        ax.plot(limits, limits, color=DATA, lw=1.7, ls=":", label="unchanged fitted scale")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(limits)
        ax.set_ylim(limits)
        ax.set_xlabel(r"fixed-$M/L$ $a_M/a_{M0}$")
        ax.set_ylabel(r"free-$M/L$ $a_M/a_{M0}$")
        ax.set_title(f"{model.replace('HRC', 'HRC-')}: scale--$M/L$ coupling")
        ax.grid(True, which="both", color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="upper left")
        fig.tight_layout()
        p.save_mpl(fig, output)
    return {
        "method": "direct frozen-column replay replacing a crop that omitted the y-axis label",
        "input": str(source_csv.relative_to(ROOT)),
        "input_sha256": sha(source_csv),
        "numeric_payload": numeric_signature(source_csv),
        "row_count": len(rows),
        "model": model,
    }


def render_fig15a_btfr_direct(p, source_csv: Path, output: Path) -> dict:
    """Replay the BTFR/tail panel without importing the adjacent histogram axis."""
    import matplotlib.pyplot as plt
    import numpy as np

    hrc = load("r123_fig15a_constants_v1", LATEX / "scripts/hrc/make_r97_hrc_completion_figures.py")
    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    good = [row for row in rows if float(row["Mbar_eff_Msun"]) > 0 and float(row["Vflat_obs_km_s"]) > 0]
    x = np.log10([float(row["Mbar_eff_Msun"]) for row in good])
    y = np.log10([float(row["Vflat_obs_km_s"]) for row in good])
    xx = np.linspace(float(np.min(x)) - 0.2, float(np.max(x)) + 0.2, 250)

    def line(acceleration):
        return np.log10((hrc.G_SI * 10.0**xx * hrc.MSUN * acceleration) ** 0.25 / 1000.0)

    fitted0 = float(np.median([float(row["aM_HRC0_si"]) for row in rows]))
    fitted3 = float(np.median([float(row["aM_HRC3_si"]) for row in rows]))
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(7.0, 5.2))
        ax.scatter(x, y, s=24, facecolor="white", edgecolor=DATA, linewidth=0.9, label="SPARC tail proxies")
        ax.plot(xx, line(hrc.A_MATCH), color=DATA, lw=2.0, ls=":", label=r"matched $a_{M0}$")
        ax.plot(xx, line(fitted0), color=HRC0, lw=2.2, ls="--", label="median HRC-0 scale")
        ax.plot(xx, line(fitted3), color=HRC3, lw=2.2, ls="-", label="median HRC-3 scale")
        ax.set_xlabel(r"$\log_{10}(M_{\rm bar,eff}/M_\odot)$")
        ax.set_ylabel(r"$\log_{10}(V_{\rm flat}/{\rm km\,s^{-1}})$")
        ax.set_title("Conditional BTFR and tail proxies")
        ax.grid(True, color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="upper left")
        fig.tight_layout()
        p.save_mpl(fig, output)
    return {
        "method": "direct frozen-column BTFR replay; adjacent histogram resources excluded",
        "input": str(source_csv.relative_to(ROOT)),
        "input_sha256": sha(source_csv),
        "numeric_payload": numeric_signature(source_csv),
        "row_count": len(rows),
        "tail_proxy_count": len(good),
    }


def render_fig17a_response_direct(p, output: Path) -> dict:
    """Replay the analytic HRC response laws as an independent full panel."""
    import matplotlib.pyplot as plt
    import numpy as np

    owner_path = LATEX / "scripts/hrc/make_r97_hrc_only_figures.py"
    owner = load("r123_fig17a_owner_v1", owner_path)
    x = np.logspace(-3, 3, 800)
    mu0 = np.asarray(owner.mu0(x), dtype=float)
    mu3 = np.asarray(owner.mu3(x), dtype=float)
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(7.0, 5.0))
        ax.plot(x, mu0, color=HRC0, lw=2.5, ls="--", label="HRC-0")
        ax.plot(x, mu3, color=HRC3, lw=2.5, ls="-", label="HRC-3")
        ax.set_xscale("log")
        ax.set_xlabel(r"$x=g/a_M$")
        ax.set_ylabel(r"$\mu_{\rm HRC}(x)$")
        ax.set_title("HRC response laws")
        ax.grid(True, which="both", color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="upper left")
        fig.tight_layout()
        p.save_mpl(fig, output)
    payload = "\n".join(f"{a:.17g},{b:.17g},{c:.17g}" for a, b, c in zip(x, mu0, mu3)) + "\n"
    return {
        "method": "direct analytic owner replay; adjacent regime-diagnostic axis excluded",
        "input": str(owner_path.relative_to(ROOT)),
        "input_sha256": sha(owner_path),
        "sample_count": len(x),
        "curve_payload_sha256": hashlib.sha256(payload.encode("ascii")).hexdigest(),
    }


def render_fig42_background_direct(p, data_json: Path, scan_json: Path, assets: Path) -> dict:
    """Replay all six background-diagnostic cells as self-contained panels."""
    import matplotlib.pyplot as plt
    import numpy as np

    data = json.loads(data_json.read_text(encoding="utf-8"))
    scan = json.loads(scan_json.read_text(encoding="utf-8"))
    rows = sorted(data["rows"], key=lambda row: row["z"])
    x = np.log1p(np.asarray([row["z"] for row in rows], dtype=float))
    p.configure_matplotlib()
    provenance = {}

    def finish(filename: str, draw) -> None:
        target = assets / filename
        with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
            fig, ax = plt.subplots(figsize=(6.8, 5.0))
            draw(fig, ax)
            fig.tight_layout()
            p.save_mpl(fig, target)
        provenance[filename] = {
            "method": "direct frozen JSON replay; neighbouring 2x3 cells excluded",
            "inputs": [str(data_json.relative_to(ROOT)), str(scan_json.relative_to(ROOT))],
            "input_sha256": {data_json.name: sha(data_json), scan_json.name: sha(scan_json)},
        }

    def common(ax):
        ax.grid(True, color="#D8D8D8", linewidth=0.7)

    finish("fig42_a_named_expansion_r123.pdf", lambda fig, ax: (
        ax.plot(x, [row["delta_E_percent"] for row in rows], color=HRC0, marker="o", ls="-", lw=2.0),
        ax.axhline(0.0, color=DATA, lw=1.2, ls=":"),
        ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$\Delta H/H_{\rm ctl}$ [\%]", title="Named two-slope expansion"),
        common(ax),
    ))
    finish("fig42_b_clock_budget_r123.pdf", lambda fig, ax: (
        ax.plot(x, [row["H0_t_two_slope"] for row in rows], color=HRC0, marker="o", lw=2.0, label="two-slope"),
        ax.plot(x, [row["H0_t_reference"] for row in rows], color=DATA, marker="s", ls="--", lw=1.7, label="matched control"),
        ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$H(0)t(z)$", title="Conditional clock budget"),
        common(ax), ax.legend(frameon=False),
    ))
    finish("fig42_c_comoving_distance_r123.pdf", lambda fig, ax: (
        ax.plot(x[1:], [row["delta_chi_percent"] for row in rows[1:]], color=HRC3, marker="^", ls="-.", lw=2.0),
        ax.axhline(0.0, color=DATA, lw=1.2, ls=":"),
        ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$\Delta\chi/\chi_{\rm ctl}$ [\%]", title="Conditional comoving distance"),
        common(ax),
    ))
    finish("fig42_d_background_w_r123.pdf", lambda fig, ax: (
        ax.plot(x, [row["w_eff_two_slope"] for row in rows], color=HRC0, marker="o", lw=2.0, label="two-slope"),
        ax.plot(x, [row["w_eff_reference"] for row in rows], color=DATA, marker="s", ls="--", lw=1.7, label="matched control"),
        ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$w_{\rm eff}=-1-2H'/(3H)$", title="Total background equation of state"),
        common(ax), ax.legend(frameon=False),
    ))

    markers = {0.01: "o", 0.03: "s", 0.08: "^"}
    colours = {0.05: NFW, 1.0: MOND, 10.0: HRC3}

    def draw_family(fig, ax):
        for row in scan["rows"]:
            ax.scatter(
                100.0 * (row["H0_t0"] / scan["reference_age_H0t0"] - 1.0),
                row["diagnostics"]["z=10"]["delta_t_percent"],
                color=colours[row["kappa"]],
                marker=markers[row["a"]],
                s=95,
                edgecolor=DATA,
                linewidth=0.8,
            )
        ax.axhline(0.0, color=DATA, lw=1.2, ls=":")
        ax.axvline(0.0, color=DATA, lw=1.2, ls=":")
        ax.set_xlabel(r"$\Delta t_0$ [\%]")
        ax.set_ylabel(r"$\Delta t(z=10)$ [\%]")
        ax.set_title(r"Calibrated $3\times3$ family")
        ax.locator_params(axis="x", nbins=5)
        common(ax)
        ax.text(0.98, 0.05, r"colour: $\kappa_s$; marker: $a_s$", transform=ax.transAxes, ha="right")

    finish("fig42_e_calibrated_family_r123.pdf", draw_family)

    def draw_scope(fig, ax):
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(0.04, 0.94, "Conditional supplied-action outputs", va="top", weight="bold", fontsize=18)
        items = [
            "not a unique P1--P6 cosmology",
            r"$H_0$ is one declared unit/state calibration",
            r"$w_{\rm eff}$ is total background kinematics, not $w_{\rm DE}$",
            "photon/perturbation likelihood owners remain Open",
        ]
        colours_local = [NFW, HRC0, MOND, HRC3]
        for index, (text, colour) in enumerate(zip(items, colours_local)):
            y = 0.76 - 0.17 * index
            ax.scatter([0.07], [y], s=80, color=colour, edgecolor=DATA, linewidth=0.6)
            ax.text(0.12, y, text, va="center", fontsize=14)

    finish("fig42_f_scope_statement_r123.pdf", draw_scope)
    return provenance


def render_fig43a_direct(p, source_csv: Path, output: Path) -> dict:
    """Replay the two-slope expansion panel without the adjacent w axis."""
    import matplotlib.pyplot as plt
    import numpy as np

    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    x = np.log1p(np.asarray([float(row["z"]) for row in rows]))
    delta = np.asarray([float(row["delta_E_percent"]) for row in rows])
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(6.6, 4.9))
        ax.plot(x, delta, color=HRC0, marker="o", ls="-", lw=2.0, label="two-slope / control")
        ax.axhline(0.0, color=DATA, lw=1.2, ls=":")
        ax.set_xlabel(r"$\ln(1+z)$")
        ax.set_ylabel(r"$100(H_{2s}/H_{\rm ctl}-1)$ [\%]")
        ax.set_title("Conditional two-slope state: expansion response")
        ax.grid(True, color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="upper left")
        fig.text(0.5, 0.018, "Supplied action/state; Level C observable diagnostic; not a unique P1--P6 cosmology.", ha="center", va="bottom", color=BARYON, fontsize=MIN_SOURCE_TEXT_PT)
        fig.tight_layout(rect=(0.0, 0.075, 1.0, 1.0))
        p.save_mpl(fig, output)
    return {
        "method": "direct frozen-column replay replacing an intrinsically contaminated sheet crop",
        "input": str(source_csv.relative_to(ROOT)),
        "input_sha256": sha(source_csv),
        "numeric_payload": numeric_signature(source_csv),
        "row_count": len(rows),
    }


def render_fig44a_direct(p, source_csv: Path, output: Path) -> dict:
    """Replay growth/equality response without the neighbouring rare-tail axis."""
    import matplotlib.pyplot as plt
    import numpy as np

    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    zeta = np.asarray([row["zeta_ER"] for row in rows])
    growth = np.asarray([row["D_over_D0_z10_zon1000"] for row in rows])
    equality = np.asarray([row["equality_ratio"] for row in rows])
    p.configure_matplotlib()
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        fig, ax = plt.subplots(figsize=(7.0, 5.1))
        ax.plot(zeta, growth, color=HRC0, lw=2.2, ls="-", marker="o", markeredgecolor=DATA, label=r"growth $D/D_0$")
        ax.plot(zeta, equality, color=MOND, lw=2.2, ls="--", marker="D", markeredgecolor=DATA, label="equality-coordinate ratio")
        ax.axhline(1.0, color=BARYON, lw=1.3, ls=":", label="control ratio = 1")
        ax.set_xscale("log")
        ax.set_xlabel(r"owner coordinate $\zeta_{\rm ER}$")
        ax.set_ylabel("dimensionless ratio")
        ax.set_title("Growth and equality response")
        ax.grid(True, color="#D8D8D8", linewidth=0.7)
        ax.legend(frameon=False, loc="upper left")
        ax.annotate(f"{growth[-1]:.3f}", (zeta[-1], growth[-1]), xytext=(-36, 8), textcoords="offset points", color=HRC0)
        ax.annotate(f"{equality[-1]:.3f}", (zeta[-1], equality[-1]), xytext=(-38, -18), textcoords="offset points", color=DATA)
        fig.tight_layout()
        p.save_mpl(fig, output)
    return {
        "method": "direct frozen-column replay; adjacent Press--Schechter sensitivity axis excluded",
        "input": str(source_csv.relative_to(ROOT)),
        "input_sha256": sha(source_csv),
        "numeric_payload": numeric_signature(source_csv),
        "row_count": len(rows),
    }


def add_vector_safe_margin(path: Path, padding_pt: float = PDF_SAFE_PAD_PT) -> None:
    """Add a literal vector page margin without rasterising or rescaling.

    ``bbox_inches='tight'`` and source-sheet crops can leave complete glyphs
    only a few points from the MediaBox.  A new page containing the original
    PDF page at a fixed offset gives every text span a machine-verifiable safe
    edge.  Scientific coordinates within the embedded page are unchanged.
    """
    import fitz

    source = fitz.open(path)
    output = fitz.open()
    for source_page in source:
        width = source_page.rect.width + 2.0 * padding_pt
        height = source_page.rect.height + 2.0 * padding_pt
        page = output.new_page(width=width, height=height)
        target = fitz.Rect(
            padding_pt,
            padding_pt,
            padding_pt + source_page.rect.width,
            padding_pt + source_page.rect.height,
        )
        page.show_pdf_page(target, source, source_page.number, keep_proportion=True)
    output.set_metadata(source.metadata)
    temporary = path.with_suffix(".safe-margin.pdf")
    output.save(temporary, garbage=4, deflate=True, clean=True, no_new_id=True)
    output.close()
    source.close()
    temporary.replace(path)


def normalize_pdf(path: Path, title: str) -> None:
    """Remove volatile PDF metadata without rasterising or changing geometry."""
    import fitz

    doc = fitz.open(path)
    doc.set_metadata(
        {
            "title": title,
            "author": "ECT reproducibility workflow",
            "subject": "Proposal-only luminance/readability overlay; scientific arrays unchanged",
            "keywords": "ECT R123 gray-safe colour vector",
            "creator": SCRIPT.name,
            "producer": f"PyMuPDF {fitz.VersionBind}",
            "creationDate": "D:20260721000000Z",
            "modDate": "D:20260721000000Z",
        }
    )
    temporary = path.with_suffix(".normalized.pdf")
    doc.save(temporary, garbage=4, deflate=True, clean=True, no_new_id=True)
    doc.close()
    temporary.replace(path)


def wait_for_materialized_pdfs(root: Path, attempts: int = 80) -> None:
    """Wait for external-volume metadata/data visibility before vector crops."""
    paths = sorted(root.rglob("*.pdf"))
    pending = set(paths)
    for _ in range(attempts):
        finished = set()
        for path in pending:
            try:
                if path.stat().st_size > 1024 and path.read_bytes()[:5] == b"%PDF-":
                    finished.add(path)
            except OSError:
                pass
        pending -= finished
        if not pending:
            return
        time.sleep(0.1)
    raise RuntimeError("unmaterialized source PDFs: " + ", ".join(str(path) for path in sorted(pending)))


def numeric_signature(path: Path) -> dict:
    """Hash all numeric tokens in source order, independent of whitespace."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    tokens = re.findall(r"(?<![A-Za-z_])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", raw)
    canonical = "\n".join(format(float(token), ".17g") for token in tokens) + "\n"
    return {
        "path": str(path.relative_to(ROOT)),
        "raw_sha256": sha(path),
        "numeric_token_count": len(tokens),
        "numeric_payload_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
    }


def build_evolution(work_sources: Path) -> tuple[dict, dict]:
    wrapper = load("r123_evolution_wording_source_v1", EVOLUTION_WORDING)
    base = wrapper.BASE_GENERATOR
    source = base.read_text(encoding="utf-8")
    patched = wrapper.guarded_replace(source, wrapper.GENERATOR_REPLACEMENTS, "evolution-generator")
    for index, (old, new) in enumerate(EVOLUTION_LAYOUT_REPLACEMENTS, start=1):
        count = patched.count(old)
        if count != 1:
            raise RuntimeError(f"evolution-layout replacement {index}: expected one anchor, found {count}")
        patched = patched.replace(old, new, 1)
    namespace = {"__file__": str(base), "__name__": "r123_curve_evolution_replay", "__package__": None}
    exec(compile(patched, str(base), "exec"), namespace)
    output = work_sources / "evolution"
    namespace["OUT"] = output
    namespace["BLUE"], namespace["GREEN"] = HRC0, HRC3
    namespace["AMBER"], namespace["OPEN"] = MOND, MOND
    namespace["RED"], namespace["GRAY"] = NFW, BARYON
    with minimum_matplotlib_text(MIN_EVOLUTION_TEXT_PT):
        namespace["verify_inputs"]()
        namespace["configure"]()
        dense = namespace["load_csv"](namespace["INPUTS"]["dense"][0])
        obs = namespace["load_csv"](namespace["INPUTS"]["observables"][0])
        namespace["conditional_post_ordering"](dense, obs)
        namespace["conditional_chronology"](obs)
    inputs = {name: sha(path) for name, (path, _) in namespace["INPUTS"].items()}
    return inputs, {name: numeric_signature(path) for name, (path, _) in namespace["INPUTS"].items() if path.suffix in {".csv", ".json"}}


def build(output_root: Path) -> dict:
    assert_frozen_sources()
    assets = output_root / "assets"
    sources = output_root / "sources"
    withdrawn = output_root / "withdrawn"
    if assets.exists():
        shutil.rmtree(assets)
    if sources.exists():
        shutil.rmtree(sources)
    if withdrawn.exists():
        shutil.rmtree(withdrawn)
    assets.mkdir(parents=True)
    sources.mkdir(parents=True)
    withdrawn.mkdir(parents=True)

    full = load("r123_full_curve_luminance_source_v1", FULL_V3 / "build_full_curve_luminance_v3.py")
    full.COMP = output_root
    full.SOURCES = sources
    full.PANELS = assets
    full.SOURCES.mkdir(parents=True, exist_ok=True)
    full.PANELS.mkdir(parents=True, exist_ok=True)
    # First render at owner typography; the context is used only to suppress
    # disposable PNGs.  Two sub-7.5-pt sheets are replayed immediately below.
    with suppress_matplotlib_hatch(), minimum_matplotlib_text(0.1):
        hrc_provenance = full.build_hrc()
        cosmology_provenance = full.build_cosmology()
    rebuild_font_sensitive_sources(full, sources)
    wait_for_materialized_pdfs(sources)

    p = load("r123_panel_builder_source_v1", PANEL_BUILDER)
    p.SOURCE_FILES.update(
        {
            15: sources / "hrc/R97_HRC_BTFR_AND_SCALE.pdf",
            16: sources / "hrc/R97_HRC_ML_SENSITIVITY.pdf",
            17: sources / "hrc/R97_HRC_RESPONSE_AND_REGIMES.pdf",
            18: sources / "hrc/R97_HRC_ROTATION_EXAMPLES.pdf",
            19: sources / "hrc/R97_HRC_ROTATION_GALLERY.pdf",
            20: sources / "hrc/R97_HRC_RESIDUAL_STRESS.pdf",
            42: sources / "cosmology/r103_ect_background_clocks.pdf",
            43: sources / "cosmology/r103_two_slope_HwG_conditional.pdf",
            44: sources / "cosmology/r114_early_response_growth_collapse_envelope.pdf",
        }
    )
    set_panel_palette(p)
    with minimum_matplotlib_text(MIN_DIRECT_PANEL_TEXT_PT):
        p.render_hatchfree_hrc_panels(assets)
    crop_provenance = {}
    fits_csv = LATEX / "data/hrc_r97/R97_HRC_PER_GALAXY_FITS.csv"
    direct_fig15a = assets / "fig15_a_btfr_tail_proxy_r123.pdf"
    crop_provenance[direct_fig15a.name] = render_fig15a_btfr_direct(p, fits_csv, direct_fig15a)
    for model, filename in (
        ("HRC0", "fig16_a_hrc0_ml_coupling_r123.pdf"),
        ("HRC3", "fig16_b_hrc3_ml_coupling_r123.pdf"),
    ):
        target = assets / filename
        crop_provenance[target.name] = render_fig16_coupling_direct(p, fits_csv, model, target)
    direct_fig17a = assets / "fig17_a_response_laws_r123.pdf"
    crop_provenance[direct_fig17a.name] = render_fig17a_response_direct(p, direct_fig17a)
    crop_provenance.update(
        render_fig42_background_direct(
            p,
            LATEX / "data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json",
            LATEX / "data/cosmology_r103/R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json",
            assets,
        )
    )
    two_slope_csv = LATEX / "data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv"
    direct_fig43a = assets / "fig43_a_two_slope_expansion_r123.pdf"
    crop_provenance[direct_fig43a.name] = render_fig43a_direct(p, two_slope_csv, direct_fig43a)
    direct_fig43b = assets / "fig43_b_two_slope_w_r123.pdf"
    crop_provenance[direct_fig43b.name] = render_fig43b_direct(
        p,
        two_slope_csv,
        direct_fig43b,
    )
    direct_fig44a = assets / "fig44_a_growth_equality_r123.pdf"
    crop_provenance[direct_fig44a.name] = render_fig44a_direct(
        p,
        LATEX / "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv",
        direct_fig44a,
    )
    for spec in p.SPECS:
        if spec.figure not in {15, 16, 17, 18, 19, 20, 42, 43, 44}:
            continue
        if not spec.stem.startswith(TARGET_PREFIXES):
            continue
        target = assets / f"{spec.stem}.pdf"
        if target.exists():
            continue
        crop_provenance[target.name] = safe_compose_crop(p, spec, p.SOURCE_FILES[spec.figure], target)

    evolution_hashes, evolution_numeric = build_evolution(sources)
    for name in EVOLUTION_TARGETS:
        shutil.copy2(sources / "evolution" / name, assets / name)

    generated = sorted(assets.glob("*.pdf"))
    expected_generated_names = {
        f.name
        for f in (FULL_V3 / "outputs/panels").glob("*.pdf")
        if f.name.startswith(TARGET_PREFIXES)
    } | set(EVOLUTION_TARGETS)
    actual_generated_names = {f.name for f in generated}
    if actual_generated_names != expected_generated_names or len(generated) != 30:
        raise RuntimeError(
            "expected exactly 30 generated candidates; "
            f"missing={sorted(expected_generated_names-actual_generated_names)}, "
            f"extra={sorted(actual_generated_names-expected_generated_names)}"
        )

    # Figures 18--20 are withdrawn as a class: their inherited multi-panel
    # sheet crops failed direct prefix/safe-edge inspection, and a separate
    # direct-render external-comparison atlas now owns those scientific panels.
    # Preserve them as explicit diagnostic provenance but never advertise an
    # install path for them in the active manifest.
    withdrawn_paths = []
    for path in generated:
        if path.name.startswith(WITHDRAWN_PREFIXES):
            target = withdrawn / path.name
            path.replace(target)
            withdrawn_paths.append(target)

    outputs = sorted(assets.glob("*.pdf"))
    expected_active_names = {
        name for name in expected_generated_names if not name.startswith(WITHDRAWN_PREFIXES)
    }
    actual_active_names = {path.name for path in outputs}
    if actual_active_names != expected_active_names or len(outputs) != EXPECTED_ACTIVE_OVERLAYS:
        raise RuntimeError(
            f"expected exactly {EXPECTED_ACTIVE_OVERLAYS} active overlays; "
            f"missing={sorted(expected_active_names-actual_active_names)}, "
            f"extra={sorted(actual_active_names-expected_active_names)}"
        )
    if len(withdrawn_paths) != EXPECTED_WITHDRAWN_CROPS:
        raise RuntimeError(f"expected {EXPECTED_WITHDRAWN_CROPS} withdrawn crops, got {len(withdrawn_paths)}")

    for path in outputs:
        add_vector_safe_margin(path)
        normalize_pdf(path, path.stem)
    for path in withdrawn_paths:
        normalize_pdf(path, path.stem + "_WITHDRAWN_NOT_FOR_INSTALL")

    numeric_inputs = {}
    owner_names = {
        "points": "R97_HRC_SOURCE_POINTS.csv",
        "fits": "R97_HRC_PER_GALAXY_FITS.csv",
        "udg": "R97_HRC_UDG_DIAGNOSTIC.csv",
    }
    for group in (hrc_provenance["owner_hashes"], cosmology_provenance["owner_hashes"]):
        for name, digest in group.items():
            owner_name = owner_names.get(name, name)
            matches = [path for path in LATEX.rglob(owner_name) if path.is_file()]
            if len(matches) == 1:
                numeric_inputs[str(matches[0].relative_to(ROOT))] = numeric_signature(matches[0])
            else:
                numeric_inputs[owner_name] = {"raw_sha256": digest, "path_resolution": f"{len(matches)} matches"}
    numeric_inputs.update({value["path"]: value for value in evolution_numeric.values()})

    provenance = {
        "schema": "ECT-R123-curve-luminance-readable-build-v1",
        "status": "PROPOSAL ONLY / SCIENTIFIC ARRAYS UNCHANGED",
        "palette": PALETTE,
        "minimum_source_text_pt": MIN_SOURCE_TEXT_PT,
        "vector_safe_padding_pt": PDF_SAFE_PAD_PT,
        "hrc": hrc_provenance,
        "cosmology": cosmology_provenance,
        "evolution_owner_hashes": evolution_hashes,
        "crop_provenance": crop_provenance,
        "numeric_payload": numeric_inputs,
        "outputs": {path.name: sha(path) for path in outputs},
        "active_overlay_count": len(outputs),
        "withdrawn_not_for_install": {
            path.name: {
                "sha256": sha(path),
                "status": "WITHDRAWN_NOT_FOR_INSTALL",
                "reason": "multi-panel sheet-crop class failed prefix/safe-edge review; superseded by direct-render external-comparison atlas",
            }
            for path in sorted(withdrawn_paths)
        },
        "live_manuscript_edited": False,
    }
    manifests = output_root / "manifests"
    manifests.mkdir(exist_ok=True)
    (manifests / "R123_CURVE_NUMERIC_PAYLOAD_SIGNATURES_v1.json").write_text(
        json.dumps(numeric_inputs, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (manifests / "R123_CURVE_LUMINANCE_READABLE_BUILD_v1.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (manifests / "R123_CURVE_CROPS_WITHDRAWN_NOT_FOR_INSTALL_v1.json").write_text(
        json.dumps(
            {
                "schema": "ECT-R123-withdrawn-crop-provenance-v1",
                "status": "WITHDRAWN_NOT_FOR_INSTALL",
                "count": len(withdrawn_paths),
                "replacement_owner": "separate direct-render external-comparison atlas",
                "failure_examples": [
                    "lost leading velocity digits in right-column Figures 18 and 20",
                    "text/ticks at or beyond crop edges",
                    "sheet-crop provenance cannot certify complete labels",
                ],
                "files": provenance["withdrawn_not_for_install"],
                "live_manuscript_edited": False,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=COMPONENT)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(args.output_root / "qa/mplconfig"))
    result = build(args.output_root)
    print(json.dumps({"status": "BUILT", "overlays": len(result["outputs"]), "output_root": str(args.output_root)}, indent=2))


if __name__ == "__main__":
    main()
