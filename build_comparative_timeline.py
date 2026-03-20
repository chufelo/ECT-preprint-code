#!/usr/bin/env python3
"""
ECT comparative cosmological timeline: ΛCDM vs ECT.
NOW anchored at same x-position for both.
ΛCDM Big Bang further LEFT (13.8 Gyr); ECT ordering transition closer to NOW (13.02 Gyr).
~780 Myr difference clearly visible as gap at left edge.
Uses schematic (non-proportional) block widths so early epochs are visible,
while preserving the key visual message: ECT starts later (closer to NOW).
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyArrowPatch
from pathlib import Path

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')
plt.rcParams.update({'font.family':'serif','font.size':9.5,
                     'figure.facecolor':'white','axes.facecolor':'white'})

# ── Epoch definitions: (x_left, x_right, label, color) ──────────────────────
# x-axis: 0=far past → 1=future beyond NOW
# NOW is at x=0.82 for BOTH rows
# Key design principle:
#   - Early epochs (log-scale physics) get fixed minimum widths for visibility
#   - Late epochs (structure formation) get proportional width
#   - The GAP between ΛCDM BB (x=0.10) and ECT OT (x=0.16) represents ~780 Myr
#     and is THE main visual message

X_NOW = 0.82

# Grayscale palette
G = {
    'undef':    '#b0b0b0',
    'euclid':   '#929292',
    'pt':       '#787878',
    'planck':   '#888888',
    'infl':     '#9e9e9e',
    'rad':      '#c4c4c4',
    'ew':       '#b8b8b8',
    'qcd':      '#cccccc',
    'bbn':      '#d4d4d4',
    'recomb':   '#dedede',
    'matter':   '#e4e4e4',
    'struct':   '#ebebeb',
    'de':       '#f2f2f2',
    'future':   '#f8f8f8',
    'gap':      '#a0a0a0',  # the 780 Myr gap region
}

# ── ΛCDM epochs: x positions ─────────────────────────────────────────────────
# Big Bang at x=0.10
# Epoch widths chosen to be visually readable (not proportional)
lcdm = [
    (0.00, 0.10, 'Undefined\n(no spacetime)', G['undef']),
    (0.10, 0.13, 'Planck+\nInflation',         G['planck']),
    (0.13, 0.20, 'Radiation\n(quarks, leptons)', G['rad']),
    (0.20, 0.24, 'EW\ntransition',              G['ew']),
    (0.24, 0.30, 'QCD+BBN',                     G['qcd']),
    (0.30, 0.38, 'Recomb.\n380 kyr',             G['recomb']),
    (0.38, 0.62, 'Radiation/Matter\ndomination', G['matter']),
    (0.62, X_NOW,'Structure\nformation',          G['struct']),
    (X_NOW, 0.93,'Future\n(de Sitter)',           G['de']),
    (0.93, 1.00, '',                              G['future']),
]

# ── ECT epochs: x positions ──────────────────────────────────────────────────
# Ordering transition at x=0.16 (visibly to the RIGHT of ΛCDM BB at 0.10)
# The region 0.10→0.16 in ECT row = Euclidean/pre-Lorentzian (no standard spacetime)
# Same epoch widths as ΛCDM AFTER the ordering transition

X_BB_LCDM = 0.10   # ΛCDM Big Bang
X_OT_ECT  = 0.19   # ECT ordering transition — shifted right to give early blocks space

# ECT early blocks span 0.19→0.44 (same width as ΛCDM 0.10→0.35)
# so early epochs are as readable as in ΛCDM row
_dw = 0.25 / 0.25  # scale factor: 0.25 width maps to 0.25
ect = [
    (0.00, X_BB_LCDM,       'Undefined',                         G['undef']),
    # THE KEY GAP: Euclidean phase in ECT (no ΛCDM analog)
    (X_BB_LCDM, X_OT_ECT,   'Euclidean /\npre-Lorentzian\nphase\n(no time, $v_0=0$)', G['euclid']),
    # After ordering transition — same epochs as ΛCDM, just offset to the right
    (X_OT_ECT,        X_OT_ECT+0.03,  'PT\nO(4)→O(3)',                  G['pt']),
    (X_OT_ECT+0.03,   X_OT_ECT+0.07,  'Inflation-like\nepoch (?)\nopen',G['infl']),
    (X_OT_ECT+0.07,   X_OT_ECT+0.13,  'Radiation\n(as in SM)',           G['rad']),
    (X_OT_ECT+0.13,   X_OT_ECT+0.17,  'EW\n$v_2$=246 GeV',              G['ew']),
    (X_OT_ECT+0.17,   X_OT_ECT+0.22,  'QCD\n+BBN',                      G['qcd']),
    (X_OT_ECT+0.22,   X_OT_ECT+0.29,  'Recomb.\n380 kyr',                G['recomb']),
    (X_OT_ECT+0.29,   0.62,            'Radiation/Matter\ndomination',   G['matter']),
    (0.62, X_NOW,  'Structure +\n$G_{\\rm eff}>G_N$\n(JWST accel.)',  G['struct']),
    (X_NOW, 0.93,  'Future\nScen. A/B',                                  G['de']),
    (0.93,  1.00,  '',                                                     G['future']),
]

# ── Figure ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(16, 5.8),
    gridspec_kw={'height_ratios':[1,1],'hspace':0.05})

Y0, Y1 = 0.12, 0.88  # band y-range

for ax in axes:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    for sp in ax.spines.values(): sp.set_visible(False)

def draw_row(ax, epochs, label):
    for x0, x1, lbl, col in epochs:
        ax.add_patch(Rectangle((x0,Y0), x1-x0, Y1-Y0,
                                facecolor=col, edgecolor='black', lw=0.45))
        if lbl and (x1-x0) > 0.01:
            ax.text((x0+x1)/2, (Y0+Y1)/2, lbl, ha='center', va='center',
                    fontsize=8, multialignment='center', fontweight='bold')
    ax.text(-0.005, (Y0+Y1)/2, label, ha='right', va='center',
            fontsize=11, fontweight='bold',
            transform=ax.transData)

draw_row(axes[0], lcdm, r'(a) $\Lambda$CDM')
draw_row(axes[1], ect,  r'(b) ECT')

# ── NOW line (same for both) ──────────────────────────────────────────────────
for ax in axes:
    ax.axvline(X_NOW, color='black', lw=2.2, zorder=8)
axes[0].text(X_NOW, Y1+0.04, 'NOW', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold')
axes[1].text(X_NOW, Y1+0.04, 'NOW', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold')

# ── ΛCDM Big Bang marker ──────────────────────────────────────────────────────
axes[0].axvline(X_BB_LCDM, color='black', lw=1.5, zorder=7)
axes[0].text(X_BB_LCDM, Y1+0.04, 'Big Bang\n$t=0$',
             ha='center', va='bottom', fontsize=8.5, fontweight='bold')

# ── ECT Ordering Transition marker ───────────────────────────────────────────
axes[1].axvline(X_OT_ECT, color='black', lw=1.5, zorder=7)
axes[1].text(X_OT_ECT, Y1+0.04, 'O(4)→O(3)\nordering trans.',
             ha='center', va='bottom', fontsize=8.5, fontweight='bold')

# ── ΛCDM BB reference dashed line in ECT row ─────────────────────────────────
axes[1].axvline(X_BB_LCDM, color='0.45', ls='--', lw=1.2, zorder=6)
axes[1].text(X_BB_LCDM, Y0-0.06, r'$\Lambda$CDM BB',
             ha='center', va='top', fontsize=8, color='0.40', style='italic')

# ── Age arrows ───────────────────────────────────────────────────────────────
# ΛCDM age arrow
axes[0].annotate('', xy=(X_NOW-0.003, 0.06), xytext=(X_BB_LCDM+0.003, 0.06),
                 arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
axes[0].text((X_BB_LCDM+X_NOW)/2, 0.02,
             r'$t_0^{\Lambda{\rm CDM}} = 13.80$ Gyr',
             ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# ECT age arrow
axes[1].annotate('', xy=(X_NOW-0.003, 0.06), xytext=(X_OT_ECT+0.003, 0.06),
                 arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
axes[1].text((X_OT_ECT+X_NOW)/2, 0.02,
             r'$t_0^{\rm ECT} = 13.02$ Gyr',
             ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# ── Δt=780 Myr gap annotation ────────────────────────────────────────────────
# Double-headed arrow between X_BB_LCDM and X_OT_ECT in the ECT row
axes[1].annotate('', xy=(X_OT_ECT-0.002, 0.50), xytext=(X_BB_LCDM+0.002, 0.50),
                 arrowprops=dict(arrowstyle='<->', color='white', lw=2.0))
axes[1].text((X_BB_LCDM+X_OT_ECT)/2, 0.64,
             r'$\Delta t\approx 780$ Myr' '\n' 'ECT starts later',
             ha='center', va='bottom', fontsize=8.5, fontweight='bold',
             color='white')

# ── Epoch boundary separators (shared) ───────────────────────────────────────
shared_seps = [0.30, 0.38, 0.62]
for ax in axes:
    for xv in shared_seps:
        ax.axvline(xv, color='0.5', ls=':', lw=0.7, alpha=0.6)

# ── x-axis time labels (bottom of ECT panel) ─────────────────────────────────
# Map key times to x positions schematically
time_marks = [
    (X_BB_LCDM,  '13.8\nGyr'),
    (X_OT_ECT,   '13.0\nGyr\n(ECT)'),
    (0.38,        '~13 Gyr'),
    (0.50,        '~10 Gyr'),
    (0.62,        '~5 Gyr'),
    (X_NOW,       'NOW'),
]
for xp, lbl in time_marks:
    axes[1].text(xp, -0.08, lbl, ha='center', va='top',
                 fontsize=8, color='0.35', multialignment='center')

axes[1].text(0.5, -0.20, r'$\longleftarrow$  further in the past',
             ha='center', va='top', fontsize=9, color='0.40',
             transform=axes[1].transAxes)

# ── JWST z~10 markers ────────────────────────────────────────────────────────
# Both are near the same absolute position (z=10 is ~471 Myr after BB for ΛCDM,
# ~394 Myr for ECT, so both fall in the Structure formation era)
x_jwst_lcdm = 0.62 + (X_NOW-0.62)*0.05   # roughly in structure formation
x_jwst_ect  = x_jwst_lcdm
for ax in axes:
    ax.axvline(x_jwst_lcdm, color='0.4', ls=':', lw=1.0)
axes[0].text(x_jwst_lcdm, Y1-0.05, r'$z\sim10$', ha='center', va='top',
             fontsize=8, color='0.35')
axes[1].text(x_jwst_ect+0.015, Y1-0.05,
             r'$z\sim10$' '\n' r'$G_{\rm eff}/G_N\approx1.5$',
             ha='center', va='top', fontsize=7.5, color='0.35')

# ── Title ─────────────────────────────────────────────────────────────────────
fig.suptitle(
    r'Comparative cosmological history: standard $\Lambda$CDM vs ECT'
    '\n'
    r'NOW is anchored at the same point $\bullet$ '
    r'ECT universe is younger by $\Delta t\approx780$ Myr'
    r'  $(\omega_0\!=\!30,\;\phi_0\!=\!-0.10,\;\Delta H_0/H_0\!=\!+2.73\%)$',
    fontsize=11, fontweight='bold', y=1.06)

# ── Status note ───────────────────────────────────────────────────────────────
fig.text(0.5, -0.13,
         'Note: schematic figure; epoch widths are not proportional to duration. '
         'ECT inflation-like epoch and horizon-resolution mechanism remain open '
         '(Level~B/Open). ECT age from derived-parent Hubble-priority parameters.',
         ha='center', va='top', fontsize=7.5, color='0.45', style='italic')

out = OUTDIR / 'ect_vs_lcdm_comparative_timeline_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
