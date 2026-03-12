#!/usr/bin/env python3
"""
Fig 2: External Field Effect in ECT phi-closure.

PHYSICS:
  g_dag depends on phi_env. External field g_ext modifies phi_env:
    g_dag_eff = g_dag_iso / sqrt(1 + g_ext/g_dag_iso)
  
  This is the phi-closure EFE (not the old r_0-based formula).
  Physically: external field raises phi_env, screening the phi-branch.

NOTE: NO G_eff(r) = G*sqrt(1+r^2/r_0^2). NO r_0 parameter.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import i0, i1, k0, k1

G = 4.302e-6
g_dag_iso = 3.7e-3  # (km/s)^2/kpc

def g_dag_eff(g_ext, g_dag_0=g_dag_iso):
    """EFE: g_dag shifts with external field."""
    return g_dag_0 / np.sqrt(1 + g_ext/g_dag_0)

def g_obs_phi(g_bar, g_dag):
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4*g_bar**2*g_dag**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))

def v_ect(r, M_d, R_d, g_dag):
    y = r / (2*R_d)
    y = np.clip(y, 1e-10, None)
    term = i0(y)*k0(y) - i1(y)*k1(y)
    v2 = np.clip(2*G*M_d/R_d * y**2 * term, 0, None)
    g_bar = v2 / r
    g_obs = g_obs_phi(g_bar, g_dag)
    return np.sqrt(np.clip(r * g_obs, 0, None))

if __name__ == '__main__':
    print('ECT External Field Effect (phi-closure)')
    print('g_dag_eff = g_dag_iso / sqrt(1 + g_ext/g_dag_iso)')
    for g_ext in [0, 1e-3, 5e-3, 1e-2]:
        gd = g_dag_eff(g_ext)
        print(f"  g_ext = {g_ext:.1e} -> g_dag_eff = {gd:.3e} (km/s)^2/kpc")
