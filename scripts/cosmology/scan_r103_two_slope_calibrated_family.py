#!/usr/bin/env python3
"""Deterministic calibrated scan of the c=a, b=3a two-slope family.

For every (a,kappa) point, the potential ratio is fixed by the vacuum
condition sigma_vac=0.  The early frozen scalar value and total potential
normalisation are then shot so that sigma(0)=0 and H(0)=1 with fixed present
Omega_m and Omega_r.  DOP853 performs the shooting; the frozen solution is
independently replayed with Radau.  All outputs are model-internal or
conditional completion diagnostics, not unique ECT predictions.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad, solve_ivp
from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent
OUT = (
    HERE.parents[1] / "data/cosmology_r103"
    if HERE.name == "cosmology" and HERE.parent.name == "scripts"
    else HERE.parent / "results"
)
JSON_OUT = OUT / "R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json"
CSV_OUT = OUT / "R103_TWO_SLOPE_CALIBRATED_SCAN_v1.csv"

N_START = -20.0
OMEGA_M0 = 0.315
OMEGA_R0 = 9.19e-5
RHO_M0 = 3.0 * OMEGA_M0
RHO_R0 = 3.0 * OMEGA_R0
A_VALUES = (0.01, 0.03, 0.08)
KAPPA_VALUES = (0.05, 1.0, 10.0)
Z_DIAGNOSTICS = (1.0, 10.0, 14.32, 20.0)
OMEGA_B_STD = 0.0493
OMEGA_GAMMA_STD = 5.45e-5
Z_DRAG_STD = 1059.94


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_e(n: float) -> float:
    omega_l0 = 1.0 - OMEGA_M0 - OMEGA_R0
    return float(np.sqrt(
        OMEGA_R0 * np.exp(-4.0 * n)
        + OMEGA_M0 * np.exp(-3.0 * n)
        + omega_l0
    ))


def reference_time(n: float) -> float:
    value, _ = quad(
        lambda nn: 1.0 / reference_e(nn), -60.0, n,
        epsabs=2e-12, epsrel=2e-12, limit=500,
    )
    return float(value)


def reference_distance(n: float) -> float:
    value, _ = quad(
        lambda nn: np.exp(-nn) / reference_e(nn), n, 0.0,
        epsabs=2e-12, epsrel=2e-12, limit=500,
    )
    return float(value)


def sound_speed_over_c(n: float) -> float:
    one_plus_z = np.exp(-n)
    baryon_loading = 3.0 * OMEGA_B_STD / (4.0 * OMEGA_GAMMA_STD * one_plus_z)
    return float(1.0 / np.sqrt(3.0 * (1.0 + baryon_loading)))


def make_model(a: float, kappa: float, q_initial: float, v_total: float):
    c = a
    b = 3.0 * a
    ratio = (b - 2.0 * a) / (2.0 * a - c)
    v_plus = v_total / (1.0 + ratio)
    v_minus = ratio * v_plus

    def point(n: float, q: float, p: float) -> dict[str, float]:
        f = float(np.exp(a * q))
        fq = a * f
        fqq = a * a * f
        kinetic = kappa * f
        kinetic_q = a * kinetic
        potential = v_minus * np.exp(c * q) + v_plus * np.exp(b * q)
        potential_q = c * v_minus * np.exp(c * q) + b * v_plus * np.exp(b * q)
        rho_m = RHO_M0 * np.exp(-3.0 * n)
        rho_r = RHO_R0 * np.exp(-4.0 * n)
        denominator = 3.0 * f + 3.0 * fq * p - 0.5 * kinetic * p * p
        if not np.isfinite(denominator) or denominator <= 0.0:
            raise FloatingPointError("non-positive Friedmann denominator")
        hubble = float(np.sqrt((rho_m + rho_r + potential) / denominator))
        qdot = hubble * p
        rhs_ray = -(
            rho_m + 4.0 * rho_r / 3.0 + kinetic * qdot * qdot
            + fqq * qdot * qdot - hubble * fq * qdot
        )
        rhs_scalar = (
            -3.0 * kinetic * hubble * qdot
            - 0.5 * kinetic_q * qdot * qdot
            - potential_q + 6.0 * fq * hubble * hubble
        )
        hdot, qddot = np.linalg.solve(
            np.array([[2.0 * f, fq], [-3.0 * fq, kinetic]]),
            np.array([rhs_ray, rhs_scalar]),
        )
        return {
            "H": hubble,
            "p_prime": float(qddot / hubble**2 - p * hdot / hubble**2),
            "Hprime_over_H": float(hdot / hubble**2),
            "F": f,
            "denominator": float(denominator),
            "determinant": float(2.0 * f * kinetic + 3.0 * fq * fq),
        }

    def rhs(n: float, state: np.ndarray) -> np.ndarray:
        q, p, elapsed = state
        del elapsed
        here = point(n, float(q), float(p))
        return np.array([p, here["p_prime"], 1.0 / here["H"]])

    def integrate(method: str, *, dense: bool = False, rtol: float = 2e-10):
        return solve_ivp(
            rhs, (N_START, 0.0), np.array([q_initial, 0.0, 0.0]),
            method=method, rtol=rtol, atol=rtol * 1e-2, max_step=0.03,
            dense_output=dense,
        )

    return point, integrate, {
        "c": c, "b": b, "ratio_Vminus_over_Vplus": ratio,
        "V_minus": v_minus, "V_plus": v_plus,
    }


def shoot(a: float, kappa: float) -> tuple[float, float, object, dict[str, float]]:
    v_guess = 3.0 * (1.0 - OMEGA_M0 - OMEGA_R0)

    def residual(x: np.ndarray) -> np.ndarray:
        q_initial = float(x[0])
        v_total = float(np.exp(x[1]))
        try:
            point, integrate, _ = make_model(a, kappa, q_initial, v_total)
            sol = integrate("DOP853", rtol=3e-9)
            if not sol.success:
                return np.array([1e3, 1e3])
            q0, p0, _ = map(float, sol.y[:, -1])
            h0 = point(0.0, q0, p0)["H"]
            return np.array([q0, h0 - 1.0])
        except (FloatingPointError, ValueError, np.linalg.LinAlgError):
            return np.array([1e3, 1e3])

    fit = least_squares(
        residual, np.array([0.0, np.log(v_guess)]),
        xtol=2e-12, ftol=2e-12, gtol=2e-12, max_nfev=80,
    )
    if not fit.success or np.linalg.norm(residual(fit.x), ord=np.inf) > 2e-8:
        raise RuntimeError(f"shooting failed for a={a}, kappa={kappa}: {fit.message}")
    q_initial = float(fit.x[0])
    v_total = float(np.exp(fit.x[1]))
    point, integrate, meta = make_model(a, kappa, q_initial, v_total)
    dop = integrate("DOP853", dense=True, rtol=1e-11)
    if not dop.success:
        raise RuntimeError(dop.message)
    return q_initial, v_total, dop, {**meta, "point": point, "integrate": integrate}


def main() -> None:
    rows: list[dict[str, object]] = []
    ref_age = reference_time(0.0)

    for kappa in KAPPA_VALUES:
        for a in A_VALUES:
            q_initial, v_total, dop, bundle = shoot(a, kappa)
            point = bundle.pop("point")
            integrate = bundle.pop("integrate")
            rad = integrate("Radau", dense=True, rtol=1e-11)
            if not rad.success:
                raise RuntimeError(rad.message)

            q0, p0, elapsed0 = map(float, dop.y[:, -1])
            q0r, p0r, elapsed0r = map(float, rad.y[:, -1])
            h0 = point(0.0, q0, p0)["H"]
            h0r = point(0.0, q0r, p0r)["H"]
            # Radiation-tail estimate from -infinity to the starting surface.
            qi, pi, _ = map(float, dop.y[:, 0])
            hi = point(N_START, qi, pi)["H"]
            tail = 1.0 / (2.0 * hi)
            age = h0 * (elapsed0 + tail)
            age_radau = h0r * (elapsed0r + tail)

            grid = np.linspace(N_START, 0.0, 2001)
            min_f = np.inf
            min_den = np.inf
            min_det = np.inf
            min_h = np.inf
            for n in grid:
                q, p, _ = map(float, dop.sol(float(n)))
                state = point(float(n), q, p)
                min_f = min(min_f, state["F"])
                min_den = min(min_den, state["denominator"])
                min_det = min(min_det, state["determinant"])
                min_h = min(min_h, state["H"])

            diagnostics: dict[str, object] = {}
            for z in Z_DIAGNOSTICS:
                n = -float(np.log1p(z))
                q, p, elapsed = map(float, dop.sol(n))
                here = point(n, q, p)
                time = h0 * (elapsed + tail)
                ref_time = reference_time(n)
                chi, _ = quad(
                    lambda nn: np.exp(-nn) * h0 / point(
                        float(nn), *map(float, dop.sol(float(nn))[:2])
                    )["H"],
                    n, 0.0, epsabs=3e-11, epsrel=3e-11, limit=300,
                )
                ref_chi = reference_distance(n)
                diagnostics[f"z={z:g}"] = {
                    "E": here["H"] / h0,
                    "delta_E_percent": 100.0 * (here["H"] / h0 / reference_e(n) - 1.0),
                    "H0_t": time,
                    "delta_t_percent": 100.0 * (time / ref_time - 1.0),
                    "H0_chi_over_c": float(chi),
                    "delta_chi_percent": 100.0 * (float(chi) / ref_chi - 1.0),
                }

            n_drag = -float(np.log1p(Z_DRAG_STD))
            rs_model, _ = quad(
                lambda nn: np.exp(-nn) * sound_speed_over_c(float(nn)) * h0
                / point(
                    float(nn), *map(float, dop.sol(float(nn))[:2])
                )["H"],
                N_START, n_drag, epsabs=3e-11, epsrel=3e-11, limit=300,
            )
            rs_reference, _ = quad(
                lambda nn: np.exp(-nn) * sound_speed_over_c(float(nn))
                / reference_e(float(nn)),
                N_START, n_drag, epsabs=3e-11, epsrel=3e-11, limit=300,
            )

            row = {
                "a": a,
                "c": a,
                "b": 3.0 * a,
                "kappa": kappa,
                "q_initial": q_initial,
                "F_initial_over_F_today": float(np.exp(a * q_initial)),
                "G_eff_early_over_today_long_range": float(np.exp(-a * q_initial)),
                "V_total_at_q0": v_total,
                **bundle,
                "q_today": q0,
                "dq_dN_today": p0,
                "H_today": h0,
                "minus_dlnF_dN_today": -a * p0,
                "omega_BD_unscreened": kappa / a**2,
                "gamma_PPN_unscreened_massless": (kappa + a**2) / (kappa + 2.0 * a**2),
                "beta_PPN_unscreened_constant_coupling": 1.0,
                "cassini_gamma_gate_2p3e_minus_5_unscreened": abs(
                    (kappa + a**2) / (kappa + 2.0 * a**2) - 1.0
                ) < 2.3e-5,
                "H0_r_s_over_c_conditional_standard_photon": float(rs_model),
                "H0_r_s_over_c_reference_same_inputs": float(rs_reference),
                "delta_r_s_percent": 100.0 * (float(rs_model) / float(rs_reference) - 1.0),
                "H0_fixed_acoustic_angle_proxy_from_67p4": 67.4 * float(rs_reference) / float(rs_model),
                "H0_t0": age,
                "delta_age_percent": 100.0 * (age / ref_age - 1.0),
                "DOP853_Radau_age_absolute_difference": abs(age - age_radau),
                "DOP853_Radau_q0_absolute_difference": abs(q0 - q0r),
                "DOP853_Radau_p0_absolute_difference": abs(p0 - p0r),
                "DOP853_Radau_H0_absolute_difference": abs(h0 - h0r),
                "min_F": min_f,
                "min_friedmann_denominator": min_den,
                "min_response_determinant": min_det,
                "min_H": min_h,
                "regular_positive": min(min_f, min_den, min_det, min_h) > 0.0,
                "diagnostics": diagnostics,
            }
            rows.append(row)

    checks = {
        "all_shooting_targets_q0_below_2e_minus_8": max(abs(float(r["q_today"])) for r in rows) < 2e-8,
        "all_shooting_targets_H0_below_2e_minus_8": max(abs(float(r["H_today"]) - 1.0) for r in rows) < 2e-8,
        "all_DOP853_Radau_age_below_2e_minus_9": max(float(r["DOP853_Radau_age_absolute_difference"]) for r in rows) < 2e-9,
        "all_regular_positive": all(bool(r["regular_positive"]) for r in rows),
        "vacuum_ratio_gives_sigma_vac_zero": all(abs(float(r["ratio_Vminus_over_Vplus"]) - 1.0) < 1e-14 for r in rows),
    }

    payload = {
        "date": "2026-07-18",
        "status": "Level A inside each supplied calibrated action/state; Level C completion scan; not a unique ECT prediction",
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "script_sha256": sha256(Path(__file__)),
        "frozen_protocol": {
            "N_start": N_START,
            "Omega_m0": OMEGA_M0,
            "Omega_r0": OMEGA_R0,
            "family": "c=a, b=3a, F=exp(a sigma), K=kappa F",
            "vacuum_root": "sigma_vac=0 via Vminus/Vplus=(b-2a)/(2a-c)",
            "shooting_variables": ["sigma(N_start)", "V_total_at_sigma=0"],
            "shooting_targets": ["sigma(0)=0", "H(0)=1"],
            "initial_velocity": "d sigma/dN at N_start = 0",
            "reference": "flat radiation+matter+constant-source control with the same Omega_m0 and Omega_r0",
            "conditional_standard_photon_layer": {
                "Omega_b": OMEGA_B_STD,
                "Omega_gamma": OMEGA_GAMMA_STD,
                "z_drag": Z_DRAG_STD,
                "status": "illustrative standard photon/recombination inputs, not derived from ECT",
            },
        },
        "reference_age_H0t0": ref_age,
        "rows": rows,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_guard": (
            "large early-time age changes must be assessed jointly with Planck-mass drift, finite-body PPN, BBN/recombination, and perturbation gates; gamma_PPN is the unscreened massless scalar limit and does not exclude a future screened completion; the scan is not a fit"
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    flat_rows = []
    for row in rows:
        flat = {k: v for k, v in row.items() if k != "diagnostics"}
        for zkey, values in row["diagnostics"].items():
            for key, value in values.items():
                flat[f"{zkey}_{key}"] = value
        flat_rows.append(flat)
    with CSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
