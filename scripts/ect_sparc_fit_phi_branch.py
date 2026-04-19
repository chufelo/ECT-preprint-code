#!/usr/bin/env python3
"""
ECT galactic-sector fitting pipeline v3d — phi-branch closure.

Variational basis (GPT 2025):
    Gamma_gal[Phi] = int d^3x [ K(|grad Phi|/g†, phi_env)/(8pi G_N) - rho_b Phi ]
    Critical branch: K -> (2/3g†)|grad Phi|^3  (= Y_phi^{3/2})
    EL equation: div[mu_phi(g/g†) grad Phi] = 4pi G_N rho_b
    mu_phi(x) = x/(x+1)  <->  g = 0.5*(gN + sqrt(gN^2 + 4*gN*g†))
    Deep regime: g = sqrt(gN * g†)  ->  BTFR v^4 = G_N M_bar g†

WHAT'S NEW IN v3d (per GPT review):
  1. UGC02885 restored in five_galaxies_comparison.csv (name normalization added)
  2. AIC and BIC added to all model comparisons (ECT/MOND/ΛCDM)
  3. --error-floor parameter (default 2.0 km/s) — sensitivity analysis
  4. "EFE band" renamed to "g† sensitivity band" — reflects true meaning
  5. --efe-mode proxy mode with g†_eff = g†_0/(1+α·gext/g†_0)
  6. Clean-sample CSV export (ect_sparc_results_clean.csv)
  7. New diagnostic plots: fixed-vs-free g† scatter, fixed-vs-free chi2, R_last
  8. Summary report: AIC/BIC stats, clean-sample stats, honest interpretation

DESIGN RULES:
  - fit_sample() is called EXACTLY ONCE on the full dataset.
  - CSV + diagnostics are written BEFORE any rotation-curve plots.
  - --selected only controls which galaxies appear in SET 2 and SET 3.
  - Physical formula NOT changed:
      g = 0.5*(gN + sqrt(gN^2 + 4*gN*g†))

OUTPUTS (all in --output-dir, default=figures/sparc_v3/):
  ect_sparc_results.csv           — full results table with AIC/BIC
  ect_sparc_results_clean.csv     — clean-sample only (no quality flags)
  five_galaxies_comparison.csv    — DDO154 NGC2403 NGC3198 NGC6503 UGC02885
  summary_report.txt              — honest text summary with AIC/BIC
  set1_milky_way.pdf
  set2_sparc_sample.pdf
  set3_gdag_sensitivity.pdf       — ECT best-fit + MOND + ΛCDM + EFE proxy
  diag_gdag_scatter4.pdf          — 2x2 scatter (165 galaxies)
  diag_gdag_vs_mbar.pdf
  diag_gdag_vs_sigma.pdf
  diag_gdag_vs_mldisk.pdf
  diag_gdag_vs_chi2.pdf
  diag_gdag_vs_rlast.pdf          — NEW: g† vs R_last
  diag_fixed_vs_free_gdag.pdf     — NEW: fixed-ML vs free-ML g†
  diag_fixed_vs_free_chi2.pdf     — NEW: fixed-ML vs free-ML chi2
  diag_chi2_comparison.pdf        — 4-panel chi2 histograms
  diag_aic_comparison.pdf         — NEW: AIC comparison
  diag_gdag_histogram.pdf

All figures in GRAYSCALE (publication-ready).

Usage:
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt --error-floor 0
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt \\
           --selected NGC3198 NGC2403 DDO154 NGC6503 UGC02885
    python ect_sparc_fit_phi_branch.py MassModels_Lelli2016c.mrt \\
           --efe-mode proxy --gext-file gext_table.csv --alpha-ext 1.0
"""
from __future__ import annotations
import argparse, math, os, warnings
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
ACC_CONV = 1e6 / 3.0856775814913673e19   # (km/s)^2/kpc -> m/s^2
C_SI     = 299792458.0
MPC_TO_M = 3.0856775814913673e22
A0_SI    = 1.20e-10            # MOND/McGaugh+2016 [m/s^2]
UPS_DISK_FIXED = 0.5           # Schombert+2019 photometric default
UPS_BUL_FIXED  = 0.7

# Number of free parameters per model (for AIC/BIC)
K_ECT_FIXED = 1   # only g†
K_ECT_FREE  = 2   # g† + Υ_disk
K_MOND      = 1   # only Υ_disk (a0 fixed)
K_LCDM      = 3   # Υ_disk, ρ_s, r_s

def cH0_si(h0: float = 70.0) -> float:
    return C_SI * h0 * 1e3 / MPC_TO_M

def gdag_baseline(h0: float = 70.0):
    ch0 = cH0_si(h0)
    return {'cH0': ch0, 'cH0_2pi': ch0 / (2 * math.pi)}

# ── Galaxy name normalisation (prevents UGC02885 vs UGC2885 mismatch) ────────
def normalize_name(name: str) -> str:
    """Strip spaces and upper-case for robust name matching."""
    return str(name).replace(' ', '').upper()

# ── Grayscale style ───────────────────────────────────────────────────────────
GS = {
    'font.family': 'serif', 'font.size': 8,
    'axes.linewidth': 0.7, 'axes.grid': True,
    'grid.alpha': 0.25, 'grid.linewidth': 0.4,
    'text.color': 'black', 'axes.labelcolor': 'black',
    'xtick.color': 'black', 'ytick.color': 'black',
}
BK  = '#000000'   # observations / ECT field best-fit / MOND
DG  = '#333333'   # ECT variants / LCDM
MG  = '#666666'   # ECT baseline cH0/2pi
LG  = '#999999'   # lighter reference lines
VLG = '#bbbbbb'   # very light reference
SBD = '#cccccc'   # sensitivity band fill (was EFE)
BAR = '#555555'   # baryons (dashed)

LS_MOND = '--'   # thick black dashed — maximally visible
LS_LCDM = ':'    # dotted dark gray

# ── Data loading ──────────────────────────────────────────────────────────────
def load_sparc(path: str, error_floor: float = 2.0) -> pd.DataFrame:
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
                    'e_Vobs': float(parts[4]),
                    'Vgas':   float(parts[5]),
                    'Vdisk':  float(parts[6]),
                    'Vbul':   float(parts[7]),
                })
            except (ValueError, IndexError):
                continue
    df = pd.DataFrame(rows)
    df['e_Vobs_raw'] = df['e_Vobs'].copy()
    if error_floor > 0:
        df['e_Vobs'] = df['e_Vobs'].clip(lower=error_floor)
    n_floored = (df['e_Vobs_raw'] < error_floor).sum() if error_floor > 0 else 0
    print(f"Loaded {len(df)} data points, {df['Galaxy'].nunique()} galaxies.")
    print(f"  Error floor: {error_floor:.1f} km/s  ({n_floored} values raised)")
    return df

# ── Optional: load external-field proxy table ─────────────────────────────────
# Physical constants for EFE computation
G_SI   = 6.67430e-11     # m^3 kg^-1 s^-2
MSUN   = 1.98847e30      # kg
KPC_M  = 3.085677581491367e19   # m per kpc

def gext_from_neighbour(M_neigh_Msun: float, d_neigh_kpc: float) -> float:
    """Level-1 EFE proxy: g_ext = G * M_neigh / d_neigh^2  [m/s^2]."""
    M = M_neigh_Msun * MSUN
    d = d_neigh_kpc * KPC_M
    return G_SI * M / d**2

def load_gext(path: Optional[str]) -> Optional[dict]:
    """Load external-field proxy CSV.

    Supported formats:
      Format A: columns galaxy, gext_m_s2            — direct value
      Format B: columns galaxy, M_neigh_Msun, d_neigh_kpc — computed Level-1

    Returns dict {normalized_name: gext_si} or None.
    Lines starting with '#' are ignored.
    """
    if path is None:
        return None
    df = pd.read_csv(path, comment='#')
    if 'galaxy' not in df.columns:
        raise ValueError("gext_file must have column: galaxy")
    result = {}
    if 'gext_m_s2' in df.columns:
        # Format A: use pre-computed value
        for _, row in df.iterrows():
            result[normalize_name(row['galaxy'])] = float(row['gext_m_s2'])
        print(f"  Loaded g_ext (Format A: direct values): {len(result)} galaxies")
    elif 'M_neigh_Msun' in df.columns and 'd_neigh_kpc' in df.columns:
        # Format B: compute from nearest-neighbour
        for _, row in df.iterrows():
            gex = gext_from_neighbour(float(row['M_neigh_Msun']),
                                      float(row['d_neigh_kpc']))
            result[normalize_name(row['galaxy'])] = gex
        print(f"  Loaded g_ext (Format B: computed from M_neigh, d_neigh): {len(result)} galaxies")
    else:
        raise ValueError(
            "gext_file must have columns: (galaxy, gext_m_s2) OR "
            "(galaxy, M_neigh_Msun, d_neigh_kpc)")
    return result

# ── Physics functions ──────────────────────────────────────────────────────────
def baryonic_velocity_squared(vgas, vdisk, vbul,
                               ml_disk=UPS_DISK_FIXED, ml_bul=UPS_BUL_FIXED):
    vbul2 = ml_bul * np.sign(vbul) * vbul**2
    vbul2 = np.where(vbul2 < 0, 0.0, vbul2)
    return vgas**2 + ml_disk * vdisk**2 + vbul2

def g_newton_from_vbar2(vbar2_kms2, R_kpc):
    return vbar2_kms2 / np.maximum(R_kpc, 1e-9)

def ect_g_obs(gN_kpc, gdagger_kpc):
    """ECT phi-branch: g = 0.5*(gN + sqrt(gN^2 + 4*gN*g†)). (km/s)^2/kpc
    IMPORTANT: This formula must not be changed."""
    return 0.5 * (gN_kpc +
                  np.sqrt(np.maximum(gN_kpc**2 + 4.0*gN_kpc*gdagger_kpc, 0.0)))

def ect_vmod(R_kpc, gN_kpc, gdagger_kpc):
    return np.sqrt(np.maximum(ect_g_obs(gN_kpc, gdagger_kpc) * R_kpc, 0.0))

def ect_gdag_eff_proxy(gdag0_si: float, gext_si: float, alpha_ext: float) -> float:
    """EFE proxy: g†_eff = g†_0 / (1 + α·g_ext/g†_0).
    Physical motivation: external condensate field suppresses internal g†.
    NOTE: This is a phenomenological ansatz, not a derived ECT result."""
    if gdag0_si <= 0 or gext_si <= 0:
        return gdag0_si
    return gdag0_si / (1.0 + alpha_ext * gext_si / gdag0_si)

