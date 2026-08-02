#!/usr/bin/env python3
"""Reproduce the owner-specific early-response sensitivity envelope.

The manuscript coordinate is zeta_ER.  It is not the withdrawn universal ECT
epsilon and not the named two-slope orbit.  It is one explicitly declared
response-envelope stress test.  The same zeta_ER dresses matter and the
constant source but not radiation.  Its matter factor is counted once in the
growth and top-hat equations.

Outputs are Level A inside this supplied envelope for background, equality and
linear-growth algebra, and Level C for the top-hat/Press--Schechter sensitivity.
They are not a CMB, JWST or full cosmological likelihood.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq


HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "data/cosmology_r113"
JSON_OUT = OUT / "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.json"
CSV_OUT = OUT / "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv"

OMEGA_M = 0.315
OMEGA_R = 9.2e-5
OMEGA_L = 1.0 - OMEGA_M - OMEGA_R
Z_ON = 1000.0
Z_OBS = 10.0
NU = 5.0
COLLAPSE_DELTA = 1.0e7

ZETA_ER_VALUES = (
    1.5612556036955692e-6,
    0.007500442556492628,
    0.029588344765651916,
    0.033,
    0.037555,
)

EXPECTED = {
    1.5612556036955692e-6: (1.00000521, 1.00002541, 1.72676032, 1.00000016, 1.00013505, 1.00013091),
    0.007500442556492628: (1.02494986, 1.13195313, 1.72810966, 1.00078159, 1.86656763, 1.83082689),
    0.029588344765651916: (1.09767905, 1.66846599, 1.73234129, 1.00323220, 9.13465297, 8.51585875),
    0.033: (1.10882221, 1.77730862, 1.73302549, 1.00362844, 11.34568870, 10.50228040),
    0.037555: (1.12366682, 1.93658864, 1.73395051, 1.00416414, 14.99787480, 13.75594876),
}


def coefficients(n: float, zeta_er: float) -> dict[str, float]:
    a = math.exp(n)
    radiation = OMEGA_R * a**-4
    matter_grav = OMEGA_M * a ** (-3.0 - 2.0 * zeta_er)
    constant_source = OMEGA_L * a ** (-2.0 * zeta_er)
    e2 = radiation + matter_grav + constant_source
    hp = (
        -4.0 * radiation
        + (-3.0 - 2.0 * zeta_er) * matter_grav
        - 2.0 * zeta_er * constant_source
    ) / (2.0 * e2)
    return {
        "E": math.sqrt(e2),
        "Hprime_over_H": hp,
        "Omega_m_grav": matter_grav / e2,
    }


def growing_exponent(zeta_er: float, n: float) -> float:
    c = coefficients(n, zeta_er)
    b = 2.0 + c["Hprime_over_H"]
    return 0.5 * (-b + math.sqrt(b * b + 6.0 * c["Omega_m_grav"]))


def solve_growth(zeta_er: float, method: str) -> object:
    n0 = -math.log1p(Z_ON)
    p0 = growing_exponent(zeta_er, n0)

    def rhs(n: float, y: np.ndarray) -> np.ndarray:
        c = coefficients(n, zeta_er)
        return np.array([
            y[1],
            -(2.0 + c["Hprime_over_H"]) * y[1]
            + 1.5 * c["Omega_m_grav"] * y[0],
        ])

    sol = solve_ivp(
        rhs,
        (n0, 0.0),
        np.array([1.0, p0]),
        method=method,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
        dense_output=True,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol


def growth_ratio(zeta_er: float, method: str = "DOP853") -> float:
    n_obs = -math.log1p(Z_OBS)
    model = solve_growth(zeta_er, method)
    control = solve_growth(0.0, method)
    return float(model.sol(n_obs)[0] / control.sol(n_obs)[0])


def collapse_barrier(zeta_er: float, method: str = "DOP853") -> float:
    n0 = -math.log1p(Z_ON)
    n1 = -math.log1p(Z_OBS)
    target_y = math.log1p(COLLAPSE_DELTA)
    p0 = growing_exponent(zeta_er, n0)

    def objective(log_delta_i: float) -> float:
        delta_i = math.exp(log_delta_i)
        y0 = math.log1p(delta_i)
        v0 = p0 * delta_i / (1.0 + delta_i)

        def rhs(n: float, state: np.ndarray) -> np.ndarray:
            c = coefficients(n, zeta_er)
            expm1_y = math.expm1(min(float(state[0]), 25.0))
            return np.array([
                state[1],
                -(2.0 + c["Hprime_over_H"]) * state[1]
                + state[1] ** 2 / 3.0
                + 1.5 * c["Omega_m_grav"] * expm1_y,
            ])

        def event(_n: float, state: np.ndarray) -> float:
            return float(state[0]) - target_y

        event.terminal = True
        event.direction = 1
        sol = solve_ivp(
            rhs,
            (n0, n1),
            np.array([y0, v0]),
            method=method,
            rtol=2.0e-9,
            atol=2.0e-11,
            max_step=0.01,
            events=event,
        )
        if sol.t_events[0].size:
            return n1 - float(sol.t_events[0][0])
        return float(sol.y[0, -1]) - target_y

    log_delta_i = brentq(
        objective,
        math.log(1.0e-7),
        math.log(0.9),
        xtol=2.0e-11,
        rtol=2.0e-11,
    )
    delta_i = math.exp(log_delta_i)

    def linear_rhs(n: float, state: np.ndarray) -> np.ndarray:
        c = coefficients(n, zeta_er)
        return np.array([
            state[1],
            -(2.0 + c["Hprime_over_H"]) * state[1]
            + 1.5 * c["Omega_m_grav"] * state[0],
        ])

    linear = solve_ivp(
        linear_rhs,
        (n0, n1),
        np.array([delta_i, p0 * delta_i]),
        method=method,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=0.01,
    )
    if not linear.success:
        raise RuntimeError(linear.message)
    return float(linear.y[0, -1])


def equality_ratio(zeta_er: float) -> float:
    return (OMEGA_M / OMEGA_R) ** (2.0 * zeta_er / (1.0 - 2.0 * zeta_er))


def cumulative_ps_ratio(growth: float, barrier_ratio: float = 1.0) -> float:
    x = barrier_ratio / growth
    return math.erfc(NU * x / math.sqrt(2.0)) / math.erfc(NU / math.sqrt(2.0))


def publication_float(value: float, significant_digits: int = 13) -> float:
    """Freeze scientific values below the declared manuscript precision.

    Solver/runtime metadata and sub-publication last-bit residuals are not part
    of the scientific JSON hash.  They remain visible during execution.
    """
    return float(f"{value:.{significant_digits}g}")


def main() -> None:
    control_barrier = collapse_barrier(0.0)
    rows = []
    max_growth_solver_difference = 0.0
    max_expected_rounding_difference = 0.0

    for zeta_er in ZETA_ER_VALUES:
        d_dop = growth_ratio(zeta_er, "DOP853")
        d_rad = growth_ratio(zeta_er, "Radau")
        max_growth_solver_difference = max(max_growth_solver_difference, abs(d_dop - d_rad))
        delta_c = collapse_barrier(zeta_er)
        delta_ratio = delta_c / control_barrier
        eq_ratio = equality_ratio(zeta_er)
        ps_fixed = cumulative_ps_ratio(d_dop)
        ps_tophat = cumulative_ps_ratio(d_dop, delta_ratio)
        values = (d_dop, eq_ratio, delta_c, delta_ratio, ps_fixed, ps_tophat)
        max_expected_rounding_difference = max(
            max_expected_rounding_difference,
            max(abs(value - expected) for value, expected in zip(values, EXPECTED[zeta_er])),
        )
        rows.append({
            "zeta_ER": zeta_er,
            "D_over_D0_z10_zon1000": publication_float(d_dop),
            "equality_ratio": publication_float(eq_ratio),
            "delta_c": publication_float(delta_c),
            "delta_c_over_control": publication_float(delta_ratio),
            "cumulative_PS_ratio_nu5_fixed_barrier": publication_float(ps_fixed),
            "cumulative_PS_ratio_nu5_tophat_barrier": publication_float(ps_tophat),
        })

    checks = {
        "growth_DOP853_Radau_agree_below_5e_minus_9": max_growth_solver_difference < 5.0e-9,
        "published_8_decimal_rows_reproduced_below_6e_minus_8": max_expected_rounding_difference < 6.0e-8,
        "epsilon_zero_control_barrier_positive": control_barrier > 0.0,
        "all_rows_positive": all(all(value > 0.0 for value in row.values()) for row in rows),
    }
    payload = {
        "date": "2026-07-20",
        "status": (
            "Level A algebra/numerics inside the declared owner-specific zeta_ER envelope; "
            "Level C collapse and rare-tail sensitivity; not the withdrawn universal ECT epsilon, named "
            "two-slope orbit, CMB fit or JWST abundance prediction"
        ),
        "scientific_freeze_policy": (
            "Runtime versions and sub-publication last-bit solver residuals are emitted "
            "during execution but excluded from the scientific file hash; displayed "
            "outputs are frozen to 13 significant digits."
        ),
        "inputs": {
            "Omega_m": OMEGA_M,
            "Omega_r": OMEGA_R,
            "Omega_constant_source": OMEGA_L,
            "z_on": Z_ON,
            "z_observed": Z_OBS,
            "nu": NU,
            "collapse_delta_threshold": COLLAPSE_DELTA,
            "zeta_ER_values": list(ZETA_ER_VALUES),
        },
        "equations": {
            "background": "E^2=Omega_r exp(-4N)+Omega_m exp(-(3+2 zeta_ER)N)+Omega_L exp(-2 zeta_ER N)",
            "growth": "D_NN+(2+E_N/E)D_N-(3/2)Omega_m^grav D=0",
            "equality": "[(1+z_eq)/(1+z_eq0)]=(Omega_m/Omega_r)^[2 zeta_ER/(1-2 zeta_ER)]",
            "tophat": "delta_NN+(2+E_N/E)delta_N-(4/3)delta_N^2/(1+delta)-(3/2)Omega_m^grav delta(1+delta)=0",
            "cumulative_PS": "erfc[nu (delta_c/delta_c0)/(sqrt(2) D/D0)]/erfc[nu/sqrt(2)]",
        },
        "control_delta_c": publication_float(control_barrier),
        "rows": rows,
        "verification_bounds": {
            "DOP853_Radau_difference": "<5e-9",
            "published_8_decimal_row_difference": "<6e-8",
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_guard": (
            "Large rare-tail ratios are accompanied by 13--94 percent shifts in the declared "
            "equality coordinate. No row closes equality, transfer/recombination, JWST selection "
            "and Solar-System gates in one physical action/state."
        ),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        "non-frozen runtime diagnostics: "
        f"max_growth_solver_difference={max_growth_solver_difference:.17g}; "
        f"max_expected_rounding_difference={max_expected_rounding_difference:.17g}"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
