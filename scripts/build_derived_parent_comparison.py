#!/usr/bin/env python3
import sys, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from pathlib import Path

sys.path.insert(0, '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/scripts')
exec(open('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/scripts/ect_hubble_jwst_background.py'
          ).read().split('def main():')[0])

OUTDIR = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')

plt.rcParams.update({
    'font.family': 'serif', 'font.size': 11,
    'axes.grid': True, 'grid.alpha': 0.18,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
})

def run_bg(p):
    df, _ = solve_background_selfconsistent(p, seed_mode="ref")
    full, summ, *_ = derived_quantities(df, p)
    return full, summ.iloc[0]

def linear_growth(full_df, p, npts=1200):
    z_bg = full_df["z"].to_numpy(); N_bg = -np.log1p(z_bg)
    E_bg = full_df["E"].to_numpy(); phi_bg = full_df["phi"].to_numpy()
    E_itp   = interp1d(N_bg, E_bg,   bounds_error=False, fill_value="extrapolate")
    phi_itp = interp1d(N_bg, phi_bg, bounds_error=False, fill_value="extrapolate")
    dlnE_arr= dlnE_from_array(N_bg, E_bg)
    dlnE_itp= interp1d(N_bg, dlnE_arr, bounds_error=False, fill_value="extrapolate")
    def rhs_ref(N, y):
        E2=float(E_itp(N))**2; dlnE=float(dlnE_itp(N))
        Om=p.omega_m_star*np.exp(-3*N)/max(float(E_ref_sq(N,p)),1e-30)
        return [y[1], -(2+dlnE)*y[1]+1.5*Om*y[0]]
    def rhs_ect(N, y):
        E2=float(E_itp(N))**2; dlnE=float(dlnE_itp(N))
        phi=float(phi_itp(N)); Geff=np.exp(-p.beta*phi)
        Om=p.omega_m_star*np.exp(-3*N)/max(E2,1e-30)
        return [y[1], -(2+dlnE)*y[1]+1.5*Om*Geff*y[0]]
    N_ini=-np.log1p(500.); kw=dict(method="RK45",dense_output=True,rtol=1e-9,atol=1e-11,max_step=0.02)
    sol_r=solve_ivp(rhs_ref,[N_ini,0.],[np.exp(N_ini),1.],**kw)
    sol_e=solve_ivp(rhs_ect,[N_ini,0.],[np.exp(N_ini),1.],**kw)
    Ng=np.linspace(N_ini,0.,npts)
    Dr=sol_r.sol(Ng)[0]; Dr/=Dr[-1]
    De=sol_e.sol(Ng)[0]; De/=De[-1]
    return np.expm1(-Ng), De/Dr

# ── Grayscale styles: solid/dashed/dotted + different gray levels ──────────
# Key rule: distinguish by BOTH linestyle AND shade so no colour needed
CASES = [
    # (Params, gray_shade, linestyle, linewidth, label)
    (Params(closure_mode="benchmark",      omega0=15, phi0=-0.12, npts=800, n_iter=3, zmax_solver=15),
     'black',  '-',  2.2, 'Benchmark'),
    (Params(closure_mode="derived_parent", omega0=25, phi0=-0.10, npts=800, n_iter=4, zmax_solver=15),
     '0.40',   '--', 2.0, 'Derived balanced (B)'),
    (Params(closure_mode="derived_parent", omega0=30, phi0=-0.10, npts=800, n_iter=4, zmax_solver=15),
     '0.65',   ':',  2.2, 'Derived H-priority (H)'),
]

fig, axes = plt.subplots(2, 2, figsize=(13, 9.5))
axes = axes.ravel()
fig.subplots_adjust(hspace=0.38, wspace=0.35)

