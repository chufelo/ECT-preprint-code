#!/usr/bin/env python3
"""
ECT galactic-sector fitting pipeline — phi-branch closure.

ECT phi-branch closure (derived from condensate dynamics):
    g_obs = 0.5 * (g_N + sqrt(g_N^2 + 4*g_N*g†_eff))

Formally identical to the MOND RAR interpolation in the deep limit,
but derived in ECT from the critical phi-branch of the order field.

Two free parameters per galaxy:
  g†_eff    — effective condensate acceleration scale
  ups_disk  — stellar disk mass-to-light ratio

The optimizer uses a 2D grid search near cH0/(2pi) followed by
local refinement to avoid degenerate minima.

Input:  MassModels_Lelli2016c.mrt  (SPARC table2.dat, whitespace-delimited)
        Columns: Galaxy D_Mpc R_kpc Vobs e_Vobs Vgas Vdisk Vbul SBdisk SBbul

Outputs:
  ect_sparc_phi_results.csv     — per-galaxy fit table
  ect_sparc_phi_curves.pdf      — rotation-curve panels
  ect_sparc_phi_histogram.pdf   — g†/(cH0/2pi) summary

Usage:
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt \\
           --galaxies NGC3198 NGC2403 DDO154 NGC6503 UGC2885
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt --n-best 20
"""
from __future__ import annotations
import argparse, math, warnings
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import minimize

warnings.filterwarnings('ignore')

# ── Physical constants ────────────────────────────────────────────────────────
ACC_CONV = 1e6 / 3.0856775814913673e19   # (km/s)^2/kpc → m/s^2
C_SI     = 299792458.0
MPC_TO_M = 3.0856775814913673e22
A0_SI    = 1.20e-10                       # McGaugh+2016 acceleration scale

def cH0_si(h0: float = 70.0) -> float:
    return C_SI * h0 * 1e3 / MPC_TO_M

# ── Data loading ──────────────────────────────────────────────────────────────
def load_sparc(path: str) -> pd.DataFrame:
    """Load SPARC table2.dat (whitespace-delimited, no header row)."""
    rows = []
    with open(path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            try:
                rows.append({
                    'Galaxy': parts[0],
                    'D_Mpc':  float(parts[1]),
                    'R_kpc':  float(parts[2]),
                    'Vobs':   float(parts[3]),
                    'e_Vobs': max(float(parts[4]), 2.0),
                    'Vgas':   float(parts[5]),
                    'Vdisk':  float(parts[6]),
                    'Vbul':   float(parts[7]),
                })
            except (ValueError, IndexError):
                continue
    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} data points, {df['Galaxy'].nunique()} galaxies.")
    return df

# ── ECT phi-branch model ──────────────────────────────────────────────────────
def bary_gN(R, Vg, Vd, Vb, ups_disk=0.5, ups_bul=0.7):
    """Baryonic Newtonian acceleration in (km/s)^2/kpc."""
    Vb2 = ups_bul * np.sign(Vb) * Vb**2
    Vb2 = np.where(Vb2 < 0, 0.0, Vb2)
    return (Vg**2 + ups_disk * Vd**2 + Vb2) / np.maximum(R, 1e-9)

def ect_vmod(R, gN, gdagger_kpc):
    """ECT rotation curve from phi-branch closure."""
    g_obs = 0.5 * (gN + np.sqrt(np.maximum(gN**2 + 4.0*gN*gdagger_kpc, 0.0)))
    return np.sqrt(np.maximum(g_obs * R, 0.0))

# ── Fitting ───────────────────────────────────────────────────────────────────
@dataclass
class GalaxyFit:
    galaxy:        str
    n_points:      int
    gdagger_si:    float
    ups_disk:      float
    chi2:          float
    chi2_red:      float
    sigma_lo_si:   float
    sigma_hi_si:   float
    ratio_cH0:     float
    ratio_cH0_2pi: float
    ratio_a0:      float

