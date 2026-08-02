#!/usr/bin/env python3
"""Publication-side covariance-aware R103 chronometer subset calculation.

This script reconstructs the exact "suggested" covariance prescription in
Moresco's official CCcovariance GitLab notebook at commit
881413330a7f1e1e5203607d6964db49b4c6c461:

    C = diag(errHz**2)
        + outer(Hz * IMF_fraction, Hz * IMF_fraction)
        + outer(Hz * SPS_out_of_overlap_fraction,
                Hz * SPS_out_of_overlap_fraction).

It then profiles the single dimensional scale H0 against the frozen R103
two-slope shape E(z).  It is deliberately a Level-C conditional calculation;
it does not claim a full 32-point likelihood or an ECT prediction of H0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.special import gammainc, gammaincc


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.hrc.external_inputs import (  # noqa: E402
    ExternalInputError,
    resolve_external_input,
)

DATA = ROOT / "data/cosmology_r103"
HZ_DATA_LOGICAL = (
    "data/cosmology_r103/"
    "OFFICIAL_CCcovariance_HzTable_MM_BC03_commit88141333.dat"
)
MODEL_DATA_LOGICAL = (
    "data/cosmology_r103/"
    "OFFICIAL_CCcovariance_data_MM20_commit88141333.dat"
)
HZ_DATA_REPACKAGED_SHA256 = (
    "0fa5e906dc0a2d58d63fdba746bfe2fbb5610a1d54e896b450795f323997fb01"
)
MODEL_DATA_REPACKAGED_SHA256 = (
    "8c88a10a0cf69620937da6c51c0c5a925377c1b514404e91ea9dae3263123c07"
)
E_SNAPSHOT = DATA / "R103_TWO_SLOPE_E_AT_OFFICIAL_BC03_15_v1.csv"
DEFAULT_OUTPUT = DATA / "R103_OFFICIAL_CCCOVARIANCE_SUBSET_RESULT_v1.json"
DEFAULT_BACKGROUND = DATA / "R103_TWO_SLOPE_BACKGROUND_DENSE_v1.csv"

OFFICIAL_REPOSITORY = "https://gitlab.com/mmoresco/CCcovariance.git"
OFFICIAL_COMMIT = "881413330a7f1e1e5203607d6964db49b4c6c461"
OFFICIAL_HZ_SHA256 = (
    "32ce92caf251cb60a7a837c71f1856bea2b44fa5c1041f85410d11cb8164da98"
)
OFFICIAL_MODEL_SHA256 = (
    "577ac2f346e346fe7cf94daa7b7000c05d04ebc8a029cda31e0d8643b956a485"
)
OFFICIAL_NOTEBOOK_SHA256 = (
    "bea181a885f76ce479c226a4504758bcec9901386fcb2c9ef4000e8ecc696e30"
)
BACKGROUND_SHA256 = (
    "03c9c3e7894e3b0f5b258ba0275abdf76faf80083223fe46f44727c25ebcfe56"
)

TAU_TWO_SLOPE = 0.9636867786415146
HUBBLE_TIME_AT_H0_1_GYR = 977.7922216807891

EXPECTED = {
    "H0": 68.58601813180302,
    "sigma": 3.949096634841164,
    "chi2": 6.2805505847112935,
    "age": 13.738739497625918,
    "age_sigma": 0.7910593353410588,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def portable_path(path: Path) -> str:
    """Return a checkout-independent path for frozen in-repository inputs."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def chi2_tails(value: float, dof: int) -> tuple[float, float]:
    shape = dof / 2.0
    x = value / 2.0
    return float(gammainc(shape, x)), float(gammaincc(shape, x))


def fit_scale(e: np.ndarray, h: np.ndarray, c: np.ndarray) -> dict[str, float]:
    ci_e = np.linalg.solve(c, e)
    ci_h = np.linalg.solve(c, h)
    denominator = float(e @ ci_e)
    h0 = float((e @ ci_h) / denominator)
    sigma = float(denominator ** -0.5)
    residual = h - h0 * e
    chi2 = float(residual @ np.linalg.solve(c, residual))
    dof = len(h) - 1
    lower, upper = chi2_tails(chi2, dof)
    return {
        "H0_best": h0,
        "H0_sigma_formal_covariance": sigma,
        "chi2_min": chi2,
        "dof": int(dof),
        "chi2_per_dof": chi2 / dof,
        "chi2_lower_tail_probability": lower,
        "chi2_upper_tail_probability": upper,
    }


