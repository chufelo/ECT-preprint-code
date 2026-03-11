#!/usr/bin/env python3
"""
fig5_cosmological_timeline.py  v5
ECT preprint - Figure 5: Cosmological Evolution Timeline

Fixes:
  1. LCDM: single future phase only (de Sitter)
  2. ECT current epoch: "Structure + v0-condensate (residual DE)"
  3. G_eff/G (Scen. B, diverges as v0->0) curve RESTORED
  4. Epoch labels alternate hi/lo to avoid overlap

Author: Valeriy Blagovidov  |  DOI: 10.5281/zenodo.18917930
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import NullFormatter, AutoMinorLocator
import matplotlib.gridspec as gridspec

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 8.5, 'axes.linewidth': 0.8,
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
    (T_PT, r'$t_\mathrm{Pl}$', BLK, '-', 1.0),
    (T_EINFL, 'end infl.', MID, '--', 0.75),
    (T_EW, 'EW', MID, '--', 0.75),
    (T_QCD, 'QCD+BBN', MID, '--', 0.75),
    (T_REC, 'Recomb.', MID, '--', 0.75),
    (T_NOW, 'NOW', BLK, '-', 1.0),
]

def add_vlines(ax, label_y=None, fs=5.5):
    for xt, lbl, col, ls, lw in VLINES:
        ax.axvline(xt, color=col, ls=ls, lw=lw, alpha=0.75, zorder=10)
        if label_y is not None:
            ax.text(xt, label_y, lbl, ha='center', va='bottom',
                    fontsize=fs, color=col, clip_on=True)

def epoch_block(ax, x0, x1, label, key, y0=0.10, h=0.80, fs=7.0, alt_pos='mid'):
    r = Rectangle((x0, y0), x1-x0, h, facecolor=GS[key], edgecolor=BLK, linewidth=0.5)
    ax.add_patch(r)
    ty = {'hi': y0+h*0.72, 'lo': y0+h*0.28, 'mid': y0+h*0.50}[alt_pos]
    ax.text((x0+x1)/2, ty, label, ha='center', va='center',
            fontsize=fs, fontweight='bold', color='#111111', clip_on=True)

fig = plt.figure(figsize=(13, 12))
gs_fig = gridspec.GridSpec(3, 1, height_ratios=[1.0, 1.15, 2.8], hspace=0.09)
ax_a = fig.add_subplot(gs_fig[0])
ax_b = fig.add_subplot(gs_fig[1], sharex=ax_a)
ax_c = fig.add_subplot(gs_fig[2], sharex=ax_a)
for ax in [ax_a, ax_b]:
    ax.set_xlim(X_MIN, X_MAX); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.yaxis.set_minor_formatter(NullFormatter())
ax_c.set_xlim(X_MIN, X_MAX)

# ── Panel (a): LCDM — single future phase ─────────────────────────────────
ax_a.text(0.005, 0.98, r'(a) Standard $\Lambda$CDM',
          transform=ax_a.transAxes, fontsize=10, fontweight='bold', va='top')
for x0, x1, lbl, key, pos in [
    (X_MIN,   T_PT,    'Undefined\n(no spacetime)',   'undef',    'mid'),
    (T_PT,    T_EINFL, 'Planck+\nInflation',           'planck',   'hi'),
    (T_EINFL, T_EW,    'Radiation\n(quarks, leptons)', 'rad',      'lo'),
    (T_EW,    T_QCD,   'EW\ntransition',               'ew',       'hi'),
    (T_QCD,   T_BBN,   'QCD+BBN',                      'qcd',      'lo'),
    (T_BBN,   T_REC,   'Radiation/Matter\ndomination', 'recomb',   'hi'),
    (T_REC,   T_NOW,   'Structure\nformation',          'struct',   'lo'),
    (T_NOW,   X_MAX,   'Future\n(de Sitter)',            'fut_lcdm', 'hi'),  # single future
]:
    epoch_block(ax_a, x0, x1, lbl, key, alt_pos=pos)
add_vlines(ax_a, label_y=0.96)
plt.setp(ax_a.get_xticklabels(), visible=False)

# ── Panel (b): ECT — corrected DE label ───────────────────────────────────
ax_b.text(0.005, 0.98, '(b) ECT (Euclidean Condensate Theory)',
          transform=ax_b.transAxes, fontsize=10, fontweight='bold', va='top')
epoch_block(ax_b, X_MIN, T_PT,
            'Euclidean phase\n(O(4)-symmetric\nno time, $v_0{=}0$)',
            'undef', y0=0.10, h=0.82, fs=7.0, alt_pos='mid')
PT_W = 1.5
epoch_block(ax_b, T_PT, T_PT+PT_W, 'PT\nO(4)$\\to$O(3)',
            'planck', y0=0.10, h=0.82, fs=6.5, alt_pos='mid')
for x0, x1, lbl, key, pos in [
    (T_PT+PT_W, T_EINFL, r'Inflation $N_e{=}60$'+'\n'+r'$n_s{=}0.967$', 'inflate', 'hi'),
    (T_EINFL,  T_EW,  'Radiation\n(as in SM)',                            'rad',    'lo'),
    (T_EW,     T_QCD, r'EW: $v_2{=}246$ GeV'+'\nW,Z,H',                 'ew',     'hi'),
    (T_QCD,    T_BBN, 'QCD+BBN',                                          'qcd',    'lo'),
    (T_BBN,    T_REC, 'Rad./Matter\ndomination',                          'recomb', 'hi'),
    # No separate "Dark energy" in ECT: DE = residual condensate vacuum energy V(v_inf)
    (T_REC,    T_NOW, 'Structure +\n$v_0$-condensate\n(residual DE)',     'struct', 'lo'),
    (T_NOW,    T_NOW+2, 'Scen. A\n$v_0{\\to}v_\\infty$',                  'futA',   'hi'),
    (T_NOW+2,  X_MAX, 'Scen. B\n$v_0{\\to}0$\nCrunch',                   'futB',   'lo'),
]:
    epoch_block(ax_b, x0, x1, lbl, key, y0=0.10, h=0.82, fs=6.5, alt_pos=pos)
for xt, note in [
    (T_PT+0.5,  r'$\alpha{>}1$, time emerges, $c_*{=}1/\!\sqrt{\alpha-1}$'),
    (T_EINFL-5, r'$v_0{\sim}M_\mathrm{Pl}$ frozen'),
    (T_EW-1.8,  r'$v_2{=}246$ GeV'),
    (T_NOW-1.8, r'$w_0{\approx}{-}0.83$ (DESI)'),
]:
    ax_b.text(xt, 0.03, note, ha='center', va='bottom', fontsize=5.3,
              bbox=dict(fc='white', ec='#999999', lw=0.4, pad=1.5), clip_on=True)
ax_b.annotate('', xy=(T_PT, 0.95), xytext=(X_MIN+4, 0.95),
              arrowprops=dict(arrowstyle='<->', color=BLK, lw=0.8))
ax_b.text((X_MIN+4+T_PT)/2, 0.97,
          r'$\Lambda$CDM: undefined  =  ECT: Euclidean phase (same boundary $t_\mathrm{Pl}$)',
          ha='center', fontsize=5.8, color=BLK)
add_vlines(ax_b, label_y=None)
plt.setp(ax_b.get_xticklabels(), visible=False)

# ── Panel (c): Condensate dynamics — G_eff curve restored ─────────────────
ax_c.text(0.005, 0.985, '(c) Condensate dynamics and cosmological observables',
          transform=ax_c.transAxes, fontsize=10, fontweight='bold', va='top')
t = np.linspace(X_MIN, X_MAX, 5000)
ax_c.axvspan(X_MIN, T_PT, color='#CCCCCC', alpha=0.50, zorder=0)
ax_c.text((X_MIN+T_PT)/2, 0.55, 'Euclidean\nphase\n(no time)',
          ha='center', va='center', fontsize=8, color='#555555', style='italic')

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

# G_eff / G — Scenario B diverges as v0 -> 0
# G_eff = G_N * (v_inf/v0)^2 -> inf as v0 -> 0
G_eff_B = np.full_like(t, np.nan)
G_eff_B[t >= T_PT] = 1.0
with np.errstate(divide='ignore', invalid='ignore'):
    G_eff_B[fm] = np.where(v0_B[fm] > 0.01, 1.0/(v0_B[fm]**2), 100.0)
G_eff_B_plot = np.clip(G_eff_B / 6.0, 0, 1.55)
G_x = t[(t >= B_start) & (t <= X_MAX)]
G_y = G_eff_B_plot[(t >= B_start) & (t <= X_MAX)]

pm2 = t >= T_PT; lw = 1.9
ax_c.plot(t[pm2], v0[pm2],   '-',  color=BLK, lw=lw+0.4,
          label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. A)')
ax_c.plot(t[pm2], v0_B[pm2], ':',  color=BLK, lw=lw,
          label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. B)')
ax_c.plot(t[pm2], v2[pm2],   '--', color=MID, lw=lw-0.3,
          label=r'$v_2(t)/v_{2,\mathrm{EW}}$ — EW condensate (SU(2))')
ax_c.plot(t[pm2], loga[pm2], '-.', color=LGT, lw=lw,
          label=r'$\log a(t)$ (scale factor, normalised)')
ax_c.plot(G_x, G_y, '-', color=MID, lw=lw+0.2, alpha=0.85,
          label=r'$G_\mathrm{eff}/G$ (Scen. B, $\propto v_0^{-2}\to\infty$)')

ax_c.text(T_PT+0.8,  1.01, r'$v_0$ (A)',  fontsize=8.5)
ax_c.text(T_NOW+0.2, 0.73, r'$v_0$ (B)',  fontsize=8)
ax_c.text(T_EINFL+4, 0.63, r'$\log a$',   fontsize=8, color=LGT)
ax_c.text(T_EW+0.4,  0.24, r'$v_2$',      fontsize=8, color=MID)
ax_c.text(T_NOW+2.3, 1.22, r'$G_\mathrm{eff}$'+'\n(Scen. B)',
          fontsize=7.5, color=MID, ha='center')
ax_c.annotate('Scenario A:\n$v_0 \\to v_\\infty$\neternal expansion',
              xy=(T_NOW+1.1, 0.99), fontsize=8,
              bbox=dict(fc='#F0F0F0', ec='#AAAAAA', lw=0.7, pad=4))
ax_c.annotate('Scenario B:\n$v_0$ slowly $\\to 0$,\n$G_\\mathrm{eff}\\to\\infty$\n'
              'Big Crunch $\\sim 10^{100}$ yr\n(off right axis)',
              xy=(T_NOW+1.1, 0.38), fontsize=7.5,
              bbox=dict(fc='#E8E8E8', ec='#AAAAAA', lw=0.7, pad=4))
ax_c.text(0.005, 0.005,
    r'Note: curves are schematic ($\tanh$-approximations to '
    r'$\ddot{v}_0+3H\dot{v}_0+V^\prime(v_0)=0$); '
    r'quantitative solutions require numerical integration.',
    transform=ax_c.transAxes, fontsize=5.5, color='#666666', va='bottom', style='italic')

add_vlines(ax_c, label_y=1.50, fs=6.0)
ax_c.set_ylim(-0.04, 1.65)
ax_c.set_ylabel('Normalised value', fontsize=10)
ax_c.legend(fontsize=7.5, loc='upper left', bbox_to_anchor=(0.005, 0.99),
            framealpha=0.95, edgecolor='#AAAAAA', handlelength=2.8)
ax_c.yaxis.set_minor_locator(AutoMinorLocator())
ticks = [-43,-40,-35,-30,-20,-10,0,5,10,12.85,17.64,20]
lbls  = [r'$10^{-43}$',r'$10^{-40}$',r'$10^{-35}$',r'$10^{-30}$',
         r'$10^{-20}$',r'$10^{-10}$','1',r'$10^5$',r'$10^{10}$',
         '380\nkyr','13.8\nGyr','']
ax_c.set_xticks(ticks); ax_c.set_xticklabels(lbls, fontsize=8)
ax_c.set_xlabel(r'$\log_{10}(t\,/\,\mathrm{s})$', fontsize=11)

import os
out = '/Users/chufelo/Documents/Physics/VDT/ECT/github_repo'
plt.savefig(os.path.join(out, 'ECT_vs_LCDM_timeline.png'), dpi=200, bbox_inches='tight', facecolor='white')
plt.savefig(os.path.join(out, 'ECT_vs_LCDM_timeline.pdf'), bbox_inches='tight', facecolor='white')
plt.close()
print("Saved to", out)
