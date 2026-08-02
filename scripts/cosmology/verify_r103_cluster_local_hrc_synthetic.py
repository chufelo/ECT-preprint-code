#!/usr/bin/env python3
"""Reproduce the local-HRC synthetic cluster map test.

The script uses declared Gaussian maps, the HRC-0 inverse response, integrated
box proxies and exact/numerical peak-preservation checks.  Results are
synthetic Level-C map diagnostics; the monotonicity statement itself is exact
algebra inside the declared local map.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
OUT = (
    HERE.parents[1] / "data/cosmology_r103"
    if HERE.name == "cosmology" and HERE.parent.name == "scripts"
    else HERE.parent / "results"
)
JSON_OUT = OUT / "R103_CLUSTER_LOCAL_HRC_SYNTHETIC_v1.json"
CSV_OUT = OUT / "R103_CLUSTER_LOCAL_HRC_SYNTHETIC_v1.csv"

G_N = 6.674e-11
M_SUN = 1.989e30
KPC = 3.086e19
N_GRID = 128
L_BOX_KPC = 2200.0
DX_KPC = L_BOX_KPC / N_GRID
XC = (np.arange(N_GRID) + 0.5) * DX_KPC - L_BOX_KPC / 2.0
X2, Y2 = np.meshgrid(XC, XC, indexing="ij")
SURFACE_UNIT = M_SUN / KPC**2

CLUSTERS = {
    "Bullet": {
        "bcg": [(-200.0, 5e12, 70.0), (200.0, 5e12, 70.0)],
        "gas": [(-80.0, 6e13, 225.0, 0.8), (80.0, 6e13, 225.0, 0.8)],
        "a_M": 1.2e-10,
        "declared_peak_class": "BCG",
    },
    "MACS J0025": {
        "bcg": [(-190.0, 3e12, 60.0), (190.0, 3e12, 60.0)],
        "gas": [(-80.0, 2e13, 250.0, 0.9), (80.0, 2e13, 250.0, 0.9)],
        "a_M": 1.0e-10,
        "declared_peak_class": "BCG",
    },
    "El Gordo": {
        "bcg": [(-250.0, 8e12, 65.0), (180.0, 5e12, 65.0)],
        "gas": [(-100.0, 5e13, 290.0, 0.75), (100.0, 3e13, 280.0, 0.75)],
        "a_M": 1.4e-10,
        "declared_peak_class": "BCG",
    },
    "Abell 520": {
        "bcg": [(-370.0, 2.5e12, 90.0), (370.0, 2.5e12, 90.0)],
        "gas": [(0.0, 5e13, 150.0, 1.0)],
        "a_M": 1.0e-10,
        "declared_peak_class": "gas",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gaussian(x0: float, y0: float, sx: float, sy: float, mass_solar: float) -> np.ndarray:
    return (
        mass_solar * M_SUN / (2.0 * np.pi * sx * sy * KPC**2)
        * np.exp(-0.5 * (((X2 - x0) / sx) ** 2 + ((Y2 - y0) / sy) ** 2))
    )


def inverse_hrc0(y: np.ndarray) -> np.ndarray:
    y_safe = np.maximum(y, 1e-300)
    return np.sqrt((1.0 + np.sqrt(1.0 + 4.0 / y_safe**2)) / 2.0)


def find_peak(array: np.ndarray, span_kpc: float = 620.0) -> tuple[float, float, tuple[int, int]]:
    lo = int((-span_kpc + L_BOX_KPC / 2.0) / DX_KPC)
    hi = int((span_kpc + L_BOX_KPC / 2.0) / DX_KPC)
    masked = np.full_like(array, -np.inf)
    masked[lo:hi, lo:hi] = array[lo:hi, lo:hi]
    index = np.unravel_index(int(np.argmax(masked)), masked.shape)
    return float(XC[index[0]]), float(XC[index[1]]), (int(index[0]), int(index[1]))


def main() -> None:
    rows = []
    for name, cfg in CLUSTERS.items():
        sigma_star = np.zeros((N_GRID, N_GRID))
        sigma_gas = np.zeros((N_GRID, N_GRID))
        for x0, mass, width in cfg["bcg"]:
            sigma_star += gaussian(x0, 0.0, width, width, mass) / SURFACE_UNIT
        for x0, mass, width, axis_ratio in cfg["gas"]:
            sigma_gas += gaussian(x0, 0.0, width, width * axis_ratio, mass) / SURFACE_UNIT
        sigma_b = sigma_star + sigma_gas
        g_n = 2.0 * np.pi * G_N * sigma_b * SURFACE_UNIT
        nu = inverse_hrc0(g_n / float(cfg["a_M"]))
        sigma_response = nu * sigma_b

        xb, yb, ib = find_peak(sigma_b)
        xr, yr, ir = find_peak(sigma_response)
        d_star = min(abs(xr - float(component[0])) for component in cfg["bcg"])
        d_gas = min(abs(xr - float(component[0])) for component in cfg["gas"])
        peak_class = "BCG" if d_star < d_gas else "gas"
        baryonic_box_mass = float(np.sum(sigma_b) * DX_KPC**2)
        response_box_mass = float(np.sum(sigma_response) * DX_KPC**2)
        response_mass_ratio = response_box_mass / baryonic_box_mass
        nu_at_baryonic_peak = float(nu[ib])

        # Direct numerical monotonicity check on the populated pixels.
        order = np.argsort(sigma_b.ravel())
        ordered_response = sigma_response.ravel()[order]
        min_order_increment = float(np.min(np.diff(ordered_response)))
        rows.append({
            "system": name,
            "a_M_m_s2_hand_set": float(cfg["a_M"]),
            "declared_peak_class": str(cfg["declared_peak_class"]),
            "replayed_peak_class": peak_class,
            "argmax_sigma_b_x_kpc": xb,
            "argmax_sigma_b_y_kpc": yb,
            "argmax_sigma_response_x_kpc": xr,
            "argmax_sigma_response_y_kpc": yr,
            "argmax_index_equal": ib == ir,
            "distance_to_nearest_BCG_kpc": d_star,
            "distance_to_nearest_gas_centre_kpc": d_gas,
            "min_sorted_response_increment": min_order_increment,
            "all_pixel_ordering_preserved_with_roundoff": min_order_increment >= -1e-10,
            "baryonic_box_mass_Msun": baryonic_box_mass,
            "local_hrc_response_box_mass_proxy_Msun": response_box_mass,
            "local_hrc_response_to_baryonic_box_mass_ratio": response_mass_ratio,
            "nu_HRC0_at_baryonic_peak": nu_at_baryonic_peak,
        })

    checks = {
        "all_argmax_indices_equal": all(bool(row["argmax_index_equal"]) for row in rows),
        "all_declared_peak_classes_replayed": all(
            row["declared_peak_class"] == row["replayed_peak_class"] for row in rows
        ),
        "all_pixel_ordering_preserved_with_roundoff": all(
            bool(row["all_pixel_ordering_preserved_with_roundoff"]) for row in rows
        ),
        "all_integrated_response_proxies_finite_and_enhanced": all(
            np.isfinite(row["local_hrc_response_to_baryonic_box_mass_ratio"])
            and row["local_hrc_response_to_baryonic_box_mass_ratio"] > 1.0
            for row in rows
        ),
    }
    payload = {
        "date": "2026-07-18",
        "status": "Level A local-map monotonicity algebra; Level C synthetic replay; no observational morphology claim",
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "script_sha256": sha256(Path(__file__)),
        "grid": {"N": N_GRID, "L_box_kpc": L_BOX_KPC, "dx_kpc": DX_KPC},
        "inputs": CLUSTERS,
        "map": "Sigma_response=nu_HRC0(2 pi G Sigma_b/a_M) Sigma_b",
        "scope_exclusions": [
            "physical collision dynamics",
            "retarded response kernel",
            "photon-metric and shear forward model",
            "observationally reconstructed surface-density maps",
        ],
        "rows": rows,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_guard": (
            "the hand-set finite-box maps give only an integrated local-HRC mass-discrepancy proxy and validate peak preservation; they are not reconstructed data or a collision, lensing, residual-mass, or morphology calculation"
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with CSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
