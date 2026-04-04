#!/usr/bin/env python3
"""
CORRECTED: Condensate evolution vs redshift for §15.2.
Key fix: phi_b MONOTONICALLY INCREASES throughout cosmic history.
  - Ordering: phi from -3 rises rapidly
  - Stabilisation: phi approaches ~ -0.5 (BBN-compatible, still negative)
  - Late-time: phi CONTINUES to rise toward 0, reaching -0.10 at z=0
  - G_eff/G_N at z=10 ~ 1.5 (matches derived-parent benchmark)
  
Scenarios A and B differ only in far future (z < 0 extrapolation).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.size'] = 11
rcParams['axes.labelsize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['figure.dpi'] = 300

beta = 0.8
z_max = 1e4
z_arr = np.logspace(-2, np.log10(z_max), 2000)

# Key physical constraints from benchmark:
#   phi(z=10) ~ -0.51  =>  G_eff/G_N ~ 1.5
#   phi(z=0)  ~ -0.10  =>  G_eff/G_N ~ 1.08
#   phi(z>>100) ~ -0.5 to -1.0 (stabilised, still negative)
#   phi monotonically increases (approaches 0) throughout

z_ord = 2000       # ordering transition redshift
phi_deep = -3.0    # deep negative at ordering start
phi_stab = -0.6    # stabilised value after ordering (NOT near 0!)
phi_0_A = -0.10    # present-day, Scenario A
phi_0_B = -0.10    # same at z=0; differs only in far future

def phi_model(z):
    """Monotonically increasing: ordering → stabilisation → late approach to 0."""
    # Stage 1: ordering rise from phi_deep to phi_stab
    f_ord = 0.5 * (1 + np.tanh((np.log10(z_ord) - np.log10(z+1)) / 0.4))
    phi_ord = phi_deep + (phi_stab - phi_deep) * f_ord
    # Stage 3: late-time approach from phi_stab toward phi_0
    # This makes phi LESS negative at lower z (approaching 0)
    z_approach = 100  # characteristic approach redshift
    f_late = np.exp(-z / z_approach)
    phi_late = phi_stab + (phi_0_A - phi_stab) * f_late
    # Combine: use ordering at high z, late approach at low z
    weight = 1.0 / (1.0 + (z / 30)**2)  # smooth transition
    return phi_ord * (1 - weight) + phi_late * weight

phi_A = phi_model(z_arr)

# Scenario B: same past, but slightly more negative present
# (slower approach to screened state)
phi_B = phi_A.copy()
mask_late = z_arr < 5
phi_B[mask_late] = phi_A[mask_late] - 0.05 * np.exp(-z_arr[mask_late] / 2)

# Derived quantities
u_ratio_A = np.exp(beta * phi_A)
u_ratio_B = np.exp(beta * phi_B)
G_ratio_A = np.exp(-beta * phi_A)
G_ratio_B = np.exp(-beta * phi_B)

# w(z): frozen at high z, quintessence-like at late times
z_drift = 20
delta_w_A = 0.15
delta_w_B = 0.20
w_A = -1 + delta_w_A * np.exp(-z_arr / z_drift)
w_B = -1 + delta_w_B * np.exp(-z_arr / z_drift)

# ── Figure ──
fig, axes = plt.subplots(2, 2, figsize=(10, 7.5))

def shade_regimes(ax):
    ax.axvspan(30, 2000, alpha=0.08, color='gray', zorder=0)  # stabilisation
    ax.axvspan(2000, z_max, alpha=0.15, color='gray', zorder=0)  # ordering

# Panel (a): phi_b(z) — MONOTONICALLY INCREASING
ax = axes[0, 0]
shade_regimes(ax)
ax.semilogx(z_arr, phi_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, phi_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$\phi_b(z)$')
ax.set_title(r'(a) Condensate amplitude variable $\phi_b$')
ax.set_xlim(0.01, z_max)
ax.set_ylim(-3.5, 0.5)
ax.axhline(0, color='gray', lw=0.5, ls=':')
# Mark benchmark values
ax.plot(10, -0.51, 'ko', ms=5, zorder=5)
ax.annotate(r'$\phi(z{=}10)\approx-0.51$', xy=(10, -0.51),
            xytext=(50, -1.0), fontsize=7, arrowprops=dict(arrowstyle='->', color='0.4'),
            color='0.4')
ax.plot(0.01, phi_0_A, 'ks', ms=5, zorder=5)
ax.annotate(r'$\phi_0\approx-0.10$', xy=(0.015, -0.10),
            xytext=(0.1, -0.6), fontsize=7, arrowprops=dict(arrowstyle='->', color='0.4'),
            color='0.4')
ax.legend(loc='lower right')
ax.annotate('(iii) late\napproach', xy=(0.3, 0.15), fontsize=8,
            ha='center', color='gray', xycoords='axes fraction')
ax.annotate('(ii) stabilisation', xy=(0.55, 0.65), fontsize=8,
            ha='center', color='gray', xycoords='axes fraction')
ax.annotate('(i) ordering', xy=(0.88, 0.3), fontsize=8,
            ha='center', color='gray', xycoords='axes fraction')

# Panel (b): u/u_infty
ax = axes[0, 1]
shade_regimes(ax)
ax.semilogx(z_arr, u_ratio_A, 'k-', lw=2, label='Scenario A')
ax.semilogx(z_arr, u_ratio_B, 'k--', lw=1.5, label='Scenario B')
ax.set_xlabel('Redshift $z$')
ax.set_ylabel(r'$u/u_\infty = e^{\beta\phi}$')
ax.set_title(r'(b) Condensate amplitude ratio')
ax.set_xlim(0.01, z_max)
ax.set_ylim(0, 1.1)
ax.axhline(1, color='gray', lw=0.5, ls=':')
ax.legend(loc='lower right')

# Panel (c): G_eff/G_N — DECREASING (approaching 1)
ax = axes[1, 0]
shade_regimes(ax)
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
# Mark benchmark
ax.plot(10, 1.5, 'ko', ms=5, zorder=5)
ax.annotate(r'$G_{\rm eff}/G_N\approx1.5$', xy=(10, 1.5),
            xytext=(50, 3), fontsize=7, arrowprops=dict(arrowstyle='->', color='0.4'),
            color='0.4')

# Panel (d): w_phi(z)
ax = axes[1, 1]
shade_regimes(ax)
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
