#!/usr/bin/env python3
"""
fig5_cosmological_timeline.py  v6
ECT preprint - Figure 5: Cosmological Evolution Timeline

Fixes v6:
  1. Panel titles moved ABOVE diagram area (no overlap with blocks)
  2. ECT leftmost labels: Euclidean phase -> lo, PT -> hi (separated)
  3. Scenario A annotation shifted left+up, away from curves
  4. G_eff/G now normalised to start at 1.0 at B_start (not arc from nowhere)
  5. All font sizes increased for legibility

Author: Valeriy Blagovidov  |  DOI: 10.5281/zenodo.18917930
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullFormatter, AutoMinorLocator
import matplotlib.gridspec as gridspec

# ── Font sizes: all bumped up ────────────────────────────────────────────────
FS_BASE   = 10.0   # global base
FS_TITLE  = 12.0   # panel title
FS_BLOCK  = 8.5    # epoch block labels
FS_VLINE  = 7.0    # vertical line labels
FS_ANN    = 9.0    # scenario annotation boxes
FS_CURVE  = 9.5    # curve labels in panel (c)
FS_LEGEND = 9.0    # legend
FS_AXIS   = 11.0   # axis label
FS_TICK   = 9.0    # tick labels
FS_NOTE   = 6.5    # footnote

plt.rcParams.update({
    'font.family': 'serif', 'font.size': FS_BASE, 'axes.linewidth': 0.8,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'xtick.major.size': 4, 'ytick.major.size': 4,
    'xtick.minor.size': 2, 'ytick.minor.size': 2,
    'xtick.minor.visible': True,
})

GS = {
    'undef': '#BEBEBE', 'planck': '#888888', 'inflate': '#999999',
    'rad': '#C8C8C8', 'ew': '#AAAAAA', 'qcd': '#B8B8B8',
    'recomb': '#D4D4D4', 'struct': '#BDBDBD', 'de': '#969696',
    'fut_lcdm': '#DEDEDE', 'futA': '#E8E8E8', 'futB': '#CCCCCC',
}
BLK = '#000000'; MID = '#555555'; LGT = '#999999'

T_PT=-43.27; T_EINFL=-32.0; T_EW=-10.0; T_QCD=-5.0
T_BBN=2.0;   T_REC=12.85;   T_NOW=17.64
X_MIN=-50.0; X_MAX=22.0

VLINES = [
    (T_PT,    r'$t_\mathrm{Pl}$', BLK, '-',  1.0),
    (T_EINFL, 'end infl.',         MID, '--', 0.75),
    (T_EW,    'EW',                MID, '--', 0.75),
    (T_QCD,   'QCD+BBN',           MID, '--', 0.75),
    (T_REC,   'Recomb.',           MID, '--', 0.75),
    (T_NOW,   'NOW',               BLK, '-',  1.0),
]

def add_vlines(ax, label_y=None, fs=FS_VLINE):
    for xt, lbl, col, ls, lw in VLINES:
        ax.axvline(xt, color=col, ls=ls, lw=lw, alpha=0.75, zorder=10)
        if label_y is not None:
            ax.text(xt, label_y, lbl, ha='center', va='bottom',
                    fontsize=fs, color=col, clip_on=True)

def epoch_block(ax, x0, x1, label, key, y0=0.05, h=0.88, fs=FS_BLOCK, alt_pos='mid'):
    """alt_pos: 'hi' top-third, 'lo' bottom-third, 'mid' centre"""
    r = Rectangle((x0, y0), x1-x0, h, facecolor=GS[key], edgecolor=BLK, linewidth=0.5)
    ax.add_patch(r)
    ty = {'hi': y0+h*0.75, 'lo': y0+h*0.25, 'mid': y0+h*0.50}[alt_pos]
    ax.text((x0+x1)/2, ty, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color='#111111', clip_on=True)

# ── Figure ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 13))
gs_fig = gridspec.GridSpec(3, 1, height_ratios=[1.0, 1.15, 2.8], hspace=0.22)
ax_a = fig.add_subplot(gs_fig[0])
ax_b = fig.add_subplot(gs_fig[1], sharex=ax_a)
ax_c = fig.add_subplot(gs_fig[2], sharex=ax_a)
for ax in [ax_a, ax_b]:
    ax.set_xlim(X_MIN, X_MAX); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.yaxis.set_minor_formatter(NullFormatter())
ax_c.set_xlim(X_MIN, X_MAX)

# ── FIX 1: titles placed ABOVE axes using set_title ─────────────────────────
# set_title puts text above the axes frame, no overlap with blocks
ax_a.set_title(r'(a) Standard $\Lambda$CDM',
               fontsize=FS_TITLE, fontweight='bold', loc='left', pad=6)
ax_b.set_title('(b) ECT (Euclidean Condensate Theory)',
               fontsize=FS_TITLE, fontweight='bold', loc='left', pad=6)
ax_c.set_title('(c) Condensate dynamics and cosmological observables',
               fontsize=FS_TITLE, fontweight='bold', loc='left', pad=6)

# ════════════════════════════════════════════════════════════════════════════
# Panel (a): ΛCDM
# ════════════════════════════════════════════════════════════════════════════
for x0, x1, lbl, key, pos in [
    (X_MIN,   T_PT,    'Undefined\n(no spacetime)',   'undef',    'mid'),
    (T_PT,    T_EINFL, 'Planck+\nInflation',           'planck',   'hi'),
    (T_EINFL, T_EW,    'Radiation\n(quarks, leptons)', 'rad',      'lo'),
    (T_EW,    T_QCD,   'EW\ntransition',               'ew',       'hi'),
    (T_QCD,   T_BBN,   'QCD+BBN',                      'qcd',      'lo'),
    (T_BBN,   T_REC,   'Radiation/Matter\ndomination', 'recomb',   'hi'),
    (T_REC,   T_NOW,   'Structure\nformation',          'struct',   'lo'),
    (T_NOW,   X_MAX,   'Future\n(de Sitter)',            'fut_lcdm', 'hi'),
]:
    epoch_block(ax_a, x0, x1, lbl, key, alt_pos=pos)
add_vlines(ax_a, label_y=0.97)
plt.setp(ax_a.get_xticklabels(), visible=False)

# ════════════════════════════════════════════════════════════════════════════
# Panel (b): ECT
# FIX 2: "Euclidean phase" -> lo,  "PT" -> hi   (separate from each other)
# ════════════════════════════════════════════════════════════════════════════
# Euclidean phase: very wide block, label at BOTTOM to avoid collision with "PT hi" label
epoch_block(ax_b, X_MIN, T_PT,
            'Euclidean phase\n(O(4)-symmetric\nno time, $v_0{=}0$)',
            'undef', y0=0.05, h=0.88, fs=FS_BLOCK, alt_pos='lo')
PT_W = 1.5
# PT block: label at TOP so it clears the Euclidean phase label
epoch_block(ax_b, T_PT, T_PT+PT_W, 'PT\nO(4)$\\to$O(3)',
            'planck', y0=0.05, h=0.88, fs=FS_BLOCK-0.5, alt_pos='hi')
for x0, x1, lbl, key, pos in [
    (T_PT+PT_W, T_EINFL, r'Inflation $N_e{=}60$'+'\n'+r'$n_s{=}0.967$', 'inflate', 'hi'),
    (T_EINFL,  T_EW,  'Radiation\n(as in SM)',                            'rad',    'lo'),
    (T_EW,     T_QCD, r'EW: $v_2{=}246$ GeV'+'\nW,Z,H',                 'ew',     'hi'),
    (T_QCD,    T_BBN, 'QCD+BBN',                                          'qcd',    'lo'),
    (T_BBN,    T_REC, 'Rad./Matter\ndomination',                          'recomb', 'hi'),
    (T_REC,    T_NOW, 'Structure +\n$v_0$-condensate\n(residual DE)',     'struct', 'lo'),
    (T_NOW,    T_NOW+2, 'Scen. A\n$v_0{\\to}v_\\infty$',                  'futA',   'hi'),
    (T_NOW+2,  X_MAX, 'Scen. B\n$v_0{\\to}0$\nCrunch',                   'futB',   'lo'),
]:
    epoch_block(ax_b, x0, x1, lbl, key, y0=0.05, h=0.88, fs=FS_BLOCK-0.5, alt_pos=pos)

for xt, note in [
    (T_PT+0.5,  r'$\alpha{>}1$, time emerges, $c_*{=}1/\!\sqrt{\alpha-1}$'),
    (T_EINFL-5, r'$v_0{\sim}M_\mathrm{Pl}$ frozen'),
    (T_EW-1.8,  r'$v_2{=}246$ GeV'),
    (T_NOW-1.8, r'$w_0{\approx}{-}0.83$ (DESI)'),
]:
    ax_b.text(xt, 0.01, note, ha='center', va='bottom', fontsize=6.5,
              bbox=dict(fc='white', ec='#999999', lw=0.4, pad=1.5), clip_on=True)

ax_b.annotate('', xy=(T_PT, 0.96), xytext=(X_MIN+4, 0.96),
              arrowprops=dict(arrowstyle='<->', color=BLK, lw=0.8))
ax_b.text((X_MIN+4+T_PT)/2, 0.985,
          r'$\Lambda$CDM: undefined  =  ECT: Euclidean phase (same boundary $t_\mathrm{Pl}$)',
          ha='center', fontsize=6.5, color=BLK)
add_vlines(ax_b, label_y=None)
plt.setp(ax_b.get_xticklabels(), visible=False)

# ════════════════════════════════════════════════════════════════════════════
# Panel (c): Condensate dynamics
# ════════════════════════════════════════════════════════════════════════════
t = np.linspace(X_MIN, X_MAX, 5000)
ax_c.axvspan(X_MIN, T_PT, color='#CCCCCC', alpha=0.50, zorder=0)
ax_c.text((X_MIN+T_PT)/2, 0.55, 'Euclidean\nphase\n(no time)',
          ha='center', va='center', fontsize=9, color='#555555', style='italic')

# v0 Scenario A
v0 = np.zeros_like(t)
v0[t >= T_PT] = np.tanh(2.0 * (t[t >= T_PT] - T_PT))
v0 = np.clip(v0, 0, 1)
im = (t >= T_PT) & (t < T_EINFL)
v0[im] *= 0.97 + 0.03 * np.cos(np.pi * (t[im] - T_PT) / (T_EINFL - T_PT))

# v0 Scenario B
v0_B = v0.copy()
B_start = T_NOW + 2.0
fm = t > B_start
v0_B[fm] = 1.0 - 0.18 * np.tanh(1.5 * (t[fm] - B_start))
v0_B = np.clip(v0_B, 0, 1)

# v2: EW condensate
v2 = np.zeros_like(t)
v2[t >= T_EW] = 0.22 * (1 - np.exp(-3.0 * (t[t >= T_EW] - T_EW)))

# log a
loga = np.zeros_like(t)
im2 = (t >= T_PT) & (t < T_EINFL)
loga[im2] = 0.03 + 0.57 * (t[im2] - T_PT) / (T_EINFL - T_PT)
pm = t >= T_EINFL
loga[pm] = 0.60 + 0.40 * np.sqrt((t[pm]-T_EINFL)/(T_NOW-T_EINFL))
loga = np.clip(loga, 0, 1.05)

# FIX 4: G_eff / G — Scenario B, normalised so it STARTS at 1.0 at B_start
# G_eff = G_N * (v_inf / v0)^2 → ∞ as v0 → 0
# By normalising to G_eff(B_start) = 1, the curve naturally starts at y=1
# (same level as v0(A)=1) and diverges upward — no "arc from nowhere"
with np.errstate(divide='ignore', invalid='ignore'):
    G_raw = np.where(v0_B[fm] > 0.005, 1.0 / (v0_B[fm]**2), 400.0)
# Normalise to 1 at the very start of the B divergence
G_norm = G_raw / G_raw[0]   # = 1 at B_start, then rises
G_eff_plot = np.clip(G_norm, 0, 1.62)
G_x = t[(t > B_start) & (t <= X_MAX)]

pm2 = t >= T_PT; lw = 2.0
ax_c.plot(t[pm2], v0[pm2],    '-',  color=BLK, lw=lw+0.5,
          label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. A)')
ax_c.plot(t[pm2], v0_B[pm2],  ':',  color=BLK, lw=lw,
          label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. B)')
ax_c.plot(t[pm2], v2[pm2],    '--', color=MID, lw=lw-0.4,
          label=r'$v_2(t)/v_{2,\mathrm{EW}}$ — EW condensate (SU(2))')
ax_c.plot(t[pm2], loga[pm2],  '-.', color=LGT, lw=lw,
          label=r'$\log a(t)$ (scale factor, normalised)')
ax_c.plot(G_x, G_eff_plot,    '-',  color=MID, lw=lw+0.2, alpha=0.85,
          label=r'$G_\mathrm{eff}/G$ (Scen. B, $\propto v_0^{-2}\to\infty$)')

# Curve labels
ax_c.text(T_PT+0.8,  1.02, r'$v_0$ (A)',  fontsize=FS_CURVE)
ax_c.text(T_NOW+0.2, 0.74, r'$v_0$ (B)',  fontsize=FS_CURVE)
ax_c.text(T_EINFL+4, 0.63, r'$\log a$',   fontsize=FS_CURVE, color=LGT)
ax_c.text(T_EW+0.4,  0.24, r'$v_2$',      fontsize=FS_CURVE, color=MID)
ax_c.text(T_NOW+2.2, 1.30, r'$G_\mathrm{eff}$'+'\n(Scen. B)',
          fontsize=FS_CURVE, color=MID, ha='center')

# FIX 3: Scenario A box shifted LEFT and UP to avoid covering the v0=1 plateau
ax_c.annotate('Scenario A:\n$v_0 \\to v_\\infty$\neternal expansion',
              xy=(T_NOW-2.5, 1.15),   # moved left of NOW line, up into clear space
              fontsize=FS_ANN,
              bbox=dict(fc='#F0F0F0', ec='#AAAAAA', lw=0.7, pad=5))

ax_c.annotate('Scenario B:\n$v_0$ slowly $\\to 0$\n$G_\\mathrm{eff}\\to\\infty$\n'
              'Big Crunch $\\sim 10^{100}$ yr\n(curve off right axis)',
              xy=(T_NOW+1.0, 0.36), fontsize=FS_ANN,
              bbox=dict(fc='#E8E8E8', ec='#AAAAAA', lw=0.7, pad=5))

ax_c.text(0.005, 0.005,
    r'Note: curves are schematic ($\tanh$-approximations to '
    r'$\ddot{v}_0+3H\dot{v}_0+V^\prime(v_0)=0$); '
    r'quantitative solutions require numerical integration.',
    transform=ax_c.transAxes, fontsize=FS_NOTE, color='#666666',
    va='bottom', style='italic')

add_vlines(ax_c, label_y=1.51, fs=FS_VLINE)
ax_c.set_ylim(-0.04, 1.68)
ax_c.set_ylabel('Normalised value', fontsize=FS_AXIS)
ax_c.legend(fontsize=FS_LEGEND, loc='upper left', bbox_to_anchor=(0.005, 0.99),
            framealpha=0.95, edgecolor='#AAAAAA', handlelength=2.8)
ax_c.yaxis.set_minor_locator(AutoMinorLocator())
ticks = [-43,-40,-35,-30,-20,-10,0,5,10,12.85,17.64,20]
lbls  = [r'$10^{-43}$',r'$10^{-40}$',r'$10^{-35}$',r'$10^{-30}$',
         r'$10^{-20}$',r'$10^{-10}$','1',r'$10^5$',r'$10^{10}$',
         '380\nkyr','13.8\nGyr','']
ax_c.set_xticks(ticks); ax_c.set_xticklabels(lbls, fontsize=FS_TICK)
ax_c.set_xlabel(r'$\log_{10}(t\,/\,\mathrm{s})$', fontsize=FS_AXIS)

import os
out = '/Users/chufelo/Documents/Physics/VDT/ECT/github_repo'
plt.savefig(os.path.join(out, 'ECT_vs_LCDM_timeline.png'), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig(os.path.join(out, 'ECT_vs_LCDM_timeline.pdf'), bbox_inches='tight', facecolor='white')
plt.close()
print("Saved v6")
