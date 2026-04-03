"""
ECT Derivational Logic diagram  v3
====================================
Generates fig_partI_derivation_logic.png in the figures/ folder.
"""

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

FS  = 18
FSL = 13
DPI = 200

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': FS,
    'mathtext.fontset': 'cm',
})

FW, FH = 24, 31

fig = plt.figure(figsize=(FW, FH), dpi=DPI)
fig.patch.set_facecolor('white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis('off')

CLR = {
    'postulate': ('#C8C8C8', '#333333', 'black',   True),
    'phenom':    ('#444444', '#111111', 'white',   True),
    'levelA':    ('#EBEBEB', '#555555', 'black',   False),
    'levelB':    ('#AAAAAA', '#444444', 'black',   False),
    'open':      ('#FFFFFF', '#888888', '#555555', False),
}

H  = 0.82
HS = 0.95
nodes = {}

def box(key, x, y, lines, kind, w, h=H):
    nodes[key] = (x, y, w, h)
    fill, edge, tc, bold = CLR[kind]
    ls = '--' if kind == 'open' else '-'
    ax.add_patch(FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle='round,pad=0.07', linewidth=1.4,
        linestyle=ls, edgecolor=edge, facecolor=fill, zorder=3))
    fw = 'bold' if bold else 'normal'
    fi = 'italic' if kind == 'open' else 'normal'
    ax.text(x, y, '\n'.join(lines),
            ha='center', va='center', fontsize=FS,
            fontweight=fw, fontstyle=fi, color=tc,
            linespacing=1.22, zorder=4)

def arr(src_key, dst_key, dashed=False):
    x0, y0, w0, h0 = nodes[src_key]
    x1, y1, w1, h1 = nodes[dst_key]
    y_src = y0 - h0 / 2
    y_dst = y1 + h1 / 2
    ymid  = (y_src + y_dst) / 2
    c  = '#AAAAAA' if dashed else '#222222'
    lw = 1.6
    ls = (0, (4, 2.5)) if dashed else '-'
    ax.plot([x0, x0], [y_src, ymid], color=c, lw=lw, linestyle=ls, zorder=2, solid_capstyle='butt')
    ax.plot([x0, x1], [ymid,  ymid], color=c, lw=lw, linestyle=ls, zorder=2, solid_capstyle='butt')
    ax.annotate('', xy=(x1, y_dst), xytext=(x1, ymid + 0.001),
        arrowprops=dict(arrowstyle='-|>', color=c, lw=lw,
                        mutation_scale=16, connectionstyle='arc3,rad=0'), zorder=5)

def arr_horiz(src_key, dst_key):
    x0, y0, w0, h0 = nodes[src_key]
    x1, y1, w1, h1 = nodes[dst_key]
    ax.annotate('', xy=(x1 - w1/2, y1), xytext=(x0 + w0/2, y0),
        arrowprops=dict(arrowstyle='-|>', color='#222222', lw=1.6, mutation_scale=16), zorder=5)

def ctr(n, xL, xR):
    step = (xR - xL) / n
    return [xL + step * (i + 0.5) for i in range(n)]

# Row vertical centres
yLeg = 1.3
yR4b = 4.2
yR4a = 7.2
yR3b = 10.4
yR3a = 13.6
yR2  = 16.8
yR1h = 19.4    # Universality row
yR1  = 21.5    # SSB
yR0  = 25.0    # Postulates

# ── Row 0: Postulates ──
xs_post = ctr(4, 0.4, 14.0)
for (key, lines, kind, w), cx in zip([
    ('P1', ['P1', '4D Euclidean', r'$\S$2'],                     'postulate', 2.8),
    ('P2', ['P2', 'O(4) action', r'$\S$2'],                      'postulate', 2.8),
    ('P3', ['P3', r'Condensate $\Phi$', r'$\S$2'],               'postulate', 2.8),
    ('P4', ['P4', 'Gradient cond.', r'$\S$2'],                   'postulate', 2.8),
], xs_post):
    box(key, cx, yR0, lines, kind, w=w)

# Ph2 and Ph1 — spread wider apart
box('Ph2', 16.5, yR0,
    ['Ph2', r'$u_0\!=\!\bar{M}_\mathrm{Pl}$ (obs.)', r'$\S$5.4'],
    'phenom', w=3.8)
box('Ph1', 21.0, yR0,
    ['Ph1', r'$c^*\!=\!c$ (structural)', r'Level B, $\S$4.8'],
    'levelB', w=3.8)

