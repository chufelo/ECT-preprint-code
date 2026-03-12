#!/usr/bin/env python3
"""
Derivation of Newton's constant from condensate parameters.

ECT: G_N = 1/(8*pi*v_0^2*(alpha-beta))
At alpha=2, beta=1: G_N = 1/(8*pi*v_0^2)
=> v_0 = M_Pl,reduced = 2.435e18 GeV

Phi-dependent coupling: G_eff(phi) = G_N * exp(-phi)
where phi = ln(chi/chi_vac).

NOTE: NO spatial G_eff(r) = G*sqrt(1+r^2/r_0^2).
NO v_0(r) spatial profile. The galactic phenomenology uses
the phi-closure: mu(g/g_dag)*g = g_bar.
"""
import numpy as np

G_N = 6.67430e-11  # m^3/(kg*s^2)
hbar = 1.054571817e-34; c = 2.99792458e8
M_Pl = np.sqrt(hbar*c/G_N)
M_Pl_red = M_Pl / np.sqrt(8*np.pi)
GeV_to_kg = 1.78266192e-27

print('ECT: G_N from condensate')
print(f'  v_0 = M_Pl,reduced = {M_Pl_red/GeV_to_kg:.3e} GeV')
print(f'  G_N = 1/(8*pi*v_0^2) = {G_N:.5e} m^3/(kg*s^2)')
print()
print('G_eff(phi) = G_N * exp(-phi)')
print('Galactic: phi-closure mu(g/g_dag)*g = g_bar')
print('NO spatial v_0(r) or G_eff(r).')
