#!/usr/bin/env python3
"""
ECT article figures (pack M): all 5 figures generated from v4 solver.
Self-contained — no external CSVs needed.

Figures generated:
  1. ect_hubble_jwst_background_bw     — benchmark control figure
  2. ect_condensate_param_scan_bw      — derived-parent param scan + B/H/A points
  3. ect_derived_parent_comparison_bw  — benchmark vs derived-parent (4 panels)
  4. ect_universe_condensate_evolution_bw — conceptual timeline
  5. ect_jwst_anchor_budget_bw         — JWST anchor age+maturity budget
"""
import sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
exec(open(Path(__file__).parent / 'ect_hubble_jwst_background.py').read().split('def main():')[0])

OUTDIR = Path(__file__).parent.parent / 'figures'
OUTDIR.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.18,
                     "figure.facecolor": "white", "axes.facecolor": "white",
                     "savefig.facecolor": "white"})

def savefig(fig, stem):
    p = OUTDIR / stem
    fig.tight_layout()
    fig.savefig(p.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(p.with_suffix('.png'), dpi=220, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {stem}.pdf/png")

def run_bg(p):
    df, _ = solve_background_selfconsistent(p, seed_mode="ref")
    full, summ, *_ = derived_quantities(df, p)
    return full, summ.iloc[0]

def linear_growth(full_df, p, npts=1200):
    """Integrate D'' + (2+H'/H)*D' - 3/2*Om(N)*Geff(N)*D = 0"""
    z_bg  = full_df["z"].to_numpy(); N_bg  = -np.log1p(z_bg)
    E_bg  = full_df["E"].to_numpy(); phi_bg= full_df["phi"].to_numpy()
    E_itp   = interp1d(N_bg, E_bg,   bounds_error=False, fill_value="extrapolate")
    phi_itp = interp1d(N_bg, phi_bg, bounds_error=False, fill_value="extrapolate")
    dlnE_arr= dlnE_from_array(N_bg, E_bg)
    dlnE_itp= interp1d(N_bg, dlnE_arr, bounds_error=False, fill_value="extrapolate")

    def rhs_ref(N, y):
        E2 = float(E_ref_sq(N, p)); dlnE = float(dlnE_itp(N))
        Om = p.omega_m_star*np.exp(-3*N)/max(E2,1e-30)
        return [y[1], -(2+dlnE)*y[1] + 1.5*Om*y[0]]

    def rhs_ect(N, y):
        E2 = float(E_itp(N))**2; dlnE = float(dlnE_itp(N))
        phi = float(phi_itp(N)); Geff = np.exp(-p.beta*phi)
        Om  = p.omega_m_star*np.exp(-3*N)/max(E2,1e-30)
        return [y[1], -(2+dlnE)*y[1] + 1.5*Om*Geff*y[0]]

    N_ini = -np.log1p(500.0); kw = dict(method="RK45", dense_output=True, rtol=1e-9, atol=1e-11, max_step=0.02)
    sol_r = solve_ivp(rhs_ref, [N_ini, 0.0], [np.exp(N_ini), 1.0], **kw)
    sol_e = solve_ivp(rhs_ect, [N_ini, 0.0], [np.exp(N_ini), 1.0], **kw)
    N_grid = np.linspace(N_ini, 0.0, npts)
    D_ref = sol_r.sol(N_grid)[0]; D_ref /= D_ref[-1]
    D_ect = sol_e.sol(N_grid)[0]; D_ect /= D_ect[-1]
    return np.expm1(-N_grid), D_ect/D_ref  # z, D_ect/D_ref

# ════════════════════════════════════════════════════════════════
# FIG 1 — Benchmark control figure (reuse existing solver function)
# ════════════════════════════════════════════════════════════════
print("Fig 1: benchmark control...")
p_bench = Params(closure_mode="benchmark", npts=1000, n_iter=3, zmax_solver=15)
full_b, s_b = run_bg(p_bench)
make_figure(full_b, pd.DataFrame([s_b]), OUTDIR/"ect_hubble_jwst_background_bw", p_bench)
print("  Saved: ect_hubble_jwst_background_bw.pdf/png")

# ════════════════════════════════════════════════════════════════
# FIG 2 — Parameter scan with B/H/A working points
# ════════════════════════════════════════════════════════════════
print("Fig 2: parameter scan...")
omega0_vals = np.array([15., 20., 25., 30., 40., 50.])
phi0_vals   = np.array([-0.15, -0.12, -0.10, -0.08, -0.05])

DH = np.full((len(phi0_vals), len(omega0_vals)), np.nan)
Age= np.full_like(DH, np.nan)
tU10=np.full_like(DH, np.nan)
G10= np.full_like(DH, np.nan)

for i, ph in enumerate(phi0_vals):
    for j, om in enumerate(omega0_vals):
        try:
            p = Params(closure_mode="derived_parent", omega0=float(om), phi0=float(ph),
                       npts=400, n_iter=4, zmax_solver=12)
            df_bg, s = run_bg(p)
            DH[i,j]  = s['DeltaH0_over_H0']*100
            Age[i,j] = s['age_ect_Gyr']
            tU10[i,j]= s.get('t_U_ect_z10', np.nan)
            j10 = abs(df_bg["z"]-10).argmin()
            G10[i,j] = np.exp(-p.beta*df_bg["phi"].iloc[j10])
        except: pass

# Working points
WP = [
    dict(label="B", name="balanced",       omega0=25, phi0=-0.10, mk="o"),
    dict(label="H", name="Hubble-priority", omega0=30, phi0=-0.10, mk="s"),
    dict(label="A", name="age-priority",    omega0=25, phi0=-0.08, mk="^"),
]
om_x = np.arange(len(omega0_vals)); phi_y = np.arange(len(phi0_vals))

panels = [
    (DH,   r"$\Delta H_0/H_0$ [\%]",       "RdYlGn",   -5, 6,   "{:.1f}"),
    (Age,  r"$t_0$ (ECT) [Gyr]",            "RdYlGn",   11.5,14.5,"{:.2f}"),
    (tU10, r"$t_U(z=10)$ [Gyr]",            "RdYlGn",   0.25,0.55,"{:.3f}"),
    (G10,  r"$G_{\rm eff}(z=10)/G_N$",      "Oranges",  1.0, 3.0, "{:.2f}"),
]

fig2, axes2 = plt.subplots(2, 2, figsize=(13, 9))
for ax, (data, title, cmap, vmin, vmax, fmt) in zip(axes2.ravel(), panels):
    im = ax.imshow(data, aspect='auto', origin='lower', cmap=cmap,
                   vmin=vmin, vmax=vmax,
                   extent=[-0.5, len(omega0_vals)-0.5, -0.5, len(phi0_vals)-0.5])
    plt.colorbar(im, ax=ax, shrink=0.9).set_label(title)
    ax.set_xticks(om_x); ax.set_xticklabels([f"{v:.0f}" for v in omega0_vals])
    ax.set_yticks(phi_y); ax.set_yticklabels([f"{v:.2f}" for v in phi0_vals])
    ax.set_xlabel(r"$\omega_0$"); ax.set_ylabel(r"$\phi_0$")
    ax.set_title(title, fontweight="bold", fontsize=10)
    # Annotate cells
    for ii in range(len(phi0_vals)):
        for jj in range(len(omega0_vals)):
            if not np.isnan(data[ii,jj]):
                v = data[ii,jj]; norm = (v-vmin)/(vmax-vmin+1e-9)
                col = "white" if norm > 0.72 else "black"
                ax.text(jj, ii, fmt.format(v), ha='center', va='center', fontsize=7.5, color=col)
    # Corridor boxes (good region)
    good = (DH >= 1.5) & (DH <= 5.0) & (Age >= 12.5) & (tU10 >= 0.33)
    for ii in range(len(phi0_vals)):
        for jj in range(len(omega0_vals)):
            if good[ii, jj]:
                ax.add_patch(plt.Rectangle((jj-0.5,ii-0.5),1,1, fill=False, edgecolor='navy', lw=2.0))
    # Plot B/H/A working points
    for wp in WP:
        ji = np.where(omega0_vals == wp['omega0'])[0]
        pi = np.where(phi0_vals   == wp['phi0'])[0]
        if len(ji) and len(pi):
            ax.plot(ji[0], pi[0], wp['mk'], ms=9, color='darkred', zorder=5)
            ax.text(ji[0]+0.3, pi[0]+0.15, wp['label'], fontsize=9, color='darkred',
                    fontweight='bold', zorder=6)

# Legend
legend_els = [mpatches.Patch(facecolor='none', edgecolor='navy', lw=2, label='Hubble-compatible corridor'),
              plt.Line2D([0],[0],marker='o',color='darkred',ls='none',ms=8,label='B = balanced'),
              plt.Line2D([0],[0],marker='s',color='darkred',ls='none',ms=8,label='H = Hubble-priority'),
              plt.Line2D([0],[0],marker='^',color='darkred',ls='none',ms=8,label='A = age-priority')]
fig2.legend(handles=legend_els, loc='lower center', ncol=4, fontsize=9, bbox_to_anchor=(0.5,-0.01))
fig2.suptitle(r"ECT derived-parent parameter scan: $\beta=0.8$, $\mu=1.5$, "
              r"$A_2=\mu^2/(6\beta^2)$, $A_3=A_4=0$", fontsize=11, fontweight='bold')
savefig(fig2, "ect_condensate_param_scan_bw")

# ════════════════════════════════════════════════════════════════
# FIG 3 — Benchmark vs derived-parent comparison (4 panels)
# ════════════════════════════════════════════════════════════════
print("Fig 3: benchmark vs derived-parent comparison...")
cases = [
    (Params(closure_mode="benchmark",      omega0=15, phi0=-0.12, npts=800, n_iter=3, zmax_solver=15),
     "black",   "-",  "Benchmark", 2.0),
    (Params(closure_mode="derived_parent", omega0=25, phi0=-0.10, npts=800, n_iter=4, zmax_solver=15),
     "#CC4400", "--", "Derived balanced (B)", 1.8),
    (Params(closure_mode="derived_parent", omega0=30, phi0=-0.10, npts=800, n_iter=4, zmax_solver=15),
     "#0055AA", ":", "Derived H-priority (H)", 1.8),
]

fig3, axes3 = plt.subplots(2, 2, figsize=(13, 9))
z_ref_arr = None; D_ref_arr = None

for p, c, ls, lab, lw in cases:
    full, s = run_bg(p)
    z   = full["z"].to_numpy(); mask = z <= 15
    phi = full["phi"].to_numpy(); E = full["E"].to_numpy()
    Geff = np.exp(-p.beta*phi)
    z_gr, D_ratio = linear_growth(full, p)
    mask_gr = z_gr <= 15

    axes3[0,0].plot(z[mask], E[mask],    color=c, ls=ls, lw=lw, label=lab)
    axes3[0,1].plot(z[mask], Geff[mask], color=c, ls=ls, lw=lw, label=lab)
    axes3[1,0].plot(z_gr[mask_gr], D_ratio[mask_gr], color=c, ls=ls, lw=lw, label=lab)
    # Maturity channels
    tff_ratio = np.sqrt(Geff)
    tBH_ratio = Geff
    axes3[1,1].plot(z[mask], tff_ratio[mask], color=c, ls=ls, lw=lw, label=f"{lab} (collapse)")
    axes3[1,1].plot(z[mask], tBH_ratio[mask], color=c, ls="--", lw=lw*0.7, alpha=0.65,
                    label=f"{lab} (BH-like)")

# Reference lines
full0, _ = run_bg(Params(closure_mode="benchmark", npts=500))
z0 = full0["z"].to_numpy(); m0 = z0 <= 15
axes3[0,0].plot(z0[m0], full0["E_ref"].to_numpy()[m0], "0.6", ls=":", lw=1.5, label="Reference (φ=0)")
axes3[0,1].axhline(1.0, color="0.6", ls=":", lw=1.5, label=r"$G_N$ (reference)")
axes3[1,0].axhline(1.0, color="0.6", ls=":", lw=1.5, label="Reference")
axes3[1,1].axhline(1.0, color="0.6", ls=":", lw=1.5)

for ax in axes3.ravel():
    ax.set_xlabel("$z$"); ax.axvline(10, color="0.75", ls="--", lw=0.8)
    ax.grid(True, alpha=0.18); ax.legend(frameon=True, fontsize=7.5)
axes3[0,0].set_ylabel(r"$E(z)=H/H_*$");                   axes3[0,0].set_title("(a) Expansion history", fontweight='bold', loc='left')
axes3[0,1].set_ylabel(r"$G_{\rm eff}/G_N$");               axes3[0,1].set_title("(b) Effective gravity", fontweight='bold', loc='left')
axes3[1,0].set_ylabel(r"$D(z)/D_{\rm ref}(z)$");           axes3[1,0].set_title("(c) Solved linear growth factor", fontweight='bold', loc='left')
axes3[1,1].set_ylabel("relative acceleration factor");     axes3[1,1].set_title("(d) Local maturity-channel acceleration", fontweight='bold', loc='left')
axes3[0,1].set_ylim(0.9, 3.0); axes3[1,0].set_ylim(0.7, 1.5)
for ax in axes3.ravel(): ax.set_xlim(0, 15)
fig3.suptitle("ECT: benchmark control vs derived-parent background\n"
              "The JWST mechanism combines background evolution + local maturity channels, not linear growth alone",
              fontsize=10, fontweight='bold', y=1.02)
savefig(fig3, "ect_derived_parent_comparison_bw")

# ════════════════════════════════════════════════════════════════
# FIG 4 — Conceptual timeline
# ════════════════════════════════════════════════════════════════
print("Fig 4: conceptual evolution timeline...")
fig4, ax = plt.subplots(figsize=(14, 5.5))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

# Epoch separators
for x, lab in [(0.20,"ordering\ntransition"), (0.42,"early\nderived-parent"), (0.70,"structure\nformation")]:
    ax.plot([x,x],[0.04,0.96], ls='--', lw=1.0, color='0.5')

# Main horizontal arrows (condensate and universe tracks)
for y, col in [(0.78,'black'),(0.24,'black')]:
    ax.annotate("", xy=(0.97,y), xytext=(0.03,y),
                arrowprops=dict(arrowstyle="->", lw=1.8, color=col))

ax.text(0.02, 0.84, "Condensate $\\phi(z)$", fontsize=11, fontweight='bold')
ax.text(0.02, 0.30, "Observable Universe", fontsize=11, fontweight='bold')

# Phase labels (top)
phases = [(0.10,"Pre-Lorentzian\nordering regime"),
          (0.31,"Early ECT:\n$G_{\\rm eff}\\gg G_N$"),
          (0.56,"Structure formation:\naccelerated maturity"),
          (0.85,"Late screened:\nbenchmark valid")]
for x, lab in phases:
    ax.text(x, 0.91, lab, ha='center', va='bottom', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.2', fc='#f0f0f0', ec='0.7'))

# Condensate curve: starts large negative, monotonically approaches 0
xs = np.linspace(0.03, 0.96, 400)
phi_curve = -0.22*(1 - 1/(1+np.exp(-18*(xs-0.75))))
phi_norm  = 0.78 + 0.14*phi_curve/0.22  # map to y-coordinates
ax.plot(xs, phi_norm, lw=2.2, color='black')
ax.text(0.33, 0.60, r"$\phi \ll 0$,  $u/u_\infty = e^{\beta\phi} \ll 1$", ha='center', fontsize=9,
        color='black', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='0.7'))
ax.text(0.88, 0.66, r"$\phi \to 0$"+"\n(screened)", ha='center', fontsize=9, color='#333333')

# Universe annotations
ann = [(0.11, 0.17, "Lorentzian branch\nemerges"),
       (0.31, 0.17, r"$G_{\rm eff}(z) > G_N$"+"\naccelerated collapse\n$t_{\\rm ff}\\propto G_{\\rm eff}^{-1/2}$"),
       (0.56, 0.17, "Linear growth alone\nnot sufficient\n(Hubble friction)"),
       (0.56, 0.07, "BH-assisted / compact-core\nmaturity channels strengthened"),
       (0.85, 0.17, "Benchmark truncation\nvalid (screened branch)")]
for x, y, lab in ann:
    ax.text(x, y, lab, ha='center', va='top', fontsize=8.5,
            bbox=dict(boxstyle='round,pad=0.2', fc='#f8f8f8', ec='0.6'))

# Annotate key relations
ax.text(0.50, 0.56, r"$G_{\rm eff}(z) = G_N e^{-\beta\phi(z)}$", ha='center', fontsize=9.5,
        color='#220055', style='italic')

fig4.suptitle("Schematic evolution of the ECT condensate and Universe (present derived-parent picture)",
              fontsize=10, fontweight='bold', y=0.99)
savefig(fig4, "ect_universe_condensate_evolution_bw")

# ════════════════════════════════════════════════════════════════
# FIG 5 — JWST anchor age + maturity budget
# ════════════════════════════════════════════════════════════════
print("Fig 5: JWST anchor budget...")
# Use Hubble-priority point
p_hp = Params(closure_mode="derived_parent", omega0=30, phi0=-0.10,
              npts=800, n_iter=4, zmax_solver=15)
full_hp, s_hp = run_bg(p_hp)
z_gr_hp, D_ratio_hp = linear_growth(full_hp, p_hp)

# JWST anchor cases
anchors = [
    dict(name="JADES-GS-z14-0", z_obs=14.32),
    dict(name="GN-z11",          z_obs=10.60),
    dict(name="mini-quenched\n$z=7.3$", z_obs=7.30),
    dict(name="RUBIES-EGS-QG-1\n$z=4.9$", z_obs=4.90),
]

p_ref = Params(closure_mode="benchmark", beta=0.001, phi0=-0.001, npts=500, n_iter=3)
rows = []
for a in anchors:
    zobs = a['z_obs']
    tU_ect = cosmic_age_from_bigbang(float(zobs), full_hp, p_hp)
    tU_ref = reference_cosmic_age(float(zobs), p_hp)
    R_req = tU_ref / max(tU_ect, 1e-5)
    j = abs(full_hp["z"] - zobs).argmin()
    phi_obs = full_hp["phi"].iloc[j]
    Geff_obs = np.exp(-p_hp.beta * phi_obs)
    # D ratio at z_obs
    j_gr = abs(z_gr_hp - zobs).argmin()
    D_rat_obs = float(D_ratio_hp[j_gr])
    R_gal = D_rat_obs * np.sqrt(Geff_obs)
    R_BH  = D_rat_obs * Geff_obs
    rows.append(dict(name=a['name'], tU_ref=tU_ref, tU_ect=tU_ect,
                     R_req=R_req, R_gal=R_gal, R_BH=R_BH))
    print(f"    {a['name']}: tU_ref={tU_ref:.3f} tU_ect={tU_ect:.3f} R_req={R_req:.3f} R_gal={R_gal:.3f} R_BH={R_BH:.3f}")

fig5, axes5 = plt.subplots(1, 2, figsize=(12, 5.2))

names = [r.replace('\n',' ') for r in [a['name'] for a in anchors]]
x = np.arange(len(rows)); w = 0.38

# Panel (a): ages
ax = axes5[0]
ax.bar(x-w/2, [r['tU_ref'] for r in rows], width=w, color='0.6',  label=r"$t_U^{\rm ref}$ (Λ\rm CDM)")
ax.bar(x+w/2, [r['tU_ect'] for r in rows], width=w, color='black', label=r"$t_U^{\rm ECT}$ (H-priority)")
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8)
ax.set_ylabel("Gyr"); ax.set_title("(a) Age of Universe at observation", fontweight='bold')
ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)

# Panel (b): maturity factors
ax = axes5[1]
ax.bar(x-0.28, [r['R_req'] for r in rows], width=0.24, color='0.35', label=r"$\mathcal{R}_{\rm req}$ (required)")
ax.bar(x,      [r['R_gal'] for r in rows], width=0.24, color='0.60', label=r"$\mathcal{R}_{\rm gal}$ (galaxy assembly)")
ax.bar(x+0.28, [r['R_BH']  for r in rows], width=0.24, color='black', label=r"$\mathcal{R}_{\rm BH}$ (BH-assisted)")
ax.axhline(1.0, color='0.4', ls='--', lw=0.9)
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8)
ax.set_ylabel("maturity factor"); ax.set_title("(b) Required vs achieved maturity factors", fontweight='bold')
ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)
ax.set_ylim(0, max([r['R_BH'] for r in rows])*1.25)

fig5.suptitle("ECT JWST anchor case budget — Hubble-priority working point "
              r"($\omega_0=30$, $\phi_0=-0.10$)",
              fontsize=10, fontweight='bold')
savefig(fig5, "ect_jwst_anchor_budget_bw")

print("\nAll figures saved to:", OUTDIR)
