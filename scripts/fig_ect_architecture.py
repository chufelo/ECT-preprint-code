"""
ECT Architecture map — larger fonts, arrows touching box edges only
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 13, 'mathtext.fontset': 'cm',
})

FW, FH = 12, 13
fig = plt.figure(figsize=(FW, FH))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis('off')

nodes = {}

def box(key, x, y, w, h, lines, fill='#f0f0f0', edge='#444', fs=13):
    nodes[key] = (x, y, w, h)
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.15', facecolor=fill, edgecolor=edge,
        linewidth=1.8, zorder=3))
    ax.text(x, y, '\n'.join(lines), ha='center', va='center',
            fontsize=fs, linespacing=1.25, zorder=4)

def arr(src, dst, dashed=False):
    x0, y0, w0, h0 = nodes[src]
    x1, y1, w1, h1 = nodes[dst]
    # Arrow from bottom of src to top of dst
    ys = y0 - h0/2
    yd = y1 + h1/2
    ls = (0,(4,2.5)) if dashed else '-'
    c = '#999' if dashed else '#333'
    ax.annotate('', xy=(x1, yd), xytext=(x0, ys),
        arrowprops=dict(arrowstyle='-|>', color=c, lw=2.0,
                        mutation_scale=18, linestyle=ls), zorder=5)

def arr_xy(x0, y0, x1, y1, dashed=False):
    ls = (0,(4,2.5)) if dashed else '-'
    c = '#999' if dashed else '#333'
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(arrowstyle='-|>', color=c, lw=2.0,
                        mutation_scale=18, linestyle=ls), zorder=5)

# Row positions
y0 = 12.0; y1 = 10.0; y2 = 8.0; y3 = 5.8; y4 = 3.5; y5 = 1.3

# === Top: Φ-medium ===
box('phi', 6, y0, 5.5, 1.0,
    [r'$\Phi$-medium on $\mathcal{M}^4$', 'P1–P6, DP'],
    fill='#c0c0c0', fs=14)

# === SSB ===
box('ssb', 6, y1, 6.5, 1.3,
    [r'$O(4)\to O(3)$ SSB',
     r'Ordered branch: $\langle\partial_A\Phi\rangle = u_0\,\delta_{Aw}$',
     r'Lorentzian window: $\alpha > \beta$',
     r'Benchmark realisation: $\alpha = 2\beta$'],
    fill='#d0d0d0', fs=12)
arr('phi', 'ssb')

# === Ordered-branch action ===
box('ord', 6, y2, 5.5, 1.0,
    [r'$S_{\rm ord}[u, n]$',
     r'$K^{AB}=\beta\,\delta^{AB}-\alpha\,n^A n^B$'],
    fill='#ddd', fs=12)
arr('ssb', 'ord')

# === Two branches ===
box('geo', 3.0, y3, 4.2, 1.2,
    ['Geometric branch',
     '(Macroscopic Physics, Part II)',
     'Long-wavelength amplitude/orientation'],
    fill='#e5e5e5', fs=11)

box('coh', 9.0, y3, 4.2, 1.2,
    ['Coherent branch',
     '(Quantum Sector, Part III)',
     'Short-wavelength phase/winding'],
    fill='#e5e5e5', fs=11)

# Arrows from ordered action to branches (from bottom corners)
arr_xy(4.5, y2 - 0.5, 3.0, y3 + 0.6)
arr_xy(7.5, y2 - 0.5, 9.0, y3 + 0.6)

# === Sub-blocks ===
box('geo_sub', 3.0, y4, 4.5, 1.2,
    [r'Einstein sector, $G_N$ matching',
     r'Cosmology, galactic $\phi$-branch',
     'BTFR, RAR, cluster lensing'],
    fill='#efefef', fs=11)
arr('geo', 'geo_sub')

box('coh_sub', 9.0, y4, 4.5, 1.2,
    [r'$S_0$, Hilbert bridge, decoherence',
     'PES, Born route, entanglement',
     'Vacuum response, BH information'],
    fill='#efefef', fs=11)
arr('coh', 'coh_sub')

# Back-reaction
ax.annotate('', xy=(4.2, y4), xytext=(7.8, y4),
    arrowprops=dict(arrowstyle='<|-|>', color='#aaa', lw=1.3,
                    mutation_scale=14, linestyle=(0,(3,2))))
ax.text(6.0, y4 + 0.25, 'back-reaction (single condensate)',
        fontsize=9.5, ha='center', color='#888', fontstyle='italic')

# === Predictions ===
box('pred', 6, y5, 7.0, 1.2,
    ['Predictions, falsifiers, open problems',
     r'BTFR slope 4, $g^\dagger\!\approx\! cH_0/(2\pi)$, LIV, 5th force',
     'Casimir 3/2, Unruh, decoherence anchors'],
    fill='#d5d5d5', fs=11)
arr_xy(3.0, y4 - 0.6, 4.5, y5 + 0.6)
arr_xy(9.0, y4 - 0.6, 7.5, y5 + 0.6)

fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '..', 'figures', 'fig_ect_architecture.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '..', 'figures', 'fig_ect_architecture.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_ect_architecture OK")
