#!/usr/bin/env python3
"""Seesaw landscape at fixed ECT scales — improved Figure 7."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
rcParams['mathtext.fontset'] = 'cm'
rcParams['font.size'] = 11
rcParams['axes.linewidth'] = 0.8

v2 = 246.0        # GeV
phi0 = 2.44e18    # GeV (reduced Planck mass)

M_R = np.logspace(6, 19, 500)  # GeV

y_values = [1.0, 0.1, 4.5e-3, 1e-3, 1e-4]
labels   = [r'$y_\nu=1$', r'$y_\nu=0.1$',
            r'$y_\nu\approx 4.5\times10^{-3}$',
            r'$y_\nu=10^{-3}$', r'$y_\nu=10^{-4}$']
styles   = ['--', '-.', '-', ':', (0,(3,1,1,1,1,1))]
widths   = [1.0, 1.0, 2.2, 1.0, 1.0]
grays    = ['0.60', '0.45', '0.0', '0.45', '0.60']

fig, ax = plt.subplots(figsize=(7.0, 4.8))

for y, lab, ls, lw, gc in zip(y_values, labels, styles, widths, grays):
    m_nu = y**2 * v2**2 / M_R  # GeV
    m_nu_eV = m_nu * 1e9       # eV
    ax.plot(M_R, m_nu_eV, linestyle=ls, linewidth=lw, color=gc, label=lab)

# Weinberg floor
weinberg_eV = v2**2 / phi0 * 1e9
ax.axhline(y=weinberg_eV, color='0.3', linestyle='--', linewidth=0.8, zorder=1)
ax.text(1.5e6, weinberg_eV * 1.8,
        r'$m_\nu^{\rm geom}=v_2^2/\phi_0$',
        fontsize=9, color='0.3', ha='left', va='bottom')

# Atmospheric scale band
ax.axhspan(0.04, 0.06, color='0.90', zorder=0)
ax.text(3e17, 0.050, r'$\Delta m^2_{\rm atm}$', fontsize=8,
        color='0.5', ha='right', va='center')

# Vertical lines
vlines = [(2.4e10, r'$M_R^{\rm geom}$', '-'),
          (1e9, r'lepto.', '--'),
          (2.44e18, r'$\phi_0$', ':')]
for xv, lab, ls in vlines:
    ax.axvline(x=xv, color='0.4', linestyle=ls, linewidth=0.7, zorder=1)
    ax.text(xv * 1.15, 2e-7, lab, fontsize=8, color='0.4',
            rotation=90, ha='left', va='bottom')

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel(r'$M_R$ [GeV]', fontsize=12)
ax.set_ylabel(r'$m_\nu$ [eV]', fontsize=12)
ax.set_xlim(1e6, 1e19)
ax.set_ylim(1e-7, 1e4)
ax.legend(loc='upper right', fontsize=9, framealpha=0.9,
          edgecolor='0.7', fancybox=False)
ax.tick_params(which='both', direction='in', top=True, right=True)

plt.tight_layout()
outpath = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_neutrino_seesaw.pdf'
fig.savefig(outpath, dpi=300, bbox_inches='tight')
print(f"✅ Saved: {outpath}")
plt.close()
