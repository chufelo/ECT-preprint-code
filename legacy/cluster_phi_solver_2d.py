#!/usr/bin/env python3
"""
2D thin-lens ECT phi-closure solver for merging clusters.

Corresponding paper
-------------------
Blagovidov V., "Euclidean Condensate Theory (ECT): Emergence of
Spacetime, Quantum Mechanics, and Gravity from Spontaneous O(4)
Symmetry Breaking", Sections 12.5-12.6, Appendix G.

Purpose
-------
Test the ECT phi-branch on cluster mergers WITHOUT any
phenomenological M_cond,coll component.
Only baryons + phi-field equation -> lensing.

Method
------
1. Baryonic surface density:
       Sigma_b(x,y) = Sigma_star(x,y) + Sigma_gas(x,y)
   Each component is a sum of Gaussian peaks:
       Sigma_i = M_i/(2*pi*s_i^2) * exp(-R^2/(2*s_i^2))

2. Thin-lens Newtonian field (projected sheet approximation):
       g_N(x,y) = 2*pi*G * Sigma_b(x,y)

3. Algebraic phi-closure (exact for spherical, proxy for 2D):
       mu(g/g_dag) * g = g_N
   with baseline interpolating function:
       mu(x) = x / sqrt(1 + x^2)

4. Enhancement factor (solved analytically):
       nu(y) = sqrt( (1 + sqrt(1 + 4/y^2)) / 2 )
   where y = g_N / g_dag.

5. Effective lensing surface density:
       Sigma_eff(x,y) = nu(g_N/g_dag) * Sigma_b(x,y)

6. Convergence map:
       kappa(x,y) = Sigma_eff(x,y) / Sigma_crit

Clusters tested
---------------
- Bullet Cluster (1E 0657-558)      [Clowe+2006, Paraficz+2016]
- MACS J0025.4-1222                  [Bradac+2008]
- El Gordo (ACT-CL J0102-4915)      [Diego+2023]
- Abell 520                          [Mahdavi+2007]

Key results
-----------
QUALITATIVE (offset morphology): ALL 4 systems PASS.
    Bullet, MACS J0025, El Gordo: kappa peaks at compact stellar clumps
    Abell 520: kappa peak at dense central gas core
    Both morphologies are natural in ECT because the phi-field
    responds to local density contrast, not to a universal
    collisionless species.

QUANTITATIVE (lensing amplitude):
    M_ECT/M_obs ~ 0.15-0.30 (2D Gaussian profiles)
    M_ECT/M_obs ~ 0.34-0.45 (spherical beta-model, see
      calc_cluster_lensing.py)
    Deficit factor ~2-3, comparable to MOND cluster problem.
    Within expected accuracy of order-of-magnitude estimate.

IMPORTANT CAVEAT
----------------
For spherically symmetric systems, the algebraic phi-closure
is the EXACT solution of the AQUAL-type field equation (by
Gauss's law). For non-spherical mergers, the thin-lens sheet
approximation g_N = 2*pi*G*Sigma_b is only a proxy; the full
calculation requires solving:
    nabla . [mu(|nabla Phi|/a_0) nabla Phi] = 4*pi*G*rho_bar
on a 3D grid. See OP22 in the paper.

References
----------
Clowe et al. 2006, ApJ 648, L109
Paraficz et al. 2016, A&A 594, A121
Bradac et al. 2008, ApJ 687, 959
Diego et al. 2023, A&A 672, A3
Mahdavi et al. 2007, ApJ 668, 806
Markevitch et al. 2004, ApJ 606, 819
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter

# ============================================================
# Physical constants
# ============================================================
KPC = 3.086e19     # metres per kiloparsec
MSUN = 1.989e30    # kg per solar mass
G_SI = 6.674e-11   # gravitational constant (SI)

# ============================================================
# Core functions
# ============================================================

def gaussian_sigma(X, Y, M_msun, sigma_kpc, x0_kpc, y0_kpc):
    """
    Gaussian projected surface density in kg/m^2.

    Parameters
    ----------
    X, Y : ndarray
        2D grid coordinates in kpc.
    M_msun : float
        Total mass of this component in solar masses.
    sigma_kpc : float
        Gaussian width (standard deviation) in kpc.
    x0_kpc, y0_kpc : float
        Centre coordinates in kpc.

    Returns
    -------
    Sigma : ndarray
        Surface density map in kg/m^2.
    """
    M_kg = M_msun * MSUN
    s_m = sigma_kpc * KPC
    Xm = X * KPC
    Ym = Y * KPC
    R2 = (Xm - x0_kpc * KPC)**2 + (Ym - y0_kpc * KPC)**2
    return (M_kg / (2 * np.pi * s_m**2)) * np.exp(-R2 / (2 * s_m**2))


def nu_phi(y):
    """
    ECT enhancement factor from phi-closure.

    For the baseline interpolating function
        mu(x) = x / sqrt(1 + x^2),
    solves mu(g/g_dag) * g = g_N analytically.

    Parameters
    ----------
    y : ndarray
        Ratio g_N / g_dag (dimensionless).

    Returns
    -------
    nu : ndarray
        Enhancement factor nu = g / g_N >= 1.
        In Newtonian regime (y >> 1): nu -> 1.
        In deep-MOND regime (y << 1): nu -> sqrt(2/y) >> 1.
    """
    y = np.clip(y, 1e-30, None)
    return np.sqrt(0.5 * (1 + np.sqrt(1 + 4 / y**2)))


def find_peaks(field, X, Y, threshold=0.3, size=9):
    """
    Simple peak finder on 2D field using local maximum filter.

    Parameters
    ----------
    field : ndarray
        2D field to search.
    threshold : float
        Minimum fraction of global max to consider.
    size : int
        Neighbourhood size for maximum filter.

    Returns
    -------
    peaks : list of (x_kpc, y_kpc, value) tuples
    """
    mx = np.max(field)
    if mx <= 0:
        return []
    mask = (field > threshold * mx) & (field == maximum_filter(field, size=size))
    return [(float(X[i, j]), float(Y[i, j]), float(field[i, j]))
            for i, j in np.argwhere(mask)]


def aperture_mass_msun(X, Y, sigma_map, x0, y0, R_ap):
    """
    Integrated mass within circular aperture.

    Parameters
    ----------
    X, Y : ndarray
        Grid in kpc.
    sigma_map : ndarray
        Surface density in kg/m^2.
    x0, y0 : float
        Aperture centre in kpc.
    R_ap : float
        Aperture radius in kpc.

    Returns
    -------
    mass : float
        Enclosed mass in solar masses.
    """
    mask = (X - x0)**2 + (Y - y0)**2 <= R_ap**2
    dx_m = (X[0, 1] - X[0, 0]) * KPC
    dy_m = (Y[1, 0] - Y[0, 0]) * KPC
    return np.sum(sigma_map[mask]) * abs(dx_m * dy_m) / MSUN


# ============================================================
# Cluster configurations
#
# Format: (M_msun, x_kpc, y_kpc, sigma_kpc)
# Parameters are order-of-magnitude characterisations
# consistent with X-ray and lensing observations.
# They should NOT be interpreted as precision fits.
# ============================================================
clusters = {
    'Bullet': {
        'description': 'Bullet Cluster 1E 0657-558, z=0.296',
        'stars': [(5e12, -250, 0, 70), (5e12, 250, 0, 70)],
        'gas': [(6e13, -150, 0, 200), (6e13, 100, 0, 250)],
        'g_dag': 1.2e-10,  # m/s^2
        'L': 800,   # kpc, half-size of computation grid
        'N': 401,   # grid resolution
        'obs': {250: 2.2e14, 500: 5e14, 1000: 1e15},
        'refs': 'Clowe+2006, Paraficz+2016, Markevitch+2004',
    },
    'MACS_J0025': {
        'description': 'MACS J0025.4-1222, z=0.586',
        'stars': [(3e12, -200, 0, 60), (3e12, 200, 0, 60)],
        'gas': [(2e13, -50, 0, 250), (2e13, 50, 0, 250)],
        'g_dag': 1.2e-10,
        'L': 800, 'N': 401,
        'obs': {500: 4.5e14},
        'refs': 'Bradac+2008',
    },
    'El_Gordo': {
        'description': 'ACT-CL J0102-4915 (El Gordo), z=0.87',
        'stars': [(8e12, -300, 0, 80), (5e12, 300, 0, 60)],
        'gas': [(5e13, -100, 0, 300), (3e13, 100, 0, 280)],
        'g_dag': 1.2e-10,
        'L': 1000, 'N': 451,
        'obs': {500: 5.5e14},
        'refs': 'Diego+2023',
    },
    'Abell_520': {
        'description': 'Abell 520, z=0.201 (dense central gas core)',
        'stars': [(3e12, -250, 0, 80), (3e12, 250, 0, 80)],
        'gas': [(3.5e13, 0, 0, 180)],
        'g_dag': 1.2e-10,
        'L': 800, 'N': 401,
        'obs': {300: 2.7e14},
        'refs': 'Mahdavi+2007',
    },
}

# ============================================================
# Main solver
# ============================================================
if __name__ == '__main__':
    print('=' * 75)
    print('2D THIN-LENS ECT phi-CLOSURE: CLUSTER SUITE')
    print('No M_cond,coll. Only baryons + phi-field.')
    print('=' * 75)

    for name, cl in clusters.items():
        L = cl['L']; N = cl['N']
        x = np.linspace(-L, L, N)
        y = np.linspace(-L, L, N)
        X, Y = np.meshgrid(x, y)

        # Build surface density maps
        Sig_star = sum(
            gaussian_sigma(X, Y, p[0], p[3], p[1], p[2])
            for p in cl['stars']
        )
        Sig_gas = sum(
            gaussian_sigma(X, Y, p[0], p[3], p[1], p[2])
            for p in cl['gas']
        )
        Sig_b = Sig_star + Sig_gas

        # Apply phi-closure
        g_N = 2 * np.pi * G_SI * Sig_b
        y_ratio = g_N / cl['g_dag']
        nu = nu_phi(y_ratio)
        Sig_eff = nu * Sig_b

        # Peak analysis
        pk_kappa = find_peaks(Sig_eff, X, Y)
        pk_star = find_peaks(Sig_star, X, Y)
        pk_gas = find_peaks(Sig_gas, X, Y)

        # Nearest-peak distances
        if pk_kappa and pk_star:
            d_star = min(
                np.sqrt((k[0]-s[0])**2 + (k[1]-s[1])**2)
                for k in pk_kappa for s in pk_star
            )
        else:
            d_star = float('nan')
        if pk_kappa and pk_gas:
            d_gas = min(
                np.sqrt((k[0]-g[0])**2 + (k[1]-g[1])**2)
                for k in pk_kappa for g in pk_gas
            )
        else:
            d_gas = float('nan')

        follows = 'STARS' if d_star < d_gas else 'GAS'
        M_bar = sum(p[0] for p in cl['stars']) + sum(p[0] for p in cl['gas'])

        print(f'\n--- {name} ({cl["description"]}) ---')
        print(f'  M_bar = {M_bar:.1e} M_sun')
        print(f'  kappa peaks follow: {follows}')
        print(f'    d(star -> kappa) = {d_star:.0f} kpc')
        print(f'    d(gas -> kappa)  = {d_gas:.0f} kpc')

        for R_obs, M_lens in cl['obs'].items():
            M_bar_ap = aperture_mass_msun(X, Y, Sig_b, 0, 0, R_obs)
            M_eff_ap = aperture_mass_msun(X, Y, Sig_eff, 0, 0, R_obs)
            mu = M_eff_ap / M_bar_ap if M_bar_ap > 0 else 0
            ratio = M_eff_ap / M_lens
            print(f'  R={R_obs} kpc: M_bar={M_bar_ap:.2e}, M_eff={M_eff_ap:.2e}, '
                  f'M_obs={M_lens:.2e}, M_ECT/M_obs={ratio:.2f}, mu={mu:.2f}')
