#!/usr/bin/env python3
"""Generate the conditional Level-C HRC galactic publication calculations.

Outputs are Level-C algebraic diagnostics.  The script does not evaluate,
plot, or compare the superseded galactic response law.  SPARC-origin inputs
are external and hash pinned; they are not redistributed by this repository.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from external_inputs import resolve_external_input


LATEX_ROOT = Path(__file__).resolve().parents[2]
ROOT = LATEX_ROOT
HERE = LATEX_ROOT / "data" / "hrc_r97"
DATA_REL = "data/MassModels_Lelli2016c.mrt"
POINTS_REL = "data/hrc_r97/R97_HRC_SOURCE_POINTS.csv"
DATA = resolve_external_input(
    LATEX_ROOT,
    DATA_REL,
    "7d027e515441c6b4ebbf6aadee0327e6ad81156c4e8b151af2f6d62cb44c3962",
)
POINTS = resolve_external_input(
    LATEX_ROOT,
    POINTS_REL,
    "5f9b884e611e61189a97cc6c8fdb01e430bfc7bf7cef3faf05be2b0d2b8a2e80",
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import differential_evolution, minimize, minimize_scalar
from scipy.special import i0, i1, k0, k1

UDG = HERE / "R97_HRC_UDG_DIAGNOSTIC.csv"
OUT = LATEX_ROOT / "figures" / "hrc"
OUT.mkdir(parents=True, exist_ok=True)
OWNED_STEMS = (
    "R97_HRC_BTFR_AND_SCALE",
    "R97_HRC_ML_SENSITIVITY",
    "R97_HRC_ROTATION_GALLERY",
    "R97_HRC_MILKY_WAY",
    "R97_HRC_UDG_STRESS",
    "R97_HRC_RESIDUAL_STRESS",
)

ACC_CONV = 1.0e6 / 3.0856775814913673e19
KPC_M = 3.0856775814913673e19
MPC_M = 3.0856775814913673e22
C_SI = 299_792_458.0
G_SI = 6.67430e-11
MSUN = 1.98847e30
H0 = 70.0
A_MATCH = C_SI * H0 * 1000.0 / MPC_M / (2.0 * math.pi)
A_HRC3 = 4.0 / 3.0
SEEDS = (75, 176, 277, 378, 479)
K_FOLDS = 5
COMMON_ML_BOUNDS = (0.3, 1.0)

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
BLACK = "#222222"
GREY = "#777777"
PURPLE = "#CC79A7"


def apply_publication_readability_floor(
    fig: plt.Figure,
    *,
    size: tuple[float, float],
    floor: float = 10.5,
    title_floor: float = 12.0,
    legend_floor: float = 10.2,
) -> None:
    """Preserve the accepted R127 readability floor in direct replays."""

    fig.set_size_inches(*size, forward=True)
    for text_item in fig.findobj(match=matplotlib.text.Text):
        if not str(text_item.get_text()).strip():
            continue
        target = title_floor if text_item in fig.texts else floor
        text_item.set_fontsize(max(float(text_item.get_fontsize()), target))
    for ax in fig.axes:
        ax.tick_params(axis="both", which="both", labelsize=floor)
        ax.title.set_fontsize(max(float(ax.title.get_fontsize()), title_floor))
        ax.xaxis.label.set_fontsize(max(float(ax.xaxis.label.get_fontsize()), floor))
        ax.yaxis.label.set_fontsize(max(float(ax.yaxis.label.get_fontsize()), floor))
    for legend in list(fig.legends) + [ax.get_legend() for ax in fig.axes]:
        if legend is None:
            continue
        for text_item in legend.get_texts():
            text_item.set_fontsize(max(float(text_item.get_fontsize()), legend_floor))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mu0_x(x):
    x = np.asarray(x, dtype=float)
    return x / np.sqrt(1.0 + x * x)


def mu3_x(x):
    x = np.asarray(x, dtype=float)
    y = x * x
    return mu0_x(x) * (1.0 - A_HRC3 * y / (1.0 + y) ** 2)


def invert_hrc3(y):
    y = np.maximum(np.asarray(y, dtype=float), 0.0)
    z = 0.5 * (y * y + y * np.sqrt(y * y + 4.0))
    z = np.maximum(z, 1.0e-30)
    for _ in range(60):
        one = 1.0 + z
        base = z / np.sqrt(one)
        q = 1.0 - A_HRC3 * z / one**2
        derivative = (1.0 + 0.5 * z) / one**1.5 * q
        derivative += base * (-A_HRC3) * (1.0 - z) / one**3
        trial = z - (base * q - y) / np.maximum(derivative, 1.0e-30)
        trial = np.where((trial > 0.0) & np.isfinite(trial), trial, 0.5 * z)
        if float(np.max(np.abs(trial - z) / np.maximum(1.0, z))) < 2.0e-14:
            z = trial
            break
        z = trial
    return z


def g_model(gn_si, a_m, model):
    gn = np.maximum(np.asarray(gn_si, dtype=float), 0.0)
    y = gn / a_m
    if model == "HRC0":
        z = 0.5 * (y * y + y * np.sqrt(y * y + 4.0))
    elif model == "HRC3":
        z = invert_hrc3(y)
    else:
        raise ValueError(model)
    return a_m * np.sqrt(np.maximum(z, 0.0))


def load_galaxies():
    raw: dict[str, list[list[float]]] = defaultdict(list)
    with DATA.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            fields = line.split()
            if len(fields) < 8 or line.lstrip().startswith("#"):
                continue
            try:
                values = [float(fields[i]) for i in (2, 3, 4, 5, 6, 7)]
            except ValueError:
                continue
            raw[fields[0]].append(values)
    out = {}
    for name, rows in sorted(raw.items()):
        a = np.asarray(rows, dtype=float)
        if len(a) < 6:
            continue
        a = a[np.argsort(a[:, 0])]
        out[name] = a
    return out


def arrays(a, ups_disk=0.5, ups_bul=0.7):
    r, vobs, err, vgas, vdisk, vbul = a.T
    vbar2 = (
        np.sign(vgas) * vgas**2
        + ups_disk * vdisk**2
        + ups_bul * np.maximum(np.sign(vbul) * vbul**2, 0.0)
    )
    valid = vbar2 > 0.0
    r = r[valid]
    return (
        r,
        vobs[valid],
        np.maximum(err[valid], 2.0),
        vbar2[valid] / r * ACC_CONV,
        vbar2[valid],
    )


def arrays_fixed_validity(a, ups_disk, validity_ups=0.3, ups_bul=0.7):
    """Return one galaxy with an M/L-independent validity mask.

    The mask is frozen at the lower common-M/L bound.  This prevents the
    optimiser from improving its objective by changing which data points are
    present and exactly matches the declared held-out transfer protocol.
    """
    r, vobs, err, vgas, vdisk, vbul = a.T
    gas_v2 = np.sign(vgas) * vgas**2
    bulge_v2 = vbul**2
    validity_vbar2 = (
        gas_v2 + validity_ups * vdisk**2 + ups_bul * bulge_v2
    )
    valid = validity_vbar2 > 0.0
    vbar2 = gas_v2 + float(ups_disk) * vdisk**2 + ups_bul * bulge_v2
    return (
        r[valid],
        vobs[valid],
        np.maximum(err[valid], 2.0),
        vbar2[valid] / np.maximum(r[valid], 1.0e-30) * ACC_CONV,
        int(np.sum(~valid)),
    )


def concatenate_fixed_validity(galaxies, names, ups_disk):
    chunks = [arrays_fixed_validity(galaxies[name], ups_disk) for name in names]
    return (
        np.concatenate([item[0] for item in chunks]),
        np.concatenate([item[1] for item in chunks]),
        np.concatenate([item[2] for item in chunks]),
        np.concatenate([item[3] for item in chunks]),
        int(sum(item[4] for item in chunks)),
    )


def chi2_array(arr, model, log_a):
    r, vobs, err, gn_si, _ = arr
    g = g_model(gn_si, 10.0**float(log_a), model)
    predicted = np.sqrt(np.maximum(g / ACC_CONV * r, 0.0))
    return float(np.sum(((vobs - predicted) / err) ** 2))


def fit_scale_array(arr, model):
    centre = math.log10(A_MATCH)
    result = minimize_scalar(
        lambda log_a: chi2_array(arr, model, float(log_a)),
        bounds=(centre - 2.0, centre + 2.0),
        method="bounded",
        options={"xatol": 1.0e-10},
    )
    return float(result.x), float(result.fun), bool(result.success)


def make_folds(names, seed):
    order = np.random.default_rng(seed).permutation(len(names))
    shuffled = np.asarray(names, dtype=object)[order]
    return [list(part) for part in np.array_split(shuffled, K_FOLDS)]


def fit_common_ml(galaxies, train_names, model):
    """Fit one scale and one disk M/L on training galaxies only."""
    lower, upper = COMMON_ML_BOUNDS
    start_arr = concatenate_fixed_validity(galaxies, train_names, 0.5)
    start_log, _, start_success = fit_scale_array(start_arr, model)

    def objective(params):
        log_a, ups_disk = params
        arr = concatenate_fixed_validity(galaxies, train_names, float(ups_disk))
        return chi2_array(arr, model, float(log_a))

    starts = [(start_log, value) for value in (lower, 0.5, 0.8)]
    bounds = ((math.log10(A_MATCH) - 2.0, math.log10(A_MATCH) + 2.0),
              COMMON_ML_BOUNDS)
    candidates = [
        minimize(
            objective,
            start,
            bounds=bounds,
            method="L-BFGS-B",
            options={"ftol": 1.0e-12, "gtol": 2.0e-7, "maxiter": 180},
        )
        for start in starts
    ]
    seed_fit = min(candidates, key=lambda item: float(item.fun))
    polish = minimize(
        objective,
        seed_fit.x,
        bounds=bounds,
        method="Powell",
        options={"xtol": 2.0e-8, "ftol": 2.0e-9, "maxiter": 260},
    )
    best = min([*candidates, polish], key=lambda item: float(item.fun))
    return {
        "aM_si": 10.0**float(best.x[0]),
        "disk_ML": float(best.x[1]),
        "train_chi2": float(best.fun),
        "train_points": len(start_arr[0]),
        "invalid_train_points": start_arr[4],
        "optimizer_success": bool(start_success and best.success),
    }


def honest_common_ml_cv():
    """Five-seed, whole-galaxy CV with one transferred common disk M/L.

    Only HRC-0 and HRC-3 are evaluated.  Each fold learns a common disk M/L
    and response scale from its training galaxies; both are then transferred
    unchanged to its held-out galaxies.  This is a deterministic algebraic
    diagnostic, not hierarchical stellar-population inference.
    """
    galaxies = load_galaxies()
    names = sorted(galaxies)
    by_model = {model: {} for model in ("HRC0", "HRC3")}
    for seed in SEEDS:
        folds = make_folds(names, seed)
        for model in by_model:
            fold_rows = []
            for fold_index, test_names in enumerate(folds):
                test_set = set(test_names)
                train_names = [name for name in names if name not in test_set]
                fitted = fit_common_ml(galaxies, train_names, model)
                test_arr = concatenate_fixed_validity(
                    galaxies, test_names, fitted["disk_ML"]
                )
                fold_rows.append({
                    "fold": fold_index,
                    "train_galaxies": len(train_names),
                    "test_galaxies": len(test_names),
                    "test_points": len(test_arr[0]),
                    "invalid_test_points": test_arr[4],
                    **fitted,
                    "test_chi2": chi2_array(
                        test_arr, model, math.log10(fitted["aM_si"])
                    ),
                })
            by_model[model][str(seed)] = {
                "folds": fold_rows,
                "test_chi2_total": float(sum(r["test_chi2"] for r in fold_rows)),
                "test_points_total": int(sum(r["test_points"] for r in fold_rows)),
                "aM_si_mean": float(np.mean([r["aM_si"] for r in fold_rows])),
                "disk_ML_mean": float(np.mean([r["disk_ML"] for r in fold_rows])),
                "disk_ML_std": float(np.std([r["disk_ML"] for r in fold_rows])),
                "all_optimizers_success": bool(
                    all(r["optimizer_success"] for r in fold_rows)
                ),
            }
    means = {
        model: float(np.mean([
            row["test_chi2_total"] for row in by_model[model].values()
        ]))
        for model in by_model
    }
    return {
        "protocol": (
            "five seeds; five whole-galaxy folds; signed gas; 2 km/s error "
            "floor; disk M/L in [0.3,1.0] fitted on training galaxies and "
            "transferred unchanged; bulge M/L=0.7"
        ),
        "models": by_model,
        "mean_test_chi2": means,
        "guards": {
            "only_HRC0_HRC3": True,
            "not_hierarchical_inference": True,
            "all_test_point_totals_3342": bool(all(
                row["test_points_total"] == 3342
                for model in by_model.values() for row in model.values()
            )),
            "all_optimizers_success": bool(all(
                row["all_optimizers_success"]
                for model in by_model.values() for row in model.values()
            )),
        },
    }


def write_common_ml_folds(common_cv):
    """Write the 50 HRC-only fold records used by the manuscript table."""
    fields = (
        "seed", "fold", "model", "train_galaxies", "test_galaxies",
        "train_points", "test_points", "invalid_train_points",
        "invalid_test_points", "aM_si", "common_disk_ML",
        "train_chi2", "test_chi2", "optimizer_success",
    )
    rows = []
    for model in ("HRC0", "HRC3"):
        for seed in sorted(common_cv["models"][model], key=int):
            for fold in common_cv["models"][model][seed]["folds"]:
                rows.append({
                    "seed": seed,
                    "fold": fold["fold"],
                    "model": model,
                    "train_galaxies": fold["train_galaxies"],
                    "test_galaxies": fold["test_galaxies"],
                    "train_points": fold["train_points"],
                    "test_points": fold["test_points"],
                    "invalid_train_points": fold["invalid_train_points"],
                    "invalid_test_points": fold["invalid_test_points"],
                    "aM_si": fold["aM_si"],
                    "common_disk_ML": fold["disk_ML"],
                    "train_chi2": fold["train_chi2"],
                    "test_chi2": fold["test_chi2"],
                    "optimizer_success": fold["optimizer_success"],
                })
    target = HERE / "R97_HRC_COMMON_ML_FOLDS.csv"
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "path": str(target.relative_to(ROOT)),
        "sha256": sha256(target),
        "rows": len(rows),
    }


def fit_scale(r, vobs, err, gn_si, model):
    def objective(log_a):
        g = g_model(gn_si, 10.0**log_a, model)
        v = np.sqrt(np.maximum(g / ACC_CONV * r, 0.0))
        return float(np.sum(((vobs - v) / err) ** 2))

    centre = math.log10(A_MATCH)
    result = minimize_scalar(
        objective,
        bounds=(centre - 2.0, centre + 2.0),
        method="bounded",
        options={"xatol": 1.0e-11},
    )
    return 10.0**float(result.x), float(result.fun), bool(result.success)


def fit_scale_and_ml(a, model):
    """Fit one HRC scale and one disk M/L; keep bulge M/L fixed at 0.7.

    This is a bounded two-parameter HRC nuisance test, not a hierarchical
    stellar-population likelihood.  Every row receives an independent global
    audit; a second global seed is required whenever the local and first
    global solutions disagree.
    """
    centre = math.log10(A_MATCH)

    def objective(params):
        log_a, ups_disk = params
        r, vobs, err, gn, _ = arrays(a, ups_disk=float(ups_disk))
        g = g_model(gn, 10.0**float(log_a), model)
        v = np.sqrt(np.maximum(g / ACC_CONV * r, 0.0))
        return float(np.sum(((vobs - v) / err) ** 2))

    best_value = math.inf
    best = np.asarray([centre, 0.5], dtype=float)
    for log_a in np.linspace(centre - 1.5, centre + 1.5, 13):
        for ups_disk in (0.15, 0.3, 0.5, 0.8, 1.2, 1.8):
            value = objective((log_a, ups_disk))
            if value < best_value:
                best_value = value
                best[:] = (log_a, ups_disk)
    result = minimize(
        objective,
        best,
        method="L-BFGS-B",
        bounds=((centre - 2.0, centre + 2.0), (0.1, 2.5)),
        options={"ftol": 1.0e-14, "gtol": 1.0e-10, "maxiter": 1000},
    )
    # L-BFGS-B can report a line-search failure or settle in a secondary
    # basin (DDO064/HRC0 is the frozen counterexample).  The global audit is
    # therefore run for every row rather than only after an optimiser flag.
    def global_run(seed):
        return differential_evolution(
            objective,
            bounds=((centre - 2.0, centre + 2.0), (0.1, 2.5)),
            seed=seed,
            popsize=12,
            maxiter=350,
            tol=1.0e-9,
            atol=1.0e-9,
            polish=True,
            updating="immediate",
            workers=1,
        )

    global_97 = global_run(97)
    local_global_gap = abs(float(result.fun) - float(global_97.fun))
    local_global_gap /= max(1.0, abs(float(global_97.fun)))
    candidates = [result, global_97]
    if (not result.success) or local_global_gap >= 1.0e-7:
        global_197 = global_run(197)
        global_297 = global_run(297)
        globals_ = [global_97, global_197, global_297]
        candidates.extend((global_197, global_297))
        best_global_value = min(float(item.fun) for item in globals_)
        near_best = [
            item for item in globals_
            if abs(float(item.fun) - best_global_value)
            / max(1.0, abs(best_global_value)) < 1.0e-7
        ]
        # At least two independently seeded global runs must agree at the
        # lowest objective.  This is robust to an individual seed entering a
        # secondary basin (the frozen NGC3972/HRC3 counterexample).
        verified = bool(len(near_best) >= 2 and
                        all(np.isfinite(item.fun) for item in near_best))
    else:
        verified = bool(np.isfinite(result.fun) and
                        np.isfinite(global_97.fun) and
                        local_global_gap < 1.0e-7)
    result = min(candidates, key=lambda item: float(item.fun))
    return (
        10.0**float(result.x[0]),
        float(result.x[1]),
        float(result.fun),
        verified,
    )


def save(fig, stem):
    frozen = datetime(2026, 7, 17, tzinfo=timezone.utc)
    fig.savefig(
        OUT / f"{stem}.pdf", dpi=220, bbox_inches="tight",
        metadata={"Creator": "ECT R97 HRC-only completion generator",
                  "CreationDate": frozen, "ModDate": frozen},
    )
    fig.savefig(
        OUT / f"{stem}.png", dpi=220, bbox_inches="tight",
        metadata={"Software": "ECT R97 HRC-only completion generator"},
    )
    plt.close(fig)


def fit_galaxies():
    rows = []
    for name, a in load_galaxies().items():
        r, vobs, err, gn, vbar2 = arrays(a)
        if len(r) < 6:
            continue
        rec = {"galaxy": name, "points": len(r)}
        for model in ("HRC0", "HRC3"):
            scale, chi2, success = fit_scale(r, vobs, err, gn, model)
            rec[f"aM_{model}_si"] = scale
            rec[f"aM_{model}_over_match"] = scale / A_MATCH
            rec[f"chi2_{model}"] = chi2
            rec[f"chi2red_{model}"] = chi2 / max(len(r) - 1, 1)
            rec[f"success_{model}"] = success
            free_scale, free_ml, free_chi2, free_success = fit_scale_and_ml(a, model)
            rec[f"aM_{model}_freeML_si"] = free_scale
            rec[f"aM_{model}_freeML_over_match"] = free_scale / A_MATCH
            rec[f"ups_disk_{model}_freeML"] = free_ml
            rec[f"chi2_{model}_freeML"] = free_chi2
            rec[f"chi2red_{model}_freeML"] = free_chi2 / max(len(r) - 2, 1)
            rec[f"success_{model}_freeML"] = free_success

        n_tail = max(3, int(math.ceil(0.25 * len(r))))
        idx = np.argsort(r)
        tail = idx[-n_tail:]
        weights = 1.0 / np.maximum(err[tail], 1.0) ** 2
        vflat = float(np.sum(weights * vobs[tail]) / np.sum(weights))
        rtail_m = float(np.median(r[tail])) * KPC_M
        gtail = float(np.median(gn[tail]))
        rec["Vflat_obs_km_s"] = vflat
        rec["Mbar_eff_Msun"] = rtail_m**2 * gtail / G_SI / MSUN
        rows.append(rec)

    fieldnames = list(rows[0])
    with (HERE / "R97_HRC_PER_GALAXY_FITS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def btfr_and_scale_figure(rows):
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5))
    good = [r for r in rows if r["Mbar_eff_Msun"] > 0 and r["Vflat_obs_km_s"] > 0]
    x = np.log10([r["Mbar_eff_Msun"] for r in good])
    y = np.log10([r["Vflat_obs_km_s"] for r in good])
    axes[0].scatter(x, y, s=14, facecolor="white", edgecolor=GREY,
                    linewidth=0.6, label="SPARC tail proxies")
    xx = np.linspace(min(x) - 0.2, max(x) + 0.2, 250)
    def line(a):
        return np.log10((G_SI * 10.0**xx * MSUN * a) ** 0.25 / 1000.0)
    fitted0 = float(np.median([r["aM_HRC0_si"] for r in rows]))
    fitted3 = float(np.median([r["aM_HRC3_si"] for r in rows]))
    axes[0].plot(xx, line(A_MATCH), color=BLACK, lw=1.9, ls=":",
                 label=r"matched $a_{M0}$")
    axes[0].plot(xx, line(fitted0), color=BLUE, lw=2.0, ls="--",
                 label="median HRC-0 scale")
    axes[0].plot(xx, line(fitted3), color=ORANGE, lw=2.0, ls="-",
                 label="median HRC-3 scale")
    axes[0].set_xlabel(r"$\log_{10}(M_{\rm bar,eff}/M_\odot)$")
    axes[0].set_ylabel(r"$\log_{10}(V_{\rm flat}/{\rm km\,s^{-1}})$")
    axes[0].set_title("Conditional BTFR and tail proxies")
    axes[0].grid(True, alpha=0.22)
    axes[0].legend(frameon=False, fontsize=7.5)

    ratios0 = np.asarray([r["aM_HRC0_over_match"] for r in rows])
    ratios3 = np.asarray([r["aM_HRC3_over_match"] for r in rows])
    bins = np.logspace(-2, 2, 31)
    axes[1].hist(ratios0, bins=bins, histtype="step", lw=2.0, ls="--",
                 color=BLUE, label="HRC-0")
    axes[1].hist(ratios3, bins=bins, histtype="stepfilled", alpha=0.22,
                 edgecolor=ORANGE, color=ORANGE, hatch="..", label="HRC-3")
    axes[1].axvline(1.0, color=BLACK, lw=1.4, ls=":", label="matched scale")
    axes[1].set_xscale("log")
    axes[1].set_xlabel(r"per-galaxy fitted $a_M/a_{M0}$")
    axes[1].set_ylabel("galaxies")
    axes[1].set_title("Algebraic scale dispersion")
    axes[1].grid(True, which="both", alpha=0.22)
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("HRC-only BTFR and fitted-scale diagnostics")
    fig.tight_layout()
    save(fig, "R97_HRC_BTFR_AND_SCALE")
    return {
        "galaxies": len(rows),
        "tail_proxies": len(good),
        "median_HRC0_ratio": float(np.median(ratios0)),
        "median_HRC3_ratio": float(np.median(ratios3)),
        "p16_p84_HRC0": [float(v) for v in np.percentile(ratios0, [16, 84])],
        "p16_p84_HRC3": [float(v) for v in np.percentile(ratios3, [16, 84])],
    }


def ml_sensitivity_figure(rows):
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.1))
    summary = {}
    for ax, model, color, marker in (
        (axes[0], "HRC0", BLUE, "o"),
        (axes[1], "HRC3", ORANGE, "s"),
    ):
        fixed = np.asarray([r[f"aM_{model}_over_match"] for r in rows])
        free = np.asarray([r[f"aM_{model}_freeML_over_match"] for r in rows])
        ax.scatter(fixed, free, s=15, marker=marker, facecolor="white",
                   edgecolor=color, linewidth=0.7, alpha=0.8)
        lim = (1.0e-2, 1.0e2)
        ax.plot(lim, lim, color=BLACK, lw=1.3, ls=":")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.set_xlabel(r"fixed-$M/L$ $a_M/a_{M0}$")
        ax.set_ylabel(r"free-$M/L$ $a_M/a_{M0}$")
        display = model.replace("HRC", "HRC-")
        ax.set_title(f"{display}: scale--$M/L$ coupling")
        ax.grid(True, which="both", alpha=0.22)
        summary[model] = {
            "median_fixed_scale_ratio": float(np.median(fixed)),
            "median_free_scale_ratio": float(np.median(free)),
            "p16_p84_free_scale_ratio": [
                float(v) for v in np.percentile(free, [16, 84])
            ],
            "median_chi2red_fixed": float(np.median(
                [r[f"chi2red_{model}"] for r in rows]
            )),
            "median_chi2red_freeML": float(np.median(
                [r[f"chi2red_{model}_freeML"] for r in rows]
            )),
            "median_ups_disk_freeML": float(np.median(
                [r[f"ups_disk_{model}_freeML"] for r in rows]
            )),
        }
    ml0 = np.asarray([r["ups_disk_HRC0_freeML"] for r in rows])
    ml3 = np.asarray([r["ups_disk_HRC3_freeML"] for r in rows])
    bins = np.linspace(0.1, 2.5, 25)
    axes[2].hist(ml0, bins=bins, histtype="step", color=BLUE, lw=2.0,
                 ls="--", label="HRC-0")
    axes[2].hist(ml3, bins=bins, histtype="stepfilled", color=ORANGE,
                 edgecolor=ORANGE, alpha=0.22, hatch="..", label="HRC-3")
    axes[2].axvline(0.5, color=BLACK, lw=1.3, ls=":", label="fixed value")
    axes[2].set_xlabel(r"fitted disk $\Upsilon_{\rm d}$")
    axes[2].set_ylabel("galaxies")
    axes[2].set_title("Two-parameter nuisance test")
    axes[2].grid(True, alpha=0.22)
    axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("HRC-only stellar-$M/L$ sensitivity")
    fig.tight_layout()
    save(fig, "R97_HRC_ML_SENSITIVITY")
    return summary


def rotation_gallery(rows):
    """Show 16 galaxies selected by a frozen, non-visual stratification rule."""
    galaxies = load_galaxies()
    enriched = []
    for rec in rows:
        a = galaxies[rec["galaxy"]]
        r, _, _, gn, _ = arrays(a)
        enriched.append((float(np.median(np.log10(gn))), rec["galaxy"]))
    enriched.sort()
    selected = []
    for block in np.array_split(np.asarray(enriched, dtype=object), 4):
        block = list(block)
        for q in (0.125, 0.375, 0.625, 0.875):
            idx = min(int(round(q * (len(block) - 1))), len(block) - 1)
            selected.append(str(block[idx][1]))

    fit_map = {r["galaxy"]: r for r in rows}
    fig, axes = plt.subplots(4, 4, figsize=(12.0, 10.8))
    for ax, name in zip(axes.flat, selected):
        a = galaxies[name]
        r, vobs, err, gn, _ = arrays(a)
        order = np.argsort(r)
        r, vobs, err, gn = r[order], vobs[order], err[order], gn[order]
        rec = fit_map[name]
        ax.errorbar(r, vobs, yerr=err, fmt="o", ms=2.5, color=BLACK,
                    ecolor=GREY, capsize=1.0)
        vbar = np.sqrt(np.maximum(gn / ACC_CONV * r, 0.0))
        ax.plot(r, vbar, color=GREEN, lw=1.0, ls=":")
        for model, color, style in (("HRC0", BLUE, "--"), ("HRC3", ORANGE, "-")):
            g = g_model(gn, rec[f"aM_{model}_si"], model)
            v = np.sqrt(np.maximum(g / ACC_CONV * r, 0.0))
            ax.plot(r, v, color=color, lw=1.4, ls=style)
        ax.set_title(name, fontsize=8)
        ax.grid(True, alpha=0.18)
        ax.tick_params(labelsize=7)
    for ax in axes[-1, :]:
        ax.set_xlabel("R [kpc]", fontsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel(r"$V$ [km s$^{-1}$]", fontsize=8)
    handles = [
        plt.Line2D([], [], color=BLACK, marker="o", ls="", ms=4, label="SPARC"),
        plt.Line2D([], [], color=GREEN, ls=":", label="baryons"),
        plt.Line2D([], [], color=BLUE, ls="--", label="HRC-0"),
        plt.Line2D([], [], color=ORANGE, ls="-", label="HRC-3"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 0.985), fontsize=8)
    fig.suptitle("HRC-only rotation-curve gallery: frozen acceleration-stratified sample",
                 y=0.999)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "R97_HRC_ROTATION_GALLERY")
    return {"selection_rule": "four quantiles in each of four median-log-gN strata",
            "galaxies": selected}


def milky_way_figure():
    r = np.asarray([4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25.0])
    vobs = np.asarray([230, 233, 235, 232, 228, 226, 225, 224, 222, 220, 217, 214, 210, 205.0])
    err = np.asarray([8, 7, 6, 6, 5, 5, 5, 5, 6, 6, 7, 8, 9, 11.0])
    m_disk, r_d = 5.0e10, 2.5
    def vdisk(radius):
        y = np.clip(radius / (2.0 * r_d), 1.0e-9, 50.0)
        term = y**2 * (i0(y) * k0(y) - i1(y) * k1(y))
        g_kpc = 4.30091e-6
        return np.sqrt(np.maximum(2.0 * g_kpc * m_disk / r_d * term, 0.0))
    gn = vdisk(r) ** 2 / r * ACC_CONV
    result = {}
    for model in ("HRC0", "HRC3"):
        a, chi2, success = fit_scale(r, vobs, err, gn, model)
        result[model] = {"aM_si": a, "aM_over_match": a / A_MATCH,
                         "chi2_red": chi2 / (len(r) - 1), "success": success}
    grid = np.linspace(2.0, 30.0, 400)
    vbar = vdisk(grid)
    gn_grid = vbar**2 / grid * ACC_CONV
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.errorbar(r, vobs, yerr=err, fmt="o", ms=4, color=BLACK,
                ecolor=GREY, capsize=2, label="representative Milky-Way data")
    ax.plot(grid, vbar, color=GREEN, lw=1.5, ls=":", label="declared baryonic disk")
    for model, color, style in (("HRC0", BLUE, "--"), ("HRC3", ORANGE, "-")):
        a = result[model]["aM_si"]
        v = np.sqrt(g_model(gn_grid, a, model) / ACC_CONV * grid)
        display = model.replace("HRC", "HRC-")
        ax.plot(grid, v, color=color, lw=2.2, ls=style,
                label=f"{display} best algebraic fit")
        vmatch = np.sqrt(g_model(gn_grid, A_MATCH, model) / ACC_CONV * grid)
        ax.plot(grid, vmatch, color=color, lw=1.0, ls=":", alpha=0.75,
                label=f"{display} matched scale")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 270)
    ax.set_xlabel("R [kpc]")
    ax.set_ylabel(r"$V$ [km s$^{-1}$]")
    ax.set_title("Milky Way: HRC-only algebraic sensitivity test")
    ax.grid(True, alpha=0.22)
    ax.legend(frameon=False, fontsize=7.2, ncol=2)
    fig.tight_layout()
    save(fig, "R97_HRC_MILKY_WAY")
    return result


def udg_figure():
    rows = read_csv(UDG)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    plotted = []
    for row in rows:
        name = row["object"]
        rdyn = float(row["Rdyn"])
        if row["domain"] == "NO_POSITIVE_HRC_ENHANCEMENT_SOLUTION":
            ax.scatter(rdyn, 1.0, marker="x", s=75, color=BLACK, linewidth=2)
            ax.annotate(name, (rdyn, 1.0), xytext=(5, 6), textcoords="offset points", fontsize=7)
            continue
        a0 = float(row["aM_HRC0_over_match"])
        a3 = float(row["aM_HRC3_over_match"])
        ax.scatter(rdyn, a0, marker="o", s=45, facecolor="white", edgecolor=BLUE, linewidth=1.5)
        ax.scatter(rdyn, a3, marker="s", s=38, facecolor=ORANGE, edgecolor=BLACK, linewidth=0.5)
        display = name
        if row["endpoint"] != "central":
            display += " (low)" if row["endpoint"].startswith("low") else " (high)"
        ax.annotate(display, (rdyn, a3), xytext=(5, 5), textcoords="offset points", fontsize=7)
        plotted.append(display)
    ax.axhline(1.0, color=BLACK, ls=":", lw=1.4, label="matched scale")
    ax.scatter([], [], marker="o", facecolor="white", edgecolor=BLUE, label="HRC-0 inverse")
    ax.scatter([], [], marker="s", facecolor=ORANGE, edgecolor=BLACK, label="HRC-3 inverse")
    ax.scatter([], [], marker="x", color=BLACK, label="no positive enhancement solution")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"central proxy $\mathcal{R}_{\rm dyn}=g_{\rm obs}/g_N$")
    ax.set_ylabel(r"required $a_M/a_{M0}$")
    ax.set_title("HRC-only UDG inverse-scale stress test")
    ax.grid(True, which="both", alpha=0.22)
    ax.legend(frameon=False, fontsize=7.3)
    fig.tight_layout()
    apply_publication_readability_floor(fig, size=(6.5, 4.8))
    save(fig, "R97_HRC_UDG_STRESS")
    return {"rows": len(rows), "positive_solution_objects": plotted}


def residual_extremes_figure():
    rows = read_csv(POINTS)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_galaxy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["galaxy"], row["source_row_index"])].append(row)
    for (name, _), values in grouped.items():
        by_galaxy[name].append(values[0])
    score = []
    for name, vals in by_galaxy.items():
        c0 = sum(float(v["chi2_HRC0"]) for v in vals)
        c3 = sum(float(v["chi2_HRC3"]) for v in vals)
        score.append((c0 - c3, c0, name))
    largest_gap = [x[2] for x in sorted(score, reverse=True)[:2]]
    hrc3_stress = [x[2] for x in sorted(score, key=lambda x: x[0])[:2]]
    selected = []
    for name in largest_gap + hrc3_stress:
        if name not in selected:
            selected.append(name)
    while len(selected) < 4:
        for _, _, name in sorted(score, key=lambda x: x[1], reverse=True):
            if name not in selected:
                selected.append(name)
                break
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.5))
    for ax, name in zip(axes.flat, selected[:4]):
        physical = []
        for (galaxy, _), values in grouped.items():
            if galaxy != name:
                continue
            first = values[0]
            physical.append((float(first["radius_kpc"]), float(first["vobs_km_s"]),
                             float(first["error_km_s"]),
                             float(np.mean([float(v["v_HRC0"]) for v in values])),
                             float(np.mean([float(v["v_HRC3"]) for v in values]))))
        a = np.asarray(sorted(physical))
        ax.errorbar(a[:, 0], a[:, 1], yerr=a[:, 2], fmt="o", ms=3.4,
                    color=BLACK, ecolor=GREY, capsize=1.4, label="SPARC")
        ax.plot(a[:, 0], a[:, 3], color=BLUE, ls="--", lw=2.0, label="HRC-0")
        ax.plot(a[:, 0], a[:, 4], color=ORANGE, ls="-", lw=2.0, label="HRC-3")
        ax.set_title(name)
        ax.set_xlabel("R [kpc]")
        ax.set_ylabel(r"$V$ [km s$^{-1}$]")
        ax.grid(True, alpha=0.22)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 0.95))
    fig.suptitle("Post-hoc HRC residual stress examples", y=0.993)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    save(fig, "R97_HRC_RESIDUAL_STRESS")
    return {"selected": selected[:4], "selection": "largest HRC0-HRC3 gaps and reverse gaps"}


def main():
    fits = fit_galaxies()
    common_cv = honest_common_ml_cv()
    common_cv["fold_registry"] = write_common_ml_folds(common_cv)
    results = {
        "status": "LEVEL_C_CONDITIONAL_PUBLICATION_CALCULATION",
        "inputs": {
            DATA_REL: sha256(DATA),
            POINTS_REL: sha256(POINTS),
            str(UDG.relative_to(ROOT)): sha256(UDG),
        },
        "matched_aM_si": A_MATCH,
        "honest_common_ML_transfer_CV": common_cv,
        "btfr_and_scale": btfr_and_scale_figure(fits),
        "ml_sensitivity": ml_sensitivity_figure(fits),
        "rotation_gallery": rotation_gallery(fits),
        "milky_way": milky_way_figure(),
        "udg": udg_figure(),
        "residual_stress": residual_extremes_figure(),
        "guards": {
            "only_HRC0_HRC3_used": True,
            "full_disk_PDE": False,
            "hierarchical_likelihood": False,
            "milky_way_data_and_baryon_model": "representative frozen inputs, not a full modern posterior",
            "residual_examples_post_hoc": True,
        },
    }
    (HERE / "R97_HRC_COMPLETION_RESULTS.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    results["outputs"] = {
        str(p.relative_to(ROOT)): sha256(p)
        for stem in OWNED_STEMS
        for p in (OUT / f"{stem}.pdf", OUT / f"{stem}.png")
        if p.is_file()
    }
    (HERE / "R97_HRC_COMPLETION_MANIFEST.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
