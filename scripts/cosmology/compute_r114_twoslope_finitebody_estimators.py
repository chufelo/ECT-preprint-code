#!/usr/bin/env python3
"""R114 publication owner for two-slope finite-body estimators.

This calculation is deliberately model-internal.  It derives and solves the
static scalar-only BVP for the supplied two-slope scalar-tensor family

    f=f_* exp(aq), K=kappa f,
    V=V_- exp(cq)+V_+ exp(bq), 0<c<2a<b,

after y=exp(aq).  It does not identify the BVP far-tail ratio with the
physical finite-body sensitivity alpha_A.  The Cassini rows are therefore
reported as required physical-charge targets, not as passes/fails of the BVP.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_bvp
from scipy.optimize import brentq
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


LATEX_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = LATEX_ROOT / "data" / "cosmology_r114"
R105_INPUT = DATA_DIR / "R114_R105_ACTION_STATE_INPUT_SNAPSHOT_v1.csv"
OUT_JSON = DATA_DIR / "R114_TWOSLOPE_FINITEBODY_TARGETS_v1.json"
OUT_BVP_CSV = DATA_DIR / "R114_TWOSLOPE_FINITEBODY_GRID_v1.csv"
OUT_TARGET_CSV = DATA_DIR / "R114_EARLYG_CASSINI_CHARGE_TARGETS_v1.csv"
OUT_RUNTIME = DATA_DIR / "R114_TWOSLOPE_FINITEBODY_RUNTIME_v1.json"

# The named cosmological slopes a=c=0.01, b=0.03 imply m=c/a=1,n=b/a=3.
M_POWER = 1.0
N_POWER = 3.0
R_BODY = 1.0  # m_out R
WIDTH = 0.03
XMIN = 1.0e-5
XMAX = 15.0
R_VALUES = [0.0, 0.5, 0.9, 0.99]
# eta is the common linearised load; it keeps the linear reference identical
# while the vacuum-wall fraction r is varied.
ETA_VALUES = [3.0, 33.0, 333.0, 3333.0]
CASSINI_DELTA_GAMMA = 2.3e-5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body_shape(x: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 - np.tanh((x - R_BODY) / WIDTH))


def mesh() -> np.ndarray:
    return np.unique(
        np.r_[np.geomspace(XMIN, 0.2, 150),
              np.linspace(0.2, 0.85, 150),
              np.linspace(0.85, 1.15, 700),
              np.linspace(1.15, XMAX, 650)]
    )


def nonlinear_rhs(u: np.ndarray, x: np.ndarray, r: float, eta: float) -> np.ndarray:
    denom = N_POWER - M_POWER * r
    vacuum = (
        u**N_POWER - r * u**M_POWER - (1.0 - r)
    ) / denom
    return vacuum - eta * body_shape(x)


def rhs_derivative(u: np.ndarray, r: float) -> np.ndarray:
    return (
        N_POWER * u ** (N_POWER - 1.0)
        - M_POWER * r * u ** (M_POWER - 1.0)
    ) / (N_POWER - M_POWER * r)


def interior_root(r: float, eta: float) -> float:
    f = lambda u: float(nonlinear_rhs(np.asarray(u), np.asarray(0.0), r, eta))
    hi = max(2.0, (eta * (N_POWER - M_POWER * r) + 2.0) ** (1.0 / N_POWER) * 3)
    while f(hi) <= 0:
        hi *= 2
    return brentq(f, 1.0, hi, xtol=1e-14, rtol=1e-14)


def far_amplitude(solution, linear: bool = False) -> tuple[float, float]:
    xs = np.linspace(5.0, 9.0, 81)
    vals = solution.sol(xs)[0]
    delta = vals if linear else vals - 1.0
    amps = xs * np.exp(xs) * delta
    mean = float(np.mean(amps))
    spread = float((np.max(amps) - np.min(amps)) / max(abs(mean), 1e-300))
    return mean, spread


def solve_linear(eta: float):
    x = mesh()
    h = body_shape(x)
    guess = eta * h / (1.0 + eta ** (2.0 / 3.0))
    y0 = np.vstack((guess, np.gradient(guess, x)))

    def ode(xv, yv):
        v, dv = yv
        return np.vstack((dv, v - eta * body_shape(xv) - 2.0 * dv / xv))

    def bc(ya, yb):
        return np.array([ya[1], yb[1] + (1.0 + 1.0 / XMAX) * yb[0]])

    sol = solve_bvp(ode, bc, x, y0, tol=2e-7, max_nodes=100_000)
    if sol.status != 0:
        raise RuntimeError(f"linear BVP failed eta={eta}: {sol.message}")
    return sol


def solve_nonlinear(r: float, eta: float, previous=None):
    x = mesh()
    root = interior_root(r, eta)
    if previous is None:
        u = 1.0 + (root - 1.0) * 0.5 * (1.0 - np.tanh((x - R_BODY) / 0.15))
        du = np.gradient(u, x)
        guess = np.vstack((u, du))
    else:
        guess = previous.sol(x)
        old_center = max(float(guess[0, 0]) - 1.0, 1e-14)
        scale = (root - 1.0) / old_center
        guess[0] = 1.0 + (guess[0] - 1.0) * scale
        guess[1] *= scale

    def ode(xv, yv):
        u, du = yv
        return np.vstack((du, nonlinear_rhs(u, xv, r, eta) - 2.0 * du / xv))

    def bc(ya, yb):
        return np.array([
            ya[1],
            yb[1] + (1.0 + 1.0 / XMAX) * (yb[0] - 1.0),
        ])

    sol = solve_bvp(ode, bc, x, guess, tol=2e-6, max_nodes=150_000)
    if sol.status != 0:
        raise RuntimeError(f"nonlinear BVP failed r={r},eta={eta}: {sol.message}")
    return sol, root


def finite_difference_check(r: float, eta: float, bvp_solution, h: float = 0.005) -> dict:
    """Independent sparse Newton solve for w=x(u-1), with exact Robin tail."""
    n_intervals = int(round(XMAX / h))
    x = np.linspace(0.0, XMAX, n_intervals + 1)
    w = x * (bvp_solution.sol(np.maximum(x, XMIN))[0] - 1.0)
    w[0] = 0.0

    def residual_jac(wf):
        xi = x[1:-1]
        ui = 1.0 + wf[1:-1] / xi
        f_int = (
            (wf[:-2] - 2.0 * wf[1:-1] + wf[2:]) / h**2
            - xi * nonlinear_rhs(ui, xi, r, eta)
        )
        f_bc = (3*wf[-1] - 4*wf[-2] + wf[-3])/(2*h) + wf[-1]
        f = np.r_[f_int, f_bc]
        size = n_intervals
        jac = lil_matrix((size, size))
        rows = np.arange(n_intervals - 1)
        jac[rows, rows] = -2.0 / h**2 - rhs_derivative(ui, r)
        if n_intervals > 2:
            jac[rows[1:], rows[1:] - 1] = 1.0 / h**2
            jac[rows[:-1], rows[:-1] + 1] = 1.0 / h**2
        jac[n_intervals - 2, n_intervals - 1] = 1.0 / h**2
        jac[n_intervals - 1, n_intervals - 3] = 1.0 / (2*h)
        jac[n_intervals - 1, n_intervals - 2] = -4.0 / (2*h)
        jac[n_intervals - 1, n_intervals - 1] = 3.0 / (2*h) + 1.0
        return f, jac.tocsc()

    history = []
    for it in range(20):
        f, jac = residual_jac(w)
        norm = float(np.max(np.abs(f)))
        history.append(norm)
        if norm < 2e-8:
            break
        delta = spsolve(jac, -f)
        base = norm
        damping = 1.0
        for _ in range(30):
            trial = w.copy()
            trial[1:] += damping * delta
            if np.any(1.0 + trial[1:] / x[1:] <= 0):
                damping *= 0.5
                continue
            ft, _ = residual_jac(trial)
            if float(np.max(np.abs(ft))) < base:
                w = trial
                break
            damping *= 0.5
        else:
            raise RuntimeError("finite-difference Newton line search failed")
    else:
        raise RuntimeError("finite-difference Newton did not converge")

    xs = np.linspace(5.0, 9.0, 81)
    wf = np.interp(xs, x, w)
    amps = np.exp(xs) * wf
    amp = float(np.mean(amps))
    bvp_amp, _ = far_amplitude(bvp_solution)
    return {
        "h": h,
        "iterations": it + 1,
        "max_residual": history[-1],
        "far_amplitude": amp,
        "bvp_far_amplitude": bvp_amp,
        "relative_amplitude_difference": abs(amp-bvp_amp)/max(abs(bvp_amp),1e-300),
    }


def bvp_grid() -> tuple[list[dict], dict]:
    # The reference equation is exactly linear in eta.  Solving it once at
    # eta=1 avoids an otherwise ill-conditioned large-amplitude collocation
    # initial guess and provides an exact scaling check rather than a fit.
    linear_unit = solve_linear(1.0)
    linear_unit_amp = far_amplitude(linear_unit, linear=True)[0]
    linear_amp = {eta: eta * linear_unit_amp for eta in ETA_VALUES}
    rows = []
    crosschecks = []
    for r in R_VALUES:
        previous = None
        for eta in ETA_VALUES:
            sol, uin = solve_nonlinear(r, eta, previous)
            previous = sol
            amp, spread = far_amplitude(sol)
            lin_amp = linear_amp[eta]
            delta_s = eta * (N_POWER - M_POWER*r) / (1.0-r)
            min_ratio = math.sqrt(rhs_derivative(np.asarray(uin), r))
            row = {
                "r_vacuum_wall_fraction": r,
                "eta_common_linear_load": eta,
                "density_contrast": 1.0 + delta_s,
                "u_in_homogeneous_root": uin,
                "m_in_R_over_m_out_R": min_ratio,
                "u_center": float(sol.sol(XMIN)[0]),
                "u_surface": float(sol.sol(R_BODY)[0]),
                "nonlinear_far_amplitude": amp,
                "linear_far_amplitude_same_load": lin_amp,
                "far_tail_suppression_proxy": amp/lin_amp,
                "far_amplitude_relative_spread_x5_x9": spread,
                "solver_nodes": int(sol.x.size),
                "max_collocation_rms_residual": float(np.max(sol.rms_residuals)),
            }
            rows.append(row)
            if (r, eta) in {(0.5,33.0),(0.99,3333.0)}:
                cc = finite_difference_check(r,eta,sol)
                cc.update({"r":r,"eta":eta})
                crosschecks.append(cc)
    return rows, {"finite_difference_crosschecks": crosschecks}


def cassini_targets() -> list[dict]:
    x_bound = CASSINI_DELTA_GAMMA / (4.0 - 2.0*CASSINI_DELTA_GAMMA)
    rows=[]
    with R105_INPUT.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    for item in source_rows:
        a=float(item["a"]); k=float(item["kappa"])
        alpha2=a*a/(4*k+6*a*a)
        gamma=(1-2*alpha2)/(1+2*alpha2)
        smax=min(1.0,x_bound/alpha2)
        rows.append({
            "a":a,
            "kappa":k,
            "G_eff_early_over_today_long_range":float(item["G_eff_early_over_today_long_range"]),
            "growth_D_ratio_z10_same_primordial":float(item["growth_D_ratio_z10_same_primordial"]),
            "alpha_infinity_squared":alpha2,
            "gamma_unscreened_recomputed":gamma,
            "gamma_unscreened_input":float(item["gamma_PPN_unscreened_massless"]),
            "required_solar_charge_factor_max":smax,
            "required_suppression_factor":1.0/smax,
            "unscreened_pass":bool(smax>=1.0),
        })
    return rows


def write_csv(path:Path,rows:list[dict]):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows,checks=bvp_grid()
    targets=cassini_targets()
    write_csv(OUT_BVP_CSV,rows)
    write_csv(OUT_TARGET_CSV,targets)
    max_gamma_diff=max(abs(x["gamma_unscreened_recomputed"]-x["gamma_unscreened_input"]) for x in targets)
    max_fd=max(x["relative_amplitude_difference"] for x in checks["finite_difference_crosschecks"])
    payload={
        "date":"2026-07-20",
        "schema":"ECT-R114-two-slope-finite-body-owner-v1",
        "supersedes":"R106 research-only finite-body bundle; numerical definitions and values are preserved",
        "status":"LEVEL_A_INSIDE_DECLARED_STATIC_SCALAR_PROXY__PHYSICAL_CHARGE_OPEN",
        "input":{"path":"data/cosmology_r114/R114_R105_ACTION_STATE_INPUT_SNAPSHOT_v1.csv","sha256":sha256(R105_INPUT)},
        "derivation":{
            "dimensional_equation":"laplacian(y)=A_plus*y^n-A_minus*y^m-D_rho*rho",
            "A_plus":"a*(b-2a)*V_plus/(f_star*(kappa+3*a^2/2))",
            "A_minus":"a*(2a-c)*V_minus/(f_star*(kappa+3*a^2/2))",
            "D_rho":"a^2/(2*f_star*(kappa+3*a^2/2))",
            "dimensionless_equation":"u''+2u'/x=[u^n-r*u^m-(1-r)*s(x)]/(n-m*r)",
            "definitions":"u=y/y_out, x=m_out*r_phys, r=A_minus*y_out^m/(A_plus*y_out^n), n=b/a, m=c/a",
            "linear_load":"eta=(1-r)*(s_in-1)/(n-m*r)",
            "named_slopes":{"m":M_POWER,"n":N_POWER},
        },
        "bvp_inputs":{"m_out_R":R_BODY,"width":WIDTH,"r_values":R_VALUES,"eta_values":ETA_VALUES},
        "bvp_rows":rows,
        "cassini":{"delta_gamma":CASSINI_DELTA_GAMMA,"rows":targets},
        "checks":{
            **checks,
            "max_gamma_reconstruction_abs_difference":max_gamma_diff,
            "max_fd_vs_bvp_far_amplitude_relative_difference":max_fd,
            "all_collocation_residuals_below_2e_minus_6":all(x["max_collocation_rms_residual"]<2e-6 for x in rows),
            "all_suppression_proxies_between_zero_and_one":all(0<x["far_tail_suppression_proxy"]<1 for x in rows),
        },
        "guards":[
            "The BVP holds the metric fixed and prescribes density; it is not a coupled stellar/Solar solution.",
            "The far-tail amplitude ratio is not identified with alpha_A/alpha_infinity.",
            "The r/eta grid is a proof-of-class sensitivity grid, not a fit to the Sun or an ECT prediction.",
            "Cassini targets assume a long-range scalar and a weak unscreened test body.",
            "A physical pass requires m_A(phi_infinity), sensitivities, metric potentials, WEP and environment.",
        ],
    }
    payload["all_internal_gates_pass"]=(
        max_gamma_diff<1e-14 and max_fd<2e-3
        and payload["checks"]["all_collocation_residuals_below_2e_minus_6"]
        and payload["checks"]["all_suppression_proxies_between_zero_and_one"]
    )
    OUT_JSON.write_text(json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    OUT_RUNTIME.write_text(json.dumps({
        "scientific_payload":"data/cosmology_r114/R114_TWOSLOPE_FINITEBODY_TARGETS_v1.json",
        "python":platform.python_version(),
        "numpy":np.__version__,
        "scipy":scipy.__version__,
    },indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "all_internal_gates_pass":payload["all_internal_gates_pass"],
        "max_fd_vs_bvp":max_fd,
        "max_gamma_diff":max_gamma_diff,
        "min_suppression_proxy":min(x["far_tail_suppression_proxy"] for x in rows),
        "max_required_suppression_factor":max(x["required_suppression_factor"] for x in targets),
    },indent=2))


if __name__ == "__main__":
    main()
