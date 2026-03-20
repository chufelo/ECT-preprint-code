#!/usr/bin/env python3
"""
ECT comparative cosmological timeline: ΛCDM vs ECT (3-row version).
Row (a): Standard ΛCDM
Row (b): ECT cosmological epochs
Row (c): ECT condensate evolution v0/phi (Scenario A + B)

NOW anchored at same x for all rows.
ECT universe is younger by ~780 Myr — visible as gap at left edge.
Scenario B (Big Crunch) shown in far future.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from pathlib import Path

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')
plt.rcParams.update({'font.family':'serif','font.size':9.5,
                     'figure.facecolor':'white','axes.facecolor':'white',
                     'savefig.facecolor':'white'})

# ── x-axis layout ─────────────────────────────────────────────────────────────
# Schematic (non-proportional) widths so all epochs are readable
# x: 0 (far past) → 1 (far future)
# NOW fixed at x = 0.76 for all rows
X_NOW     = 0.76
X_BB      = 0.10   # ΛCDM Big Bang
X_OT      = 0.21   # ECT ordering transition (13.02 Gyr; +780 Myr vs ΛCDM)
X_FUTURE  = 1.00

# Colours (grayscale)
G = dict(
    undef='#b0b0b0', euclid='#909090', pt='#707070',
    infl='#999999',  rad='#c0c0c0',   ew='#b4b4b4',
    qcd='#c8c8c8',   recomb='#d8d8d8', matter='#e2e2e2',
    struct='#ebebeb', de='#f2f2f2',    future_a='#f6f6f6',
    future_b='#d8d8d8',  cond_bg='#fafafa',
)

def band(ax, x0, x1, y0, y1, col, lbl='', fs=8.5, lw=0.5, bold=True):
    ax.add_patch(Rectangle((x0,y0), x1-x0, y1-y0,
                            facecolor=col, edgecolor='black', lw=lw))
    if lbl and (x1-x0) >= 0.01:
        ax.text((x0+x1)/2, (y0+y1)/2, lbl, ha='center', va='center',
                fontsize=fs, multialignment='center',
                fontweight='bold' if bold else 'normal')

# ── Figure: 3 rows ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(17, 8.5),
    gridspec_kw={'height_ratios':[1,1,1.2],'hspace':0.06})

YB, YT = 0.10, 0.90  # band y-range (common)

for ax in axes:
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    for sp in ax.spines.values(): sp.set_visible(False)

# ════════════════════════════════════════════════════════════════════════════
# ROW (a) — ΛCDM
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0]
ax.text(-0.005, 0.50, r'(a) $\Lambda$CDM', ha='right', va='center',
        fontsize=11, fontweight='bold', transform=ax.transData)

# Note: ΛCDM has "undefined" only left of BB (x < 0.10), then epochs
lcdm_epochs = [
    (0.00, X_BB,   'Undefined\n(no spacetime)',                G['undef']),
    (X_BB, 0.13,   'Planck+\nInflation',                       G['infl']),
    (0.13, 0.18,   'Radiation\n(quarks,\nleptons)',             G['rad']),
    (0.18, 0.21,   'EW\ntrans.',                               G['ew']),
    (0.21, 0.26,   'QCD+\nBBN',                               G['qcd']),
    (0.26, 0.34,   'Recomb.\n380 kyr',                         G['recomb']),
    (0.34, 0.55,   'Radiation/Matter\ndomination',             G['matter']),
    (0.55, X_NOW,  'Structure formation',                      G['struct']),
    (X_NOW,0.90,   'Future\n(de Sitter)',                      G['de']),
    (0.90, 1.00,   '',                                         G['future_a']),
]
for x0,x1,lbl,col in lcdm_epochs:
    band(ax, x0, x1, YB, YT, col, lbl)

# Big Bang marker
ax.axvline(X_BB, color='black', lw=1.8, zorder=7)
ax.text(X_BB, YT+0.05, 'Big Bang\n$t=0$', ha='center', va='bottom',
        fontsize=8.5, fontweight='bold')

# ΛCDM age arrow
ax.annotate('', xy=(X_NOW-0.003, 0.08), xytext=(X_BB+0.003, 0.08),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
ax.text((X_BB+X_NOW)/2, 0.03,
        r'$t_0^{\Lambda{\rm CDM}} = 13.80$ Gyr',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# ════════════════════════════════════════════════════════════════════════════
# ROW (b) — ECT cosmological epochs
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1]
ax.text(-0.005, 0.50, '(b) ECT\nepochs', ha='right', va='center',
        fontsize=11, fontweight='bold', transform=ax.transData,
        multialignment='right')

ect_epochs = [
    (0.00,  X_BB,  'Undefined',                                G['undef']),
    # THE KEY: Euclidean phase exists between ΛCDM BB and ECT OT
    (X_BB,  X_OT,  'Euclidean /\npre-Lorentzian phase\n($v_0=0$, no time)', G['euclid']),
    # After ordering transition — wider blocks for readability
    # Merged early blocks — avoids label crowding
    (X_OT,       X_OT+0.06,  'PT O(4)→O(3)\n+Inflation-like\nepoch (?)  open', G['pt']),
    (X_OT+0.06,  X_OT+0.22,  'Radiation, EW $v_2$=246 GeV, QCD+BBN\n(as in SM)', G['rad']),
    (X_OT+0.22,  X_OT+0.31,  'Recombination\n380 kyr',        G['recomb']),
    (X_OT+0.31,  0.55,        'Radiation/Matter\ndomination',  G['matter']),
    (0.55,  X_NOW, 'Structure +\n$G_{\\rm eff}>G_N$\n(JWST accel.)', G['struct']),
    (X_NOW, 0.88,  'Scen. A:\n$v_0\\to v_\\infty$\neternal',  G['future_a']),
    (0.88,  1.00,  'Scen. B:\n$v_0\\to 0$\nBig Crunch\n$\\sim10^{100}$ yr', G['future_b']),
]
for x0,x1,lbl,col in ect_epochs:
    band(ax, x0, x1, YB, YT, col, lbl)

# ECT ordering transition
ax.axvline(X_OT, color='black', lw=1.8, zorder=7)
ax.text(X_OT, YT+0.05, 'O(4)→O(3)\nordering trans.',
        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

# ΛCDM BB reference (dashed)
ax.axvline(X_BB, color='0.45', ls='--', lw=1.2, zorder=6)
ax.text(X_BB, YB-0.07, r'$\Lambda$CDM BB', ha='center', va='top',
        fontsize=8, color='0.40', style='italic')

# ECT age arrow
ax.annotate('', xy=(X_NOW-0.003, 0.08), xytext=(X_OT+0.003, 0.08),
            arrowprops=dict(arrowstyle='<->', color='black', lw=1.3))
ax.text((X_OT+X_NOW)/2, 0.03,
        r'$t_0^{\rm ECT} = 13.02$ Gyr',
        ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Δt gap annotation
axes[1].annotate('', xy=(X_OT-0.002, 0.50),
                 xytext=(X_BB+0.002, 0.50),
                 arrowprops=dict(arrowstyle='<->', color='white', lw=2.0))
axes[1].text((X_BB+X_OT)/2, 0.67,
             r'$\Delta t\approx780$ Myr', ha='center', va='bottom',
             fontsize=8.5, fontweight='bold', color='white')

# Scenario B arrow annotation
ax.annotate('',xy=(0.94, YT-0.12), xytext=(0.94, YT-0.32),
            arrowprops=dict(arrowstyle='->', color='black', lw=1.0))
ax.text(0.94, YT-0.33,
        r'$G_{\rm eff}\to\infty$',
        ha='center', va='top', fontsize=7.5,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))

# ════════════════════════════════════════════════════════════════════════════
# ROW (c) — ECT condensate evolution
# ════════════════════════════════════════════════════════════════════════════
ax = axes[2]
ax.text(-0.005, 0.50, '(c) ECT\ncondensate\n$v_0(t)$, $\\phi(t)$',
        ha='right', va='center', fontsize=11, fontweight='bold',
        transform=ax.transData, multialignment='right')

# Background
band(ax, 0.00, X_BB,   0.05, 0.95, G['undef'],    '', fs=7)
band(ax, X_BB, X_OT,   0.05, 0.95, G['euclid'],   'Euclidean\n$v_0=0$\n$\\phi$ undef.', fs=7.5)
band(ax, X_OT, X_NOW,  0.05, 0.95, G['cond_bg'],  '', fs=7)
band(ax, X_NOW, 0.88,  0.05, 0.95, G['future_a'], '', fs=7)
band(ax, 0.88,  1.00,  0.05, 0.95, G['future_b'], '', fs=7)

xs = np.linspace(X_OT, 1.00, 600)

# ── v0/v_inf Scenario A: rises sharply after OT, stays at ~1 ─────────────
v0_A = np.zeros(len(xs))
for i,x in enumerate(xs):
    if x < X_OT + 0.025:
        v0_A[i] = 0.50*(1 + np.tanh(40*(x-(X_OT+0.012))))
    else:
        v0_A[i] = 1.0
# small inflationary dip
dip = (xs > X_OT+0.025) & (xs < X_OT+0.07)
v0_A[dip] = 0.93 + 0.07*np.tanh(25*(xs[dip]-(X_OT+0.05)))
ax.plot(xs, 0.12 + v0_A*0.55, '-', color='black', lw=2.2,
        label=r'$v_0(t)/v_\infty$ — Scen. A')

# ── v0 Scenario B: starts same, drops after NOW ───────────────────────────
v0_B = v0_A.copy()
mask_B = xs > X_NOW + 0.03
v0_B[mask_B] = np.exp(-4.5*(xs[mask_B]-(X_NOW+0.03)))
ax.plot(xs[xs>=X_NOW], 0.12 + v0_B[xs>=X_NOW]*0.55,
        ':', color='black', lw=2.0, label=r'$v_0(t)/v_\infty$ — Scen. B ($\to0$)')

# ── φ(t): starts very negative at OT, rises to −0.10 by NOW ──────────────
# phi_norm: 0=phi_early(−0.60) → 1=phi_now(−0.10)
phi_norm = 1 - np.exp(-4.5*(xs - X_OT)/(X_NOW-X_OT))
phi_norm = np.clip(phi_norm, 0, 1)
# Map: 0→y=0.15, 1→y=0.60
y_phi = 0.15 + phi_norm*0.45
ax.plot(xs[xs<=X_NOW+0.01], y_phi[xs<=X_NOW+0.01],
        '--', color='0.40', lw=1.8,
        label=r'$\phi(t)$: $\phi\ll0$ early $\to$ $\phi\to-0.10$ now')

# ── G_eff/G_N = exp(−βφ) ─────────────────────────────────────────────────
beta = 0.8; phi_vals = -0.60 + 0.50*phi_norm  # phi: −0.60 → −0.10
G_eff = np.exp(-beta*phi_vals)  # 1.6 → 1.08
# Scen B future: G_eff diverges
G_eff_B = G_eff.copy()
mB = xs > X_NOW+0.04
G_eff_B[mB] = G_eff[np.searchsorted(xs, X_NOW+0.04)] * np.exp(3*(xs[mB]-(X_NOW+0.04)))
G_eff_B = np.clip(G_eff_B, 1, 2.5)
y_Geff = 0.12 + (G_eff_B - 1.0)/(2.5 - 1.0) * 0.55
ax.plot(xs, y_Geff, '-.', color='0.35', lw=1.6,
        label=r'$G_{\rm eff}(t)/G_N=e^{-\beta\phi}$')

# G_eff=1 reference
y_ref = 0.12 + 0.0/1.5*0.55
ax.axhline(0.12, color='0.65', ls=':', lw=0.9)
ax.text(X_NOW+0.005, 0.12, r'$G_{\rm eff}=G_N$', va='center', fontsize=7.5, color='0.55')

# Key annotations
ax.text(X_OT+0.005, 0.79, r'$v_0$ rises', ha='left', va='center',
        fontsize=8, color='black',
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))
ax.text((X_OT+0.55)/2, 0.82,
        r'$\phi\ll0$,  $G_{\rm eff}/G_N\approx1.5$–$1.7$',
        ha='center', va='center', fontsize=8.5,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=2))
ax.text(X_NOW-0.01, 0.82, r'$\phi\to-0.10$'+'\nscreened',
        ha='right', va='center', fontsize=8,
        bbox=dict(fc='white', ec='0.5', lw=0.5, pad=1.5))
ax.text(0.92, 0.78, r'Scen. B:'+'\n'+r'$G_{\rm eff}\to\infty$',
        ha='center', va='center', fontsize=8,
        bbox=dict(fc='white', ec='0.6', lw=0.6, pad=2))
ax.text((X_BB+X_OT)/2, 0.50, r'$v_0=0$'+'\n'+r'$\phi$ undefined',
        ha='center', va='center', fontsize=8.5, color='white', fontweight='bold')

# Legend
leg = ax.legend(fontsize=8.5, loc='lower right', framealpha=0.95,
                edgecolor='0.5', ncol=2, columnspacing=0.8,
                bbox_to_anchor=(0.99, 0.01))

# Separators
for ax2 in axes:
    for xv in [X_BB, X_OT, 0.34, 0.48, 0.55, X_NOW]:
        ax2.axvline(xv, color='0.45', ls=':', lw=0.6, alpha=0.5, zorder=4)

# ════════════════════════════════════════════════════════════════════════════
# SHARED: NOW marker + x-axis labels
# ════════════════════════════════════════════════════════════════════════════
for i, ax2 in enumerate(axes):
    ax2.axvline(X_NOW, color='black', lw=2.2, zorder=9)
axes[0].text(X_NOW, YT+0.05, 'NOW', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold')
axes[1].text(X_NOW, YT+0.05, 'NOW', ha='center', va='bottom',
             fontsize=10.5, fontweight='bold')
axes[2].text(X_NOW, 0.97, 'NOW', ha='center', va='top',
             fontsize=10, fontweight='bold')

# z~10 dotted markers
for ax2 in axes[:2]:
    ax2.axvline(0.63, color='0.4', ls=':', lw=1.0)
axes[0].text(0.63, YT-0.05, r'$z\sim10$', ha='center', va='top', fontsize=8, color='0.35')
axes[1].text(0.63, YT-0.05, r'$z\sim10$', ha='center', va='top', fontsize=7.5, color='0.35')

# x-axis time ticks (bottom of panel c)
tick_xvals = [X_BB, X_OT, 0.40, 0.55, 0.67, X_NOW, 0.88]
tick_lbls  = ['13.8\nGyr', '13.0\nGyr\n(ECT)', '~11\nGyr', '~8\nGyr',
               '~5\nGyr', 'NOW', r'$10^{100}$yr'+'\n(Scen.B)']
for xp, lbl in zip(tick_xvals, tick_lbls):
    axes[2].text(xp, -0.08, lbl, ha='center', va='top',
                 fontsize=8, color='0.30', multialignment='center',
                 transform=axes[2].transData)

axes[2].text(0.5, -0.21, r'$\longleftarrow$  further in the past',
             ha='center', va='top', fontsize=9, color='0.40',
             transform=axes[2].transAxes)

# ════════════════════════════════════════════════════════════════════════════
# Title + status note
# ════════════════════════════════════════════════════════════════════════════
fig.suptitle(
    r'Comparative cosmological history: standard $\Lambda$CDM vs ECT''\n'
    r'NOW anchored at same point $\bullet$ '
    r'ECT younger by $\Delta t\approx780$ Myr $\bullet$ '
    r'Scen.\,B: Big Crunch at $\sim10^{100}$ yr'
    r'   $(\omega_0\!=\!30,\;\phi_0\!=\!-0.10,\;\Delta H_0/H_0\!=\!+2.73\%)$',
    fontsize=11, fontweight='bold', y=1.04)

fig.text(0.5, -0.10,
         'Note: schematic; epoch widths non-proportional. '
         'ECT inflation-like epoch and horizon-resolution mechanism remain open (Level~B/Open). '
         'Condensate curves schematic; only $\\phi$-sector resolved quantitatively.',
         ha='center', va='top', fontsize=7.5, color='0.45', style='italic')

out = OUTDIR / 'ect_vs_lcdm_comparative_timeline_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
