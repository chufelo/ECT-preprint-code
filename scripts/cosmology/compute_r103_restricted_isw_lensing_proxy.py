#!/usr/bin/env python3
"""Restricted ISW/lensing proxy for one frozen R103 two-slope state.

This is deliberately not a gauge-complete ECT perturbation calculation.
It asks a narrower conditional question.  If Jordan dust is conserved,
the scalar is massless and unmixed on the selected sub-horizon scales,
the photon and matter metrics coincide, the gravitational slip vanishes,
and Sigma_QS=F0/F, what instantaneous Weyl-amplitude and ISW-source proxies
follow from the already frozen two-slope background and growth equation?

The background and growth systems are reconstructed independently here.
DOP853 and Radau are run separately.  The analytic logarithmic derivative
of the Weyl proxy is also checked by fourth-order finite differences.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp


HERE = Path(__file__).resolve().parent
LATEX_ROOT = HERE.parents[1]
PACKAGE = LATEX_ROOT
OUT = LATEX_ROOT / 'data/cosmology_r103'
JSON_OUT = OUT / 'R103_RESTRICTED_ISW_LENSING_PROXY_v1.json'

SOURCE_SCRIPT = HERE / 'compute_r103_two_slope_conditional_observables.py'
SOURCE_JSON = OUT / 'R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json'

# Frozen near-GR two-slope action/state used by the R103 conditional-observable
# calculation.  H and all times remain in the same dimensionless units.
A = 0.01
C = 0.01
B = 0.03
KAPPA = 10.0
RHO_M0 = 0.9
RHO_R0 = 3.0e-4
V_MINUS = 0.82485
V_PLUS = 1.27485
N_INITIAL = -60.0
N_GROWTH = -float(np.log(101.0))
Z_EVAL = (0.0, 0.5, 1.0, 2.0)
FD_STEPS = (1.0e-4, 5.0e-5)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def background_point(n: float, q: float, p: float) -> dict[str, float]:
    """Exact homogeneous equations inside the supplied scalar action."""
    f = float(np.exp(A * q))
    f_q = A * f
    f_qq = A * A * f
    kinetic = KAPPA * f
    kinetic_q = A * kinetic
    potential = V_MINUS * np.exp(C * q) + V_PLUS * np.exp(B * q)
    potential_q = C * V_MINUS * np.exp(C * q) + B * V_PLUS * np.exp(B * q)
    rho_m = RHO_M0 * np.exp(-3.0 * n)
    rho_r = RHO_R0 * np.exp(-4.0 * n)
    denominator = 3.0 * f + 3.0 * f_q * p - 0.5 * kinetic * p * p
    if not np.isfinite(denominator) or denominator <= 0.0:
        raise FloatingPointError("non-positive Friedmann denominator")
    hubble = float(np.sqrt((rho_m + rho_r + potential) / denominator))
    q_dot = hubble * p
    rhs_ray = -(
        rho_m
        + 4.0 * rho_r / 3.0
        + kinetic * q_dot * q_dot
        + f_qq * q_dot * q_dot
        - hubble * f_q * q_dot
    )
    rhs_scalar = (
        -3.0 * kinetic * hubble * q_dot
        - 0.5 * kinetic_q * q_dot * q_dot
        - potential_q
        + 6.0 * f_q * hubble * hubble
    )
    h_dot, q_ddot = np.linalg.solve(
        np.array([[2.0 * f, f_q], [-3.0 * f_q, kinetic]]),
        np.array([rhs_ray, rhs_scalar]),
    )
    return {
        "H": hubble,
        "Hprime_over_H": float(h_dot / hubble**2),
        "p_prime": float(q_ddot / hubble**2 - p * h_dot / hubble**2),
        "F": f,
        "rho_m": float(rho_m),
        "rho_r": float(rho_r),
        "friedmann_denominator": float(denominator),
        "response_determinant": float(2.0 * f * kinetic + 3.0 * f_q**2),
    }


def integrate_background(method: str):
    def rhs(n: float, y: np.ndarray) -> np.ndarray:
        point = background_point(n, float(y[0]), float(y[1]))
        return np.array([y[1], point["p_prime"]])

    sol = solve_ivp(
        rhs,
        (N_INITIAL, 0.0),
        np.array([0.0, 0.0]),
        method=method,
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.02,
        dense_output=True,
    )
    if not sol.success:
        raise RuntimeError(f"{method} background failure: {sol.message}")
    return sol


def build_solution(method: str, omega_control: dict[str, float]):
    """Run one background/growth method with one frozen control state."""
    bg = integrate_background(method)
    q0, p0 = map(float, bg.y[:, -1])
    today = background_point(0.0, q0, p0)
    f0 = today["F"]
    h0 = today["H"]

    def model_point(n: float) -> dict[str, float]:
        q, p = map(float, bg.sol(n))
        point = background_point(n, q, p)
        point.update({"q": q, "p": p})
        return point

    om = omega_control["Omega_m0"]
    orad = omega_control["Omega_r0"]
    olam = omega_control["Omega_Lambda0"]

    def e_control(n: float) -> float:
        return float(np.sqrt(
            orad * np.exp(-4.0 * n)
            + om * np.exp(-3.0 * n)
            + olam
        ))

    def growth_model_rhs(n: float, y: np.ndarray) -> np.ndarray:
        point = model_point(n)
        # This is the deliberately restricted R103 closure, not a general
        # scalar-tensor perturbation theorem.
        omega_m_fixed = point["rho_m"] / (3.0 * f0 * point["H"]**2)
        sigma_qs = f0 / point["F"]
        d, dprime = y
        return np.array([
            dprime,
            -(2.0 + point["Hprime_over_H"]) * dprime
            + 1.5 * omega_m_fixed * sigma_qs * d,
        ])

    def growth_control_rhs(n: float, y: np.ndarray) -> np.ndarray:
        e = e_control(n)
        hprime_over_h = -(
            4.0 * orad * np.exp(-4.0 * n)
            + 3.0 * om * np.exp(-3.0 * n)
        ) / (2.0 * e * e)
        omega_m = om * np.exp(-3.0 * n) / (e * e)
        d, dprime = y
        return np.array([
            dprime,
            -(2.0 + hprime_over_h) * dprime + 1.5 * omega_m * d,
        ])

    gm = solve_ivp(
        growth_model_rhs,
        (N_GROWTH, 0.0),
        np.array([1.0, 1.0]),
        method=method,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
        dense_output=True,
    )
    gc = solve_ivp(
        growth_control_rhs,
        (N_GROWTH, 0.0),
        np.array([1.0, 1.0]),
        method=method,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
        dense_output=True,
    )
    if not gm.success or not gc.success:
        raise RuntimeError(f"{method} growth failure")

    return {
        "method": method,
        "background": bg,
        "model_point": model_point,
        "growth_model": gm,
        "growth_control": gc,
        "F0": f0,
        "H0": h0,
        "E_control": e_control,
    }


def q_weyl_model(bundle: dict, n: float) -> float:
    d = float(bundle["growth_model"].sol(n)[0])
    point = bundle["model_point"](n)
    f_rel = point["F"] / bundle["F0"]
    return float(d / (np.exp(n) * f_rel))


def q_weyl_control(bundle: dict, n: float) -> float:
    d = float(bundle["growth_control"].sol(n)[0])
    return float(d / np.exp(n))


def derivative_fd(fun, n: float, h: float) -> float:
    """Fourth-order derivative, one-sided only at today's endpoint."""
    if abs(n) < 1.0e-14:
        return float(
            (25.0 * fun(n) - 48.0 * fun(n - h) + 36.0 * fun(n - 2.0 * h)
             - 16.0 * fun(n - 3.0 * h) + 3.0 * fun(n - 4.0 * h))
            / (12.0 * h)
        )
    return float(
        (fun(n - 2.0 * h) - 8.0 * fun(n - h) + 8.0 * fun(n + h)
         - fun(n + 2.0 * h))
        / (12.0 * h)
    )


