#!/usr/bin/env python3
"""
Figure for Appendix A1 (Hubble + r_s):
  chi-squared curve vs eps, with 1sigma and 2sigma shaded bands.
  GRAYSCALE only per preprint convention.

Outputs:
  figures/fig_hubble_rs_extraction_bw.pdf
"""
import os, sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../scripts/epsilon_convergence")
from ch1_hubble import (H0_P, sigma_P, H0_SH0ES, sigma_SH, DeltaH0)

Delta_obs   = H0_SH0ES - H0_P
Delta_sigma = np.sqrt(sigma_P**2 + sigma_SH**2)

# eps grid
eps_grid = np.linspace(0.0, 0.07, 401)
delta_pred = np.array([DeltaH0(e) for e in eps_grid])
chi2 = ((delta_pred - Delta_obs) / Delta_sigma) ** 2

# Known 1sigma and 2sigma edges from result_ch1.json
eps_central = 0.03231
eps_lo_1s, eps_hi_1s = 0.02671, 0.03755
eps_lo_2s, eps_hi_2s = 0.02069, 0.04250

# Figure
fig, ax = plt.subplots(figsize=(6.2, 3.8))

# Shade 2sigma (lighter gray) and 1sigma (darker gray)
ax.axvspan(eps_lo_2s, eps_hi_2s, color='0.85', zorder=0,
           label=r'$2\sigma$ interval')
ax.axvspan(eps_lo_1s, eps_hi_1s, color='0.65', zorder=1,
           label=r'$1\sigma$ interval')

# chi^2 curve (solid black)
ax.plot(eps_grid, chi2, '-', color='black', linewidth=1.4, zorder=3)

# Central value marker
ax.axvline(eps_central, color='black', linestyle=':', linewidth=1.0, zorder=2)

# Delta chi^2 = 1 and 4 reference lines
ax.axhline(1.0, color='black', linestyle='--', linewidth=0.7, alpha=0.6, zorder=2)
ax.axhline(4.0, color='black', linestyle='--', linewidth=0.7, alpha=0.6, zorder=2)

ax.set_xlabel(r'$\varepsilon$')
ax.set_ylabel(r'$\chi^2(\varepsilon)$')
ax.set_xlim(0.0, 0.07)
ax.set_ylim(0.0, 12.0)

# Annotations
ax.text(eps_central, 11.2,
        r'$\varepsilon_* = 0.032$',
        ha='center', va='top', fontsize=9)
ax.text(0.066, 1.3, r'$\Delta\chi^2 = 1$', ha='right', va='bottom', fontsize=8)
ax.text(0.066, 4.3, r'$\Delta\chi^2 = 4$', ha='right', va='bottom', fontsize=8)

ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

plt.tight_layout()
outdir = os.path.dirname(os.path.abspath(__file__)) + "/../figures"
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, 'fig_hubble_rs_extraction_bw.pdf')
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved {out}")
