#!/usr/bin/env python3
"""Build the R149 reader-facing coherence-retention regime figure.

This is an isolated proposal owner.  It does not write to LaTex/figures or to
any live manuscript.  The only physical input is the declared pure-dephasing
closure

    V_ab / V_0 = exp(-Phi_ab).

The regime band edges are plotting guides, not physical thresholds.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784894400")
RUNTIME_ROOT = Path(__file__).resolve().parent / ".runtime"
RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(RUNTIME_ROOT / "cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image


SCRIPT_VERSION = "R149 coherence-regime owner v1"
FIXED_TIME = dt.datetime(2026, 7, 24, 12, 0, 0, tzinfo=dt.timezone.utc)
X_MIN = 1.0e-3
X_LEFT_GUIDE = 1.0e-1
X_RIGHT_GUIDE = 3.0
X_MAX = 3.0e1

COLORS = {
    "curve": "#0072B2",
    "coherent_fill": "#EDF6FC",
    "coherent_edge": "#0072B2",
    "crossover_fill": "#BFDCCB",
    "crossover_edge": "#007A5E",
    "dephased_fill": "#D39A89",
    "dephased_edge": "#A64022",
    "external": "#222222",
    "toy": "#D55E00",
    "neutral": "#666666",
    "grid": "#D7D7D7",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_preview_variants(source_png: Path, preview_dir: Path) -> dict[str, str]:
    preview_dir.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(Image.open(source_png).convert("RGB"), dtype=np.float64) / 255.0

    transforms = {
        "protanopia": np.array(
            [
                [0.56667, 0.43333, 0.00000],
                [0.55833, 0.44167, 0.00000],
                [0.00000, 0.24167, 0.75833],
            ]
        ),
        "deuteranopia": np.array(
            [
                [0.62500, 0.37500, 0.00000],
                [0.70000, 0.30000, 0.00000],
                [0.00000, 0.30000, 0.70000],
            ]
        ),
        "tritanopia": np.array(
            [
                [0.95000, 0.05000, 0.00000],
                [0.00000, 0.43333, 0.56667],
                [0.00000, 0.47500, 0.52500],
            ]
        ),
    }

    output_paths: dict[str, Path] = {}
    original_path = preview_dir / "fig_coherence_regimes_r149__original.png"
    Image.fromarray(np.uint8(np.clip(rgb, 0.0, 1.0) * 255.0)).save(
        original_path, optimize=False, compress_level=9
    )
    output_paths["original"] = original_path

    # Rec. 709 luminance.  The three regime fills intentionally retain
    # distinct luminance values, while literal labels preserve the semantics.
    gray = rgb @ np.array([0.2126, 0.7152, 0.0722])
    gray_rgb = np.repeat(gray[..., None], 3, axis=2)
    gray_path = preview_dir / "fig_coherence_regimes_r149__grayscale.png"
    Image.fromarray(np.uint8(np.clip(gray_rgb, 0.0, 1.0) * 255.0)).save(
        gray_path, optimize=False, compress_level=9
    )
    output_paths["grayscale"] = gray_path

    for name, matrix in transforms.items():
        converted = np.clip(rgb @ matrix.T, 0.0, 1.0)
        target = preview_dir / f"fig_coherence_regimes_r149__{name}.png"
        Image.fromarray(np.uint8(converted * 255.0)).save(
            target, optimize=False, compress_level=9
        )
        output_paths[name] = target

    return {name: sha256(path) for name, path in output_paths.items()}


def build(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    preview_dir = outdir / "previews"

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 9.6,
            "axes.labelsize": 10.4,
            "axes.titlesize": 10.8,
            "xtick.labelsize": 8.7,
            "ytick.labelsize": 8.7,
            "legend.fontsize": 7.7,
            "mathtext.fontset": "dejavuserif",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
        }
    )

    # 6.25 in is the 160 mm text width of the A4 manuscript with 25 mm margins.
    fig = plt.figure(figsize=(6.25, 4.45), constrained_layout=False)
    grid = fig.add_gridspec(
        nrows=2,
        ncols=1,
        height_ratios=(0.78, 3.95),
        hspace=0.055,
        left=0.105,
        right=0.985,
        bottom=0.205,
        top=0.905,
    )
    regime_ax = fig.add_subplot(grid[0])
    ax = fig.add_subplot(grid[1], sharex=regime_ax)

    for axis in (regime_ax, ax):
        axis.set_xscale("log")
        axis.set_xlim(X_MIN, X_MAX)

    regimes = [
        (
            X_MIN,
            X_LEFT_GUIDE,
            COLORS["coherent_fill"],
            COLORS["coherent_edge"],
            "-",
            r"$\Phi_{ab}\ll 1$",
            "coherent /\nhigh visibility",
        ),
        (
            X_LEFT_GUIDE,
            X_RIGHT_GUIDE,
            COLORS["crossover_fill"],
            COLORS["crossover_edge"],
            "--",
            r"$\Phi_{ab}\sim 1$",
            "continuous\ncrossover",
        ),
        (
            X_RIGHT_GUIDE,
            X_MAX,
            COLORS["dephased_fill"],
            COLORS["dephased_edge"],
            "-.",
            r"$\Phi_{ab}\gg 1$",
            "strongly dephased /\nlow visibility",
        ),
    ]

    for left, right, fill, edge, style, phi_label, regime_label in regimes:
        regime_ax.axvspan(
            left,
            right,
            ymin=0.02,
            ymax=0.68,
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.25,
            linestyle=style,
            zorder=1,
        )
        center = np.sqrt(left * right)
        regime_ax.text(
            center,
            0.51,
            phi_label,
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color="#111111",
            zorder=3,
        )
        regime_ax.text(
            center,
            0.20,
            regime_label,
            ha="center",
            va="center",
            fontsize=7.2,
            color="#111111",
            zorder=3,
        )

    regime_ax.annotate(
        "increasing accumulated pairwise dephasing",
        xy=(2.0e1, 0.94),
        xytext=(2.0e-3, 0.94),
        arrowprops={"arrowstyle": "-|>", "color": "#222222", "lw": 0.9},
        ha="left",
        va="center",
        fontsize=7.7,
        annotation_clip=False,
    )
    regime_ax.set_ylim(0.0, 1.12)
    regime_ax.set_yticks([])
    regime_ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    for spine in regime_ax.spines.values():
        spine.set_visible(False)

    phi = np.logspace(np.log10(X_MIN), np.log10(X_MAX), 1000)
    retention = np.exp(-phi)
    ax.plot(
        phi,
        retention,
        color=COLORS["curve"],
        linewidth=2.5,
        solid_capstyle="round",
        zorder=5,
        label=r"declared pure-dephasing closure $V_{ab}/V_0=e^{-\Phi_{ab}}$",
    )

    # Plotting-guide band edges: they communicate the asymptotic reading only.
    ax.axvline(
        X_LEFT_GUIDE,
        color=COLORS["coherent_edge"],
        linewidth=0.9,
        linestyle=":",
        alpha=0.9,
        zorder=2,
    )
    ax.axvline(
        X_RIGHT_GUIDE,
        color=COLORS["dephased_edge"],
        linewidth=0.9,
        linestyle="-.",
        alpha=0.9,
        zorder=2,
    )

    # Preserve the two imported source-model visibility proxies shown in the
    # earlier figure.  They are not ECT predictions.
    imported = [
        (0.006, "s", "P"),
        (0.062, "D", "J"),
    ]
    for x_value, marker, short_label in imported:
        y_value = float(np.exp(-x_value))
        ax.plot(
            x_value,
            y_value,
            marker=marker,
            markersize=6.2,
            markerfacecolor="white",
            markeredgecolor=COLORS["external"],
            markeredgewidth=1.1,
            linestyle="none",
            zorder=7,
        )
        ax.annotate(
            short_label,
            xy=(x_value, y_value),
            xytext=(0, -13),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=7.1,
            color=COLORS["external"],
        )

    # Preserve the two model/toy markers while making their status explicit.
    chsh_marker = float(np.log(np.sqrt(2.0)))
    ax.axvline(
        chsh_marker,
        color=COLORS["toy"],
        linestyle=(0, (5, 3)),
        linewidth=1.15,
        zorder=3,
    )
    ax.axvline(
        1.0,
        color=COLORS["neutral"],
        linestyle=(0, (1.2, 2.0)),
        linewidth=1.2,
        zorder=3,
    )

    ax.text(
        1.8e-3,
        0.835,
        r"$V/V_0\simeq 1-\Phi_{ab}$",
        color="#222222",
        fontsize=8.3,
        ha="left",
        va="center",
    )
    ax.text(
        1.6e1,
        0.085,
        r"$V/V_0\rightarrow 0$",
        color="#222222",
        fontsize=8.3,
        ha="right",
        va="center",
    )

    ax.set_xlabel(r"pairwise dephasing exponent $\Phi_{ab}$")
    ax.set_ylabel(r"coherence retention $V_{ab}/V_0$")
    ax.set_ylim(0.0, 1.04)
    ax.set_yticks(np.linspace(0.0, 1.0, 6))
    ax.grid(True, which="major", color=COLORS["grid"], linewidth=0.65)
    ax.grid(True, which="minor", axis="x", color="#E8E8E8", linewidth=0.42)
    ax.set_axisbelow(True)

    imported_handle = Line2D(
        [],
        [],
        color=COLORS["external"],
        marker="s",
        markerfacecolor="white",
        markeredgewidth=1.0,
        linestyle="none",
        markersize=5.2,
        label="P, J: imported source-model visibility proxies",
    )
    chsh_handle = Line2D(
        [],
        [],
        color=COLORS["toy"],
        linestyle=(0, (5, 3)),
        linewidth=1.15,
        label="CHSH toy marker",
    )
    order_handle = Line2D(
        [],
        [],
        color=COLORS["neutral"],
        linestyle=(0, (1.2, 2.0)),
        linewidth=1.2,
        label="order-unity model marker",
    )
    handles, labels = ax.get_legend_handles_labels()
    handles.extend([imported_handle, chsh_handle, order_handle])
    labels.extend(
        [
            imported_handle.get_label(),
            chsh_handle.get_label(),
            order_handle.get_label(),
        ]
    )
    legend = ax.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.19),
        ncol=2,
        frameon=False,
        handlelength=2.8,
        columnspacing=1.15,
        handletextpad=0.55,
        borderaxespad=0.0,
    )
    for text in legend.get_texts():
        text.set_color("#222222")

    fig.suptitle(
        "Protocol-dependent coherence-retention regimes",
        x=0.105,
        y=0.992,
        ha="left",
        va="top",
        fontsize=10.7,
        fontweight="bold",
    )

    pdf_path = outdir / "fig_coherence_regimes_r149.pdf"
    png_path = outdir / "fig_coherence_regimes_r149.png"
    pdf_metadata = {
        "Title": "Protocol-dependent coherence-retention regimes",
        "Author": "ECT R149 reproducibility pipeline",
        "Subject": "Pure-dephasing model visual guide; not a universal boundary",
        "Keywords": "ECT R149 coherence dephasing visibility protocol guard",
        "Creator": SCRIPT_VERSION,
        "Producer": "Matplotlib",
        "CreationDate": FIXED_TIME,
        "ModDate": FIXED_TIME,
    }
    fig.savefig(pdf_path, metadata=pdf_metadata)
    fig.savefig(
        png_path,
        dpi=240,
        metadata={
            "Software": SCRIPT_VERSION,
            "Description": "Pure-dephasing regime guide; plotting edges are not physical thresholds.",
        },
    )
    plt.close(fig)

    preview_hashes = save_preview_variants(png_path, preview_dir)
    runtime = {
        "script_version": SCRIPT_VERSION,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "pillow": Image.__version__,
        "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        "fixed_time_utc": FIXED_TIME.isoformat(),
        "figure_size_inches": [6.25, 4.45],
        "plotting_guides": {
            "left": X_LEFT_GUIDE,
            "right": X_RIGHT_GUIDE,
            "status": "illustrative asymptotic guides; not physical thresholds",
        },
        "scientific_input": "V_ab/V_0 = exp(-Phi_ab)",
        "outputs": {
            "fig_coherence_regimes_r149.pdf": sha256(pdf_path),
            "fig_coherence_regimes_r149.png": sha256(png_path),
            "previews": preview_hashes,
        },
    }
    (outdir / "R149_COHERENCE_RUNTIME_v1.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
    )
    args = parser.parse_args()
    build(args.outdir.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
