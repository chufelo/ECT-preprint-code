#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECT late-time cosmology solver (v5 — benchmark + derived-parent modes + linear growth).

Two closure modes are supported:

1. benchmark (--closure_mode benchmark)
   Local screened-branch truncation for backward compatibility,
   current article figures/tables, and robustness comparisons:
       F(phi)     = exp(beta*phi)
       K(phi)     = kappa * (1 + k1*phi + k2*phi^2)
       V(phi)     = Omega_V* + mu^2/6*phi^2 + lambda3/18*phi^3 + lambda4/72*phi^4

2. derived_parent (--closure_mode derived_parent, DEFAULT)
   Full derived condensate-background mode from ordered-branch EFT:
       F(phi)        = exp(beta*phi)
       omega(phi)    = omega0 * exp(2*beta*phi)
       Omega_U(phi)  = Omega_V* + A2*(exp(beta*phi)-1)^2
                                 + A3*(exp(beta*phi)-1)^3
                                 + A4*(exp(beta*phi)-1)^4
   Default A2 = mu^2/(6*beta^2) to match local quadratic benchmark at phi=0.

The benchmark mode is retained as control/comparison/reproduction mode.
The derived_parent mode is the primary physical mode for full condensate
background calculations (phi=(1/beta)*ln(u/u_inf), u=u_inf*exp(beta*phi)).
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

    beta:  float = 0.8
    mu:    float = 1.5

    # benchmark truncation parameters
    kappa:   float = 15.0
    k1:      float = 0.0
    k2:      float = 0.0
    lambda3: float = 0.0
    lambda4: float = 0.0

    # derived-parent parameters
    omega0: float = 15.0
    A2:     float = None   # default: mu^2/(6*beta^2) — matches local benchmark
    A3:     float = 0.0
    A4:     float = 0.0

    phi0:         float = -0.12
    closure_mode: str   = "derived_parent"

    zmax_solver: float = 15.0
    zplot:       float = 15.0
    z_match:     float = 10.0
    z_inf:       float = 1e6
    npts:  int = 3000
    n_iter: int = 4

    def __post_init__(self):
        if self.omega_V_star is None:
            self.omega_V_star = 1.0 - self.omega_m_star - self.omega_r_star
        if self.A2 is None:
            # match local quadratic benchmark: A2*(beta*phi)^2 ~ mu^2/6*phi^2
            self.A2 = self.mu**2 / (6.0 * self.beta**2)
        if self.closure_mode not in {"benchmark", "derived_parent"}:
            raise ValueError(f"Unknown closure_mode: {self.closure_mode!r}")

# ── closure helpers ─────────────────────────────────────────────────────────
def F_response(phi, p: Params):
    """F(phi) = exp(beta*phi)  [structural, both modes]."""
    return np.exp(p.beta * phi)

# -- benchmark kinetic/potential --
def K_closure(phi, p: Params):
    """K(phi) = K0*(1 + k1*phi + k2*phi^2)  [benchmark mode]."""
    return p.kappa * (1.0 + p.k1*phi + p.k2*phi**2)

def OmegaU_benchmark(phi, p: Params):
    """Benchmark dimensionless potential."""
    return (p.omega_V_star
            + (p.mu**2/6.0)*phi**2
            + (p.lambda3/18.0)*phi**3
            + (p.lambda4/72.0)*phi**4)

def dOmegaU_benchmark_dphi(phi, p: Params):
    return ((p.mu**2/3.0)*phi
            + (p.lambda3/6.0)*phi**2
            + (p.lambda4/18.0)*phi**3)

# -- derived-parent kinetic/potential --
def omega_parent(phi, p: Params):
    """omega(phi) = omega0 * exp(2*beta*phi)  [derived-parent mode]."""
    return p.omega0 * np.exp(2.0 * p.beta * phi)

def OmegaU_parent(phi, p: Params):
    """Omega_U(phi) = Omega_V* + A2*s^2 + A3*s^3 + A4*s^4,  s=exp(beta*phi)-1."""
    s = np.exp(p.beta * phi) - 1.0
    return p.omega_V_star + p.A2*s**2 + p.A3*s**3 + p.A4*s**4

def dOmegaU_parent_dphi(phi, p: Params):
    s = np.exp(p.beta * phi) - 1.0
    e = np.exp(p.beta * phi)
    return p.beta * e * (2.0*p.A2*s + 3.0*p.A3*s**2 + 4.0*p.A4*s**3)

# -- mode dispatch --
def omega_or_K(phi, p: Params):
    return K_closure(phi, p) if p.closure_mode == "benchmark" else omega_parent(phi, p)

def OmegaU(phi, p: Params):
    return OmegaU_benchmark(phi, p) if p.closure_mode == "benchmark" else OmegaU_parent(phi, p)

def dOmegaU_dphi(phi, p: Params):
    return (dOmegaU_benchmark_dphi(phi, p)
            if p.closure_mode == "benchmark"
            else dOmegaU_parent_dphi(phi, p))

# ── Friedmann ────────────────────────────────────────────────────────────────
def E_ref_sq(N, p: Params):
    return (p.omega_m_star*np.exp(-3*N)
            + p.omega_r_star*np.exp(-4*N)
            + p.omega_V_star)

def E_sq_ect(N, phi, q, p: Params):
    """ECT Friedmann E^2 — benchmark or derived-parent."""
    num = (p.omega_m_star*np.exp(-3*N)
           + p.omega_r_star*np.exp(-4*N)
           + OmegaU(phi, p))
    Wphi = omega_or_K(phi, p)
    Fphi = F_response(phi, p)
    den  = Fphi - (Wphi/6.0)*q*q + p.beta*Fphi*q
    den  = np.where(den > 1e-10, den, 1e-10) if np.ndim(den) > 0 else max(den, 1e-10)
    return num / den

def dlnE_from_array(N_arr, E_arr):
    return np.gradient(np.log(E_arr), N_arr)

# ── balance functions ────────────────────────────────────────────────────────
def q_from_balance_benchmark(N, phi, E2, dlnE_dN, p: Params):
    """Slow-drift balance for benchmark mode."""
    Kphi = K_closure(phi, p)
    Fphi = F_response(phi, p)
    Ks   = max(float(Kphi), 1e-20)
    return ((p.beta/Ks)*Fphi*(2.0+dlnE_dN)
            - (p.mu**2/(3.0*Ks))*(phi/max(E2, 1e-20)))

def q0_parent_from_balance(phi0, E2_0, dlnE0, p: Params):
    """Initial q estimate for derived-parent mode."""
    om  = max(float(omega_parent(phi0, p)), 1e-20)
    src = (3.0*p.beta*np.exp(p.beta*phi0)*(2.0 + dlnE0)
           - 3.0*dOmegaU_parent_dphi(phi0, p)/max(E2_0, 1e-20))
    return src / (om * max(3.0 + dlnE0, 1e-20))

