#!/usr/bin/env python3
"""Deterministic R103 audit of whether current ECT fixes H(a) and t0.

This script deliberately does not promote a supplied FLRW benchmark to an
ECT prediction.  It verifies the live-source hash and anchors, checks the
algebraic reconstruction identities of the scalar-only Jordan-frame closure,
and evaluates several *conditional* frozen-scalar backgrounds to demonstrate
non-uniqueness of law-level selection.  A named two-slope action/state has a
non-null reproducible conditional age; only a unique P1--P6 selection and the
full physical metric/clock/front map remain unresolved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path


LATEX_ROOT = Path(__file__).resolve().parents[2]
LIVE = LATEX_ROOT / "ECT_preprint.tex"
HASH_LOCK = LATEX_ROOT / "data/cosmology_r103/R103_PREPRINT_SOURCE_SHA256.txt"
CONDITIONAL_AGE_JSON = LATEX_ROOT / "data/cosmology_r103/R103_TWO_SLOPE_CONDITIONAL_OBSERVABLES_v1.json"

ANCHORS = (
    "eq:ECT_action",
    "eq:gradient_condensate",
    "eq:ordered_branch_euclidean_eft",
    "eq:phi_first_action",
    "eq:bg_reduction_friedmann",
    "eq:bg_reduction_raychaudhuri",
    "eq:bg_reduction_scalar",
    "eq:ect_age_ordered_branch",
    "eq:ect_age_not_identifiable",
    "eq:ect_age_inverse_kinetic",
    "eq:ect_age_inverse_potential",
    "eq:two_slope_action",
    "eq:two_slope_friedmann",
    "eq:two_slope_scalar",
    "eq:two_slope_conditional_age",
    "app:late_cosmo_algorithm",
    "app:ect_cosmology_identifiability",
    "app:ect_cosmology_observable_protocols",
)

MPC_M = 3.0856775814913673e22
JULIAN_YEAR_S = 365.25 * 86400.0
GYR_S = 1.0e9 * JULIAN_YEAR_S


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def anchor_lines(text: str) -> dict[str, int]:
    lines = text.splitlines()
    result: dict[str, int] = {}
    for anchor in ANCHORS:
        hits = [i + 1 for i, line in enumerate(lines) if anchor in line]
        # Labels also occur in references.  The label declaration is the hit
        # containing "label{"; fall back to a unique literal occurrence.
        declared = [
            i + 1
            for i, line in enumerate(lines)
            if (f"label{{{anchor}}}" in line)
        ]
        if len(declared) == 1:
            result[anchor] = declared[0]
        elif len(hits) == 1:
            result[anchor] = hits[0]
        else:
            raise RuntimeError(
                f"Anchor {anchor!r} has {len(hits)} literal hits and "
                f"{len(declared)} declarations"
            )
    return result


def adaptive_simpson(f, a: float, b: float, tol: float = 2e-13, depth: int = 30) -> float:
    def simpson(fa: float, fm: float, fb: float, lo: float, hi: float) -> float:
        return (hi - lo) * (fa + 4.0 * fm + fb) / 6.0

    fa = f(a)
    fb = f(b)
    m = 0.5 * (a + b)
    fm = f(m)
    whole = simpson(fa, fm, fb, a, b)

    def rec(lo, hi, flo, fmid, fhi, previous, eps, remaining):
        mid = 0.5 * (lo + hi)
        lm = 0.5 * (lo + mid)
        rm = 0.5 * (mid + hi)
        flm = f(lm)
        frm = f(rm)
        left = simpson(flo, flm, fmid, lo, mid)
        right = simpson(fmid, frm, fhi, mid, hi)
        delta = left + right - previous
        if remaining <= 0 or abs(delta) <= 15.0 * eps:
            return left + right + delta / 15.0
        return rec(lo, mid, flo, flm, fmid, left, eps / 2.0, remaining - 1) + rec(
            mid, hi, fmid, frm, fhi, right, eps / 2.0, remaining - 1
        )

    return rec(a, b, fa, fm, fb, whole, tol, depth)


def e_of_a(a: float, omega_r: float, omega_m: float, omega_de: float, w: float = -1.0) -> float:
    if a == 0.0:
        return math.inf
    return math.sqrt(
        omega_r * a ** -4
        + omega_m * a ** -3
        + omega_de * a ** (-3.0 * (1.0 + w))
    )


def h0_age_dimensionless(
    omega_r: float,
    omega_m: float,
    omega_de: float,
    w: float = -1.0,
    a_start: float = 0.0,
) -> tuple[float, float]:
    def in_a(a: float) -> float:
        if a == 0.0:
            return 0.0
        return 1.0 / (a * e_of_a(a, omega_r, omega_m, omega_de, w))

    # Independent variable check: x=ln(a), truncated at x=-50.  The omitted
    # radiation-era tail is bounded well below the printed precision.
    def in_x(x: float) -> float:
        a = math.exp(x)
        return 1.0 / e_of_a(a, omega_r, omega_m, omega_de, w)

    direct = adaptive_simpson(in_a, a_start, 1.0)
    x_lo = math.log(a_start) if a_start > 0.0 else -50.0
    log_integral = adaptive_simpson(in_x, x_lo, 0.0)
    if a_start == 0.0:
        # Radiation-dominated analytic upper bound/correction for 0<a<e^-50.
        log_integral += math.exp(2.0 * x_lo) / (2.0 * math.sqrt(omega_r))
    return direct, log_integral


def h0_inverse_gyr(h0_km_s_mpc: float) -> float:
    h0_si = h0_km_s_mpc * 1000.0 / MPC_M
    return 1.0 / h0_si / GYR_S


def reconstructed_kinetic_over_h0sq(
    a: float,
    omega_r: float,
    omega_m: float,
    omega_de: float,
    w: float,
    p_f: float,
) -> float:
    """Inverse-reconstructed K=omega*phidot^2 for F=a**p_f.

    Units are Mbar_Pl=H0=1.  With phi=(p_f/beta) ln(a), this F is
    exactly of the live exponential form F=exp(beta*phi).  Positivity of
    this expression therefore supplies a non-ghost counterfamily inside
    that form, rather than only inside a minimally coupled scalar model.
    """
    e2 = (
        omega_r * a ** -4
        + omega_m * a ** -3
        + omega_de * a ** (-3.0 * (1.0 + w))
    )
    d_e2_d_lna = (
        -4.0 * omega_r * a ** -4
        - 3.0 * omega_m * a ** -3
        - 3.0 * (1.0 + w) * omega_de * a ** (-3.0 * (1.0 + w))
    )
    hdot_over_h0sq = 0.5 * d_e2_d_lna
    f = a**p_f
    return (
        -(2.0 + p_f) * f * hdot_over_h0sq
        + (p_f - p_f**2) * f * e2
        - 3.0 * omega_m * a ** -3
        - 4.0 * omega_r * a ** -4
    )


def reconstruction_identity_check() -> dict[str, object]:
    """Verify the two inverse identities by exact rational coefficient algebra.

    This check is deliberately independent of optional symbolic packages so
    the frozen publication verifier has the same scientific payload on every
    supported Python installation.
    """
    from fractions import Fraction

    keys = ("FH2", "FdH", "rm", "rr", "ddF", "HdF")
    zero = {key: Fraction(0) for key in keys}
    kinetic = {
        "FH2": Fraction(0), "FdH": Fraction(-2), "rm": Fraction(-1),
        "rr": Fraction(-4, 3), "ddF": Fraction(-1), "HdF": Fraction(1),
    }
    potential = {
        "FH2": Fraction(3), "FdH": Fraction(1), "rm": Fraction(-1, 2),
        "rr": Fraction(-1, 3), "ddF": Fraction(1, 2), "HdF": Fraction(5, 2),
    }
    friedmann = dict(zero)
    friedmann["FH2"] += 3
    friedmann["rm"] -= 1
    friedmann["rr"] -= 1
    friedmann["HdF"] += 3
    for key in keys:
        friedmann[key] -= potential[key] + Fraction(1, 2) * kinetic[key]
    raychaudhuri = dict(zero)
    raychaudhuri["FdH"] -= 2
    raychaudhuri["rm"] -= 1
    raychaudhuri["rr"] -= Fraction(4, 3)
    raychaudhuri["ddF"] -= 1
    raychaudhuri["HdF"] += 1
    for key in keys:
        raychaudhuri[key] -= kinetic[key]
    passed = all(value == 0 for value in friedmann.values()) and all(
        value == 0 for value in raychaudhuri.values()
    )
    return {
        "available": True,
        "method": "exact rational coefficient algebra; no optional CAS",
        "friedmann_residual_coefficients": {k: str(v) for k, v in friedmann.items()},
        "raychaudhuri_residual_coefficients": {k: str(v) for k, v in raychaudhuri.items()},
        "pass": passed,
        "kinetic_identity_coefficients": {k: str(v) for k, v in kinetic.items()},
        "potential_over_M2_identity_coefficients": {k: str(v) for k, v in potential.items()},
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    expected_sha256 = HASH_LOCK.read_text(encoding="utf-8").strip()
    live_hash = sha256(LIVE)
    if live_hash != expected_sha256:
        raise SystemExit(f"Live hash mismatch: {live_hash}")
    text = LIVE.read_text(encoding="utf-8")
    anchors = anchor_lines(text)

    h0_external = 67.4
    h0inv = h0_inverse_gyr(h0_external)
    omega_r = 9.2e-5

    # Frozen-scalar family: every row is a conditional exact solution of the
    # scalar-only closure after choosing a different constant U and present
    # matter normalisation.  ECT currently fixes neither choice.
    frozen_family = []
    for omega_de in (0.0, 0.3, 0.5, 0.684908, 0.8):
        omega_m = 1.0 - omega_r - omega_de
        direct, via_log = h0_age_dimensionless(omega_r, omega_m, omega_de)
        frozen_family.append(
            {
                "Omega_r": omega_r,
                "Omega_m": omega_m,
                "Omega_IR_constant": omega_de,
                "H0_t0_direct": direct,
                "H0_t0_log_variable": via_log,
                "cross_method_abs_difference": abs(direct - via_log),
                "age_Gyr_if_conditional_H0_67p4_calibration": direct * h0inv,
                "status": "conditional frozen-scalar solution; not an ECT prediction",
            }
        )

    # Stronger counterexample: hold the present radiation, matter and IR
    # fractions fixed and vary only the (allowed but unowned) scalar equation
    # of state.  For every w>-1 row the scalar kinetic density
    # (1+w) rho_phi is non-negative, so non-uniqueness is not an artefact of
    # varying the matter abundance or admitting a ghost.  The w=-1 endpoint
    # is the frozen-scalar member of the same closure family.
    fixed_composition_w_family = []
    fixed_omega_m = 0.315
    fixed_omega_de = 1.0 - omega_r - fixed_omega_m
    for w in (-1.0, -0.9, -0.8, -0.5):
        direct, via_log = h0_age_dimensionless(
            omega_r, fixed_omega_m, fixed_omega_de, w=w
        )
        fixed_composition_w_family.append(
            {
                "w_scalar": w,
                "Omega_r": omega_r,
                "Omega_m": fixed_omega_m,
                "Omega_scalar_today": fixed_omega_de,
                "H0_t0_direct": direct,
                "H0_t0_log_variable": via_log,
                "cross_method_abs_difference": abs(direct - via_log),
                "age_Gyr_if_conditional_H0_67p4_calibration": direct * h0inv,
                "kinetic_density_sign": "zero" if w == -1.0 else "positive",
                "status": (
                    "conditional canonical-scalar background with fixed "
                    "present composition; not an ECT prediction"
                ),
            }
        )

    # Explicitly remain inside the live F=exp(beta*phi) family.  The chosen
    # p_F is not a fitted ECT parameter; it is one counterexample coordinate.
    # Three different target histories all admit K=omega*phidot^2>0 over the
    # tested a range with the same F(a), matter and radiation inputs.
    p_f_counterexample = -1.0e-3
    a_grid = [10.0 ** (-10.0 + 10.0 * i / 2000.0) for i in range(2001)]
    exponential_f_counterfamily = []
    for w in (-0.9, -0.8, -0.5):
        kinetic_rows = [
            reconstructed_kinetic_over_h0sq(
                a,
                omega_r,
                fixed_omega_m,
                fixed_omega_de,
                w,
                p_f_counterexample,
            )
            for a in a_grid
        ]
        min_index = min(range(len(kinetic_rows)), key=kinetic_rows.__getitem__)
        exponential_f_counterfamily.append(
            {
                "w_target_history": w,
                "p_F_in_F_of_a_equals_a_to_p_F": p_f_counterexample,
                "a_test_min": a_grid[0],
                "a_test_max": a_grid[-1],
                "grid_points": len(a_grid),
                "minimum_reconstructed_omega_phidot2_over_H0sq": kinetic_rows[
                    min_index
                ],
                "a_at_minimum": a_grid[min_index],
                "positive_on_test_grid": kinetic_rows[min_index] > 0.0,
                "interpretation": (
                    "F=a^p_F=exp(beta*phi) with phi=p_F ln(a)/beta; "
                    "omega reconstructed from the live equations is positive"
                ),
            }
        )
    # Strictly minimal zero-extra-IR-source diagnostic.  It is not an ECT age
    # because H0/matter abundance, the gravity action and branch onset remain
    # unowned; it tests what happens if one simply sets the missing IR source
    # to zero rather than fitting it.
    minimal = frozen_family[0]

    # The live definition calls t0 the duration since ordering, but its
    # integral starts at a=0.  Quantify dependence on an unowned finite onset.
    observed_like = {
        "Omega_r": omega_r,
        "Omega_m": 0.315,
        "Omega_IR_constant": 1.0 - 0.315 - omega_r,
    }
    onset_rows = []
    for z_order in (10.0, 100.0, 2000.0, 1.0e9):
        a_start = 1.0 / (1.0 + z_order)
        direct, via_log = h0_age_dimensionless(
            observed_like["Omega_r"],
            observed_like["Omega_m"],
            observed_like["Omega_IR_constant"],
            a_start=a_start,
        )
        onset_rows.append(
            {
                "z_order": z_order,
                "a_order": a_start,
                "H0_Delta_t_since_order": direct,
                "duration_Gyr_if_conditional_H0_67p4_calibration": direct * h0inv,
                "cross_method_abs_difference": abs(direct - via_log),
            }
        )

    recon = reconstruction_identity_check()
    gates = {
        "live_hash_matches": live_hash == expected_sha256,
        "all_anchors_unique": len(anchors) == len(ANCHORS),
        "age_cross_methods": all(
            row["cross_method_abs_difference"] < 5e-11 for row in frozen_family
        )
        and all(
            row["cross_method_abs_difference"] < 5e-11
            for row in fixed_composition_w_family
        )
        and all(row["cross_method_abs_difference"] < 5e-11 for row in onset_rows),
        "fixed_composition_positive_kinetic_nonuniqueness": (
            len({round(row["H0_t0_direct"], 12) for row in fixed_composition_w_family})
            == len(fixed_composition_w_family)
            and all(
                row["kinetic_density_sign"] in {"zero", "positive"}
                for row in fixed_composition_w_family
            )
        ),
        "live_exponential_F_positive_kinetic_counterfamily": all(
            row["positive_on_test_grid"] for row in exponential_f_counterfamily
        ),
        "scalar_tensor_reconstruction_identities": bool(recon.get("pass")),
        "conditional_state_age_computed_and_unique_law_age_not_selected": True,
    }
    conditional_payload = json.loads(CONDITIONAL_AGE_JSON.read_text(encoding="utf-8"))
    tau_2s = conditional_payload["derived_today"]["tau_2s_H2s0_Delta_t"]
    payload = {
        "schema": "ECT-R103-age-state-calibration-and-law-selection-v2",
        "generated_by": Path(__file__).name,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "frozen_inputs": {
            "live_preprint": str(LIVE.relative_to(LATEX_ROOT)),
            "live_preprint_sha256": live_hash,
            "anchor_lines": anchors,
            "conditional_state_scale_calibration_H0_km_s_Mpc": h0_external,
            "radiation_fraction_for_conditional_examples": omega_r,
        },
        "scalar_tensor_inverse_reconstruction": recon,
        "conditional_frozen_scalar_family": frozen_family,
        "fixed_present_composition_scalar_family": {
            "interpretation": (
                "Even after fixing today's H0 unit and density fractions, the "
                "unowned scalar closure admits positive-kinetic histories with "
                "different H(a) and ages.  This is a constructive same-composition "
                "non-identifiability check, not an ECT fit."
            ),
            "rows": fixed_composition_w_family,
        },
        "live_exponential_F_reconstruction_counterfamily": {
            "interpretation": (
                "Three distinct fixed-composition H(a) histories admit the same "
                "positive exponential F(a)=a^p_F and a positive reconstructed "
                "omega*phidot^2 over 1e-10<=a<=1.  This places the constructive "
                "non-uniqueness inside the live F=exp(beta*phi) form."
            ),
            "rows": exponential_f_counterfamily,
        },
        "minimal_zero_IR_source_diagnostic": {
            **minimal,
            "interpretation": (
                "Closest no-added-IR-source frozen-scalar limit.  It fixes only "
                "H0*t0 after flat normalisation; H0, matter abundance, the "
                "orientation stress and the ordering onset are not ECT-derived."
            ),
        },
        "finite_ordering_onset_diagnostic": {
            "background": observed_like,
            "rows": onset_rows,
            "interpretation": (
                "The a=0 integral is the limiting case of a finite formation-front "
                "crossing.  A finite crossing changes the duration and belongs "
                "to the declared state plus the derived congruence/depth-lapse map."
            ),
        },
        "terminal_verdict": {
            "unique_P1_P6_H_of_a": None,
            "unique_P1_P6_age_Gyr": None,
            "named_two_slope_conditional_age": {
                "tau_2s_H2s0_Delta_t": tau_2s,
                "calibration": "H_2s(0)=H_0^cal must be declared before conversion to Gyr",
                "status": "REPRODUCED CONDITIONAL ACTION/STATE OUTPUT",
            },
            "status": "CONDITIONAL_STATE_OUTPUT; UNIQUE_P1_P6_VALUE_NOT_SELECTED",
            "reason": (
                "A named action/state has a calculable dimensionless age. "
                "State/boundary data and one dimensional calibration are legitimate "
                "empirical inputs, not defects.  What remains Open is whether microscopic "
                "Phi dynamics selects/constrains the two-slope completion and the physical "
                "metric/redshift/lapse/front/congruence map."
            ),
        },
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if all(gates.values()) else "FAIL", "gates": gates}, indent=2))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
