#!/usr/bin/env python3
"""
ECT Derivation Map — master logic graph for Part IV.
Matplotlib-based with mathtext for proper formula rendering.
Greyscale, 300 dpi. Proportions tuned for one full journal page.
"""
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(7.5, 13))
ax.set_xlim(-0.2, 7.7)
ax.set_ylim(-0.8, 23.5)
ax.set_aspect('equal')
ax.axis('off')

def box(ax, x, y, w, h, lines, fs=7.5,
        fc='#e8e8e8', ec='#333333', lw=1.2, ls='-'):
    b = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle="round,pad=0.12",
                       facecolor=fc, edgecolor=ec,
                       linewidth=lw, linestyle=ls)
    ax.add_patch(b)
    n = len(lines)
    sp = min(0.26, (h - 0.15) / max(n - 1, 1))
    top = y + (n - 1) * sp / 2
    for i, ln in enumerate(lines):
        ax.text(x, top - i * sp, ln, ha='center', va='center',
                fontsize=fs, fontfamily='serif')

def ar(ax, x1, y1, x2, y2, dashed=False):
    a = FancyArrowPatch((x1, y1), (x2, y2),
                        arrowstyle='->', linewidth=0.8,
                        color='#777' if dashed else '#444',
                        linestyle='--' if dashed else '-',
                        mutation_scale=8)
    ax.add_patch(a)

CX = 3.75
D = u"\u00b7"
xl, xr = 1.85, 5.65
nw = 3.5  # node width for branches

# ==================== TIER 0: PHI ====================
box(ax, CX, 23, 6.2, 0.85,
    [r"$\Phi$-medium: 4D Euclidean manifold ($\mathcal{M}^4,\,\delta_{AB}$), scalar condensate $\Phi$"],
    fs=8, fc='#bbb', lw=2.0)

# ==================== TIER 1: POSTULATES ====================
py1, py2, py3 = 21.65, 20.85, 20.05
pw = 3.5

box(ax, xl, py1, pw, 0.6,
    [r"P1: 4D Euclidean arena $(\mathcal{M}^4,\delta_{AB})$"], fs=7, fc='#d5d5d5')
box(ax, xr, py1, pw, 0.6,
    [r"P2: $O(4)$-invariant action $S_E[\Psi]$"], fs=7, fc='#d5d5d5')
box(ax, xl, py2, pw, 0.6,
    ["P3: Minimal scalar microdynamics"], fs=7, fc='#d5d5d5')
box(ax, xr, py2, pw, 0.6,
    [r"P4: Ordered vacuum branch $\langle\partial\Phi\rangle\!\neq\!0$"], fs=7, fc='#d5d5d5')
box(ax, xl, py3, pw, 0.6,
    [r"P5: Medium character $\to$ gauge redundancy"], fs=7, fc='#d5d5d5')
box(ax, xr, py3, pw, 0.6,
    ["P6: Multiplicity of configurations"], fs=7, fc='#d5d5d5')

brd = FancyBboxPatch((0.0, py3 - 0.42), 7.5, py1 - py3 + 0.95,
                      boxstyle="round,pad=0.08",
                      facecolor='none', edgecolor='#999', lw=0.7, linestyle='--')
ax.add_patch(brd)
ax.text(0.15, py1 + 0.37, "Foundational Postulates P1\u2013P6",
        fontsize=7, color='#555', fontstyle='italic')

for px in [xl, xr]:
    ar(ax, CX, 23 - 0.42, px, py1 + 0.3)

# ==================== TIER 2: SSB ====================
ssb = 18.95
box(ax, CX, ssb, 6.5, 0.85,
    [r"$O(4)\!\rightarrow\!O(3)$ SSB: preferred direction $n_A\!=\!\delta_{Aw}$, ordered background"],
    fs=8, fc='#b0b0b0', lw=1.8)
ar(ax, xl, py3 - 0.3, CX - 1.2, ssb + 0.42)
ar(ax, xr, py3 - 0.3, CX + 1.2, ssb + 0.42)

