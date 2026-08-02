#!/usr/bin/env python3
"""Freeze and verify the corrected interpretation of the R103 finite-body proxy.

The expensive collocation/sparse-Newton calculation is replayed by the frozen
Python bytecode beside this file.  This correction verifier checks that the
scientific profile payload agrees with the pre-correction replay to floating
precision, recomputes the small-body regime independently, and emits a v2
JSON whose terminal verdict does not confuse unreachable homogeneous roots
with realised finite-body fields.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LATEX_ROOT = ROOT.parents[1]
RESULTS = LATEX_ROOT / "data/cosmology_r103"
REPLAY = RESULTS / "R103_TWOSLOPE_FINITE_BODY_REPLAY_ORIGINAL_v1.json"
REFERENCE = RESULTS / "R103_TWOSLOPE_FINITE_BODY_RESULTS_REFERENCE_v1.json"
OUT = RESULTS / "R103_TWOSLOPE_FINITE_BODY_RESULTS_v2.json"

A = 0.01
KAPPA = 10.0
V_MINUS = 0.82485
V_PLUS = 1.27485
SOURCE_COEFF = (V_PLUS - V_MINUS) / (3.0 * V_PLUS - V_MINUS)
DISPLAYED_CASSINI_GATE = 2.3e-5
CASSINI_CENTRAL = 2.1e-5
CASSINI_ONE_SIGMA = 2.3e-5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close_tree(a, b, path="root") -> list[str]:
    """Return discrepancies, accepting only harmless floating round-off."""
    errors: list[str] = []
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            errors.append(f"{path}: key mismatch")
            return errors
        for key in sorted(a):
            errors.extend(close_tree(a[key], b[key], f"{path}.{key}"))
        return errors
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length mismatch"]
        for i, (av, bv) in enumerate(zip(a, b, strict=True)):
            errors.extend(close_tree(av, bv, f"{path}[{i}]"))
        return errors
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isclose(float(a), float(b), rel_tol=5e-14, abs_tol=5e-15):
            errors.append(f"{path}: {a!r} != {b!r}")
        return errors
    if a != b:
        errors.append(f"{path}: {a!r} != {b!r}")
    return errors


def science_payload(payload: dict) -> dict:
    keep_checks = (
        "rho_out_matches_named_state",
        "positive_vacuum_root",
        "exterior_linear_mass_normalised",
        "all_flux_identities_below_2e_minus_5",
        "two_methods_below_3e_minus_3",
        "far_suppression_monotone",
    )
    return {
        "derivation": payload["derivation"],
        "inputs": payload["inputs"],
        "rows": payload["rows"],
        "checks": {k: payload["checks"][k] for k in keep_checks},
    }


def main() -> None:
    replay = json.loads(REPLAY.read_text(encoding="utf-8"))
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    profile_errors = close_tree(science_payload(replay), science_payload(reference))

    corrected_rows = []
    row_errors = []
    for row in reference["dimensional_object_diagnostic"]["rows"]:
        contrast = float(row["density_contrast_to_cosmic_matter"])
        mout_r = float(row["m_out_R"])
        xi = SOURCE_COEFF * (contrast - 1.0) * mout_r**2
        surface = xi / (3.0 * (1.0 + mout_r))
        center = surface + xi / 6.0
        updated = dict(row)
        for key, expected in (
            ("small_body_source_Xi_body", xi),
            ("linear_delta_u_surface", surface),
            ("linear_delta_u_center", center),
        ):
            actual = float(row["small_body_source_Xi"] if key == "small_body_source_Xi_body" else row[key])
            # The frozen reference stored the leading m_out R -> 0 forms
            # Xi/3 and Xi/2.  Their relative difference from the exact
            # linear Yukawa matching is O(m_out R), which is checked here.
            allowed_rel = max(5e-14, 2.0 * mout_r)
            if not math.isclose(actual, expected, rel_tol=allowed_rel, abs_tol=1e-30):
                row_errors.append(f"{row['object']}.{key}: {actual} != {expected}")
            updated[key] = expected
        updated.pop("small_body_source_Xi", None)
        corrected_rows.append(updated)

    gamma = (KAPPA + A**2) / (KAPPA + 2.0 * A**2)
    abs_gamma_minus_one = abs(gamma - 1.0)
    cassini_sigma_distance = abs((gamma - 1.0) - CASSINI_CENTRAL) / CASSINI_ONE_SIGMA
    checks = {
        "frozen_profile_replay_matches_reference_within_5e_minus_14": not profile_errors,
        "small_body_formula_reproduced": not row_errors,
        "all_named_objects_Xi_body_below_1e_minus_8": all(
            float(r["small_body_source_Xi_body"]) < 1e-8 for r in corrected_rows
        ),
        "all_named_objects_counterfactual_m_in_R_below_1": all(
            float(r["counterfactual_equilibrium_m_in_R"]) < 1.0
            for r in corrected_rows
        ),
        "unscreened_gamma_passes_displayed_project_gate": (
            abs_gamma_minus_one < DISPLAYED_CASSINI_GATE
        ),
        "unscreened_gamma_within_two_sigma_of_Cassini_central": (
            cassini_sigma_distance < 2.0
        ),
    }
    payload = {
        "date": "2026-07-18",
        "status": "CORRECTED_MODEL_INTERNAL_REGIME_CLASSIFICATION",
        "supersedes": (
            "Sections 4-5 and the terminal interpretation of "
            "R103_TWOSLOPE_FINITE_BODY_AUDIT_v1.md"
        ),
        "unchanged_profile_science": science_payload(reference),
        "dimensional_object_diagnostic": {
            "rows": corrected_rows,
            "unscreened_gamma_PPN": gamma,
            "unscreened_abs_gamma_minus_one": abs_gamma_minus_one,
            "displayed_project_Cassini_abs_gamma_minus_one_gate": DISPLAYED_CASSINI_GATE,
            "Cassini_measured_gamma_minus_one_central": CASSINI_CENTRAL,
            "Cassini_measured_gamma_minus_one_one_sigma": CASSINI_ONE_SIGMA,
            "conditional_unscreened_proxy_distance_from_Cassini_central_sigma": cassini_sigma_distance,
            "verdict": (
                "NO MASS SCREENING in the named near-GR two-slope slice. "
                "The formal homogeneous equilibrium roots are not reached; "
                "Xi_body is tiny and u remains close to 1. The displayed "
                "absolute-deviation proxy gate passes and the displayed "
                "conditional unscreened proxy lies within two formal quoted "
                "sigmas, but outside the literal one-sigma interval "
                "of the Cassini central value. The coupled finite-body "
                "metric, beta, preferred-frame, WEP, variation and "
                "environmental-charge observables remain Open."
            ),
        },
        "checks": checks,
        "profile_discrepancies": profile_errors,
        "small_body_discrepancies": row_errors,
        "all_checks_pass": all(checks.values()),
        "provenance": {
            "frozen_replay_json_sha256": sha256(REPLAY),
            "corrected_reference_json_sha256": sha256(REFERENCE),
            "reference_csv_sha256": sha256(
                RESULTS / "R103_TWOSLOPE_FINITE_BODY_RESULTS_REFERENCE_v1.csv"
            ),
            "correction_note_sha256": sha256(
                RESULTS / "R103_TWOSLOPE_FINITE_BODY_CORRECTION_v2.md"
            ),
            "verifier_sha256": sha256(Path(__file__)),
        },
        "runtime": {"python": platform.python_version()},
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
