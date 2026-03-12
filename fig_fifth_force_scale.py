#!/usr/bin/env python3
"""Figure 3: Scale dependence of fifth interaction — φ-screening + acceleration budget."""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import i0, i1, k0, k1

plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.linewidth': 0.5,
    'xtick.direction': 'in', 'ytick.direction': 'in'})

G = 4.302e-6
g_dag = 3703.2  # CORRECT: (km/s)²/kpc

def g_obs_phi(g_bar, gd=g_dag):
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4*g_bar**2*gd**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# ═══ (a) F₅/F₅^max: relative φ-effect for 3 galaxy types ═════
densities = {
    r'Dense ($\rho = 10^3\bar\rho$)': (5e10+5e9, 2.5, '--', '0.55'),
    r'Field ($\rho = \bar\rho$)': (5e9+3e9, 2.0, '-.', '0.35'),
    r'Void ($\rho = 0.1\bar\rho$)': (3e7+3e8, 0.8, '-', '0.15'),
}

for label, (Md, Rd, ls, col) in densities.items():
    r = np.linspace(0.3, 50, 300)
    y = r / (2*Rd); y = np.clip(y, 1e-10, None)
    v2 = np.clip(2*G*Md/Rd * y**2 * (i0(y)*k0(y) - i1(y)*k1(y)), 0, None)
    g_bar = v2 / r
    g_obs = g_obs_phi(g_bar)
    # F₅ ∝ (g_obs - g_bar), normalized to max
    F5 = g_obs - g_bar
    F5_norm = F5 / np.max(F5) if np.max(F5) > 0 else F5
    ax1.plot(r, F5_norm, ls=ls, color=col, lw=1.5, label=label)

ax1.set_xlabel('$r$ [kpc]', fontsize=10)
ax1.set_ylabel(r'$F_5/F_5^{\rm max}$', fontsize=10)
ax1.set_title(r'(a) Fifth force range: $\phi$-screening', fontsize=10, fontweight='bold')
ax1.legend(fontsize=7.5, loc='upper right')
ax1.set_xlim(0, 50); ax1.set_ylim(0, 1.1)

# ═══ (b) Acceleration budget for MW-type galaxy ═══════════════
Md_MW = 5.5e10; Rd_MW = 2.5
phi_env = 2.15  # representative
r = np.linspace(0.5, 25, 200)
y = r / (2*Rd_MW); y = np.clip(y, 1e-10, None)
v2_bar = np.clip(2*G*Md_MW/Rd_MW * y**2 * (i0(y)*k0(y) - i1(y)*k1(y)), 0, None)
g_bar = v2_bar / r
g_obs = g_obs_phi(g_bar)
g_cond = g_obs - g_bar  # condensate contribution

ax2.plot(r, g_bar, '--', color='0.55', lw=1.3, label='Newtonian $g_{\\rm bar}$')
ax2.plot(r, g_obs, '-', color='0.15', lw=1.8, label='ECT total $g_{\\rm obs}$')
ax2.plot(r, g_cond, ':', color='0.35', lw=1.3, label='Condensate $g_{\\rm obs}-g_{\\rm bar}$')
ax2.axhline(g_dag, color='0.70', ls='-.', lw=0.8)
ax2.text(22, g_dag*1.3, r'$g_\dagger$', fontsize=8, color='0.50')

ax2.set_xlabel('$r$ [kpc]', fontsize=10)
ax2.set_ylabel(r'$g$ [(km/s)$^2$/kpc]', fontsize=10)
ax2.set_title(r'(b) Acceleration budget (MW-type)', fontsize=10, fontweight='bold')
ax2.legend(fontsize=7.5, loc='upper right')
ax2.set_xlim(0, 25)
ax2.set_yscale('log')
ax2.set_ylim(1e1, 1e5)

plt.tight_layout()
plt.savefig('/home/claude/LaTex/figures/fig_fifth_force_scale.png',
            dpi=220, bbox_inches='tight', facecolor='white')
print("Figure 3 saved")
