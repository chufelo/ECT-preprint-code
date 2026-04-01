#!/usr/bin/env python3
"""
fig5_cosmological_timeline_v2.py — COMPLETE REWRITE
ECT cosmological timeline: LCDM vs ECT comparison.
ECT universe is younger (13.02 vs 13.8 Gyr).
Shift is exaggerated on log axis for visibility (actual difference 6%).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams.update({'font.family':'serif','font.size':9,'axes.linewidth':0.8})

G = dict(undef='#999999', planck='#666666', order='#888888',
         rad='#bbbbbb', ew='#aaaaaa', qcd='#999999',
         recomb='#cccccc', struct='#e0e0e0', dark='#d0d0d0',
         scenA='#e8e8e8', scenB='#c0c0c0')

XMIN, XMAX = -44, 21
# Physical times (log10 s):
LP = -43.3; END_ORD = -32; EW = -10; QCD = -4
RECOMB = 13.1; NOW_L = 17.64; NOW_E = 17.61
# Visual shift for ECT (exaggerated; real shift 0.03 log units = invisible)
VSHIFT = 3.0

fig = plt.figure(figsize=(16, 12.5))
gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 1.7], hspace=0.30)

def bar(ax, x0, x1, col, lbl='', y0=0.12, y1=0.88, fs=7.5):
    ax.add_patch(Rectangle((x0,y0), x1-x0, y1-y0, fc=col, ec='k', lw=0.5))
    if lbl:
        ax.text((x0+x1)/2, (y0+y1)/2, lbl, ha='center', va='center',
                fontsize=fs, fontweight='bold', multialignment='center')

# ════════════════════ (a) ΛCDM ════════════════════
ax1 = fig.add_subplot(gs[0])
ax1.set_xlim(XMIN, XMAX); ax1.set_ylim(0,1); ax1.set_yticks([])
ax1.set_xticks([])
ax1.text(0.0, 1.02, r'(a) Standard $\Lambda$CDM', transform=ax1.transAxes,
         fontsize=11, fontweight='bold', va='bottom')

bar(ax1, XMIN,  LP,       G['undef'],  'Undefined\n(no spacetime)')
bar(ax1, LP,    END_ORD,  G['planck'],  'Planck +\nInflation')
bar(ax1, END_ORD, EW,     G['rad'],    'Radiation\n(quarks, leptons)')
bar(ax1, EW,    QCD,      G['ew'],     'EW\ntransition')
bar(ax1, QCD,   RECOMB,   G['qcd'],    'QCD + BBN')
bar(ax1, RECOMB, NOW_L,   G['recomb'], 'Radiation / Matter\ndomination')
bar(ax1, NOW_L, XMAX,     G['scenA'],  'Future\n(de Sitter)', fs=7)

ax1.axvline(NOW_L, color='k', ls='--', lw=1.2)
ax1.text(NOW_L, 0.95, 'Now', ha='center', va='bottom', fontsize=8, fontweight='bold')
ax1.text(NOW_L+0.2, 0.50, '13.8 Gyr', fontsize=8, va='center', rotation=90,
         fontweight='bold')

for x, lb in [(LP,r'$t_{\rm Pl}$'),(EW,'EW'),(QCD,'QCD+BBN'),(RECOMB,'Recomb.')]:
    ax1.axvline(x, color='0.4', ls=':', lw=0.6)
    ax1.text(x, 0.95, lb, ha='center', va='bottom', fontsize=6.5, color='0.4')

# ════════════════════ (b) ECT ════════════════════
ax2 = fig.add_subplot(gs[1])
ax2.set_xlim(XMIN, XMAX); ax2.set_ylim(0,1); ax2.set_yticks([])
ax2.set_xticks([])
ax2.text(0.0, 1.02, '(b) ECT (Euclidean Condensate Theory)', transform=ax2.transAxes,
         fontsize=11, fontweight='bold', va='bottom')

# ECT epochs shifted RIGHT by VSHIFT (exaggerated for visibility)
S = VSHIFT
bar(ax2, XMIN+S, LP+S,       G['undef'],  'Eucl. phase\nO(4)-symm.\nno time')
bar(ax2, LP+S,   LP+S+1,     G['planck'],  'PT')
bar(ax2, LP+S+1, END_ORD+S,  G['order'],  'Ordering\ntransition')
bar(ax2, END_ORD+S, EW+S,    G['rad'],    'Radiation\n(as in SM)')
bar(ax2, EW+S,   QCD+S,      G['ew'],     'EW: $v_2{=}246$ GeV\nW,Z,H')
bar(ax2, QCD+S,  RECOMB+S,   G['qcd'],    'QCD + BBN')
# Late epochs: use NOW_L (aligned with LCDM) instead of NOW_E+S
bar(ax2, RECOMB+S, NOW_L-0.5, G['recomb'], 'Rad./Matter dom.')
bar(ax2, NOW_L-0.5, NOW_L,   G['struct'], '', fs=6)
bar(ax2, NOW_L, NOW_L+2,     G['scenA'],  '', fs=6)
bar(ax2, NOW_L+2, XMAX,      G['scenB'],  '', fs=6)

# Labels for narrow epochs — placed ABOVE or BELOW bars to avoid overlap
ax2.text(NOW_L-0.25, 0.04, 'Struct.', ha='center', va='bottom', fontsize=6)
ax2.text(NOW_L+1.0, 0.04, 'Scen. A', ha='center', va='bottom', fontsize=6)
ax2.text(NOW_L+3.0, 0.04, 'Scen. B', ha='center', va='bottom', fontsize=6)

ax2.axvline(NOW_L, color='k', ls='--', lw=1.2)
ax2.text(NOW_L, 0.95, 'Now', ha='center', va='bottom', fontsize=8, fontweight='bold')
ax2.text(NOW_L+0.2, 0.50, '13.02 Gyr', fontsize=8, va='center', rotation=90,
         fontweight='bold', color='#222222')

# White gap at LEFT showing ECT starts later
ax2.axvspan(XMIN, XMIN+S, fc='white', ec='none', zorder=5)
ax2.text(XMIN+S/2, 0.50, 'No time yet\n(ECT younger)', ha='center', va='center',
         fontsize=7.5, color='0.5', style='italic', zorder=6,
         bbox=dict(fc='white', ec='0.7', lw=0.5, pad=3))

for x, lb in [(EW+S,'EW'),(QCD+S,''),(RECOMB+S,'Recomb.')]:
    ax2.axvline(x, color='0.4', ls=':', lw=0.6)
    if lb:
        ax2.text(x, 0.95, lb, ha='center', va='bottom', fontsize=6.5, color='0.4')

# Bottom strip
ax2.text((LP+S+END_ORD+S)/2, 0.01,
         r'$\alpha>\beta$, time emerges, $c_*=1/\sqrt{\alpha-\beta}$, $u_0{\sim}\bar{M}_{\rm Pl}$',
         ha='center', va='bottom', fontsize=5.5, bbox=dict(fc='white',ec='none',pad=1))
ax2.text((EW+S+QCD+S)/2, 0.01, r'$v_2=246$ GeV',
         ha='center', va='bottom', fontsize=5.5, bbox=dict(fc='white',ec='none',pad=1))
ax2.text((RECOMB+S+NOW_L)/2, 0.01,
         r'$w_0\approx-0.83$ (DESI); $\Delta H_0/H_0{=}+2.73\%$',
         ha='center', va='bottom', fontsize=5.5, bbox=dict(fc='white',ec='none',pad=1))

# Age difference caption
ax2.text(0.5, -0.12, '(Age difference exaggerated for visibility; actual difference 0.8 Gyr = 6%)',
         transform=ax2.transAxes, ha='center', fontsize=7, style='italic', color='0.4')

# ════════════════════ (c) Condensate dynamics ════════════════════
ax3 = fig.add_subplot(gs[2])
ax3.text(0.0, 1.02, '(c) Condensate dynamics and cosmological observables',
         transform=ax3.transAxes, fontsize=11, fontweight='bold', va='bottom')

t = np.linspace(XMIN, XMAX, 5000)
PT = LP

# u0(t)/u0(inf) — Scenario A
v0A = np.zeros_like(t)
v0A[t >= PT] = 0.5*(1 + np.tanh(3.5*(t[t>=PT] - PT - 0.5)))
v0A[t >= PT+2] = 1.0
v0A[(t>=PT+0.8)&(t<END_ORD)] = 0.95 + 0.05*np.tanh(2*(t[(t>=PT+0.8)&(t<END_ORD)]+36))

# u0(t)/u0(inf) — Scenario B
v0B = v0A.copy()
v0B[t > NOW_L+0.5] = np.exp(-0.55*(t[t>NOW_L+0.5] - NOW_L - 0.5))

# v2(t)/v2_EW
v2 = np.zeros_like(t)
v2[t >= EW] = 0.20*(1 + np.tanh(4*(t[t>=EW] - EW + 0.3)))
v2 = np.clip(v2, 0, 0.25)

# log a(t) normalised
la = np.zeros_like(t)
la[(t>=PT+0.8)&(t<END_ORD)] = 60*(t[(t>=PT+0.8)&(t<END_ORD)]-PT-0.8)/(END_ORD-PT-0.8)
la[(t>=END_ORD)&(t<RECOMB)] = 60 + 0.48*(t[(t>=END_ORD)&(t<RECOMB)]-END_ORD)
la[t>=RECOMB] = 60 + 0.48*(RECOMB-END_ORD) + 0.33*(t[t>=RECOMB]-RECOMB)
la = np.clip(la, 0, None)
la /= np.max(la)

# G_eff/G (Scen B)
Geff = np.ones_like(t)
Geff[t>NOW_L+0.5] = np.exp(1.0*(t[t>NOW_L+0.5]-NOW_L-0.5))
Geff = np.clip(Geff, 0.5, 2.2)

YMAX = 1.75
ax3.plot(t, v0A, '-',  color='black', lw=2.2, label=r'$u_0(t)/u_0(\infty)$ — Scen. A')
ax3.plot(t, v0B, ':',  color='black', lw=1.8, label=r'$u_0(t)/u_0(\infty)$ — Scen. B')
ax3.plot(t, v2,  '--', color='0.45',  lw=1.5, label=r'$v_2(t)/v_{2,\rm EW}$ — EW condensate')
ax3.plot(t, la,  '-.', color='0.60',  lw=1.4, label=r'$\log a(t)$ (normalised)')
ax3.plot(t, Geff,'-',  color='0.30',  lw=1.2, label=r'$G_{\rm eff}/G$ (Scen. B)')

# Euclidean shading
ax3.axvspan(XMIN, PT, alpha=0.07, color='black')
ax3.text(-43.5, 0.50, 'Eucl.\nphase', ha='center', va='center', fontsize=7,
         color='0.4', style='italic')

# Epoch markers — placed at TOP, staggered
markers = [('PT',PT,YMAX*0.97,'k'), ('EW',EW,YMAX*0.97,'0.5'),
           ('QCD+BBN',QCD,YMAX*0.90,'0.5'), ('Recomb.',RECOMB,YMAX*0.97,'0.5')]
for lb,x,y,c in markers:
    ax3.axvline(x, color=c, ls='--', lw=0.6, alpha=0.6)
    ax3.text(x, y, lb, ha='center', va='top', fontsize=6, color=c)

# NOW markers — well separated
ax3.axvline(NOW_L, color='0.5', ls='--', lw=0.8, alpha=0.7)
ax3.text(NOW_L+0.3, YMAX*0.97, r'NOW ($\Lambda$CDM)', ha='left', va='top',
         fontsize=6.5, color='0.5')
ax3.axvline(NOW_E, color='k', ls='--', lw=1.0)
ax3.text(NOW_E-0.3, YMAX*0.80, 'NOW (ECT)', ha='right', va='top',
         fontsize=6.5, color='k', fontweight='bold')

# Scenario A — arrow from box TO the flat curve at u0=1 in the future
ax3.annotate('Scenario A:\n$u_0{\\to}u_\\infty$, eternal expansion',
             xy=(NOW_L+2.0, 1.0),
             xytext=(14, 1.55),
             fontsize=7, ha='center', va='center',
             bbox=dict(fc='white', ec='0.4', lw=0.8, pad=3, alpha=0.9),
             arrowprops=dict(arrowstyle='->', color='0.3', lw=1.0))

# Scenario B — arrow from box TO the decaying curve
ax3.annotate('Scenario B:\n$u_0{\\to}0$, $G_{\\rm eff}{\\to}\\infty$\nBig Crunch $\\sim10^{100}$ yr',
             xy=(NOW_L+2.5, 0.35),
             xytext=(14, 0.15),
             fontsize=7, ha='center', va='center',
             bbox=dict(fc='#f0f0f0', ec='0.4', lw=0.8, pad=3, alpha=0.9),
             arrowprops=dict(arrowstyle='->', color='0.3', lw=1.0))

# Key results box — center-right, transparent
ax3.text(0.35, 0.97,
         r'$t_0^{\rm ECT}=13.02$ Gyr ($\Lambda$CDM: 13.8 Gyr)' '\n'
         r'$H_0^{\rm ECT}=69.2$ km/s/Mpc, $\Delta H_0/H_0=+2.73\%$' '\n'
         r'$R_{\rm gal}\approx1.21$, $R_{\rm BH}\approx1.48$--$1.51$ at $z{=}10$',
         transform=ax3.transAxes, fontsize=7, va='top', ha='left',
         bbox=dict(fc='white', ec='0.5', lw=0.8, pad=4, alpha=0.75))

# Legend — center-left, transparent
ax3.legend(fontsize=7.5, loc='upper left', bbox_to_anchor=(0.01, 0.70),
           framealpha=0.75, edgecolor='0.5')

ax3.set_xlim(XMIN, XMAX); ax3.set_ylim(0, YMAX)
ax3.set_ylabel('Normalised value', fontsize=10)
ax3.set_xlabel(r'$\log_{10}(t\,/\,\mathrm{s})$', fontsize=11)

# x-ticks — fewer in crowded region
ticks = [-43,-40,-35,-30,-20,-10,0,5,10,13,17]
tlabs = [r'$10^{-43}$',r'$10^{-40}$',r'$10^{-35}$',r'$10^{-30}$',
         r'$10^{-20}$',r'$10^{-10}$','1 s',r'$10^5$ s',
         r'$10^{10}$ s',r'380 kyr',r'$\sim\!14$ Gyr']
ax3.set_xticks(ticks)
ax3.set_xticklabels(tlabs, fontsize=7)
ax3.minorticks_on()

# Bottom note
ax3.text(0.5, -0.09,
         'Note: curves are schematic; exact shapes require numerical integration.',
         transform=ax3.transAxes, ha='center', fontsize=6.5, color='0.4', style='italic')

out = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig5_ECT_timeline_condensate_v2'
plt.savefig(out+'.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig(out+'.pdf', bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out}.png/.pdf")
