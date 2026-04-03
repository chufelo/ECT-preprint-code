"""F6: PES Venn diagram — v2: larger fonts, labels inside zones"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 13, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(8, 8))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.02, 0.04, 0.96, 0.92])
ax.set_xlim(-4.2, 4.2); ax.set_ylim(-4, 4.2); ax.axis('off')
ax.set_aspect('equal')

r = 2.4
cx = [0, -1.35, 1.35]
cy = [1.2, -0.65, -0.65]
fills = ['#ccc', '#bbb', '#aaa']

for i in range(3):
    ax.add_patch(Circle((cx[i], cy[i]), r, fc=fills[i], ec='#444', lw=1.8, alpha=0.18, zorder=2))
    ax.add_patch(Circle((cx[i], cy[i]), r, fc='none', ec='#444', lw=1.8, zorder=4))

# Labels INSIDE circles (upper zone of each)
ax.text(0, 3.0, 'Extremal\n(stationary action)', ha='center', va='center',
        fontsize=14, fontweight='bold', color='#333')
ax.text(-2.8, -2.2, 'Decoherence-\nresistant\n' + r'($\Gamma_{\rm loop}\ll 1$)',
        ha='center', va='center', fontsize=13, fontweight='bold', color='#333')
ax.text(2.8, -2.2, 'Phase-compact\n(well-defined\nwinding number)',
        ha='center', va='center', fontsize=13, fontweight='bold', color='#333')

# Pairwise labels
ax.text(-0.7, 1.7, 'smooth\nextremal', ha='center', va='center', fontsize=11, color='#555', fontstyle='italic')
ax.text(0.7, 1.7, 'compact\nextremal', ha='center', va='center', fontsize=11, color='#555', fontstyle='italic')
ax.text(0, -1.6, 'stable\ncoherent', ha='center', va='center', fontsize=11, color='#555', fontstyle='italic')

# Center: PES
bbox = dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#333', linewidth=2.2, alpha=0.95)
ax.text(0, 0.0, 'PES\npersistent\nconfiguration', ha='center', va='center',
        fontsize=14, fontweight='bold', color='#222', bbox=bbox, zorder=10)

# Bottom annotation
ax.text(0, -3.7, 'Observable quantum states = configurations satisfying\nall three conditions simultaneously',
        ha='center', va='center', fontsize=12, color='#444', fontstyle='italic')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_pes_diagram.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_pes_diagram.png'), dpi=300, bbox_inches='tight')
plt.close(); print("OK")
