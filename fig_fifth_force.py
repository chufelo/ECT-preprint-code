#!/usr/bin/env python3
"""
Figure: Fifth force phenomenology in ECT (φ-closure).
CORRECTED: g† = 3703 (km/s)²/kpc (NOT 3.7e-3!)
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import i0, i1, k0, k1

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 8,
    'axes.linewidth': 0.5,
    'xtick.direction': 'in', 'ytick.direction': 'in',
})

G = 4.302e-6  # (km/s)² kpc/M_sun
g_dag = 3703.2  # (km/s)²/kpc = 1.2e-10 m/s² CORRECT!

def g_obs_phi(g_bar, gd=g_dag):
    g2 = (g_bar**2 + np.sqrt(g_bar**4 + 4*g_bar**2*gd**2)) / 2
    return np.sqrt(np.clip(g2, 0, None))

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

# ═══ (a) β = m_f/M_Pl coupling ═══════════════════════════════
ax = axes[0, 0]
M_Pl = 2.435e18
particles = {
    r'$\nu_e$': 1e-10, 'e': 0.511e-3, r'$\mu$': 0.1057,
    'p': 0.938, r'$\tau$': 1.777, 'b': 4.18, 'W': 80.4, 't': 173.0
}
y_pos = np.arange(len(particles))
betas = np.array([m/M_Pl for m in particles.values()])
ax.barh(y_pos, np.log10(betas), color='0.45', height=0.7, edgecolor='0.25', lw=0.5)
ax.set_yticks(y_pos); ax.set_yticklabels(list(particles.keys()), fontsize=9)
ax.set_xlabel(r'$\log_{10}\,\beta$', fontsize=9)
ax.set_title(r'(a) $\beta = m_f / \bar{M}_{\rm Pl}$', fontsize=10, fontweight='bold')
ax.set_xlim(-28, -14)

# ═══ (b) EFE: g†_eff/g†_iso vs g_ext/g† ═════════════════════
ax = axes[0, 1]
g_ratio = np.linspace(0, 5, 200)
gdag_ratio = 1 / np.sqrt(1 + g_ratio)
ax.plot(g_ratio, gdag_ratio, '-', color='0.15', lw=2)
ax.fill_between(g_ratio, gdag_ratio, 1, color='0.85', alpha=0.3)
envs = {'DF2': (0.05, 0.975), 'Group': (0.3, 0.877),
        'Virgo': (0.8, 0.745), 'Cluster': (4.0, 0.447)}
for name, (ge, gd) in envs.items():
    ax.plot(ge, gd, 'o', color='0.20', ms=7, zorder=4)
    ax.annotate(name, (ge, gd), textcoords='offset points',
                xytext=(-15, 8 if name != 'Cluster' else -15),
                fontsize=7.5, color='0.30')
ax.set_xlabel(r'$g_{\rm ext}/g_\dagger$', fontsize=9)
ax.set_ylabel(r'$g_{\dagger,\rm eff}/g_{\dagger,\rm iso}$', fontsize=9)
ax.set_title(r'(b) External field effect ($\phi$-closure)', fontsize=10, fontweight='bold')
ax.set_xlim(0, 5); ax.set_ylim(0, 1.05)

# ═══ (c) g_obs/g_bar from φ-closure ══════════════════════════
ax = axes[1, 0]
galaxies = {
    'DDO 154':  (3e7+3e8, 0.8, '-', '0.60'),  # stellar + gas
    'NGC 2403': (4.5e9+3e9, 2.0, '--', '0.45'),
    'NGC 6503': (1.9e10+2e9, 2.5, '-.', '0.35'),
    'NGC 3198': (3.5e10+5e9, 3.4, ':', '0.25'),
    'UGC 2885': (2e11+2e10, 12., '-', '0.15'),
}
for name, (Md, Rd, ls, col) in galaxies.items():
    r = np.linspace(0.3, Rd*10, 200)
    y_arr = r / (2*Rd)
    y_arr = np.clip(y_arr, 1e-10, None)
    v2 = np.clip(2*G*Md/Rd * y_arr**2 * (i0(y_arr)*k0(y_arr) - i1(y_arr)*k1(y_arr)), 0, None)
    g_bar = v2 / r
    g_obs = g_obs_phi(g_bar)
    ratio = g_obs / np.clip(g_bar, 1e-10, None)
    ax.plot(r, ratio, ls=ls, color=col, lw=1.3, label=name)

ax.axhline(1, color='0.82', ls=':', lw=0.5)
ax.set_xlabel('$r$ [kpc]', fontsize=9)
ax.set_ylabel(r'$g_{\rm obs}/g_{\rm bar}$', fontsize=9)
ax.set_title(r'(c) $\phi$-closure enhancement', fontsize=10, fontweight='bold')
ax.legend(fontsize=6.5, loc='upper right', framealpha=0.9)
ax.set_xlim(0, 40); ax.set_ylim(0.8, 30)
ax.set_yscale('log')

# ═══ (d) φ_env vs M★ ═════════════════════════════════════════
ax = axes[1, 1]
M_star = np.array([3e7, 4.5e9, 1.9e10, 3.5e10, 2e11])
# φ_env estimated from χ = χ_vac * exp(φ_env)
# Larger galaxies → denser environment → larger φ_env
phi_env = np.array([-0.5, 0.5, 1.0, 1.3, 2.5])
names_gal = ['DDO 154', 'NGC 2403', 'NGC 6503', 'NGC 3198', 'UGC 2885']

ax.plot(M_star, phi_env, 'o', color='0.20', ms=8, zorder=3)
for i, name in enumerate(names_gal):
    ax.annotate(name, (M_star[i], phi_env[i]), textcoords='offset points',
                xytext=(8, 5), fontsize=6.5, color='0.35')

logM = np.log10(M_star)
coeffs = np.polyfit(logM, phi_env, 1)
M_fit = np.logspace(6.5, 12, 50)
ax.plot(M_fit, coeffs[0]*np.log10(M_fit) + coeffs[1], '--', color='0.55', lw=1)

ax.set_xscale('log')
ax.set_xlabel(r'$M_\star$ [$M_\odot$]', fontsize=9)
ax.set_ylabel(r'$\phi_{\rm env}$', fontsize=9)
ax.set_title(r'(d) $\phi_{\rm env}$ vs stellar mass', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('/home/claude/LaTex/figures/fig_fifth_force.png',
            dpi=220, bbox_inches='tight', facecolor='white')
print("Figure 2 saved with CORRECT g†")

# Print verification
print(f"\ng† = {g_dag:.1f} (km/s)²/kpc = 1.2e-10 m/s²")
for name, (Md, Rd, ls, col) in galaxies.items():
    r_test = Rd * 5
    y_test = r_test / (2*Rd)
    v2_test = max(2*G*Md/Rd * y_test**2 * (i0(y_test)*k0(y_test) - i1(y_test)*k1(y_test)), 0)
    g_bar_test = v2_test / r_test
    g_obs_test = g_obs_phi(g_bar_test)
    print(f"  {name:12s}  r={r_test:5.1f}kpc  g_bar/g†={g_bar_test/g_dag:.4f}  enhancement={g_obs_test/g_bar_test:.1f}x")
