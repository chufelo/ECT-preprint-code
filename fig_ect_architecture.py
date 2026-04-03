"""
ECT Architecture map — with "α>β (Lorentzian window) / benchmark: α=2β"
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'mathtext.fontset': 'cm',
})

FW, FH = 11, 11
fig = plt.figure(figsize=(FW, FH))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis('off')

def box(x, y, w, h, lines, fill='#f0f0f0', edge='#444', fs=11):
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.12', facecolor=fill, edgecolor=edge,
        linewidth=1.6, zorder=3))
    ax.text(x, y, '\n'.join(lines), ha='center', va='center',
            fontsize=fs, linespacing=1.25, zorder=4)

def arr(x0, y0, x1, y1, label='', dashed=False):
    ls = (0,(4,2.5)) if dashed else '-'
    c = '#999' if dashed else '#333'
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='-|>', color=c, lw=1.8,
                        mutation_scale=16, linestyle=ls), zorder=5)
    if label:
        mx, my = (x0+x1)/2, (y0+y1)/2
        ax.text(mx+0.15, my, label, fontsize=8.5, ha='left', va='center',
                color='#666', fontstyle='italic')

# === Top: Φ-medium ===
box(5.5, 10.2, 5.0, 0.9,
    [r'$\Phi$-medium on $\mathcal{M}^4$',
     r'P1–P6, DP'],
    fill='#c8c8c8', fs=12)

# === SSB ===
box(5.5, 8.5, 5.5, 1.1,
    [r'$O(4)\to O(3)$ SSB',
     r'Ordered branch: $\langle\partial_A\Phi\rangle = u_0\,\delta_{Aw}$',
     r'Lorentzian window: $\alpha>\beta$',
     r'Benchmark realisation: $\alpha=2\beta$'],
    fill='#d8d8d8', fs=10.5)
arr(5.5, 9.75, 5.5, 9.1)

# === Ordered-branch action ===
box(5.5, 6.8, 4.5, 0.8,
    [r'$S_{\rm ord}[u, n]$',
     r'$K^{AB}=\beta\,\delta^{AB}-\alpha\,n^A n^B$'],
    fill='#e0e0e0', fs=10.5)
arr(5.5, 7.9, 5.5, 7.25)

# === Two branches ===
# Geometric branch (left)
box(2.8, 5.0, 3.8, 1.0,
    [r'\textbf{Geometric branch}',
     r'(Macroscopic Physics, Part II)',
     r'Long-wavelength amplitude/orientation'],
    fill='#e8e8e8', fs=10)
arr(4.3, 6.4, 3.2, 5.55, dashed=False)

# Coherent branch (right)
box(8.2, 5.0, 3.8, 1.0,
    [r'\textbf{Coherent branch}',
     r'(Quantum Sector, Part III)',
     r'Short-wavelength phase/winding'],
    fill='#e8e8e8', fs=10)
arr(6.7, 6.4, 7.8, 5.55, dashed=False)

# === Geometric sub-blocks ===
box(2.8, 3.3, 3.5, 1.0,
    [r'Einstein sector, $G_N$ matching',
     r'Cosmology, galactic $\phi$-branch',
     r'BTFR, RAR, cluster lensing'],
    fill='#f0f0f0', fs=9.5)
arr(2.8, 4.45, 2.8, 3.85)

# === Coherent sub-blocks ===
box(8.2, 3.3, 3.5, 1.0,
    [r'$S_0$, Hilbert bridge, decoherence',
     r'PES, Born route, entanglement',
     r'Vacuum response, BH information'],
    fill='#f0f0f0', fs=9.5)
arr(8.2, 4.45, 8.2, 3.85)

# === Back-reaction arrow ===
ax.annotate('', xy=(3.8, 3.3), xytext=(7.2, 3.3),
    arrowprops=dict(arrowstyle='<|-|>', color='#999', lw=1.4,
                    mutation_scale=14, linestyle=(0,(3,2))))
ax.text(5.5, 3.55, 'back-reaction\n(single condensate)', fontsize=8,
        ha='center', va='bottom', color='#888', fontstyle='italic')

# === Predictions ===
box(5.5, 1.5, 6.0, 1.0,
    [r'Predictions, falsifiers, open problems',
     r'BTFR slope 4, $g^\dagger\approx cH_0/(2\pi)$, LIV, 5th force',
     r'Casimir $3/2$, Unruh, decoherence anchors'],
    fill='#ddd', fs=9.5)
arr(2.8, 2.75, 4.5, 2.05)
arr(8.2, 2.75, 6.5, 2.05)

fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '..', 'figures', 'fig_ect_architecture.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '..', 'figures', 'fig_ect_architecture.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_ect_architecture generated")