def mond_g_obs(gN_kpc, a0_kpc):
    """MOND RAR: g = gN / (1 - exp(-sqrt(gN/a0))). McGaugh+2016."""
    x = np.sqrt(np.maximum(gN_kpc / a0_kpc, 0.0))
    denom = np.where(x < 1e-7, x + x**3/24.0, 1.0 - np.exp(-x))
    denom = np.maximum(denom, 1e-30)
    return gN_kpc / denom

def mond_vmod(R_kpc, gN_kpc, a0_kpc):
    return np.sqrt(np.maximum(mond_g_obs(gN_kpc, a0_kpc) * R_kpc, 0.0))

def nfw_g(R_kpc, rho_s_Msun_kpc3, r_s_kpc):
    x = np.maximum(R_kpc / r_s_kpc, 1e-9)
    M = 4*np.pi * rho_s_Msun_kpc3 * r_s_kpc**3 * (np.log(1+x) - x/(1+x))
    return G_KPC * np.maximum(M, 0) / np.maximum(R_kpc**2, 1e-9)

def lcdm_vmod(R_kpc, gN_kpc, rho_s, r_s_kpc):
    return np.sqrt(np.maximum((gN_kpc + nfw_g(R_kpc, rho_s, r_s_kpc)) * R_kpc, 0.0))

def compute_aic_bic(chi2_raw: float, k: int, N: int):
    """AIC = χ² + 2k,  BIC = χ² + k·ln(N)."""
    aic = chi2_raw + 2 * k
    bic = chi2_raw + k * math.log(max(N, 1))
    return aic, bic

# ── Baryonic mass proxy ───────────────────────────────────────────────────────
def baryonic_mass_proxy(sub, ml_disk=UPS_DISK_FIXED, ml_bul=UPS_BUL_FIXED):
    last = sub.iloc[-1]
    R    = last['R_kpc']
    vb2  = baryonic_velocity_squared(
        np.array([last['Vgas']]), np.array([last['Vdisk']]),
        np.array([last['Vbul']]), ml_disk, ml_bul)[0]
    return vb2 * R / G_KPC

# ── Data structure ────────────────────────────────────────────────────────────
@dataclass
class GalaxyFit:
    galaxy:              str
    n_points:            int
    D_Mpc:               float
    R_last:              float
    Mbar_proxy:          float
    Sigma_bar_proxy:     float
    # FIXED M/L
    gdag_fixed_si:       float
    gdag_fixed_kpc:      float
    chi2_fixed:          float      # raw chi2
    chi2_red_fixed:      float
    aic_fixed:           float
    bic_fixed:           float
    sigma_lo_fixed_si:   float
    sigma_hi_fixed_si:   float
    # FREE M/L
    gdag_free_si:        float
    gdag_free_kpc:       float
    ml_disk_best:        float
    chi2_free:           float      # raw chi2
    chi2_red_free:       float
    aic_free:            float
    bic_free:            float
    # BASELINES
    chi2_red_base_cH0:   float
    chi2_red_base_cH0_2pi: float
    # MOND
    ml_mond:             float
    chi2_mond:           float      # raw chi2
    chi2_red_mond:       float
    aic_mond:            float
    bic_mond:            float
    # ΛCDM NFW
    ml_lcdm:             float
    rho_s:               float
    r_s_kpc:             float
    chi2_lcdm:           float      # raw chi2
    chi2_red_lcdm:       float
    aic_lcdm:            float
    bic_lcdm:            float
    # EFE proxy (populated only if --efe-mode proxy and galaxy in gext table)
    gext_si:             float      # 0.0 if not available
    gdag_proxy_si:       float      # 0.0 if not available
    chi2_red_proxy:      float      # 0.0 if not available
    # Ratios
    ratio_cH0:           float
    ratio_cH0_2pi:       float
    ratio_a0:            float
    # Quality flags
    flag_ml_edge:        bool
    flag_bad_fit:        bool
    flag_low_points:     bool
    flag_bulge_sensitive: bool
    flag_low_quality:    bool

def _get_arrays(sub):
    R   = sub['R_kpc' ].to_numpy()
    Vob = sub['Vobs'  ].to_numpy()
    eVo = sub['e_Vobs'].to_numpy()
    Vg  = sub['Vgas'  ].to_numpy()
    Vd  = sub['Vdisk' ].to_numpy()
    Vb  = sub['Vbul'  ].to_numpy()
    return R, Vob, eVo, Vg, Vd, Vb

# ── Fitting ───────────────────────────────────────────────────────────────────
def _fit_gdag_fixed(R, Vob, eVo, Vg, Vd, Vb, h0, log_bounds=(0, 7)):
    ch0_2pi_kpc = cH0_si(h0)/(2*math.pi)/ACC_CONV
    gN = g_newton_from_vbar2(
        baryonic_velocity_squared(Vg, Vd, Vb, UPS_DISK_FIXED, UPS_BUL_FIXED), R)
    def chi2(log10g):
        return float(np.sum(((Vob - ect_vmod(R, gN, 10**log10g)) / eVo)**2))
    centre = math.log10(ch0_2pi_kpc)
    lo, hi = max(log_bounds[0], centre-3), min(log_bounds[1], centre+3)
    res = minimize_scalar(chi2, bounds=(lo, hi), method='bounded', options={'xatol': 1e-10})
    g_kpc, chi2_min = 10**res.x, float(res.fun)
    g2   = np.linspace(res.x-1.5, res.x+1.5, 400)
    v2   = np.array([chi2(x) for x in g2])
    mask = v2 <= chi2_min + 1.0
    lo_kpc = (10**g2[np.where(mask)[0][ 0]] if np.any(mask) else g_kpc)
    hi_kpc = (10**g2[np.where(mask)[0][-1]] if np.any(mask) else g_kpc)
    return g_kpc, chi2_min, g_kpc - lo_kpc, hi_kpc - g_kpc

def _fit_gdag_free(R, Vob, eVo, Vg, Vd, Vb, h0):
    ch0_2pi_kpc = cH0_si(h0)/(2*math.pi)/ACC_CONV
    centre = math.log10(ch0_2pi_kpc)
    def chi2(params):
        log10g, ups = params
        gN = g_newton_from_vbar2(
            baryonic_velocity_squared(Vg, Vd, Vb, ups, UPS_BUL_FIXED), R)
        return float(np.sum(((Vob - ect_vmod(R, gN, 10**log10g)) / eVo)**2))
    best_val, best_x = np.inf, [centre, 0.5]
    for lg in np.linspace(centre-1.5, centre+1.5, 14):
        for ups in [0.2, 0.4, 0.6, 0.8, 1.0, 1.4]:
            c = chi2([lg, ups])
            if c < best_val:
                best_val, best_x = c, [lg, ups]
    res = minimize(chi2, best_x,
                   bounds=[(centre-2.5, centre+2.5), (0.1, 2.5)],
                   method='L-BFGS-B',
                   options={'ftol': 1e-14, 'gtol': 1e-10, 'maxiter': 1000})
    return 10**res.x[0], float(res.x[1]), float(res.fun)

def _baseline_chi2(R, Vob, eVo, Vg, Vd, Vb, gdag_kpc):
    gN = g_newton_from_vbar2(
        baryonic_velocity_squared(Vg, Vd, Vb, UPS_DISK_FIXED, UPS_BUL_FIXED), R)
    return float(np.sum(((Vob - ect_vmod(R, gN, gdag_kpc)) / eVo)**2))

def _fit_mond(R, Vob, eVo, Vg, Vd, Vb):
    a0_kpc = A0_SI / ACC_CONV
    def chi2(ups):
        gN = g_newton_from_vbar2(
            baryonic_velocity_squared(Vg, Vd, Vb, ups, UPS_BUL_FIXED), R)
        return float(np.sum(((Vob - mond_vmod(R, gN, a0_kpc)) / eVo)**2))
    res = minimize_scalar(chi2, bounds=(0.1, 2.5), method='bounded')
    return float(res.x), float(res.fun)

def _fit_lcdm(R, Vob, eVo, Vg, Vd, Vb):
    def chi2(params):
        ups, log_rho, log_rs = params
        gN = g_newton_from_vbar2(
            baryonic_velocity_squared(Vg, Vd, Vb, ups, UPS_BUL_FIXED), R)
        return float(np.sum(((Vob - lcdm_vmod(R, gN, 10**log_rho, 10**log_rs)) / eVo)**2))
    best_val, best_x = np.inf, [0.5, 7.0, 0.5]
    for ups in [0.3, 0.5, 0.8]:
        for lr in [6.0, 7.0, 8.0]:
            for lrs in [0.0, 0.5, 1.0]:
                c = chi2([ups, lr, lrs])
                if c < best_val:
                    best_val, best_x = c, [ups, lr, lrs]
    res = minimize(chi2, best_x, bounds=[(0.1,2.5),(3,11),(-1,2.5)], method='L-BFGS-B')
    return float(res.x[0]), 10**float(res.x[1]), 10**float(res.x[2]), float(res.fun)

