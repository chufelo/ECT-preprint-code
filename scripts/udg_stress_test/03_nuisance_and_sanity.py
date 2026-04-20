#!/usr/bin/env python3
"""
Nuisance budget and side diagnostics for the UDG stress test.

Produces the quantitative content of Appendix `app:udg_stress_test`
subsections:
  - app:udg:nuisance (distance covariance, M/L, small-N MC)
  - app:udg:efe (external field benchmark)
  - app:udg:side_checks (UFDs, GCs, FCC 224 non-spherical, selection)

Scientific scope: DIAGNOSTIC.  Does not claim any rescue mechanism.
"""
import math
import numpy as np

G      = 6.6743e-11
c_SI   = 2.998e8
M_sun  = 1.989e30
kpc    = 3.086e19
H0     = 67.4e3 / 3.086e22
a_0    = 1.2e-10
g_dag0 = c_SI * H0 / (2 * math.pi)

def xi_req(M_star_solar, Re_kpc, sigma_kms, R_half_factor=4.0/3.0, f_e=0.5):
    M_star = M_star_solar * M_sun
    Re     = Re_kpc * kpc
    R_half = R_half_factor * Re
    sigma  = sigma_kms * 1000.0
    M_dyn  = 4.0 * sigma**2 * R_half / G
    M_bar  = f_e * M_star
    r      = M_dyn / M_bar
    g_N    = G * M_bar / R_half**2
    return r, max(0.0, r*(r-1)*g_N/g_dag0)

def section(title):
    print("\n" + "="*80); print(title); print("="*80)

# -----------------------------------------------------------------
section("Distance covariance for DF4 (L, M*, R_e all scale with D)")
# If D -> f * D_fid, then L ~ f^2, M_star ~ f^2, R_e ~ f, sigma independent
for D in (13, 15, 17, 20, 22, 25):
    f = D / 20.0
    r, Xi = xi_req(1.5e8 * f*f, 1.6 * f, 6.3)
    print(f"  D = {D:3d} Mpc  ->  r = {r:5.2f},  Xi_req = {Xi:.3e}")
print("  -> factor ~10 swing across plausible distance range")

# -----------------------------------------------------------------
section("M/L sensitivity for DF4 (central sigma = 6.3 km/s)")
L_V_fid = 1.5e8 / 2.0   # fiducial at M/L = 2
for ML in (1.0, 1.5, 2.0, 3.0, 4.0):
    M_star = ML * L_V_fid
    r, Xi = xi_req(M_star, 1.6, 6.3)
    print(f"  M/L = {ML:4.2f}  ->  M* = {M_star/1e8:.2f}e8,  r = {r:5.3f},  Xi_req = {Xi:.3e}")
print("  -> factor ~10 swing across plausible M/L range")

# -----------------------------------------------------------------
section("Small-N likelihood MC for DF4 (N = 7 GC tracers)")
np.random.seed(42)
N = 7
true_sigma = 6.3
trials = 10000
meas = np.empty(trials)
for i in range(trials):
    v = np.random.normal(0.0, true_sigma, N)
    meas[i] = math.sqrt(np.mean(v*v))
q2_5, q16, q50, q84, q97_5 = np.percentile(meas, [2.5, 16, 50, 84, 97.5])
print(f"  True sigma = {true_sigma} km/s, N = {N}")
print(f"  68% CI: [{q16:.2f}, {q84:.2f}] km/s")
print(f"  95% CI: [{q2_5:.2f}, {q97_5:.2f}] km/s")
print(f"  Published 1-sigma: +2.5 / -1.6 km/s  (avg ~2.05)")
print()
print("  Xi_req across 95% CI:")
for s in (3.0, 4.7, 6.3, 8.8, 11.0):
    r, Xi = xi_req(1.5e8, 1.6, s)
    print(f"    sigma = {s:4.1f}  ->  Xi_req = {Xi:.3e}")
print("  -> 95% upper edge Xi ~ 0.15  << 1 still.")

# -----------------------------------------------------------------
section("External field effect benchmark (MOND-EFE)")
efe = [
    ("NGC 1052-DF4",      1e11,   80),
    ("FCC 224",           3e10,   70),
    ("NGC 5846-UDG1",     5e11,  100),
    ("Dragonfly 44",      1e13,  500),
]
print(f"{'Object':<20} {'M_host/Msun':>11} {'d_proj/kpc':>10} {'g_ext/a_0':>10}")
for n, Mh, d in efe:
    g_ext = G * Mh * M_sun / (d * kpc)**2
    print(f"{n:<20} {Mh:>11.2e} {d:>10d} {g_ext/a_0:>10.3f}")
print("  -> g_ext/a_0 << 1 for all four; EFE screening minor")
print("     does not numerically distinguish DF4 from NGC 5846-UDG1.")

# -----------------------------------------------------------------
section("UFDs side diagnostic (NOT validation, only that proxy does not break)")
ufds = [
    ("Draco",         2.9e5, 0.22, 9.1),
    ("Sculptor",      2.3e6, 0.28, 9.2),
    ("Fornax",        1.3e7, 0.79, 10.7),
    ("Ursa Minor",    3.9e5, 0.28, 9.5),
    ("Carina",        3.8e5, 0.25, 6.6),
    ("Segue I",       3.4e2, 0.03, 3.7),
    ("Bootes I",      2.9e4, 0.24, 4.6),
    ("Willman 1",     1.0e3, 0.03, 4.0),
]
print(f"{'Object':<15} {'M*/Msun':>10} {'R_e/kpc':>8} {'sigma':>6} {'r':>8} {'Xi_req':>10}")
for n, Ms, Re, s in ufds:
    r, Xi = xi_req(Ms, Re, s)
    print(f"{n:<15} {Ms:>10.1e} {Re:>8.3f} {s:>6.1f} {r:>8.1f} {Xi:>10.2f}")
print("  -> Xi in [2, 1000].  Spread driven by binary inflation,")
print("     tidal non-equilibrium, anisotropy.  Side diagnostic only.")

# -----------------------------------------------------------------
section("GCs Newton sanity check (g_N / g_dagger_0 >> 1)")
gcs = [
    ("47 Tuc",       7.9e5, 0.0042, 11.0),
    ("Omega Cen",    4.0e6, 0.0071, 16.8),
    ("M13",          6.1e5, 0.0033,  7.1),
    ("M15 core",     5.6e5, 0.0018, 13.5),
]
print(f"{'Object':<15} {'M*/Msun':>10} {'R_h kpc':>9} {'sigma':>6} {'g_N/g_d0':>10}")
for n, Ms, Rh, s in gcs:
    g_N_half = G * 0.5 * Ms * M_sun / ((4.0/3.0) * Rh * kpc)**2
    r, _ = xi_req(Ms, Rh, s)
    print(f"{n:<15} {Ms:>10.1e} {Rh:>9.5f} {s:>6.1f} {g_N_half/g_dag0:>10.1f}")
print("  -> All g_N/g_dagger_0 >> 1, closure returns g -> g_N automatically.")
print("     Trivial Newton recovery at high density.")
