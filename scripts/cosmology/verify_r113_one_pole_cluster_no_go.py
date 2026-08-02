#!/usr/bin/env python3
"""Verify the conditional one-real-pole Bullet-scale mismatch.

The calculation tests one deliberately narrow identification:

    tau_pole = tau_aM = 2 pi / H0,    ell = v tau_pole.

It does not identify a KMS imaginary-time period with a retarded pole, does
not exclude multi-pole/dispersive kernels, and is not a cluster simulation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "data/cosmology_r113"
JSON_OUT = OUT / "R113_ONE_POLE_CLUSTER_NO_GO_v2.json"

MPC_KM = 3.0856775814913673e19
KPC_KM = MPC_KM / 1000.0
JULIAN_YEAR_S = 31_557_600.0
GYR_S = 1.0e9 * JULIAN_YEAR_S
MYR_S = 1.0e6 * JULIAN_YEAR_S

H0_VALUES = (67.4, 70.0, 73.04)
SPEEDS_KM_S = (2250.0, 3000.0)
OFFSETS_KPC = (70.0, 100.0)


def tau_gyr(h0_km_s_mpc: float) -> float:
    return 2.0 * math.pi * MPC_KM / h0_km_s_mpc / GYR_S


def distance_mpc(speed_km_s: float, tau_in_gyr: float) -> float:
    return speed_km_s * tau_in_gyr * GYR_S / MPC_KM


def travel_time_myr(offset_kpc: float, speed_km_s: float) -> float:
    return offset_kpc * KPC_KM / speed_km_s / MYR_S


def main() -> None:
    taus = {f"H0={h0:g}": tau_gyr(h0) for h0 in H0_VALUES}
    tau70 = tau_gyr(70.0)
    transport = {
        f"v={speed:g}": distance_mpc(speed, tau70) for speed in SPEEDS_KM_S
    }
    required = {
        f"offset={offset:g},v={speed:g}": travel_time_myr(offset, speed)
        for offset in OFFSETS_KPC
        for speed in SPEEDS_KM_S
    }
    transport_min = min(transport.values())
    transport_max = max(transport.values())
    time_min = min(required.values())
    time_max = max(required.values())
    mismatch_low = tau70 * 1000.0 / time_max
    mismatch_high = tau70 * 1000.0 / time_min

    checks = {
        "tau70_matches_87p7664_Gyr": abs(tau70 - 87.7664) < 5.0e-5,
        "transport_range_matches_201p96_to_269p28_Mpc": (
            abs(transport_min - 201.96) < 0.01
            and abs(transport_max - 269.28) < 0.01
        ),
        "required_time_matches_22p82_to_43p46_Myr": (
            abs(time_min - 22.82) < 0.01 and abs(time_max - 43.46) < 0.01
        ),
        "mismatch_exceeds_three_orders": mismatch_low > 1000.0,
    }
    payload = {
        "date": "2026-07-20",
        "status": (
            "Conditional Level A arithmetic/no-go for one real constant Debye pole "
            "plus ballistic transport; not a no-go for general retarded response"
        ),
        "scientific_freeze_policy": (
            "Runtime metadata is execution provenance and is excluded from this "
            "deterministic scientific JSON payload."
        ),
        "assumptions": {
            "pole_identification": "tau_pole=tau_aM=2*pi/H0",
            "transport_law": "ell=v*tau_pole",
            "reference_H0_km_s_Mpc": 70.0,
            "merger_speeds_km_s": list(SPEEDS_KM_S),
            "target_offsets_kpc": list(OFFSETS_KPC),
        },
        "tau_aM_Gyr": taus,
        "ballistic_transport_at_H0_70_Mpc": transport,
        "required_offset_times_Myr": required,
        "ranges": {
            "transport_Mpc": [transport_min, transport_max],
            "required_time_Myr": [time_min, time_max],
            "tau_to_required_time_ratio": [mismatch_low, mismatch_high],
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation_guard": (
            "A KMS Euclidean period fixes no retarded pole without a spectral-function "
            "derivation. Multipole, dispersive, anisotropic or separately owned merger "
            "kernels are not tested."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not payload["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
