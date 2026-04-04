"""BH shell schematic — straight labels in zones, proper LaTeX."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np
import os

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'mathtext.fontset': 'cm',
    'text.usetex': False,
})

fig, ax = plt.subplots(1, 1, figsize=(9.5, 5.8))
ax.set_xlim(-3.8, 6.8)
ax.set_ylim(-3.8, 3.5)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')

cx, cy = 0, 0
r_ext, r_shell, r_int = 2.8, 2.0, 1.1

# Three concentric circles with graduated fills
c1 = Circle((cx, cy), r_ext, fc='#e8e8e8', ec='#555', lw=1.5, zorder=1)
c2 = Circle((cx, cy), r_shell, fc='#cccccc', ec='#555', lw=1.5, ls=(0,(6,4)), zorder=2)
c3 = Circle((cx, cy), r_int, fc='#a0a0a0', ec='#555', lw=1.5, zorder=3)
ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)

# === Zone labels (straight, positioned in each annular band) ===

# H_ext — in the exterior annulus (between r_ext and top edge)
ax.text(cx, r_ext - 0.35, r'$\mathcal{H}_{\rm ext}$: asymptotically accessible exterior',
        fontsize=10, ha='center', va='center', zorder=10)

# Critical shell boundary — along the dashed circle
ax.text(cx, r_shell + 0.18, '— critical shell boundary —',
        fontsize=8.5, ha='center', va='center', color='#444', zorder=10)

# H_shell — in the shell annulus
ax.text(cx, (r_shell + r_int)/2 + 0.1,
        r'$\mathcal{H}_{\rm shell}$: ordered-phase shell',
        fontsize=10, ha='center', va='center', zorder=10)

# H_int — centered in inner circle
ax.text(cx, cy + 0.25, r'$\mathcal{H}_{\rm int}$:',
        fontsize=11, ha='center', va='center', zorder=10)
ax.text(cx, cy - 0.15, 'inaccessible', fontsize=10, ha='center', va='center', zorder=10)
ax.text(cx, cy - 0.50, 'strong-field sector', fontsize=10, ha='center', va='center', zorder=10)

# === Right-side annotations ===

# Arrow 1: strong-field coupling → shell zone (upper)
ax.annotate('', xy=(1.55, 1.55), xytext=(3.8, 2.2),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.3), zorder=8)
ax.text(4.0, 2.5, 'Strong-field coupling of', fontsize=10, color='#333')
ax.text(4.0, 2.1, 'coherent & topological modes', fontsize=10, color='#333')

# Arrow 2: observer traces → interior (lower)
ax.annotate('', xy=(1.0, -0.5), xytext=(3.8, -1.0),
    arrowprops=dict(arrowstyle='->', color='#444', lw=1.3), zorder=8)
ax.text(4.0, -0.7, 'Observer traces over', fontsize=10, color='#333')
ax.text(4.0, -1.1, 'shell + interior sectors', fontsize=10, color='#333')

# === Formula box ===
box = FancyBboxPatch((3.0, -3.2), 3.5, 0.7, boxstyle='round,pad=0.1',
                      fc='white', ec='#555', lw=1.2, zorder=8)
ax.add_patch(box)
ax.text(4.75, -2.85,
        r'$\rho_{\rm ext} = \mathrm{Tr}_{\rm sh,int}\,|\Psi\rangle\langle\Psi|$',
        fontsize=13, ha='center', va='center', zorder=10)

# Dashed arrow from bottom of circles to formula box
ax.annotate('', xy=(3.1, -2.85), xytext=(1.2, -2.4),
    arrowprops=dict(arrowstyle='->', color='#999', lw=1.0, ls='--'), zorder=7)

outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(outdir, 'fig_bh_shell.pdf'), bbox_inches='tight', dpi=300)
fig.savefig(os.path.join(outdir, 'fig_bh_shell.png'), bbox_inches='tight', dpi=300)
plt.close()
print("fig_bh_shell OK")
