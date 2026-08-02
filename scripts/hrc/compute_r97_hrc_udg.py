#!/usr/bin/env python3
"""HRC-only spherical Wolf-proxy diagnostic for selected UDGs.

This replaces the superseded phenomenological inversion with direct HRC-0 and
HRC-3 inversions.  It is a Level-C central-value proxy, not a Jeans posterior
or a prediction of an environment law.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


LATEX_ROOT = Path(__file__).resolve().parents[2]
OUT = LATEX_ROOT / "data" / "hrc_r97"
G = 6.67430e-11
M_SUN = 1.98847e30
KPC = 3.085677581491367e19
C = 299792458.0
MPC = 3.0856775814913673e22
H0 = 70.0 * 1000.0 / MPC
A_MATCH = C * H0 / (2.0 * math.pi)

# The stellar masses, effective radii and dispersions are the disclosed
# central inputs already used by the live UDG diagnostic.  At the 3D
# half-light radius R_1/2=4R_e/3, the enclosed stellar mass proxy is M*/2.
OBJECTS = [
    ("NGC 1052--DF4", 1.50, 1.60, 6.3, "central"),
    ("FCC 224", 1.74, 1.89, 7.8, "central"),
    ("NGC 1052--DF2", 1.30, 2.20, 8.6, "low dispersion endpoint"),
    ("NGC 1052--DF2", 1.30, 2.20, 14.9, "high dispersion endpoint"),
    ("NGC 5846-UDG1", 1.10, 2.10, 17.0, "central"),
    ("Dragonfly 44", 3.00, 4.70, 33.0, "central"),
]

# Quoted dispersion-only intervals retained from the source diagnostic.  They
# are heterogeneous literature ranges, not common-confidence intervals.
INTERVALS = [
    ("NGC 1052--DF4", 1.50, 1.60, 4.7, 8.8),
    ("FCC 224", 1.74, 1.89, 3.4, 14.5),
    ("NGC 1052--DF2", 1.30, 2.20, 8.6, 14.9),
    ("NGC 5846-UDG1", 1.10, 2.10, 15.0, 19.0),
    ("Dragonfly 44", 3.00, 4.70, 30.0, 36.0),
]


def mu3(x: float) -> float:
    y = x * x
    return x / math.sqrt(1.0 + y) * (1.0 - (4.0 / 3.0) * y / (1.0 + y) ** 2)


def invert_monotone_mu3(target: float) -> float:
    lo, hi = 1e-14, 1e14
    for _ in range(240):
        mid = math.sqrt(lo * hi)
        if mu3(mid) < target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def row_for(item: tuple[str, float, float, float, str]) -> dict[str, object]:
    name, mass_1e8, re_kpc, sigma_kms, endpoint = item
    r_half = (4.0 / 3.0) * re_kpc * KPC
    m_half = 0.5 * mass_1e8 * 1e8 * M_SUN
    g_n = G * m_half / r_half**2
    g_obs = 3.0 * (sigma_kms * 1000.0) ** 2 / r_half
    ratio = g_obs / g_n
    output: dict[str, object] = {
        "object": name,
        "endpoint": endpoint,
        "Mstar_1e8_Msun": mass_1e8,
        "Re_kpc": re_kpc,
        "sigma_km_s": sigma_kms,
        "gN_m_s2": g_n,
        "gobs_m_s2": g_obs,
        "Rdyn": ratio,
        "aM_match_m_s2": A_MATCH,
    }
    if ratio < 1.0:
        output.update(
            {
                "domain": "NO_POSITIVE_HRC_ENHANCEMENT_SOLUTION",
                "aM_HRC0_m_s2": None,
                "aM_HRC0_over_match": None,
                "aM_HRC3_m_s2": None,
                "aM_HRC3_over_match": None,
            }
        )
        return output

    target_mu = 1.0 / ratio
    x0 = 1.0 / math.sqrt(ratio * ratio - 1.0)
    x3 = invert_monotone_mu3(target_mu)
    a0 = g_obs / x0
    a3 = g_obs / x3
    output.update(
        {
            "domain": "POSITIVE_HRC_SOLUTION",
            "aM_HRC0_m_s2": a0,
            "aM_HRC0_over_match": a0 / A_MATCH,
            "aM_HRC3_m_s2": a3,
            "aM_HRC3_over_match": a3 / A_MATCH,
            "inverse_residual_HRC0": abs((x0 / math.sqrt(1.0 + x0 * x0)) - target_mu),
            "inverse_residual_HRC3": abs(mu3(x3) - target_mu),
        }
    )
    return output


def main() -> None:
    rows = [row_for(item) for item in OBJECTS]
    csv_path = OUT / "R97_HRC_UDG_DIAGNOSTIC.csv"
    fieldnames = list(rows[0].keys())
    for row in rows[1:]:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    interval_rows = []
    for name, mass, radius, sigma_lo, sigma_hi in INTERVALS:
        lo = row_for((name, mass, radius, sigma_lo, "interval low"))
        hi = row_for((name, mass, radius, sigma_hi, "interval high"))
        interval_rows.append(
            {
                "object": name,
                "sigma_lo_km_s": sigma_lo,
                "sigma_hi_km_s": sigma_hi,
                "Rdyn_lo": lo["Rdyn"],
                "Rdyn_hi": hi["Rdyn"],
                "HRC_domain_lo": lo["domain"],
                "HRC_domain_hi": hi["domain"],
                "aM_HRC0_lo_over_match": lo.get("aM_HRC0_over_match"),
                "aM_HRC0_hi_over_match": hi.get("aM_HRC0_over_match"),
                "aM_HRC3_lo_over_match": lo.get("aM_HRC3_over_match"),
                "aM_HRC3_hi_over_match": hi.get("aM_HRC3_over_match"),
            }
        )
    interval_path = OUT / "R97_HRC_UDG_INTERVALS.csv"
    with interval_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(interval_rows[0]))
        writer.writeheader()
        writer.writerows(interval_rows)

    result = {
        "status": "LEVEL_C_CENTRAL_PROXY_NOT_JEANS_POSTERIOR",
        "method": {
            "R_half": "4 Re / 3",
            "Mbar_enclosed": "Mstar / 2",
            "g_obs": "3 sigma^2 / R_half",
            "HRC_equation": "g_N = mu(g/a_M) g",
            "aM_match": "c H0 / (2 pi), H0=70 km/s/Mpc",
        },
        "rows": rows,
        "dispersion_only_intervals": interval_rows,
        "guards": {
            "superseded_law_used": False,
            "spherical_proxy_only": True,
            "central_values_only": True,
            "environment_law_derived": False,
            "disc_solver_used": False,
        },
    }
    json_path = OUT / "R97_HRC_UDG_DIAGNOSTIC.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "interval_csv_sha256": hashlib.sha256(interval_path.read_bytes()).hexdigest(),
        "json_sha256": hashlib.sha256(json_path.read_bytes()).hexdigest(),
        "max_inverse_residual": max(
            max(float(row.get("inverse_residual_HRC0", 0.0)), float(row.get("inverse_residual_HRC3", 0.0)))
            for row in rows
            if row["domain"] == "POSITIVE_HRC_SOLUTION"
        ),
    }
    (OUT / "R97_HRC_UDG_VERIFICATION.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
