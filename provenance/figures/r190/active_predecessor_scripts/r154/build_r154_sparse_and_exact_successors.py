#!/usr/bin/env python3
"""Build proposal-only R154 non-rotation curve-semantics successors.

The renderer is deliberately bounded:

* exact analytic or densely evaluated solver curves remain continuous, while
  decorative markers attached to those lines are removed;
* sparse deterministic scans remain at their frozen nodes and are not joined;
* the one-pole ballistic relation is evaluated densely as the exact
  ``d = v tau`` law, with the two frozen source nodes overlaid separately;
* R103 background quantities are replayed from the frozen 3001-point solver
  owner wherever that owner contains enough information.  The 8/9 published
  diagnostic nodes remain separate source markers and are used as QA anchors.

No smoothing, regression, spline, fit, or new physical model is introduced.
The script refuses to write outside the named R154 candidate directory and
never edits live TeX, the figure registry, or ``LaTex/figures``.
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
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable


SCRIPT = Path(__file__).resolve()
LATEX = SCRIPT.parents[2]
ROOT = LATEX.parent
DEFAULT_OUTPUT = (
    LATEX
    / "work/preprint/R154_SMOOTH_CURVE_SEMANTICS_CANDIDATE_v1/nonrotation"
)

# Keep Matplotlib/font caches inside the proposal package.
os.environ.setdefault(
    "MPLCONFIGDIR", str(DEFAULT_OUTPUT / "runtime/matplotlib")
)
os.environ.setdefault("XDG_CACHE_HOME", str(DEFAULT_OUTPUT / "runtime/cache"))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784937600")
os.environ.setdefault("TZ", "UTC")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import Image  # noqa: E402


FIXED_TIME = datetime(2026, 7, 25, 0, 0, 0, tzinfo=timezone.utc)
VERSION = "R154_SMOOTH_CURVE_SEMANTICS_CANDIDATE_v1"

INK = "#222222"
GRAPHITE = "#666666"
GRID = "#D8D8D8"
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#C57A00"
VERMILION = "#B3451F"
PURPLE = "#6F4FA3"
PALE_BLUE = "#D9EAF5"
PALE_GRAY = "#EBEBEB"

INPUT_LOCKS = {
    "work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/"
    "remaining_figure_typography/scripts/build_r149_remaining_typography.py":
        "13dbcc2c9d950c339f048217df41f43447ac5591cb2040c2d9b4f05c0d2f89dc",
    "work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/"
    "figure_typography_successors/scripts/build_r149_evolution_typography_successors.py":
        "7f8474f74c67670fa157a026146bfee91f783800e69462d9eba409a31179040e",
    "scripts/fig_bh_information.py":
        "7563a09f920b6d75af2daf4e5e0fcb8866d20b6e95cd12c792df0ad0a02c56e8",
    "scripts/figures/make_r114_finitebody_scalar_gate_figure.py":
        "5c691300999eace32f232eaa9bfe5bc89d2541b73ce3b0111c9b1539091adc93",
    "scripts/cosmology/compute_r103_two_slope_conditional_observables.py":
        "e4b9fdd76744b9af70c624cf21f42fd423920c3b14d03283c9389c8357b7f892",
    "work/preprint/R114_VERIFIED_COSMOLOGY_PES_CASCADE_CANDIDATE_v1/"
    "ECT_preprint_R114_verified_cosmology_pes_cascade_candidate_v1.tex":
        "549992e9d48fc2fa716325d249b96f53cf4092f10dab66030dc3cf5f72e1367a",
    "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv":
        "8a6fd7818ee0fc0ed5683ec58fa3beeff778e7966590c5ba606442f71e631e35",
    "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.json":
        "a538c86d69989e6030a157465a779dd7fb950acdb7573c9680c043e92a222db0",
    "data/cosmology_r113/R113_ONE_POLE_CLUSTER_NO_GO_v2.json":
        "d0cbf68192cc26629b9ec92a561b0b999888b6fd5dc518c5648e6cbbbc86fff0",
    "data/cosmology_r103/R103_TWO_SLOPE_BACKGROUND_DENSE_v1.csv":
        "03c9c3e7894e3b0f5b258ba0275abdf76faf80083223fe46f44727c25ebcfe56",
    "data/cosmology_r103/R103_TWO_SLOPE_BACKGROUND_DENSE_METADATA_v1.json":
        "94bc139e3f76701a9f7cee574d20e8d2e7cbed4bf174a8206e3191e6faeff6da",
    "data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json":
        "7ab8fb98486fbd9a4a80e0c2777f666bc455a26c8f3d9bb0c6d19aa4217f151f",
    "data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv":
        "fe7d5c9b4aca42ff7e552e38eef96284efcdc89cdd9066d63b8f5bfe6c4acd8e",
    "data/cosmology_r103/R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json":
        "58bcb51d1c22823f165dfcd490705825add959e3378a60268be4f44243f834eb",
}

CVD_MATRICES = {
    "protanopia": np.array(
        [
            [0.152286, 1.052583, -0.204868],
            [0.114503, 0.786281, 0.099216],
            [-0.003882, -0.048116, 1.051998],
        ]
    ),
    "deuteranopia": np.array(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ]
    ),
    "tritanopia": np.array(
        [
            [1.255528, -0.076749, -0.178779],
            [-0.078411, 0.930809, 0.147602],
            [0.004733, 0.691367, 0.303900],
        ]
    ),
}

SERIES_QA: list[dict[str, Any]] = []
OUTPUTS: list[dict[str, Any]] = []
UNRESOLVED = [
    {
        "figure_id": "fig:r114_pes_m1_same_channel_fdt_protocol",
        "outcome": "NO DENSE RECOVERED OWNER",
        "reason": (
            "The flat same-channel input is analytic, but the recovered "
            "susceptibility is supplied at only seven protocol nodes.  R154 "
            "does not invent a dense recovered curve between those nodes."
        ),
    },
    {
        "figure_id": "fig:r103_ect_restricted_perturbation_proxies",
        "outcome": "PARAMETRIC ONLY",
        "reason": (
            "The 3001-point owner contains q, dq/dN, H, F and background "
            "densities, but not the downstream growth, Weyl, ISW or velocity "
            "carrier solves.  The existing R153 four-node unconnected-marker "
            "render is therefore the safe endpoint."
        ),
    },
    {
        "figure_id": "fig:r123_atlas_f42e",
        "outcome": "INDEPENDENT PARAMETER GRID",
        "reason": (
            "The existing panel is a three-by-three collection of separately "
            "evaluated action/state points rather than samples of one "
            "continuous owner curve.  Its unconnected scatter semantics "
            "remain appropriate."
        ),
    },
    {
        "figure_id": "fig:r114_early_response_growth_collapse_envelope",
        "outcome": "NO DENSE OWNER",
        "reason": (
            "Only five prescribed owner rows exist.  R154 renders them as "
            "unconnected markers and does not invent an interpolant."
        ),
    },
    {
        "figure_id": (
            "fig:r114_early_response_growth_collapse_envelope"
            "__continuation_rare_tail"
        ),
        "outcome": "NO DENSE OWNER",
        "reason": (
            "Only five prescribed rare-tail rows exist.  R154 renders them as "
            "unconnected markers and does not invent an interpolant."
        ),
    },
    {
        "figure_id": "fig:r114_finitebody_scalar_gates",
        "outcome": "NO DENSE OWNER",
        "reason": (
            "The fixed-metric BVP proxy table contains four supplied density "
            "rows.  R154 renders them as unconnected markers."
        ),
    },
    {
        "figure_id": "fig:r123_atlas_f10b",
        "outcome": "INDEPENDENT PARAMETER NODES",
        "reason": (
            "Each kappa family contains three separately solved a-values, not "
            "a continuous a-scan.  R154 removes the straight guide segments."
        ),
    },
    {
        "figure_id": "fig:r123_conditional_universe_timeline",
        "outcome": "NO CONTINUOUS EVENT OWNER",
        "reason": (
            "The frozen event-redshift table is not a dense event-history "
            "solution.  The existing R153 residual markers remain appropriate."
        ),
    },
]

CAPTION_PHRASES = {
    "fig:neutrino_seesaw": (
        "The five curves are densely evaluated analytic benchmark relations; "
        "no sampled-data markers or fitted interpolation is implied."
    ),
    "fig:neutrino_corrections": (
        "Both traces are densely evaluated analytic benchmark relations; "
        "no sampled-data markers or fitted interpolation is implied."
    ),
    "fig:r123_condensate_orbit": (
        "Panels (a,b) are dense frozen solver histories without decorative "
        "markers; panels (c,d) use solver-owned dense background traces with "
        "the nine published diagnostic nodes shown separately."
    ),
    "fig:qubit_info_decoherence": (
        "Both continuous traces are analytic relations of the declared "
        "pure-dilation toy; no sampled-data markers are implied."
    ),
    "fig:r123_atlas_f35a": (
        "The smooth line is the densely evaluated exact external Tolman "
        "relation, not a fit to sampled data."
    ),
    "fig:r123_atlas_f35c": (
        "The smooth line is the densely evaluated exact external Hawking "
        "benchmark, not a fit to sampled data."
    ),
    "fig:r114_early_response_growth_collapse_envelope": (
        "The five prescribed owner rows are shown as unconnected markers; "
        "no intermediate interpolation is implied."
    ),
    (
        "fig:r114_early_response_growth_collapse_envelope"
        "__continuation_rare_tail"
    ): (
        "The five prescribed rare-tail rows are shown as unconnected markers; "
        "no intermediate interpolation is implied."
    ),
    "fig:r114_finitebody_scalar_gates": (
        "The four supplied fixed-metric BVP rows are shown as unconnected "
        "markers; no continuous density scan is implied."
    ),
    "fig:r123_atlas_f10b": (
        "Each kappa family consists of three independently solved parameter "
        "nodes shown without connecting segments."
    ),
    "fig:r123_atlas_f11b": (
        "The continuous trace is the densely evaluated exact relation "
        "d=v tau; crosses mark the frozen source nodes."
    ),
    "fig:r103_ect_background_clocks": (
        "The continuous clock traces are replayed from the frozen 3001-point "
        "background owner; the nine published nodes are shown separately."
    ),
    "fig:r103_two_slope_HwG_conditional": (
        "The continuous expansion trace is replayed from the frozen "
        "3001-point background owner; the nine published nodes are shown "
        "separately."
    ),
    (
        "fig:r103_two_slope_HwG_conditional"
        "__continuation_inverse_F"
    ): (
        "The continuous inverse-F trace is evaluated directly on the frozen "
        "3001-point background owner; the nine published nodes are shown "
        "separately."
    ),
    "fig:r123_atlas_f42a": (
        "The continuous expansion trace is evaluated on the frozen "
        "3001-point background owner; the nine published nodes are shown "
        "separately."
    ),
    "fig:r123_atlas_f42c": (
        "The continuous distance trace is obtained by deterministic "
        "quadrature of the frozen dense background; the eight nonzero-z "
        "published nodes are shown separately."
    ),
    "fig:r123_atlas_f42d": (
        "Both continuous effective-equation-of-state traces are evaluated on the frozen dense "
        "background and declared matched control; the nine published nodes "
        "are shown separately."
    ),
    "fig:r123_atlas_f43b": (
        "Both continuous effective-equation-of-state traces are evaluated on the frozen dense "
        "background and declared matched control; the nine published nodes "
        "are shown separately."
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def canonical_array_hash(*arrays: Iterable[float]) -> str:
    digest = hashlib.sha256()
    for values in arrays:
        arr = np.ascontiguousarray(np.asarray(values, dtype="<f8"))
        digest.update(str(arr.shape).encode("ascii"))
        digest.update(arr.tobytes())
    return digest.hexdigest()


def assert_input_locks() -> dict[str, str]:
    actual: dict[str, str] = {}
    for relative, expected in INPUT_LOCKS.items():
        path = LATEX / relative
        if not path.is_file():
            raise RuntimeError(f"missing frozen input: {path}")
        digest = sha256(path)
        if digest != expected:
            raise RuntimeError(
                f"input lock mismatch for {relative}: {digest} != {expected}"
            )
        actual[f"LaTex/{relative}"] = digest
    return actual


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_numeric_csv(path: Path) -> list[dict[str, float]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [
            {key: float(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]
    if not rows:
        raise RuntimeError(f"empty numeric CSV: {path}")
    return rows


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.2,
            "axes.titlesize": 12.0,
            "axes.labelsize": 10.6,
            "legend.fontsize": 9.2,
            "xtick.labelsize": 9.4,
            "ytick.labelsize": 9.4,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.85,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "grid.alpha": 0.8,
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4,
    )


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    return np.where(
        rgb <= 0.0031308,
        12.92 * rgb,
        1.055 * np.power(np.clip(rgb, 0.0, None), 1.0 / 2.4) - 0.055,
    )


def make_accessibility_previews(png_path: Path, qa_dir: Path) -> list[Path]:
    qa_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(png_path).convert("RGB")
    outputs: list[Path] = []
    colour = qa_dir / f"{png_path.stem}_colour.png"
    source.save(colour, optimize=False)
    outputs.append(colour)
    gray = qa_dir / f"{png_path.stem}_grayscale.png"
    source.convert("L").convert("RGB").save(gray, optimize=False)
    outputs.append(gray)
    rgb = np.asarray(source, dtype=float) / 255.0
    linear = srgb_to_linear(rgb)
    for name, matrix in CVD_MATRICES.items():
        transformed = np.einsum("...j,ij->...i", linear, matrix)
        encoded = np.clip(linear_to_srgb(transformed), 0.0, 1.0)
        path = qa_dir / f"{png_path.stem}_{name}.png"
        Image.fromarray(np.uint8(np.rint(encoded * 255.0))).save(
            path, optimize=False
        )
        outputs.append(path)
    return outputs


def record_series(
    *,
    figure_id: str,
    output_stem: str,
    series: str,
    semantics: str,
    scientific_status: str,
    source_path: Path,
    source_points: int,
    line_points: int,
    marker_points: int,
    x: Iterable[float],
    y: Iterable[float],
    decorative_markers_removed: bool = False,
    source_node_max_abs_residual: float | None = None,
    source_node_max_rel_residual: float | None = None,
    tolerance: float | None = None,
    method: str = "",
    verdict: str = "PASS",
) -> None:
    SERIES_QA.append(
        {
            "figure_id": figure_id,
            "output_stem": output_stem,
            "series": series,
            "semantics": semantics,
            "scientific_status": scientific_status,
            "source_path": rel(source_path),
            "source_sha256": sha256(source_path),
            "source_points": int(source_points),
            "rendered_line_points": int(line_points),
            "rendered_marker_points": int(marker_points),
            "numeric_payload_sha256": canonical_array_hash(x, y),
            "decorative_markers_removed": decorative_markers_removed,
            "source_node_max_abs_residual": source_node_max_abs_residual,
            "source_node_max_rel_residual": source_node_max_rel_residual,
            "declared_tolerance": tolerance,
            "method": method,
            "verdict": verdict,
        }
    )


def write_figure(
    fig: plt.Figure,
    output_root: Path,
    stem: str,
    title: str,
    figure_ids: list[str],
) -> None:
    assets = output_root / "assets"
    qa_dir = output_root / "qa"
    assets.mkdir(parents=True, exist_ok=True)
    pdf = assets / f"{stem}.pdf"
    png = assets / f"{stem}.png"
    metadata = {
        "Title": title,
        "Author": "ECT reproducibility workflow",
        "Subject": (
            "R154 proposal-only line-semantics successor; frozen numerical "
            "payload; no smoothing or new fit"
        ),
        "Keywords": "ECT R154 curve semantics proposal-only",
        "Creator": SCRIPT.name,
        "CreationDate": FIXED_TIME,
        "ModDate": FIXED_TIME,
    }
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.08, metadata=metadata)
    fig.savefig(
        png,
        dpi=240,
        bbox_inches="tight",
        pad_inches=0.08,
        metadata={
            "Software": SCRIPT.name,
            "Title": title,
            "Description": metadata["Subject"],
        },
    )
    plt.close(fig)
    previews = make_accessibility_previews(png, qa_dir)
    with Image.open(png) as image:
        pixel_size = [int(image.width), int(image.height)]
    OUTPUTS.append(
        {
            "stem": stem,
            "figure_ids": figure_ids,
            "title": title,
            "pdf": rel(pdf),
            "pdf_sha256": sha256(pdf),
            "png": rel(png),
            "png_sha256": sha256(png),
            "png_pixels": pixel_size,
            "accessibility_previews": [
                {"path": rel(path), "sha256": sha256(path)} for path in previews
            ],
        }
    )


def marker_visible(line: Line2D) -> bool:
    return line.get_marker() not in (None, "None", "", " ")


def refresh_existing_legends(fig: plt.Figure) -> None:
    """Rebuild legends after artist semantics change.

    Matplotlib legends retain copied handles, so changing a source line after
    ``legend()`` does not remove the old decorative marker from the legend.
    """

    for ax in fig.findobj(match=Axes):
        legend = ax.get_legend()
        if legend is None:
            continue
        location = getattr(legend, "_loc", "best")
        frameon = legend.get_frame_on()
        handles, labels = ax.get_legend_handles_labels()
        legend.remove()
        if handles:
            ax.legend(handles, labels, loc=location, frameon=frameon)


def refresh_combined_legend(
    fig: plt.Figure,
    *,
    target: Axes,
    location: str,
) -> None:
    handles: list[Any] = []
    labels: list[str] = []
    for ax in fig.findobj(match=Axes):
        current_handles, current_labels = ax.get_legend_handles_labels()
        handles.extend(current_handles)
        labels.extend(current_labels)
        if ax.get_legend() is not None:
            ax.get_legend().remove()
    target.legend(handles, labels, loc=location, frameon=False)


def strip_dense_decorative_markers(
    fig: plt.Figure,
    *,
    figure_id: str,
    output_stem: str,
    source_path: Path,
    scientific_status: str,
    min_points: int,
) -> int:
    changed = 0
    for ax in fig.findobj(match=Axes):
        for index, line in enumerate(ax.lines):
            x = np.asarray(line.get_xdata(), dtype=float)
            y = np.asarray(line.get_ydata(), dtype=float)
            if (
                x.size < min_points
                or y.size != x.size
                or not marker_visible(line)
                or line.get_linestyle() in (None, "None", "", " ")
            ):
                continue
            label = line.get_label()
            line.set_marker("None")
            line.set_markevery(None)
            record_series(
                figure_id=figure_id,
                output_stem=output_stem,
                series=label if label and not label.startswith("_") else f"dense_line_{index}",
                semantics="exact_or_dense_curve",
                scientific_status=scientific_status,
                source_path=source_path,
                source_points=x.size,
                line_points=x.size,
                marker_points=0,
                x=x,
                y=y,
                decorative_markers_removed=True,
                tolerance=0.0,
                method="unchanged x/y arrays; decorative marker artist removed",
            )
            changed += 1
    return changed


def record_marker_free_dense_lines(
    fig: plt.Figure,
    *,
    figure_id: str,
    output_stem: str,
    source_path: Path,
    scientific_status: str,
    min_points: int,
    already_recorded_labels: set[str],
) -> None:
    for ax in fig.findobj(match=Axes):
        for index, line in enumerate(ax.lines):
            x = np.asarray(line.get_xdata(), dtype=float)
            y = np.asarray(line.get_ydata(), dtype=float)
            label = line.get_label()
            key = label if label and not label.startswith("_") else f"dense_line_{index}"
            if (
                x.size < min_points
                or y.size != x.size
                or marker_visible(line)
                or line.get_linestyle() in (None, "None", "", " ")
                or key in already_recorded_labels
            ):
                continue
            record_series(
                figure_id=figure_id,
                output_stem=output_stem,
                series=key,
                semantics="exact_or_dense_curve",
                scientific_status=scientific_status,
                source_path=source_path,
                source_points=x.size,
                line_points=x.size,
                marker_points=0,
                x=x,
                y=y,
                tolerance=0.0,
                method="existing continuous exact/dense line retained unchanged",
            )


def capture_r149_figure(module: ModuleType, function_name: str) -> plt.Figure:
    holder: dict[str, plt.Figure] = {}

    def capture(
        fig: plt.Figure,
        _stem: str,
        _title: str,
        _subject: str,
    ) -> None:
        holder["fig"] = fig

    module.save = capture
    getattr(module, function_name)()
    if "fig" not in holder:
        raise RuntimeError(f"R149 capture failed: {function_name}")
    return holder["fig"]


def build_r149_exact_curves(output_root: Path) -> None:
    source = (
        LATEX
        / "work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/"
        "remaining_figure_typography/scripts/build_r149_remaining_typography.py"
    )
    module = load_module("r154_r149_remaining", source)
    module.configure()
    specs = [
        (
            "seesaw",
            "fig:neutrino_seesaw",
            "fig_neutrino_seesaw_smooth_r154",
            "Conditional supplied seesaw benchmark",
            "Level C/Open supplied benchmark; not an ECT prediction",
            4,
        ),
        (
            "neutrino_correction",
            "fig:neutrino_corrections",
            "fig_neutrino_corrections_smooth_r154",
            "Optional preferred-direction neutrino diagnostic",
            "Open vertex/coefficient; benchmark only",
            2,
        ),
        (
            "qubit",
            "fig:qubit_info_decoherence",
            "fig_qubit_info_decoherence_smooth_r154",
            "Pure-dilation qubit toy",
            "Model-internal toy; no collapse or unique-outcome claim",
            2,
        ),
    ]
    for function, figure_id, stem, title, status, expected in specs:
        fig = capture_r149_figure(module, function)
        before = len(SERIES_QA)
        changed = strip_dense_decorative_markers(
            fig,
            figure_id=figure_id,
            output_stem=stem,
            source_path=source,
            scientific_status=status,
            min_points=400,
        )
        if changed != expected:
            raise RuntimeError(
                f"{figure_id}: expected {expected} decorative-marker curves, "
                f"found {changed}"
            )
        labels = {row["series"] for row in SERIES_QA[before:]}
        record_marker_free_dense_lines(
            fig,
            figure_id=figure_id,
            output_stem=stem,
            source_path=source,
            scientific_status=status,
            min_points=400,
            already_recorded_labels=labels,
        )
        if function == "qubit":
            refresh_combined_legend(
                fig,
                target=fig.axes[0],
                location="lower right",
            )
        else:
            refresh_existing_legends(fig)
        write_figure(fig, output_root, stem, title, [figure_id])


def r103_dense_payload() -> dict[str, Any]:
    dense_path = (
        LATEX / "data/cosmology_r103/R103_TWO_SLOPE_BACKGROUND_DENSE_v1.csv"
    )
    meta_path = (
        LATEX
        / "data/cosmology_r103/R103_TWO_SLOPE_BACKGROUND_DENSE_METADATA_v1.json"
    )
    sparse_path = (
        LATEX
        / "data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json"
    )
    dense_rows = load_numeric_csv(dense_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    sparse = json.loads(sparse_path.read_text(encoding="utf-8"))
    if (
        len(dense_rows) != 3001
        or meta.get("grid", {}).get("points") != 3001
        or not meta.get("constraint_gate", {}).get("pass")
        or not sparse.get("all_checks_pass")
    ):
        raise RuntimeError("R103 dense/background owner gate failed")

    frozen_arrays = {
        key: np.asarray([row[key] for row in dense_rows], dtype=float)
        for key in dense_rows[0]
    }
    owner_n = frozen_arrays["N"]
    if (
        not np.all(np.diff(owner_n) > 0.0)
        or not np.all(frozen_arrays["H"] > 0.0)
        or not np.all(frozen_arrays["F"] > 0.0)
    ):
        raise RuntimeError("R103 dense owner monotonicity/positivity gate failed")

    solver_path = (
        LATEX / "scripts/cosmology/compute_r103_two_slope_conditional_observables.py"
    )
    solver = load_module("r154_r103_solver_owner", solver_path)
    dop = solver.integrate_background("DOP853")

    # Replay every frozen owner coordinate first.  This is a provenance gate:
    # subsequent visible traces are owned by the same action, state and solver,
    # not by interpolation of the nine publication nodes.
    owner_q, owner_p, _owner_elapsed = dop.sol(owner_n)
    owner_points = [
        solver.background_point(float(nn), float(qq), float(pp))
        for nn, qq, pp in zip(owner_n, owner_q, owner_p)
    ]
    replay_checks = {
        "q_max_abs": float(np.max(np.abs(owner_q - frozen_arrays["q"]))),
        "p_max_abs": float(np.max(np.abs(owner_p - frozen_arrays["p"]))),
        "H_max_rel": float(
            np.max(
                np.abs(
                    np.asarray([point["H"] for point in owner_points])
                    - frozen_arrays["H"]
                )
                / frozen_arrays["H"]
            )
        ),
        "F_max_abs": float(
            np.max(
                np.abs(
                    np.asarray([point["F"] for point in owner_points])
                    - frozen_arrays["F"]
                )
            )
        ),
    }
    if (
        replay_checks["q_max_abs"] > 5.0e-12
        or replay_checks["p_max_abs"] > 5.0e-12
        or replay_checks["H_max_rel"] > 5.0e-12
        or replay_checks["F_max_abs"] > 5.0e-12
    ):
        raise RuntimeError(f"R103 3001-point owner replay drift: {replay_checks}")

    derived = sparse["derived_today"]
    q0, p0, elapsed0 = map(float, dop.sol(0.0))
    today = solver.background_point(0.0, q0, p0)
    h0 = float(today["H"])
    f0 = float(today["F"])
    if abs(h0 - float(derived["H_in_reference_units"])) > 1.0e-12:
        raise RuntimeError("R103 present-H replay mismatch")
    omega_m = float(derived["Omega_m0_reference_comparator"])
    omega_r = float(derived["Omega_r0_reference_comparator"])
    omega_l = float(derived["Omega_Lambda_reference_comparator"])

    sparse_rows = sorted(sparse["rows"], key=lambda row: float(row["z"]))
    sparse_z = np.asarray([float(row["z"]) for row in sparse_rows])
    sparse_n = -np.log1p(sparse_z)
    n_min = -math.log1p(20.0)
    visible_owner_n = owner_n[owner_n >= n_min]
    # Include the exact publication-node coordinates in the dense solver
    # replay.  The line therefore passes through those independently checked
    # nodes without treating them as interpolation control points.
    n = np.unique(np.concatenate([visible_owner_n, sparse_n]))
    q, p, elapsed = dop.sol(n)
    points = [
        solver.background_point(float(nn), float(qq), float(pp))
        for nn, qq, pp in zip(n, q, p)
    ]
    h = np.asarray([point["H"] for point in points])
    f = np.asarray([point["F"] for point in points])
    h_prime_over_h = np.asarray(
        [point["Hprime_over_H"] for point in points]
    )

    def e_reference(nn: float | np.ndarray) -> float | np.ndarray:
        return np.sqrt(
            omega_r * np.exp(-4.0 * nn)
            + omega_m * np.exp(-3.0 * nn)
            + omega_l
        )

    # The original owner used adaptive quadrature.  Equivalent dense-output
    # ODE integrals preserve the declared tolerances while evaluating every
    # visible owner coordinate in one deterministic replay.
    reference_integrals = solver.solve_ivp(
        lambda nn, _state: np.asarray(
            [1.0 / e_reference(nn), np.exp(-nn) / e_reference(nn)]
        ),
        (solver.N_INITIAL, 0.0),
        np.asarray([0.0, 0.0]),
        method="DOP853",
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
        dense_output=True,
    )
    model_chi_integral = solver.solve_ivp(
        lambda nn, _state: np.asarray(
            [
                np.exp(-nn)
                * h0
                / solver.background_point(
                    nn,
                    float(dop.sol(nn)[0]),
                    float(dop.sol(nn)[1]),
                )["H"]
            ]
        ),
        (solver.N_INITIAL, 0.0),
        np.asarray([0.0]),
        method="DOP853",
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
        dense_output=True,
    )
    if not reference_integrals.success or not model_chi_integral.success:
        raise RuntimeError("R103 dense integral replay failed")

    e_two = h / h0
    e_ref = np.asarray(e_reference(n))
    delta_e = 100.0 * (e_two / e_ref - 1.0)
    w_two = -1.0 - 2.0 * h_prime_over_h / 3.0
    h_prime_ref = -(
        4.0 * omega_r * np.exp(-4.0 * n)
        + 3.0 * omega_m * np.exp(-3.0 * n)
    ) / (2.0 * e_ref**2)
    w_ref = -1.0 - 2.0 * h_prime_ref / 3.0
    age_two = h0 * elapsed
    reference_values = reference_integrals.sol(n)
    age_ref = reference_values[0]
    chi_ref = float(reference_integrals.y[1, -1]) - reference_values[1]
    model_chi_values = model_chi_integral.sol(n)[0]
    chi_two = float(model_chi_integral.y[0, -1]) - model_chi_values
    delta_chi = np.zeros_like(n)
    nonzero = chi_ref > 0.0
    delta_chi[nonzero] = 100.0 * (
        chi_two[nonzero] / chi_ref[nonzero] - 1.0
    )
    f_over_f0 = f / f0
    inverse_f_percent = 100.0 * (1.0 / f_over_f0 - 1.0)

    return {
        "dense_path": dense_path,
        "solver_path": solver_path,
        "sparse_path": sparse_path,
        "owner_points": len(owner_n),
        "owner_replay_gate": replay_checks,
        "N_all": n,
        "N": n,
        "z": np.exp(-n) - 1.0,
        "E_two_slope": e_two,
        "E_reference": e_ref,
        "delta_E_percent": delta_e,
        "w_eff_two_slope": w_two,
        "w_eff_reference": w_ref,
        "H0_t_two_slope": age_two,
        "H0_t_reference": age_ref,
        "H0_chi_over_c_two_slope": chi_two,
        "H0_chi_over_c_reference": chi_ref,
        "delta_chi_percent": delta_chi,
        "F_over_F0": f_over_f0,
        "inverse_F_percent": inverse_f_percent,
        "all": {
            "E_two_slope": e_two,
            "E_reference": e_ref,
            "delta_E_percent": delta_e,
            "w_eff_two_slope": w_two,
            "w_eff_reference": w_ref,
            "H0_t_two_slope": age_two,
            "H0_t_reference": age_ref,
            "H0_chi_over_c_two_slope": chi_two,
            "H0_chi_over_c_reference": chi_ref,
            "delta_chi_percent": delta_chi,
            "F_over_F0": f_over_f0,
            "inverse_F_percent": inverse_f_percent,
        },
        "sparse_rows": sparse_rows,
        "sparse_z": sparse_z,
        "sparse_n": sparse_n,
    }


R103_TOLERANCES = {
    "E_two_slope": 5.0e-10,
    "E_reference": 5.0e-10,
    "delta_E_percent": 5.0e-9,
    "w_eff_two_slope": 5.0e-10,
    "w_eff_reference": 5.0e-10,
    "H0_t_two_slope": 5.0e-10,
    "H0_t_reference": 5.0e-9,
    "H0_chi_over_c_two_slope": 5.0e-9,
    "H0_chi_over_c_reference": 5.0e-9,
    "delta_chi_percent": 5.0e-7,
    "F_over_F0": 5.0e-10,
    "inverse_F_percent": 5.0e-8,
}


def sparse_values(payload: dict[str, Any], key: str) -> np.ndarray:
    rows = payload["sparse_rows"]
    if key == "inverse_F_percent":
        return np.asarray(
            [100.0 * (1.0 / float(row["F_over_F0"]) - 1.0) for row in rows]
        )
    return np.asarray([float(row[key]) for row in rows])


def r103_residual(
    payload: dict[str, Any],
    key: str,
    *,
    omit_z0: bool = False,
) -> tuple[float, float, int]:
    source = sparse_values(payload, key)
    nodes = payload["sparse_n"]
    if omit_z0:
        source = source[1:]
        nodes = nodes[1:]
    reconstructed = np.interp(
        nodes,
        payload["N_all"],
        payload["all"][key],
    )
    residual = reconstructed - source
    max_abs = float(np.max(np.abs(residual)))
    scale = np.maximum(np.abs(source), 1.0e-12)
    max_rel = float(np.max(np.abs(residual) / scale))
    tolerance = R103_TOLERANCES[key]
    if max_abs > tolerance:
        raise RuntimeError(
            f"R103 dense/source-node gate failed for {key}: "
            f"{max_abs} > {tolerance}"
        )
    return max_abs, max_rel, len(source)


def record_r103_series(
    payload: dict[str, Any],
    *,
    figure_id: str,
    output_stem: str,
    key: str,
    series: str,
    omit_z0: bool = False,
    status: str = (
        "Level A background inside supplied action/state; Level C physical map"
    ),
) -> None:
    max_abs, max_rel, nodes = r103_residual(
        payload, key, omit_z0=omit_z0
    )
    x = np.log1p(payload["z"])
    y = payload[key]
    if omit_z0:
        valid = payload["z"] > 0.0
        x = x[valid]
        y = y[valid]
    record_series(
        figure_id=figure_id,
        output_stem=output_stem,
        series=series,
        semantics="dense_frozen_solver_curve_plus_source_markers",
        scientific_status=status,
        source_path=payload["dense_path"],
        source_points=payload["owner_points"],
        line_points=len(x),
        marker_points=nodes,
        x=x,
        y=y,
        source_node_max_abs_residual=max_abs,
        source_node_max_rel_residual=max_rel,
        tolerance=R103_TOLERANCES[key],
        method=(
            "canonical owner solver replay on the visible coordinates of the "
            "frozen 3001-point grid, augmented by exact published-node "
            "coordinates; separate 8/9 nodes are QA/source markers"
        ),
    )


def source_marker_overlay(
    ax: Axes,
    payload: dict[str, Any],
    key: str,
    *,
    marker: str,
    colour: str,
    omit_z0: bool = False,
) -> None:
    z = payload["sparse_z"]
    y = sparse_values(payload, key)
    if omit_z0:
        z = z[1:]
        y = y[1:]
    ax.plot(
        np.log1p(z),
        y,
        linestyle="None",
        marker=marker,
        ms=4.2,
        markerfacecolor="white",
        markeredgecolor=colour,
        markeredgewidth=0.9,
        alpha=0.85,
        label="_nolegend_",
        zorder=5,
    )


def dense_xy(payload: dict[str, Any], key: str) -> tuple[np.ndarray, np.ndarray]:
    x = np.log1p(payload["z"])
    order = np.argsort(x)
    return x[order], np.asarray(payload[key])[order]


def build_background_panels(
    output_root: Path,
    payload: dict[str, Any],
) -> None:
    specs = [
        {
            "ids": ["fig:r123_atlas_f42a"],
            "stem": "fig42_a_named_expansion_dense_r154",
            "title": "Named two-slope expansion",
            "ylabel": r"$\Delta H/H_{\rm ctl}$ [\%]",
            "series": [
                ("delta_E_percent", "two-slope / matched control", BLUE, "-", "o", False)
            ],
            "footer": "Dense frozen background replay; not a unique P1--P6 cosmology.",
        },
        {
            "ids": ["fig:r103_ect_background_clocks"],
            "stem": "fig42_b_clock_budget_dense_r154",
            "title": "Conditional clock budget",
            "ylabel": r"$H(0)t(z)$",
            "series": [
                ("H0_t_two_slope", "two-slope", BLUE, "-", "o", False),
                ("H0_t_reference", "matched control", GRAPHITE, "--", "s", False),
            ],
            "footer": "Dense background quadrature; H0 remains a declared calibration.",
        },
        {
            "ids": ["fig:r123_atlas_f42c"],
            "stem": "fig42_c_comoving_distance_dense_r154",
            "title": "Conditional comoving distance",
            "ylabel": r"$\Delta\chi/\chi_{\rm ctl}$ [\%]",
            "series": [
                ("delta_chi_percent", "two-slope / matched control", PURPLE, "-.", "^", True)
            ],
            "footer": "Dense background quadrature; photon metric remains a supplied assumption.",
        },
        {
            "ids": ["fig:r123_atlas_f42d"],
            "stem": "fig42_d_background_w_dense_r154",
            "title": "Total background equation of state",
            "ylabel": r"$w_{\rm eff}=-1-2H'/(3H)$",
            "series": [
                ("w_eff_two_slope", "two-slope", BLUE, "-", "o", False),
                ("w_eff_reference", "matched control", GRAPHITE, "--", "s", False),
            ],
            "footer": r"Total kinematic $w_{\rm eff}$; not $w_{\rm DE}$.",
        },
        {
            "ids": ["fig:r103_two_slope_HwG_conditional"],
            "stem": "fig43_a_two_slope_expansion_dense_r154",
            "title": "Conditional two-slope expansion response",
            "ylabel": r"$100(H_{2s}/H_{\rm ctl}-1)$ [\%]",
            "series": [
                ("delta_E_percent", "two-slope / control", BLUE, "-", "o", False)
            ],
            "footer": "Supplied action/state; Level C observable diagnostic.",
        },
        {
            "ids": [
                "fig:r103_two_slope_HwG_conditional"
                "__continuation_inverse_F"
            ],
            "stem": "r149_inverse_f_proxy_dense_r154",
            "title": r"Inverse-$F$ background proxy",
            "ylabel": r"$100(F_0/F-1)$ [\%]",
            "series": [
                ("inverse_F_percent", r"$F_0/F(z)-1$", ORANGE, "-.", "D", False)
            ],
            "footer": r"Background proxy only; not a local $G_N$.",
        },
        {
            "ids": ["fig:r123_atlas_f43b"],
            "stem": "fig43_b_two_slope_w_dense_r154",
            "title": "Conditional total kinematic equation of state",
            "ylabel": r"$w_{\rm eff}=-1-2H'/(3H)$",
            "series": [
                ("w_eff_two_slope", "two-slope", GREEN, "-.", "^", False),
                ("w_eff_reference", "matched control", GRAPHITE, "--", "s", False),
            ],
            "footer": "Supplied action/state; no common-epsilon law.",
        },
    ]
    for spec in specs:
        fig, ax = plt.subplots(figsize=(6.65, 4.9))
        fig.subplots_adjust(left=0.14, right=0.98, bottom=0.20, top=0.83)
        for key, label, colour, linestyle, marker, omit_z0 in spec["series"]:
            x, y = dense_xy(payload, key)
            if omit_z0:
                keep = x > 0.0
                x, y = x[keep], y[keep]
            ax.plot(x, y, color=colour, ls=linestyle, lw=2.0, label=label)
            source_marker_overlay(
                ax,
                payload,
                key,
                marker=marker,
                colour=colour,
                omit_z0=omit_z0,
            )
            record_r103_series(
                payload,
                figure_id=spec["ids"][0],
                output_stem=spec["stem"],
                key=key,
                series=label,
                omit_z0=omit_z0,
            )
        if any(
            key in {"delta_E_percent", "delta_chi_percent", "inverse_F_percent"}
            for key, *_rest in spec["series"]
        ):
            ax.axhline(0.0, color=GRAPHITE, lw=1.0, ls=":")
        ax.set_xlim(0.0, math.log1p(20.0))
        ax.set_xlabel(r"$\ln(1+z)$")
        ax.set_ylabel(spec["ylabel"])
        ax.set_title(spec["title"], weight="bold")
        ax.legend(frameon=False, loc="best")
        fig.text(
            0.5,
            0.055,
            spec["footer"],
            ha="center",
            va="bottom",
            fontsize=9.0,
            color=GRAPHITE,
        )
        write_figure(
            fig,
            output_root,
            spec["stem"],
            spec["title"],
            spec["ids"],
        )


def axis_with_title(fig: plt.Figure, token: str) -> Axes:
    matches = [
        ax for ax in fig.findobj(match=Axes) if token in ax.get_title()
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one axis titled {token!r}, got {len(matches)}")
    return matches[0]


def replace_sparse_line_with_dense(
    ax: Axes,
    *,
    payload: dict[str, Any],
    key: str,
    source_label: str | None,
    dense_label: str,
    colour: str,
    linestyle: str,
    marker: str,
    omit_z0: bool,
    semilogy: bool = False,
) -> None:
    candidates = []
    for line in ax.lines:
        x = np.asarray(line.get_xdata())
        if x.size not in (8, 9) or not marker_visible(line):
            continue
        if source_label is not None and line.get_label() != source_label:
            continue
        candidates.append(line)
    if len(candidates) != 1:
        raise RuntimeError(
            f"{ax.get_title()}/{key}: expected one sparse source line, "
            f"got {len(candidates)}"
        )
    source = candidates[0]
    source.set_linestyle("None")
    source.set_linewidth(0.0)
    source.set_label("_nolegend_")
    n = payload["N"]
    y = payload[key]
    if omit_z0:
        keep = payload["z"] > 0.0
        n, y = n[keep], y[keep]
    method = ax.semilogy if semilogy else ax.plot
    method(
        n,
        y,
        color=colour,
        ls=linestyle,
        lw=2.0,
        label=dense_label,
        zorder=3,
    )


def build_condensate_orbit(
    output_root: Path,
    payload: dict[str, Any],
) -> None:
    source = (
        LATEX
        / "work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/"
        "figure_typography_successors/scripts/"
        "build_r149_evolution_typography_successors.py"
    )
    module = load_module("r154_evolution_owner", source)
    module.verify_inputs()
    dense = module.load_csv(module.INPUTS["dense"][0])
    observables = module.load_csv(module.INPUTS["observables"][0])
    holder: dict[str, plt.Figure] = {}

    def capture(fig: plt.Figure, stem: str) -> None:
        if stem != "r149_conditional_post_ordering_evolution_typography":
            raise RuntimeError(f"unexpected evolution stem: {stem}")
        holder["fig"] = fig

    module.save = capture
    module.conditional_post_ordering(dense, observables)
    fig = holder["fig"]
    stem = "conditional_post_ordering_dense_r154"
    figure_id = "fig:r123_condensate_orbit"

    removed = strip_dense_decorative_markers(
        fig,
        figure_id=figure_id,
        output_stem=stem,
        source_path=source,
        scientific_status=(
            "Level A background inside supplied action/state; dimensional "
            "readings Level C"
        ),
        min_points=500,
    )
    if removed != 2:
        raise RuntimeError(
            f"{figure_id}: expected two decorative dense markers, found {removed}"
        )
    record_marker_free_dense_lines(
        fig,
        figure_id=figure_id,
        output_stem=stem,
        source_path=source,
        scientific_status=(
            "Level A background inside supplied action/state; dimensional "
            "readings Level C"
        ),
        min_points=500,
        already_recorded_labels={row["series"] for row in SERIES_QA if row["output_stem"] == stem},
    )

    expansion = axis_with_title(fig, "Expansion history")
    replace_sparse_line_with_dense(
        expansion,
        payload=payload,
        key="E_two_slope",
        source_label="two-slope orbit",
        dense_label="two-slope orbit",
        colour=BLUE,
        linestyle="-",
        marker="o",
        omit_z0=False,
        semilogy=True,
    )
    replace_sparse_line_with_dense(
        expansion,
        payload=payload,
        key="E_reference",
        source_label="matched control",
        dense_label="matched control",
        colour=GRAPHITE,
        linestyle="--",
        marker="D",
        omit_z0=False,
        semilogy=True,
    )
    expansion.legend(frameon=False, loc="upper left")

    inset_matches = [
        ax
        for ax in fig.findobj(match=Axes)
        if "honest residual" in ax.get_title()
    ]
    if len(inset_matches) != 1:
        raise RuntimeError("could not identify conditional-orbit residual inset")
    inset = inset_matches[0]
    residual_line = next(
        (
            line
            for line in inset.lines
            if np.asarray(line.get_xdata()).size == 9 and marker_visible(line)
        ),
        None,
    )
    if residual_line is None:
        raise RuntimeError("missing nine-node residual source line")
    residual_line.set_linestyle("None")
    residual_line.set_linewidth(0.0)
    inset.plot(
        payload["N"],
        1.0e4 * payload["delta_E_percent"],
        color=ORANGE,
        lw=1.5,
    )

    clock = axis_with_title(fig, "Conditional branch clock")
    replace_sparse_line_with_dense(
        clock,
        payload=payload,
        key="H0_t_two_slope",
        source_label="two-slope orbit",
        dense_label="two-slope orbit",
        colour=BLUE,
        linestyle="-",
        marker="o",
        omit_z0=False,
    )
    replace_sparse_line_with_dense(
        clock,
        payload=payload,
        key="H0_t_reference",
        source_label="matched control",
        dense_label="matched control",
        colour=GRAPHITE,
        linestyle="--",
        marker="D",
        omit_z0=False,
    )
    clock.legend(frameon=False, loc="upper left")

    for key, label in (
        ("E_two_slope", "two-slope expansion"),
        ("E_reference", "matched-control expansion"),
        ("delta_E_percent", "expansion residual"),
        ("H0_t_two_slope", "two-slope branch clock"),
        ("H0_t_reference", "matched-control clock"),
    ):
        record_r103_series(
            payload,
            figure_id=figure_id,
            output_stem=stem,
            key=key,
            series=label,
        )
    refresh_existing_legends(fig)
    write_figure(
        fig,
        output_root,
        stem,
        "Conditional post-ordering evolution of the supplied two-slope condensate",
        [figure_id],
    )


def build_black_hole_exact(output_root: Path) -> None:
    source = LATEX / "scripts/fig_bh_information.py"

    fig, ax = plt.subplots(figsize=(6.45, 4.75))
    x = np.linspace(0.035, 6.0, 1200)
    y = 1.0 / x
    ax.plot(
        x,
        y,
        color=BLUE,
        lw=2.2,
        label=r"external kinematics $T_{\rm loc}/T_{\rm ref}=\rho_{\rm ref}/\rho$",
    )
    ax.axhline(
        1.0,
        color=GREEN,
        ls="--",
        lw=1.6,
        label=r"arbitrary reference $T_{\rm ref}$",
    )
    ax.axvline(1.0, color=VERMILION, ls=":", lw=1.8)
    ax.text(
        1.06,
        2.55,
        r"reference point only: $\rho=\rho_{\rm ref}$",
        rotation=90,
        va="center",
        color=VERMILION,
    )
    ax.set(
        xlim=(0.0, 6.0),
        ylim=(0.0, 6.0),
        xlabel=r"proper distance $\rho/\rho_{\rm ref}$",
        ylabel=r"$T_{\rm loc}/T_{\rm ref}$",
        title="External Tolman kinematics",
    )
    ax.legend(loc="upper right", fontsize=8.4)
    stem = "fig35_a_tolman_kinematics_smooth_r154"
    record_series(
        figure_id="fig:r123_atlas_f35a",
        output_stem=stem,
        series=r"$T_{\rm loc}/T_{\rm ref}=1/x$",
        semantics="exact_external_analytic_curve",
        scientific_status="Standard external benchmark; not ECT-specific",
        source_path=source,
        source_points=len(x),
        line_points=len(x),
        marker_points=0,
        x=x,
        y=y,
        decorative_markers_removed=True,
        tolerance=0.0,
        method="exact source formula retained; markevery decoration removed",
    )
    write_figure(
        fig,
        output_root,
        stem,
        "External Tolman kinematics",
        ["fig:r123_atlas_f35a"],
    )

    hbar = 1.054571817e-34
    c = 299_792_458.0
    grav = 6.67430e-11
    kb = 1.380649e-23
    msun = 1.98847e30
    ratio = np.logspace(0.0, 9.0, 500)
    temperature = hbar * c**3 / (8.0 * np.pi * grav * kb * ratio * msun)
    fig, ax = plt.subplots(figsize=(6.45, 4.75))
    ax.loglog(
        ratio,
        temperature,
        color=BLUE,
        lw=2.2,
        label=r"standard Hawking $T_H(M)$",
    )
    ax.text(
        0.50,
        0.25,
        "ECT shell depth: NOT IDENTIFIED\n"
        "requires a P4 control variable, metric,\nstate and transfer map",
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=9.3,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": VERMILION,
            "linewidth": 1.5,
        },
    )
    ax.set(
        xlabel=r"black-hole mass $M/M_\odot$",
        ylabel=r"temperature $T_H$ [K]",
        title="External Hawking benchmark",
    )
    ax.legend(loc="upper right", fontsize=8.4)
    stem = "fig35_c_hawking_benchmark_smooth_r154"
    record_series(
        figure_id="fig:r123_atlas_f35c",
        output_stem=stem,
        series=r"standard Hawking $T_H(M)$",
        semantics="exact_external_analytic_curve",
        scientific_status="Standard external benchmark; ECT shell depth Open",
        source_path=source,
        source_points=len(ratio),
        line_points=len(ratio),
        marker_points=0,
        x=ratio,
        y=temperature,
        decorative_markers_removed=True,
        tolerance=0.0,
        method="exact source formula retained; markevery decoration removed",
    )
    write_figure(
        fig,
        output_root,
        stem,
        "External Hawking benchmark",
        ["fig:r123_atlas_f35c"],
    )


def early_rows() -> tuple[Path, list[dict[str, float]]]:
    source = (
        LATEX
        / "data/cosmology_r113/"
        "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv"
    )
    meta = json.loads(
        (
            LATEX
            / "data/cosmology_r113/"
            "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.json"
        ).read_text(encoding="utf-8")
    )
    rows = sorted(load_numeric_csv(source), key=lambda row: row["zeta_ER"])
    if len(rows) != 5 or not meta.get("all_checks_pass"):
        raise RuntimeError("R113 early-response five-row owner gate failed")
    return source, rows


def marker_series(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    *,
    colour: str,
    marker: str,
    label: str,
    filled: bool = True,
) -> None:
    ax.plot(
        x,
        y,
        linestyle="None",
        marker=marker,
        ms=7.0,
        color=colour,
        markerfacecolor=colour if filled else "white",
        markeredgecolor=INK,
        markeredgewidth=0.65,
        label=label,
        zorder=4,
    )


def build_sparse_early_response(output_root: Path) -> None:
    source, rows = early_rows()
    zeta = np.asarray([row["zeta_ER"] for row in rows])
    specs = [
        (
            "fig:r114_early_response_growth_collapse_envelope",
            "fig44_a_growth_equality_nodes_r154",
            "Growth and equality response",
            "dimensionless ratio",
            [
                (
                    "D_over_D0_z10_zon1000",
                    r"growth $D/D_0$",
                    BLUE,
                    "o",
                    True,
                    "Level A algebra inside supplied early-response envelope",
                ),
                (
                    "equality_ratio",
                    "equality-coordinate ratio",
                    ORANGE,
                    "D",
                    False,
                    "Level A algebra inside supplied early-response envelope",
                ),
            ],
            False,
        ),
        (
            (
                "fig:r114_early_response_growth_collapse_envelope"
                "__continuation_rare_tail"
            ),
            "r149_rare_tail_nodes_r154",
            "Rare-tail sensitivity under two declared collapse barriers",
            "cumulative Press--Schechter sensitivity ratio",
            [
                (
                    "cumulative_PS_ratio_nu5_fixed_barrier",
                    r"fixed barrier, $\nu_0=5$",
                    GREEN,
                    "^",
                    True,
                    "Level C sensitivity; not a posterior or JWST prediction",
                ),
                (
                    "cumulative_PS_ratio_nu5_tophat_barrier",
                    r"top-hat barrier, $\nu_0=5$",
                    PURPLE,
                    "D",
                    False,
                    "Level C sensitivity; not a posterior or JWST prediction",
                ),
            ],
            True,
        ),
    ]
    for figure_id, stem, title, ylabel, series, ylog in specs:
        fig, ax = plt.subplots(figsize=(6.55, 5.0))
        fig.subplots_adjust(left=0.14, right=0.98, bottom=0.16, top=0.88)
        for key, label, colour, marker, filled, status in series:
            y = np.asarray([row[key] for row in rows])
            marker_series(
                ax,
                zeta,
                y,
                colour=colour,
                marker=marker,
                label=label,
                filled=filled,
            )
            record_series(
                figure_id=figure_id,
                output_stem=stem,
                series=label,
                semantics="sparse_deterministic_scan_unconnected_markers",
                scientific_status=status,
                source_path=source,
                source_points=5,
                line_points=0,
                marker_points=5,
                x=zeta,
                y=y,
                tolerance=0.0,
                method="five frozen owner rows; no interpolation or guide segments",
            )
        ax.axhline(1.0, color=GRAPHITE, lw=1.0, ls=":")
        ax.set_xscale("log")
        if ylog:
            ax.set_yscale("log")
        ax.set_xlabel(r"owner coordinate $\zeta_{\rm ER}$")
        if ylog:
            # This inherited descriptor is intentionally retained verbatim,
            # but needs a smaller size to stay inside the standalone page box.
            ax.set_ylabel(ylabel, fontsize=11.5)
        else:
            ax.set_ylabel(ylabel)
        ax.set_title(title, weight="bold")
        ax.legend(frameon=False, loc="upper left")
        ax.text(
            0.98,
            0.04,
            "five prescribed rows; no intermediate curve is implied",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8.8,
            color=GRAPHITE,
        )
        write_figure(fig, output_root, stem, title, [figure_id])


def build_finitebody_nodes(output_root: Path) -> None:
    parser_path = (
        LATEX / "scripts/figures/make_r114_finitebody_scalar_gate_figure.py"
    )
    tex_path = (
        LATEX
        / "work/preprint/R114_VERIFIED_COSMOLOGY_PES_CASCADE_CANDIDATE_v1/"
        "ECT_preprint_R114_verified_cosmology_pes_cascade_candidate_v1.tex"
    )
    module = load_module("r154_finitebody_parser", parser_path)
    text = tex_path.read_text(encoding="utf-8")
    rows = module.parse_proxy_table(text)
    if len(rows) != 4:
        raise RuntimeError("finite-body proxy owner must contain four rows")
    density = np.asarray([float(row["density_contrast"]) for row in rows])
    flux = np.asarray([float(row["surface_flux_ratio"]) for row in rows])
    tail = np.asarray([float(row["far_tail_ratio"]) for row in rows])

    fig, ax = plt.subplots(figsize=(6.55, 5.0))
    marker_series(
        ax,
        density,
        flux,
        colour=BLUE,
        marker="o",
        label="surface flux / linear source",
        filled=True,
    )
    marker_series(
        ax,
        density,
        tail,
        colour=ORANGE,
        marker="D",
        label=r"far tail $A_{\rm far}/A_{\rm lin}$",
        filled=False,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 1.15)
    ax.set_xlabel(r"density contrast $\rho_{\rm in}/\rho_{\rm out}$")
    ax.set_ylabel("dimensionless suppression ratio")
    ax.set_title(r"Fixed-metric BVP, $m_{\rm out}R=1$", weight="bold")
    ax.legend(frameon=False, loc="lower left")
    ax.text(
        0.97,
        0.96,
        "four supplied rows; no continuous density scan is implied",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.7,
        color=GRAPHITE,
    )
    stem = "fig45_a_fixed_metric_bvp_nodes_r154"
    for label, y in (
        ("surface flux / linear source", flux),
        (r"far tail $A_{\rm far}/A_{\rm lin}$", tail),
    ):
        record_series(
            figure_id="fig:r114_finitebody_scalar_gates",
            output_stem=stem,
            series=label,
            semantics="sparse_deterministic_scan_unconnected_markers",
            scientific_status=(
                "Fixed-metric scalar BVP only; not a physical body "
                "sensitivity or PPN prediction"
            ),
            source_path=tex_path,
            source_points=4,
            line_points=0,
            marker_points=4,
            x=density,
            y=y,
            tolerance=0.0,
            method="four hash-frozen manuscript-table rows; no interpolant",
        )
    write_figure(
        fig,
        output_root,
        stem,
        "Fixed-metric finite-body scalar BVP",
        ["fig:r114_finitebody_scalar_gates"],
    )


def build_fixed_angle_nodes(output_root: Path) -> None:
    source = (
        LATEX
        / "data/cosmology_r103/R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload["rows"]
    if len(rows) != 9 or not payload.get("all_checks_pass"):
        raise RuntimeError("fixed-angle calibrated scan owner gate failed")
    colours = {0.05: VERMILION, 1.0: ORANGE, 10.0: GREEN}
    styles = {0.01: "o", 0.03: "s", 0.08: "^"}
    fig, ax = plt.subplots(figsize=(6.55, 5.0))
    stem = "fig10_b_fixed_angle_proxy_nodes_r154"
    for kappa in (0.05, 1.0, 10.0):
        subset = sorted(
            (row for row in rows if float(row["kappa"]) == kappa),
            key=lambda row: float(row["a"]),
        )
        if len(subset) != 3:
            raise RuntimeError(f"kappa={kappa}: expected three fixed-angle nodes")
        x = np.asarray(
            [float(row["G_eff_early_over_today_long_range"]) for row in subset]
        )
        y = np.asarray(
            [
                float(row["H0_fixed_acoustic_angle_proxy_from_67p4"])
                for row in subset
            ]
        )
        for row, xx, yy in zip(subset, x, y):
            ax.scatter(
                xx,
                yy,
                color=colours[kappa],
                marker=styles[float(row["a"])],
                s=72,
                edgecolor=INK,
                linewidth=0.6,
                zorder=4,
            )
        record_series(
            figure_id="fig:r123_atlas_f10b",
            output_stem=stem,
            series=rf"$\kappa_s={kappa:g}$",
            semantics="independent_parameter_nodes_unconnected",
            scientific_status="Level C diagnostic; not a CMB likelihood",
            source_path=source,
            source_points=3,
            line_points=0,
            marker_points=3,
            x=x,
            y=y,
            tolerance=0.0,
            method="three separately solved a-values; no continuous a-scan owner",
        )
    ax.axhline(73.04, color=PURPLE, ls=":", lw=1.2, label="73.04 reference")
    ax.set_xlabel(r"$G_{\rm eff,early}/G_{\rm eff,0}$")
    ax.set_ylabel(r"rough fixed-angle $H_0$ proxy")
    ax.set_title("Diagnostic, not a CMB likelihood", weight="bold")
    kappa_handles = [
        Line2D(
            [0],
            [0],
            color=colours[kappa],
            marker="o",
            ls="None",
            label=rf"$\kappa_s={kappa:g}$",
        )
        for kappa in (0.05, 1.0, 10.0)
    ]
    a_handles = [
        Line2D(
            [0],
            [0],
            color=GRAPHITE,
            marker=marker,
            ls="None",
            label=rf"$a_s={a:g}$",
        )
        for a, marker in styles.items()
    ]
    first = ax.legend(
        handles=kappa_handles,
        frameon=False,
        loc="upper left",
        title="colour",
    )
    ax.add_artist(first)
    ax.legend(
        handles=a_handles,
        frameon=False,
        loc="lower right",
        title="marker",
    )
    write_figure(
        fig,
        output_root,
        stem,
        "Fixed-angle diagnostic proxy",
        ["fig:r123_atlas_f10b"],
    )


def build_ballistic_exact(output_root: Path) -> None:
    source = (
        LATEX / "data/cosmology_r113/R113_ONE_POLE_CLUSTER_NO_GO_v2.json"
    )
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not payload.get("all_checks_pass"):
        raise RuntimeError("one-pole owner gate failed")
    pairs = sorted(
        (
            float(key.removeprefix("v=")),
            1000.0 * float(value),
        )
        for key, value in payload[
            "ballistic_transport_at_H0_70_Mpc"
        ].items()
    )
    speeds, distances = np.asarray(pairs, dtype=float).T
    factor = distances / speeds
    constant = float(np.median(factor))
    residual = distances - constant * speeds
    max_abs = float(np.max(np.abs(residual)))
    if max_abs > 1.0e-9:
        raise RuntimeError(f"ballistic d=v*tau identity gate failed: {max_abs}")
    dense_speed = np.linspace(float(speeds.min()), float(speeds.max()), 401)
    dense_distance = constant * dense_speed

    fig, ax = plt.subplots(figsize=(6.55, 4.85))
    fig.subplots_adjust(left=0.14, right=0.98, bottom=0.20, top=0.83)
    ax.axhspan(
        70.0,
        100.0,
        facecolor=PALE_BLUE,
        edgecolor=BLUE,
        hatch="///",
        linewidth=0.9,
        label="70--100 kpc target offset",
    )
    ax.plot(
        dense_speed,
        dense_distance,
        color=VERMILION,
        ls="-.",
        lw=2.0,
        label=r"exact $d=v\tau_{a_M}$ at $H_0=70$",
    )
    ax.plot(
        speeds,
        distances,
        linestyle="None",
        marker="x",
        ms=8.4,
        mew=1.8,
        color=VERMILION,
        label="frozen source nodes",
    )
    ax.set_yscale("log")
    ax.set_xlabel(r"speed [km s$^{-1}$]")
    ax.set_ylabel("distance [kpc]")
    ax.set_title("Ballistic-distance mismatch", weight="bold")
    ax.legend(frameon=False, loc="center left")
    ax.text(
        0.975,
        0.60,
        "mismatch $2.02\\times10^3$--$3.85\\times10^3$\n"
        "restricted to one real pole + ballistic transport",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=9.1,
        bbox={
            "boxstyle": "round,pad=.28",
            "facecolor": "white",
            "edgecolor": GRAPHITE,
            "linewidth": 0.75,
        },
    )
    fig.text(
        0.5,
        0.055,
        "Conditional no-go for the named one-real-pole + ballistic model; "
        "general causal kernels remain Open.",
        ha="center",
        fontsize=8.8,
        color=GRAPHITE,
    )
    stem = "fig11_b_ballistic_distance_exact_r154"
    record_series(
        figure_id="fig:r123_atlas_f11b",
        output_stem=stem,
        series=r"$d=v\tau_{a_M}$",
        semantics="dense_exact_line_plus_frozen_source_markers",
        scientific_status=(
            "Conditional Level-A no-go only inside one-real-pole plus "
            "ballistic assumptions"
        ),
        source_path=source,
        source_points=len(speeds),
        line_points=401,
        marker_points=len(speeds),
        x=dense_speed,
        y=dense_distance,
        source_node_max_abs_residual=max_abs,
        source_node_max_rel_residual=float(
            np.max(np.abs(residual) / distances)
        ),
        tolerance=1.0e-9,
        method="exact linear d=v*tau law inferred and verified from frozen owner",
    )
    write_figure(
        fig,
        output_root,
        stem,
        "One-real-pole cluster-scale test: ballistic distance",
        ["fig:r123_atlas_f11b"],
    )


def write_machine_outputs(
    output_root: Path,
    input_hashes: dict[str, str],
) -> None:
    qa_path = output_root / "R154_NONROTATION_SERIES_QA_v1.json"
    manifest_path = output_root / "R154_NONROTATION_OUTPUT_MANIFEST_v1.json"
    asset_map_path = output_root / "R154_NONROTATION_ASSET_MAP_v1.json"
    unresolved_path = output_root / "R154_NONROTATION_UNRESOLVED_v1.json"
    runtime_path = output_root / "R154_NONROTATION_RUNTIME_v1.json"
    report_path = output_root / "R154_NONROTATION_REPORT_v1.md"

    if any(row["verdict"] != "PASS" for row in SERIES_QA):
        raise RuntimeError("one or more per-series QA rows failed")
    qa_payload = {
        "schema": "ECT-R154-nonrotation-series-QA-v1",
        "version": VERSION,
        "policy": {
            "dense_exact_or_solver": "continuous line; no decorative markers",
            "sparse_deterministic": "unconnected source markers",
            "exact_with_source_nodes": (
                "dense exact line plus separate frozen source markers"
            ),
            "smoothing_or_fit_added": False,
        },
        "series_count": len(SERIES_QA),
        "all_pass": True,
        "series": SERIES_QA,
    }
    qa_path.write_text(
        json.dumps(qa_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (LATEX / "FIGURE_REGISTRY.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        registry = {
            row["figure_id"]: row for row in csv.DictReader(handle)
        }
    tex_text = (LATEX / "ECT_preprint.tex").read_text(encoding="utf-8")
    import re

    tex_pdf_tokens: dict[str, set[str]] = {}
    for match in re.finditer(r"([A-Za-z0-9_./-]+\.pdf)", tex_text):
        token = match.group(1)
        tex_pdf_tokens.setdefault(Path(token).name, set()).add(token)

    output_by_id = {
        figure_id: item
        for item in OUTPUTS
        for figure_id in item["figure_ids"]
    }
    asset_rows = []
    for figure_id, output in sorted(output_by_id.items()):
        if figure_id not in registry:
            raise RuntimeError(f"asset-map figure absent from registry: {figure_id}")
        row = registry[figure_id]
        registered = row["current_asset_token"]
        basename = Path(registered).name
        candidates = sorted(tex_pdf_tokens.get(basename, set()))
        installed = [
            token for token in candidates if token.startswith("figures/")
        ]
        if len(installed) == 1:
            live_token = installed[0]
        elif len(candidates) == 1:
            live_token = candidates[0]
        else:
            live_token = registered
        live_path = (
            ROOT / live_token
            if live_token.startswith("LaTex/")
            else LATEX / live_token
        )
        if not live_path.is_file():
            raise RuntimeError(
                f"resolved live asset does not exist for {figure_id}: {live_path}"
            )
        candidate_pdf = ROOT / output["pdf"]
        phrase = CAPTION_PHRASES.get(figure_id)
        if phrase is None:
            raise RuntimeError(f"missing intended caption phrase: {figure_id}")
        asset_rows.append(
            {
                "figure_id": figure_id,
                "live_source_asset_token": live_token,
                "live_source_asset_path": rel(live_path),
                "live_source_asset_basename": live_path.name,
                "live_source_asset_sha256": sha256(live_path),
                "candidate_successor_pdf": output["pdf"],
                "candidate_successor_pdf_sha256": sha256(candidate_pdf),
                "intended_caption_phrase": phrase,
                "apply_status": "CANDIDATE ONLY; NOT APPLIED",
            }
        )
    asset_map_path.write_text(
        json.dumps(
            {
                "schema": "ECT-R154-nonrotation-asset-map-v1",
                "version": VERSION,
                "mapping_count": len(asset_rows),
                "mappings": asset_rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": "ECT-R154-nonrotation-output-manifest-v1",
        "version": VERSION,
        "generator": rel(SCRIPT),
        "generator_sha256": sha256(SCRIPT),
        "input_sha256": input_hashes,
        "outputs": OUTPUTS,
        "series_qa": rel(qa_path),
        "series_qa_sha256": sha256(qa_path),
        "asset_map": rel(asset_map_path),
        "asset_map_sha256": sha256(asset_map_path),
        "candidate_only": True,
        "live_manuscript_changed": False,
        "live_registry_changed": False,
        "publication_figures_changed": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    unresolved_path.write_text(
        json.dumps(
            {
                "schema": "ECT-R154-nonrotation-unresolved-v1",
                "items": UNRESOLVED,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    runtime_path.write_text(
        json.dumps(
            {
                "schema": "ECT-R154-nonrotation-runtime-v1",
                "python": platform.python_version(),
                "numpy": np.__version__,
                "matplotlib": matplotlib.__version__,
                "r103_dense_method": (
                    "canonical DOP853 owner replay plus deterministic "
                    "dense-output clock/distance integrals"
                ),
                "pillow": getattr(Image, "__version__", "unknown"),
                "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
                "timezone": "UTC",
                "render_command": (
                    "python3 LaTex/scripts/r154_curve_semantics/"
                    "build_r154_sparse_and_exact_successors.py"
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# R154 non-rotation curve-semantics candidate",
        "",
        f"- Outputs: {len(OUTPUTS)} PDF/PNG pairs.",
        f"- Per-series QA rows: {len(SERIES_QA)}; all PASS.",
        "- Smoothing, regression, spline or new fit: none.",
        "- Live TeX, registry and publication figures: untouched.",
        "",
        "## Candidate outputs",
        "",
    ]
    for item in OUTPUTS:
        ids = ", ".join(f"`{value}`" for value in item["figure_ids"])
        lines.append(
            f"- {ids}: `{item['pdf']}` (`{item['pdf_sha256']}`)."
        )
    lines.extend(
        [
            "",
            "## Cases without a safe dense replay",
            "",
        ]
    )
    for item in UNRESOLVED:
        lines.append(
            f"- `{item['figure_id']}` — **{item['outcome']}**: "
            f"{item['reason']}"
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_output_root(output_root: Path) -> Path:
    output_root = output_root.resolve()
    allowed = DEFAULT_OUTPUT.resolve()
    if output_root != allowed and allowed not in output_root.parents:
        raise RuntimeError(
            f"candidate-only guard: output must be {allowed} or its child"
        )
    if LATEX / "figures" in [output_root, *output_root.parents]:
        raise RuntimeError("refusing to write into publication figures")
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_root = validate_output_root(args.output_dir)
    configure()
    input_hashes = assert_input_locks()
    r103 = r103_dense_payload()

    build_r149_exact_curves(output_root)
    build_condensate_orbit(output_root, r103)
    build_black_hole_exact(output_root)
    build_sparse_early_response(output_root)
    build_finitebody_nodes(output_root)
    build_fixed_angle_nodes(output_root)
    build_ballistic_exact(output_root)
    build_background_panels(output_root, r103)
    write_machine_outputs(output_root, input_hashes)
    print(
        json.dumps(
            {
                "version": VERSION,
                "output_dir": rel(output_root),
                "outputs": len(OUTPUTS),
                "series_qa_rows": len(SERIES_QA),
                "unresolved_or_markers_only": len(UNRESOLVED),
                "all_pass": True,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
