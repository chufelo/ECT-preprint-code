#!/usr/bin/env python3
"""Render the canonical popular ECT derivation-map source."""
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "figures" / "source" / "graphviz" / "fig_ect_derivation_map_pop.dot"
OUTPUT = ROOT / "figures" / "fig_ect_derivation_map_pop.png"
DOT = shutil.which("dot")
if not DOT:
    raise SystemExit("ERROR: Graphviz dot not found")
if not SOURCE.exists():
    raise SystemExit(f"ERROR: canonical source missing: {SOURCE}")
subprocess.run([DOT, "-Tplain", str(SOURCE)], check=True,
               stdout=subprocess.DEVNULL)
subprocess.run([DOT, "-Tpng", "-Gdpi=300", str(SOURCE), "-o", str(OUTPUT)],
               check=True)
with OUTPUT.open("rb") as fh:
    fh.read(16); width, height = struct.unpack(">II", fh.read(8))
print(f"Regenerated {OUTPUT} from {SOURCE}: {width}x{height}")
