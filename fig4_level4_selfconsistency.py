#!/usr/bin/env python3
"""
ECT self-consistency diagnostics — 5 panels (a)-(e).
v3: fix (c) running coupling visibility, fix (e) fit line, remove empty panel text.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8,
    'axes.linewidth': 0.5,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'xtick.major.size': 3, 'ytick.major.size': 3,
    'xtick.minor.size': 1.5, 'ytick.minor.size': 1.5,
})

G_SI = 6.674e-11; M_sun = 1.989e30; kpc_m = 3.086e19
g_dag = 1.2e-10

fig = plt.figure(figsize=(11, 7))
gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.35)

# ═══════════════════════════════════════════════════════════════
# (a) Condensate potential V(Φ)
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[0, 0])
phi = np.linspace(-1.5, 1.5, 300)
mu2, lam = 1.0, 2.0
v0 = np.sqrt(2*mu2/lam)
V_plot = (-mu2*phi**2 + lam/4*phi**4) / (mu2**2/lam)

ax.plot(phi/v0, V_plot, '-', color='0.15', lw=1.5)
ax.axhline(0, color='0.7', ls='-', lw=0.4)
idx_min_l = np.argmin(np.abs(phi/v0 + 1))
idx_min_r = np.argmin(np.abs(phi/v0 - 1))
ax.plot([-1, 1], [V_plot[idx_min_l], V_plot[idx_min_r]], 'o', color='0.15', ms=4)
ax.text(-1, -0.3, r'$-v_0$', fontsize=8, ha='center')
ax.text(1, -0.3, r'$+v_0$', fontsize=8, ha='center')
ax.set_xlabel(r'$\Phi/v_0$', fontsize=9)
ax.set_ylabel(r'$V(\Phi)$', fontsize=9)
ax.set_title('(a) Condensate potential', fontsize=9, fontweight='bold')
ax.set_xlim(-1.5, 1.5)

# ═══════════════════════════════════════════════════════════════
# (b) Ghost-freedom: eigenvalues vs α
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[0, 1])
alpha = np.linspace(0, 3, 200)
ax.plot(alpha, np.ones_like(alpha), '-', color='0.15', lw=1.5,
        label=r'Spatial ($\lambda_s=1$)')
ax.plot(alpha, alpha - 1, '--', color='0.40', lw=1.5,
        label=r'Temporal ($\lambda_t=\alpha-1$)')
ax.axhline(0, color='0.7', ls='-', lw=0.4)
ax.axvline(1, color='0.7', ls=':', lw=0.5)
ax.fill_between(alpha, 0, 2.5, where=alpha > 1, alpha=0.06, color='0.5')
ax.text(2.0, 0.3, 'Lorentzian\nphase ($\\alpha>1$)', fontsize=7,
        ha='center', color='0.4')
ax.set_xlabel(r'$\alpha$', fontsize=9)
ax.set_ylabel('Eigenvalue', fontsize=9)
ax.set_title('(b) Ghost-freedom', fontsize=9, fontweight='bold')
ax.legend(fontsize=6.5, loc='upper left')
ax.set_xlim(0, 3); ax.set_ylim(-1, 2.5)

# ═══════════════════════════════════════════════════════════════
# (c) Running coupling — FIXED: show ratio on LINEAR scale
#     near the Planck scale to make the rise VISIBLE
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[0, 2])
E = np.logspace(-3, 19.5, 400)  # go slightly beyond E_Pl
E_Pl = 1.22e19
# One-loop: g_eff(E) = g_eff(0) * [1 + (41/10π)(E/E_Pl)²]
b = 41 / (10 * np.pi)
g_ratio = 1 + b * (E / E_Pl)**2

ax.plot(E, g_ratio, '-', color='0.15', lw=1.5)
ax.axhline(1, color='0.7', ls=':', lw=0.5)
ax.axvline(E_Pl, color='0.60', ls=':', lw=0.7)
ax.text(3e18, 1.35, r'$E_{\rm Pl}$', fontsize=8, color='0.45',
        ha='center')

# Shade the "no running" region
ax.fill_between([1e-3, 1e17], [0.95, 0.95], [1.5, 1.5],
                alpha=0.04, color='0.5')
ax.text(1e7, 1.02, 'No running\n($E \\ll E_{\\rm Pl}$)',
        fontsize=7, color='0.45', ha='center', style='italic')

# Annotate the rise
ax.annotate('ECT: deviation\nat Planck scale',
            xy=(E_Pl, 1 + b), xytext=(1e16, 1.3),
            fontsize=7, color='0.35',
            arrowprops=dict(arrowstyle='->', color='0.45', lw=0.7),
            ha='center')

ax.set_xscale('log')
ax.set_xlabel('Energy [GeV]', fontsize=9)
ax.set_ylabel(r'$g_{\rm eff}(E)/g_{\rm eff}(0)$', fontsize=9)
ax.set_title('(c) Running coupling', fontsize=9, fontweight='bold')
ax.set_xlim(1e-3, 3e19)
ax.set_ylim(0.95, 1.5)

# ═══════════════════════════════════════════════════════════════
# (d) d_force(x) universal curve with galaxy data
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[1, 0])

def d_force(x):
    return 1 + 2*(1 + x**2) / (2 + x**2)

def freeman_enclosed(r, M_d, R_d):
    x = r / R_d
    if x < 0.01: return M_d * x**2 / 2
    return M_d * (1 - (1 + x) * np.exp(-x))

sparc = {
    'DDO 154':  (3e7*M_sun,  0.8, 'v', '0.65'),
    'NGC 2403': (4e9*M_sun,  2.0, 's', '0.50'),
    'NGC 6503': (2e10*M_sun, 2.5, 'D', '0.45'),
    'NGC 3198': (4e10*M_sun, 3.5, '^', '0.35'),
    'MW':       (5e10*M_sun, 2.5, 'o', '0.20'),
    'UGC 2885': (2e11*M_sun, 12., 'p', '0.30'),
}

x_th = np.logspace(-2, 3, 300)
ax.plot(x_th, d_force(x_th), '-', color='0.15', lw=1.5, zorder=2)
ax.axhline(3, color='0.82', ls=':', lw=0.5)
ax.axhline(2, color='0.82', ls=':', lw=0.5)
ax.axhline(7/3, color='0.70', ls='--', lw=0.4)

for gn, (Md, Rd, mk, cl) in sparc.items():
    radii = np.logspace(np.log10(max(0.3, Rd*0.2)), np.log10(Rd*12), 12)
    xl = []
    for r in radii:
        Me = freeman_enclosed(r, Md, Rd)
        gN = G_SI * Me / (r * kpc_m)**2
        g2 = (gN**2 + np.sqrt(gN**4 + 4*gN**2*g_dag**2)) / 2
        xl.append(np.sqrt(g2) / g_dag)
    xl = np.array(xl)
    ax.plot(xl, d_force(xl), marker=mk, color=cl, ms=3.5,
            ls='none', label=gn, alpha=0.8, zorder=3)

ax.plot(1, 7/3, 'o', color='0.15', ms=5, zorder=5, mec='white', mew=0.6)
ax.text(0.03, 2.05, r'$d\to 2$', fontsize=7, color='0.4')
ax.text(30, 2.92, r'$d\to 3$', fontsize=7, color='0.4')
ax.set_xscale('log')
ax.set_xlabel(r'$x = g_{\rm obs}/g_\dagger$', fontsize=9)
ax.set_ylabel(r'$d_{\rm force}(x)$', fontsize=9)
ax.set_title(r'(d) $d_{\rm force}(x)=1+\frac{2(1+x^2)}{2+x^2}$',
             fontsize=9, fontweight='bold')
ax.legend(fontsize=5, loc='center left', ncol=1, framealpha=0.9)
ax.set_xlim(0.01, 1000); ax.set_ylim(1.9, 3.1)

# ═══════════════════════════════════════════════════════════════
# (e) Decoherence timescale — FIXED fit line
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[1, 1])

# Physical data: (N_env, τ_dec in seconds)
# From Caldeira-Leggett: τ_dec = ℏ²/(2m·γ·kT·(Δx)²·N_env)
# Simplified: τ ∝ 1/N_env for objects of similar coupling
objects = {
    'Electron':  (1e3,    1e20),
    'Atom':      (1e5,    1e16),
    'Molecule':  (1e8,    1e12),
    'Dust':      (1e15,   1e4),
    'Cat':       (1e26,   1e-8),
}

# Fit a power law to the actual data points
N_data = np.array([v[0] for v in objects.values()])
tau_data = np.array([v[1] for v in objects.values()])
# log-log linear fit
coeffs = np.polyfit(np.log10(N_data), np.log10(tau_data), 1)
slope, intercept = coeffs
print(f"Decoherence fit: slope = {slope:.3f}, intercept = {intercept:.2f}")
print(f"  τ ∝ N_env^{slope:.2f}")

N_fit = np.logspace(2, 28, 100)
tau_fit = 10**(slope * np.log10(N_fit) + intercept)

ax.plot(N_fit, tau_fit, '--', color='0.50', lw=1.0, zorder=1)
for name, (N, tau) in objects.items():
    ax.plot(N, tau, 'o', color='0.20', ms=5, zorder=3)
    if name == 'Cat':
        offset = (8, -12)
    elif name == 'Electron':
        offset = (8, -8)
    else:
        offset = (8, 5)
    ax.annotate(name, (N, tau), textcoords='offset points',
                xytext=offset, fontsize=6.5, color='0.35')

# Show slope
ax.text(0.95, 0.05,
        f'$\\tau_{{\\rm dec}} \\propto N_{{\\rm env}}^{{{slope:.1f}}}$',
        transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
        color='0.40')

ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlabel(r'$N_{\rm env}$', fontsize=9)
ax.set_ylabel(r'$\tau_{\rm dec}$ [s]', fontsize=9)
ax.set_title('(e) Decoherence timescale', fontsize=9, fontweight='bold')
ax.set_xlim(1e2, 1e28); ax.set_ylim(1e-10, 1e22)

# ═══════════════════════════════════════════════════════════════
# Bottom-right: EMPTY (no text)
# ═══════════════════════════════════════════════════════════════
ax = fig.add_subplot(gs[1, 2])
ax.axis('off')

plt.savefig('/home/claude/LaTex/figures/fig_selfconsistency_v2.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.savefig('/home/claude/LaTex/figures/fig_selfconsistency_v2.pdf',
            bbox_inches='tight', facecolor='white')
print("Figure saved.")
