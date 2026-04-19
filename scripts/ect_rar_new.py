#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAR 6-panel figure from the new ECT galactic closure."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ect_sparc_plot_utils import *

ML_BUL   = 0.7
SELECTED = ["NGC3198","NGC2403","DDO154","NGC6503","UGC02885"]
MARKERS  = {"NGC3198":"o","NGC2403":"s","DDO154":"^","NGC6503":"D","UGC02885":"v"}
PANEL_LABELS = {
    "NGC3198":  "(a) NGC 3198\n(Sb, large spiral)",
    "NGC2403":  "(b) NGC 2403\n(SABcd, medium spiral)",
    "DDO154":   "(c) DDO 154\n(IBm, gas-rich dwarf)",
    "NGC6503":  "(d) NGC 6503\n(Sc, edge-on spiral)",
    "UGC02885": "(e) UGC 2885\n(Sb, giant spiral)",
}

def get_gdf(sparc, galaxy_norm_key):
    gdf = sparc.loc[sparc["galaxy_norm"] == galaxy_norm_key]
    if len(gdf) == 0:
        # fallback: try without spaces/dashes
        gdf = sparc.loc[sparc["galaxy"].map(normalize_name) == galaxy_norm_key]
    return gdf

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mrt",     required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--outdir",  required=True)
    parser.add_argument("--h0",      type=float, default=70.0)
    args = parser.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    sparc   = load_sparc_mrt(args.mrt)
    results = load_fit_results(args.results)
    gdag0   = gdag0_cH0_over_2pi(args.h0)

    apply_bw_matplotlib_style(plt)
    fig, axes = plt.subplots(2, 3, figsize=(15, 11))
    axes = axes.ravel()

    all_gbar_list, all_gobs_list = [], []

    for i, gal in enumerate(SELECTED):
        ax = axes[i]
        gdf = get_gdf(sparc, gal)
        if len(gdf) == 0:
            ax.set_title(PANEL_LABELS.get(gal, gal), fontsize=11, fontweight="bold", loc="left")
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
            continue

        try:
            row = get_result_row(results, gal)
            gdag_fit = get_fixed_ml_gdag_si(row)
            ml_d     = get_ml_disk_fixed(row, 0.5)
        except (KeyError, Exception) as e:
            print(f"  skip {gal}: {e}")
            continue

        R     = gdf["R_kpc"].to_numpy()
        Vobs  = gdf["Vobs_kms"].to_numpy()
        eV    = gdf["e_Vobs_kms"].to_numpy()
        Vgas  = gdf["Vgas_kms"].to_numpy()
        Vdisk = gdf["Vdisk_kms"].to_numpy()
        Vbul  = gdf["Vbul_kms"].to_numpy()

        vbar2 = baryonic_v2_kms2(Vgas, Vdisk, Vbul, ml_d, ML_BUL)
        gbar  = g_from_v2_and_R(vbar2, R)
        gobs  = gobs_from_Vobs(Vobs, R)

        mask = (gbar > 0) & (gobs > 0) & np.isfinite(gbar) & np.isfinite(gobs)
        gbar, gobs, R, eV, Vobs = gbar[mask], gobs[mask], R[mask], eV[mask], Vobs[mask]

        all_gbar_list.append(gbar)
        all_gobs_list.append(gobs)

        xs     = np.logspace(np.log10(max(gbar.min()*0.6, 1e-14)), np.log10(gbar.max()*1.5), 300)
        g_ect  = ect_g_from_gbar(xs, gdag_fit)
        g_mond = mond_g_from_gbar(xs, A0_MOND)

        yerr = np.clip(np.abs((2*np.maximum(eV,0.5)/np.maximum(Vobs,0.1)) / np.log(10)), 0, 0.35)
        ax.errorbar(np.log10(gbar), np.log10(gobs), yerr=yerr,
                    fmt=MARKERS.get(gal,"o"), color="0.45", mfc="0.45", mec="0.45",
                    ms=6, lw=0.8, capsize=2, label=f"SPARC (N={len(gdf)})")
        ax.plot(np.log10(xs), np.log10(g_mond), color="0.55", ls="--", lw=1.8,
                label=r"MOND ($a_0$ univ.)")
        ax.plot(np.log10(xs), np.log10(g_ect),  color="black", lw=2.2,
                label=fr"ECT ($g^\dagger={gdag_fit/gdag0:.2f}\,cH_0/2\pi$)")

        # guides
        xx = np.linspace(-13, -8, 80)
        ax.plot(xx, xx, color="0.78", lw=1.1)
        ax.text(-9.1, -9.3, "Newton", color="0.55", rotation=36, fontsize=8)
        gg = np.logspace(-13, -9, 100)
        ax.plot(np.log10(gg), np.log10(np.sqrt(gg*A0_MOND)), color="0.72", ls="-.", lw=1.0)
        ax.text(-12.1, -11.2, r"$\sqrt{g_\mathrm{bar}\,a_0}$", color="0.55", rotation=28, fontsize=8)

        ax.set_xlim(-13, -8.5); ax.set_ylim(-12, -8.5)
        ax.set_title(PANEL_LABELS.get(gal, gal), fontsize=11, fontweight="bold", loc="left")
        ax.set_xlabel(r"$\log_{10}[g_\mathrm{bar}\ (\mathrm{m\,s^{-2}})]$", fontsize=10)
        ax.set_ylabel(r"$\log_{10}[g_\mathrm{obs}\ (\mathrm{m\,s^{-2}})]$", fontsize=10)
        ax.legend(frameon=True, fontsize=8, loc="lower right")

    # ── Panel (f): full sample cloud ──────────────────────────────────────────
    ax = axes[5]
    n_plotted = 0
    for galaxy, gdf_all in sparc.groupby("galaxy"):
        try:
            row = get_result_row(results, galaxy)
            ml_d = get_ml_disk_fixed(row, 0.5)
        except KeyError:
            continue
        R    = gdf_all["R_kpc"].to_numpy()
        Vobs = gdf_all["Vobs_kms"].to_numpy()
        Vgas = gdf_all["Vgas_kms"].to_numpy()
        Vdisk= gdf_all["Vdisk_kms"].to_numpy()
        Vbul = gdf_all["Vbul_kms"].to_numpy()
        vbar2 = baryonic_v2_kms2(Vgas, Vdisk, Vbul, ml_d, ML_BUL)
        gbar  = g_from_v2_and_R(vbar2, R)
        gobs  = gobs_from_Vobs(Vobs, R)
        mask  = (gbar>0)&(gobs>0)&np.isfinite(gbar)&np.isfinite(gobs)
        if mask.sum() == 0: continue
        ax.scatter(np.log10(gbar[mask]), np.log10(gobs[mask]),
                   s=5, color="0.80", alpha=0.40, linewidths=0, zorder=1)
        n_plotted += 1

    # overlay selected galaxies
    for gal in SELECTED:
        if len(all_gbar_list) == 0: break
        gdf = get_gdf(sparc, gal)
        if len(gdf) == 0: continue
        try:
            row  = get_result_row(results, gal)
            ml_d = get_ml_disk_fixed(row, 0.5)
        except: continue
        R    = gdf["R_kpc"].to_numpy()
        Vobs = gdf["Vobs_kms"].to_numpy()
        Vgas = gdf["Vgas_kms"].to_numpy()
        Vdisk= gdf["Vdisk_kms"].to_numpy()
        Vbul = gdf["Vbul_kms"].to_numpy()
        vbar2 = baryonic_v2_kms2(Vgas, Vdisk, Vbul, ml_d, ML_BUL)
        gbar  = g_from_v2_and_R(vbar2, R)
        gobs  = gobs_from_Vobs(Vobs, R)
        mask  = (gbar>0)&(gobs>0)&np.isfinite(gbar)&np.isfinite(gobs)
        ax.scatter(np.log10(gbar[mask]), np.log10(gobs[mask]),
                   s=35, marker=MARKERS[gal], color="0.20",
                   edgecolors="0.10", linewidths=0.4,
                   label=gal.replace("UGC0","UGC "), zorder=4)

    xs = np.logspace(-13, -8.5, 300)
    ax.plot(np.log10(xs), np.log10(mond_g_from_gbar(xs, A0_MOND)),
            color="0.50", ls="--", lw=1.8, label="MOND ($a_0$ univ.)")
    ax.plot(np.log10(xs), np.log10(ect_g_from_gbar(xs, gdag0)),
            color="black", lw=2.2, label=r"ECT baseline $cH_0/(2\pi)$")
    xx = np.linspace(-13,-8.5,80)
    ax.plot(xx, xx, color="0.78", lw=1.1)
    ax.text(-9.1,-9.3,"Newton",color="0.55",rotation=36,fontsize=8)
    gg=np.logspace(-13,-9,100)
    ax.plot(np.log10(gg),np.log10(np.sqrt(gg*A0_MOND)),color="0.72",ls="-.",lw=1.0)
    ax.text(-12.1,-11.2,r"$\sqrt{g_\mathrm{bar}\,a_0}$",color="0.55",rotation=28,fontsize=8)

    ax.set_xlim(-13,-8.5); ax.set_ylim(-12,-8.5)
    ax.set_title(f"(f) Full SPARC sample (N={n_plotted} galaxies)\n+ selected", 
                 fontsize=11, fontweight="bold", loc="left")
    ax.set_xlabel(r"$\log_{10}[g_\mathrm{bar}\ (\mathrm{m\,s^{-2}})]$", fontsize=10)
    ax.set_ylabel(r"$\log_{10}[g_\mathrm{obs}\ (\mathrm{m\,s^{-2}})]$", fontsize=10)
    ax.legend(frameon=True, fontsize=8, loc="upper left", ncol=2)

    fig.suptitle("Radial Acceleration Relation — ECT new closure vs MOND",
                 fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(outdir / "ect_rar_new_6panel_bw.pdf", dpi=300, bbox_inches="tight")
    fig.savefig(outdir / "ect_rar_new_6panel_bw.png", dpi=220, bbox_inches="tight")
    plt.close()
    print("RAR saved.")

if __name__ == "__main__":
    main()
