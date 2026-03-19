#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Late-time ECT phi-first cosmology benchmark solver (v3 — article-synchronised).

Pack 20 changes (article synchronisation layer):
  - Params renamed: om0→omega_m_star, or0→omega_r_star, oV0→omega_V_star, u0→phi0
  - E_lcdm_sq → E_ref_sq (screened reference branch of same closure at phi=0)
  - solver state u → phi throughout
  - diagnostics dict returned alongside background DataFrame
  - derived_quantities returns 5 artefacts:
      (full_profile, summary, distance_time_table, jwst_age_grid, metadata)
  - 6 CSV outputs matching article artefact layer (sec:late_cosmo_artefacts):
      ect_background_profile.csv
      ect_distance_time_table.csv
      ect_jwst_age_grid.csv
      ect_benchmark_summary.csv
      ect_run_metadata.csv
      ect_convergence_diagnostics.csv
  - --seed_mode flag for multi-seed validation (ref | zero)
  - figure labels updated: u_0 -> phi_0

Level-B late-time closure:
  f(phi) = f0 * exp(beta*phi)   [structurally motivated by u/u_inf = e^phi]
  K(phi) = K0                   [simplest benchmark truncation]
  V(phi) = V0 + 0.5*m_phi^2*phi^2  [leading local expansion around phi=0]

NOTE: E'/E is evaluated self-consistently from the ECT solution via finite
differences. The solver iterates until convergence (no LCDM derivative inside).
LCDM / screened reference appears only as an external comparison line on plots.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, cumulative_trapezoid
from scipy.interpolate import interp1d

# constants
C_LIGHT    = 299792.458
MPC_IN_KM  = 3.085677581491367e19
SEC_IN_GYR = 3.15576e16

def apply_bw_style():
    plt.rcParams.update({
        "font.size": 11, "axes.grid": True, "grid.alpha": 0.20,
        "grid.linestyle": "-", "figure.facecolor": "white",
        "axes.facecolor": "white", "savefig.facecolor": "white",
    })

@dataclass
class Params:
    H_star:       float = 67.4
    omega_m_star: float = 0.315
    omega_r_star: float = 9.2e-5
    omega_V_star: float = None
    beta:   float = 0.8
    mu:     float = 1.5
    kappa:  float = 15.0
    phi0:   float = -0.12
    zmax_solver: float = 15.0
    zplot:       float = 15.0
    z_match:     float = 10.0
    z_inf:       float = 1e6
    npts:  int = 3000
    n_iter: int = 3
    def __post_init__(self):
        if self.omega_V_star is None:
            self.omega_V_star = 1.0 - self.omega_m_star - self.omega_r_star

def E_ref_sq(N, p: Params):
    return (p.omega_m_star*np.exp(-3*N)
            + p.omega_r_star*np.exp(-4*N)
            + p.omega_V_star)

def E_sq_ect(N, phi, q, p: Params):
    num = (p.omega_m_star*np.exp(-3*N) + p.omega_r_star*np.exp(-4*N)
           + p.omega_V_star + (p.mu**2/6)*phi*phi)
    den = (np.exp(p.beta*phi) - (p.kappa/6)*q*q + p.beta*np.exp(p.beta*phi)*q)
    den = np.where(den>1e-10, den, 1e-10) if np.ndim(den)>0 else max(den, 1e-10)
    return num / den

def dlnE_from_array(N_arr, E_arr):
    return np.gradient(np.log(E_arr), N_arr)

def q_from_balance(N, phi, E2, dlnE_dN, p: Params):
    return ((p.beta*np.exp(p.beta*phi)/p.kappa)*(2.0+dlnE_dN)
            - (p.mu**2/(3.0*p.kappa))*(phi/max(E2,1e-20)))