print("Computing cases...")
for p, gray, ls, lw, lab in CASES:
    full, s = run_bg(p)
    z    = full["z"].to_numpy(); mask = z <= 15
    phi  = full["phi"].to_numpy(); E = full["E"].to_numpy()
    Geff = np.exp(-p.beta * phi)
    z_gr, D_ratio = linear_growth(full, p)
    mg = z_gr <= 15
    tff = np.sqrt(Geff)   # t_ff^ref / t_ff^ECT = sqrt(G_eff/G_N)
    tBH = Geff             # t_BH^ref / t_BH^ECT = G_eff/G_N

    axes[0].plot(z[mask],  E[mask],         color=gray, ls=ls, lw=lw, label=lab)
    axes[1].plot(z[mask],  Geff[mask],      color=gray, ls=ls, lw=lw, label=lab)
    axes[2].plot(z_gr[mg], D_ratio[mg],     color=gray, ls=ls, lw=lw, label=lab)
    # panel (d): two channels per case — collapse (thicker) and BH-like (thinner)
    axes[3].plot(z[mask], tff[mask], color=gray, ls=ls,   lw=lw,     label=f'{lab} (collapse)')
    axes[3].plot(z[mask], tBH[mask], color=gray, ls='--', lw=lw*0.65, label=f'{lab} (BH-like)', alpha=0.80)
    print(f"  {lab}: done")

# Reference lines
full0, _ = run_bg(Params(closure_mode="benchmark", npts=500))
z0 = full0["z"].to_numpy(); m0 = z0 <= 15
axes[0].plot(z0[m0], full0["E_ref"].to_numpy()[m0], color='0.55', ls=':', lw=1.5, label=r'Reference ($\phi=0$)')
axes[1].axhline(1.0,  color='0.55', ls=':', lw=1.5, label=r'$G_N$ (reference)')
axes[2].axhline(1.0,  color='0.55', ls=':', lw=1.5, label='Reference')
axes[3].axhline(1.0,  color='0.55', ls=':', lw=1.0)

# Axis labels & titles
props = [
    (r"$E(z)=H/H_*$",            "(a) Expansion history"),
    (r"$G_{\rm eff}/G_N$",        "(b) Effective gravity"),
    (r"$D(z)/D_{\rm ref}(z)$",    "(c) Solved linear growth factor"),
    ("relative acceleration factor", "(d) Local maturity-channel acceleration"),
]
for ax, (yl, tit) in zip(axes, props):
    ax.set_xlabel("$z$", fontsize=11)
    ax.set_ylabel(yl,    fontsize=11)
    ax.set_title(tit, fontweight='bold', loc='left', fontsize=10.5)
    ax.set_xlim(0, 15)
    ax.axvline(10, color='0.70', ls='--', lw=0.9)

axes[1].set_ylim(0.95, 3.05)
axes[2].set_ylim(0.70, 1.55)

# Legends — use compact custom legends to avoid colour confusion
for ax in axes[:3]:
    ax.legend(frameon=True, fontsize=8.5, edgecolor='0.5')

# Panel (d) legend: group by case, show both channel styles
leg_lines = []
for gray, ls, lw, lab in [('black','–',2.2,'Benchmark'),
                            ('0.40','– –',2.0,'Derived balanced (B)'),
                            ('0.65','···',2.2,'Derived H-priority (H)')]:
    leg_lines += [
        Line2D([0],[0], color=gray, ls='-',  lw=2.0, label=f'{lab} (collapse)'),
        Line2D([0],[0], color=gray, ls='--', lw=1.3, label=f'{lab} (BH-like)', alpha=0.80),
    ]
axes[3].legend(handles=leg_lines, frameon=True, fontsize=7.5, edgecolor='0.5',
               ncol=2, loc='upper left', columnspacing=0.8)

fig.suptitle(
    "ECT: benchmark control vs derived-parent background\n"
    "The JWST mechanism combines background evolution + local maturity channels, not linear growth alone",
    fontsize=11, fontweight='bold', y=1.02)

out = OUTDIR / 'ect_derived_parent_comparison_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
