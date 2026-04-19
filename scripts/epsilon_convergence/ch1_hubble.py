#!/usr/bin/env python3
"""
CHANNEL 1 (Tier A): Hubble + r_s extraction.

Updated 2026-04-19: uses shared ect_background module (H, t_0, t(z)) so
that the ECT-native age-of-universe dependence on epsilon is
propagated consistently across all channels.  At leading order in the
Hubble + r_s channel, t_0 does not enter -- the extraction is carried
by the distance integral I(eps) and sound horizon r_s(eps) at fixed
theta_s.  But the shared module is still used so that the background
is uniform across channels.

Numerics unchanged for this channel: result_ch1.json same as before.

SEE ect_background.py for E_ECT, H_ECT, t_0, t_cosmic.
"""
import numpy as np
from scipy import integrate
from scipy.optimize import brentq
import json, os

from ect_background import (
    E_ECT, H_ECT, t_0, t_cosmic,
    H0_BASE as H0_P, OMEGA_M, OMEGA_R, OMEGA_L, OMEGA_B,
    Z_STAR, Z_DRAG, C_KMS,
)

H0_SH0ES   = 73.04
sigma_P    = 0.5
sigma_SH   = 1.04

def I_integral(eps, z_up=Z_STAR):
    return integrate.quad(lambda z: 1.0/E_ECT(z, eps),
                          0, z_up, limit=500, epsrel=1e-9)[0]

def R_bg(z):
    return 3*OMEGA_B / (4*OMEGA_R) / (1+z)

def c_s(z):
    return C_KMS / np.sqrt(3 * (1 + R_bg(z)))

def r_s_integral(eps, z_low=Z_DRAG, z_high=1e6):
    integrand = lambda z: c_s(z) / (H0_P * E_ECT(z, eps))
    return integrate.quad(integrand, z_low, z_high, limit=500, epsrel=1e-8)[0]

def H0_inferred(eps):
    I_L   = I_integral(0.0)
    I_E   = I_integral(eps)
    r_s_L = r_s_integral(0.0)
    r_s_E = r_s_integral(eps)
    return H0_P * (I_E / I_L) * (r_s_L / r_s_E)

def DeltaH0(eps):
    return H0_inferred(eps) - H0_P

if __name__ == "__main__":
    print("="*72)
    print("CHANNEL 1 (Tier A): Hubble + r_s (ECT-native background module)")
    print("="*72)
    print(f"Local H0_SH0ES = {H0_SH0ES} +/- {sigma_SH}")
    print(f"Baseline H0    = {H0_P} +/- {sigma_P}")
    print(f"Target shift   = {H0_SH0ES-H0_P:.2f} +/- "
          f"{np.sqrt(sigma_P**2+sigma_SH**2):.2f}")
    print()
    print(f"{'eps':>8}  {'H0_inf':>8}  {'dH0':>7}  {'r_s ratio':>10}  "
          f"{'t_0 Gyr':>8}")
    for e in [0.0, 0.01, 0.02, 0.03, 0.04, 0.05]:
        H = H0_inferred(e); t = t_0(e)
        r_e = r_s_integral(e); r_0 = r_s_integral(0.0)
        print(f"{e:>8.4f}  {H:>8.3f}  {H-H0_P:>+7.3f}  "
              f"{r_e/r_0:>10.4f}  {t:>8.3f}")
    print()

    Delta_obs   = H0_SH0ES - H0_P
    Delta_sigma = np.sqrt(sigma_P**2 + sigma_SH**2)

    eps_best = brentq(lambda e: DeltaH0(e)-Delta_obs, 0.001, 0.10)
    eps_lo   = brentq(lambda e: DeltaH0(e)-(Delta_obs-Delta_sigma), 0.0001, 0.10)
    eps_hi   = brentq(lambda e: DeltaH0(e)-(Delta_obs+Delta_sigma), 0.0001, 0.10)
    eps_lo2  = brentq(lambda e: DeltaH0(e)-(Delta_obs-2*Delta_sigma), 0.0001, 0.10)
    eps_hi2  = brentq(lambda e: DeltaH0(e)-(Delta_obs+2*Delta_sigma), 0.0001, 0.10)

    print(f"eps_* = {eps_best:.4f}   t_0(eps_*) = {t_0(eps_best):.3f} Gyr")
    print(f"1 sigma: [{eps_lo:.4f}, {eps_hi:.4f}]")
    print(f"2 sigma: [{eps_lo2:.4f}, {eps_hi2:.4f}]")

    result = {
        'channel': 'Hubble + r_s (Tier A)', 'tier': 'Tier A',
        'eps_central': float(eps_best),
        'eps_lo_1s': float(eps_lo), 'eps_hi_1s': float(eps_hi),
        'eps_lo_2s': float(eps_lo2), 'eps_hi_2s': float(eps_hi2),
        't0_at_eps_central_Gyr': float(t_0(eps_best)),
        't0_at_eps_0_Gyr': float(t_0(0.0)),
        'caveat': 'ECT-native background via ect_background.py; '
                  't_0 enters other channels more strongly.',
        'notes': 'Hubble + r_s channel weakly sensitive to t_0; '
                 'extraction through acoustic scale ratio.',
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch1.json')
    with open(out, 'w') as f: json.dump(result, f, indent=2)
    print(f"\nSaved {out}")
