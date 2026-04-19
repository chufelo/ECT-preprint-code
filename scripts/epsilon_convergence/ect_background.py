#!/usr/bin/env python3
"""
ECT-native background module for the epsilon_convergence pipeline.

Provides H(z, eps), t(z, eps), and t_0(eps) computed self-consistently
from the ECT-native late-time ordered-branch Friedmann equation under
the uniform-eps ansatz.  Used by all per-channel extraction scripts
(ch1_hubble.py, ch2_jwst.py, ...) so that every channel sees the same
background -- including the modified cosmic age.

Key equations (see app:late_cosmo_background and
app:late_cosmo_algorithm in the preprint):

  E^2(z, eps) = Omega_r * (1+z)^4
             + Omega_m * (1+z)^{3+2*eps}
             + Omega_Lambda * (1+z)^{2*eps}

  H(z, eps) = H0 * E(z, eps)
  t(z, eps) = integral from z to infinity of dz' / [(1+z') * H(z', eps)]
  t_0(eps) = t(0, eps)

At eps=0 this reproduces the LCDM background with H0 = H0_base.
At eps > 0 the background has G_eff(z)/G_N = (1+z)^{2*eps}, which
modifies H(z), and therefore t_0 and t(z) as well.

ALL CHANNELS should import from this module instead of hardcoding
values.  This guarantees consistent eps-propagation into every
extraction.

Units: H0 in km/s/Mpc, t in Gyr (internally; conversion constant
MPC_IN_KM / SEC_IN_YEAR).
"""

import numpy as np
from scipy import integrate

# ---- Baseline cosmological parameters (LCDM fit, used as proxy) ----
H0_BASE    = 67.4            # km/s/Mpc (Planck 2018 LCDM)
OMEGA_M    = 0.315
OMEGA_R    = 9.2e-5
OMEGA_B    = 0.0493
OMEGA_L    = 1.0 - OMEGA_M - OMEGA_R
Z_STAR     = 1089.80
Z_DRAG     = 1059.94
C_KMS      = 299792.458

# Unit conversion: 1 / (km/s/Mpc) -> Gyr
# 1 Mpc = 3.0857e19 km;  1 Gyr = 3.1557e16 s
HUBBLE_TIME_GYR = 3.0857e19 / (3.1557e16)   # (km/s/Mpc)^{-1} -> Gyr/(km/s/Mpc)
# so  t [Gyr] = HUBBLE_TIME_GYR / H [km/s/Mpc]

def E_ECT(z, eps):
    """Dimensionless Hubble rate E(z,eps) = H(z,eps)/H0_base."""
    return np.sqrt(
        OMEGA_R * (1.0 + z)**4
        + OMEGA_M * (1.0 + z)**(3.0 + 2.0*eps)
        + OMEGA_L * (1.0 + z)**(2.0*eps)
    )

def H_ECT(z, eps, H0=H0_BASE):
    """Hubble rate H(z,eps) in km/s/Mpc."""
    return H0 * E_ECT(z, eps)

def t_cosmic(z, eps, H0=H0_BASE, z_upper=1e8):
    """Cosmic time at redshift z under ECT-native background.

    t(z) = integral from z to z_upper of dz' / [(1+z') * H(z',eps)]
    Returned in Gyr.

    Integral is split into chunks to preserve accuracy: most of the
    cosmic time at low z comes from z in [0, 10], so that range is
    integrated at high precision; higher-z ranges contribute little
    but are integrated in logarithmic chunks to avoid roundoff.
    """
    def integrand(zp):
        return 1.0 / ((1.0 + zp) * H0 * E_ECT(zp, eps))

    # Split into physically meaningful chunks
    breakpoints = [z, max(z, 10), max(z, 1e3), max(z, 1e5), z_upper]
    # Remove duplicates while preserving order
    seen = []
    for b in breakpoints:
        if not seen or b > seen[-1]:
            seen.append(b)

    total = 0.0
    for a, b in zip(seen[:-1], seen[1:]):
        val, _ = integrate.quad(integrand, a, b,
                                 limit=500, epsrel=1e-10, epsabs=1e-30)
        total += val
    # total has units of (km/s/Mpc)^{-1}; convert to Gyr
    return total * HUBBLE_TIME_GYR

def t_0(eps, H0=H0_BASE):
    """Cosmic age today t_0(eps) in Gyr."""
    return t_cosmic(0.0, eps, H0=H0)

def t_at_z(z, eps, H0=H0_BASE):
    """Alias for t_cosmic(z, eps, H0)."""
    return t_cosmic(z, eps, H0=H0)

if __name__ == "__main__":
    print("="*72)
    print("ECT-native background: age scan over epsilon")
    print("="*72)
    print(f"Baseline H0 = {H0_BASE} km/s/Mpc (Planck 2018 LCDM)")
    print()
    print(f"{'eps':>8}  {'t_0 (Gyr)':>12}  {'t(z=10) Gyr':>12}  "
          f"{'t(z=1100) Gyr':>14}")
    print("-"*72)
    for e in [0.00, 0.010, 0.020, 0.027, 0.032, 0.038, 0.043]:
        t0 = t_0(e)
        t10 = t_at_z(10.0, e)
        t1100 = t_at_z(1100.0, e)
        print(f"{e:>8.4f}  {t0:>12.4f}  {t10:>12.5f}  {t1100:>14.6f}")
    print()
    print("Reference:")
    print(f"  LCDM (eps=0): t_0 = {t_0(0.0):.3f} Gyr, "
          f"t(z=10) = {t_at_z(10.0, 0.0)*1000:.1f} Myr, "
          f"t(z=1100) = {t_at_z(1100.0, 0.0)*1000:.4f} Myr")
    print(f"  Published LCDM: t_0 = 13.79 Gyr, t(z=10) ~ 475 Myr, "
          f"t(z=1100) ~ 0.37 Myr")
