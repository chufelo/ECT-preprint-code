"""
ECT Equation Hierarchy — 4-level figure with K^{AB}=βδ^{AB}−αn^An^B
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 13,
    'mathtext.fontset': 'cm',
})

fig, ax = plt.subplots(figsize=(8, 11))
ax.set_xlim(0, 8); ax.set_ylim(0, 11); ax.axis('off')
fig.patch.set_facecolor('white')

def box(x, y, w, h, text, level_text, fill='#f0f0f0', edge='#333'):
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.15', facecolor=fill, edgecolor=edge,
        linewidth=1.8, zorder=3))
    ax.text(x, y+0.15, text, ha='center', va='center', fontsize=12,
            zorder=4, linespacing=1.3)
    ax.text(x, y-h/2+0.18, level_text, ha='center', va='bottom',
            fontsize=9, color='#666', fontstyle='italic', zorder=4)

def arrow(x, y1, y2, label):
    ymid = (y1+y2)/2
    ax.annotate('', xy=(x, y2+0.55), xytext=(x, y1-0.55),
        arrowprops=dict(arrowstyle='-|>', color='#444', lw=2.0,
                        mutation_scale=18))
    ax.text(x+0.15, ymid, label, fontsize=9.5, ha='left', va='center',
            color='#555', fontstyle='italic')

# Level 0: Euclidean condensate equation
box(4, 9.8, 6.5, 1.3,
    r'$\delta^{AB}\partial_A\partial_B\Phi - V\prime(\Phi) = 0$'
    + '\n' + r'Euclidean condensate equation',
    'Level 0: fundamental', fill='#d8d8d8')

# Arrow: SSB
arrow(4, 9.8, 7.6, r'$O(4)\!\to\!O(3)$ SSB')

# Level 1: Ordered-branch equation
box(4, 7.0, 6.5, 1.5,
    r'$K^{AB}\partial_A\partial_B\chi + m_\sigma^2\chi = 0$'
    + '\n' + r'$K^{AB}=\beta\,\delta^{AB}-\alpha\,n^A n^B$'
    + '\n' + r'Ordered-branch field equation',
    'Level 1: broken-phase EFT', fill='#e4e4e4')

# Arrow: real parametrisation
arrow(4, 7.0, 4.8, r'Real parametrisation $t=w/c_*$')

# Level 2: Klein-Gordon
box(4, 4.2, 6.5, 1.3,
    r'$\partial_t^2\varphi - c_*^2\nabla^2\varphi + M^2\varphi = 0$'
    + '\n' + r'Klein–Gordon equation',
    'Level 2: Lorentzian branch', fill='#efefef')

# Arrow: NR limit
arrow(4, 4.2, 2.0, r'Nonrelativistic limit')

# Level 3: Schrödinger
box(4, 1.4, 6.5, 1.3,
    r'$i S_0\,\partial_t\psi = -\frac{S_0^2}{2m}\nabla^2\psi + V\psi$'
    + '\n' + r'Schrödinger equation ($S_0\to\hbar$)',
    'Level 3: NR coherent branch', fill='#f8f8f8')

fig.tight_layout()
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out_dir, 'fig_equation_hierarchy.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out_dir, 'fig_equation_hierarchy.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_equation_hierarchy generated")
