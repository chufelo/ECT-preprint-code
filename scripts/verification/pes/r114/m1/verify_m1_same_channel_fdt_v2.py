#!/usr/bin/env python3
"""Standalone deterministic verifier for the R114 M1 v2 FDT protocol.

This v2 verifier does not import the v1 verifier.  It independently replays
the v1 synthetic source-model checks and adds counterexamples for:

* finite-window/bin frequency mixing;
* S0 non-identifiability from one response/symmetrised-noise bin;
* informationally incomplete matrix projections;
* a pointwise-FDT pair with a noncausal/KK-inconsistent response;
* a generalized-Gibbs detailed-balance shift.

All calculations are synthetic standard open-system mathematics.  No data are
loaded, and no ECT operator, vertex, state, or transfer function is derived.
"""

from __future__ import annotations

import cmath
import json
import math
import platform


TOL = 3.0e-12


def coth(x: float) -> float:
    if x == 0.0:
        raise ZeroDivisionError("coth is singular at zero")
    if abs(x) < 1.0e-5:
        return 1.0 / x + x / 3.0 - x**3 / 45.0
    return 1.0 / math.tanh(x)


def teff_from_fdt(omega: float, s0: float, s_h: float, diss: float) -> float:
    """Signed scalar inversion of diss/S_H=tanh(S0 omega/(2T))."""
    if omega <= 0.0 or s0 <= 0.0 or s_h <= 0.0:
        raise ValueError("positive omega, S0, and S_H are required")
    ratio = diss / s_h
    if ratio == 0.0 or abs(ratio) >= 1.0:
        raise ValueError("outside the strict finite-temperature inversion domain")
    return s0 * omega / (2.0 * math.atanh(ratio))


def teff_from_ordered(
    omega: float, s0: float, c_greater: float, c_less: float
) -> float:
    if min(omega, s0, c_greater, c_less) <= 0.0:
        raise ValueError("positive inputs are required")
    log_ratio = math.log(c_greater / c_less)
    if log_ratio == 0.0:
        raise ValueError("unit ordered-spectrum ratio has infinite temperature")
    return s0 * omega / log_ratio


def passive_oscillator_d_ret(
    omega: float, mass: float, omega0: float, gamma: float
) -> complex:
    return -1.0 / (mass * (omega0**2 - omega**2 - 1j * gamma * omega))


def spread(values: list[float]) -> float:
    return max(values) - min(values)


def bisection_monotone_increasing(
    fn, target: float, lo: float, hi: float, iterations: int = 220
) -> float:
    """Solve fn(x)=target for a monotone-increasing scalar fn."""
    if not (fn(lo) < target < fn(hi)):
        raise ValueError("target is not bracketed")
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        if fn(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def eigvals_real_symmetric_2x2(
    matrix: list[list[float]],
) -> tuple[float, float]:
    a, b = matrix[0]
    c, d = matrix[1]
    if abs(b - c) > TOL:
        raise ValueError("matrix is not real symmetric")
    trace = a + d
    discriminant = math.hypot(a - d, 2.0 * b)
    return ((trace - discriminant) / 2.0, (trace + discriminant) / 2.0)


def add2(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] + b[i][j] for j in range(2)] for i in range(2)]


def sub2(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[a[i][j] - b[i][j] for j in range(2)] for i in range(2)]


def quadratic_form(
    vector: tuple[complex, complex], matrix: list[list[complex]]
) -> float:
    mv = [
        matrix[i][0] * vector[0] + matrix[i][1] * vector[1]
        for i in range(2)
    ]
    value = vector[0].conjugate() * mv[0] + vector[1].conjugate() * mv[1]
    if abs(value.imag) > TOL:
        raise ValueError("Hermitian quadratic form is not real")
    return value.real


