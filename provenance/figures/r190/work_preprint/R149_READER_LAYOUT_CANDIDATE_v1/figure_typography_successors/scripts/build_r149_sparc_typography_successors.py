#!/usr/bin/env python3
"""Render R149 print-typography successors from frozen R102 point curves.

The generator performs no fit and changes no scientific number.  Every plotted
ordinate is read from the independently verified R102 point-curve table.  The
only changes relative to the R102 research render are publication layout,
direct labels, sparse marker redundancy and a luminance-separated calm palette.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "LaTex/ECT_preprint.tex").is_file())
R123_ROTATION = ROOT / "LaTex/work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1/components/rotation_comparison"
FROZEN = R123_ROTATION / "frozen_r102"
PALETTE_SOURCE = ROOT / "LaTex/work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1/scripts/r123_palette.py"

POINTS = FROZEN / "R102_SPARC_MODEL_POINT_CURVES_v1.csv"
SAMPLE = FROZEN / "R102_SPARC_SAMPLE_REGISTRY_v1.csv"
RESULTS = FROZEN / "R102_SPARC_MODEL_RESULTS_v1.json"

STEM = "R149_SPARC_EXTERNAL_MODEL_COMPARISON_TYPOGRAPHY_v1"

INPUT_HASHES = {
    "point_curves": "d1071900bdded8c17c9d857b5ea207a415f37d4c01a7f15d5ea643559f320a56",
    "sample_registry": "0b90133caba285fb78453b7d4112afb0a0b1c5b66d10e52ad453effc2782624e",
    "results": "9037ffbfe36ed0b4d074e8851d7356c57f53748ad301ea239850e36ca9c5eed9",
    "palette": "5ac5336db41e8b444d048019983e2be0db16a59f6793aa0d32762ede8dbc4bdd",
}
MIN_FONT_PT = 10.5

_palette_spec = importlib.util.spec_from_file_location("r123_palette", PALETTE_SOURCE)
if _palette_spec is None or _palette_spec.loader is None:
    raise RuntimeError(f"Cannot import the canonical R123 palette: {PALETTE_SOURCE}")
_palette = importlib.util.module_from_spec(_palette_spec)
_palette_spec.loader.exec_module(_palette)

# The colour roles are imported from the one canonical R123 policy source.
# Gray-safe interpretation does not rely on colour alone: every model also has
# a distinct line style, sparse marker and direct label.  Dense hatch is absent.
COLORS = {
    "observed": _palette.DATA,
    "baryons": _palette.BARYON,
    "MOND-standard": _palette.MOND,
    "HRC-0": _palette.HRC0,
    "HRC-3": _palette.HRC3,
    "NFW-fit": _palette.NFW,
}
STYLES = {
    "baryons": (":", 1.8, "v"),
    "MOND-standard": ("-.", 1.9, "^"),
    "HRC-0": ("--", 2.0, "s"),
    "HRC-3": ("-", 2.15, "D"),
    "NFW-fit": ((0, (5, 1, 1, 1)), 1.95, "P"),
}
DIRECT = {
    "baryons": r"baryons $\simeq$ GR",
    "MOND-standard": "MOND",
    "HRC-0": "HRC-0",
    "HRC-3": "HRC-3",
    "NFW-fit": "NFW",
}
MODELS = tuple(STYLES)
SHORT_CATEGORY = {
    "DDO154": "gas-rich diffuse dwarf",
    "IC2574": "extended diffuse dwarf",
    "F568-3": "low-surface-brightness disk",
    "NGC3198": "extended benchmark disk",
    "NGC2903": "high-surface-brightness spiral",
    "NGC7814": "bulge-dominated disk",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def encoded_luma(hex_color: str) -> float:
    rgb = [int(hex_color[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frozen_inputs() -> None:
    actual = {
        "point_curves": sha256(POINTS),
        "sample_registry": sha256(SAMPLE),
        "results": sha256(RESULTS),
        "palette": sha256(PALETTE_SOURCE),
    }
    wrong = [f"{key}: expected {INPUT_HASHES[key]}, got {actual[key]}" for key in actual if actual[key] != INPUT_HASHES[key]]
    if wrong:
        raise RuntimeError("Frozen input guard failed:\n" + "\n".join(wrong))


def assert_min_font(fig: plt.Figure) -> None:
    too_small = []
    for text in fig.findobj(match=lambda obj: hasattr(obj, "get_fontsize")):
        if text.get_text() and float(text.get_fontsize()) < MIN_FONT_PT - 1.0e-9:
            too_small.append((text.get_text()[:72], float(text.get_fontsize())))
    if too_small:
        raise RuntimeError(f"Text below {MIN_FONT_PT} pt: {too_small[:8]}")


def deuteranopia_preview(source: Path, target: Path) -> None:
    """Write a deterministic diagnostic deuteranopia simulation in sRGB."""

    matrix = np.asarray([
        [0.367, 0.861, -0.228],
        [0.280, 0.673, 0.047],
        [-0.012, 0.043, 0.969],
    ])
    with Image.open(source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    simulated = np.clip(rgb @ matrix.T, 0.0, 1.0)
    encoded = np.rint(simulated * 255.0).astype(np.uint8)
    Image.fromarray(encoded, mode="RGB").save(
        target, format="PNG", compress_level=9, optimize=False
    )


def spread_labels(values: dict[str, float], lower: float, upper: float) -> dict[str, float]:
    """Deterministically separate endpoint labels while retaining vertical order."""

    span = max(upper - lower, 1.0)
    gap = 0.050 * span
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


def plot_direct_labels(ax: plt.Axes, radius: np.ndarray, curves: dict[str, np.ndarray]) -> None:
    xmax = float(np.max(radius))
    ymin, ymax = ax.get_ylim()
    endpoint = {model: float(curves[model][-1]) for model in MODELS}
    placed = spread_labels(endpoint, ymin + 0.05 * (ymax - ymin), ymax - 0.05 * (ymax - ymin))
    connector_x = xmax * 1.025
    text_x = xmax * 1.052
    for model in MODELS:
        ax.plot(
            [xmax, connector_x],
            [endpoint[model], placed[model]],
            color=COLORS[model],
            lw=0.8,
            clip_on=False,
        )
        ax.text(
            text_x,
            placed[model],
            DIRECT[model],
            color=COLORS[model],
            fontsize=10.5,
            fontweight="semibold",
            va="center",
            ha="left",
            clip_on=False,
        )
    ax.set_xlim(0.0, xmax * 1.205)


def render_page(
    out: Path,
    page_id: str,
    page_title: str,
    sample: list[dict[str, str]],
    rows_by_name: dict[str, list[dict[str, str]]],
    result_by_name: dict[str, dict[str, object]],
) -> list[Path]:
    """Render two A4-width panels with type safely above the print floor."""

    if len(sample) != 2:
        raise ValueError("R149 successor pages each carry exactly two frozen galaxies")
    # Live A4 text width is ~6.30 in.  A 7.7-in canvas retains the 10.5-pt
    # public text floor above 8 pt after a width=\textwidth insertion.
    fig, axes = plt.subplots(2, 1, figsize=(7.7, 6.9), constrained_layout=False)
    for ax, item in zip(axes, sample):
        galaxy = item["galaxy"]
        rows = sorted(rows_by_name[galaxy], key=lambda row: int(row["point_index"]))
        radius = np.asarray([float(row["radius_kpc"]) for row in rows])
        observed = np.asarray([float(row["vobs_km_s"]) for row in rows])
        error = np.asarray([float(row["used_error_km_s"]) for row in rows])
        curves = {
            model: np.asarray([float(row[f"v_{model}_km_s"]) for row in rows])
            for model in MODELS
        }

        ax.errorbar(
            radius,
            observed,
            yerr=error,
            fmt="o",
            ms=3.7,
            color=COLORS["observed"],
            ecolor=_palette.GRAPHITE,
            elinewidth=0.85,
            capsize=1.5,
            zorder=7,
        )
        marker_every = max(2, int(math.ceil(len(radius) / 6.0)))
        for model in MODELS:
            style, width, marker = STYLES[model]
            ax.plot(
                radius,
                curves[model],
                color=COLORS[model],
                ls=style,
                lw=width,
                marker=marker,
                markevery=marker_every,
                ms=3.6,
                mfc="white",
                mec=COLORS[model],
                mew=0.8,
                zorder=3,
            )

        ymax = max(float(np.max(observed + error)), *(float(np.max(curve)) for curve in curves.values()))
        ax.set_ylim(0.0, 1.10 * ymax)
        plot_direct_labels(ax, radius, curves)
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
            color=_palette.GRAPHITE,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.2},
        )
        ax.set_title(
            f"{galaxy} — {SHORT_CATEGORY[galaxy]}    "
            rf"($T={item['T']}$; $\Sigma_{{0,d}}={float(item['SB_disk_Lsun_pc2']):.0f}\,L_\odot\,\mathrm{{pc}}^{{-2}}$)"
        )
        ax.set_ylabel(r"circular speed [km s$^{-1}$]")
        ax.grid(True, color=_palette.GRID, lw=0.55)
        ax.spines[["top", "right"]].set_visible(False)

    axes[-1].set_xlabel("R [kpc]")
    # Keep the title safely inside the PDF media box; 0.993 clipped its ascenders
    # in a full-page raster check even though the curve panels themselves fit.
    fig.suptitle(page_title, y=0.980, fontsize=13.0, fontweight="semibold")
    fig.text(
        0.5,
        0.948,
        r"Black circles: SPARC; curves are directly labelled.  HRC-0 $\equiv$ MOND-standard at equal scale.",
        ha="center",
        va="center",
        fontsize=10.5,
        color=_palette.INK,
    )
    fig.text(
        0.5,
        0.918,
        r"Plotted fixed scales: $a_M=1.0824\times10^{-10}$ and "
        r"$a_0=1.2\times10^{-10}\,\mathrm{m\,s^{-2}}$;",
        ha="center",
        va="center",
        fontsize=10.5,
        color=_palette.INK,
    )
    fig.text(
        0.5,
        0.896,
        "NFW parameters are fitted per galaxy.",
        ha="center",
        va="center",
        fontsize=10.5,
        color=_palette.INK,
    )
    fig.text(
        0.5,
        0.035,
        r"$\Lambda$CDM-motivated free NFW fit; not a unique $\Lambda$CDM prediction.",
        ha="center",
        va="center",
        fontsize=10.5,
        color=_palette.INK,
    )
    fig.text(
        0.5,
        0.015,
        r"All panels: $\Upsilon_d=0.5$, $\Upsilon_b=0.7$, signed gas and a "
        r"$2\,\mathrm{km\,s^{-1}}$ error floor.",
        ha="center",
        va="center",
        fontsize=10.5,
        color=_palette.INK,
    )
    fig.subplots_adjust(left=0.105, right=0.865, bottom=0.12, top=0.838, hspace=0.48)

    fixed_time = datetime(2026, 7, 21, 0, 0, 0, tzinfo=timezone.utc)
    base = f"{STEM}_{page_id}"
    pdf = out / f"{base}.pdf"
    png = out / f"{base}.png"
    grey = out / f"{base}_GRAYSAFE_PREVIEW.png"
    deuteranopia = out / f"{base}_DEUTERANOPIA_PREVIEW.png"
    assert_min_font(fig)
    fig.savefig(
        pdf,
        dpi=240,
        metadata={
            "Creator": "ECT R149 frozen R102 typography-successor renderer",
            "CreationDate": fixed_time,
            "ModDate": fixed_time,
        },
    )
    fig.savefig(
        png,
        dpi=240,
        metadata={"Software": "ECT R149 frozen R102 typography-successor renderer"},
    )
    plt.close(fig)
    with Image.open(png) as image:
        image.convert("L").save(grey, format="PNG", compress_level=9, optimize=False)
    deuteranopia_preview(png, deuteranopia)
    return [pdf, png, grey, deuteranopia]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=HERE.parent / "outputs")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    verify_frozen_inputs()
    sample = sorted(read_csv(SAMPLE), key=lambda row: int(row["sample_order"]))
    points = read_csv(POINTS)
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    result_by_name = {row["galaxy"]: row for row in result["galaxies"]}
    rows_by_name = {
        item["galaxy"]: [row for row in points if row["galaxy"] == item["galaxy"]]
        for item in sample
    }

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11.5,
        "axes.titlesize": 11.5,
        "axes.labelsize": 11.0,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    outputs: list[Path] = []
    outputs.extend(render_page(
        out,
        "A",
        "SPARC comparison I: diffuse systems",
        sample[:2],
        rows_by_name,
        result_by_name,
    ))
    outputs.extend(render_page(
        out,
        "B",
        "SPARC comparison II: low-surface-brightness and benchmark disks",
        sample[2:4],
        rows_by_name,
        result_by_name,
    ))
    outputs.extend(render_page(
        out,
        "C",
        "SPARC comparison III: bright and bulge-dominated disks",
        sample[4:6],
        rows_by_name,
        result_by_name,
    ))

    render_sidecar = {
        "status": "LEVEL_C_EXTERNAL_MODEL_COMPARISON_RENDER",
        "scientific_numbers_changed_from_r102": False,
        "layout": "three sequential A4-width figures with two panels each; minimum public font 10.5 pt before TeX insertion",
        "font_gate": {
            "minimum_public_font_pt": MIN_FONT_PT,
            "smaller_pdf_Tf_values_are_math_subscripts_or_superscripts": True,
        },
        "page_galaxies": {
            "A": [item["galaxy"] for item in sample[:2]],
            "B": [item["galaxy"] for item in sample[2:4]],
            "C": [item["galaxy"] for item in sample[4:6]],
        },
        "inputs": {
            "point_curves": f"frozen_r102/{POINTS.name}",
            "sample_registry": f"frozen_r102/{SAMPLE.name}",
            "results": f"frozen_r102/{RESULTS.name}",
        },
        "series_columns": {model: f"v_{model}_km_s" for model in MODELS},
        "observations": ["vobs_km_s", "used_error_km_s"],
        "palette": {
            key: {"hex": value, "encoded_rec709_luma": encoded_luma(value)}
            for key, value in COLORS.items()
        },
        "palette_source": {
            "path_from_component": "../../scripts/r123_palette.py",
            "sha256": sha256(PALETTE_SOURCE),
            "policy": "R123_LUMINANCE_FIRST_VISUAL_POLICY_v1.md",
        },
        "redundant_channels": ["luminance", "line_style", "marker", "direct_label"],
        "hatch_used": False,
        "outputs": [path.name for path in outputs],
    }
    (out / "R149_SPARC_TYPOGRAPHY_RENDER_SIDECAR_v1.json").write_text(
        json.dumps(render_sidecar, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
