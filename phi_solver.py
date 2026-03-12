#!/usr/bin/env python3
"""
ECT φ-equation solver for galaxy rotation curves.
VERSION 2: CORRECT UNITS.

Core equation (spherical AQUAL from Y^{3/2} critical branch):
    μ(g_obs/g†) · g_obs = g_N(r)

where μ(x) = x/√(1+x²)  (standard interpolating function)
      g† = g†(φ_env) = environment-dependent threshold

UNITS: G in (km/s)² kpc/M☉, g† in (km/s)²/kpc
       a₀ = 1.2e-10 m/s² = 3703 (km/s)²/kpc  [CORRECT]
"""
import numpy as np
from scipy.special import i0, i1, k0, k1

G = 4.302e-6    # (km/s)² kpc/M☉
g_dag0 = 3703.0 # (km/s)²/kpc = 1.2e-10 m/s² [CORRECT CONVERSION]
conv_si = 1e6 / 3.086e19  # (km/s)²/kpc → m/s²

def mu_phi(x):
    """μ(x) = x/√(1+x²). From Y^{3/2} critical branch.
    x ≪ 1: μ→x (deep-MOND, nonlinear φ-branch)
    x ≫ 1: μ→1 (Newtonian, screened)"""
    return x / np.sqrt(1 + x**2)

def solve_g_obs(g_N, g_dag):
    """Solve μ(g/g†)·g = g_N algebraically.
    g⁴ - g_N²·g² - g_N²·g†² = 0
    g² = (g_N² + √(g_N⁴ + 4·g_N²·g†²)) / 2"""
    g_N = np.atleast_1d(np.float64(g_N))
    disc = g_N**4 + 4 * g_N**2 * g_dag**2
    g2 = (g_N**2 + np.sqrt(disc)) / 2
    return np.sqrt(np.maximum(g2, 0))

def g_dagger_env(phi_env, gamma=0.3):
    """g†(φ_env) = g†₀ · exp(γ·φ_env).
    φ_env > 0: denser → higher g† → more Newtonian
    φ_env < 0: void → lower g† → deeper MOND
    φ_env = 0: cosmological mean (g† = g†₀ ≈ a₀)"""
    return g_dag0 * np.exp(gamma * phi_env)

# ========== Baryonic models ==========
def v_freeman(r, Md, Rd):
    y = np.clip(r/(2*Rd), 1e-10, 50)
    return np.sqrt(np.clip(2*G*Md/Rd * y**2*(i0(y)*k0(y)-i1(y)*k1(y)), 0, None))

def v_hernquist(r, Mb, ab):
    if Mb <= 0: return np.zeros_like(r)
    return np.sqrt(G*Mb*r/(r+ab)**2)

def g_newtonian(r, Md, Rd, Mb=0, ab=1.0):
    """Baryonic Newtonian acceleration = v²_bar/r"""
    vd2 = v_freeman(r, Md, Rd)**2
    vb2 = v_hernquist(r, Mb, ab)**2
    return (vd2 + vb2) / r

# ========== MAIN φ-SOLVER ==========
def v_phi(r, Md, Rd, phi_env, Mb=0, ab=1.0, gamma=0.3):
    """Rotation curve from φ-AQUAL equation.
    
    NEW CALCULATION — not the legacy G_eff proxy.
    
    Steps:
    1. Compute g_N(r) from baryonic profile
    2. Compute g†(φ_env) from environment
    3. Solve μ(g/g†)·g = g_N algebraically
    4. v(r) = √(g_obs · r)
    """
    gN = g_newtonian(r, Md, Rd, Mb, ab)
    gdag = g_dagger_env(phi_env, gamma)
    g_obs = solve_g_obs(gN, gdag)
    return np.sqrt(np.clip(g_obs * r, 0, None))

def v_baryon(r, Md, Rd, Mb=0, ab=1.0):
    return np.sqrt(v_freeman(r, Md, Rd)**2 + v_hernquist(r, Mb, ab)**2)

# ========== φ-RAR ==========
def phi_rar_si(g_bar_si, phi_env=0.0, gamma=0.3):
    """RAR from φ-AQUAL. Input/output in m/s²."""
    gdag_si = 1.2e-10 * np.exp(gamma * phi_env)
    gb = np.atleast_1d(np.float64(g_bar_si))
    disc = gb**4 + 4*gb**2*gdag_si**2
    g2 = (gb**2 + np.sqrt(disc)) / 2
    return np.sqrt(np.maximum(g2, 0))

if __name__ == '__main__':
    r = np.linspace(1, 30, 300)
    v = v_phi(r, 5.5e10, 2.6, phi_env=0.0, Mb=1e10, ab=0.5)
    print(f"MW (φ-solver, φ_env=0):  v(8)={np.interp(8,r,v):.0f}, v(15)={np.interp(15,r,v):.0f}, v(25)={np.interp(25,r,v):.0f} km/s")
    
    vb = v_baryon(r, 5.5e10, 2.6, 1e10, 0.5)
    print(f"MW (baryons only):       v(8)={np.interp(8,r,vb):.0f}, v(15)={np.interp(15,r,vb):.0f}, v(25)={np.interp(25,r,vb):.0f} km/s")
    print(f"MW observed (Eilers+19): v(8)≈230, v(15)≈225, v(25)≈218 km/s")
    print(f"g†₀ = {g_dag0} (km/s)²/kpc = {g_dag0*conv_si:.2e} m/s²")
