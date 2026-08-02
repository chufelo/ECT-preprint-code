#!/usr/bin/env python3
"""Strict verification for the conditional Level-C HRC publication package.

The verifier is intentionally independent of the plotting entry points.  It
checks manifest ownership and hashes, the HRC-only projection schema, analytic
HRC-0 inversion, an independent monotone HRC-3 inversion, signed-gas handling,
UDG inverse residuals, and the frozen per-galaxy regression sentinels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path, PurePosixPath

from external_inputs import (
    declared_external_input_hashes,
    resolve_external_input,
)


LATEX_ROOT = Path(__file__).resolve().parents[2]
DATA = LATEX_ROOT / "data" / "hrc_r97"
FIGURES = LATEX_ROOT / "figures" / "hrc"
OUT = DATA / "R97_HRC_RELEASE_VERIFICATION.json"
EXTERNAL_INPUT_HASHES = declared_external_input_hashes(LATEX_ROOT)

ONLY_STEMS = {
    "R97_HRC_RESPONSE_AND_REGIMES",
    "R97_HRC_ROTATION_EXAMPLES",
    "R97_HRC_RAR_DIAGNOSTIC",
}
COMPLETION_STEMS = {
    "R97_HRC_BTFR_AND_SCALE",
    "R97_HRC_ML_SENSITIVITY",
    "R97_HRC_ROTATION_GALLERY",
    "R97_HRC_MILKY_WAY",
    "R97_HRC_UDG_STRESS",
    "R97_HRC_RESIDUAL_STRESS",
}
POINT_COLUMNS = [
    "seed", "fold", "galaxy", "source_row_index", "radius_kpc",
    "vobs_km_s", "error_km_s", "gN_si", "v_HRC0", "chi2_HRC0",
    "v_HRC3", "chi2_HRC3",
]
REGIME_COLUMNS = [
    "bin_kind", "bin", "prediction_rows", "unique_physical_points",
    "mean_yN_ref", "chi2_HRC0_per_one_dataset", "chi2_HRC0_per_point",
    "chi2_HRC3_per_one_dataset", "chi2_HRC3_per_point",
]
COMMON_ML_COLUMNS = [
    "seed", "fold", "model", "train_galaxies", "test_galaxies",
    "train_points", "test_points", "invalid_train_points",
    "invalid_test_points", "aM_si", "common_disk_ML",
    "train_chi2", "test_chi2", "optimizer_success",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def safe_owned_path(rel: str) -> Path:
    posix = PurePosixPath(rel)
    if posix.is_absolute() or ".." in posix.parts:
        raise AssertionError(f"unsafe manifest path: {rel}")
    if not posix.parts or posix.parts[0] in {"LaTex", "research", ".workspace"}:
        raise AssertionError(f"non-repository-relative manifest path: {rel}")
    if rel in EXTERNAL_INPUT_HASHES:
        return resolve_external_input(
            LATEX_ROOT, rel, EXTERNAL_INPUT_HASHES[rel]
        )
    path = (LATEX_ROOT / Path(*posix.parts)).resolve()
    root = LATEX_ROOT.resolve()
    if root not in path.parents:
        raise AssertionError(f"manifest path escapes repository: {rel}")
    if not path.is_file():
        raise AssertionError(f"manifest path is missing or not regular: {rel}")
    return path


def verify_hash_map(mapping: dict[str, str], label: str) -> None:
    for rel, expected in sorted(mapping.items()):
        path = safe_owned_path(rel)
        actual = sha256(path)
        if actual != expected:
            raise AssertionError(f"{label} hash mismatch: {rel}: {actual} != {expected}")


def expected_outputs(stems: set[str]) -> set[str]:
    return {
        f"figures/hrc/{stem}.{suffix}"
        for stem in stems
        for suffix in ("pdf", "png")
    }


def mu0_x(x: float) -> float:
    return x / math.hypot(1.0, x)


def mu3_x(x: float) -> float:
    y = x * x
    return mu0_x(x) * (1.0 - (4.0 / 3.0) * y / ((1.0 + y) ** 2))


def hrc0_inverse(y: float) -> float:
    # Stable positive root of z^2-y^2 z-y^2=0 with z=x^2.
    z = 0.5 * y * (y + math.hypot(y, 2.0))
    return math.sqrt(z)


def hrc3_inverse_bisection(y: float) -> float:
    lo = 0.0
    hi = max(1.0, 2.0 * y + 2.0)
    while hi * mu3_x(hi) < y:
        hi *= 2.0
    for _ in range(220):
        mid = 0.5 * (lo + hi)
        if mid * mu3_x(mid) < y:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def log_grid(lo: float, hi: float, count: int) -> list[float]:
    a = math.log10(lo)
    b = math.log10(hi)
    return [10.0 ** (a + (b - a) * i / (count - 1)) for i in range(count)]


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    logical_path = f"data/hrc_r97/{name}"
    path = (
        resolve_external_input(
            LATEX_ROOT, logical_path, EXTERNAL_INPUT_HASHES[logical_path]
        )
        if logical_path in EXTERNAL_INPUT_HASHES
        else DATA / name
    )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def main() -> None:
    only = load_json("R97_HRC_ONLY_FIGURE_MANIFEST.json")
    completion = load_json("R97_HRC_COMPLETION_MANIFEST.json")
    if set(only["outputs"]) != expected_outputs(ONLY_STEMS):
        raise AssertionError("HRC-only manifest owns a non-exact figure set")
    if set(completion["outputs"]) != expected_outputs(COMPLETION_STEMS):
        raise AssertionError("completion manifest owns a non-exact figure set")
    if set(only["outputs"]) & set(completion["outputs"]):
        raise AssertionError("figure ownership overlaps")
    verify_hash_map(only["inputs"], "HRC-only input")
    verify_hash_map(only["outputs"], "HRC-only output")
    verify_hash_map(completion["inputs"], "completion input")
    verify_hash_map(completion["outputs"], "completion output")

    point_header, point_rows = read_csv("R97_HRC_SOURCE_POINTS.csv")
    regime_header, regime_rows = read_csv("R97_HRC_SOURCE_REGIMES.csv")
    if point_header != POINT_COLUMNS or len(point_rows) != 16715:
        raise AssertionError("HRC source-point projection schema/count drift")
    if regime_header != REGIME_COLUMNS or len(regime_rows) != 10:
        raise AssertionError("HRC source-regime projection schema/count drift")

    common_header, common_rows = read_csv("R97_HRC_COMMON_ML_FOLDS.csv")
    if common_header != COMMON_ML_COLUMNS or len(common_rows) != 50:
        raise AssertionError("HRC common-M/L fold registry schema/count drift")
    expected_grid = {
        (str(seed), str(fold), model)
        for seed in (75, 176, 277, 378, 479)
        for fold in range(5)
        for model in ("HRC0", "HRC3")
    }
    actual_grid = {(r["seed"], r["fold"], r["model"]) for r in common_rows}
    if actual_grid != expected_grid:
        raise AssertionError("HRC common-M/L seed/fold/model grid drift")
    common_totals: dict[str, dict[str, float]] = {
        model: {} for model in ("HRC0", "HRC3")
    }
    for model in common_totals:
        for seed in (75, 176, 277, 378, 479):
            rows = [
                r for r in common_rows
                if r["model"] == model and r["seed"] == str(seed)
            ]
            if any(r["optimizer_success"] != "True" for r in rows):
                raise AssertionError("HRC common-M/L optimiser failure")
            if any(int(r["train_galaxies"]) + int(r["test_galaxies"]) != 165 for r in rows):
                raise AssertionError("HRC common-M/L galaxy-count drift")
            if sum(int(r["test_points"]) for r in rows) != 3342:
                raise AssertionError("HRC common-M/L test-point count drift")
            if sum(int(r["train_points"]) for r in rows) != 4 * 3342:
                raise AssertionError("HRC common-M/L train-point count drift")
            if sum(int(r["invalid_test_points"]) for r in rows) != 3:
                raise AssertionError("HRC common-M/L validity-mask drift")
            if sum(int(r["invalid_train_points"]) for r in rows) != 4 * 3:
                raise AssertionError("HRC common-M/L training-mask drift")
            if any(not (0.3 <= float(r["common_disk_ML"]) <= 1.0) for r in rows):
                raise AssertionError("HRC common-M/L bound violation")
            numeric = [
                float(r[key])
                for r in rows
                for key in ("aM_si", "common_disk_ML", "train_chi2", "test_chi2")
            ]
            if not all(math.isfinite(value) for value in numeric):
                raise AssertionError("HRC common-M/L non-finite output")
            common_totals[model][str(seed)] = float(
                sum(float(r["test_chi2"]) for r in rows)
            )
    common_means = {
        model: sum(by_seed.values()) / len(by_seed)
        for model, by_seed in common_totals.items()
    }
    frozen_common_means = {
        "HRC0": 109439.94619430431,
        "HRC3": 103763.46201964984,
    }
    if any(
        abs(common_means[model] - expected) > 2.0e-3
        for model, expected in frozen_common_means.items()
    ):
        raise AssertionError("HRC-only common-M/L rerun no longer reproduces frozen means")
    completion_results = load_json("R97_HRC_COMPLETION_RESULTS.json")
    recorded_common = completion_results["honest_common_ML_transfer_CV"]["mean_test_chi2"]
    if any(
        not math.isclose(common_means[model], float(recorded_common[model]),
                         rel_tol=0.0, abs_tol=2.0e-9)
        for model in common_means
    ):
        raise AssertionError("common-M/L CSV and completion JSON disagree")
    manuscript = (LATEX_ROOT / "ECT_preprint.tex").read_text(encoding="utf-8")
    if any(f"{common_means[model]:.2f}" not in manuscript for model in common_means):
        raise AssertionError("common-M/L manuscript table is not tied to rerun output")

    actual_figure_files = {
        str(path.relative_to(LATEX_ROOT))
        for path in FIGURES.iterdir()
        if path.is_file()
    }
    expected_figure_files = expected_outputs(ONLY_STEMS | COMPLETION_STEMS)
    if actual_figure_files != expected_figure_files:
        raise AssertionError(
            "figures/hrc contains missing or unowned files: "
            f"missing={sorted(expected_figure_files - actual_figure_files)}, "
            f"extra={sorted(actual_figure_files - expected_figure_files)}"
        )

    forbidden = (
        "x/(1+x)", "x / (1 + x)", "mu_simple", "v_simple",
        "adopted level-c functional g", "level-c galactic functional",
        "adopted level-c galactic", "independently adopted level-c",
        "practical level-c phenomenological galactic",
        "adopted low-acceleration branch",
    )
    scan_paths = [LATEX_ROOT / "ECT_preprint.tex", LATEX_ROOT / "README.md"]
    scan_paths += sorted((LATEX_ROOT / "scripts" / "hrc").glob("*"))
    scan_paths += sorted(DATA.glob("*"))
    old_hits: list[str] = []
    for path in scan_paths:
        if not path.is_file() or path == OUT or path.name == "verify_hrc_release.py":
            continue
        body = path.read_text(encoding="utf-8", errors="ignore").lower()
        normalised_body = " ".join(body.split())
        for token in forbidden:
            if token.lower() in body or " ".join(token.lower().split()) in normalised_body:
                old_hits.append(f"{path.relative_to(LATEX_ROOT)}:{token}")
    if old_hits:
        raise AssertionError("superseded response law remains active: " + ", ".join(old_hits))

    max_h0_residual = 0.0
    for y in log_grid(1.0e-14, 1.0e14, 50001):
        x = hrc0_inverse(y)
        residual = abs(x * mu0_x(x) - y) / y
        max_h0_residual = max(max_h0_residual, residual)
    if max_h0_residual > 2.0e-14:
        raise AssertionError(f"HRC-0 analytic inversion residual {max_h0_residual}")

    max_h3_residual = 0.0
    previous_x = -1.0
    for y in log_grid(1.0e-14, 1.0e14, 2001):
        x = hrc3_inverse_bisection(y)
        if not math.isfinite(x) or x <= previous_x:
            raise AssertionError("HRC-3 independent inverse is not positive/monotone")
        previous_x = x
        residual = abs(x * mu3_x(x) - y) / y
        max_h3_residual = max(max_h3_residual, residual)
    if max_h3_residual > 2.0e-13:
        raise AssertionError(f"HRC-3 independent inversion residual {max_h3_residual}")

    signed_gas = [math.copysign(v * v, v) if v else 0.0 for v in (-3.0, 0.0, 4.0)]
    if signed_gas != [-9.0, 0.0, 16.0]:
        raise AssertionError("signed-gas convention failed")
    completion_source = (LATEX_ROOT / "scripts/hrc/make_r97_hrc_completion_figures.py").read_text(
        encoding="utf-8"
    )
    if "np.sign(vgas) * vgas**2" not in completion_source:
        raise AssertionError("publication fitter lost signed-gas implementation")

    fit_header, fits = read_csv("R97_HRC_PER_GALAXY_FITS.csv")
    if len(fits) != 165 or "success_HRC3_freeML" not in fit_header:
        raise AssertionError("per-galaxy HRC fit registry drift")
    success_columns = (
        "success_HRC0", "success_HRC0_freeML", "success_HRC3", "success_HRC3_freeML"
    )
    if any(row[key] != "True" for row in fits for key in success_columns):
        raise AssertionError("at least one frozen HRC fit is unsuccessful")
    by_name = {row["galaxy"]: row for row in fits}
    sentinels = {
        ("DDO064", "chi2_HRC0_freeML"): 3.5164308031237983,
        ("DDO064", "aM_HRC0_freeML_over_match"): 1.3386984277354894,
        ("DDO064", "ups_disk_HRC0_freeML"): 0.3323875468509858,
        ("NGC3972", "chi2_HRC3_freeML"): 10.81035357422795,
    }
    for (galaxy, key), expected in sentinels.items():
        actual = float(by_name[galaxy][key])
        if not math.isclose(actual, expected, rel_tol=2.0e-12, abs_tol=2.0e-12):
            raise AssertionError(f"fit sentinel drift: {galaxy}/{key}: {actual}")

    udg = load_json("R97_HRC_UDG_VERIFICATION.json")
    udg_hashes = {
        "R97_HRC_UDG_DIAGNOSTIC.csv": udg["csv_sha256"],
        "R97_HRC_UDG_INTERVALS.csv": udg["interval_csv_sha256"],
        "R97_HRC_UDG_DIAGNOSTIC.json": udg["json_sha256"],
    }
    for name, expected in udg_hashes.items():
        if sha256(DATA / name) != expected:
            raise AssertionError(f"UDG hash drift: {name}")
    if float(udg["max_inverse_residual"]) > 5.0e-14:
        raise AssertionError("UDG inverse residual exceeds tolerance")

    try:
        import numpy as np
        import scipy
        import matplotlib
        environment = {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        }
    except ImportError as exc:
        raise AssertionError(f"declared publication environment incomplete: {exc}") from exc

    scripts = LATEX_ROOT / "scripts" / "hrc"
    script_hashes = {
        str(path.relative_to(LATEX_ROOT)): sha256(path)
        for path in sorted(scripts.glob("*.py"))
    }
    result = {
        "pass": True,
        "status": "HRC_LEVEL_C_PUBLICATION_STATIC_INTEGRITY_PASS",
        "scientific_scope": "LEVEL_C_CONDITIONAL_PUBLICATION_CALCULATION",
        "note": "Generator rerun reproducibility is a separate clean-copy release gate.",
        "environment": environment,
        "publication_script_sha256": script_hashes,
        "manifest_path_and_hash_gate": True,
        "external_input_contract": {
            "environment_variable": "ECT_EXTERNAL_INPUT_ROOT",
            "declared_inputs": len(EXTERNAL_INPUT_HASHES),
            "hashes_verified": True,
            "redistributed_by_repository": False,
        },
        "exact_figure_ownership": {
            "only": 6, "completion": 12, "total": 18,
            "directory_set_equality": True,
        },
        "source_projection": {"point_rows": len(point_rows), "regime_rows": len(regime_rows)},
        "common_ML_transfer_CV": {
            "fold_rows": len(common_rows),
            "test_points_per_seed": 3342,
            "mean_test_chi2": common_means,
            "max_abs_difference_from_frozen_R75": max(
                abs(common_means[model] - frozen_common_means[model])
                for model in common_means
            ),
        },
        "old_response_law_hits": old_hits,
        "max_relative_residual": {"HRC0_analytic": max_h0_residual, "HRC3_bisection": max_h3_residual},
        "signed_gas_gate": True,
        "fit_rows": len(fits),
        "fit_success_flags": 4 * len(fits),
        "UDG_max_inverse_residual": float(udg["max_inverse_residual"]),
        "scope_guards": {
            "full_disk_PDE": False,
            "hierarchical_likelihood": False,
            "metric_lensing_completion": False,
            "P1_P6_owner_derived": False,
        },
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