def load_inputs(hz_data: Path, model_data: Path) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    z, h, err = np.genfromtxt(
        hz_data,
        comments="#",
        usecols=(0, 1, 2),
        delimiter=",",
        unpack=True,
    )
    z_mod, imf, slib, sps, spsooo = np.genfromtxt(
        model_data,
        comments="#",
        unpack=True,
    )
    e_table = np.genfromtxt(
        E_SNAPSHOT,
        comments="#",
        delimiter=",",
        skip_header=3,
        names=True,
    )
    if len(z) != 15 or len(e_table) != 15:
        raise SystemExit("15-point input-size gate failed")
    if not np.all(np.diff(z) > 0) or not np.all(err > 0):
        raise SystemExit("input ordering/positivity gate failed")
    if not np.array_equal(z, np.asarray(e_table["z"], dtype=float)):
        raise SystemExit("E(z) redshift alignment gate failed")
    imf_fraction = np.interp(z, z_mod, imf) / 100.0
    slib_fraction = np.interp(z, z_mod, slib) / 100.0
    sps_fraction = np.interp(z, z_mod, sps) / 100.0
    spsooo_fraction = np.interp(z, z_mod, spsooo) / 100.0
    e = np.asarray(e_table["E_two_slope_pchip"], dtype=float)
    return (
        z,
        h,
        err,
        imf_fraction,
        slib_fraction,
        sps_fraction,
        spsooo_fraction,
        e,
    )


