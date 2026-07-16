#!/usr/bin/env python3
"""Render the accepted phenomenological regime schematic.

This is deliberately not a calibrated phi-versus-acceleration phase diagram:
there is no derived u<->chi map, density-screening boundary, body charge or
PPN placement in the current closure.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "fig_regime_diagram.png"

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.linewidth": 0.5,
    "xtick.direction": "in", "ytick.direction": "in",
})

fig, ax = plt.subplots(figsize=(7, 4.8))
ax.axhspan(0, 2, color="0.92", zorder=0)
ax.axhspan(-2, 0, color="0.98", zorder=0)
ax.axhline(0, color="black", lw=1.0)
ax.text(0.04, 0.08, r"$g=g^\dagger$", transform=ax.get_yaxis_transform(),
        ha="left", va="bottom")

ax.text(0.5, 1.05,
        "High-acceleration Newtonian asymptote\nof the adopted closure",
        ha="center", va="center", fontweight="bold")
ax.text(0.5, -0.72,
        "Low-acceleration phenomenological branch",
        ha="center", va="center", fontweight="bold")

ax.text(0.5, -1.48,
        "Canonical screening mass, composite-body charge,\n"
        "and PPN reachability: Open",
        ha="center", va="center",
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white",
              "edgecolor": "black", "linestyle": "--", "linewidth": 1.0})

ax.set_xlim(0, 1)
ax.set_ylim(-2, 2)
ax.set_xticks([])
ax.set_yticks([-2, -1, 0, 1, 2])
ax.set_yticklabels([r"$10^{-2}$", r"$10^{-1}$", r"$1$", r"$10$", r"$10^2$"])
ax.set_xlabel(r"Closure coordinate (schematic; no calibrated $u\leftrightarrow\chi$ map)")
ax.set_ylabel(r"$g/g^\dagger$")
ax.set_title("Phenomenological regime schematic (not a derived phase diagram)",
             fontweight="bold")
ax.tick_params(which="both", right=True)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=220, bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT}")