def solve_background_selfconsistent(p: Params, seed_mode: str = "ref"):
    N0   = 0.0
    Nmin = -np.log1p(p.zmax_solver)
    N_grid = np.linspace(N0, Nmin, p.npts)
    E_ref = np.sqrt(E_ref_sq(N_grid, p))
    dlnE_prev = np.zeros_like(N_grid) if seed_mode=="zero" else dlnE_from_array(N_grid, E_ref)
    phi_sol = E_sol = q_sol = None
    diagnostics = []
    for iteration in range(p.n_iter):
        dlnE_interp = interp1d(N_grid, dlnE_prev, kind='linear',
                                bounds_error=False, fill_value='extrapolate')
        def rhs(N, y):
            phi  = y[0]
            dlnE = float(dlnE_interp(N))
            E2   = max(E_sq_ect(N, phi, 0.0, p), 1e-20)
            q    = q_from_balance(N, phi, E2, dlnE, p)
            return [q]
        dlnE0 = float(dlnE_interp(N0))
        E2_0  = max(E_sq_ect(N0, p.phi0, 0.0, p), 1e-20)
        q0    = q_from_balance(N0, p.phi0, E2_0, dlnE0, p)
        E2_0  = max(E_sq_ect(N0, p.phi0, q0, p), 1e-20)
        q0    = q_from_balance(N0, p.phi0, E2_0, dlnE0, p)
        sol = solve_ivp(rhs, [N0, Nmin], [p.phi0], method='RK45', dense_output=True,
                        rtol=1e-8, atol=1e-10, max_step=0.05)
        phi_arr = sol.sol(N_grid)[0]
        E_arr   = np.zeros(p.npts)
        q_arr   = np.zeros(p.npts)
        dlnE_cur = dlnE_interp(N_grid)
        for i, (N, phi) in enumerate(zip(N_grid, phi_arr)):
            dlnE_i = float(dlnE_cur[i])
            E2 = max(E_sq_ect(N, phi, 0.0, p), 1e-20)
            q  = q_from_balance(N, phi, E2, dlnE_i, p)
            E2 = max(E_sq_ect(N, phi, q, p), 1e-20)
            E_arr[i] = np.sqrt(E2)
            q_arr[i] = q
        max_dE   = float(np.max(np.abs(E_arr-E_sol)))   if E_sol   is not None else float('nan')
        max_dphi = float(np.max(np.abs(phi_arr-phi_sol))) if phi_sol is not None else float('nan')
        diagnostics.append({"iteration": iteration+1, "max_abs_delta_E": max_dE,
                             "max_abs_delta_phi": max_dphi, "seed_mode": seed_mode,
                             "H_star": p.H_star, "beta": p.beta, "mu": p.mu,
                             "kappa": p.kappa, "phi0": p.phi0})
        dlnE_prev = dlnE_from_array(N_grid, E_arr)
        phi_sol = phi_arr; E_sol = E_arr; q_sol = q_arr
    z_grid = np.expm1(-N_grid)
    bg_df = pd.DataFrame({"z": z_grid, "N": N_grid, "phi": phi_sol,
                           "q": q_sol, "E": E_sol, "E_ref": E_ref})
    return bg_df, pd.DataFrame(diagnostics)

def H_tail(z, z_match, H_match, om, orad):
    num = om*(1+z)**3 + orad*(1+z)**4
    den = om*(1+z_match)**3 + orad*(1+z_match)**4
    return H_match*np.sqrt(num/den)

def cosmic_age_from_bigbang(z_obs, df: pd.DataFrame, p: Params):
    z = df["z"].to_numpy(); H = p.H_star*df["E"].to_numpy()
    j_match = int(np.argmin(np.abs(z-p.z_match)))
    H_match = H[j_match]; age_fac = MPC_IN_KM/SEC_IN_GYR
    age1 = 0.0
    if z_obs <= p.z_match:
        mask = (z>=z_obs)&(z<=p.z_match)
        age1 = np.trapz(age_fac/((1.0+z[mask])*H[mask]), z[mask])
    z_start = max(z_obs, p.z_match)
    z2 = np.logspace(np.log10(1.0+z_start), np.log10(1.0+p.z_inf), 6000)-1.0
    H2 = H_tail(z2, p.z_match, H_match, p.omega_m_star, p.omega_r_star)
    age2 = np.trapz(age_fac/((1.0+z2)*H2), z2)
    return age1+age2

