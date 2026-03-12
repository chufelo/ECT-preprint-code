#!/usr/bin/env python3
"""
Fig 1: SPARC rotation curves — phi-closure framework.

PHYSICS (phi-closure):
  mu(g_obs/g_dag) * g_obs = g_bar
  with mu(x) = x/sqrt(1+x^2)

  Solution: g_obs^2 = (g_bar^2 + sqrt(g_bar^4 + 4*g_bar^2*g_dag^2))/2

  One environment parameter phi_env per galaxy sets g_dag(phi_env).
  g_dag ~ 1.2e-10 m/s^2 (quasi-universal).

NOTE: NO G_eff(r) = G*sqrt(1+r^2/r_0^2). NO r_0 parameter.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import i0, i1, k0, k1

G = 4.302e-6  # (km/s)^2 kpc / M_sun
g_dag_default = 3.7e-3  # (km/s)^2/kpc = 1.2e-10 m/s^2

def g_obs_phi(g_bar, g_dag=g_dag_default):
    """Exact phi-closure: mu(g/g_dag)*g = g_bar, mu(x)=x/sqrt(1+x^2)"""
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4*g_bar**2*g_dag**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))

def v_bar_disk(r, M_d, R_d):
    """Freeman exponential disk baryonic velocity."""
    y = r / (2*R_d)
    y = np.clip(y, 1e-10, None)
    term = i0(y)*k0(y) - i1(y)*k1(y)
    return np.sqrt(np.clip(2*G*M_d/R_d * y**2 * term, 0, None))

def v_ect(r, M_d, R_d, g_dag=g_dag_default, M_b=0, r_b=1):
    """ECT rotation curve from phi-closure."""
    v2_bar = v_bar_disk(r, M_d, R_d)**2
    if M_b > 0:
        v2_bar += G*M_b*r / (r + r_b)**2
    g_bar = v2_bar / r
    g_obs = g_obs_phi(g_bar, g_dag)
    return np.sqrt(np.clip(r * g_obs, 0, None))

# SPARC galaxy parameters
galaxies = {
    'NGC 3198': {'M_d': 3.5e10, 'R_d': 3.4, 'g_dag': 3.7e-3},
    'NGC 2403': {'M_d': 4.5e9,  'R_d': 2.0, 'g_dag': 3.7e-3},
    'DDO 154':  {'M_d': 3e7,    'R_d': 0.8, 'g_dag': 3.7e-3},
    'NGC 6503': {'M_d': 1.9e10, 'R_d': 2.5, 'g_dag': 3.7e-3},
    'UGC 2885': {'M_d': 2e11,   'R_d': 12., 'g_dag': 3.7e-3},
}

if __name__ == '__main__':
    print('ECT phi-closure rotation curves')
    print('mu(g/g_dag)*g = g_bar, mu(x)=x/sqrt(1+x^2)')
    print('No r_0. One g_dag per galaxy.')
    for name, p in galaxies.items():
        r = np.linspace(0.5, p['R_d']*10, 100)
        v = v_ect(r, p['M_d'], p['R_d'], p['g_dag'])
        print(f"  {name}: v_flat ~ {v[-1]:.0f} km/s")