def fit_one(sub: pd.DataFrame, h0: float = 70.0,
            gext_table: Optional[dict] = None,
            alpha_ext: float = 1.0) -> GalaxyFit:
    R, Vob, eVo, Vg, Vd, Vb = _get_arrays(sub)
    N    = len(sub)
    dof2 = max(N - K_ECT_FREE, 1)
    dof1 = max(N - K_MOND,     1)
    dof3 = max(N - K_LCDM,     1)
    BL = gdag_baseline(h0)

    # Fixed ML
    gf_kpc, chi2_f, slo, shi = _fit_gdag_fixed(R, Vob, eVo, Vg, Vd, Vb, h0)
    gf_si = gf_kpc * ACC_CONV
    aic_f, bic_f = compute_aic_bic(chi2_f, K_ECT_FIXED, N)

    # Free ML
    gv_kpc, ml_best, chi2_v = _fit_gdag_free(R, Vob, eVo, Vg, Vd, Vb, h0)
    gv_si = gv_kpc * ACC_CONV
    aic_v, bic_v = compute_aic_bic(chi2_v, K_ECT_FREE, N)

    # Baselines
    chi2_base_cH0     = _baseline_chi2(R, Vob, eVo, Vg, Vd, Vb, BL['cH0']     / ACC_CONV)
    chi2_base_cH0_2pi = _baseline_chi2(R, Vob, eVo, Vg, Vd, Vb, BL['cH0_2pi'] / ACC_CONV)

    # MOND (1 free param: Υ_disk)
    ml_mond, chi2_mond = _fit_mond(R, Vob, eVo, Vg, Vd, Vb)
    aic_mond, bic_mond = compute_aic_bic(chi2_mond, K_MOND, N)

    # ΛCDM (3 free params)
    ml_lcdm, rho_s, r_s_kpc, chi2_lcdm = _fit_lcdm(R, Vob, eVo, Vg, Vd, Vb)
    aic_lcdm, bic_lcdm = compute_aic_bic(chi2_lcdm, K_LCDM, N)

    # EFE proxy (optional)
    gex_si = 0.0; gdag_proxy_si = 0.0; chi2r_proxy = 0.0
    gal_norm = normalize_name(str(sub['Galaxy'].iloc[0]))
    if gext_table and gal_norm in gext_table:
        gex_si        = gext_table[gal_norm]
        gdag_p_si     = ect_gdag_eff_proxy(gf_si, gex_si, alpha_ext)
        gdag_p_kpc    = gdag_p_si / ACC_CONV
        gN_fix        = g_newton_from_vbar2(
            baryonic_velocity_squared(Vg, Vd, Vb, UPS_DISK_FIXED, UPS_BUL_FIXED), R)
        chi2_p        = float(np.sum(((Vob - ect_vmod(R, gN_fix, gdag_p_kpc)) / eVo)**2))
        gdag_proxy_si = gdag_p_si
        chi2r_proxy   = chi2_p / max(N - K_ECT_FIXED, 1)

    # Baryonic mass proxy
    Mbar   = baryonic_mass_proxy(sub, UPS_DISK_FIXED, UPS_BUL_FIXED)
    R_last = float(sub['R_kpc'].max())
    Sigma  = Mbar / (math.pi * R_last**2) if R_last > 0 else 0.0

    # Quality flags
    flag_ml_edge = (ml_best < 0.15) or (ml_best > 2.3)
    flag_bad_fit = (chi2_f / max(N - K_ECT_FIXED, 1)) > 5.0
    flag_low_pts = N < 8
    vbul2_mean   = float(np.mean(UPS_BUL_FIXED * np.sign(Vb) * np.maximum(Vb**2, 0)))
    vbar2_mean   = float(np.mean(baryonic_velocity_squared(Vg, Vd, Vb)))
    flag_bulge   = (vbul2_mean / max(vbar2_mean, 1e-9)) > 0.2
    flag_low_q   = flag_ml_edge or flag_bad_fit or flag_low_pts

    ch0, ch0_2pi = BL['cH0'], BL['cH0_2pi']
    dof_fix = max(N - K_ECT_FIXED, 1)
    return GalaxyFit(
        galaxy=str(sub['Galaxy'].iloc[0]), n_points=N,
        D_Mpc=float(sub['D_Mpc'].iloc[0]),
        R_last=R_last, Mbar_proxy=Mbar, Sigma_bar_proxy=Sigma,
        gdag_fixed_si=gf_si, gdag_fixed_kpc=gf_kpc,
        chi2_fixed=chi2_f, chi2_red_fixed=chi2_f/dof_fix,
        aic_fixed=aic_f, bic_fixed=bic_f,
        sigma_lo_fixed_si=slo*ACC_CONV, sigma_hi_fixed_si=shi*ACC_CONV,
        gdag_free_si=gv_si, gdag_free_kpc=gv_kpc, ml_disk_best=ml_best,
        chi2_free=chi2_v, chi2_red_free=chi2_v/dof2,
        aic_free=aic_v, bic_free=bic_v,
        chi2_red_base_cH0=chi2_base_cH0/max(N-1,1),
        chi2_red_base_cH0_2pi=chi2_base_cH0_2pi/max(N-1,1),
        ml_mond=ml_mond, chi2_mond=chi2_mond, chi2_red_mond=chi2_mond/dof1,
        aic_mond=aic_mond, bic_mond=bic_mond,
        ml_lcdm=ml_lcdm, rho_s=rho_s, r_s_kpc=r_s_kpc,
        chi2_lcdm=chi2_lcdm, chi2_red_lcdm=chi2_lcdm/dof3,
        aic_lcdm=aic_lcdm, bic_lcdm=bic_lcdm,
        gext_si=gex_si, gdag_proxy_si=gdag_proxy_si, chi2_red_proxy=chi2r_proxy,
        ratio_cH0=gf_si/ch0, ratio_cH0_2pi=gf_si/ch0_2pi,
        ratio_a0=gf_si/A0_SI,
        flag_ml_edge=flag_ml_edge, flag_bad_fit=flag_bad_fit,
        flag_low_points=flag_low_pts, flag_bulge_sensitive=flag_bulge,
        flag_low_quality=flag_low_q,
    )

def fit_sample(df, h0=70.0, min_pts=6,
               gext_table=None, alpha_ext=1.0):
    fits = []
    gals = sorted(df['Galaxy'].unique())
    for i, gal in enumerate(gals):
        sub = df[df['Galaxy']==gal].sort_values('R_kpc').reset_index(drop=True)
        if len(sub) < min_pts:
            continue
        try:
            f = fit_one(sub, h0, gext_table=gext_table, alpha_ext=alpha_ext)
            fits.append(f)
            flag = 'EDGE' if f.flag_ml_edge else ('POOR' if f.flag_bad_fit else 'ok')
            print(f"  [{i+1:3d}/{len(gals)}] {gal:<14} "
                  f"chi2_fix={f.chi2_red_fixed:.2f}  "
                  f"chi2_free={f.chi2_red_free:.2f}  "
                  f"g†/(cH0/2pi)={f.ratio_cH0_2pi:.3f}  "
                  f"ML={f.ml_disk_best:.2f}  "
                  f"AIC_fix={f.aic_fixed:.1f}  [{flag}]")
        except Exception as ex:
            print(f"  [{i+1:3d}] skip {gal}: {ex}")
    return sorted(fits, key=lambda f: f.chi2_red_fixed)

# ── Smooth baryonic acceleration ──────────────────────────────────────────────
def _smooth_gN(R_data, Vg, Vd, Vb, R_mod, ml_disk=UPS_DISK_FIXED):
    return g_newton_from_vbar2(
        baryonic_velocity_squared(
            np.interp(R_mod, R_data, Vg),
            np.interp(R_mod, R_data, Vd),
            np.interp(R_mod, R_data, Vb), ml_disk, UPS_BUL_FIXED),
        R_mod)

# ── Rotation curve plotting (GRAYSCALE) ───────────────────────────────────────
def plot_rotation_curve(ax, sub, fit: GalaxyFit, h0=70.0,
                        show_sens_band=True, show_mond=True, show_lcdm=True,
                        show_free=True):
    plt.rcParams.update(GS)
    R, Vob, eVo, Vg, Vd, Vb = _get_arrays(sub)
    Rmod = np.linspace(max(R.min()*0.4, 0.05), R.max()*1.05, 300)

    gN_fix = _smooth_gN(R, Vg, Vd, Vb, Rmod, UPS_DISK_FIXED)
    Vbar   = np.sqrt(np.maximum(gN_fix * Rmod, 0))
    V_ect_fix = ect_vmod(Rmod, gN_fix, fit.gdag_fixed_kpc)
    g2pi_kpc  = cH0_si(h0)/(2*math.pi)/ACC_CONV
    V_2pi     = ect_vmod(Rmod, gN_fix, g2pi_kpc)

    if show_free:
        gN_free    = _smooth_gN(R, Vg, Vd, Vb, Rmod, fit.ml_disk_best)
        V_ect_free = ect_vmod(Rmod, gN_free, fit.gdag_free_kpc)

    # g† sensitivity band (×0.5 – ×2): shows how curve shifts with g†
    # NOTE: this is NOT a computed external-field effect; it is an illustration
    # of the sensitivity of the fit to order-unity variation in g†_eff.
    if show_sens_band:
        V_lo = ect_vmod(Rmod, gN_fix, fit.gdag_fixed_kpc * 0.5)
        V_hi = ect_vmod(Rmod, gN_fix, fit.gdag_fixed_kpc * 2.0)
        ax.fill_between(Rmod, V_lo, V_hi, color=SBD, alpha=0.6,
                        label=r'$g^\dagger$ sensitivity band ($\times$0.5–2)')

    if show_mond:
        gN_mond = _smooth_gN(R, Vg, Vd, Vb, Rmod, fit.ml_mond)
        V_mond  = mond_vmod(Rmod, gN_mond, A0_SI/ACC_CONV)
        ax.plot(Rmod, V_mond, LS_MOND, color=MG, lw=1.4,
                label=f'MOND  χ²={fit.chi2_red_mond:.1f}  AIC={fit.aic_mond:.0f}')

    if show_lcdm:
        gN_lcdm = _smooth_gN(R, Vg, Vd, Vb, Rmod, fit.ml_lcdm)
        V_lcdm  = lcdm_vmod(Rmod, gN_lcdm, fit.rho_s, fit.r_s_kpc)
        ax.plot(Rmod, V_lcdm, LS_LCDM, color=VLG, lw=1.4,
                label=f'ΛCDM  χ²={fit.chi2_red_lcdm:.1f}  AIC={fit.aic_lcdm:.0f}')

    ax.plot(Rmod, Vbar,    '--', color=BAR, lw=1.0, label=f'Baryons (Υ={UPS_DISK_FIXED})')
    ax.plot(Rmod, V_2pi,   '-',  color=MG,  lw=1.0, label=r'ECT $g^\dagger_0=cH_0/2\pi$')
    if show_free:
        ax.plot(Rmod, V_ect_free, '-', color=DG, lw=1.2, alpha=0.6,
                label=f'ECT free Υ={fit.ml_disk_best:.2f}  χ²={fit.chi2_red_free:.1f}')
    ax.plot(Rmod, V_ect_fix, '-', color=BK, lw=1.8,
            label=f'ECT fixed Υ  χ²={fit.chi2_red_fixed:.1f}  AIC={fit.aic_fixed:.0f}')

    # EFE proxy curve — shown only if real g_ext was loaded for this galaxy
    if fit.gdag_proxy_si > 0:
        gdag_proxy_kpc = fit.gdag_proxy_si / ACC_CONV
        V_proxy = ect_vmod(Rmod, gN_fix, gdag_proxy_kpc)
        ax.plot(Rmod, V_proxy, '-', color=LG, lw=1.4, alpha=0.9,
                label=f'ECT+EFE proxy  χ²={fit.chi2_red_proxy:.1f}')

    ax.errorbar(R, Vob, yerr=eVo, fmt='o', ms=2.5, color=BK,
                elinewidth=0.7, capsize=1.2, label='Obs', zorder=5)

    flag_str = ' [EDGE]' if fit.flag_ml_edge else ''
    ax.set_title(f'{fit.galaxy}  N={fit.n_points}{flag_str}\n'
                 f'g†={fit.gdag_fixed_si:.2e} m/s²  ({fit.ratio_cH0_2pi:.2f}·cH₀/2π)',
                 fontsize=6.5)
    ax.set_xlabel('R (kpc)', fontsize=7)
    ax.set_ylabel('V (km/s)', fontsize=7)
    ax.tick_params(labelsize=6)
    ax.legend(fontsize=4.0, loc='lower right', framealpha=0.8)
    ax.set_xlim(left=0); ax.set_ylim(bottom=0)

