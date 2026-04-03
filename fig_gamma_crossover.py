"""
ECT Γ_loop crossover map — log-scale grayscale, clean labels
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
ax.plot(G, P, 'k-', lw=2.5, label=r'$P_{\rm back}/P_{\rm fwd}=e^{-\Gamma_{\rm loop}}$')

# Regime shading (grayscale)
ax.axvspan(1e-3, 0.15, alpha=0.08, color='#888')
ax.axvspan(2.0, 100, alpha=0.08, color='#888')

# Regime labels — single set, bold, at top
ax.text(0.012, 0.97, 'Coherent regime', fontsize=11, fontweight='bold',
        va='top', ha='left')
ax.text(0.55, 0.97, 'Marginal', fontsize=11, fontweight='bold',
        va='top', ha='center')
ax.text(15, 0.97, 'Effectively\nclassical', fontsize=11, fontweight='bold',
        va='top', ha='center')

# Data points
ax.plot(0.006, np.exp(-0.006), 's', ms=11, color='#333', zorder=5)
ax.annotate('Procopio 2015\n$V=0.994$', xy=(0.006, np.exp(-0.006)),
            xytext=(0.02, 0.82), fontsize=10, ha='left',
            arrowprops=dict(arrowstyle='->', lw=1.2, color='#555'))

ax.plot(0.062, np.exp(-0.062), 's', ms=11, color='#555', zorder=5)
ax.annotate('Jacques 2007\n(closed config.)\n$V\\approx 0.94$',
            xy=(0.062, np.exp(-0.062)), xytext=(0.12, 0.72),
            fontsize=10, ha='left',
            arrowprops=dict(arrowstyle='->', lw=1.2, color='#555'))

# Theory thresholds
ax.axvline(0.25, color='#666', ls='--', lw=1.5)
ax.axvline(np.log(np.sqrt(2)), color='#666', ls='--', lw=1.5)
ax.axvline(1.0, color='#aaa', ls=':', lw=1.5)

# Boxed annotations — spread apart vertically
bbox = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#999', alpha=0.9)
ax.text(np.log(np.sqrt(2)), 0.40, 'Bell/CHSH\ncrossover', fontsize=9.5,
        ha='center', va='center', bbox=bbox)
ax.text(0.25, 0.18, 'Info bound\n(1 bit)', fontsize=9.5,
        ha='center', va='center', bbox=bbox)
ax.text(1.0, 0.62, r'$\Gamma=1$', fontsize=9.5,
        ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2',
        facecolor='white', edgecolor='#bbb', alpha=0.9))

ax.set_xscale('log')
ax.set_xlabel(r'$\Gamma_{\rm loop}$', fontsize=14)
ax.set_ylabel(r'$P_{\rm back}/P_{\rm fwd}$', fontsize=14)
ax.set_xlim(1e-3, 100)
ax.set_ylim(0, 1.05)
ax.legend(loc='upper right', fontsize=11, framealpha=0.9)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_gamma_crossover OK")
