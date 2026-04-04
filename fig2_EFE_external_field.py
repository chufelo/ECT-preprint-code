#!/usr/bin/env python3
"""
fig2_EFE_external_field.py
===========================
Figure: ECT External Field Effect (EFE) on galaxy rotation curves.

Paper location: Figure 2, Section 11.2 (EFE prediction)

Formula: r_{0,eff} = r_{0,iso} / sqrt(1 + g_ext/g_dag)

Physics:
  In ECT, the condensate scale r_0 characterises where G_eff(r) deviates
  from Newtonian G. When a galaxy is embedded in an external gravitational
  field g_ext (from a cluster or group), the condensate is partially
  suppressed, reducing r_{0,eff}.

  The suppression formula r_{0,eff} = r_{0,iso}/sqrt(1 + g_ext/g_dag)
  is a ZERO-PARAMETER prediction: once r_{0,iso} is known for an isolated
  galaxy, the effect of any external field is fully determined.

  g_dag = c^2/r_0 ~ 1.2e-10 m/s^2 is the ECT/RAR acceleration scale.
  In rotation curve units: g_dag = 3.724e-3 (km/s)^2/kpc.

  This is analogous to the External Field Effect (EFE) in MOND, but
  derived from condensate physics rather than postulated.

Output: ECT_EFE_rotation_curves.png, ECT_EFE_rotation_curves.pdf

Dependencies: numpy, matplotlib, scipy
Usage: python fig2_EFE_external_field.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import i0, i1, k0, k1

# ============================================================
# Plot style
# ============================================================
plt.rcParams.update({
    'font.family': 'serif', 'font.size': 9,
    'axes.linewidth': 0.8, 'axes.grid': True, 'grid.alpha': 0.3,
})

C_BARYON = '#2166ac'
C_ECT    = '#1a9641'
C_EFE    = '#d73027'
C_OBS    = '#333333'
C_MOND   = '#f4a442'
C_ACCENT2= '#7b2d8b'

# ============================================================
# Physical constants (rotation curve units)
# ============================================================
G = 4.302e-6         # (km/s)^2 kpc / Msun
g_dag = 3.724e-3     # (km/s)^2/kpc = 1.20e-10 m/s^2

# ============================================================
# Baryonic model functions
# ============================================================
def v_baryon(r, M_d, R_d):
    """Newtonian exponential disc rotation curve (Freeman 1970)."""
    y = r / (2 * R_d)
    y = np.clip(y, 1e-10, 50)
    term = y**2 * (i0(y)*k0(y) - i1(y)*k1(y))
    return np.sqrt(np.clip(2 * G * M_d / R_d * term, 0, None))

def v_ect(r, M_d, R_d, r0):
    """ECT rotation curve: G -> G*sqrt(1+(r/r0)^2)."""
    y = r / (2 * R_d)
    y = np.clip(y, 1e-10, 50)
    G_eff = G * np.sqrt(1 + (r / r0)**2)
    term = y**2 * (i0(y)*k0(y) - i1(y)*k1(y))
    return np.sqrt(np.clip(2 * G_eff * M_d / R_d * term, 0, None))

def r0_eff_func(r0_iso, g_ext):
    """ECT EFE formula: r_{0,eff} = r_{0,iso} / sqrt(1 + g_ext/g_dag).
    
    g_ext must be in the same units as g_dag: (km/s)^2/kpc.
    """
    return r0_iso / np.sqrt(1 + g_ext / g_dag)

# ============================================================
# Galaxy parameters
# ============================================================
M_d_3198, R_d_3198, r0_iso_3198 = 3.5e10, 3.2, 6.7
M_d_2403, R_d_2403, r0_iso_2403 = 4.5e9,  1.8, 2.3

obs_3198 = {
    'r': [1.2,2.4,3.6,4.8,6.0,7.5,9.0,11.0,13.5,16.0,19.0,22.0,25.0,28.0,31.0,34.0],
    'v': [148,155,158,162,161,158,155,152,150,150,148,148,147,148,148,147],
    'e': [8,7,6,5,5,4,4,4,5,5,5,6,7,7,8,9],
}
obs_2403 = {
    'r': [0.9,1.8,2.7,3.6,4.5,5.5,7.0,8.5,10.0,12.0,14.5,17.0,20.0],
    'v': [90,110,120,128,132,134,134,132,130,128,127,125,125],
    'e': [6,5,5,4,4,4,4,5,5,5,6,7,8],
}

r_range = np.linspace(0.1, 35, 500)

fig = plt.figure(figsize=(10, 10))
gs  = fig.add_gridspec(3, 2, hspace=0.32, wspace=0.3)

# ---- (a) NGC 3198 isolated ----
ax1 = fig.add_subplot(gs[0, 0])
vb = v_baryon(r_range, M_d_3198, R_d_3198)
vs = v_ect(r_range, M_d_3198, R_d_3198, r0_iso_3198)
ax1.plot(r_range, vb, '--', color=C_BARYON, lw=1.2, label='Baryons (Newton)')
ax1.plot(r_range, vs, '-',  color=C_ECT,   lw=1.5, label=f'ECT isolated ($r_0$={r0_iso_3198} kpc)')
ax1.errorbar(obs_3198['r'], obs_3198['v'], yerr=obs_3198['e'],
             fmt='o', color=C_OBS, ms=4, capsize=2, capthick=0.8, elinewidth=0.8,
             label='Observations (SPARC)', zorder=5)
ax1.text(0.03, 0.95, '(a) NGC 3198, isolated', transform=ax1.transAxes, fontsize=8, va='top')
ax1.set_xlabel(r'$r$ [kpc]'); ax1.set_ylabel(r'$V$ [km/s]')
ax1.set_xlim(0, 35); ax1.set_ylim(0, 200)
ax1.legend(fontsize=6); ax1.minorticks_on()

# ---- (b) NGC 3198 + EFE ----
# g_ext = 5e-12 m/s^2 = 5e-12 / 3.24e-14 (km/s)^2/kpc = ...
# Unit conversion: 1 m/s^2 = 1/(3.086e19 m/kpc) * (1 m/s)^2 * 1e-6 km^2/m^2
# = 1e-6 / 3.086e19 (km/s)^2/kpc = 3.241e-26 -> NO
# Simpler: g_dag = 1.2e-10 m/s^2 = 3.724e-3 (km/s)^2/kpc
# => 1 (km/s)^2/kpc = 1.2e-10 / 3.724e-3 m/s^2 = 3.22e-8 m/s^2
# => 1 m/s^2 = 1/3.22e-8 (km/s)^2/kpc = 3.10e7 (km/s)^2/kpc
# g_ext = 5e-12 m/s^2 * 3.10e7 (km/s)^2/kpc per (m/s^2) = 1.55e-4 (km/s)^2/kpc
conv = g_dag / 1.2e-10  # (km/s)^2/kpc per (m/s^2)
g_ext_3198_si = 5e-12   # m/s^2
g_ext_3198    = g_ext_3198_si * conv  # (km/s)^2/kpc
r0e_3198      = r0_eff_func(r0_iso_3198, g_ext_3198)

ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(r_range, vb, '--', color=C_BARYON, lw=1.2, label='Baryons (Newton)')
ax2.plot(r_range, vs, '-',  color=C_ECT,   lw=1.0, alpha=0.4,
         label=f'ECT isolated ($r_0$={r0_iso_3198} kpc)')
ax2.plot(r_range, v_ect(r_range, M_d_3198, R_d_3198, r0e_3198),
         '-', color=C_EFE, lw=1.5,
         label=f'ECT+EFE ($r_{{0,\\mathrm{{eff}}}}$={r0e_3198:.2f} kpc)')
ax2.errorbar(obs_3198['r'], obs_3198['v'], yerr=obs_3198['e'],
             fmt='o', color=C_OBS, ms=4, capsize=2, capthick=0.8, elinewidth=0.8,
             label='Observations (SPARC)', zorder=5)
ax2.text(0.03, 0.95, r'(b) NGC 3198, $g_{\rm ext}=5\times10^{-12}$ m/s$^2$',
         transform=ax2.transAxes, fontsize=8, va='top')
ax2.set_xlabel(r'$r$ [kpc]'); ax2.set_ylabel(r'$V$ [km/s]')
ax2.set_xlim(0, 35); ax2.set_ylim(0, 200)
ax2.legend(fontsize=5.5); ax2.minorticks_on()

# ---- (c) NGC 2403 isolated ----
ax3 = fig.add_subplot(gs[1, 0])
vb2 = v_baryon(r_range, M_d_2403, R_d_2403)
vs2 = v_ect(r_range, M_d_2403, R_d_2403, r0_iso_2403)
ax3.plot(r_range, vb2, '--', color=C_BARYON, lw=1.2, label='Baryons (Newton)')
ax3.plot(r_range, vs2, '-',  color=C_ECT,   lw=1.5, label=f'ECT isolated ($r_0$={r0_iso_2403} kpc)')
ax3.errorbar(obs_2403['r'], obs_2403['v'], yerr=obs_2403['e'],
             fmt='o', color=C_OBS, ms=4, capsize=2, capthick=0.8, elinewidth=0.8,
             label='Observations (SPARC)', zorder=5)
ax3.text(0.03, 0.95, '(c) NGC 2403, isolated', transform=ax3.transAxes, fontsize=8, va='top')
ax3.set_xlabel(r'$r$ [kpc]'); ax3.set_ylabel(r'$V$ [km/s]')
ax3.set_xlim(0, 35); ax3.set_ylim(0, 200)
ax3.legend(fontsize=6); ax3.minorticks_on()

# ---- (d) NGC 2403 + EFE ----
g_ext_2403_si = 1.5e-11  # m/s^2
g_ext_2403    = g_ext_2403_si * conv
r0e_2403      = r0_eff_func(r0_iso_2403, g_ext_2403)

ax4 = fig.add_subplot(gs[1, 1])
ax4.plot(r_range, vb2, '--', color=C_BARYON, lw=1.2, label='Baryons (Newton)')
ax4.plot(r_range, vs2, '-',  color=C_ECT,   lw=1.0, alpha=0.4,
         label=f'ECT isolated ($r_0$={r0_iso_2403} kpc)')
ax4.plot(r_range, v_ect(r_range, M_d_2403, R_d_2403, r0e_2403),
         '-', color=C_EFE, lw=1.5,
         label=f'ECT+EFE ($r_{{0,\\mathrm{{eff}}}}$={r0e_2403:.2f} kpc)')
ax4.errorbar(obs_2403['r'], obs_2403['v'], yerr=obs_2403['e'],
             fmt='o', color=C_OBS, ms=4, capsize=2, capthick=0.8, elinewidth=0.8,
             label='Observations (SPARC)', zorder=5)
ax4.text(0.03, 0.95, r'(d) NGC 2403, $g_{\rm ext}=1.5\times10^{-11}$ m/s$^2$',
         transform=ax4.transAxes, fontsize=8, va='top')
ax4.set_xlabel(r'$r$ [kpc]'); ax4.set_ylabel(r'$V$ [km/s]')
ax4.set_xlim(0, 35); ax4.set_ylim(0, 200)
ax4.legend(fontsize=5.5); ax4.minorticks_on()

# ---- (e) Parametric study ----
ax5 = fig.add_subplot(gs[2, 0])
M_ref, R_ref, r0_ref = 5e10, 3.0, 8.0
vb_ref = v_baryon(r_range, M_ref, R_ref)
ax5.plot(r_range, vb_ref, '--', color=C_BARYON, lw=1.2, label='Baryons (Newton)')
ax5.plot(r_range, v_ect(r_range, M_ref, R_ref, r0_ref), '-', color=C_ECT, lw=1.5,
         label=r'Isolated ($g_{\rm ext}$=0)')
g_ext_list = [1e-12, 5e-12, 1.5e-11, 1e-10, 5e-10]  # m/s^2
colors_efe = ['#CC9900', '#CC6600', '#CC3333', '#AA22AA', '#6666CC']
for ge_si, ce in zip(g_ext_list, colors_efe):
    ge = ge_si * conv
    r0e = r0_eff_func(r0_ref, ge)
    ax5.plot(r_range, v_ect(r_range, M_ref, R_ref, r0e), '-', color=ce, lw=1.0,
             label=f'$g_{{\\rm ext}}$={ge_si:.0e} m/s$^2$ ({ge_si/(1.2e-10):.3f} $g^\\dagger$)')
ax5.text(0.03, 0.95, r'(e) $M_\star=5\times10^{10}\,M_\odot$, $r_{0,{\rm iso}}$=8 kpc',
         transform=ax5.transAxes, fontsize=8, va='top')
ax5.set_xlabel(r'$r$ [kpc]'); ax5.set_ylabel(r'$V$ [km/s]')
ax5.set_xlim(0, 35); ax5.set_ylim(0, 260)
ax5.legend(fontsize=5, loc='lower right'); ax5.minorticks_on()

# ---- (f) Suppression curve ----
ax6 = fig.add_subplot(gs[2, 1])
x_ratio = np.logspace(-3, 1.5, 500)
y_ratio = 1.0 / np.sqrt(1 + x_ratio)
ax6.plot(x_ratio, y_ratio, '-', color=C_ECT, lw=2.0,
         label=r'$r_{0,\rm eff}/r_{0,\rm iso} = 1/\sqrt{1+g_{\rm ext}/g^\dagger}$')

envs = [
    (0.04, 'Weak groups\n(DF2/NGC1052)', C_BARYON),
    (0.12, 'Typical\ngroups', C_EFE),
    (0.5,  'Virgo\n(outskirts)', C_MOND),
    (0.7,  'Virgo\n(center)', C_ACCENT2),
]
for gx, lbl, clr in envs:
    yv = 1.0 / np.sqrt(1 + gx)
    ax6.plot(gx, yv, 'o', color=clr, ms=8, zorder=5)
    ax6.annotate(lbl, (gx, yv), textcoords='offset points', xytext=(8, -5),
                 fontsize=6, color=clr)

ax6.axvline(1.0, color='gray', ls=':', lw=0.8)
ax6.text(1.05, 0.95, r'$g_{\rm ext} = g^\dagger$', fontsize=7, color='gray')
ax6.axhline(0.5, color=C_MOND, ls='--', lw=0.8, alpha=0.5)
ax6.text(0.03, 0.95, '(f)', transform=ax6.transAxes, fontsize=8, va='top', fontweight='bold')
ax6.set_xscale('log')
ax6.set_xlabel(r'$g_{\rm ext} / g^\dagger$')
ax6.set_ylabel(r'$r_{0,\rm eff} / r_{0,\rm iso}$')
ax6.set_xlim(1e-3, 30); ax6.set_ylim(0, 1.05)
ax6.legend(fontsize=6.5, loc='lower left'); ax6.minorticks_on()

plt.savefig('ECT_EFE_rotation_curves.png', dpi=300, bbox_inches='tight')
plt.savefig('ECT_EFE_rotation_curves.pdf', bbox_inches='tight')
plt.close()
print("Saved: ECT_EFE_rotation_curves.png, ECT_EFE_rotation_curves.pdf")