def row_for(bundle: dict, z: float) -> dict[str, float | dict[str, float]]:
    n = -float(np.log1p(z))
    a_scale = float(np.exp(n))
    point = bundle["model_point"](n)
    dm, dmp = map(float, bundle["growth_model"].sol(n))
    dc, dcp = map(float, bundle["growth_control"].sol(n))
    f_growth = dmp / dm
    f_growth_control = dcp / dc
    f_rel = point["F"] / bundle["F0"]
    sigma_qs = 1.0 / f_rel
    dlnf_dn = A * point["p"]

    q_model = dm / (a_scale * f_rel)
    q_control = dc / a_scale
    log_slope_model = f_growth - 1.0 - dlnf_dn
    log_slope_control = f_growth_control - 1.0
    dqdn_model = q_model * log_slope_model
    dqdn_control = q_control * log_slope_control
    e_model = point["H"] / bundle["H0"]
    e_control = bundle["E_control"](n)
    source_model = a_scale * e_model * dqdn_model
    source_control = a_scale * e_control * dqdn_control

    finite_difference = {}
    for h in FD_STEPS:
        key = f"h={h:.0e}"
        fd_model = derivative_fd(lambda x: q_weyl_model(bundle, x), n, h)
        fd_control = derivative_fd(lambda x: q_weyl_control(bundle, x), n, h)
        finite_difference[key] = {
            "dQdN_model": fd_model,
            "dQdN_control": fd_control,
            "model_absolute_error": abs(fd_model - dqdn_model),
            "control_absolute_error": abs(fd_control - dqdn_control),
            "model_relative_error": abs(fd_model / dqdn_model - 1.0),
            "control_relative_error": abs(fd_control / dqdn_control - 1.0),
        }

    return {
        "z": z,
        "N": n,
        "a": a_scale,
        "E_model": e_model,
        "E_control": e_control,
        "F_over_F0": f_rel,
        "Sigma_QS_assumed": sigma_qs,
        "D_model_same_primordial_norm": dm,
        "D_control_same_primordial_norm": dc,
        "growth_rate_f_model": f_growth,
        "growth_rate_f_control": f_growth_control,
        "dlnF_dN": dlnf_dn,
        "Q_W_model": q_model,
        "Q_W_control": q_control,
        "Q_W_ratio_model_over_control": q_model / q_control,
        "delta_Q_W_percent": 100.0 * (q_model / q_control - 1.0),
        "dlnQ_W_dN_model": log_slope_model,
        "dlnQ_W_dN_control": log_slope_control,
        "dQ_W_dN_model_analytic": dqdn_model,
        "dQ_W_dN_control_analytic": dqdn_control,
        "S_ISW_proxy_model": source_model,
        "S_ISW_proxy_control": source_control,
        "S_ISW_proxy_ratio_model_over_control": source_model / source_control,
        "delta_S_ISW_proxy_percent": 100.0 * (source_model / source_control - 1.0),
        "finite_difference": finite_difference,
    }


