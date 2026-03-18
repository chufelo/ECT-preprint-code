#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Updated g_dagger analysis from the new ECT SPARC pipeline."""
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
    args = parser.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    sparc   = load_sparc_mrt(args.mrt)
    results = load_fit_results(args.results)
    gdag0   = gdag0_cH0_over_2pi(args.h0)

    rows = []
    for galaxy, gdf in sparc.groupby("galaxy"):
        try:
            row  = get_result_row(results, galaxy)
            gdag = get_fixed_ml_gdag_si(row)
        except KeyError:
            continue
        if len(gdf) < 6:
            continue

        ml_d  = get_ml_disk_fixed(row, 0.5)
        R     = gdf["R_kpc"].to_numpy()
        Vobs  = gdf["Vobs_kms"].to_numpy()
        eV    = gdf["e_Vobs_kms"].to_numpy()
        Vgas  = gdf["Vgas_kms"].to_numpy()
        Vdisk = gdf["Vdisk_kms"].to_numpy()
        Vbul  = gdf["Vbul_kms"].to_numpy()

        vbar2 = baryonic_v2_kms2(Vgas, Vdisk, Vbul, ml_d, ML_BUL)
        gbar  = g_from_v2_and_R(vbar2, R)
        _, _, tail_mask = estimate_tail_velocity(R, Vobs, eV, 0.25, 3)
        mbar_eff = estimate_outer_effective_baryonic_mass(R, gbar, tail_mask)

        rows.append({
            "galaxy":             galaxy,
            "clean":              get_clean_flag(row),
            "Mbar_eff_Msun":      mbar_eff,
            "Sigma_bar_proxy":    row.get("Sigma_bar_proxy", np.nan)
                                  if "Sigma_bar_proxy" in row.index else np.nan,
            "gdag_fit_si":        gdag,
            "gdag_over_a0":       gdag / A0_MOND,
            "gdag_over_cH0_2pi":  gdag / gdag0,
        })

    df = pd.DataFrame(rows).dropna(subset=["gdag_fit_si"])
    df.to_csv(outdir / "ect_gdagger_analysis_results.csv", index=False)
    print(f"g†-analysis: {len(df)} galaxies")

    apply_bw_matplotlib_style(plt)
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.5))

    # ── Panel A: g†_eff vs Mbar_eff ───────────────────────────────────────────
    ax = axes[0]
    clean = df["clean"].to_numpy().astype(bool)
    logM  = np.log10(df["Mbar_eff_Msun"].to_numpy())
    logg  = np.log10(df["gdag_fit_si"].to_numpy())
    mask_valid = np.isfinite(logM) & np.isfinite(logg)

    ax.scatter(logM[mask_valid & ~clean], logg[mask_valid & ~clean],
               s=16, facecolors="white", edgecolors="0.55", lw=0.7, label="SPARC (flagged)", zorder=2)
    ax.scatter(logM[mask_valid & clean],  logg[mask_valid & clean],
               s=16, facecolors="0.35",  edgecolors="0.20", lw=0.5, label="SPARC (clean)",   zorder=3)

    ax.axhline(np.log10(A0_MOND), color="0.45", ls="--", lw=2.0, label=r"MOND $a_0$")
    ax.axhline(np.log10(gdag0),   color="black",  ls="-",  lw=2.2,
               label=r"ECT baseline $cH_0/(2\pi)$")

    # IQR band for clean sample
    if clean.sum() > 4:
        q1, q3 = np.nanpercentile(logg[clean & mask_valid], [25, 75])
        ax.axhspan(q1, q3, color="0.90", zorder=0, label="clean-sample IQR")

    # highlight selected
    highlight = {"NGC3198":"o","NGC2403":"s","DDO154":"D","NGC6503":"^","UGC02885":"v"}
    for gal, mk in highlight.items():
        sub = df.loc[df["galaxy"].map(normalize_name) == gal]
        if len(sub) == 0: continue
        xx = np.log10(sub.iloc[0]["Mbar_eff_Msun"])
        yy = np.log10(sub.iloc[0]["gdag_fit_si"])
        if np.isfinite(xx) and np.isfinite(yy):
            ax.scatter([xx],[yy], s=100, marker=mk, color="0.10", zorder=5)
            ax.annotate(gal.replace("UGC0","UGC "), (xx, yy),
                        xytext=(5,4), textcoords="offset points", fontsize=9)

    ax.set_xlabel(r"$\log_{10}(M_\mathrm{bar,eff}/M_\odot)$", fontsize=12)
    ax.set_ylabel(r"$\log_{10}(g^\dagger_\mathrm{eff}\ [\mathrm{m\,s^{-2}}])$", fontsize=12)
    ax.set_title(r"(a) Fitted $g^\dagger_\mathrm{eff}$ vs. effective baryonic mass", fontsize=12)
    ax.legend(frameon=True, fontsize=9, loc="upper right")

    # ── Panel B: bar chart g†/a0 for selected ─────────────────────────────────
    ax = axes[1]
    sel_names = ["UGC 2885","NGC 6503","DDO 154","NGC 2403","NGC 3198"]
    sel_keys  = ["UGC02885","NGC6503","DDO154","NGC2403","NGC3198"]
    mk_list   = ["v","^","D","s","o"]

    vals, labels = [], []
    for lab, key in zip(sel_names, sel_keys):
        sub = df.loc[df["galaxy"].map(normalize_name) == key]
        if len(sub):
            vals.append(sub.iloc[0]["gdag_over_a0"])
            labels.append(lab)

    y = np.arange(len(labels))
    bars = ax.barh(y, vals, color="0.72", edgecolor="0.15", height=0.55)
    # shade bars above/below 1
    for bar, v in zip(bars, vals):
        bar.set_facecolor("0.45" if v > 1.0 else "0.80")

    ax.axvline(1.0, color="black", ls="--", lw=2.2,
               label=r"MOND: $g^\dagger/a_0=1$")
    ax.axvline(gdag0/A0_MOND, color="0.40", ls=":", lw=1.8,
               label=r"ECT: $cH_0/(2\pi)/a_0$")

    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel(r"$g^\dagger_\mathrm{eff}/a_0$", fontsize=12)
    ax.set_title(r"(b) Deviation of $g^\dagger_\mathrm{eff}$ from universal $a_0$", fontsize=12)
    ax.legend(frameon=True, fontsize=10)

    fig.tight_layout()
    fig.savefig(outdir / "fig_gdagger_analysis_new_bw.pdf", dpi=300)
    fig.savefig(outdir / "fig_gdagger_analysis_new_bw.png", dpi=220)
    plt.close()
    print("g†-analysis saved.")

if __name__ == "__main__":
    main()