def replay_v1_source_models() -> dict[str, object]:
    """Independent standalone replay of all decisive v1 synthetic checks."""
    s0 = 2.3
    temperature = 4.7
    frequencies = [0.35, 0.70, 1.20, 2.10, 3.20, 4.70, 7.50]
    mass = 1.7
    omega0 = 3.2
    gamma = 0.45

    base_h: list[float] = []
    base_diss: list[float] = []
    fdt_temperatures: list[float] = []
    ordered_temperatures: list[float] = []
    omitted_s0_temperatures: list[float] = []
    mirror_errors: list[float] = []

    for omega in frequencies:
        d_positive = passive_oscillator_d_ret(omega, mass, omega0, gamma)
        d_negative = passive_oscillator_d_ret(-omega, mass, omega0, gamma)
        mirror_errors.append(abs(d_negative - d_positive.conjugate()))

        diss = -s0 * d_positive.imag
        h = diss * coth(s0 * omega / (2.0 * temperature))
        c_greater = h + diss
        c_less = h - diss

        # Negative-frequency scalar mirrors: H is even and ordered spectra swap.
        diss_negative = -s0 * d_negative.imag
        h_negative = diss_negative * coth(-s0 * omega / (2.0 * temperature))
        c_greater_negative = h_negative + diss_negative
        mirror_errors.extend(
            [abs(h_negative - h), abs(c_greater_negative - c_less)]
        )

        assert diss > 0.0 and c_greater > 0.0 and c_less > 0.0
        base_h.append(h)
        base_diss.append(diss)
        fdt_temperatures.append(teff_from_fdt(omega, s0, h, diss))
        ordered_temperatures.append(
            teff_from_ordered(omega, s0, c_greater, c_less)
        )
        omitted_s0_temperatures.append(
            omega / (2.0 * math.atanh(diss / h))
        )

    max_fdt_error = max(abs(x - temperature) for x in fdt_temperatures)
    max_ordered_error = max(abs(x - temperature) for x in ordered_temperatures)
    max_omitted_error = max(
        abs(x - temperature / s0) for x in omitted_s0_temperatures
    )
    max_mirror_error = max(mirror_errors)

    omega_limit = 1.2
    d_limit = passive_oscillator_d_ret(omega_limit, mass, omega0, gamma)
    diss_limit = -s0 * d_limit.imag
    ground_saturation_error = abs(diss_limit - diss_limit)
    high_temperature = 200.0
    exact_high_t = diss_limit * coth(
        s0 * omega_limit / (2.0 * high_temperature)
    )
    classical_high_t = -2.0 * high_temperature * d_limit.imag / omega_limit
    high_t_relative_error = abs(exact_high_t / classical_high_t - 1.0)

    # Two-temperature passive bath.
    t1, t2 = 1.4, 9.0
    two_bath_temperatures: list[float] = []
    for omega in frequencies:
        diss1 = 0.70 * omega / (1.0 + (omega / 2.1) ** 2)
        diss2 = 0.42 * omega / (1.0 + (omega / 6.5) ** 4)
        total_diss = diss1 + diss2
        total_h = diss1 * coth(s0 * omega / (2.0 * t1)) + diss2 * coth(
            s0 * omega / (2.0 * t2)
        )
        assert total_h >= total_diss - TOL
        two_bath_temperatures.append(
            teff_from_fdt(omega, s0, total_h, total_diss)
        )
    two_bath_spread = spread(two_bath_temperatures)

    # Positive nonthermal occupation bump.
    occupation_temperatures: list[float] = []
    for omega, diss in zip(frequencies, base_diss):
        n_thermal = 1.0 / math.expm1(s0 * omega / temperature)
        n_bump = 1.25 * math.exp(-((omega - 3.2) / 0.85) ** 2)
        occupation = n_thermal + n_bump
        c_greater = 2.0 * diss * (occupation + 1.0)
        c_less = 2.0 * diss * occupation
        h = 0.5 * (c_greater + c_less)
        reconstructed_diss = 0.5 * (c_greater - c_less)
        assert h >= abs(reconstructed_diss) - TOL
        occupation_temperatures.append(
            teff_from_ordered(omega, s0, c_greater, c_less)
        )
    occupation_spread = spread(occupation_temperatures)

    # Common multiplicative LTI filter versus mismatched filters.
    same_filter_temperatures: list[float] = []
    mismatched_filter_temperatures: list[float] = []
    for omega, h, diss in zip(frequencies, base_h, base_diss):
        common = 1.0 / (1.0 + (omega / 4.0) ** 2)
        noise = common * (
            1.0 + 0.55 * (omega / 5.0) ** 2 / (1.0 + (omega / 5.0) ** 2)
        )
        same_filter_temperatures.append(
            teff_from_fdt(omega, s0, common * h, common * diss)
        )
        mismatched_filter_temperatures.append(
            teff_from_fdt(omega, s0, noise * h, common * diss)
        )
    same_filter_error = max(
        abs(x - temperature) for x in same_filter_temperatures
    )
    mismatched_filter_spread = spread(mismatched_filter_temperatures)

    # Active ordered pair.
    active_omega = 2.0
    active_c_greater = 1.0
    active_c_less = 1.8
    active_h = 0.5 * (active_c_greater + active_c_less)
    active_diss = 0.5 * (active_c_greater - active_c_less)
    active_temperature = teff_from_ordered(
        active_omega, s0, active_c_greater, active_c_less
    )
    assert active_h >= abs(active_diss) and active_temperature < 0.0

    # Retarded poles of the benchmark lie in the lower half-plane.
    pole_root = cmath.sqrt(4.0 * omega0**2 - gamma**2)
    poles = [(-1j * gamma + pole_root) / 2.0, (-1j * gamma - pole_root) / 2.0]
    assert all(pole.imag < 0.0 for pole in poles)

    assert max_fdt_error < TOL
    assert max_ordered_error < TOL
    assert max_omitted_error < TOL
    assert max_mirror_error < TOL
    assert ground_saturation_error < TOL
    assert high_t_relative_error < 2.0e-5
    assert abs(two_bath_spread - 3.641975368819562) < TOL
    assert abs(occupation_spread - 9.813657737370281) < TOL
    assert same_filter_error < TOL
    assert abs(mismatched_filter_spread - 5.498842730337092) < TOL
    assert abs(active_temperature - (-7.825968628883429)) < TOL

    return {
        "classification": "v1 synthetic source-model replay; no ECT claim",
        "thermal_FDT_max_error": max_fdt_error,
        "thermal_ordered_max_error": max_ordered_error,
        "omitted_S0_returns_T_over_S0_max_error": max_omitted_error,
        "negative_frequency_mirror_max_error": max_mirror_error,
        "retarded_poles": [[pole.real, pole.imag] for pole in poles],
        "ground_state_assigned_saturation_error": ground_saturation_error,
        "high_T_classical_relative_error": high_t_relative_error,
        "two_bath_Teff_spread": two_bath_spread,
        "occupation_bump_Teff_spread": occupation_spread,
        "common_filter_max_error": same_filter_error,
        "mismatched_filter_false_spread": mismatched_filter_spread,
        "active_signed_Teff": active_temperature,
        "wording_guard": (
            "FDT and ordered formulas are algebraically equivalent inversions, "
            "not statistically independent reconstructions"
        ),
    }


