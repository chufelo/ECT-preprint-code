#!/usr/bin/env python3
"""
ECT qubit information–decoherence curve.

Formula (eq:info_decoherence in ECT preprint):
  I(S:E) = 2 h_2((1+exp(-Gamma))/2)  [in nats]
  I_bits = I_nats / ln(2)

Visibility / residual coherence: V = exp(-Gamma)

Operational anchors from ECT paper:
  - Procopio 2015:  V=0.994 -> Gamma~0.006
  - Jacques 2007:   V~0.94  -> Gamma~0.062
  - Bell/CHSH:      Gamma=ln(sqrt(2))~0.347
  - 1-bit info:     Gamma~0.25
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def h2(p):
    """Binary entropy in nats, safe for p near 0 or 1."""
    p = np.clip(p, 1e-15, 1-1e-15)
    return -p*np.log(p) - (1-p)*np.log(1-p)

Gamma = np.logspace(-3, 1.5, 1000)
V = np.exp(-Gamma)
p_plus = (1 + V) / 2
I_nats = 2 * h2(p_plus)
I_bits = I_nats / np.log(2)

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 10,
    'mathtext.fontset': 'cm', 'axes.linewidth': 0.6,
})
fig, ax1 = plt.subplots(figsize=(7, 4.5))

# I(S:E) in bits
ax1.semilogx(Gamma, I_bits, '-', color='0.15', lw=1.8,
             label='$I(S{:}E)$ [bits]')
ax1.set_xlabel(r'Decoherence parameter $\Gamma_{\rm loop}$', fontsize=11)
ax1.set_ylabel(r'Mutual information $I(S{:}E)$ [bits]', fontsize=11)
ax1.set_xlim(1e-3, 30)
ax1.set_ylim(0, 2.15)

# Residual coherence on right axis
ax2 = ax1.twinx()
ax2.semilogx(Gamma, V, '--', color='0.55', lw=1.4,
             label='Coherence $V=e^{-\\Gamma}$')
ax2.set_ylabel(r'Residual coherence $V = e^{-\Gamma}$', fontsize=11, color='0.45')
ax2.set_ylim(0, 1.07)
ax2.tick_params(axis='y', colors='0.45')

# Operational anchors
anchors = [
    (0.006, 'Procopio 2015\n$V=0.994$', 0.008, 1.55),
    (0.062, 'Jacques 2007\n$V\\approx 0.94$', 0.085, 1.25),
    (0.25,  '1-bit info\nthreshold', 0.35, 0.75),
    (0.347, 'Bell/CHSH\ncrossover', 0.12, 0.35),
]
for gam, label, tx, ty in anchors:
    ax1.axvline(gam, color='0.7', ls=':', lw=0.7, zorder=0)
    ax1.annotate(label, xy=(gam, ty), fontsize=7.5, color='0.4',
                 ha='left' if gam < 0.3 else 'right',
                 xytext=(tx, ty))

# Γ=1 marker
ax1.axvline(1.0, color='0.5', ls='--', lw=0.8, zorder=0)
ax1.text(1.15, 1.95, '$\\Gamma=1$', fontsize=8, color='0.5')

# Regime labels
ax1.text(0.003, 0.15, 'Coherent\nregime', fontsize=9, color='0.5',
         ha='center', style='italic')
ax1.text(10, 0.15, 'Effectively\nclassical', fontsize=9, color='0.5',
         ha='center', style='italic')

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, loc='center right', fontsize=9,
           framealpha=0.9)

ax1.grid(True, which='major', ls='-', lw=0.2, color='0.85')
ax1.grid(True, which='minor', ls=':', lw=0.1, color='0.92')

fig.tight_layout()
outdir = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures'
fig.savefig(f'{outdir}/fig_qubit_info_decoherence.pdf', bbox_inches='tight')
fig.savefig(f'{outdir}/fig_qubit_info_decoherence.png', dpi=300, bbox_inches='tight')
plt.close()
print("Qubit info-decoherence plot saved.")
