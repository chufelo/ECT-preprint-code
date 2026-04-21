#!/usr/bin/env python3
"""
Generate two grayscale figures for the UDG stress-test section of the ECT
preprint:

  (A) fig_udg_stress_test.pdf -- bar chart of diagnostic Xi_req for the
      five spherical reference objects, with RAR-normal band and 95% CL
      nuisance-budget error bars.  Legend moved to an external panel on
      the right so that it does not overlap the bars or the "RAR-normal"
      band label.

  (B) fig_udg_regime_diagram.pdf -- positioning of the UDG reference
      objects in the (phi, log10 g/g_dagger) regime plane, contrasting
      the location predicted by the closure from baryonic density (open
      markers, MOND-like branch) with the location implied by the
      observed kinematics (filled markers, near Newton).  Makes visible
      the sharp mismatch that defines the stress test and explicitly
      mirrors the preprint's existing ECT regime diagram.

Outputs written to figures/.
"""
import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------- constants ----------
G       = 6.6743e-11
c_SI    = 2.998e8
M_sun   = 1.989e30
kpc     = 3.086e19
H0      = 67.4e3 / 3.086e22
g_dag0  = c_SI * H0 / (2 * math.pi)

# ---------- objects for bar chart ----------
# (name, Xi_req_central, err_low, err_high, category)
objects = [
    ("NGC 1052--DF4",   1.0e-3,  1.0e-4, 1.5e-1, "anomalous"),
    ("FCC 224",         2.0e-2,  2.0e-3, 2.0e-1, "anomalous"),
    ("NGC 1052--DF2",   0.5,     0.1,    1.4,    "ambiguous"),
    ("NGC 5846-UDG1",   1.6,     1.0,    2.5,    "normal"),
    ("Dragonfly 44",    8.9,     5.0,    15.0,   "upper tail"),
]
shade_map = {
    "anomalous":  0.15,
    "ambiguous":  0.55,
    "normal":     0.35,
    "upper tail": 0.70,
}

# ============================================================
# FIGURE A: bar chart diagnostic
# ============================================================
def figure_A():
    # GridSpec: left panel = chart, right panel = legend (external)
    fig = plt.figure(figsize=(9.0, 4.8))
    gs  = fig.add_gridspec(1, 2, width_ratios=[3.4, 1.0], wspace=0.03)
    ax  = fig.add_subplot(gs[0, 0])
    lax = fig.add_subplot(gs[0, 1])
    lax.axis("off")

    # Shaded RAR-normal band
    ax.axhspan(0.5, 2.0, facecolor="0.88", edgecolor="none", zorder=0)
    ax.axhline(1.0, color="0.55", lw=1.0, ls=":", zorder=1)
    # RAR-normal label placed at LEFT side where there are no tall bars
    ax.text(0.03, 1.12, r"RAR-normal band  $\Xi\!\sim\!O(1)$",
            transform=ax.transAxes, color="0.25", fontsize=9,
            ha="left", va="bottom")

    xs = np.arange(len(objects))
    for i, (name, Xi, lo, hi, cat) in enumerate(objects):
        shade = str(shade_map[cat])
        ax.bar(i, Xi, width=0.55, color=shade, edgecolor="0.1",
               linewidth=0.9, zorder=3)
        ax.errorbar(i, Xi, yerr=[[Xi - lo], [hi - Xi]], fmt="none",
                    ecolor="0.2", capsize=4, capthick=1.2, lw=1.2, zorder=4)

    ax.set_yscale("log")
    ax.set_ylim(5e-4, 5e1)
    ax.set_xticks(xs)
    ax.set_xticklabels([o[0] for o in objects], rotation=20, ha="right")
    ax.set_ylabel(r"Required $\Xi_{\rm req}$ at baseline $g^{\dagger}_{0}$")
    ax.set_title(
        "DM-deficient UDG stress test of the current Level-B galactic closure"
        "\n"
        r"$\Xi_{\rm req}=r(r-1)\,g_N/g^{\dagger}_{0}$,  evaluated at  $R_{1/2}=\frac{4}{3}R_e$",
        fontsize=10.5, pad=10)
    ax.grid(True, which="major", axis="y", color="0.85", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    # External legend (in right panel, no overlap with chart)
    handles = [
        mpatches.Patch(color=str(shade_map["anomalous"]),
                       label="anomalously cold\n(DF4, FCC 224)"),
        mpatches.Patch(color=str(shade_map["ambiguous"]),
                       label="observationally\nambiguous (DF2)"),
        mpatches.Patch(color=str(shade_map["normal"]),
                       label="matched DM-rich\ncontrol (NGC 5846-UDG1)"),
        mpatches.Patch(color=str(shade_map["upper tail"]),
                       label="upper tail\n(Dragonfly 44)"),
    ]
    lax.legend(handles=handles, loc="center left", fontsize=8.2,
               framealpha=0.95, edgecolor="0.7", borderpad=0.6,
               labelspacing=0.9)
    lax.text(0.02, 0.12,
             "Error bars:\n95% CL nuisance band\n(distance, M/L,\nsmall-$N$, anisotropy)",
             transform=lax.transAxes, fontsize=7.8, va="bottom", ha="left",
             color="0.20")

    plt.subplots_adjust(left=0.09, right=0.995, top=0.88, bottom=0.20)
    out_pdf = os.path.join("figures", "fig_udg_stress_test.pdf")
    out_png = os.path.join("figures", "fig_udg_stress_test.png")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_pdf}")
    print(f"Wrote {out_png}")


