#!/usr/bin/env python3
"""Build three typography-only R149 successors from hash-locked owners.

The scientific payload and status text remain in the frozen owner scripts.
This builder applies only explicit typography, canvas and output-path
substitutions in memory and executes the modified sources inside this
proposal directory.  It never edits an owner, a live figure or manuscript.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("SOURCE_DATE_EPOCH", "1784894400")


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ROOT = HERE.parents[6]
OUT = COMPONENT / "outputs"
RUNTIME = COMPONENT / ".runtime"
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(RUNTIME / "cache"))

OWNERS = {
    "dimensionality": (
        ROOT / "LaTex/scripts/fig6_dimensionality.py",
        "ee578321b0ce0acc605b9a8a3c616c89e9882f811a622961e26f9f5a02365f8e",
    ),
    "regime": (
        ROOT / "LaTex/scripts/fig_regime_diagram.py",
        "4520915af51f5f0a7c77691a1701b4fcfa42afe130a1491f09257d4c8a4757e1",
    ),
    "coherence": (
        ROOT
        / "LaTex/work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/coherence/"
        "build_coherence_regimes_r149.py",
        "8e7397f396f5a56ede25cad4d070acd3de11eee6295a8e7959d29d06c714e3cf",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def locked_source(key: str) -> tuple[Path, str]:
    path, expected = OWNERS[key]
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"{key} owner drift: {actual} != {expected}")
    return path, path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one replacement, found {count}: {old!r}")
    return text.replace(old, new)


def replace_exact(text: str, old: str, new: str, expected: int) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            f"expected {expected} replacements, found {count}: {old!r}"
        )
    return text.replace(old, new)


def execute(text: str, owner: Path, extra: dict | None = None) -> dict:
    namespace = {
        "__name__": f"r149_successor_{owner.stem}",
        "__file__": str(owner),
        "OUTPUT_DIR": OUT,
    }
    if extra:
        namespace.update(extra)
    exec(compile(text, str(owner), "exec"), namespace)
    return namespace


def build_dimensionality() -> list[Path]:
    # The hash lock ensures these formulae and constants still match the
    # publication owner.  The portrait relayout below changes only placement.
    locked_source("dimensionality")
    import datetime as dt
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 10.2,
            "axes.labelsize": 10.4,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 8.8,
            "mathtext.fontset": "dejavuserif",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.7,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )

    g_si, m_sun, kpc_m = 6.674e-11, 1.989e30, 3.086e19
    a_m0 = 1.0824013602e-10

    def d_force(x):
        return 1.0 + 2.0 * (1.0 + x**2) / (2.0 + x**2)

    def x_of_r(r_kpc, mass):
        r_m = r_kpc * kpc_m
        g_n = g_si * mass / r_m**2
        g_obs2 = (g_n**2 + np.sqrt(g_n**4 + 4.0 * g_n**2 * a_m0**2)) / 2.0
        return np.sqrt(g_obs2) / a_m0

    def r_star(mass):
        return np.sqrt(g_si * mass / a_m0) / kpc_m

    curves = [
        (r"Dwarf-mass point source ($10^8\,M_\odot$)", 1e8 * m_sun, "--", "#009E73", 1.7),
        (r"MW-mass point source ($5{\times}10^{10}\,M_\odot$)", 5e10 * m_sun, "-", "#0072B2", 2.2),
        (r"Giant-mass point source ($5{\times}10^{11}\,M_\odot$)", 5e11 * m_sun, "-.", "#D55E00", 1.7),
    ]

    fig = plt.figure(figsize=(6.25, 7.35), constrained_layout=False)
    grid = fig.add_gridspec(
        2, 1, height_ratios=(1.7, 1.0), hspace=0.32,
        left=0.13, right=0.98, top=0.955, bottom=0.135
    )
    ax1 = fig.add_subplot(grid[0])
    ax2 = fig.add_subplot(grid[1])

    for level in (3, 2):
        ax1.axhline(level, color="0.82", ls=":", lw=0.7, zorder=0)
    for name, mass, style, colour, width in curves:
        rs = r_star(mass)
        r_kpc = np.logspace(-0.3, 3.5, 400)
        xx = np.array([x_of_r(r, mass) for r in r_kpc])
        yy = d_force(xx)
        r_mpc = r_kpc / 1000.0
        isolation = 300 if mass < 1e9 * m_sun else (2000 if mass < 1e11 * m_sun else 3000)
        ok = r_kpc <= isolation
        ax1.plot(r_mpc[ok], yy[ok], style, color=colour, lw=width, label=name)
        if np.any(~ok):
            ax1.plot(r_mpc[~ok], yy[~ok], style, color=colour, lw=0.55 * width, alpha=0.28)
        ax1.plot(rs / 1000.0, d_force(x_of_r(rs, mass)), "o", color=colour, ms=5.2)
    ax1.axvline(3.0, color="0.58", lw=0.7)
    ax1.text(
        2.75, 2.42, "single-source\nscope limit", rotation=90,
        ha="right", va="center", color="0.38", fontsize=8.8, style="italic"
    )
    ax1.annotate(
        "high acceleration:\n$g\\propto1/r^2$", xy=(8e-4, 2.99),
        xytext=(3e-3, 2.72), fontsize=9.0, color="0.28",
        arrowprops={"arrowstyle": "->", "color": "0.35", "lw": 0.8}
    )
    ax1.annotate(
        "conditional HRC-0 branch:\n$g\\propto1/r\\Rightarrow v_{\\rm flat}$",
        xy=(0.30, 2.01), xytext=(0.015, 1.63), fontsize=9.0,
        color="0.24", arrowprops={"arrowstyle": "->", "color": "0.35", "lw": 0.8}
    )
    rs_mw = r_star(5e10 * m_sun)
    ax1.annotate(
        fr"$r_*\ (g_N=a_M)\simeq {rs_mw:.0f}$ kpc",
        xy=(rs_mw / 1000.0, d_force(x_of_r(rs_mw, 5e10 * m_sun))),
        xytext=(0.035, 2.58), fontsize=9.0,
        arrowprops={"arrowstyle": "->", "color": "0.35", "lw": 0.8}
    )
    ax1.set_xscale("log")
    ax1.set_xlim(3e-4, 600)
    ax1.set_ylim(1.2, 3.15)
    ax1.set_xlabel("Scale $r$ [Mpc]")
    ax1.set_ylabel(r"Force-law dimensionality $d_{\rm force}(r)$")
    ax1.set_title("(a) Idealised point-source mass benchmarks", loc="left", weight="bold")
    ax1.legend(loc="lower right", frameon=True, edgecolor="0.65", ncol=1)
    ax1.tick_params(which="both", top=True, right=True)

    x_arr = np.logspace(-2, 3, 500)
    ax2.plot(x_arr, d_force(x_arr), "-", color="#0072B2", lw=2.2)
    ax2.axhline(3, color="0.82", ls=":", lw=0.7)
    ax2.axhline(2, color="0.82", ls=":", lw=0.7)
    ax2.text(40, 2.91, r"$d\to3$ (Newtonian)", fontsize=9.0, color="0.35")
    ax2.text(
        0.018, 2.07, r"$d\to2$ (conditional HRC-0 $\mu_{g,0}$)",
        fontsize=9.0, color="0.35"
    )
    ax2.text(
        0.97, 0.08,
        r"$d_{\rm force}(x)=1+\dfrac{2(1+x^2)}{2+x^2}$",
        transform=ax2.transAxes, ha="right", va="bottom", fontsize=10.0,
        bbox={"fc": "white", "ec": "0.55", "lw": 0.7, "pad": 4}
    )
    ax2.set_xscale("log")
    ax2.set_xlim(0.01, 1000)
    ax2.set_ylim(1.9, 3.1)
    ax2.set_xlabel(r"$x=g_{\rm obs}/a_M$")
    ax2.set_ylabel(r"$d_{\rm force}(x)$")
    ax2.set_title("(b) Universal conditional HRC-0 relation", loc="left", weight="bold")
    ax2.tick_params(which="both", top=True, right=True)

    fig.text(
        0.5, 0.050,
        r"Synthetic HRC-0 benchmark: $a_{M0}=1.0824\times10^{-10}\,\mathrm{m\,s^{-2}}$.",
        ha="center", fontsize=8.5, style="italic"
    )
    fig.text(
        0.5, 0.030,
        "Idealised point sources; no observational data overlay.",
        ha="center", fontsize=8.5, style="italic"
    )
    fig.text(
        0.5, 0.010,
        "Faded isolation cutoffs are display-only.",
        ha="center", fontsize=8.5, style="italic"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / "fig_dimensionality_phi_typography_r149.pdf"
    png = OUT / "fig_dimensionality_phi_typography_r149.png"
    fixed = dt.datetime(2026, 7, 24, 12, 0, tzinfo=dt.timezone.utc)
    fig.savefig(
        pdf,
        metadata={
            "Title": "Conditional HRC-0 point-source dimensionality benchmark",
            "Creator": "ECT R149 typography successor",
            "CreationDate": fixed,
            "ModDate": fixed,
        },
    )
    fig.savefig(
        png, dpi=240,
        metadata={"Software": "ECT R149 typography successor"}
    )
    plt.close(fig)
    return [
        pdf,
        png,
    ]


def build_regime() -> list[Path]:
    owner, text = locked_source("regime")
    substitutions = {
        '"font.family": "serif", "font.size": 9,':
        '"font.family": "serif", "font.size": 10.2,',
        "fig, ax = plt.subplots(figsize=(7, 4.8))":
        "fig, ax = plt.subplots(figsize=(6.25, 4.5))",
        'OUT = ROOT / "figures" / "fig_regime_diagram.png"':
        'OUT = OUTPUT_DIR / "fig_regime_diagram_typography_r149.png"',
        'fig.savefig(OUT, dpi=220, bbox_inches="tight", facecolor="white")':
        'fig.savefig(OUTPUT_DIR / "fig_regime_diagram_typography_r149.pdf", '
        'bbox_inches="tight", facecolor="white", metadata={"Title": '
        '"Conditional HRC regime schematic", "Creator": '
        '"ECT R149 typography successor"}); '
        'fig.savefig(OUT, dpi=240, bbox_inches="tight", facecolor="white", '
        'metadata={"Software": "ECT R149 typography successor"})',
    }
    for old, new in substitutions.items():
        text = replace_once(text, old, new)
    OUT.mkdir(parents=True, exist_ok=True)
    execute(text, owner)
    return [
        OUT / "fig_regime_diagram_typography_r149.pdf",
        OUT / "fig_regime_diagram_typography_r149.png",
    ]


def build_coherence() -> list[Path]:
    owner, text = locked_source("coherence")
    substitutions = {
        'SCRIPT_VERSION = "R149 coherence-regime owner v1"':
        'SCRIPT_VERSION = "R149 coherence-regime typography successor v2"',
        'RUNTIME_ROOT = Path(__file__).resolve().parent / ".runtime"':
        f'RUNTIME_ROOT = Path({str(RUNTIME)!r})',
        '"legend.fontsize": 7.7,': '"legend.fontsize": 8.7,',
        "fontsize=7.2,": "fontsize=8.6,",
        "fontsize=7.7,": "fontsize=8.7,",
        "fontsize=7.1,": "fontsize=8.6,",
    }
    for old, new in substitutions.items():
        text = replace_once(text, old, new)
    text = replace_exact(text, "fontsize=8.3,", "fontsize=8.7,", 2)
    namespace = execute(text, owner)
    target = OUT / "coherence"
    target.mkdir(parents=True, exist_ok=True)
    namespace["build"](target)
    return [
        target / "fig_coherence_regimes_r149.pdf",
        target / "fig_coherence_regimes_r149.png",
        target / "R149_COHERENCE_RUNTIME_v1.json",
    ]


def main() -> int:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    outputs = build_dimensionality() + build_regime() + build_coherence()
    runtime = {
        "schema": "ECT-R149-main-A-typography-successors-v1",
        "status": "PROPOSAL ONLY; live sources untouched",
        "scope": "typography, canvas and output path only",
        "owners": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": expected}
            for key, (path, expected) in OWNERS.items()
        },
        "outputs": {
            str(path.relative_to(COMPONENT)): sha256(path)
            for path in outputs
        },
        "runtime": {
            "python": platform.python_version(),
            "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        },
    }
    (COMPONENT / "manifests" / "R149_MAIN_A_SUCCESSORS_BUILD_v1.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(runtime["outputs"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
