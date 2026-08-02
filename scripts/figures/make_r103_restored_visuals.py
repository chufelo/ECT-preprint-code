#!/usr/bin/env python3
"""Generate three status-safe R103 publication visualisations.

The script has no manuscript-text side effects.  It uses the Okabe-Ito palette,
while line style, marker, border style, hatch and explicit status text make
colour redundant.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.lines import Line2D
import numpy as np


BLUE = "#0072B2"
SKY = "#56B4E9"
GREEN = "#009E73"
ORANGE = "#E69F00"
VERMILION = "#D55E00"
PURPLE = "#CC79A7"
YELLOW = "#F0E442"
BLACK = "#222222"
GRAY = "#737373"
LIGHT_BLUE = "#DCECF7"
LIGHT_GREEN = "#DDF2E9"
LIGHT_ORANGE = "#FBE9C9"
LIGHT_RED = "#F5DDD7"
LIGHT_GRAY = "#E8E8E8"

PDF_METADATA = {
    "Title": "R103 corrected publication visual",
    "Author": "ECT reproducibility workflow",
    "Subject": "Status-safe ECT visualisation",
    "Keywords": "ECT R103 reproducible visualisation",
    "Creator": "make_r103_restored_visuals.py",
    "CreationDate": dt.datetime(2026, 7, 19, 0, 0, 0, tzinfo=dt.timezone.utc),
    "ModDate": dt.datetime(2026, 7, 19, 0, 0, 0, tzinfo=dt.timezone.utc),
}


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9.5,
            "legend.fontsize": 8.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "r103-restored-visuals-v1",
        }
    )


def save(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", metadata=PDF_METADATA)
    fig.savefig(stem.with_suffix(".png"), dpi=240, bbox_inches="tight", metadata={"Software": "ECT R103 deterministic visual"})
    plt.close(fig)


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    *,
    face: str,
    edge: str,
    linestyle: str = "-",
    hatch: str | None = None,
    linewidth: float = 1.6,
    title_font: float = 9.4,
    body_font: float = 7.8,
    title_y: float = 0.64,
    body_y: float = 0.30,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.08",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        linestyle=linestyle,
        hatch=hatch,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + title_y * h, title, ha="center", va="center", weight="bold", fontsize=title_font, linespacing=1.05)
    ax.text(x + w / 2, y + body_y * h, body, ha="center", va="center", fontsize=body_font, linespacing=1.20)


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str,
    linestyle: str = "-",
    label: str = "",
    label_y: float | None = None,
    linewidth: float = 1.7,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
        )
    )
    if label:
        ax.text(
            0.5 * (start[0] + end[0]),
            label_y if label_y is not None else 0.5 * (start[1] + end[1]) + 0.18,
            label,
            ha="center",
            va="bottom",
            color=BLACK,
            fontsize=7.2,
        )


def cn_scale_chain(out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 5.9))
    ax.set_xlim(0, 9.0)
    ax.set_ylim(0, 6.0)
    ax.axis("off")
    ax.text(4.5, 5.72, r"Orientation stiffness and the open tensor-normalisation bridge", ha="center", va="center", fontsize=12.4, weight="bold")
    ax.text(4.5, 5.43, "Solid: established/conditional route under stated assumptions. Dashed: missing physical owner.", ha="center", color=GRAY, fontsize=8.2)

    h, w = 1.35, 2.42
    xs = [0.25, 3.29, 6.33]
    y_top, y_bottom = 3.58, 1.62
    common = dict(title_font=8.8, body_font=7.2, title_y=0.66, body_y=0.27)
    box(ax, xs[0], y_top, w, h, "Ordered variables", "$\\partial_A\\Phi=u n_A$\nP4 kinematics", face=LIGHT_BLUE, edge=BLUE, **common)
    box(ax, xs[1], y_top, w, h, "Heavy-radial determinant", "$\\frac{1}{2}\\,\\mathrm{Tr}\\ln\\mathcal{O}_\\sigma$\nNLO; declared closure", face=LIGHT_GREEN, edge=GREEN, hatch="//", **common)
    box(ax, xs[2], y_top, w, h, "Orientation coefficient $\\mathcal{C}_n$", "$\\mathcal{C}_n=\\hat a_{\\rm eff}/(16\\pi^2m_\\sigma^2)$\nconditional; matching open", face=LIGHT_GREEN, edge=GREEN, hatch="//", **common)
    box(ax, xs[2], y_bottom, w, h, "Orientation stiffness $\\kappa_n$", "$\\kappa_n\\equiv\\mathcal{C}_nu_0^2$\nexact EFT definition", face=LIGHT_BLUE, edge=BLUE, **common)
    box(ax, xs[1], y_bottom, w, h, "Physical tensor scale $M_G$", "$M_G^2\\;?=\\;c_M\\kappa_n$\nTT owner/source missing", face=LIGHT_ORANGE, edge=ORANGE, linestyle="--", hatch="xx", **common)
    box(ax, xs[0], y_bottom, w, h, "Newton constant $G_N$", "$G_N=c_{\\rm char}^4/(8\\pi M_G^2)$\nstandard tensor-EFT matching", face=LIGHT_GRAY, edge=BLACK, **common)

    arrow(ax, (xs[0] + w, y_top + h / 2), (xs[1], y_top + h / 2), color=BLUE, label="background reduction", label_y=5.02)
    arrow(ax, (xs[1] + w, y_top + h / 2), (xs[2], y_top + h / 2), color=GREEN, label="operator basis", label_y=5.02)
    arrow(ax, (xs[2] + w / 2, y_top), (xs[2] + w / 2, y_bottom + h), color=BLUE, label="definition", label_y=3.08)
    arrow(ax, (xs[2], y_bottom + h / 2), (xs[1] + w, y_bottom + h / 2), color=ORANGE, linestyle="--", label="OPEN: $c_M$ + tensor owner", label_y=3.02, linewidth=2.0)
    arrow(ax, (xs[1], y_bottom + h / 2), (xs[0] + w, y_bottom + h / 2), color=BLACK, label="standard weak-field matching", label_y=3.02)

    ax.text(4.5, 1.25, r"Established owner chain ends at $\kappa_n$: dimensional equality alone creates neither helicity-2 dynamics nor a static-density vertex.", ha="center", fontsize=8.4, weight="bold")
    handles = [
        Patch(facecolor=LIGHT_BLUE, edgecolor=BLUE, label="established definition/kinematics"),
        Patch(facecolor=LIGHT_GREEN, edgecolor=GREEN, hatch="//", label="conditional under declared assumptions"),
        Patch(facecolor=LIGHT_ORANGE, edgecolor=ORANGE, hatch="xx", linestyle="--", label="Open/missing owner"),
        Patch(facecolor=LIGHT_GRAY, edgecolor=BLACK, label="standard result inside supplied completion"),
    ]
    ax.legend(handles=handles, ncol=2, loc="lower center", frameon=False, bbox_to_anchor=(0.5, 0.015), fontsize=7.2)
    save(fig, out_dir / "r103_Cn_scalechain_corrected")


def mediator_47c(out_dir: Path) -> None:
    rows = [
        ("Linear director", "fixed-map mode", "$T^{00}h_{00}=0$", "absent", "MISSING VERTEX", "missing"),
        ("Scalar trace", "parametric response", "trace vertex only", "absolute noise absent", "NOT IDENTIFIABLE", "open"),
        ("Director\ncomposite", r"$O\sim\delta n_i\delta n_i$", "coefficient/projector open", r"$J_O\sim\omega^9$ tested", "INCOMPATIBLE with\nuniversal D-P", "fail"),
        ("HRC/static\ncompliance", "augmented static owner", "not a record operator", "state/noise absent", "NOT IDENTIFIABLE\nas PES", "open"),
        ("Independent\ntensor", "supplied completion", r"$h_{\mu\nu}T^{\mu\nu}/2$ conditional", "ECT bath state absent", "NOT IDENTIFIABLE", "open"),
        ("Integrated\nradial mode", "already reduced", "possible trace term", "no new split", "DOUBLE-COUNTED\nunless subtracted", "fail"),
        ("Mixed channel", "operator absent", "vertex absent", "state/noise absent", "MISSING VERTEX /\nNOT IDENTIFIABLE", "missing"),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 8.9))
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 8.95)
    ax.axis("off")
    ax.text(4.3, 8.67, "Terminal 47C taxonomy of candidate gravitational record channels", ha="center", fontsize=11.8, weight="bold")
    ax.text(4.3, 8.39, r"No row closes variable/split $\rightarrow$ dynamics $\rightarrow$ physical vertex $\rightarrow$ state/noise.", ha="center", color=GRAY, fontsize=8.0)

    cols = [(0.16, 1.44), (1.69, 2.23), (4.01, 1.86), (5.96, 2.48)]
    headers = ["Candidate", "Dynamics / vertex", "State / noise", "Terminal 47C result"]
    for (x, w), title in zip(cols, headers):
        box(ax, x, 7.88, w, 0.45, title, "", face=LIGHT_GRAY, edge=BLACK, linewidth=1.1, title_font=8.0, title_y=0.52)
    y0, rh = 7.02, 0.72
    for i, (candidate, dyn, vertex, state, terminal, status) in enumerate(rows):
        y = y0 - i * 0.88
        if status == "fail":
            face, edge, ls, hatch = LIGHT_RED, VERMILION, "-.", "xx"
        elif status == "missing":
            face, edge, ls, hatch = LIGHT_ORANGE, ORANGE, "--", "//"
        else:
            face, edge, ls, hatch = LIGHT_ORANGE, ORANGE, ":", ".."
        bface = "#F7F7F7" if i % 2 == 0 else "#ECECEC"
        box(ax, x=cols[0][0], y=y, w=cols[0][1], h=rh, title=candidate, body="", face=bface, edge=GRAY, linewidth=0.8, title_font=7.5, title_y=0.52)
        box(ax, x=cols[1][0], y=y, w=cols[1][1], h=rh, title=dyn, body=vertex, face=bface, edge=GRAY, linewidth=0.8, title_font=7.1, body_font=6.6, title_y=0.66, body_y=0.26)
        box(ax, x=cols[2][0], y=y, w=cols[2][1], h=rh, title=state, body="", face=bface, edge=GRAY, linewidth=0.8, title_font=7.0, title_y=0.52)
        box(ax, x=cols[3][0], y=y, w=cols[3][1], h=rh, title=terminal, body="", face=face, edge=edge, linestyle=ls, hatch=hatch, linewidth=1.4, title_font=7.0, title_y=0.52)
        for j in range(3):
            x1 = cols[j][0] + cols[j][1]
            x2 = cols[j + 1][0]
            arrow(ax, (x1 + 0.02, y + rh / 2), (x2 - 0.02, y + rh / 2), color=GRAY, linewidth=0.8)

    ax.text(4.3, 0.64, "PES-R KEEP: response and noise remain distinct; static compliance is not a noise kernel;\nD-P numbers are external Level-C benchmarks.", fontsize=7.6, color=BLACK, ha="center")
    handles = [
        Patch(facecolor=LIGHT_ORANGE, edgecolor=ORANGE, hatch="//", linestyle="--", label="missing vertex"),
        Patch(facecolor=LIGHT_ORANGE, edgecolor=ORANGE, hatch="..", linestyle=":", label="not identifiable / Open inputs"),
        Patch(facecolor=LIGHT_RED, edgecolor=VERMILION, hatch="xx", linestyle="-.", label="incompatible or double-counted"),
    ]
    ax.legend(handles=handles, loc="lower center", frameon=False, ncol=3, bbox_to_anchor=(0.5, 0.005), fontsize=6.9)
    save(fig, out_dir / "r103_mediator_channels_terminal_47C")


def load_hwg(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def two_slope_hwg(data_csv: Path, out_dir: Path) -> None:
    d = load_hwg(data_csv)
    x = np.log1p(d["z"])
    g_proxy = 100.0 * (1.0 / d["F_over_F0"] - 1.0)
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 4.15), constrained_layout=True)

    ax = axes[0]
    ax.plot(x, d["delta_E_percent"], color=BLUE, marker="o", ls="-", lw=1.7, label="two-slope / control")
    ax.axhline(0.0, color=BLACK, ls=":", lw=0.9)
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$100(H_{2s}/H_{\rm ctl}-1)$ [\%]", title="(a) Expansion response")
    ax.legend(frameon=False, loc="upper left")

    ax = axes[1]
    ax.plot(x, d["w_eff_reference"], color=BLACK, marker="s", ls="--", lw=1.2, label="matched control")
    ax.plot(x, d["w_eff_two_slope"], color=GREEN, marker="^", markerfacecolor="white", markeredgewidth=1.4, ls="-.", lw=1.7, label="two-slope")
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$w_{\rm eff}=-1-2H'/(3H)$", title="(b) Total kinematic $w_{eff}$")
    ax.legend(frameon=False, loc="lower right")
    ax.text(0.03, 0.93, "curves overlap at this scale", transform=ax.transAxes, fontsize=7.4, va="top")

    ax = axes[2]
    ax.plot(x, g_proxy, color=ORANGE, marker="D", ls=(0, (5, 2, 1, 2)), lw=1.7, label=r"$F_0/F(z)-1$")
    ax.axhline(0.0, color=BLACK, ls=":", lw=0.9)
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$100(F_0/F-1)$ [\%]", title="(c) Inverse-$F$ background proxy")
    ax.legend(frameon=False, loc="upper left")
    ax.text(0.03, 0.09, "not local $G_N$; finite-body/PPN map Open", transform=ax.transAxes, fontsize=7.4)

    fig.suptitle("Conditional two-slope state: $H$, total $w_{eff}$ and inverse-$F$ response (no common-$\\varepsilon$ law)", fontsize=12.5, weight="bold")
    fig.text(0.5, -0.015, "Level A only inside the supplied action/state; Level C observable diagnostic; not a unique P1-P6 cosmology.", ha="center", fontsize=8.3, color=GRAY)
    save(fig, out_dir / "r103_two_slope_HwG_conditional")


def main() -> None:
    latex_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hwg-csv",
        type=Path,
        default=latex_root / "data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=latex_root / "figures/r103",
    )
    args = parser.parse_args()
    configure()
    cn_scale_chain(args.output_dir)
    mediator_47c(args.output_dir)
    two_slope_hwg(args.hwg_csv, args.output_dir)


if __name__ == "__main__":
    main()
