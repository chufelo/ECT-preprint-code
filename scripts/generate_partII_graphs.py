#!/usr/bin/env python3
"""Validate/render Part-II graphs without overwriting the canonical source.

Canonical: scripts/fig_partII_derivation_logic.gv.
Derived: companion/scripts/fig_partII_derivation_logic_pop.gv.
Default mode is read-only validation.  Use --sync-companion before --render.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "fig_partII_derivation_logic.gv"
COMPANION = ROOT / "companion" / "scripts" / "fig_partII_derivation_logic_pop.gv"
DOT = shutil.which("dot")

def derive_companion(text: str) -> str:
    pop = re.sub(r'<BR/>§[0-9]+(\.[0-9]+)?', '', text)
    pop = re.sub(r'<BR/>§§[0-9]+(\.[0-9]+)?(–[0-9]+)?', '', pop)
    pop = re.sub(r' \(§[0-9]+(\.[0-9]+)?\)', '', pop)
    return re.sub(r' §[0-9]+(\.[0-9]+)?', '', pop)

def validate(path: Path) -> None:
    if not DOT:
        raise SystemExit("ERROR: Graphviz dot not found")
    subprocess.run([DOT, "-Tplain", str(path)], check=True,
                   stdout=subprocess.DEVNULL)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync-companion", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    canonical = SOURCE.read_text(encoding="utf-8")
    if "screening/body charge Open" not in canonical or "color=gray" in canonical:
        raise SystemExit("ERROR: canonical Part-II source is not status-synchronised")
    expected = derive_companion(canonical)
    if args.sync_companion:
        COMPANION.write_text(expected, encoding="utf-8")
    elif not COMPANION.exists() or COMPANION.read_text(encoding="utf-8") != expected:
        raise SystemExit("ERROR: companion source stale; run --sync-companion")
    validate(SOURCE)
    validate(COMPANION)
    if args.render:
        subprocess.run([DOT, "-Tpdf", str(SOURCE), "-o",
                        str(ROOT / "figures" / "fig_partII_derivation_logic.pdf")], check=True)
        subprocess.run([DOT, "-Tpdf", str(COMPANION), "-o",
                        str(ROOT / "figures" / "fig_partII_derivation_logic_pop.pdf")], check=True)
    print("PASS: canonical source validated; companion derivative exact")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
