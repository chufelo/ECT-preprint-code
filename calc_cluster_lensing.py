#!/usr/bin/env python3
"""
ECT cluster lensing: spherical radial-profile phi-closure.

Corresponding paper
-------------------
Blagovidov V., "Euclidean Condensate Theory (ECT)", Section 12.6,
Table in Section 12.6 (Bullet Cluster results), Appendix G.

Purpose
-------
Compute the phi-closure enhancement mu(r) at each radius for a
spherical baryonic mass profile. This is complementary to the 2D
projected solver (cluster_phi_solver_2d.py):
  - This script: best for amplitude estimates (realistic baryon profile)
  - 2D script: best for offset morphology (captures spatial separation)

Method
------
1. NFW-like or beta-model baryonic mass profile M_bar(<r).
2. g_bar(r) = G * M_bar(<r) / r^2.
3. Algebraic phi-closure: mu(g/g_dag) * g = g_bar
   with mu(x) = x / sqrt(1 + x^2).
4. Solved: g_obs = sqrt((g_bar^2 + sqrt(g_bar^4 + 4*g_bar^2*g_dag^2))/2)
5. Enhancement: mu(r) = g_obs / g_bar.
6. Effective mass: M_ECT(<r) = mu(r) * M_bar(<r).

For spherical symmetry, this algebraic closure is the EXACT
solution of the AQUAL-type field equation (by Gauss's law).
No spatial discretisation needed.

Key results
-----------
Bullet Cluster (beta-model, M_gas = 1.2e14 M_sun):
  R = 250 kpc:  M_ECT/M_obs = 0.45 (mu = 1.14)
  R = 1500 kpc: M_ECT/M_obs = 0.34 (mu = 3.96)
  Deficit factor ~2-3, within expected accuracy of the method.

References
----------
Clowe et al. 2006, ApJ 648, L109
Paraficz et al. 2016, A&A 594, A121
Bradac et al. 2008, ApJ 687, 959
Diego et al. 2023, A&A 672, A3
Mahdavi et al. 2007, ApJ 668, 806
"""
import numpy as np

# Constants in (km/s)^2 kpc / M_sun system
G = 4.302e-6        # (km/s)^2 kpc / M_sun
g_dag = 3703.2       # (km/s)^2/kpc = 1.2e-10 m/s^2


def g_obs_phi(g_bar, gd=g_dag):
    """
    Exact phi-closure for spherical symmetry.

    Solves mu(g/gd)*g = g_bar with mu(x) = x/sqrt(1+x^2).
    Returns g_obs in the same units as g_bar.
    """
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4 * g_bar**2 * gd**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))


def nfw_mass(r, M200, c, R200):
    """NFW enclosed mass at radius r."""
    rs = R200 / c
    x = r / rs
    return M200 * (np.log(1 + x) - x / (1 + x)) / (np.log(1 + c) - c / (1 + c))


def beta_model_mass(r, M_total, r_c):
    """Enclosed mass for simplified isothermal beta-model (beta ~ 2/3)."""
    return M_total * r**3 / (r**3 + r_c**3)


if __name__ == '__main__':
    print('ECT cluster lensing: spherical phi-closure')
    print('=' * 80)

    # ── Bullet Cluster: realistic beta-model ──────────────────
    print('\n--- Bullet Cluster (beta-model) ---')
    print('Gas: M_gas = 1.2e14 M_sun, r_c = 200 kpc')
    print('Stars: M_star = 8e12 M_sun, r_c = 80 kpc')
    print()
    print(f'{"R (kpc)":>8} {"M_bar":>12} {"g_bar/g_dag":>10} '
          f'{"mu_phi":>7} {"M_ECT":>12} {"M_obs":>12} {"Ratio":>7}')
    print('-' * 75)

    M_obs_bullet = {250: 2.2e14, 500: 5e14, 1000: 1e15, 1500: 1.5e15}

    for R in [100, 250, 500, 750, 1000, 1500]:
        M_gas = beta_model_mass(R, 1.2e14, 200)
        M_star = beta_model_mass(R, 8e12, 80)
        M_bar = M_gas + M_star
        g_bar = G * M_bar / R**2
        g_obs = g_obs_phi(g_bar)
        mu = g_obs / g_bar
        M_ect = mu * M_bar
        M_obs = M_obs_bullet.get(R, None)
        if M_obs:
            print(f'{R:>8} {M_bar:>12.2e} {g_bar/g_dag:>10.4f} '
                  f'{mu:>7.2f} {M_ect:>12.2e} {M_obs:>12.2e} {M_ect/M_obs:>7.2f}')
        else:
            print(f'{R:>8} {M_bar:>12.2e} {g_bar/g_dag:>10.4f} '
                  f'{mu:>7.2f} {M_ect:>12.2e}')

    # ── All 4 clusters: NFW profiles ─────────────────────────
    print('\n--- All clusters (NFW) ---')
    print(f'{"Cluster":>14} {"R":>6} {"M_bar":>11} {"g/g_dag":>8} '
          f'{"mu":>6} {"M_ECT":>11} {"M_obs":>11} {"Ratio":>7}')
    print('-' * 75)

    clusters = [
        ('Bullet',     6.0e13, 1500, 3,
         [(250, 2.2e14), (500, 5e14), (1000, 1e15), (1500, 1.5e15)]),
        ('MACS_J0025', 4.6e13, 1200, 3,
         [(500, 4.5e14)]),
        ('El_Gordo',   9.3e13, 2000, 3,
         [(500, 5.5e14)]),
        ('Abell_520',  4.1e13, 1000, 3,
         [(300, 2.7e14)]),
    ]

    for name, M_bar_200, R200, c, obs in clusters:
        for R_obs, M_lens in obs:
            M_enc = nfw_mass(R_obs, M_bar_200, c, R200)
            g_bar = G * M_enc / R_obs**2
            mu = g_obs_phi(g_bar) / g_bar
            M_ect = mu * M_enc
            ratio = M_ect / M_lens
            print(f'{name:>14} {R_obs:>6} {M_enc:>11.2e} '
                  f'{g_bar/g_dag:>8.4f} {mu:>6.2f} '
                  f'{M_ect:>11.2e} {M_lens:>11.2e} {ratio:>7.2f}')