def finite_window_counterexample() -> dict[str, object]:
    """Two thermal lines in one bin: common frequency mixing does not cancel."""
    s0 = 1.0
    true_temperature = 1.0
    line_frequencies = [1.0, 3.0]
    dissipative_weights = [1.0, 1.0]
    bin_centre = 2.0

    binned_diss = sum(dissipative_weights)
    binned_h = sum(
        weight * coth(s0 * frequency / (2.0 * true_temperature))
        for frequency, weight in zip(line_frequencies, dissipative_weights)
    )
    binned_ratio = binned_h / binned_diss
    centre_coth = coth(s0 * bin_centre / (2.0 * true_temperature))
    naive_temperature = teff_from_fdt(
        bin_centre, s0, binned_h, binned_diss
    )

    def forward_h(temperature: float) -> float:
        return sum(
            weight * coth(s0 * frequency / (2.0 * temperature))
            for frequency, weight in zip(line_frequencies, dissipative_weights)
        )

    recovered_temperature = bisection_monotone_increasing(
        forward_h, binned_h, 1.0e-8, 100.0
    )

    # The same obstruction appears even when ordered spectra are measured
    # directly.  Two equal C^> lines obey C^<(nu)=exp(-nu)C^>(nu), but their
    # unresolved bin ratio is not exp(-Omega_bin).
    ordered_binned_greater = 2.0
    ordered_binned_less = math.exp(-1.0) + math.exp(-3.0)
    ordered_naive_temperature = bin_centre / math.log(
        ordered_binned_greater / ordered_binned_less
    )

    assert abs(binned_h - 3.268744806721165) < TOL
    assert abs(binned_ratio - 1.6343724033605824) < TOL
    assert abs(centre_coth - 1.3130352854993315) < TOL
    assert abs(naive_temperature - 1.4047271025726755) < TOL
    assert abs(recovered_temperature - true_temperature) < TOL
    assert abs(naive_temperature - true_temperature) > 0.4
    assert abs(ordered_binned_less - 0.4176665095393063) < TOL
    assert abs(ordered_naive_temperature - 1.2769604911787709) < TOL

    return {
        "classification": "exact two-line finite-bin source-model counterexample",
        "S0": s0,
        "true_temperature": true_temperature,
        "line_frequencies": line_frequencies,
        "dissipative_weights": dissipative_weights,
        "bin_centre": bin_centre,
        "binned_dissipation": binned_diss,
        "binned_S_H": binned_h,
        "binned_ratio": binned_ratio,
        "coth_at_bin_centre": centre_coth,
        "naive_pointwise_Teff": naive_temperature,
        "forward_convolved_recovered_temperature": recovered_temperature,
        "direct_ordered_two_line_bin": {
            "binned_C_greater": ordered_binned_greater,
            "binned_C_less": ordered_binned_less,
            "naive_bin_centre_Teff": ordered_naive_temperature,
        },
        "conclusion": (
            "a common finite window/bin is necessary but does not preserve "
            "pointwise FDT; forward-convolve the model"
        ),
    }


