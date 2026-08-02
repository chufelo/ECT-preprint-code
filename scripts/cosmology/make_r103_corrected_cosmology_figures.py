#!/usr/bin/env python3
"""Generate corrected R103 cosmology figures from frozen public JSON only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
VERMILION = "#D55E00"
PURPLE = "#CC79A7"
BLACK = "#222222"
GRAY = "#777777"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def finish(fig: plt.Figure, out: Path) -> None:
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def background_figure(data: dict, scan: dict, out: Path) -> None:
    rows = sorted(data["rows"], key=lambda r: r["z"])
    z = np.array([r["z"] for r in rows])
    log1pz = np.log1p(z)
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 7.4), constrained_layout=True)

    ax = axes[0, 0]
    ax.plot(log1pz, [r["delta_E_percent"] for r in rows], color=BLUE, marker="o", ls="-")
    ax.axhline(0, color=BLACK, lw=0.8, ls=":")
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$\Delta H/H_{\rm ctl}$ [\%]", title="Named two-slope expansion")

    ax = axes[0, 1]
    ax.plot(log1pz, [r["H0_t_two_slope"] for r in rows], color=BLUE, marker="o", label="two-slope")
    ax.plot(log1pz, [r["H0_t_reference"] for r in rows], color=BLACK, marker="s", ls="--", label="matched control")
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$H(0)t(z)$", title="Conditional clock budget")
    ax.legend(frameon=False)

    ax = axes[0, 2]
    ax.plot(log1pz[1:], [r["delta_chi_percent"] for r in rows[1:]], color=GREEN, marker="^", ls="-.")
    ax.axhline(0, color=BLACK, lw=0.8, ls=":")
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$\Delta\chi/\chi_{\rm ctl}$ [\%]", title="Conditional comoving distance")

    ax = axes[1, 0]
    ax.plot(log1pz, [r["w_eff_two_slope"] for r in rows], color=BLUE, marker="o", label="two-slope")
    ax.plot(log1pz, [r["w_eff_reference"] for r in rows], color=BLACK, marker="s", ls="--", label="matched control")
    ax.set(xlabel=r"$\ln(1+z)$", ylabel=r"$w_{\rm eff}=-1-2H'/(3H)$", title="Total background equation of state")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 1]
    markers = {0.01: "o", 0.03: "s", 0.08: "^"}
    colors = {0.05: VERMILION, 1.0: ORANGE, 10.0: GREEN}
    for r in scan["rows"]:
        ax.scatter(
            100.0 * (r["H0_t0"] / scan["reference_age_H0t0"] - 1.0),
            r["diagnostics"]["z=10"]["delta_t_percent"],
            color=colors[r["kappa"]], marker=markers[r["a"]], s=55,
            edgecolor=BLACK, linewidth=0.35,
        )
    ax.axhline(0, color=BLACK, lw=0.8, ls=":")
    ax.axvline(0, color=BLACK, lw=0.8, ls=":")
    ax.set(xlabel=r"$\Delta t_0$ [\%]", ylabel=r"$\Delta t(z=10)$ [\%]", title=r"Calibrated $3\times3$ family")
    ax.text(0.98, 0.05, r"colour: $\kappa_s$; marker: $a_s$", transform=ax.transAxes, ha="right", fontsize=8)
    ax = axes[1, 2]
    ax.axis("off")
    ax.text(
        0.02, 0.96,
        "Conditional supplied-action outputs\n"
        "• not a unique P1–P6 cosmology\n"
        "• $H_0$ is one declared unit/state calibration\n"
        "• $w_{eff}$ is total background kinematics, not $w_{DE}$\n"
        "• photon/perturbation likelihood owners remain open",
        va="top", fontsize=10,
    )
    finish(fig, out)


def tradeoff_figure(scan: dict, out: Path) -> None:
    rows = scan["rows"]
    gamma = np.array([abs(r["gamma_PPN_unscreened_massless"] - 1.0) for r in rows])
    rs = np.array([-r["delta_r_s_percent"] for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.15), constrained_layout=True)
    colors = {0.05: VERMILION, 1.0: ORANGE, 10.0: GREEN}
    styles = {0.05: "-", 1.0: "--", 10.0: "-."}
    markers = {0.01: "o", 0.03: "s", 0.08: "^"}

    ax = axes[0]
    for kappa in (0.05, 1.0, 10.0):
        subset = sorted((r for r in rows if r["kappa"] == kappa), key=lambda r: r["a"])
        ax.plot(
            [abs(r["gamma_PPN_unscreened_massless"] - 1.0) for r in subset],
            [-r["delta_r_s_percent"] for r in subset],
            color=colors[kappa], ls=styles[kappa], lw=1.25,
        )
        for r in subset:
            ax.scatter(
                abs(r["gamma_PPN_unscreened_massless"] - 1.0),
                -r["delta_r_s_percent"],
                color=colors[kappa], marker=markers[r["a"]], s=72,
                edgecolor=BLACK, linewidth=0.55, zorder=3,
            )
    ax.axvline(2.3e-5, color=VERMILION, ls="--", lw=1.3, label="Cassini threshold")
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=0.02)
    ax.set(xlabel=r"unscreened $|\gamma_{\rm PPN}-1|$", ylabel=r"$-\Delta r_s/r_s$ [\%]", title="Acoustic leverage versus local-gravity gate")
    kappa_handles = [
        Line2D([0], [0], color=colors[k], ls=styles[k], lw=1.5,
               label=rf"$\kappa_s={k:g}$")
        for k in (0.05, 1.0, 10.0)
    ]
    a_handles = [
        Line2D([0], [0], color=GRAY, marker=markers[a], ls="None", ms=6,
               markeredgecolor=BLACK, label=rf"$a_s={a:g}$")
        for a in (0.01, 0.03, 0.08)
    ]
    first_legend = ax.legend(handles=kappa_handles, frameon=False, fontsize=7,
                             loc="upper left", title="line/colour")
    ax.add_artist(first_legend)
    ax.legend(handles=a_handles, frameon=False, fontsize=7,
              loc="lower right", title="marker")

    ax = axes[1]
    for kappa, color, ls in ((0.05, VERMILION, "-"), (1.0, ORANGE, "--"), (10.0, GREEN, "-.")):
        subset = sorted((r for r in rows if r["kappa"] == kappa), key=lambda r: r["a"])
        ax.plot(
            [r["G_eff_early_over_today_long_range"] for r in subset],
            [r["H0_fixed_acoustic_angle_proxy_from_67p4"] for r in subset],
            color=color, ls=ls, label=rf"$\kappa_s={kappa:g}$",
        )
        for r in subset:
            ax.scatter(
                r["G_eff_early_over_today_long_range"],
                r["H0_fixed_acoustic_angle_proxy_from_67p4"],
                color=color, marker=markers[r["a"]], s=62,
                edgecolor=BLACK, linewidth=0.5, zorder=3,
            )
    ax.axhline(73.04, color=PURPLE, ls=":", lw=1.2, label="73.04 reference")
    ax.set(xlabel=r"$G_{\rm eff,early}/G_{\rm eff,0}$", ylabel=r"rough fixed-angle $H_0$ proxy", title="Diagnostic, not a CMB likelihood")
    ax.legend(frameon=False, fontsize=8)
    finish(fig, out)


def proxy_figure(background: dict, isw: dict, flow: dict, out: Path) -> None:
    brow = {float(r["z"]): r for r in background["rows"]}
    rows = isw["rows_primary"]
    z = np.array([r["z"] for r in rows])
    dz = np.array([brow[float(v)]["delta_D_percent"] for v in z])
    q = np.array([r["delta_Q_W_percent"] for r in rows])
    s = np.array([r["delta_S_ISW_proxy_percent"] for r in rows])
    frow = {float(r["z"]): r for r in flow["rows"]}
    v = np.array([frow[float(vv)]["delta_velocity_carrier_percent"] for vv in z])
    vp = np.array([frow[float(vv)]["delta_velocity_power_carrier_percent"] for vv in z])
    fig, ax = plt.subplots(figsize=(8.2, 4.9), constrained_layout=True)
    ax.plot(z, dz, color=BLUE, marker="o", ls="-", label=r"growth amplitude $D$")
    ax.plot(z, q, color=GREEN, marker="s", ls="--", label=r"Weyl carrier $Q_W$")
    ax.plot(z, s, color=ORANGE, marker="^", ls="-.", label=r"derivative carrier $S_{\rm ISW}^{proxy}$")
    ax.plot(z, v, color=PURPLE, marker="D", ls=":", label=r"velocity carrier $aHfD$")
    ax.plot(z, vp, color=VERMILION, marker="v", ls=(0, (5, 2, 1, 2)), label="velocity-power carrier")
    ax.axhline(0, color=BLACK, lw=0.8)
    ax.set(xlabel="redshift $z$", ylabel=r"model/control difference [\%]", title="Restricted near-GR perturbation carriers")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    ax.text(0.01, 0.02, "Level C: same metric, zero slip, sub-horizon; not projected spectra", transform=ax.transAxes, fontsize=8)
    finish(fig, out)


def inverse_hrc0(y: np.ndarray) -> np.ndarray:
    y = np.maximum(y, 1e-300)
    return np.sqrt((1.0 + np.sqrt(1.0 + 4.0 / y**2)) / 2.0)


def cluster_figure(cluster: dict, out: Path) -> None:
    g_si = 6.674e-11
    msun = 1.989e30
    kpc = 3.086e19
    x = np.linspace(-620, 620, 1001)
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 7.2), constrained_layout=True, sharex=True)
    for ax, (name, cfg) in zip(axes.flat, cluster["inputs"].items()):
        sigma = np.zeros_like(x)
        for x0, mass, width in cfg["bcg"]:
            sigma += mass * msun / (2 * np.pi * (width * kpc) ** 2) * np.exp(-0.5 * ((x - x0) / width) ** 2)
        for x0, mass, width, axis_ratio in cfg["gas"]:
            sigma += mass * msun / (2 * np.pi * width * width * axis_ratio * kpc**2) * np.exp(-0.5 * ((x - x0) / width) ** 2)
        response = inverse_hrc0(2 * np.pi * g_si * sigma / cfg["a_M"]) * sigma
        sigma /= sigma.max()
        response /= response.max()
        ax.plot(x, sigma, color=BLACK, ls="--", lw=1.5, label="input baryonic map")
        ax.plot(x, response, color=BLUE, ls="-", lw=1.5, label="local HRC response")
        peak = x[int(np.argmax(sigma))]
        ax.axvline(peak, color=VERMILION, ls=":", lw=1.2)
        ax.set_title(name)
        ax.set_ylim(0, 1.08)
        ax.text(0.02, 0.04, "same argmax", transform=ax.transAxes, fontsize=8)
    axes[1, 0].set_xlabel("projected $x$ [kpc]")
    axes[1, 1].set_xlabel("projected $x$ [kpc]")
    axes[0, 0].set_ylabel("normalised surface field")
    axes[1, 0].set_ylabel("normalised surface field")
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.suptitle("Synthetic conditional local-HRC test: exact peak-preservation no-go", fontsize=12)
    finish(fig, out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--isw-json", type=Path)
    parser.add_argument("--flow-json", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    background = load(args.data_dir / "R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json")
    scan = load(args.data_dir / "R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json")
    isw = load(args.isw_json or args.data_dir / "R103_RESTRICTED_ISW_LENSING_PROXY_v1.json")
    flow = load(args.flow_json or args.data_dir / "R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json")
    cluster = load(args.data_dir / "R103_CLUSTER_LOCAL_HRC_SYNTHETIC_v1.json")
    background_figure(background, scan, args.output_dir / "r103_ect_background_clocks")
    tradeoff_figure(scan, args.output_dir / "r103_ect_acoustic_ppn_tradeoff")
    proxy_figure(background, isw, flow, args.output_dir / "r103_ect_restricted_perturbation_proxies")
    cluster_figure(cluster, args.output_dir / "r103_cluster_local_no_go")


if __name__ == "__main__":
    main()
