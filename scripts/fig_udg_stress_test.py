#!/usr/bin/env python3
"""

Generate two proposal-only grayscale UDG diagnostic figures:

  (A) fig_udg_stress_test.pdf -- the signed algebraic inverse
      Xi_alg for the corrected Wolf coefficient C=3.  Dispersion
      brackets are mapped as continuous intervals, including the
      interior quadratic minimum when R=1/2 is crossed.  Negative
      Xi_alg is a no-nonnegative-Xi boundary outcome, not a log bar.

  (B) fig_udg_regime_diagram.pdf -- a one-dimensional paired
      comparison, by object, of the acceleration returned by the
      adopted Level-C closure and the acceleration inferred from
      the observed velocity dispersion.  No microscopic field
      coordinate or screening regime is inferred.

Outputs written to figures/.
"""
import os
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D


# ---------- constants ----------
G       = 6.6743e-11
c_SI    = 2.998e8
M_sun   = 1.989e30
kpc     = 3.086e19
H0      = 67.4e3 / 3.086e22
g_dag0  = c_SI * H0 / (2 * math.pi)
WOLF_C  = 3.0

# name, M*/Msun, Re/kpc, sigma central/low/high [km/s], category.
# The low/high bounds are the quoted dispersion brackets used for this
# diagnostic figure.  They are not advertised as a full joint posterior.
OBJECTS = [
    ("NGC 1052--DF4", 1.5e8,  1.60, 6.3,  4.7,  8.8,  "anomalous"),
    ("FCC 224",       1.74e8, 1.89, 7.8,  3.4, 14.5,  "anomalous"),
    ("NGC 1052--DF2", 1.3e8,  2.20, 10.0, 8.6, 14.9, "ambiguous"),
    ("NGC 5846-UDG1", 1.1e8,  2.10, 17.0, 15.0, 19.0, "normal"),
    ("Dragonfly 44",  3.0e8,  4.70, 33.0, 30.0, 36.0, "upper tail"),
]

def wolf_values(Ms, Re, sigma):
    """Wolf C=3 diagnostic at r_1/2=4 Re/3; Xi_alg is kept signed."""
    R_half = (4.0 / 3.0) * Re * kpc
    M_bar_half = 0.5 * Ms * M_sun
    g_N = G * M_bar_half / R_half**2
    g_obs = WOLF_C * (sigma * 1e3)**2 / R_half
    r = g_obs / g_N
    Xi_alg = r * (r - 1.0) * g_N / g_dag0
    return {
        "r": r, "Xi_alg": Xi_alg, "g_N": g_N,
        "g_obs": g_obs, "R_half_m": R_half,
    }

ROWS = []
for name, Ms, Re, sig, sig_lo, sig_hi, cat in OBJECTS:
    cen = wolf_values(Ms, Re, sig)
    lo = wolf_values(Ms, Re, sig_lo)
    hi = wolf_values(Ms, Re, sig_hi)
    alpha = cen["g_N"] / g_dag0
    crosses_vertex = lo["r"] <= 0.5 <= hi["r"]
    endpoint_values = [lo["Xi_alg"], hi["Xi_alg"]]
    image_min = -alpha / 4.0 if crosses_vertex else min(endpoint_values)
    image_max = max(endpoint_values)
    ROWS.append({
        "name": name, "Mstar_Msun": Ms, "Re_kpc": Re,
        "sigma_kms": sig, "sigma_low_kms": sig_lo,
        "sigma_high_kms": sig_hi, "category": cat,
        **cen,
        "r_sigma_low_endpoint": lo["r"],
        "r_sigma_high_endpoint": hi["r"],
        "Xi_sigma_low_endpoint": lo["Xi_alg"],
        "Xi_sigma_high_endpoint": hi["Xi_alg"],
        "Xi_interval_image_min": image_min,
        "Xi_interval_image_max": image_max,
        "interval_crosses_R_vertex_half": crosses_vertex,
        "admissible_nonnegative_Xi": cen["Xi_alg"] >= 0.0,
    })

shade_map = {
    "anomalous": 0.15, "ambiguous": 0.55,
    "normal": 0.35, "upper tail": 0.70,
}

