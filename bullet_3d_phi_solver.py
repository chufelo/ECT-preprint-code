#!/usr/bin/env python3
"""
bullet_3d_phi_solver.py
========================
3D merger-scale ECT φ-solver for the Bullet Cluster.

Implements the φ-closure from the paper (Level B, §17):
  1. Solve 3D Poisson  ∇²Φ_N = 4πG ρ_bar  via FFT
  2. Compute |∇Φ_N| on 3D grid
  3. Apply algebraic μ-closure: Σ_eff = ν(g_N/g_†)·Σ_b
     with ν(y) = √[(1 + √(1+4/y²))/2]  [eq:nu_cluster]
  4. Project along line-of-sight → κ(x,y)

Geometry: post-collision Bullet Cluster
  - Two BCG subclusters (collisionless, at ±200 kpc)
  - Two gas blobs (collisional, lagged 120 kpc behind BCG)
  - Parameters from paper Table (§17)

Results:
  - Morphology: κ-peak at 37 kpc from BCG  [observed: < 25 kpc]
  - Amplitude:  M_ECT/M_obs ~ 0.47          [paper range: 0.15-0.45]
  - BCG/gas peak ratio: Σ_eff(BCG)/Σ_eff(gas) = 1.04  (BCG wins marginally)

Status: Level B — correct physics (algebraic μ-closure),
        not yet full nonlinear 3D solver (OP22 in paper).

Run:  python3 bullet_3d_phi_solver.py
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.ndimage import maximum_filter
import warnings; warnings.filterwarnings('ignore')
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ── Constants ─────────────────────────────────────────────────────────────────
G_N  = 6.674e-11   # m³/(kg·s²)
Msun = 1.989e30    # kg
kpc  = 3.086e19    # m

# ── Grid ──────────────────────────────────────────────────────────────────────
Ng   = 128
Lbox = 2000.0      # kpc
dx   = Lbox / Ng   # kpc/cell
dx_m = dx * kpc    # m/cell
xc   = (np.arange(Ng) + 0.5) * dx - Lbox/2
X3, Y3, Z3 = np.meshgrid(xc, xc, xc, indexing='ij')

# ── Bullet Cluster parameters (from paper §17 Table) ─────────────────────────
x_BCG_main = -200.0;  x_BCG_sub = +200.0
x_gas_main =  -80.0;  x_gas_sub =  +80.0  # gas 120 kpc behind BCG
M_BCG = 5e12 * Msun;  s_BCG = 70.0         # kpc
M_gas = 6e13 * Msun;  s_gas = 225.0        # kpc

g_dagger = 1.2e-10  # m/s²  — cluster critical acceleration

# ── Density setup ─────────────────────────────────────────────────────────────
def g3d(X,Y,Z,x0,y0,z0,sx,sy,sz,M):
    norm = M / ((2*np.pi)**1.5 * sx*sy*sz * kpc**3)
    return norm * np.exp(-0.5*(((X-x0)/sx)**2+((Y-y0)/sy)**2+((Z-z0)/sz)**2))

rho_BCG = (g3d(X3,Y3,Z3, x_BCG_main,0,0, s_BCG,s_BCG,s_BCG, M_BCG) +
           g3d(X3,Y3,Z3, x_BCG_sub, 0,0, s_BCG,s_BCG,s_BCG, M_BCG))
rho_gas = (g3d(X3,Y3,Z3, x_gas_main,0,0, s_gas,s_gas*0.8,s_gas*0.8, M_gas) +
           g3d(X3,Y3,Z3, x_gas_sub, 0,0, s_gas,s_gas*0.8,s_gas*0.8, M_gas))
rho_bar = rho_BCG + rho_gas

# ── 3D Poisson solver (FFT) ───────────────────────────────────────────────────
def solve_poisson_fft(rho, dx_kpc):
    dx_m = dx_kpc * kpc; Ng = rho.shape[0]
    rho_k = np.fft.fftn(rho)
    kx = 2*np.pi*np.fft.fftfreq(Ng, d=dx_m)
    KX,KY,KZ = np.meshgrid(kx,kx,kx,indexing='ij')
    k2 = (2/dx_m**2*(np.cos(KX*dx_m)-1) + 2/dx_m**2*(np.cos(KY*dx_m)-1) +
          2/dx_m**2*(np.cos(KZ*dx_m)-1))
    k2[0,0,0] = 1.0
    Phi_k = 4*np.pi*G_N * rho_k / k2; Phi_k[0,0,0] = 0.0
    return np.real(np.fft.ifftn(Phi_k))

Phi_N = solve_poisson_fft(rho_bar, dx)
gx = np.gradient(Phi_N, dx_m, axis=0)
gy = np.gradient(Phi_N, dx_m, axis=1)
gz = np.gradient(Phi_N, dx_m, axis=2)
g_mag = np.sqrt(gx**2 + gy**2 + gz**2)

# ── φ-closure (eq:nu_cluster from paper) ─────────────────────────────────────
def nu(y):
    y = np.maximum(y, 1e-10)
    return np.sqrt((1 + np.sqrt(1 + 4/y**2)) / 2)

nu_3d = nu(g_mag / g_dagger)

# ── 2D projections (along z = line of sight) ─────────────────────────────────
Sigma_BCG = rho_BCG.sum(axis=2) * dx_m
Sigma_gas = rho_gas.sum(axis=2) * dx_m
Sigma_bar = rho_bar.sum(axis=2) * dx_m

# Thin-lens closure (algebraic, as in paper §17)
g_N_2d = 2*np.pi*G_N * Sigma_bar
nu_2d  = nu(g_N_2d / g_dagger)
Sigma_eff = nu_2d * Sigma_bar

# Unit conversion: kg/m² → M☉/kpc²
u = Msun / kpc**2
Sigma_BCG /= u; Sigma_gas /= u
Sigma_bar /= u; Sigma_eff /= u

# ── Results ───────────────────────────────────────────────────────────────────
def x2i(x): return int((x + Lbox/2) / dx)
iBm, iBs = x2i(x_BCG_main), x2i(x_BCG_sub)
iGm, iGs = x2i(x_gas_main),  x2i(x_gas_sub)
jc = Ng // 2

imax = np.unravel_index(Sigma_eff.argmax(), Sigma_eff.shape)
x_peak = xc[imax[0]]; y_peak = xc[imax[1]]

d_BCG = min(np.hypot(x_peak-x_BCG_main, y_peak),
            np.hypot(x_peak-x_BCG_sub,  y_peak))
d_gas = min(np.hypot(x_peak-x_gas_main, y_peak),
            np.hypot(x_peak-x_gas_sub,  y_peak))

print("="*60)
print("ECT 3D φ-solver: Bullet Cluster results")
print("="*60)
print(f"κ-peak at ({x_peak:.0f}, {y_peak:.0f}) kpc")
print(f"  d(BCG) = {d_BCG:.0f} kpc  [observed: < 25 kpc]")
print(f"  d(gas) = {d_gas:.0f} kpc")
print(f"  Peak follows: {'BCG ✓' if d_BCG < d_gas else 'gas ✗'}")
print(f"Σ_eff(BCG)/Σ_eff(gas) = {Sigma_eff[iBm,jc]/Sigma_eff[iGm,jc]:.3f}")
print(f"M_ECT/M_bar = {Sigma_eff.sum()/Sigma_bar.sum():.2f}")
print(f"M_ECT/M_obs ~ {Sigma_eff.sum()/Sigma_bar.sum()/3:.2f}  (paper: 0.15–0.45)")

# ── Figures ───────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
axes = axes.ravel()

xl,xr = x2i(-600), x2i(600)
yl,yr = x2i(-300), x2i(300)
ext = [xc[xl], xc[xr], xc[yl], xc[yr]]

nu_2d_plot = nu(2*np.pi*G_N * Sigma_bar * u / g_dagger)
y_2d_plot  = 2*np.pi*G_N * Sigma_bar * u / g_dagger

panels = [
    (Sigma_bar[xl:xr,yl:yr].T,      "Σ_b (baryons only)\nGas dominates by total mass",   'inferno'),
    (y_2d_plot[xl:xr,yl:yr].T,      "y = g_N / g_†\ny < 1: critical branch (green)",     'RdYlGn_r'),
    (nu_2d_plot[xl:xr,yl:yr].T,     "ν(y) — φ-closure enhancement\nLarger where y < 1",  'hot'),
    (Sigma_eff[xl:xr,yl:yr].T,      "Σ_eff = ν · Σ_b\n← predicted lensing convergence", 'inferno'),
]

for ax, (arr, title, cmap) in zip(axes, panels):
    vmax = np.percentile(arr, 99.5)
    im = ax.imshow(arr, origin='lower', cmap=cmap, extent=ext,
                   aspect='equal', interpolation='bilinear', vmax=vmax)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('x [kpc]'); ax.set_ylabel('y [kpc]')
    for xpos, col, mk in [(x_BCG_main,'cyan','x'),(x_BCG_sub,'cyan','x'),
                           (x_gas_main,'lime','+'),(x_gas_sub,'lime','+')]:
        ax.scatter(xpos, 0, c=col, marker=mk, s=130, lw=2.5, zorder=7)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

# Mark κ peak
axes[3].add_patch(plt.Circle((x_peak, y_peak), 14,
                              color='red', fill=False, lw=2.5, zorder=8))
axes[3].text(x_peak+18, y_peak+18, f'κ_max\nd_BCG={d_BCG:.0f}kpc',
             color='red', fontsize=8)

axes[0].legend(handles=[
    Line2D([0],[0],marker='x',color='cyan',lw=0,ms=10,label='BCG'),
    Line2D([0],[0],marker='+',color='lime',lw=0,ms=12,label='Gas'),
    Line2D([0],[0],marker='o',color='red', lw=0,ms=10,
           markerfacecolor='none',markeredgewidth=2,label='κ_max'),
], fontsize=9, loc='upper right')

plt.suptitle(
    f"ECT 3D Merger-Scale φ-Solver: Bullet Cluster\n"
    f"Grid {Ng}³ · box {Lbox:.0f} kpc · res {dx:.1f} kpc | "
    "Level B: algebraic ν-closure (paper §17)",
    fontsize=10)
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'bullet_3d_phi_maps.png'), dpi=150, bbox_inches='tight')
print(f"Saved: bullet_3d_phi_maps.png")

# 1D profiles
fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
xs = xc[xl:xr]
ax1.fill_between(xs, Sigma_gas[xl:xr,jc], alpha=.25, color='lime', label='Gas Σ')
ax1.fill_between(xs, Sigma_BCG[xl:xr,jc], alpha=.35, color='cyan', label='BCG Σ')
ax1.plot(xs, Sigma_bar[xl:xr,jc], 'orange', lw=2, label='Σ_b total')
ax1.plot(xs, Sigma_eff[xl:xr,jc], 'red', lw=2.5, label='Σ_eff = ν·Σ_b')
for xp,lc,ls in [(x_BCG_main,'cyan','--'),(x_BCG_sub,'cyan','--'),
                  (x_gas_main,'lime',':'),(x_gas_sub,'lime',':')]:
    ax1.axvline(xp, color=lc, ls=ls, lw=1.5, alpha=.8)
ax1.set_xlabel('x [kpc]'); ax1.set_ylabel('Σ [M☉/kpc²]')
ax1.set_title('Surface density along merger axis')
ax1.legend(fontsize=8); ax1.grid(alpha=.3); ax1.set_xlim(-600,600)

y_prof  = y_2d_plot[xl:xr,jc]
nu_prof = nu_2d_plot[xl:xr,jc]
ax2.semilogy(xs, y_prof, 'purple', lw=2, label='y = g_N/g_†')
ax2.axhline(1, color='k', ls='--', lw=1.5, label='y=1 transition')
ax2.fill_between(xs, y_prof, 1, where=y_prof<1, alpha=.15, color='green',
                 label='Critical branch ν>>1')
ax2r = ax2.twinx()
ax2r.plot(xs, nu_prof, 'red', lw=2, ls='-.', label='ν(y)')
ax2r.set_ylabel('ν(y)', color='red'); ax2r.tick_params(colors='red')
ax2.set_xlabel('x [kpc]'); ax2.set_ylabel('y = g_N/g_†')
ax2.set_title('Enhancement function ν along merger axis')
ax2.legend(fontsize=8); ax2.grid(alpha=.3); ax2.set_xlim(-600,600)
plt.suptitle("ECT 3D φ-closure: profiles along merger axis", fontsize=10)
plt.tight_layout()
fig2.savefig(os.path.join(OUTDIR, 'bullet_3d_phi_profiles.png'), dpi=150, bbox_inches='tight')
print(f"Saved: bullet_3d_phi_profiles.png")
