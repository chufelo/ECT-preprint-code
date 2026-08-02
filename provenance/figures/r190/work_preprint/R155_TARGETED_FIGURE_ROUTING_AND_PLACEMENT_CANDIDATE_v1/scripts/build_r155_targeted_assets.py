#!/usr/bin/env python3
"""Build the four bounded R155 figure successors requested in reader review.

The scientific payload, status vocabulary, node sets, edge sets, equations,
and analytic arrays are inherited unchanged from their declared R123--R154
owners.  R155 changes only edge routing, annotation ownership, legend
placement, and page-readable geometry.  It never overwrites historical assets.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r155-targeted-mpl")
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784937600")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np

SCRIPT = Path(__file__).resolve()
LATEX = SCRIPT.parents[4]
PACKAGE = SCRIPT.parent.parent
DEFAULT_OUTPUT = PACKAGE / "publication_build/LaTex/figures/r155"

TARGETED_SOURCE = (
    LATEX
    / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v2/"
    "components/targeted_readability_assets/build_targeted_readability_assets.py"
)
R153_SOURCE = LATEX / "scripts/r153_figures/build_bh_shell_r153.py"

PDF_META = {
    "Title": "ECT R155 targeted reader-layout successors",
    "Author": "ECT reproducibility workflow",
    "Subject": "Presentation-only routing and annotation correction",
    "Keywords": "ECT R155 grayscale-safe routing",
    "Creator": "build_r155_targeted_assets.py",
    "CreationDate": datetime(2026, 7, 25, 15, 0, 0, tzinfo=timezone.utc),
    "ModDate": datetime(2026, 7, 25, 15, 0, 0, tzinfo=timezone.utc),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


T = load_module("r155_targeted_owner", TARGETED_SOURCE)
G = load_module("r155_r153_owner", R153_SOURCE)


def save_pair(fig: plt.Figure, outdir: Path, stem: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        outdir / f"{stem}.pdf",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={**PDF_META, "Title": stem},
    )
    fig.savefig(
        outdir / f"{stem}.png",
        dpi=220,
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={"Software": "ECT R155 targeted renderer"},
    )
    plt.close(fig)


def ontology(outdir: Path) -> None:
    """Preserve seven nodes/seven edges while routing every edge around boxes."""
    T.configure()
    fig = plt.figure(figsize=(6.20, 8.40))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis("off")
    ax.text(
        5,
        12.55,
        "Status-guarded full/reduced-description map",
        ha="center",
        va="center",
        fontsize=12.2,
        weight="bold",
    )
    ax.text(
        5,
        12.15,
        "Status is explicit; border style and luminance remain redundant.",
        ha="center",
        va="center",
        fontsize=10.8,
        color=T.P.GRAPHITE,
    )

    T.status_box(ax, (5, 10.90), 7.4, 1.20, "Full condensate candidate description", "interacting OS/unitarity completion", T.P.OPEN_FILL, T.P.OPEN_EDGE, "OPEN", "--")
    T.status_box(ax, (5, 8.95), 7.4, 1.20, "Declared resolved/unresolved split", "physical vertices + state + protocol required", T.P.EXTERNAL_FILL, T.P.EXTERNAL_EDGE, "SUPPLIED SPLIT")
    T.status_box(ax, (2.55, 6.65), 4.45, 1.55, "Coherence-retaining channel", r"small $\Phi_{ab}$ for declared" + "\ncomparisons", T.P.LEVEL_B_FILL, T.P.LEVEL_B_EDGE, "CONDITIONAL", "-.")
    T.status_box(ax, (7.45, 6.65), 4.45, 1.55, "Record-forming channel", r"large $\Phi_{ab}$ for declared" + "\ncomparisons", T.P.LEVEL_B_FILL, T.P.LEVEL_B_EDGE, "CONDITIONAL", "-.")
    T.status_box(ax, (5.00, 4.65), 7.40, 1.35, "Gravity mediator / GIE", "own vertex and channel required", T.P.OPEN_FILL, T.P.OPEN_EDGE, "OPEN", "--")
    T.status_box(ax, (3.05, 2.65), 5.25, 1.45, "No universal transition", r"no metric-signature or ontology" + "\n" + r"jump from $\Phi_{ab}$", T.P.TENSION_FILL, T.P.TENSION_EDGE, "NO-GO GUARD", title_size=11.0)
    T.status_box(ax, (7.72, 2.65), 3.55, 1.45, "Unique outcome / update", "OP-Q19", T.P.OPEN_FILL, T.P.OPEN_EDGE, "OPEN", "--", title_size=10.8)

    T.arrow(ax, (5, 10.28), (5, 9.57))
    T.arrow(ax, (5, 8.33), (2.55, 7.44))
    T.arrow(ax, (5, 8.33), (7.45, 7.44))
    T.arrow(ax, (5, 8.33), (5, 5.34), dashed=True)
    # The original diagonal crossed the gravity-mediator box.  This edge now
    # uses the free lane left of that box.
    T.routed_arrow(ax, [(1.10, 5.86), (1.10, 3.62), (1.45, 3.39)])
    # Preserve the original second no-go edge and the independent Open branch.
    T.routed_arrow(ax, [(7.25, 5.86), (0.55, 5.55), (0.55, 3.58), (1.00, 3.39)])
    T.routed_arrow(ax, [(7.70, 5.86), (9.72, 5.55), (9.72, 3.58), (8.78, 3.39)], dashed=True)

    ax.text(5, 1.25, "Solid arrows: declared reduction/guard.  Dashed arrows: Open branch.", ha="center", fontsize=10.8, color=T.P.INK)
    ax.text(5, 0.78, "The map classifies supplied, conditional, Open, or ruled-out steps;", ha="center", fontsize=10.8, color=T.P.GRAPHITE)
    ax.text(5, 0.42, "it does not add a metric-signature, gravity-mediator, or outcome theorem.", ha="center", fontsize=10.8, color=T.P.GRAPHITE)
    save_pair(fig, outdir, "fig_two_level_ontology_r155")


def pes_r(outdir: Path) -> None:
    """Preserve five nodes/four edges; route persistence through the free lane."""
    G.configure()
    fig, ax = G.canvas(6.25, 6.35, (0, 10), (0, 9.65))
    ax.text(5, 9.29, "PES-R: response–persistence classification", ha="center", weight="bold", fontsize=12.2)
    ax.text(5, 8.91, "Persistence is mode-type specific; none of these tests is a Born, spectrum or outcome theorem.", ha="center", fontsize=8.4, color=G.EDGE_GRAY)

    G.box(ax, 0.35, 6.78, 4.35, 1.56, "1. Dynamical admissibility", "physical pole / eigenmode /\nconstrained solution", status="A", tag="DYNAMICS", title_size=9.3, body_size=8.4)
    G.box(ax, 5.30, 6.36, 4.35, 1.98, "2. Type-specific persistence", "pole: width / survival\nnon-normal: transient gain\nbranch cut: finite-window retention\nzero mode: leakage / diffusion / gap", status="B", tag="PERSISTENCE", title_size=9.0, body_size=8.0, title_y=0.55, body_y=0.23)
    G.box(ax, 0.35, 4.05, 4.35, 1.68, "3. Pairwise record test", "quiet / loud / intermediate\nfor a declared pair, state,\nchannel and named protocol", status="B", tag="RECORD", title_size=8.8, body_size=8.2, title_y=0.55, body_y=0.20)
    G.box(ax, 5.30, 4.31, 4.35, 1.35, "Sector constraints", "boundary, charge, representation\nand optional topology", status="OPEN", tag="SECTOR-SPECIFIC", title_size=9.3, body_size=8.4)
    G.box(ax, 0.55, 1.78, 8.90, 1.68, "PES-R: Level-B organising taxonomy", "ECT record operator, state, and response/noise kernels remain Open.\nIt is not a spectrum, Born, Crooks, or unique-outcome theorem.", status="B", tag="LEVEL B / OPEN", title_size=9.5, body_size=7.9)

    G.arrow(ax, (4.70, 7.56), (5.30, 7.56))
    G.arrow(ax, (2.52, 4.05), (3.20, 3.46), conditional=True)
    G.arrow(ax, (7.48, 4.31), (6.80, 3.46), conditional=True)
    G.routed_arrow(
        ax,
        ((6.10, 6.36), (5.02, 5.92), (5.02, 3.74), (5.80, 3.46)),
    )

    handles = [
        Patch(facecolor=G.FILL_A, edgecolor=G.EDGE_BLUE, label="structural dynamical test"),
        Patch(facecolor=G.FILL_B, edgecolor=G.EDGE_GREEN, linestyle="-.", label="Level-B classification/test"),
        Patch(facecolor=G.FILL_OPEN, edgecolor=G.EDGE_GRAY, linestyle="--", label="sector-specific/Open input"),
        Line2D([0], [0], color=G.EDGE, ls="--", label="independent/conditional axis"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=2, frameon=False, fontsize=8.4)
    save_pair(fig, outdir, "fig_pes_diagram_r155")


def qubit(outdir: Path) -> None:
    """Keep the two exact analytic curves; move legend and marker annotation."""
    G.configure()
    phi = np.logspace(-3, 1.5, 1000)
    visibility = np.exp(-phi)
    p = np.clip((1 + visibility) / 2, 1e-15, 1 - 1e-15)
    entropy = -(p * np.log(p) + (1 - p) * np.log(1 - p))
    information = 2 * entropy / np.log(2)

    fig, ax = plt.subplots(figsize=(7.2, 5.25))
    ax2 = ax.twinx()
    line1 = ax.semilogx(
        phi,
        information,
        color=G.LEVEL_A_EDGE,
        lw=2.1,
        label=r"total $I(S{:}E)$ in the pure-dilation toy",
    )[0]
    line2 = ax2.semilogx(
        phi,
        visibility,
        color=G.LEVEL_B_EDGE,
        ls="--",
        lw=1.9,
        label=r"residual coherence $V=e^{-\Phi}$",
    )[0]
    ax.set(
        xlabel=r"pairwise dephasing parameter $\Phi$",
        ylabel=r"mutual information $I(S{:}E)$ [bits]",
        xlim=(1e-3, 30),
        ylim=(0, 2.12),
    )
    ax2.set_ylabel(r"residual coherence $V$", color=G.LEVEL_B_EDGE)
    ax2.tick_params(axis="y", colors=G.LEVEL_B_EDGE)
    ax2.set_ylim(0, 1.05)
    for x, label, y in [
        (0.006, "visibility proxy", 0.12),
        (0.062, "visibility proxy", 0.12),
        (np.log(np.sqrt(2)), "Werner toy marker", 0.38),
    ]:
        ax.axvline(x, color=G.GRAPHITE, ls=":" if x < 0.1 else "--", lw=0.9)
        ax.text(x * 1.08, y, label, rotation=90, va="bottom", fontsize=9.5, color=G.GRAPHITE)
    ax.axvline(1, color=G.LEVEL_C_EDGE, ls="-.", lw=1.0)
    ax.text(
        1.08,
        0.10,
        r"$\Phi=1$: model marker, not boundary",
        rotation=90,
        va="bottom",
        fontsize=9.5,
        color=G.LEVEL_C_EDGE,
    )
    ax.grid(True, which="both", color="#D8D8D8", lw=0.45)
    ax.legend(
        [line1, line2],
        [line1.get_label(), line2.get_label()],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=2,
        frameon=False,
        fontsize=9.0,
    )
    fig.subplots_adjust(left=0.13, right=0.87, top=0.79, bottom=0.17)
    save_pair(fig, outdir, "fig_qubit_info_decoherence_r155")


def shell(outdir: Path) -> None:
    """Make the supplied coupling input and conditional-trace dataflow explicit."""
    G.configure()
    fig, ax = G.canvas(6.25, 5.10, (-3.35, 5.75), (-3.75, 3.40))
    ax.set_aspect("equal")
    ax.text(1.20, 3.18, "HYPOTHETICAL COMPLETION · LEVEL C / OPEN", ha="center", weight="bold", fontsize=10.3, color=G.EDGE_RED)
    ax.text(1.20, 2.89, "No ECT shell action, location, stability, coupling or dynamics has been derived.", ha="center", fontsize=8.0, color=G.INK)

    outer = G.Circle((0, 0), 2.70, facecolor=G.EXTERNAL_FILL, edgecolor=G.EXTERNAL_EDGE, linewidth=1.5, zorder=1)
    response = G.Circle((0, 0), 1.96, facecolor=G.OPEN_FILL, edgecolor=G.OPEN_EDGE, linewidth=1.8, linestyle="--", zorder=2)
    inner = G.Circle((0, 0), 1.08, facecolor=G.GRAPHITE, edgecolor=G.INK, linewidth=1.6, zorder=3)
    ax.add_patch(outer)
    ax.add_patch(response)
    ax.add_patch(inner)
    G.text_along_arc(ax, "H_ext · ACCESSIBLE EXTERIOR", 2.42, -64, 64, fontsize=8.4, weight="bold")
    G.text_along_arc(ax, "H_shell · RESPONSE LAYER · OPEN", 1.62, -70, 70, fontsize=8.4, weight="bold")
    ax.text(0, 0.22, r"$\mathcal{H}_{\rm int}$", ha="center", va="center", fontsize=12.0, color=G.WHITE, weight="bold", zorder=12)
    ax.text(0, -0.18, "inaccessible", ha="center", va="center", fontsize=9.2, color=G.WHITE, zorder=12)
    ax.text(0, -0.52, "strong-field sector", ha="center", va="center", fontsize=8.7, color=G.WHITE, zorder=12)

    # Explicit source callout: a supplied mode sector feeds the shell ansatz.
    G.box(
        ax,
        3.05,
        1.15,
        2.40,
        1.05,
        "coherent and topological modes",
        "candidate strong coupling",
        status="C",
        tag="SUPPLIED ANSATZ",
        title_size=7.7,
        body_size=7.6,
        title_y=0.50,
        body_y=0.20,
    )
    G.arrow(
        ax,
        (3.05, 1.66),
        (1.50, 1.03),
        conditional=True,
        color=G.EDGE_AMBER,
        rad=0.10,
        zorder=8,
    )

    # The shell and interior are the selected factors of the trace operation.
    # The two source lines intentionally have no arrowheads: they are
    # bookkeeping leaders, not physical flows or derived couplings.  The only
    # dataflow arrow is from the declared operation to the reduced state.
    G.box(
        ax,
        3.05,
        -0.62,
        2.40,
        0.98,
        "conditional trace",
        r"over $\mathcal{H}_{\rm shell}\otimes\mathcal{H}_{\rm int}$",
        status="OPEN",
        tag="SUPPLIED SPLIT",
        title_size=8.2,
        body_size=7.4,
        title_y=0.50,
        body_y=0.20,
    )
    ax.add_patch(
        FancyArrowPatch(
            (1.82, -0.48),
            (3.05, -0.22),
            arrowstyle="-",
            linewidth=1.15,
            linestyle="--",
            color=G.EDGE_GRAY,
            connectionstyle="arc3,rad=-0.08",
            zorder=8,
        )
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.82, -0.33),
            (3.05, -0.02),
            arrowstyle="-",
            linewidth=1.15,
            linestyle="--",
            color=G.EDGE_GRAY,
            connectionstyle="arc3,rad=-0.14",
            zorder=8,
        )
    )
    formula = FancyBboxPatch(
        (2.48, -2.94),
        3.10,
        1.12,
        boxstyle="round,pad=0.08,rounding_size=0.08",
        facecolor=G.FILL_OPEN,
        edgecolor=G.EDGE_GRAY,
        linewidth=1.2,
        linestyle="--",
    )
    ax.add_patch(formula)
    ax.text(4.03, -2.24, r"$\rho_{\rm ext}=\mathrm{Tr}_{\rm sh,int}|\Psi\rangle\langle\Psi|$", ha="center", va="center", fontsize=9.4)
    ax.text(4.03, -2.63, "bookkeeping after a supplied\nfactor split", ha="center", va="center", fontsize=7.7, color=G.INK)
    G.arrow(ax, (4.25, -0.62), (4.03, -1.82), conditional=True, color=G.EDGE_GRAY, zorder=8)

    handles = [
        Patch(facecolor=G.EXTERNAL_FILL, edgecolor=G.EXTERNAL_EDGE, label="accessible exterior"),
        Patch(facecolor=G.OPEN_FILL, edgecolor=G.OPEN_EDGE, linestyle="--", label="hypothetical response layer / Open"),
        Patch(facecolor=G.GRAPHITE, edgecolor=G.INK, label="inaccessible strong-field sector"),
    ]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.005, 0.005), frameon=False, fontsize=8.1, ncol=1)
    save_pair(fig, outdir, "fig_bh_shell_r155")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    ontology(args.outdir)
    pes_r(args.outdir)
    qubit(args.outdir)
    shell(args.outdir)
    print(f"R155 targeted assets written to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