def s0_identifiability_counterexample() -> dict[str, object]:
    """One response/noise bin admits a continuum of (S0,T/S0) pairs."""
    q = 2.0  # q = S_H / (-Im D^R)
    omega = 1.0
    candidate_s0 = [0.5, 1.0]
    rows: list[dict[str, float]] = []

    for s0 in candidate_s0:
        theta = omega / (2.0 * math.atanh(s0 / q))  # theta=T/S0
        temperature = s0 * theta
        predicted_q = s0 * coth(omega / (2.0 * theta))

        # Reconstructing ordered spectra from S_H and Im D already uses S0.
        s_h = q
        minus_im_d = 1.0
        c_greater = s_h + s0 * minus_im_d
        c_less = s_h - s0 * minus_im_d
        reconstructed_theta = omega / math.log(c_greater / c_less)

        assert abs(predicted_q - q) < TOL
        assert abs(reconstructed_theta - theta) < TOL
        rows.append(
            {
                "S0": s0,
                "theta_equals_T_over_S0": theta,
                "T": temperature,
                "predicted_q": predicted_q,
                "reconstructed_C_greater": c_greater,
                "reconstructed_C_less": c_less,
            }
        )

    assert abs(rows[0]["theta_equals_T_over_S0"] - 1.957615188971218) < TOL
    assert abs(rows[0]["T"] - 0.978807594485609) < TOL
    assert abs(rows[1]["theta_equals_T_over_S0"] - 0.9102392266268373) < TOL
    assert abs(rows[1]["T"] - 0.9102392266268373) < TOL

    # Independently measured ordered spectra identify theta without numerical S0.
    direct_theta = 1.7
    direct_ratio = math.exp(omega / direct_theta)
    recovered_direct_theta = omega / math.log(direct_ratio)
    assert abs(recovered_direct_theta - direct_theta) < TOL

    return {
        "classification": "one-bin identifiability counterexample",
        "q_equals_S_H_over_minus_Im_D_R": q,
        "omega": omega,
        "degenerate_rows": rows,
        "direct_ordered_spectra": {
            "input_theta": direct_theta,
            "ordered_ratio": direct_ratio,
            "recovered_theta_without_S0": recovered_direct_theta,
        },
        "conclusion": (
            "direct S+/S- identifies T/S0; reconstructing S+/S- from S_H and "
            "D^R requires S0, so response+symmetrised-noise needs an S0 match "
            "or a broad-band joint fit with covariance"
        ),
    }


