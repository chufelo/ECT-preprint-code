#!/usr/bin/env python3
"""
ECT full three-sector conceptual evolution figure.
Shows:
  (i)  Ordering / Lorentzian-branch emergence layer (top band)
  (ii) Gravitational condensate amplitude sector: phi(z), G_eff/G_N
  (iii) Electroweak condensate sector: v2/v2_EW

Horizontal axis: conceptual timeline from Euclidean phase to late screened epoch.
Grayscale, publication-quality.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')

plt.rcParams.update({
    'font.family': 'serif',
    'font.size':   10.5,
    'axes.linewidth': 0.8,
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'savefig.facecolor': 'white',
})

# ── Timeline coordinate ───────────────────────────────────────────────────────
# We use a conceptual x-axis with named epochs mapped to positions 0..1
# Positions (approximate):
#   0.00  Euclidean / pre-Lorentzian
#   0.10  O(4)→O(3) ordering transition
#   0.18  Inflation end / Lorentzian branch established
#   0.35  EW condensation (v2 turns on)
#   0.55  Structure formation / JWST epoch (z~10-14)
#   0.75  Recombination / Matter domination
#   0.88  Present (NOW ECT, t0=13.02 Gyr)
#   1.00  Far future (Scenario A/B)

EPOCHS = [
    (0.00, "Euclidean\nphase"),
    (0.10, "O(4)$\\to$O(3)\nordering"),
    (0.18, "Inflation\n$N_e=60$"),
    (0.35, "EW: $v_2=246$ GeV\nW, Z, H"),
    (0.55, "JWST epoch\n$z\\sim10$--14"),
    (0.75, "Recomb.\n380 kyr"),
    (0.88, "NOW (ECT)\n13.02 Gyr"),
    (1.00, "Future\nScen. A/B"),
]

xs = np.linspace(0, 1, 800)

# ── Figure: 3 panels stacked ──────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 9.5))
gs = fig.add_gridspec(3, 1,
    height_ratios=[1.0, 2.2, 1.8],
    hspace=0.0,
    left=0.08, right=0.93, top=0.94, bottom=0.09)

# shared x limits
XMIN, XMAX = -0.02, 1.03

# ── Panel 1: Ordering / branch emergence ─────────────────────────────────────
ax1 = fig.add_subplot(gs[0])
ax1.set_xlim(XMIN, XMAX); ax1.set_ylim(0, 1)
ax1.set_yticks([]); ax1.set_xticks([])

# Phase bands
phase_bands = [
    (0.00, 0.10, '#d0d0d0', 'Euclidean / pre-Lorentzian\n(no macroscopic time, $u_0=0$)'),
    (0.10, 0.18, '#a0a0a0', 'Ordering transition\nO(4)$\\to$O(3), $\\alpha>1$\nLorentzian branch emerges'),
    (0.18, 0.88, '#e8e8e8', 'Causal macroscopic Lorentzian regime\n(ordered branch, $c_*=1/\\sqrt{\\alpha-1}$, time established)'),
    (0.88, 1.03, '#f4f4f4', 'Scen. A/B\nfuture'),
]
for x0, x1, col, lbl in phase_bands:
    ax1.add_patch(Rectangle((x0, 0.05), x1-x0, 0.88,
                            facecolor=col, edgecolor='black', lw=0.5))
    ax1.text((x0+min(x1,1.02))/2, 0.50, lbl,
             ha='center', va='center', fontsize=8.5, multialignment='center')

ax1.text(-0.01, 1.04, '(i) Ordering / Lorentzian-branch emergence',
         transform=ax1.transAxes, fontsize=10, fontweight='bold', va='bottom')

# Epoch separators (shared across all panels)
for xp, _ in EPOCHS[1:]:
    ax1.axvline(xp, color='0.4', ls='--', lw=0.7, alpha=0.6)

# ── Panel 2: Gravitational condensate amplitude sector ───────────────────────
ax2 = fig.add_subplot(gs[1])
ax2.set_xlim(XMIN, XMAX)
ax2.set_xticks([]); ax2.spines['top'].set_visible(False)

# phi(x): starts very negative at x=0.10, rises toward 0 by x=0.88
x_pt = 0.10; x_now = 0.88
phi = np.zeros_like(xs)
mask = xs >= x_pt
phi[mask] = -0.10 * (1 + 4.5*(1 - np.tanh(5.5*(xs[mask]-x_pt-0.05)/(x_now-x_pt))))
phi[xs >= x_now] = -0.10   # phi0 = -0.10 today

# u/u_inf = exp(beta*phi), beta=0.8
beta = 0.8
u_norm = np.where(xs >= x_pt, np.exp(beta * phi), 0.0)

# G_eff/G_N = exp(-beta*phi)
G_eff = np.where(xs >= x_pt, np.exp(-beta * phi), 1.0)

# Scenario B: G_eff diverges
G_eff_B = G_eff.copy()
mask_fut = xs > 0.91
G_eff_B[mask_fut] = G_eff[np.searchsorted(xs, 0.91)] * np.exp(4.0*(xs[mask_fut]-0.91))
G_eff_B = np.clip(G_eff_B, 1.0, 2.8)

# Plot
ax2.plot(xs, u_norm, '-', color='black', lw=2.2,
         label=r'$u(t)/u_\infty = e^{\beta\phi}$ (condensate amplitude, Scen. A)')
ax2.plot(xs, G_eff,  '--', color='0.35', lw=2.0,
         label=r'$G_{\rm eff}(t)/G_N = e^{-\beta\phi}$ (effective gravity)')
ax2.plot(xs, G_eff_B, ':', color='0.35', lw=1.6,
         label=r'$G_{\rm eff}/G_N$ (Scen. B, $\to\infty$ as $u_0\to 0$)')

# Key annotations
# phi<0 early
ax2.annotate('', xy=(0.28, 0.62), xytext=(0.22, 0.78),
             arrowprops=dict(arrowstyle='->', lw=1.0, color='black'))
ax2.text(0.21, 0.80, r'$\phi\ll 0$' '\n' r'$u/u_\infty\ll 1$',
         ha='center', va='bottom', fontsize=9,
         bbox=dict(fc='white', ec='0.5', pad=2, lw=0.6))

# G_eff > G_N early  — JWST epoch
xjw = 0.55
jjw = np.argmin(np.abs(xs - xjw))
ax2.annotate('', xy=(xjw, G_eff[jjw]), xytext=(xjw, G_eff[jjw]+0.25),
             arrowprops=dict(arrowstyle='->', lw=1.0))
ax2.text(xjw, G_eff[jjw]+0.27,
         r'$G_{\rm eff}/G_N\approx1.5$–$1.7$' '\n'
         r'at JWST epoch $z\sim10$–$14$' '\n'
         r'$\Rightarrow$ accelerated local maturity',
         ha='center', va='bottom', fontsize=8.5,
         bbox=dict(fc='white', ec='0.5', pad=2.5, lw=0.7))

# screened branch today
xnow = 0.88
ax2.annotate(r'$\phi\to -0.10$ (today, screened branch)' '\n'
             r'benchmark truncation valid',
             xy=(xnow, u_norm[np.argmin(np.abs(xs-xnow))]),
             xytext=(0.70, 0.30),
             fontsize=8.5,
             arrowprops=dict(arrowstyle='->', lw=0.9),
             bbox=dict(fc='white', ec='0.5', pad=2, lw=0.6))

# linear growth note
ax2.text(0.55, 0.06,
         'Linear growth $D(z)/D_{\\rm ref}\\approx0.98$–$0.99$: nearly neutral\n'
         'BH-assisted maturity channel dominant: $R_{\\rm BH}\\approx1.48--1.54$',
         ha='center', va='bottom', fontsize=8.5,
         bbox=dict(fc='#f0f0f0', ec='0.5', pad=3, lw=0.7))

ax2.axhline(1.0, color='0.6', ls=':', lw=0.8)
ax2.set_ylim(-0.05, 2.85)
ax2.set_ylabel(r'Normalised value', fontsize=10)
ax2.legend(fontsize=8.5, loc='upper right', bbox_to_anchor=(1.0, 0.98),
           framealpha=0.97, edgecolor='0.5')
ax2.text(-0.01, 1.02, '(ii) Gravitational condensate amplitude sector',
         transform=ax2.transAxes, fontsize=10, fontweight='bold', va='bottom')

for xp, _ in EPOCHS[1:]:
    ax2.axvline(xp, color='0.45', ls='--', lw=0.7, alpha=0.55)

# Euclidean shading
ax2.axvspan(XMIN, x_pt, alpha=0.08, color='black')
ax2.text(0.05, 1.35, 'Euclidean\nphase\n(no $\\phi$)',
         ha='center', va='center', fontsize=8, color='0.4', style='italic')

# ── Panel 3: Electroweak condensate sector ────────────────────────────────────
ax3 = fig.add_subplot(gs[2])
ax3.set_xlim(XMIN, XMAX)
ax3.spines['top'].set_visible(False)

# v2/v2_EW: 0 before EW transition at x=0.35, rises to ~0.22 (kept lower than grav sector)
x_ew = 0.35
v2 = np.zeros_like(xs)
mask_ew = xs >= x_ew
v2[mask_ew] = 0.75*(1 + np.tanh(25*(xs[mask_ew]-x_ew-0.02)))
v2 = np.clip(v2, 0, 0.85)

ax3.fill_between(xs, 0, v2, alpha=0.18, color='black', label='EW condensate inactive')
ax3.plot(xs, v2, '-', color='black', lw=2.0,
         label=r'$v_2(t)/v_{2,\rm EW}$ (SU(2) condensate amplitude)')

# SM-like regime annotation
ax3.text(0.62, 0.55,
         r'$v_2\approx 246$ GeV — Standard Model electroweak condensate' '\n'
         r'W, Z, H mass generation; SM fermion Yukawa couplings',
         ha='center', va='center', fontsize=8.5,
         bbox=dict(fc='white', ec='0.5', pad=2.5, lw=0.7))

# Before EW
ax3.text(0.22, 0.45,
         'EW sector\nnot yet formed\n($v_2=0$)',
         ha='center', va='center', fontsize=9, color='0.4',
         bbox=dict(fc='white', ec='none', pad=1))

# EW transition arrow
ax3.annotate('', xy=(x_ew+0.01, 0.15), xytext=(x_ew-0.04, 0.15),
             arrowprops=dict(arrowstyle='->', lw=1.2, color='black'))
ax3.text(x_ew+0.02, 0.17, r'EW condensation' '\n' r'$v_2=246$ GeV turns on',
         ha='left', va='bottom', fontsize=8.5)

ax3.set_ylim(-0.02, 1.05)
ax3.set_ylabel(r'$v_2(t)/v_{2,\rm EW}$', fontsize=10)
ax3.legend(fontsize=8.5, loc='lower right', framealpha=0.97, edgecolor='0.5')
ax3.text(-0.01, 1.02, '(iii) Electroweak condensate sector',
         transform=ax3.transAxes, fontsize=10, fontweight='bold', va='bottom')

for xp, _ in EPOCHS[1:]:
    ax3.axvline(xp, color='0.45', ls='--', lw=0.7, alpha=0.55)
ax3.axvspan(XMIN, x_pt, alpha=0.08, color='black')

# ── Shared x-axis labels (bottom of panel 3) ─────────────────────────────────
epoch_positions = [ep[0] for ep in EPOCHS]
epoch_labels    = [ep[1] for ep in EPOCHS]
ax3.set_xticks(epoch_positions)
ax3.set_xticklabels(epoch_labels, fontsize=8.5, multialignment='center')
ax3.tick_params(axis='x', which='major', pad=4)

# ── Suptitle ──────────────────────────────────────────────────────────────────
fig.text(0.50, 0.965,
         "ECT: schematic full evolution of the ordered-branch condensate sectors and the observable Universe",
         ha='center', fontsize=11.5, fontweight='bold')
fig.text(0.50, 0.948,
         r"$\beta=0.8$, $\phi_0=-0.10$ (Hubble-priority);  "
         r"$G_{\rm eff}(z=10)/G_N\approx1.49$;  "
         r"$\Delta H_0/H_0=+2.73\%$;  $t_0^{\rm ECT}=13.02$ Gyr",
         ha='center', fontsize=9.5, color='0.3')

out = OUTDIR / 'ect_full_condensate_universe_evolution_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