# ── solver ───────────────────────────────────────────────────────────────────
def solve_background_selfconsistent(p: Params, seed_mode: str = "ref"):
    N0   = 0.0
    Nmin = -np.log1p(p.zmax_solver)
    N_grid = np.linspace(N0, Nmin, p.npts)

    E_ref = np.sqrt(E_ref_sq(N_grid, p))
    dlnE_prev = (np.zeros_like(N_grid) if seed_mode == "zero"
                 else dlnE_from_array(N_grid, E_ref))

    phi_sol = E_sol = q_sol = None
    diagnostics = []

    for iteration in range(p.n_iter):
        dlnE_interp = interp1d(N_grid, dlnE_prev, kind="linear",
                                bounds_error=False, fill_value="extrapolate")

        if p.closure_mode == "benchmark":
            def rhs(N, y):
                phi  = y[0]
                dlnE = float(dlnE_interp(N))
                E2   = max(E_sq_ect(N, phi, 0.0, p), 1e-20)
                q    = q_from_balance_benchmark(N, phi, E2, dlnE, p)
                return [q]

            dlnE0 = float(dlnE_interp(N0))
            E2_0  = max(E_sq_ect(N0, p.phi0, 0.0, p), 1e-20)
            q0    = q_from_balance_benchmark(N0, p.phi0, E2_0, dlnE0, p)
            E2_0  = max(E_sq_ect(N0, p.phi0, q0, p), 1e-20)
            q0    = q_from_balance_benchmark(N0, p.phi0, E2_0, dlnE0, p)

            sol = solve_ivp(rhs, [N0, Nmin], [p.phi0],
                            method="RK45", dense_output=True,
                            rtol=1e-8, atol=1e-10, max_step=0.05)

            phi_arr = sol.sol(N_grid)[0]
            q_arr   = np.zeros(p.npts)
            E_arr   = np.zeros(p.npts)
            dlnE_cur = dlnE_interp(N_grid)
            for i, (N, phi) in enumerate(zip(N_grid, phi_arr)):
                dlnE_i = float(dlnE_cur[i])
                E2 = max(E_sq_ect(N, phi, 0.0, p), 1e-20)
                q  = q_from_balance_benchmark(N, phi, E2, dlnE_i, p)
                E2 = max(E_sq_ect(N, phi, q, p), 1e-20)
                E_arr[i] = np.sqrt(E2)
                q_arr[i] = q

        else:  # derived_parent
            def rhs_parent(N, y):
                phi, q = y
                dlnE = float(dlnE_interp(N))
                E2   = max(E_sq_ect(N, phi, q, p), 1e-20)
                om   = max(float(omega_parent(phi, p)), 1e-20)
                dOmU = float(dOmegaU_parent_dphi(phi, p))
                dq   = (-(3.0 + dlnE)*q
                        - p.beta*q*q
                        - (3.0*dOmU/max(E2, 1e-20)
                           - 3.0*p.beta*np.exp(p.beta*phi)*(2.0 + dlnE)) / om)
                return [q, dq]

            dlnE0 = float(dlnE_interp(N0))
            E2_0  = max(E_sq_ect(N0, p.phi0, 0.0, p), 1e-20)
            q0    = q0_parent_from_balance(p.phi0, E2_0, dlnE0, p)
            E2_0  = max(E_sq_ect(N0, p.phi0, q0, p), 1e-20)

            sol = solve_ivp(rhs_parent, [N0, Nmin], [p.phi0, q0],
                            method="RK45", dense_output=True,
                            rtol=1e-8, atol=1e-10, max_step=0.05)

            phi_arr = sol.sol(N_grid)[0]
            q_arr   = sol.sol(N_grid)[1]
            E_arr   = np.zeros(p.npts)
            for i, (N, phi, q) in enumerate(zip(N_grid, phi_arr, q_arr)):
                E_arr[i] = np.sqrt(max(E_sq_ect(N, phi, q, p), 1e-20))

        max_dE   = float(np.max(np.abs(E_arr   - E_sol)))   if E_sol   is not None else float("nan")
        max_dphi = float(np.max(np.abs(phi_arr - phi_sol))) if phi_sol is not None else float("nan")

        diagnostics.append({
            "iteration":          iteration + 1,
            "closure_mode":       p.closure_mode,
            "max_abs_delta_E":    max_dE,
            "max_abs_delta_phi":  max_dphi,
            "seed_mode":          seed_mode,
            "H_star":             p.H_star,
            "beta":               p.beta,
            "mu":                 p.mu,
            "phi0":               p.phi0,
        })

        dlnE_prev = dlnE_from_array(N_grid, E_arr)
        phi_sol = phi_arr; E_sol = E_arr; q_sol = q_arr

    z_grid = np.expm1(-N_grid)
    bg_df = pd.DataFrame({"z": z_grid, "N": N_grid, "phi": phi_sol,
                           "q": q_sol, "E": E_sol, "E_ref": E_ref})
    return bg_df, pd.DataFrame(diagnostics)



def solve_linear_growth(df: pd.DataFrame, p: Params):
    """
    Solve the linear growth equation on the solved background:
        delta'' + (2 + dlnH/dN) delta' - 1.5 * mu_eff * Omega_m(a) * delta = 0
    with N = ln a. The same initial conditions are used for ECT and reference
    runs at the highest redshift available in the solved background.
    """
    N_desc = df["N"].to_numpy()
    z_desc = df["z"].to_numpy()
    E_desc = df["E"].to_numpy()
    Eref_desc = df["E_ref"].to_numpy()
    Geff_desc = np.exp(np.clip(-p.beta * df["phi"].to_numpy(), -50, 50))

    N = N_desc[::-1]
    z = z_desc[::-1]
    E = E_desc[::-1]
    Eref = Eref_desc[::-1]
    Geff = Geff_desc[::-1]

    dlnE = dlnE_from_array(N, E)
    dlnE_ref = dlnE_from_array(N, Eref)

    def omega_m_of_N(Nv, Ev):
        return p.omega_m_star * np.exp(-3.0 * Nv) / np.maximum(Ev**2, 1e-20)

    def rhs_ect(Nv, y):
        delta, ddelta = y
        Ev = float(np.interp(Nv, N, E))
        dlnEv = float(np.interp(Nv, N, dlnE))
        mu_eff = float(np.interp(Nv, N, Geff))
        Om = omega_m_of_N(Nv, Ev)
        d2 = -(2.0 + dlnEv) * ddelta + 1.5 * mu_eff * Om * delta
        return [ddelta, d2]

    def rhs_ref(Nv, y):
        delta, ddelta = y
        Ev = float(np.interp(Nv, N, Eref))
        dlnEv = float(np.interp(Nv, N, dlnE_ref))
        Om = omega_m_of_N(Nv, Ev)
        d2 = -(2.0 + dlnEv) * ddelta + 1.5 * Om * delta
        return [ddelta, d2]

    Nini = float(N[0])
    delta_ini = np.exp(Nini)
    ddelta_ini = delta_ini

    sol_ect = solve_ivp(rhs_ect, [Nini, 0.0], [delta_ini, ddelta_ini],
                        method="RK45", dense_output=True, rtol=1e-8, atol=1e-10, max_step=0.05)
    sol_ref = solve_ivp(rhs_ref, [Nini, 0.0], [delta_ini, ddelta_ini],
                        method="RK45", dense_output=True, rtol=1e-8, atol=1e-10, max_step=0.05)

    if (not sol_ect.success) or (not sol_ref.success) or (sol_ect.sol is None) or (sol_ref.sol is None):
        nan = np.full_like(N, np.nan, dtype=float)
        return pd.DataFrame({
            "z": z[::-1], "N": N[::-1],
            "delta_ect": nan[::-1], "delta_ref": nan[::-1],
            "D_ect": nan[::-1], "D_ref": nan[::-1],
            "delta_ratio": nan[::-1], "D_ratio": nan[::-1],
            "f_ect": nan[::-1], "f_ref": nan[::-1], "f_ratio": nan[::-1],
        })

    delta_ect = sol_ect.sol(N)[0]
    ddelta_ect = sol_ect.sol(N)[1]
    delta_ref = sol_ref.sol(N)[0]
    ddelta_ref = sol_ref.sol(N)[1]

    D_ect = delta_ect / np.maximum(delta_ect[-1], 1e-30)
    D_ref = delta_ref / np.maximum(delta_ref[-1], 1e-30)
    f_ect = ddelta_ect / np.maximum(delta_ect, 1e-30)
    f_ref = ddelta_ref / np.maximum(delta_ref, 1e-30)

    return pd.DataFrame({
        "z": z[::-1],
        "N": N[::-1],
        "delta_ect": delta_ect[::-1],
        "delta_ref": delta_ref[::-1],
        "D_ect": D_ect[::-1],
        "D_ref": D_ref[::-1],
        "delta_ratio": (delta_ect / np.maximum(delta_ref, 1e-30))[::-1],
        "D_ratio": (D_ect / np.maximum(D_ref, 1e-30))[::-1],
        "f_ect": f_ect[::-1],
        "f_ref": f_ref[::-1],
        "f_ratio": (f_ect / np.maximum(f_ref, 1e-30))[::-1],
    })


