#!/usr/bin/env python3
"""Deterministic checks for R114 M5 bridge-invariant audit.

This is a synthetic/algebraic verification only.  It does not fit SPARC data,
derive an ECT gravity vertex, or identify a physical retarded kernel.
"""

from __future__ import annotations

import json
import math
import platform


TOL = 5.0e-14


def mu0(s: float) -> float:
    if s < 0.0:
        raise ValueError("mu0 requires s >= 0")
    return math.sqrt(s / (1.0 + s))


def f_rational(x: float) -> float:
    return x * x / (1.0 + 2.0 * x)


def b_rational(x: float) -> float:
    return 1.0 / (1.0 + 2.0 * x)


def b_alternative(x: float, alpha: float = 3.0) -> float:
    """Positive bridge with the same B(0), B'(0), but different shape."""
    return 1.0 / (1.0 + 2.0 * x + alpha * x * x)


def df_rational_dy(x: float) -> float:
    """d f(Y)/dY for Y=x^2 and f=Y/(1+2 sqrt(Y))."""
    return (1.0 + x) / (1.0 + 2.0 * x) ** 2


def bridge_j(b0: float, b1: float) -> float:
    if b0 <= 0.0:
        raise ValueError("B(0) must be positive")
    return b1 / (b0 ** 1.5)


def main() -> None:
    grid = [10.0 ** (-4.0 + 5.0 * i / 200.0) for i in range(201)]

    response_identity_error = max(
        abs(mu0(f_rational(x)) - x / (1.0 + x)) for x in grid
    )
    action_formula_error = max(
        abs(
            mu0(f_rational(x)) * df_rational_dy(x)
            - x / (1.0 + 2.0 * x) ** 2
        )
        for x in grid
    )
    action_vs_simple_at_x_01 = abs(
        mu0(f_rational(0.1)) * df_rational_dy(0.1) - 0.1 / 1.1
    )

    # Horizontal acceleration-scale covariance B_c(x)=c^2 B_1(c x).
    base_b0 = 1.0
    base_b1 = -2.0
    c_scale = 4.0
    scaled_b0 = c_scale**2 * base_b0
    scaled_b1 = c_scale**3 * base_b1
    j_base = bridge_j(base_b0, base_b1)
    j_scaled = bridge_j(scaled_b0, scaled_b1)

    # Independent vertical/internal-coordinate normalization is not a symmetry.
    lambda_internal = 4.0
    j_internal_rescaled = bridge_j(
        lambda_internal * base_b0, lambda_internal * base_b1
    )

    # Live action-pullback series: mu0(f) f_Y = B0^(3/2) x
    # + 2 sqrt(B0) B1 x^2 + O(x^3).  Match x-x^2+...
    action_b0 = 1.0
    action_b1 = -0.5
    action_leading = action_b0**1.5
    action_quadratic = 2.0 * math.sqrt(action_b0) * action_b1
    j_action_simple = bridge_j(action_b0, action_b1)

    # Same linear static susceptibility, arbitrary nonlinear curvature.
    kappa = 2.0
    lambdas = [0.0, 1.0, 3.0]
    linear_susceptibilities = [1.0 / kappa for _ in lambdas]
    normalized_curvatures = [-2.0 * lam / kappa for lam in lambdas]

    # Same local J=-2, different positive global bridge shapes.
    x_probe = 0.5
    nonunique_shape_gap = abs(b_rational(x_probe) - b_alternative(x_probe))

    assert response_identity_error < TOL
    assert action_formula_error < TOL
    assert action_vs_simple_at_x_01 > 1.0e-3
    assert abs(j_base + 2.0) < TOL
    assert abs(j_scaled - j_base) < TOL
    assert abs(j_internal_rescaled + 1.0) < TOL
    assert abs(action_leading - 1.0) < TOL
    assert abs(action_quadratic + 1.0) < TOL
    assert abs(j_action_simple + 0.5) < TOL
    assert len(set(linear_susceptibilities)) == 1
    assert len(set(normalized_curvatures)) == len(lambdas)
    assert nonunique_shape_gap > 0.1

    result = {
        "classification": "synthetic algebraic verification only",
        "python": platform.python_version(),
        "response_coordinate_bridge": {
            "max_identity_error": response_identity_error,
            "J": j_base,
        },
        "live_action_pullback_of_same_rational_f": {
            "max_closed_formula_error": action_formula_error,
            "absolute_mismatch_from_simple_mu_at_x_0p1": action_vs_simple_at_x_01,
            "actual_mu": "x/(1+2x)^2",
        },
        "horizontal_scale_test": {
            "c": c_scale,
            "J_base": j_base,
            "J_scaled": j_scaled,
        },
        "internal_coordinate_counterexample": {
            "lambda": lambda_internal,
            "J_after_rescaling": j_internal_rescaled,
        },
        "action_consistent_simple_mu_local_series": {
            "B0": action_b0,
            "B1": action_b1,
            "J": j_action_simple,
            "mu_x_coefficient": action_leading,
            "mu_x2_coefficient": action_quadratic,
        },
        "nonuniqueness": {
            "x_probe": x_probe,
            "shape_gap_with_same_B0_B1": nonunique_shape_gap,
        },
        "same_DR_different_nonlinearity": {
            "kappa": kappa,
            "lambdas": lambdas,
            "DR_static": linear_susceptibilities,
            "normalized_curvatures": normalized_curvatures,
        },
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
