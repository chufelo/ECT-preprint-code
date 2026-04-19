"""
ECT Equation Hierarchy — compact boxes, arrows touching edges only
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 12, 'mathtext.fontset': 'cm',
})

fig, ax = plt.subplots(figsize=(7, 9))
ax.set_xlim(0, 7); ax.set_ylim(0, 9); ax.axis('off')
fig.patch.set_facecolor('white')

nodes = {}

def box(key, x, y, w, h, lines, sub, fill='#f0f0f0', edge='#333', fs=11.5):
    nodes[key] = (x, y, w, h)
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.12', facecolor=fill, edgecolor=edge,
        linewidth=1.6, zorder=3))
    ax.text(x, y + 0.08, '\n'.join(lines), ha='center', va='center',
            fontsize=fs, zorder=4, linespacing=1.2)
    ax.text(x, y - h/2 + 0.12, sub, ha='center', va='bottom',
            fontsize=8.5, color='#777', fontstyle='italic', zorder=4)

def arr(src, dst, label):
    x0, y0, w0, h0 = nodes[src]
    x1, y1, w1, h1 = nodes[dst]
    ys = y0 - h0/2   # bottom of source
    yd = y1 + h1/2   # top of dest
    mid = (ys + yd) / 2
    ax.annotate('', xy=(x1, yd), xytext=(x0, ys),
        arrowprops=dict(arrowstyle='-|>', color='#444', lw=1.8,
                        mutation_scale=16))
    ax.text(x0 + 0.15, mid, label, fontsize=9, ha='left', va='center',
            color='#666', fontstyle='italic')

# Level 0
box('L0', 3.5, 8.2, 5.5, 0.9,
    [r'$\delta^{AB}\partial_A\partial_B\Phi - V\prime(\Phi) = 0$',
     'Euclidean condensate equation'],
    'Level 0: fundamental', fill='#d5d5d5')

# Level 1
box('L1', 3.5, 6.1, 5.5, 1.05,
    [r'$K^{AB}\partial_A\partial_B\chi + m_\sigma^2\chi = 0$',
     r'$K^{AB}=\beta\,\delta^{AB} - \alpha\,n^A n^B$',
     'Ordered-branch field equation'],
    'Level 1: broken-phase EFT', fill='#e0e0e0')

arr('L0', 'L1', r'$O(4)\!\to\!O(3)$ SSB')

# Level 2
box('L2', 3.5, 4.0, 5.5, 0.9,
    [r'$\partial_t^2\varphi - c_*^2\nabla^2\varphi + M^2\varphi = 0$',
     r'Klein–Gordon equation'],
    'Level 2: Lorentzian branch', fill='#eaeaea')

arr('L1', 'L2', r'Real parametrisation $t\!=\!w/c_*$')

# Level 3
box('L3', 3.5, 1.9, 5.5, 0.9,
    [r'$iS_0\,\partial_t\psi = -\frac{S_0^2}{2m}\nabla^2\psi + V\psi$',
     r'Schrödinger equation ($S_0\!\to\!\hbar$)'],
    'Level 3: NR coherent branch', fill='#f2f2f2')

arr('L2', 'L3', 'Nonrelativistic limit')

fig.tight_layout()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_equation_hierarchy.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_equation_hierarchy.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_equation_hierarchy OK")
