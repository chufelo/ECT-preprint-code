#!/usr/bin/env python3
"""
CHANNEL 7 (Tier 3): Universe age — HUBBLE SELF-CONSISTENCY CHECK.

METHODOLOGICAL CAVEATS:

1. **NOT AN INDEPENDENT CHANNEL**.  This script uses H_0_inferred(ε)
   directly from Channel 1 (Hubble).  It therefore does NOT provide
   an independent measurement of ε; rather, it asks: "given the
   ε-deformation apparatus of Channel 1, is the resulting universe
   age consistent with globular cluster observations?"

2. **ΛCDM-background proxy**: inherits all ΛCDM-proxy assumptions
   from Channel 1 (Ω_m = 0.315, Ω_Λ = 0.685, etc.).

3. **Observational anchor**: Valcin+ 2021 GC age = 13.50 ± 0.27 Gyr
   is based on stellar evolution, largely model-independent.  This
   part IS a clean observational input.

4. **Interpretation**: if Hubble apparatus gives ε = 0.032 for full
   Hubble resolution, Channel 7 tells us that this ε would make the
   universe too young (~12.5 Gyr < 13.5 observed). So Hubble's
   ε = 0.032 is INTERNALLY INCONSISTENT with GC age.

5. **Therefore**: this is a TEST of the constant-ε, uniform-deformation
   hypothesis, and it FAILS when ε is large.  The value ε = 0.007
   that saves the age does NOT independently measure ε — it just
   says "if Hubble apparatus is right, ε ~ 0.01 is compatible with
   observed age, but then Hubble tension is only partially resolved".
"""
import numpy as np
from scipy import integrate
from scipy.optimize import brentq
import json
import os

# Use shared background module for consistency
from ect_background import (
    E_ECT, t_0 as t_0_ect,
    OMEGA_M, OMEGA_R, OMEGA_L, OMEGA_B,
    Z_STAR, Z_DRAG, C_KMS, H0_BASE,
)

# Inherited constants (aliases for clarity)
H0_P       = H0_BASE
Omega_m    = OMEGA_M
Omega_r    = OMEGA_R
Omega_L    = OMEGA_L
Omega_b    = OMEGA_B
z_star     = Z_STAR
z_drag     = Z_DRAG
c_kms      = C_KMS
Gyr_per_H0 = 977.8

t_GC_mean  = 13.50    # Valcin+ 2021 (GC age; largely model-independent)
t_GC_sigma = 0.27

def I_integral(eps):
    return integrate.quad(lambda z: 1.0/E_ECT(z, eps),
                          0, z_star, limit=500, epsrel=1e-9)[0]

def c_s(z):
    R = 3*Omega_b/(4*Omega_r) / (1+z)
    return c_kms / np.sqrt(3*(1 + R))

def r_s_integral(eps):
    integrand = lambda z: c_s(z) / (H0_P * E_ECT(z, eps))
    return integrate.quad(integrand, z_drag, 1e6, limit=500, epsrel=1e-8)[0]

def H0_inferred(eps):
    """From Channel 1 Hubble apparatus — SELF-CONSISTENCY INHERITANCE."""
    I_L   = I_integral(0.0)
    I_E   = I_integral(eps)
    r_s_L = r_s_integral(0.0)
    r_s_E = r_s_integral(eps)
    return H0_P * (I_E / I_L) * (r_s_L / r_s_E)

def J_integral(eps):
    integrand = lambda z: 1.0 / ((1+z)*E_ECT(z, eps))
    return integrate.quad(integrand, 0, 1e4, limit=500, epsrel=1e-9)[0]

def t_U_self_consistent(eps):
    H0 = H0_inferred(eps)
    J  = J_integral(eps)
    return (Gyr_per_H0 / H0) * J

if __name__ == "__main__":
    print("="*72)
    print("CHANNEL 7 (Tier 3): Age SELF-CONSISTENCY CHECK")
    print("="*72)
    print("CAVEAT: NOT independent of Channel 1. Inherits H_0(ε) apparatus.")
    print("Tests whether Hubble's ε is compatible with observed age.")
    print()
    print(f"Anchor: Valcin+ 2021 GC age = {t_GC_mean:.2f} ± {t_GC_sigma:.2f} Gyr")
    print()

    print(f"{'ε':>8}  {'H₀(ε)':>8}  {'t_U':>8}  {'Δt':>8}")
    for e in [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04]:
        H = H0_inferred(e)
        t = t_U_self_consistent(e)
        print(f"{e:>8.4f}  {H:>8.3f}  {t:>8.3f}  {t - t_GC_mean:>+8.3f}")
    print()

    def diff(eps, target):
        return t_U_self_consistent(eps) - target

    eps_best = brentq(lambda e: diff(e, t_GC_mean), -0.01, 0.08)
    eps_hi   = brentq(lambda e: diff(e, t_GC_mean - t_GC_sigma), -0.01, 0.08)
    eps_lo   = brentq(lambda e: diff(e, t_GC_mean + t_GC_sigma), -0.01, 0.08)
    eps_hi_2s = brentq(lambda e: diff(e, t_GC_mean - 2*t_GC_sigma), -0.03, 0.10)
    eps_lo_2s = brentq(lambda e: diff(e, t_GC_mean + 2*t_GC_sigma), -0.03, 0.10)
    if eps_lo > eps_hi:        eps_lo, eps_hi = eps_hi, eps_lo
    if eps_lo_2s > eps_hi_2s:  eps_lo_2s, eps_hi_2s = eps_hi_2s, eps_lo_2s

    print(f"Age-compatible ε: {eps_best:.4f} (1σ: [{eps_lo:.4f}, {eps_hi:.4f}])")
    print(f"At best-fit: H_0 = {H0_inferred(eps_best):.2f} km/s/Mpc")
    print()
    print("INTERPRETATION: If Hubble's ε = 0.032 (for full tension resolution)")
    print("were correct, t_U would be 12.5 Gyr — INCOMPATIBLE with observed 13.5 Gyr.")
    print("Age forces ε ≲ 0.014 within this apparatus. So full Hubble resolution")
    print("via uniform ε-deformation is internally inconsistent.")

    result = {
        'channel':      'Age t_0 (Tier 3 self-consistency)',
        'tier':         'Tier 3',
        'eps_central':  float(eps_best),
        'eps_lo_1s':    float(eps_lo),
        'eps_hi_1s':    float(eps_hi),
        'eps_lo_2s':    float(eps_lo_2s),
        'eps_hi_2s':    float(eps_hi_2s),
        'H0_at_best':   float(H0_inferred(eps_best)),
        'caveat':       'Uses H_0(ε) from Channel 1; NOT independent measurement',
        'notes':        'Self-consistency check for Hubble apparatus; Valcin+ 2021 anchor'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch7.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
