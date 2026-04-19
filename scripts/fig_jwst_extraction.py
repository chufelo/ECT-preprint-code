#!/usr/bin/env python3
"""
Grayscale figure for Appendix A2 (JWST extraction).

Decomposition R_PS(eps) * R_time(eps) = R_obs, with robustness-check
time-budget exponents p=0,1,1.5,2.  Output: fig_jwst_extraction_bw.pdf
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import the JWST module for self-consistent R_PS, R_time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'epsilon_convergence'))

from ch2_jwst import R_PS, R_time, z_JWST, z_form, nu_central
from scipy.optimize import brentq

eps_grid = np.linspace(0.0, 0.09, 500)

# Observational target
R_obs = 10.0
nu = nu_central  # 5.0

# Compute components
RPS  = np.array([R_PS(e, nu, z_JWST) for e in eps_grid])
RT_1 = np.array([R_time(e, z_form, z_JWST) for e in eps_grid])
# Robustness variants: p=0 (no time budget), p=1.5, p=2
RT_0   = np.ones_like(eps_grid)
RT_15  = RT_1 ** 1.5
RT_2   = RT_1 ** 2
R_total_1 = RPS * RT_1

# Invert for each p
def eps_at(p):
    if p == 0:
        return brentq(lambda e: R_PS(e, nu, z_JWST) - R_obs, 1e-4, 0.30)
    else:
        return brentq(
            lambda e: R_PS(e, nu, z_JWST) * (R_time(e, z_form, z_JWST))**p
                      - R_obs, 1e-4, 0.30)

eps_p0   = eps_at(0)    # PS only
eps_p1   = eps_at(1)    # default
eps_p15  = eps_at(1.5)
eps_p2   = eps_at(2)

# 1-sigma and 2-sigma intervals (from result_ch2.json)
import json
with open(os.path.join(SCRIPT_DIR, 'epsilon_convergence', 'result_ch2.json')) as f:
    ch2 = json.load(f)
eps_lo_1s = max(ch2['eps_lo_1s'], 0.0)
eps_hi_1s = ch2['eps_hi_1s']
eps_lo_2s = max(ch2['eps_lo_2s'], 0.0)
eps_hi_2s = ch2['eps_hi_2s']
eps_central = ch2['eps_central']

# ============== Figure ==============
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 6.8),
                               gridspec_kw={'height_ratios': [2, 1]})

# Top panel: R_PS, R_time, R_total vs eps
ax1.plot(eps_grid, RPS, color='0.2', linestyle='-', linewidth=1.6,
         label=r'$R_{\rm PS}(\varepsilon)$')
ax1.plot(eps_grid, RT_1, color='0.35', linestyle='--', linewidth=1.4,
         label=r'$R_{\rm time}(\varepsilon),\ p=1$')
ax1.plot(eps_grid, R_total_1, color='0.0', linestyle='-', linewidth=2.2,
         label=r'$R_{\rm total}=R_{\rm PS}\cdot R_{\rm time}$ ($p=1$)')
# Horizontal target
ax1.axhline(R_obs, color='0.3', linestyle=':', linewidth=1.0)
ax1.text(0.0015, R_obs*1.1, r'$R_{\rm obs}=10$', fontsize=9, color='0.3')
# Vertical lines: central eps for each p
ax1.axvline(eps_p0,  color='0.5', linestyle=':',  linewidth=0.9)
ax1.axvline(eps_p1,  color='0.0', linestyle='-',  linewidth=1.0)
ax1.axvline(eps_p15, color='0.5', linestyle=':',  linewidth=0.9)
ax1.axvline(eps_p2,  color='0.5', linestyle=':',  linewidth=0.9)
ax1.text(eps_p0,  20, r'$p=0$',   fontsize=8, rotation=90, va='bottom', ha='right', color='0.3')
ax1.text(eps_p1,  20, r'$p=1$',   fontsize=8, rotation=90, va='bottom', ha='right', color='0.0')
ax1.text(eps_p15, 20, r'$p=1.5$', fontsize=8, rotation=90, va='bottom', ha='right', color='0.3')
ax1.text(eps_p2,  20, r'$p=2$',   fontsize=8, rotation=90, va='bottom', ha='right', color='0.3')
ax1.set_yscale('log')
ax1.set_xlim(0.0, 0.09)
ax1.set_ylim(0.7, 100)
ax1.set_xlabel(r'$\varepsilon$', fontsize=11)
ax1.set_ylabel(r'excess factor', fontsize=11)
ax1.grid(True, which='both', alpha=0.3, linestyle=':')
ax1.set_title(r'JWST excess at $z=10$, $\nu=5$: '
              r'$R_{\rm PS}(\varepsilon)\cdot R_{\rm time}(\varepsilon)=R_{\rm obs}$',
              fontsize=10)
ax1.legend(loc='lower right', fontsize=9, framealpha=0.95)

# Bottom panel: extracted epsilon intervals
ax2.axvspan(eps_lo_2s, eps_hi_2s, color='0.85', alpha=0.7, zorder=1,
            label=rf'$2\sigma$: $[{eps_lo_2s:.3f},\,{eps_hi_2s:.3f}]$')
ax2.axvspan(eps_lo_1s, eps_hi_1s, color='0.55', alpha=0.7, zorder=2,
            label=rf'$1\sigma$: $[{eps_lo_1s:.3f},\,{eps_hi_1s:.3f}]$')
ax2.axvline(eps_central, color='0.0', linestyle='-', linewidth=1.5,
            label=rf'$\varepsilon_*={eps_central:.4f}$')
# Robustness brackets (p variation)
ax2.scatter([eps_p0, eps_p1, eps_p15, eps_p2], [0.5]*4,
            marker='|', s=200, color='0.0', zorder=5)
ax2.text(eps_p0, 0.72, 'p=0', fontsize=8, ha='center', color='0.2')
ax2.text(eps_p1, 0.72, 'p=1', fontsize=8, ha='center', color='0.0',
         fontweight='bold')
ax2.text(eps_p15, 0.72, '1.5', fontsize=8, ha='center', color='0.2')
ax2.text(eps_p2, 0.72, 'p=2', fontsize=8, ha='center', color='0.2')
ax2.set_xlim(0.0, 0.09)
ax2.set_ylim(0, 1)
ax2.set_yticks([])
ax2.set_xlabel(r'$\varepsilon$  (physical region $\geq 0$)', fontsize=11)
ax2.grid(axis='x', alpha=0.3, linestyle=':')
ax2.legend(loc='upper right', fontsize=8, framealpha=0.95)
ax2.set_title('Extracted interval + robustness of time-budget exponent $p$',
              fontsize=9.5, style='italic')

plt.tight_layout()
out_pdf = os.path.join(SCRIPT_DIR, '..', 'figures', 'fig_jwst_extraction_bw.pdf')
plt.savefig(out_pdf, dpi=300, bbox_inches='tight')
print(f"Saved {out_pdf}")
print(f"eps_p0={eps_p0:.5f}, eps_p1={eps_p1:.5f}, "
      f"eps_p1.5={eps_p15:.5f}, eps_p2={eps_p2:.5f}")
