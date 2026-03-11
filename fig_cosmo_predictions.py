#!/usr/bin/env python3
"""
Figure 11: Cosmological predictions of ECT.

Three panels:
  (a) Redshift anomaly: δz = ½ δφ vs |δφ|
      - General ECT: spatially varying Lorentz-order field φ
        produces anomalous redshift contribution.
      - Horizontal line: DESI spectroscopic precision.
      - No dependence on galactic G_eff(r) or v₀(r).

  (b) Dark energy EOS w(z):
      - ECT: w₀ = -1 + 2ρ_kin/(3ρ_cond) ≈ -0.83
        (calibrated to DESI 2024, not derived from first principles).
      - ΛCDM: w = -1 (cosmological constant).
      - DESI 2024 1σ band.
      - Pure condensate thermodynamics, no galactic physics.

  (c) Running gravitational coupling G_eff(z)/G_N:
      - ECT: G_eff(z) = G_N(1+z)^{2ε}, ε ≈ 0.01
        (from cosmological evolution of condensate amplitude v₀(z)).
      - GR: G = const.
      - ΔH₀ ≈ 3 km/s/Mpc shift.
      - This is COSMOLOGICAL G evolution, NOT galactic G_eff(r).

All formulas are general ECT condensate physics.
None depend on the galactic φ-closure or v₀(r) profile.

Corresponding paper: ECT preprint (Blagovidov, 2025)
  Section 13.3 (dark energy), 13.6 (Hubble tension),
  13.8 (redshift anomalies).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Grayscale style ──────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'axes.linewidth': 0.6,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.top': True,
    'ytick.right': True,
})

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4.2))

# ════════════════════════════════════════════════════════════
# (a) Redshift anomaly: δz = ½ δφ
# ════════════════════════════════════════════════════════════
dphi = np.linspace(0, 0.05, 200)
dz = 0.5 * dphi

ax1.plot(dphi, dz, '-', color='black', lw=2.0,
         label=r'$\delta z = \frac{1}{2}\,\delta\phi$')

# DESI spectroscopic precision ~ 10^{-4} in redshift
desi_precision = 1e-4
ax1.axhline(desi_precision, ls='--', color='0.50', lw=1.0,
            label='DESI precision')

# Shade detectable region
ax1.fill_between(dphi, desi_precision, dz,
                 where=dz > desi_precision,
                 alpha=0.15, color='0.40', hatch='///')

ax1.set_xlabel(r'$|\delta\phi|$ (Lorentz-order fluctuation)', fontsize=10)
ax1.set_ylabel(r'$\delta z$', fontsize=10)
ax1.set_title('(a) Redshift anomaly', fontsize=10, fontweight='bold')
ax1.legend(fontsize=8, loc='upper left')
ax1.set_xlim(0, 0.05)
ax1.set_ylim(0, 0.026)

# ════════════════════════════════════════════════════════════
# (b) Dark energy EOS w(z)
#     ECT: w(z) = w₀ + wₐ z/(1+z)
#     w₀ ≈ -0.83, wₐ ≈ -0.75 (CPL parametrization)
# ════════════════════════════════════════════════════════════
z = np.linspace(0, 2.0, 300)

# ECT prediction
w0_ect = -0.83
wa_ect = -0.75
w_ect = w0_ect + wa_ect * z / (1 + z)

# ΛCDM
w_lcdm = -1.0 * np.ones_like(z)

# DESI 2024 1σ band around ECT
w0_err = 0.059
w_upper = (w0_ect + w0_err) + wa_ect * z / (1 + z)
w_lower = (w0_ect - w0_err) + wa_ect * z / (1 + z)

ax2.fill_between(z, w_lower, w_upper, alpha=0.20, color='0.50',
                 label=r'DESI 2024 $1\sigma$')
ax2.plot(z, w_ect, '-', color='black', lw=2.0,
         label=r'ECT: $w_0 = -0.83$')
ax2.plot(z, w_lcdm, '--', color='0.50', lw=1.5,
         label=r'$\Lambda$CDM: $w = -1$')

ax2.set_xlabel('Redshift $z$', fontsize=10)
ax2.set_ylabel(r'$w(z)$', fontsize=10)
ax2.set_title('(b) Dark energy EOS', fontsize=10, fontweight='bold')
ax2.legend(fontsize=8, loc='lower left')
ax2.set_xlim(0, 2.0)
ax2.set_ylim(-1.1, -0.6)

# ════════════════════════════════════════════════════════════
# (c) Running G and Hubble tension
#     ECT: G_eff(z) = G_N (1+z)^{2ε}, ε ≈ 0.01
#     This is COSMOLOGICAL evolution from v₀(z), not galactic.
# ════════════════════════════════════════════════════════════
z_c = np.linspace(0, 1200, 1000)

eps = 0.01
G_eff = (1 + z_c)**(2 * eps)
G_const = np.ones_like(z_c)

ax3.plot(z_c, G_eff, '-', color='black', lw=2.0,
         label=r'ECT: $\varepsilon = 0.01$')
ax3.plot(z_c, G_const, '--', color='0.50', lw=1.5,
         label=r'$G = \mathrm{const}$ (GR)')

# Mark the Hubble tension shift
ax3.annotate(r'$\Delta H_0 \sim 3\,\mathrm{km/s/Mpc}$',
             xy=(1000, G_eff[np.argmin(np.abs(z_c - 1000))]),
             xytext=(600, 1.12),
             arrowprops=dict(arrowstyle='->', color='0.30', lw=1.0),
             fontsize=8, color='0.20')

ax3.set_xlabel('Redshift $z$', fontsize=10)
ax3.set_ylabel(r'$G_{\mathrm{eff}}(z)/G_N$', fontsize=10)
ax3.set_title('(c) Running $G$ and Hubble tension',
              fontsize=10, fontweight='bold')
ax3.legend(fontsize=8, loc='upper left')
ax3.set_xlim(0, 1200)
ax3.set_ylim(0.98, 1.15)

plt.tight_layout()
plt.savefig('/home/claude/LaTex/figures/fig_cosmo_predictions.png',
            dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('/home/claude/fig_cosmo_predictions.pdf',
            bbox_inches='tight', facecolor='white')
plt.close()
print("fig_cosmo_predictions.png saved")
