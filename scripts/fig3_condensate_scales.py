#!/usr/bin/env python3
"""Render the Round-58 dimensionally separated ECT scale inventory.

Proposal only: the output is written beside this script and does not touch
the live publication figure.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parents[1] / "figures" / "fig_condensate_scales.png"

# Frozen inputs for the conditional Level-C fit-length panel.
G_N = 6.67430e-11  # m^3 kg^-1 s^-2
M_SUN = 1.98847e30  # kg
KPC = 3.0856775814913673e19  # m
A_M0 = 1.0824013602e-10  # m s^-2, matched benchmark

PHI_0_GEV = 2.435e18
V2_GEV = 246.22


def main() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.alpha": 0.25,
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.8))

    # Panel (a): compare only quantities with energy dimension.
    x = np.array([0.0, 1.0])
    energies = np.array([PHI_0_GEV, V2_GEV])
    ax1.scatter(x, energies, s=[90, 75], c=["black", "0.4"], zorder=3)
    ax1.set_yscale("log")
    ax1.set_xlim(-0.45, 1.45)
    ax1.set_ylim(1e1, 1e20)
    ax1.set_xticks(x, [r"$\phi_0$", r"$v_2$"])
    ax1.set_ylabel("energy / matching scale [GeV]")
    ax1.set_title("(a) Energy-dimension inventory", loc="left", fontweight="bold")
    ax1.annotate(
        r"$\phi_0\simeq\bar M_{\rm Pl}$" + "\n" + r"$2.435\times10^{18}$ GeV",
        (0.0, PHI_0_GEV), xytext=(20, -10), textcoords="offset points",
        ha="left", va="top", arrowprops={"arrowstyle": "->", "color": "0.5"},
    )
    ax1.annotate(
        r"$v_2=246.22$ GeV" + "\nmatched; origin Open",
        (1.0, V2_GEV), xytext=(-15, 20), textcoords="offset points",
        ha="right", va="bottom", color="0.25",
        arrowprops={"arrowstyle": "->", "color": "0.5"},
    )
    ax1.text(
        0.5, 0.48,
        r"$\phi_0/v_2\simeq9.9\times10^{15}$" + "\nmechanism Open",
        transform=ax1.transAxes, ha="center", va="center",
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "0.55"},
    )

    # Panel (b): a length plotted against the mass on which it depends.
    masses_solar = np.logspace(7, 12, 300)
    r_kpc = np.sqrt(G_N * masses_solar * M_SUN / A_M0) / KPC
    ax2.plot(masses_solar, r_kpc, color="#0072B2", lw=2.0)
    m_ref = 1.0e10
    r_ref = np.sqrt(G_N * m_ref * M_SUN / A_M0) / KPC
    ax2.scatter([m_ref], [r_ref], s=75, color="#D55E00", zorder=3)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"baryonic mass $M_{\rm bar}$ [$M_\odot$]")
    ax2.set_ylabel(r"conditional HRC matching length $L_{\rm gal}=r_*$ [kpc]")
    ax2.set_title("(b) Conditional HRC matching length", loc="left", fontweight="bold")
    ax2.annotate(
        rf"$M_{{\rm bar}}=10^{{10}}M_\odot$" + "\n" + rf"$r_*={r_ref:.1f}$ kpc",
        (m_ref, r_ref), xytext=(20, -25), textcoords="offset points",
        ha="left", va="top", arrowprops={"arrowstyle": "->", "color": "0.5"},
    )
    ax2.text(
        0.04, 0.96,
        r"$r_*=\sqrt{G_NM_{\rm bar}/a_{M0}}$" + "\n"
        + r"$a_{M0}=1.0824\times10^{-10}$ m s$^{-2}$ (matched)",
        transform=ax2.transAxes, ha="left", va="top",
        bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": "0.55"},
    )
    ax2.text(
        0.96, 0.06,
        "No common GeV axis\nNo RG link claimed",
        transform=ax2.transAxes, ha="right", va="bottom", color="0.3",
    )

    fig.tight_layout()
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"SAVED {OUT}")


if __name__ == "__main__":
    main()
