#!/usr/bin/env python3
"""Verify immutable inputs and output structure of R149 typography successors."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "LaTex/ECT_preprint.tex").is_file())
R123 = ROOT / "LaTex/work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v1"
OUT = COMPONENT / "outputs"
QA = COMPONENT / "qa"

EXPECTED = {
    R123 / "components/evolution_restoration/scripts/make_r123_evolution_restoration.py": "97f3dc5c64f9c107a10fce0c5b32c892fee3d28b3cddda419e0c9c5170b85e7b",
    R123 / "components/rotation_comparison/render_r123_rotation_comparison.py": "084621935a557eb9b39c36a194b4a4dfa94b6d6d99f78845d0c56e38b44ab27e",
    R123 / "components/rotation_comparison/frozen_r102/R102_SPARC_MODEL_POINT_CURVES_v1.csv": "d1071900bdded8c17c9d857b5ea207a415f37d4c01a7f15d5ea643559f320a56",
    R123 / "components/rotation_comparison/frozen_r102/R102_SPARC_SAMPLE_REGISTRY_v1.csv": "0b90133caba285fb78453b7d4112afb0a0b1c5b66d10e52ad453effc2782624e",
    R123 / "components/rotation_comparison/frozen_r102/R102_SPARC_MODEL_RESULTS_v1.json": "9037ffbfe36ed0b4d074e8851d7356c57f53748ad301ea239850e36ca9c5eed9",
    R123 / "scripts/r123_palette.py": "5ac5336db41e8b444d048019983e2be0db16a59f6793aa0d32762ede8dbc4bdd",
}

PDFS = [
    "r149_external_internal_history_map_typography.pdf",
    "r149_conditional_post_ordering_evolution_typography.pdf",
    "R149_SPARC_EXTERNAL_MODEL_COMPARISON_TYPOGRAPHY_v1_A.pdf",
    "R149_SPARC_EXTERNAL_MODEL_COMPARISON_TYPOGRAPHY_v1_B.pdf",
    "R149_SPARC_EXTERNAL_MODEL_COMPARISON_TYPOGRAPHY_v1_C.pdf",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_pages(path: Path) -> int:
    output = subprocess.check_output(["pdfinfo", str(path)], text=True)
    return int(next(line.split(":", 1)[1].strip() for line in output.splitlines() if line.startswith("Pages:")))


def main() -> None:
    QA.mkdir(parents=True, exist_ok=True)
    inputs = {str(path.relative_to(ROOT)): {"expected": expected, "actual": sha(path), "ok": sha(path) == expected} for path, expected in EXPECTED.items()}
    point_csv = R123 / "components/rotation_comparison/frozen_r102/R102_SPARC_MODEL_POINT_CURVES_v1.csv"
    sample_csv = R123 / "components/rotation_comparison/frozen_r102/R102_SPARC_SAMPLE_REGISTRY_v1.csv"
    points = list(csv.DictReader(point_csv.open(encoding="utf-8")))
    sample = sorted(list(csv.DictReader(sample_csv.open(encoding="utf-8"))), key=lambda row: int(row["sample_order"]))
    required_models = ["v_baryons_km_s", "v_MOND-standard_km_s", "v_HRC-0_km_s", "v_HRC-3_km_s", "v_NFW-fit_km_s"]
    curve_checks = {
        "row_count": len(points),
        "galaxies": [row["galaxy"] for row in sample],
        "pairs": {"A": [row["galaxy"] for row in sample[:2]], "B": [row["galaxy"] for row in sample[2:4]], "C": [row["galaxy"] for row in sample[4:6]]},
        "all_required_series_present": all(all(key in row for key in required_models) for row in points),
        "numeric_payload_sha256": sha(point_csv),
    }
    outputs = {name: {"exists": (OUT / name).is_file(), "sha256": sha(OUT / name) if (OUT / name).is_file() else None, "pages": pdf_pages(OUT / name) if (OUT / name).is_file() else None} for name in PDFS}
    preview_expectations = [
        f"{Path(name).stem}_{suffix}.png" for name in PDFS for suffix in ("GRAYSAFE", "DEUTERANOPIA", "PROTANOPIA", "TRITANOPIA")
    ]
    previews = {name: (COMPONENT / "previews" / name).is_file() for name in preview_expectations}
    report = {
        "status": "PASS" if all(v["ok"] for v in inputs.values()) and all(v["exists"] and v["pages"] == 1 for v in outputs.values()) and curve_checks["all_required_series_present"] and all(previews.values()) else "FAIL",
        "inputs": inputs,
        "curve_payload": curve_checks,
        "outputs": outputs,
        "previews": previews,
        "scientific_payload_change": False,
        "scope": "layout and typography successors only",
    }
    (QA / "R149_TYPOGRAPHY_SUCCESSORS_VERIFICATION_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
