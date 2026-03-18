#!/usr/bin/env python3
"""
ECT galactic-sector fitting pipeline — phi-branch closure.

ECT phi-branch closure (derived from critical Y^{3/2} free energy):
    g_obs = 0.5*(g_N + sqrt(g_N^2 + 4*g_N*g†_eff))
    ↔ mu_phi(x) = x/(x+1),  x = g/g†

Variational derivation (GPT, 2025):
    Gamma_gal[Phi] = int d^3x [K(|nabla Phi|/g†, phi_env)/(8pi G_N) - rho_b Phi]
    Critical branch: K → (2/3g†)|nabla Phi|^3  (= Y_phi^{3/2} in phi-logic)
    EL equation: nabla·[mu_phi(g/g†, phi_env) nabla Phi] = 4pi G_N rho_b
    Deep regime (spherical): g = sqrt(g_N * g†) → BTFR v^4 = G_N M_bar g†

Also computes:
  - MOND RAR curve: g = g_N / (1 - exp(-sqrt(g_N/a0)))
  - LambdaCDM NFW: g = g_N + g_NFW(r; r_s, rho_s)  [2-param fit]
  - EFE curves: phi-branch with g†_eff = g†_0 * exp(gamma * phi_env)

Input:  MassModels_Lelli2016c.mrt (whitespace-delimited, 10 cols)
        Galaxy D_Mpc R_kpc Vobs e_Vobs Vgas Vdisk Vbul SBdisk SBbul

Outputs:
  ect_sparc_phi_results.csv       — per-galaxy fit table
  ect_sparc_phi_curves.pdf        — rotation-curve panels (ECT+MOND+LCDM+EFE)
  ect_sparc_phi_histogram.pdf     — g†/(cH0/2pi) distribution

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
from scipy.optimize import minimize, minimize_scalar

warnings.filterwarnings('ignore')

# ── Physical constants ────────────────────────────────────────────────────────
G_KPC    = 4.30091e-6          # (km/s)^2 kpc / M_sun
ACC_CONV = 1e6 / 3.0856775814913673e19   # (km/s)^2/kpc → m/s^2
C_SI     = 299792458.0
MPC_TO_M = 3.0856775814913673e22
A0_SI    = 1.20e-10            # MOND/McGaugh acceleration scale [m/s^2]

def cH0_si(h0: float = 70.0) -> float:
    return C_SI * h0 * 1e3 / MPC_TO_M

# ── Data loading ──────────────────────────────────────────────────────────────
def load_sparc(path: str) -> pd.DataFrame:
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

# ── Baryonic model ────────────────────────────────────────────────────────────
def bary_gN(R, Vg, Vd, Vb, ups_disk=0.5, ups_bul=0.7):
    """Baryonic Newtonian acceleration in (km/s)^2/kpc."""
    Vb2 = ups_bul * np.sign(Vb) * Vb**2
    Vb2 = np.where(Vb2 < 0, 0.0, Vb2)
    return (Vg**2 + ups_disk * Vd**2 + Vb2) / np.maximum(R, 1e-9)

# ── ECT phi-branch model ──────────────────────────────────────────────────────
def ect_vmod(R, gN, gdagger_kpc):
    """ECT rotation curve: g = 0.5*(gN + sqrt(gN^2 + 4 gN g†))."""
    g_obs = 0.5*(gN + np.sqrt(np.maximum(gN**2 + 4.0*gN*gdagger_kpc, 0.0)))
    return np.sqrt(np.maximum(g_obs * R, 0.0))

# ── MOND RAR model ────────────────────────────────────────────────────────────
def mond_vmod(R, gN, a0_kpc):
    """MOND with McGaugh+2016 RAR interpolation: g = gN/(1-exp(-sqrt(gN/a0)))."""
    x = np.sqrt(np.maximum(gN / a0_kpc, 0.0))
    denom = np.where(x < 1e-6, x, 1.0 - np.exp(-x))
    denom = np.maximum(denom, 1e-30)
    g_obs = gN / denom
    return np.sqrt(np.maximum(g_obs * R, 0.0))

# ── ΛCDM NFW model ────────────────────────────────────────────────────────────
def nfw_gN(R_kpc, rho_s_Msun_kpc3, r_s_kpc):
    """NFW halo acceleration in (km/s)^2/kpc."""
    x = R_kpc / r_s_kpc
    M_nfw = 4*np.pi*rho_s_Msun_kpc3 * r_s_kpc**3 * (np.log(1+x) - x/(1+x))
    return G_KPC * np.maximum(M_nfw, 0) / np.maximum(R_kpc**2, 1e-9)

def lcdm_vmod(R, gN, rho_s, r_s):
    """ΛCDM = baryons + NFW halo."""
    g_nfw  = nfw_gN(R, rho_s, r_s)
    g_tot  = gN + g_nfw
    return np.sqrt(np.maximum(g_tot * R, 0.0))

# ── Fitting ───────────────────────────────────────────────────────────────────
@dataclass
class GalaxyFit:
    galaxy:           str
    n_points:         int
    # ECT
    gdagger_si:       float
    ups_disk:         float
    chi2_ect:         float
    chi2_red_ect:     float
    sigma_lo_si:      float
    sigma_hi_si:      float
    ratio_cH0:        float
    ratio_cH0_2pi:    float
    ratio_a0:         float
    # MOND (a0 fixed, ups_disk fit)
    ups_mond:         float
    chi2_red_mond:    float
    # LCDM (ups_disk, rho_s, r_s fit)
    ups_lcdm:         float
    rho_s:            float
    r_s_kpc:          float
    chi2_red_lcdm:    float

def _arrays(sub):
    return (sub['R_kpc'].to_numpy(), sub['Vobs'].to_numpy(),
            sub['e_Vobs'].to_numpy(), sub['Vgas'].to_numpy(),
            sub['Vdisk'].to_numpy(), sub['Vbul'].to_numpy())

def fit_ect(sub, h0=70.0):
    R, Vob, eVo, Vg, Vd, Vb = _arrays(sub)
    ch0_2pi_kpc = cH0_si(h0)/(2*math.pi)/ACC_CONV

    def chi2(params):
        log10g, ups = params
        gN = bary_gN(R, Vg, Vd, Vb, ups_disk=ups)
        Vm = ect_vmod(R, gN, 10**log10g)
        return float(np.sum(((Vob-Vm)/eVo)**2))

    log10_ref = math.log10(ch0_2pi_kpc)
    best_val, best_x = np.inf, [log10_ref, 0.5]
    for lg in np.linspace(log10_ref-1.5, log10_ref+1.5, 15):
        for ups in [0.2, 0.5, 0.8, 1.2]:
            c = chi2([lg, ups])
            if c < best_val:
                best_val, best_x = c, [lg, ups]
    res = minimize(chi2, best_x,
                   bounds=[(log10_ref-2.5, log10_ref+2.5), (0.1, 2.5)],
                   method='L-BFGS-B',
                   options={'ftol':1e-14,'gtol':1e-10,'maxiter':1000})
    g_kpc = 10**res.x[0];  g_si = g_kpc*ACC_CONV;  ups = float(res.x[1])
    chi2_min = float(res.fun);  dof = max(len(sub)-2, 1)
    # 1-sigma scan
    grid = np.linspace(res.x[0]-1.5, res.x[0]+1.5, 400)
    vals = np.array([chi2([x, ups]) for x in grid])
    mask = vals <= chi2_min + 1.0
    lo_si = (10**grid[np.where(mask)[0][0]]  if np.any(mask) else g_kpc)*ACC_CONV
    hi_si = (10**grid[np.where(mask)[0][-1]] if np.any(mask) else g_kpc)*ACC_CONV
    ch0     = cH0_si(h0);  ch0_2pi = ch0/(2*math.pi)
    return dict(gdagger_si=g_si, ups_disk=ups,
                chi2_ect=chi2_min, chi2_red_ect=chi2_min/dof,
                sigma_lo_si=max(g_si-lo_si,0), sigma_hi_si=max(hi_si-g_si,0),
                ratio_cH0=g_si/ch0, ratio_cH0_2pi=g_si/ch0_2pi, ratio_a0=g_si/A0_SI)

def fit_mond(sub):
    R, Vob, eVo, Vg, Vd, Vb = _arrays(sub)
    a0_kpc = A0_SI/ACC_CONV
    def chi2(ups):
        gN = bary_gN(R, Vg, Vd, Vb, ups_disk=ups)
        Vm = mond_vmod(R, gN, a0_kpc)
        return float(np.sum(((Vob-Vm)/eVo)**2))
    res = minimize_scalar(chi2, bounds=(0.1, 2.5), method='bounded')
    dof = max(len(sub)-1, 1)
    return dict(ups_mond=float(res.x), chi2_red_mond=float(res.fun)/dof)

def fit_lcdm(sub):
    R, Vob, eVo, Vg, Vd, Vb = _arrays(sub)
    def chi2(params):
        ups, log_rho, log_rs = params
        gN  = bary_gN(R, Vg, Vd, Vb, ups_disk=ups)
        Vm  = lcdm_vmod(R, gN, 10**log_rho, 10**log_rs)
        return float(np.sum(((Vob-Vm)/eVo)**2))
    best_val, best_x = np.inf, [0.5, 7.0, 0.5]
    for ups in [0.3, 0.5, 0.8]:
        for lr in [6, 7, 8]:
            for lrs in [0.0, 0.5, 1.0]:
                c = chi2([ups, lr, lrs])
                if c < best_val:
                    best_val, best_x = c, [ups, lr, lrs]
    res = minimize(chi2, best_x,
                   bounds=[(0.1,2.5),(4,10),(-1,2)],
                   method='L-BFGS-B')
    dof = max(len(sub)-3, 1)
    return dict(ups_lcdm=float(res.x[0]),
                rho_s=10**float(res.x[1]), r_s_kpc=10**float(res.x[2]),
                chi2_red_lcdm=float(res.fun)/dof)

def fit_one(sub, h0=70.0):
    e  = fit_ect(sub, h0)
    m  = fit_mond(sub)
    l  = fit_lcdm(sub)
    return GalaxyFit(galaxy=str(sub['Galaxy'].iloc[0]), n_points=len(sub),
                     **e, **m, **l)

def fit_sample(df, h0=70.0, min_pts=8):
    fits = []
    gals = sorted(df['Galaxy'].unique())
    for i, gal in enumerate(gals):
        sub = df[df['Galaxy']==gal].sort_values('R_kpc').reset_index(drop=True)
        if len(sub) < min_pts:
            continue
        try:
            f = fit_one(sub, h0)
            fits.append(f)
            print(f"  [{i+1:3d}/{len(gals)}] {gal:<14}  "
                  f"ECT χ²_r={f.chi2_red_ect:.2f}  "
                  f"MOND χ²_r={f.chi2_red_mond:.2f}  "
                  f"ΛCDM χ²_r={f.chi2_red_lcdm:.2f}  "
                  f"g†/(cH₀/2π)={f.ratio_cH0_2pi:.3f}")
        except Exception as ex:
            print(f"  [{i+1:3d}] skip {gal}: {ex}")
    return sorted(fits, key=lambda f: f.chi2_red_ect)

# ── Visualisation: rotation curves ───────────────────────────────────────────
STYLE = {'font.family':'serif','font.size':8,'axes.linewidth':0.7,
         'axes.grid':True,'grid.alpha':0.25,'grid.linewidth':0.4}
C_OBS='#222222'; C_BAR='#2166ac'; C_ECT='#1a9641'
C_MOND='#d73027'; C_LCDM='#7570b3'; C_2PI='#f4a582'; C_EFE='#984ea3'

def plot_galaxy(ax, sub, fit: GalaxyFit, h0=70.0):
    R   = sub['R_kpc' ].to_numpy();  Vob = sub['Vobs'  ].to_numpy()
    eVo = sub['e_Vobs'].to_numpy();  Vg  = sub['Vgas'  ].to_numpy()
    Vd  = sub['Vdisk' ].to_numpy();  Vb  = sub['Vbul'  ].to_numpy()
    Rmod = np.linspace(max(R.min()*0.4, 0.05), R.max()*1.05, 300)

    # ECT best fit
    gN_data  = bary_gN(R,  Vg, Vd, Vb, ups_disk=fit.ups_disk)
    gN_mod   = bary_gN(Rmod, np.interp(Rmod,R,Vg),
                            np.interp(Rmod,R,Vd), np.interp(Rmod,R,Vb),
                            ups_disk=fit.ups_disk)
    Vbar     = np.sqrt(np.maximum(gN_data * R, 0))
    g_kpc    = fit.gdagger_si / ACC_CONV
    V_ect    = ect_vmod(Rmod, gN_mod, g_kpc)

    # ECT reference: g† = cH0/(2pi)
    g2pi_kpc = cH0_si(h0)/(2*math.pi)/ACC_CONV
    V_2pi    = ect_vmod(Rmod, gN_mod, g2pi_kpc)

    # MOND
    gN_mond  = bary_gN(Rmod, np.interp(Rmod,R,Vg),
                             np.interp(Rmod,R,Vd), np.interp(Rmod,R,Vb),
                             ups_disk=fit.ups_mond)
    V_mond   = mond_vmod(Rmod, gN_mond, A0_SI/ACC_CONV)

    # ΛCDM
    gN_lcdm  = bary_gN(Rmod, np.interp(Rmod,R,Vg),
                             np.interp(Rmod,R,Vd), np.interp(Rmod,R,Vb),
                             ups_disk=fit.ups_lcdm)
    V_lcdm   = lcdm_vmod(Rmod, gN_lcdm, fit.rho_s, fit.r_s_kpc)

    # EFE curves: g†_eff = g† * {0.5, 2.0}  (low/high environment)
    V_efe_lo = ect_vmod(Rmod, gN_mod, g_kpc * 0.5)  # void (low phi_env)
    V_efe_hi = ect_vmod(Rmod, gN_mod, g_kpc * 2.0)  # group (high phi_env)

    ax.errorbar(R, Vob, yerr=eVo, fmt='o', ms=2.5, color=C_OBS,
                elinewidth=0.7, capsize=1.2, label='Obs', zorder=5)
    ax.plot(R,    Vbar,    ':',  color=C_BAR,  lw=1.0, label=f'Baryons (Υ={fit.ups_disk:.2f})')
    ax.plot(Rmod, V_ect,   '-',  color=C_ECT,  lw=1.8,
            label=f'ECT  χ²={fit.chi2_red_ect:.1f}')
    ax.plot(Rmod, V_2pi,   '-',  color=C_2PI,  lw=1.0, alpha=0.8,
            label=r'ECT $g^\dagger_0=cH_0/2\pi$')
    ax.fill_between(Rmod, V_efe_lo, V_efe_hi, color=C_EFE, alpha=0.15,
                    label='ECT EFE band (×0.5 – ×2)')
    ax.plot(Rmod, V_mond,  '--', color=C_MOND, lw=1.2,
            label=f'MOND  χ²={fit.chi2_red_mond:.1f}')
    ax.plot(Rmod, V_lcdm,  '-.', color=C_LCDM, lw=1.2,
            label=f'ΛCDM  χ²={fit.chi2_red_lcdm:.1f}')

    ax.set_title(
        f'{fit.galaxy}\n'
        f'ECT g†={fit.gdagger_si:.1e}  ({fit.ratio_cH0_2pi:.2f}·cH₀/2π)',
        fontsize=6.5)
    ax.set_xlabel('R (kpc)', fontsize=7); ax.set_ylabel('V (km/s)', fontsize=7)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=4.5, loc='lower right', framealpha=0.7, ncol=1)
    ax.set_xlim(left=0); ax.set_ylim(bottom=0)

def make_figure(df, fits, out_pdf, h0=70.0, ncols=4):
    plt.rcParams.update(STYLE)
    n = len(fits);  nrows = math.ceil(n/ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*3.5, nrows*3.1))
    axes_flat = np.array(axes).reshape(-1)
    for i, fit in enumerate(fits):
        sub = df[df['Galaxy']==fit.galaxy].sort_values('R_kpc').reset_index(drop=True)
        plot_galaxy(axes_flat[i], sub, fit, h0)
    for j in range(i+1, len(axes_flat)):
        axes_flat[j].set_visible(False)
    fig.suptitle('ECT φ-branch vs MOND vs ΛCDM  |  EFE band = ×0.5–×2 g†',
                 fontsize=9, y=1.002)
    fig.tight_layout()
    fig.savefig(out_pdf, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_pdf}"); plt.close(fig)

# ── EFE summary plot ──────────────────────────────────────────────────────────
def plot_efe_summary(fits, out_pdf, h0=70.0):
    """Show per-galaxy g†_eff vs environment proxy (ratio_cH0_2pi order)."""
    plt.rcParams.update(STYLE)
    ratios   = np.array([f.ratio_cH0_2pi for f in fits])
    chi2_ect = np.array([f.chi2_red_ect   for f in fits])
    chi2_mond= np.array([f.chi2_red_mond  for f in fits])
    chi2_lcdm= np.array([f.chi2_red_lcdm  for f in fits])
    galaxies = [f.galaxy for f in fits]
    idx      = np.argsort(ratios)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Panel 1: g†/(cH0/2pi) sorted by value
    ax = axes[0,0]
    ax.scatter(range(len(fits)), ratios[idx], c=C_ECT, s=12, alpha=0.7)
    ax.axhline(1.0,  color=C_2PI,  lw=1.5, ls='--', label='cH₀/2π')
    ax.axhline(0.5,  color=C_EFE,  lw=0.8, ls=':',  label='void lower bound')
    ax.axhline(2.0,  color=C_EFE,  lw=0.8, ls=':',  label='group upper bound')
    ax.set_xlabel('Galaxy rank (sorted by g†)'); ax.set_ylabel('g† / (cH₀/2π)')
    ax.set_title('ECT per-galaxy acceleration scale\n(EFE scatter expected)')
    ax.legend(fontsize=7); ax.set_ylim(0, min(12, ratios.max()*1.1))

    # Panel 2: chi2 comparison ECT vs MOND vs LCDM
    ax = axes[0,1]
    x = np.arange(3)
    for i_gal, ratio in enumerate(ratios):
        c_ect  = chi2_ect[i_gal];  c_mond = chi2_mond[i_gal]; c_lcdm = chi2_lcdm[i_gal]
        col = C_ECT if c_ect < c_mond else C_MOND
        ax.scatter([0,1,2], [c_ect, c_mond, c_lcdm],
                   c=col, s=4, alpha=0.3)
    ax.set_xticks([0,1,2]); ax.set_xticklabels(['ECT','MOND','ΛCDM'], fontsize=8)
    ax.set_ylabel('χ²_red'); ax.set_ylim(0, 20)
    ax.axhline(1.0, color='gray', lw=1, ls='--')
    ax.set_title('χ²_red comparison\n(green=ECT wins, red=MOND wins)')

    # Panel 3: g†/(cH0/2pi) histogram
    ax = axes[1,0]
    ax.hist(ratios, bins=30, color=C_ECT, alpha=0.75, edgecolor='white', lw=0.4)
    ax.axvline(1.0,             color=C_2PI,  lw=1.5, ls='--', label=f'cH₀/2π (median={np.median(ratios):.2f})')
    ax.axvline(np.median(ratios),color='k',   lw=1.2,          label=f'Median={np.median(ratios):.2f}')
    ax.axvspan(0.5, 2.0, color=C_EFE, alpha=0.15, label='EFE band [0.5–2.0]')
    ax.set_xlabel('g†_eff / (cH₀/2π)'); ax.set_ylabel('N galaxies')
    ax.set_title(f'ECT scale distribution\n({np.mean((ratios>=0.5)&(ratios<=2.0))*100:.0f}% in EFE band)')
    ax.legend(fontsize=7)

    # Panel 4: chi2_red distributions
    ax = axes[1,1]
    bins = np.linspace(0, 15, 31)
    ax.hist(np.clip(chi2_ect,  0,15), bins=bins, color=C_ECT,  alpha=0.6,
            label=f'ECT  med={np.median(chi2_ect):.1f}',  histtype='stepfilled')
    ax.hist(np.clip(chi2_mond, 0,15), bins=bins, color=C_MOND, alpha=0.6,
            label=f'MOND med={np.median(chi2_mond):.1f}', histtype='step', lw=1.5)
    ax.hist(np.clip(chi2_lcdm, 0,15), bins=bins, color=C_LCDM, alpha=0.6,
            label=f'ΛCDM med={np.median(chi2_lcdm):.1f}', histtype='step', lw=1.5, ls='--')
    ax.axvline(1.0, color='gray', lw=1, ls='--', label='χ²=1')
    ax.set_xlabel('χ²_red (clipped at 15)'); ax.set_ylabel('N galaxies')
    ax.set_title('Fit quality comparison\nECT 2-param vs MOND 1-param vs ΛCDM 3-param')
    ax.legend(fontsize=7)

    fig.suptitle(f'ECT EFE analysis: {len(fits)} SPARC galaxies  '
                 f'|  ECT median χ²={np.median(chi2_ect):.1f}  '
                 f'MOND median χ²={np.median(chi2_mond):.1f}  '
                 f'ΛCDM median χ²={np.median(chi2_lcdm):.1f}',
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(out_pdf, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_pdf}"); plt.close(fig)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--h0',       type=float, default=70.0)
    ap.add_argument('--min-pts',  type=int,   default=8)
    ap.add_argument('--galaxies', nargs='+',  default=None)
    ap.add_argument('--n-best',   type=int,   default=None)
    ap.add_argument('--ncols',    type=int,   default=4)
    ap.add_argument('--out-csv',  default='ect_sparc_phi_results.csv')
    ap.add_argument('--out-pdf',  default='ect_sparc_phi_curves.pdf')
    ap.add_argument('--out-efe',  default='ect_sparc_efe_analysis.pdf')
    args = ap.parse_args()

    df = load_sparc(args.input)
    if args.galaxies:
        df = df[df['Galaxy'].isin(args.galaxies)]
        print(f"Filtered to {df['Galaxy'].nunique()} galaxies.")

    print("\nFitting ECT + MOND + ΛCDM...")
    fits = fit_sample(df, h0=args.h0, min_pts=args.min_pts)
    print(f"\nFitted: {len(fits)} galaxies")

    pd.DataFrame([f.__dict__ for f in fits]).to_csv(args.out_csv, index=False)
    print(f"Saved: {args.out_csv}")

    ch0     = cH0_si(args.h0);  ch0_2pi = ch0/(2*math.pi)
    print(f"\ncH₀       = {ch0:.3e} m/s²")
    print(f"cH₀/(2π)  = {ch0_2pi:.3e} m/s²")
    print(f"a₀ (MOND) = {A0_SI:.3e} m/s²\n")

    print(f"{'Galaxy':<14}{'N':>4}  {'g†(m/s²)':>12}  {'Υ':>5}  "
          f"{'ECT χ²':>7}  {'MOND χ²':>8}  {'ΛCDM χ²':>8}  {'g†/(cH₀/2π)':>12}")
    print('-'*80)
    for f in fits[:25]:
        print(f"{f.galaxy:<14}{f.n_points:>4}  {f.gdagger_si:>12.3e}  "
              f"{f.ups_disk:>5.2f}  {f.chi2_red_ect:>7.2f}  "
              f"{f.chi2_red_mond:>8.2f}  {f.chi2_red_lcdm:>8.2f}  "
              f"{f.ratio_cH0_2pi:>12.3f}")

    ratios    = [f.ratio_cH0_2pi  for f in fits]
    chi2_ect  = [f.chi2_red_ect   for f in fits]
    chi2_mond = [f.chi2_red_mond  for f in fits]
    chi2_lcdm = [f.chi2_red_lcdm  for f in fits]
    ect_wins  = sum(1 for e,m in zip(chi2_ect, chi2_mond) if e < m)

    print(f"\n{'─'*50}")
    print(f"Median  g†/(cH₀/2π) = {np.median(ratios):.3f}")
    print(f"Fraction in [0.5,2.0] = {np.mean([(0.5<=r<=2) for r in ratios])*100:.0f}%  ← EFE scatter band")
    print(f"Median  ECT  χ²_red  = {np.median(chi2_ect):.2f}")
    print(f"Median  MOND χ²_red  = {np.median(chi2_mond):.2f}")
    print(f"Median  ΛCDM χ²_red  = {np.median(chi2_lcdm):.2f}")
    print(f"ECT better than MOND = {ect_wins}/{len(fits)} galaxies")

    to_plot = fits[:args.n_best] if args.n_best else fits
    if to_plot:
        make_figure(df, to_plot, args.out_pdf, h0=args.h0, ncols=args.ncols)

    if len(fits) > 3:
        plot_efe_summary(fits, args.out_efe, h0=args.h0)

if __name__ == '__main__':
    main()
