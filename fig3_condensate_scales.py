#!/usr/bin/env python3
"""fig3_condensate_scales.py — GRAYSCALE version"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 9,
    'axes.linewidth': 0.8, 'axes.grid': True, 'grid.alpha': 0.3,
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

# Panel (a)
logmu = np.linspace(19, -42, 1000)
lambda_val = 0.01 - 0.08 * (1 / (1 + np.exp(0.3 * (logmu + 35))))

ax1.plot(logmu, lambda_val, '-', color='black', lw=2.0,
         label=r'$\lambda(\mu)$, running coupling')

ax1.plot(18.4, 0.01, 'o', color='black', ms=9, zorder=5)
ax1.annotate(r'$u_0 \sim \bar{M}_{\rm Pl}$' + '\n' + r'$2.4\times10^{18}$ GeV',
             (18.4, 0.01), textcoords='offset points', xytext=(-25, -30),
             fontsize=7.5, color='black', ha='center',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax1.plot(2.39, 0.01, 'o', color='0.35', ms=8, zorder=5)
ax1.annotate(r'$v_2 = 246$ GeV (electroweak)',
             (2.39, 0.01), textcoords='offset points', xytext=(15, 15),
             fontsize=7, color='0.35', ha='left',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax1.plot(-42, -0.07, 's', color='0.5', ms=8, zorder=5)
ax1.annotate(r'$v_{\rm gal} \sim 10^{-42}$ GeV',
             (-42, -0.07), textcoords='offset points', xytext=(-30, 10),
             fontsize=7, color='0.5', ha='center',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax1.fill_between(logmu, lambda_val, 0, where=(lambda_val < 0),
                 alpha=0.12, color='0.5', label=r'$\lambda < 0$ (metastable)')
ax1.axhline(0, color='black', lw=0.5)

ax1.text(0.97, 0.95, r'$\bf{(a)}$', transform=ax1.transAxes,
         fontsize=11, va='top', ha='right')
ax1.set_xlabel(r'$\log_{10}(\mu \,/\, {\rm GeV})$')
ax1.set_ylabel(r'$\lambda(\mu)$')
ax1.set_xlim(20, -45); ax1.set_ylim(-0.09, 0.03)
ax1.legend(fontsize=7, loc='lower left'); ax1.minorticks_on()

# Panel (b)
logmu_curve = np.linspace(19, -35, 500)
logv0_curve = 18.4 - 0.9 * (18.4 - logmu_curve)

ax2.plot(logmu_curve, 10**(logv0_curve), '-', color='black', lw=2.0,
         label=r'$u_0(\mu) = \sqrt{\mu/\lambda(\mu)}$')

ax2.plot(18.4, 2.4e18, 'o', color='black', ms=9, zorder=5)
ax2.annotate(r'$u_0 = 2.4\times10^{18}$ GeV' + '\n' + r'($\to G, \hbar, c$)',
             (18.4, 2.4e18), textcoords='offset points',
             xytext=(15, -20), fontsize=7, color='black', ha='left',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax2.plot(2.39, 246, 'o', color='0.35', ms=8, zorder=5)
ax2.annotate(r'$v_2 = 246$ GeV' + '\n' + r'($\to W, Z$, Higgs)',
             (2.39, 246), textcoords='offset points',
             xytext=(12, 12), fontsize=7, color='0.35', ha='left',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax2.plot(-33, 1e-33, 's', color='0.5', ms=8, zorder=5)
ax2.annotate(r'$v_{\rm gal} \sim 10^{-33}$ GeV' + '\n(rotation curves)',
             (-33, 1e-33), textcoords='offset points',
             xytext=(-50, 15), fontsize=7, color='0.5', ha='center',
             arrowprops=dict(arrowstyle='->', color='0.5', lw=0.8))

ax2.annotate('RG connects\nall three scales',
             xy=(7, 1e8), fontsize=8, ha='center',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', lw=0.5))

ax2.text(0.97, 0.95, r'$\bf{(b)}$', transform=ax2.transAxes,
         fontsize=11, va='top', ha='right')
ax2.set_xlabel(r'$\log_{10}(\mu \,/\, {\rm GeV})$')
ax2.set_ylabel(r'$u_0(\mu)$ [GeV]')
ax2.set_yscale('log')
ax2.set_xlim(20, -40); ax2.set_ylim(1e-40, 1e20)
ax2.legend(fontsize=7, loc='lower left'); ax2.minorticks_on()

plt.tight_layout()
plt.savefig('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_condensate_scales.png',
            dpi=300, bbox_inches='tight')
plt.close()
print("SAVED grayscale fig_condensate_scales.png")
