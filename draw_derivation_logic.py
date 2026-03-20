"""
ECT Derivational Logic diagram
================================
Generates fig_derivation_logic.png (and .pdf) in the figures/ folder.

Key parameters to tweak:
  FS   — node font size (currently 20)
  FSL  — legend font size (currently 15)
  DPI  — output resolution (currently 200)
  FW, FH — canvas size in inches (currently 22 x 27)
  H    — standard box height (currently 0.82)
  yR*  — vertical centres of each row

To increase ONLY the font (text grows relative to boxes):
  raise FS without changing FW/FH/H.
"""

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

# ── Parameters ────────────────────────────────────────────────────────────────
FS  = 20     # node font size
FSL = 15     # legend font size
DPI = 200    # output resolution

plt.rcParams.update({
    'font.family':      'serif',
    'font.size':         FS,
    'mathtext.fontset': 'cm',
})

FW, FH = 22, 27   # canvas in inches

fig = plt.figure(figsize=(FW, FH), dpi=DPI)
fig.patch.set_facecolor('white')
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis('off')

# ── Colour palette ────────────────────────────────────────────────────────────
CLR = {
    'postulate': ('#C8C8C8', '#333333', 'black',   True),
    'phenom':    ('#444444', '#111111', 'white',   True),
    'levelA':    ('#EBEBEB', '#555555', 'black',   False),
    'levelB':    ('#AAAAAA', '#444444', 'black',   False),
    'open':      ('#FFFFFF', '#888888', '#555555', False),
}

H  = 0.82   # standard box height
HS = 0.95   # SSB box height

# Each node stores (cx, cy, w, h) for precise arrow endpoints
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
    """Orthogonal elbow arrow from bottom edge of src to top edge of dst."""
    x0, y0, w0, h0 = nodes[src_key]
    x1, y1, w1, h1 = nodes[dst_key]
    y_src = y0 - h0 / 2        # bottom of source
    y_dst = y1 + h1 / 2        # top of destination
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
    """Horizontal arrow from right edge of src to left edge of dst (same row)."""
    x0, y0, w0, h0 = nodes[src_key]
    x1, y1, w1, h1 = nodes[dst_key]
    ax.annotate('', xy=(x1 - w1/2, y1), xytext=(x0 + w0/2, y0),
        arrowprops=dict(arrowstyle='-|>', color='#222222', lw=1.6, mutation_scale=16), zorder=5)

def ctr(n, xL, xR):
    """Return n evenly-spaced centres in [xL, xR]."""
    step = (xR - xL) / n
    return [xL + step * (i + 0.5) for i in range(n)]

# ═══ Row vertical centres (bottom → top) ══════════════════════════════════════
yLeg = 1.3
yR4b = 4.2    # Predictions II  (Infl, DE, RotC, JWST, LIV)
yR4a = 7.2    # Predictions I   (Lepto, SU3, HUP, law2, FF, Gen)
yR3b = 10.4   # Equations B     (Dirac, BH, Casimir, Ein)
yR3a = 13.6   # Equations A     (Gauge, Unruh, KG, Sch)
yR2  = 16.8   # Direct consequences
yR1  = 19.7   # SSB
yR0  = 23.2   # Postulates

# ── Row 0: Postulates ─────────────────────────────────────────────────────────
for (key, lines, kind, w), cx in zip([
    ('P1',  ['P1', '4D Euclidean'],                          'postulate', 2.6),
    ('P2',  ['P2', 'O(4) action'],                           'postulate', 2.6),
    ('P3',  ['P3', r'Condensate $\Phi$'],                    'postulate', 2.7),
    ('P4',  ['P4', 'Gradient cond.'],                        'postulate', 2.6),
], ctr(4, 0.4, 15.0)):
    box(key, cx, yR0, lines, kind, w=w)

