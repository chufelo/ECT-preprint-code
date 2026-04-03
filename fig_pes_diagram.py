"""
F6: Principle of Euclidean Stationarity (PES) — Venn-style diagram
Three conditions whose intersection defines persistent configurations
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 11, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(8, 7.5))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
ax.set_xlim(-4, 4); ax.set_ylim(-3.5, 4); ax.axis('off')
ax.set_aspect('equal')

# Three overlapping circles
r = 2.3
cx = [0, -1.3, 1.3]
cy = [1.2, -0.6, -0.6]
colors = ['#bbb', '#aaa', '#999']
labels_out = [
    ('Extremal\n(stationary action)', 0, 3.8, 12),
    ('Decoherence-\nresistant\n' + r'($\Gamma_{\rm loop}\ll 1$)', -3.3, -1.8, 11),
    ('Phase-compact\n(well-defined\nwinding number)', 3.3, -1.8, 11),
]

for i in range(3):
    circle = Circle((cx[i], cy[i]), r, facecolor=colors[i], edgecolor='#555',
                     linewidth=1.5, alpha=0.15, zorder=2)
    ax.add_patch(circle)
    circle2 = Circle((cx[i], cy[i]), r, facecolor='none', edgecolor='#555',
                      linewidth=1.5, zorder=4)
    ax.add_patch(circle2)

# Outer labels
for label, x, y, fs in labels_out:
    ax.text(x, y, label, ha='center', va='center', fontsize=fs,
            fontweight='bold', color='#333')

# Center label: PES intersection
bbox_pes = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#333',
                linewidth=2, alpha=0.95)
ax.text(0, 0.0, 'PES\npersistent\nconfiguration', ha='center', va='center',
        fontsize=12, fontweight='bold', color='#222', bbox=bbox_pes, zorder=10)

# Pairwise intersection labels (smaller, gray)
ax.text(-0.65, 1.8, 'smooth\nextremal', ha='center', va='center',
        fontsize=8.5, color='#666', fontstyle='italic')
ax.text(0.65, 1.8, 'compact\nextremal', ha='center', va='center',
        fontsize=8.5, color='#666', fontstyle='italic')
ax.text(0, -1.5, 'stable\ncoherent', ha='center', va='center',
        fontsize=8.5, color='#666', fontstyle='italic')

# Bottom annotation
ax.text(0, -3.2,
    'Observable quantum states = configurations satisfying all three conditions simultaneously',
    ha='center', va='center', fontsize=10.5, color='#444', fontstyle='italic')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_pes_diagram.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_pes_diagram.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_pes_diagram OK")
