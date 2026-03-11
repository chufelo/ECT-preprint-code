#!/usr/bin/env python3
"""
ECT regime diagram: phi vs log10(g/g_dag).

Physics:
  The Lorentz-order field phi = ln(chi/chi_vac) and the local
  acceleration g determine which gravitational regime applies.

  Four regimes:
  1. Newtonian/screened: g > g_dag, moderate-high phi
     -> GR recovered, phi-branch inactive
  2. Critical phi-branch: g < g_dag, moderate phi
     -> mu(g/g_dag)*g = g_bar, flat rotation curves
  3. Deep-MOND/void: g << g_dag, low phi
     -> maximum gravitational enhancement
  4. Quantum/Planckian: g >> g_dag, low phi
     -> condensate incoherent, Lorentzian structure breaks down

  Screening boundary: high phi (dense environments) -> GR
  regardless of g. This is the chameleon-like mechanism.

Representative systems:
  - Planck:       phi ~ -1,   log(g/g_dag) ~ 5
  - Solar System: phi ~ 2.5,  log(g/g_dag) ~ 2
  - Lab:          phi ~ 4,    log(g/g_dag) ~ 1
  - Spiral disk:  phi ~ 0.5,  log(g/g_dag) ~ 0
  - Cluster:      phi ~ 1.5,  log(g/g_dag) ~ -0.5
  - Void dwarf:   phi ~ -0.5, log(g/g_dag) ~ -1.5
  - Cosmic void:  phi ~ -1,   log(g/g_dag) ~ -4

Screening boundary:
  phi_screen(g) ~ phi_0 + slope * log10(g/g_dag)
  Objects to the right of this boundary are screened (GR).

All in grayscale for publication.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 9,
    'axes.linewidth': 0.5,
    'xtick.direction': 'in', 'ytick.direction': 'in',
})

fig, ax = plt.subplots(figsize=(7, 6))

# Axes
phi = np.linspace(-2, 5, 200)
log_g = np.linspace(-6, 6, 200)

# Critical line: g = g_dag (log_g = 0)
ax.axhline(0, color='0.50', ls='-', lw=1.0)
ax.text(-1.8, 0.2, r'$g = g_\dagger$', fontsize=9, color='0.40')

# Screening boundary (diagonal)
phi_screen = np.linspace(-0.5, 5, 50)
g_screen = -1.5 * (phi_screen - 1)
ax.plot(phi_screen, g_screen, '-', color='0.60', lw=1.5)
ax.fill_between(phi_screen, g_screen, 6, alpha=0.08, color='0.5',
                hatch='///', edgecolor='0.70')
ax.text(3.5, -0.5, 'Screened\n(dense)', fontsize=8, color='0.45',
        ha='center', style='italic')
ax.text(1.5, 1.2, 'matter $\\to$ screening', fontsize=7,
        color='0.50', rotation=-55, ha='center')

# Regime labels
ax.text(-1.5, 3.5, 'Quantum /\nPlanckian', fontsize=9, color='0.30',
        ha='center', fontweight='bold')
ax.text(1.5, 2, 'Newtonian (GR)\nscreened', fontsize=9, color='0.30',
        ha='center', fontweight='bold')
ax.text(-1.2, -0.8, 'MOND-like\ncritical $\\phi$-branch', fontsize=9,
        color='0.20', ha='center', fontweight='bold')
ax.text(-1.2, -4, 'Deep-MOND\nvoid regime', fontsize=9, color='0.30',
        ha='center', fontweight='bold')

# Representative systems
systems = {
    'Planck':      (-0.5,  5.0),
    'Solar System': (2.5,  2.0),
    'Lab':          (4.0,  1.0),
    'Spiral disk':  (0.5,  -0.3),
    'Cluster':      (1.5,  -0.5),
    'Void dwarf':  (-0.5,  -1.5),
    'Cosmic void': (-1.0,  -3.5),
}
for name, (p, g) in systems.items():
    ax.plot(p, g, 'o', color='0.25', ms=6, zorder=4)
    offset = (8, 5)
    if name == 'Lab': offset = (8, -10)
    if name == 'Cosmic void': offset = (8, 5)
    ax.annotate(name, (p, g), textcoords='offset points',
                xytext=offset, fontsize=7.5, color='0.35')

ax.set_xlabel(r'$\phi = \ln(\chi/\chi_{\rm vac})$', fontsize=11)
ax.set_ylabel(r'$\log_{10}(g/g_\dagger)$', fontsize=11)
ax.set_title('ECT Regime Diagram', fontsize=11, fontweight='bold')
ax.set_xlim(-2, 5); ax.set_ylim(-6, 6)
ax.tick_params(which='both', top=True, right=True)

plt.tight_layout()
plt.savefig('fig_regime_diagram.png', dpi=220, bbox_inches='tight',
            facecolor='white')
plt.savefig('fig_regime_diagram.pdf', bbox_inches='tight',
            facecolor='white')
print('Saved: fig_regime_diagram.png/pdf')