def build_covariance(
    h: np.ndarray,
    err: np.ndarray,
    imf_fraction: np.ndarray,
    spsooo_fraction: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    imf_load = h * imf_fraction
    spsooo_load = h * spsooo_fraction
    covariance = (
        np.diag(err**2)
        + np.outer(imf_load, imf_load)
        + np.outer(spsooo_load, spsooo_load)
    )
    return covariance, imf_load, spsooo_load


def woodbury_inverse(
    err: np.ndarray,
    imf_load: np.ndarray,
    spsooo_load: np.ndarray,
) -> np.ndarray:
    diagonal_inverse = np.diag(err**-2)
    loads = np.column_stack((imf_load, spsooo_load))
    core = np.eye(2) + loads.T @ diagonal_inverse @ loads
    return (
        diagonal_inverse
        - diagonal_inverse
        @ loads
        @ np.linalg.solve(core, loads.T @ diagonal_inverse)
    )


def four_node_lagrange(
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    queries: np.ndarray,
) -> np.ndarray:
    values: list[float] = []
    for query in queries:
        right = int(np.searchsorted(x_grid, query))
        right = max(2, min(right, len(x_grid) - 2))
        xs = x_grid[right - 2 : right + 2]
        ys = y_grid[right - 2 : right + 2]
        value = 0.0
        for j in range(4):
            basis = 1.0
            for k in range(4):
                if j != k:
                    basis *= (query - xs[k]) / (xs[j] - xs[k])
            value += ys[j] * basis
        values.append(value)
    return np.asarray(values, dtype=float)


def optional_background_check(
    background: Path,
    z: np.ndarray,
    e: np.ndarray,
    h: np.ndarray,
    covariance: np.ndarray,
) -> dict:
    if not background.exists():
        return {
            "performed": False,
            "reason": f"background not present at {background}",
        }
    if sha256(background) != BACKGROUND_SHA256:
        raise SystemExit("frozen background hash gate failed")
    try:
        from scipy.interpolate import PchipInterpolator
        import scipy
    except ImportError as exc:
        raise SystemExit("SciPy is required when --background is checked") from exc
    bg = np.genfromtxt(background, delimiter=",", names=True)
    n_data = -np.log1p(z)
    reconstructed = (
        np.asarray(PchipInterpolator(bg["N"], bg["H"])(n_data), dtype=float)
        / float(bg["H"][-1])
    )
    difference = np.abs(reconstructed - e)
    if float(np.max(difference)) > 2e-15:
        raise SystemExit("frozen E(z) snapshot reconstruction gate failed")
    normalised_h = np.asarray(bg["H"], dtype=float) / float(bg["H"][-1])
    lagrange = four_node_lagrange(bg["N"], normalised_h, n_data)
    linear = np.interp(n_data, bg["N"], normalised_h)
    lagrange_fit = fit_scale(lagrange, h, covariance)
    linear_fit = fit_scale(linear, h, covariance)
    return {
        "performed": True,
        "background": portable_path(background),
        "background_sha256": sha256(background),
        "scipy": scipy.__version__,
        "max_abs_E_difference": float(np.max(difference)),
        "independent_four_node_lagrange": {
            "max_abs_E_difference_from_PCHIP": float(
                np.max(np.abs(lagrange - reconstructed))
            ),
            "fit": lagrange_fit,
            "delta_H0_from_PCHIP": (
                lagrange_fit["H0_best"] - EXPECTED["H0"]
            ),
            "delta_chi2_from_PCHIP": (
                lagrange_fit["chi2_min"] - EXPECTED["chi2"]
            ),
        },
        "linear_interpolation_sensitivity": {
            "max_abs_E_difference_from_PCHIP": float(
                np.max(np.abs(linear - reconstructed))
            ),
            "fit": linear_fit,
            "delta_H0_from_PCHIP": (
                linear_fit["H0_best"] - EXPECTED["H0"]
            ),
            "delta_chi2_from_PCHIP": (
                linear_fit["chi2_min"] - EXPECTED["chi2"]
            ),
        },
    }


def optional_official_repo_check(repository: Path | None) -> dict:
    if repository is None:
        return {
            "performed": False,
            "reason": "no --official-repo path supplied",
        }
    if not repository.exists():
        return {
            "performed": False,
            "reason": f"official repository not present at {repository}",
        }
    hz = repository / "data/HzTable_MM_BC03.dat"
    model = repository / "data/data_MM20.dat"
    notebook = repository / "examples/CC_covariance.ipynb"
    observed = {
        "HzTable_MM_BC03.dat": sha256(hz),
        "data_MM20.dat": sha256(model),
        "CC_covariance.ipynb": sha256(notebook),
    }
    expected = {
        "HzTable_MM_BC03.dat": OFFICIAL_HZ_SHA256,
        "data_MM20.dat": OFFICIAL_MODEL_SHA256,
        "CC_covariance.ipynb": OFFICIAL_NOTEBOOK_SHA256,
    }
    if observed != expected:
        raise SystemExit("official repository source-hash gate failed")
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if commit != OFFICIAL_COMMIT:
        raise SystemExit("official repository commit gate failed")
    return {
        "performed": True,
        "repository_path": str(repository),
        "commit": commit,
        "source_sha256": observed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", type=Path, default=DEFAULT_BACKGROUND)
    parser.add_argument(
        "--official-repo",
        type=Path,
        default=None,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        hz_data = resolve_external_input(
            ROOT, HZ_DATA_LOGICAL, HZ_DATA_REPACKAGED_SHA256
        )
        model_data = resolve_external_input(
            ROOT, MODEL_DATA_LOGICAL, MODEL_DATA_REPACKAGED_SHA256
        )
    except ExternalInputError as exc:
        raise SystemExit(str(exc)) from exc

    (
        z,
        h,
        err,
        imf_fraction,
        slib_fraction,
        sps_fraction,
        spsooo_fraction,
        e,
    ) = load_inputs(hz_data, model_data)
    covariance, imf_load, spsooo_load = build_covariance(
        h, err, imf_fraction, spsooo_fraction
    )

    eigenvalues = np.linalg.eigvalsh(covariance)
    if float(eigenvalues[0]) <= 0:
        raise SystemExit("positive-definite covariance gate failed")

    primary = fit_scale(e, h, covariance)

    # Independent linear-algebra path 1: Cholesky solves.
    chol = np.linalg.cholesky(covariance)
    whitened_e = np.linalg.solve(chol, e)
    whitened_h = np.linalg.solve(chol, h)
    h0_cholesky = float(
        (whitened_e @ whitened_h) / (whitened_e @ whitened_e)
    )
    sigma_cholesky = float((whitened_e @ whitened_e) ** -0.5)
    residual_cholesky = whitened_h - h0_cholesky * whitened_e
    chi2_cholesky = float(residual_cholesky @ residual_cholesky)

    # Independent linear-algebra path 2: rank-two Woodbury identity.
    covariance_inverse_woodbury = woodbury_inverse(
        err, imf_load, spsooo_load
    )
    denominator_woodbury = float(e @ covariance_inverse_woodbury @ e)
    h0_woodbury = float(
        (e @ covariance_inverse_woodbury @ h) / denominator_woodbury
    )
    sigma_woodbury = float(denominator_woodbury ** -0.5)
    residual_woodbury = h - h0_woodbury * e
    chi2_woodbury = float(
        residual_woodbury
        @ covariance_inverse_woodbury
        @ residual_woodbury
    )

    crosscheck = {
        "cholesky": {
            "H0_best": h0_cholesky,
            "H0_sigma": sigma_cholesky,
            "chi2": chi2_cholesky,
        },
        "woodbury": {
            "H0_best": h0_woodbury,
            "H0_sigma": sigma_woodbury,
            "chi2": chi2_woodbury,
            "max_abs_inverse_difference": float(
                np.max(
                    np.abs(
                        covariance_inverse_woodbury
                        - np.linalg.inv(covariance)
                    )
                )
            ),
        },
    }
    if max(
        abs(primary["H0_best"] - h0_cholesky),
        abs(primary["H0_best"] - h0_woodbury),
        abs(primary["H0_sigma_formal_covariance"] - sigma_cholesky),
        abs(primary["H0_sigma_formal_covariance"] - sigma_woodbury),
        abs(primary["chi2_min"] - chi2_cholesky),
        abs(primary["chi2_min"] - chi2_woodbury),
    ) > 2e-12:
        raise SystemExit("independent linear-algebra cross-check failed")

    for key, actual in (
        ("H0", primary["H0_best"]),
        ("sigma", primary["H0_sigma_formal_covariance"]),
        ("chi2", primary["chi2_min"]),
    ):
        if abs(actual - EXPECTED[key]) > 2e-12:
            raise SystemExit(f"provisional-value gate failed for {key}")

    age = TAU_TWO_SLOPE * HUBBLE_TIME_AT_H0_1_GYR / primary["H0_best"]
    age_sigma = (
        age
        * primary["H0_sigma_formal_covariance"]
        / primary["H0_best"]
    )
    if (
        abs(age - EXPECTED["age"]) > 2e-12
        or abs(age_sigma - EXPECTED["age_sigma"]) > 2e-12
    ):
        raise SystemExit("conditional-age gate failed")

    diagonal_fit = fit_scale(e, h, np.diag(err**2))

    # The official components notebook also displays two more conservative
    # rank-one model-covariance choices.  They are not the requested primary
    # prescription, but quantify prescription sensitivity.
    slib_load = h * slib_fraction
    sps_load = h * sps_fraction
    conservative_covariance = covariance + np.outer(slib_load, slib_load)
    extra_conservative_covariance = (
        np.diag(err**2)
        + np.outer(imf_load, imf_load)
        + np.outer(slib_load, slib_load)
        + np.outer(sps_load, sps_load)
    )
    covariance_variant_fits = {
        "suggested_primary": primary,
        "conservative_spsooo_plus_slib": fit_scale(
            e, h, conservative_covariance
        ),
        "extra_conservative_sps_plus_slib": fit_scale(
            e, h, extra_conservative_covariance
        ),
    }
    for variant in covariance_variant_fits.values():
        variant_age = (
            TAU_TWO_SLOPE
            * HUBBLE_TIME_AT_H0_1_GYR
            / variant["H0_best"]
        )
        variant["conditional_age_Gyr"] = variant_age
        variant["formal_H0_only_age_sigma_Gyr"] = (
            variant_age
            * variant["H0_sigma_formal_covariance"]
            / variant["H0_best"]
        )

    omega_m = 0.29996713424139704
    omega_r = 9.998904474713234e-05
    omega_late = 0.6999328767138558
    e_control = np.sqrt(
        omega_r * (1 + z) ** 4
        + omega_m * (1 + z) ** 3
        + omega_late
    ) / np.sqrt(omega_r + omega_m + omega_late)
    control = fit_scale(e_control, h, covariance)

    correlation = covariance / np.sqrt(
        np.outer(np.diag(covariance), np.diag(covariance))
    )
    off_diagonal = correlation[~np.eye(len(z), dtype=bool)]

    payload = {
        "schema": "ECT-R103-official-CCcovariance-BC03-subset-v1",
        "date": "2026-07-19",
        "status": (
            "Level-C covariance-aware 15-point BC03 subset calibration; "
            "not a full/latest 32-point CC likelihood"
        ),
        "official_source": {
            "repository": OFFICIAL_REPOSITORY,
            "commit": OFFICIAL_COMMIT,
            "commit_date": "2021-03-19T12:29:06+01:00",
            "HzTable_MM_BC03_original_sha256": OFFICIAL_HZ_SHA256,
            "data_MM20_original_sha256": OFFICIAL_MODEL_SHA256,
            "CC_covariance_notebook_sha256": OFFICIAL_NOTEBOOK_SHA256,
            "covariance_formula": (
                "diag(errHz^2) + outer(Hz*imf_fraction) "
                "+ outer(Hz*spsooo_fraction)"
            ),
        },
        "local_inputs": {
            Path(HZ_DATA_LOGICAL).name: sha256(hz_data),
            Path(MODEL_DATA_LOGICAL).name: sha256(model_data),
            E_SNAPSHOT.name: sha256(E_SNAPSHOT),
        },
        "official_repository_check": optional_official_repo_check(
            args.official_repo
        ),
        "background_check": optional_background_check(
            args.background, z, e, h, covariance
        ),
        "covariance_diagnostics": {
            "dimension": int(len(z)),
            "minimum_eigenvalue": float(eigenvalues[0]),
            "maximum_eigenvalue": float(eigenvalues[-1]),
            "condition_number_2": float(np.linalg.cond(covariance)),
            "log_determinant": float(np.linalg.slogdet(covariance)[1]),
            "off_diagonal_correlation_min": float(np.min(off_diagonal)),
            "off_diagonal_correlation_max": float(np.max(off_diagonal)),
            "off_diagonal_abs_correlation_median": float(
                np.median(np.abs(off_diagonal))
            ),
        },
        "primary_covariance_fit": primary,
        "conditional_age": {
            "tau_two_slope": TAU_TWO_SLOPE,
            "age_Gyr": age,
            "formal_covariance_sigma_Gyr_from_H0_only": age_sigma,
            "interpretation": (
                "conditional selected-history age after the same H0 "
                "calibration; not a universal P1--P6 prediction"
            ),
        },
        "independent_linear_algebra_crosschecks": crosscheck,
        "diagonal_same_15_point_subset": diagonal_fit,
        "official_components_notebook_covariance_variant_sensitivity": (
            covariance_variant_fits
        ),
        "same_present_fraction_flat_control": {
            "omega_m": omega_m,
            "omega_r": omega_r,
            "omega_late": omega_late,
            "fit": control,
            "delta_H0_ECT_minus_control": (
                primary["H0_best"] - control["H0_best"]
            ),
            "delta_chi2_ECT_minus_control": (
                primary["chi2_min"] - control["chi2_min"]
            ),
        },
        "interpretation": {
            "established": (
                "The official suggested covariance formula and the analytic "
                "one-scale profile are reproduced."
            ),
            "allowed": (
                "May serve as the main covariance-aware approximate ECT "
                "chronometer calibration if labelled as the official "
                "15-point BC03 subset."
            ),
            "not_allowed": (
                "Must not be called a full/latest 32-point likelihood, an "
                "ECT prediction of H0, an ECT age prediction, a Hubble-"
                "tension resolution, or ECT-specific discrimination."
            ),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }

    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