def fit_one(sub: pd.DataFrame, h0: float = 70.0) -> GalaxyFit:
    R   = sub['R_kpc' ].to_numpy()
    Vob = sub['Vobs'  ].to_numpy()
    eVo = sub['e_Vobs'].to_numpy()
    Vg  = sub['Vgas'  ].to_numpy()
    Vd  = sub['Vdisk' ].to_numpy()
    Vb  = sub['Vbul'  ].to_numpy()

    ch0_2pi_kpc = cH0_si(h0) / (2*math.pi) / ACC_CONV

    def chi2(params):
        log10g, ups = params
        gN = bary_gN(R, Vg, Vd, Vb, ups_disk=ups)
        Vm = ect_vmod(R, gN, 10**log10g)
        res = (Vob - Vm) / eVo
        return float(np.sum(res**2))

    # Grid search near cH0/(2pi) to find good starting point
    log10_ref = math.log10(ch0_2pi_kpc)
    best_val = np.inf
    best_x   = [log10_ref, 0.5]
    for log10g in np.linspace(log10_ref - 1.5, log10_ref + 1.5, 20):
        for ups in np.linspace(0.2, 1.5, 12):
            c = chi2([log10g, ups])
            if c < best_val:
                best_val = c
                best_x   = [log10g, ups]

    # Local refinement
    res = minimize(chi2, best_x,
                   bounds=[(log10_ref - 2.5, log10_ref + 2.5), (0.1, 2.5)],
                   method='L-BFGS-B',
                   options={'ftol': 1e-14, 'gtol': 1e-10, 'maxiter': 1000})
    g_kpc = 10**res.x[0]
    g_si  = g_kpc * ACC_CONV
    ups   = float(res.x[1])
    dof   = max(len(sub) - 2, 1)
    chi2_min = float(res.fun)

    # 1-sigma on g† (ups fixed)
    grid = np.linspace(res.x[0] - 1.5, res.x[0] + 1.5, 400)
    vals = np.array([chi2([x, ups]) for x in grid])
    mask = vals <= chi2_min + 1.0
    if np.any(mask):
        lo_si = 10**grid[np.where(mask)[0][ 0]] * ACC_CONV
        hi_si = 10**grid[np.where(mask)[0][-1]] * ACC_CONV
    else:
        lo_si = hi_si = g_si

    ch0     = cH0_si(h0)
    ch0_2pi = ch0 / (2*math.pi)
    return GalaxyFit(
        galaxy        = str(sub['Galaxy'].iloc[0]),
        n_points      = len(sub),
        gdagger_si    = g_si,
        ups_disk      = ups,
        chi2          = chi2_min,
        chi2_red      = chi2_min / dof,
        sigma_lo_si   = max(g_si - lo_si, 0),
        sigma_hi_si   = max(hi_si - g_si, 0),
        ratio_cH0     = g_si / ch0,
        ratio_cH0_2pi = g_si / ch0_2pi,
        ratio_a0      = g_si / A0_SI,
    )

def fit_sample(df: pd.DataFrame, h0: float = 70.0,
               min_pts: int = 8) -> List[GalaxyFit]:
    fits = []
    gals = sorted(df['Galaxy'].unique())
    for i, gal in enumerate(gals):
        sub = df[df['Galaxy'] == gal].sort_values('R_kpc').reset_index(drop=True)
        if len(sub) < min_pts:
            continue
        try:
            f = fit_one(sub, h0=h0)
            fits.append(f)
            print(f"  [{i+1:3d}/{len(gals)}] {gal:<14}  "
                  f"g†={f.gdagger_si:.2e}  ups={f.ups_disk:.2f}  "
                  f"chi2_r={f.chi2_red:.2f}  "
                  f"g†/(cH0/2pi)={f.ratio_cH0_2pi:.3f}")
        except Exception as e:
            print(f"  [{i+1:3d}/{len(gals)}] skip {gal}: {e}")
    return sorted(fits, key=lambda f: f.chi2_red)

# ── Visualisation ─────────────────────────────────────────────────────────────
STYLE = {
    'font.family': 'serif', 'font.size': 8,
    'axes.linewidth': 0.7, 'axes.grid': True,
    'grid.alpha': 0.25, 'grid.linewidth': 0.4,
}
C_OBS = '#222222'; C_BAR = '#2166ac'
C_ECT = '#1a9641'; C_2PI = '#d73027'

