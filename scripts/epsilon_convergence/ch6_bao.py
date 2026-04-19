#!/usr/bin/env python3
"""
CHANNEL 6 (Tier 1): BAO from DESI 2024 — SHAPE-ONLY fit.

METHODOLOGICAL CAVEATS:

1. **ΛCDM-background proxy**: Ω_m = 0.315 FIXED. If Ω_m floats
   jointly with ε, the constraint on ε broadens considerably because
   BAO cannot disentangle Ω_m from ε-deformation.

2. **Diagonal errors only**: no full DESI covariance matrix.  Real
   correlations between measurements would change χ² surface.

3. **Shape-only fit**: H_0 and r_d both profiled out.  This removes
   absolute-distance/absolute-sound-horizon information, keeping only
   SHAPE of D_M(z), D_H(z).  More conservative than fixing r_d at
   Planck value.

4. **r_d modification in ECT**: pre-recombination G_eff drift would
   change r_d.  Letting r_d float captures this partly, but a full
   treatment would tie r_d(ε) to the same ε via ECT closure.

5. **Result ε = -0.013 with 1σ [-0.033, +0.007]**: tight constraint
   pulling toward ε ≈ 0 at low z.  This genuinely tensions any
   claim of ε ≥ 0.03 from a UNIFORM-ε-across-z model.

Data: DESI 2024 DR1 (Adame+ 2024), 12 BAO measurements in z ∈ [0.3, 2.3].
"""
import numpy as np
from scipy import integrate
from scipy.optimize import minimize
import json
import os

# Use shared background module for consistency across channels
from ect_background import E_ECT, OMEGA_M, OMEGA_L

Omega_m = OMEGA_M   # from ect_background (0.315 LCDM-fit)
Omega_L = OMEGA_L
c_kms   = 299792.458

def D_H(z, H0, eps):
    return c_kms / (H0 * E_ECT(z, eps))

def D_M(z, H0, eps):
    integ, _ = integrate.quad(lambda zp: 1.0/E_ECT(zp, eps), 0, z, limit=500)
    return (c_kms/H0) * integ

def D_V(z, H0, eps):
    return (z * D_M(z, H0, eps)**2 * D_H(z, H0, eps))**(1/3)

BAO_DATA = [
    (0.295, 'DV',  7.93,  0.15),
    (0.510, 'DM', 13.62,  0.25),
    (0.510, 'DH', 20.98,  0.61),
    (0.706, 'DM', 16.85,  0.32),
    (0.706, 'DH', 20.08,  0.60),
    (0.930, 'DM', 21.71,  0.28),
    (0.930, 'DH', 17.88,  0.35),
    (1.317, 'DM', 27.79,  0.69),
    (1.317, 'DH', 13.82,  0.42),
    (1.491, 'DV', 26.07,  0.67),
    (2.330, 'DM', 39.71,  0.94),
    (2.330, 'DH',  8.52,  0.17),
]

def predict(z, obs_type, H0, eps, r_d):
    if obs_type == 'DV': return D_V(z, H0, eps) / r_d
    if obs_type == 'DM': return D_M(z, H0, eps) / r_d
    if obs_type == 'DH': return D_H(z, H0, eps) / r_d
    raise ValueError(obs_type)

def chi2(params, eps):
    H0, r_d = params
    if H0 <= 0 or r_d <= 0:
        return 1e10
    total = 0.0
    for z, typ, obs, sig in BAO_DATA:
        th = predict(z, typ, H0, eps, r_d)
        total += ((obs - th)/sig)**2
    return total

def chi2_profile(eps):
    res = minimize(lambda p: chi2(p, eps),
                   x0=[67.4, 147.05],
                   method='Nelder-Mead',
                   options={'xatol': 1e-4, 'fatol': 1e-6})
    return res.fun, res.x[0], res.x[1]

if __name__ == "__main__":
    print("="*72)
    print("CHANNEL 6 (Tier 1): BAO DESI 2024 — shape-only")
    print("="*72)
    print("CAVEAT: ΛCDM-background (Ω_m fixed); diagonal errors; shape-only.")
    print()

    eps_grid   = np.linspace(-0.05, 0.15, 201)
    chi2_grid  = np.zeros_like(eps_grid)
    H0_grid    = np.zeros_like(eps_grid)
    rd_grid    = np.zeros_like(eps_grid)
    for i, e in enumerate(eps_grid):
        c, H, r = chi2_profile(e)
        chi2_grid[i], H0_grid[i], rd_grid[i] = c, H, r

    i_best = np.argmin(chi2_grid)
    eps_best    = eps_grid[i_best]
    chi2_best   = chi2_grid[i_best]
    H0_best     = H0_grid[i_best]
    rd_best     = rd_grid[i_best]
    dof         = len(BAO_DATA) - 3

    print(f"ε_best     = {eps_best:+.4f}")
    print(f"H_0 (prof) = {H0_best:.2f}")
    print(f"r_d (prof) = {rd_best:.2f} Mpc")
    print(f"χ²/dof     = {chi2_best:.2f}/{dof}")

    dchi2 = chi2_grid - chi2_best
    def find_range(dchi2, eps_grid, threshold):
        below = dchi2 <= threshold
        if not np.any(below):
            return np.nan, np.nan
        return eps_grid[below].min(), eps_grid[below].max()
    eps_lo_1s, eps_hi_1s = find_range(dchi2, eps_grid, 1.0)
    eps_lo_2s, eps_hi_2s = find_range(dchi2, eps_grid, 4.0)

    print(f"1σ: [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]")
    print(f"2σ: [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]")

    result = {
        'channel':     'BAO (Tier 1)',
        'tier':        'Tier 1',
        'eps_central': float(eps_best),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'H0_best':     float(H0_best),
        'rd_best':     float(rd_best),
        'chi2_min':    float(chi2_best),
        'dof':         int(dof),
        'caveat':      'ΛCDM-background proxy; Ω_m fixed; diagonal errors; shape-only',
        'notes':       'DESI 2024 DR1; H_0 and r_d both profiled'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch6.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
