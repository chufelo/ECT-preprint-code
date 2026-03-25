#!/usr/bin/env python3
"""
ECT comparative cosmological timeline — 3-row, staggered labels.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from pathlib import Path

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')
plt.rcParams.update({'font.family':'serif','font.size':9.5,
                     'figure.facecolor':'white','axes.facecolor':'white',
                     'savefig.facecolor':'white'})

X_NOW = 0.76
X_BB  = 0.10   # ΛCDM Big Bang
X_OT  = 0.21   # ECT ordering transition

G = dict(
    undef='#b0b0b0', euclid='#909090', pt='#6e6e6e',
    infl='#999999',  rad='#c0c0c0',   ew='#b4b4b4',
    qcd='#c8c8c8',   recomb='#d8d8d8', matter='#e2e2e2',
    struct='#ebebeb', de='#f2f2f2',
    future_a='#f6f6f6', future_b='#d0d0d0',
    cond_bg='#fafafa',
)

YB, YT = 0.05, 0.95   # band y range

def rect(ax, x0, x1, col, lw=0.5):
    ax.add_patch(Rectangle((x0, YB), x1-x0, YT-YB,
                            facecolor=col, edgecolor='black', lw=lw, zorder=1))

def lbl(ax, x0, x1, text, ypos='mid', fs=8.5, bold=True, clip=True):
    """Place label; ypos: 'mid','top','bot','top2','bot2'."""
    xm = (x0+x1)/2
    yd = {'mid': (YB+YT)/2,
          'top': YT - 0.13*(YT-YB),
          'bot': YB + 0.13*(YT-YB),
          'top2': YT - 0.28*(YT-YB),
          'bot2': YB + 0.28*(YT-YB)}
    y  = yd.get(ypos, (YB+YT)/2)
    va = 'center'
    ax.text(xm, y, text, ha='center', va=va, fontsize=fs,
            fontweight='bold' if bold else 'normal',
            multialignment='center', zorder=3,
            clip_on=True)

def lbl_out(ax, x0, x1, text, above=True, fs=8.0):
    """Label outside (above/below) the band with a small tick."""
    xm = (x0+x1)/2
    y0_tick = YT if above else YB
    y_text  = YT+0.06 if above else YB-0.06
    ax.plot([xm, xm], [y0_tick, y_text], color='black', lw=0.6, zorder=4)
    ax.text(xm, y_text, text, ha='center',
            va='bottom' if above else 'top',
            fontsize=fs, multialignment='center', zorder=5)

fig, axes = plt.subplots(3, 1, figsize=(18, 9.5),
    gridspec_kw={'height_ratios':[1,1,1.3],'hspace':0.10})

for ax in axes:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    for sp in ax.spines.values(): sp.set_visible(False)

# ── Shared epoch separators ───────────────────────────────────────────────────
shared_v = [X_BB, X_OT, 0.34, 0.50, 0.58, X_NOW]
for ax in axes:
    for xv in shared_v:
        ax.axvline(xv, color='0.55', ls=':', lw=0.55, alpha=0.55, zorder=2)

# ════════════════════════════════════════════════════════════════════════════
# ROW (a) — ΛCDM
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0]
ax.text(-0.003, 0.50, r'(a) $\Lambda$CDM', ha='right', va='center',
        fontsize=11, fontweight='bold', transform=ax.transData)

lcdm_segs = [
    (0.00,  X_BB,   G['undef']),
    (X_BB,  0.13,   G['infl']),
    (0.13,  0.18,   G['rad']),
    (0.18,  0.21,   G['ew']),
    (0.21,  0.26,   G['qcd']),
    (0.26,  0.34,   G['recomb']),
    (0.34,  0.50,   G['matter']),
    (0.50,  X_NOW,  G['struct']),
    (X_NOW, 0.90,   G['de']),
    (0.90,  1.00,   G['future_a']),
]
for x0,x1,col in lcdm_segs:
    rect(ax, x0, x1, col)

# Staggered labels ΛCDM — early block alternates above/inside
lbl(ax, 0.00,  X_BB,  'Undefined\n(no spacetime)',     'mid', fs=8)
lbl_out(ax, X_BB, 0.13, 'Planck+\nInflation',          above=True, fs=8)
lbl(ax, 0.13,  0.18,  'Radiation\n(quarks,\nleptons)', 'bot', fs=7.5)
lbl_out(ax, 0.18, 0.21, 'EW\ntrans.',                  above=False, fs=7.5)
lbl(ax, 0.21,  0.26,  'QCD+\nBBN',                    'top', fs=7.5)
lbl(ax, 0.26,  0.34,  'Recomb.\n380 kyr',              'mid', fs=8)
lbl(ax, 0.34,  0.50,  'Radiation/Matter\ndomination',  'mid', fs=8.5)
lbl(ax, 0.50,  X_NOW, 'Structure formation',           'mid', fs=9)
lbl(ax, X_NOW, 0.90,  'Future\n(de Sitter)',           'mid', fs=8.5)

# Big Bang marker
ax.axvline(X_BB, color='black', lw=1.8, zorder=7)
ax.text(X_BB, YT+0.10, 'Big Bang\n$t=0$', ha='center', va='bottom',
        fontsize=9, fontweight='bold')

# Age arrow
ax.annotate('', xy=(X_NOW-0.003, 0.04), xytext=(X_BB+0.003, 0.04),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
ax.text((X_BB+X_NOW)/2, 0.01,
        r'$t_0^{\Lambda{\rm CDM}} = 13.80$ Gyr',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# z~10
ax.axvline(0.63, color='0.4', ls=':', lw=1.0)
ax.text(0.63, YT-0.08, r'$z\!\sim\!10$', ha='center', va='top',
        fontsize=8, color='0.35')

# ════════════════════════════════════════════════════════════════════════════
# ROW (b) — ECT epochs
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1]
ax.text(-0.003, 0.50, '(b) ECT\nepochs', ha='right', va='center',
        fontsize=11, fontweight='bold', transform=ax.transData,
        multialignment='right')

# Epoch colours only (no text yet)
ect_segs = [
    (0.00,  X_BB,        G['undef']),
    (X_BB,  X_OT,        G['euclid']),   # Euclidean gap
    (X_OT,  X_OT+0.06,  G['pt']),
    (X_OT+0.06, X_OT+0.16, G['infl']),
    (X_OT+0.16, X_OT+0.24, G['rad']),
    (X_OT+0.24, X_OT+0.29, G['recomb']),
    (X_OT+0.29, 0.50,    G['matter']),
    (0.50,  X_NOW,       G['struct']),
    (X_NOW, 0.88,        G['future_a']),
    (0.88,  1.00,        G['future_b']),
]
for x0,x1,col in ect_segs:
    rect(ax, x0, x1, col)

# Labels — staggered to avoid overlap
lbl(ax, 0.00,  X_BB,  'Undefined',                           'mid', fs=8)
# Euclidean block: inside, small
lbl(ax, X_BB,  X_OT,  'Euclidean /\npre-Lorentzian\nphase\n($u_0\!=\!0$, no time)',
    'mid', fs=7.5)
# PT: outside above (too narrow for inside)
lbl_out(ax, X_OT, X_OT+0.06, 'PT\nO(4)→O(3)',               above=True, fs=7.5)
# Inflation-like: outside below
lbl_out(ax, X_OT+0.06, X_OT+0.16,
        'Inflation-like\nepoch (?)\nopen',                   above=False, fs=7.5)
# Radiation: outside above
lbl_out(ax, X_OT+0.16, X_OT+0.24,
        'Radiation,\nEW $v_2$=246 GeV,\nQCD+BBN (as in SM)', above=True, fs=7.5)
# Recomb: outside below
lbl_out(ax, X_OT+0.24, X_OT+0.29, 'Recomb.\n380 kyr',       above=False, fs=7.5)
# Matter: inside
lbl(ax, X_OT+0.29, 0.50, 'Radiation/Matter\ndomination',    'mid', fs=8)
# Structure
lbl(ax, 0.50,  X_NOW,
    'Structure +\n$G_{\\rm eff}>G_N$\n(JWST accel.)',         'mid', fs=8.5)
# Future A / B
lbl(ax, X_NOW, 0.88, 'Scen. A:\n$u_0$ nonzero asympt.\neternal', 'mid', fs=8)
lbl(ax, 0.88,  1.00,
    'Scen. B:\n$u_0\\to 0$\nBig Crunch\n$\\sim\\!10^{100}$yr',  'mid', fs=7.5)

# Scen B arrow: G_eff diverges
ax.annotate('', xy=(0.94, YT-0.12), xytext=(0.94, YT-0.30),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.0))
ax.text(0.94, YT-0.31, r'$G_{\rm eff}\to\infty$',
        ha='center', va='top', fontsize=7.5,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))

# ECT ordering transition marker
ax.axvline(X_OT, color='black', lw=1.8, zorder=7)
ax.text(X_OT, YT+0.18, 'O(4)→O(3)\nordering trans.',
        ha='center', va='bottom', fontsize=9, fontweight='bold')

# ΛCDM BB reference
ax.axvline(X_BB, color='0.45', ls='--', lw=1.2, zorder=6)
ax.text(X_BB, YB-0.10, r'$\Lambda$CDM BB',
        ha='center', va='top', fontsize=8, color='0.40', style='italic')

# ECT age arrow
ax.annotate('', xy=(X_NOW-0.003, 0.04), xytext=(X_OT+0.003, 0.04),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
ax.text((X_OT+X_NOW)/2, 0.01,
        r'$t_0^{\rm ECT} = 13.02$ Gyr',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Δt annotation inside Euclidean block (white text on dark bg)
axes[1].annotate('', xy=(X_OT-0.003, 0.55), xytext=(X_BB+0.003, 0.55),
                 arrowprops=dict(arrowstyle='<->', color='white', lw=2.0))
axes[1].text((X_BB+X_OT)/2, 0.68,
             r'$\Delta t\!\approx\!780$ Myr',
             ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='white')

# z~10
ax.axvline(0.63, color='0.4', ls=':', lw=1.0)
ax.text(0.63, YT-0.08, r'$z\!\sim\!10$',
        ha='center', va='top', fontsize=8, color='0.35')

# ════════════════════════════════════════════════════════════════════════════
# ROW (c) — Condensate evolution
# ════════════════════════════════════════════════════════════════════════════
ax = axes[2]
ax.text(-0.003, 0.50, '(c) ECT\ncondensate\n$u_0(t),\\phi(t)$',
        ha='right', va='center', fontsize=11, fontweight='bold',
        transform=ax.transData, multialignment='right')

# Background
ax.add_patch(Rectangle((0.00, 0.05), X_BB,     0.90, facecolor=G['undef'],    ec='black', lw=0.5))
ax.add_patch(Rectangle((X_BB, 0.05), X_OT-X_BB, 0.90, facecolor=G['euclid'], ec='black', lw=0.5))
ax.add_patch(Rectangle((X_OT, 0.05), X_NOW-X_OT, 0.90, facecolor=G['cond_bg'], ec='black', lw=0.5))
ax.add_patch(Rectangle((X_NOW, 0.05), 0.88-X_NOW, 0.90, facecolor=G['future_a'], ec='black', lw=0.5))
ax.add_patch(Rectangle((0.88, 0.05),  0.12,       0.90, facecolor=G['future_b'],  ec='black', lw=0.5))

xs = np.linspace(X_OT, 1.00, 600)

# v0 Scenario A
v0_A = np.zeros(len(xs))
for i,x in enumerate(xs):
    if x < X_OT + 0.025:
        v0_A[i] = 0.5*(1 + np.tanh(40*(x-(X_OT+0.012))))
    else:
        v0_A[i] = 1.0
dip = (xs > X_OT+0.025) & (xs < X_OT+0.07)
v0_A[dip] = 0.93 + 0.07*np.tanh(25*(xs[dip]-(X_OT+0.05)))
yA = 0.12 + v0_A*0.55

# v0 Scenario B
v0_B = v0_A.copy()
mB = xs > X_NOW + 0.03
v0_B[mB] = np.exp(-4.5*(xs[mB]-(X_NOW+0.03)))
yB = 0.12 + v0_B*0.55

ax.plot(xs, yA, '-', color='black', lw=2.3,
        label=r'$u_0(t)/u_0(\infty)$ — Scen. A')
ax.plot(xs[xs >= X_NOW], yB[xs >= X_NOW],
        ':', color='black', lw=2.0,
        label=r'$u_0(t)/u_0(\infty)$ — Scen. B ($u_0\to0$)')

# φ(t): normalised rise
phi_n = 1 - np.exp(-4.5*(xs-X_OT)/(X_NOW-X_OT))
phi_n = np.clip(phi_n, 0, 1)
y_phi = 0.15 + phi_n*0.42
ax.plot(xs[xs <= X_NOW+0.01], y_phi[xs <= X_NOW+0.01],
        '--', color='0.40', lw=1.9,
        label=r'$\phi(t)$: $\phi\ll0$ early $\to$ $\phi\to-0.10$ now')

# G_eff
beta = 0.8
phi_v = -0.60 + 0.50*phi_n
G_eff = np.exp(-beta*phi_v)
G_B = G_eff.copy()
mGB = xs > X_NOW+0.04
G_B[mGB] = G_eff[np.searchsorted(xs, X_NOW+0.04)] * np.exp(3*(xs[mGB]-(X_NOW+0.04)))
G_B = np.clip(G_B, 1, 2.8)
y_G = 0.12 + (G_B-1.0)/1.8*0.55
ax.plot(xs, y_G, '-.', color='0.35', lw=1.7,
        label=r'$G_{\rm eff}(t)/G_N=e^{-\beta\phi}$')
ax.axhline(0.12, color='0.65', ls=':', lw=0.9)
ax.text(X_NOW+0.007, 0.12, r'$G_{\rm eff}\!=\!G_N$',
        va='center', fontsize=7.5, color='0.50')

# ── Annotations — staggered to avoid overlap ──────────────────────────────
# Euclidean region label
ax.text((X_BB+X_OT)/2, 0.55,
        r'$u_0=0$' '\n' r'$\phi$ undef.',
        ha='center', va='center', fontsize=8.5, color='white',
        fontweight='bold', multialignment='center')

# v0 rises — outside top
ax.annotate('$u_0$ rises\nafter PT',
            xy=(X_OT+0.015, yA[5]), xytext=(X_OT-0.005, 0.88),
            fontsize=8, ha='center',
            arrowprops=dict(arrowstyle='->', lw=0.8, color='black'),
            bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))

# G_eff > G_N annotation — top centre of early region
ax.text((X_OT+0.15+0.55)/2, 0.90,
        r'$\phi\ll0$,   $G_{\rm eff}/G_N\approx1.5$–$1.7$   (JWST epoch)',
        ha='center', va='top', fontsize=8.5,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=2))

# phi -> -0.10 screened — below the phi curve at NOW
ax.text(X_NOW-0.015, 0.22,
        r'$\phi\to-0.10$'+'\nscreened\nbranch',
        ha='right', va='bottom', fontsize=8,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))

# Scen B divergence
ax.text(0.94, 0.80,
        r'Scen. B:' '\n' r'$G_{\rm eff}\to\infty$',
        ha='center', va='top', fontsize=8,
        bbox=dict(fc='white', ec='0.6', lw=0.6, pad=2))

# Legend — bottom right
ax.legend(fontsize=8.5, loc='lower right', framealpha=0.97,
          edgecolor='0.5', ncol=2, columnspacing=0.8,
          bbox_to_anchor=(0.998, 0.01))

# ════════════════════════════════════════════════════════════════════════════
# SHARED: NOW line + z~10 in row c
# ════════════════════════════════════════════════════════════════════════════
for ax in axes:
    ax.axvline(X_NOW, color='black', lw=2.2, zorder=9)
axes[0].text(X_NOW, YT+0.10, 'NOW', ha='center', va='bottom',
             fontsize=11, fontweight='bold')
axes[1].text(X_NOW, YT+0.36, 'NOW', ha='center', va='bottom',
             fontsize=11, fontweight='bold')
axes[2].text(X_NOW, 0.97, 'NOW', ha='center', va='top',
             fontsize=10, fontweight='bold')

axes[2].axvline(0.63, color='0.4', ls=':', lw=1.0)
axes[2].text(0.63, 0.97, r'$z\!\sim\!10$',
             ha='center', va='top', fontsize=8, color='0.35')

# ════════════════════════════════════════════════════════════════════════════
# Row labels (left axis)
# ════════════════════════════════════════════════════════════════════════════
# (already done inline above)

# ════════════════════════════════════════════════════════════════════════════
# x-axis time scale (bottom of row c)
# ════════════════════════════════════════════════════════════════════════════
tmarks = [(X_BB, '13.8\nGyr'), (X_OT, '13.0\nGyr\n(ECT)'),
          (0.40, '~11 Gyr'), (0.53, '~8 Gyr'),
          (0.66, '~5 Gyr'),  (X_NOW, 'NOW'), (0.94, r'$10^{100}$yr'+'\n(Scen.B)')]
for xp, lb in tmarks:
    axes[2].text(xp, -0.07, lb, ha='center', va='top',
                 fontsize=8, color='0.30', multialignment='center',
                 transform=axes[2].transData)
axes[2].text(0.5, -0.20,
             r'$\longleftarrow$  further in the past',
             ha='center', va='top', fontsize=9, color='0.40',
             transform=axes[2].transAxes)

# ════════════════════════════════════════════════════════════════════════════
# Title + note
# ════════════════════════════════════════════════════════════════════════════
fig.suptitle(
    r'Comparative cosmological history: standard $\Lambda$CDM vs ECT' '\n'
    r'NOW anchored at same point $\bullet$ '
    r'ECT younger by $\Delta t\approx780$ Myr $\bullet$ '
    r'Scen.~B: Big Crunch at $\sim10^{100}$ yr'
    r'   $(\omega_0\!=\!30,\;\phi_0\!=\!-0.10,\;\Delta H_0/H_0\!=\!+2.73\%)$',
    fontsize=11, fontweight='bold', y=1.03)

fig.text(0.5, -0.09,
    'Note: schematic; epoch widths non-proportional. '
    'ECT inflation-like epoch and horizon-resolution mechanism remain open (Level~B/Open). '
    r'Condensate curves schematic; only $\phi$-sector resolved quantitatively.',
    ha='center', va='top', fontsize=7.5, color='0.45', style='italic')

out = OUTDIR / 'ect_vs_lcdm_comparative_timeline_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