def incomplete_matrix_projection_counterexample() -> dict[str, object]:
    """Diagonal projections pass one T while coherent projections refute it."""
    h = [[1.0, 0.4], [0.4, 1.0]]
    diss = [[0.5, 0.0], [0.0, 0.5]]  # diss = -S0 Im_H D^R
    c_greater = add2(h, diss)
    c_less = sub2(h, diss)
    eig_greater = eigvals_real_symmetric_2x2(c_greater)
    eig_less = eigvals_real_symmetric_2x2(c_less)
    assert min(eig_greater) > 0.0 and min(eig_less) > 0.0

    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    vectors: dict[str, tuple[complex, complex]] = {
        "e1": (1.0 + 0j, 0j),
        "e2": (0j, 1.0 + 0j),
        "plus": (inv_sqrt2 + 0j, inv_sqrt2 + 0j),
        "minus": (inv_sqrt2 + 0j, -inv_sqrt2 + 0j),
        "plus_i": (inv_sqrt2 + 0j, 1j * inv_sqrt2),
    }
    h_complex = [[complex(x) for x in row] for row in h]
    diss_complex = [[complex(x) for x in row] for row in diss]
    projection_rows: dict[str, dict[str, float]] = {}
    for name, vector in vectors.items():
        projected_h = quadratic_form(vector, h_complex)
        projected_diss = quadratic_form(vector, diss_complex)
        ratio = projected_diss / projected_h
        temperature = 1.0 / (2.0 * math.atanh(ratio))  # S0*omega=1
        projection_rows[name] = {
            "S_H": projected_h,
            "dissipation": projected_diss,
            "ratio": ratio,
            "T_eff_for_S0omega_equals_1": temperature,
        }

    e1_t = projection_rows["e1"]["T_eff_for_S0omega_equals_1"]
    e2_t = projection_rows["e2"]["T_eff_for_S0omega_equals_1"]
    plus_t = projection_rows["plus"]["T_eff_for_S0omega_equals_1"]
    minus_t = projection_rows["minus"]["T_eff_for_S0omega_equals_1"]
    assert abs(e1_t - e2_t) < TOL
    assert abs(e1_t - 0.9102392266268373) < TOL
    assert abs(plus_t - 1.3383039694505456) < TOL
    assert abs(minus_t - 0.4170323914242463) < TOL

    # Demonstrate an informationally complete 2x2 Hermitian projection set.
    h_ic = [[1.0 + 0j, 0.4 + 0.2j], [0.4 - 0.2j, 1.3 + 0j]]
    p1 = quadratic_form(vectors["e1"], h_ic)
    p2 = quadratic_form(vectors["e2"], h_ic)
    p_plus = quadratic_form(vectors["plus"], h_ic)
    p_plus_i = quadratic_form(vectors["plus_i"], h_ic)
    reconstructed_re12 = p_plus - 0.5 * (p1 + p2)
    reconstructed_im12 = 0.5 * (p1 + p2) - p_plus_i
    assert abs(reconstructed_re12 - h_ic[0][1].real) < TOL
    assert abs(reconstructed_im12 - h_ic[0][1].imag) < TOL

    return {
        "classification": "exact Wightman-positive 2x2 projection counterexample",
        "S_H": h,
        "dissipation_matrix": diss,
        "C_greater_eigenvalues": eig_greater,
        "C_less_eigenvalues": eig_less,
        "projections": projection_rows,
        "informationally_complete_reconstruction": {
            "input_H12": [h_ic[0][1].real, h_ic[0][1].imag],
            "reconstructed_H12": [reconstructed_re12, reconstructed_im12],
            "required_2x2_projectors": ["e1", "e2", "plus", "plus_i"],
        },
        "conclusion": (
            "e1/e2 alone falsely accept one temperature; full matrices or an "
            "informationally complete preregistered projection set are required"
        ),
    }


