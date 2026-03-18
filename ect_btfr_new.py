#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ECT BTFR plot from the new galactic closure."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ect_sparc_plot_utils import *

ML_BUL = 0.7

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mrt",     required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--outdir",  required=True)
    parser.add_argument("--h0",      type=float, default=70.0)
    parser.add_argument("--tail-frac",  type=float, default=0.25)
    parser.add_argument("--min-points", type=int,   default=6)
    args = parser.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    sparc   = load_sparc_mrt(args.mrt)
    results = load_fit_results(args.results)
    gdag0   = gdag0_cH0_over_2pi(args.h0)

    rows = []
    for galaxy, gdf in sparc.groupby("galaxy"):
        try:
            row = get_result_row(results, galaxy)
        except KeyError:
            continue
        if len(gdf) < args.min_points:
            continue
        try:
            gdag_fit = get_fixed_ml_gdag_si(row)
        except KeyError:
            continue

        ml_disk = get_ml_disk_fixed(row, 0.5)
        R    = gdf["R_kpc"].to_numpy()
        Vobs = gdf["Vobs_kms"].to_numpy()
        eV   = gdf["e_Vobs_kms"].to_numpy()
        Vgas = gdf["Vgas_kms"].to_numpy()
        Vdisk= gdf["Vdisk_kms"].to_numpy()
        Vbul = gdf["Vbul_kms"].to_numpy()

        vbar2 = baryonic_v2_kms2(Vgas, Vdisk, Vbul, ml_disk, ML_BUL)
        gbar  = g_from_v2_and_R(vbar2, R)
        vflat, evflat, tail_mask = estimate_tail_velocity(R, Vobs, eV,
                                        tail_fraction=args.tail_frac, min_points=3)
        if not np.isfinite(vflat):
            continue
        mbar_eff = estimate_outer_effective_baryonic_mass(R, gbar, tail_mask)
        if not np.isfinite(mbar_eff) or mbar_eff <= 0:
            continue

        rows.append({
            "galaxy":   galaxy,
            "clean":    get_clean_flag(row),
            "Vflat_obs_kms":          vflat,
            "eVflat_obs_kms":         evflat,
            "Mbar_eff_Msun":          mbar_eff,
            "gdag_fit_si":            gdag_fit,
            "gdag_fit_over_cH0_2pi":  gdag_fit / gdag0,
        })

    btfr = pd.DataFrame(rows).sort_values("Mbar_eff_Msun")
    btfr.to_csv(outdir / "ect_btfr_results.csv", index=False)
    print(f"BTFR: {len(btfr)} galaxies")

    apply_bw_matplotlib_style(plt)
    fig, ax = plt.subplots(figsize=(8.5, 6.5))

    x = np.log10(btfr["Mbar_eff_Msun"].to_numpy())
    y = np.log10(btfr["Vflat_obs_kms"].to_numpy())
    c = btfr["clean"].to_numpy().astype(bool)

    ax.scatter(x[~c], y[~c], s=24, marker="o", facecolors="white",
               edgecolors="0.55", linewidths=0.8, label="SPARC (flagged)", zorder=3)
    ax.scatter(x[c],  y[c],  s=28, marker="o", facecolors="black",
               edgecolors="black", label="SPARC (clean)", zorder=4)

    xx = np.linspace(np.nanmin(x)-0.3, np.nanmax(x)+0.3, 300)
    def line_logV(logM, gdag):
        M = 10**logM * MSUN
        return np.log10((G_SI * M * gdag)**0.25 / KM)

    ax.plot(xx, line_logV(xx, gdag0),   color="black", lw=2.2,
            label=r"ECT baseline $g^\dagger_0=cH_0/(2\pi)$")
    ax.plot(xx, line_logV(xx, A0_MOND), color="0.40", lw=1.8, ls="--",
            label=r"MOND baseline $a_0$")

    med = btfr["gdag_fit_over_cH0_2pi"].median()
    ax.text(0.03, 0.97,
        f"N = {len(btfr)} galaxies\n"
        f"median($g^\\dagger$/(cH$_0$/2π)) = {med:.2f}\n"
        r"$M_\mathrm{bar,eff}=R_\mathrm{tail}^2\,g_N(R_\mathrm{tail})/G$",
        transform=ax.transAxes, va="top", ha="left", fontsize=10,
        bbox=dict(boxstyle="round", fc="white", ec="0.6"))

    ax.set_xlabel(r"$\log_{10}(M_\mathrm{bar,eff}/M_\odot)$", fontsize=13)
    ax.set_ylabel(r"$\log_{10}(V_\mathrm{flat}/\mathrm{km\,s^{-1}})$", fontsize=13)
    ax.set_title("ECT Baryonic Tully–Fisher Relation (new closure)", fontsize=13)
    ax.legend(frameon=True, fontsize=10, loc='lower right')
    fig.tight_layout()
    fig.savefig(outdir / "ect_btfr_new_bw.pdf", dpi=300)
    fig.savefig(outdir / "ect_btfr_new_bw.png", dpi=200)
    plt.close()
    print("BTFR saved.")

if __name__ == "__main__":
    main()