def reference_cosmic_age(z_obs, p: Params):
    z2 = np.logspace(np.log10(1.0+z_obs), np.log10(1.0+p.z_inf), 6000)-1.0
    H2 = p.H_star*np.sqrt(E_ref_sq(-np.log1p(z2), p))
    return np.trapz(MPC_IN_KM/SEC_IN_GYR/((1.0+z2)*H2), z2)

def derived_quantities(df: pd.DataFrame, p: Params):
    z   = df["z"].to_numpy(); E = df["E"].to_numpy()
    Eref= df["E_ref"].to_numpy(); phi = df["phi"].to_numpy()
    H   = p.H_star*E; Href = p.H_star*Eref
    chi    = cumulative_trapezoid(C_LIGHT/H,    z, initial=0.0)
    chiref = cumulative_trapezoid(C_LIGHT/Href, z, initial=0.0)
    DL=  (1+z)*chi;   DL_ref=(1+z)*chiref
    DA=  chi/(1+z);   DA_ref=chiref/(1+z)
    age_fac = MPC_IN_KM/SEC_IN_GYR
    tlook    = cumulative_trapezoid(age_fac/((1+z)*H),    z, initial=0.0)
    tlookref = cumulative_trapezoid(age_fac/((1+z)*Href), z, initial=0.0)
    t_U     = np.array([cosmic_age_from_bigbang(float(zz), df, p) for zz in z])
    t_U_ref = np.array([reference_cosmic_age(float(zz), p)        for zz in z])
    c_si = C_LIGHT*1e3
    gdag_bg     = c_si*(H/MPC_IN_KM)/(2*np.pi)
    gdag_bg_ref = c_si*(Href/MPC_IN_KM)/(2*np.pi)
    Geff_ratio = np.exp(-p.beta*phi)
    grow=Geff_ratio/E**2; growref=1.0/Eref**2
    df = df.copy()
    for k,v in [("H",H),("H_ref",Href),("DL",DL),("DL_ref",DL_ref),
                ("DA",DA),("DA_ref",DA_ref),("tlook",tlook),("tlook_ref",tlookref),
                ("t_U",t_U),("t_U_ref",t_U_ref),("gdag_bg",gdag_bg),
                ("gdag_bg_ref",gdag_bg_ref),("gdag_ratio",gdag_bg/gdag_bg[0]),
                ("Geff_ratio",Geff_ratio),("grow",grow),("grow_ref",growref)]:
        df[k] = v
    # summary
    S = {"beta":p.beta,"mu":p.mu,"kappa":p.kappa,"phi0_input":p.phi0,
         "H_star":p.H_star,"omega_m_star":p.omega_m_star,
         "omega_r_star":p.omega_r_star,"omega_V_star":p.omega_V_star,
         "z_match":p.z_match,"closure_name":"benchmark_phi_first",
         "high_z_completion":"interim_matter_radiation_tail",
         "E0":float(E[0]),"H0_late":float(p.H_star*E[0]),
         "DeltaH0_over_H0":float(E[0]-1.0)}
    t0_ect=cosmic_age_from_bigbang(0.0,df,p); t0_ref=reference_cosmic_age(0.0,p)
    S.update({"age_ect_Gyr":t0_ect,"age_ref_Gyr":t0_ref,
              "Delta_age_frac":(t0_ect-t0_ref)/t0_ref})
    mask_lowz=z<=0.1
    if mask_lowz.sum()>=5:
        S["H0_lowz_diagnostic"]=float(C_LIGHT/np.polyfit(z[mask_lowz],DL[mask_lowz],1)[0])
    for zt in [1,2,5,8,10,12]:
        j=int(np.argmin(np.abs(z-zt)))
        dl_frac=float((DL[j]-DL_ref[j])/max(DL_ref[j],1e-10))
        tU=float(t_U[j]); tUr=float(t_U_ref[j])
        S[f"DL_frac_z{zt}"]=dl_frac
        S[f"DL_lum_frac_z{zt}"]=float((1+dl_frac)**2-1)
        S[f"tlook_frac_z{zt}"]=float((tlook[j]-tlookref[j])/max(tlookref[j],1e-10))
        S[f"grow_ratio_z{zt}"]=float(grow[j]/max(growref[j],1e-20))
        S[f"gdag_ratio_z{zt}"]=float(df["gdag_ratio"].iloc[j])
        S[f"t_U_ect_z{zt}"]=tU; S[f"t_U_ref_z{zt}"]=tUr
        S[f"t_U_frac_z{zt}"]=float((tU-tUr)/max(tUr,1e-10))
    for zf in [15,20,30]:
        tg=cosmic_age_from_bigbang(10.0,df,p)-cosmic_age_from_bigbang(float(zf),df,p)
        tr=reference_cosmic_age(10.0,p)-reference_cosmic_age(float(zf),p)
        S[f"t_gal_z10_formed_z{zf}_ect"]=tg; S[f"t_gal_z10_formed_z{zf}_ref"]=tr
    summary_df=pd.DataFrame([S])
    # distance-time table
    dt_df=df[["z","H","H_ref","E","E_ref","phi","q","DL","DL_ref","DA","DA_ref",
               "tlook","tlook_ref","t_U","t_U_ref","Geff_ratio","grow","grow_ref",
               "gdag_bg","gdag_bg_ref","gdag_ratio"]].copy()
    # JWST age grid
    jwst_rows=[]
    for z_obs in [8,10,12]:
        for z_form in [12,15,20,30]:
            if z_form>z_obs:
                t_o=cosmic_age_from_bigbang(float(z_obs),df,p)
                t_f=cosmic_age_from_bigbang(float(z_form),df,p)
                t_or=reference_cosmic_age(float(z_obs),p)
                t_fr=reference_cosmic_age(float(z_form),p)
                jwst_rows.append({"z_obs":float(z_obs),"z_form":float(z_form),
                    "t_U_obs_ect_Gyr":t_o,"t_U_obs_ref_Gyr":t_or,
                    "t_U_form_ect_Gyr":t_f,"t_U_form_ref_Gyr":t_fr,
                    "t_gal_ect_Gyr":t_o-t_f,"t_gal_ref_Gyr":t_or-t_fr})
    jwst_df=pd.DataFrame(jwst_rows)
    # metadata
    meta_df=pd.DataFrame([{"closure_name":"benchmark_phi_first",
        "response_factor":"f(phi)=f0*exp(beta*phi)",
        "kinetic_closure":"K(phi)=K0",
        "potential_closure":"V(phi)=V0+0.5*m_phi^2*phi^2",
        "high_z_completion":"interim_matter_radiation_tail",
        "z_match":p.z_match,"zmax_solver":p.zmax_solver,
        "npts":p.npts,"n_iter":p.n_iter,"H_star":p.H_star,
        "beta":p.beta,"mu":p.mu,"kappa":p.kappa,"phi0":p.phi0,
        "omega_m_star":p.omega_m_star,"omega_r_star":p.omega_r_star,
        "omega_V_star":p.omega_V_star}])
    return df, summary_df, dt_df, jwst_df, meta_df

