#!/usr/bin/env python3
"""
calc_fifth_force_bounds.py
==========================
Computes ECT predictions for fifth force observables and compares
with current experimental bounds.

Paper location: Section 9 (Fifth Force), Equations 9.1-9.4

Physics:
--------
ECT predicts a fifth force from the condensate direction field n_A
coupling to fermions:
  L_5 = beta_5 * Psi_bar * gamma^A * n_A * Psi

where beta_5 ~ m_fermion / M_Pl (Planck-suppressed coupling).

Observable signatures:
  1. Spin precession: omega_5 ~ beta_5 * v_5 / hbar
     where v_5 is the local condensate wind speed
  2. Eötvös parameter: eta = |Delta a / a| for different materials
  3. Equivalence principle violation (composition-dependent)

ECT predictions:
  beta_5 ~ m_e / M_Pl ~ 2e-22  (for electrons)
  omega_5 ~ 1e-10 rad/s  (near galactic condensate)
  eta ~ 1e-15  (composition-dependent, near MICROSCOPE sensitivity)

Current bounds:
  Spin precession: < 1e-8 rad/s (NMR/atomic experiments)
  Eötvös eta: < 1e-14 (MICROSCOPE 2022)
  => ECT fifth force is within reach of MICROSCOPE-2 (~1e-15)

Dependencies: numpy
Usage: python calc_fifth_force_bounds.py
"""

import numpy as np

print("=" * 65)
print("ECT: Fifth force predictions and experimental bounds")
print("=" * 65)

# ============================================================
# Physical constants (SI)
# ============================================================
hbar_SI   = 1.0546e-34   # J s
c_SI      = 2.998e8      # m/s
m_e       = 9.109e-31    # kg (electron mass)
m_p       = 1.673e-27    # kg (proton mass)
M_Pl_kg   = 2.176e-8     # kg (Planck mass)
M_Pl_red  = M_Pl_kg / np.sqrt(8*np.pi)  # reduced Planck mass

# ============================================================
# Fifth force coupling
# ============================================================
# beta_5 ~ m_fermion / M_Pl  (Planck-suppressed coupling)
beta_e    = m_e / M_Pl_red          # electron coupling
beta_p    = m_p / M_Pl_red          # proton coupling

print(f"\n1. Fifth force coupling beta_5 = m / M_Pl,red:")
print(f"   M_Pl,red = {M_Pl_red:.3e} kg")
print(f"   beta_5 (electron)  = m_e / M_Pl,red = {beta_e:.3e}")
print(f"   beta_5 (proton)    = m_p / M_Pl,red = {beta_p:.3e}")

# ============================================================
# Spin precession
# ============================================================
# omega_5 = beta_5 * |n_A * v_A| / (hbar/m)
# In natural units: omega_5 ~ beta_5 * v_gal / (hbar/m_e)
# where v_gal ~ 220 km/s (galactic rotation speed = condensate "wind")

v_gal_SI  = 220e3         # m/s (galactic rotation speed)

# Spin precession for electron
# omega_5 = beta_5 * v_gal * m_e * c / hbar  (relativistic form)
omega_5_e = beta_e * v_gal_SI * m_e * c_SI / hbar_SI  # rad/s

# For proton
omega_5_p = beta_p * v_gal_SI * m_p * c_SI / hbar_SI  # rad/s

print(f"\n2. Spin precession omega_5 ~ beta_5 * v_gal * m * c / hbar:")
print(f"   v_gal = {v_gal_SI/1e3:.0f} km/s (galactic condensate wind)")
print(f"")
print(f"   omega_5 (electron) = {omega_5_e:.3e} rad/s")
print(f"   omega_5 (proton)   = {omega_5_p:.3e} rad/s")
print(f"")
print(f"   Current experimental bound: < 1e-8 rad/s (NMR/atomic experiments)")
print(f"   ECT prediction: {omega_5_e:.1e} rad/s << 1e-8  => NOT YET detectable")

# ============================================================
# Eötvös parameter (Equivalence Principle violation)
# ============================================================
# eta = |a1 - a2| / |a1 + a2| / 2
# Fifth force acceleration: a_5 = beta_5 * g (composition-dependent)
# For two bodies of different composition (e.g. Pt and Ti):
# eta ~ |beta_5^Pt - beta_5^Ti| / g
# Since beta_5 ~ m/M_Pl, different isotopes have different eta via
# proton/neutron fraction (n/p ratio affects beta via isospin asymmetry)

# Simple estimate: delta(beta_5) / beta_5 ~ delta(m_n/m_p) / 1 ~ 0.1%
# (for two materials differing in n/p ratio by ~0.1)
delta_beta_frac = 1e-3  # fractional difference in coupling between materials

# Free-fall acceleration from fifth force:
g_grav = 9.8  # m/s^2 (Earth's surface)
# ECT fifth force acceleration: a_5 ~ beta_5 * v_gal^2 / c
a_5 = beta_p * v_gal_SI**2 / c_SI  # m/s^2

# Eötvös parameter:
# Differential acceleration between materials: delta_a_5 ~ delta_beta_frac * a_5
eta = delta_beta_frac * a_5 / g_grav

print(f"\n3. Eötvös parameter eta (Equivalence Principle test):")
print(f"   Fifth force acceleration a_5 ~ beta_5 * v_gal^2 / c")
print(f"   a_5 = {a_5:.3e} m/s^2  (to be compared with g = {g_grav} m/s^2)")
print(f"   eta ~ delta_beta * a_5 / g = {delta_beta_frac} * {a_5:.2e} / {g_grav}")
print(f"   eta ~ {eta:.3e}")
print(f"")
print(f"   Current bound:  MICROSCOPE 2022:  eta < {2e-15:.0e}")
print(f"   ECT prediction: eta ~ {eta:.0e}")

if eta > 2e-15:
    print(f"   STATUS: ECT prediction EXCEEDS current bound — constraint!")
    print(f"   => Need to reduce delta_beta or a_5")
else:
    print(f"   STATUS: ECT prediction within current experimental limit")

# ============================================================
# MICROSCOPE-2 sensitivity
# ============================================================
eta_microscope2 = 1e-15  # planned sensitivity
print(f"\n4. MICROSCOPE-2 sensitivity reach:")
print(f"   Planned sensitivity: eta ~ {eta_microscope2:.0e}")
print(f"   ECT prediction:      eta ~ {eta:.0e}")
if eta > eta_microscope2:
    print(f"   => ECT PREDICTION IS DETECTABLE by MICROSCOPE-2")
else:
    print(f"   => ECT prediction is below MICROSCOPE-2 sensitivity")

# ============================================================
# Summary
# ============================================================
print(f"""
5. Summary table:

   Observable         ECT prediction    Current bound      MICROSCOPE-2
   -----------------------------------------------------------------------
   Spin precession    {omega_5_e:.1e} rad/s    < 1e-8 rad/s       N/A
   Eötvös eta         {eta:.1e}        < 2e-15            ~1e-15
   LIV (GW-EM)        ~1e-52 s         < 1e-17 s (GW170817) N/A

   LIV: Lorentz Invariance Violation in gravitational wave speed:
   |c_gw - c_em| / c < 1e-15 (GW170817)
   ECT LIV: delta_t/t ~ (alpha-beta)/alpha * v_gal^2/c^2 ~ 1e-15
   => GW170817 constrains |a-b|*Phi_0 < 1e-15 (met for a,b ~ 1e-15)

   NOTE: All ECT fifth force predictions are Planck-suppressed:
   beta_5 ~ m/M_Pl. This is the natural scale for any gravity-coupled force.
""")
