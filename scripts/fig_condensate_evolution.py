#!/usr/bin/env python3
"""
Generate schematic condensate evolution figure for §15.2.
Shows the three-stage picture:
  (i)  Ordering stage: phi grows from deep negative
  (ii) Stabilisation: phi approaches near-constant (BBN constraint)
  (iii) Late-time slow drift

Four panels:
  (a) phi_b(z) — condensate amplitude variable
  (b) u/u_infty = exp(beta*phi) — condensate amplitude ratio
  (c) G_eff/G_N = exp(-beta*phi) — effective gravitational coupling
  (d) w_phi(z) — effective equation of state

Both Scenario A and Scenario B shown where applicable.
Grayscale, 300 dpi, publication quality.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.size'] = 11
rcParams['axes.labelsize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['figure.dpi'] = 300

# ── Model parameters ──
beta = 0.8
z_max = 1e4  # extend to high z for full picture
z_arr = np.logspace(-2, np.log10(z_max), 2000)

# ── Schematic phi_b(z) ──
# Three stages:
#   z > z_ord ~ 1e3: ordering stage, phi rises from deep negative
#   z_stab ~ 100 < z < z_ord: stabilisation, phi ~ const
#   z < z_stab: late-time slow drift

z_ord = 2000   # ordering scale
z_stab = 50    # stabilisation complete
phi_early = -3.0   # deep negative at ordering
phi_stab = -0.05   # stabilised value (near zero but slightly negative)
phi_0_A = -0.10    # present-day value, Scenario A
phi_0_B = -0.15    # Scenario B: drifts further

def phi_model_A(z):
    """Scenario A: ordering -> stabilisation -> slow drift -> screened"""
    # Ordering rise: tanh from phi_early to phi_stab
    f_ord = 0.5 * (1 + np.tanh((np.log10(z_ord) - np.log10(z+1)) / 0.4))
    phi_ord = phi_early + (phi_stab - phi_early) * f_ord
    # Late-time drift: small additional negative shift at low z
    drift = phi_0_A - phi_stab
    f_late = np.exp(-z / z_stab)
    return phi_ord + drift * f_late

def phi_model_B(z):
    """Scenario B: like A but drift continues, phi -> more negative"""
    phi_A = phi_model_A(z)
    # Additional drift at late times
    extra_drift = (phi_0_B - phi_0_A) * np.exp(-z / z_stab)
    return phi_A + extra_drift

phi_A = phi_model_A(z_arr)
phi_B = phi_model_B(z_arr)

# Derived quantities
u_ratio_A = np.exp(beta * phi_A)
u_ratio_B = np.exp(beta * phi_B)
G_ratio_A = np.exp(-beta * phi_A)
G_ratio_B = np.exp(-beta * phi_B)

# Equation of state: w = (K - U)/(K + U)
# For slow-drift: K ~ 0.5 * omega * dphi/dt^2, U ~ U(phi)
# Schematic: w -> -1 at high z (frozen), w > -1 at late times
# Use w = -1 + delta_w * exp(-z/z_drift)
z_drift = 20
delta_w_A = 0.15
delta_w_B = 0.25
w_A = -1 + delta_w_A * np.exp(-z_arr / z_drift)
w_B = -1 + delta_w_B * np.exp(-z_arr / z_drift)

# ── Figure ──
fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))

# Shading for three regimes
def shade_regimes(ax, ymin, ymax):
    ax.axvspan(z_stab, z_ord, alpha=0.08, color='gray', zorder=0)
    ax.axvspan(z_ord, z_max, alpha=0.15, color='gray', zorder=0)

# Panel (a): phi_b(z)
ax = axes[0, 0]
shade_regimes(ax, -3.5, 0.5)
ax.semilogx(z_arr, phi_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, phi_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$\phi_b(z)$')
ax.set_title(r'(a) Condensate amplitude variable $\phi_b$')
ax.set_xlim(0.01, z_max)
ax.set_ylim(-3.5, 0.5)
ax.axhline(0, color='gray', lw=0.5, ls=':')
ax.legend(loc='lower right')
# Annotations
ax.annotate('(iii) slow\ndrift', xy=(0.5, 0.3), fontsize=8,
            ha='center', color='gray',
            xycoords='axes fraction')
ax.annotate('(ii) stabilisation', xy=(0.55, 0.7), fontsize=8,
            ha='center', color='gray',
            xycoords='axes fraction')
ax.annotate('(i) ordering', xy=(0.88, 0.3), fontsize=8,
            ha='center', color='gray',
            xycoords='axes fraction')

# Panel (b): u/u_infty
ax = axes[0, 1]
shade_regimes(ax, 0, 1.1)
ax.semilogx(z_arr, u_ratio_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, u_ratio_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$u/u_\infty = e^{\beta\phi}$')
ax.set_title(r'(b) Condensate amplitude ratio')
ax.set_xlim(0.01, z_max)
ax.set_ylim(0, 1.1)
ax.axhline(1, color='gray', lw=0.5, ls=':')
ax.legend(loc='lower right')

# Panel (c): G_eff/G_N
ax = axes[1, 0]
shade_regimes(ax, 0.8, 12)
ax.semilogx(z_arr, G_ratio_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, G_ratio_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$G_{\rm eff}/G_N = e^{-\beta\phi}$')
ax.set_title(r'(c) Effective gravitational coupling')
ax.set_xlim(0.01, z_max)
ax.set_ylim(0.8, 12)
ax.axhline(1, color='gray', lw=0.5, ls=':')
ax.legend(loc='upper right')
ax.set_yscale('log')

# Panel (d): w_phi(z)
ax = axes[1, 1]
shade_regimes(ax, -1.05, -0.7)
ax.semilogx(z_arr, w_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, w_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$w_\phi(z)$')
ax.set_title(r'(d) Effective equation of state')
ax.set_xlim(0.01, z_max)
ax.set_ylim(-1.05, -0.7)
ax.axhline(-1, color='gray', lw=0.5, ls=':', label=r'$\Lambda$CDM ($w=-1$)')
ax.legend(loc='upper right')

plt.tight_layout()
outpath = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/ect_condensate_evolution_schematic_bw.pdf'
plt.savefig(outpath, dpi=300, bbox_inches='tight')
print(f'Saved: {outpath}')
plt.close()
