#!/usr/bin/env python3
"""Build deterministic presentation-only R149 successors for figure block B.

The script changes typography/layout only.  Scientific arrays are replayed
from the frozen JSON owners, vector crops preserve the embedded source form,
and status schematics preserve the source-owner nodes, equations and terminal
classifications.  No live publication path is written.
"""

from __future__ import annotations

import hashlib
import json
import os
import csv
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
OUT = SCRIPT.parent
ROOT = next(parent for parent in SCRIPT.parents if (parent / "ECT_preprint.tex").is_file())
LATEX = ROOT
ASSETS = OUT / "assets"

os.environ.setdefault("MPLCONFIGDIR", str(OUT / "runtime" / "mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(OUT / "runtime" / "cache"))
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784764800")

import fitz
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

FIXED_DT = datetime(2026, 7, 24, 0, 0, 0, tzinfo=timezone.utc)
PDF_META = {
    "Title": "ECT R149 reader-typography successor",
    "Author": "ECT reproducibility workflow",
    "Subject": "Presentation-only successor; scientific payload unchanged",
    "Keywords": "ECT R149 reader typography grayscale safe",
    "Creator": SCRIPT.name,
    "CreationDate": FIXED_DT,
    "ModDate": FIXED_DT,
}
FITZ_META = {
    "title": "ECT R149 reader-typography successor",
    "author": "ECT reproducibility workflow",
    "subject": "Presentation-only successor; scientific payload unchanged",
    "keywords": "ECT R149 reader typography grayscale safe",
    "creator": SCRIPT.name,
    "producer": f"PyMuPDF {fitz.VersionBind}",
    "creationDate": "D:20260724000000Z",
    "modDate": "D:20260724000000Z",
}

INK = "#222222"
GRAPHITE = "#666666"
GRID = "#D9D9D9"
PAPER = "#FFFFFF"
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
VERMILLION = "#D55E00"
PURPLE = "#6F4FA3"
BLUE_FILL = "#DCECF7"
GREEN_FILL = "#DDF2E9"
OPEN_FILL = "#FBE9C9"
FAIL_FILL = "#F5DDD7"
EXTERNAL_FILL = "#E8E8E8"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.0,
            "axes.titlesize": 12.0,
            "axes.labelsize": 10.2,
            "legend.fontsize": 9.4,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "r149-main-b-v1",
            "savefig.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRAPHITE,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )


def save_mpl(fig: plt.Figure, path: Path, tight: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"bbox_inches": "tight", "pad_inches": 0.08} if tight else {}
    fig.savefig(path, format="pdf", metadata=PDF_META, **kwargs)
    plt.close(fig)


def rounded_box(
    ax,
    xy,
    width,
    height,
    title,
    body,
    face,
    edge,
    linestyle="-",
    tag="",
    title_size=10.2,
    body_size=9.2,
    title_fraction=0.58,
    body_fraction=0.25,
):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.05",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.7,
        linestyle=linestyle,
    )
    ax.add_patch(patch)
    if tag:
        ax.text(
            x + 0.08,
            y + height - 0.14,
            tag,
            ha="left",
            va="top",
            fontsize=9.0,
            weight="bold",
            color=edge,
        )
    ax.text(
        x + width / 2,
        y + height * title_fraction,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        weight="bold",
    )
    ax.text(
        x + width / 2,
        y + height * body_fraction,
        body,
        ha="center",
        va="center",
        fontsize=body_size,
        linespacing=1.12,
    )


def render_mediator() -> dict:
    configure()
    fig, ax = plt.subplots(figsize=(6.5, 5.8))
    ax.set(xlim=(0, 10), ylim=(0, 9.2))
    ax.axis("off")
    ax.text(5, 8.85, "47C necessary-screen summary", ha="center", fontsize=13.0, weight="bold")
    ax.text(
        5,
        8.48,
        "10 detailed ledger rows -> 7 reader-facing families -> 0 identified physical PES channels",
        ha="center",
        fontsize=8.9,
        color=VERMILLION,
        weight="bold",
    )
    rounded_box(
        ax,
        (0.35, 6.55),
        9.3,
        1.42,
        "Necessary gates (passing them is not sufficient by itself)",
        "action + declared split -> constrained, canonically normalised modes\n"
        "-> physical vertex/projector -> physical state + retarded/noise kernels\n"
        "-> finite pairwise record functional",
        GREEN_FILL,
        "#397A54",
        "-.",
        "NECESSARY SCREEN",
        10.0,
        9.0,
    )
    rounded_box(
        ax,
        (0.35, 4.56),
        4.45,
        1.50,
        "Missing physical vertex",
        "linear director; mixed channel",
        OPEN_FILL,
        ORANGE,
        "--",
        "MISSING VERTEX",
    )
    rounded_box(
        ax,
        (5.20, 4.56),
        4.45,
        1.50,
        "Not identifiable",
        "scalar trace; HRC/static;\nindependent tensor; mixed",
        OPEN_FILL,
        GRAPHITE,
        ":",
        "OPEN INPUTS",
    )
    rounded_box(
        ax,
        (0.35, 2.18),
        4.45,
        2.08,
        "Scoped incompatibility",
        "minimal director composite\n"
        "tested vacuum/thermal only\ngeneral channel:\nNOT IDENTIFIABLE",
        FAIL_FILL,
        VERMILLION,
        "-.",
        "TESTED SCOPE ONLY",
        body_size=9.0,
        title_fraction=0.65,
        body_fraction=0.34,
    )
    rounded_box(
        ax,
        (5.20, 2.18),
        4.45,
        2.08,
        "Conditional double counting",
        "integrated radial mode needs\nnew Wilsonian split,\n"
        "subtraction and counterterms\nproved before reuse",
        FAIL_FILL,
        "#8C3B2A",
        "--",
        "SPLIT REQUIRED",
        title_size=9.5,
        body_size=9.0,
        title_fraction=0.65,
        body_fraction=0.34,
    )
    ax.text(
        5,
        1.82,
        "The seven-family graphic aggregates - and does not replace - the detailed ten-row ledger.",
        ha="center",
        fontsize=9.1,
        color=GRAPHITE,
    )
    ax.text(
        5,
        1.46,
        "Static HRC compliance is a response, not a PES noise kernel;",
        ha="center",
        fontsize=9.1,
        color=INK,
    )
    ax.text(
        5,
        1.17,
        "imported D-P numbers are external Level C.",
        ha="center",
        fontsize=9.1,
        color=INK,
    )
    handles = [
        Patch(facecolor=OPEN_FILL, edgecolor=ORANGE, linestyle="--", label="missing physical vertex"),
        Patch(facecolor=OPEN_FILL, edgecolor=GRAPHITE, linestyle=":", label="not identifiable / Open inputs"),
        Patch(facecolor=FAIL_FILL, edgecolor=VERMILLION, linestyle="-.", label="incompatible in tested scope"),
        Patch(facecolor=FAIL_FILL, edgecolor="#8C3B2A", linestyle="--", label="double counting unless split proved"),
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=8.9, bbox_to_anchor=(0.5, 0.015))
    out = ASSETS / "r149_mediator_channels_summary_47C.pdf"
    save_mpl(fig, out)
    source = (
        LATEX
        / "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1/"
        "components/core_schematics/build_core_schematics.py"
    )
    return {
        "id": "mediator_channels_summary_47C",
        "output": str(out.relative_to(ROOT)),
        "output_sha256": sha(out),
        "source_owners": {str(source.relative_to(ROOT)): sha(source)},
        "scientific_payload": "same necessary gates, four terminal classes, qualifications and legend; layout/type only",
    }


def hierarchy_box(ax, key, nodes, x, y, w, h, lines, status, fill, edge):
    nodes[key] = (x, y, w, h)
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.10",
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.5,
        )
    )
    ax.text(x, y + 0.10, "\n".join(lines), ha="center", va="center", fontsize=11.4, linespacing=1.16)
    ax.text(
        x,
        y - h / 2 + 0.12,
        status,
        ha="center",
        va="bottom",
        fontsize=9.3,
        color=GRAPHITE,
        fontstyle="italic",
    )


