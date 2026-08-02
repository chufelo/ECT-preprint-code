#!/usr/bin/env python3
"""Render the two R123 singleton colour remediations owned by this component.

The numerical seesaw arrays are identical to the live owner script.  The
common-vacuum diagram is a status-preserving externalisation of the live TikZ
figure: hues separate response mechanisms, while every box retains a literal
status label and all non-derived links remain dashed.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path

# Matplotlib otherwise attempts to materialise a font cache under the user's
# home directory.  Keep every generated/cache byte inside this proposal
# component and freeze the PDF timestamp for byte-identical replay.
_SCRIPT_PATH = Path(__file__).resolve()
_COMPONENT_PATH = _SCRIPT_PATH.parent.parent
_MPLCONFIG = _COMPONENT_PATH / "qa" / "mplconfig"
_MPLCONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLCONFIG))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")  # 2026-07-21 UTC

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
R123 = HERE.parents[2]
PALETTE_PATH = R123 / "scripts" / "r123_palette.py"


def load_palette():
    spec = importlib.util.spec_from_file_location("r123_palette", PALETTE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


P = load_palette()
PDF_METADATA = {
    "Creator": "ECT R123 deterministic renderer",
    "Producer": "Matplotlib",
    "CreationDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
    "ModDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def common_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 11.5,
            "axes.titlesize": 12.0,
            "axes.labelsize": 11.5,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10.5,
            "mathtext.fontset": "cm",
            "axes.linewidth": 0.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def build_seesaw(out: Path) -> dict:
    """Re-render the unchanged supplied seesaw benchmark in R123 colours."""
    common_style()
    v2 = 246.0
    phi0 = 2.44e18
    mass = np.logspace(6, 19, 500)
    y_values = [1.0, 0.1, 4.5e-3, 1e-3, 1e-4]
    labels = [
        r"$y_\nu=1$",
        r"$y_\nu=0.1$",
        r"$y_\nu\approx4.5\times10^{-3}$",
        r"$y_\nu=10^{-3}$",
        r"$y_\nu=10^{-4}$",
    ]
    colours = [P.GRAPHITE, P.NFW, P.HRC0, P.HRC3, P.MOND]
    styles = ["--", "-.", "-", ":", (0, (7, 2, 1.5, 2))]
    markers = ["s", "D", "o", "^", "v"]
    widths = [1.7, 1.8, 2.8, 1.8, 1.8]

    fig, ax = plt.subplots(figsize=(7.25, 5.15), constrained_layout=True)
    fig.suptitle(
        "SUPPLIED SEESAW BENCHMARK — Level C/Open; anchors are not ECT predictions",
        fontsize=10.2,
        fontweight="bold",
        color=P.TENSION_EDGE,
    )
    arrays = {}
    for y, label, colour, linestyle, marker, width in zip(
        y_values, labels, colours, styles, markers, widths
    ):
        values = y**2 * v2**2 / mass * 1e9
        arrays[f"y={y:g}"] = {
            "first": float(values[0]),
            "last": float(values[-1]),
            "count": int(values.size),
        }
        ax.plot(
            mass,
            values,
            color=colour,
            linestyle=linestyle,
            marker=marker,
            markevery=70,
            markersize=3.4,
            linewidth=width,
            label=label,
        )

    weinberg = v2**2 / phi0 * 1e9
    ax.axhline(weinberg, color=P.GRAPHITE, linestyle=(0, (6, 3)), linewidth=1.2)
    ax.text(1.4e6, weinberg * 1.75, r"supplied $m_\nu=v_2^2/\phi_0$", fontsize=10.5, color=P.INK)
    ax.axhspan(0.04, 0.06, color=P.EXTERNAL_FILL, alpha=0.95, zorder=0)
    ax.text(3e17, 0.050, r"imported atmospheric band", fontsize=10.2, color=P.INK, ha="right", va="center")

    for x, label, linestyle, colour in [
        (2.4e10, r"supplied $M_R$ anchor", "-", P.HRC0),
        (1e9, "leptogenesis benchmark", "--", P.MOND),
        (phi0, r"$\phi_0$", ":", P.NFW),
    ]:
        ax.axvline(x, color=colour, linestyle=linestyle, linewidth=1.15)
        ax.text(x * 1.12, 2e-7, label, fontsize=10.2, color=P.INK, rotation=90, ha="left", va="bottom")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(xlabel=r"$M_R$ [GeV]", ylabel=r"$m_\nu$ [eV]", xlim=(1e6, 1e19), ylim=(1e-7, 1e4))
    ax.grid(True, which="major", color=P.GRID, linewidth=0.7)
    ax.legend(loc="upper right", frameon=True, edgecolor=P.GRAPHITE, facecolor=P.PAPER)
    ax.tick_params(which="both", direction="in", top=True, right=True)
    fig.savefig(out, metadata={**PDF_METADATA, "Title": "R123 supplied seesaw benchmark"})
    plt.close(fig)
    return {"arrays": arrays, "weinberg_floor_eV": weinberg}


def draw_box(ax, xy, width, height, title, body, fill, edge, status):
    x, y = xy
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=1.8,
        edgecolor=edge,
        facecolor=fill,
    )
    ax.add_patch(patch)
    ax.text(x, y + 0.16 * height, title, ha="center", va="center", fontsize=10.0, fontweight="bold", color=P.INK)
    ax.text(x, y - 0.05 * height, body, ha="center", va="center", fontsize=8.8, color=P.INK)
    ax.text(x, y - 0.32 * height, status, ha="center", va="center", fontsize=7.9, fontweight="bold", color=edge)


def build_vacuum_response(out: Path) -> dict:
    common_style()
    fig, ax = plt.subplots(figsize=(10.8, 6.1), constrained_layout=True)
    ax.set_xlim(-6.2, 6.2)
    ax.set_ylim(-6.1, 1.5)
    ax.axis("off")
    ax.set_title("Open common-response programme — all four targets remain Open", fontsize=12.0, fontweight="bold", color=P.INK)

    draw_box(ax, (0, 0.3), 3.2, 1.05, "Ordered coherent vacuum", "programme-level structural input", P.EXTERNAL_FILL, P.GRAPHITE, "STRUCTURAL INPUT")
    channels = [
        (-4.8, -2.25, "Boundary response", "Casimir", P.OPEN_FILL, P.OPEN_EDGE),
        (-1.6, -2.25, "Time-dependent response", "particle production", P.OPEN_FILL, P.OPEN_EDGE),
        (1.6, -2.25, "Observer response", "Unruh", P.OPEN_FILL, P.OPEN_EDGE),
        (4.8, -2.25, "Strong-field interface", "Hawking / horizon", P.OPEN_FILL, P.OPEN_EDGE),
    ]
    for x, y, title, body, fill, edge in channels:
        draw_box(ax, (x, y), 2.75, 1.25, title, body, fill, edge, "EXTERNAL TARGET")
        ax.annotate("", xy=(x, y + 0.64), xytext=(0, -0.24), arrowprops={"arrowstyle": "-", "linestyle": "--", "linewidth": 1.4, "color": P.INK})

    draw_box(ax, (0, -4.8), 3.35, 1.05, "Analogue-gravity continuity", "motivation and comparison only", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "EXTERNAL MOTIVATION")
    for x, y, *_ in channels:
        ax.annotate("", xy=(x, y - 0.64), xytext=(0, -4.28), arrowprops={"arrowstyle": "-", "linestyle": "--", "linewidth": 1.15, "color": P.INK})

    ax.text(0, -5.72, "Dashed links = conceptual continuity; no common physical bundle, state, continuation or coupling has been derived.", ha="center", va="center", fontsize=8.6, color=P.GRAPHITE)
    ax.text(0, -6.00, "The shared gold fill is the R123 Open status colour; mechanism names, not hue, distinguish the targets.", ha="center", va="center", fontsize=8.3, color=P.GRAPHITE)
    fig.savefig(out, metadata={**PDF_METADATA, "Title": "R123 open common-response programme"})
    plt.close(fig)
    return {"channel_count": 4, "all_links": "dashed/open", "status_preserved": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=COMPONENT / "assets" / "singletons")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    seesaw = args.output / "fig_neutrino_seesaw_r123.pdf"
    vacuum = args.output / "fig_qs_vacuum_unified_r123.pdf"
    scientific = {
        "seesaw": build_seesaw(seesaw),
        "vacuum_response": build_vacuum_response(vacuum),
    }
    manifest = {
        "schema": "ECT-R123-singletons-v1",
        "status": "PROPOSAL ONLY - LIVE APPLY NOT AUTHORISED",
        "palette_owner": str(PALETTE_PATH.relative_to(HERE.parents[6])),
        "outputs": {
            seesaw.name: sha256(seesaw),
            vacuum.name: sha256(vacuum),
        },
        "scientific_payload": scientific,
        "runtime": {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__},
    }
    path = args.output / "R123_SINGLETON_MANIFEST_v1.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest["outputs"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