def main() -> None:
    # The comparator densities are frozen by today's model state exactly as in
    # the owning conditional-observable calculation.
    bg_primary = integrate_background("DOP853")
    q0, p0 = map(float, bg_primary.y[:, -1])
    today = background_point(0.0, q0, p0)
    omega_m0 = RHO_M0 / (3.0 * today["F"] * today["H"]**2)
    omega_r0 = RHO_R0 / (3.0 * today["F"] * today["H"]**2)
    omega_control = {
        "Omega_m0": float(omega_m0),
        "Omega_r0": float(omega_r0),
        "Omega_Lambda0": float(1.0 - omega_m0 - omega_r0),
    }

    primary = build_solution("DOP853", omega_control)
    secondary = build_solution("Radau", omega_control)
    rows_primary = [row_for(primary, z) for z in Z_EVAL]
    rows_secondary = [row_for(secondary, z) for z in Z_EVAL]

    cross_method = []
    for rp, rs in zip(rows_primary, rows_secondary, strict=True):
        cross_method.append({
            "z": rp["z"],
            "Q_W_model_absolute_difference": abs(rp["Q_W_model"] - rs["Q_W_model"]),
            "Q_W_control_absolute_difference": abs(rp["Q_W_control"] - rs["Q_W_control"]),
            "S_model_absolute_difference": abs(rp["S_ISW_proxy_model"] - rs["S_ISW_proxy_model"]),
            "S_control_absolute_difference": abs(rp["S_ISW_proxy_control"] - rs["S_ISW_proxy_control"]),
            "Q_W_model_relative_difference": abs(rp["Q_W_model"] / rs["Q_W_model"] - 1.0),
            "S_model_relative_difference": abs(rp["S_ISW_proxy_model"] / rs["S_ISW_proxy_model"] - 1.0),
        })

    max_fd_rel = max(
        entry["model_relative_error"]
        for row in rows_primary
        for entry in row["finite_difference"].values()
    )
    max_fd_control_rel = max(
        entry["control_relative_error"]
        for row in rows_primary
        for entry in row["finite_difference"].values()
    )
    max_q_method_rel = max(row["Q_W_model_relative_difference"] for row in cross_method)
    max_s_method_rel = max(row["S_model_relative_difference"] for row in cross_method)

    grid = np.linspace(N_INITIAL, 0.0, 3001)
    bg_checks = [primary["model_point"](float(n)) for n in grid]
    checks = {
        "source_files_exist": SOURCE_SCRIPT.is_file() and SOURCE_JSON.is_file(),
        "background_F_positive": min(row["F"] for row in bg_checks) > 0.0,
        "background_H_positive": min(row["H"] for row in bg_checks) > 0.0,
        "background_friedmann_denominator_positive": min(
            row["friedmann_denominator"] for row in bg_checks
        ) > 0.0,
        "background_response_determinant_positive": min(
            row["response_determinant"] for row in bg_checks
        ) > 0.0,
        "DOP853_Radau_Q_relative_below_2e_minus_10": max_q_method_rel < 2.0e-10,
        "DOP853_Radau_ISW_source_relative_below_2e_minus_9": max_s_method_rel < 2.0e-9,
        "analytic_FD_model_relative_below_2e_minus_7": max_fd_rel < 2.0e-7,
        "analytic_FD_control_relative_below_2e_minus_7": max_fd_control_rel < 2.0e-7,
        "same_primordial_growth_initial_conditions": bool(
            np.array_equal(primary["growth_model"].y[:, 0], np.array([1.0, 1.0]))
            and np.array_equal(primary["growth_control"].y[:, 0], np.array([1.0, 1.0]))
        ),
    }

    payload = {
        "date": "2026-07-18",
        "status": {
            "background": "Level A inside the supplied frozen two-slope action/state",
            "proxy_algebra": "Level A under the explicitly imposed limiting assumptions",
            "source_model": "Level C restricted quasistatic completion diagnostic",
            "data": "untested; no data or likelihood used",
            "ECT_specific": "Open; no gauge-complete perturbation action or metric bridge",
            "publication_verdict": "PROXY ONLY; NOT A PHYSICAL ECT ISW OR LENSING PREDICTION",
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "immutable_inputs": {
            "source_script": str(SOURCE_SCRIPT.relative_to(PACKAGE)),
            "source_script_sha256": sha256(SOURCE_SCRIPT),
            "source_json": str(SOURCE_JSON.relative_to(PACKAGE)),
            "source_json_sha256": sha256(SOURCE_JSON),
            "action_state": {
                "a": A,
                "b": B,
                "c": C,
                "kappa": KAPPA,
                "rho_m0": RHO_M0,
                "rho_r0": RHO_R0,
                "V_minus": V_MINUS,
                "V_plus": V_PLUS,
                "N_initial": N_INITIAL,
                "N_growth": N_GROWTH,
            },
            "control_state": omega_control,
            "evaluation_redshifts": list(Z_EVAL),
            "finite_difference_steps_in_N": list(FD_STEPS),
        },
        "assumptions": [
            "conserved pressureless Jordan-frame dust",
            "physical matter and photon metrics coincide",
            "sub-horizon quasistatic limit",
            "negligible scalar mass, mixing, scale dependence, radiation perturbations, and anisotropic stress",
            "zero gravitational slip, Phi=Psi",
            "Sigma_QS=F0/F",
            "same primordial growth normalization D=1 and dD/dN=1 at z=100",
            "flat radiation+matter+constant-source control with the same present density fractions",
        ],
        "definitions": {
            "F_relative": "F(N)/F(0)",
            "Q_W": "D/[a F_relative] for the model and D/a for the control",
            "dlnQ_W_dN": "f-1-dlnF/dN",
            "S_ISW_proxy": "(a H/H0) dQ_W/dN",
            "physical_sign_guard": (
                "for a positive overdensity and the stated Poisson convention, "
                "d(Phi+Psi)/deta is proportional to -S_ISW_proxy"
            ),
        },
        "primary_method": "DOP853",
        "secondary_method": "Radau",
        "rows_primary": rows_primary,
        "rows_secondary": rows_secondary,
        "cross_method": cross_method,
        "validation_summary": {
            "max_model_Q_W_relative_DOP853_Radau_difference": max_q_method_rel,
            "max_model_S_relative_DOP853_Radau_difference": max_s_method_rel,
            "max_model_analytic_FD_relative_difference": max_fd_rel,
            "max_control_analytic_FD_relative_difference": max_fd_control_rel,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "falsifiers_and_missing_owners": [
            "a gauge-reduced quadratic perturbation action may produce a different Poisson kernel or slip",
            "a finite scalar mass or mode mixing makes Sigma scale dependent and invalidates Sigma_QS=F0/F",
            "a distinct photon metric changes the Weyl map and lensing kernel",
            "radiation, neutrino anisotropic stress, initial isocurvature, and super-horizon evolution are omitted",
            "no line-of-sight source distribution, transfer spectrum, nonlinear correction, or covariance is included",
        ],
        "interpretation_guard": (
            "The rows quantify only a restricted limiting proxy for one supplied action/state. "
            "They cannot be called ECT C_l, weak-lensing, CMB-lensing, ISW, or ISW-galaxy predictions."
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