def figure_A():
    fig = plt.figure(figsize=(9.2, 5.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[3.6, 1.05], wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    lax = fig.add_subplot(gs[0, 1])
    lax.axis("off")

    y_floor = 1.0e-4
    ax.axhspan(0.5, 2.0, facecolor="0.88", edgecolor="none", zorder=0)
    ax.axhline(1.0, color="0.55", lw=1.0, ls=":", zorder=1)
    ax.text(0.03, 0.91, r"RAR-normal reference  $\Xi\sim O(1)$",
            transform=ax.transAxes, color="0.25", fontsize=9,
            ha="left", va="bottom")

    for i, row in enumerate(ROWS):
        xi = row["Xi_alg"]
        lo = row["Xi_interval_image_min"]
        hi = row["Xi_interval_image_max"]
        col = str(shade_map[row["category"]])
        if xi >= 0.0:
            ax.bar(i, xi, width=0.55, color=col, edgecolor="0.1",
                   linewidth=0.9, zorder=3)
            low_plot = max(lo, y_floor)
            high_plot = max(hi, xi)
            ax.errorbar(
                i, xi,
                yerr=[[max(xi-low_plot, 0.0)], [max(high_plot-xi, 0.0)]],
                fmt="none", ecolor="0.2", capsize=4, capthick=1.2,
                lw=1.2, zorder=4,
            )
            if lo < 0.0:
                ax.annotate("", xy=(i, y_floor), xytext=(i, y_floor*4),
                            arrowprops=dict(arrowstyle="-|>", color="0.2",
                                            lw=1.0), zorder=5)
        else:
            # Negative Xi is outside the admissible Xi>=0 model domain:
            # show a boundary marker rather than an artificial log bar.
            ax.plot(i, y_floor*1.35, marker="X", ms=8, color=col,
                    markeredgecolor="0.05", zorder=5)
            if hi > 0:
                ax.vlines(i, y_floor*1.35, hi, color=col, ls="--",
                          lw=1.1, zorder=3)
                ax.plot(i, hi, marker="_", ms=10, color=col, zorder=4)
            ax.annotate(r"central: no $\Xi\geq0$ solution",
                        xy=(i, y_floor*1.35), xytext=(i+0.10, 4e-4),
                        fontsize=7.2, rotation=90, va="bottom",
                        ha="left", color="0.15")

    ax.set_yscale("log")
    ax.set_ylim(y_floor, 2.0e1)
    ax.set_xticks(np.arange(len(ROWS)))
    ax.set_xticklabels([row["name"] for row in ROWS],
                       rotation=20, ha="right")
    ax.set_ylabel(r"Algebraic inverse $\Xi_{\rm alg}$ (positive domain shown)")
    ax.set_title(
        "UDG inverse diagnostic with the corrected Wolf coefficient C=3\n"
        "(bars: central values; brackets: full continuous interval images)",
        fontsize=10.3, pad=10)
    ax.grid(True, which="major", axis="y", color="0.85", lw=0.5)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    handles = [
        mpatches.Patch(color=str(shade_map["anomalous"]),
                       label="low-dispersion\nstress cases"),
        mpatches.Patch(color=str(shade_map["ambiguous"]),
                       label="ambiguous (DF2)"),
        mpatches.Patch(color=str(shade_map["normal"]),
                       label="matched control"),
        mpatches.Patch(color=str(shade_map["upper tail"]),
                       label="upper tail"),
        Line2D([], [], marker="X", color="0.15", linestyle="none",
               label=r"no central $\Xi\geq0$ solution"),
    ]
    lax.legend(handles=handles, loc="center left", fontsize=8.1,
               framealpha=0.95, edgecolor="0.7", borderpad=0.6,
               labelspacing=0.85)
    lax.text(
        0.02, 0.08,
        "Bracket display:\nfull continuous image of\nquoted dispersion interval;\nnegative part ends at the\nXi=0 model boundary.\nNot a full nuisance posterior.",
        transform=lax.transAxes, fontsize=7.5, va="bottom",
        ha="left", color="0.20")

    plt.subplots_adjust(left=0.09, right=0.995, top=0.86, bottom=0.22)
    out_pdf = os.path.join("figures", "fig_udg_stress_test.pdf")
    out_png = os.path.join("figures", "fig_udg_stress_test.png")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_pdf}")
    print(f"Wrote {out_png}")

def write_values():
    payload = {
        "schema_version": 1,
        "status": "PROPOSAL_ONLY",
        "wolf_coefficient_C": WOLF_C,
        "R_half_over_Re": 4.0/3.0,
        "Mbar_half_over_Mstar": 0.5,
        "g_dagger0_m_s2": g_dag0,
        "uncertainty_scope": (
            "full continuous images of quoted dispersion brackets at fixed "
            "central Mstar and Re, including an interior R=1/2 minimum; "
            "not a full joint nuisance posterior"
        ),
        "diagnostic_quantity": (
            "signed algebraic inverse Xi_alg=alpha*r*(r-1); negative values "
            "mean no admissible nonnegative-Xi solution"
        ),
        "rows": ROWS,
    }
    out = os.path.join("figures", "udg_wolf_c3_values.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote {out}")

# ============================================================
# FIGURE B: regime-diagram positioning
# ============================================================

def figure_B():
    """Paired acceleration comparison; no microscopic field axis is assumed."""
    fig, ax = plt.subplots(figsize=(9.2, 4.9))

    names, y_cl, y_obs, cats = [], [], [], []
    for row in ROWS:
        name = row["name"]
        g_N = row["g_N"]
        cat = row["category"]
        g_cl = 0.5 * (g_N + math.sqrt(g_N*g_N + 4 * g_N * g_dag0))
        g_obs = row["g_obs"]
        names.append(name)
        y_cl.append(math.log10(g_cl / g_dag0))
        y_obs.append(math.log10(g_obs / g_dag0))
        cats.append(cat)

    shade = {"anomalous": "0.15", "ambiguous": "0.45",
             "normal": "0.35", "upper tail": "0.70"}
    x = np.arange(len(names), dtype=float)
    for i, (yc, yo, cat) in enumerate(zip(y_cl, y_obs, cats)):
        col = shade[cat]
        ax.plot(i - 0.08, yc, marker="D", markersize=8,
                markerfacecolor="white", markeredgecolor=col,
                markeredgewidth=1.6, zorder=4)
        ax.plot(i + 0.08, yo, marker="o", markersize=9,
                markerfacecolor=col, markeredgecolor="0.05",
                markeredgewidth=0.8, zorder=5)
        ax.plot([i - 0.08, i + 0.08], [yc, yo], color=col,
                lw=1.2, zorder=3)

    ax.axhline(0.0, color="0.55", lw=0.8, ls="--")
    ax.text(0.01, 0.98, r"$g=g^\dagger_0$", transform=ax.transAxes,
            ha="left", va="top", fontsize=8, color="0.35")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=18, ha="right")
    ax.set_xlim(-0.55, len(names) - 0.45)
    ax.set_ylim(-3.0, 1.2)
    ax.set_ylabel(r"$\log_{10}(g/g^{\dagger}_{0})$")
    ax.set_xlabel("Reference object")
    ax.set_title(
        "UDG acceleration stress test: adopted Level-C closure output "
        "versus observed kinematics",
        fontsize=10.5, pad=10)

    ax.plot([], [], marker="D", linestyle="none", markersize=8,
            markerfacecolor="white", markeredgecolor="0.15",
            markeredgewidth=1.6,
            label="adopted closure output from baryons (Level C)")
    ax.plot([], [], marker="o", linestyle="none", markersize=9,
            markerfacecolor="0.35", markeredgecolor="0.05",
            markeredgewidth=0.8,
            label=r"acceleration inferred from observed $\sigma$")
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95,
              edgecolor="0.7")
    ax.grid(True, which="major", axis="y", color="0.88", lw=0.5)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    plt.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.23)
    out_pdf = os.path.join("figures", "fig_udg_regime_diagram.pdf")
    out_png = os.path.join("figures", "fig_udg_regime_diagram.png")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_pdf}")
    print(f"Wrote {out_png}")

if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)
    figure_A()
    figure_B()
    write_values()