def semi_analytic_structure_proxies(df: pd.DataFrame):
    """Simple semi-analytic JWST/BH development proxies from the solved background."""
    out = pd.DataFrame({"z": df["z"].to_numpy()})
    geff = df["Geff_ratio"].to_numpy()
    out["tff_ratio"] = 1.0 / np.sqrt(np.maximum(geff, 1e-30))
    out["virial_speed_ratio"] = np.sqrt(np.maximum(geff, 1e-30))
    out["bh_growth_time_ratio"] = 1.0 / np.maximum(geff, 1e-30)
    out["jeans_mass_ratio"] = 1.0 / np.maximum(geff, 1e-30)**1.5
    return out


def parse_float_grid(spec: str):
    return [float(x.strip()) for x in spec.split(",") if x.strip()]


def run_derived_grid_scan(base_params: Params, omega0_values, phi0_values, seed_mode="ref"):
    rows = []
    scan_npts = min(base_params.npts, 1200)
    scan_n_iter = min(base_params.n_iter, 3)
    for omega0 in omega0_values:
        for phi0 in phi0_values:
            p = Params(
                H_star=base_params.H_star,
                omega_m_star=base_params.omega_m_star,
                omega_r_star=base_params.omega_r_star,
                omega_V_star=base_params.omega_V_star,
                beta=base_params.beta,
                mu=base_params.mu,
                kappa=base_params.kappa,
                k1=base_params.k1,
                k2=base_params.k2,
                lambda3=base_params.lambda3,
                lambda4=base_params.lambda4,
                omega0=omega0,
                A2=base_params.A2,
                A3=base_params.A3,
                A4=base_params.A4,
                phi0=phi0,
                closure_mode="derived_parent",
                zmax_solver=base_params.zmax_solver,
                zplot=base_params.zplot,
                z_match=base_params.z_match,
                npts=scan_npts,
                n_iter=scan_n_iter,
            )
            try:
                bg, _ = solve_background_selfconsistent(p, seed_mode=seed_mode)
                full, summary, *_ = derived_quantities(bg, p)
                growth = solve_linear_growth(full, p)
                s = summary.iloc[0]
            except Exception:
                rows.append({
                    "omega0": omega0, "phi0": phi0,
                    "DeltaH0_over_H0": np.nan, "H0_late": np.nan, "age_ect_Gyr": np.nan,
                    "t_U_ect_z10": np.nan, "t_gal_z10_formed_z15_ect": np.nan, "DL_frac_z10": np.nan,
                    "Geff_ratio_z10": np.nan, "grow_proxy_ratio_z10": np.nan,
                    "linear_delta_ratio_z10": np.nan, "linear_D_ratio_z10": np.nan,
                    "tff_ratio_z10": np.nan, "virial_speed_ratio_z10": np.nan,
                    "bh_growth_time_ratio_z10": np.nan,
                    "hubble_candidate": False, "age_candidate": False,
                    "balanced_candidate": False, "status": "failed"
                })
                continue

            def near(frame, col, zt):
                j = int(np.argmin(np.abs(frame["z"].to_numpy() - zt)))
                return float(frame.iloc[j][col])

            rows.append({
                "omega0": omega0,
                "phi0": phi0,
                "DeltaH0_over_H0": float(s["DeltaH0_over_H0"]),
                "H0_late": float(s["H0_late"]),
                "age_ect_Gyr": float(s["age_ect_Gyr"]),
                "t_U_ect_z10": float(s.get("t_U_ect_z10", np.nan)),
                "t_gal_z10_formed_z15_ect": float(s.get("t_gal_z10_formed_z15_ect", np.nan)),
                "DL_frac_z10": float(s.get("DL_frac_z10", np.nan)),
                "Geff_ratio_z10": near(full, "Geff_ratio", 10.0),
                "grow_proxy_ratio_z10": near(full, "grow", 10.0) / max(near(full, "grow_ref", 10.0), 1e-30),
                "linear_delta_ratio_z10": near(growth, "delta_ratio", 10.0),
                "linear_D_ratio_z10": near(growth, "D_ratio", 10.0),
                "tff_ratio_z10": 1.0 / np.sqrt(max(near(full, "Geff_ratio", 10.0), 1e-30)),
                "virial_speed_ratio_z10": np.sqrt(max(near(full, "Geff_ratio", 10.0), 1e-30)),
                "bh_growth_time_ratio_z10": 1.0 / max(near(full, "Geff_ratio", 10.0), 1e-30),
                "hubble_candidate": bool(0.02 <= float(s["DeltaH0_over_H0"]) <= 0.05),
                "age_candidate": bool(float(s["age_ect_Gyr"]) >= 12.5),
                "status": "ok",
            })
    scan_df = pd.DataFrame(rows)
    scan_df["balanced_candidate"] = scan_df["hubble_candidate"] & scan_df["age_candidate"]
    return scan_df

# ── age functions ────────────────────────────────────────────────────────────
def H_tail(z, z_match, H_match, om, orad):
    num = om*(1+z)**3 + orad*(1+z)**4
    den = om*(1+z_match)**3 + orad*(1+z_match)**4
    return H_match*np.sqrt(num/den)