def hierarchy_arrow(ax, nodes, src, dst, label):
    x0, y0, _, h0 = nodes[src]
    x1, y1, _, h1 = nodes[dst]
    ys, yd = y0 - h0 / 2, y1 + h1 / 2
    ax.annotate(
        "",
        xy=(x1, yd),
        xytext=(x0, ys),
        arrowprops=dict(arrowstyle="-|>", color=GRAPHITE, lw=1.7, linestyle=(0, (4, 2.5))),
    )
    ax.text(x0 + 0.18, (ys + yd) / 2, label, fontsize=9.3, ha="left", va="center", color=GRAPHITE, fontstyle="italic")


def render_hierarchy() -> dict:
    configure()
    fig, ax = plt.subplots(figsize=(6.5, 8.6))
    ax.set(xlim=(0, 7), ylim=(0, 9))
    ax.axis("off")
    nodes = {}
    hierarchy_box(
        ax,
        "L0",
        nodes,
        3.5,
        8.2,
        5.7,
        1.0,
        [r"$\delta^{AB}\partial_A\partial_B\Phi - V'(\Phi)=0$", "Euclidean condensate equation"],
        "Level 0: supplied bare scalar model",
        BLUE_FILL,
        BLUE,
    )
    hierarchy_box(
        ax,
        "L1",
        nodes,
        3.5,
        6.1,
        5.7,
        1.18,
        [
            r"$K^{AB}\partial_A\partial_B\chi + m_\sigma^2\chi=0$",
            r"$K^{AB}=\beta\delta^{AB}-\alpha n^A n^B$",
            "Ordered-branch scalar equation",
        ],
        "Level 1: supplied P4 / EFT closure",
        GREEN_FILL,
        GREEN,
    )
    hierarchy_box(
        ax,
        "L2",
        nodes,
        3.5,
        4.0,
        5.7,
        1.0,
        [r"$\partial_t^2\varphi-c_*^2\nabla^2\varphi+M^2\varphi=0$", "conditional scalar Klein-Gordon form"],
        "Level 2: clock / physical-state map Open",
        OPEN_FILL,
        ORANGE,
    )
    hierarchy_box(
        ax,
        "L3",
        nodes,
        3.5,
        1.9,
        5.7,
        1.0,
        [r"$iS_0\partial_t\psi=-\frac{S_0^2}{2m}\nabla^2\psi+V\psi$", "conditional Schrödinger-type envelope"],
        "Level 3: state / operator / $S_0$ owners Open",
        FAIL_FILL,
        VERMILLION,
    )
    hierarchy_arrow(ax, nodes, "L0", "L1", r"P4 supplies $O(4)\to O(3)$ branch")
    hierarchy_arrow(ax, nodes, "L1", "L2", "conditional coordinate / cone map")
    hierarchy_arrow(ax, nodes, "L2", "L3", "state + positive-frequency + NR assumptions")
    ax.text(
        3.5,
        0.55,
        "Dashed arrows are conditional dependencies, not status upgrades.",
        ha="center",
        fontsize=9.4,
        color=GRAPHITE,
    )
    out = ASSETS / "r149_equation_hierarchy.pdf"
    save_mpl(fig, out)
    source = LATEX / "scripts/fig_equation_hierarchy.py"
    return {
        "id": "equation_hierarchy",
        "output": str(out.relative_to(ROOT)),
        "output_sha256": sha(out),
        "source_owners": {str(source.relative_to(ROOT)): sha(source)},
        "scientific_payload": "same four levels, equations, statuses and three conditional arrows; typography/palette only",
    }