for (key, lines, kind, w), cx in zip([
    ('Ph2', ['Ph2', r'$v_0=\bar{M}_\mathrm{Pl}$ (obs.)'],   'phenom', 3.8),
    ('Ph1', ['Ph1', r'$c^*=c,\ \alpha=2\beta$'],              'phenom', 3.4),
], ctr(2, 16.0, 21.6)):
    box(key, cx, yR0, lines, kind, w=w)

# ── Row 1: SSB ────────────────────────────────────────────────────────────────
box('SSB', 7.0, yR1,
    ['SSB', r'O(4)$\to$O(3)', 'selects $w$-dir.'],
    'levelA', w=3.6, h=HS)
for k in ['P1', 'P2', 'P3', 'P4']:
    arr(k, 'SSB')

# ── Row 2: Direct consequences ────────────────────────────────────────────────
for (key, lines, kind, w), cx in zip([
    ('hbar',  [r'$\hbar=S_\mathrm{min}/2\pi$', 'Planck const.'],    'levelB', 3.2),
    ('GE',    ['Euclidean corr.', r'$G_E(X,X^\prime)$'],            'levelA', 3.0),
    ('Lor',   ['Lorentzian', 'metric'],                              'levelA', 2.6),
    ('Golds', ['3 Goldstone', r'bosons (fuzzy DM)'],                 'levelA', 3.0),
    ('GN',    [r'$G_N=1/(8\pi v_0^2)$', 'Grav. const.'],            'levelA', 3.2),
    ('cstar', [r'$c^*=\sqrt{\beta/(\alpha-\beta)}$', 'Light sp.'],   'levelA', 3.4),
], ctr(6, 0.4, 21.6)):
    box(key, cx, yR2, lines, kind, w=w)

for k in ['hbar', 'GE', 'Lor', 'Golds', 'GN', 'cstar']:
    arr('SSB', k)
arr('P3',  'hbar',  dashed=True)
arr('Ph2', 'GN',    dashed=True)
arr('Ph1', 'cstar', dashed=True)

# ── Row 3a: Gauge / Unruh / KG / Sch ─────────────────────────────────────────
for (key, lines, kind, w), cx in zip([
    ('Gauge', ['Gauge fields', 'U(1), SU(2)'],                        'levelB', 2.8),
    ('Unruh', ['Unruh effect', r'$T_U=\hbar a/(2\pi c^* k_B)$'],     'levelA', 3.6),
    ('KG',    ['Klein-Gordon', 'equation'],                            'levelA', 2.8),
    ('Sch',   ['Schrödinger', 'equation'],                             'levelA', 2.8),
], ctr(4, 0.4, 21.6)):
    box(key, cx, yR3a, lines, kind, w=w)

arr('GE',  'Unruh');          arr('hbar', 'Unruh', dashed=True)
arr('Lor', 'KG')
arr('P3',  'Gauge', dashed=True)
arr_horiz('KG', 'Sch')        # same-row horizontal arrow

# ── Row 3b: Dirac / BH / Casimir / Ein ───────────────────────────────────────
for (key, lines, kind, w), cx in zip([
    ('Dirac',   ['Dirac', 'equation'],                                          'levelB', 2.6),
    ('BH',      ['BH thermo.', r'$S=A/(4G_N\hbar)$'],                          'levelB', 3.0),
    ('Casimir', ['Casimir effect', r'$(F/A)=\frac{3}{2}(F/A)_\mathrm{QED}$'],  'levelA', 4.0),
    ('Ein',     ['Einstein eqs.', '(linearised)'],                              'levelA', 3.0),
], ctr(4, 0.4, 21.6)):
    box(key, cx, yR3b, lines, kind, w=w)

arr('Lor',   'Dirac',   dashed=True)
arr('GN',    'BH',      dashed=True);  arr('hbar', 'BH', dashed=True)
arr('Golds', 'Casimir')
arr('GN',    'Ein');    arr('Lor', 'Ein')

