#!/usr/bin/env python3
"""Build clipping-free R123 panels directly from frozen scientific owners.

This proposal-only renderer intentionally does not crop publication PDFs.
For each multi-panel owner it replays the original plotting function against
the same frozen arrays, retains only the requested axes, assigns them to a new
one-panel (or 2x2 gallery) GridSpec, and saves a fresh vector PDF with explicit
padding.  Numerical artists are hashed before and after the layout-only step.

Nothing below writes to live LaTeX, publication figures, Git, or the R123
``final_candidate`` tree.
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
import subprocess
import sys
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parent
ECT_ROOT = SCRIPT.parents[6]
LATEX_ROOT = ECT_ROOT / "LaTex"
R123_ROOT = LATEX_ROOT / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"
P1_ROOT = R123_ROOT / "components/global_visual_remediation/p1_panel_work"

os.environ.setdefault("MPLCONFIGDIR", str(COMPONENT / "runtime/mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(COMPONENT / "runtime/cache"))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")
os.environ.setdefault("TZ", "UTC")

import fitz  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import colors as mcolors  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


FIXED_DT = datetime(2026, 7, 21, 0, 0, 0, tzinfo=timezone.utc)
PDF_METADATA = {
    "Title": "R123 clipping-free panel replay",
    "Author": "ECT reproducibility workflow",
    "Subject": "Proposal-only layout repair; frozen scientific payload unchanged",
    "Keywords": "ECT R123 vector panel deterministic owner replay",
    "Creator": SCRIPT.name,
    "CreationDate": FIXED_DT,
    "ModDate": FIXED_DT,
}

# The mapping is intentionally luminance-spread.  Line style, marker shape and
# direct labels remain redundant, but no decorative hatch is needed.
COLOR_REMAP = {
    "#0072b2": "#2A6F97",  # dark calm blue
    "#d55e00": "#8C3B2A",  # dark muted vermillion
    "#009e73": "#397A54",  # medium green
    "#e69f00": "#A27716",  # ochre, darker than the source yellow-orange
    "#cc79a7": "#755E85",  # muted purple
    "#56b4e9": "#5A9ABC",  # pale sky blue
    "#f0e442": "#B79A18",  # readable ochre if encountered
    "#777777": "#666666",
    "#737373": "#666666",
}
FILL_REMAP = {
    "#e8e8e8": "#E1E7EA",
    "#f7f7f7": "#F4F7F8",
    "#ececec": "#E9EFF1",
}
HRC_COLOR_REMAP = {
    "#0072b2": "#2A6F97",  # HRC-0
    "#d55e00": "#5D8B61",  # HRC-3, lighter value than HRC-0
    "#009e73": "#7B7B7B",  # baryonic comparator
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ECT_ROOT))
    except ValueError:
        return str(path.resolve())


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def import_module(path: Path, tag: str):
    spec = importlib.util.spec_from_file_location(f"r123_clip_{tag}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import owner module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE_PATHS = {
    "cosmo103": LATEX_ROOT / "scripts/cosmology/make_r103_corrected_cosmology_figures.py",
    "closure114": LATEX_ROOT / "scripts/figures/make_r114_closure_figures.py",
    "hrc_only": LATEX_ROOT / "scripts/hrc/make_r97_hrc_only_figures.py",
    "hrc_completion": LATEX_ROOT / "scripts/hrc/make_r97_hrc_completion_figures.py",
    "bh": LATEX_ROOT / "scripts/fig_bh_information.py",
    "restored103": LATEX_ROOT / "scripts/figures/make_r103_restored_visuals.py",
    "finitebody114": LATEX_ROOT / "scripts/figures/make_r114_finitebody_scalar_gate_figure.py",
    "pesm1": LATEX_ROOT / "scripts/figures/make_r114_pes_m1_fdt_figure_v2.py",
}

DATA_PATHS = {
    "cosmo_background": LATEX_ROOT / "data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json",
    "cosmo_scan": LATEX_ROOT / "data/cosmology_r103/R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json",
    "early_csv": LATEX_ROOT / "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv",
    "one_pole": LATEX_ROOT / "data/cosmology_r113/R113_ONE_POLE_CLUSTER_NO_GO_v2.json",
    "hrc_points": LATEX_ROOT / "data/hrc_r97/R97_HRC_SOURCE_POINTS.csv",
    "hrc_regimes": LATEX_ROOT / "data/hrc_r97/R97_HRC_SOURCE_REGIMES.csv",
    "hrc_fits": LATEX_ROOT / "data/hrc_r97/R97_HRC_PER_GALAXY_FITS.csv",
    "sparc_massmodels": LATEX_ROOT / "data/MassModels_Lelli2016c.mrt",
    "hwg": LATEX_ROOT / "data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv",
    "finitebody_tex": LATEX_ROOT / "work/preprint/R114_VERIFIED_COSMOLOGY_PES_CASCADE_CANDIDATE_v1/ECT_preprint_R114_verified_cosmology_pes_cascade_candidate_v1.tex",
    "m1_protocol": ECT_ROOT / "research/derivations/pes_usage/gpt/R114_PES_FRONTIER_CODEX/derivations/M1_FDT_PROTOCOL/M1_SAME_CHANNEL_FDT_PROTOCOL_v2.md",
    # The historical erratum source is not materialised in the live workspace;
    # its frozen hash remains recorded by this immutable figure manifest.
    "m1_figure_manifest": LATEX_ROOT / "work/preprint/R114_PES_M1_FIGURE_CANDIDATE_v2/assets/R114_PES_M1_FIGURE_MANIFEST_v2.json",
    "m1_protocol_verifier": LATEX_ROOT / "scripts/verification/pes/r114/m1/verify_m1_same_channel_fdt_v2.py",
    "m1_baseline_verifier": LATEX_ROOT / "scripts/verification/pes/r114/m1/verify_m1_same_channel_fdt.py",
}

OLD_ASSETS = P1_ROOT / "assets"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def numeric_float(value: str) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def load_numeric_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [{key: numeric_float(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def finite_array(values: Iterable[Any]) -> list[float]:
    arr = np.asarray(list(values), dtype=float).ravel()
    return [float(x) if np.isfinite(x) else str(x) for x in arr]


def artist_payload(axes: Iterable[plt.Axes]) -> dict[str, Any]:
    """Canonical numerical content, deliberately excluding layout and colour.

    Titles and axis-label strings are excluded because the clipping repair may
    repeat an already-present common label on a newly independent gallery
    canvas.  Scales, limits, curve labels, arrays, points and patch geometry
    remain inside the hash.
    """

    result: dict[str, Any] = {"axes": []}
    for ax in axes:
        axis: dict[str, Any] = {
            "xscale": ax.get_xscale(),
            "yscale": ax.get_yscale(),
            "xlim": finite_array(ax.get_xlim()),
            "ylim": finite_array(ax.get_ylim()),
            "lines": [],
            "collections": [],
            "patches": [],
        }
        for line in ax.lines:
            axis["lines"].append(
                {
                    "label": line.get_label(),
                    "x": finite_array(line.get_xdata(orig=True)),
                    "y": finite_array(line.get_ydata(orig=True)),
                }
            )
        for coll in ax.collections:
            offsets = getattr(coll, "get_offsets", lambda: np.empty((0, 2)))()
            arrays = getattr(coll, "get_array", lambda: None)()
            paths = []
            for path in getattr(coll, "get_paths", lambda: [])():
                paths.append(finite_array(path.vertices))
            axis["collections"].append(
                {
                    "label": coll.get_label(),
                    "offsets": finite_array(np.asarray(offsets).ravel()),
                    "array": [] if arrays is None else finite_array(np.asarray(arrays).ravel()),
                    "paths": paths,
                }
            )
        for patch in ax.patches:
            # A zorder below -5 is reserved by this renderer for a purely
            # decorative page-level status guard.  Scientific bars/regions
            # retain ordinary zorder and remain hashed.
            if patch.get_zorder() < -5:
                continue
            item: dict[str, Any] = {"type": type(patch).__name__, "label": patch.get_label()}
            for attr in ("get_x", "get_y", "get_width", "get_height"):
                if hasattr(patch, attr):
                    try:
                        item[attr.removeprefix("get_")] = float(getattr(patch, attr)())
                    except (TypeError, ValueError):
                        pass
            axis["patches"].append(item)
        result["axes"].append(axis)
    return result


def remap_colour(value: Any, *, fill: bool = False, role: str = "general") -> Any:
    try:
        rgba = mcolors.to_rgba(value)
    except (TypeError, ValueError):
        return value
    hex_value = mcolors.to_hex(rgba, keep_alpha=False).lower()
    if role == "hrc" and hex_value in HRC_COLOR_REMAP:
        target = HRC_COLOR_REMAP[hex_value]
    else:
        target = (FILL_REMAP if fill else COLOR_REMAP).get(hex_value)
    if target is None:
        return value
    return mcolors.to_rgba(target, alpha=rgba[3])


def style_axes(axes: Iterable[plt.Axes], *, role: str = "general") -> None:
    """Layout-only and appearance-only remediation; numerical arrays untouched."""

    for ax in axes:
        ax.tick_params(labelsize=9.2, pad=4)
        ax.title.set_fontsize(11.0)
        ax.xaxis.label.set_fontsize(10.2)
        ax.yaxis.label.set_fontsize(10.2)
        for spine in ax.spines.values():
            spine.set_color("#444444")
            spine.set_linewidth(0.9)
        for line in ax.lines:
            line.set_color(remap_colour(line.get_color(), role=role))
            line.set_linewidth(max(1.35, line.get_linewidth()))
        for coll in ax.collections:
            try:
                faces = coll.get_facecolors()
                if len(faces):
                    coll.set_facecolors([remap_colour(c, fill=True, role=role) for c in faces])
                edges = coll.get_edgecolors()
                if len(edges):
                    coll.set_edgecolors([remap_colour(c, role=role) for c in edges])
            except (AttributeError, ValueError):
                pass
        for patch in ax.patches:
            if hasattr(patch, "set_hatch"):
                patch.set_hatch(None)
            try:
                patch.set_facecolor(remap_colour(patch.get_facecolor(), fill=True, role=role))
                patch.set_edgecolor(remap_colour(patch.get_edgecolor(), role=role))
            except (TypeError, ValueError):
                pass
        legend = ax.get_legend()
        if legend is not None:
            if role == "hrc":
                handles, labels = ax.get_legend_handles_labels()
                location = getattr(legend, "_loc", "best")
                title = legend.get_title().get_text()
                legend.remove()
                legend = ax.legend(handles, labels, loc=location, title=title or None)
            legend.set_frame_on(True)
            legend.get_frame().set_facecolor("#FFFFFF")
            legend.get_frame().set_edgecolor("#B8B8B8")
            legend.get_frame().set_alpha(0.94)
            for txt in legend.get_texts():
                txt.set_fontsize(8.6)


@contextmanager
def capture_save(module: Any, save_name: str):
    holder: dict[str, Figure] = {}
    original = getattr(module, save_name)

    def capture(fig: Figure, *_args: Any, **_kwargs: Any) -> None:
        holder["fig"] = fig

    setattr(module, save_name, capture)
    try:
        yield holder
    finally:
        setattr(module, save_name, original)


@contextmanager
def capture_direct_render(module: Any):
    """Capture a renderer that calls ``Figure.savefig`` and ``plt.close`` directly."""

    holder: dict[str, Figure] = {}
    original_subplots = module.plt.subplots
    original_savefig = Figure.savefig
    original_close = module.plt.close

    def subplots(*args: Any, **kwargs: Any):
        fig, axes = original_subplots(*args, **kwargs)
        holder["fig"] = fig
        return fig, axes

    module.plt.subplots = subplots
    Figure.savefig = lambda self, *_args, **_kwargs: None  # type: ignore[method-assign]
    module.plt.close = lambda *_args, **_kwargs: None
    try:
        yield holder
    finally:
        module.plt.subplots = original_subplots
        Figure.savefig = original_savefig  # type: ignore[method-assign]
        module.plt.close = original_close


def clean_figure_text(fig: Figure) -> None:
    for text in list(fig.texts):
        text.remove()
    for legend in list(fig.legends):
        legend.remove()


def solo_layout(
    fig: Figure,
    indices: list[int],
    *,
    title: str,
    grid: tuple[int, int] = (1, 1),
    global_legend: bool = False,
    status_guard: bool = False,
    palette_role: str = "general",
) -> tuple[list[plt.Axes], str, str]:
    all_axes = list(fig.axes)
    targets = [all_axes[index] for index in indices]
    before = canonical_hash(artist_payload(targets))
    legend_handles: list[Any] = []
    legend_labels: list[str] = []
    if global_legend:
        if fig.legends:
            source_legend = fig.legends[0]
            legend_handles = list(getattr(source_legend, "legend_handles", []))
            legend_labels = [text.get_text() for text in source_legend.get_texts()]
        if not legend_handles:
            legend_handles, legend_labels = targets[0].get_legend_handles_labels()

    for ax in all_axes:
        if ax not in targets:
            ax.remove()
    clean_figure_text(fig)
    fig.set_size_inches(7.35, 5.45 if grid == (1, 1) else 7.0, forward=True)
    fig.set_layout_engine("constrained", h_pad=0.105, w_pad=0.105, hspace=0.08, wspace=0.08)
    gs = fig.add_gridspec(*grid)
    for i, ax in enumerate(targets):
        row, col = divmod(i, grid[1])
        ax.set_subplotspec(gs[row, col])
        ax.set_in_layout(True)
        ax.set_visible(True)
    style_axes(targets, role=palette_role)

    if status_guard:
        ax = targets[0]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.add_patch(
            FancyBboxPatch(
                (0.01, 0.03),
                0.96,
                0.91,
                transform=ax.transAxes,
                boxstyle="round,pad=0.018,rounding_size=0.025",
                facecolor="#DCEBF4",
                edgecolor="#2A6F97",
                linewidth=1.6,
                zorder=-10,
            )
        )
        for text in ax.texts:
            text.set_fontsize(max(10.2, text.get_fontsize()))

    if grid != (1, 1):
        for i, ax in enumerate(targets):
            if i // grid[1] == grid[0] - 1 and not ax.get_xlabel():
                ax.set_xlabel("R [kpc]")
            if i % grid[1] == 0 and not ax.get_ylabel():
                ax.set_ylabel(r"$V$ [km s$^{-1}$]")
    fig.suptitle(title, fontsize=12.0, weight="bold")
    if global_legend and legend_handles:
        final_legend = fig.legend(
            legend_handles,
            legend_labels,
            loc="outside lower center",
            ncol=min(4, len(legend_handles)),
            frameon=False,
            fontsize=8.6,
        )
        for handle in getattr(final_legend, "legend_handles", []):
            if hasattr(handle, "get_color") and hasattr(handle, "set_color"):
                handle.set_color(remap_colour(handle.get_color(), role=palette_role))
            if hasattr(handle, "get_facecolor") and hasattr(handle, "set_facecolor"):
                try:
                    handle.set_facecolor(remap_colour(handle.get_facecolor(), role=palette_role))
                    handle.set_edgecolor(remap_colour(handle.get_edgecolor(), role=palette_role))
                except (TypeError, ValueError):
                    pass
    after = canonical_hash(artist_payload(targets))
    return targets, before, after


def save_panel(fig: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf", metadata=PDF_METADATA, facecolor="white", pad_inches=0.12)
    plt.close(fig)


def render_png(pdf: Path, output: Path, dpi: int = 118) -> None:
    doc = fitz.open(pdf)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False, colorspace=fitz.csRGB)
    output.parent.mkdir(parents=True, exist_ok=True)
    pix.save(output)
    doc.close()


def cvd_image(image: Image.Image, mode: str) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    if mode == "gray":
        lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
        out = np.repeat(lum[..., None], 3, axis=2)
    elif mode == "deutan":
        matrix = np.array([[0.625, 0.375, 0.000], [0.700, 0.300, 0.000], [0.000, 0.300, 0.700]])
        out = arr @ matrix.T
    else:
        out = arr
    return Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255), mode="RGB")


def contact_sheet(images: list[tuple[str, Path]], output: Path, mode: str) -> None:
    thumb_w, thumb_h = 310, 245
    cols = 4
    rows = math.ceil(len(images) / cols)
    canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 25)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, (name, path) in enumerate(images):
        im = cvd_image(Image.open(path), mode)
        im.thumbnail((thumb_w - 10, thumb_h - 10), Image.Resampling.LANCZOS)
        col, row = i % cols, i // cols
        x = col * thumb_w + (thumb_w - im.width) // 2
        y0 = row * (thumb_h + 25)
        y = y0 + 20 + (thumb_h - im.height) // 2
        canvas.paste(im, (x, y))
        draw.text((col * thumb_w + 5, y0 + 4), name, fill="#111111", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", compress_level=9, optimize=False)


def make_cosmo103(kind: str) -> Figure:
    module = import_module(MODULE_PATHS["cosmo103"], f"cosmo103_{kind}")
    background = load_json(DATA_PATHS["cosmo_background"])
    scan = load_json(DATA_PATHS["cosmo_scan"])
    with capture_save(module, "finish") as holder:
        if kind == "tradeoff":
            module.tradeoff_figure(scan, Path("unused"))
        elif kind == "background":
            module.background_figure(background, scan, Path("unused"))
        else:
            raise ValueError(kind)
    return holder["fig"]


def make_closure114(kind: str) -> Figure:
    module = import_module(MODULE_PATHS["closure114"], f"closure114_{kind}")
    module.configure()
    with capture_save(module, "save_figure") as holder:
        if kind == "one_pole":
            module.one_pole_figure(load_json(DATA_PATHS["one_pole"]), Path("unused"))
        elif kind == "early":
            module.early_response_figure(module.read_early_rows(DATA_PATHS["early_csv"]), Path("unused"))
        else:
            raise ValueError(kind)
    return holder["fig"]


def make_hrc_only(kind: str) -> Figure:
    module = import_module(MODULE_PATHS["hrc_only"], f"hrconly_{kind}")
    with capture_save(module, "save") as holder:
        if kind == "response":
            module.response_and_regime_figure()
        elif kind == "examples":
            module.rotation_examples_figure()
        else:
            raise ValueError(kind)
    return holder["fig"]


def hrc_rows() -> list[dict[str, Any]]:
    rows = load_numeric_csv(DATA_PATHS["hrc_fits"])
    if not rows or any(not isinstance(r.get("aM_HRC0_si"), float) for r in rows):
        raise RuntimeError("frozen per-galaxy HRC fits could not be parsed")
    return rows


def make_hrc_completion(kind: str) -> Figure:
    module = import_module(MODULE_PATHS["hrc_completion"], f"hrccompletion_{kind}")
    rows = hrc_rows()
    with capture_save(module, "save") as holder:
        if kind == "btfr":
            module.btfr_and_scale_figure(rows)
        elif kind == "ml":
            module.ml_sensitivity_figure(rows)
        elif kind == "gallery":
            module.rotation_gallery(rows)
        elif kind == "residual":
            module.residual_extremes_figure()
        else:
            raise ValueError(kind)
    return holder["fig"]


def make_restored103() -> Figure:
    module = import_module(MODULE_PATHS["restored103"], "restored103_hwg")
    module.configure()
    with capture_save(module, "save") as holder:
        module.two_slope_hwg(DATA_PATHS["hwg"], Path("unused"))
    return holder["fig"]


def make_finitebody114() -> Figure:
    module = import_module(MODULE_PATHS["finitebody114"], "finitebody114")
    module.configure()
    text = DATA_PATHS["finitebody_tex"].read_text(encoding="utf-8")
    proxy = module.parse_proxy_table(text)
    estimators = module.parse_estimator_registry(text)
    objects = module.parse_object_table(text)
    with capture_direct_render(module) as holder:
        module.render(proxy, estimators, objects, Path("unused"))
    return holder["fig"]


def make_pesm1() -> Figure:
    module = import_module(MODULE_PATHS["pesm1"], "pesm1")
    module.configure()
    payload = module.payload_from_verifiers(
        DATA_PATHS["m1_protocol_verifier"], DATA_PATHS["m1_baseline_verifier"]
    )
    with capture_direct_render(module) as holder:
        module.render(payload, Path("unused"))
    return holder["fig"]


def make_black_hole() -> Figure:
    """Replay the public formulas from ``fig_bh_information.py`` exactly."""

    script = MODULE_PATHS["bh"].read_text(encoding="utf-8")
    required = [
        "y = 1.0 / x",
        "coarse = np.sqrt(t)",
        "th = HBAR * C**3 / (8.0 * np.pi * G * KB * mass)",
    ]
    if any(token not in script for token in required):
        raise RuntimeError("black-hole owner formulas changed; refusing manual replay")
    hbar, c, grav, kb, msun = 1.054571817e-34, 299_792_458.0, 6.67430e-11, 1.380649e-23, 1.98847e30
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.25), constrained_layout=True)
    x = np.linspace(0.035, 6.0, 1200)
    y = 1.0 / x
    ax = axes[0]
    ax.plot(x, y, color="#0072B2", lw=2.2, marker="o", markevery=120, ms=3.0,
            label=r"external kinematics $T_{\rm loc}/T_{\rm ref}=\rho_{\rm ref}/\rho$")
    ax.axhline(1.0, color="#009E73", ls="--", lw=1.6, label=r"arbitrary reference $T_{\rm ref}$")
    ax.axvline(1.0, color="#D55E00", ls=":", lw=1.8)
    ax.text(1.06, 2.55, r"reference point only: $\rho=\rho_{\rm ref}$", rotation=90, va="center", color="#D55E00")
    ax.set(xlim=(0, 6), ylim=(0, 6), xlabel=r"proper distance $\rho/\rho_{\rm ref}$",
           ylabel=r"$T_{\rm loc}/T_{\rm ref}$", title="(a) External Tolman kinematics")
    ax.legend(loc="upper right", fontsize=7.4)

    t = np.linspace(0, 1, 800)
    coarse = np.sqrt(t)
    ax = axes[1]
    ax.plot(t, coarse, color="#D55E00", lw=2, ls="--", label="coarse-grained (semiclassical)")
    ax.fill_between(t, 0, coarse, color="#E2BD65", edgecolor="#7A5A12", alpha=0.55,
                    label="fine-grained ECT curve: Open within this region")
    ax.text(0.5, 0.23, "Missing: Hilbert split, state,\nevaporation channel and Hamiltonian",
            ha="center", va="center", fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#333333"})
    ax.set(xlim=(0, 1), ylim=(0, 1.08), xlabel=r"evaporation time $t/t_{\rm evap}$",
           ylabel="normalised entropy", title="(b) Semiclassical benchmark; ECT curve Open")
    ax.legend(loc="upper left", fontsize=7.4)

    ratio = np.logspace(0, 9, 500)
    temp = hbar * c**3 / (8 * np.pi * grav * kb * ratio * msun)
    ax = axes[2]
    ax.loglog(ratio, temp, color="#0072B2", lw=2.2, marker="o", markevery=85, ms=3.2,
              label=r"standard Hawking $T_H(M)$")
    ax.text(0.5, 0.25, "ECT shell depth: NOT IDENTIFIED\nrequires a P4 control variable, metric,\nstate and transfer map",
            transform=ax.transAxes, ha="center", va="center", fontsize=9, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": "#D55E00", "linewidth": 1.5})
    ax.set(xlabel=r"black-hole mass $M/M_\odot$", ylabel=r"temperature $T_H$ [K]",
           title="(c) External Hawking benchmark")
    ax.legend(loc="upper right", fontsize=7.4)
    return fig


def source_hashes(keys: Iterable[str]) -> dict[str, str]:
    paths: list[Path] = []
    for key in keys:
        path = MODULE_PATHS.get(key) or DATA_PATHS.get(key)
        if path is None:
            raise KeyError(key)
        paths.append(path)
    return {rel(path): sha256(path) for path in paths}


def panel_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(
        filename: str,
        factory: Callable[[], Figure],
        indices: list[int],
        title: str,
        owner_keys: list[str],
        *,
        grid: tuple[int, int] = (1, 1),
        legend: bool = False,
        status_guard: bool = False,
        palette_role: str = "general",
    ) -> None:
        specs.append(
            {
                "filename": filename,
                "factory": factory,
                "indices": indices,
                "title": title,
                "owner_keys": owner_keys,
                "grid": grid,
                "legend": legend,
                "status_guard": status_guard,
                "palette_role": palette_role,
            }
        )

    add("fig10_a_acoustic_gate_r123.pdf", lambda: make_cosmo103("tradeoff"), [0],
        "Acoustic leverage versus the local-gravity gate", ["cosmo103", "cosmo_scan"])
    add("fig10_b_fixed_angle_proxy_r123.pdf", lambda: make_cosmo103("tradeoff"), [1],
        "Fixed-angle diagnostic proxy (not a CMB likelihood)", ["cosmo103", "cosmo_scan"])
    add("fig11_a_timescale_mismatch_r123.pdf", lambda: make_closure114("one_pole"), [0],
        "One-real-pole cluster-scale test: timescale", ["closure114", "one_pole"])
    add("fig11_b_ballistic_distance_mismatch_r123.pdf", lambda: make_closure114("one_pole"), [1],
        "One-real-pole cluster-scale test: ballistic distance", ["closure114", "one_pole"])

    add("fig15_a_btfr_tail_proxy_r123.pdf", lambda: make_hrc_completion("btfr"), [0],
        "Conditional BTFR and tail proxies", ["hrc_completion", "hrc_fits"], palette_role="hrc")
    add("fig15_b_scale_dispersion_r123.pdf", lambda: make_hrc_completion("btfr"), [1],
        "Algebraic fitted-scale dispersion (Level C)", ["hrc_completion", "hrc_fits"], palette_role="hrc")
    for suffix, index, title in (
        ("a_hrc0_ml_coupling", 0, "HRC-0 scale--stellar-M/L coupling"),
        ("b_hrc3_ml_coupling", 1, "HRC-3 scale--stellar-M/L coupling"),
        ("c_two_parameter_nuisance", 2, "Two-parameter stellar-M/L nuisance test"),
    ):
        add(f"fig16_{suffix}_r123.pdf", lambda: make_hrc_completion("ml"), [index], title,
            ["hrc_completion", "hrc_fits"], palette_role="hrc")
    add("fig17_a_response_laws_r123.pdf", lambda: make_hrc_only("response"), [0],
        "HRC response laws", ["hrc_only", "hrc_regimes"], palette_role="hrc")
    add("fig17_b_sparc_regime_diagnostic_r123.pdf", lambda: make_hrc_only("response"), [1],
        "Frozen algebraic SPARC regime diagnostic", ["hrc_only", "hrc_regimes"], palette_role="hrc")

    for suffix, index, galaxy in (("a_ddo154", 0, "DDO154"), ("b_ngc2403", 1, "NGC2403"),
                                  ("c_ngc3198", 2, "NGC3198"), ("d_ngc6503", 3, "NGC6503")):
        add(f"fig18_{suffix}_r123.pdf", lambda: make_hrc_only("examples"), [index],
            f"Held-out HRC rotation-curve example: {galaxy}", ["hrc_only", "hrc_points"], legend=True, palette_role="hrc")

    gallery_groups = (("a_gallery_lowacc_1", [0, 1, 2, 3], "gallery page 1/4"),
                      ("b_gallery_lowacc_2", [4, 5, 6, 7], "gallery page 2/4"),
                      ("c_gallery_highacc_1", [8, 9, 10, 11], "gallery page 3/4"),
                      ("d_gallery_highacc_2", [12, 13, 14, 15], "gallery page 4/4"))
    for suffix, indices, label in gallery_groups:
        add(f"fig19_{suffix}_r123.pdf", lambda: make_hrc_completion("gallery"), indices,
            f"HRC-only frozen acceleration-stratified {label}",
            ["hrc_completion", "hrc_fits", "sparc_massmodels"], grid=(2, 2), legend=True, palette_role="hrc")

    for suffix, index, galaxy in (("a_ugc02953", 0, "UGC02953"), ("b_ugc09133", 1, "UGC09133"),
                                  ("c_ngc6946", 2, "NGC6946"), ("d_ngc7331", 3, "NGC7331")):
        add(f"fig20_{suffix}_r123.pdf", lambda: make_hrc_completion("residual"), [index],
            f"Post-hoc HRC residual-stress example: {galaxy}",
            ["hrc_completion", "hrc_points"], legend=True, palette_role="hrc")

    for suffix, index, title in (("a_tolman_kinematics", 0, "External Tolman kinematics"),
                                 ("b_page_curve_benchmark", 1, "Semiclassical benchmark; ECT curve Open"),
                                 ("c_hawking_benchmark", 2, "External Hawking benchmark")):
        add(f"fig35_{suffix}_r123.pdf", make_black_hole, [index], title, ["bh"])

    bg_titles = (
        ("a_named_expansion", 0, "Named two-slope expansion"),
        ("b_clock_budget", 1, "Conditional clock budget"),
        ("c_comoving_distance", 2, "Conditional comoving distance"),
        ("d_background_w", 3, "Total background equation of state"),
        ("e_calibrated_family", 4, "Calibrated supplied-action family"),
        ("f_scope_statement", 5, "Scope and missing-owner statement"),
    )
    for suffix, index, title in bg_titles:
        add(f"fig42_{suffix}_r123.pdf", lambda: make_cosmo103("background"), [index], title,
            ["cosmo103", "cosmo_background", "cosmo_scan"], status_guard=(index == 5))

    add("fig43_a_two_slope_expansion_r123.pdf", make_restored103, [0],
        "Conditional two-slope expansion response", ["restored103", "hwg"])
    add("fig43_b_two_slope_w_r123.pdf", make_restored103, [1],
        "Conditional total kinematic equation of state", ["restored103", "hwg"])
    add("fig44_a_growth_equality_r123.pdf", lambda: make_closure114("early"), [0],
        "Owner-specific growth and equality response", ["closure114", "early_csv"])

    add("fig45_a_fixed_metric_bvp_r123.pdf", make_finitebody114, [0],
        "Fixed-metric finite-body scalar BVP", ["finitebody114", "finitebody_tex"])
    add("fig45_b_tail_estimators_r123.pdf", make_finitebody114, [1],
        "Three finite-body tail estimators (not averaged)", ["finitebody114", "finitebody_tex"])

    add("fig47_a_single_kms_channel_r123.pdf", make_pesm1, [0],
        "M1 same-channel FDT: single KMS channel", ["pesm1", "m1_protocol", "m1_figure_manifest", "m1_protocol_verifier", "m1_baseline_verifier"])
    add("fig47_b_counterexamples_r123.pdf", make_pesm1, [1],
        "M1 same-channel FDT: ordinary counterexamples", ["pesm1", "m1_protocol", "m1_figure_manifest", "m1_protocol_verifier", "m1_baseline_verifier"])
    return specs


def pdf_sanity(path: Path) -> dict[str, Any]:
    doc = fitz.open(path)
    if len(doc) != 1:
        raise RuntimeError(f"{path.name}: expected one page, got {len(doc)}")
    page = doc[0]
    rect = page.rect
    text = page.get_text("text")
    blocks = page.get_text("blocks")
    outside = []
    for block in blocks:
        x0, y0, x1, y1, block_text = block[:5]
        if not str(block_text).strip():
            continue
        if x0 < -0.75 or y0 < -0.75 or x1 > rect.width + 0.75 or y1 > rect.height + 0.75:
            outside.append([round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3), str(block_text)[:120]])
    result = {
        "pages": 1,
        "mediabox_pt": [round(rect.width, 3), round(rect.height, 3)],
        "embedded_text_chars": len(text),
        "text_blocks_outside_mediabox": outside,
        "one_page": True,
        "embedded_text_present": len(text.strip()) >= 20,
        "text_inside_mediabox": not outside,
    }
    doc.close()
    return result


def build(output_root: Path) -> dict[str, Any]:
    assets = output_root / "assets"
    previews = output_root / "previews/color"
    manifests = output_root / "manifests"
    qa = output_root / "qa"
    for directory in (assets, previews, manifests, qa):
        directory.mkdir(parents=True, exist_ok=True)

    records = []
    preview_inputs = []
    for number, spec in enumerate(panel_specs(), start=1):
        fig = spec["factory"]()
        targets, before, after = solo_layout(
            fig,
            spec["indices"],
            title=spec["title"],
            grid=spec["grid"],
            global_legend=spec["legend"],
            status_guard=spec["status_guard"],
            palette_role=spec["palette_role"],
        )
        if before != after:
            raise RuntimeError(f"scientific payload changed during layout: {spec['filename']}")
        output = assets / spec["filename"]
        save_panel(fig, output)
        preview = previews / output.with_suffix(".png").name
        render_png(output, preview)
        sanity = pdf_sanity(output)
        if not all((sanity["one_page"], sanity["embedded_text_present"], sanity["text_inside_mediabox"])):
            raise RuntimeError(f"PDF sanity failed for {output.name}: {sanity}")
        old = OLD_ASSETS / spec["filename"]
        if not old.is_file():
            raise RuntimeError(f"old crop-derived panel is missing: {old}")
        records.append(
            {
                "ordinal": number,
                "filename": spec["filename"],
                "old_crop_asset": rel(old),
                "old_crop_sha256": sha256(old),
                "new_asset": f"assets/{output.name}",
                "new_asset_sha256": sha256(output),
                "preview": f"previews/color/{preview.name}",
                "preview_sha256": sha256(preview),
                "owner_hashes": source_hashes(spec["owner_keys"]),
                "owner_axis_indices": spec["indices"],
                "new_grid": list(spec["grid"]),
                "title": spec["title"],
                "method": "fresh Matplotlib vector replay from frozen owner arrays/functions; no PDF crop",
                "scientific_payload_sha256_before_layout": before,
                "scientific_payload_sha256_after_layout": after,
                "scientific_payload_identical": before == after,
                "pdf_sanity": sanity,
                "decorative_hatch_removed": True,
                "live_file_edited": False,
            }
        )
        preview_inputs.append((output.stem, preview))

    contact_modes = (("color", "color"), ("true_gray", "gray"), ("deutan", "deutan"))
    for label, mode in contact_modes:
        contact_sheet(preview_inputs, output_root / f"previews/R123_CLIPPING_REMEDIATION_{label}_CONTACT.png", mode)

    manifest_path = manifests / "R123_CLIPPING_REMEDIATION_V2_MANIFEST.json"
    map_path = manifests / "R123_CLIPPING_REMEDIATION_V2_OLD_TO_NEW.csv"
    with map_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "filename", "old_crop_asset", "old_crop_sha256", "new_asset", "new_asset_sha256",
            "scientific_payload_sha256", "pdf_sanity_pass", "method",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "filename": record["filename"],
                    "old_crop_asset": record["old_crop_asset"],
                    "old_crop_sha256": record["old_crop_sha256"],
                    "new_asset": record["new_asset"],
                    "new_asset_sha256": record["new_asset_sha256"],
                    "scientific_payload_sha256": record["scientific_payload_sha256_before_layout"],
                    "pdf_sanity_pass": "TRUE",
                    "method": record["method"],
                }
            )

    manifest = {
        "schema": "ECT_R123_CLIPPING_REMEDIATION_V2",
        "status": "PROPOSAL_ONLY_NOT_APPLIED",
        "fixed_build_time": "2026-07-21T00:00:00Z",
        "scope": "40 formerly crop-derived or companion panels replayed on independent canvases",
        "generator": rel(SCRIPT),
        "generator_sha256_pre_manifest": sha256(SCRIPT),
        "environment": {
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pymupdf": fitz.VersionBind,
            "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        },
        "policy": {
            "pdf_cropping_used": False,
            "fresh_owner_replay": True,
            "new_canvas_per_output": True,
            "constrained_layout_and_padding": True,
            "scientific_arrays_changed": False,
            "decorative_hatching_used": False,
            "colour_only_semantics": False,
            "luminance_first_colour": True,
            "line_marker_label_redundancy_retained": True,
            "fig42_f_calm_colour_status_guard": True,
        },
        "panel_count": len(records),
        "old_to_new_map": f"manifests/{map_path.name}",
        "old_to_new_map_sha256": sha256(map_path),
        "contact_sheets": {
            label: {
                "path": f"previews/R123_CLIPPING_REMEDIATION_{label}_CONTACT.png",
                "sha256": sha256(output_root / f"previews/R123_CLIPPING_REMEDIATION_{label}_CONTACT.png"),
            }
            for label, _mode in contact_modes
        },
        "panels": records,
        "all_scientific_payload_hashes_match": all(r["scientific_payload_identical"] for r in records),
        "all_pdf_sanity_pass": all(
            r["pdf_sanity"]["one_page"]
            and r["pdf_sanity"]["embedded_text_present"]
            and r["pdf_sanity"]["text_inside_mediabox"]
            for r in records
        ),
        "proposal_component_written": True,
        "live_manuscript_changed": False,
        "git_index_changed": False,
        "git_history_changed": False,
        "remote_changed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    report_path = output_root / "R123_CLIPPING_REMEDIATION_V2_REPORT.md"
    report_path.write_text(
        "# R123 clipping remediation v2 — proposal only\n\n"
        "- Status: **PASS / PROPOSAL ONLY / NOT APPLIED**.\n"
        f"- Panels: **{len(records)}** fresh one-page vector PDFs.\n"
        "- Scientific payload: numeric artist hash before layout equals the hash after layout for every panel.\n"
        "- Rendering: original frozen owner functions/arrays; no source-PDF crop, no `show_pdf_page`, no raster scientific payload.\n"
        "- Layout: one independent canvas per output (2x2 only for the four gallery pages), constrained layout with explicit padding.\n"
        "- Accessibility: calm luminance-spread colours, line/marker/text redundancy, no decorative hatch; colour, true-gray and deutan sheets included.\n"
        "- PDF sanity: one page, embedded text, and all extracted text blocks inside MediaBox for every output.\n"
        "- Figure 42f: calm blue status guard, while all scientific/status wording is unchanged.\n"
        "- Live manuscript/publication figures: **untouched**; Git index/history/remote: **untouched**.\n"
        "- The only workspace write is this untracked proposal component.\n\n"
        "The old-to-new CSV records every superseded crop-derived hash and its replacement hash.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=COMPONENT)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    if args.clean:
        for name in ("assets", "previews", "manifests", "qa"):
            shutil.rmtree(output_root / name, ignore_errors=True)
        for name in ("R123_CLIPPING_REMEDIATION_V2_REPORT.md", "SHA256SUMS"):
            (output_root / name).unlink(missing_ok=True)
    manifest = build(output_root)
    print(
        json.dumps(
            {
                "status": "PASS",
                "panels": manifest["panel_count"],
                "payload": manifest["all_scientific_payload_hashes_match"],
                "pdf_sanity": manifest["all_pdf_sanity_pass"],
                "manifest": str(output_root / "manifests/R123_CLIPPING_REMEDIATION_V2_MANIFEST.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
