#!/usr/bin/env python3
"""Deterministic checks for the corrected R114 M6 spectral LMIs.

The script verifies matrix algebra and a conditional power-counting gate.  It
does not establish a CP reduced map or derive an ECT gravitational channel.
"""

from __future__ import annotations

import json
import math
import platform


TOL = 5.0e-14


def add(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(2)] for i in range(2)]


def sub(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(2)] for i in range(2)]


def scale(c: float, a: list[list[float]]) -> list[list[float]]:
    return [[c * a[i][j] for j in range(2)] for i in range(2)]


def eigvals_symmetric_2x2(a: list[list[float]]) -> tuple[float, float]:
    if abs(a[0][1] - a[1][0]) > TOL:
        raise ValueError("matrix is not symmetric")
    trace = a[0][0] + a[1][1]
    disc = math.hypot(a[0][0] - a[1][1], 2.0 * a[0][1])
    return ((trace - disc) / 2.0, (trace + disc) / 2.0)


def main() -> None:
    # Two positive ordered spectra C^> and C^<.
    c_greater = [[1.0, 0.0], [0.0, 0.0]]
    c_less = [[0.5, 0.5], [0.5, 0.5]]
    s_h = scale(0.5, add(c_greater, c_less))
    s0_a = scale(0.5, sub(c_greater, c_less))

    lmi_plus = add(s_h, s0_a)
    lmi_minus = sub(s_h, s0_a)
    eig_c_greater = eigvals_symmetric_2x2(c_greater)
    eig_c_less = eigvals_symmetric_2x2(c_less)
    eig_lmi_plus = eigvals_symmetric_2x2(lmi_plus)
    eig_lmi_minus = eigvals_symmetric_2x2(lmi_minus)

    # Here (S0 A)^2 = I/8 exactly, hence |S0 A|=I/(2 sqrt(2)).
    abs_a_scale = 1.0 / (2.0 * math.sqrt(2.0))
    abs_s0_a = [[abs_a_scale, 0.0], [0.0, abs_a_scale]]
    matrix_absolute_difference = sub(s_h, abs_s0_a)
    eig_matrix_absolute_difference = eigvals_symmetric_2x2(
        matrix_absolute_difference
    )
    exact_negative_eigenvalue = (1.0 - math.sqrt(2.0)) / 2.0

    # Scalar Wightman decomposition: S=(C>+C<)/2, S0 A=(C>-C<)/2.
    scalar_c_greater = 3.0
    scalar_c_less = 1.0
    scalar_s_h = 0.5 * (scalar_c_greater + scalar_c_less)
    scalar_s0_a = 0.5 * (scalar_c_greater - scalar_c_less)
    scalar_margin = scalar_s_h - abs(scalar_s0_a)

    # Positive-frequency ground-state example: one ordered spectrum vanishes.
    ground_c_greater = 2.0
    ground_c_less = 0.0
    ground_s_h = 0.5 * (ground_c_greater + ground_c_less)
    ground_s0_a = 0.5 * (ground_c_greater - ground_c_less)
    ground_saturation_error = abs(ground_s_h - abs(ground_s0_a))

    # Conditional same-channel IR power-law gate in ledger units S0=1.
    omega = 1.0e-3
    filtered_noise_omega9 = omega**9
    unfiltered_dissipation_omega3 = omega**3
    mismatched_filter_margin = filtered_noise_omega9 - unfiltered_dissipation_omega3
    same_filter_dissipation_omega9 = omega**9
    same_filter_margin = filtered_noise_omega9 - same_filter_dissipation_omega9

    assert min(eig_c_greater) >= -TOL
    assert min(eig_c_less) >= -TOL
    assert min(eig_lmi_plus) >= -TOL
    assert min(eig_lmi_minus) >= -TOL
    assert eig_matrix_absolute_difference[0] < -0.2
    assert abs(
        eig_matrix_absolute_difference[0] - exact_negative_eigenvalue
    ) < TOL
    assert scalar_margin > 0.0
    assert ground_saturation_error < TOL
    assert mismatched_filter_margin < 0.0
    assert abs(same_filter_margin) < TOL

    result = {
        "classification": "synthetic spectral-matrix algebra only",
        "python": platform.python_version(),
        "correct_pair_of_LMIs": {
            "eigenvalues_C_greater": eig_c_greater,
            "eigenvalues_C_less": eig_c_less,
            "eigenvalues_S_plus_S0A": eig_lmi_plus,
            "eigenvalues_S_minus_S0A": eig_lmi_minus,
        },
        "matrix_absolute_counterexample": {
            "eigenvalues_S_minus_abs_S0A": eig_matrix_absolute_difference,
            "exact_negative_eigenvalue": exact_negative_eigenvalue,
            "conclusion": "pair LMIs do not imply S >= |A| for noncommuting matrices",
        },
        "scalar_projection": {
            "S_H": scalar_s_h,
            "abs_S0A": abs(scalar_s0_a),
            "margin": scalar_margin,
        },
        "ground_state_positive_frequency": {
            "S_H": ground_s_h,
            "abs_S0A": abs(ground_s0_a),
            "saturation_error": ground_saturation_error,
        },
        "conditional_power_law_gate_S0_equals_1": {
            "omega": omega,
            "filtered_noise_omega9": filtered_noise_omega9,
            "unfiltered_dissipation_omega3": unfiltered_dissipation_omega3,
            "mismatched_filter_margin": mismatched_filter_margin,
            "same_filter_dissipation_omega9": same_filter_dissipation_omega9,
            "same_filter_margin": same_filter_margin,
            "guard": "response and noise must use the same operator and filter",
        },
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
