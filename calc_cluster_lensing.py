#!/usr/bin/env python3
"""
ECT cluster lensing: HONEST calculation from first principles.

NO phenomenological M_cond,coll.
NO extra components.
ONLY: baryons + φ-field equation → lensing potential → κ map.

Method:
  1. Baryonic density profile ρ_bar(r) [NFW-like, from observations]
  2. Newtonian potential: ∇²Φ_N = 4πG ρ_bar
  3. φ-closure field equation (AQUAL form):
     ∇·[μ(|∇Φ|/a₀) ∇Φ] = 4πG ρ_bar
     where μ(x) = x/√(1+x²)
  4. This gives Φ_ECT(r) directly
  5. Lensing convergence: κ(R) = Σ_eff(R) / Σ_crit
     where Σ_eff from the ECT potential

For spherical systems, AQUAL reduces to:
  μ(g/g†) × g = g_N  (algebraic, exact for spherical!)

So for a spherical cluster, the algebraic closure IS the
honest solution. The 2D/3D solver only matters for
non-spherical merger geometry.

This means: our current numbers ARE honest for spherical
approximation. The question is whether merger geometry
changes things significantly.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

G = 4.302e-6      # (km/s)² kpc/M_sun
g_dag = 3703.2     # (km/s)²/kpc = 1.2e-10 m/s²

def g_obs_phi(g_bar, gd=g_dag):
    """EXACT φ-closure for spherical symmetry."""
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4*g_bar**2*gd**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))

def nfw_mass(r, M200, c, R200):
    rs = R200 / c
    x = r / rs
    return M200 * (np.log(1+x) - x/(1+x)) / (np.log(1+c) - c/(1+c))

def nfw_density(r, M200, c, R200):
    rs = R200 / c
    x = r / rs
    rho_s = M200 / (4*np.pi*rs**3 * (np.log(1+c) - c/(1+c)))
    return rho_s / (x * (1+x)**2)

print("=" * 70)
print("ECT CLUSTER: HONEST FIRST-PRINCIPLES CALCULATION")
print("NO M_cond,coll. NO extra components.")
print("Only baryons + φ-equation → lensing.")
print("=" * 70)

# ══════════════════════════════════════════════════════════════════
# BULLET CLUSTER
# ══════════════════════════════════════════════════════════════════
print("\n" + "═" * 70)
print("BULLET CLUSTER — spherical φ-closure (exact for spherical)")
print("═" * 70)

M_bar_200 = 6e13    # M_sun (total baryonic)
R_200 = 1500        # kpc
c_bar = 3           # baryonic concentration

# Radial profile: g_bar(r) → g_obs(r) → v_circ(r) → M_eff(<r)
r = np.logspace(np.log10(10), np.log10(2000), 500)
M_enc = nfw_mass(r, M_bar_200, c_bar, R_200)
g_bar = G * M_enc / r**2
g_obs = g_obs_phi(g_bar)
mu = g_obs / g_bar
M_eff = mu * M_enc  # effective dynamical mass

# Lensing: projected Σ_eff
# For spherical NFW, Σ(R) = 2 ∫_R^∞ ρ(r) r dr / √(r²-R²)
# M_lens(<R) ≈ M_eff(<R) for quasi-spherical (Abel transform ≈ identity for enclosed mass)

print(f"\n  Baryonic: M_bar,200 = {M_bar_200:.1e} M☉")
print(f"\n  {'R (kpc)':>8} {'M_bar(<R)':>12} {'g_bar/g†':>9} {'μ_φ':>6} {'M_ECT(<R)':>12}")
print("  " + "─" * 55)
for R_test in [100, 250, 500, 750, 1000, 1500]:
    idx = np.argmin(np.abs(r - R_test))
    print(f"  {R_test:>8} {M_enc[idx]:>12.2e} {g_bar[idx]/g_dag:>9.4f} "
          f"{mu[idx]:>6.2f} {M_eff[idx]:>12.2e}")

# OBSERVED lensing masses at different apertures
# (from Clowe+2006, Paraficz+2016, Bradač+2006)
print(f"\n  COMPARISON WITH OBSERVATIONS:")
print(f"  {'R (kpc)':>8} {'M_ECT':>12} {'M_obs (lens)':>14} {'M_ECT/M_obs':>12} {'Status':>10}")
print("  " + "─" * 60)

# Bullet: lensing mass estimates at different radii
# Bradač+2006: M(<250kpc) ≈ 1.5e14 (main) + 7e13 (sub) ≈ 2.2e14
# Clowe+2006: M(<R200) ≈ 1.5e15
observations = [
    (250, 2.2e14, "Bradač+2006 (core)"),
    (500, 5.0e14, "interpolated"),
    (1000, 1.0e15, "Clowe+2006 (partial)"),
    (1500, 1.5e15, "Clowe+2006 (R200)"),
]

for R_obs, M_lens_obs, ref in observations:
    idx = np.argmin(np.abs(r - R_obs))
    M_ect = M_eff[idx]
    ratio = M_ect / M_lens_obs
    status = "GOOD" if ratio > 0.7 else "PARTIAL" if ratio > 0.3 else "TENSION"
    print(f"  {R_obs:>8} {M_ect:>12.2e} {M_lens_obs:>14.2e} {ratio:>12.2f} {status:>10}")

# ══════════════════════════════════════════════════════════════════
# WHAT DOES ECT *ACTUALLY* PREDICT FOR BULLET?
# ══════════════════════════════════════════════════════════════════
print(f"\n{'═' * 70}")
print("WHAT ECT ACTUALLY PREDICTS (no extra components)")
print(f"{'═' * 70}")

print(f"""
ECT prediction for Bullet (spherical approximation):
  At R = 250 kpc:  M_ECT = {M_eff[np.argmin(np.abs(r-250))]:.2e} M☉
                   M_obs = 2.2e+14 M☉
                   Ratio = {M_eff[np.argmin(np.abs(r-250))]/2.2e14:.2f}
                   → ECT explains {M_eff[np.argmin(np.abs(r-250))]/2.2e14*100:.0f}% of observed lensing mass

  At R = 1500 kpc: M_ECT = {M_eff[np.argmin(np.abs(r-1500))]:.2e} M☉
                   M_obs = 1.5e+15 M☉
                   Ratio = {M_eff[np.argmin(np.abs(r-1500))]/1.5e15:.2f}
                   → ECT explains {M_eff[np.argmin(np.abs(r-1500))]/1.5e15*100:.0f}% of observed lensing mass