def crop_ect_vs_qm() -> dict:
    source = LATEX / "figures/r134/fig_ect_vs_qm_r134.pdf"
    src = fitz.open(source)
    clip = fitz.Rect(22, 0, 658, 420) & src[0].rect
    outdoc = fitz.open()
    page = outdoc.new_page(width=clip.width, height=clip.height)
    page.show_pdf_page(page.rect, src, 0, clip=clip, keep_proportion=True)
    outdoc.set_metadata(FITZ_META)
    out = ASSETS / "r149_ect_vs_qm_reader_crop.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    outdoc.save(out, garbage=4, clean=True, deflate=True, no_new_id=True)
    outdoc.close()
    src.close()
    owner = LATEX / "figures/source/svg/r134/fig_ect_vs_qm.svg"
    generator = LATEX / "scripts/r134_graphs/render_fig_ect_vs_qm.py"
    return {
        "id": "ect_vs_qm",
        "output": str(out.relative_to(ROOT)),
        "output_sha256": sha(out),
        "source_owners": {
            str(source.relative_to(ROOT)): sha(source),
            str(owner.relative_to(ROOT)): sha(owner),
            str(generator.relative_to(ROOT)): sha(generator),
        },
        "scientific_payload": "exact embedded source form; symmetric white-margin crop only",
        "clip": [22, 0, 658, 420],
    }


