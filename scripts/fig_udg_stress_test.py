#!/usr/bin/env python3
"""
Generate grayscale figure fig_udg_stress_test for ECT preprint.

Bar chart of the central-value diagnostic Xi_req for the six reference
objects of the UDG stress test, on a log scale, with the RAR-normal
band Xi in [0.5, 2] indicated as a shaded horizontal band.

Output: figures/fig_udg_stress_test.pdf (grayscale, per preprint style).

This accompanies Appendix `app:udg_stress_test`.
"""
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Data: (name, Xi_req_central, err_low, err_high, category)
# "category" controls the bar shade only (darker = stress-low,
# medium = normal RAR, light = upper tail / ambiguous / rotator)
objects = [
    ("NGC 1052--DF4",   1.0e-3,  1.0e-4, 1.5e-1, "stress-low"),
    ("FCC 224",         2.0e-2,  2.0e-3, 2.0e-1, "stress-low"),
    ("NGC 1052--DF2",   0.5,     0.1,    1.4,    "ambiguous"),
    ("NGC 5846-UDG1",   1.6,     1.0,    2.5,    "normal"),
    ("Dragonfly 44",    8.9,     5.0,    15.0,   "upper tail"),
]

shade_map = {
    "stress-low":  0.15,
    "ambiguous":   0.55,
    "normal":      0.35,
    "upper tail":  0.70,
}

fig, ax = plt.subplots(figsize=(7.8, 4.8))

# RAR-normal band (shaded horizontal strip)
ax.axhspan(0.5, 2.0, facecolor="0.88", edgecolor="none", zorder=0)
ax.axhline(1.0, color="0.55", lw=1.0, ls=":", zorder=1)
ax.text(len(objects)-0.5, 1.07, r"RAR-normal band $\Xi\sim O(1)$",
        color="0.35", fontsize=9, ha="right", va="bottom")

# Bars with asymmetric error
xs = np.arange(len(objects))
for i, (name, Xi, lo, hi, cat) in enumerate(objects):
    shade = str(shade_map[cat])
    ax.bar(i, Xi, width=0.6, color=shade, edgecolor="0.1", linewidth=0.9,
           zorder=3)
    # asymmetric error bars in log space: draw from lo to hi
    ax.errorbar(i, Xi, yerr=[[Xi-lo], [hi-Xi]], fmt="none",
                ecolor="0.2", capsize=4, capthick=1.2, lw=1.2, zorder=4)

ax.set_yscale("log")
ax.set_ylim(5e-4, 5e1)
ax.set_xticks(xs)
ax.set_xticklabels([o[0] for o in objects], rotation=20, ha="right")
ax.set_ylabel(r"Required $\Xi_{\rm req}$ at baseline $g^\dagger_0$")

# Legend patches
stress_patch = mpatches.Patch(color=str(shade_map["stress-low"]),
                              label="stress-low (DF4, FCC 224)")
normal_patch = mpatches.Patch(color=str(shade_map["normal"]),
                              label="normal RAR (NGC 5846-UDG1)")
ambig_patch  = mpatches.Patch(color=str(shade_map["ambiguous"]),
                              label="ambiguous (DF2)")
upper_patch  = mpatches.Patch(color=str(shade_map["upper tail"]),
                              label="upper tail (Dragonfly 44)")
ax.legend(handles=[stress_patch, ambig_patch, normal_patch, upper_patch],
          loc="upper left", fontsize=8.5, framealpha=0.95, edgecolor="0.7")

# Title and annotation
ax.set_title(
    r"DM-deficient UDG stress test of the current Level-B galactic closure"
    "\n"
    r"$\Xi_{\rm req}=r(r-1)\,g_N/g^\dagger_0$  evaluated at  $R_{1/2}=\frac{4}{3}R_e$",
    fontsize=10.5, pad=10)

# Error bar explanation text (inside plot)
ax.text(0.02, 0.985, "Error bars: 95% CL nuisance band\n"
        "(distance, $M/L$, small-$N$, anisotropy)",
        transform=ax.transAxes, fontsize=8.2, va="top", ha="left",
        color="0.20",
        bbox=dict(facecolor="white", edgecolor="0.6",
                  boxstyle="round,pad=0.3", alpha=0.9))

ax.grid(True, which="major", axis="y", color="0.85", lw=0.5, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)

plt.tight_layout()
import os
outdir = "figures"
os.makedirs(outdir, exist_ok=True)
fname = os.path.join(outdir, "fig_udg_stress_test.pdf")
plt.savefig(fname, bbox_inches="tight")
plt.close()
print(f"Wrote {fname}")

# Also PNG for web / companion
png = fname.replace(".pdf", ".png")
fig2, ax2 = plt.subplots(figsize=(7.8, 4.8))
# regenerate for PNG
ax2.axhspan(0.5, 2.0, facecolor="0.88", edgecolor="none", zorder=0)
ax2.axhline(1.0, color="0.55", lw=1.0, ls=":", zorder=1)
ax2.text(len(objects)-0.5, 1.07, r"RAR-normal band $\Xi\sim O(1)$",
         color="0.35", fontsize=9, ha="right", va="bottom")
for i, (name, Xi, lo, hi, cat) in enumerate(objects):
    shade = str(shade_map[cat])
    ax2.bar(i, Xi, width=0.6, color=shade, edgecolor="0.1", linewidth=0.9, zorder=3)
    ax2.errorbar(i, Xi, yerr=[[Xi-lo], [hi-Xi]], fmt="none",
                 ecolor="0.2", capsize=4, capthick=1.2, lw=1.2, zorder=4)
ax2.set_yscale("log")
ax2.set_ylim(5e-4, 5e1)
ax2.set_xticks(xs)
ax2.set_xticklabels([o[0] for o in objects], rotation=20, ha="right")
ax2.set_ylabel(r"Required $\Xi_{\rm req}$ at baseline $g^\dagger_0$")
ax2.legend(handles=[stress_patch, ambig_patch, normal_patch, upper_patch],
           loc="upper left", fontsize=8.5, framealpha=0.95, edgecolor="0.7")
ax2.set_title(
    r"DM-deficient UDG stress test of the current Level-B galactic closure"
    "\n"
    r"$\Xi_{\rm req}=r(r-1)\,g_N/g^\dagger_0$  evaluated at  $R_{1/2}=\frac{4}{3}R_e$",
    fontsize=10.5, pad=10)
ax2.text(0.02, 0.985, "Error bars: 95% CL nuisance band\n"
         "(distance, $M/L$, small-$N$, anisotropy)",
         transform=ax2.transAxes, fontsize=8.2, va="top", ha="left",
         color="0.20",
         bbox=dict(facecolor="white", edgecolor="0.6",
                   boxstyle="round,pad=0.3", alpha=0.9))
ax2.grid(True, which="major", axis="y", color="0.85", lw=0.5, zorder=0)
ax2.set_axisbelow(True)
for spine in ("top", "right"):
    ax2.spines[spine].set_visible(False)
plt.tight_layout()
plt.savefig(png, dpi=180, bbox_inches="tight")
plt.close()
print(f"Wrote {png}")
