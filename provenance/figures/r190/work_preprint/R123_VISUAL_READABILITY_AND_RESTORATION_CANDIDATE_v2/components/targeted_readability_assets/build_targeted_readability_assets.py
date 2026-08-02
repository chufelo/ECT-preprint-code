#!/usr/bin/env python3
"""Build targeted R123 readability replacements without touching live files.

The scientific values, node/edge topology, status words, and comparison text
are frozen to their named R123 owners.  This builder changes only physical
page size, layout, line wrapping, and the shared luminance-first palette.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import sys

SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parent
LATEX = next(parent for parent in SCRIPT.parents if (parent / "ECT_preprint.tex").is_file())
WORKSPACE = LATEX.parent
PROVENANCE_WORK = LATEX / "provenance/figures/r190/work_preprint"
R123_V1 = PROVENANCE_WORK / "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"
R123_V2 = PROVENANCE_WORK / "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v2"
PALETTE_PATH = R123_V1 / "scripts/r123_palette.py"
MPLCONFIG = Path(os.environ.get("MPLCONFIGDIR", "/tmp/ect-r123-targeted-mpl"))
MPLCONFIG.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPLCONFIG)
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784592000")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np
from PIL import Image

spec = importlib.util.spec_from_file_location("r123_palette", PALETTE_PATH)
P = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = P
assert spec.loader is not None
spec.loader.exec_module(P)

PDF_META = {
    "Creator": "ECT R123 targeted readability renderer",
    "Producer": "Matplotlib",
    "CreationDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
    "ModDate": datetime(2026, 7, 21, tzinfo=timezone.utc),
}

# A4 with the preprint's 2.5 cm margins: 16 cm physical text width.
TEXTWIDTH_PS_PT = 160.0 / 25.4 * 72.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11.2,
            "axes.titlesize": 12.0,
            "axes.labelsize": 11.2,
            "xtick.labelsize": 10.8,
            "ytick.labelsize": 10.8,
            "legend.fontsize": 10.8,
            "mathtext.fontset": "dejavusans",
            "axes.linewidth": 0.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save(fig, out: Path, preview: Path, title: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    preview.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, metadata={**PDF_META, "Title": title})
    fig.savefig(preview, dpi=170, metadata={"Software": "ECT R123 targeted readability renderer"})
    plt.close(fig)


def gray_preview(color: Path, gray: Path) -> None:
    gray.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(color) as im:
        im.convert("L").save(gray, optimize=False)


def status_box(
    ax,
    center: tuple[float, float],
    width: float,
    height: float,
    title: str,
    body: str,
    fill: str,
    edge: str,
    status: str,
    linestyle: str = "-",
    title_size: float = 11.2,
    body_size: float = 10.8,
    status_size: float = 10.8,
    title_y: float = 0.22,
    body_y: float = -0.02,
    status_y: float = -0.35,
) -> None:
    x, y = center
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.045",
        facecolor=fill,
        edgecolor=edge,
        linewidth=1.8,
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    ax.text(x, y + title_y * height, title, ha="center", va="center", fontsize=title_size, weight="bold", color=P.INK, linespacing=0.98)
    ax.text(x, y + body_y * height, body, ha="center", va="center", fontsize=body_size, color=P.INK, linespacing=1.06)
    ax.text(x, y + status_y * height, status, ha="center", va="center", fontsize=status_size, weight="bold", color=edge)


def arrow(ax, start: tuple[float, float], end: tuple[float, float], dashed: bool = False) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "linewidth": 1.45,
            "linestyle": "--" if dashed else "-",
            "color": P.INK,
            "mutation_scale": 11,
        },
    )


def routed_arrow(ax, points: list[tuple[float, float]], dashed: bool = False) -> None:
    """Orthogonal/segmented arrow used only to keep edges outside boxes."""
    for idx, (start, end) in enumerate(zip(points, points[1:])):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>" if idx == len(points) - 2 else "-",
                mutation_scale=11,
                linewidth=1.45,
                linestyle="--" if dashed else "-",
                color=P.INK,
                connectionstyle="arc3,rad=0",
                shrinkA=0,
                shrinkB=0,
            )
        )


def build_scales(out: Path, color: Path) -> dict:
    """Exact R123 numerical payload, now on two full-width stacked axes."""
    configure()
    g_n, m_sun, kpc = 6.67430e-11, 1.98847e30, 3.0856775814913673e19
    a_m0, phi0, v2 = 1.0824013602e-10, 2.435e18, 246.22
    masses = np.logspace(7, 12, 300)
    r_kpc = np.sqrt(g_n * masses * m_sun / a_m0) / kpc
    m_ref = 1e10
    r_ref = np.sqrt(g_n * m_ref * m_sun / a_m0) / kpc

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.20, 8.25), constrained_layout=True)
    x = np.array([0.0, 1.0])
    energies = np.array([phi0, v2])
    ax1.plot(x, energies, "--", color=P.GRAPHITE, lw=1.7, zorder=1)
    ax1.scatter([0], [phi0], s=115, color=P.LEVEL_A_EDGE, edgecolor=P.INK, marker="o", zorder=3)
    ax1.scatter([1], [v2], s=110, color=P.EXTERNAL_EDGE, edgecolor=P.INK, marker="s", zorder=3)
    ax1.set_yscale("log")
    ax1.set_xlim(-0.20, 1.20)
    ax1.set_ylim(1e1, 1e20)
    ax1.set_xticks(x, [r"$\phi_0$", r"$v_2$"])
    ax1.set_ylabel("energy / matching scale [GeV]")
    ax1.set_title("(a) Energy-dimension inventory", loc="left", weight="bold")
    ax1.annotate(
        r"$\phi_0\simeq\bar M_{\rm Pl}$" + "\n" + r"$2.435\times10^{18}$ GeV",
        (0, phi0),
        xytext=(0.12, 2.3e17),
        textcoords="data",
        ha="left",
        va="top",
        fontsize=11.0,
        arrowprops={"arrowstyle": "->", "color": P.LEVEL_A_EDGE, "lw": 1.3},
        bbox={"boxstyle": "round,pad=.25", "fc": P.LEVEL_A_FILL, "ec": P.LEVEL_A_EDGE},
    )
    ax1.annotate(
        r"$v_2=246.22$ GeV" + "\nmatched; origin Open",
        (1, v2),
        xytext=(0.86, 2.4e4),
        textcoords="data",
        ha="right",
        va="bottom",
        fontsize=11.0,
        arrowprops={"arrowstyle": "->", "color": P.EXTERNAL_EDGE, "lw": 1.3},
        bbox={"boxstyle": "round,pad=.25", "fc": P.EXTERNAL_FILL, "ec": P.EXTERNAL_EDGE},
    )
    ax1.text(
        0.50,
        0.52,
        r"$\phi_0/v_2\simeq9.9\times10^{15}$" + "\nmechanism Open",
        transform=ax1.transAxes,
        ha="center",
        va="center",
        fontsize=11.0,
        bbox={"boxstyle": "round,pad=.30", "fc": P.OPEN_FILL, "ec": P.OPEN_EDGE},
    )
    ax1.grid(True, color=P.GRID, lw=0.75)

    ax2.plot(masses, r_kpc, color=P.HRC0, lw=2.6, ls="-", label="conditional HRC matching identity")
    ax2.scatter([m_ref], [r_ref], s=105, color=P.NFW, edgecolor=P.INK, marker="D", zorder=3, label="declared reference mass")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"baryonic mass $M_{\rm bar}$ [$M_\odot$]")
    ax2.set_ylabel(r"conditional matching length $L_{\rm gal}=r_*$ [kpc]")
    ax2.set_title("(b) Conditional HRC matching length", loc="left", weight="bold")
    ax2.annotate(
        r"$M_{\rm bar}=10^{10}M_\odot$" + "\n" + rf"$r_*={r_ref:.1f}$ kpc",
        (m_ref, r_ref),
        xytext=(1.7e10, r_ref / 2.4),
        textcoords="data",
        ha="left",
        va="top",
        fontsize=11.0,
        arrowprops={"arrowstyle": "->", "color": P.NFW, "lw": 1.3},
        bbox={"boxstyle": "round,pad=.25", "fc": P.TENSION_FILL, "ec": P.TENSION_EDGE},
    )
    ax2.text(
        0.035,
        0.95,
        r"$r_*=\sqrt{G_NM_{\rm bar}/a_{M0}}$" + "\n" + r"$a_{M0}=1.0824\times10^{-10}$ m s$^{-2}$ (matched)",
        transform=ax2.transAxes,
        ha="left",
        va="top",
        fontsize=11.2,
        bbox={"boxstyle": "round,pad=.28", "fc": P.LEVEL_C_FILL, "ec": P.LEVEL_C_EDGE},
    )
    ax2.text(0.035, 0.06, "No common GeV axis\nNo RG link claimed", transform=ax2.transAxes, ha="left", va="bottom", fontsize=10.8, color=P.GRAPHITE)
    ax2.grid(True, color=P.GRID, lw=0.75)
    ax2.legend(loc="lower right", frameon=True, edgecolor=P.GRAPHITE)
    save(fig, out, color, "R123 readable dimensionally separated scale inventory")
    return {
        "phi0_GeV": phi0,
        "v2_GeV": v2,
        "a_M0": a_m0,
        "r_ref_kpc": r_ref,
        "points": 300,
        "layout_only": "two stacked full-width panels",
    }


def build_ontology(out: Path, color: Path) -> dict:
    """Same seven nodes and seven directed edges in a readable portrait map."""
    configure()
    fig = plt.figure(figsize=(6.20, 8.40))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis("off")
    ax.text(5, 12.55, "Status-guarded full/reduced-description map", ha="center", va="center", fontsize=12.2, weight="bold")
    ax.text(5, 12.15, "Status is explicit; border style and luminance remain redundant.", ha="center", va="center", fontsize=10.8, color=P.GRAPHITE)

    status_box(ax, (5, 10.90), 7.4, 1.20, "Full condensate candidate description", "interacting OS/unitarity completion", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--")
    status_box(ax, (5, 8.95), 7.4, 1.20, "Declared resolved/unresolved split", "physical vertices + state + protocol required", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "SUPPLIED SPLIT")
    status_box(ax, (2.55, 6.65), 4.45, 1.55, "Coherence-retaining channel", r"small $\Phi_{ab}$ for declared" + "\ncomparisons", P.LEVEL_B_FILL, P.LEVEL_B_EDGE, "CONDITIONAL", "-.")
    status_box(ax, (7.45, 6.65), 4.45, 1.55, "Record-forming channel", r"large $\Phi_{ab}$ for declared" + "\ncomparisons", P.LEVEL_B_FILL, P.LEVEL_B_EDGE, "CONDITIONAL", "-.")
    status_box(ax, (5.00, 4.65), 7.40, 1.35, "Gravity mediator / GIE", "own vertex and channel required", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--")
    status_box(ax, (3.05, 2.65), 5.25, 1.45, "No universal transition", r"no metric-signature or ontology" + "\n" + r"jump from $\Phi_{ab}$", P.TENSION_FILL, P.TENSION_EDGE, "NO-GO GUARD", title_size=11.0)
    status_box(ax, (7.72, 2.65), 3.55, 1.45, "Unique outcome / update", "OP-Q19", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--", title_size=10.8)

    arrow(ax, (5, 10.28), (5, 9.57))
    arrow(ax, (5, 8.33), (2.55, 7.44))
    arrow(ax, (5, 8.33), (7.45, 7.44))
    arrow(ax, (5, 8.33), (5, 5.34), dashed=True)
    arrow(ax, (2.55, 5.86), (3.05, 3.39))
    routed_arrow(ax, [(7.25, 5.86), (0.55, 5.55), (0.55, 3.58), (1.00, 3.39)])
    routed_arrow(ax, [(7.70, 5.86), (9.72, 5.55), (9.72, 3.58), (8.78, 3.39)], dashed=True)
    ax.text(5, 1.25, "Solid arrows: declared reduction/guard.  Dashed arrows: Open branch.", ha="center", fontsize=10.8, color=P.INK)
    ax.text(5, 0.78, "The map classifies supplied, conditional, Open, or ruled-out steps;", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 0.42, "it does not add a metric-signature, gravity-mediator, or outcome theorem.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    save(fig, out, color, "R123 readable status-guarded full/reduced ontology map")
    return {"nodes": 7, "edges": 7, "topology_preserved": True, "text_preserved": True}


def build_qm_compare(out: Path, color: Path) -> dict:
    """Same five-row comparison; portrait physical width prevents 0.58 scaling."""
    configure()
    fig = plt.figure(figsize=(6.20, 9.10))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14.2)
    ax.axis("off")
    ax.text(5, 13.88, "Status-sensitive comparison", ha="center", fontsize=12.4, weight="bold")
    ax.text(5, 13.52, "Standard quantum mechanics versus the current ECT programme", ha="center", fontsize=10.8, color=P.GRAPHITE)
    status_box(ax, (2.55, 12.72), 4.55, 0.92, "Standard quantum mechanics", "external comparison column", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "EXTERNAL", title_size=11.2)
    status_box(ax, (7.45, 12.72), 4.55, 0.92, "Euclidean Condensate Theory", "status-sensitive programme", P.LEVEL_B_FILL, P.LEVEL_B_EDGE, "MIXED STATUS", "-.", title_size=11.2)

    left = [
        ("Cauchy initial-value problem", "wavefunction at initial time given;\nevolve forward"),
        (r"$i\hbar\,\partial_t\psi=H\psi$", "Schrödinger / Dirac equation"),
        (r"$|\psi|^2$: Born rule", "fundamental axiom"),
        ("Time: fundamental coordinate", "Lorentzian spacetime a priori"),
        ("Measurement / update rule", "textbook formulations;\ninterpretations differ"),
    ]
    right = [
        ("Specified BVP / ensemble", "existence / uniqueness /\nselection Open", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--"),
        (r"$\delta^{AB}\partial_A\partial_B\Phi-V'(\Phi)=0$", "Euclidean condensate equation", P.LEVEL_A_FILL, P.LEVEL_A_EDGE, "MODEL-INTERNAL", "-"),
        ("Born probability /\nphysical weights", "Gleason represents a supplied measure;\nreconstruction/outcome Open", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--"),
        ("P4 supplies an\nordered direction", "scalar signature needs supplied\ncoefficients; cones Open", P.LEVEL_B_FILL, P.LEVEL_B_EDGE, "CONDITIONAL", "-."),
        ("Measurement / outcome map", "decoherence alone does not\nselect outcome", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--"),
    ]
    ys = [10.95, 8.75, 6.55, 4.35, 2.15]
    for y, (title, body) in zip(ys, left):
        status_box(ax, (2.55, y), 4.55, 1.55, title, body, P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "EXTERNAL", title_size=10.8, body_size=10.8)
    for y, (title, body, fill, edge, status, ls) in zip(ys, right):
        if "\n" in title:
            status_box(
                ax,
                (7.45, y),
                4.55,
                1.55,
                title,
                body,
                fill,
                edge,
                status,
                ls,
                title_size=10.2,
                body_size=10.2,
                title_y=0.27,
                body_y=-0.12,
                status_y=-0.38,
            )
        else:
            status_box(ax, (7.45, y), 4.55, 1.55, title, body, fill, edge, status, ls, title_size=10.8, body_size=10.8)
    ax.plot([5, 5], [1.28, 13.22], color=P.GRAPHITE, ls="--", lw=1.0)
    ax.text(5, 0.78, "Scientific status is written explicitly and remains redundant", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 0.42, "with luminance and border style.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    save(fig, out, color, "R123 readable status-sensitive ECT versus standard-QM comparison")
    return {"rows": 5, "scientific_text_preserved": True, "status_mapping_preserved": True}


def build_common_response(out: Path, color: Path) -> dict:
    """Same six-node/eight-link Open programme, with four readable columns."""
    configure()
    fig = plt.figure(figsize=(6.20, 5.95))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    ax.text(5, 9.30, "Open common-response programme", ha="center", fontsize=12.4, weight="bold")
    ax.text(5, 8.91, "All four response targets remain Open.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 8.57, "Dashed links show conceptual continuity only.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    status_box(ax, (5, 7.55), 5.8, 1.12, "Ordered coherent vacuum", "programme-level structural input", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "STRUCTURAL INPUT")

    channels = [
        (1.30, "Boundary\nresponse", "Casimir"),
        (3.75, "Time-dependent\nresponse", "particle production"),
        (6.25, "Observer\nresponse", "Unruh"),
        (8.70, "Strong-field\ninterface", "Hawking / horizon"),
    ]
    for x, title, body in channels:
        status_box(
            ax,
            (x, 5.25),
            2.15,
            1.58,
            title,
            body,
            P.OPEN_FILL,
            P.OPEN_EDGE,
            "EXTERNAL TARGET",
            "--",
            title_size=10.2,
            body_size=10.2,
            status_size=9.7,
            title_y=0.27,
            body_y=-0.08,
            status_y=-0.38,
        )
        arrow(ax, (5, 6.98), (x, 6.06), dashed=True)

    status_box(ax, (5, 2.55), 6.25, 1.14, "Analogue-gravity continuity", "motivation and comparison only", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "EXTERNAL MOTIVATION")
    for x, _, _ in channels:
        arrow(ax, (x, 4.44), (5, 3.14), dashed=True)
    ax.text(5, 1.40, "No common physical bundle, state, continuation, or coupling has been derived.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 1.01, "Mechanism names and explicit status labels—not hue—", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 0.67, "distinguish the four targets.", ha="center", fontsize=10.8, color=P.GRAPHITE)
    save(fig, out, color, "R123 readable Open common-response programme")
    return {"nodes": 6, "edges": 8, "channels": 4, "all_links": "dashed/open", "status_preserved": True}


def build_tensor_bridge(out: Path, color: Path) -> dict:
    """Exact four-box owner chain with bounded physical width and larger type."""
    configure()
    fig = plt.figure(figsize=(6.20, 6.25))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9.2)
    ax.axis("off")
    ax.text(5, 8.83, "Tensor-normalisation bridge remains Open", ha="center", fontsize=12.4, weight="bold")
    ax.text(5, 8.43, r"The established chain ends at $\kappa_n$; dimensional equality supplies neither", ha="center", fontsize=10.8, color=P.GRAPHITE)
    ax.text(5, 8.07, "helicity-2 dynamics nor a static-density vertex.", ha="center", fontsize=10.8, color=P.GRAPHITE)

    status_box(ax, (5, 6.85), 8.6, 1.05, r"Orientation coefficient $\mathcal{C}_n$", "conditional; matching Open", P.LEVEL_B_FILL, P.LEVEL_B_EDGE, "CONDITIONAL", "-.")
    status_box(ax, (5, 5.25), 8.6, 1.05, r"Orientation stiffness $\kappa_n$", r"$\kappa_n\equiv\mathcal{C}_nu_0^2$ -- exact EFT definition", P.LEVEL_A_FILL, P.LEVEL_A_EDGE, "LEVEL A")
    status_box(ax, (5, 3.65), 8.6, 1.05, r"Physical tensor scale $M_G$", r"$M_G^2\;?=\;c_M\kappa_n$ -- TT owner/source missing", P.OPEN_FILL, P.OPEN_EDGE, "OPEN", "--")
    status_box(ax, (5, 2.05), 8.6, 1.05, r"Newton constant $G_N$", r"$G_N=c_{\rm char}^4/(8\pi M_G^2)$ -- external supplied completion", P.EXTERNAL_FILL, P.EXTERNAL_EDGE, "EXTERNAL")
    arrow(ax, (5, 6.31), (5, 5.79))
    ax.text(5.30, 6.05, "definition", ha="left", va="center", fontsize=10.8, color=P.INK)
    arrow(ax, (5, 4.71), (5, 4.19), dashed=True)
    ax.text(5.30, 4.45, r"Open: $c_M$ + tensor owner", ha="left", va="center", fontsize=10.8, color=P.OPEN_EDGE)
    arrow(ax, (5, 3.11), (5, 2.59))
    ax.text(5.30, 2.85, "standard weak-field matching", ha="left", va="center", fontsize=10.8, color=P.INK)
    handles = [
        Patch(facecolor=P.LEVEL_A_FILL, edgecolor=P.LEVEL_A_EDGE, label="exact EFT definition"),
        Patch(facecolor=P.LEVEL_B_FILL, edgecolor=P.LEVEL_B_EDGE, linestyle="-.", label="conditional input"),
        Patch(facecolor=P.OPEN_FILL, edgecolor=P.OPEN_EDGE, linestyle="--", label="Open / missing owner"),
        Patch(facecolor=P.EXTERNAL_FILL, edgecolor=P.EXTERNAL_EDGE, label="external completion"),
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=10.8, bbox_to_anchor=(0.5, 0.01))
    save(fig, out, color, "R123 readable tensor-normalisation open bridge")
    return {"nodes": 4, "edges": 3, "chain_preserved": True, "status_preserved": True}


BUILDERS = {
    "fig_condensate_scales_r123.pdf": build_scales,
    "fig_two_level_ontology_r123.pdf": build_ontology,
    "fig_ect_vs_qm_r123.pdf": build_qm_compare,
    "fig_qs_vacuum_unified_r123.pdf": build_common_response,
    "fig41_b_tensor_normalisation_open_bridge_r123.pdf": build_tensor_bridge,
}

OWNER_PATHS = {
    "fig_condensate_scales_r123.pdf": [
        LATEX / "scripts/fig3_condensate_scales.py",
        R123_V1 / "components/global_visual_remediation/scripts/build_r123_remaining_monochrome.py",
    ],
    "fig_two_level_ontology_r123.pdf": [
        LATEX / "scripts/fig_two_level_ontology.gv",
        R123_V1 / "components/global_visual_remediation/scripts/build_r123_remaining_monochrome.py",
    ],
    "fig_ect_vs_qm_r123.pdf": [
        LATEX / "scripts/render_fig_ect_vs_qm.py",
        LATEX / "figures/source/svg/fig_ect_vs_qm.svg",
        R123_V1 / "components/global_visual_remediation/scripts/build_r123_remaining_monochrome.py",
    ],
    "fig_qs_vacuum_unified_r123.pdf": [
        R123_V1 / "components/global_visual_remediation/scripts/build_r123_recolored_singletons.py",
    ],
    "fig41_b_tensor_normalisation_open_bridge_r123.pdf": [
        R123_V1 / "components/global_visual_remediation/p1_panel_work/scripts/build_r123_p1_panel_relayout.py",
    ],
}

UPSTREAM_KEEP = {
    "fig_pes_diagram_r123.pdf": R123_V1 / "components/core_schematics/assets/fig_pes_diagram_r123.pdf",
}

OVERLAY_PATHS = {
    "fig_condensate_scales_r123.pdf": "figures/r123/fig_condensate_scales_r123.pdf",
    "fig_two_level_ontology_r123.pdf": "figures/r123/fig_two_level_ontology_r123.pdf",
    "fig_ect_vs_qm_r123.pdf": "figures/r123/fig_ect_vs_qm_r123.pdf",
    "fig_qs_vacuum_unified_r123.pdf": "figures/r123/fig_qs_vacuum_unified_r123.pdf",
    "fig41_b_tensor_normalisation_open_bridge_r123.pdf": "figures/r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=COMPONENT)
    args = ap.parse_args()
    outroot = args.output.resolve()
    assets = outroot / "assets"
    color_dir = outroot / "previews/color"
    gray_dir = outroot / "previews/grayscale"
    payload = {}
    outputs = {}
    preview_hashes = {}

    for name, builder in BUILDERS.items():
        pdf = assets / name
        color = color_dir / name.replace(".pdf", ".png")
        payload[name] = builder(pdf, color)
        gray = gray_dir / color.name
        gray_preview(color, gray)
        outputs[name] = sha256(pdf)
        preview_hashes[str(color.relative_to(outroot))] = sha256(color)
        preview_hashes[str(gray.relative_to(outroot))] = sha256(gray)

    upstream = {}
    for name, source in UPSTREAM_KEEP.items():
        target = outroot / "references/upstream_keep" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        outputs[f"reference:{name}"] = sha256(target)
        upstream[name] = {
            "source": str(source.relative_to(WORKSPACE)),
            "source_sha256": sha256(source),
            "disposition": "KEEP: already physically narrow and readable; no replacement overlay",
        }

    owners = {
        name: [
            {"path": str(p.relative_to(WORKSPACE)), "sha256": sha256(p)}
            for p in paths
        ]
        for name, paths in OWNER_PATHS.items()
    }
    manifest = {
        "schema": "ECT-R123-targeted-readability-assets-v1",
        "status": "PROPOSAL ONLY - LIVE APPLY NOT AUTHORISED",
        "scope": "layout, line wrapping, physical page size, and luminance-first palette only",
        "preprint_textwidth_ps_pt": TEXTWIDTH_PS_PT,
        "palette_owner": {"path": str(PALETTE_PATH.relative_to(WORKSPACE)), "sha256": sha256(PALETTE_PATH)},
        "owners": owners,
        "outputs": outputs,
        "overlays": {
            name: {
                "component_asset": f"assets/{name}",
                "candidate_install_path": install_path,
                "sha256": outputs[name],
            }
            for name, install_path in OVERLAY_PATHS.items()
        },
        "preview_hashes": preview_hashes,
        "scientific_payload": payload,
        "upstream_keep": upstream,
        "runtime": {
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pillow": Image.__version__,
        },
    }
    (outroot / "R123_TARGETED_READABILITY_ASSETS_MANIFEST_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(outputs, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
