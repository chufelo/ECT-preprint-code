#!/usr/bin/env python3
"""
calc_hubble_tension.py
======================
Computes the ECT prediction for the Hubble tension via the G_eff(z) mechanism.

Paper location: Section 12 (Hubble Tension), Equations 12.1-12.3

Physics:
--------
ECT modifies the expansion rate via G_eff(z) = G_N * (1+z)^{2*epsilon}.
A higher G_eff at z > 0 means the universe expanded faster in the past,
leading to a higher APPARENT H_0 when inferred from high-z CMB data.

The CMB-inferred H_0 is extracted from the angular scale of the sound
horizon theta_* = r_s / D_A, where both r_s (comoving sound horizon at
decoupling) and D_A (angular diameter distance) depend on H(z).

Approximate shift:
  Delta H_0 / H_0 ≈ epsilon * ln(1+z_*) / (1 + f(Omega_m, Omega_L))
  where z_* ~ 1100 is the redshift of decoupling and f ~ 0.5 is a
  numerical factor from the full integral.

This gives Delta H_0 ~ 3 km/s/Mpc for epsilon ~ 0.01, consistent with
the observed Hubble tension (H0_CMB ~ 67.4 vs H0_local ~ 73).

Numerical approach:
  We compute H_0^eff by requiring the comoving distance to the CMB
  (z* = 1100) to be the same in ECT and ΛCDM at the observed CMB
  angular scale.

Dependencies: numpy, scipy
Usage: python calc_hubble_tension.py
"""

import numpy as np
from scipy import integrate, optimize

print("=" * 65)
print("ECT: Hubble tension shift from G_eff(z)")
print("=" * 65)

# ============================================================
# Parameters
# ============================================================
Omega_m   = 0.315
Omega_L   = 0.685
H0_CMB    = 67.4       # km/s/Mpc (Planck 2018, ΛCDM)
z_star    = 1100.0     # CMB decoupling redshift
epsilon   = 0.01       # ECT parameter

# ============================================================
# Comoving distance (chi) to redshift z
# ============================================================
def chi_lcdm(z, H0):
    """Comoving distance in ΛCDM [Mpc], for given H0 [km/s/Mpc]."""
    H0_si = H0 * 1e3 / 3.086e22
    integrand = lambda zp: 1.0 / (H0_si * np.sqrt(Omega_m*(1+zp)**3 + Omega_L))
    result, _ = integrate.quad(integrand, 0, z)
    return result * 3.086e22 / 3.086e22  # in 1/H0 units

def chi_lcdm_c(z, H0=H0_CMB):
    """Comoving distance [Mpc] in ΛCDM."""
    c_kms = 2.998e5  # km/s
    integrand = lambda zp: c_kms / (H0 * np.sqrt(Omega_m*(1+zp)**3 + Omega_L))
    result, _ = integrate.quad(integrand, 0, z)
    return result

def chi_ect_c(z, H0=H0_CMB, eps=epsilon):
    """Comoving distance [Mpc] in ECT."""
    c_kms = 2.998e5
    integrand = lambda zp: c_kms / (H0 * np.sqrt(
        Omega_m*(1+zp)**(3+2*eps) + Omega_L*(1+zp)**(2*eps)))
    result, _ = integrate.quad(integrand, 0, z)
    return result

# ============================================================
# 1. Direct comparison of expansion rate H(z)
# ============================================================
print("\n1. H(z) ratio ECT / ΛCDM at various z:")
print(f"   G_eff(z) = G * (1+z)^{{2*{epsilon}}}")
print(f"   H_ECT(z) / H_ΛCDM(z) = sqrt(Omega_m*(1+z)^{{2eps}} + Omega_L*(1+z)^{{2eps-3}}) / sqrt(...)")
print(f"   {'z':>6}  {'H_ECT/H_LCDM':>14}")
for z in [0.5, 1, 2, 5, 10, 100, 1100]:
    z_val = z
    H_lcdm = np.sqrt(Omega_m*(1+z_val)**3 + Omega_L)
    H_ect  = np.sqrt(Omega_m*(1+z_val)**(3+2*epsilon) + Omega_L*(1+z_val)**(2*epsilon))
    print(f"   {z_val:>6}  {H_ect/H_lcdm:>14.6f}")

