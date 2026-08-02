#!/usr/bin/env python3
"""Build the R123 core-schematic proposal assets.

This generator is intentionally self-contained and does not write to the live
``LaTex/figures`` tree.  It preserves the scientific statuses of the current
Part-II, PES-R, 47C and black-hole-shell figures while replacing page-scale
layouts that render below ordinary print-readable font sizes.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Patch

# Import the one candidate-wide palette.  Component generators must not grow
# private colour conventions: the shared module is the publication contract.
CANDIDATE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CANDIDATE_ROOT / "scripts"))
from r123_palette import (  # noqa: E402
    EXTERNAL_EDGE,
    EXTERNAL_FILL,
    GRAPHITE,
    INK,
    LEVEL_A_EDGE,
    LEVEL_A_FILL,
    LEVEL_B_EDGE,
    LEVEL_B_FILL,
    LEVEL_C_EDGE,
    LEVEL_C_FILL,
    OPEN_EDGE,
    OPEN_FILL,
    PAPER,
    TENSION_EDGE,
    TENSION_FILL,
)

EDGE = GRAPHITE
EDGE_BLUE = LEVEL_A_EDGE
EDGE_GREEN = LEVEL_B_EDGE
EDGE_AMBER = LEVEL_C_EDGE
EDGE_RED = TENSION_EDGE
EDGE_GRAY = EXTERNAL_EDGE
FILL_A = LEVEL_A_FILL
FILL_B = LEVEL_B_FILL
FILL_C = LEVEL_C_FILL
FILL_OPEN = OPEN_FILL
FILL_FAIL = TENSION_FILL
FILL_NEUTRAL = EXTERNAL_FILL
WHITE = PAPER

PDF_METADATA = {
    "Title": "ECT R123 readable core schematic",
    "Author": "ECT reproducibility workflow",
    "Subject": "Proposal-only visual restoration; scientific status preserved",
    "Keywords": "ECT R123 readability grayscale-safe",
    "Creator": "build_core_schematics.py",
    "CreationDate": dt.datetime(2026, 7, 21, 0, 0, 0, tzinfo=dt.timezone.utc),
    "ModDate": dt.datetime(2026, 7, 21, 0, 0, 0, tzinfo=dt.timezone.utc),
}


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.2,
            "axes.titlesize": 12.0,
            "axes.labelsize": 9.2,
            "legend.fontsize": 8.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "ect-r123-core-schematics-v1",
        }
    )


def save(fig: plt.Figure, outdir: Path, stem: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        outdir / f"{stem}.pdf",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata=PDF_METADATA,
    )
    fig.savefig(
        outdir / f"{stem}.png",
        dpi=240,
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={"Software": "ECT R123 deterministic core-schematic renderer"},
    )
    plt.close(fig)


def canvas(width: float, height: float, xlim: tuple[float, float], ylim: tuple[float, float]) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    return fig, ax


def style_for(status: str) -> tuple[str, str, str, float]:
    return {
        "A": (FILL_A, EDGE_BLUE, "-", 1.45),
        "B": (FILL_B, EDGE_GREEN, "-.", 1.45),
        "C": (FILL_C, EDGE_AMBER, ":", 1.65),
        "OPEN": (FILL_OPEN, EDGE_GRAY, "--", 1.45),
        "FAIL": (FILL_FAIL, EDGE_RED, "-", 2.0),
        "NEUTRAL": (FILL_NEUTRAL, EDGE, "-", 1.25),
    }[status]


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str = "",
    *,
    status: str = "OPEN",
    title_size: float = 9.0,
    body_size: float = 8.0,
    tag: str | None = None,
    title_y: float = 0.64,
    body_y: float = 0.28,
) -> None:
    face, edge, ls, lw = style_for(status)
    # A literal status tag occupies its own top band.  Clamp the title/body
    # baselines into lower bands so the status can never collide with content.
    if tag:
        title_y = min(title_y, 0.53)
        body_y = max(body_y, 0.24)
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.07",
        facecolor=face,
        edgecolor=edge,
        linestyle=ls,
        linewidth=lw,
    )
    ax.add_patch(patch)
    if tag:
        ax.text(
            x + 0.09,
            y + h - 0.09,
            tag,
            ha="left",
            va="top",
            fontsize=8.4,
            weight="bold",
            color=edge,
        )
    ax.text(
        x + w / 2,
        y + title_y * h,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        weight="bold",
        color=INK,
        linespacing=1.05,
    )
    if body:
        ax.text(
            x + w / 2,
            y + body_y * h,
            body,
            ha="center",
            va="center",
            fontsize=body_size,
            color=INK,
            linespacing=1.10,
        )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    conditional: bool = False,
    label: str = "",
    label_xy: tuple[float, float] | None = None,
    color: str = EDGE,
    rad: float = 0.0,
    width: float = 1.25,
) -> None:
    ls = "--" if conditional else "-"
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10.5,
            linewidth=width,
            linestyle=ls,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
        )
    )
    if label:
        lx, ly = label_xy or ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.12)
        ax.text(lx, ly, label, ha="center", va="center", fontsize=8.4, color=INK)


def routed_arrow(
    ax: plt.Axes,
    points: tuple[tuple[float, float], ...],
    *,
    conditional: bool = False,
    color: str = EDGE,
    width: float = 1.25,
) -> None:
    """Draw one semantic edge along a polyline, with one terminal arrowhead.

    Intermediate line segments are render-only routing geometry: they do not add
    logical nodes or dependencies to the diagram.
    """
    if len(points) < 2:
        raise ValueError("A routed arrow requires at least a start and an end point.")
    ls = "--" if conditional else "-"
    final_segment = len(points) - 2
    for index, (start, end) in enumerate(zip(points, points[1:])):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>" if index == final_segment else "-",
                mutation_scale=10.5,
                linewidth=width,
                linestyle=ls,
                color=color,
                connectionstyle="arc3,rad=0.0",
            )
        )


def legend(ax: plt.Axes, *, y: float = 0.12, ncol: int = 3) -> None:
    handles = [
        Patch(facecolor=FILL_A, edgecolor=EDGE_BLUE, linewidth=1.4, label="Level A / structural"),
        Patch(facecolor=FILL_B, edgecolor=EDGE_GREEN, linestyle="-.", linewidth=1.4, label="Level B / conditional"),
        Patch(facecolor=FILL_C, edgecolor=EDGE_AMBER, linestyle=":", linewidth=1.7, label="Level C / matched diagnostic"),
        Patch(facecolor=FILL_OPEN, edgecolor=EDGE_GRAY, linestyle="--", linewidth=1.4, label="Open / missing owner"),
        Patch(facecolor=FILL_FAIL, edgecolor=EDGE_RED, linewidth=2.0, label="Incompatible / no-go"),
        Line2D([0], [0], color=EDGE, lw=1.4, ls="--", label="Conditional/Open dependency"),
    ]
    ax.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, y),
        frameon=False,
        ncol=ncol,
        fontsize=8.4,
        handlelength=2.2,
        columnspacing=1.2,
    )


def partii_overview(outdir: Path) -> None:
    fig, ax = canvas(6.25, 6.40, (0, 10), (0, 9.7))
    ax.text(5, 9.37, "Part II derivation logic — readable overview", ha="center", weight="bold", fontsize=12.2)
    ax.text(5, 9.02, "Navigation only. Panels A–C carry the status-bearing detail at print scale.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    box(ax, 2.60, 7.82, 4.80, 0.78, "Part I outputs", "P1–P6, BR1 and declared inputs", status="A", tag="LEVEL A", title_y=0.61, body_y=0.23)
    box(ax, 2.60, 6.57, 4.80, 0.78, "Bridge §11", "inherited scalar inputs", status="A", tag="LEVEL A", title_y=0.61, body_y=0.23)
    box(ax, 1.15, 5.08, 7.70, 0.92, "Panel A · physical map and scalar–tensor closure", "metric · source · tensor · clock owners Open", status="OPEN", tag="OPEN OWNERS", title_y=0.62, body_y=0.24)
    box(ax, 1.15, 3.62, 7.70, 0.92, "Panel B · galactic and cosmological diagnostics", "HRC / RAR / BTFR: C · cosmology: C / Open", status="C", tag="LEVEL C / OPEN", title_y=0.62, body_y=0.24)
    box(ax, 1.15, 2.16, 7.70, 0.92, "Panel C · missing owners and terminal gates", "PPN · Boltzmann · merger transport · state maps Open", status="OPEN", tag="OPEN PROGRAMME", title_y=0.62, body_y=0.24)

    arrow(ax, (5.0, 7.82), (5.0, 7.35))
    arrow(ax, (5.0, 6.57), (5.0, 6.00), conditional=True)
    arrow(ax, (5.0, 5.08), (5.0, 4.54), conditional=True)
    arrow(ax, (5.0, 3.62), (5.0, 3.08), conditional=True)

    ax.text(5, 1.59, "Solid arrow = declared dependency or organisation. Dashed arrow = conditional or Open link.", ha="center", fontsize=8.4, color=INK)
    ax.text(5, 1.28, "Colour never upgrades status; literal tags and border styles remain authoritative.", ha="center", fontsize=8.4, color=INK)
    legend(ax, y=-0.005, ncol=3)
    save(fig, outdir, "fig_partII_derivation_logic_overview_r123")


def partii_panel_a(outdir: Path) -> None:
    fig, ax = canvas(6.25, 8.65, (0, 10), (0, 13.6))
    ax.text(5, 13.27, "Part II — panel A: physical map and scalar–tensor closure", ha="center", weight="bold", fontsize=11.8)
    ax.text(5, 12.93, "Internal algebra is kept distinct from every missing physical owner.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    box(ax, 2.55, 11.75, 4.90, 0.76, "Part I outputs → Bridge §11", r"P1–P6, BR1; $\beta<\alpha<4\beta$, $\hat c_*$, $u_0$, $K^{AB}$", status="A", tag="LEVEL A", title_y=0.60, body_y=0.23)

    box(ax, 0.25, 10.20, 4.45, 1.02, "Scalar-coordinate Lorentz algebra", "clock / rod / matter map Open", status="OPEN", tag="ALGEBRA A · MAP OPEN")
    box(ax, 5.30, 10.20, 4.45, 1.02, "Scalar principal tensor", "principal tensor A · metric Open", status="OPEN", tag="ALGEBRA A · METRIC OPEN")

    box(ax, 0.25, 8.58, 4.45, 1.02, "Noether source conserved", "static-density vertex is missing", status="OPEN", tag="MISSING VERTEX")
    box(ax, 5.30, 8.58, 4.45, 1.02, "Conditional tensor match", "normalisation B · tensor owner Open", status="B", tag="LEVEL B / OPEN")

    box(ax, 2.55, 6.88, 4.90, 1.08, "Scalar–tensor closure §13.5", "corrected EOM · closure ansatz B", status="B", tag="LEVEL B")

    box(ax, 0.25, 5.18, 4.45, 1.05, "Amplitude closure ansatz", "closure B · variable bridge Open", status="B", tag="LEVEL B / OPEN")
    box(ax, 5.30, 5.18, 4.45, 1.05, "Frozen-$F$ GR limit", "screening / body charge Open", status="OPEN", tag="OPEN")

    box(ax, 0.25, 3.52, 4.45, 1.02, "Flat Euclidean ambient", "physical metric bridge Open", status="OPEN", tag="LEVEL A / OPEN")
    box(ax, 5.30, 3.52, 4.45, 1.02, r"$\pi_2(S^3)=0$", "no primary monopoles", status="A", tag="LEVEL A")
    box(ax, 2.55, 1.88, 4.90, 1.02, "One longitudinal scalar mode", "strict pullback A · larger bundle Open", status="OPEN", tag="LEVEL A / OPEN")

    arrow(ax, (5.0, 11.75), (2.48, 11.22))
    arrow(ax, (5.0, 11.75), (7.52, 11.22))
    arrow(ax, (2.48, 10.20), (2.48, 9.60))
    arrow(ax, (7.52, 10.20), (7.52, 9.60), conditional=True)
    arrow(ax, (2.48, 8.58), (4.15, 7.96), conditional=True)
    arrow(ax, (7.52, 8.58), (5.85, 7.96), conditional=True)
    arrow(ax, (5.0, 6.88), (2.48, 6.23), conditional=True)
    arrow(ax, (5.0, 6.88), (7.52, 6.23), conditional=True)
    # These remain exactly three closure dependencies.  Their routes avoid the
    # two intermediate boxes, while retaining their original endpoints and
    # solid/dashed (unconditional/conditional) semantics.
    routed_arrow(
        ax,
        ((5.0, 6.88), (4.92, 6.52), (0.05, 6.52), (0.05, 4.78), (2.48, 4.54)),
    )
    routed_arrow(
        ax,
        ((5.0, 6.88), (5.08, 6.52), (9.95, 6.52), (9.95, 4.78), (7.52, 4.54)),
        conditional=True,
    )
    routed_arrow(
        ax,
        ((5.0, 6.88), (5.05, 6.52), (5.05, 3.22), (5.0, 2.90)),
        conditional=True,
    )

    legend(ax, y=-0.005, ncol=3)
    save(fig, outdir, "fig_partII_derivation_logic_panel_A_r123")


def partii_panel_b(outdir: Path) -> None:
    fig, ax = canvas(6.25, 9.20, (0, 10), (0, 14.4))
    ax.text(5, 14.05, "Part II — panel B: galactic and cosmological diagnostics", ha="center", weight="bold", fontsize=11.8)
    ax.text(5, 13.70, "Applications do not upgrade the Open gravity, metric, state or likelihood bridges.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    box(ax, 0.25, 12.16, 4.45, 1.02, "Amplitude closure ansatz", "supplied closure · owner Open", status="B", tag="LEVEL B / OPEN")
    box(ax, 5.30, 12.16, 4.45, 1.02, "HRC response bridge", "matched scale C · P1–P6 owner Open", status="OPEN", tag="OPEN")

    box(ax, 0.25, 10.56, 4.45, 1.02, "Branch orientation", "T reversal A · persistence B", status="B", tag="LEVEL A / B")
    box(ax, 5.30, 10.56, 4.45, 1.02, r"Environment/history law $\Xi$", "sign and amplitude remain Open", status="OPEN", tag="OPEN")

    box(
        ax, 0.25, 8.96, 4.45, 1.15,
        "Conditional no-phantom\nbound", "conditional inequality only",
        status="B", tag="LEVEL B", title_size=8.4, title_y=0.55,
        body_size=8.0, body_y=0.13,
    )
    box(ax, 5.30, 8.96, 4.45, 1.02, "Calibrated two-slope state", "one supplied state · Level C", status="C", tag="LEVEL C / OPEN")

    box(ax, 0.25, 7.36, 4.45, 1.02, "Named age integral", "conditional time budget · C", status="C", tag="LEVEL C / OPEN")
    box(ax, 5.30, 7.36, 4.45, 1.02, "JWST forward model", "growth + baryons + selection Open", status="OPEN", tag="OPEN")

    box(ax, 0.25, 5.76, 4.45, 1.02, "HRC algebraic diagnostic", "SPARC algebra · no metric likelihood", status="C", tag="LEVEL C")
    box(ax, 5.30, 5.76, 4.45, 1.02, "BTFR slope 4", "algebra A · bridge B · data C", status="C", tag="LEVEL A / B / C")

    box(ax, 0.25, 4.16, 4.45, 1.02, "HRC RAR diagnostic", "matched scale · residual scatter", status="C", tag="LEVEL C")
    box(ax, 5.30, 4.16, 4.45, 1.02, "Cluster local-map identity", "order A · lensing/morphology Open", status="OPEN", tag="LEVEL A / OPEN")

    box(
        ax, 0.25, 2.56, 4.45, 1.15,
        "No halo term in\nalgebraic test", "test C · particle content Open",
        status="C", tag="LEVEL C / OPEN", title_size=8.4, title_y=0.55,
        body_size=8.0, body_y=0.13,
    )
    box(ax, 5.30, 2.56, 4.45, 1.02, "Late source / proof class", "physical owner remains Open", status="OPEN", tag="OPEN")

    arrow(ax, (2.48, 12.16), (2.48, 11.58))
    arrow(ax, (7.52, 12.16), (7.52, 11.58), conditional=True)
    arrow(ax, (2.48, 10.56), (2.48, 9.98), conditional=True)
    arrow(ax, (7.52, 10.56), (7.52, 9.98), conditional=True)
    arrow(ax, (2.48, 8.96), (2.48, 8.38), conditional=True)
    arrow(ax, (7.52, 8.96), (7.52, 8.38), conditional=True)
    arrow(ax, (2.48, 5.76), (2.48, 5.18))
    arrow(ax, (7.52, 5.76), (7.52, 5.18), conditional=True)
    arrow(ax, (2.48, 4.16), (2.48, 3.58), conditional=True)
    arrow(ax, (7.52, 4.16), (7.52, 3.58), conditional=True)

    ax.text(5, 1.92, "Terminal reading: these are controlled diagnostics and conditional envelopes—not a closed ECT cosmology.", ha="center", fontsize=8.4, color=INK)
    legend(ax, y=-0.005, ncol=3)
    save(fig, outdir, "fig_partII_derivation_logic_panel_B_r123")


def partii_panel_c(outdir: Path) -> None:
    fig, ax = canvas(6.25, 8.70, (0, 10), (0, 13.7))
    ax.text(5, 13.36, "Part II — panel C: missing owners and terminal gates", ha="center", weight="bold", fontsize=11.8)
    ax.text(5, 13.02, "Open nodes are explicit research requirements—not derived ECT predictions.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    box(ax, 0.25, 11.36, 4.45, 1.05, "EFT and primordial inputs", r"$Z_u$, $W(u)$, $\beta$, $n_s$, $r$: Open", status="OPEN", tag="OPEN")
    box(ax, 5.30, 11.36, 4.45, 1.05, "Cosmological fraction budget", "state / observable map Open", status="OPEN", tag="OPEN")

    box(ax, 0.25, 9.66, 4.45, 1.05, "Canonical scalar BVP", "body charge / PPN map Open", status="OPEN", tag="OPEN")
    box(ax, 5.30, 9.66, 4.45, 1.05, "Orientation determinant fixed", "result A · action descent Open", status="A", tag="LEVEL A / OPEN")

    box(ax, 0.25, 7.96, 4.45, 1.05, r"Trace-free $V+C_I$ route", "action B · state map Open", status="OPEN", tag="LEVEL B / OPEN")
    box(ax, 5.30, 7.96, 4.45, 1.05, "Baryogenesis inventory", "arithmetic C · transport Open", status="OPEN", tag="LEVEL C / OPEN")

    box(
        ax, 0.25, 6.26, 4.45, 1.18,
        "Cluster response", "order map A · lensing/\nmorphology Open",
        status="OPEN", tag="LEVEL A / OPEN", title_y=0.58,
        body_size=8.0, body_y=0.20,
    )
    box(ax, 5.30, 6.26, 4.45, 1.05, "JWST completion", "growth / baryons / selection Open", status="OPEN", tag="OPEN")

    box(
        ax, 0.25, 4.56, 4.45, 1.18,
        "Physical metric /\nsource owners", "clock · tensor · density vertex",
        status="OPEN", tag="OPEN", title_size=8.4, title_y=0.58,
        body_size=8.0, body_y=0.13,
    )
    box(ax, 5.30, 4.56, 4.45, 1.05, "Application owners", "screening · Boltzmann · merger", status="OPEN", tag="OPEN")

    box(ax, 2.55, 2.66, 4.90, 1.10, "13 tests / closure gates", "F1–F13 retain the declared hierarchy", status="NEUTRAL")

    arrow(ax, (2.48, 11.36), (2.48, 10.71), conditional=True)
    arrow(ax, (7.52, 11.36), (7.52, 10.71), conditional=True)
    arrow(ax, (2.48, 9.66), (2.48, 9.01), conditional=True)
    arrow(ax, (7.52, 9.66), (7.52, 9.01), conditional=True)
    arrow(ax, (2.48, 7.96), (2.48, 7.31), conditional=True)
    arrow(ax, (7.52, 7.96), (7.52, 7.31), conditional=True)
    arrow(ax, (2.48, 6.26), (2.48, 5.61), conditional=True)
    arrow(ax, (7.52, 6.26), (7.52, 5.61), conditional=True)
    arrow(ax, (2.48, 4.56), (4.20, 3.76), conditional=True)
    arrow(ax, (7.52, 4.56), (5.80, 3.76), conditional=True)

    ax.text(5, 2.10, "Terminal reading: the inventory localises missing action, state, vertex and likelihood owners; it does not supply them.", ha="center", fontsize=8.4, color=INK)
    legend(ax, y=-0.005, ncol=3)
    save(fig, outdir, "fig_partII_derivation_logic_panel_C_r123")


def pes_r(outdir: Path) -> None:
    fig, ax = canvas(6.25, 6.35, (0, 10), (0, 9.65))
    ax.text(5, 9.29, "PES-R: response–persistence classification", ha="center", weight="bold", fontsize=12.2)
    ax.text(5, 8.91, "Persistence is mode-type specific; none of these tests is a Born, spectrum or outcome theorem.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    box(ax, 0.35, 6.78, 4.35, 1.56, "1. Dynamical admissibility", "physical pole / eigenmode /\nconstrained solution", status="A", tag="DYNAMICS", title_size=9.3, body_size=8.4)
    box(
        ax,
        5.30,
        6.36,
        4.35,
        1.98,
        "2. Type-specific persistence",
        "pole: width / survival\nnon-normal: transient gain\nbranch cut: finite-window retention\nzero mode: leakage / diffusion / gap",
        status="B",
        tag="PERSISTENCE",
        title_size=9.0,
        body_size=8.0,
        title_y=0.55,
        body_y=0.23,
    )
    box(ax, 0.35, 4.05, 4.35, 1.68, "3. Pairwise record test", "quiet / loud / intermediate\nfor a declared pair, state,\nchannel and named protocol", status="B", tag="RECORD", title_size=8.8, body_size=8.2, title_y=0.55, body_y=0.20)
    box(ax, 5.30, 4.31, 4.35, 1.35, "Sector constraints", "boundary, charge, representation\nand optional topology", status="OPEN", tag="SECTOR-SPECIFIC", title_size=9.3, body_size=8.4)
    box(ax, 1.15, 1.85, 7.70, 1.55, "PES-R: Level-B organising taxonomy", "ECT record operator, state, and response/noise kernels remain Open.\nIt is not a spectrum, Born, Crooks, or unique-outcome theorem.", status="B", tag="LEVEL B / OPEN", title_size=9.8, body_size=8.4)

    arrow(ax, (4.70, 7.56), (5.30, 7.56))
    arrow(ax, (2.52, 4.05), (3.35, 3.40), conditional=True)
    arrow(ax, (7.48, 4.31), (6.65, 3.40), conditional=True)
    arrow(ax, (7.48, 6.36), (7.25, 3.40))

    handles = [
        Patch(facecolor=FILL_A, edgecolor=EDGE_BLUE, label="structural dynamical test"),
        Patch(facecolor=FILL_B, edgecolor=EDGE_GREEN, linestyle="-.", label="Level-B classification/test"),
        Patch(facecolor=FILL_OPEN, edgecolor=EDGE_GRAY, linestyle="--", label="sector-specific/Open input"),
        Line2D([0], [0], color=EDGE, ls="--", label="independent/conditional axis"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=2, frameon=False, fontsize=8.4)
    save(fig, outdir, "fig_pes_diagram_r123")


def channel_summary(outdir: Path) -> None:
    fig, ax = canvas(6.25, 6.45, (0, 10), (0, 9.82))
    ax.text(5, 9.47, "47C necessary-screen summary", ha="center", weight="bold", fontsize=12.2)
    ax.text(5, 9.05, "10 detailed ledger rows → 7 reader-facing families → 0 identified physical PES channels", ha="center", fontsize=9.5, weight="bold", color=EDGE_RED)

    box(
        ax,
        0.28,
        7.05,
        9.44,
        1.48,
        "Necessary gates (passing them is not sufficient by itself)",
        "action + declared split → constrained, canonically normalised modes → physical vertex/projector\n→ physical state + retarded/noise kernels → finite pairwise record functional",
        status="B",
        tag="NECESSARY SCREEN",
        title_size=9.2,
        body_size=8.0,
        title_y=0.55,
        body_y=0.22,
    )

    box(ax, 0.28, 4.95, 4.45, 1.50, "Missing physical vertex", "linear director; mixed channel", status="C", tag="MISSING VERTEX", title_size=8.9, body_size=8.3)
    box(ax, 5.27, 4.95, 4.45, 1.50, "Not identifiable", "scalar trace; HRC/static;\nindependent tensor; mixed", status="OPEN", tag="OPEN INPUTS", title_size=8.9, body_size=8.3)
    box(
        ax,
        0.28,
        2.73,
        4.45,
        1.70,
        "Scoped incompatibility",
        "minimal director composite:\ntested vacuum/thermal channels only;\ngeneral case NOT IDENTIFIABLE",
        status="FAIL",
        tag="TESTED SCOPE ONLY",
        title_size=8.9,
        body_size=8.0,
        title_y=0.52,
        body_y=0.22,
    )
    box(
        ax,
        5.27,
        2.73,
        4.45,
        1.70,
        "Conditional double counting",
        "integrated radial mode unless a new\nWilsonian split, subtraction and\ncounterterm ledger are proved",
        status="FAIL",
        tag="SPLIT REQUIRED",
        title_size=8.7,
        body_size=8.0,
        title_y=0.52,
        body_y=0.22,
    )

    ax.text(5, 2.18, "The seven-family graphic aggregates—and does not replace—the detailed ten-row ledger.", ha="center", fontsize=8.4, color=EDGE_GRAY)
    ax.text(5, 1.80, "Static HRC compliance is a response, not a PES noise kernel; imported D–P numbers are external Level C.", ha="center", fontsize=8.2, color=INK)

    handles = [
        Patch(facecolor=FILL_C, edgecolor=EDGE_AMBER, linestyle=":", label="missing physical vertex"),
        Patch(facecolor=FILL_OPEN, edgecolor=EDGE_GRAY, linestyle="--", label="not identifiable / Open inputs"),
        Patch(facecolor=FILL_FAIL, edgecolor=EDGE_RED, label="incompatible in tested scope"),
        Patch(facecolor=FILL_FAIL, edgecolor=EDGE_RED, linestyle="--", label="double counting unless split proved"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=2, frameon=False, fontsize=8.1)
    save(fig, outdir, "r123_mediator_channels_summary_47C")


def channel_detail(outdir: Path) -> None:
    rows = [
        ("Linear\ndirector", "fixed-map mode\n$T^{00}h_{00}=0$", "state absent", "MISSING\nVERTEX", "C"),
        ("Scalar\ntrace", "parametric trace response;\nabsolute scale not fixed", "absolute noise\nabsent", "NOT\nIDENTIFIABLE", "OPEN"),
        ("Director\ncomposite", r"$O\sim\delta n_i\delta n_i$;\ncoefficient open", r"$J_O\sim\omega^9$\ntested", "INCOMPATIBLE with\nuniversal D-P", "FAIL"),
        ("HRC /\nstatic", "augmented static owner;\nnot a record operator", "state/noise\nabsent", "NOT IDENTIFIABLE\nas PES", "OPEN"),
        ("Independent\ntensor", r"supplied $h_{\mu\nu}T^{\mu\nu}/2$", "ECT bath state\nabsent", "NOT\nIDENTIFIABLE", "OPEN"),
        ("Integrated\nradial", "already reduced;\npossible trace term", "no new split", "DOUBLE-COUNTED\nunless subtracted", "FAIL"),
        ("Mixed\nchannel", "operator / vertex\nabsent", "state/noise\nabsent", "MISSING VERTEX /\nNOT IDENTIFIABLE", "C"),
    ]
    fig, ax = canvas(9.20, 6.30, (0, 1), (0, 1))
    ax.text(0.5, 0.965, "Detailed 47C candidate-channel ledger", ha="center", weight="bold", fontsize=12.2)
    ax.text(0.5, 0.925, "Landscape appendix asset; read each row from candidate to terminal result.", ha="center", fontsize=8.4, color=EDGE_GRAY)

    headers = ["Candidate", "Dynamics / physical vertex", "State / noise", "Terminal 47C result"]
    table = ax.table(
        cellText=[r[:4] for r in rows],
        colLabels=headers,
        cellLoc="center",
        colLoc="center",
        colWidths=[0.15, 0.35, 0.20, 0.30],
        bbox=[0.02, 0.13, 0.96, 0.74],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.2)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(EXTERNAL_EDGE)
        cell.set_linewidth(1.1)
        cell.get_text().set_color(INK)
        if r == 0:
            cell.set_facecolor(EXTERNAL_FILL)
            cell.get_text().set_weight("bold")
            cell.get_text().set_fontsize(8.5)
        else:
            status = rows[r - 1][4]
            if c == 3:
                face, edge, ls, lw = style_for(status)
                cell.set_facecolor(face)
                cell.set_edgecolor(edge)
                cell.set_linestyle(ls)
                cell.set_linewidth(lw)
                cell.get_text().set_weight("bold")
            else:
                cell.set_facecolor(EXTERNAL_FILL)
    ax.text(0.5, 0.070, "Response and noise remain distinct; no row closes variable/split → dynamics → vertex → state/noise.", ha="center", fontsize=8.4, weight="bold")
    ax.text(0.5, 0.035, "Static HRC compliance is a response; imported Diósi–Penrose numbers remain external Level-C benchmarks.", ha="center", fontsize=8.4)
    save(fig, outdir, "r123_mediator_channels_detail_47C")


def text_along_arc(
    ax: plt.Axes,
    text: str,
    radius: float,
    start_deg: float,
    end_deg: float,
    *,
    fontsize: float,
    color: str = INK,
    weight: str = "normal",
) -> None:
    """Place literal characters along a top arc; 0 degrees is top."""
    import numpy as np

    chars = list(text)
    angles = np.linspace(np.radians(start_deg), np.radians(end_deg), len(chars))
    for ch, a in zip(chars, angles):
        x = radius * np.sin(a)
        y = radius * np.cos(a)
        ax.text(
            x,
            y,
            ch,
            ha="center",
            va="center",
            rotation=-np.degrees(a),
            fontsize=fontsize,
            color=color,
            weight=weight,
            zorder=10,
        )


def bh_shell(outdir: Path) -> None:
    fig, ax = canvas(6.25, 4.95, (-3.35, 5.65), (-3.75, 3.40))
    ax.set_aspect("equal")
    ax.text(1.15, 3.18, "HYPOTHETICAL COMPLETION · LEVEL C / OPEN", ha="center", weight="bold", fontsize=10.3, color=EDGE_RED)
    ax.text(1.15, 2.89, "No ECT shell action, location, stability or dynamics has been derived.", ha="center", fontsize=8.0, color=INK)

    # Concentric sectors.  Distinct relative luminances make the rings remain
    # separated after grayscale conversion without dense hatch.
    outer = Circle((0, 0), 2.70, facecolor=EXTERNAL_FILL, edgecolor=EXTERNAL_EDGE, linewidth=1.5, zorder=1)
    shell = Circle((0, 0), 1.96, facecolor=OPEN_FILL, edgecolor=OPEN_EDGE, linewidth=1.8, linestyle="--", zorder=2)
    inner = Circle((0, 0), 1.08, facecolor=GRAPHITE, edgecolor=INK, linewidth=1.6, zorder=3)
    ax.add_patch(outer)
    ax.add_patch(shell)
    ax.add_patch(inner)

    text_along_arc(ax, "H_ext · ACCESSIBLE EXTERIOR", 2.42, -64, 64, fontsize=8.4, weight="bold")
    text_along_arc(ax, "H_shell · RESPONSE LAYER · OPEN", 1.62, -70, 70, fontsize=8.4, weight="bold")
    ax.text(0, 0.22, r"$\mathcal{H}_{\rm int}$", ha="center", va="center", fontsize=12.0, color=WHITE, weight="bold", zorder=12)
    ax.text(0, -0.18, "inaccessible", ha="center", va="center", fontsize=9.2, color=WHITE, zorder=12)
    ax.text(0, -0.52, "strong-field sector", ha="center", va="center", fontsize=8.7, color=WHITE, zorder=12)

    arrow(ax, (3.75, 1.86), (1.48, 1.30), conditional=True, label="candidate coupling (ansatz)", label_xy=(3.20, 2.18), color=EDGE_AMBER)
    ax.text(3.85, 1.58, "coherent and topological modes", fontsize=8.2, color=INK, ha="left")
    arrow(ax, (3.75, -0.62), (0.95, -0.40), conditional=True, label="conditional trace", label_xy=(3.10, -0.31), color=EDGE_GRAY)
    ax.text(3.85, -0.94, "over shell + interior sectors", fontsize=8.2, color=INK, ha="left")

    formula = FancyBboxPatch((2.58, -2.94), 3.02, 1.12, boxstyle="round,pad=0.08,rounding_size=0.08", facecolor=FILL_OPEN, edgecolor=EDGE_GRAY, linewidth=1.2, linestyle="--")
    ax.add_patch(formula)
    ax.text(4.09, -2.24, r"$\rho_{\rm ext}=\mathrm{Tr}_{\rm sh,int}|\Psi\rangle\langle\Psi|$", ha="center", va="center", fontsize=10.5)
    ax.text(4.09, -2.63, "bookkeeping after a supplied\nfactor split", ha="center", va="center", fontsize=8.4, color=INK)
    arrow(ax, (1.35, -2.28), (2.58, -2.37), conditional=True, color=EDGE_GRAY)

    handles = [
        Patch(facecolor=EXTERNAL_FILL, edgecolor=EXTERNAL_EDGE, label="accessible exterior"),
        Patch(facecolor=OPEN_FILL, edgecolor=OPEN_EDGE, linestyle="--", label="hypothetical response layer / Open"),
        Patch(facecolor=GRAPHITE, edgecolor=INK, label="inaccessible strong-field sector"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.005, 0.005), frameon=False, fontsize=8.4, ncol=1)
    save(fig, outdir, "fig_bh_shell_r123")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent / "assets")
    args = parser.parse_args()
    configure()
    partii_overview(args.outdir)
    partii_panel_a(args.outdir)
    partii_panel_b(args.outdir)
    partii_panel_c(args.outdir)
    pes_r(args.outdir)
    channel_summary(args.outdir)
    channel_detail(args.outdir)
    bh_shell(args.outdir)
    print(f"R123 core schematics written to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
