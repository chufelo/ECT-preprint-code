"""
ECT Γ_loop crossover map — regenerated with GPT corrections:
  - Regime names: Coherent / Crossover / Effective classical
  - Jacques label: "Jacques 2007 (closed config.)"
  - Bell and info annotations spread apart
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'mathtext.fontset': 'cm',
})

fig, ax = plt.subplots(figsize=(12, 5))

# Gamma range
G = np.linspace(0.001, 4.0, 500)
P = np.exp(-G)

ax.plot(G, P, 'k-', lw=2.2, label=r'$P_{\rm back}/P_{\rm fwd}=e^{-\Gamma_{\rm loop}}$')

# Experimental anchors (filled markers)
ax.plot(0.006, np.exp(-0.006), 'o', ms=10, color='#333', zorder=5)
ax.annotate('Procopio 2015\n' + r'$V\!=\!0.994$, $\Gamma\!=\!0.006$',
            xy=(0.006, np.exp(-0.006)), xytext=(0.08, 0.82),
            fontsize=9.5, ha='left',
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2))

ax.plot(0.062, np.exp(-0.062), 's', ms=10, color='#555', zorder=5)
ax.annotate('Jacques 2007\n(closed config.)\n' + r'$V\!\approx\!0.94$, $\Gamma\!\approx\!0.062$',
            xy=(0.062, np.exp(-0.062)), xytext=(0.22, 0.65),
            fontsize=9.5, ha='left',
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2))

# Theory thresholds (dashed vertical lines)
# Qubit 1-bit bound
ax.axvline(0.25, color='#888', ls='--', lw=1.2)
ax.annotate(r'1-bit bound' + '\n' + r'$\Gamma\!\approx\!0.25$',
            xy=(0.25, 0.25), xytext=(0.06, 0.22),
            fontsize=9, ha='left', color='#666',
            arrowprops=dict(arrowstyle='->', color='#888', lw=1.0))

# Bell/CHSH crossover
ax.axvline(np.log(np.sqrt(2)), color='#888', ls='--', lw=1.2)
ax.annotate(r'Bell/CHSH' + '\n' + r'$\Gamma\!=\!\ln\sqrt{2}\!\approx\!0.35$',
            xy=(np.log(np.sqrt(2)), 0.55), xytext=(0.55, 0.52),
            fontsize=9, ha='left', color='#666',
            arrowprops=dict(arrowstyle='->', color='#888', lw=1.0))

# Γ=1 dotted line
ax.axvline(1.0, color='#aaa', ls=':', lw=1.5)
ax.text(1.05, 0.92, r'$\Gamma_{\rm loop}=1$', fontsize=9, color='#999', va='top')

# Regime labels (updated per GPT)
ax.fill_betweenx([0, 1.05], 0, 0.15, alpha=0.06, color='blue')
ax.fill_betweenx([0, 1.05], 0.15, 1.5, alpha=0.04, color='orange')
ax.fill_betweenx([0, 1.05], 1.5, 4.0, alpha=0.06, color='red')

ax.text(0.04, 1.02, 'Coherent\nregime', fontsize=10, va='top', ha='left',
        fontstyle='italic', color='#336')
ax.text(0.7, 1.02, 'Crossover\nregime', fontsize=10, va='top', ha='center',
        fontstyle='italic', color='#663')
ax.text(2.7, 1.02, 'Effective\nclassical regime', fontsize=10, va='top', ha='center',
        fontstyle='italic', color='#633')

ax.set_xlabel(r'$\Gamma_{\rm loop}$', fontsize=13)
ax.set_ylabel(r'$P_{\rm back}/P_{\rm fwd}$', fontsize=13)
ax.set_xlim(0, 4.0)
ax.set_ylim(0, 1.08)
ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
ax.set_title('')

fig.tight_layout()

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out_dir, 'fig_gamma_crossover.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out_dir, 'fig_gamma_crossover.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_gamma_crossover generated")
