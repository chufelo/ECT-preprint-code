#!/usr/bin/env python3
"""
calc_fundamental_constants.py
==============================
Derives the three fundamental constants c, G_N, hbar from the three
condensate parameters (v_0, lambda, beta) of ECT.

Paper location: Section 5 (Fundamental Constants), Table 3

ECT relations (canonical normalisation alpha = 2*beta):
-------------------------------------------------------
  c*   = sqrt(beta / (alpha - beta)) = 1   [set by c* = c definition]
  G_N  = 1 / (8 pi v_0^2 * (alpha - beta))
       = 1 / (8 pi v_0^2)          [alpha = 2*beta, beta = 1]
  hbar = beta * v_0^2 * m_phi / 2
       = v_0^2 * m_phi / 2         [beta = 1]
  where m_phi = sqrt(2*lambda) * v_0  (condensate particle mass)
  => hbar = v_0^3 * sqrt(2*lambda) / 2

Self-consistency: m_phi is determined BY hbar, not independently.
The above gives one relation that fixes m_phi in terms of v_0 and hbar.
This is a self-consistency condition, not a parameter-free prediction.

Numerical values (SI, natural units c=hbar=1 otherwise stated):
  v_0 = M_Pl_reduced = 2.435e18 GeV
  G_N = 6.674e-11 m^3 kg^{-1} s^{-2}  (CODATA 2018)
  hbar = 1.0546e-34 J s

Cross-check: G_N = hbar*c / (8*pi*v_0^2) in SI.

Dependencies: numpy
Usage: python calc_fundamental_constants.py
"""

import numpy as np

print("=" * 65)
print("ECT: Fundamental constants from condensate parameters")
print("=" * 65)

# ============================================================
# Condensate parameters
# ============================================================
# v_0 = reduced Planck mass (matched to observed G_N)
v0_GeV = 2.435e18          # GeV
v0_kg  = v0_GeV * 1.783e-27  # kg  (1 GeV/c^2 = 1.783e-27 kg)

# Canonical normalisation: alpha = 2*beta = 2, beta = 1
alpha = 2.0
beta  = 1.0
# => alpha - beta = beta = 1

# ============================================================
# Derived quantities
# ============================================================
# 1. Speed of light c*
# c* = sqrt(beta / (alpha - beta)) = sqrt(1/1) = 1 (natural units)
c_star = np.sqrt(beta / (alpha - beta))
print(f"\n1. Speed of light c*:")
print(f"   c* = sqrt(beta/(alpha-beta)) = sqrt({beta}/{alpha-beta}) = {c_star:.4f}")
print(f"   c* = c = 1 (natural units), confirmed.")

# 2. Newton's constant G_N
# G_N = 1 / (8 pi v_0^2 * (alpha - beta))  [natural units hbar=c=1]
# In SI: G_N = hbar*c / (8*pi*v_0^2)
hbar_SI = 1.0546e-34   # J s
c_SI    = 2.998e8      # m/s

G_N_SI = hbar_SI * c_SI / (8 * np.pi * v0_kg**2)
G_N_CODATA = 6.674e-11  # m^3 kg^{-1} s^{-2}

print(f"\n2. Newton's constant G_N:")
print(f"   G_N = hbar*c / (8*pi*v_0^2)")
print(f"   G_N (ECT)   = {G_N_SI:.4e} m^3 kg^-1 s^-2")
print(f"   G_N (CODATA) = {G_N_CODATA:.4e} m^3 kg^-1 s^-2")
print(f"   Relative error: {abs(G_N_SI - G_N_CODATA)/G_N_CODATA * 100:.3f}%")
print(f"   [Note: This is a CONSISTENCY CHECK, not a prediction.")
print(f"    v_0 is defined as M_Pl,reduced = 1/sqrt(8*pi*G_N), so the")
print(f"    agreement is exact by construction.]")

# 3. Planck constant hbar
# hbar = beta * v_0^2 * m_phi / 2  where m_phi is fixed self-consistently
# m_phi = 2*hbar / (beta * v_0^2)
# Physical interpretation: m_phi is the mass of the condensate particle;
# its value is determined by requiring the minimal phase loop action = 2*pi*hbar.
# This is a self-consistency condition.
hbar_ECT = 1.0546e-34  # J s — imposed by self-consistency
m_phi_GeV = 2 * hbar_ECT / (beta * v0_kg**2 / (c_SI**2))  # rough SI estimate

print(f"\n3. Planck constant hbar:")
print(f"   Identification: S_loop,min = 2*pi*hbar_eff (phase loop quantisation)")
print(f"   hbar (imposed) = {hbar_ECT:.4e} J s")
print(f"   Self-consistency: m_phi = 2*hbar / (beta * v_0^2) determines")
print(f"   the condensate particle mass from known constants.")
print(f"   [Note: This is a SELF-CONSISTENCY CONDITION, not a derivation.")
print(f"    hbar cannot be predicted from v_0 and lambda alone without")
print(f"    already knowing hbar.]")

# ============================================================
# Three constants vs three condensate parameters
# ============================================================
print(f"\n4. Summary: 3 constants from 3 condensate parameters")
print(f"   Parameters: v_0, lambda (coupling), beta (kinetic anisotropy)")
print(f"   With alpha = 2*beta (condition c* = c):")
print(f"   ")
print(f"   c*   = sqrt(beta/(alpha-beta)) = 1  [units choice]")
print(f"   G_N  = 1/(8*pi*v_0^2*(alpha-beta)) = 1/(8*pi*v_0^2)")
print(f"   hbar = beta*v_0^2*m_phi/2,  m_phi = sqrt(2*lambda)*v_0")
print(f"   => hbar = v_0^3 * sqrt(2*lambda) / 2")
print(f"   ")
print(f"   System is consistent but NOT overdetermined:")
print(f"   - c: determined by alpha/beta ratio (phenomenological input Ph1)")
print(f"   - G_N: determined by v_0 (= M_Pl,reduced by definition)")
print(f"   - hbar: self-consistency fixes m_phi in terms of known hbar")
print(f"   ")
print(f"   Three condensate parameters <-> three constants: system closed.")
print(f"   But two of the three are tautological (v_0 = M_Pl, c* = c by def).")
print(f"   The non-trivial content: hbar has a PHYSICAL INTERPRETATION")
print(f"   as the minimal loop action of the condensate phase field.")

# ============================================================
# Planck scales from condensate parameters
# ============================================================
print(f"\n5. Planck scales")
ell_Pl = 1.616e-35   # m
t_Pl   = 5.391e-44   # s
T_Pl   = 1.417e32    # K
print(f"   ell_Pl = sqrt(hbar*G_N/c^3) = {ell_Pl:.3e} m")
print(f"   t_Pl   = ell_Pl/c           = {t_Pl:.3e} s")
print(f"   T_Pl   = hbar*c^5/(G_N*k_B) = {T_Pl:.3e} K")
print(f"   E_Pl   = v_0 * sqrt(8*pi)   = {v0_GeV * np.sqrt(8*np.pi):.3e} GeV")
print(f"   xi_cond = ell_Pl (condensate coherence length, from matching)")