# ── SET 1: Milky Way ──────────────────────────────────────────────────────────
MW_DATA = {
    'R_kpc': [4,  5,  6,  7,  8,  9, 10, 12, 14, 16, 18, 20, 22, 25],
    'Vobs':  [230,233,235,232,228,226,225,224,222,220,217,214,210,205],
    'e_Vobs':[8,  7,  6,  6,  5,  5,  5,  5,  6,  6,  7,  8,  9, 11],
}

def plot_milky_way(out_path, h0=70.0):
    plt.rcParams.update(GS)
    R   = np.array(MW_DATA['R_kpc'], dtype=float)
    Vob = np.array(MW_DATA['Vobs'],  dtype=float)
    eVo = np.array(MW_DATA['e_Vobs'],dtype=float)
    Rmod = np.linspace(2, 30, 400)

    M_disk = 5.0e10; R_d = 2.5
    from scipy.special import i0, i1, k0, k1
    def v_disk_kms(r):
        y = np.clip(r/(2*R_d), 1e-9, 50)
        t = y**2*(i0(y)*k0(y) - i1(y)*k1(y))
        return np.sqrt(np.maximum(2*G_KPC*M_disk/R_d*t, 0))
    Vbar_MW = v_disk_kms(Rmod)
    gN_MW   = Vbar_MW**2 / Rmod

    g2pi_kpc = cH0_si(h0)/(2*math.pi)/ACC_CONV
    V_2pi_MW = ect_vmod(Rmod, gN_MW, g2pi_kpc)

    from scipy.special import i0 as _i0, i1 as _i1, k0 as _k0, k1 as _k1
    def _vd_sq(r):
        y = np.clip(r/(2*R_d), 1e-9, 50)
        t = y**2*(_i0(y)*_k0(y)-_i1(y)*_k1(y))
        return np.maximum(2*G_KPC*M_disk/R_d*t, 0)
    gN_at_data = _vd_sq(R) / np.maximum(R, 1e-9)

    def chi2_mw(log10g):
        return float(np.sum(((Vob - ect_vmod(R, gN_at_data, 10**log10g))/eVo)**2))
    c0   = math.log10(g2pi_kpc)
    grid = np.linspace(c0-2, c0+2, 300)
    best_c = grid[np.argmin([chi2_mw(x) for x in grid])]
    from scipy.optimize import minimize_scalar as _ms
    res_mw  = _ms(chi2_mw, bounds=(best_c-0.4, best_c+0.4), method='bounded')
    g_best_kpc  = 10**res_mw.x
    chi2_r_mw   = float(res_mw.fun) / max(len(R)-1, 1)
    g_best_si   = g_best_kpc * ACC_CONV
    V_ect_MW    = ect_vmod(Rmod, gN_MW, g_best_kpc)
    V_lo = ect_vmod(Rmod, gN_MW, g_best_kpc*0.5)
    V_hi = ect_vmod(Rmod, gN_MW, g_best_kpc*2.0)
    V_mond_MW = mond_vmod(Rmod, gN_MW, A0_SI/ACC_CONV)
    V_lcdm_MW = lcdm_vmod(Rmod, gN_MW, rho_s=8.5e6, r_s_kpc=20.0)

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    # NOTE: sensitivity band, NOT a computed EFE
    ax.fill_between(Rmod, V_lo, V_hi, color=SBD, alpha=0.65, zorder=1,
                    label=r'$g^\dagger$ sensitivity band ($\times$0.5–2)')
    ax.plot(Rmod, Vbar_MW,   '--', color=BAR, lw=1.2, zorder=2,
            label='Baryons disk (McMillan 2017)')
    ax.plot(Rmod, V_mond_MW, LS_MOND, color=BK, lw=1.8, zorder=5,
            label='MOND (a0 fixed, McGaugh+2016)')
    ax.plot(Rmod, V_lcdm_MW, LS_LCDM, color=DG, lw=1.4, zorder=4,
            label='LCDM NFW (Bland-Hawthorn+2016)')
    ax.plot(Rmod, V_2pi_MW,  '-', color=MG, lw=1.3, zorder=3,
            label='ECT g†=cH0/2pi')
    ax.plot(Rmod, V_ect_MW,  '-', color=BK, lw=2.0, zorder=6,
            label=f'ECT best-fit g†={g_best_si:.2e} m/s²  chi2_r={chi2_r_mw:.2f}')
    ax.errorbar(R, Vob, yerr=eVo, fmt='o', ms=4.0, color=BK,
                elinewidth=0.9, capsize=2.5, zorder=7, label='Eilers+2019')
    ax.set_xlabel('R (kpc)', fontsize=9); ax.set_ylabel('V (km/s)', fontsize=9)
    ax.set_title(f'Milky Way rotation curve  ECT phi-branch\n'
                 f'g†_fit={g_best_si:.2e} m/s²  '
                 f'= {g_best_si/(cH0_si(h0)/(2*math.pi)):.2f} x cH0/2pi  '
                 f'chi2_r = {chi2_r_mw:.2f}', fontsize=9)
    ax.legend(fontsize=7.5, loc='lower left', framealpha=0.9)
    ax.tick_params(labelsize=8)
    ax.set_xlim(0, 30); ax.set_ylim(0, 270)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"Saved: {out_path}"); plt.close(fig)
    return g_best_si, chi2_r_mw

# ── SET 2: SPARC gallery ──────────────────────────────────────────────────────
def plot_sparc_gallery(df, fits, out_path, ncols=4, h0=70.0):
    plt.rcParams.update(GS)
    n = len(fits); nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*3.5, nrows*3.1))
    axes_flat = np.array(axes).reshape(-1)
    for i, fit in enumerate(fits):
        sub = df[df['Galaxy']==fit.galaxy].sort_values('R_kpc').reset_index(drop=True)
        plot_rotation_curve(axes_flat[i], sub, fit, h0=h0,
                            show_sens_band=False, show_free=False)
    for j in range(i+1, len(axes_flat)):
        axes_flat[j].set_visible(False)
    fig.suptitle('ECT φ-branch rotation curves vs MOND vs ΛCDM  (fixed Υ_disk=0.5)',
                 fontsize=9, y=1.002)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}"); plt.close(fig)

