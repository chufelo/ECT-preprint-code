"""BH shell schematic with text along arcs, proper mathcal H, subscripts."""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np
import os

fig, ax = plt.subplots(1, 1, figsize=(9, 6.5))
ax.set_xlim(-3.5, 6.5)
ax.set_ylim(-4.2, 3.5)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')

cx, cy = 0, 0
r_ext, r_shell, r_int = 2.8, 2.0, 1.1

# Draw circles
c1 = Circle((cx, cy), r_ext, fc='#ededed', ec='#666', lw=1.5, zorder=1)
c2 = Circle((cx, cy), r_shell, fc='#d0d0d0', ec='#666', lw=1.5, ls='--', zorder=2)
c3 = Circle((cx, cy), r_int, fc='#aaaaaa', ec='#666', lw=1.5, zorder=3)
ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)

# === Curved text function ===
def text_along_arc(ax, text, cx, cy, radius, start_angle, end_angle, fontsize=10, style='normal', color='#222', weight='normal'):
    """Place text along an arc. Angles in degrees, 0=top, clockwise."""
    n = len(text)
    angles = np.linspace(np.radians(start_angle), np.radians(end_angle), n)
    for i, ch in enumerate(text):
        a = angles[i]
        x = cx + radius * np.sin(a)
        y = cy + radius * np.cos(a)
        rotation = -np.degrees(a)
        ax.text(x, y, ch, fontsize=fontsize, ha='center', va='center',
                rotation=rotation, fontstyle=style, color=color, fontweight=weight,
                fontfamily='serif', zorder=10)

# === Arc labels ===
# H_ext label along outer arc (top half)
text_along_arc(ax, r"$\mathcal{H}$", cx, cy, (r_ext+r_shell)/2 + 0.25, -42, -38, fontsize=13, style='italic')
text_along_arc(ax, "ext", cx, cy, (r_ext+r_shell)/2 + 0.15, -35, -27, fontsize=8)
text_along_arc(ax, ": asymptotically accessible exterior", cx, cy, (r_ext+r_shell)/2 + 0.25, -22, 62, fontsize=10)

# Shell boundary label along dashed arc
text_along_arc(ax, "--- critical shell boundary ---", cx, cy, r_shell + 0.15, -38, 38, fontsize=8, color='#555')

# H_shell label along shell region
text_along_arc(ax, r"$\mathcal{H}$", cx, cy, (r_shell+r_int)/2 + 0.15, -32, -28, fontsize=12, style='italic')
text_along_arc(ax, "shell", cx, cy, (r_shell+r_int)/2 + 0.05, -24, -10, fontsize=8)
text_along_arc(ax, ": ordered-phase shell", cx, cy, (r_shell+r_int)/2 + 0.15, -5, 38, fontsize=10)

# H_int label — centered in inner circle (too small for arc)
ax.text(cx, cy + 0.25, r'$\mathcal{H}_{\rm int}$ :', fontsize=12, ha='center', va='center',
        fontstyle='italic', zorder=10, fontfamily='serif')
ax.text(cx, cy - 0.1, 'inaccessible', fontsize=10, ha='center', va='center', zorder=10, fontfamily='serif')
ax.text(cx, cy - 0.4, 'strong-field sector', fontsize=10, ha='center', va='center', zorder=10, fontfamily='serif')

# === Right-side annotations ===
# Arrow 1: strong-field coupling → shell zone
ax.annotate('', xy=(1.6, 1.2), xytext=(3.5, 1.8),
    arrowprops=dict(arrowstyle='->', color='#555', lw=1.3), zorder=8)
ax.text(3.7, 2.1, 'Strong-field coupling of', fontsize=10, color='#333', fontfamily='serif')
ax.text(3.7, 1.7, 'coherent & topological modes', fontsize=10, color='#333', fontfamily='serif')

# Arrow 2: observer traces → interior
ax.annotate('', xy=(1.0, -0.6), xytext=(3.5, -1.2),
    arrowprops=dict(arrowstyle='->', color='#555', lw=1.3), zorder=8)
ax.text(3.7, -0.9, 'Observer traces over', fontsize=10, color='#333', fontfamily='serif')
ax.text(3.7, -1.3, 'shell + interior sectors', fontsize=10, color='#333', fontfamily='serif')

# === Formula box ===
box = FancyBboxPatch((2.5, -3.5), 3.8, 0.7, boxstyle='round,pad=0.1',
                      fc='white', ec='#666', lw=1.2, zorder=8)
ax.add_patch(box)
ax.text(4.4, -3.15, r'$\rho_{\rm ext} = {\rm Tr}_{\rm sh,int}\,|\Psi\rangle\langle\Psi|$',
        fontsize=13, ha='center', va='center', zorder=10, fontfamily='serif')

# Dashed arrow from circle to formula box
ax.annotate('', xy=(2.8, -3.15), xytext=(1.5, -2.5),
    arrowprops=dict(arrowstyle='->', color='#999', lw=1.0, ls='--'), zorder=7)

outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(outdir, 'fig_bh_shell.pdf'), bbox_inches='tight', dpi=300)
fig.savefig(os.path.join(outdir, 'fig_bh_shell.png'), bbox_inches='tight', dpi=300)
plt.close()
print("fig_bh_shell OK")