# ── Row 4a: Predictions I ─────────────────────────────────────────────────────
for (key, l1, l2, kind, w), cx in zip([
    ('Lepto', 'Leptogenesis',  r'$\eta_B\sim9\times10^{-10}$',  'levelB', 3.2),
    ('SU3',   'SU(3),',        r'$\alpha_\mathrm{fs}$ [OPEN]',  'open',   2.8),
    ('HUP',   'Uncertainty',   'principle',                      'levelA', 2.8),
    ('law2',  '2nd law of',    'thermodynamics',                 'levelA', 2.8),
    ('FF',    '5th force',     r'$\omega_5\sim10^{-10}$ rad/s', 'levelB', 3.4),
    ('Gen',   '3 generations', '[OPEN]',                         'open',   2.8),
], ctr(6, 0.4, 21.6)):
    box(key, cx, yR4a, [l1, l2], kind, w=w)

arr('Gauge', 'Lepto');           arr('Gauge', 'SU3',  dashed=True)
arr('hbar',  'HUP')
arr('KG',    'law2')
arr('Dirac', 'FF',  dashed=True); arr('Dirac', 'Gen', dashed=True)

# ── Row 4b: Predictions II ────────────────────────────────────────────────────
for (key, l1, l2, kind, w), cx in zip([
    ('Infl', 'Inflation/part.prod.', r'$n_s=0.967$',                    'levelB', 3.4),
    ('DE',   'Dark energy',          r'$w_0>-1$',                       'levelB', 2.8),
    ('RotC', 'Rotation curves',      r'$G_\mathrm{eff}(r),\,g^\dagger$', 'levelB', 3.4),
    ('JWST', 'JWST galaxies',        r'$\times$2–3 enh.',               'levelB', 2.8),
    ('LIV',  'Planck-scale LIV',    r'$|\delta c/c|<10^{-15}$',        'levelB', 3.6),
], ctr(5, 0.4, 21.6)):
    box(key, cx, yR4b, [l1, l2], kind, w=w)

arr('Ein',   'Infl');            arr('Ein',   'DE')
arr('GN',    'RotC');            arr('GN',    'JWST',  dashed=True)
arr('cstar', 'LIV',  dashed=True)
arr('Golds', 'Infl', dashed=True)

# ── Legend (horizontal, no title) ─────────────────────────────────────────────
ax.axhline(2.3, color='#CCCCCC', lw=1.0, xmin=0.01, xmax=0.99)
leg = [
    ('postulate', 'Postulate (P1–P4)'),
    ('phenom',    'Phenomenological input'),
    ('levelA',    'Derived – Level A (strict)'),
    ('levelB',    'Derived – Level B (+assump.)'),
    ('open',      'Open problem'),
]
for (kind, label), cx in zip(leg, ctr(5, 0.4, 21.6)):
    fill, edge, tc, bold = CLR[kind]
    ls = '--' if kind == 'open' else '-'
    ax.add_patch(FancyBboxPatch(
        (cx - 2.0, yLeg - 0.32), 4.0, 0.64,
        boxstyle='round,pad=0.08', linewidth=1.2,
        linestyle=ls, edgecolor=edge, facecolor=fill, zorder=3))
    fw = 'bold' if bold else 'normal'
    fi = 'italic' if kind == 'open' else 'normal'
    ax.text(cx, yLeg, label,
            ha='center', va='center', fontsize=FSL,
            fontweight=fw, fontstyle=fi, color=tc, zorder=4)

# ── Save ──────────────────────────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(script_dir, '..', 'figures')

out_png = os.path.join(figures_dir, 'fig_derivation_logic.png')
out_pdf = os.path.join(figures_dir, 'fig_derivation_logic.pdf')

plt.savefig(out_png, dpi=DPI, bbox_inches='tight', facecolor='white')
plt.savefig(out_pdf,          bbox_inches='tight', facecolor='white')
plt.close()
print(f"PNG saved: {out_png}  ({os.path.getsize(out_png)//1024} KB)")
print(f"PDF saved: {out_pdf}  ({os.path.getsize(out_pdf)//1024} KB)")
