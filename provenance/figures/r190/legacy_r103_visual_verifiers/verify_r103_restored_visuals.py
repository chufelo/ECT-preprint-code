#!/usr/bin/env python3
"""Verify the integrated R103 restored visualisations.

Checks frozen input and manuscript insertions, byte-for-byte replay, one-page PDF
structure, searchable status text, rasterisation, and grayscale information.
The manuscript source is read-only; only the requested verification directory
is regenerated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import matplotlib
import numpy as np
from PIL import Image
import pypdf


CSV_SHA256 = "fe7d5c9b4aca42ff7e552e38eef96284efcdc89cdd9066d63b8f5bfe6c4acd8e"
SOURCE_JSON_SHA256 = "7ab8fb98486fbd9a4a80e0c2777f666bc455a26c8f3d9bb0c6d19aa4217f151f"
STEMS = (
    "r103_Cn_scalechain_corrected",
    "r103_mediator_channels_terminal_47C",
    "r103_two_slope_HwG_conditional",
)

INTEGRATED_SNIPPETS = {
    "Cn_scalechain": "\\includegraphics[width=0.96\\textwidth]{figures/r103/r103_Cn_scalechain_corrected.pdf}",
    "mediator_47C": "\\includegraphics[width=0.96\\textwidth]{figures/r103/r103_mediator_channels_terminal_47C.pdf}",
    "two_slope_HwG": "\\includegraphics[width=0.98\\textwidth]{figures/r103/r103_two_slope_HwG_conditional.pdf}",
}

NEW_LABELS = (
    "fig:r103_Cn_scalechain_corrected",
    "fig:mediator_channels_terminal_47C",
    "fig:r103_two_slope_HwG_conditional",
)

PDF_TEXT_GUARDS = {
    "r103_Cn_scalechain_corrected": (
        "Established owner chain ends at",
        "OPEN:",
        "Physical tensor scale",
    ),
    "r103_mediator_channels_terminal_47C": (
        "MISSING VERTEX",
        "NOT IDENTIFIABLE",
        "DOUBLE-COUNTED",
        "response and noise remain distinct",
    ),
    "r103_two_slope_HwG_conditional": (
        "no common-",
        "not local",
        "Level C observable diagnostic",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--hwg-csv", type=Path, required=True)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--candidate-tex", type=Path, required=True)
    parser.add_argument("--expected-candidate-sha", required=True)
    parser.add_argument("--verification-dir", type=Path, required=True)
    args = parser.parse_args()

    args.verification_dir.mkdir(parents=True, exist_ok=True)
    rendered_dir = args.verification_dir / "rendered_pdf"
    grayscale_dir = args.verification_dir / "grayscale"
    shutil.rmtree(rendered_dir, ignore_errors=True)
    shutil.rmtree(grayscale_dir, ignore_errors=True)
    rendered_dir.mkdir()
    grayscale_dir.mkdir()

    results: dict[str, object] = {
        "status": "PASS",
        "scope": "integrated isolated-candidate verification; manuscript source read-only",
        "environment": {
            "python": sys.version.split()[0],
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pypdf": pypdf.__version__,
        },
        "inputs": {},
        "anchors": {},
        "figures": {},
        "redundant_encodings": {
            "Cn_scalechain": "fill + hatch + border style + arrow style + explicit status text",
            "mediator_47C": "hatch + border style + explicit terminal status text",
            "two_slope_HwG": "line style + marker shape/fill + direct labels; colour is redundant",
        },
    }

    csv_hash = sha256(args.hwg_csv)
    source_hash = sha256(args.source_json)
    candidate_hash_before = sha256(args.candidate_tex)
    results["inputs"] = {
        "hwg_csv": {"path": str(args.hwg_csv), "sha256": csv_hash, "expected": CSV_SHA256},
        "source_json": {"path": str(args.source_json), "sha256": source_hash, "expected": SOURCE_JSON_SHA256},
        "candidate_tex": {
            "path": str(args.candidate_tex),
            "sha256_before": candidate_hash_before,
            "expected": args.expected_candidate_sha,
        },
        "generator": {"path": str(args.generator), "sha256": sha256(args.generator)},
    }
    if csv_hash != CSV_SHA256 or source_hash != SOURCE_JSON_SHA256 or candidate_hash_before != args.expected_candidate_sha:
        results["status"] = "FAIL"

    subset_fields = (
        "z",
        "E_two_slope",
        "E_reference",
        "delta_E_percent",
        "w_eff_two_slope",
        "w_eff_reference",
        "F_over_F0",
    )
    source_rows = json.loads(args.source_json.read_text(encoding="utf-8"))["rows"]
    with args.hwg_csv.open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    diffs = []
    for source_row, csv_row in zip(source_rows, csv_rows):
        for field in subset_fields:
            diffs.append(abs(float(source_row[field]) - float(csv_row[field])))
    subset_exact = len(source_rows) == len(csv_rows) and max(diffs, default=float("inf")) == 0.0
    results["inputs"]["hwg_csv"]["source_subset_fields"] = list(subset_fields)
    results["inputs"]["hwg_csv"]["source_rows"] = len(source_rows)
    results["inputs"]["hwg_csv"]["csv_rows"] = len(csv_rows)
    results["inputs"]["hwg_csv"]["max_abs_subset_difference"] = max(diffs, default=None)
    results["inputs"]["hwg_csv"]["exact_source_subset"] = subset_exact
    if not subset_exact:
        results["status"] = "FAIL"

    candidate_text = args.candidate_tex.read_text(encoding="utf-8")
    for name, snippet in INTEGRATED_SNIPPETS.items():
        count = candidate_text.count(snippet)
        results["anchors"][name] = {"count": count, "required": 1}
        if count != 1:
            results["status"] = "FAIL"
    for label in NEW_LABELS:
        count = candidate_text.count(label)
        results["anchors"][f"integrated_label::{label}"] = {"count": count, "required": 1}
        if count != 1:
            results["status"] = "FAIL"

    with tempfile.TemporaryDirectory(prefix="r103_visual_replay_") as tmp:
        replay = Path(tmp)
        subprocess.run(
            [
                sys.executable,
                str(args.generator),
                "--hwg-csv",
                str(args.hwg_csv),
                "--output-dir",
                str(replay),
            ],
            check=True,
        )
        for stem in STEMS:
            entry: dict[str, object] = {}
            for suffix in (".pdf", ".png"):
                canonical = args.figures_dir / f"{stem}{suffix}"
                reproduced = replay / f"{stem}{suffix}"
                identical = canonical.read_bytes() == reproduced.read_bytes()
                entry[suffix[1:]] = {
                    "sha256": sha256(canonical),
                    "byte_identical_replay": identical,
                    "bytes": canonical.stat().st_size,
                }
                if not identical:
                    results["status"] = "FAIL"

            pdf = args.figures_dir / f"{stem}.pdf"
            info = run(["pdfinfo", str(pdf)])
            pages = int(next(line.split(":", 1)[1].strip() for line in info.splitlines() if line.startswith("Pages:")))
            entry["pdf_pages"] = pages
            if pages != 1:
                results["status"] = "FAIL"

            extracted = "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(str(pdf)).pages)
            text_checks = {guard: guard in extracted for guard in PDF_TEXT_GUARDS[stem]}
            entry["pdf_text_guards"] = text_checks
            if not all(text_checks.values()):
                results["status"] = "FAIL"

            render_prefix = rendered_dir / stem
            subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-r", "180", "-png", str(pdf), str(render_prefix)], check=True)
            rendered = render_prefix.with_suffix(".png")
            with Image.open(rendered) as image:
                gray = image.convert("L")
                gray_path = grayscale_dir / f"{stem}_gray.png"
                gray.save(gray_path, optimize=False)
                pixels = np.asarray(gray, dtype=np.uint8)
                nonwhite = pixels[pixels < 248]
                entry["render"] = {
                    "path": str(rendered),
                    "size_px": list(image.size),
                    "grayscale_path": str(gray_path),
                    "grayscale_min": int(pixels.min()),
                    "grayscale_max": int(pixels.max()),
                    "nonwhite_fraction": float(nonwhite.size / pixels.size),
                    "nonwhite_luma_p05_p50_p95": [float(x) for x in np.percentile(nonwhite, [5, 50, 95])],
                }
                if pixels.min() > 40 or nonwhite.size / pixels.size < 0.01:
                    results["status"] = "FAIL"

            results["figures"][stem] = entry

    candidate_hash_after = sha256(args.candidate_tex)
    results["inputs"]["candidate_tex"]["sha256_after"] = candidate_hash_after
    results["inputs"]["candidate_tex"]["unchanged"] = candidate_hash_after == candidate_hash_before
    if candidate_hash_after != candidate_hash_before:
        results["status"] = "FAIL"

    output = args.verification_dir / "R103_RESTORED_VISUALS_VERIFICATION_v1.json"
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + os.linesep, encoding="utf-8")
    print(json.dumps({"status": results["status"], "output": str(output)}, sort_keys=True))
    if results["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
