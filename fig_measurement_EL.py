"""F5: Measurement E→L transition — v2: larger fonts, spaced boxes, arrows to edges"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

plt.rcParams.update({'font.family': 'serif', 'font.size': 12, 'mathtext.fontset': 'cm'})

fig = plt.figure(figsize=(14, 4.5))
fig.patch.set_facecolor('white')
ax = fig.add_axes([0.01, 0.03, 0.98, 0.94])
ax.set_xlim(0, 14); ax.set_ylim(0, 4.5); ax.axis('off')

nodes = {}
def box(key, x, y, w, h, lines, fill='#eee', fs=12):
    nodes[key] = (x, y, w, h)
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h,
        boxstyle='round,pad=0.12', facecolor=fill, edgecolor='#444', linewidth=1.5, zorder=3))
    ax.text(x, y, '\n'.join(lines), ha='center', va='center', fontsize=fs,
            linespacing=1.2, zorder=4)

def arr(src, dst, label=''):
    x0,y0,w0,h0 = nodes[src]; x1,y1,w1,h1 = nodes[dst]
    ax.annotate('', xy=(x1-w1/2, y1), xytext=(x0+w0/2, y0),
        arrowprops=dict(arrowstyle='-|>', color='#444', lw=1.8, mutation_scale=16))
    if label:
        mx = (x0+w0/2 + x1-w1/2)/2
        ax.text(mx, y0+0.35, label, fontsize=10, ha='center', va='bottom',
                color='#555', fontstyle='italic')

box('E', 1.8, 2.25, 2.8, 3.2,
    ['Euclidean\ncoherent regime', '',
     r'$\Gamma_{\rm loop}\ll 1$', '',
     'Multiple winding\nsectors coexist',
     'No definite outcome'],
    fill='#d0d0d0', fs=12)

box('env', 5.5, 2.25, 2.6, 3.2,
    ['Environmental\ncoupling', '',
     r'$N_{\rm eff}\gg 1$ modes', '',
     'Decoherence functional',
     r'$\Gamma[q]$ grows'],
    fill='#ddd', fs=12)

box('trans', 9.2, 2.25, 2.6, 3.2,
    [r'E$\to$L transition', '',
     r'$\Gamma_{\rm loop}\gtrsim 1$', '',
     'Off-diagonal phases\nsuppressed',
     'Effective classicality'],
    fill='#e5e5e5', fs=12)

box('L', 12.5, 2.25, 2.2, 3.2,
    ['Effective\nLorentzian\noutcome', '',
     'Single branch\nselected', '',
     '"Collapse"'],
    fill='#f0f0f0', fs=12)

arr('E', 'env', 'detector enters\ncondensate BVP')
arr('env', 'trans', r'$N_{\rm eff}\gamma t \to 1$')
arr('trans', 'L', 'classical\nlimit')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'figures')
fig.savefig(os.path.join(out, 'fig_measurement_EL.pdf'), bbox_inches='tight')
fig.savefig(os.path.join(out, 'fig_measurement_EL.png'), dpi=300, bbox_inches='tight')
plt.close(); print("OK")
