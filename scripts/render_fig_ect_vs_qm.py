#!/usr/bin/env python3
"""Render the candidate-local, status-controlled ECT/QM comparison SVG."""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures/source/svg/fig_ect_vs_qm.svg"
OUTPUT = ROOT / "figures/fig_ect_vs_qm.pdf"
EXPECTED_SOURCE_SHA256 = "e4022a89abdffe53e829e36c9ec9c9effb4d9e195e0b3d50ccb35a981d7a4f64"
actual_source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if actual_source_sha256 != EXPECTED_SOURCE_SHA256:
    raise SystemExit(
        f"fig_ect_vs_qm source hash mismatch: {actual_source_sha256} "
        f"!= {EXPECTED_SOURCE_SHA256}"
    )
RSVG = shutil.which("rsvg-convert") or "/opt/homebrew/bin/rsvg-convert"
if not Path(RSVG).exists():
    raise SystemExit("rsvg-convert not found")
env = dict(os.environ)
env["SOURCE_DATE_EPOCH"] = "0"
subprocess.run([RSVG, "-f", "pdf", "-o", str(OUTPUT), str(SOURCE)],
               check=True, env=env)
print(f"rendered {OUTPUT.relative_to(ROOT)}")
