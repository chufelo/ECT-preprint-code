#!/usr/bin/env python3
"""Generate the conditional Level-C HRC-0/HRC-3 publication figures.

The script reads the frozen R89 held-out outputs and produces only HRC-0 and
HRC-3 diagnostics.  It does not refit or alter manuscript source.  SPARC-
derived projections are external, hash-pinned inputs and are not redistributed
in the public repository.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from external_inputs import resolve_external_input


LATEX_ROOT = Path(__file__).resolve().parents[2]
ROOT = LATEX_ROOT
DATA_DIR = LATEX_ROOT / "data" / "hrc_r97"
POINTS_REL = "data/hrc_r97/R97_HRC_SOURCE_POINTS.csv"
REGIMES_REL = "data/hrc_r97/R97_HRC_SOURCE_REGIMES.csv"
POINTS = resolve_external_input(
    LATEX_ROOT,
    POINTS_REL,
    "5f9b884e611e61189a97cc6c8fdb01e430bfc7bf7cef3faf05be2b0d2b8a2e80",
)
REGIMES = resolve_external_input(
    LATEX_ROOT,
    REGIMES_REL,
    "134d74573524e024a3e3433c02380a159f5ff83a00fca34b95f8eb289ef48d7e",
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = DATA_DIR / "R97_HRC_SOURCE_SCALE_SUMMARY.json"
OUT = LATEX_ROOT / "figures" / "hrc"
OUT.mkdir(parents=True, exist_ok=True)
OWNED_STEMS = (
    "R97_HRC_RESPONSE_AND_REGIMES",
    "R97_HRC_ROTATION_EXAMPLES",
    "R97_HRC_RAR_DIAGNOSTIC",
)

ACC_CONV = 1e6 / 3.0856775814913673e19

# Okabe--Ito roles plus line-style and marker redundancy.  Every comparison
# remains legible after grayscale conversion.
BLUE = "#0072B2"       # HRC-0
ORANGE = "#D55E00"     # HRC-3
GREEN = "#009E73"      # observations / independent data
BLACK = "#222222"
GREY = "#777777"


def apply_publication_readability_floor(
    fig: plt.Figure,
    *,
    size: tuple[float, float],
    floor: float = 10.5,
    title_floor: float = 12.0,
    legend_floor: float = 10.2,
) -> None:
    """Preserve the accepted R127 readability floor in direct replays."""

    fig.set_size_inches(*size, forward=True)
    for text_item in fig.findobj(match=matplotlib.text.Text):
        if not str(text_item.get_text()).strip():
            continue
        target = title_floor if text_item in fig.texts else floor
        text_item.set_fontsize(max(float(text_item.get_fontsize()), target))
    for ax in fig.axes:
        ax.tick_params(axis="both", which="both", labelsize=floor)
        ax.title.set_fontsize(max(float(ax.title.get_fontsize()), title_floor))
        ax.xaxis.label.set_fontsize(max(float(ax.xaxis.label.get_fontsize()), floor))
        ax.yaxis.label.set_fontsize(max(float(ax.yaxis.label.get_fontsize()), floor))
    for legend in list(fig.legends) + [ax.get_legend() for ax in fig.axes]:
        if legend is None:
            continue
        for text_item in legend.get_texts():
            text_item.set_fontsize(max(float(text_item.get_fontsize()), legend_floor))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mu0(x: np.ndarray | float) -> np.ndarray | float:
    return x / np.sqrt(1.0 + np.asarray(x) ** 2)


def mu3(x: np.ndarray | float) -> np.ndarray | float:
    xx = np.asarray(x)
    y = xx**2
    return mu0(xx) * (1.0 - (4.0 / 3.0) * y / (1.0 + y) ** 2)


def solve_g(g_n: float, a_m: float, which: str) -> float:
    """Solve g_N = mu(g/a_M) g by monotone bisection."""

    if g_n <= 0:
        return 0.0
    law = mu0 if which == "HRC0" else mu3
    lo = g_n
    hi = max(g_n + a_m, math.sqrt(g_n * a_m) * 4.0, a_m)
    while float(law(hi / a_m)) * hi < g_n:
        hi *= 2.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if float(law(mid / a_m)) * mid < g_n:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig: plt.Figure, stem: str) -> None:
    frozen_time = datetime(2026, 7, 17, 0, 0, 0, tzinfo=timezone.utc)
    fig.savefig(
        OUT / f"{stem}.pdf",
        dpi=220,
        bbox_inches="tight",
        metadata={
            "Creator": "ECT R97 deterministic HRC figure generator",
            "CreationDate": frozen_time,
            "ModDate": frozen_time,
        },
    )
    fig.savefig(
        OUT / f"{stem}.png",
        dpi=220,
        bbox_inches="tight",
        metadata={"Software": "ECT R97 deterministic HRC figure generator"},
    )
    plt.close(fig)


def response_and_regime_figure() -> None:
    rows = [r for r in load_rows(REGIMES) if r["bin_kind"] == "coarse"]
    order = ["deep_yN_lt_0p1", "crossover_0p1_to_10", "newtonian_yN_gt_10"]
    names = {r["bin"]: r for r in rows}

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))
    x = np.logspace(-3, 3, 800)
    axes[0].plot(x, mu0(x), color=BLUE, lw=2.4, ls="--", label="HRC-0")
    axes[0].plot(x, mu3(x), color=ORANGE, lw=2.4, ls="-", label="HRC-3")
    axes[0].set_xscale("log")
    axes[0].set_xlabel(r"$x=g/a_M$")
    axes[0].set_ylabel(r"$\mu_{\rm HRC}(x)$")
    axes[0].set_title("HRC response laws")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend(frameon=False)

    idx = np.arange(3)
    width = 0.34
    h0 = [float(names[key]["chi2_HRC0_per_point"]) for key in order]
    h3 = [float(names[key]["chi2_HRC3_per_point"]) for key in order]
    axes[1].bar(
        idx - width / 2,
        h0,
        width,
        color=BLUE,
        edgecolor=BLACK,
        hatch="//",
        label="HRC-0",
    )
    axes[1].bar(
        idx + width / 2,
        h3,
        width,
        color=ORANGE,
        edgecolor=BLACK,
        hatch="..",
        label="HRC-3",
    )
    axes[1].set_xticks(idx, ["deep", "crossover", "Newtonian"])
    axes[1].set_ylabel(r"held-out $\chi^2$ per point")
    axes[1].set_title("Frozen algebraic SPARC diagnostic")
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].legend(frameon=False)
    fig.suptitle("HRC-only response and regime diagnostics", fontsize=13)
    fig.tight_layout()
    save(fig, "R97_HRC_RESPONSE_AND_REGIMES")


def rotation_examples_figure() -> None:
    rows = load_rows(POINTS)
    selected = ["DDO154", "NGC2403", "NGC3198", "NGC6503"]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["galaxy"] in selected:
            grouped[(row["galaxy"], row["source_row_index"])].append(row)

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.5), sharex=False, sharey=False)
    for ax, galaxy in zip(axes.flat, selected):
        points = []
        for (name, _), values in grouped.items():
            if name != galaxy:
                continue
            first = values[0]
            points.append(
                (
                    float(first["radius_kpc"]),
                    float(first["vobs_km_s"]),
                    float(first["error_km_s"]),
                    float(np.mean([float(v["v_HRC0"]) for v in values])),
                    float(np.mean([float(v["v_HRC3"]) for v in values])),
                    float(np.min([float(v["v_HRC0"]) for v in values])),
                    float(np.max([float(v["v_HRC0"]) for v in values])),
                    float(np.min([float(v["v_HRC3"]) for v in values])),
                    float(np.max([float(v["v_HRC3"]) for v in values])),
                )
            )
        points.sort()
        arr = np.asarray(points)
        ax.errorbar(
            arr[:, 0],
            arr[:, 1],
            yerr=arr[:, 2],
            fmt="o",
            ms=3.6,
            color=BLACK,
            ecolor=GREY,
            capsize=1.5,
            label="SPARC",
        )
        ax.plot(arr[:, 0], arr[:, 3], color=BLUE, ls="--", lw=2.0, label="HRC-0")
        ax.plot(arr[:, 0], arr[:, 4], color=ORANGE, ls="-", lw=2.0, label="HRC-3")
        ax.fill_between(arr[:, 0], arr[:, 5], arr[:, 6], color=BLUE, alpha=0.10)
        ax.fill_between(arr[:, 0], arr[:, 7], arr[:, 8], color=ORANGE, alpha=0.10)
        ax.set_title(galaxy)
        ax.set_xlabel("R [kpc]")
        ax.set_ylabel(r"$V$ [km s$^{-1}$]")
        ax.grid(True, alpha=0.25)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.947),
        ncol=3,
        frameon=False,
    )
    fig.suptitle(
        "Held-out HRC rotation-curve examples (mean over five whole-galaxy splits)",
        y=0.992,
        fontsize=12.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.895))
    save(fig, "R97_HRC_ROTATION_EXAMPLES")


def rar_figure() -> None:
    rows = load_rows(POINTS)
    # One physical copy of each data point: the held-out rows repeat over five seeds.
    physical: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        physical.setdefault((row["galaxy"], row["source_row_index"]), row)

    g_n = np.asarray([float(row["gN_si"]) for row in physical.values()])
    g_obs = np.asarray(
        [
            float(row["vobs_km_s"]) ** 2
            / max(float(row["radius_kpc"]), 1e-12)
            * ACC_CONV
            for row in physical.values()
        ]
    )
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    a0 = float(
        np.mean(
            [
                value["a0_si_mean"]
                for value in result["cross_validation"]["HRC0"]["by_seed"].values()
            ]
        )
    )
    a3 = float(
        np.mean(
            [
                value["a0_si_mean"]
                for value in result["cross_validation"]["HRC3"]["by_seed"].values()
            ]
        )
    )
    grid = np.logspace(-13.5, -8.5, 350)
    pred0 = np.asarray([solve_g(v, a0, "HRC0") for v in grid])
    pred3 = np.asarray([solve_g(v, a3, "HRC3") for v in grid])

    fig, ax = plt.subplots(figsize=(6.5, 5.4))
    ax.scatter(g_n, g_obs, s=5, alpha=0.16, color=GREY, rasterized=True, label="SPARC points")
    ax.plot(grid, grid, color=BLACK, lw=1.3, ls=":", label="Newtonian")
    ax.plot(grid, pred0, color=BLUE, lw=2.2, ls="--", label=f"HRC-0, $a_M={a0:.2e}$")
    ax.plot(grid, pred3, color=ORANGE, lw=2.2, ls="-", label=f"HRC-3, $a_M={a3:.2e}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$g_N$ [m s$^{-2}$]")
    ax.set_ylabel(r"$g_{\rm obs}$ [m s$^{-2}$]")
    ax.set_title("HRC-only radial-acceleration diagnostic")
    ax.grid(True, which="both", alpha=0.22)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    apply_publication_readability_floor(fig, size=(6.2, 5.0))
    save(fig, "R97_HRC_RAR_DIAGNOSTIC")


def main() -> None:
    response_and_regime_figure()
    rotation_examples_figure()
    rar_figure()
    manifest = {
        "status": "LEVEL_C_CONDITIONAL_PUBLICATION_CALCULATION",
        "inputs": {
            POINTS_REL: sha256(POINTS),
            REGIMES_REL: sha256(REGIMES),
            str(RESULTS.relative_to(ROOT)): sha256(RESULTS),
        },
        "outputs": {
            str(path.relative_to(ROOT)): sha256(path)
            for stem in OWNED_STEMS
            for path in (OUT / f"{stem}.pdf", OUT / f"{stem}.png")
            if path.is_file()
        },
        "guards": {
            "simple_law_plotted": False,
            "only_HRC0_HRC3_theory_curves": True,
            "old_law_used_as_refit_input": False,
            "full_disk_PDE": False,
            "hierarchical_likelihood": False,
        },
    }
    (DATA_DIR / "R97_HRC_ONLY_FIGURE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