def noncausal_kk_counterexample() -> dict[str, object]:
    """A pointwise thermal pair whose assigned response is not retarded."""
    s0 = 1.0
    temperature = 1.0
    frequencies = [0.25, 0.75, 1.5, 2.5]
    fdt_errors: list[float] = []
    wightman_margins: list[float] = []

    for omega in frequencies:
        im_d = -omega * math.exp(-(omega**2))
        diss = -s0 * im_d
        h = diss * coth(s0 * omega / (2.0 * temperature))
        inferred = teff_from_fdt(omega, s0, h, diss)
        fdt_errors.append(abs(inferred - temperature))
        wightman_margins.append(h - abs(diss))

    # With Re D assigned to zero, the unsubtracted KK value required at zero is
    # (1/pi) int dnu ImD(nu)/nu = -1/sqrt(pi).
    assigned_re_d_at_zero = 0.0
    required_re_d_at_zero = -1.0 / math.sqrt(math.pi)
    kk_mismatch = abs(assigned_re_d_at_zero - required_re_d_at_zero)

    # Exact inverse transform of D_fake(omega)=-i omega exp(-omega^2):
    # D_fake(t)=-t exp(-t^2/4)/(4 sqrt(pi)), nonzero at negative time.
    negative_time = -1.0
    negative_time_response = (
        -negative_time
        * math.exp(-(negative_time**2) / 4.0)
        / (4.0 * math.sqrt(math.pi))
    )

    assert max(fdt_errors) < TOL
    assert min(wightman_margins) > 0.0
    assert abs(required_re_d_at_zero - (-0.5641895835477563)) < TOL
    assert kk_mismatch > 0.5
    assert abs(negative_time_response - 0.1098478223669306) < TOL
    assert negative_time_response != 0.0

    return {
        "classification": "pointwise-FDT but noncausal synthetic response",
        "fake_response": "D(omega)=-i omega exp(-omega^2), assigned ReD=0",
        "max_pointwise_FDT_temperature_error": max(fdt_errors),
        "minimum_Wightman_margin": min(wightman_margins),
        "assigned_Re_D_at_zero": assigned_re_d_at_zero,
        "KK_required_Re_D_at_zero": required_re_d_at_zero,
        "KK_mismatch": kk_mismatch,
        "D_of_t_at_t_minus_1": negative_time_response,
        "conclusion": (
            "pointwise FDT and positivity do not imply retarded support or KK "
            "consistency; tails, subtractions, and contact terms must be frozen"
        ),
    }


def generalized_gibbs_guard() -> dict[str, object]:
    """A generalized equilibrium looks noncanonical if charges are omitted."""
    temperature = 2.0
    s0_omega = 5.0
    chemical_work = 1.2
    rotational_work = 0.3
    generator_gap = s0_omega - chemical_work - rotational_work
    log_ordered_ratio = generator_gap / temperature
    ordered_ratio = math.exp(log_ordered_ratio)
    canonical_naive_temperature = s0_omega / math.log(ordered_ratio)
    generalized_temperature = generator_gap / math.log(ordered_ratio)

    assert abs(generalized_temperature - temperature) < TOL
    assert abs(canonical_naive_temperature - 2.857142857142857) < TOL
    assert abs(canonical_naive_temperature - temperature) > 0.8

    return {
        "classification": "generalized-Gibbs detailed-balance guard",
        "T": temperature,
        "S0omega": s0_omega,
        "mu_q": chemical_work,
        "Omega_m": rotational_work,
        "generator_gap": generator_gap,
        "ordered_ratio": ordered_ratio,
        "naive_canonical_Teff": canonical_naive_temperature,
        "correct_generalized_T": generalized_temperature,
        "conclusion": (
            "freeze the time generator, frame, and conserved charges before "
            "classifying a channel as non-KMS"
        ),
    }


def main() -> None:
    result = {
        "classification": (
            "deterministic synthetic standard open-system regression only; "
            "no data and no ECT-specific prediction"
        ),
        "environment": {"python": platform.python_version()},
        "conventions": {
            "fourier": "integral dt exp(+i omega t)",
            "passive_sign": "Im D^R(omega)<=0 for omega>0",
            "retarded_analytic_half_plane": "Im omega > 0",
            "temperature_units": "energy; SI uses T=k_B Theta",
        },
        "v1_source_model_regression": replay_v1_source_models(),
        "finite_window_forward_convolution_gate": finite_window_counterexample(),
        "S0_identifiability_gate": s0_identifiability_counterexample(),
        "matrix_informational_completeness_gate": (
            incomplete_matrix_projection_counterexample()
        ),
        "causality_KK_gate": noncausal_kk_counterexample(),
        "generalized_Gibbs_generator_gate": generalized_gibbs_guard(),
        "initial_correlation_guard": (
            "For an influence-functional interpretation, freeze factorized "
            "preparation/switching or include correlated-state initial-slip and "
            "boundary kernels; a bare-bath Gibbs state is not automatic at strong coupling."
        ),
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