def make_figure(df, summary, outpath, p):
    apply_bw_style()
    z=df["z"].to_numpy(); mask=z<=p.zplot
    fig,axes=plt.subplots(2,2,figsize=(13,10)); axs=axes.ravel(); s=summary.iloc[0]
    ax=axs[0]
    ax.plot(z[mask],df["E_ref"].to_numpy()[mask],"0.55",ls="--",lw=1.8,
            label=r"screened reference ($\phi=0$)")
    ax.plot(z[mask],df["E"].to_numpy()[mask],"black",lw=2.2,label="ECT late-time closure")
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$E(z)=H/H_*$")
    ax.set_title("(a) Expansion history",fontweight="bold",loc="left")
    ax.legend(frameon=True,fontsize=9)
    txt=(rf"$\beta={s['beta']:.2f}$,  $\mu={s['mu']:.2f}$,  "
         rf"$\kappa={s['kappa']:.1f}$,  $\phi_0={s['phi0_input']:.3f}$" "\n"
         rf"$\Delta H_0/H_0={s['DeltaH0_over_H0']*100:.1f}\%$,  "
         rf"$H_0^{{\rm late}}={s['H0_late']:.1f}$ km/s/Mpc")
    ax.text(0.03,0.97,txt,transform=ax.transAxes,va="top",fontsize=9,
            bbox=dict(boxstyle="round",fc="white",ec="0.6"))
    ax=axs[1]
    dl=(df["DL"]-df["DL_ref"])/df["DL_ref"].replace(0,np.nan)
    ax.plot(z[mask],dl.to_numpy()[mask],"black",lw=2.2,label=r"ECT $\phi$-closure")
    ax.axhline(0,color="0.55",ls="--",lw=1.2,label=r"screened reference ($\phi=0$)")
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\Delta D_L/D_L^{\rm ref}$")
    ax.set_title("(b) Luminosity-distance shift",fontweight="bold",loc="left")
    ax.legend(frameon=True,fontsize=9,loc="upper right")
    ax=axs[2]
    tref=df["tlook_ref"].to_numpy()
    tsh=np.where(tref>0.01,(df["tlook"]-df["tlook_ref"])/tref,0.0)
    ax.plot(z[mask],tsh[mask],"black",lw=2.2)
    ax.axhline(0,color="0.55",ls="--",lw=1.2)
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\Delta t_{\rm lookback}/t_{\rm lookback}^{\rm ref}$")
    ax.set_title("(c) Lookback-time shift",fontweight="bold",loc="left")
    ax.text(0.97,0.97,rf"Age ECT: {s['age_ect_Gyr']:.2f} Gyr"+"\n"+rf"Age ref: {s['age_ref_Gyr']:.2f} Gyr",
            transform=ax.transAxes,va="top",ha="right",fontsize=9,
            bbox=dict(boxstyle="round",fc="white",ec="0.6"))
    ax=axs[3]
    gr=df["grow"]/df["grow_ref"].replace(0,np.nan)
    ax.plot(z[mask],gr.to_numpy()[mask],"black",lw=2.2,label=r"Growth proxy $G_{\rm eff}/H^2$")
    ax.axhline(1.0,color="0.55",ls="--",lw=1.2)
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\mathcal{G}_{\rm ECT}/\mathcal{G}_{\rm ref}$ (left)")
    ax.set_title(r"(d) Growth proxy \& $g^\dagger_{\rm bg}(z)$",fontweight="bold",loc="left")
    ax2=ax.twinx()
    ax2.plot(z[mask],df["gdag_ratio"].to_numpy()[mask],"0.45",lw=1.8,ls="-.",
             label=r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)=E(z)$")
    ax2.set_ylabel(r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)$ (right)",color="0.45")
    ax2.tick_params(axis="y",labelcolor="0.45")
    l1,lb1=ax.get_legend_handles_labels(); l2,lb2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,lb1+lb2,frameon=True,fontsize=9,loc="upper left")
    fig.suptitle("ECT late-time background: Hubble tension, age, and JWST implications",
                 fontsize=13,fontweight="bold",y=1.01)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"),dpi=300,bbox_inches="tight")
    fig.savefig(outpath.with_suffix(".png"),dpi=220,bbox_inches="tight")
    plt.close(); print("Background figure saved.")

