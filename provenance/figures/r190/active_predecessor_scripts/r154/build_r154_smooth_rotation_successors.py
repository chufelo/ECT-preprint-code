#!/usr/bin/env python3
"""Build R154 display-curve successors for every active SPARC comparison.

This is a proposal-only renderer.  It does not change a fit, a tabulated
model ordinate, an observation, an uncertainty, or any reported statistic.

The older renderers drew straight segments through model values evaluated at
the irregular SPARC radii.  Those segments looked like a piecewise physical
law.  R154 instead:

* keeps observations as unconnected error-bar markers;
* keeps the original tabulated model ordinates as faint, unconnected nodes;
* regularises only the displayed node ordinates to a fixed sub-error RMS
  target under hard residual and topology bounds;
* draws a shape-preserving C1 curve through those regularised display nodes;
* records and gates the residual between that display curve and every source
  model ordinate;
* keeps all numerical fits and diagnostics tied to the original ordinates.

The smoothing target is deterministic and deliberately far below the
observational error scale.  It is a rendering operation, not an additional
astrophysical fit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image
from scipy.interpolate import PchipInterpolator


HERE = Path(__file__).resolve().parent


def discover_workspace_root() -> Path:
    """Locate the full ECT workspace without embedding a machine-specific path.

    The frozen public-repository provenance copy can sit outside the full
    workspace tree.  In that case the renderer requires ``ECT_WORKSPACE_ROOT``
    to name a checkout that contains the historical R123/R149 source owners.
    The public repository intentionally does not redistribute the SPARC-origin
    inputs required by that owner; see ``EXTERNAL_INPUTS.json``.  Absence of a
    complete owner checkout must therefore fail closed, never silently fall
    back to a different data product or a regenerated fit.
    """

    for parent in HERE.parents:
        # Stop at the standalone publication-repository boundary.  That
        # checkout has ECT_preprint.tex at its root and an explicit external-
        # input contract; walking farther upward could accidentally discover a
        # private full workspace and make an apparently standalone replay use
        # undeclared files.
        if (parent / "ECT_preprint.tex").is_file() and (
            parent / "EXTERNAL_INPUTS.json"
        ).is_file():
            break
        if (parent / "LaTex/ECT_preprint.tex").is_file():
            return parent
    supplied = os.environ.get("ECT_WORKSPACE_ROOT")
    if supplied:
        candidate = Path(supplied).expanduser().resolve()
        if (candidate / "LaTex/ECT_preprint.tex").is_file():
            return candidate
        raise RuntimeError(
            "ECT_WORKSPACE_ROOT does not contain LaTex/ECT_preprint.tex: "
            f"{candidate}"
        )
    raise RuntimeError(
        "PROVENANCE_ONLY_EXTERNAL_INPUTS_REQUIRED: the archived R154 renderer "
        "requires the hash-locked R123 atlas producer and non-redistributed "
        "SPARC-origin inputs declared by EXTERNAL_INPUTS.json; set "
        "ECT_WORKSPACE_ROOT only to a complete owner checkout containing "
        "LaTex/ECT_preprint.tex"
    )


ROOT = discover_workspace_root()

MAIN_SOURCE = (
    ROOT
    / "LaTex/work/preprint/R149_READER_LAYOUT_CANDIDATE_v1"
    / "figure_typography_successors/scripts/build_r149_sparc_typography_successors.py"
)
ATLAS_SOURCE = (
    ROOT
    / "LaTex/work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v3"
    / "components/rotation_comparison_full_atlas_r127"
    / "produce_rotation_comparison_full_atlas_r127.py"
)

FIXED_TIME = datetime(2026, 7, 25, 0, 0, 0, tzinfo=timezone.utc)
R154_VERSION = "R154_SMOOTH_CURVE_SEMANTICS_CANDIDATE_v1"
MIN_TOL_KM_S = 0.10
MAX_TOL_KM_S = 0.25
ERROR_FRACTION = 0.05
TARGET_NORMALISED_RMS = 0.20
MAX_NORMALISED_RMS = 0.21
MAX_NORMALISED_ABS = 1.00
MIN_DENSE_POINTS = 401

QA_ROWS: list[dict[str, Any]] = []


def spread_labels_with_minimum_gap(
    values: dict[str, float],
    low: float,
    high: float,
    minimum_gap: float,
) -> dict[str, float]:
    """Spread direct labels deterministically inside a fixed vertical band."""

    ordered = sorted(values, key=lambda key: (values[key], key))
    if not ordered:
        return {}
    positions: dict[str, float] = {}
    previous = low - minimum_gap
    for key in ordered:
        positions[key] = max(values[key], previous + minimum_gap, low)
        previous = positions[key]
    overflow = positions[ordered[-1]] - high
    if overflow > 0.0:
        for key in ordered:
            positions[key] -= overflow
    underflow = low - positions[ordered[0]]
    if underflow > 0.0:
        for key in ordered:
            positions[key] += underflow
    return positions


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tolerance_from_errors(errors: np.ndarray) -> float:
    finite = np.asarray(errors, dtype=float)
    finite = finite[np.isfinite(finite) & (finite > 0.0)]
    if finite.size == 0:
        return MAX_TOL_KM_S
    return float(
        min(
            MAX_TOL_KM_S,
            max(MIN_TOL_KM_S, ERROR_FRACTION * float(np.median(finite))),
        )
    )


def curvature_operator(x: np.ndarray) -> np.ndarray:
    """Return an irregular-grid second-slope-difference operator.

    The radius is first mapped to [0, 1].  Penalising this operator smooths
    the displayed node ordinates without selecting an astrophysical model.
    """

    scaled = (x - x[0]) / (x[-1] - x[0])
    rows = np.zeros((len(x) - 2, len(x)), dtype=float)
    for i in range(1, len(x) - 1):
        left = scaled[i] - scaled[i - 1]
        right = scaled[i + 1] - scaled[i]
        rows[i - 1, i - 1] = 1.0 / left
        rows[i - 1, i] = -(1.0 / left + 1.0 / right)
        rows[i - 1, i + 1] = 1.0 / right
    return rows


def regularised_display_nodes(
    x: np.ndarray,
    y: np.ndarray,
    tolerance: float,
) -> tuple[np.ndarray, float]:
    """Reach a fixed sub-error RMS target with quadratic regularisation.

    The target is one per cent of the median displayed observational error
    whenever the tolerance is not clamped.  We intentionally do *not*
    maximise the regularisation parameter: doing so would spend the entire
    allowed distortion budget and would require a global connectedness proof
    for the combined L2/L-infinity/positivity admissible set.
    """

    penalty = curvature_operator(x)
    identity = np.eye(len(x), dtype=float)

    def solve(lam: float) -> np.ndarray:
        return np.linalg.solve(identity + lam * (penalty.T @ penalty), y)

    target_rms = TARGET_NORMALISED_RMS * tolerance
    low = 0.0
    high = 1.0e-12
    while high < 1.0e12:
        trial = solve(high)
        trial_rms = float(np.sqrt(np.mean((trial - y) ** 2)))
        if trial_rms >= target_rms:
            break
        high *= 10.0
    if high >= 1.0e12:
        raise RuntimeError("display RMS target was not bracketed")

    # For this symmetric positive quadratic smoother the L2 residual norm is
    # monotone in lambda.  Bisection therefore selects the declared RMS
    # target directly; no claim is made about a globally maximal admissible
    # lambda under the separate componentwise and positivity guards.
    for _ in range(80):
        trial = 0.5 * (low + high)
        nodes = solve(trial)
        trial_rms = float(np.sqrt(np.mean((nodes - y) ** 2)))
        if trial_rms < target_rms:
            low = trial
        else:
            high = trial
    regularisation = 0.5 * (low + high)
    nodes = solve(regularisation)
    residual = nodes - y
    # If the fixed L2 target would violate a componentwise or positivity
    # guard, reduce lambda geometrically from that already-bracketed target.
    # This is a conservative fallback, not a claim of global maximisation.
    while (
        np.max(np.abs(residual)) > MAX_NORMALISED_ABS * tolerance + 1.0e-12
        or np.min(nodes) < -1.0e-12
    ):
        regularisation *= 0.5
        if regularisation <= 1.0e-24:
            raise RuntimeError("display regularisation cannot satisfy componentwise gates")
        nodes = solve(regularisation)
        residual = nodes - y
    if np.sqrt(np.mean(residual**2)) > MAX_NORMALISED_RMS * tolerance + 1.0e-12:
        raise RuntimeError("fixed-RMS display regularisation violates the RMS gate")
    return nodes, regularisation


def extrema_count(values: np.ndarray) -> int:
    """Count strict sign changes of first differences, ignoring roundoff."""

    delta = np.diff(np.asarray(values, dtype=float))
    scale = max(float(np.max(np.abs(values))), 1.0)
    delta[np.abs(delta) <= 1.0e-11 * scale] = 0.0
    signs = np.sign(delta)
    signs = signs[signs != 0.0]
    return int(np.count_nonzero(signs[1:] * signs[:-1] < 0.0))


def smooth_display_curve(
    radius: np.ndarray,
    values: np.ndarray,
    errors: np.ndarray,
    *,
    figure: str,
    galaxy: str,
    series: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a deterministic smooth display curve and source-node residuals."""

    x = np.asarray(radius, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError(f"{figure}/{galaxy}/{series}: invalid one-dimensional inputs")
    if len(x) < 4:
        raise ValueError(f"{figure}/{galaxy}/{series}: smooth display curve needs >=4 nodes")
    if not np.all(np.diff(x) > 0.0):
        raise ValueError(f"{figure}/{galaxy}/{series}: radius nodes are not strictly increasing")
    if not np.all(np.isfinite(y)):
        raise ValueError(f"{figure}/{galaxy}/{series}: non-finite source ordinate")

    tolerance = tolerance_from_errors(errors)
    display_nodes, regularisation = regularised_display_nodes(x, y, tolerance)
    spline = PchipInterpolator(x, display_nodes, extrapolate=False)
    dense_x = np.linspace(float(x[0]), float(x[-1]), max(MIN_DENSE_POINTS, 20 * len(x)))
    dense_y = np.asarray(spline(dense_x), dtype=float)
    source_reconstruction = display_nodes
    residual = source_reconstruction - y
    rms = float(np.sqrt(np.mean(residual**2)))
    max_abs = float(np.max(np.abs(residual)))
    normalised_rms = rms / tolerance
    normalised_max = max_abs / tolerance
    negative_minimum = float(np.min(dense_y))
    exact_hits = int(np.count_nonzero(np.isclose(residual, 0.0, rtol=0.0, atol=1.0e-12)))
    source_extrema = extrema_count(y)
    display_extrema = extrema_count(display_nodes)

    row = {
        "figure": figure,
        "galaxy": galaxy,
        "series": series,
        "nodes": int(len(x)),
        "tolerance_km_s": tolerance,
        "rms_residual_km_s": rms,
        "max_abs_residual_km_s": max_abs,
        "normalised_rms": normalised_rms,
        "normalised_max_abs": normalised_max,
        "regularisation_lambda": regularisation,
        "dense_minimum_km_s": negative_minimum,
        "exact_source_hits": exact_hits,
        "source_extrema": source_extrema,
        "display_node_extrema": display_extrema,
        "new_extrema": max(0, display_extrema - source_extrema),
        "curve_class": "shape-preserving PCHIP through regularised display nodes",
        "status": "PASS",
    }
    failures = []
    if normalised_rms > MAX_NORMALISED_RMS + 1.0e-9:
        failures.append("RMS")
    if normalised_max > MAX_NORMALISED_ABS + 1.0e-9:
        failures.append("MAX_ABS")
    if negative_minimum < -1.0e-8:
        failures.append("NEGATIVE")
    if display_extrema > source_extrema:
        failures.append("NEW_EXTREMA")
    if failures:
        row["status"] = "FAIL:" + ",".join(failures)
    QA_ROWS.append(row)
    if failures:
        raise RuntimeError(f"{figure}/{galaxy}/{series}: display-curve gate failed: {failures}")
    return dense_x, dense_y, display_nodes


def display_curves(
    radius: np.ndarray,
    curves: dict[str, np.ndarray],
    errors: np.ndarray,
    *,
    figure: str,
    galaxy: str,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    rendered = {
        series: smooth_display_curve(
            radius,
            values,
            errors,
            figure=figure,
            galaxy=galaxy,
            series=series,
        )
        for series, values in curves.items()
    }
    names = list(rendered)
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            source_delta = np.asarray(curves[left_name]) - np.asarray(curves[right_name])
            left_x, left_dense, left_nodes = rendered[left_name]
            right_x, right_dense, right_nodes = rendered[right_name]
            if not np.array_equal(left_x, right_x):
                raise RuntimeError(f"{figure}/{galaxy}: dense grids disagree")
            display_node_delta = left_nodes - right_nodes
            stable = np.abs(source_delta) > 1.0e-9
            if np.any(
                stable
                & (np.sign(source_delta) != np.sign(display_node_delta))
            ):
                raise RuntimeError(
                    f"{figure}/{galaxy}/{left_name}/{right_name}: "
                    "regularisation reverses model order at a source radius"
                )
            for interval in range(len(radius) - 1):
                endpoint_delta = source_delta[interval : interval + 2]
                if (
                    np.min(np.abs(endpoint_delta)) <= 1.0e-9
                    or np.sign(endpoint_delta[0]) != np.sign(endpoint_delta[1])
                ):
                    continue
                dense_mask = (left_x >= radius[interval]) & (left_x <= radius[interval + 1])
                dense_delta = left_dense[dense_mask] - right_dense[dense_mask]
                if np.any(np.sign(dense_delta) != np.sign(endpoint_delta[0])):
                    raise RuntimeError(
                        f"{figure}/{galaxy}/{left_name}/{right_name}: "
                        "display interpolation creates an artificial crossing"
                    )
    return {
        series: (payload[0], payload[1])
        for series, payload in rendered.items()
    }


def main_render_page_factory(module: ModuleType):
    def render_page(
        out: Path,
        page_id: str,
        page_title: str,
        sample: list[dict[str, str]],
        rows_by_name: dict[str, list[dict[str, str]]],
        result_by_name: dict[str, dict[str, object]],
    ) -> list[Path]:
        if len(sample) != 2:
            raise ValueError("R154 main pages each carry exactly two frozen galaxies")
        fig, axes = plt.subplots(2, 1, figsize=(7.7, 6.9), constrained_layout=False)
        for ax, item in zip(axes, sample):
            galaxy = item["galaxy"]
            rows = sorted(rows_by_name[galaxy], key=lambda row: int(row["point_index"]))
            radius = np.asarray([float(row["radius_kpc"]) for row in rows])
            observed = np.asarray([float(row["vobs_km_s"]) for row in rows])
            error = np.asarray([float(row["used_error_km_s"]) for row in rows])
            curves = {
                model: np.asarray([float(row[f"v_{model}_km_s"]) for row in rows])
                for model in module.MODELS
            }
            smooth = display_curves(
                radius,
                curves,
                error,
                figure=f"main-{page_id}",
                galaxy=galaxy,
            )

            ax.errorbar(
                radius,
                observed,
                yerr=error,
                fmt="o",
                ms=3.7,
                color=module.COLORS["observed"],
                ecolor=module._palette.GRAPHITE,
                elinewidth=0.85,
                capsize=1.5,
                zorder=7,
            )
            for model in module.MODELS:
                style, width, _marker = module.STYLES[model]
                dense_x, dense_y = smooth[model]
                ax.plot(
                    dense_x,
                    dense_y,
                    color=module.COLORS[model],
                    ls=style,
                    lw=width,
                    zorder=3,
                )
                ax.scatter(
                    radius,
                    curves[model],
                    s=6.0,
                    facecolors="white",
                    edgecolors=module.COLORS[model],
                    linewidths=0.45,
                    alpha=0.42,
                    zorder=4,
                )

            ymax = max(
                float(np.max(observed + error)),
                *(float(np.max(item[1])) for item in smooth.values()),
            )
            ax.set_ylim(0.0, 1.10 * ymax)
            smooth_for_labels = {model: smooth[model][1] for model in module.MODELS}
            label_radius = smooth[module.MODELS[0]][0]
            module.plot_direct_labels(ax, label_radius, smooth_for_labels)
            nfw = result_by_name[galaxy]["nfw_fit"]
            boundary = ", boundary" if nfw["at_parameter_boundary"] else ""
            ax.text(
                0.018,
                0.955,
                rf"NFW: $V_{{200}}={nfw['v200_km_s']:.1f}$ km s$^{{-1}}$, "
                rf"$c_{{200}}={nfw['concentration']:.2f}${boundary}",
                transform=ax.transAxes,
                va="top",
                ha="left",
                fontsize=10.5,
                color=module._palette.GRAPHITE,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.2},
            )
            ax.set_title(
                f"{galaxy} — {module.SHORT_CATEGORY[galaxy]}    "
                rf"($T={item['T']}$; $\Sigma_{{0,d}}={float(item['SB_disk_Lsun_pc2']):.0f}\,"
                rf"L_\odot\,\mathrm{{pc}}^{{-2}}$)"
            )
            ax.set_ylabel(r"circular speed [km s$^{-1}$]")
            ax.grid(True, color=module._palette.GRID, lw=0.55)
            ax.spines[["top", "right"]].set_visible(False)

        axes[-1].set_xlabel("R [kpc]")
        fig.suptitle(page_title, y=0.980, fontsize=13.0, fontweight="semibold")
        fig.text(
            0.5,
            0.948,
            r"Black circles: SPARC.  Smooth traces: residual-gated display curves; "
            r"faint nodes: frozen model ordinates.",
            ha="center",
            va="center",
            fontsize=10.5,
            color=module._palette.INK,
        )
        fig.text(
            0.5,
            0.918,
            r"Fits and diagnostics use the unsmoothed nodes.  HRC-0 $\equiv$ "
            r"MOND-standard at equal scale.",
            ha="center",
            va="center",
            fontsize=10.5,
            color=module._palette.INK,
        )
        fig.text(
            0.5,
            0.896,
            r"Fixed scales: $a_M=1.0824\times10^{-10}$ and "
            r"$a_0=1.2\times10^{-10}\,\mathrm{m\,s^{-2}}$; NFW fitted per galaxy.",
            ha="center",
            va="center",
            fontsize=10.5,
            color=module._palette.INK,
        )
        fig.text(
            0.5,
            0.035,
            r"$\Lambda$CDM-motivated free NFW fit; not a unique $\Lambda$CDM prediction.",
            ha="center",
            va="center",
            fontsize=10.5,
            color=module._palette.INK,
        )
        fig.text(
            0.5,
            0.015,
            r"All panels: $\Upsilon_d=0.5$, $\Upsilon_b=0.7$, signed gas and a "
            r"$2\,\mathrm{km\,s^{-1}}$ error floor.",
            ha="center",
            va="center",
            fontsize=10.5,
            color=module._palette.INK,
        )
        fig.subplots_adjust(left=0.105, right=0.865, bottom=0.12, top=0.838, hspace=0.48)

        base = f"R154_SPARC_SMOOTH_DISPLAY_{page_id}"
        pdf = out / f"{base}.pdf"
        png = out / f"{base}.png"
        grey = out / f"{base}_GRAYSAFE_PREVIEW.png"
        deuteranopia = out / f"{base}_DEUTERANOPIA_PREVIEW.png"
        module.assert_min_font(fig)
        fig.savefig(
            pdf,
            dpi=240,
            metadata={
                "Creator": "ECT R154 display-curve semantics renderer",
                "CreationDate": FIXED_TIME,
                "ModDate": FIXED_TIME,
            },
        )
        fig.savefig(png, dpi=240, metadata={"Software": "ECT R154 renderer"})
        plt.close(fig)
        with Image.open(png) as image:
            image.convert("L").save(grey, format="PNG", compress_level=9, optimize=False)
        module.deuteranopia_preview(png, deuteranopia)
        return [pdf, png, grey, deuteranopia]

    return render_page


def atlas_legend_handles(module: ModuleType) -> list[Line2D]:
    handles = [
        Line2D(
            [],
            [],
            color=module.COLORS["observed"],
            marker="o",
            linestyle="",
            markersize=4.0,
            label="SPARC observations",
        )
    ]
    labels = {
        "baryons": "baryons / weak-field GR",
        "MOND-standard": "MOND-standard",
        "HRC-0": "HRC-0",
        "HRC-3": "HRC-3",
        "NFW-fit": "NFW two-parameter fit",
    }
    for model in module.MODELS:
        style, width, _marker = module.STYLES[model]
        handles.append(
            Line2D(
                [],
                [],
                color=module.COLORS[model],
                linestyle=style,
                linewidth=width,
                label=labels[model],
            )
        )
    return handles


def atlas_plot_galaxy_factory(module: ModuleType):
    def plot_galaxy(
        ax: plt.Axes,
        payload: dict[str, Any],
        spec: dict[str, Any],
        *,
        compact_panel: bool = False,
    ) -> None:
        radius = np.asarray(payload["radius"], dtype=float)
        observed = np.asarray(payload["vobs"], dtype=float)
        error = np.asarray(payload["error"], dtype=float)
        curves = {model: np.asarray(payload[model], dtype=float) for model in module.MODELS}
        smooth = display_curves(
            radius,
            curves,
            error,
            figure=spec["panel_id"],
            galaxy=payload["galaxy"],
        )

        ax.errorbar(
            radius,
            observed,
            yerr=error,
            fmt="o",
            ms=3.5,
            color=module.COLORS["observed"],
            ecolor="#5E5E5E",
            elinewidth=0.75,
            capsize=1.25,
            zorder=8,
        )
        if spec["family"] == "fig18":
            for model in ("HRC-0", "HRC-3"):
                center_nodes = curves[model]
                lower_nodes = np.asarray(payload[f"{model}-min"], dtype=float)
                upper_nodes = np.asarray(payload[f"{model}-max"], dtype=float)
                if np.any(lower_nodes > upper_nodes):
                    raise RuntimeError(f"{spec['panel_id']}/{payload['galaxy']}/{model}: inverted range")
                if np.any(center_nodes < lower_nodes) or np.any(center_nodes > upper_nodes):
                    raise RuntimeError(
                        f"{spec['panel_id']}/{payload['galaxy']}/{model}: "
                        "held-out mean lies outside its pointwise split range"
                    )
                # The five held-out splits own a range at each evaluated
                # radius, not a continuous extremal path.  Render exact
                # per-radius range bars; never join or fill their extrema.
                ax.errorbar(
                    radius,
                    center_nodes,
                    yerr=np.vstack((center_nodes - lower_nodes, upper_nodes - center_nodes)),
                    fmt="none",
                    color=module.COLORS[model],
                    alpha=0.28,
                    elinewidth=0.70,
                    capsize=1.4,
                    capthick=0.70,
                    zorder=1,
                )

        for model in module.MODELS:
            style, width, _marker = module.STYLES[model]
            dense_x, dense_y = smooth[model]
            ax.plot(
                dense_x,
                dense_y,
                color=module.COLORS[model],
                ls=style,
                lw=width,
                zorder=4,
            )
            ax.scatter(
                radius,
                curves[model],
                s=4.2 if compact_panel else 5.6,
                facecolors="white",
                edgecolors=module.COLORS[model],
                linewidths=0.38,
                alpha=0.40,
                zorder=5,
            )

        ymax = max(
            float(np.max(observed + error)),
            *(float(np.max(item[1])) for item in smooth.values()),
        )
        ax.set_ylim(0.0, 1.17 * ymax)
        xmin, xmax = float(np.min(radius)), float(np.max(radius))
        span = max(xmax - xmin, xmax, 1.0)
        endpoints = {
            "observed": float(observed[-1]),
            **{model: float(smooth[model][1][-1]) for model in module.MODELS},
        }
        dense_gallery_page = compact_panel and spec["panel_id"] == "fig19_d"
        if dense_gallery_page:
            # This particular four-panel page contains several nearly
            # coincident terminal values.  Preserve the exact endpoints but
            # give their direct labels a slightly larger deterministic gap.
            # Connector segments retain the endpoint-to-label mapping.
            placed = spread_labels_with_minimum_gap(
                endpoints,
                0.10 * ymax,
                1.08 * ymax,
                0.108 * (1.08 - 0.10) * ymax,
            )
        else:
            placed = module.spread_labels(endpoints, 0.10 * ymax, 1.08 * ymax)
        connector_x = xmax + 0.025 * span
        text_x = xmax + 0.045 * span
        for key in ("observed", *module.MODELS):
            ax.plot(
                [xmax, connector_x],
                [endpoints[key], placed[key]],
                color=module.COLORS[key],
                lw=0.70,
                clip_on=False,
            )
            ax.text(
                text_x,
                placed[key],
                module.DIRECT[key],
                color=module.COLORS[key],
                fontsize=8.6,
                fontweight="semibold",
                va="center",
                ha="left",
                clip_on=False,
            )
        ax.set_xlim(max(0.0, xmin - 0.02 * span), xmax + 0.34 * span)

        if spec["family"] == "fig18":
            protocol_note = "HRC: held-out mean over five whole-galaxy train-to-test transfers"
        elif spec["family"] == "fig19":
            if compact_panel:
                protocol_note = (
                    f"aM0/match={payload['hrc0_scale_si']/module.A_MATCH:.2f}; "
                    f"aM3/match={payload['hrc3_scale_si']/module.A_MATCH:.2f}"
                )
            else:
                protocol_note = (
                    "HRC per-galaxy fixed-M/L scales: "
                    f"aM0/aMmatch={payload['hrc0_scale_si']/module.A_MATCH:.2f}, "
                    f"aM3/aMmatch={payload['hrc3_scale_si']/module.A_MATCH:.2f}"
                )
        else:
            protocol_note = "Post-hoc residual-stress selection; HRC traces are held-out five-split means"
        ax.text(
            0.012,
            0.975,
            protocol_note,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8.6,
            color="#222222",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 1.0},
        )
        domain = payload["lcdm_domain"]
        domain_in = domain["HMF_mean_domain"] == "IN"
        domain_note = domain["panel_note"]
        if dense_gallery_page:
            # Keep the status wording verbatim while preventing the long box
            # from running through the direct-label lane on the right.
            domain_note = domain_note.replace(": ", ":\n", 1)
        ax.text(
            0.012,
            0.865,
            domain_note,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8.6,
            color="#222222",
            linespacing=1.10,
            bbox={
                "facecolor": "#F2F6F3" if domain_in else "#FFF4DD",
                "edgecolor": "#397A54" if domain_in else "#8A5D00",
                "linewidth": 0.75,
                "alpha": 0.94,
                "pad": 1.4,
            },
            zorder=20,
        )
        nfw = payload["nfw"]
        boundary = "; boundary" if nfw["at_parameter_boundary"] else ""
        if compact_panel:
            if dense_gallery_page:
                nfw_note = (
                    f"NFW 2p: V200={nfw['v200_km_s']:.1f} km/s,\n"
                    f"c200={nfw['concentration']:.2f}{boundary}"
                )
            else:
                nfw_note = (
                    f"NFW 2p: V200={nfw['v200_km_s']:.1f} km/s, "
                    f"c200={nfw['concentration']:.2f}{boundary}"
                )
        else:
            nfw_note = (
                f"{module.NFW_LABEL}\n"
                f"V200={nfw['v200_km_s']:.1f} km/s, c200={nfw['concentration']:.2f}{boundary}"
            )
        ax.text(
            0.988,
            0.025,
            nfw_note,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8.6,
            color=module.COLORS["NFW-fit"],
            bbox={"facecolor": "white", "edgecolor": "#D8D8D8", "alpha": 0.88, "pad": 1.4},
        )
        ax.set_title(
            f"{payload['galaxy']} — HMF mean-domain: {domain['HMF_mean_domain']}",
            fontsize=9.4,
            fontweight="semibold",
        )
        ax.set_xlabel("R [kpc]", fontsize=9.0)
        ax.set_ylabel("V [km s^-1]", fontsize=9.0)
        ax.tick_params(labelsize=8.6)
        ax.grid(True, color="#D8D8D8", lw=0.45, alpha=0.62)
        ax.spines[["top", "right"]].set_visible(False)

    return plot_galaxy


