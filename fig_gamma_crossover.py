"""
ECT Γ_loop crossover map — log-scale grayscale, clean layout
v4: labels below, data labels shifted left, grid added
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 12, 'mathtext.fontset': 'cm',
})

fig, ax = plt.subplots(figsize=(10, 5))

G = np.logspace(-3, 2, 500)
P = np.exp(-G)
ax.plot(G, P, 'k-', lw=2.5, zorder=10,
        label=r'$P_{\rm back}/P_{\rm fwd}=e^{-\Gamma_{\rm loop}}$')

# Regime shading (grayscale)
ax.axvspan(1e-3, 0.15, alpha=0.08, color='#888')
ax.axvspan(2.0, 100, alpha=0.08, color='#888')

# Regime labels — BOTTOM of graph, large bold
ax.text(0.015, 0.06, 'Coherent\nregime', fontsize=12, fontweight='bold',
        va='bottom', ha='left', color='#444')
ax.text(0.55, 0.06, 'Marginal', fontsize=12, fontweight='bold',
        va='bottom', ha='center', color='#444')
ax.text(12, 0.06, 'Effectively\nclassical\nregime', fontsize=12, fontweight='bold',
        va='bottom', ha='center', color='#444')

# Data points
ax.plot(0.006, np.exp(-0.006), 's', ms=11, color='#333', zorder=12)
ax.annotate('Procopio 2015\n$V=0.994$', xy=(0.006, np.exp(-0.006)),
            xytext=(0.0025, 0.86), fontsize=10, ha='left',
            arrowprops=dict(arrowstyle='->', lw=1.2, color='#555'))

ax.plot(0.062, np.exp(-0.062), 'D', ms=10, color='#555', zorder=12)
ax.annotate('Jacques 2007\n(closed config.)\n$V\\approx 0.94$',
            xy=(0.062, np.exp(-0.062)), xytext=(0.015, 0.68),
            fontsize=10, ha='left',
            arrowprops=dict(arrowstyle='->', lw=1.2, color='#555'))

# Theory thresholds
ax.axvline(0.25, color='#666', ls='--', lw=1.5)
ax.axvline(np.log(np.sqrt(2)), color='#666', ls='--', lw=1.5)
ax.axvline(1.0, color='#aaa', ls=':', lw=1.5)

# Boxed annotations — spread apart
bbox = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#888',
            alpha=0.92, lw=1.2)
ax.text(np.log(np.sqrt(2)), 0.40, 'Bell/CHSH\ncrossover', fontsize=10,
        ha='center', va='center', fontweight='bold', bbox=bbox)
ax.text(0.25, 0.20, 'Info bound\n(1 bit)', fontsize=10,
        ha='center', va='center', fontweight='bold', bbox=bbox)
ax.text(1.0, 0.62, r'$\Gamma=1$', fontsize=10,
        ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2',
        facecolor='white', edgecolor='#bbb', alpha=0.9, lw=1.0))

# Grid (subtle)
ax.grid(True, which='major', color='#ddd', lw=0.6, alpha=0.7)
ax.grid(True, which='minor', color='#eee', lw=0.3, alpha=0.5)
ax.set_axisbelow(True)

ax.set_xscale('log')
ax.set_xlabel(r'$\Gamma_{\rm loop}$', fontsize=14)
ax.set_ylabel(r'$P_{\rm back}/P_{\rm fwd}$', fontsize=14)
ax.set_xlim(1e-3, 100)
ax.set_ylim(0, 1.05)
ax.legend(loc='upper right', fontsize=11, framealpha=0.95)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_gamma_crossover OK")
