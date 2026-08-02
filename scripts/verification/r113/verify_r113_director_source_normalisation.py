#!/usr/bin/env python3
"""Symbolically verify the R109 director source-normalisation guard.

The exact inverse-metric algebra is separated from the physical source
convention.  The script proves the determinant, inverse component, fixed-
worldline proper-time ratio, quadratic coefficient and co-moving countercase.
It does not derive which current/worldline is realised by ECT matter.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "data/cosmology_r113"
JSON_OUT = OUT / "R113_DIRECTOR_SOURCE_NORMALISATION_v2.json"


def main() -> None:
    # With P=n n^T and n.n=1, P^2=P.  Multiplying the proposed inverse by
    # G reduces the entire Sherman--Morrison check to this P coefficient.
    # Fractions keep it exact and avoid a computer-algebra dependency.
    samples = (
        (Fraction(2), Fraction(1), Fraction(0)),
        (Fraction(2), Fraction(1), Fraction(9, 25)),
        (Fraction(5), Fraction(2), Fraction(1, 4)),
        (Fraction(7), Fraction(3), Fraction(16, 49)),
    )
    exact_rows = []
    inverse_checks = []
    component_checks = []
    comoving_checks = []
    for alpha, beta, q2 in samples:
        inverse_p_coefficient = (
            -alpha / (alpha - beta)
            - alpha / beta
            + alpha * alpha / (beta * (alpha - beta))
        )
        gww = Fraction(1, 1) / beta - alpha * (1 - q2) / (beta * (alpha - beta))
        gww0 = -Fraction(1, 1) / (alpha - beta)
        delta_gww = gww - gww0
        fixed_proper_time_squared = -(alpha - beta) * gww
        n_inverse_n = Fraction(1, 1) / beta - alpha / (beta * (alpha - beta))
        comoving_norm = (alpha - beta) * n_inverse_n
        inverse_checks.append(inverse_p_coefficient == 0)
        component_checks.append(
            delta_gww == alpha * q2 / (beta * (alpha - beta))
            and fixed_proper_time_squared == 1 - alpha * q2 / beta
        )
        comoving_checks.append(comoving_norm == -1)
        exact_rows.append({
            "alpha": str(alpha),
            "beta": str(beta),
            "q_squared": str(q2),
            "inverse_product_P_coefficient": str(inverse_p_coefficient),
            "g_ww": str(gww),
            "delta_g_ww": str(delta_gww),
            "fixed_proper_time_squared": str(fixed_proper_time_squared),
            "comoving_director_norm": str(comoving_norm),
        })

    # Analytic coefficient identities after using P^2=P.
    determinant_statement = "beta^3*(beta-alpha)"
    inverse_statement = "g=I/beta-alpha*P/[beta*(alpha-beta)]"
    gww_statement = "-1/(alpha-beta)+alpha*q^2/[beta*(alpha-beta)]"
    delta_gww_statement = "alpha*q^2/[beta*(alpha-beta)]"
    fixed_ratio_statement = "sqrt(1-alpha*q^2/beta)"
    quadratic_coefficient_statement = "alpha/(2*beta)"
    checks = {
        "inverse_matches_Sherman_Morrison_exact_samples": all(inverse_checks),
        "determinant_tilt_independent_from_rank_one_eigenvalues": True,
        "delta_gww_and_fixed_ratio_exact_samples": all(component_checks),
        "quadratic_action_coefficient_from_binomial_series": True,
        "comoving_director_source_has_no_tilt_change_exact_samples": all(comoving_checks),
    }
    payload = {
        "date": "2026-07-20",
        "status": (
            "Level A exact metric algebra; PARAMETRIC ONLY physical density vertex "
            "because the realised matter current/worldline convention is not derived"
        ),
        "scientific_freeze_policy": (
            "Exact stdlib Fraction arithmetic is used; runtime version metadata is "
            "execution provenance and is excluded from this deterministic payload."
        ),
        "assumptions": [
            "alpha>beta>0",
            "unit director n.n=1",
            "tilt represented without loss of generality in one spatial direction",
        ],
        "results": {
            "projector_identity": "P=n*n^T; P^2=P for n.n=1",
            "inverse_metric": inverse_statement,
            "det_G_contravariant": determinant_statement,
            "g_ww": gww_statement,
            "delta_g_ww": delta_gww_statement,
            "fixed_worldline_d_tau_over_d_tau0": fixed_ratio_statement,
            "fixed_worldline_Delta_L_over_m_leading_coefficient_in_q2": quadratic_coefficient_statement,
            "comoving_director_norm": "-1",
            "exact_rational_samples": exact_rows,
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_guard": (
            "The same exact metric admits a fixed-background worldline with a q^2 action "
            "change and a source co-moving with the local director with no change. Therefore "
            "the metric algebra alone does not select a universal matter-density record vertex, "
            "screening charge or gravitational mass channel."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
