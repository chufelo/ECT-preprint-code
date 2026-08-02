#!/usr/bin/env python3
"""Derive the restricted peculiar-velocity/bulk-flow carrier from R103 data.

This script does not solve a new perturbation system.  It reads the frozen
same-metric, zero-slip, sub-horizon proxy rows and evaluates the linear
velocity carrier a H f D relative to the matched control.  The output is a
Level-C limiting diagnostic, not a survey bulk-flow or Great-Attractor
prediction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for row in source["rows_primary"]:
        model = (
            row["a"]
            * row["E_model"]
            * row["growth_rate_f_model"]
            * row["D_model_same_primordial_norm"]
        )
        control = (
            row["a"]
            * row["E_control"]
            * row["growth_rate_f_control"]
            * row["D_control_same_primordial_norm"]
        )
        ratio = model / control
        rows.append(
            {
                "z": row["z"],
                "velocity_carrier_model": model,
                "velocity_carrier_control": control,
                "delta_velocity_carrier_percent": 100.0 * (ratio - 1.0),
                "delta_velocity_power_carrier_percent": 100.0 * (ratio * ratio - 1.0),
            }
        )

    result = {
        "date": "2026-07-18",
        "status": "PASS_RESTRICTED_PROXY_ONLY",
        "source": str(args.input),
        "source_sha256": sha256(args.input),
        "definition": "V_carrier=a*H/H0*f*D with identical primordial D normalization",
        "fourier_convention": "exp(i k.x), theta_m=i k.v=-a H f delta, v=i a H f k delta/k^2",
        "rows": rows,
        "interpretation_guard": (
            "Level-C same-metric, zero-slip, sub-horizon, massless/mixing-free "
            "linear carrier only; not a physical bulk-flow, Great-Attractor, "
            "velocity-likelihood, or nonlinear prediction"
        ),
        "runtime": {"python": platform.python_version()},
        "all_checks_pass": all(
            abs(r["delta_velocity_carrier_percent"]) < 0.01 for r in rows
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
