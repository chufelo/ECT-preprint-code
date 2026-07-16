#!/usr/bin/env python3
"""Build only the two SPARC assets embedded in the Round-58 preprint."""
from __future__ import annotations
import argparse
from pathlib import Path
import ect_sparc_fit_phi_branch as s

ap = argparse.ArgumentParser()
ap.add_argument("input")
ap.add_argument("output_dir")
args = ap.parse_args()
out = Path(args.output_dir)
out.mkdir(parents=True, exist_ok=True)
df = s.load_sparc(args.input, error_floor=2.0)
fits = list(s.fit_sample(df, h0=70.0, min_pts=6))
if len(fits) <= 10:
    raise RuntimeError(f"insufficient SPARC fits: {len(fits)}")
s.plot_milky_way(str(out / "set1_milky_way.pdf"), h0=70.0)
s.plot_sparc_gallery(
    df, fits[:20], str(out / "set2_sparc_sample.pdf"),
    ncols=4, h0=70.0,
)
print(f"R58 selected SPARC assets: Nfit={len(fits)}, gallery={min(20, len(fits))}")