def crop_axis_successor(
    *,
    ident: str,
    source_rel: str,
    source_sha: str,
    clip_tuple: tuple[float, float, float, float],
    header: str,
    footer: str,
    output_name: str,
) -> dict:
    source = LATEX / source_rel
    if sha(source) != source_sha:
        raise RuntimeError(f"frozen source mismatch: {source}")
    src = fitz.open(source)
    clip = fitz.Rect(*clip_tuple) & src[0].rect
    width, margin, header_h, footer_h = 468.0, 18.0, 23.0, 38.0
    target_w = width - 2 * margin
    scale = target_w / clip.width
    target_h = clip.height * scale
    doc = fitz.open()
    page = doc.new_page(width=width, height=margin + header_h + target_h + footer_h + margin)
    # Reuse a standard PDF font only for the presentation-only added strings.
    page.insert_textbox(
        fitz.Rect(margin, margin, width - margin, margin + header_h),
        header,
        fontname="helv",
        fontsize=11.0,
        color=(0.13, 0.13, 0.13),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    target = fitz.Rect(margin, margin + header_h, width - margin, margin + header_h + target_h)
    page.show_pdf_page(target, src, 0, clip=clip, keep_proportion=True)
    rc = page.insert_textbox(
        fitz.Rect(margin, target.y1 + 4, width - margin, target.y1 + footer_h),
        footer,
        fontname="helv",
        fontsize=9.5,
        color=(0.28, 0.28, 0.28),
        align=fitz.TEXT_ALIGN_CENTER,
    )
    if rc < 0:
        raise RuntimeError(f"footer does not fit: {ident}")
    doc.set_metadata(FITZ_META)
    out = ASSETS / output_name
    doc.save(out, garbage=4, clean=True, deflate=True, no_new_id=True)
    doc.close()
    src.close()
    generator = LATEX / "scripts/figures/build_r148_readable_axis_successors.py"
    return {
        "id": ident,
        "output": str(out.relative_to(ROOT)),
        "output_sha256": sha(out),
        "source_owners": {
            str(source.relative_to(ROOT)): sha(source),
            str(generator.relative_to(ROOT)): sha(generator),
        },
        "scientific_payload": "exact embedded frozen panel form; expanded crop retained; header/footer enlarged only",
        "clip": list(clip_tuple),
    }


def render_rare_tail() -> dict:
    """Re-render the frozen R113 two-curve payload at readable publication scale."""
    configure()
    source = LATEX / "data/cosmology_r113/R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv"
    rows = []
    with source.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append({key: float(value) for key, value in row.items()})
    rows.sort(key=lambda row: row["zeta_ER"])
    zeta = np.asarray([row["zeta_ER"] for row in rows], dtype=float)
    fixed = np.asarray([row["cumulative_PS_ratio_nu5_fixed_barrier"] for row in rows], dtype=float)
    tophat = np.asarray([row["cumulative_PS_ratio_nu5_tophat_barrier"] for row in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(6.5, 5.75), constrained_layout=True)
    ax.plot(
        zeta,
        fixed,
        color=GREEN,
        marker="^",
        linestyle="-.",
        linewidth=2.0,
        markersize=6.2,
        label=r"fixed barrier, $\nu_0=5$",
    )
    ax.plot(
        zeta,
        tophat,
        color=PURPLE,
        marker="D",
        markerfacecolor=PAPER,
        markeredgewidth=1.5,
        linestyle=":",
        linewidth=2.2,
        markersize=5.7,
        label=r"top-hat barrier, $\nu_0=5$",
    )
    ax.axhline(1.0, color=GRAPHITE, linewidth=1.1, linestyle="--", label="control")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both", color=GRID, linewidth=0.7)
    ax.set(
        xlabel=r"early-response coordinate $\zeta_{\rm ER}$",
        ylabel="cumulative Press–Schechter sensitivity ratio",
        title="Rare-tail sensitivity under two declared collapse barriers",
    )
    ax.legend(frameon=False, loc="upper left", fontsize=9.5)
    ax.text(
        0.985,
        0.035,
        "Level C sensitivity envelope; not a posterior,\nJWST prediction, or cosmological likelihood.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.4,
        color=INK,
        bbox=dict(facecolor=OPEN_FILL, edgecolor=ORANGE, boxstyle="round,pad=0.26"),
    )
    out = ASSETS / "r149_rare_tail.pdf"
    save_mpl(fig, out)
    original = LATEX / "figures/r114/r114_early_response_growth_collapse_envelope.pdf"
    generator = LATEX / "scripts/figures/make_r114_closure_figures.py"
    owners = {
        str(source.relative_to(ROOT)): sha(source),
        str(original.relative_to(ROOT)): sha(original),
    }
    if generator.exists():
        owners[str(generator.relative_to(ROOT))] = sha(generator)
    return {
        "id": "rare_tail",
        "output": str(out.relative_to(ROOT)),
        "output_sha256": sha(out),
        "source_owners": owners,
        "scientific_payload": (
            "exact replay of both frozen R113 cumulative Press-Schechter sensitivity arrays; "
            "typography/palette only"
        ),
        "array_payload": {
            "zeta_ER": zeta.tolist(),
            "fixed_barrier_nu5": fixed.tolist(),
            "tophat_barrier_nu5": tophat.tolist(),
        },
    }


def render_restricted() -> dict:
    configure()
    data_root = LATEX / "data/cosmology_r103"
    p_bg = data_root / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json"
    p_isw = data_root / "R103_RESTRICTED_ISW_LENSING_PROXY_v1.json"
    p_flow = data_root / "R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json"
    bg = json.loads(p_bg.read_text())
    isw = json.loads(p_isw.read_text())
    flow = json.loads(p_flow.read_text())
    brow = {float(r["z"]): r for r in bg["rows"]}
    rows = isw["rows_primary"]
    z = np.asarray([r["z"] for r in rows], dtype=float)
    dz = np.asarray([brow[float(v)]["delta_D_percent"] for v in z])
    q = np.asarray([r["delta_Q_W_percent"] for r in rows])
    deriv = np.asarray([r["delta_S_ISW_proxy_percent"] for r in rows])
    frow = {float(r["z"]): r for r in flow["rows"]}
    vel = np.asarray([frow[float(v)]["delta_velocity_carrier_percent"] for v in z])
    velp = np.asarray([frow[float(v)]["delta_velocity_power_carrier_percent"] for v in z])

    fig, ax = plt.subplots(figsize=(6.5, 5.45), constrained_layout=True)
    ax.plot(z, dz, color=BLUE, marker="o", ls="-", lw=2.0, label=r"growth amplitude $D$")
    ax.plot(z, q, color=GREEN, marker="s", ls="--", lw=2.0, label=r"Weyl carrier $Q_W$")
    ax.plot(z, deriv, color=PURPLE, marker="^", ls="-.", lw=2.0, label=r"derivative carrier $S_{\rm ISW}^{\rm proxy}$")
    ax.plot(z, vel, color=INK, marker="D", markerfacecolor=PAPER, ls=":", lw=2.0, label=r"velocity carrier $aHfD$")
    ax.plot(z, velp, color=VERMILLION, marker="v", ls=(0, (5, 2, 1, 2)), lw=2.0, label="velocity-power carrier")
    ax.axhline(0, color=INK, lw=0.9)
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set(
        xlabel="redshift $z$",
        ylabel="model/control difference [%]",
        title="Restricted near-GR perturbation carriers",
    )
    ax.legend(frameon=False, fontsize=9.6, ncol=2, loc="upper left")
    ax.text(
        0.01,
        0.018,
        "Level C: same metric, zero slip, sub-horizon; not projected spectra",
        transform=ax.transAxes,
        fontsize=9.4,
        bbox=dict(facecolor=EXTERNAL_FILL, edgecolor=GRAPHITE, boxstyle="round,pad=0.24"),
    )
    out = ASSETS / "r149_restricted_perturbation_proxies.pdf"
    save_mpl(fig, out)
    owner = (
        LATEX
        / "provenance/figures/r190/work_preprint/"
        "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1/"
        "components/global_visual_remediation/p1_panel_work/scripts/build_r123_p1_panel_relayout.py"
    )
    return {
        "id": "restricted_perturbation_proxies",
        "output": str(out.relative_to(ROOT)),
        "output_sha256": (
            sha(out) if out.is_file() else "CAPTURED_BY_DOWNSTREAM_RENDERER"
        ),
        "source_owners": {
            str(p_bg.relative_to(ROOT)): sha(p_bg),
            str(p_isw.relative_to(ROOT)): sha(p_isw),
            str(p_flow.relative_to(ROOT)): sha(p_flow),
            str(owner.relative_to(ROOT)): sha(owner),
        },
        "scientific_payload": "exact replay of the five frozen R103 carrier arrays; typography/palette only",
        "array_payload": {
            "z": z.tolist(),
            "growth": dz.tolist(),
            "weyl": q.tolist(),
            "derivative": deriv.tolist(),
            "velocity": vel.tolist(),
            "velocity_power": velp.tolist(),
        },
    }


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    records = [
        render_mediator(),
        render_hierarchy(),
        crop_ect_vs_qm(),
        crop_axis_successor(
            ident="inverse_f_proxy",
            source_rel="figures/r103/r103_two_slope_HwG_conditional.pdf",
            source_sha="c35d151ef30c27c65acc2721212bfde91dedd98701b36d2b7fa3dc545bbff6ad",
            clip_tuple=(492.0, 20.0, 742.7995, 299.7),
            header="Conditional two-slope state; no common-epsilon law",
            footer=(
                "Level A only inside the supplied action/state; Level C observable diagnostic;\n"
                "not a unique P1-P6 cosmology."
            ),
            output_name="r149_inverse_f_proxy.pdf",
        ),
        render_rare_tail(),
        render_restricted(),
    ]
    manifest = {
        "schema": "ECT-R149-main-b-successors-v1",
        "script": str(SCRIPT.relative_to(ROOT)),
        "script_sha256": sha(SCRIPT),
        "live_manuscript_edited": False,
        "records": records,
    }
    (OUT / "R149_MAIN_B_SUCCESSOR_MANIFEST_v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({r["id"]: r["output_sha256"] for r in records}, indent=2))


if __name__ == "__main__":
    main()
