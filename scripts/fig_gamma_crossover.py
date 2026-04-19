"""
ECT Γ_loop crossover map — log-scale grayscale
v5: log grid ticks, distinct regime shading
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

# Three distinct regime shadings
ax.axvspan(1e-3, 0.15, alpha=0.12, color='#999', zorder=0)   # coherent — darker
ax.axvspan(0.15, 2.0,  alpha=0.05, color='#888', zorder=0)   # marginal — lightest
ax.axvspan(2.0,  100,  alpha=0.10, color='#777', zorder=0)   # classical — medium

# Log-scale grid with minor ticks
ax.set_xscale('log')
ax.grid(True, which='major', axis='both', color='#ccc', lw=0.7, zorder=1)
ax.grid(True, which='minor', axis='x',   color='#e0e0e0', lw=0.4, zorder=1)
ax.grid(True, which='minor', axis='y',   color='#e8e8e8', lw=0.3, zorder=1)
ax.minorticks_on()
ax.set_axisbelow(True)

# Main curve
ax.plot(G, P, 'k-', lw=2.5, zorder=10,
        label=r'$P_{\rm back}/P_{\rm fwd}=e^{-\Gamma_{\rm loop}}$')

# Regime labels at bottom
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
ax.axvline(0.25, color='#666', ls='--', lw=1.5, zorder=8)
ax.axvline(np.log(np.sqrt(2)), color='#666', ls='--', lw=1.5, zorder=8)
ax.axvline(1.0, color='#aaa', ls=':', lw=1.5, zorder=8)

bbox = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#888',
            alpha=0.92, lw=1.2)
ax.text(np.log(np.sqrt(2)), 0.40, 'Bell/CHSH\ncrossover', fontsize=10,
        ha='center', va='center', fontweight='bold', bbox=bbox, zorder=15)
ax.text(0.25, 0.20, 'Info bound\n(1 bit)', fontsize=10,
        ha='center', va='center', fontweight='bold', bbox=bbox, zorder=15)
ax.text(1.0, 0.62, r'$\Gamma=1$', fontsize=10,
        ha='center', va='center', zorder=15,
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  edgecolor='#bbb', alpha=0.9, lw=1.0))

ax.set_xlabel(r'$\Gamma_{\rm loop}$', fontsize=14)
ax.set_ylabel(r'$P_{\rm back}/P_{\rm fwd}$', fontsize=14)
ax.set_xlim(1e-3, 100)
ax.set_ylim(0, 1.05)
ax.legend(loc='upper right', fontsize=11, framealpha=0.95)
ax.tick_params(which='both', direction='in', top=True, right=True)

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_gamma_crossover.png'), dpi=300, bbox_inches='tight')
plt.close()
print("OK")