""")

# ══════════════════════════════════════════════════════════════════
# ALL 4 CLUSTERS — HONEST (no M_cond,coll)
# ══════════════════════════════════════════════════════════════════
print(f"{'═' * 70}")
print("ALL 4 CLUSTERS: HONEST ECT (NO extra components)")
print(f"{'═' * 70}")

clusters = [
    # name, M_bar, R200, c, [(R_obs, M_lens_obs, ref)]
    ('Bullet', 6e13, 1500, 3, [
        (250, 2.2e14, 'Bradač+2006'),
        (1500, 1.5e15, 'Clowe+2006'),
    ]),
    ('MACS J0025', 4.6e13, 1200, 3, [
        (500, 4.5e14, 'Bradač+2008'),
    ]),
    ('El Gordo', 9.3e13, 2000, 3, [
        (500, 5.5e14, 'Diego+2023'),
        (1500, 2.0e15, 'lensing'),
    ]),
    ('Abell 520', 4.1e13, 1000, 3, [
        (300, 2.7e14, 'Mahdavi+2007'),
    ]),
]

print(f"\n{'Cluster':<14} {'R':>5} {'M_ECT':>11} {'M_obs':>11} {'Ratio':>7} {'ECT explains':>13}")
print("─" * 65)

for name, M_bar, R200, c, obs_list in clusters:
    r_cl = np.logspace(1, np.log10(R200*1.5), 500)
    M_enc_cl = nfw_mass(r_cl, M_bar, c, R200)
    g_bar_cl = G * M_enc_cl / r_cl**2
    g_obs_cl = g_obs_phi(g_bar_cl)
    M_eff_cl = (g_obs_cl / g_bar_cl) * M_enc_cl
    
    for R_obs, M_lens_obs, ref in obs_list:
        idx = np.argmin(np.abs(r_cl - R_obs))
        M_ect = M_eff_cl[idx]
        ratio = M_ect / M_lens_obs
        print(f"{name:<14} {R_obs:>5} {M_ect:>11.2e} {M_lens_obs:>11.2e} "
              f"{ratio:>7.2f} {ratio*100:>12.0f}%")

# ══════════════════════════════════════════════════════════════════
# WHAT CHANGES IF WE USE MERGER GEOMETRY?
# ══════════════════════════════════════════════════════════════════
print(f"\n{'═' * 70}")
print("EFFECT OF MERGER GEOMETRY (2D vs spherical)")
print(f"{'═' * 70}")

# For a Bullet-like merger, the key effect is:
# The TWO subclusters are separated by ~700 kpc.
# Each subcluster has its OWN φ-well.
# The total M_eff = M_eff(sub1) + M_eff(sub2), each with smaller R.

# Subcluster 1 (main): M ~ 4e13, R_char ~ 200 kpc
# Subcluster 2 (bullet): M ~ 2e13, R_char ~ 150 kpc

print(f"\n  Spherical (single halo):")
M_enc_single = nfw_mass(250, 6e13, 3, 1500)
g_single = G * M_enc_single / 250**2
mu_single = g_obs_phi(g_single) / g_single
print(f"    M(<250) = {M_enc_single:.2e}, g/g† = {g_single/g_dag:.4f}, μ = {mu_single:.2f}")

print(f"\n  Two subclusters (merger geometry):")
# Main: NFW with M=4e13, R200=1000, c=3
M1 = nfw_mass(200, 4e13, 3, 1000)
g1 = G * M1 / 200**2
mu1 = g_obs_phi(g1) / g1
# Bullet: NFW with M=2e13, R200=800, c=4
M2 = nfw_mass(150, 2e13, 4, 800)
g2 = G * M2 / 150**2
mu2 = g_obs_phi(g2) / g2

M_eff_merger = mu1*M1 + mu2*M2
M_bar_merger = M1 + M2
mu_eff_merger = M_eff_merger / M_bar_merger

print(f"    Main:   M(<200) = {M1:.2e}, g/g† = {g1/g_dag:.4f}, μ = {mu1:.2f}")
print(f"    Bullet: M(<150) = {M2:.2e}, g/g† = {g2/g_dag:.4f}, μ = {mu2:.2f}")
print(f"    Combined: M_eff = {M_eff_merger:.2e}, μ_eff = {mu_eff_merger:.2f}")
print(f"    vs single halo: μ = {mu_single:.2f}")
print(f"    Geometry bonus: ×{mu_eff_merger/mu_single:.2f}")

# Compare with observed
M_obs_core = 2.2e14
print(f"\n    M_ECT(merger) = {M_eff_merger:.2e}")
print(f"    M_obs(core)   = {M_obs_core:.2e}")
print(f"    Ratio         = {M_eff_merger/M_obs_core:.2f}")
print(f"    → ECT explains {M_eff_merger/M_obs_core*100:.0f}% (merger geometry)")

print(f"\n{'═' * 70}")
print("FINAL HONEST SUMMARY")
print(f"{'═' * 70}")
print(f"""
ECT PREDICTS (from φ-equation alone, no extra components):

  Bullet (250 kpc):
    Spherical:        M_ECT/M_obs ≈ 9% 
    Merger geometry:  M_ECT/M_obs ≈ {M_eff_merger/M_obs_core*100:.0f}%
    
  The φ-branch explains ~{M_eff_merger/M_obs_core*100:.0f}% at core scales, 
  ~23% at R_200 scales.
  
  The remaining ~{100-M_eff_merger/M_obs_core*100:.0f}% is an HONEST DEFICIT of ECT.
  
  Possible resolutions (NOT included in this calculation):
    - Environmental g† modulation (untested)
    - Gravitational slip (not derived)
    - Non-equilibrium φ-dynamics (not computed)
    
  What is NOT acceptable:
    - Adding M_cond,coll as a free parameter (phenomenology, not ECT)
    - Claiming "approximation error" without computing the correction
    
  STATUS: Bullet Cluster is an OPEN PROBLEM in ECT.
  The φ-branch gives the right morphology (offset) but not
  the full lensing amplitude. This is honest.
""")
