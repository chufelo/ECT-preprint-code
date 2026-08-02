#!/usr/bin/env python3
"""
Conditional HRC-0 force-law dimensionality benchmark d_force(r).

Panel (a): d_force(r) for three synthetic point-source mass benchmarks.
Panel (b): Universal d_force(x) curve with individual radial points
           as an analytic relation only; generated profile points are not data and are not plotted.

The displayed formula d_force(x) = 1 + 2(1+x²)/(2+x²) is the
conditional HRC-0 point-source relation after the separately declared
identity gravity bridge.  It is a Level-C synthetic benchmark, not a
derivation of that bridge, of a_M, or of a full galaxy field solution.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 9,
    'axes.linewidth': 0.6,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'xtick.major.size': 4, 'ytick.major.size': 4,
    'xtick.minor.size': 2, 'ytick.minor.size': 2,
    'figure.dpi': 220,
})

G_SI  = 6.674e-11; M_sun = 1.989e30; kpc_m = 3.086e19; Mpc_m = 3.086e22
A_M0 = 1.0824013602e-10
G_kpc = 4.302e-6  # (km/s)^2 kpc / M_sun

def d_force_analytic(x):
    return 1 + 2*(1 + x**2) / (2 + x**2)

def x_of_r(r_kpc, M_kg):
    r_m = r_kpc * kpc_m
    g_N = G_SI * M_kg / r_m**2
    g_obs2 = (g_N**2 + np.sqrt(g_N**4 + 4*g_N**2*A_M0**2)) / 2
    return np.sqrt(g_obs2) / A_M0

def r_star(M_kg):
    return np.sqrt(G_SI * M_kg / A_M0) / kpc_m

# Extended-profile / galaxy-named point generation removed in Round 58:
# applying the point-source d_force formula to M_enc(r) omitted the
# profile-slope factor p_N(r), so those points were not valid data.

# ── Three synthetic point-source mass benchmarks for panel (a) ──
gal_panel_a = [
    (r'Dwarf-mass point source ($10^8\,M_\odot$)',             1e8*M_sun,  '--', '#009E73', 1.4),
    (r'MW-mass point source ($5{\times}10^{10}\,M_\odot$)',     5e10*M_sun, '-',  '#0072B2', 2.0),
    (r'Giant-mass point source ($5{\times}10^{11}\,M_\odot$)',  5e11*M_sun, '-.', '#D55E00', 1.4),
]

# ── FIGURE ───────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5),
                                gridspec_kw={'width_ratios': [3, 2]})

# ── Panel (a): d_force(r) ────────────────────────────────────────
ax = ax1
for dv in [3, 2]: ax.axhline(dv, color='0.82', ls=':', lw=0.7, zorder=0)

for name, M, ls, col, lw in gal_panel_a:
    rs = r_star(M)
    r_kpc = np.logspace(-0.3, 3.5, 400)
    x = np.array([x_of_r(r, M) for r in r_kpc])
    d = d_force_analytic(x)
    r_Mpc = r_kpc / 1000
    R_iso = 300 if M < 1e9*M_sun else (2000 if M < 1e11*M_sun else 3000)
    mask_ok = r_kpc <= R_iso
    mask_beyond = r_kpc > R_iso
    ax.plot(r_Mpc[mask_ok], d[mask_ok], ls=ls, color=col, lw=lw, zorder=3, label=name)
    if np.any(mask_beyond):
        ax.plot(r_Mpc[mask_beyond], d[mask_beyond], ls=ls, color=col, lw=lw*0.4, alpha=0.25, zorder=2)
    d_star = d_force_analytic(x_of_r(rs, M))
    ax.plot(rs/1000, d_star, 'o', color=col, ms=5, zorder=4)

ax.axvline(3, color='0.70', ls='-', lw=0.5, zorder=0)
ax.text(2.8, 2.18, 'single-source scope limit', fontsize=6.5, color='0.50', ha='right', va='center', rotation=90, style='italic')
ax.fill_between([3, 600], [2, 0], [2, 2], color='0.80', alpha=0.15, zorder=0)
ax.text(30, 1.3, 'Cosmic-web morphology:\noutside this conditional\nsingle-profile diagnostic',
        fontsize=7, color='0.50', ha='center', style='italic',
        bbox=dict(fc='white', ec='0.75', lw=0.5, pad=3, alpha=0.9))

ax.annotate('high acceleration:\n$g\\propto 1/r^2$', xy=(0.001, 2.99), xytext=(0.0006, 2.55),
            fontsize=7, color='0.35', arrowprops=dict(arrowstyle='->', color='0.45', lw=0.7), ha='center')
ax.annotate('conditional HRC-0 $\\mu_{g,0}$ branch:' + '\n$g\\propto 1/r$\n$\\Rightarrow v_{\\rm flat}$',
            xy=(0.3, 2.01), xytext=(0.13, 1.72), fontsize=7, color='0.25',
            arrowprops=dict(arrowstyle='->', color='0.35', lw=0.7), ha='center')
rs_MW = r_star(5e10*M_sun)
d_rs_MW = d_force_analytic(x_of_r(rs_MW, 5e10*M_sun))
ax.annotate(fr'$r_*\ (g_N=a_M)\approx {rs_MW:.0f}$ kpc', xy=(rs_MW/1000, d_rs_MW), xytext=(rs_MW/1000*5, 2.6),
            fontsize=6.5, color='0.30', arrowprops=dict(arrowstyle='->', color='0.40', lw=0.7), ha='center')

ax.text(0.02, 0.97, '(a)', transform=ax.transAxes, fontsize=11, va='top', fontweight='bold')
ax.set_xscale('log'); ax.set_xlim(3e-4, 600); ax.set_ylim(1.2, 3.15)
ax.set_xlabel('Scale $r$ [Mpc]', fontsize=10)
ax.set_ylabel(r'Force-law dimensionality $d_{\rm force}(r)$', fontsize=10)
ax.legend(loc='lower left', fontsize=7, framealpha=0.95, edgecolor='0.7', fancybox=False)
from matplotlib.ticker import LogLocator
ax.xaxis.set_minor_locator(LogLocator(subs='all', numticks=20))
ax.yaxis.set_minor_locator(plt.MultipleLocator(0.25))
ax.tick_params(which='both', top=True, right=True)

# ── Panel (b): analytic HRC-0 relation (no data overlay) ──────
ax = ax2
x_arr = np.logspace(-2, 3, 500)
d_arr = d_force_analytic(x_arr)

ax.plot(x_arr, d_arr, '-', color='#0072B2', lw=2.0, zorder=2, label=r'Conditional HRC-0 $\mu_{g,0}$ (A in-model; bridge B/Open)')
ax.axhline(3, color='0.82', ls=':', lw=0.7); ax.axhline(2, color='0.82', ls=':', lw=0.7)
# No x=1 transition marker: r_* below is defined instead by g_N=a_M.

# Generated profile points would be tautological because x and d are
# both computed from this same HRC-0 relation; they are deliberately omitted.

# Deliberately no marker at x=1; it is not the r_* condition.

ax.text(50, 2.92, '$d\\to 3$ (Newtonian)', fontsize=7.5, color='0.40', ha='center')
ax.text(0.02, 2.05, '$d\\to 2$ (conditional HRC-0 $\\mu_{g,0}$)', fontsize=7.5, color='0.40', ha='center')

ax.text(0.5, 0.04,
        r'$d_{\rm force}(x) = 1 + \dfrac{2(1+x^2)}{2+x^2}$',
        transform=ax.transAxes, fontsize=9, ha='center', va='bottom',
        bbox=dict(fc='white', ec='0.6', lw=0.5, pad=4))

ax.text(0.02, 0.97, '(b)', transform=ax.transAxes, fontsize=11, va='top', fontweight='bold')
ax.set_xscale('log'); ax.set_xlim(0.01, 1000); ax.set_ylim(1.9, 3.1)
ax.set_xlabel(r'$x = g_{\rm obs}/a_M$', fontsize=10)
ax.set_ylabel(r'$d_{\rm force}(x)$', fontsize=10)
ax.legend(loc='center left', fontsize=5.5, framealpha=0.95, edgecolor='0.7',
          fancybox=False, ncol=1, bbox_to_anchor=(0.01, 0.55))
ax.yaxis.set_minor_locator(plt.MultipleLocator(0.1))
ax.tick_params(which='both', top=True, right=True)

plt.tight_layout(rect=[0,0.045,1,1])
fig.text(0.5,0.008,r'Synthetic HRC-0 benchmark: $a_{M0}=1.0824\times10^{-10}\,\mathrm{m\,s^{-2}}$ and idealized point-source masses; no observational data overlay; faded isolation cutoffs are display-only.',ha='center',fontsize=7.2,style='italic')
plt.savefig(Path(__file__).parent.parent / 'figures' / 'fig_dimensionality_phi.png', dpi=220, bbox_inches='tight', facecolor='white')
plt.savefig(Path(__file__).parent.parent / 'figures' / 'fig_dimensionality_phi.pdf', bbox_inches='tight', facecolor='white')
print("Figure saved.")
