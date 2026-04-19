#!/usr/bin/env python3
"""
Grayscale figures for Appendix A3 (CC), A4 (fσ_8), A5 (ISW).

Produces:
  fig_cc_extraction_bw.pdf
  fig_fsigma8_extraction_bw.pdf
  fig_isw_extraction_bw.pdf
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EPS_DIR    = os.path.join(SCRIPT_DIR, 'epsilon_convergence')
sys.path.insert(0, EPS_DIR)
OUT_DIR = os.path.join(SCRIPT_DIR, '..', 'figures')

# ==================== A3: Cosmic Chronometers ====================
from ch4_cosmic_chronometers import (
    CC_DATA, z_data as z_cc, H_data as H_cc, s_data as s_cc,
    H_ECT as H_CC_ECT, chi2_profile as chi2_cc_profile,
)

eps_grid_cc = np.linspace(-0.02, 0.15, 171)
chi2_grid_cc = np.zeros_like(eps_grid_cc)
H0_grid_cc   = np.zeros_like(eps_grid_cc)
for i, e in enumerate(eps_grid_cc):
    chi2_grid_cc[i], H0_grid_cc[i] = chi2_cc_profile(e)
i_best = int(np.argmin(chi2_grid_cc))
eps_best_cc = eps_grid_cc[i_best]
chi2_best_cc = chi2_grid_cc[i_best]
H0_best_cc = H0_grid_cc[i_best]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 6.4),
                               gridspec_kw={'height_ratios': [1.4, 1]})
z_curve = np.linspace(0, 2.1, 200)
H_LCDM  = H_CC_ECT(z_curve, 67.4, 0.0)
H_retained = H_CC_ECT(z_curve, H0_best_cc, 0.032)
ax1.errorbar(z_cc, H_cc, yerr=s_cc, fmt='o', color='0.2', markersize=5,
             capsize=2, capthick=0.8, elinewidth=0.8, label='Moresco+2022 (31 pts)')
ax1.plot(z_curve, H_LCDM, '--', color='0.2', linewidth=1.3,
         label=r'$\Lambda$CDM ($\varepsilon=0$)')
ax1.plot(z_curve, H_retained, '-', color='0.0', linewidth=1.6,
         label=r'ECT ($\varepsilon=0.032$)')
ax1.set_xlim(0, 2.1)
ax1.set_ylabel(r'$H(z)$ [km s$^{-1}$ Mpc$^{-1}$]', fontsize=10)
ax1.grid(alpha=0.3, linestyle=':')
ax1.legend(loc='upper left', fontsize=9, framealpha=0.95)
ax1.set_title('Cosmic chronometers $H(z)$: data vs. ECT model', fontsize=10)

ax2.plot(eps_grid_cc, chi2_grid_cc - chi2_best_cc, '-', color='0.0', linewidth=1.4)
ax2.axhline(1, color='0.35', linestyle=':', linewidth=0.9)
ax2.axhline(4, color='0.5',  linestyle=':', linewidth=0.9)
ax2.axvline(0.0, color='0.5', linestyle='--', linewidth=0.7)
ax2.text(0.002, 4.2, r'$\Delta\chi^2=4$', fontsize=8, color='0.4')
ax2.text(0.002, 1.15, r'$\Delta\chi^2=1$', fontsize=8, color='0.3')
ax2.axvspan(0.0, 0.087, color='0.55', alpha=0.4,
            label=r'$1\sigma$: $[0,\,0.087]$ (clipped)')
ax2.set_xlim(-0.02, 0.15)
ax2.set_ylim(-0.5, 8)
ax2.set_xlabel(r'$\varepsilon$', fontsize=10)
ax2.set_ylabel(r'$\Delta\chi^2(\varepsilon)$', fontsize=10)
ax2.grid(alpha=0.3, linestyle=':')
ax2.legend(loc='upper right', fontsize=8.5)
plt.tight_layout()
out_cc = os.path.join(OUT_DIR, 'fig_cc_extraction_bw.pdf')
plt.savefig(out_cc, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved {out_cc}")


# ==================== A4: f σ_8 RSD ====================
from ch8_fsigma8 import (
    z_data as z_rsd, fs8_data, fs8_sig,
    chi2_profile as chi2_fs_profile,
    fsigma8_model,
)

eps_grid_fs = np.linspace(-0.12, 0.15, 136)
chi2_grid_fs = np.zeros_like(eps_grid_fs)
s8_grid_fs   = np.zeros_like(eps_grid_fs)
for i, e in enumerate(eps_grid_fs):
    chi2_grid_fs[i], s8_grid_fs[i] = chi2_fs_profile(e)
i_min = int(np.argmin(chi2_grid_fs))
eps_best_fs = eps_grid_fs[i_min]
chi2_best_fs = chi2_grid_fs[i_min]

# 1 sigma upper edge from Brent-refinement point (already computed before)
eps_hi_1s_fs = 0.0396

# Model curves for top panel
z_curve_rsd = np.linspace(0.05, 2.0, 100)
fs8_LCDM = fsigma8_model(z_curve_rsd, 0.0,  0.797)
fs8_ECT  = fsigma8_model(z_curve_rsd, 0.032, 0.771)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 6.4),
                               gridspec_kw={'height_ratios': [1.3, 1]})
ax1.errorbar(z_rsd, fs8_data, yerr=fs8_sig, fmt='o', color='0.2',
             markersize=5, capsize=2, capthick=0.8, elinewidth=0.8,
             label='RSD compilation (14 pts)')
ax1.plot(z_curve_rsd, fs8_LCDM, '--', color='0.2', linewidth=1.3,
         label=r'$\Lambda$CDM ($\varepsilon=0$)')
ax1.plot(z_curve_rsd, fs8_ECT, '-', color='0.0', linewidth=1.6,
         label=r'ECT ($\varepsilon=0.032$)')
ax1.set_xlim(0, 2.1)
ax1.set_ylim(0.2, 0.7)
ax1.set_ylabel(r'$f\sigma_8(z)$', fontsize=10)
ax1.grid(alpha=0.3, linestyle=':')
ax1.legend(loc='lower left', fontsize=9, framealpha=0.95)
ax1.set_title(r'$f\sigma_8$ RSD: data vs. ECT model', fontsize=10)

ax2.plot(eps_grid_fs, chi2_grid_fs - chi2_best_fs, '-', color='0.0',
         linewidth=1.4)
ax2.axhline(1, color='0.35', linestyle=':', linewidth=0.9)
ax2.axhline(4, color='0.5',  linestyle=':', linewidth=0.9)
ax2.axvline(0.0, color='0.3', linestyle='--', linewidth=1.0)
ax2.text(0.003, -0.3, r'physical prior $\varepsilon\geq0$',
         fontsize=8, color='0.2')
ax2.text(-0.11, 4.2, r'$\Delta\chi^2=4$', fontsize=8, color='0.4')
ax2.text(-0.11, 1.15, r'$\Delta\chi^2=1$', fontsize=8, color='0.3')
ax2.axvspan(0.0, eps_hi_1s_fs, color='0.55', alpha=0.4,
            label=rf'retained $1\sigma$: $[0,\,{eps_hi_1s_fs:.4f}]$')
ax2.axvspan(eps_hi_1s_fs, 0.15, color='0.85', alpha=0.4,
            label=r'retained $2\sigma$ (grid-limited)')
ax2.set_xlim(-0.12, 0.15)
ax2.set_ylim(-1, 8)
ax2.set_xlabel(r'$\varepsilon$', fontsize=10)
ax2.set_ylabel(r'$\Delta\chi^2(\varepsilon)$', fontsize=10)
ax2.grid(alpha=0.3, linestyle=':')
ax2.legend(loc='upper right', fontsize=8.5)
plt.tight_layout()
out_fs = os.path.join(OUT_DIR, 'fig_fsigma8_extraction_bw.pdf')
plt.savefig(out_fs, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved {out_fs}")


# ==================== A5: ISW (provisional proxy) ====================
from ch3_isw import A_ISW, kappa_ISW, A_ISW_obs, A_ISW_sigma

fig, ax = plt.subplots(figsize=(7.2, 5.0))

eps_line = np.linspace(-0.15, 0.15, 300)
A_model = np.array([A_ISW(e) for e in eps_line])

# Horizontal bands for observational A_ISW
ax.axhspan(A_ISW_obs - 2*A_ISW_sigma, A_ISW_obs + 2*A_ISW_sigma,
           color='0.85', alpha=0.6,
           label=rf'$A_{{\rm ISW}}^{{\rm obs}}\pm 2\sigma$')
ax.axhspan(A_ISW_obs - A_ISW_sigma, A_ISW_obs + A_ISW_sigma,
           color='0.55', alpha=0.6,
           label=rf'$A_{{\rm ISW}}^{{\rm obs}}={A_ISW_obs}\pm{A_ISW_sigma}$')
ax.axhline(A_ISW_obs, color='0.2', linestyle=':', linewidth=1.0)

# Linear model line
ax.plot(eps_line, A_model, '-', color='0.0', linewidth=1.6,
        label=rf'$A_{{\rm ISW}}^{{\rm model}}=1+\kappa_{{\rm ISW}}\,\varepsilon$, $\kappa_{{\rm ISW}}={kappa_ISW:.0f}$')

# Extracted intervals on eps axis at bottom
ax.axvspan(0.0, 0.0433, ymin=0, ymax=0.05, color='0.55', alpha=0.75)
ax.axvspan(0.0433, 0.0933, ymin=0, ymax=0.05, color='0.85', alpha=0.75)
ax.text(0.02, 0.07, r'retained $1\sigma$: $[0,\,0.0433]$',
        fontsize=9, ha='left', color='0.0', fontweight='bold')

# Physical-prior line
ax.axvline(0.0, color='0.3', linestyle='--', linewidth=1.0)
ax.text(0.003, 1.5, r'physical prior $\varepsilon\geq0$',
        fontsize=9, color='0.2', rotation=90, va='bottom')

# Big annotation: "kappa_ISW not recalibrated"
ax.text(-0.14, 2.0, r'$\kappa_{\rm ISW}$ NOT recalibrated' + '\n' +
        r'on common background',
        fontsize=10, color='0.1', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                  edgecolor='0.3', linewidth=1.0),
        ha='left', va='center')

ax.set_xlim(-0.15, 0.15)
ax.set_ylim(-0.3, 2.5)
ax.set_xlabel(r'$\varepsilon$', fontsize=11)
ax.set_ylabel(r'$A_{\rm ISW}$', fontsize=11)
ax.set_title(r'ISW extraction (provisional proxy): '
             r'$A_{\rm ISW}^{\rm obs}=0.96\pm0.30$', fontsize=10)
ax.grid(alpha=0.3, linestyle=':')
ax.legend(loc='lower right', fontsize=8.5)
plt.tight_layout()
out_isw = os.path.join(OUT_DIR, 'fig_isw_extraction_bw.pdf')
plt.savefig(out_isw, dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved {out_isw}")

print("\n=== ALL A3/A4/A5 GRAYSCALE FIGURES GENERATED ===")