# ── Row 1: SSB ──
box('SSB', 7.0, yR1,
    ['SSB', r'O(4)$\to$O(3), selects $w$', r'$\S$3'],
    'levelA', w=4.4, h=HS)
for k in ['P1', 'P2', 'P3', 'P4']:
    arr(k, 'SSB')

# ── Row 1.5: Universality ──
box('Univ', 12.0, yR1h,
    ['Universality Corollary', r'one $\Phi \to$ one $K^{AB} \to$ one cone', r'$\S$4.3'],
    'levelA', w=5.8, h=HS)
arr('SSB', 'Univ')

# ── Row 2: Direct consequences ──
for (key, lines, kind, w), cx in zip([
    ('hbar',  [r'$\hbar\!=\!S_\mathrm{min}/2\pi$', 'Planck const.', r'$\S$5.6'],   'levelB', 3.2),
    ('GE',    ['Euclidean corr.', r'$G_E(X,X^\prime)$', r'$\S$5'],                  'levelA', 3.0),
    ('Lor',   ['Lorentzian', 'metric', r'$\S$3.6'],                                 'levelA', 2.6),
    ('Golds', ['3 Goldstone', 'bosons (fuzzy DM)', r'$\S$4'],                       'levelA', 3.0),
    ('GN',    [r'$G_N\!=\!c_*^4/(8\pi M_G^2)$', 'Grav. const.', r'$\S$5.4'],       'levelA', 3.6),
    ('cstar', [r'$c^*\!=\!\sqrt{\beta/(\alpha\!-\!\beta)}$', 'Light sp.', r'$\S$5.3'], 'levelA', 3.6),
], ctr(6, 0.4, 23.6)):
    box(key, cx, yR2, lines, kind, w=w)

for k in ['hbar', 'GE', 'Lor', 'Golds', 'GN', 'cstar']:
    arr('SSB', k)
arr('P3',  'hbar',  dashed=True)
arr('Ph2', 'GN',    dashed=True)
arr('Univ', 'cstar')

# ── Row 3a ──
for (key, lines, kind, w), cx in zip([
    ('Gauge', ['Gauge fields', 'U(1), SU(2)', r'$\S$7'],                     'levelB', 2.8),
    ('Unruh', ['Unruh effect', r'$T_U\!=\!\hbar a/(2\pi c^* k_B)$', r'QS'], 'levelA', 3.8),
    ('KG',    ['Klein-Gordon', 'equation', r'$\S$3.6'],                      'levelA', 2.8),
    ('Sch',   [u'Schr\u00f6dinger', 'equation', r'QS'],                     'levelB', 2.8),
], ctr(4, 0.4, 23.6)):
    box(key, cx, yR3a, lines, kind, w=w)

arr('GE',  'Unruh');  arr('hbar', 'Unruh', dashed=True)
arr('Lor', 'KG')
arr('P3',  'Gauge', dashed=True)
arr_horiz('KG', 'Sch')

# ── Row 3b ──
for (key, lines, kind, w), cx in zip([
    ('Dirac',   ['Dirac eq.', r'$\S$9'],                                             'levelB', 2.6),
    ('BH',      ['BH thermo.', r'$S\!=\!A/(4G_N\hbar)$', r'QS'],                    'levelB', 3.2),
    ('Casimir', ['Casimir effect', r'$(F/A)\!=\!\frac{3}{2}(F/A)_\mathrm{QED}$', r'QS'], 'levelB', 4.2),
    ('Ein',     ['Einstein eqs.', '(linearised)', r'$\S$6'],                         'levelA', 3.0),
], ctr(4, 0.4, 23.6)):
    box(key, cx, yR3b, lines, kind, w=w)

arr('Lor',   'Dirac', dashed=True)
arr('GN',    'BH',    dashed=True);  arr('hbar', 'BH', dashed=True)
arr('Golds', 'Casimir')
arr('GN',    'Ein');  arr('Lor', 'Ein')

# ── Row 4a ──
for (key, l1, l2, l3, kind, w), cx in zip([
    ('Lepto', 'Leptogenesis',  r'$\eta_B\!\sim\!9\times10^{-10}$', r'$\S$7', 'levelB', 3.4),
    ('SU3',   'SU(3),',        r'$\alpha_\mathrm{fs}$ [OPEN]',     '',       'open',   2.8),
    ('HUP',   'Uncertainty',   'principle',                         r'QS',   'levelA', 2.8),
    ('law2',  '2nd law of',    'thermodynamics',                    r'$\S$3.9','levelB', 2.8),
    ('FF',    '5th force',     r'$\omega_5\!\sim\!10^{-10}$ rad/s', r'$\S$7.6','levelB', 3.6),
    ('Gen',   '3 generations', '[OPEN]',                            '',       'open',   2.8),
], ctr(6, 0.4, 23.6)):
    ls = [l1, l2] if not l3 else [l1, l2, l3]
    box(key, cx, yR4a, ls, kind, w=w)