def run_module(module: ModuleType, argv: list[str]) -> None:
    previous = sys.argv[:]
    try:
        sys.argv = argv
        module.main()
    finally:
        sys.argv = previous


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--scratch-dir", type=Path, required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    scratch_dir = args.scratch_dir.resolve()
    main_output = output_root / "assets/main"
    atlas_output = output_root / "assets/atlas"
    main_output.mkdir(parents=True, exist_ok=True)
    atlas_output.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    main_module = load_module("r154_main_owner", MAIN_SOURCE)
    main_module.render_page = main_render_page_factory(main_module)
    run_module(
        main_module,
        [
            str(MAIN_SOURCE),
            "--output-dir",
            str(main_output),
        ],
    )

    atlas_module = load_module("r154_atlas_owner", ATLAS_SOURCE)
    atlas_module.plot_galaxy = atlas_plot_galaxy_factory(atlas_module)
    atlas_module.legend_handles = lambda: atlas_legend_handles(atlas_module)
    run_module(
        atlas_module,
        [
            str(ATLAS_SOURCE),
            "--output-root",
            str(atlas_output),
            "--scratch-dir",
            str(scratch_dir / "atlas"),
        ],
    )

    caption_path = atlas_output / "R127_ROTATION_FULL_ATLAS_CAPTION_PROPOSAL_v1.tex"
    caption = caption_path.read_text(encoding="utf-8")
    old_caption_tail = (
        "The thin HRC envelopes on the held-out panels, where present,\n"
        "are frozen train-to-test transfer ranges and are not $\\Lambda$CDM prior bands.\n"
        "All comparator curves remain Level-C diagnostics; no model-selection or\n"
        "ECT-discrimination claim is made."
    )
    new_caption_tail = (
        "On held-out panels, vertical whiskers show the pointwise minimum-to-maximum\n"
        "range across five train-to-test splits at each evaluated radius; they are\n"
        "neither a continuous envelope nor a confidence or credibility band.\n"
        "Observations are unconnected error-bar markers.  Each coloured trace is a\n"
        "deterministic residual-gated, shape-preserving display approximation to the\n"
        "frozen model ordinates shown as faint unconnected nodes.  It is not a\n"
        "separately derived continuous physical solution, and all fits, residuals,\n"
        "likelihoods and quoted statistics use only the frozen ordinates.  All\n"
        "comparators remain Level-C diagnostics; no model-selection or\n"
        "ECT-discrimination claim is made."
    )
    if caption.count(old_caption_tail) != 1:
        raise RuntimeError("atlas caption owner phrase is not unique")
    caption_path.write_text(
        caption.replace(old_caption_tail, new_caption_tail),
        encoding="utf-8",
    )

    report_path = atlas_output / "R127_ROTATION_FULL_ATLAS_REPORT_v1.md"
    report = report_path.read_text(encoding="utf-8")
    replacements = {
        "Twelve exact-name vector PDFs now cover": (
            "Twelve exact-name vector PDFs now cover"
        ),
        "fig18 uses the exact R97 held-out mean over five whole-galaxy train-to-test transfers; the thin   boundaries show the frozen five-split envelope.": (
            "fig18 uses the frozen R97 held-out mean over five whole-galaxy "
            "train-to-test transfers; vertical per-radius whiskers show the "
            "pointwise five-split range and do not define a continuous envelope."
        ),
        "fig20 uses the exact held-out five-split mean traces, but the galaxies were selected post hoc from   the residual statistic; it is an explanatory stress diagnostic, not held-out model selection.": (
            "fig20 uses residual-gated display approximations to the frozen held-out "
            "five-split mean ordinates, but the galaxies were selected post hoc from "
            "the residual statistic; it is an explanatory stress diagnostic, not "
            "held-out model selection."
        ),
    }
    for old, new in replacements.items():
        if report.count(old) != 1:
            raise RuntimeError(f"atlas report phrase is not unique: {old}")
        report = report.replace(old, new)
    report += (
        "\n## R154 display-curve semantics supersession\n\n"
        "Observations remain unconnected error-bar markers.  Frozen model ordinates "
        "remain visible as faint unconnected nodes.  Coloured traces are deterministic "
        "residual-gated, shape-preserving display approximations only; no continuous "
        "physical owner or inter-node prediction is asserted.  The displayed-node RMS "
        "target is one per cent of the median observational error whenever the declared "
        "tolerance is unclamped.  All fits, residuals, likelihoods and quoted statistics "
        "continue to use the frozen unsmoothed ordinates.  Held-out ranges are shown as "
        "independent per-radius whiskers rather than a filled or joined envelope.\n"
    )
    report_path.write_text(report, encoding="utf-8")

    failed = [row for row in QA_ROWS if row["status"] != "PASS"]
    payload = {
        "version": R154_VERSION,
        "status": "PASS" if not failed else "FAIL",
        "scope": "15 active SPARC pages: 3 main/companion pages and 12 full-atlas pages",
        "scientific_values_changed": False,
        "fit_or_likelihood_recomputed": False,
        "display_method": {
            "kind": (
                "fixed-sub-error-RMS quadratic curvature regularisation of displayed "
                "nodes, followed by a shape-preserving PCHIP curve"
            ),
            "selection": (
                f"lambda selected by monotone L2 bisection for target RMS "
                f"{TARGET_NORMALISED_RMS:.2f} times the declared display tolerance; "
                "lambda is halved conservatively if the componentwise or positivity "
                "gate would fail; topology is a separate fail-closed gate"
            ),
            "tolerance_km_s": (
                f"clamp({ERROR_FRACTION:.2f} * median displayed observational error, "
                f"{MIN_TOL_KM_S:.2f}, {MAX_TOL_KM_S:.2f})"
            ),
            "source_nodes": "retained as faint unconnected open markers",
            "observations": "retained as unconnected error-bar markers",
            "held_out_ranges": (
                "unconnected per-radius range bars; no continuous extremal envelope"
            ),
            "use_in_scientific_metrics": False,
        },
        "gates": {
            "max_normalised_rms": MAX_NORMALISED_RMS,
            "target_normalised_rms": TARGET_NORMALISED_RMS,
            "max_normalised_abs": MAX_NORMALISED_ABS,
            "no_negative_dense_velocity": True,
            "no_new_extrema": True,
            "no_source_node_model_order_reversal": True,
            "no_artificial_pairwise_crossing": True,
            "held_out_mean_inside_pointwise_range": True,
            "positive_regularisation": True,
            "rows": len(QA_ROWS),
            "failed_rows": len(failed),
        },
        "owner_hashes": {
            "main_source": sha256(MAIN_SOURCE),
            "atlas_source": sha256(ATLAS_SOURCE),
            "this_renderer": sha256(Path(__file__)),
        },
        "rows": QA_ROWS,
        "outputs": {
            str(path.relative_to(output_root)): sha256(path)
            for path in sorted(output_root.rglob("*.pdf"))
        },
    }
    (output_root / "qa").mkdir(parents=True, exist_ok=True)
    (output_root / "qa/R154_SMOOTH_CURVE_SEMANTICS_QA_v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if failed:
        raise RuntimeError(f"R154 QA has {len(failed)} failed rows")


if __name__ == "__main__":
    main()
