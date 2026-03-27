#!/usr/bin/env python3
"""
Condensate evolution over cosmic time (Gyr).
Complementary to the z-based fig_condensate_evolution.py.

Shows:
  (a) phi_b(t) and u/u_infty(t)  — condensate amplitude
  (b) G_eff(t)/G_N               — effective gravitational coupling
  
With:
  - Three-stage shading (ordering, stabilisation, slow drift)
  - Key epoch labels (BBN, recombination, today)
  - Scenarios A and B for the future
  - Grayscale, 300 dpi, publication quality

Time mapping: approximate ΛCDM background for t(z) conversion.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.integrate import quad

rcParams['font.size'] = 11
rcParams['axes.labelsize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['figure.dpi'] = 300

# ── Cosmological parameters (Planck 2018) ──
H0 = 67.4  # km/s/Mpc
h = H0 / 100.0
Omega_m = 0.315
Omega_r = 9.1e-5
Omega_L = 1 - Omega_m - Omega_r
H0_s = H0 * 1e3 / (3.0856776e22)  # H0 in s^-1
Gyr = 3.1557e16  # seconds in 1 Gyr

def E(z):
    return np.sqrt(Omega_r*(1+z)**4 + Omega_m*(1+z)**3 + Omega_L)

def t_of_z(z):
    """Cosmic time since Big Bang (in Gyr) at redshift z."""
    integrand = lambda zp: 1.0 / ((1+zp) * E(zp))
    result, _ = quad(integrand, z, np.inf, limit=200)
    return result / (H0_s * Gyr)

# ── Build time array ──
z_arr = np.logspace(np.log10(3e4), -2, 500)  # z from 30000 to 0.01
z_future = np.array([0.0])  # today

t_arr = np.array([t_of_z(z) for z in z_arr])
t_today = t_of_z(0)

# Add future points (extend past today)
t_future = np.linspace(t_today, 50, 100)  # up to 50 Gyr

# ── Model parameters ──
beta = 0.8

# Key times
t_ordering = 1e-6  # Gyr (ordering transition)
t_bbn = 0.003      # Gyr (~3 min after BB)
t_recomb = 0.38    # Gyr (~380 kyr)
t_eq = 0.05        # Gyr (matter-radiation equality)

# ── Schematic phi_b(t) ──
# Stage (i):   t < 0.001 Gyr — ordering, phi from -3 toward ~-0.05
# Stage (ii):  0.001 < t < 0.5 Gyr — stabilisation near phi ~ -0.05
# Stage (iii): t > 0.5 Gyr — slow drift toward 0 (Scenario A) or further negative (B)

def phi_of_t_A(t):
    """Scenario A: ordering -> stabilisation -> drift toward 0."""
    # Ordering rise
    t_rise = 0.0005  # characteristic ordering time (Gyr)
    phi_deep = -3.0
    phi_stab = -0.05
    f_ord = 1.0 / (1.0 + np.exp(-(np.log10(t+1e-10) - np.log10(t_rise)) / 0.3))
    phi_base = phi_deep + (phi_stab - phi_deep) * f_ord
    # Late drift toward 0
    phi_0 = -0.10  # present value
    t_drift = 3.0  # drift timescale (Gyr)
    drift = (phi_0 - phi_stab) * (1.0 / (1.0 + np.exp(-(np.log10(t+1e-10) - np.log10(t_drift)) / 0.25)))
    phi = phi_base + drift
    # Future: approach 0
    f_future = np.where(t > t_today, 
                        phi * np.exp(-(t - t_today) / 30.0),
                        phi)
    return np.where(t > t_today, f_future, phi)

def phi_of_t_B(t):
    """Scenario B: like A but continues drifting negative in the future."""
    phi_A = phi_of_t_A(t)
    # In the future, drift continues
    extra = np.where(t > t_today, 
                     -0.003 * (t - t_today),
                     0.0)
    return phi_A + extra

# Build full time array (past + future)
t_full = np.sort(np.concatenate([t_arr, t_future]))
t_full = t_full[t_full > 1e-8]  # avoid log(0)

phi_A = np.array([phi_of_t_A(t) for t in t_full])
phi_B = np.array([phi_of_t_B(t) for t in t_full])

u_ratio_A = np.exp(beta * phi_A)
u_ratio_B = np.exp(beta * phi_B)
G_ratio_A = np.exp(-beta * phi_A)
G_ratio_B = np.exp(-beta * phi_B)

# ── Figure ──
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

# Shading for three stages
for ax in [ax1, ax2]:
    ax.axvspan(1e-8, t_bbn, alpha=0.15, color='gray', zorder=0)    # ordering
    ax.axvspan(t_bbn, t_recomb, alpha=0.08, color='gray', zorder=0) # stabilisation
    ax.axvline(t_today, color='gray', ls=':', lw=0.8, zorder=0)

# Panel (a): phi_b and u/u_infty (twin y-axis)
ax1.semilogx(t_full, phi_A, 'k-', lw=2, label=r'$\phi_b$ — Scenario A')
ax1.semilogx(t_full, phi_B, 'k--', lw=1.5, label=r'$\phi_b$ — Scenario B')
ax1.set_ylabel(r'$\phi_b$', fontsize=13)
ax1.set_ylim(-3.5, 0.5)
ax1.axhline(0, color='gray', lw=0.5, ls=':')
ax1.legend(loc='lower right', fontsize=9)
ax1.set_title(r'(a) Condensate amplitude variable $\phi_b$ and ratio $u/u_\infty$')

# Twin axis for u/u_infty
ax1t = ax1.twinx()
ax1t.semilogx(t_full, u_ratio_A, color='0.5', ls='-', lw=1.2, alpha=0.7)
ax1t.semilogx(t_full, u_ratio_B, color='0.5', ls='--', lw=1.0, alpha=0.7)
ax1t.set_ylabel(r'$u/u_\infty = e^{\beta\phi}$', color='0.5', fontsize=11)
ax1t.set_ylim(0, 1.15)
ax1t.tick_params(axis='y', colors='0.5')

# Epoch labels on ax1
ax1.annotate('(i)\nordering', xy=(3e-5, 0.3), fontsize=8, ha='center', color='0.4')
ax1.annotate('(ii)\nstabilisation', xy=(0.03, 0.3), fontsize=8, ha='center', color='0.4')
ax1.annotate('(iii) slow drift', xy=(5, -0.5), fontsize=8, ha='center', color='0.4')
ax1.annotate('today', xy=(t_today, 0.35), fontsize=7, ha='center', color='0.4')
ax1.annotate('BBN', xy=(t_bbn, 0.35), fontsize=7, ha='center', color='0.4')

# Panel (b): G_eff/G_N
ax2.loglog(t_full, G_ratio_A, 'k-', lw=2, label='Scenario A')
ax2.loglog(t_full, G_ratio_B, 'k--', lw=1.5, label='Scenario B')
ax2.set_xlabel('Cosmic time $t$ [Gyr]', fontsize=12)
ax2.set_ylabel(r'$G_{\rm eff}/G_N = e^{-\beta\phi}$', fontsize=13)
ax2.set_ylim(0.8, 15)
ax2.axhline(1, color='gray', lw=0.5, ls=':')
ax2.legend(loc='upper right', fontsize=9)
ax2.set_title(r'(b) Effective gravitational coupling')
ax2.set_xlim(1e-6, 50)

# Epoch markers on ax2
for t_ep, lab in [(t_bbn, 'BBN'), (t_recomb, 'Recombination'), (t_today, 'Today')]:
    ax2.annotate(lab, xy=(t_ep, 12), fontsize=7, ha='center', color='0.4',
                rotation=90 if lab != 'Today' else 0)

plt.tight_layout()
outpath = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/ect_condensate_evolution_time_bw.pdf'
plt.savefig(outpath, dpi=300, bbox_inches='tight')
print(f'Saved: {outpath}')
plt.close()