def cosmic_age_from_bigbang(z_obs, df: pd.DataFrame, p: Params):
    z = df["z"].to_numpy(); H = p.H_star*df["E"].to_numpy()
    j_match = int(np.argmin(np.abs(z - p.z_match)))
    H_match = H[j_match]; age_fac = MPC_IN_KM/SEC_IN_GYR
    age1 = 0.0
    if z_obs <= p.z_match:
        mask = (z >= z_obs) & (z <= p.z_match)
        age1 = np.trapezoid(age_fac/((1.0+z[mask])*H[mask]), z[mask])
    z_start = max(z_obs, p.z_match)
    z2 = np.logspace(np.log10(1.0+z_start), np.log10(1.0+p.z_inf), 6000) - 1.0
    H2 = H_tail(z2, p.z_match, H_match, p.omega_m_star, p.omega_r_star)
    age2 = np.trapezoid(age_fac/((1.0+z2)*H2), z2)
    return age1 + age2

def reference_cosmic_age(z_obs, p: Params):
    z2 = np.logspace(np.log10(1.0+z_obs), np.log10(1.0+p.z_inf), 6000) - 1.0
    H2 = p.H_star*np.sqrt(E_ref_sq(-np.log1p(z2), p))
    return np.trapezoid(MPC_IN_KM/SEC_IN_GYR/((1.0+z2)*H2), z2)

