#!/usr/bin/env python3
"""
CHANNEL 4 (Tier 2): Cosmic chronometers — BACKGROUND H(z) FIT.

METHODOLOGICAL CAVEATS:

1. **ΛCDM-background proxy**: fits H_ECT(z) = H_0·√[Ω_m(1+z)^(3+2ε)+
   Ω_Λ(1+z)^(2ε)] with Ω_m = 0.315 fixed.  The Ω_m value is ΛCDM-FIT
   and includes ΛCDM "dark matter".  In ECT, Ω_m would be derived
   from closure.  Letting Ω_m float broadens ε range considerably.

2. **Approximate compilation**: uses a subset of Moresco+ 2022
   published values; not the full compilation with complete
   systematic error budget.

3. **Broad band, weak constraint**: best-fit ε = 0.006 has 1σ range
   [-0.020, +0.087] — essentially consistent with anything in
   [-0.02, 0.09].  This is a CONSISTENCY CHECK, not a strong probe.

4. **H_0 profiled freely**: best-fit H_0 ≈ 68 km/s/Mpc at ε=0, close
   to Planck.  Does NOT give independent H_0 determination.

Data: 31 H(z) points from Moresco+ 2022 (approximate).
"""
import numpy as np
from scipy.optimize import minimize_scalar
import json
import os

# Use shared background module for consistency across channels
from ect_background import E_ECT as _E_ECT, OMEGA_M, OMEGA_L

CC_DATA = np.array([
    [0.07,     69.0,   19.6], [0.09,     69.0,   12.0],
    [0.12,     68.6,   26.2], [0.17,     83.0,    8.0],
    [0.1791,   75.0,    4.0], [0.1993,   75.0,    5.0],
    [0.20,     72.9,   29.6], [0.27,     77.0,   14.0],
    [0.28,     88.8,   36.6], [0.3519,   83.0,   14.0],
    [0.3802,   83.0,   13.5], [0.4,      95.0,   17.0],
    [0.4004,   77.0,   10.2], [0.4247,   87.1,   11.2],
    [0.4497,   92.8,   12.9], [0.47,     89.0,   50.0],
    [0.4783,   80.9,    9.0], [0.48,     97.0,   62.0],
    [0.5929,  104.0,   13.0], [0.6797,   92.0,    8.0],
    [0.7812,  105.0,   12.0], [0.8754,  125.0,   17.0],
    [0.88,     90.0,   40.0], [0.9,     117.0,   23.0],
    [1.037,   154.0,   20.0], [1.3,     168.0,   17.0],
    [1.363,   160.0,   33.6], [1.43,    177.0,   18.0],
    [1.53,    140.0,   14.0], [1.75,    202.0,   40.0],
    [1.965,   186.5,   50.4],
])

z_data = CC_DATA[:, 0]
H_data = CC_DATA[:, 1]
s_data = CC_DATA[:, 2]

Omega_m = OMEGA_M   # from ect_background (0.315, LCDM-fit — CAVEAT)
Omega_L = OMEGA_L

def H_ECT(z, H0, eps):
    """Wraps ect_background.E_ECT with arbitrary H0 for CC fits."""
    return H0 * _E_ECT(z, eps)

def chi2(H0, eps):
    model = H_ECT(z_data, H0, eps)
    return np.sum(((H_data - model)/s_data)**2)

def chi2_profile(eps):
    res = minimize_scalar(lambda H0: chi2(H0, eps),
                          bounds=(50.0, 100.0), method='bounded')
    return res.fun, res.x

if __name__ == "__main__":
    print("="*66)
    print("CHANNEL 4 (Tier 2): Cosmic chronometers (Moresco+ 2022)")
    print("="*66)
    print("CAVEAT: ΛCDM-background proxy; Ω_m = 0.315 FIXED.")
    print("Weak consistency check only.")
    print()

    eps_grid = np.linspace(-0.02, 0.15, 171)
    chi2_grid  = np.zeros_like(eps_grid)
    H0_grid    = np.zeros_like(eps_grid)
    for i, e in enumerate(eps_grid):
        chi2_grid[i], H0_grid[i] = chi2_profile(e)

    i_best      = np.argmin(chi2_grid)
    eps_best    = eps_grid[i_best]
    chi2_best   = chi2_grid[i_best]
    H0_best     = H0_grid[i_best]

    print(f"ε_best   = {eps_best:+.4f}")
    print(f"H_0_prof = {H0_best:.2f} km/s/Mpc")
    print(f"χ²/dof   = {chi2_best:.2f}/{len(z_data)-2}")

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
        'channel':     'Cosmic chronometers (Tier 2)',
        'tier':        'Tier 2',
        'eps_central': float(eps_best),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'H0_best':     float(H0_best),
        'chi2_min':    float(chi2_best),
        'dof':         int(len(z_data)-2),
        'caveat':      'ΛCDM-background proxy; Ω_m fixed; approximate compilation',
        'notes':       'Weak consistency check; not a strong probe'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch4.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