arr('Gauge', 'Lepto');  arr('Gauge', 'SU3', dashed=True)
arr('hbar',  'HUP')
arr('SSB',   'law2', dashed=True)  # arrow of time from SSB, not from KG
arr('Dirac', 'FF', dashed=True);  arr('Dirac', 'Gen', dashed=True)

# ── Row 4b ──
for (key, l1, l2, kind, w), cx in zip([
    ('Infl', 'Primordial perturb.', r'$n_s\!=\!0.967$',                     'levelB', 3.6),
    ('DE',   'Dark energy',          r'$w_0>-1$',                            'levelB', 2.8),
    ('RotC', 'Rotation curves',      r'$G_\mathrm{eff}(r),\,g^\dagger$',    'levelB', 3.6),
    ('JWST', 'JWST galaxies',        r'$\times$2\u20133 enh.',              'levelB', 2.8),
    ('LIV',  'Planck-scale LIV',     r'$|\delta c/c|<10^{-15}$',            'levelB', 3.6),
], ctr(5, 0.4, 23.6)):
    box(key, cx, yR4b, [l1, l2], kind, w=w)

arr('Ein',   'Infl');  arr('Ein', 'DE')
arr('GN',    'RotC');  arr('GN',  'JWST', dashed=True)
arr('cstar', 'LIV',   dashed=True)
arr('Golds', 'Infl',  dashed=True)

# ── Legend ──
ax.axhline(2.3, color='#CCCCCC', lw=1.0, xmin=0.01, xmax=0.99)
yLn = 1.6
leg_nodes = [
    ('postulate', 'Postulate (P1\u2013P4)'),
    ('phenom',    'Phenomenological input'),
    ('levelA',    'Derived \u2013 Level A (strict)'),
    ('levelB',    'Derived \u2013 Level B (+assump.)'),
    ('open',      'Open problem'),
]
for (kind, label), cx in zip(leg_nodes, ctr(5, 0.4, 23.6)):
    fill, edge, tc, bold = CLR[kind]
    ls = '--' if kind == 'open' else '-'
    ax.add_patch(FancyBboxPatch(
        (cx - 2.2, yLn - 0.32), 4.4, 0.64,
        boxstyle='round,pad=0.08', linewidth=1.2,
        linestyle=ls, edgecolor=edge, facecolor=fill, zorder=3))
    fw = 'bold' if bold else 'normal'
    fi = 'italic' if kind == 'open' else 'normal'
    ax.text(cx, yLn, label,
            ha='center', va='center', fontsize=FSL,
            fontweight=fw, fontstyle=fi, color=tc, zorder=4)

yLa = 0.7
x_s0, x_s1 = 3.5, 6.5
ax.annotate('', xy=(x_s1, yLa), xytext=(x_s0, yLa),
    arrowprops=dict(arrowstyle='-|>', color='#222222', lw=1.6, mutation_scale=16), zorder=5)
ax.text((x_s0+x_s1)/2, yLa + 0.3, 'Strict derivation', ha='center', va='bottom',
        fontsize=FSL, color='#222222')
x_d0, x_d1 = 16.5, 19.5
ax.annotate('', xy=(x_d1, yLa), xytext=(x_d0, yLa),
    arrowprops=dict(arrowstyle='-|>', color='#AAAAAA', lw=1.6, mutation_scale=16,
                    linestyle=(0,(4,2.5))), zorder=5)
ax.text((x_d0+x_d1)/2, yLa + 0.3, 'Requires assumptions', ha='center', va='bottom',
        fontsize=FSL, color='#888888')

# ── Save ──
script_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(script_dir, '..', 'figures')
out_png = os.path.join(figures_dir, 'fig_partI_derivation_logic.png')
out_pdf = os.path.join(figures_dir, 'fig_partI_derivation_logic.pdf')
plt.savefig(out_png, dpi=DPI, bbox_inches='tight', facecolor='white')
plt.savefig(out_pdf,          bbox_inches='tight', facecolor='white')
plt.close()
print(f"PNG saved: {out_png}  ({os.path.getsize(out_png)//1024} KB)")
print(f"PDF saved: {out_pdf}  ({os.path.getsize(out_pdf)//1024} KB)")
