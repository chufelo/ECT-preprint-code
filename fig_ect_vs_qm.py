"""F4: ECT vs QM — v2: compact, no inter-row arrows, larger fonts"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 12, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(12, 6.5))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
ax.set_xlim(0, 12); ax.set_ylim(0, 6.5); ax.axis('off')

def box(x, y, w, h, lines, fill='#eee', fs=11.5):
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.1', facecolor=fill, edgecolor='#444', linewidth=1.4, zorder=3))
    ax.text(x, y, '\n'.join(lines), ha='center', va='center', fontsize=fs,
            linespacing=1.2, zorder=4)

# Headers
box(3, 6.0, 5.0, 0.65, ['Standard Quantum Mechanics'], fill='#c0c0c0', fs=14)
box(9, 6.0, 5.0, 0.65, ['Euclidean Condensate Theory'], fill='#c0c0c0', fs=14)

# Row labels (left margin)
rows = [
    ('Problem type', 5.0),
    ('Equation', 4.0),
    ('Probability', 3.0),
    ('Time', 2.0),
    ('Measurement', 1.0),
]

qm_boxes = [
    ['Initial-value (Cauchy) problem', r'$\psi(\mathbf{x}, t_0)$ given → evolve forward'],
    [r'$i\hbar\,\partial_t\psi = H\psi$', 'Schrödinger / Dirac equation'],
    [r'$|\psi|^2$ = Born rule', '(fundamental axiom)'],
    ['Time: fundamental coordinate', 'Lorentzian spacetime a priori'],
    ['Measurement: extra postulate', 'Collapse / decoherence'],
]

ect_boxes = [
    ['Boundary-value (elliptic) problem', r'$\Phi(X)$ on entire $\mathcal{M}^4$'],
    [r'$\delta^{AB}\partial_A\partial_B\Phi - V^\prime(\Phi) = 0$', 'Euclidean condensate equation'],
    [r'$|\psi|^2$ from coarse-graining', '(emergent, not axiom)'],
    [r'Time: emergent from $O(4)\to O(3)$', 'SSB selects $w$-direction'],
    [r'Measurement: E$\to$L transition', 'Under environmental locking'],
]

for i, (label, y) in enumerate(rows):
    box(3, y, 5.0, 0.72, qm_boxes[i], fill='#e5e5e5')
    box(9, y, 5.0, 0.72, ect_boxes[i], fill='#e0e0e0')

# Vertical divider
ax.plot([6, 6], [0.5, 5.5], color='#bbb', lw=1, ls='--')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_ect_vs_qm.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_ect_vs_qm.png'), dpi=300, bbox_inches='tight')
plt.close(); print("OK")
