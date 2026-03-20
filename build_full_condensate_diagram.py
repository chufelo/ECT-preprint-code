#!/usr/bin/env python3
"""
ECT full conceptual evolution diagram — four horizontal bands.
Diagram-style (axes off), no chart grid, manual annotation boxes.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
from pathlib import Path

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')

plt.rcParams.update({
    'font.family': 'serif',
    'font.size':   9.5,
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'savefig.facecolor': 'white',
})

fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# ── Phase boundaries (x-coordinates) ────────────────────────────────────────
X = dict(
    start      = 0.00,
    end_euclid = 0.08,   # end of Euclidean / pre-Lorentzian
    end_order  = 0.15,   # end of ordering / branch selection
    end_infl   = 0.21,   # end of inflation
    ew_trans   = 0.40,   # EW condensation
    jwst_start = 0.55,   # structure formation / JWST epoch begins
    recomb     = 0.70,   # recombination
    now        = 0.83,   # present day (ECT, 13.02 Gyr)
    end        = 1.00,
)

# ── Band y-ranges ─────────────────────────────────────────────────────────────
# Each band: (y_bottom, y_top)
B = dict(
    title    = (0.93, 1.00),
    order    = (0.74, 0.92),   # band 1: ordering / branch
    grav     = (0.42, 0.73),   # band 2: gravitational condensate
    ew       = (0.18, 0.41),   # band 3: EW condensate
    universe = (0.00, 0.17),   # band 4: observable Universe
)

def band_mid(key): return (B[key][0] + B[key][1]) / 2
def band_h(key):   return B[key][1] - B[key][0]

# ── Colours ───────────────────────────────────────────────────────────────────
COL = dict(
    euclid   = '#c8c8c8',
    order_tr = '#a0a0a0',
    lorentz  = '#e8e8e8',
    future   = '#f0f0f0',
    early_g  = '#d8d8d8',
    late_g   = '#f0f0f0',
    ew_off   = '#e0e0e0',
    ew_on    = '#d0d0d0',
    univ_bg  = '#f4f4f4',
    box_bg   = 'white',
    sep      = '0.40',
    arrow    = '0.20',
)

def rect(x0, x1, y0, y1, color, ec='black', lw=0.5, zorder=1, alpha=1.0):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x0, y0), x1-x0, y1-y0,
        boxstyle='square,pad=0', facecolor=color, edgecolor=ec, lw=lw,
        zorder=zorder, alpha=alpha))

def annot(x, y, text, fs=8.5, ha='center', va='center', bold=False,
          box=True, bfc='white', bec='0.5', blw=0.6, pad=2.5, zorder=5, color='black'):
    kw = dict(ha=ha, va=va, fontsize=fs, color=color, zorder=zorder,
               fontweight='bold' if bold else 'normal', multialignment=ha)
    if box:
        kw['bbox'] = dict(boxstyle='round,pad=%.1f' % (pad/10), fc=bfc, ec=bec, lw=blw)
    ax.text(x, y, text, **kw)

def arrow(x0, y0, x1, y1, color='0.3', lw=1.0, style='->', zorder=4):
    ax.annotate('', xy=(x1,y1), xytext=(x0,y0),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw),
                zorder=zorder)

def vsep(x, y0=0.0, y1=0.93, lw=0.8, ls='--', color='0.40', zorder=6):
    ax.plot([x,x], [y0,y1], ls=ls, lw=lw, color=color, zorder=zorder)

# ════════════════════════════════════════════════════════════════════════════
# TITLE
# ════════════════════════════════════════════════════════════════════════════
ax.text(0.50, 0.965,
        'ECT: schematic full evolution of condensate sectors and observable Universe',
        ha='center', va='center', fontsize=12.5, fontweight='bold')
ax.text(0.50, 0.942,
        r'Hubble-priority: $\omega_0=30$, $\phi_0=-0.10$; '
        r'$\Delta H_0/H_0=+2.73\%$; $H_0^{\rm ECT}=69.2$ km/s/Mpc; '
        r'$t_0^{\rm ECT}=13.02$ Gyr; $G_{\rm eff}(z=10)/G_N\approx1.49$',
        ha='center', va='center', fontsize=8.5, color='0.35')

# ════════════════════════════════════════════════════════════════════════════
# VERTICAL SEPARATORS (behind everything)
# ════════════════════════════════════════════════════════════════════════════
for xv, lbl in [
    (X['end_euclid'],  ''),
    (X['end_order'],   ''),
    (X['end_infl'],    ''),
    (X['ew_trans'],    'EW\ntrans.'),
    (X['jwst_start'],  r'$z\sim14$' '\nJWST'),
    (X['recomb'],      'Recomb.\n380 kyr'),
    (X['now'],         'NOW\n13.02 Gyr'),
]:
    vsep(xv)
    if lbl:
        ax.text(xv, 0.935, lbl, ha='center', va='top', fontsize=7.5,
                color='0.35', multialignment='center')

# ════════════════════════════════════════════════════════════════════════════
# BAND 1 — ORDERING / LORENTZIAN BRANCH
# ════════════════════════════════════════════════════════════════════════════
y0, y1 = B['order']
ym = band_mid('order')

# Background blocks
rect(X['start'],     X['end_euclid'], y0, y1, COL['euclid'])
rect(X['end_euclid'],X['end_order'],  y0, y1, COL['order_tr'])
rect(X['end_order'], X['now'],        y0, y1, COL['lorentz'])
rect(X['now'],       X['end'],        y0, y1, COL['future'])

# Band label
ax.text(-0.003, ym, '(i)\nOrdering /\nLorentzian\nbranch',
        ha='right', va='center', fontsize=9, fontweight='bold',
        multialignment='right')

# Phase labels inside blocks
annot((X['start']+X['end_euclid'])/2, ym,
      'Euclidean /\npre-Lorentzian\nno time, $v_0=0$', fs=8.0, box=False, color='0.20')
annot((X['end_euclid']+X['end_order'])/2, ym,
      'O(4)$\\to$O(3)\nordering\n$\\alpha>1$', fs=8.0, box=False)
annot((X['end_order']+X['now'])/2, ym,
      'Causal macroscopic Lorentzian regime\n'
      r'(ordered branch; $c_*=1/\sqrt{\alpha-1}$; time established)',
      fs=8.5, box=False)
annot((X['now']+X['end'])/2, ym,
      'Scen. A\nor B\nfuture', fs=8.0, box=False, color='0.30')

# Transition arrow
arrow(X['end_euclid']+0.005, ym, X['end_order']-0.005, ym, lw=1.5)

# ════════════════════════════════════════════════════════════════════════════
# BAND 2 — GRAVITATIONAL CONDENSATE
# ════════════════════════════════════════════════════════════════════════════
y0, y1 = B['grav']
ym = band_mid('grav')

rect(X['start'],     X['end_order'],  y0, y1, COL['euclid'],   lw=0.3)
rect(X['end_order'], X['now'],        y0, y1, COL['early_g'])
rect(X['now'],       X['end'],        y0, y1, COL['late_g'])

ax.text(-0.003, ym, '(ii)\nGravitational\ncondensate\n$\\phi$, $G_{\\rm eff}$',
        ha='right', va='center', fontsize=9, fontweight='bold',
        multialignment='right')

# phi curve: schematic rise from very negative to -0.10
xs_g = np.linspace(X['end_order'], X['end'], 400)
phi_vals = -0.10 * (1 + 4.8*(1 - np.tanh(6.0*(xs_g - X['end_order'] - 0.04)/
                                            (X['now']-X['end_order']))))
# Map phi to y: phi=-0.60 → y0+0.07,  phi=-0.10 → y1-0.07
phi_min, phi_max = -0.60, -0.08
y_curve = y0 + 0.07 + (phi_vals - phi_min)/(phi_max - phi_min) * (y1 - y0 - 0.14)
ax.plot(xs_g, y_curve, '-', color='black', lw=2.2, zorder=4,
        label=r'$u/u_\infty = e^{\beta\phi}$ (condensate amplitude)')

# G_eff curve: inverse of phi curve (G_eff = e^{-beta*phi} > 1)
beta = 0.8
G_eff_vals = np.exp(-beta * phi_vals)  # 1.05..~1.6
G_min, G_max = 1.0, 1.70
y_geff = y0 + 0.07 + (G_eff_vals - G_min)/(G_max - G_min) * (y1 - y0 - 0.14)
y_geff = np.clip(y_geff, y0+0.02, y1-0.02)
ax.plot(xs_g, y_geff, '--', color='0.40', lw=1.8, zorder=4,
        label=r'$G_{\rm eff}/G_N = e^{-\beta\phi}$')

# G_eff = 1 reference line
y_ref = y0 + 0.07 + (1.0 - G_min)/(G_max - G_min) * (y1 - y0 - 0.14)
ax.plot([X['end_order'], X['end']], [y_ref, y_ref],
        ':', color='0.60', lw=1.0, zorder=3)
ax.text(X['end']+0.002, y_ref, r'$G_{\rm eff}=G_N$',
        ha='left', va='center', fontsize=7.5, color='0.50')

# Euclidean — inactive stripe
annot((X['start']+X['end_order'])/2, ym,
      'Euclidean phase\n(no $\\phi$, no $G_{\\rm eff}$)', fs=8.0, box=False, color='0.40')

# Early phi annotation
annot(0.30, y0 + 0.07,
      r'$\phi\ll 0$    $u/u_\infty\ll 1$' '\n'
      r'$G_{\rm eff}=G_N e^{-\beta\phi}>G_N$',
      fs=8.5, bec='0.5', pad=2)

# JWST epoch box
xjw = X['jwst_start']
jjw = np.argmin(np.abs(xs_g - xjw))
yp  = float(y_geff[jjw])
arrow(xjw, yp+0.01, xjw, yp+0.055, lw=0.9)
annot(xjw, yp+0.075,
      r'$G_{\rm eff}/G_N\approx1.5$–$1.7$' '\n'
      r'JWST $z\sim10$–$14$' '\n'
      'accelerated local maturity',
      fs=8.0, bec='0.4', pad=2.5)

# Late branch annotation
annot(X['now']+0.055, y0+0.10,
      r'$\phi\to -0.10$' '\n' r'screened branch' '\n' 'benchmark valid',
      fs=8.0, bec='0.5', pad=2)
arrow(X['now']-0.002, float(y_curve[-40]), X['now']+0.005, y0+0.18, lw=0.9)

# Linear growth note
annot(0.62, y0+0.02,
      r'Linear growth $D/D_{\rm ref}\approx0.98$–$0.99$: nearly neutral     '
      r'$R_{\rm BH}\approx1.48$–$1.54$ (BH-assisted maturity dominant)',
      fs=8.0, bec='0.45', pad=2, bfc='#f8f8f8')

# Legend for grav sector
leg_lines = [
    Line2D([0],[0], color='black', lw=2.2, label=r'$u/u_\infty=e^{\beta\phi}$'),
    Line2D([0],[0], color='0.40',  lw=1.8, ls='--', label=r'$G_{\rm eff}/G_N=e^{-\beta\phi}$'),
    Line2D([0],[0], color='0.60',  lw=1.0, ls=':',  label=r'$G_{\rm eff}=G_N$ reference'),
]
ax.legend(handles=leg_lines, loc='upper left',
          bbox_to_anchor=(X['end_order']+0.005, y1-0.005),
          fontsize=8.0, framealpha=0.95, edgecolor='0.5',
          ncol=3, columnspacing=1.0)

# ════════════════════════════════════════════════════════════════════════════
# BAND 3 — ELECTROWEAK CONDENSATE
# ════════════════════════════════════════════════════════════════════════════
y0, y1 = B['ew']
ym = band_mid('ew')

rect(X['start'],    X['ew_trans'],  y0, y1, COL['ew_off'])
rect(X['ew_trans'], X['end'],       y0, y1, COL['ew_on'])

ax.text(-0.003, ym, '(iii)\nElectroweak\ncondensate\n$v_2$',
        ha='right', va='center', fontsize=9, fontweight='bold',
        multialignment='right')

# v2 curve: step at EW transition
xs_ew  = np.linspace(X['start'], X['end'], 600)
v2_y   = np.where(xs_ew < X['ew_trans'],
                   y0 + 0.10,
                   y0 + 0.10 + (y1-y0-0.20)*(1 - np.exp(-30*(xs_ew - X['ew_trans']))))
ax.plot(xs_ew, v2_y, '-', color='black', lw=2.0, zorder=4)

# Before EW
annot((X['start']+X['ew_trans'])/2, ym,
      'EW sector not yet active\n$v_2 = 0$\n(SM gauge bosons massless)',
      fs=8.5, bec='0.5', pad=2.5)

# EW transition arrow
arrow(X['ew_trans']-0.015, ym-0.02, X['ew_trans']+0.005, ym-0.01, lw=1.3)
annot(X['ew_trans']+0.045, ym-0.025,
      'EW condensation\n$v_2=246$ GeV turns on\nW, Z, H mass generation',
      fs=8.5, bec='0.5', pad=2.5)

# After EW
annot((X['ew_trans']+X['end'])/2 + 0.05, y1-0.025,
      r'Late EW-condensed regime: $v_2\approx246$ GeV' '\n'
      'Standard Model fermion masses, Yukawa couplings active',
      fs=8.5, bec='0.5', pad=2.5)

# ════════════════════════════════════════════════════════════════════════════
# BAND 4 — OBSERVABLE UNIVERSE
# ════════════════════════════════════════════════════════════════════════════
y0, y1 = B['universe']
ym = band_mid('universe')

rect(X['start'],     X['end_order'],  y0, y1, '#d4d4d4')
rect(X['end_order'], X['jwst_start'], y0, y1, '#e4e4e4')
rect(X['jwst_start'],X['recomb'],     y0, y1, '#eeeeee')
rect(X['recomb'],    X['now'],        y0, y1, COL['univ_bg'])
rect(X['now'],       X['end'],        y0, y1, COL['future'])

ax.text(-0.003, ym, '(iv)\nObservable\nUniverse',
        ha='right', va='center', fontsize=9, fontweight='bold',
        multialignment='right')

annot((X['start']+X['end_order'])/2, ym,
      'No standard observable\nspacetime', fs=8.0, box=False, color='0.30')
annot((X['end_order']+X['jwst_start'])/2, ym,
      'Lorentzian Universe\n$G_{\\rm eff}>G_N$\ncollapse accelerated',
      fs=8.0, box=False)
annot((X['jwst_start']+X['recomb'])/2, ym,
      'Structure formation\nJWST epoch:\naccelerated maturity',
      fs=8.0, box=False)
annot((X['recomb']+X['now'])/2, ym,
      'CMB / recombination\nRadiation$\\to$matter', fs=8.0, box=False)
annot((X['now']+X['end'])/2, ym,
      'Screened epoch\nbenchmark valid\nScen. A/B', fs=8.0, box=False)

# Key boxes in structure formation
annot(X['jwst_start']+0.01, y0-0.004,
      'linear growth alone not sufficient\nlocal collapse accelerated: '
      r'$t_{\rm ff}\propto G_{\rm eff}^{-1/2}$' '     '
      'BH-assisted channels dominant',
      ha='left', va='top', fs=8.0, bec='0.45', pad=2, bfc='#f4f4f4')

# NOW vertical marker (extra thick)
ax.plot([X['now'], X['now']], [0, 0.92], '-', color='black', lw=1.4, zorder=7)
ax.text(X['now'], -0.025, 'NOW\n(ECT: 13.02 Gyr)', ha='center', va='top',
        fontsize=8.5, fontweight='bold')

# ════════════════════════════════════════════════════════════════════════════
# Phase labels at bottom (shared x-axis)
# ════════════════════════════════════════════════════════════════════════════
phase_labels = [
    ((X['start']+X['end_order'])/2,      'Pre-Lorentzian /\nEuclidean regime'),
    ((X['end_order']+X['end_infl'])/2,   'Ordering /\nbranch selection'),
    ((X['end_infl']+X['ew_trans'])/2,    'Early derived-parent\ncosmology'),
    ((X['ew_trans']+X['recomb'])/2,      'Structure formation era\n(JWST epoch)'),
    ((X['recomb']+X['now'])/2,           'Late radiation/\nmatter domination'),
    ((X['now']+X['end'])/2,              'Late screened\nepoch / future'),
]
for xp, lbl in phase_labels:
    ax.text(xp, -0.045, lbl, ha='center', va='top', fontsize=8.0,
            multialignment='center', color='0.25')

# ════════════════════════════════════════════════════════════════════════════
# Status note at bottom
# ════════════════════════════════════════════════════════════════════════════
ax.text(0.50, -0.095,
        'Note: figure is schematic. Only the gravitational condensate amplitude sector (ii) '
        'is resolved quantitatively in the present derived-parent analysis. '
        'Layers (i), (iii), and (iv) represent the current conceptual ECT picture.',
        ha='center', va='top', fontsize=7.5, color='0.40', style='italic')

out = OUTDIR / 'ect_full_condensate_universe_evolution_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
