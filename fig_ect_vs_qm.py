"""
F4: ECT vs Standard QM — Cauchy vs Boundary-Value Problem
Two-column comparison diagram
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 11, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(12, 8))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis('off')

def box(x, y, w, h, lines, fill='#f0f0f0', edge='#444', fs=10.5, bold_first=False):
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.12', facecolor=fill, edgecolor=edge, linewidth=1.5, zorder=3))
    txt = '\n'.join(lines)
    ax.text(x, y, txt, ha='center', va='center', fontsize=fs, linespacing=1.25, zorder=4)

def arr(x0, y0, x1, y1):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='-|>', color='#444', lw=1.6, mutation_scale=15))

# === Headers ===
box(3, 7.5, 4.8, 0.7, ['Standard Quantum Mechanics'], fill='#c0c0c0', fs=13)
box(9, 7.5, 4.8, 0.7, ['Euclidean Condensate Theory'], fill='#c0c0c0', fs=13)

# === Row 1: Problem type ===
box(3, 6.3, 4.8, 0.8, ['Initial-value (Cauchy) problem',
    r'$\psi(\mathbf{x}, t_0)$ given $\;\to\;$ evolve forward'], fill='#e8e8e8')
box(9, 6.3, 4.8, 0.8, ['Boundary-value (elliptic) problem',
    r'$\Phi(X)$ on entire $\mathcal{M}^4$'], fill='#e0e0e0')

# === Row 2: Equation ===
box(3, 5.0, 4.8, 0.8, [r'$i\hbar\,\partial_t\psi = H\psi$',
    'Schrödinger / Dirac equation'], fill='#efefef')
box(9, 5.0, 4.8, 0.8, [r'$\delta^{AB}\partial_A\partial_B\Phi - V^\prime(\Phi) = 0$',
    'Euclidean condensate equation'], fill='#efefef')

# === Row 3: Probability ===
box(3, 3.7, 4.8, 0.8, ['Probability: fundamental axiom',
    r'$|\psi|^2$ = Born rule (postulated)'], fill='#e8e8e8')
box(9, 3.7, 4.8, 0.8, ['Probability: emergent',
    r'$|\psi|^2$ from coarse-graining over', 
    'untracked condensate modes'], fill='#e0e0e0')

# === Row 4: Time ===
box(3, 2.4, 4.8, 0.8, ['Time: fundamental coordinate',
    'Lorentzian spacetime given a priori'], fill='#efefef')
box(9, 2.4, 4.8, 0.8, ['Time: emergent from SSB',
    r'$O(4)\to O(3)$ selects $w$-direction'], fill='#efefef')

# === Row 5: Measurement ===
box(3, 1.1, 4.8, 0.8, ['Measurement: extra postulate',
    'wavefunction collapse / decoherence'], fill='#e8e8e8')
box(9, 1.1, 4.8, 0.8, ['Measurement: structural',
    r'E$\to$L transition under env. locking',
    '(no extra postulate)'], fill='#e0e0e0')

# Arrows
for y in [6.3, 5.0, 3.7, 2.4, 1.1]:
    arr(3, y-0.4, 3, y-0.72)
    arr(9, y-0.4, 9, y-0.72)

# Vertical divider
ax.plot([6, 6], [0.4, 7.1], color='#bbb', lw=1, ls='--')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_ect_vs_qm.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_ect_vs_qm.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_ect_vs_qm OK")
