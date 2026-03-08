#!/usr/bin/env python3
"""
calc_universe_age.py
====================
Numerically computes the age of the universe in ECT and ΛCDM,
and the age at each redshift z.

Paper location: Section 12 (Hubble Tension), discussion

Physics:
--------
ECT modifies the Friedmann equation via G_eff(z) = G_N * (1+z)^{2*epsilon}:
  H(z)^2 = H_0^2 [ Omega_m*(1+z)^{3+2*eps} + Omega_L*(1+z)^{2*eps} ]

vs standard ΛCDM:
  H(z)^2 = H_0^2 [ Omega_m*(1+z)^3 + Omega_L ]

Age integral:
  t_0 = integral_0^infty  dz / [(1+z) * H(z)]

Parameter:
  epsilon ~ 0.01 (fitted from Hubble tension, not from rotation curves)
  The same epsilon that shifts H_0 by ~3 km/s/Mpc.

Result:
  ΛCDM: t_0 = 13.80 Gyr
  ECT:  t_0 = 13.69 Gyr  (Delta = -0.1 Gyr, i.e. ~1% younger)

Significance:
  The difference Delta t = 0.1 Gyr is within the uncertainty of globular
  cluster ages (12.5 ± 0.5 Gyr). ECT gives a slightly younger universe,
  consistent with a higher effective H_0.

Note: This is NOT a prediction of the universe age from first principles.
ECT modifies the expansion history slightly; the precise age depends on
the cosmological parameters assumed.

Dependencies: numpy, scipy
Usage: python calc_universe_age.py
"""

import numpy as np
from scipy import integrate

print("=" * 65)
print("ECT vs ΛCDM: Universe age calculation")
print("=" * 65)

# ============================================================
# Cosmological parameters (Planck 2018)
# ============================================================
H0_kms_Mpc = 67.4        # km/s/Mpc
H0_si = H0_kms_Mpc * 1e3 / 3.086e22   # s^{-1}
Omega_m   = 0.315
Omega_L   = 0.685
epsilon   = 0.01          # ECT G_eff evolution parameter

yr_s = 3.156e7            # seconds per year

# ============================================================
# Integrand functions
# ============================================================
def integrand_lcdm(z):
    """Standard ΛCDM integrand: 1 / [(1+z) * H(z)]"""
    H = H0_si * np.sqrt(Omega_m*(1+z)**3 + Omega_L)
    return 1.0 / ((1+z) * H)

def integrand_ect(z, eps=epsilon):
    """ECT integrand with G_eff(z) = G*(1+z)^{2*eps}"""
    H = H0_si * np.sqrt(Omega_m*(1+z)**(3+2*eps) + Omega_L*(1+z)**(2*eps))
    return 1.0 / ((1+z) * H)

# ============================================================
# Universe age today (z=0)
# ============================================================
t0_lcdm, _ = integrate.quad(integrand_lcdm, 0, 1e4)
t0_ect,  _ = integrate.quad(integrand_ect,  0, 1e4)

t0_lcdm_Gyr = t0_lcdm / yr_s / 1e9
t0_ect_Gyr  = t0_ect  / yr_s / 1e9

print(f"\n1. Universe age today:")
print(f"   ΛCDM:  t_0 = {t0_lcdm_Gyr:.3f} Gyr")
print(f"   ECT:   t_0 = {t0_ect_Gyr:.3f} Gyr")
print(f"   Delta: {(t0_ect_Gyr - t0_lcdm_Gyr):.3f} Gyr  ({(t0_ect_Gyr/t0_lcdm_Gyr - 1)*100:.2f}%)")
print(f"   Factor F = t_ECT / t_ΛCDM = {t0_ect_Gyr / t0_lcdm_Gyr:.4f}")

# ============================================================
# Age at specific redshifts (cosmic time since Big Bang)
# ============================================================
print(f"\n2. Cosmic time t(z) [universe age at redshift z]:")
print(f"   {'z':>5}  {'t_ΛCDM(Myr)':>13}  {'t_ECT(Myr)':>12}  {'Delta(Myr)':>12}")
print(f"   {'-'*5}  {'-'*13}  {'-'*12}  {'-'*12}")

for z in [0, 1, 2, 5, 7, 10, 12, 15, 20, 30, 50, 100, 1000]:
    tL, _ = integrate.quad(integrand_lcdm, z, 1e4)
    tE, _ = integrate.quad(integrand_ect,  z, 1e4)
    tL_Myr = tL / yr_s / 1e6
    tE_Myr = tE / yr_s / 1e6
    print(f"   {z:>5}  {tL_Myr:>13.1f}  {tE_Myr:>12.1f}  {(tE_Myr-tL_Myr):>+12.1f}")

# ============================================================
# Globular cluster age constraint
# ============================================================
print(f"\n3. Consistency with globular cluster ages:")
gc_age_low = 12.5 - 0.5   # Gyr, lower bound (VandenBerg+2013)
gc_age_high = 12.5 + 0.5  # Gyr, upper bound
print(f"   Globular cluster age lower bound: {gc_age_low:.1f} - {gc_age_high:.1f} Gyr")
print(f"   ΛCDM: t_0 = {t0_lcdm_Gyr:.2f} Gyr  {'OK' if t0_lcdm_Gyr > gc_age_low else 'TENSION'}")
print(f"   ECT:  t_0 = {t0_ect_Gyr:.2f} Gyr  {'OK' if t0_ect_Gyr > gc_age_low else 'TENSION'}")

# ============================================================
# Conclusion
# ============================================================
print(f"\n4. Physical interpretation:")
print(f"   ECT with epsilon=0.01 gives a universe ~{abs(t0_ect_Gyr-t0_lcdm_Gyr)*1000:.0f} Myr younger.")
print(f"   This is because G_eff(z) > G_N at z>0 also accelerates expansion,")
print(f"   leading to a slightly faster expansion history and shorter age.")
print(f"   The effect (0.1 Gyr) is well within current observational uncertainties.")
print(f"   A precision age measurement would require MCMC with CMB+BAO+SN data.")
