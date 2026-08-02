#!/usr/bin/env python3
"""Build R149 print-typography successors from frozen R103 owners.

This producer is deliberately proposal-only.  It reads the immutable R103
background/observable products and writes only inside the R123 component.  It
does not infer a trajectory through the condensate-formation front, a local
Newton constant, a universal P1--P6 cosmology, or a spherical outer boundary.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np


SCRIPT = Path(__file__).resolve()
COMPONENT = SCRIPT.parents[1]


def find_workspace_root() -> Path:
    for parent in SCRIPT.parents:
        if (parent / "ECT_preprint.tex").is_file():
            return parent
    raise RuntimeError("ECT workspace root not found")


ROOT = find_workspace_root()
DATA = ROOT / "data/cosmology_r103"
OUT = COMPONENT / "outputs"
# Preserve the immutable R123 palette owner; this successor changes only
# typography and page geometry, never numeric inputs or status semantics.
PALETTE_DIR = (
    ROOT
    / "provenance/figures/r190/work_preprint/"
    "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1/scripts"
)
sys.path.insert(0, str(PALETTE_DIR))
import r123_palette as palette  # noqa: E402

INPUTS = {
    "dense": (
        DATA / "R103_TWO_SLOPE_BACKGROUND_DENSE_v1.csv",
        "03c9c3e7894e3b0f5b258ba0275abdf76faf80083223fe46f44727c25ebcfe56",
    ),
    "observables": (
        DATA / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.csv",
        "67d87a0dd709d7816a21ec375ab7e1827c1ce367256e536804e1a26e194edff6",
    ),
    "observables_json": (
        DATA / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json",
        "7ab8fb98486fbd9a4a80e0c2777f666bc455a26c8f3d9bb0c6d19aa4217f151f",
    ),
    "chronometer": (
        DATA / "R103_OFFICIAL_CCCOVARIANCE_SUBSET_RESULT_v1.json",
        "e1f9969194e94ec1f186d34e236595883e6e48ee9052cdf8dc7a1d88e14e3776",
    ),
    "age_matching": (
        DATA / "R103_CONDITIONAL_ECT_AGE_MATCHING_RESULTS_v1.json",
        "e967d42e2013970576c831d05baf9baf54c68c744e9882081298136a29a3bc5a",
    ),
    "dense_metadata": (
        DATA / "R103_TWO_SLOPE_BACKGROUND_DENSE_METADATA_v1.json",
        "94bc139e3f76701a9f7cee574d20e8d2e7cbed4bf174a8206e3191e6faeff6da",
    ),
}


# Canonical shared R123 luminance-first palette.  Colour is reinforced by
# marker, line and border style; no hatch is used as a primary encoding.
INK = palette.INK
BLUE = palette.LEVEL_A_EDGE
GREEN = palette.LEVEL_B_EDGE
AMBER = palette.LEVEL_C_EDGE
OPEN = palette.OPEN_EDGE
RED = palette.TENSION_EDGE
GRAY = palette.GRAPHITE
PALE_BLUE = palette.LEVEL_A_FILL
PALE_GREEN = palette.LEVEL_B_FILL
PALE_AMBER = palette.LEVEL_C_FILL
PALE_OPEN = palette.OPEN_FILL
PALE_RED = palette.TENSION_FILL
PALE_GRAY = palette.EXTERNAL_FILL
WHITE = palette.PAPER

MIN_FONT_PT = 10.5
# Current R114/live branch display calibration.  The covariance-fitted
# H0=68.586... clock result is a separate Level-C calibration and must not be
# mixed into the current branch chronology.
H0_BRANCH = 67.4
HUBBLE_TIME_GYR = 977.7922216807891 / H0_BRANCH

PDF_METADATA = {
    "Title": "R149 ECT evolution typography successor",
    "Author": "ECT reproducibility workflow",
    "Subject": "Conditional post-ordering evolution and owner map",
    "Keywords": "ECT R123 R103 evolution conditional owner status",
    "Creator": "build_r149_evolution_typography_successors.py",
    "Producer": "Matplotlib",
    "CreationDate": dt.datetime(2026, 7, 24, 0, 0, tzinfo=dt.timezone.utc),
    "ModDate": dt.datetime(2026, 7, 24, 0, 0, tzinfo=dt.timezone.utc),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs() -> None:
    failures = []
    for name, (path, expected) in INPUTS.items():
        actual = sha256(path)
        if actual != expected:
            failures.append(f"{name}: expected {expected}, got {actual}")
    if failures:
        raise RuntimeError("Frozen input guard failed:\n" + "\n".join(failures))


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11.5,
            "axes.titlesize": 12.0,
            "axes.labelsize": 11.0,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10.5,
            "figure.titlesize": 14.0,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.8,
            "grid.color": "#D8DDDF",
            "grid.linewidth": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": WHITE,
        }
    )


def load_csv(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}


def assert_min_font(fig: plt.Figure) -> None:
    too_small = []
    for text in fig.findobj(match=lambda obj: hasattr(obj, "get_fontsize")):
        size = float(text.get_fontsize())
        if text.get_text() and size < MIN_FONT_PT - 1.0e-9:
            too_small.append((text.get_text()[:80], size))
    if too_small:
        raise RuntimeError(f"Text below {MIN_FONT_PT} pt: {too_small[:8]}")


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assert_min_font(fig)
    fig.savefig(
        OUT / f"{stem}.pdf",
        bbox_inches="tight",
        metadata=PDF_METADATA,
    )
    fig.savefig(
        OUT / f"{stem}.png",
        dpi=260,
        bbox_inches="tight",
        metadata={"Software": "ECT R123 deterministic visual producer"},
    )
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        0.98,
        0.98,
        label,
        transform=ax.transAxes,
        ha="right",
        va="top",
        weight="bold",
        fontsize=11.5,
    )


def conditional_post_ordering(dense: dict[str, np.ndarray], obs: dict[str, np.ndarray]) -> None:
    # A 7.7-in width inserted at the live A4 text width (~6.30 in) keeps the
    # 10.5-pt public floor above 8 pt after TeX scaling.
    fig, axes = plt.subplots(2, 2, figsize=(7.7, 7.25))
    fig.suptitle("Conditional post-ordering evolution of the supplied two-slope condensate", weight="bold", y=0.975)
    fig.subplots_adjust(left=0.085, right=0.91, bottom=0.12, top=0.89, wspace=0.30, hspace=0.36)

    # Panel (a): the frozen orbit.  The visible window starts well inside the
    # regular radiation branch; the integration itself extends to N=-60.
    ax = axes[0, 0]
    mask = dense["N"] >= -20.0
    n = dense["N"][mask]
    ax.plot(n, 1.0e3 * dense["q"][mask], color=BLUE, lw=2.0, label=r"$10^3 q$")
    ax.plot(
        n,
        1.0e3 * dense["p"][mask],
        color=AMBER,
        lw=1.8,
        ls="--",
        marker="o",
        markevery=100,
        ms=3.0,
        label=r"$10^3\,dq/dN$",
    )
    ax.axvspan(-20.0, -12.0, color=PALE_GRAY, alpha=0.55, zorder=-5)
    ax.text(-19.5, 0.40, "regular radiation\nasymptote", color=GRAY, va="bottom", fontsize=10.5)
    ax.set(xlabel=r"$N=\ln a$", ylabel="dimensionless amplitude", title="Frozen scalar orbit")
    ax.grid(True)
    ax.legend(frameon=False, loc="upper left")
    panel_label(ax, "(a)")

    # Panel (b): F evolution and the explicitly non-local-G inverse-F proxy.
    ax = axes[0, 1]
    f0 = dense["F"][-1]
    delta_f_ppm = 1.0e6 * (dense["F"][mask] / f0 - 1.0)
    inv_f_ppm = 1.0e6 * (f0 / dense["F"][mask] - 1.0)
    ax.plot(n, delta_f_ppm, color=GREEN, lw=2.0, label=r"$10^6(F/F_0-1)$")
    ax.plot(n, inv_f_ppm, color=RED, lw=1.8, ls="-.", marker="s", markevery=100, ms=2.8, label=r"$10^6(F_0/F-1)$")
    ax.axhline(0.0, color=INK, lw=0.8, ls=":")
    ax.set(xlabel=r"$N=\ln a$", ylabel="fractional change [ppm]", title="Condensate coupling coordinate")
    ax.grid(True)
    ax.legend(frameon=False, loc="upper left")
    ax.text(
        0.03,
        0.08,
        "inverse-$F$ background proxy\n(not a local $G_N$)",
        transform=ax.transAxes,
        color=RED,
        fontsize=10.5,
    )
    panel_label(ax, "(b)")

    # Panels (c,d) use the frozen conditional-observable table.
    order = np.argsort(-np.log1p(obs["z"]))
    n_obs = -np.log1p(obs["z"])[order]
    e_two = obs["E_two_slope"][order]
    e_ctl = obs["E_reference"][order]

    ax = axes[1, 0]
    ax.semilogy(n_obs, e_two, color=BLUE, lw=2.1, marker="o", ms=4.0, label="two-slope orbit")
    ax.semilogy(n_obs, e_ctl, color=GRAY, lw=1.6, ls="--", marker="D", ms=3.2, mfc=WHITE, label="matched control")
    ax.set(xlabel=r"$N=-\ln(1+z)$", ylabel=r"$E(z)=H(z)/H_0$", title="Expansion history")
    ax.grid(True, which="both")
    ax.legend(frameon=False, loc="upper left")
    inset = ax.inset_axes([0.54, 0.14, 0.42, 0.40])
    inset.plot(n_obs, 1.0e4 * obs["delta_E_percent"][order], color=AMBER, lw=1.5, marker="o", ms=2.6)
    inset.axhline(0.0, color=INK, lw=0.6, ls=":")
    inset.set_title("honest residual", fontsize=10.5)
    inset.set_ylabel(r"$\Delta E$ [ppm]", fontsize=10.5)
    inset.tick_params(labelsize=10.5)
    inset.grid(True)
    panel_label(ax, "(c)")

    ax = axes[1, 1]
    tau_two = obs["H0_t_two_slope"][order]
    tau_ctl = obs["H0_t_reference"][order]
    ax.plot(n_obs, tau_two, color=BLUE, lw=2.1, marker="o", ms=4.0, label="two-slope orbit")
    ax.plot(n_obs, tau_ctl, color=GRAY, lw=1.6, ls="--", marker="D", ms=3.2, mfc=WHITE, label="matched control")
    ax.set(xlabel=r"$N=-\ln(1+z)$", ylabel=r"$H_0t(z)$", title="Conditional branch clock")
    ax.grid(True)
    ax.legend(frameon=False, loc="upper left")
    sec = ax.secondary_yaxis(
        "right",
        functions=(lambda tau: tau * HUBBLE_TIME_GYR, lambda gyr: gyr / HUBBLE_TIME_GYR),
    )
    sec.set_ylabel(f"conditional age [Gyr], $H_0={H0_BRANCH:.1f}$")
    ax.text(
        0.04,
        0.08,
        r"$t_0=13.980496$ Gyr at $H_0=67.4$" "\n" "(declared branch calibration)",
        transform=ax.transAxes,
        color=INK,
        fontsize=10.5,
    )
    panel_label(ax, "(d)")

    fig.text(
        0.5,
        0.025,
        "Status: Level A inside the named action/state; redshift, clock and physical-map readings are conditional Level C.\n"
        "Formation/front selection remains Open; no common-$\\varepsilon$ or HRC interpolation law enters.",
        ha="center",
        va="center",
        fontsize=10.5,
        color=INK,
    )
    save(fig, "r149_conditional_post_ordering_evolution_typography")


def conditional_chronology(obs: dict[str, np.ndarray]) -> None:
    order = np.argsort(obs["z"])[::-1]
    z = obs["z"][order]
    t_two = HUBBLE_TIME_GYR * obs["H0_t_two_slope"][order]
    t_ctl = HUBBLE_TIME_GYR * obs["H0_t_reference"][order]
    residual_kyr = 1.0e6 * (t_two - t_ctl)

    fig, (ax, residual) = plt.subplots(
        2,
        1,
        figsize=(7.0, 5.9),
        gridspec_kw={"height_ratios": [2.3, 1.0]},
    )
    fig.suptitle("Conditional chronology of the named two-slope ordered branch", weight="bold", y=0.975)
    fig.subplots_adjust(left=0.075, right=0.975, bottom=0.14, top=0.88, hspace=0.43)

    ax.set_xscale("log")
    ax.set_xlim(0.14, 16.0)
    ax.set_ylim(0.0, 1.22)
    ax.set_yticks([])
    ax.set_xlabel("conditional branch age [Gyr, logarithmic scale]")
    ax.set_xticks([0.2, 0.5, 1.0, 2.0, 5.0, 10.0])
    ax.set_xticklabels(["0.2", "0.5", "1", "2", "5", "10"])
    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    ax.grid(True, axis="x")
    ax.text(
        0.02,
        1.08,
        "Formation/front selection: Open\nsolver enters an already ordered regular branch",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=10.5,
        weight="bold",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": PALE_OPEN, "edgecolor": OPEN, "linestyle": "--", "linewidth": 1.3},
    )

    ax.plot([t_two[0], t_two[-1]], [0.57, 0.57], color=BLUE, lw=3.0, solid_capstyle="round")
    ax.plot([t_ctl[0], t_ctl[-1]], [0.43, 0.43], color=GRAY, lw=1.8, ls="--")
    ax.text(13.65, 0.64, "two-slope", color=BLUE, ha="right", fontsize=9.0, weight="bold")
    ax.text(13.65, 0.33, "matched control", color=GRAY, ha="right", fontsize=9.0)

    for i, (zi, ti, tc) in enumerate(zip(z, t_two, t_ctl)):
        ax.plot(ti, 0.57, marker="o", ms=5.0, color=BLUE, zorder=4)
        ax.plot(tc, 0.43, marker="D", ms=3.8, mfc=WHITE, mec=GRAY, zorder=4)
        y_text = 0.19 if i % 2 == 0 else 0.78
        va = "top" if y_text < 0.3 else "bottom"
        ax.plot([ti, ti], [0.53 if y_text < 0.3 else 0.61, y_text + (0.018 if y_text < 0.3 else -0.018)], color="#AAB0B3", lw=0.7)
        age = f"{ti:.3f}" if ti < 10 else f"{ti:.2f}"
        ax.text(ti, y_text, f"$z={zi:g}$\n{age} Gyr", ha="center", va=va, fontsize=9.0)

    residual.plot(z, residual_kyr, color=AMBER, lw=1.8, marker="o", ms=4.2, label=r"$t_{2s}-t_{ctl}$")
    residual.axhline(0.0, color=INK, ls=":", lw=0.8)
    residual.set_xscale("log")
    residual.invert_xaxis()
    residual.set(
        xlabel="redshift $z$ (early $\\rightarrow$ present)",
        ylabel="age residual [kyr]",
        title="Residual shown on its own scale; the two histories overlap in the main chronology",
    )
    residual.grid(True)
    residual.legend(frameon=False, loc="lower left")
    residual.text(
        0.99,
        0.05,
        "same present fractions; no independent JWST likelihood",
        transform=residual.transAxes,
        ha="right",
        fontsize=9.0,
        color=GRAY,
    )

    fig.text(
        0.5,
        0.035,
        r"Current branch calibration: $H_0=67.4$ km s$^{-1}$ Mpc$^{-1}$, $t_0=13.980496$ Gyr. "
        "\n" r"The separate BC03 clock fit ($H_0=68.586\pm3.949$) is not used here; neither calibration is a universal P1--P6 prediction.",
        ha="center",
        va="center",
        fontsize=9.0,
    )
    save(fig, "r123_conditional_chronology")


def node(
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
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.035,rounding_size=0.07",
            facecolor=face,
            edgecolor=edge,
            linewidth=1.45,
            linestyle=linestyle,
        )
    )
    ax.text(x + w / 2, y + 0.66 * h, title, ha="center", va="center", weight="bold", fontsize=11.0)
    ax.text(x + w / 2, y + 0.28 * h, body, ha="center", va="center", fontsize=10.5, linespacing=1.12)


def down_arrow(ax: plt.Axes, x: float, y_top: float, y_bottom: float, *, solid: bool, label: str = "") -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x, y_top),
            (x, y_bottom),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.45,
            linestyle="-" if solid else "--",
            color=BLUE if solid else OPEN,
        )
    )
    if label:
        ax.text(x + 0.13, (y_top + y_bottom) / 2, label, va="center", fontsize=10.5, color=INK)


def external_internal_map() -> None:
    fig, ax = plt.subplots(figsize=(7.7, 7.35))
    fig.suptitle("Shape-agnostic external Euclidean view and internal cosmological history", y=0.985, weight="bold")
    fig.subplots_adjust(left=0.035, right=0.975, bottom=0.105, top=0.91)
    ax.set_xlim(0.0, 12.0)
    # Reserve a separate lower information band so the formula box and
    # status legend never intersect the physical front curve.
    ax.set_ylim(-1.55, 8.6)
    ax.axis("off")

    # External side: a deliberately non-spherical local front patch.
    y = np.linspace(1.05, 7.65, 320)
    x_front = 3.15 + 0.20 * np.sin(1.35 * y) + 0.07 * np.sin(3.20 * y + 0.4)
    ax.fill_betweenx(y, 0.35, x_front, color=PALE_GRAY, alpha=0.95)
    ax.fill_betweenx(y, x_front, 5.55, color=PALE_BLUE, alpha=0.95)
    ax.plot(x_front, y, color=OPEN, lw=2.4)
    ax.text(1.55, 8.05, "external Euclidean description", ha="center", weight="bold", fontsize=12.0)
    ax.text(1.30, 6.95, "uncondensed /\nnot selected", ha="center", va="top", color=GRAY, fontsize=10.5)
    ax.text(4.38, 6.95, "ordered\nside", ha="center", va="top", color=BLUE, weight="bold", fontsize=10.5)
    ax.text(3.18, 7.42, r"generic local front $\Sigma_{ord}$", ha="center", color=OPEN, weight="bold", fontsize=10.5)
    ax.text(3.18, 0.50, "shape and global topology are not specified", ha="center", color=RED, fontsize=10.5)

    # One action-owned congruence and a directional depth; no global radius.
    yy = 4.45
    xf = float(np.interp(yy, y, x_front))
    ax.add_patch(
        FancyArrowPatch(
            (xf + 0.05, yy),
            (5.22, yy + 0.52),
            connectionstyle="arc3,rad=-0.08",
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=2.0,
            color=BLUE,
        )
    )
    ax.plot([xf + 0.08, 4.78], [yy, yy + 0.42], color=GREEN, lw=4.0, alpha=0.68, solid_capstyle="round")
    ax.text(4.12, 5.18, r"one congruence $\gamma_p$", ha="center", color=BLUE, fontsize=10.5, weight="bold")
    ax.text(4.07, 4.12, r"directional depth $d\ell_E$", ha="center", color=GREEN, fontsize=10.5)
    ax.text(3.14, 2.05, "not a sphere; not a universal radius", ha="center", color=RED, fontsize=10.5, weight="bold")

    # The two exact directional identities, conditioned on a supplied lapse and map.
    node(
        ax,
        0.62,
        -0.68,
        4.85,
        0.68,
        "Directional internal/external identities",
        r"$d\tau=(N_\Phi/c_u)d\ell_E$     $H=(c_u/N_\Phi)a^{-1}da/d\ell_E$",
        face=PALE_GREEN,
        edge=GREEN,
    )

    # Internal owner chain.  Solid means available inside the named supplied
    # completion; dashed means an unclosed physical bridge.
    ax.text(8.83, 8.05, "internal history and ownership", ha="center", weight="bold", fontsize=12.0)
    x0, width, height = 6.45, 4.78, 1.00
    ys = [6.78, 5.33, 3.88, 2.43, 0.98]
    node(ax, x0, ys[0], width, height, "Formation/front boundary data", "state selection / geometry: Open", face=PALE_OPEN, edge=OPEN, linestyle="--")
    node(ax, x0, ys[1], width, height, "Named two-slope ordered orbit", r"$q,H,F$: Level A in supplied" "\n" "action/state", face=PALE_BLUE, edge=BLUE)
    node(ax, x0, ys[2], width, height, "Matter/photon metric + clock", "conditional map;" "\n" "first-principles owner Open", face=PALE_GREEN, edge=GREEN)
    node(ax, x0, ys[3], width, height, "Primordial microphysics", "BBN / recombination /" "\n" "perturbations owner: Open", face=PALE_GRAY, edge=GRAY, linestyle="--")
    node(ax, x0, ys[4], width, height, "Late response sectors", "HRC / PPN / PES:" "\n" "distinct Open interfaces", face=PALE_OPEN, edge=OPEN, linestyle="--")

    xc = x0 + width / 2
    down_arrow(ax, xc, ys[0], ys[1] + height, solid=False, label="selection bridge")
    down_arrow(ax, xc, ys[1], ys[2] + height, solid=False, label="physical-map bridge")
    down_arrow(ax, xc, ys[2], ys[3] + height, solid=False, label="microphysical owner")
    down_arrow(ax, xc, ys[3], ys[4] + height, solid=False, label="response matching")

    ax.add_patch(
        FancyArrowPatch(
            (5.45, 4.72),
            (6.36, 6.00),
            connectionstyle="arc3,rad=0.15",
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.4,
            linestyle="--",
            color=OPEN,
        )
    )
    ax.text(5.02, 5.88, "lapse / clock\nidentification", ha="center", fontsize=10.5, color=OPEN)

    handles = [
        Patch(facecolor=PALE_BLUE, edgecolor=BLUE, label="owned inside named completion"),
        Patch(facecolor=PALE_GREEN, edgecolor=GREEN, label="conditional identity"),
        Patch(facecolor=PALE_OPEN, edgecolor=OPEN, linestyle="--", label="Open bridge/input"),
        Patch(facecolor=PALE_GRAY, edgecolor=GRAY, linestyle="--", label="external/imported layer"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=4, frameon=False, fontsize=10.5)
    save(fig, "r149_external_internal_history_map_typography")


def main() -> None:
    verify_inputs()
    configure()
    dense = load_csv(INPUTS["dense"][0])
    obs = load_csv(INPUTS["observables"][0])
    conditional_post_ordering(dense, obs)
    # Not an R149 typography target: do not create an unneeded duplicate.
    external_internal_map()
    print(f"Wrote four R149 typography-successor assets under {OUT}")


if __name__ == "__main__":
    main()
