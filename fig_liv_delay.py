#!/usr/bin/env python3
"""
ECT LIV time-of-flight delay plot.

Formula (eq. LIV_delay in ECT preprint):
  Delta_t = (E / M_Pl c^2) * (L / c)
at benchmark alpha=2beta, beta=1.

M_Pl = 1.22e19 GeV (full Planck mass).
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# --- Constants ---
M_Pl_GeV = 1.22e19          # Full Planck mass in GeV
Gpc_m    = 3.086e25          # 1 Gpc in metres
c_ms     = 2.998e8           # speed of light m/s

# --- Formula ---
def dt_LIV(E_GeV, L_Gpc):
    """LIV time delay in seconds."""
    L_m = L_Gpc * Gpc_m
    return (E_GeV / M_Pl_GeV) * (L_m / c_ms)

# --- Energy axis ---
E = np.logspace(-1, 5, 500)  # 0.1 GeV to 100 TeV

# --- Source distances ---
distances = [
    (0.04,  'L = 40 Mpc',         '-',   0.9),
    (0.4,   'L = 0.4 Gpc',        '--',  0.7),
    (4.0,   'L = 4 Gpc (GRB)',    '-.',  0.4),
    (13.0,  'L = 13 Gpc (Hubble)', ':',  0.15),
]

# --- Plot ---
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'mathtext.fontset': 'cm',
    'axes.linewidth': 0.6,
})

fig, ax = plt.subplots(figsize=(7, 5))

for L_Gpc, label, ls, gray in distances:
    dt = dt_LIV(E, L_Gpc)
    ax.plot(E, dt, ls=ls, color=str(gray), lw=1.4, label=label)

# --- Fermi-LAT constraint region ---
# GRB 090510: E_QG,1 > 7.6 M_Pl => at benchmark M_QG=M_Pl,
# prediction is 7.6x above allowed.  Show as upper bound.
# Fermi timing resolution ~ 10 ms for short GRBs
ax.axhspan(1e-2, 1e6, color='0.88', zorder=0)
ax.text(0.15, 3e-2, 'Fermi-LAT constrained\nregion ($\\Delta t > 10^{-2}$ s)',
        fontsize=9, color='0.45', ha='left')

# --- CTA projected sensitivity ---
# CTA expects to reach ~ 10^{-4} s timing at TeV energies
ax.axhline(1e-4, color='0.5', ls='--', lw=0.8)
ax.text(0.15, 1.5e-4, 'CTA projected sensitivity',
        fontsize=8, color='0.5', ha='left')

# --- Reference points ---
# E=10 GeV, L=4 Gpc
dt_ref = dt_LIV(10, 4.0)
ax.plot(10, dt_ref, 'o', color='0.3', ms=5, zorder=5)
ax.annotate(f'  $E=10$ GeV, $L=4$ Gpc\n  $\\Delta t \\approx {dt_ref:.2f}$ s',
            xy=(10, dt_ref), fontsize=8, color='0.3',
            xytext=(30, dt_ref*0.3),
            arrowprops=dict(arrowstyle='->', color='0.5', lw=0.6))

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Photon energy $E$ (GeV)', fontsize=11)
ax.set_ylabel('LIV time delay $\\Delta t_{\\rm LIV}$ (s)', fontsize=11)
ax.set_xlim(0.1, 1e5)
ax.set_ylim(1e-8, 1e4)
ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax.grid(True, which='major', ls='-', lw=0.3, color='0.8')
ax.grid(True, which='minor', ls=':', lw=0.15, color='0.9')

# Add formula annotation
ax.text(0.97, 0.97,
        '$\\Delta t_{\\rm LIV} = \\frac{E}{M_{\\rm Pl}\\,c^2}\\,\\frac{L}{c}$\n'
        '(ECT benchmark: $\\alpha=2\\beta,\\;\\beta=1$)',
        transform=ax.transAxes, fontsize=9, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='0.7', lw=0.5))

fig.tight_layout()
outdir = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures'
fig.savefig(f'{outdir}/fig_liv_delay.pdf', bbox_inches='tight')
fig.savefig(f'{outdir}/fig_liv_delay.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"LIV plot saved. Reference: E=10 GeV, L=4 Gpc -> dt={dt_ref:.4f} s")
