#!/usr/bin/env python3
"""
fig_bh_information.py
---------------------
ECT Black-Hole Information Scenario — three-panel figure.
Generates fig_bh_information.pdf (greyscale, suitable for print).

Panel (a): Tolman temperature profile T_loc(rho) near horizon
Panel (b): Schematic Page curve (coarse-grained vs fine-grained entropy)
Panel (c): Critical shell depth rho_c/r_s and T_H/T_c vs BH mass

Physics:
  T_loc(rho) = hbar*c / (2*pi*k_B*rho)   [Tolman / Rindler near-horizon]
  T_c = v0 * sqrt(6)                       [ECT condensate critical temp]
  rho_c = hbar*c / (2*pi*k_B*T_c)         [critical shell distance]
       = l_Pl / sqrt(3*pi) ~ 0.33 l_Pl    [parameter-free ECT result]
  r_s = 2*G_N*M / c^2                     [Schwarzschild radius]
  T_H = hbar*c^3 / (8*pi*G_N*M*k_B)      [Hawking temperature]

All greyscale: no colour — suitable for black-and-white printing.

Author: ECT collaboration (Valeriy Blagovidov + Claude)
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ── physical constants ──────────────────────────────────────────────────────
hbar_c_GeV_m = 197.3269804e-18  # hbar*c in GeV*m  (= 197.3 MeV*fm = 0.1973 GeV*fm)
k_B_eV_K     = 8.617333262e-5   # Boltzmann in eV/K
v0_GeV       = 2.435e18          # ECT condensate VEV [GeV]
v0_eV        = v0_GeV * 1e9      # in eV
l_Pl_m       = 1.616255e-35      # Planck length [m]
G_N_SI       = 6.674e-11         # G_N [m^3 kg^-1 s^-2]
c_SI         = 2.998e8           # c [m/s]
hbar_SI      = 1.0546e-34        # hbar [J·s]
k_B_SI       = 1.381e-23         # k_B [J/K]
M_sun_kg     = 1.989e30          # solar mass [kg]

# ── ECT derived quantities ──────────────────────────────────────────────────
T_c_eV  = v0_eV * np.sqrt(6)          # critical temperature [eV]
T_c_GeV = T_c_eV / 1e9                # [GeV]
# rho_c = hbar*c / (2*pi*k_B*T_c)
rho_c_m = hbar_c_GeV_m / (2*np.pi * T_c_GeV)   # hbar*c [GeV*m] / T_c [GeV] = m
# simpler: rho_c = l_Pl / sqrt(3*pi)
rho_c_analytic_m = l_Pl_m / np.sqrt(3*np.pi)
rho_c_in_lPl = rho_c_analytic_m / l_Pl_m   # ≈ 0.326

print(f"T_c = {T_c_GeV:.3e} GeV")
print(f"rho_c (formula)   = {rho_c_m:.3e} m = {rho_c_m/l_Pl_m:.4f} l_Pl")
print(f"rho_c (analytic)  = {rho_c_analytic_m:.3e} m = {rho_c_in_lPl:.4f} l_Pl")
print(f"  = l_Pl/sqrt(3*pi) -- parameter-free ECT prediction")

# ── matplotlib style ────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "lines.linewidth": 1.6,
    "figure.dpi": 150,
})

fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.17, wspace=0.38)

# ════════════════════════════════════════════════════════════════════════════
# Panel (a): Tolman temperature profile
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0]

rho_over_rho_c = np.linspace(0.05, 6.0, 500)
T_over_Tc = 1.0 / (2*np.pi * rho_over_rho_c)  # T_loc = T_c at rho=rho_c
# Wait: T_loc = hbar*c / (2*pi*k_B*rho) and T_c = hbar*c / (2*pi*k_B*rho_c)
# => T_loc/T_c = rho_c/rho
T_over_Tc = 1.0 / rho_over_rho_c   # T_loc/T_c = rho_c/rho

# Split into two regions
mask_hot  = rho_over_rho_c <= 1.0   # T_loc > T_c  → shell / broken phase
mask_cold = rho_over_rho_c >= 1.0   # T_loc < T_c  → ordered Lorentzian

# Filled regions
rho_cold = rho_over_rho_c[mask_cold]
T_cold   = T_over_Tc[mask_cold]
ax.fill_between(rho_cold, T_cold, 0,
                color='0.82', label=r'Ordered Lorentzian ($T_{\rm loc}<T_c$)')
ax.fill_between(rho_over_rho_c[mask_hot], T_over_Tc[mask_hot], 0,
                color='0.45', alpha=0.5,
                label=r'Critical shell ($T_{\rm loc}>T_c$)')

# Curve
ax.plot(rho_over_rho_c, T_over_Tc, 'k-', lw=2.0,
        label=r'$T_{\rm loc}(\rho) = T_c\,(\rho_c/\rho)$')

# Critical lines
ax.axhline(1.0, color='k', ls='--', lw=1.2, label=r'$T_c = v_0\sqrt{6}$')
ax.axvline(1.0, color='k', ls=':', lw=1.2, label=r'$\rho_c\approx 0.33\,\ell_{\rm Pl}$')

# Annotations
ax.annotate(r'$\rho_c\approx 0.33\,\ell_{\rm Pl}$',
            xy=(1.0, 2.8), ha='center', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none', alpha=0.8))
ax.annotate('Horizon\n' + r'($\rho=0$)', xy=(0.08, 4.5),
            ha='left', fontsize=8, color='0.3')

ax.set_xlim(0, 6)
ax.set_ylim(0, 6)
ax.set_xlabel(r'Proper distance $\rho/\rho_c$')
ax.set_ylabel(r'$T_{\rm loc}/T_c$')
ax.set_title('(a) Tolman temperature profile')
ax.legend(fontsize=7.5, loc='upper right')

# ════════════════════════════════════════════════════════════════════════════
# Panel (b): Schematic Page curve
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1]

t = np.linspace(0, 1, 500)

# Coarse-grained (semiclassical Hawking): monotonically increasing
S_coarse = np.sqrt(t) * 1.0   # rough shape: rises as ~sqrt(t)

# Fine-grained (ECT unitary): rises then falls symmetrically at Page time
t_page = 0.53   # Page time ≈ evaporation half-way
S_fine = np.where(
    t <= t_page,
    S_coarse,                              # tracks coarse-grained before Page
    S_coarse[int(t_page*500)] * np.sqrt((1-t)/(1-t_page))  # falls after
)
# Make the fine-grained curve a smooth arch: rises then falls
def page_entropy(t, t_p=0.53):
    s_peak = np.sqrt(t_p)
    if t <= t_p:
        return np.sqrt(t)
    else:
        return s_peak * np.sqrt((1-t)/(1-t_p))

S_fine = np.array([page_entropy(ti) for ti in t])

ax.plot(t, S_coarse, 'k--', lw=1.8, label='Coarse-grained\n(semiclassical)')
ax.plot(t, S_fine,   'k-',  lw=2.0, label='Fine-grained\n(ECT unitary)')
ax.axvline(t_page, color='k', ls=':', lw=1.0, alpha=0.7)
ax.annotate('Page\ntime', xy=(t_page+0.02, 0.1), fontsize=8)

# Shade region between curves (information stored in shell)
ax.fill_between(t[t>=t_page], S_coarse[t>=t_page], S_fine[t>=t_page],
                color='0.70', alpha=0.6,
                label='Information\nreturned via shell')

ax.set_xlim(0, 1)
ax.set_ylim(0, 1.15)
ax.set_xlabel(r'Evaporation time $t/t_{\rm evap}$')
ax.set_ylabel(r'Entropy $S_{\rm rad}/S_{BH,0}$')
ax.set_title('(b) Schematic Page curve')
ax.legend(fontsize=7.5, loc='upper left')
ax.text(0.05, 0.95, 'Schematic only;\nquantitative curve requires\nshell Hamiltonian',
        transform=ax.transAxes, fontsize=7, va='top',
        bbox=dict(boxstyle='round', fc='white', ec='0.6', alpha=0.9))

# ════════════════════════════════════════════════════════════════════════════
# Panel (c): rho_c/r_s and T_H vs BH mass
# ════════════════════════════════════════════════════════════════════════════
ax = axes[2]
ax2 = ax.twinx()

# Mass range: 1 M_sun to 10^9 M_sun
M_sun_arr = np.logspace(0, 9, 300)
M_kg      = M_sun_arr * M_sun_kg

# Schwarzschild radius r_s = 2*G_N*M / c^2
r_s = 2.0 * G_N_SI * M_kg / c_SI**2

# rho_c / r_s
ratio = rho_c_analytic_m / r_s   # ∝ 1/M

# Hawking temperature T_H = hbar*c^3 / (8*pi*G_N*M*k_B)  [K]
T_H_K = hbar_SI * c_SI**3 / (8*np.pi * G_N_SI * M_kg * k_B_SI)
T_c_K = T_c_GeV * 1e9 * 1.160e4   # GeV → K   (1 eV = 11604.5 K)

line1, = ax.loglog(M_sun_arr, ratio, 'k-', lw=2.0,
                   label=r'$\rho_c/r_s \propto M^{-1}$')
line2, = ax2.loglog(M_sun_arr, T_H_K, 'k--', lw=1.8,
                    label=r'$T_H \propto M^{-1}$ [K]')

# Mark solar mass BH
idx1 = 0
ax.plot(M_sun_arr[idx1], ratio[idx1], 'ks', ms=6)
ax.annotate(r'$1\,M_\odot$', xy=(M_sun_arr[idx1]*1.5, ratio[idx1]*1.5),
            fontsize=8)

# Mark T_H = T_c line on right axis
T_c_K_val = T_c_K
ax2.axhline(T_c_K_val, color='k', ls=':', lw=1.0, alpha=0.6)
ax2.annotate(r'$T_c$', xy=(1e8, T_c_K_val*1.5), fontsize=8)

ax.set_xlabel(r'Black-hole mass $M/M_\odot$')
ax.set_ylabel(r'$\rho_c/r_s$  (shell depth)', color='k')
ax2.set_ylabel(r'Hawking temperature $T_H$ [K]', color='k')
ax.set_title('(c) Shell depth and Hawking $T$ vs mass')

lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax.legend(lines, labels, fontsize=7.5, loc='lower left')

# Panel labels
for i, label in enumerate(['(a)', '(b)', '(c)']):
    axes[i].text(-0.13, 1.04, label, transform=axes[i].transAxes,
                 fontsize=11, fontweight='bold', va='top')

# Save
out_pdf = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_bh_information.pdf"
out_png = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_bh_information.png"
fig.savefig(out_pdf, bbox_inches='tight')
fig.savefig(out_png, dpi=200, bbox_inches='tight')
print(f"Saved: {out_pdf}")
print(f"Saved: {out_png}")

# Numerical summary
print("\n── Numerical summary ──")
print(f"rho_c = l_Pl / sqrt(3*pi) = {rho_c_in_lPl:.4f} * l_Pl")
print(f"T_c   = v0*sqrt(6) = {T_c_GeV:.3e} GeV")
M_test_solar = np.array([1, 10, 1e6, 4e6])
for m in M_test_solar:
    m_kg = m * M_sun_kg
    rs = 2*G_N_SI*m_kg/c_SI**2
    th = hbar_SI*c_SI**3/(8*np.pi*G_N_SI*m_kg*k_B_SI)
    print(f"  M={m:.0e} M_sun: r_s={rs:.2e} m, rho_c/r_s={rho_c_analytic_m/rs:.2e}, T_H={th:.2e} K")