# ============================================================
# FIGURE B: regime-diagram positioning
# ============================================================
def figure_B():
    """
    Show in the (phi, log10 g/g_dagger) plane where the reference UDGs
    would sit according to the current closure applied to their
    baryonic content (open markers, on the MOND-like branch) versus
    where their observed kinematics place them (filled markers).
    """
    fig, ax = plt.subplots(figsize=(8.4, 4.8))

    # Regime bands (qualitative, mirroring preprint Fig. 18)
    # Vertical axis: log10(g / g_dagger_0)
    # Horizontal axis: phi = ln(chi / chi_vac), qualitative
    ax.axhspan( 0.5,  3.0, facecolor="0.95", edgecolor="none", zorder=0)  # Newton / screened
    ax.axhspan(-0.5,  0.5, facecolor="0.90", edgecolor="none", zorder=0)  # RAR-normal
    ax.axhspan(-3.5, -0.5, facecolor="0.82", edgecolor="none", zorder=0)  # MOND-like / deep-MOND
    ax.axhline( 0.5, color="0.5", lw=0.8, ls="--")
    ax.axhline(-0.5, color="0.5", lw=0.8, ls="--")

    ax.text(0.02, 0.92, "Newtonian / screened branch",
            transform=ax.transAxes, color="0.30", fontsize=9)
    ax.text(0.02, 0.50, "RAR-normal strip  ($\\Xi\\!\\sim\\!O(1)$)",
            transform=ax.transAxes, color="0.30", fontsize=9)
    ax.text(0.02, 0.08, "MOND-like critical / deep-MOND branch",
            transform=ax.transAxes, color="0.30", fontsize=9)

    # Objects: (name, phi_x, g_closure_expected, g_observed, category)
    # phi_x ordering is qualitative: dense systems to the right, diffuse
    # low-phi systems to the left.  Values chosen only for presentation.
    obj = [
        # name,           phi_x, log10(g/g†)_closure_expected, log10(g/g†)_observed, cat
        ("NGC 1052--DF4", 0.3, -1.6, -1.8, "anomalous"),  # closure->deep-MOND, obs->also low but Newton-like in terms of r
        # Note: here "closure expected" means the MOND-branch acceleration at their g_N;
        # "observed" means the g inferred from sigma_obs, which is near g_N itself.
        ("FCC 224",       0.5, -1.4, -1.55, "anomalous"),
        ("NGC 1052--DF2", 0.6, -1.3, -0.8, "ambiguous"),
        ("NGC 5846-UDG1", 0.8, -0.5, -0.5, "normal"),
        ("Dragonfly 44",  1.2,  0.0, +0.4, "upper tail"),
    ]

    # Replace the (g_closure_expected, g_observed) pairs with physically
    # meaningful values based on (g_N, g from sigma_obs).
    # For each object compute: g_N = GM_bar/R_1/2^2 (Newton-only), and
    # g_obs = 3 sigma_obs^2 / R_1/2 (from Wolf).  Then closure MOND branch
    # expects roughly sqrt(g_N * g_dag0) when g_N << g_dag0.
    data = [
        # name,           M*/Msun,  R_e/kpc,   sigma/kms,   phi_x,  cat
        ("NGC 1052--DF4", 1.5e8,    1.6,       6.3,         0.3,  "anomalous"),
        ("FCC 224",       1.74e8,   1.89,      7.8,         0.5,  "anomalous"),
        ("NGC 1052--DF2", 1.3e8,    2.2,       10.0,        0.6,  "ambiguous"),
        ("NGC 5846-UDG1", 1.1e8,    2.1,       17.0,        0.8,  "normal"),
        ("Dragonfly 44",  3.0e8,    4.7,       33.0,        1.2,  "upper tail"),
    ]

    xs_phi  = []
    ys_expc = []   # log10(g_closure / g_dag0) at MOND branch
    ys_obs  = []   # log10(g_obs      / g_dag0)
    names   = []
    cats    = []
    for name, Ms, Re, sig, phi, cat in data:
        M_bar_half = 0.5 * Ms * M_sun
        R_half     = (4.0/3.0) * Re * kpc
        g_N        = G * M_bar_half / R_half**2
        # Closure at baseline: g_closure = 0.5*(g_N + sqrt(g_N^2 + 4 g_N g_dag0))
        g_closure  = 0.5 * (g_N + math.sqrt(g_N*g_N + 4 * g_N * g_dag0))
        # Observed acceleration at R_1/2: g_obs = 3 sigma^2 / R_1/2
        g_obs      = 3.0 * (sig * 1e3)**2 / R_half
        xs_phi.append(phi)
        ys_expc.append(math.log10(g_closure / g_dag0))
        ys_obs.append(math.log10(g_obs / g_dag0))
        names.append(name)
        cats.append(cat)

    # Plot: open markers for closure-expected, filled markers for observed.
    shade = {"anomalous": "0.15", "ambiguous": "0.45",
             "normal": "0.35", "upper tail": "0.70"}

    for phi, y_e, y_o, nm, cat in zip(xs_phi, ys_expc, ys_obs, names, cats):
        col = shade[cat]
        # closure-expected (open diamond)
        ax.plot(phi, y_e, marker="D", markersize=9, markerfacecolor="white",
                markeredgecolor=col, markeredgewidth=1.7, zorder=4)
        # observed (filled circle)
        ax.plot(phi, y_o, marker="o", markersize=10, markerfacecolor=col,
                markeredgecolor="0.05", markeredgewidth=0.8, zorder=5)
        # connector arrow if mismatch is significant
        if abs(y_e - y_o) > 0.08:
            ax.annotate("", xy=(phi, y_o), xytext=(phi, y_e),
                        arrowprops=dict(arrowstyle="-|>,head_width=0.22,head_length=0.35",
                                        color=col, lw=1.4, shrinkA=7, shrinkB=7),
                        zorder=3)
        # label
        label_y = y_o + 0.25 if y_o > y_e else y_o - 0.25
        va = "bottom" if y_o > y_e else "top"
        ax.annotate(nm, xy=(phi, y_o), xytext=(phi + 0.05, label_y),
                    fontsize=8.5, va=va, ha="left", color="0.1", zorder=6)

    ax.set_xlim(-0.2, 1.9)
    ax.set_ylim(-3.0, 2.0)
    ax.set_xlabel(r"$\phi = \ln(\chi/\chi_{\rm vac})$  (qualitative)")
    ax.set_ylabel(r"$\log_{10}(g/g^{\dagger}_{0})$")
    ax.set_title(
        "Mismatch between closure-expected and observed acceleration\n"
        "for the UDG reference objects in the ECT regime plane",
        fontsize=10.5, pad=10)

    # Legend: open diamond = closure-expected, filled circle = observed
    ax.plot([], [], marker="D", linestyle="none", markersize=9,
            markerfacecolor="white", markeredgecolor="0.15",
            markeredgewidth=1.7, label="closure prediction from baryons only")
    ax.plot([], [], marker="o", linestyle="none", markersize=10,
            markerfacecolor="0.35", markeredgecolor="0.05",
            markeredgewidth=0.8, label="acceleration inferred from observed $\\sigma$")
    ax.legend(loc="upper right", fontsize=8.8, framealpha=0.95,
              edgecolor="0.7")

    ax.grid(True, which="major", color="0.88", lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    plt.subplots_adjust(left=0.09, right=0.98, top=0.88, bottom=0.14)
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
