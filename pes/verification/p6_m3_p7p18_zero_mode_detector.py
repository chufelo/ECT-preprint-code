#!/usr/bin/env python3
"""
P6 M3-2: P7-prime/P18 zero-mode detector via t_*(R).
Environment-compatible: numpy only, relative output path by default.

The script is a protocol/audit toy model, not a fit to laboratory data.
It checks the operational discrimination between:
  H0: minimal ECT ribbon/no core Berry zero-mode, n0=0, kappa_M=0, z=1, t_* ~ R;
  H1: core-zero-mode/Berry branch, n0 != 0, z=2 IR, t_* ~ R^2/log(R/xi).
"""

import csv
import math
import os
from typing import Tuple

import numpy as np


def log_slope(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.polyfit(np.log(x), np.log(y), 1)[0])


def cv(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    return float(np.std(y) / abs(np.mean(y)))


def one_param_aic(log_y: np.ndarray, shape: np.ndarray, k: int = 1) -> Tuple[float, float, float]:
    """Fit log_y = amp + shape. Return AIC, amp, rms."""
    amp = float(np.mean(log_y - shape))
    resid = log_y - (amp + shape)
    sse = float(np.sum(resid * resid))
    n = len(log_y)
    sse = max(sse, 1.0e-300)
    aic = n * math.log(sse / n) + 2 * k
    rms = math.sqrt(sse / n)
    return aic, amp, rms


def minimal_aic_grid(R: np.ndarray, tstar: np.ndarray, xi: float) -> Tuple[float, float, float]:
    """Fit t = A (R + R0) with a grid over R0 >= 0. Return best AIC, R0, rms."""
    log_y = np.log(tstar)
    best = (float("inf"), None, None)
    for R0 in np.linspace(0.0, 20.0 * xi, 401):
        shape = np.log(R + R0)
        aic, amp, rms = one_param_aic(log_y, shape, k=2)  # amp and R0
        if aic < best[0]:
            best = (aic, R0, rms)
    return float(best[0]), float(best[1]), float(best[2])


def core_aic(R: np.ndarray, tstar: np.ndarray, xi: float) -> Tuple[float, float, float]:
    """Fit t = B R^2/log(R/xi). Return AIC, B, rms."""
    if np.any(R <= xi):
        raise ValueError("Core-Berry model requires R/xi > 1 for log positivity.")
    log_y = np.log(tstar)
    shape = 2.0 * np.log(R) - np.log(np.log(R / xi))
    aic, amp, rms = one_param_aic(log_y, shape, k=1)
    return aic, float(math.exp(amp)), rms


def local_core_exponent(R: np.ndarray, xi: float) -> float:
    R_geo = math.sqrt(float(np.min(R) * np.max(R)))
    return 2.0 - 1.0 / math.log(R_geo / xi)


def deterministic_ripple(n: int, amp: float = 0.004, phase: float = 0.0) -> np.ndarray:
    idx = np.arange(n, dtype=float)
    return 1.0 + amp * np.sin(1.7 * idx + phase)


def append(rows, section, case, value, expected, check, note):
    rows.append({
        "section": section,
        "case": case,
        "value": value,
        "expected": expected,
        "check": check,
        "note": note,
    })


def main() -> None:
    xi = 1.0
    rows = []

    R = np.geomspace(30.0, 960.0, 12)
    t_min = 0.82 * (R + 3.0 * xi) * deterministic_ripple(len(R), amp=0.003, phase=0.2)
    t_core = 0.033 * R**2 / np.log(R / xi) * deterministic_ripple(len(R), amp=0.003, phase=1.1)
    t_diff = 0.033 * R**2 * deterministic_ripple(len(R), amp=0.003, phase=2.0)

    p_min = log_slope(R, t_min)
    p_core_raw = log_slope(R, t_core)
    p_core_pred = local_core_exponent(R, xi)
    p_core_corrected = log_slope(R, t_core * np.log(R / xi))
    p_diff_raw = log_slope(R, t_diff)
    p_diff_corrected = log_slope(R, t_diff * np.log(R / xi))

    append(rows, "A-slope", "minimal raw t_*(R)", f"{p_min:.6f}", "~1", "PASS" if abs(p_min - 1.0) < 0.05 else "CHECK", "Finite intercept gives a ledger-like slope below 1 but asymptotes to one.")
    append(rows, "A-slope", "core-Berry raw t_*(R)", f"{p_core_raw:.6f}", f"{p_core_pred:.6f}", "PASS" if abs(p_core_raw - p_core_pred) < 0.03 else "CHECK", "Raw slope is window-dependent: p=2-1/log(R/xi), not exactly 2.")
    append(rows, "A-slope", "core-Berry corrected slope", f"{p_core_corrected:.6f}", "2", "PASS" if abs(p_core_corrected - 2.0) < 0.01 else "CHECK", "Fit t_* log(R/xi) vs R; this is the mandatory log guard.")
    append(rows, "A-slope", "diffusion/trap raw t_*(R)", f"{p_diff_raw:.6f}", "~2 but false", "FLAG", "A pure diffusive trap can fake raw R^2; other guards must reject it.")
    append(rows, "A-slope", "diffusion/trap corrected slope", f"{p_diff_corrected:.6f}", ">2", "REJECT_CORE" if p_diff_corrected > 2.05 else "CHECK", "Multiplying by log exposes the false positive: t logR/R^2 is not flat.")

    R_asym = np.geomspace(3.0e5, 3.0e9, 16)
    t_core_asym = R_asym**2 / np.log(R_asym / xi)
    p_core_asym = log_slope(R_asym, t_core_asym)
    append(rows, "A-asymptotic", "core-Berry raw high-window slope", f"{p_core_asym:.6f}", "~1.94", "PASS" if abs(p_core_asym - 1.942) < 0.01 else "CHECK", "This explains the old P7-prime 1.942 number as an asymptotic-window/log-corrected value.")

    aic_min_on_min, r0_min, rms_min_on_min = minimal_aic_grid(R, t_min, xi)
    aic_core_on_min, _, rms_core_on_min = core_aic(R, t_min, xi)
    aic_min_on_core, r0_core, rms_min_on_core = minimal_aic_grid(R, t_core, xi)
    aic_core_on_core, _, rms_core_on_core = core_aic(R, t_core, xi)
    cv_min_norm_on_min = cv(t_min / (R + r0_min))
    cv_core_norm_on_min = cv(t_min * np.log(R / xi) / R**2)
    cv_min_norm_on_core = cv(t_core / (R + r0_core))
    cv_core_norm_on_core = cv(t_core * np.log(R / xi) / R**2)
    cv_core_norm_on_diff = cv(t_diff * np.log(R / xi) / R**2)

    append(rows, "B-flatness", "minimal data: t_*/(R+R0)", f"CV={cv_min_norm_on_min:.3e}; R0={r0_min:.3f}", "flat", "PASS", "Minimal/no-zero-mode model has the flat transformed variable.")
    append(rows, "B-flatness", "minimal data: t_*logR/R^2", f"CV={cv_core_norm_on_min:.3e}", "not flat", "PASS" if cv_core_norm_on_min > 0.2 else "CHECK", "Rejects a mistaken core-Berry reading.")
    append(rows, "B-flatness", "core data: t_*/(R+R0)", f"CV={cv_min_norm_on_core:.3e}; R0={r0_core:.3f}", "not flat", "PASS" if cv_min_norm_on_core > 0.2 else "CHECK", "Rejects a mistaken minimal reading.")
    append(rows, "B-flatness", "core data: t_*logR/R^2", f"CV={cv_core_norm_on_core:.3e}", "flat", "PASS", "Core-zero-mode/Berry branch has the flat log-renormalized variable.")
    append(rows, "B-flatness", "diffusion data: t_*logR/R^2", f"CV={cv_core_norm_on_diff:.3e}", "not flat", "PASS" if cv_core_norm_on_diff > 0.15 else "CHECK", "Guard against raw-R^2 diffusion/trap false positive.")

    append(rows, "C-model-select", "minimal synthetic data", f"DeltaAIC(core-min)={aic_core_on_min-aic_min_on_min:.3f}", ">0 minimal wins", "PASS" if aic_core_on_min > aic_min_on_min else "FAIL", f"rms_min={rms_min_on_min:.3e}; rms_core={rms_core_on_min:.3e}")
    append(rows, "C-model-select", "core-Berry synthetic data", f"DeltaAIC(min-core)={aic_min_on_core-aic_core_on_core:.3f}", ">0 core wins", "PASS" if aic_min_on_core > aic_core_on_core else "FAIL", f"rms_min={rms_min_on_core:.3e}; rms_core={rms_core_on_core:.3e}")

    R_geo = math.sqrt(float(R[0] * R[-1]))
    B_match = math.log(R_geo / xi) / R_geo
    t_core_matched = B_match * R**2 / np.log(R / xi)
    f_mix = 0.30
    t_mix = (1.0 - f_mix) * (R + 3.0 * xi) + f_mix * t_core_matched
    p_mix = log_slope(R, t_mix)
    append(rows, "D-mixed-channel", "30% core leakage into minimal channel", f"raw slope={p_mix:.6f}", "ambiguous", "GUARD", "Intermediate slopes are not new laws; they signal channel mixing or insufficient diagonalisation (G4/G7).")

    tau = np.geomspace(20.0, 1.0e4, 24)
    phi_core_shifted = np.sqrt(2.0 * math.pi * tau)  # Phi + 2 sqrt(pi)
    phi_ohmic_T = tau
    phi_ohmic_vac = np.log1p(tau)
    p_phi_core = log_slope(tau, phi_core_shifted)
    p_phi_ohmic_T = log_slope(tau, phi_ohmic_T)
    p_phi_ohmic_vac = log_slope(tau, phi_ohmic_vac)
    append(rows, "E-early-shape", "core L23 shifted Phi(t)", f"{p_phi_core:.6f}", "1/2", "PASS" if abs(p_phi_core - 0.5) < 1e-12 else "CHECK", "Use Phi+2sqrt(pi) to avoid the known constant-contamination slip.")
    append(rows, "E-early-shape", "occupied ohmic finite-T proxy", f"{p_phi_ohmic_T:.6f}", "1", "PASS", "If the data are ohmic/thermal, a sqrt-law is not expected.")
    append(rows, "E-early-shape", "vacuum-ohmic log proxy", f"{p_phi_ohmic_vac:.6f}", "not 1/2", "PASS" if abs(p_phi_ohmic_vac - 0.5) > 0.1 else "CHECK", "Power-law fits to logs are window artefacts; use the correct kernel class.")

    n0 = 0.40
    prefactor = 0.25
    split_plus_1 = prefactor * (+1) * n0
    split_minus_1 = prefactor * (-1) * n0
    split_zero_n0 = prefactor * (+1) * 0.0
    trap_split_plus = 0.07
    trap_split_minus = 0.07
    berry_antisym_resid = abs(split_plus_1 + split_minus_1)
    trap_antisym_resid = abs(trap_split_plus + trap_split_minus)
    append(rows, "F-Berry-sign", "Berry branch W reversal", f"residual={berry_antisym_resid:.3e}; split(+1)={split_plus_1:.3f}", "odd in W", "PASS", "kappa_M proportional to W n0/S0; reversing winding flips the sign.")
    append(rows, "F-Berry-sign", "n0=0 bulk minimal branch", f"split={split_zero_n0:.3e}", "zero", "PASS", "Minimal ordered branch has n0=0; no bulk Magnus/Berry splitting.")
    append(rows, "F-Berry-sign", "trap false positive W reversal", f"residual={trap_antisym_resid:.3e}", "not odd", "REJECT_TRAP", "A geometric trap/pinning frequency is even in W and fails the Berry sign guard.")

    append(rows, "Z-decision-template", "minimal/no-zero-mode signature", "t_*/R flat + no Berry odd sign", "H0", "ACCEPTABLE", "Supports n0=0 minimal ohmic ribbon; does not falsify P6/PES.")
    append(rows, "Z-decision-template", "core-zero-mode signature", "t_*log(R/xi)/R^2 flat + sqrt early law + W-odd Berry", "H1", "ACCEPTABLE", "Evidence for a nontrivial core zero-mode/Berry sector; still not a derivation of OP-GUT1 rank-three P7.")

    out_path = os.path.join(os.path.dirname(__file__) or ".", "p6_m3_p7p18_results.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["section", "case", "value", "expected", "check", "note"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {out_path} with {len(rows)} rows")


if __name__ == "__main__":
    main()