# ── derived quantities ───────────────────────────────────────────────────────
def derived_quantities(df: pd.DataFrame, p: Params):
    z    = df["z"].to_numpy(); E = df["E"].to_numpy()
    Eref = df["E_ref"].to_numpy(); phi = df["phi"].to_numpy()
    H    = p.H_star*E; Href = p.H_star*Eref

    chi    = cumulative_trapezoid(C_LIGHT/H,    z, initial=0.0)
    chiref = cumulative_trapezoid(C_LIGHT/Href, z, initial=0.0)
    DL = (1+z)*chi;    DL_ref = (1+z)*chiref
    DA = chi/(1+z);    DA_ref = chiref/(1+z)

    age_fac  = MPC_IN_KM/SEC_IN_GYR
    tlook    = cumulative_trapezoid(age_fac/((1+z)*H),    z, initial=0.0)
    tlookref = cumulative_trapezoid(age_fac/((1+z)*Href), z, initial=0.0)
    t_U     = np.array([cosmic_age_from_bigbang(float(zz), df, p) for zz in z])
    t_U_ref = np.array([reference_cosmic_age(float(zz), p)        for zz in z])

    c_si = C_LIGHT*1e3
    gdag_bg     = c_si*(H/MPC_IN_KM)/(2*np.pi)
    gdag_bg_ref = c_si*(Href/MPC_IN_KM)/(2*np.pi)
    Geff_ratio = np.exp(-p.beta*phi)
    grow    = Geff_ratio/E**2
    growref = 1.0/Eref**2

    df = df.copy()
    for k, v in [("H",H),("H_ref",Href),("DL",DL),("DL_ref",DL_ref),
                 ("DA",DA),("DA_ref",DA_ref),("tlook",tlook),("tlook_ref",tlookref),
                 ("t_U",t_U),("t_U_ref",t_U_ref),("gdag_bg",gdag_bg),
                 ("gdag_bg_ref",gdag_bg_ref),("gdag_ratio",gdag_bg/gdag_bg[0]),
                 ("Geff_ratio",Geff_ratio),("grow",grow),("grow_ref",growref)]:
        df[k] = v

    growth_df = solve_linear_growth(df, p)
    struct_df = semi_analytic_structure_proxies(df)
    df = df.merge(growth_df[["z","delta_ect","delta_ref","D_ect","D_ref","delta_ratio","D_ratio","f_ect","f_ref","f_ratio"]], on="z", how="left")
    df = df.merge(struct_df, on="z", how="left")

    # closure member tag
    _is_bench = (p.closure_mode == "benchmark"
                 and p.k1==0.0 and p.k2==0.0 and p.lambda3==0.0 and p.lambda4==0.0)
    _member = ("benchmark" if _is_bench
               else "derived_parent" if p.closure_mode=="derived_parent"
               else "deformed")

    # summary
    S = {"beta": p.beta, "mu": p.mu,
         "kappa": p.kappa, "k1": p.k1, "k2": p.k2,
         "lambda3": p.lambda3, "lambda4": p.lambda4,
         "omega0": p.omega0, "A2": p.A2, "A3": p.A3, "A4": p.A4,
         "phi0_input": p.phi0,
         "closure_mode": p.closure_mode, "closure_member": _member,
         "H_star": p.H_star, "omega_m_star": p.omega_m_star,
         "omega_r_star": p.omega_r_star, "omega_V_star": p.omega_V_star,
         "z_match": p.z_match, "closure_name": (
             "derived_parent_condensate" if p.closure_mode=="derived_parent"
             else "admissible_phi_first"),
         "high_z_completion": "interim_matter_radiation_tail",
         "seed_mode": "ref",
         "zmax_solver": p.zmax_solver, "npts": p.npts, "n_iter": p.n_iter,
         "E0": float(E[0]), "H0_late": float(p.H_star*E[0]),
         "DeltaH0_over_H0": float(E[0]-1.0)}

    t0_ect = cosmic_age_from_bigbang(0.0, df, p)
    t0_ref = reference_cosmic_age(0.0, p)
    S.update({"age_ect_Gyr": t0_ect, "age_ref_Gyr": t0_ref,
              "Delta_age_frac": (t0_ect-t0_ref)/t0_ref})

    mask_lowz = z <= 0.1
    if mask_lowz.sum() >= 5:
        S["H0_lowz_diagnostic"] = float(C_LIGHT/np.polyfit(z[mask_lowz],DL[mask_lowz],1)[0])

    for zt in [1,2,5,8,10,12]:
        j = int(np.argmin(np.abs(z-zt)))
        dl_frac = float((DL[j]-DL_ref[j])/max(DL_ref[j],1e-10))
        tU  = float(t_U[j]); tUr = float(t_U_ref[j])
        S[f"DL_frac_z{zt}"]     = dl_frac
        S[f"DL_lum_frac_z{zt}"] = float((1+dl_frac)**2-1)
        S[f"tlook_frac_z{zt}"]  = float((tlook[j]-tlookref[j])/max(tlookref[j],1e-10))
        S[f"grow_ratio_z{zt}"]  = float(grow[j]/max(growref[j],1e-20))
        S[f"linear_delta_ratio_z{zt}"] = float(df["delta_ratio"].iloc[j])
        S[f"linear_D_ratio_z{zt}"] = float(df["D_ratio"].iloc[j])
        S[f"f_ratio_z{zt}"] = float(df["f_ratio"].iloc[j])
        S[f"tff_ratio_z{zt}"] = float(df["tff_ratio"].iloc[j])
        S[f"virial_speed_ratio_z{zt}"] = float(df["virial_speed_ratio"].iloc[j])
        S[f"bh_growth_time_ratio_z{zt}"] = float(df["bh_growth_time_ratio"].iloc[j])
        S[f"gdag_ratio_z{zt}"]  = float(df["gdag_ratio"].iloc[j])
        S[f"t_U_ect_z{zt}"]     = tU
        S[f"t_U_ref_z{zt}"]     = tUr
        S[f"t_U_frac_z{zt}"]    = float((tU-tUr)/max(tUr,1e-10))

    for zf in [15,20,30]:
        tg = cosmic_age_from_bigbang(10.0,df,p) - cosmic_age_from_bigbang(float(zf),df,p)
        tr = reference_cosmic_age(10.0,p) - reference_cosmic_age(float(zf),p)
        S[f"t_gal_z10_formed_z{zf}_ect"] = tg
        S[f"t_gal_z10_formed_z{zf}_ref"] = tr
    summary_df = pd.DataFrame([S])

    # distance-time table
    dt_df = df[["z","H","H_ref","E","E_ref","phi","q","DL","DL_ref","DA","DA_ref",
                "tlook","tlook_ref","t_U","t_U_ref","Geff_ratio","grow","grow_ref",
                "gdag_bg","gdag_bg_ref","gdag_ratio"]].copy()

    # JWST age grid
    jwst_rows = []
    for z_obs in [8,10,12]:
        for z_form in [12,15,20,30]:
            if z_form > z_obs:
                t_o  = cosmic_age_from_bigbang(float(z_obs),  df, p)
                t_f  = cosmic_age_from_bigbang(float(z_form), df, p)
                t_or = reference_cosmic_age(float(z_obs),  p)
                t_fr = reference_cosmic_age(float(z_form), p)
                jwst_rows.append({"z_obs": float(z_obs), "z_form": float(z_form),
                    "t_U_obs_ect_Gyr": t_o, "t_U_obs_ref_Gyr": t_or,
                    "t_U_form_ect_Gyr": t_f, "t_U_form_ref_Gyr": t_fr,
                    "t_gal_ect_Gyr": t_o-t_f, "t_gal_ref_Gyr": t_or-t_fr})
    jwst_df = pd.DataFrame(jwst_rows)

    key_pairs = {(10,12),(10,15),(10,20),(10,30),(12,15),(12,20)}
    jwst_key_df = jwst_df[
        jwst_df.apply(lambda r: (int(r.z_obs),int(r.z_form)) in key_pairs, axis=1)
    ].reset_index(drop=True)

    panel_ab_df = df[["z","E","E_ref"]].copy()
    panel_ab_df["DL_frac"] = (df["DL"]-df["DL_ref"])/df["DL_ref"].replace(0, float("nan"))

    tref_s = df["tlook_ref"].copy(); tref_s[tref_s < 0.01] = float("nan")
    panel_cd_df = df[["z","t_U","t_U_ref","grow","grow_ref","gdag_ratio","delta_ratio","D_ratio","f_ratio","tff_ratio","virial_speed_ratio","bh_growth_time_ratio"]].copy()
    panel_cd_df["tlook_frac"] = (df["tlook"]-df["tlook_ref"])/tref_s
    panel_cd_df["grow_ratio"] = df["grow"]/df["grow_ref"].replace(0, float("nan"))

    # metadata
    meta_df = pd.DataFrame([{
        "closure_name": ("derived_parent_condensate" if p.closure_mode=="derived_parent"
                         else "admissible_phi_first"),
        "closure_mode":    p.closure_mode,
        "closure_family":  ("derived_parent" if p.closure_mode=="derived_parent"
                            else "benchmark_truncation"),
        "closure_member":  _member,
        "response_factor": "F(phi)=exp(beta*phi)",
        "kinetic_closure": ("omega(phi)=omega0*exp(2*beta*phi)"
                            if p.closure_mode=="derived_parent"
                            else "K(phi)=K0*(1+k1*phi+k2*phi^2)"),
        "potential_closure": (
            "Omega_U(phi)=Omega_V*+A2*(exp(beta*phi)-1)^2+A3*(exp(beta*phi)-1)^3+A4*(exp(beta*phi)-1)^4"
            if p.closure_mode=="derived_parent"
            else "V(phi)=V0+0.5*m_phi^2*phi^2+lambda3/3!*phi^3+lambda4/4!*phi^4"),
        "high_z_completion": "interim_matter_radiation_tail",
        "z_match": p.z_match, "zmax_solver": p.zmax_solver,
        "npts": p.npts, "n_iter": p.n_iter,
        "H_star": p.H_star, "beta": p.beta, "mu": p.mu, "phi0": p.phi0,
        "omega0": p.omega0, "A2": p.A2, "A3": p.A3, "A4": p.A4,
        "kappa": p.kappa, "k1": p.k1, "k2": p.k2,
        "lambda3": p.lambda3, "lambda4": p.lambda4,
        "omega_m_star": p.omega_m_star, "omega_r_star": p.omega_r_star,
        "omega_V_star": p.omega_V_star,
        "article_figure_background":   "ect_hubble_jwst_background_bw.pdf",
        "article_figure_h0_scan":      "ect_h0_scan_bw.pdf",
        "article_table_summary":       "ect_benchmark_summary.csv",
        "article_table_distance_time": "ect_distance_time_table.csv",
        "article_table_jwst":          "ect_jwst_age_grid.csv",
    }])

    manifest_rows = [
      {"filename":"ect_background_profile.csv","artifact_type":"background_table",
       "description":"Full background: z,H,E,phi,q,E_ref and derived cols",
       "supports_article_section":"sec:hubble_jwst, app:late_cosmo_background",
       "supports_figure_or_table":"fig:ect_hubble_jwst_background"},
      {"filename":"ect_distance_time_table.csv","artifact_type":"distance_time_table",
       "description":"D_L,D_A,t_lookback,t_U,G_eff on redshift grid",
       "supports_article_section":"sec:hubble_jwst, app:late_cosmo_background",
       "supports_figure_or_table":"eq:app_late_dist, eq:app_late_agegal"},
      {"filename":"ect_jwst_age_grid.csv","artifact_type":"jwst_age_grid",
       "description":"t_gal(z_obs;z_form) for all (z_obs,z_form) pairs",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"JWST discussion numbers"},
      {"filename":"ect_jwst_key_rows.csv","artifact_type":"jwst_key_rows",
       "description":"Compact JWST grid: key (z_obs,z_form) pairs for main text",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"main text JWST numbers"},
      {"filename":"ect_benchmark_summary.csv","artifact_type":"run_summary",
       "description":"Run summary: Hubble shift, ages, JWST outputs, closure metadata",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"main text numbers"},
      {"filename":"ect_run_metadata.csv","artifact_type":"run_metadata",
       "description":"Run metadata including closure mode, family parameters, and numerical settings",
       "supports_article_section":"app:late_cosmo_artefacts, sec:late_cosmo_roadmap",
       "supports_figure_or_table":"metadata"},
      {"filename":"ect_convergence_diagnostics.csv","artifact_type":"convergence_diagnostics",
       "description":"max |delta_E| and |delta_phi| per iteration",
       "supports_article_section":"app:late_cosmo_algorithm",
       "supports_figure_or_table":"convergence report"},
      {"filename":"ect_panel_ab_background.csv","artifact_type":"figure_panel_data",
       "description":"Panels (a)+(b): z, E, E_ref, DL_frac",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:ect_hubble_jwst_background panels a+b"},
      {"filename":"ect_panel_cd_growth_age.csv","artifact_type":"figure_panel_data",
       "description":"Panels (c)+(d): z, tlook_frac, grow_ratio, gdag_ratio, t_U, linear-growth and structure proxies",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:ect_hubble_jwst_background panels c+d"},
      {"filename":"ect_linear_growth_table.csv","artifact_type":"linear_growth_table",
       "description":"Linear growth solution: delta, D, f and ratios to reference on common z-grid",
       "supports_article_section":"sec:hubble_jwst, app:late_cosmo_artefacts",
       "supports_figure_or_table":"linear growth diagnostics"},
      {"filename":"ect_structure_proxies.csv","artifact_type":"structure_proxy_table",
       "description":"Semi-analytic structure proxies: free-fall, virial speed, BH growth time, Jeans-mass ratios",
       "supports_article_section":"sec:hubble_jwst, app:late_cosmo_artefacts",
       "supports_figure_or_table":"semi-analytic JWST/BH development estimates"},
      {"filename":"ect_hubble_jwst_background_bw.pdf","artifact_type":"figure",
       "description":"Four-panel background figure (PDF)",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:ect_hubble_jwst_background"},
      {"filename":"ect_hubble_jwst_background_bw.png","artifact_type":"figure",
       "description":"Four-panel background figure (PNG)",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:ect_hubble_jwst_background"},
      {"filename":"ect_h0_scan_bw.pdf","artifact_type":"figure",
       "description":"Parameter window scan beta vs phi_0 (PDF, benchmark only)",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:h0_scan_main"},
      {"filename":"ect_h0_scan_bw.png","artifact_type":"figure",
       "description":"Parameter window scan beta vs phi_0 (PNG, benchmark only)",
       "supports_article_section":"sec:hubble_jwst",
       "supports_figure_or_table":"fig:h0_scan_main"},
    ]
    manifest_df = pd.DataFrame(manifest_rows)

    linear_growth_df = growth_df.copy()
    structure_df = struct_df.copy()
    return df, summary_df, dt_df, jwst_df, jwst_key_df, panel_ab_df, panel_cd_df, linear_growth_df, structure_df, meta_df, manifest_df

# ── figures ──────────────────────────────────────────────────────────────────
def make_figure(df, summary, outpath, p):
    apply_bw_style()
    z = df["z"].to_numpy(); mask = z <= p.zplot
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    axs = axes.ravel(); s = summary.iloc[0]
    mode_label = "ECT derived-parent" if p.closure_mode=="derived_parent" else "ECT benchmark"

    ax = axs[0]
    ax.plot(z[mask], df["E_ref"].to_numpy()[mask], "0.55", ls="--", lw=1.8,
            label=r"screened reference ($\phi=0$)")
    ax.plot(z[mask], df["E"].to_numpy()[mask], "black", lw=2.2, label=mode_label)
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$E(z)=H/H_*$")
    ax.set_title("(a) Expansion history", fontweight="bold", loc="left")
    ax.legend(frameon=True, fontsize=9)
    omega0_str = f", $\\omega_0={p.omega0:.1f}$" if p.closure_mode=="derived_parent" else f", $\\kappa={p.kappa:.1f}$"
    txt = (rf"$\beta={s['beta']:.2f}$,  $\mu={s['mu']:.2f}${omega0_str},  $\phi_0={s['phi0_input']:.3f}$" "\n"
           rf"$\Delta H_0/H_0={s['DeltaH0_over_H0']*100:.1f}\%$,  "
           rf"$H_0^{{\rm late}}={s['H0_late']:.1f}$ km/s/Mpc  [{p.closure_mode}]")
    ax.text(0.03, 0.97, txt, transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(boxstyle="round", fc="white", ec="0.6"))

    ax = axs[1]
    dl = (df["DL"]-df["DL_ref"])/df["DL_ref"].replace(0, np.nan)
    ax.plot(z[mask], dl.to_numpy()[mask], "black", lw=2.2, label=mode_label)
    ax.axhline(0, color="0.55", ls="--", lw=1.2, label=r"screened reference")
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\Delta D_L/D_L^{\rm ref}$")
    ax.set_title("(b) Luminosity-distance shift", fontweight="bold", loc="left")
    ax.legend(frameon=True, fontsize=9, loc="upper right")

    ax = axs[2]
    tref = df["tlook_ref"].to_numpy()
    tsh  = np.where(tref > 0.01, (df["tlook"]-df["tlook_ref"])/tref, 0.0)
    ax.plot(z[mask], tsh[mask], "black", lw=2.2)
    ax.axhline(0, color="0.55", ls="--", lw=1.2)
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\Delta t_{\rm lookback}/t_{\rm lookback}^{\rm ref}$")
    ax.set_title("(c) Lookback-time shift", fontweight="bold", loc="left")
    ax.text(0.97, 0.97,
            rf"Age ECT: {s['age_ect_Gyr']:.2f} Gyr" "\n" rf"Age ref: {s['age_ref_Gyr']:.2f} Gyr",
            transform=ax.transAxes, va="top", ha="right", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="0.6"))

    ax = axs[3]
    gr = df["grow"]/df["grow_ref"].replace(0, np.nan)
    ax.plot(z[mask], gr.to_numpy()[mask], "black", lw=2.2, label=r"Growth proxy $G_{\rm eff}/H^2$")
    ax.axhline(1.0, color="0.55", ls="--", lw=1.2)
    ax.set_xlabel("$z$"); ax.set_ylabel(r"$\mathcal{G}_{\rm ECT}/\mathcal{G}_{\rm ref}$ (left)")
    ax.set_title(r"(d) Growth proxy \& $g^\dagger_{\rm bg}(z)$", fontweight="bold", loc="left")
    ax2 = ax.twinx()
    ax2.plot(z[mask], df["gdag_ratio"].to_numpy()[mask], "0.45", lw=1.8, ls="-.",
             label=r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)$")
    ax2.set_ylabel(r"$g^\dagger_{\rm bg}(z)/g^\dagger_{\rm bg}(0)$ (right)", color="0.45")
    ax2.tick_params(axis="y", labelcolor="0.45")
    l1, lb1 = ax.get_legend_handles_labels(); l2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(l1+l2, lb1+lb2, frameon=True, fontsize=9, loc="upper left")

    fig.suptitle(f"ECT late-time background [{p.closure_mode}]: Hubble tension, age, and JWST implications",
                 fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"), dpi=300, bbox_inches="tight")
    fig.savefig(outpath.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(); print("Background figure saved.")

def make_scan_figure(outpath, p):
    """Benchmark-only analytic scan."""
    apply_bw_style()
    bb = np.linspace(0.3, 1.5, 80); pp = np.linspace(-0.20, -0.01, 80)
    BB, PP = np.meshgrid(bb, pp); DH = p.mu**2*PP**2/12 - 0.5*BB*PP
    fig, ax = plt.subplots(figsize=(8, 6))
    levels = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10]
    cs = ax.contourf(BB, PP, DH, levels=levels, cmap="Greys")
    fig.colorbar(cs, ax=ax, label=r"$\Delta H_0/H_0$")
    ct = ax.contour(BB, PP, DH, levels=levels, colors="black", linewidths=0.8)
    ax.clabel(ct, fmt="%.2f", fontsize=9)
    ax.plot(0.8, -0.12, "k*", ms=12, label="Benchmark B")
    ax.plot(1.0, -0.12, "k^", ms=9,  label="Benchmark C")
    ax.set_xlabel(r"$\beta$", fontsize=12)
    ax.set_ylabel(r"$\phi_0=\phi(z=0)$", fontsize=12)
    ax.set_title(rf"$\Delta H_0/H_0\approx\mu^2\phi_0^2/12-\beta\phi_0/2$" "\n"
                 rf"($\mu={p.mu:.1f}$, $\kappa={p.kappa:.0f}$, benchmark only)", fontsize=11)
    ax.legend(frameon=True, fontsize=10)
    fig.tight_layout()
    fig.savefig(outpath.with_suffix(".pdf"), dpi=300)
    fig.savefig(outpath.with_suffix(".png"), dpi=220)
    plt.close(); print("Scan figure saved.")

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="ECT cosmology solver v5: benchmark/derived-parent modes + linear growth")
    ap.add_argument("--outdir",       required=True)
    ap.add_argument("--H_star",       type=float, default=67.4)
    ap.add_argument("--om0",          type=float, default=0.315)
    ap.add_argument("--or0",          type=float, default=9.2e-5)
    ap.add_argument("--oV0",          type=float, default=None)
    ap.add_argument("--beta",         type=float, default=0.8)
    ap.add_argument("--mu",           type=float, default=1.5)
    ap.add_argument("--closure_mode", choices=["benchmark","derived_parent"],
                    default="derived_parent",
                    help="Physics mode: derived_parent (default) or benchmark (truncation)")
    # benchmark parameters
    ap.add_argument("--kappa",   type=float, default=15.0)
    ap.add_argument("--k1",      type=float, default=0.0)
    ap.add_argument("--k2",      type=float, default=0.0)
    ap.add_argument("--lambda3", type=float, default=0.0)
    ap.add_argument("--lambda4", type=float, default=0.0)
    # derived-parent parameters
    ap.add_argument("--omega0",  type=float, default=15.0)
    ap.add_argument("--A2",      type=float, default=None,
                    help="Derived potential A2 coefficient (default: mu^2/(6*beta^2))")
    ap.add_argument("--A3",      type=float, default=0.0)
    ap.add_argument("--A4",      type=float, default=0.0)
    # common
    ap.add_argument("--phi0","--u0", dest="phi0", type=float, default=-0.12,
                    help="phi0=phi(z=0), macroscopic amplitude variable")
    ap.add_argument("--zmax",          type=float, default=15.0)
    ap.add_argument("--zplot",         type=float, default=15.0)
    ap.add_argument("--z_match",       type=float, default=10.0)
    ap.add_argument("--npts",          type=int,   default=3000)
    ap.add_argument("--n_iter",        type=int,   default=4)
    ap.add_argument("--scan",          action="store_true",
                    help="Generate scan figure (benchmark mode only)")
    ap.add_argument("--validate_multiseed", action="store_true")
    ap.add_argument("--compare_to_benchmark", action="store_true",
                    help="Also run pure benchmark and save comparison CSV")
    ap.add_argument("--seed_mode", choices=["ref","zero"], default="ref")
    ap.add_argument("--scan_derived_grid", action="store_true",
                    help="Run a small derived-parent grid scan over omega0 and phi0")
    ap.add_argument("--omega0_grid", type=str, default="15,20,25,30,40,50")
    ap.add_argument("--phi0_grid", type=str, default="-0.15,-0.12,-0.10,-0.08,-0.05")
    args = ap.parse_args()

    omega_V_star = args.oV0 if args.oV0 is not None else 1.0 - args.om0 - args.or0
    p = Params(
        H_star=args.H_star, omega_m_star=args.om0, omega_r_star=args.or0,
        omega_V_star=omega_V_star, beta=args.beta, mu=args.mu,
        closure_mode=args.closure_mode,
        kappa=args.kappa, k1=args.k1, k2=args.k2,
        lambda3=args.lambda3, lambda4=args.lambda4,
        omega0=args.omega0, A2=args.A2, A3=args.A3, A4=args.A4,
        phi0=args.phi0, zmax_solver=args.zmax, zplot=args.zplot,
        z_match=args.z_match, npts=args.npts, n_iter=args.n_iter,
    )

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    print(f"ECT solver v5: mode={p.closure_mode}, "
          f"beta={p.beta}, mu={p.mu}, phi0={p.phi0}, "
          f"kappa={p.kappa}, omega0={p.omega0}, "
          f"k1={p.k1}, k2={p.k2}, lambda3={p.lambda3}, lambda4={p.lambda4}, "
          f"A2={p.A2:.4f}, A3={p.A3}, A4={p.A4}, seed={args.seed_mode}")

    df, diagnostics = solve_background_selfconsistent(p, seed_mode=args.seed_mode)
    full, summary, distance_time, jwst_grid, jwst_key, panel_ab, panel_cd, linear_growth, structure_df, metadata, manifest = \
        derived_quantities(df, p)

    metadata["seed_mode"]           = args.seed_mode
    summary["seed_mode"]            = args.seed_mode
    metadata["validate_multiseed"]  = bool(args.validate_multiseed)
    summary["validate_multiseed"]   = bool(args.validate_multiseed)
    _ib = (p.closure_mode=="benchmark"
           and p.k1==0.0 and p.k2==0.0 and p.lambda3==0.0 and p.lambda4==0.0)
    summary["is_benchmark_member"]  = bool(_ib)
    metadata["is_benchmark_member"] = bool(_ib)

    # save core artefacts
    full.to_csv(          outdir/"ect_background_profile.csv",      index=False)
    distance_time.to_csv( outdir/"ect_distance_time_table.csv",     index=False)
    jwst_grid.to_csv(     outdir/"ect_jwst_age_grid.csv",           index=False)
    summary.to_csv(       outdir/"ect_benchmark_summary.csv",       index=False)
    metadata.to_csv(      outdir/"ect_run_metadata.csv",            index=False)
    diagnostics.to_csv(   outdir/"ect_convergence_diagnostics.csv", index=False)
    panel_ab.to_csv(      outdir/"ect_panel_ab_background.csv",     index=False)
    panel_cd.to_csv(      outdir/"ect_panel_cd_growth_age.csv",     index=False)
    linear_growth.to_csv( outdir/"ect_linear_growth_table.csv",     index=False)
    structure_df.to_csv(  outdir/"ect_structure_proxies.csv",       index=False)
    jwst_key.to_csv(      outdir/"ect_jwst_key_rows.csv",           index=False)

    s = summary.iloc[0]
    print(f"\n=== SUMMARY [{p.closure_mode}] ===")
    print(f"  DH0/H0  = {s['DeltaH0_over_H0']*100:.2f}%")
    print(f"  H0 late = {s['H0_late']:.2f} km/s/Mpc")
    print(f"  Age ECT = {s['age_ect_Gyr']:.2f} Gyr  (ref = {s['age_ref_Gyr']:.2f} Gyr)")
    for zt in [5, 10, 12]:
        j = int(np.argmin(np.abs(full["z"].to_numpy()-zt)))
        print(f"  z={zt:2d}: DL/DL={s.get(f'DL_frac_z{zt}',0)*100:.2f}%  "
              f"tU={s.get(f't_U_ect_z{zt}',0):.3f} Gyr  "
              f"delta_ratio={s.get(f'linear_delta_ratio_z{zt}',0):.3f}  "
              f"Geff/GN={full.iloc[j]['Geff_ratio']:.3f}")

    # multiseed validation
    if args.validate_multiseed:
        df2, _ = solve_background_selfconsistent(p, seed_mode="zero")
        ms_df = pd.DataFrame({
            "z": df["z"].to_numpy(),
            "phi_refseed": df["phi"].to_numpy(), "phi_zeroseed": df2["phi"].to_numpy(),
            "E_refseed": df["E"].to_numpy(),     "E_zeroseed": df2["E"].to_numpy(),
            "delta_phi": df["phi"].to_numpy()-df2["phi"].to_numpy(),
            "delta_E":   df["E"].to_numpy()-df2["E"].to_numpy(),
        })
        ms_df.to_csv(outdir/"ect_multiseed_comparison.csv", index=False)
        print(f"  Multiseed: max|delta_phi|={ms_df.delta_phi.abs().max():.2e}  "
              f"max|delta_E|={ms_df.delta_E.abs().max():.2e}")
        manifest = pd.concat([manifest, pd.DataFrame([{
            "filename": "ect_multiseed_comparison.csv",
            "artifact_type": "validation_table",
            "description": "Comparison ref vs zero seed: phi/E deltas",
            "supports_article_section": "app:late_cosmo_interface",
            "supports_figure_or_table": "validation checks"}])], ignore_index=True)

    # compare_to_benchmark
    is_pure_bench = (p.closure_mode=="benchmark"
                     and p.k1==0.0 and p.k2==0.0 and p.lambda3==0.0 and p.lambda4==0.0)
    if args.compare_to_benchmark and not is_pure_bench:
        p_bench = Params(
            H_star=p.H_star, omega_m_star=p.omega_m_star,
            omega_r_star=p.omega_r_star, omega_V_star=p.omega_V_star,
            beta=p.beta, mu=p.mu,
            kappa=p.kappa, k1=0.0, k2=0.0, lambda3=0.0, lambda4=0.0,
            omega0=p.omega0, A2=p.A2, A3=p.A3, A4=p.A4,
            phi0=p.phi0, closure_mode="benchmark",
            zmax_solver=p.zmax_solver, zplot=p.zplot,
            z_match=p.z_match, npts=p.npts, n_iter=p.n_iter,
        )
        df_b, _ = solve_background_selfconsistent(p_bench, seed_mode=args.seed_mode)
        comp_df = pd.DataFrame({
            "z": df["z"].to_numpy(),
            "phi_run": df["phi"].to_numpy(), "phi_benchmark": df_b["phi"].to_numpy(),
            "E_run":   df["E"].to_numpy(),   "E_benchmark":   df_b["E"].to_numpy(),
            "delta_phi_vs_benchmark": df["phi"].to_numpy()-df_b["phi"].to_numpy(),
            "delta_E_vs_benchmark":   df["E"].to_numpy()-df_b["E"].to_numpy(),
        })
        comp_df.to_csv(outdir/"ect_benchmark_comparison.csv", index=False)
        dph = comp_df.delta_phi_vs_benchmark.abs().max()
        dE  = comp_df.delta_E_vs_benchmark.abs().max()
        print(f"  Benchmark comparison: max|delta_phi|={dph:.3e}  max|delta_E|={dE:.3e}")
        manifest = pd.concat([manifest, pd.DataFrame([{
            "filename": "ect_benchmark_comparison.csv",
            "artifact_type": "comparison_table",
            "description": "Difference between current run and benchmark truncation",
            "supports_article_section": "app:late_closure_robustness",
            "supports_figure_or_table": "closure-family robustness"}])], ignore_index=True)


    if args.scan_derived_grid:
        omega0_values = parse_float_grid(args.omega0_grid)
        phi0_values = parse_float_grid(args.phi0_grid)
        scan_df = run_derived_grid_scan(p, omega0_values, phi0_values, seed_mode=args.seed_mode)
        scan_df.to_csv(outdir/"ect_derived_grid_scan.csv", index=False)
        candidates = scan_df[scan_df["balanced_candidate"]].copy()
        candidates.to_csv(outdir/"ect_derived_candidate_points.csv", index=False)
        print(f"  Derived grid scan: {len(scan_df)} points, {len(candidates)} balanced candidates")
        manifest = pd.concat([manifest, pd.DataFrame([
            {
                "filename": "ect_derived_grid_scan.csv",
                "artifact_type": "parameter_scan",
                "description": "Derived-parent scan over omega0 and phi0 with Hubble/age/growth metrics",
                "supports_article_section": "sec:hubble_jwst, app:late_closure_robustness",
                "supports_figure_or_table": "parameter-corridor selection"
            },
            {
                "filename": "ect_derived_candidate_points.csv",
                "artifact_type": "candidate_table",
                "description": "Subset of derived-parent scan satisfying simple Hubble+age candidate filters",
                "supports_article_section": "sec:hubble_jwst, app:late_closure_robustness",
                "supports_figure_or_table": "working points"
            }
        ])], ignore_index=True)

    # save manifest (after all optional entries)
    manifest.to_csv(outdir/"ect_output_manifest.csv", index=False)

    # consistency check
    required = [outdir/fn for fn in [
        "ect_background_profile.csv","ect_distance_time_table.csv",
        "ect_jwst_age_grid.csv","ect_jwst_key_rows.csv",
        "ect_benchmark_summary.csv","ect_run_metadata.csv",
        "ect_convergence_diagnostics.csv",
        "ect_panel_ab_background.csv","ect_panel_cd_growth_age.csv",
        "ect_linear_growth_table.csv","ect_structure_proxies.csv",
        "ect_output_manifest.csv"]]
    missing = [f.name for f in required if not f.exists()]
    if missing:
        raise RuntimeError(f"Missing required artefacts: {missing}")

    # figures
    make_figure(full, summary, outdir/"ect_hubble_jwst_background_bw", p)
    if args.scan:
        if p.closure_mode != "benchmark":
            print("Scan figure is benchmark-only; skipping (closure_mode != benchmark).")
        else:
            make_scan_figure(outdir/"ect_h0_scan_bw", p)

    saved_files = [
        "ect_background_profile.csv","ect_distance_time_table.csv",
        "ect_jwst_age_grid.csv","ect_jwst_key_rows.csv",
        "ect_benchmark_summary.csv","ect_run_metadata.csv",
        "ect_convergence_diagnostics.csv",
        "ect_panel_ab_background.csv","ect_panel_cd_growth_age.csv",
        "ect_linear_growth_table.csv","ect_structure_proxies.csv",
        "ect_output_manifest.csv",
        "ect_hubble_jwst_background_bw.pdf","ect_hubble_jwst_background_bw.png",
    ]
    if args.scan and p.closure_mode=="benchmark":
        saved_files += ["ect_h0_scan_bw.pdf","ect_h0_scan_bw.png"]
    if args.validate_multiseed:
        saved_files.append("ect_multiseed_comparison.csv")
    if args.compare_to_benchmark and not is_pure_bench:
        saved_files.append("ect_benchmark_comparison.csv")
    if args.scan_derived_grid:
        saved_files += ["ect_derived_grid_scan.csv", "ect_derived_candidate_points.csv"]
    print("\nSaved artefacts:")
    for fn in saved_files:
        print(f"  - {fn}")

if __name__ == "__main__":
    main()