def plot_galaxy(ax, sub: pd.DataFrame, fit: GalaxyFit, h0: float = 70.0):
    R   = sub['R_kpc' ].to_numpy()
    Vob = sub['Vobs'  ].to_numpy()
    eVo = sub['e_Vobs'].to_numpy()
    Vg  = sub['Vgas'  ].to_numpy()
    Vd  = sub['Vdisk' ].to_numpy()
    Vb  = sub['Vbul'  ].to_numpy()

    gN_data = bary_gN(R, Vg, Vd, Vb, ups_disk=fit.ups_disk)
    Vbar = np.sqrt(np.maximum(gN_data * R, 0.0))

    # Smooth curves over extended radial range
    Rmod    = np.linspace(max(R.min()*0.4, 0.05), R.max()*1.05, 300)
    gN_s    = np.interp(Rmod, R, gN_data)
    g_kpc   = fit.gdagger_si / ACC_CONV
    Vmod    = ect_vmod(Rmod, gN_s, g_kpc)
    g2pi    = cH0_si(h0) / (2*math.pi) / ACC_CONV
    Vmod2pi = ect_vmod(Rmod, gN_s, g2pi)

    ax.errorbar(R, Vob, yerr=eVo, fmt='o', ms=2.8, color=C_OBS,
                elinewidth=0.8, capsize=1.5, label='Observed', zorder=5)
    ax.plot(R,    Vbar,    ':',  color=C_BAR, lw=1.2,
            label=f'Baryons ('+r'$\Upsilon$'+f'={fit.ups_disk:.2f})')
    ax.plot(Rmod, Vmod,    '-',  color=C_ECT, lw=1.8,
            label=f'ECT fit  '+r'$\chi^2_r$'+f'={fit.chi2_red:.1f}')
    ax.plot(Rmod, Vmod2pi, '--', color=C_2PI, lw=1.0, alpha=0.8,
            label=r'ECT $g^\dagger=cH_0/2\pi$')

    ax.set_title(
        f'{fit.galaxy}  '
        f'$g^\\dagger$={fit.gdagger_si:.2e} m/s$^2$\n'
        f'({fit.ratio_cH0_2pi:.2f}'+r'$\times cH_0/2\pi$)',
        fontsize=6.5)
    ax.set_xlabel('R  (kpc)', fontsize=7)
    ax.set_ylabel('V  (km/s)', fontsize=7)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=5.0, loc='lower right', framealpha=0.7)
    ax.set_xlim(left=0); ax.set_ylim(bottom=0)

def make_figure(df: pd.DataFrame, fits: List[GalaxyFit],
                out_pdf: str, h0: float = 70.0, ncols: int = 4):
    plt.rcParams.update(STYLE)
    n     = len(fits)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 3.4, nrows * 3.0))
    axes_flat = np.array(axes).reshape(-1)

    for i, fit in enumerate(fits):
        sub = df[df['Galaxy'] == fit.galaxy].sort_values('R_kpc').reset_index(drop=True)
        plot_galaxy(axes_flat[i], sub, fit, h0=h0)
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        'ECT phi-branch rotation curves  '
        '(g_obs = 0.5[g_N + sqrt(g_N^2 + 4 g_N g†)])',
        fontsize=9, y=1.002)
    fig.tight_layout()
    fig.savefig(out_pdf, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_pdf}")
    plt.close(fig)