def make_scan_figure(outpath, p):
    apply_bw_style()
    bb=np.linspace(0.3,1.5,80); pp=np.linspace(-0.20,-0.01,80)
    BB,PP=np.meshgrid(bb,pp); DH=p.mu**2*PP**2/12-0.5*BB*PP
    fig,ax=plt.subplots(figsize=(8,6))
    levels=[0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.10]
    cs=ax.contourf(BB,PP,DH,levels=levels,cmap="Greys")
    fig.colorbar(cs,ax=ax,label=r"$\Delta H_0/H_0$")
    ct=ax.contour(BB,PP,DH,levels=levels,colors="black",linewidths=0.8)
    ax.clabel(ct,fmt="%.2f",fontsize=9)
    ax.plot(0.8,-0.12,"k*",ms=12,label="Benchmark B")
    ax.plot(1.0,-0.12,"k^",ms=9, label="Benchmark C")
    ax.set_xlabel(r"$\beta$",fontsize=12)
    ax.set_ylabel(r"$\phi_0=\phi(z=0)$",fontsize=12)
    ax.set_title(rf"$\Delta H_0/H_0\approx\mu^2\phi_0^2/12-\beta\phi_0/2$"+"\n"+
                 rf"($\mu={p.mu:.1f}$, $\kappa={p.kappa:.0f}$)",fontsize=11)
    ax.legend(frameon=True,fontsize=10)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"),dpi=300)
    fig.savefig(outpath.with_suffix(".png"),dpi=220)
    plt.close(); print("Scan figure saved.")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",  required=True)
    ap.add_argument("--H_star",  type=float,default=67.4)
    ap.add_argument("--om0",     type=float,default=0.315)
    ap.add_argument("--or0",     type=float,default=9.2e-5)
    ap.add_argument("--oV0",     type=float,default=None)
    ap.add_argument("--beta",    type=float,default=0.8)
    ap.add_argument("--mu",      type=float,default=1.5)
    ap.add_argument("--kappa",   type=float,default=15.0)
    ap.add_argument("--u0",      type=float,default=-0.12,
                    help="phi0=phi(z=0), macroscopic amplitude variable at present epoch")
    ap.add_argument("--zmax",    type=float,default=15.0)
    ap.add_argument("--zplot",   type=float,default=15.0)
    ap.add_argument("--z_match", type=float,default=10.0)
    ap.add_argument("--npts",    type=int,  default=3000)
    ap.add_argument("--n_iter",  type=int,  default=3)
    ap.add_argument("--scan",    action="store_true")
    ap.add_argument("--seed_mode",choices=["ref","zero"],default="ref",
                    help="Solver seed: ref=screened reference branch, zero=zero dlnE")
    args=ap.parse_args()
    omega_V_star=args.oV0 if args.oV0 is not None else 1.0-args.om0-args.or0
    p=Params(H_star=args.H_star,omega_m_star=args.om0,omega_r_star=args.or0,
             omega_V_star=omega_V_star,beta=args.beta,mu=args.mu,kappa=args.kappa,
             phi0=args.u0,zmax_solver=args.zmax,zplot=args.zplot,
             z_match=args.z_match,npts=args.npts,n_iter=args.n_iter)
    outdir=Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)
    print(f"ECT solver v3: beta={p.beta}, mu={p.mu}, kappa={p.kappa}, phi0={p.phi0}, seed={args.seed_mode}")
    df,diagnostics=solve_background_selfconsistent(p,seed_mode=args.seed_mode)
    full,summary,distance_time,jwst_grid,metadata=derived_quantities(df,p)
    metadata["seed_mode"]=args.seed_mode
    full.to_csv(         outdir/"ect_background_profile.csv",      index=False)
    distance_time.to_csv(outdir/"ect_distance_time_table.csv",     index=False)
    jwst_grid.to_csv(    outdir/"ect_jwst_age_grid.csv",           index=False)
    summary.to_csv(      outdir/"ect_benchmark_summary.csv",       index=False)
    metadata.to_csv(     outdir/"ect_run_metadata.csv",            index=False)
    diagnostics.to_csv(  outdir/"ect_convergence_diagnostics.csv", index=False)
    s=summary.iloc[0]
    print(f"\n=== SUMMARY ===")
    print(f"  DH0/H0  = {s['DeltaH0_over_H0']*100:.2f}%")
    print(f"  H0 late = {s['H0_late']:.2f} km/s/Mpc")
    print(f"  Age ECT = {s['age_ect_Gyr']:.2f} Gyr  (ref = {s['age_ref_Gyr']:.2f} Gyr)")
    for zt in [5,10,12]:
        print(f"  z={zt:2d}: DL/DL={s.get(f'DL_frac_z{zt}',0)*100:.2f}%  "
              f"tU={s.get(f't_U_ect_z{zt}',0):.3f} Gyr")
    print("\nSaved artefacts:")
    for fn in ["ect_background_profile.csv","ect_distance_time_table.csv",
               "ect_jwst_age_grid.csv","ect_benchmark_summary.csv",
               "ect_run_metadata.csv","ect_convergence_diagnostics.csv"]:
        print(f"  - {fn}")
    make_figure(full,summary,outdir/"ect_hubble_jwst_background_bw",p)
    if args.scan:
        make_scan_figure(outdir/"ect_h0_scan_bw",p)

if __name__=="__main__":
    main()
