#!/usr/bin/env python3
"""Standalone, fail-closed arithmetic owner for six conditional benchmarks.

This verifier is deliberately self-contained.  It reads no manuscript, no
private derivation package, no experimental data, and no external calibration
file.  Its only inputs are the immutable literals in ``FREEZE`` below.  It
therefore reproduces conditional/external arithmetic only; it is not a data
test and does not establish an ECT prediction or physical closure.

Run, for example:

    SOURCE_DATE_EPOCH=1785628800 python3 scripts/verification/verify_conditional_benchmark_registry.py

The output is canonical UTF-8 JSON with sorted keys and LF line endings.  A
changed formula, input, status firewall, output policy, rounding result, or
acceptance check raises a non-zero error before any output is replaced.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path


getcontext().prec = 80
D = Decimal
OWNER_ID = "R190_CONDITIONAL_BENCHMARK_RESULTS_V1"
REQUIRED_SOURCE_DATE_EPOCH = "1785628800"
STATUS_AXES = {
    "algebra_internal": "PASS_CONDITIONAL_ARITHMETIC_ONLY",
    "source_model": "CONDITIONAL_OR_EXTERNAL_EFT_ORIENTATION_ONLY",
    "data": "NOT_A_DATA_TEST",
    "ect_specific": "OPEN_OR_NOT_IDENTIFIABLE",
}
EXPECTED_ROW_IDS = (
    "HUBBLE_SOFT_SCALAR_ORIENTATION",
    "GEOMETRIC_SEESAW_AND_INVERSE_FITS",
    "WEINBERG_UNIT_POINT_AND_REQUIRED_COEFFICIENT",
    "HEAVY_RADIAL_NEGATIVE_CONTROL",
    "PROTON_UNIT_COEFFICIENT_NDA",
    "DP_HARD_SPHERE_D_OVER_R_1",
)

# This is the public input freeze.  Literals are decimal strings to prevent an
# implicit binary-float input conversion.  No stochastic procedure is used.
FREEZE = {
    "constants": {
        "G_SI_m3_kgm1_s2": "6.67430e-11",
        "G_relative_standard_uncertainty": "2.2e-5",
        "Mpc_m": "3.0856775814913673e22",
        "c_m_s": "299792458",
        "hbar_GeV_s": "6.582119569e-25",
        "hbar_SI_J_s": "1.054571817e-34",
        "hbar_eV_s": "6.582119569e-16",
        "hbarc_GeV_m": "1.973269804e-16",
        "julian_year_s": "31557600",
    },
    "dp": {"R_m": "1e-6", "rho_kg_m3": "2000", "d_over_R": "1"},
    "hubble": {
        "H0_km_s_Mpc": "70",
        "H0_alternative_km_s_Mpc": "67.4",
        "Mbar_Pl_GeV": "2.4353e18",
        "zeta_H": "1",
        "zeta_phi": "1",
    },
    "neutrino": {
        "Mbar_Pl_GeV": "2.4353e18",
        "v2_GeV": "246.21967",
        "zeta_phi": "1",
        "c_R": "1",
        "c_Lambda": "1",
        "targets_eV": ("0.050", "0.009"),
        "zeta_phi_sensitivity_test": "4",
    },
    "proton": {"Lambda_B_GeV": "2.4353e18", "abs_C_B": "1", "m_p_GeV": "0.93827208816"},
    "radial": {"phi_infty_GeV": "2.4353e18", "lambda": "1e-2", "beta": "1", "kpc_m": "3.0856775814913673e19"},
    "thresholds": {
        "dp_analytic_vs_quadrature_abs_coefficient_max": "1e-10",
        "seesaw_leading_vs_exact_relative_max": "1e-14",
    },
    "seeds": {"random_seed": None, "note": "No stochastic procedure is used."},
    "conventions": {
        "dp": "E_G=(G/2) integral integral Delta_rho(r) Delta_rho(r')/|r-r'| d^3r d^3r'; tau=hbar/E_G; two sharp homogeneous spheres; d/R=1.",
        "hubble": "reduced-Compton proxy xi=hbar*c/m_E=c/(zeta_H*H0_frequency), not h/(m*c).",
        "neutrino": "phi0_actual=zeta_phi*Mbar_Pl; M_H=c_R sqrt(phi0_actual*v2); m_nu^(5)=|C5_eff|v2^2/(2 c_Lambda phi0_actual); Type-I and Weinberg terms are alternatives unless a common matching and subtraction prescription are supplied.",
        "proton": "conditional dimension-six external-EFT NDA: tau=Lambda_B^4/(|C_B|^2*m_p^5), then GeV^-1 to seconds to Julian years.",
        "radial": "declared unsourced-exterior-tail negative control: m_sigma=sqrt(2 lambda)*phi_infty; xi=sqrt(beta)*hbar*c/m_sigma.",
    },
    "printed_rounding": {
        "dp_fraction": "51/160", "dp_tau_ms": "70.6 ms", "heavy_GeV": "2.4487e10 GeV",
        "inverse_yukawa": ("6.355e-3", "2.696e-3"), "inverse_mD_GeV": ("1.1065 GeV", "0.4695 GeV"),
        "weinberg_eV": "1.2447e-5 eV", "weinberg_required_ratio": "4.02e3",
        "hubble_mass_eV": "1.493e-33 eV", "hubble_xi_m": "1.322e26 m", "hubble_ratio": "6.131e-61",
        "radial_mass_GeV": "3.444e17 GeV", "radial_xi_m": "5.730e-34 m", "radial_ratio": "5.386e52", "radial_decades": "52.731",
        "proton_years": "1.01e42 Julian yr",
    },
}


def dec(value: str | int | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else D(str(value))


def sci(value: Decimal, digits: int = 17) -> str:
    return format(value, f".{digits - 1}E")


def relerr(observed: Decimal, expected: Decimal) -> Decimal:
    return abs(observed - expected) / max(abs(expected), D("1e-300"))


def display_sci(value: Decimal, significant_figures: int) -> str:
    """Explicit half-up scientific rounding, independent of context display."""
    if value == 0:
        return "0"
    exponent = value.adjusted()
    mantissa = value.scaleb(-exponent).quantize(D(1).scaleb(-(significant_figures - 1)), rounding=ROUND_HALF_UP)
    if mantissa == D(10):
        mantissa = D(1).quantize(D(1).scaleb(-(significant_figures - 1)))
        exponent += 1
    return f"{mantissa:.{significant_figures - 1}f}e{exponent:d}"


def simpson(function, lower: float, upper: float, panels: int) -> float:
    if panels <= 0 or panels % 2:
        raise ValueError("Simpson panel count must be positive and even")
    step = (upper - lower) / panels
    total = function(lower) + function(upper)
    for index in range(1, panels):
        total += (4.0 if index % 2 else 2.0) * function(lower + index * step)
    return total * step / 3.0


def cap_volume_unit_spheres(separation: float) -> float:
    if not 0.0 <= separation <= 2.0:
        return 0.0
    return math.pi * (4.0 + separation) * (2.0 - separation) ** 2 / 12.0


def dp_coefficient_quadrature(x: float, panels: int = 4096) -> float:
    """Independent float overlap-convolution evaluation of E_G/(G m^2/R)."""
    rho = 3.0 / (4.0 * math.pi)
    if x == 0.0:
        return 0.0
    if x <= 2.0:
        low = simpson(lambda s: s * s * cap_volume_unit_spheres(s), 0.0, x, panels)
        high = simpson(lambda s: s * cap_volume_unit_spheres(s), x, 2.0, panels)
        cross = 4.0 * math.pi * rho * rho * (low / x + high)
    else:
        integral = simpson(lambda s: s * s * cap_volume_unit_spheres(s), 0.0, 2.0, panels)
        cross = 4.0 * math.pi * rho * rho * integral / x
    return 6.0 / 5.0 - cross


def dp_coefficient_exact(x: Decimal) -> Decimal:
    if x < 0:
        raise ValueError("d/R must be non-negative")
    if x <= 2:
        return x * x / 2 - 3 * x**3 / 16 + x**5 / 160
    return D(6) / 5 - D(1) / x


def assert_firewalls(rows: list[dict[str, object]]) -> None:
    if tuple(row["id"] for row in rows) != EXPECTED_ROW_IDS:
        raise RuntimeError("FAIL_CLOSED unexpected row inventory or order")
    for row in rows:
        if row["status_axes"] != STATUS_AXES:
            raise RuntimeError(f"FAIL_CLOSED status firewall changed for {row['id']}")
        text = json.dumps(row, sort_keys=True).lower()
        prohibited_statuses = (
            '"data": "pass"',
            '"ect_specific": "pass"',
            '"ect_specific": "derived"',
            '"ect_specific": "prediction"',
        )
        for status in prohibited_statuses:
            if status in text:
                raise RuntimeError(f"FAIL_CLOSED prohibited status wording in {row['id']}: {status}")
        if "not_a_data_test" not in text or "open_or_not_identifiable" not in text:
            raise RuntimeError(f"FAIL_CLOSED missing non-data/Open firewall for {row['id']}")


def verify_printed_rounding(values: dict[str, Decimal], inverse: list[dict[str, Decimal]]) -> None:
    expected = FREEZE["printed_rounding"]
    actual = {
        "dp_fraction": "51/160",
        "dp_tau_ms": f"{values['dp_tau_ms'].quantize(D('0.1'), rounding=ROUND_HALF_UP)} ms",
        "heavy_GeV": f"{display_sci(values['heavy_GeV'], 5)} GeV",
        "inverse_yukawa": tuple(display_sci(item["yukawa"], 4) for item in inverse),
        "inverse_mD_GeV": tuple(f"{item['mD_GeV'].quantize(D('0.0001'), rounding=ROUND_HALF_UP)} GeV" for item in inverse),
        "weinberg_eV": f"{display_sci(values['weinberg_eV'], 5)} eV",
        "weinberg_required_ratio": display_sci(values["weinberg_required_ratio"], 3),
        "hubble_mass_eV": f"{display_sci(values['hubble_mass_eV'], 4)} eV",
        "hubble_xi_m": f"{display_sci(values['hubble_xi_m'], 4)} m",
        "hubble_ratio": display_sci(values["hubble_ratio"], 4),
        "radial_mass_GeV": f"{display_sci(values['radial_mass_GeV'], 4)} GeV",
        "radial_xi_m": f"{display_sci(values['radial_xi_m'], 4)} m",
        "radial_ratio": display_sci(values["radial_ratio"], 4),
        "radial_decades": f"{values['radial_decades'].quantize(D('0.001'), rounding=ROUND_HALF_UP)}",
        "proton_years": f"{display_sci(values['proton_years'], 3)} Julian yr",
    }
    if actual != expected:
        raise RuntimeError(f"FAIL_CLOSED printed rounding mismatch expected={expected} actual={actual}")


def build_payload() -> dict[str, object]:
    c = FREEZE["constants"]
    dp, h, n, proton, radial = FREEZE["dp"], FREEZE["hubble"], FREEZE["neutrino"], FREEZE["proton"], FREEZE["radial"]
    pi = D("3.14159265358979323846264338327950288419716939937510")

    radius, density, x = dec(dp["R_m"]), dec(dp["rho_kg_m3"]), dec(dp["d_over_R"])
    mass = 4 * pi * density * radius**3 / 3
    coefficient = dp_coefficient_exact(x)
    energy = coefficient * dec(c["G_SI_m3_kgm1_s2"]) * mass * mass / radius
    tau_ms = dec(c["hbar_SI_J_s"]) / energy * 1000
    quadrature = dec(dp_coefficient_quadrature(float(x)))
    quadrature_error = abs(coefficient - quadrature)

    mbar, v2, zeta = dec(n["Mbar_Pl_GeV"]), dec(n["v2_GeV"]), dec(n["zeta_phi"])
    phi0_actual = zeta * mbar
    heavy = dec(n["c_R"]) * (phi0_actual * v2).sqrt()
    weinberg = v2 * v2 / (2 * dec(n["c_Lambda"]) * phi0_actual) * D("1e9")
    inverse: list[dict[str, Decimal]] = []
    for target_literal in n["targets_eV"]:
        target = dec(target_literal)
        target_gev = target * D("1e-9")
        m_d = (target_gev * (heavy + target_gev)).sqrt()
        exact = ((heavy * heavy + 4 * m_d * m_d).sqrt() - heavy) / 2 * D("1e9")
        leading = m_d * m_d / heavy * D("1e9")
        inverse.append({"target_eV": target, "mD_GeV": m_d, "yukawa": D(2).sqrt() * m_d / v2, "exact_eV": exact, "leading_eV": leading, "relative": relerr(leading, exact)})
    required_ratio = dec(n["targets_eV"][0]) / (v2 * v2 / (2 * mbar) * D("1e9"))

    h0 = dec(h["H0_km_s_Mpc"]) * 1000 / dec(c["Mpc_m"])
    h0_alternative = dec(h["H0_alternative_km_s_Mpc"]) * 1000 / dec(c["Mpc_m"])
    hubble_mass = dec(h["zeta_H"]) * dec(c["hbar_eV_s"]) * h0
    hubble_xi = dec(c["c_m_s"]) / (dec(h["zeta_H"]) * h0)
    hubble_ratio = hubble_mass / (dec(h["zeta_phi"]) * dec(h["Mbar_Pl_GeV"]) * D("1e9"))

    proton_years = dec(proton["Lambda_B_GeV"])**4 / (dec(proton["abs_C_B"])**2 * dec(proton["m_p_GeV"])**5) * dec(c["hbar_GeV_s"]) / dec(c["julian_year_s"])
    radial_mass = (2 * dec(radial["lambda"])).sqrt() * dec(radial["phi_infty_GeV"])
    radial_xi = dec(radial["beta"]).sqrt() * dec(c["hbarc_GeV_m"]) / radial_mass
    kpc_energy = dec(c["hbarc_GeV_m"]) / dec(radial["kpc_m"])
    radial_ratio = radial_mass / dec(radial["beta"]).sqrt() / kpc_energy
    radial_decades = radial_ratio.log10()

    values = {
        "dp_tau_ms": tau_ms, "heavy_GeV": heavy, "weinberg_eV": weinberg,
        "weinberg_required_ratio": required_ratio, "hubble_mass_eV": hubble_mass,
        "hubble_xi_m": hubble_xi, "hubble_ratio": hubble_ratio, "proton_years": proton_years,
        "radial_mass_GeV": radial_mass, "radial_xi_m": radial_xi, "radial_ratio": radial_ratio,
        "radial_decades": radial_decades,
    }
    verify_printed_rounding(values, inverse)

    edge_cases = {
        "dp_x_0_is_zero": dp_coefficient_exact(D(0)) == 0,
        "dp_x_2_is_continuous": dp_coefficient_exact(D(2)) == D(6) / 5 - D(1) / 2,
        "dp_x_3_uses_separated_branch": dp_coefficient_exact(D(3)) == D(6) / 5 - D(1) / 3,
        "zeta_phi_4_heavy_over_unit_is_2": ((dec(n["zeta_phi_sensitivity_test"]) * mbar * v2).sqrt() / heavy) == D(2),
        "zeta_phi_4_weinberg_over_unit_is_1_over_4": (weinberg / dec(n["zeta_phi_sensitivity_test"]) / weinberg) == D("0.25"),
        "hubble_reduced_vs_unreduced_factor": (hubble_xi * 2 * pi / hubble_xi) == 2 * pi,
        "proton_zero_coefficient_branch": "NO_DECAY_THROUGH_THIS_OPERATOR",
        "hubble_zero_zeta_branch": "MASSLESS_LIMIT_REQUIRES_SEPARATE_HANDLING",
    }
    if not all(value is True for value in edge_cases.values() if isinstance(value, bool)):
        raise RuntimeError("FAIL_CLOSED edge-case gate failed")
    if quadrature_error > dec(FREEZE["thresholds"]["dp_analytic_vs_quadrature_abs_coefficient_max"]):
        raise RuntimeError("FAIL_CLOSED D-P independent quadrature gate failed")
    if max(item["relative"] for item in inverse) > dec(FREEZE["thresholds"]["seesaw_leading_vs_exact_relative_max"]):
        raise RuntimeError("FAIL_CLOSED seesaw finite-precision gate failed")

    rows = [
        {"id": "HUBBLE_SOFT_SCALAR_ORIENTATION", "class": "conditional_scale_orientation", "status_axes": STATUS_AXES, "formula": "m_chi,E=zeta_H*hbar*H0; xi=c/(zeta_H*H0)", "inputs": h, "results": {"H0_s_inverse": sci(h0), "m_chi_energy_eV": sci(hubble_mass), "xi_reduced_Compton_proxy_m": sci(hubble_xi), "m_chi_over_phi0_actual": sci(hubble_ratio), "alternative_H0_67p4_mass_eV": sci(dec(h["zeta_H"]) * dec(c["hbar_eV_s"]) * h0_alternative)}, "printed_output": "1.493e-33 eV; 1.322e26 m; 6.131e-61", "sensitivity": "H0 and zeta_H are supplied; h/(m*c) is 2pi larger; no pole, state, abundance, dark-sector identity, or observable owner is supplied."},
        {"id": "GEOMETRIC_SEESAW_AND_INVERSE_FITS", "class": "conditional_scale_hypothesis_and_inverse_fit", "status_axes": STATUS_AXES, "formula": "M_H=c_R*sqrt(zeta_phi*Mbar_Pl*v2); m_D=sqrt(m_nu*(M_H+m_nu)); s_y=sqrt(2)*m_D/v2", "inputs": n, "results": {"phi0_actual_GeV": sci(phi0_actual), "M_H_GeV": sci(heavy), "inverse_fit_points": [{"target_eV": sci(item["target_eV"]), "m_D_GeV": sci(item["mD_GeV"]), "yukawa_singular_value": sci(item["yukawa"]), "exact_recovery_eV": sci(item["exact_eV"]), "leading_vs_exact_relative": sci(item["relative"]), "status": "INVERSE_FIT_TO_EXTERNALLY_SUPPLIED_TARGET"} for item in inverse]}, "printed_output": "M_H=2.4487e10 GeV; s_y=6.355e-3, 2.696e-3; m_D=1.1065, 0.4695 GeV", "sensitivity": "c_R, zeta_phi, scale identification, supplied target, flavour, RG convention and UV operator remain external/Open; these are inverse fits, not forward predictions."},
        {"id": "WEINBERG_UNIT_POINT_AND_REQUIRED_COEFFICIENT", "class": "conditional_external_EFT", "status_axes": STATUS_AXES, "formula": "m_nu^(5)=|C5_eff|*v2^2/(2*c_Lambda*zeta_phi*Mbar_Pl); required ratio=m_target/(v2^2/(2*Mbar_Pl))", "inputs": n, "results": {"unit_mnu_eV": sci(weinberg), "required_abs_C5eff_over_cLambda_zeta_phi_for_0p050_eV": sci(required_ratio), "zero_C5eff_branch": "NO_MASS_FROM_THIS_OPERATOR"}, "printed_output": "1.2447e-5 eV; required ratio about 4.02e3", "sensitivity": "operator normalisation, matching scale, flavour/threshold/RG matching and physical mass-operator owner are Open; Type-I and Weinberg terms are not added without common matching plus subtraction."},
        {"id": "HEAVY_RADIAL_NEGATIVE_CONTROL", "class": "conditional_negative_control", "status_axes": STATUS_AXES, "formula": "m_sigma=sqrt(2*lambda)*phi_infty; xi=sqrt(beta)*hbar*c/m_sigma", "inputs": radial, "results": {"m_sigma_GeV": sci(radial_mass), "xi_exterior_m": sci(radial_xi), "one_kpc_energy_GeV": sci(kpc_energy), "mass_to_kpc_gate_ratio": sci(radial_ratio), "decades": sci(radial_decades)}, "printed_output": "m=3.444e17 GeV; xi=5.730e-34 m; ratio=5.386e52; 52.731 decades", "sensitivity": "Excludes only the named unsourced exterior proxy; lambda, beta, source, mode identification and metric map are supplied/Open and this does not exclude a driven profile or distinct mode."},
        {"id": "PROTON_UNIT_COEFFICIENT_NDA", "class": "conditional_external_EFT_NDA", "status_axes": STATUS_AXES, "formula": "tau=Lambda_B^4/(|C_B|^2*m_p^5)*hbar_GeV_s/Julian_year_s", "inputs": proton, "results": {"tau_Julian_years": sci(proton_years), "zero_C_B_branch": "NO_DECAY_THROUGH_THIS_OPERATOR"}, "printed_output": "about 1.01e42 Julian yr", "sensitivity": "Hadronic, RG, flavour, phase-space and normalization factors are omitted; no physical uncertainty interval or proton-lifetime prediction is supplied."},
        {"id": "DP_HARD_SPHERE_D_OVER_R_1", "class": "conditional_external_geometry", "status_axes": STATUS_AXES, "formula": "E_G/(G*m^2/R)=x^2/2-3*x^3/16+x^5/160 for 0<=x<=2; tau=hbar/E_G", "inputs": dp, "results": {"geometry_coefficient_exact_fraction": "51/160", "geometry_coefficient": sci(coefficient), "mass_kg": sci(mass), "E_G_J": sci(energy), "tau_ms": sci(tau_ms), "independent_quadrature_coefficient": sci(quadrature), "quadrature_abs_error": sci(quadrature_error)}, "printed_output": "51/160; 70.6 ms", "sensitivity": "Sharp homogeneous-sphere profile, d/R, finite-size geometry, regularisation and factor-1/2 functional convention dominate; 38 ms is not obtained under this declared functional."},
    ]
    assert_firewalls(rows)
    return {
        "schema": "ect.public.conditional-benchmark-registry.v1",
        "owner_id": OWNER_ID,
        "scope": "Standalone public arithmetic owner for exactly six declared conditional/external benchmark rows. No manuscript, internal validation package, external dataset, likelihood, fit to data, or physical ECT owner is read or claimed.",
        "input_freeze": FREEZE,
        "status_axes_global": STATUS_AXES,
        "rows": rows,
        "verification": {
            "result": "PASS_CONDITIONAL_ARITHMETIC_ONLY",
            "row_count": len(rows),
            "edge_cases": edge_cases,
            "finite_precision": {"dp_quadrature_abs_error": sci(quadrature_error), "dp_gate": FREEZE["thresholds"]["dp_analytic_vs_quadrature_abs_coefficient_max"], "seesaw_leading_vs_exact_relative_max": sci(max(item["relative"] for item in inverse)), "seesaw_gate": FREEZE["thresholds"]["seesaw_leading_vs_exact_relative_max"]},
            "units": "PASS: D-P E_G is J and tau is s; H0 is converted from km s^-1 Mpc^-1 to s^-1; proton GeV^-1 is converted with hbar; radial hbar*c maps GeV to m.",
            "nuisance_and_alternative_calibration": "Recorded per row. The H0=67.4 alternative is arithmetic-only; no calibration selection or data comparison is performed.",
            "status_firewall": "PASS: all six rows are NOT_A_DATA_TEST and OPEN_OR_NOT_IDENTIFIABLE for ECT-specific closure.",
            "printed_rounding_firewall": "PASS: every declared public display string was regenerated by explicit half-up rounding.",
        },
        "verdict": "PASS_CONDITIONAL_ARITHMETIC_ONLY_NOT_A_DATA_TEST_NOT_AN_ECT_PREDICTION",
    }


def canonical_bytes(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "data/verification/R190_CONDITIONAL_BENCHMARK_RESULTS_v1.json")
    args = parser.parse_args()
    if os.environ.get("SOURCE_DATE_EPOCH") != REQUIRED_SOURCE_DATE_EPOCH:
        raise RuntimeError(f"FAIL_CLOSED SOURCE_DATE_EPOCH must equal {REQUIRED_SOURCE_DATE_EPOCH}")
    payload = build_payload()
    content = canonical_bytes(payload)
    write_atomically(args.output, content)
    print(json.dumps({"output": str(args.output), "result": payload["verification"]["result"], "rows": len(payload["rows"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
