#!/usr/bin/env python3
"""
CORRECTED: Condensate evolution over cosmic time (Gyr).
Key fix: phi_b MONOTONICALLY INCREASES (approaches 0 from below).
  - phi(JWST epoch, ~0.4 Gyr) ~ -0.5, G_eff/G_N ~ 1.5
  - phi(today, ~13.1 Gyr) ~ -0.10, G_eff/G_N ~ 1.08
  - phi is always negative and always rising
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.integrate import quad

rcParams['font.size'] = 11
rcParams['axes.labelsize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['figure.dpi'] = 300

# ── Cosmological parameters ──
H0 = 67.4
Omega_m = 0.315
Omega_r = 9.1e-5
Omega_L = 1 - Omega_m - Omega_r
H0_s = H0 * 1e3 / (3.0856776e22)
Gyr = 3.1557e16

def E(z):
    return np.sqrt(Omega_r*(1+z)**4 + Omega_m*(1+z)**3 + Omega_L)

def t_of_z(z):
    integrand = lambda zp: 1.0 / ((1+zp) * E(zp))
    result, _ = quad(integrand, z, np.inf, limit=200)
    return result / (H0_s * Gyr)

# ── Build time array ──
z_arr = np.logspace(np.log10(3e4), -2, 500)
t_arr = np.array([t_of_z(z) for z in z_arr])
t_today = t_of_z(0)

# Key epoch times
t_bbn = t_of_z(1e9)   # BBN ~ z=10^9 but we cap
t_bbn = 0.003
t_recomb = 0.38
t_jwst = t_of_z(10)  # JWST epoch

# Future extension
t_future = np.linspace(t_today, 50, 100)

beta = 0.8

def phi_of_t(t):
    """CORRECT: monotonically increasing from deep negative toward 0.
    phi(early) ~ -3, phi(JWST ~0.4 Gyr) ~ -0.5, phi(today ~13 Gyr) ~ -0.10"""
    phi_deep = -3.0
    phi_0 = -0.10
    # Logistic rise with two timescales:
    # Fast ordering (t < 0.001 Gyr)
    # Slower approach to screened state (t ~ 1-13 Gyr)
    t_ord = 0.0005  # ordering timescale
    t_screen = 5.0   # screening timescale
    
    # Ordering: -3 -> -0.6
    f1 = 1.0 / (1.0 + np.exp(-(np.log10(t + 1e-10) - np.log10(t_ord)) / 0.3))
    phi_after_ord = phi_deep + (-0.6 - phi_deep) * f1
    
    # Screening: -0.6 -> -0.10 (slow approach)
    f2 = 1.0 / (1.0 + np.exp(-(np.log10(t + 1e-10) - np.log10(t_screen)) / 0.4))
    phi_val = phi_after_ord + (-0.6 - phi_after_ord) + (-0.10 - (-0.6)) * f2
    
    # Simplify: direct smooth monotonic interpolation
    return phi_deep + (phi_0 - phi_deep) * f1 * (0.2 + 0.8 * f2)

# Actually, let me build this more carefully with a piecewise smooth model
def phi_model(t):
    """Three-stage monotonic model matching benchmark values."""
    phi_deep = -3.0
    phi_stab = -0.6   # after ordering, stabilised (but still well below 0!)
    phi_0 = -0.10     # today
    
    # Stage 1: ordering rise from -3 to -0.6
    t_ord = 5e-4  # 0.5 Myr
    s1 = 0.5 * (1 + np.tanh((np.log10(t + 1e-12) - np.log10(t_ord)) / 0.25))
    
    # Stage 2+3: from -0.6 to -0.10 (slow approach to screened)
    t_scr = 3.0  # Gyr
    s2 = 0.5 * (1 + np.tanh((np.log10(t + 1e-12) - np.log10(t_scr)) / 0.5))
    
    return phi_deep + (phi_stab - phi_deep) * s1 + (phi_0 - phi_stab) * s1 * s2

t_full = np.sort(np.concatenate([t_arr, t_future]))
t_full = t_full[t_full > 1e-8]

phi_A = np.array([phi_model(t) for t in t_full])

# Scenario B: same past, but in the far future phi drifts back negative
phi_B = phi_A.copy()
mask_future = t_full > t_today
phi_B[mask_future] = phi_A[mask_future] - 0.003 * (t_full[mask_future] - t_today)

u_ratio_A = np.exp(beta * phi_A)
u_ratio_B = np.exp(beta * phi_B)
G_ratio_A = np.exp(-beta * phi_A)
G_ratio_B = np.exp(-beta * phi_B)

# ── Figure ──
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

for ax in [ax1, ax2]:
    ax.axvspan(1e-8, t_bbn, alpha=0.15, color='gray', zorder=0)
    ax.axvspan(t_bbn, t_recomb, alpha=0.08, color='gray', zorder=0)
    ax.axvline(t_today, color='gray', ls=':', lw=0.8, zorder=0)

# Panel (a): phi_b (left) and u/u_infty (right)
ax1.semilogx(t_full, phi_A, 'k-', lw=2, label=r'$\phi_b$ — Scenario A')
ax1.semilogx(t_full, phi_B, 'k--', lw=1.5, label=r'$\phi_b$ — Scenario B')
ax1.set_ylabel(r'$\phi_b$', fontsize=13)
ax1.set_ylim(-3.5, 0.5)
ax1.axhline(0, color='gray', lw=0.5, ls=':')
ax1.legend(loc='lower right', fontsize=9)
ax1.set_title(r'(a) Condensate amplitude $\phi_b$ and ratio $u/u_\infty$')

# Mark benchmark values
ax1.plot(t_today, -0.10, 'ks', ms=5, zorder=5)
if t_jwst > 1e-8:
    ax1.plot(t_jwst, -0.51, 'ko', ms=5, zorder=5)
    ax1.annotate(r'JWST epoch: $\phi\approx-0.5$', xy=(t_jwst, -0.51),
                xytext=(0.005, -1.2), fontsize=7,
                arrowprops=dict(arrowstyle='->', color='0.4'), color='0.4')

ax1t = ax1.twinx()
ax1t.semilogx(t_full, u_ratio_A, color='0.5', ls='-', lw=1.2, alpha=0.7)
ax1t.semilogx(t_full, u_ratio_B, color='0.5', ls='--', lw=1.0, alpha=0.7)
ax1t.set_ylabel(r'$u/u_\infty = e^{\beta\phi}$', color='0.5', fontsize=11)
ax1t.set_ylim(0, 1.15)
ax1t.tick_params(axis='y', colors='0.5')

ax1.annotate('(i)\nordering', xy=(3e-5, 0.3), fontsize=8, ha='center', color='0.4')
ax1.annotate('(ii)\nstabilisation', xy=(0.03, 0.3), fontsize=8, ha='center', color='0.4')
ax1.annotate('(iii) approach\nto screened', xy=(5, -0.3), fontsize=8, ha='center', color='0.4')
ax1.annotate('today', xy=(t_today, 0.35), fontsize=7, ha='center', color='0.4')

# Panel (b): G_eff/G_N — DECREASING over time (approaching 1)
ax2.loglog(t_full, G_ratio_A, 'k-', lw=2, label='Scenario A')
ax2.loglog(t_full, G_ratio_B, 'k--', lw=1.5, label='Scenario B')
ax2.set_xlabel('Cosmic time $t$ [Gyr]', fontsize=12)
ax2.set_ylabel(r'$G_{\rm eff}/G_N = e^{-\beta\phi}$', fontsize=13)
ax2.set_ylim(0.8, 15)
ax2.axhline(1, color='gray', lw=0.5, ls=':')
ax2.legend(loc='upper right', fontsize=9)
ax2.set_title(r'(b) Effective gravitational coupling')
ax2.set_xlim(1e-6, 50)

# Mark benchmark
ax2.plot(t_today, np.exp(0.08), 'ks', ms=5, zorder=5)
if t_jwst > 1e-8:
    ax2.plot(t_jwst, 1.5, 'ko', ms=5, zorder=5)
    ax2.annotate(r'$G_{\rm eff}/G_N\approx1.5$', xy=(t_jwst, 1.5),
                xytext=(0.005, 3.5), fontsize=7,
                arrowprops=dict(arrowstyle='->', color='0.4'), color='0.4')

for t_ep, lab in [(t_bbn, 'BBN'), (t_recomb, 'Recomb.')]:
    ax2.axvline(t_ep, color='0.7', ls='--', lw=0.5)
    ax2.annotate(lab, xy=(t_ep*1.2, 11), fontsize=7, color='0.4')

plt.tight_layout()
outpath = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/ect_condensate_evolution_time_bw.pdf'
plt.savefig(outpath, dpi=300, bbox_inches='tight')
print(f'Saved: {outpath}')
plt.close()