# ==================== TIER 3: LORENTZIAN ====================
lor = 17.65
box(ax, CX, lor, 6.5, 0.85,
    ["Emergent Lorentzian structure: " +
     r"diag$(-1,1,1,1)$, $c_*\!=\!1/\sqrt{\alpha\!-\!\beta}$, causal cone"],
    fs=7.5, fc='#c5c5c5', lw=1.5)
ar(ax, CX, ssb - 0.42, CX, lor + 0.42)
ax.text(CX + 0.15, (ssb + lor)/2, r"$\alpha\!>\!\beta$",
        fontsize=7, color='#555', ha='left')

# ==================== TIER 4: BRANCHES ====================
br = 16.65
box(ax, xl, br, nw, 0.55,
    ["Macroscopic / Tensor Branch (Part II)"], fs=7.5, fc='#d0d0d0')
box(ax, xr, br, nw, 0.55,
    ["Quantum / Coherent Branch (Part III)"], fs=7.5, fc='#d0d0d0')
ar(ax, CX - 1.2, lor - 0.42, xl, br + 0.27)
ar(ax, CX + 1.2, lor - 0.42, xr, br + 0.27)

# ==================== MACRO BRANCH (left) ====================
mx = xl

gr = 15.35
box(ax, mx, gr, nw, 1.05,
    ["General Relativity",
     r"Fierz\u2013Pauli $\to$ Einstein eqs.",
     r"$G_N\!=\!c_*^{\,2}(\alpha\!-\!\beta)/(16\pi v_0^2)$  [A/B]"],
    fs=7)
ar(ax, mx, br - 0.27, mx, gr + 0.52)

cos = 13.85
box(ax, mx, cos, nw, 1.0,
    ["Cosmology",
     r"Inflation $n_s\!\approx\!0.967$ " + D + r" $\Lambda_{\rm eff}$",
     "Hubble tension route  [B]"],
    fs=7)
ar(ax, mx, gr - 0.52, mx, cos + 0.5)

gal = 12.35
box(ax, mx, gal, nw, 1.0,
    ["Galactic Dynamics",
     r"$\phi$-branch " + D + " BTFR slope=4 " + D + " RAR",
     r"$g_\dagger\!\sim\!cH_0/(2\pi)$  [B]"],
    fs=7)
ar(ax, mx, cos - 0.5, mx, gal + 0.5)

bh = 10.9
box(ax, mx, bh, nw, 1.0,
    ["Black Holes & Strong Field",
     r"Shell $\rho_c\!=\!\ell_{\rm Pl}/\sqrt{3\pi}$",
     "BH thermo " + D + " Information  [B/Open]"],
    fs=7)
ar(ax, mx, gal - 0.5, mx, bh + 0.5)

fi = 9.55
box(ax, mx, fi, nw, 0.85,
    ["5th Force",
     r"$\beta_5\!\sim\!m_f/M_{\rm Pl}$ " + D + r" $M_{\rm max}\!\approx\!2.17\,M_\odot$  [B]"],
    fs=7)
ar(ax, mx, bh - 0.5, mx, fi + 0.42)

cl = 8.3
box(ax, mx, cl, nw, 0.8,
    ["Cluster Lensing",
     r"Bullet, A520, El Gordo: $\nu$-closure  [B]"],
    fs=7)
ar(ax, mx, fi - 0.42, mx, cl + 0.4)

# ==================== QUANTUM BRANCH (right) ====================
qx = xr

s0 = 15.35
box(ax, qx, s0, nw, 0.85,
    [r"Action Scale $S_0$",
     "Winding sectors " + D + " Phase quant.  [A]"],
    fs=7)
ar(ax, qx, br - 0.27, qx, s0 + 0.42)

sc = 14.05
box(ax, qx, sc, nw, 0.85,
    [u"Schr\u00f6dinger Equation",
     "Canonical phase " + D + " Uncertainty  [A/B]"],
    fs=7)
ar(ax, qx, s0 - 0.42, qx, sc + 0.42)

va = 12.8
box(ax, qx, va, nw, 0.85,
    ["Vacuum Response",
     r"Casimir $(3/2)$ " + D + r" Unruh $T_U$ " + D + " Part. prod.  [A/B]"],
    fs=7)
ar(ax, qx, sc - 0.42, qx, va + 0.42)