# ── SET 3: g† sensitivity curves ─────────────────────────────────────────────
# IMPORTANT TERMINOLOGY:
#   These are NOT computed external-field-effect (EFE) curves.
#   They show how the rotation curve changes if the effective g† differs
#   from the best-fit value by factors ×0.25, ×0.5, ×1, ×2.
#   This illustrates sensitivity to g†_eff, not a computed EFE.
#   A true EFE computation would require g_ext from environment catalogs.
def plot_sensitivity_set(df, fits, out_path, h0=70.0, ncols=3):
    """ECT best-fit + ECT baseline + MOND + ΛCDM on each panel. EFE proxy if available."""
    plt.rcParams.update(GS)
    n = len(fits); nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*3.5, nrows*3.2))
    axes_flat = np.array(axes).reshape(-1)

    for i, fit in enumerate(fits):
        sub  = df[df['Galaxy']==fit.galaxy].sort_values('R_kpc').reset_index(drop=True)
        R, Vob, eVo, Vg, Vd, Vb = _get_arrays(sub)
        Rmod = np.linspace(max(R.min()*0.4, 0.05), R.max()*1.05, 300)
        gN   = _smooth_gN(R, Vg, Vd, Vb, Rmod, UPS_DISK_FIXED)
        ax   = axes_flat[i]

        # ECT best-fit curve (fixed Υ)
        V_best = ect_vmod(Rmod, gN, fit.gdag_fixed_kpc)
        ax.plot(Rmod, V_best, '-', color=BK, lw=2.2, zorder=3,
                label=f'ECT best-fit  χ²={fit.chi2_red_fixed:.1f}  AIC={fit.aic_fixed:.0f}')
        # ECT baseline cH0/2π
        g2pi_kpc_s = cH0_si(h0) / (2 * math.pi) / ACC_CONV
        V_base = ect_vmod(Rmod, gN, g2pi_kpc_s)
        ax.plot(Rmod, V_base, '-', color=MG, lw=1.2, zorder=3,
                label=r'ECT $g^\dagger_0 = cH_0/2\pi$')

        # LCDM
        gN_lcdm = _smooth_gN(R, Vg, Vd, Vb, Rmod, fit.ml_lcdm)
        V_lcdm  = lcdm_vmod(Rmod, gN_lcdm, fit.rho_s, fit.r_s_kpc)
        ax.plot(Rmod, V_lcdm, LS_LCDM, color=DG, lw=1.5, zorder=4,
                label=f'ΛCDM  χ²={fit.chi2_red_lcdm:.1f}')

        # MOND: always on top
        gN_mond = _smooth_gN(R, Vg, Vd, Vb, Rmod, fit.ml_mond)
        V_mond  = mond_vmod(Rmod, gN_mond, A0_SI/ACC_CONV)
        ax.plot(Rmod, V_mond, LS_MOND, color=BK, lw=2.2, zorder=8,
                label=f'MOND  χ²={fit.chi2_red_mond:.1f}')

        # EFE proxy curve on sensitivity plot
        if fit.gdag_proxy_si > 0:
            gdag_proxy_kpc = fit.gdag_proxy_si / ACC_CONV
            V_proxy = ect_vmod(Rmod, gN, gdag_proxy_kpc)
            ax.plot(Rmod, V_proxy, '-', color=LG, lw=1.8, zorder=7,
                    label=f'ECT+EFE proxy  χ²={fit.chi2_red_proxy:.1f}')

        ax.errorbar(R, Vob, yerr=eVo, fmt='o', ms=2.8, color=BK,
                    elinewidth=0.8, capsize=1.5, zorder=9, label='Obs')

        ax.set_title(f'{fit.galaxy}  g†={fit.gdag_fixed_si:.2e} m/s²\n'
                     f'({fit.ratio_cH0_2pi:.2f}·cH₀/2π)', fontsize=6.5)
        ax.set_xlabel('R (kpc)', fontsize=7); ax.set_ylabel('V (km/s)', fontsize=7)
        ax.tick_params(labelsize=6)
        ax.legend(fontsize=4.0, loc='lower right', framealpha=0.85)
        ax.set_xlim(left=0); ax.set_ylim(bottom=0)

    for j in range(i+1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.suptitle(
        r'ECT $g^\dagger$ best-fit curves vs MOND vs $\Lambda$CDM' '\n'
        r'ECT+EFE proxy shown where $g_{\rm ext}$ data available  '
        r'(Level-1: $g_{\rm ext} \ll cH_0/2\pi$)',
        fontsize=8, y=1.002)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {out_path}"); plt.close(fig)

# ── Diagnostic scatter helper ─────────────────────────────────────────────────
def _scatter_gray(ax, x, y, flags, xlabel, ylabel, title,
                  ref_y=None, ref_label=None, log_x=False, log_y=False,
                  ref_y2=None, ref_label2=None):
    good = np.array([not f for f in flags])
    bad  = np.array(flags)
    if good.any():
        ax.scatter(x[good], y[good], s=12, color=DG, alpha=0.7, marker='o', label='clean fit')
    if bad.any():
        ax.scatter(x[bad],  y[bad],  s=12, color=MG, alpha=0.5, marker='x', label='flagged')
    if ref_y is not None:
        ax.axhline(ref_y, color=BK, lw=1.2, ls='--', label=ref_label)
    if ref_y2 is not None:
        ax.axhline(ref_y2, color=MG, lw=0.8, ls=':', label=ref_label2)
    ax.set_xlabel(xlabel, fontsize=8); ax.set_ylabel(ylabel, fontsize=8)
    ax.set_title(title, fontsize=8)
    if log_x: ax.set_xscale('log')
    if log_y: ax.set_yscale('log')
    ax.legend(fontsize=7)

# ── Diagnostics ───────────────────────────────────────────────────────────────
def plot_diagnostics(fits: List[GalaxyFit], out_dir: str, h0=70.0):
    """Generate all diagnostic figures. MUST be called with the full fits list."""
    N = len(fits)
    print(f"  plot_diagnostics: N={N} galaxies")
    plt.rcParams.update(GS)

    ratios   = np.array([f.ratio_cH0_2pi  for f in fits])
    gdag_si  = np.array([f.gdag_fixed_si   for f in fits])
    gdag_fr  = np.array([f.gdag_free_si    for f in fits])
    chi2_fix = np.array([f.chi2_red_fixed  for f in fits])
    chi2_fre = np.array([f.chi2_red_free   for f in fits])
    chi2_mon = np.array([f.chi2_red_mond   for f in fits])
    chi2_lcd = np.array([f.chi2_red_lcdm   for f in fits])
    aic_fix  = np.array([f.aic_fixed        for f in fits])
    aic_fre  = np.array([f.aic_free         for f in fits])
    aic_mon  = np.array([f.aic_mond         for f in fits])
    aic_lcd  = np.array([f.aic_lcdm         for f in fits])
    bic_fix  = np.array([f.bic_fixed        for f in fits])
    bic_fre  = np.array([f.bic_free         for f in fits])
    bic_mon  = np.array([f.bic_mond         for f in fits])
    bic_lcd  = np.array([f.bic_lcdm         for f in fits])
    ml_free  = np.array([f.ml_disk_best    for f in fits])
    Mbar     = np.array([f.Mbar_proxy      for f in fits])
    Sigma    = np.array([f.Sigma_bar_proxy for f in fits])
    R_last   = np.array([f.R_last          for f in fits])
    flags    = [f.flag_low_quality         for f in fits]
    ch0_ref  = cH0_si(h0)/(2*math.pi)
    ch0_val  = cH0_si(h0)

    # ── 2×2 combined scatter ──────────────────────────────────────────────
    r_ml_corr = np.corrcoef(ml_free, np.log10(gdag_si))[0,1]
    fig4, ax4s = plt.subplots(2, 2, figsize=(10, 7))
    ax4s = ax4s.reshape(-1)
    _scatter_gray(ax4s[0], Mbar, gdag_si, flags, 'Mbar proxy (Msun)', 'g_dagger (m/s^2)',
                  '(A) g† vs baryonic mass', ref_y=ch0_ref, ref_label='cH0/2pi',
                  ref_y2=ch0_val, ref_label2='cH0', log_x=True, log_y=True)
    _scatter_gray(ax4s[1], Sigma, gdag_si, flags, 'Sigma_bar (Msun/kpc^2)', 'g_dagger (m/s^2)',
                  '(B) g† vs surface density', ref_y=ch0_ref, ref_label='cH0/2pi',
                  log_x=True, log_y=True)
    _scatter_gray(ax4s[2], ml_free, gdag_si, flags, 'Fitted Upsilon_disk', 'g_dagger (m/s^2)',
                  f'(C) g† vs M/L  (Pearson r={r_ml_corr:.2f})',
                  ref_y=ch0_ref, ref_label='cH0/2pi', log_y=True)
    _scatter_gray(ax4s[3], chi2_fix, gdag_si, flags, 'chi2_red (ECT fixed ML)', 'g_dagger (m/s^2)',
                  '(D) g† vs fit quality', ref_y=ch0_ref, ref_label='cH0/2pi', log_y=True)
    ax4s[3].axvline(5, color=MG, lw=1, ls=':', label='chi2=5 cut')
    ax4s[3].legend(fontsize=7)
    fig4.suptitle(f'ECT g†_eff diagnostic scatter plots ({N} galaxies)\n'
                  'Dashed line = cH₀/2π baseline; dotted = cH₀', fontsize=9)
    fig4.tight_layout()
    fig4.savefig(os.path.join(out_dir,'diag_gdag_scatter4.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig4)

    # ── Individual scatter files ───────────────────────────────────────────
    for arr, xl, yl, ttl, lx, ly, fname in [
        (Mbar,    r'$M_{\rm bar}$ (proxy, $M_\odot$)', r'$g^\dagger$ (m/s²)',
         r'$g^\dagger$ vs baryonic mass', True, True, 'diag_gdag_vs_mbar'),
        (Sigma,   r'$\Sigma_{\rm bar}$ ($M_\odot$/kpc²)', r'$g^\dagger$ (m/s²)',
         r'$g^\dagger$ vs surface density', True, True, 'diag_gdag_vs_sigma'),
        (ml_free, r'Fitted $\Upsilon_{\rm disk}$', r'$g^\dagger$ (m/s²)',
         r'$g^\dagger$ vs $\Upsilon_{\rm disk}$', False, True, 'diag_gdag_vs_mldisk'),
        (chi2_fix,r'$\chi^2_{\rm red}$ (ECT fixed ML)', r'$g^\dagger$ (m/s²)',
         r'$g^\dagger$ vs fit quality', False, True, 'diag_gdag_vs_chi2'),
        (R_last,  r'$R_{\rm last}$ (kpc)', r'$g^\dagger$ (m/s²)',
         r'$g^\dagger$ vs outermost radius', False, True, 'diag_gdag_vs_rlast'),
    ]:
        fig, ax = plt.subplots(figsize=(5, 3.8))
        _scatter_gray(ax, arr, gdag_si, flags, xl, yl, ttl,
                      ref_y=ch0_ref, ref_label=r'$cH_0/2\pi$', log_x=lx, log_y=ly)
        if fname == 'diag_gdag_vs_chi2':
            ax.axvline(5, color=MG, lw=1, ls=':', label='χ²=5 threshold')
            ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, fname+'.pdf'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    # ── Fixed vs free g† scatter ──────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.scatter(gdag_si, gdag_fr, s=12, color=DG, alpha=0.6, label='galaxies')
    lim = [min(gdag_si.min(), gdag_fr.min())*0.8,
           max(gdag_si.max(), gdag_fr.max())*1.2]
    ax.plot(lim, lim, '-', color=BK, lw=0.8, label='y=x')
    ax.set_xlabel(r'$g^\dagger$ fixed $\Upsilon$ (m/s²)', fontsize=8)
    ax.set_ylabel(r'$g^\dagger$ free $\Upsilon$ (m/s²)', fontsize=8)
    ax.set_title(r'Fixed-ML vs free-ML $g^\dagger$ (M/L degeneracy check)', fontsize=8)
    ax.set_xscale('log'); ax.set_yscale('log')
    r_val = np.corrcoef(np.log10(gdag_si), np.log10(gdag_fr))[0,1]
    ax.text(0.05, 0.95, f'log–log Pearson r = {r_val:.3f}',
            transform=ax.transAxes, fontsize=8, va='top')
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir,'diag_fixed_vs_free_gdag.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ── Fixed vs free chi2 scatter ────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ax.scatter(chi2_fix, chi2_fre, s=12, color=DG, alpha=0.6, label='galaxies')
    lim2 = [0, min(chi2_fix.max(), 15)]
    ax.plot([0, 15], [0, 15], '-', color=BK, lw=0.8, label='y=x')
    ax.set_xlabel(r'$\chi^2_{\rm red}$ fixed $\Upsilon$', fontsize=8)
    ax.set_ylabel(r'$\chi^2_{\rm red}$ free $\Upsilon$', fontsize=8)
    ax.set_title(r'Fixed-ML vs free-ML $\chi^2_{\rm red}$', fontsize=8)
    ax.set_xlim(0, 12); ax.set_ylim(0, 12)
    frac_better = np.mean(chi2_fre < chi2_fix) * 100
    ax.text(0.05, 0.95, f'Free ML improves chi2: {frac_better:.0f}% of galaxies',
            transform=ax.transAxes, fontsize=7, va='top')
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir,'diag_fixed_vs_free_chi2.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # ── chi2 comparison: 4 panels ─────────────────────────────────────────
    fig_c, axc = plt.subplots(1, 4, figsize=(13, 3.8), sharey=True)
    bins_c = np.linspace(0, 12, 25)
    for ax_c, vals_c, ttl_c, hatch_c in zip(
        axc,
        [chi2_fix, chi2_fre, chi2_mon, chi2_lcd],
        ['ECT fixed Υ=0.5\n(1 free param: g†)',
         'ECT free Υ\n(2 free params: g†, Υ)',
         'MOND  a0 fixed\n(1 free param: Υ)',
         'ΛCDM NFW\n(3 params: Υ, ρ_s, r_s)'],
        ['/', '\\', 'x', '.']
    ):
        ax_c.hist(np.clip(vals_c,0,12), bins=bins_c, color=DG, alpha=0.65,
                  edgecolor=BK, lw=0.4, hatch=hatch_c)
        ax_c.axvline(1.0, color=BK, lw=1.2, ls='--', label='χ²=1')
        ax_c.axvline(np.median(vals_c), color=BK, lw=1.5, ls='-',
                     label=f'Median={np.median(vals_c):.1f}')
        ax_c.axvline(5.0, color=MG, lw=0.8, ls=':', label='χ²=5 cut')
        pct_c = np.mean(vals_c<5)*100
        ax_c.set_title(ttl_c + f'\nGood (χ²<5): {pct_c:.0f}%', fontsize=7.5)
        ax_c.set_xlabel('χ²_red (clipped at 12)', fontsize=8)
        ax_c.legend(fontsize=6, loc='upper right')
        ax_c.tick_params(labelsize=7)
    axc[0].set_ylabel('N galaxies', fontsize=8)
    fig_c.suptitle(
        f'Fit quality comparison — {N} SPARC galaxies\n'
        'χ²_red histogram per model  |  NOTE: ΛCDM has 3 free params vs 1 for ECT/MOND',
        fontsize=9)
    fig_c.tight_layout()
    fig_c.savefig(os.path.join(out_dir,'diag_chi2_comparison.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig_c)

    # ── AIC comparison: 4 panels ──────────────────────────────────────────
    # AIC correctly penalises extra parameters → honest comparison
    fig_a, axa = plt.subplots(1, 4, figsize=(13, 3.8), sharey=True)
    for ax_a, vals_a, ttl_a, hatch_a in zip(
        axa,
        [aic_fix, aic_fre, aic_mon, aic_lcd],
        ['ECT fixed Υ=0.5\n(k=1)', 'ECT free Υ\n(k=2)',
         'MOND\n(k=1)', 'ΛCDM NFW\n(k=3)'],
        ['/', '\\', 'x', '.']
    ):
        clipped = np.clip(vals_a, -50, 300)
        ax_a.hist(clipped, bins=30, color=DG, alpha=0.65,
                  edgecolor=BK, lw=0.4, hatch=hatch_a)
        ax_a.axvline(np.median(vals_a), color=BK, lw=1.5, ls='-',
                     label=f'Median={np.median(vals_a):.0f}')
        pct_a = np.mean(vals_a < np.median(aic_fix))*100
        ax_a.set_title(ttl_a + f'\nBelow ECT-fixed median: {pct_a:.0f}%', fontsize=7.5)
        ax_a.set_xlabel('AIC (clipped)', fontsize=8)
        ax_a.legend(fontsize=6, loc='upper right')
        ax_a.tick_params(labelsize=7)
    axa[0].set_ylabel('N galaxies', fontsize=8)
    # wins: galaxies where ECT fixed beats MOND and ΛCDM by AIC
    ect_beats_mond_aic = np.mean(aic_fix < aic_mon)*100
    ect_beats_lcdm_aic = np.mean(aic_fix < aic_lcd)*100
    fig_a.suptitle(
        f'AIC comparison (accounts for model complexity) — {N} galaxies\n'
        f'ECT fixed beats MOND by AIC: {ect_beats_mond_aic:.0f}%  |  '
        f'beats ΛCDM by AIC: {ect_beats_lcdm_aic:.0f}%',
        fontsize=9)
    fig_a.tight_layout()
    fig_a.savefig(os.path.join(out_dir,'diag_aic_comparison.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig_a)

    # ── g†/(cH0/2pi) histogram: fixed vs free M/L ─────────────────────────
    ratios_free = np.array([f.gdag_free_si/ch0_ref for f in fits])
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, r, title in [
        (axes[0], ratios,      'g† fixed Υ=0.5  (no ML degeneracy)'),
        (axes[1], ratios_free, 'g† free Υ  (includes ML degeneracy)'),
    ]:
        ax.hist(np.clip(r, 0, 8), bins=30, color=DG, alpha=0.75, edgecolor='white', lw=0.4)
        ax.axvline(1.0, color=BK, lw=1.5, ls='--', label='cH₀/2π')
        ax.axvline(np.median(r), color=BK, lw=1.2, label=f'Median={np.median(r):.2f}')
        ax.set_xlabel(r'$g^\dagger_{\rm eff}\,/\,(cH_0/2\pi)$'); ax.set_ylabel('N galaxies')
        ax.set_title(title); ax.legend(fontsize=7)
    fig.suptitle(f'Comparing fixed vs free Υ fits  |  N={N} galaxies', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir,'diag_gdag_histogram.pdf'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    # ── EFE proxy diagnostics (only if proxy data available) ──────────────
    gext_arr = np.array([f.gext_si for f in fits])
    has_gext  = gext_arr > 0
    n_gext    = np.sum(has_gext)

    if n_gext >= 3:
        print(f"  EFE diagnostics: {n_gext} galaxies with g_ext data")
        gdag_with  = gdag_si[has_gext]
        gext_with  = gext_arr[has_gext]
        proxy_with = np.array([f.gdag_proxy_si for f in fits])[has_gext]
        flags_with = [f.flag_low_quality for f, h in zip(fits, has_gext) if h]

        # Plot A: g†_fit vs g_ext
        fig_e, axes_e = plt.subplots(1, 2, figsize=(10, 4.5))

        ax_ea = axes_e[0]
        good_e = np.array([not fl for fl in flags_with])
        bad_e  = np.array(flags_with)
        if good_e.any():
            ax_ea.scatter(gext_with[good_e], gdag_with[good_e],
                          s=20, color=DG, alpha=0.8, marker='o', label='clean fit')
        if bad_e.any():
            ax_ea.scatter(gext_with[bad_e], gdag_with[bad_e],
                          s=20, color=MG, alpha=0.5, marker='x', label='flagged')
        ax_ea.axhline(ch0_ref, color=BK, lw=1.2, ls='--', label=r'$cH_0/2\pi$')
        ax_ea.set_xscale('log'); ax_ea.set_yscale('log')
        ax_ea.set_xlabel(r'$g_{\rm ext}$ (m/s²) — Level 1 proxy', fontsize=8)
        ax_ea.set_ylabel(r'$g^\dagger_{\rm fit}$ (m/s²)', fontsize=8)
        ax_ea.set_title(
            r'$g^\dagger_{\rm fit}$ vs $g_{\rm ext}$' + f'  (N={n_gext})', fontsize=8)
        if n_gext >= 2:
            r_e = np.corrcoef(np.log10(gext_with), np.log10(gdag_with))[0,1]
            ax_ea.text(0.05, 0.95, f'log-log Pearson r={r_e:.3f}\n'
                       f'(anti-correlation expected if EFE active)',
                       transform=ax_ea.transAxes, fontsize=7, va='top')
        ax_ea.legend(fontsize=7)

        # Plot B: g†_fit/g†_0 vs g_ext/g†_0  (dimensionless)
        ax_eb = axes_e[1]
        ratio_fit   = gdag_with  / ch0_ref
        ratio_gext  = gext_with  / ch0_ref
        if good_e.any():
            ax_eb.scatter(ratio_gext[good_e], ratio_fit[good_e],
                          s=20, color=DG, alpha=0.8, marker='o', label='clean fit')
        if bad_e.any():
            ax_eb.scatter(ratio_gext[bad_e], ratio_fit[bad_e],
                          s=20, color=MG, alpha=0.5, marker='x', label='flagged')
        ax_eb.axhline(1.0, color=BK, lw=1.2, ls='--', label=r'$g^\dagger_0 = cH_0/2\pi$')
        ax_eb.set_xscale('log')
        ax_eb.set_xlabel(r'$g_{\rm ext}/g^\dagger_0$ (dimensionless)', fontsize=8)
        ax_eb.set_ylabel(r'$g^\dagger_{\rm fit}/g^\dagger_0$', fontsize=8)
        ax_eb.set_title(
            'Dimensionless EFE ratio plot' + f'  (N={n_gext})', fontsize=8)
        ax_eb.legend(fontsize=7)

        fig_e.suptitle(
            'EFE diagnostic — Level 1 nearest-neighbour proxy\n'
            r'NOTE: Level 1 estimates $g_{\rm ext} \sim G M_{{\rm neigh}}/d^2$; '
            'typical values $\ll cH_0/2\pi$',
            fontsize=8)
        fig_e.tight_layout()
        fig_e.savefig(os.path.join(out_dir,'diag_efe_gext.pdf'),
                      dpi=150, bbox_inches='tight')
        plt.close(fig_e)
        print(f"  EFE diagnostic saved: diag_efe_gext.pdf")

        # Summary: compare chi2_red_base_cH0_2pi vs chi2_red_proxy
        chi2_base_arr  = np.array([f.chi2_red_base_cH0_2pi for f, h in zip(fits, has_gext) if h])
        chi2_proxy_arr = np.array([f.chi2_red_proxy         for f, h in zip(fits, has_gext) if h])
        valid_proxy = chi2_proxy_arr > 0
        if valid_proxy.sum() >= 2:
            delta_chi2 = np.median(chi2_base_arr[valid_proxy] - chi2_proxy_arr[valid_proxy])
            print(f"  EFE proxy vs baseline cH0/2pi: median Δchi2_red = {delta_chi2:+.3f}")
            print(f"  (positive = proxy improves fit, negative = proxy worsens fit)")
    else:
        print(f"  EFE diagnostics skipped: only {n_gext} galaxies with g_ext < 3")

    print(f"  Diagnostics saved to {out_dir}")

# ── Five-galaxy comparison ────────────────────────────────────────────────────
FIVE_GALS_NORM = [normalize_name(g) for g in
                  ['DDO154', 'NGC2403', 'NGC3198', 'NGC6503', 'UGC02885']]

def save_five_comparison(fits, out_path, h0=70.0):
    ch0_2pi = cH0_si(h0)/(2*math.pi)
    # Build map using normalized names to avoid UGC02885 vs UGC2885 mismatch
    fit_map = {normalize_name(f.galaxy): f for f in fits}
    rows = []
    for gal_norm in FIVE_GALS_NORM:
        if gal_norm not in fit_map:
            print(f"  WARNING: {gal_norm} not found in fit results. "
                  f"Available (sample): {list(fit_map.keys())[:10]}")
            continue
        f = fit_map[gal_norm]
        rows.append({
            'galaxy': f.galaxy, 'N_pts': f.n_points,
            'gdag_fixed_si': f.gdag_fixed_si,
            'gdag_fixed/a0': f.gdag_fixed_si/A0_SI,
            'gdag_fixed/(cH0/2pi)': f.ratio_cH0_2pi,
            'chi2_red_fixed': f.chi2_red_fixed,
            'aic_fixed': f.aic_fixed, 'bic_fixed': f.bic_fixed,
            'gdag_free_si': f.gdag_free_si,
            'gdag_free/(cH0/2pi)': f.gdag_free_si/ch0_2pi,
            'chi2_red_free': f.chi2_red_free,
            'aic_free': f.aic_free, 'bic_free': f.bic_free,
            'ML_disk_best': f.ml_disk_best,
            'chi2_red_mond': f.chi2_red_mond,
            'aic_mond': f.aic_mond, 'bic_mond': f.bic_mond,
            'chi2_red_lcdm': f.chi2_red_lcdm,
            'aic_lcdm': f.aic_lcdm, 'bic_lcdm': f.bic_lcdm,
            'flag_ml_edge': f.flag_ml_edge, 'flag_bad_fit': f.flag_bad_fit,
        })
    pd.DataFrame(rows).to_csv(out_path, index=False, float_format='%.4e')
    print(f"Saved: {out_path}  ({len(rows)}/5 galaxies)")
    print(f"\n{'Galaxy':<12} {'g†(m/s²)':>12} {'g†/a0':>7} {'g†/(cH0/2pi)':>13} "
          f"{'chi2_r':>7} {'AIC_fix':>9} {'chi2_mond':>10} {'AIC_mond':>9}")
    print('-'*80)
    for r in rows:
        print(f"{r['galaxy']:<12} {r['gdag_fixed_si']:>12.3e} "
              f"{r['gdag_fixed/a0']:>7.3f} {r['gdag_fixed/(cH0/2pi)']:>13.3f} "
              f"{r['chi2_red_fixed']:>7.2f} {r['aic_fixed']:>9.1f} "
              f"{r['chi2_red_mond']:>10.2f} {r['aic_mond']:>9.1f}")

# ── Summary report ─────────────────────────────────────────────────────────────
def write_summary(fits, out_path, h0=70.0, mw_result=None, error_floor=2.0):
    ch0_2pi = cH0_si(h0)/(2*math.pi)
    ratios_fix  = [f.ratio_cH0_2pi        for f in fits]
    ratios_free = [f.gdag_free_si/ch0_2pi for f in fits]
    chi2_fix    = [f.chi2_red_fixed        for f in fits]
    chi2_mond   = [f.chi2_red_mond         for f in fits]
    chi2_lcdm   = [f.chi2_red_lcdm         for f in fits]
    chi2_fre    = [f.chi2_red_free         for f in fits]
    aic_fix     = [f.aic_fixed             for f in fits]
    aic_fre     = [f.aic_free              for f in fits]
    aic_mond    = [f.aic_mond              for f in fits]
    aic_lcdm    = [f.aic_lcdm             for f in fits]
    bic_fix     = [f.bic_fixed             for f in fits]
    bic_fre     = [f.bic_free              for f in fits]
    bic_mond    = [f.bic_mond              for f in fits]
    bic_lcdm    = [f.bic_lcdm             for f in fits]
    ml_free     = [f.ml_disk_best          for f in fits]
    good        = [not f.flag_low_quality  for f in fits]

    # clean sample: no quality flags AND chi2_r < 5
    clean = [not f.flag_low_quality and f.chi2_red_fixed < 5.0 for f in fits]
    ratios_clean = [r for r, c in zip(ratios_fix, clean) if c]
    chi2_clean   = [c2 for c2, c in zip(chi2_fix, clean) if c]

    ect_beats_mond_chi2 = sum(1 for e,m in zip(chi2_fix, chi2_mond) if e<m)
    ect_beats_mond_aic  = sum(1 for e,m in zip(aic_fix, aic_mond) if e<m)
    ect_beats_lcdm_aic  = sum(1 for e,m in zip(aic_fix, aic_lcdm) if e<m)

    with open(out_path, 'w') as fp:
        def w(s=''): fp.write(s + '\n')
        w('ECT SPARC Rotation Curve Analysis — Summary Report (v3d)'); w('='*60)
        w(f'H0 assumed: {h0:.1f} km/s/Mpc')
        w(f'cH0       = {cH0_si(h0):.3e} m/s^2')
        w(f'cH0/(2pi) = {ch0_2pi:.3e} m/s^2')
        w(f'a0 (MOND) = {A0_SI:.3e} m/s^2')
        w(f'Error floor: {error_floor:.1f} km/s'); w()

        w('DATA')
        w(f'  Total galaxies fitted          : {len(fits)}')
        w(f'  Clean fits (no quality flags)  : {sum(good)} / {len(fits)}')
        w(f'  Clean + chi2<5 (used below)    : {sum(clean)} / {len(fits)}')
        w(f'  Galaxies with N_pts < 8        : {sum(f.flag_low_points for f in fits)}')
        w(f'  Galaxies with ML at edge       : {sum(f.flag_ml_edge for f in fits)}')
        w(f'  Galaxies with chi2_r > 5       : {sum(f.flag_bad_fit for f in fits)}'); w()

        w('ECT FIXED M/L  (Υ_disk=0.5, only g† fitted — k=1, no ML degeneracy)')
        w(f'  Median g†/(cH0/2pi)   = {np.median(ratios_fix):.3f}')
        w(f'  Mean   g†/(cH0/2pi)   = {np.mean(ratios_fix):.3f}')
        w(f'  Std    g†/(cH0/2pi)   = {np.std(ratios_fix):.3f}')
        w(f'  Frac in [0.5, 2.0]    = {np.mean([(0.5<=r<=2) for r in ratios_fix])*100:.0f}%')
        w(f'  Median chi2_red       = {np.median(chi2_fix):.2f}')
        w(f'  Good fits chi2_r < 5  = {sum(c<5 for c in chi2_fix)}/{len(fits)} '
          f'= {sum(c<5 for c in chi2_fix)/len(fits)*100:.0f}%')
        w(f'  Median AIC            = {np.median(aic_fix):.1f}')
        w(f'  Median BIC            = {np.median(bic_fix):.1f}'); w()

        w('ECT FIXED M/L — CLEAN SUBSAMPLE (no flags, chi2<5)')
        w(f'  N clean               = {sum(clean)}')
        if ratios_clean:
            w(f'  Median g†/(cH0/2pi)   = {np.median(ratios_clean):.3f}')
            w(f'  Std    g†/(cH0/2pi)   = {np.std(ratios_clean):.3f}')
            w(f'  Median chi2_red       = {np.median(chi2_clean):.2f}'); w()

        w('ECT FREE M/L  (g† + Υ_disk both fitted — k=2, includes ML degeneracy)')
        w(f'  Median g†/(cH0/2pi)   = {np.median(ratios_free):.3f}')
        w(f'  Std    g†/(cH0/2pi)   = {np.std(ratios_free):.3f}')
        w(f'  Median Υ_disk         = {np.median(ml_free):.3f}')
        w(f'  (photometric reference ~0.5, Schombert+2019)')
        w(f'  Median chi2_red       = {np.median(chi2_fre):.2f}')
        w(f'  Median AIC            = {np.median(aic_fre):.1f}')
        w(f'  Median BIC            = {np.median(bic_fre):.1f}'); w()

        w('COMPARISON  (chi2_red)')
        w(f'  Median ECT fixed chi2_r = {np.median(chi2_fix):.2f}')
        w(f'  Median MOND chi2_r      = {np.median(chi2_mond):.2f}')
        w(f'  Median LCDM chi2_r      = {np.median(chi2_lcdm):.2f}')
        w(f'  ECT better than MOND    = {ect_beats_mond_chi2}/{len(fits)} '
          f'= {ect_beats_mond_chi2/len(fits)*100:.0f}%  [by chi2_r]')
        w()
        w('COMPARISON  (AIC — penalises extra parameters)')
        w(f'  Median ECT fixed AIC    = {np.median(aic_fix):.1f}  (k=1)')
        w(f'  Median ECT free  AIC    = {np.median(aic_fre):.1f}  (k=2)')
        w(f'  Median MOND AIC         = {np.median(aic_mond):.1f}  (k=1)')
        w(f'  Median LCDM AIC         = {np.median(aic_lcdm):.1f}  (k=3)')
        w(f'  ECT fixed beats MOND    = {ect_beats_mond_aic}/{len(fits)} '
          f'= {ect_beats_mond_aic/len(fits)*100:.0f}%  [by AIC]')
        w(f'  ECT fixed beats LCDM    = {ect_beats_lcdm_aic}/{len(fits)} '
          f'= {ect_beats_lcdm_aic/len(fits)*100:.0f}%  [by AIC]')
        w(f'  NOTE: AIC < 0 for perfectly-fitting models; '
          f'relative ΔAIC is what matters.')
        w()
        w('COMPARISON  (BIC — stronger penalty for parameters)')
        w(f'  Median ECT fixed BIC    = {np.median(bic_fix):.1f}')
        w(f'  Median MOND BIC         = {np.median(bic_mond):.1f}')
        w(f'  Median LCDM BIC         = {np.median(bic_lcdm):.1f}'); w()

        w('MILKY WAY')
        if mw_result:
            g_mw, chi2_mw = mw_result
            w(f'  Best-fit g†      = {g_mw:.3e} m/s^2')
            w(f'  g†/(cH0/2pi)    = {g_mw/ch0_2pi:.3f}')
            w(f'  chi2_red         = {chi2_mw:.2f}')
        else:
            w('  (not computed)')
        w()

        # EFE proxy results block (only if data available)
        has_proxy = [f for f in fits if f.gext_si > 0]
        if has_proxy:
            w()
            w('EFE PROXY RESULTS (Level-1 nearest-neighbour)')
            w(f'  Galaxies with g_ext data    : {len(has_proxy)} / {len(fits)}')
            g_ext_arr  = np.array([f.gext_si for f in has_proxy])
            gdag_arr   = np.array([f.gdag_fixed_si for f in has_proxy])
            gdag0_arr  = np.array([cH0_si(h0)/(2*math.pi)] * len(has_proxy))
            w(f'  Median g_ext (m/s^2)        : {np.median(g_ext_arr):.3e}')
            w(f'  Median g_ext / g†_0         : {np.median(g_ext_arr/gdag0_arr):.6f}')
            w()
            w('  IMPORTANT FINDING:')
            w(f'  Level-1 g_ext << cH_0/(2pi) by factor ~{np.median(gdag0_arr/g_ext_arr):.0f}x')
            w('  => Level-1 EFE proxy corrections to g†_eff are negligible (< 0.1%).')
            w('  => The observed scatter in g†_eff is NOT explained by Level-1 EFE.')
            w('  => Possible explanations:')
            w('     (i)  Higher-order environment (Level 2/3: group potential, LSS)')
            w('     (ii) M/L systematics dominate the scatter')
            w('     (iii) ECT internal physics beyond the Level-1 proxy')
            w('  => Full EFE requires Level-2: summing over all group members.')

        w()
        w('SENSITIVITY BAND NOTE')
        w('  The grey band on rotation-curve plots (×0.5–×2) is a')
        w('  g†-sensitivity band, NOT a computed external-field effect.')
        w('  It shows how the predicted rotation curve changes if g†_eff')
        w('  varies by a factor of two in either direction.')
        w('  A genuine EFE computation would require g_ext from environment')
        w('  catalogs (HyperLeda, AMIGA group membership).')
        w()
        w('INTERPRETATION NOTE (honest assessment)')
        w('  The present results are a first-pass test of the ECT galactic')
        w('  closure. Key findings:')
        w('  - The preferred baseline cH_0/(2π) is numerically plausible')
        w('    (median ratio ~0.86 for fixed ML) but not yet proven.')
        w('  - Scatter in g†_eff is present in both fixed and free ML modes,')
        w('    suggesting it is not purely a fitting artefact.')
        w('  - ECT (k=1) and MOND (k=1) are on equal footing by parameter count.')
        w('    AIC comparison is therefore the honest comparison vs ΛCDM (k=3).')
        w('  - A decisive interpretation requires:')
        w('    (i)   explicit EFE/environment modelling with real g_ext,')
        w('    (ii)  photometric M/L constraints (Schombert+2019 SPS),')
        w('    (iii) bulge-dominated galaxy treatment improvement.')
        w('  - The scatter in g†_eff may reflect environmental variation')
        w('    (physical) and/or residual M/L systematics.')
    print(f"Saved: {out_path}")

# ── Save full CSV ─────────────────────────────────────────────────────────────
def save_results(fits, out_path, clean_path=None):
    df_all = pd.DataFrame([f.__dict__ for f in fits])
    df_all.to_csv(out_path, index=False)
    print(f"Saved: {out_path}  (N={len(fits)} rows)")
    if clean_path:
        df_clean = df_all[~df_all['flag_low_quality'] & (df_all['chi2_red_fixed'] < 5.0)]
        df_clean.to_csv(clean_path, index=False)
        print(f"Saved: {clean_path}  (N={len(df_clean)} clean rows)")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description='ECT SPARC rotation curve fitting — phi-branch v3d')
    ap.add_argument('input',
                    help='SPARC mass-model table (MassModels_Lelli2016c.mrt)')
    ap.add_argument('--h0',         type=float, default=70.0)
    ap.add_argument('--min-pts',    type=int,   default=6)
    ap.add_argument('--error-floor',type=float, default=2.0,
                    help='Error floor in km/s (default 2.0; use 0 to disable)')
    ap.add_argument('--selected',   nargs='+',  default=None,
                    help='Galaxies for SET 2/3 plots only (diagnostics always use ALL)')
    ap.add_argument('--n-best',     type=int,   default=20)
    ap.add_argument('--n-sens',     type=int,   default=6,
                    help='Galaxies for sensitivity-band plot (was --n-efe)')
    ap.add_argument('--ncols',      type=int,   default=4)
    ap.add_argument('--output-dir', default=None)
    ap.add_argument('--efe-mode',   choices=['none','proxy'], default='none',
                    help='EFE proxy mode (requires --gext-file)')
    ap.add_argument('--gext-file',  default=None,
                    help='CSV with columns: galaxy, gext_m_s2')
    ap.add_argument('--alpha-ext',  type=float, default=1.0,
                    help='EFE coupling constant α (default 1.0)')
    args = ap.parse_args()

    if args.output_dir:
        out_dir = args.output_dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(os.path.dirname(script_dir), 'figures', 'sparc_v3')
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output directory: {out_dir}")

    # ── Step 1: Load data ─────────────────────────────────────────────────
    df_all = load_sparc(args.input, error_floor=args.error_floor)

    # ── Step 2: Load optional EFE proxy table ─────────────────────────────
    gext_table = None
    if args.efe_mode == 'proxy':
        if args.gext_file is None:
            print("WARNING: --efe-mode proxy requires --gext-file. Skipping EFE proxy.")
        else:
            gext_table = load_gext(args.gext_file)
            print(f"Loaded g_ext table: {len(gext_table)} galaxies")

    # ── Step 3: Fit ALL galaxies ONCE ─────────────────────────────────────
    # DESIGN RULE: fit_sample() called exactly once on full dataset.
    print(f"\nFitting ALL {df_all['Galaxy'].nunique()} galaxies "
          f"(error_floor={args.error_floor} km/s)...")
    fits_full = list(fit_sample(df_all, h0=args.h0, min_pts=args.min_pts,
                                gext_table=gext_table, alpha_ext=args.alpha_ext))
    N_full = len(fits_full)
    print(f"\nFitted: {N_full} galaxies total\n")
    assert N_full > 10, f"ERROR: only {N_full} fits — something is wrong!"

    # ── Step 4: Save CSV + diagnostics BEFORE any rotation-curve plots ────
    print("Saving CSV and diagnostics...")
    csv_path   = os.path.join(out_dir, 'ect_sparc_results.csv')
    clean_path = os.path.join(out_dir, 'ect_sparc_results_clean.csv')
    save_results(fits_full, csv_path, clean_path=clean_path)
    save_five_comparison(fits_full, os.path.join(out_dir, 'five_galaxies_comparison.csv'),
                         h0=args.h0)
    plot_diagnostics(fits_full, out_dir, h0=args.h0)

    # ── Step 5: Determine plot subset ─────────────────────────────────────
    if args.selected:
        df_plot  = df_all[df_all['Galaxy'].isin(args.selected)]
        fit_map  = {normalize_name(f.galaxy): f for f in fits_full}
        fits_plot = [fit_map[normalize_name(g)]
                     for g in args.selected if normalize_name(g) in fit_map]
        print(f"Plot subset: {len(fits_plot)} selected galaxies")
    else:
        df_plot   = df_all
        fits_plot = fits_full

    # ── Step 6: Rotation-curve plots ──────────────────────────────────────
    mw_path = os.path.join(out_dir, 'set1_milky_way.pdf')
    mw_result = plot_milky_way(mw_path, h0=args.h0)

    to_plot = fits_plot[:args.n_best]
    if to_plot:
        plot_sparc_gallery(df_plot, to_plot,
                           os.path.join(out_dir, 'set2_sparc_sample.pdf'),
                           ncols=args.ncols, h0=args.h0)

    sens_gals = fits_plot[:args.n_sens]
    if sens_gals:
        plot_sensitivity_set(df_plot, sens_gals,
                             os.path.join(out_dir, 'set3_gdag_sensitivity.pdf'),
                             h0=args.h0, ncols=3)

    # ── Step 7: Summary report ─────────────────────────────────────────────
    write_summary(fits_full, os.path.join(out_dir, 'summary_report.txt'),
                  h0=args.h0, mw_result=mw_result,
                  error_floor=args.error_floor)

    # ── Console summary ────────────────────────────────────────────────────
    ch0_2pi     = cH0_si(args.h0)/(2*math.pi)
    ratios      = [f.ratio_cH0_2pi        for f in fits_full]
    ratios_free = [f.gdag_free_si/ch0_2pi for f in fits_full]
    chi2s       = [f.chi2_red_fixed        for f in fits_full]
    chi2_m      = [f.chi2_red_mond         for f in fits_full]
    chi2_l      = [f.chi2_red_lcdm         for f in fits_full]
    aic_f_arr   = [f.aic_fixed             for f in fits_full]
    aic_m_arr   = [f.aic_mond              for f in fits_full]
    aic_l_arr   = [f.aic_lcdm             for f in fits_full]
    ml_free     = [f.ml_disk_best          for f in fits_full]
    clean_mask  = [not f.flag_low_quality and f.chi2_red_fixed < 5.0 for f in fits_full]

    print(f"\n{'─'*65}")
    print(f"cH0/(2π)              = {ch0_2pi:.3e} m/s²  (ECT baseline)")
    print(f"a0 (MOND)             = {A0_SI:.3e} m/s²")
    print(f"\n── FIXED M/L (Υ=0.5, k=1) ──")
    print(f"Median g†/(cH0/2π)    = {np.median(ratios):.3f}")
    print(f"Std    g†/(cH0/2π)    = {np.std(ratios):.3f}")
    print(f"In band [0.5,2.0]     = {np.mean([(0.5<=r<=2) for r in ratios])*100:.0f}%")
    print(f"Median ECT χ²_r       = {np.median(chi2s):.2f}")
    print(f"Median ECT AIC        = {np.median(aic_f_arr):.1f}")
    print(f"Clean sample N        = {sum(clean_mask)}/{N_full}")
    print(f"Clean median g†/(cH₀/2π) = "
          f"{np.median([r for r,c in zip(ratios,clean_mask) if c]):.3f}")
    print(f"\n── FREE M/L (k=2) ──")
    print(f"Median g†/(cH0/2π)    = {np.median(ratios_free):.3f}")
    print(f"Median Υ_disk         = {np.median(ml_free):.3f}")
    print(f"\n── COMPARISON (χ²_r, note different k) ──")
    print(f"Median MOND χ²_r      = {np.median(chi2_m):.2f}")
    print(f"Median ΛCDM χ²_r      = {np.median(chi2_l):.2f}")
    ect_beats_chi2 = sum(1 for e,m in zip(chi2s,chi2_m) if e<m)
    print(f"ECT > MOND (chi2_r)   = {ect_beats_chi2}/{N_full} = {ect_beats_chi2/N_full*100:.0f}%")
    print(f"\n── COMPARISON (AIC, accounts for k) ──")
    ect_beats_mond_a = sum(1 for e,m in zip(aic_f_arr,aic_m_arr) if e<m)
    ect_beats_lcdm_a = sum(1 for e,m in zip(aic_f_arr,aic_l_arr) if e<m)
    print(f"Median MOND AIC       = {np.median(aic_m_arr):.1f}")
    print(f"Median ΛCDM AIC       = {np.median(aic_l_arr):.1f}")
    print(f"ECT > MOND (AIC)      = {ect_beats_mond_a}/{N_full} = {ect_beats_mond_a/N_full*100:.0f}%")
    print(f"ECT > ΛCDM (AIC)      = {ect_beats_lcdm_a}/{N_full} = {ect_beats_lcdm_a/N_full*100:.0f}%")
    print(f"\n[!] g† band = SENSITIVITY band, not computed EFE.")
    print(f"[!] Scatter interpretation premature: M/L + environment not resolved.")

if __name__ == '__main__':
    main()
