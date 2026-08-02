#!/usr/bin/env python3
"""Render status-safe black-hole kinematics and open-programme diagnostics.

The figure contains only external Tolman/Hawking kinematics and an explicit
inventory of what an ECT black-hole completion still lacks.  It contains no
critical-temperature identification, shell depth, Page curve, or information-
return mechanism.  Colour, line style, markers and hatching are redundant so
the figure remains readable in grayscale.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)

HBAR = 1.054571817e-34
C = 299_792_458.0
G = 6.67430e-11
KB = 1.380649e-23
MSUN = 1.98847e30

# Okabe--Ito roles plus redundant line/marker/hatch channels.
BLUE = "#0072B2"
GREEN = "#009E73"
AMBER = "#E69F00"
VERMILLION = "#D55E00"
NEUTRAL = "#333333"
GRID = "#B8B8B8"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 9.5,
        "mathtext.fontset": "cm",
        "axes.grid": True,
        "grid.color": GRID,
        "grid.alpha": 0.45,
        "grid.linestyle": ":",
    }
)

fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.25), constrained_layout=True)

# (a) Universal dimensionless Tolman kinematics in arbitrary reference units.
ax = axes[0]
x = np.linspace(0.035, 6.0, 1200)
y = 1.0 / x
ax.plot(x, y, color=BLUE, lw=2.2, marker="o", markevery=120, ms=3.0,
        label=r"external kinematics $T_{\rm loc}/T_{\rm ref}=\rho_{\rm ref}/\rho$")
ax.axhline(1.0, color=GREEN, ls="--", lw=1.6, label=r"arbitrary reference $T_{\rm ref}$")
ax.axvline(1.0, color=VERMILLION, ls=":", lw=1.8)
ax.text(1.06, 2.55, r"reference point only: $\rho=\rho_{\rm ref}$",
        rotation=90, va="center", color=VERMILLION)
ax.set(xlim=(0.0, 6.0), ylim=(0.0, 6.0),
       xlabel=r"proper distance $\rho/\rho_{\rm ref}$",
       ylabel=r"$T_{\rm loc}/T_{\rm ref}$",
       title="(a) External Tolman kinematics")
ax.legend(loc="upper right", fontsize=7.4, framealpha=0.93)

# (b) No fine-grained curve is supplied: show only the external benchmark and
# the region in which a future ECT completion would have to determine it.
ax = axes[1]
t = np.linspace(0.0, 1.0, 800)
coarse = np.sqrt(t)
ax.plot(t, coarse, color=VERMILLION, lw=2.0, ls="--", label="coarse-grained (semiclassical)")
ax.fill_between(t, 0.0, coarse, color=AMBER, alpha=0.14, hatch="//",
                edgecolor=AMBER, linewidth=0.0,
                label="fine-grained ECT curve: Open within this region")
ax.text(0.50, 0.23,
        "Missing: Hilbert split, state,\nevaporation channel and Hamiltonian",
        ha="center", va="center", fontsize=8.5, color=NEUTRAL,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": NEUTRAL})
ax.set(xlim=(0.0, 1.0), ylim=(0.0, 1.08),
       xlabel=r"evaporation time $t/t_{\rm evap}$", ylabel=r"normalised entropy",
       title="(b) Semiclassical benchmark; ECT curve Open")
ax.legend(loc="upper left", fontsize=7.4, framealpha=0.93)

# (c) Standard external Hawking benchmark; the ECT-specific object is a status
# statement rather than a fabricated shell-depth curve.
ax = axes[2]
mass_ratio = np.logspace(0.0, 9.0, 500)
mass = mass_ratio * MSUN
th = HBAR * C**3 / (8.0 * np.pi * G * KB * mass)
ax.loglog(mass_ratio, th, color=BLUE, lw=2.2, marker="o", markevery=85,
          ms=3.2, label=r"standard Hawking $T_H(M)$")
ax.text(0.50, 0.25,
        "ECT shell depth: NOT IDENTIFIED\n"
        "requires a P4 control variable, metric,\nstate and transfer map",
        transform=ax.transAxes, ha="center", va="center", fontsize=9.0,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": VERMILLION, "linewidth": 1.5})
ax.set(xlabel=r"black-hole mass $M/M_\odot$", ylabel=r"temperature $T_H$ [K]",
       title="(c) External Hawking benchmark")
ax.legend(loc="upper right", fontsize=7.4, framealpha=0.93)

fig.suptitle(
    "Black-hole external kinematics and ECT completion status",
    fontsize=10.5,
)

metadata = {
    "Title": "Black-hole external kinematics and open ECT completion",
    "Author": "Valeriy Blagovidov",
    "Subject": "No P4 shell depth Page curve or information-return mechanism is derived",
    "CreationDate": datetime(2026, 7, 17, tzinfo=timezone.utc),
    "ModDate": datetime(2026, 7, 17, tzinfo=timezone.utc),
}
fig.savefig(OUT / "fig_bh_information.pdf", dpi=300, metadata=metadata)
plt.close(fig)

print("rendered external Tolman/Hawking benchmarks; all ECT-specific black-hole owners remain Open")