de = 11.55
box(ax, qx, de, nw, 0.85,
    ["Decoherence & Arrow of Time",
     "Influence func. " + D + " Entropy " + D + " Crooks  [A/B]"],
    fs=7)
ar(ax, qx, va - 0.42, qx, de + 0.42)

bo = 10.35
box(ax, qx, bo, nw, 0.75,
    ["Born Rule",
     u"Gleason route (C1\u2013C3)  [B/Open]"],
    fs=7)
ar(ax, qx, de - 0.42, qx, bo + 0.37)

to = 9.2
box(ax, qx, to, nw, 0.85,
    ["Exchange Topology & Spinors",
     r"$\pi_1(\mathcal{M}_2)\!=\!\mathbb{Z}_2$ " + D + " Dirac " + D + " Entanglement  [A]"],
    fs=7)
ar(ax, qx, bo - 0.37, qx, to + 0.42)

# ==================== GAUGE (centre) ====================
gy = 6.8
box(ax, CX, gy, 7.0, 1.3,
    ["Gauge & Matter Sector",
     r"$U(1)\!\to\!$ photon " + D + r" $SU(2)\!\to\!W^\pm\!,Z$ " + D + r" Higgs ($v_2\!\approx\!246$ GeV)",
     r"Fermions: $O(3)$ spinor reps " + D + r" $SU(3)$: open " + D + " 3 gen.: open  [A/B/Open]"],
    fs=7, fc='#ddd')
ar(ax, mx, cl - 0.4, CX - 1.8, gy + 0.65)
ar(ax, qx, to - 0.42, CX + 1.8, gy + 0.65)

# ==================== PREDICTIONS ====================
pr = 4.7
box(ax, CX, pr, 7.0, 1.3,
    ["Quantitative Predictions",
     r"LIV: $|\delta c/c|\!<\!10^{-15}$ " + D + " Casimir: $3/2\!\times\!$QED " + D + r" $g_\dagger\!\approx\!1.1\!\times\!10^{-10}$ m/s$^2$",
     r"BTFR slope = 4 " + D + r" $n_s\!\approx\!0.967$ " + D + r" $M_{\rm max}\!\approx\!2.17\,M_\odot$ " + D + r" Env.-dep. $g_\dagger$"],
    fs=7, fc='#ccc', lw=1.5)
ar(ax, CX, gy - 0.65, CX, pr + 0.65)

# FALSIFIERS
fa = 2.7
box(ax, CX, fa, 7.0, 1.2,
    ["Cross-Sector Architectural Falsifiers",
     r"Single $c_*$ " + D + r" Single $S_0$ " + D + r" Single UV threshold $m_\sigma$",
     "No DM particles in lab " + D + " Env.-dependent transition morphology"],
    fs=7, fc='#ccc', lw=1.5)
ar(ax, CX, pr - 0.65, CX, fa + 0.6)

# OPEN
op = 0.8
box(ax, CX, op, 7.0, 1.2,
    ["Major Open Fronts",
     r"$S_0\!=\!\hbar$ " + D + r" $SU(3)$ " + D + " Yukawa " + D + r" $\alpha_{\rm fs}\!=\!1/137$ " + D + " Full nonlinear GR",
     "Born rule unconditional " + D + " Bell correlators " + D + " Page curve " + D + " 3 generations"],
    fs=7, fc='white', ec='#666', ls='--')
ar(ax, CX, fa - 0.6, CX, op + 0.6, dashed=True)

# ==================== LEGEND ====================
ax.text(0.1, -0.3,
        "[A] = structural theorem    [A/B] = singled out    "
        "[B] = closure-dependent    [Open] = programme-level",
        fontsize=6.5, color='#555')
ax.text(0.1, -0.6,
        "Solid arrow = strict derivation    "
        "Dashed arrow = open / incomplete route",
        fontsize=6.5, color='#555')

plt.tight_layout(pad=0.2)
out = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures"
plt.savefig(f"{out}/fig_ect_derivation_map.png", dpi=300,
            bbox_inches='tight', facecolor='white')
plt.savefig(f"{out}/fig_ect_derivation_map.pdf",
            bbox_inches='tight', facecolor='white')
print("Done")
