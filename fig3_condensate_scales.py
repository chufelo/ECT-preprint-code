#!/usr/bin/env python3
"""
fig3_condensate_scales.py
==========================
Figure: Three scales of ONE condensate field Phi — hierarchy via
renormalization group (RG) running.

Paper location: Figure 3, Section 5.3 (Hierarchy of physical scales)

Physics:
--------
ECT postulates a single scalar field Phi whose condensate expectation value
v_0(mu) runs with the RG scale mu. The running coupling lambda(mu) connects
three widely separated energy scales through a single field:

  1. v_0 ~ M_Pl = 2.4e18 GeV   Planck scale => G_N, hbar, c
  2. v_2 = 246 GeV              electroweak scale => W, Z, Higgs
  3. v_gal ~ c/r_0              galactic scale => rotation curves

Left panel (a): running coupling lambda(mu). It stays positive at high scales
(stable condensate), transitions to metastable negative regime at galactic
scales. The three red/blue dots mark the three physical scales.

Right panel (b): v_0(mu) = sqrt(mu/lambda(mu)) on log-log scale, showing
the enormous range of the single condensate field.

The RG connection between scales is qualitative in the current version;
see Open Problem OP17. The three condensate parameters (v_0, lambda, beta)
determine the three fundamental constants c, G_N, hbar (Section 5).

Dependencies: numpy, matplotlib
Usage:
    python fig3_condensate_scales.py
Output:
    ECT_condensate_scales.png  (300 dpi)
    ECT_condensate_scales.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# Plot style
# ============================================================
plt.rcParams.update({
    'font.family': 'serif', 'font.size': 9,
    'axes.linewidth': 0.8, 'axes.grid': True, 'grid.alpha': 0.3,
})

# Colour palette consistent with all ECT figures
C_ECT     = '#1a9641'
C_BARYON  = '#2166ac'
C_MOND    = '#d73027'
C_ACCENT1 = '#762a83'
C_ACCENT2 = '#e08214'

# ============================================================
# Main figure
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# ---- Panel (a): Running coupling lambda(mu) ----
# Qualitative sketch: lambda stays ~0.01 from Planck to EW scale,
# then decreases and turns negative at galactic scale.
# This is a schematic illustration, not a precision calculation.
logmu = np.linspace(19, -42, 1000)
lambda_val = 0.01 - 0.08 * (1 / (1 + np.exp(0.3 * (logmu + 35))))

ax1.plot(logmu, lambda_val, '-', color=C_ECT, lw=2.0,
         label=r'$\lambda(\mu)$, running coupling')

# Planck scale mark
ax1.plot(18.4, 0.01, 'o', color=C_BARYON, ms=10, zorder=5)
ax1.annotate(r'$v_0 \sim M_{\rm Pl}$' + '\n' + r'$2.4\times10^{18}$ GeV',
             (18.4, 0.01), textcoords='offset points', xytext=(-5, 12),
             fontsize=8, color=C_BARYON, ha='center')

# Electroweak scale mark
ax1.plot(2.39, 0.01, 'o', color=C_BARYON, ms=8, zorder=5)
ax1.annotate(r'$v_2 = 246$ GeV' + '\n(electroweak)',
             (2.39, 0.01), textcoords='offset points', xytext=(10, 12),
             fontsize=7, color=C_BARYON, ha='left')

# Galactic scale mark
ax1.plot(-42, -0.07, 'o', color=C_ACCENT2, ms=8, zorder=5)
ax1.annotate(r'$v_{\rm gal} \sim c/r_0$' + '\n' + r'$\sim10^{-42}$ GeV',
             (-42, -0.07), textcoords='offset points', xytext=(-15, -18),
             fontsize=7, color=C_ACCENT2, ha='center')

# Shade metastable region (lambda < 0)
ax1.fill_between(logmu, lambda_val, 0, where=(lambda_val < 0),
                 alpha=0.15, color=C_MOND, label=r'$\lambda < 0$ (metastable)')
ax1.axhline(0, color='black', lw=0.5)

ax1.text(0.03, 0.95, '(a)', transform=ax1.transAxes, fontsize=10, va='top', fontweight='bold')
ax1.set_xlabel(r'$\log_{10}(\mu \,/\, {\rm GeV})$')
ax1.set_ylabel(r'$\lambda(\mu)$')
ax1.set_xlim(20, -45); ax1.set_ylim(-0.09, 0.03)
ax1.legend(fontsize=7, loc='lower left'); ax1.minorticks_on()

# ---- Panel (b): v_0(mu) hierarchy ----
# v_0(mu) = sqrt(mu / lambda(mu)) — schematic, power-law interpolation
logmu_curve = np.linspace(19, -35, 500)
logv0_curve = 18.4 - 0.9 * (18.4 - logmu_curve)

ax2.plot(logmu_curve, 10**(logv0_curve), '-', color=C_ACCENT1, lw=2.0,
         label=r'$v_0(\mu) = \sqrt{\mu/\lambda(\mu)}$')

# Three scale annotations
scales = [
    (18.4, 2.4e18, r'$v_0 \approx 2.4\times10^{18}$ GeV' + '\n' + r'($\to G, \hbar, c$)', C_BARYON, 'right'),
    (2.39, 246,    r'$v_2 = 246$ GeV' + '\n' + r'($\to W, Z$, Higgs)', C_BARYON, 'left'),
    (-33,  1e-33,  r'$v_{\rm gal} \sim 10^{-33}$ GeV' + '\n(rotation curves)', C_ACCENT2, 'left'),
]
for lm, v0, label, clr, ha in scales:
    ax2.plot(lm, v0, 'o', color=clr, ms=10, zorder=5)
    xt = -12 if ha == 'right' else 10
    ax2.annotate(label, (lm, v0), textcoords='offset points',
                 xytext=(xt, 10), fontsize=7, color=clr, ha=ha)

ax2.annotate('RG connects\nall three scales',
             xy=(10, 1e10), fontsize=8, ha='center',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='gray', lw=0.5))

ax2.text(0.03, 0.95, '(b)', transform=ax2.transAxes, fontsize=10, va='top', fontweight='bold')
ax2.set_xlabel(r'$\log_{10}(\mu \,/\, {\rm GeV})$')
ax2.set_ylabel(r'$v_0(\mu)$ [GeV]')
ax2.set_yscale('log')
ax2.set_xlim(20, -40); ax2.set_ylim(1e-40, 1e20)
ax2.legend(fontsize=7, loc='lower left'); ax2.minorticks_on()

plt.tight_layout()
plt.savefig('ECT_condensate_scales.png', dpi=300, bbox_inches='tight')
plt.savefig('ECT_condensate_scales.pdf', bbox_inches='tight')
plt.close()
print("Saved: ECT_condensate_scales.png, ECT_condensate_scales.pdf")
