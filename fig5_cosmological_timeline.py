#!/usr/bin/env python3
"""
fig5_cosmological_timeline.py
==============================
Figure: Cosmological evolution comparison — Lambda-CDM vs ECT.

Paper location: Figure 5, Section 12 (Cosmological Predictions)

Panels:
-------
(a) Standard Lambda-CDM timeline: colour-coded epochs from Planck era
    to today and future, with time axis in log10(t/s).

(b) ECT timeline: same axis, but with O(4)->O(3) phase transition
    explicitly shown as the origin of Lorentzian time. Inflation driven
    by the condensate with n_s = 0.967 (N_e = 60). Dark energy = residual
    condensate energy. Two future scenarios:
      Scenario A: v_0 -> const  (eternal expansion)
      Scenario B: v_0 -> 0      (Big Crunch at ~10^100 yr)

(c) Condensate dynamics: schematic plot of v_0(t)/v_infty, scale factor
    a(t), and G_eff(t)/G_N as functions of log10(t/s).
    The condensate starts at 0 (pre-transition), rises to v_infty,
    and may decrease in scenario B.

Key ECT predictions shown:
  - Phase transition at t ~ 10^{-42} s creates Lorentzian arrow of time
  - Inflation: n_s = 1 - 2/N_e = 0.967 for N_e = 60 (Planck 2018: 0.965 ± 0.004)
  - Dark energy EOS: w = -1 + 2*rho_kin/(3*rho_cond) ~ -0.83 at z~1 (DESI compatible)
  - G_eff(z) = G_N*(1+z)^{2*epsilon}, epsilon ~ 0.01 (Hubble tension partial resolution)

Dependencies: numpy, matplotlib
Usage:
    python fig5_cosmological_timeline.py
Output:
    ECT_vs_LCDM_timeline.png  (300 dpi)
    ECT_vs_LCDM_timeline.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ============================================================
# Plot style
# ============================================================
plt.rcParams.update({
    'font.family': 'serif', 'font.size': 9,
    'axes.linewidth': 0.8,
})

C_ECT    = '#1a9641'
C_BARYON = '#2166ac'
C_MOND   = '#d73027'
C_EFE    = '#e08214'
C_ACCENT1= '#762a83'
C_ACCENT2= '#7b2d8b'
C_ACCENT3= '#008080'

epoch_colors = {
    'planck':    '#7755BB',
    'inflation': '#CC44AA',
    'GUT':       '#CC4444',
    'EW':        '#CC8800',
    'QCD':       '#CC5500',
    'BBN':       '#44AA44',
    'recomb':    '#22AAAA',
    'dark':      '#2255AA',
    'future':    '#3333AA',
    'structure': '#55BB55',
}

# ============================================================
fig = plt.figure(figsize=(11, 10))
gs  = fig.add_gridspec(4, 1, height_ratios=[1.2, 0.3, 1.2, 1.5], hspace=0.25)

# ============================================================
# (a) Lambda-CDM Timeline
# Time axis: log10(t/s), ranging from -44 (Planck time) to +20 (far future)
# NOW is at log10(13.8e9 yr * 3.156e7 s/yr) ≈ 17.6
# ============================================================
ax1 = fig.add_subplot(gs[0])
ax1.set_xlim(-44, 20); ax1.set_ylim(0, 1)
ax1.text(0.0, 1.02, r'(a) Standard $\Lambda$CDM', transform=ax1.transAxes,
         fontsize=10, fontweight='bold', va='bottom')

lcdm_epochs = [
    (-43, -35, 'Planck+\nInflation',         epoch_colors['planck']),
    (-35, -10, 'GUT era\n(quarks)',           epoch_colors['GUT']),
    (-10,  -5, 'Electroweak\ntransition',     epoch_colors['EW']),
    ( -5,   0, 'QCD\nNucleosynthesis',        epoch_colors['QCD']),
    (  0,  13, 'Recombination\n(380 kyr)',    epoch_colors['recomb']),
    ( 13,  17, 'Dark energy\ndomination',     epoch_colors['dark']),
    ( 17, 17.6,'Galaxies\ntoday',             epoch_colors['structure']),
    (17.6,  20, 'Future\n(LCDM)',             epoch_colors['future']),
]
for x0, x1, label, color in lcdm_epochs:
    rect = Rectangle((x0, 0.15), x1-x0, 0.55,
                     facecolor=color, alpha=0.6, edgecolor='black', lw=0.5)
    ax1.add_patch(rect)
    ax1.text((x0+x1)/2, 0.42, label, ha='center', va='center', fontsize=6, fontweight='bold')

ax1.axvline(17.6, color='black', ls='--', lw=1.0)
ax1.text(17.6, 0.85, 'NOW\n13.8 Gyr', fontsize=7, ha='center', fontweight='bold')

time_labels = [(-43, r'$10^{-43}$ s'), (-35, r'$10^{-35}$ s'), (-10, r'$10^{-10}$ s'),
               (-5, r'$10^{-5}$ s'), (0, '1 s'), (13, r'$10^{5}$ yr'), (17.6, r'$10^{10}$ yr')]
for xt, lbl in time_labels:
    ax1.text(xt, 0.05, lbl, ha='center', fontsize=5, rotation=30)
ax1.set_yticks([])

# ============================================================
# Connecting annotations between panels
# ============================================================
ax2 = fig.add_subplot(gs[1])
ax2.set_xlim(-44, 20); ax2.set_ylim(0, 1); ax2.axis('off')

annotations = [
    (-42, r'O(4)$\to$O(3)' + '\n' + r'$\alpha>1$'),
    (-10, 'QFT, quarks\nbaryons'),
    (-3,  'SU(3) symm.\nconfinement'),
    (16,  r'fluct. $v_0(x)$' + '\nJWST'),
    (18,  r'$v_0 \to$const' + '\nexpansion'),
]
for xt, lbl in annotations:
    ax2.text(xt, 0.5, lbl, ha='center', va='center', fontsize=6,
             bbox=dict(fc='white', ec='gray', lw=0.5, pad=2))

# ============================================================
# (b) ECT Timeline
# Key difference: O(4)->O(3) phase transition generates Lorentzian time.
# Inflation driven by condensate rolling to O(3)-broken minimum.
# ============================================================
ax3 = fig.add_subplot(gs[2])
ax3.set_xlim(-44, 20); ax3.set_ylim(0, 1)
ax3.text(0.0, 1.02, '(b) ECT (Euclidean Condensate Theory)',
         transform=ax3.transAxes, fontsize=10, fontweight='bold', va='bottom')

ect_epochs = [
    (-44, -42, 'Planck\nepoch\n(Euclidean)', epoch_colors['planck']),
    (-42, -38, 'Phase\ntransition',          '#CC44AA'),
    (-38, -35, 'Inflation\n(cond.)',          epoch_colors['inflation']),
    (-35, -10, 'Hot\nBig Bang',               epoch_colors['GUT']),
    (-10,  -5, 'EW\ntransition',              epoch_colors['EW']),
    ( -5,   0, 'QCD',                         epoch_colors['QCD']),
    (  0,  13, 'Nucleosynth.\nRecomb.',       epoch_colors['recomb']),
    ( 13, 17.6,'Structure,\ngalaxies',        epoch_colors['structure']),
    (17.6, 19, 'Scenario A\n(expansion)',     epoch_colors['dark']),
    ( 19,  20, 'Scenario B\n(Big\nCrunch?)', epoch_colors['future']),
]
for x0, x1, label, color in ect_epochs:
    rect = Rectangle((x0, 0.15), x1-x0, 0.55,
                     facecolor=color, alpha=0.6, edgecolor='black', lw=0.5)
    ax3.add_patch(rect)
    ax3.text((x0+x1)/2, 0.42, label, ha='center', va='center', fontsize=5.5, fontweight='bold')

ax3.axvline(17.6, color='black', ls='--', lw=1.0)
ax3.text(17.6, 0.85, 'NOW', fontsize=7, ha='center', fontweight='bold')

ect_notes = [
    (-43, 'O(4)-symm.\n' + r'$v_0$=0, no $t$'),
    (-37, r'$\alpha>1$' + '\n' + r'$n_s$=0.967'),
    (-8,  'SU(2)-cond.\nW,Z,H'),
    ( 6,  r'$G_{\rm eff} \sim G_N$' + '\nstandard'),
    (17,  r'$\rho_v$: cond.' + '\n' + r'$w \approx -0.83$ (DESI)'),
    (19.5,r'$v_0 \to 0$?' + '\nBig Crunch'),
]
for xt, lbl in ect_notes:
    ax3.text(xt, 0.0, lbl, ha='center', va='top', fontsize=5,
             bbox=dict(fc='lightyellow', ec='gray', lw=0.3, pad=1))
ax3.set_yticks([])

# ============================================================
# (c) Condensate dynamics
# Schematic: v_0(t)/v_infty, log a(t), G_eff(t)/G_N vs log10(t/s)
# ============================================================
ax4 = fig.add_subplot(gs[3])
ax4.text(0.0, 1.02, '(c)', transform=ax4.transAxes, fontsize=10, fontweight='bold', va='bottom')

t = np.linspace(-44, 20, 2000)

# v_0 Scenario A (stays constant after condensation)
v0_norm = np.ones_like(t)
mask_early = t < -42
v0_norm[mask_early] = 0.5 * (1 + np.tanh((t[mask_early] + 42) * 3))
mask_trans = (t >= -42) & (t < -38)
v0_norm[mask_trans] = 0.5 + 0.5 * np.tanh((t[mask_trans] + 40) * 2)

# v_0 Scenario B (decreasing in far future)
v0_norm_b = v0_norm.copy()
mask_future = t > 18
v0_norm_b[mask_future] = 1.0 * np.exp(-(t[mask_future] - 18) * 0.5)

# Scale factor (log scale, normalised)
log_a = np.zeros_like(t)
mask_inf = (t >= -38) & (t < -35)
log_a[mask_inf] = 60 * (t[mask_inf] + 38) / 3
mask_post = t >= -35
log_a[mask_post] = 60 + 0.5 * np.log10(np.clip(10**(t[mask_post]+35), 1e-50, None))
log_a  = np.clip(log_a, 0, 65)
a_norm = log_a / 130 + 0.5

# G_eff (mild increase in the future via G_eff ~ G*(1+z)^{2eps})
G_eff_norm = np.ones_like(t)
mask_late  = t > 15
G_eff_norm[mask_late] = 1.0 + 0.03 * (t[mask_late] - 15)

ax4.plot(t, v0_norm,   '-', color=C_ECT,    lw=2.0, label=r'$v_0(t)/v_\infty$ — ECT condensate (Scenario A)')
ax4.plot(t, v0_norm_b, ':', color=C_ECT,    lw=1.5, alpha=0.5, label='Scenario B')
ax4.plot(t, a_norm,    '--', color=C_BARYON, lw=1.5, label=r'$\log a(t)/130 + 0.5$ — scale factor')
ax4.plot(t, G_eff_norm, '-', color=C_MOND,  lw=1.0, label=r'$G_{\rm eff}/G$ (rescaled)')

for xt, lbl, clr in [(-42, 'PT', C_ACCENT1), (-8, 'EW', C_EFE),
                      (13, 'Rec.', C_ACCENT3), (17.6, 'Now', 'black')]:
    ax4.axvline(xt, color=clr, ls='--', lw=0.6, alpha=0.5)
    ax4.text(xt, 1.95, lbl, fontsize=6, ha='center', color=clr)

ax4.annotate('Scenario B:\n' + r'$v_0 \to 0$, $G_{\rm eff} \to \infty$' + '\n' + r'$\sim 10^{100}$ yr',
             xy=(19, 0.3), fontsize=6, ha='center',
             bbox=dict(fc='lightyellow', ec='gray', lw=0.5, pad=2))

ax4.set_xlabel(r'$\log_{10}(t$ / s$)$')
ax4.set_ylabel('Normalized value')
ax4.set_xlim(-44, 20); ax4.set_ylim(0, 2.0)
ax4.legend(fontsize=7, loc='center left'); ax4.minorticks_on()

plt.savefig('ECT_vs_LCDM_timeline.png', dpi=300, bbox_inches='tight')
plt.savefig('ECT_vs_LCDM_timeline.pdf', bbox_inches='tight')
plt.close()
print("Saved: ECT_vs_LCDM_timeline.png, ECT_vs_LCDM_timeline.pdf")
