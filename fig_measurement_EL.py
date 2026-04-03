"""
F5: Measurement as Euclidean→Lorentzian transition
Flow diagram showing the structural reading of measurement in ECT
"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 11, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(12, 5))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.01, 0.02, 0.98, 0.96])
ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis('off')

nodes = {}
def box(key, x, y, w, h, lines, fill='#eee', edge='#444', fs=10.5):
    nodes[key] = (x, y, w, h)
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.12', facecolor=fill, edgecolor=edge, linewidth=1.5, zorder=3))
    ax.text(x, y, '\n'.join(lines), ha='center', va='center', fontsize=fs,
            linespacing=1.2, zorder=4)

def arr(src, dst, label=''):
    x0, y0, w0, h0 = nodes[src]
    x1, y1, w1, h1 = nodes[dst]
    ax.annotate('', xy=(x1-w1/2, y1), xytext=(x0+w0/2, y0),
        arrowprops=dict(arrowstyle='-|>', color='#444', lw=1.8, mutation_scale=16))
    if label:
        mx = (x0+w0/2 + x1-w1/2)/2
        my = (y0+y1)/2 + 0.25
        ax.text(mx, my, label, fontsize=9, ha='center', va='bottom',
                color='#555', fontstyle='italic')

# Stage 1: Euclidean coherent
box('E', 1.5, 2.5, 2.4, 2.5,
    ['Euclidean\ncoherent regime', '',
     r'$\Gamma_{\rm loop}\ll 1$', '',
     'Multiple winding\nsectors coexist',
     'No definite outcome'],
    fill='#d5d5d5', fs=10)

# Stage 2: Environmental coupling
box('env', 4.8, 2.5, 2.4, 2.5,
    ['Environmental\ncoupling', '',
     r'$N_{\rm eff}\gg 1$ modes', '',
     'Decoherence functional',
     r'$\Gamma[q]$ grows'],
    fill='#e0e0e0', fs=10)

# Stage 3: E→L transition
box('trans', 8.0, 2.5, 2.2, 2.5,
    ['E→L transition', '',
     r'$\Gamma_{\rm loop}\gtrsim 1$', '',
     'Off-diagonal phases\nsuppressed',
     'Effective classicality'],
    fill='#eaeaea', fs=10)

# Stage 4: Lorentzian outcome
box('L', 11.0, 2.5, 1.6, 2.5,
    ['Effective\nLorentzian\noutcome', '',
     'Single branch\nselected', '',
     '"Collapse"'],
    fill='#f2f2f2', fs=10)

arr('E', 'env', 'detector enters\ncondensate BVP')
arr('env', 'trans', r'$N_{\rm eff}\gamma t \to 1$')
arr('trans', 'L', 'classical\nlimit')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_measurement_EL.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_measurement_EL.png'), dpi=300, bbox_inches='tight')
plt.close()
print("fig_measurement_EL OK")