def plot_summary(fits: List[GalaxyFit], out_pdf: str, h0: float = 70.0):
    plt.rcParams.update(STYLE)
    ratios  = np.array([f.ratio_cH0_2pi for f in fits])
    chi2s   = np.array([f.chi2_red      for f in fits])
    ups_arr = np.array([f.ups_disk       for f in fits])

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))

    ax = axes[0]
    ax.hist(ratios, bins=25, color=C_ECT, alpha=0.75, edgecolor='white', lw=0.4)
    ax.axvline(1.0, color=C_2PI, lw=1.5, ls='--', label='cH0/(2pi)')
    ax.axvline(np.median(ratios), color='k', lw=1.2,
               label=f'Median = {np.median(ratios):.2f}')
    ax.set_xlabel('g† / (cH0/2pi)')
    ax.set_ylabel('N galaxies')
    ax.set_title('ECT scale distribution')
    ax.legend(fontsize=7)

    ax = axes[1]
    good = chi2s < 20
    ax.hist(chi2s[good], bins=25, color=C_OBS, alpha=0.6, edgecolor='white', lw=0.4,
            label=f'chi2_r<20  ({good.sum()}/{len(fits)} gal)')
    ax.axvline(1.0, color='gray', lw=1.2, ls='--', label='chi2_r=1')
    ax.axvline(np.median(chi2s[good]), color='k', lw=1.2,
               label=f'Median = {np.median(chi2s[good]):.1f}')
    ax.set_xlabel('chi2_red')
    ax.set_ylabel('N galaxies')
    ax.set_title('Fit quality')
    ax.legend(fontsize=7)

    ax = axes[2]
    ax.hist(ups_arr, bins=20, color='#7570b3', alpha=0.75, edgecolor='white', lw=0.4)
    ax.axvline(0.5, color='gray', lw=1.2, ls='--', label='ups=0.5 (photometric)')
    ax.axvline(np.median(ups_arr), color='k', lw=1.2,
               label=f'Median = {np.median(ups_arr):.2f}')
    ax.set_xlabel('Fitted ups_disk (M/L)')
    ax.set_ylabel('N galaxies')
    ax.set_title('Stellar mass-to-light ratios')
    ax.legend(fontsize=7)

    fig.suptitle(
        f'ECT phi-branch: {len(fits)} SPARC galaxies  |  '
        f'Median chi2_r = {np.median(chi2s):.1f}  |  '
        f'Median g†/(cH0/2pi) = {np.median(ratios):.2f}',
        fontsize=9)
    fig.tight_layout()
    fig.savefig(out_pdf, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_pdf}")
    plt.close(fig)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--h0',       type=float, default=70.0)
    ap.add_argument('--min-pts',  type=int,   default=8)
    ap.add_argument('--galaxies', nargs='+',  default=None)
    ap.add_argument('--n-best',   type=int,   default=None,
                    help='Plot only N best-fit galaxies (sorted by chi2_red)')
    ap.add_argument('--ncols',    type=int,   default=4)
    ap.add_argument('--out-csv',  default='ect_sparc_phi_results.csv')
    ap.add_argument('--out-pdf',  default='ect_sparc_phi_curves.pdf')
    ap.add_argument('--out-hist', default='ect_sparc_phi_histogram.pdf')
    args = ap.parse_args()

    df = load_sparc(args.input)
    if args.galaxies:
        df = df[df['Galaxy'].isin(args.galaxies)]
        print(f"Filtered to {df['Galaxy'].nunique()} galaxies.")

    print("\nFitting (2 params: g†, ups_disk; grid-initialized near cH0/2pi)...")
    fits = fit_sample(df, h0=args.h0, min_pts=args.min_pts)
    print(f"\nFitted: {len(fits)} galaxies")

    pd.DataFrame([f.__dict__ for f in fits]).to_csv(args.out_csv, index=False)
    print(f"Saved: {args.out_csv}")

    ch0     = cH0_si(args.h0)
    ch0_2pi = ch0 / (2*math.pi)
    print(f"\ncH0       = {ch0:.3e} m/s^2")
    print(f"cH0/(2pi) = {ch0_2pi:.3e} m/s^2")
    print(f"a0 (MOND) = {A0_SI:.3e} m/s^2\n")

    print(f"{'Galaxy':<14} {'N':>4}  {'g†(m/s²)':>12}  {'ups':>5}  "
          f"{'chi2_r':>6}  {'g†/(cH0/2pi)':>12}  {'g†/a0':>7}")
    print('-' * 72)
    for f in fits[:30]:
        print(f"{f.galaxy:<14} {f.n_points:>4}  {f.gdagger_si:>12.3e}  "
              f"{f.ups_disk:>5.2f}  {f.chi2_red:>6.2f}  "
              f"{f.ratio_cH0_2pi:>12.3f}  {f.ratio_a0:>7.3f}")
    if len(fits) > 30:
        print(f"  ... {len(fits)-30} more in {args.out_csv}")

    ratios = [f.ratio_cH0_2pi for f in fits]
    chi2s  = [f.chi2_red      for f in fits]
    print(f"\nMedian  g†/(cH0/2pi) = {np.median(ratios):.3f}")
    print(f"Mean    g†/(cH0/2pi) = {np.mean(ratios):.3f}")
    print(f"Std     g†/(cH0/2pi) = {np.std(ratios):.3f}")
    print(f"Median  chi2_red     = {np.median(chi2s):.2f}")
    good = sum(1 for c in chi2s if c < 5)
    print(f"Good fits (chi2_r<5) = {good}/{len(fits)}")

    to_plot = fits[:args.n_best] if args.n_best else fits
    if to_plot:
        make_figure(df, to_plot, args.out_pdf, h0=args.h0, ncols=args.ncols)

    if len(fits) > 3:
        plot_summary(fits, args.out_hist, h0=args.h0)

if __name__ == '__main__':
    main()
