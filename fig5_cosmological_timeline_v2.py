#!/usr/bin/env python3
"""
fig5_cosmological_timeline_v2.py
=================================
Updated timeline figure for ECT preprint.
Same format as the original fig5_ECT_timeline_condensate.png, but
updated with derived-parent ECT numerical results:
  - t0(ECT) = 13.02 Gyr  (Hubble-priority: omega0=30, phi0=-0.10)
  - H0(ECT) = 69.2 km/s/Mpc  (DeltaH0/H0 = +2.73%)
  - G_eff(z=10)/G_N = 1.49,  G_eff(z=14)/G_N ~ 1.7
  - phi(z=0) = -0.10,  phi(z=10) ~ -0.38  (derived-parent)
  - R_gal ~ 1.21,  R_BH ~ 1.48-1.51  at z=10
  - Benchmark truncation valid near screened branch (phi -> 0)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.linewidth': 0.8,
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
})

# Grayscale palette (matching original)
G = dict(
    undefined = '#999999',
    planck    = '#666666',
    inflation = '#888888',
    radiation = '#bbbbbb',
    ew        = '#aaaaaa',
    qcd       = '#999999',
    bbn       = '#cccccc',
    recomb    = '#dddddd',
    structure = '#e8e8e8',
    dark_en   = '#d0d0d0',
    scen_a    = '#e0e0e0',
    scen_b    = '#c0c0c0',
)

# ── Time conversions ───────────────────────────────────────────────────────
# log10(t/s):
#   Planck time   ~ 5.4e-44 s → -43.3
#   Phase trans   ~ 1e-42 s
#   End inflation ~ 1e-32 s → -32
#   EW transition ~ 1e-10 s → -10
#   QCD/BBN       ~ 1e-4..1 s → -4..0
#   Recombination ~ 380 kyr = 1.2e13 s → 13.1
#   JWST z=14     ~ 0.239 Gyr = 7.5e15 s → 15.88
#   JWST z=10     ~ 0.394 Gyr = 1.24e16 s → 16.09
#   NOW (LCDM)    ~ 13.8 Gyr = 4.35e17 s → 17.64
#   NOW (ECT)     ~ 13.02 Gyr = 4.11e17 s → 17.61
#   Future        up to 20

LOG_PT      = -42.0
LOG_END_INF = -32.0
LOG_EW      = -10.0
LOG_QCD     = -4.0
LOG_BBN     = -1.0
LOG_RECOMB  = 13.1
LOG_JWST14  = 15.88   # z=14.32, t=0.239 Gyr
LOG_JWST10  = 16.09   # z=10.60, t=0.394 Gyr
LOG_NOW_LCDM= 17.64   # 13.8 Gyr
LOG_NOW_ECT = 17.61   # 13.02 Gyr (Hubble-priority)
LOG_MAX     = 20.5

def make_epoch_bar(ax, x0, x1, label, color, y0=0.10, y1=0.90, fs=7.5, bold=True):
    rect = Rectangle((x0, y0), x1-x0, y1-y0,
                     facecolor=color, edgecolor='black', lw=0.5)
    ax.add_patch(rect)
    xm = (x0+x1)/2
    ax.text(xm, (y0+y1)/2, label, ha='center', va='center',
            fontsize=fs, fontweight='bold' if bold else 'normal',
            wrap=True, multialignment='center')

def add_vline(ax, x, label='', y_label=0.93, fs=6, color='black', ls='--', lw=0.8):
    ax.axvline(x, color=color, ls=ls, lw=lw)
    if label:
        ax.text(x, y_label, label, ha='center', va='bottom', fontsize=fs, color=color)

# ══════════════════════════════════════════════════════════════════════════
# Figure layout: 3 tall panels + note row
# ══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12.5))
gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 1.7], hspace=0.32)

XMIN, XMAX = -44, 21.5

# ══════════════════════════════════════════════════════════════════════════
# Panel (a) — Standard ΛCDM
# ══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_subplot(gs[0])
ax1.set_xlim(XMIN, XMAX); ax1.set_ylim(0, 1); ax1.set_yticks([])
ax1.text(-0.01, 1.01, r'(a) Standard $\Lambda$CDM',
         transform=ax1.transAxes, fontsize=11, fontweight='bold', va='bottom')

lcdm_epochs = [
    (XMIN,     LOG_PT,      'Undefined\n(no spacetime)',          G['undefined']),
    (LOG_PT,   LOG_END_INF, 'Planck+\nInflation',                 G['planck']),
    (LOG_END_INF, LOG_EW,   'Radiation\n(quarks, leptons)',        G['radiation']),
    (LOG_EW,   LOG_QCD,     'EW\ntransition',                     G['ew']),
    (LOG_QCD,  LOG_RECOMB,  'QCD+BBN',                            G['qcd']),
    (LOG_RECOMB, LOG_NOW_LCDM-0.5, 'Radiation/Matter\ndomination', G['bbn']),
    (LOG_NOW_LCDM-0.5, LOG_NOW_LCDM, 'Structure\nformation',     G['structure']),
    (LOG_NOW_LCDM, LOG_MAX, 'Future\n(de Sitter)',                 G['scen_a']),
]
for x0,x1,lbl,col in lcdm_epochs:
    make_epoch_bar(ax1, x0, x1, lbl, col)

# Epoch boundary markers
for xl, lbl in [(LOG_PT,r'$t_{\rm Pl}$'), (LOG_END_INF,''), (LOG_EW,'EW'),
                (LOG_QCD,'QCD+BBN'), (LOG_RECOMB,'Recomb.'), (LOG_NOW_LCDM,'Now')]:
    add_vline(ax1, xl, lbl, y_label=0.92, fs=6.5)

ax1.text(LOG_NOW_LCDM+0.1, 0.50, '13.8 Gyr', fontsize=7, va='center', rotation=90)
ax1.set_xticks([])

# ══════════════════════════════════════════════════════════════════════════
# Panel (b) — ECT
# ══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_subplot(gs[1])
ax2.set_xlim(XMIN, XMAX); ax2.set_ylim(0, 1); ax2.set_yticks([])
ax2.text(-0.01, 1.01, '(b) ECT (Euclidean Condensate Theory)',
         transform=ax2.transAxes, fontsize=11, fontweight='bold', va='bottom')

LOG_ECT_PT_END = LOG_PT + 0.8  # end of O(4)->O(3) transition

ect_epochs = [
    (XMIN,         LOG_PT,          'Euclidean phase\nO(4)-symmetric\nno time, $v_0=0$', G['undefined']),
    (LOG_PT,       LOG_ECT_PT_END,  'PT\nO(4)$\\to$O(3)',                                  G['planck']),
    (LOG_ECT_PT_END, LOG_END_INF,   'Inflation $N_e=60$\n$n_s=0.967$',                    G['inflation']),
    (LOG_END_INF,  LOG_EW,          'Radiation\n(as in SM)',                               G['radiation']),
    (LOG_EW,       LOG_QCD,         'EW: $v_2=246$ GeV\nW,Z,H',                           G['ew']),
    (LOG_QCD,      LOG_RECOMB,      'QCD+BBN',                                             G['qcd']),
    # Structure formation: G_eff > G_N → accelerated early maturity
    (LOG_RECOMB,   LOG_JWST14,      'Rad./Matter\ndomination',                             G['bbn']),
    (LOG_JWST14,   LOG_JWST10,      'JWST $z{\\sim}14$\n$G_{\\rm eff}/G_N{\\approx}1.7$', G['structure']),
    (LOG_JWST10,   LOG_NOW_ECT-0.1, 'Structure +\n$v_0$-condensate\n(residual DE)',        '#d8d8d8'),
    (LOG_NOW_ECT,  LOG_NOW_ECT+1.5, 'Scen. A\n$v_0{\\to}v_\\infty$',                      G['scen_a']),
    (LOG_NOW_ECT+1.5, LOG_MAX,      'Scen. B\n$v_0{\\to}0$\nCrunch',                       G['scen_b']),
]
for x0,x1,lbl,col in ect_epochs:
    make_epoch_bar(ax2, x0, x1, lbl, col, fs=7.0)

# Epoch boundary markers
for xl, lbl in [(LOG_PT,''), (LOG_ECT_PT_END,''), (LOG_END_INF,''),
                (LOG_EW,'EW'), (LOG_QCD,''), (LOG_RECOMB,''),
                (LOG_JWST14,'JWST\n$z{\\sim}14$'), (LOG_JWST10,'JWST\n$z{\\sim}10$'),
                (LOG_NOW_ECT,'Now')]:
    add_vline(ax2, xl, lbl, y_label=0.93, fs=6.0)

ax2.text(LOG_NOW_ECT+0.05, 0.65, '13.02 Gyr', fontsize=7, va='center', rotation=90, color='#222222')

# Bottom annotation strip
notes = [
    (XMIN+1,          r'$O(4)$-symm.'),
    (LOG_PT+0.2,       r'$\alpha>1$, time emerges, $c_*=1/\sqrt{\alpha-1}$, $v_0{\sim}M_{\rm Pl}$ frozen'),
    ((LOG_EW+LOG_QCD)/2, r'$v_2=246$ GeV'),
    ((LOG_RECOMB+LOG_NOW_ECT)/2, r'$w_0\approx -0.83$ (DESI); $\Delta H_0/H_0{=}+2.73\%$'),
]
for xt, lbl in notes:
    ax2.text(xt, 0.02, lbl, ha='center', va='bottom', fontsize=5.5,
             bbox=dict(fc='white', ec='none', pad=1))
ax2.set_xticks([])

# ══════════════════════════════════════════════════════════════════════════
# Panel (c) — Condensate dynamics
# ══════════════════════════════════════════════════════════════════════════
ax3 = fig.add_subplot(gs[2])
ax3.text(-0.01, 1.01, '(c) Condensate dynamics and cosmological observables',
         transform=ax3.transAxes, fontsize=11, fontweight='bold', va='bottom')

t = np.linspace(XMIN, LOG_MAX, 5000)

# ── v0(t)/v∞  Scenario A ────────────────────────────────────────────────
# Rises sharply at phase transition, stays at 1
v0_A = np.zeros_like(t)
mask_pre = t < LOG_PT
v0_A[mask_pre] = 0.0
mask_rise = (t >= LOG_PT) & (t < LOG_ECT_PT_END+1)
v0_A[mask_rise] = 0.5*(1 + np.tanh(3.5*(t[mask_rise] - (LOG_PT+0.5))))
mask_post = t >= LOG_ECT_PT_END+1
v0_A[mask_post] = 1.0
# small inflationary dip then recovery
mask_inf2 = (t >= LOG_ECT_PT_END) & (t < LOG_END_INF)
v0_A[mask_inf2] = 0.95 + 0.05*np.tanh(2*(t[mask_inf2]-(-36)))

# ── v0(t)/v∞  Scenario B ────────────────────────────────────────────────
v0_B = v0_A.copy()
mask_fut = t > LOG_NOW_ECT + 0.5
v0_B[mask_fut] = np.exp(-0.55*(t[mask_fut] - (LOG_NOW_ECT+0.5)))

# ── v2(t)/v2_EW  (electroweak condensate, rises at EW transition) ────────
v2 = np.zeros_like(t)
mask_ew = t >= LOG_EW
v2[mask_ew] = 0.20*(1 + np.tanh(4*(t[mask_ew] - LOG_EW + 0.3)))
v2 = np.clip(v2, 0, 0.25)

# ── log a(t)  (scale factor, normalized) ─────────────────────────────────
# Before inflation: nothing; inflation: exponential; after: power law
log_a = np.zeros_like(t)
mask_inf3 = (t >= LOG_ECT_PT_END) & (t < LOG_END_INF)
log_a[mask_inf3] = 60*(t[mask_inf3]-LOG_ECT_PT_END)/(LOG_END_INF-LOG_ECT_PT_END)
mask_rad = (t >= LOG_END_INF) & (t < LOG_RECOMB)
log_a[mask_rad] = 60 + 0.48*(t[mask_rad]-LOG_END_INF)
mask_mat = t >= LOG_RECOMB
log_a[mask_mat] = 60 + 0.48*(LOG_RECOMB-LOG_END_INF) + 0.33*(t[mask_mat]-LOG_RECOMB)
log_a = np.clip(log_a, 0, None)
a_norm = log_a / np.max(log_a)   # normalize to [0,1]

# ── φ(t) = (1/β)·ln(u/u∞)  — derived-parent ─────────────────────────────
# At phase transition φ starts very negative, rises toward 0
# phi0(today) = -0.10, phi(z=10) ~ -0.38, phi(z=14) ~ -0.50
# Map time to approximate redshift behaviour
phi = np.zeros_like(t)
mask_phi = t >= LOG_PT
# Simple model: phi rises from -0.8 to -0.10 between PT and now
t_now = LOG_NOW_ECT; t_pt = LOG_PT
phi_now = -0.10; phi_early = -0.60
phi[mask_phi] = phi_now + (phi_early - phi_now)*(1 - np.tanh(1.2*(t[mask_phi]-t_pt+2)/(t_now-t_pt)))
phi[~mask_phi] = 0.0   # Euclidean phase: no phi

# ── G_eff(t)/G_N = exp(-β·φ), β=0.8 ─────────────────────────────────────
beta = 0.8
G_eff = np.where(t >= LOG_PT, np.exp(-beta*phi), 1.0)
# Scenario B future: G_eff diverges as v0->0
G_eff_B = G_eff.copy()
mask_futB = t > LOG_NOW_ECT + 0.5
G_eff_B[mask_futB] = G_eff[np.where(mask_futB)[0][0]] * np.exp(1.0*(t[mask_futB]-(LOG_NOW_ECT+0.5)))
G_eff_B = np.clip(G_eff_B, 1, 2.2)

# ── Plot ──────────────────────────────────────────────────────────────────
YMAX = 1.75
ax3.plot(t, v0_A,  '-',  color='black', lw=2.2, label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. A)')
ax3.plot(t, v0_B,  ':',  color='black', lw=1.8, label=r'$v_0(t)/v_\infty$ — Planck condensate (Scen. B)')
ax3.plot(t, v2,    '--', color='0.45',  lw=1.6, label=r'$v_2(t)/v_{2,\rm EW}$ — EW condensate (SU(2))')
ax3.plot(t, a_norm,'-.', color='0.60',  lw=1.5, label=r'$\log a(t)$ (scale factor, normalised)')
ax3.plot(t, G_eff_B, '-', color='0.30', lw=1.4, label=r'$G_{\rm eff}/G$ (Scen. B,  $\propto v_0^{-2}\to\infty$)')

# G_eff annotation: JWST epochs
jw14_idx = np.argmin(np.abs(t - LOG_JWST14))
jw10_idx = np.argmin(np.abs(t - LOG_JWST10))
ax3.annotate('', xy=(LOG_JWST14, G_eff[jw14_idx]),
             xytext=(LOG_JWST14, G_eff[jw14_idx]+0.15),
             arrowprops=dict(arrowstyle='->', lw=1.0))
ax3.text(LOG_JWST14-0.1, G_eff[jw14_idx]+0.23, r'$G_{\rm eff}/G_N{\approx}1.7$'+r', $z{\sim}14$',
         ha='center', va='bottom', fontsize=7.5)
ax3.annotate('', xy=(LOG_JWST10, G_eff[jw10_idx]),
             xytext=(LOG_JWST10, G_eff[jw10_idx]+0.15),
             arrowprops=dict(arrowstyle='->', lw=1.0))
ax3.text(LOG_JWST10+0.1, G_eff[jw10_idx]+0.23, r'$G_{\rm eff}/G_N{\approx}1.5$'+r', $z{\sim}10$',
         ha='center', va='bottom', fontsize=7.5)

# Epoch vertical markers
for xl, lbl, clr in [
    (LOG_PT,       'PT',      'black'),
    (LOG_END_INF,  '',        '0.6'),
    (LOG_EW,       'EW',      '0.5'),
    (LOG_QCD,      'QCD+BBN', '0.5'),
    (LOG_RECOMB,   'Recomb.', '0.5'),
    (LOG_JWST14,   '',        '0.4'),
    (LOG_JWST10,   '$z\\!\\sim\\!10$', '0.35'),
    (LOG_NOW_LCDM, 'NOW\n(ΛCDM)', '0.5'),
    (LOG_NOW_ECT,  'NOW\n(ECT)',  'black'),
]:
    ax3.axvline(xl, color=clr, ls='--', lw=0.7, alpha=0.7)
    if lbl:
        ax3.text(xl, YMAX*0.96, lbl, ha='center', va='top', fontsize=6.5, color=clr)

# Scenario A/B boxes
ax3.text(LOG_NOW_ECT+0.8, 1.30,
         'Scenario A:\n$v_0\\to v_\\infty$\neternal expansion',
         ha='center', fontsize=7.5, va='center',
         bbox=dict(fc='white', ec='0.4', lw=0.8, pad=3))
ax3.text(LOG_NOW_ECT+2.2, 0.38,
         'Scenario B:\n$v_0$ slowly $\\to0$\n$G_{\\rm eff}\\to\\infty$\nBig Crunch $\\sim10^{100}$ yr',
         ha='center', fontsize=7.5, va='center',
         bbox=dict(fc='#f0f0f0', ec='0.4', lw=0.8, pad=3))

# Derived-parent key result box
ax3.text(0.015, 0.95,
         r'Hubble-priority point: $\omega_0=30$, $\phi_0=-0.10$' '\n'
         r'$\Delta H_0/H_0=+2.73\%$, $H_0^{\rm ECT}=69.2$ km/s/Mpc' '\n'
         r'$t_0^{\rm ECT}=13.02$ Gyr  ($\Lambda$CDM: 13.8 Gyr)' '\n'
         r'$R_{\rm gal}\approx1.21$,  $R_{\rm BH}\approx1.48$--$1.51$ at $z{=}10$',
         transform=ax3.transAxes, fontsize=7.5, va='top', ha='left',
         bbox=dict(fc='white', ec='0.5', lw=0.8, pad=4))

# Euclidean phase shading
ax3.axvspan(XMIN, LOG_PT, alpha=0.07, color='black')
ax3.text(-43, 0.50, 'Euclidean\nphase\n(no time)', ha='center', va='center',
         fontsize=7, color='0.35', style='italic')

ax3.set_xlim(XMIN, XMAX); ax3.set_ylim(0, YMAX)
ax3.set_xlabel(r'$\log_{10}(t\,/\,\mathrm{s})$', fontsize=11)
ax3.set_ylabel('Normalised value', fontsize=10)
ax3.legend(fontsize=8, loc='upper left', bbox_to_anchor=(0.0, 0.72),
           framealpha=0.95, edgecolor='0.5')
ax3.minorticks_on()

# Bottom disclaimer
ax3.text(0.5, -0.09,
         'Note: curves are schematic; exact shapes require numerical integration. '
         'Condensate dynamics: derived-parent ECT (Pack H–M).',
         transform=ax3.transAxes, ha='center', fontsize=6.5, color='0.4', style='italic')

# ── Shared x-ticks ────────────────────────────────────────────────────────
tick_vals = [-43,-40,-35,-30,-20,-10,0,5,10,13,15,16,17,18,19,20]
tick_lbls = [r'$10^{-43}$', r'$10^{-40}$', r'$10^{-35}$', r'$10^{-30}$',
             r'$10^{-20}$', r'$10^{-10}$', '1 s',
             r'$10^5$ s', r'$10^{10}$ s', r'$10^5$ yr',
             '380\nkyr', r'$10^9$ yr', r'$10^{10}$ yr',
             r'13.8', r'$10^{12}$', r'$10^{13}$']
ax3.set_xticks(tick_vals)
ax3.set_xticklabels(tick_lbls, fontsize=7)

out = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig5_ECT_timeline_condensate_v2'
plt.savefig(out+'.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig(out+'.pdf', bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out}.png/pdf")