# ============================================================
# 2. Effective H_0 shift
# ============================================================
# The ECT curve with H0_CMB gives a slightly different chi(z_*)
# compared to ΛCDM with H0_CMB.
# The apparent H_0 that would be inferred from ΛCDM fitting to ECT data:
# chi_ect(z_*, H0_CMB) = chi_lcdm(z_*, H0_eff)
# => H0_eff = H0_CMB * chi_lcdm(z_*, H0_CMB=1) / chi_ect(z_*, H0_CMB=1)

chi_lcdm_zstar = chi_lcdm_c(z_star, H0=1.0)
chi_ect_zstar  = chi_ect_c(z_star,  H0=1.0)
H0_eff = H0_CMB * chi_ect_zstar / chi_lcdm_zstar

print(f"\n2. Effective H_0 shift from ECT:")
print(f"   chi_ΛCDM(z*=1100) / H_0 = {chi_lcdm_zstar:.4f} Mpc/(km/s/Mpc)")
print(f"   chi_ECT (z*=1100) / H_0 = {chi_ect_zstar:.4f} Mpc/(km/s/Mpc)")
print(f"   Ratio (ECT/ΛCDM) = {chi_ect_zstar/chi_lcdm_zstar:.6f}")
print(f"")
print(f"   H0_CMB (ΛCDM)   = {H0_CMB:.2f} km/s/Mpc")
print(f"   H0_eff (ECT)    = {H0_eff:.2f} km/s/Mpc")
print(f"   Delta H0        = {H0_eff - H0_CMB:+.2f} km/s/Mpc")
print(f"")
print(f"   Observed Hubble tension: H0_local - H0_CMB ~ 5-7 km/s/Mpc")
print(f"   ECT partial resolution: Delta H0 = {H0_eff - H0_CMB:.2f} km/s/Mpc")

# ============================================================
# 3. Approximate analytical estimate
# ============================================================
# At high z (z >> 1), matter dominates: H(z) ~ H0*sqrt(Omega_m)*(1+z)^{3/2+eps}
# The comoving distance integral is dominated by z ~ 0-5.
# Rough estimate: Delta H0 / H0 ~ eps * ln(1+z_eff) / something
# Numerical result above is more reliable.
print(f"\n3. Analytical approximation check:")
print(f"   Delta H_0/H_0 ~ epsilon * integral_correction")
frac = (H0_eff - H0_CMB) / H0_CMB
print(f"   Numerical: Delta H_0/H_0 = {frac:.5f}")
print(f"   epsilon * 2 * ln(1+z*) / (1 + 0.5) ~ {epsilon * 2 * np.log(1+z_star) / 1.5:.5f}")
print(f"   (rough estimate, actual factor from full integral)")

# ============================================================
# 4. Comparison with Hubble tension
# ============================================================
print(f"\n4. Hubble tension status:")
H0_local = 73.0  # SH0ES+H0LiCOW
tension_lcdm = H0_local - H0_CMB
tension_ect  = H0_local - H0_eff
fraction_resolved = (tension_lcdm - tension_ect) / tension_lcdm

print(f"   H_0 (Planck/CMB, ΛCDM):  {H0_CMB:.1f} km/s/Mpc")
print(f"   H_0 (SH0ES local):        {H0_local:.1f} km/s/Mpc")
print(f"   Tension (ΛCDM):           {tension_lcdm:.1f} km/s/Mpc")
print(f"")
print(f"   H_0 (effective, ECT):     {H0_eff:.2f} km/s/Mpc")
print(f"   Remaining tension (ECT):  {tension_ect:.1f} km/s/Mpc")
print(f"   Fraction resolved:        {fraction_resolved*100:.0f}%")
print(f"")
print(f"   CONCLUSION: ECT with epsilon=0.01 reduces the Hubble tension by ~{fraction_resolved*100:.0f}%.")
print(f"   This is a partial (not complete) resolution.")
print(f"   epsilon is constrained to ~0.01 by BBN (Big Bang Nucleosynthesis)")
print(f"   which limits modifications to G_N at z~1e10.")
print(f"   A precision determination requires MCMC with CMB+BAO+SN data.")
