#!/usr/bin/env python3
"""Verify the proposal-only R114 finite-body scalar-gate figure family."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


EXPECTED = {
    "candidate_tex": "549992e9d48fc2fa716325d249b96f53cf4092f10dab66030dc3cf5f72e1367a",
    "r113_manifest": "5b11dae4993190ab1c0ae0f5e2783638dc7f445c757208c953904d5e19adf806",
    "r114_manifest": "b4fa7b018aab10793e2285c34e0efd6eab00b551e2e27c25f27f84c4a00cf7b7",
    "producer": "b63770e7ef354d8296214fce409b1c40edd0d629e0ee16843ddc9eae59c61a5b",
    "redteam": "d5e00cefa6c68b625d33f935c031a374f1cc51094a5a4ebc014e6b040e889da7",
}
STEM = "r114_finitebody_scalar_gates"
PREVIEWS = ("colour", "grayscale", "protanopia", "deuteranopia", "tritanopia")
PDF_TOKENS = (
    "R114 finite-body scalar gates",
    "Fixed-metric BVP",
    "Three tail estimators (not averaged)",
    "all Ξbody",
    "not physical body sensitivity",
    "not coupled metric",
    "not Cassini/WEP/full PPN prediction",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a: float, b: float, tolerance: float = 5e-13) -> bool:
    return math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance)


def run_renderer(
    renderer: Path,
    candidate_tex: Path,
    r113_manifest: Path,
    r114_manifest: Path,
    producer: Path,
    redteam: Path,
    output_dir: Path,
    qa_dir: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(renderer),
            "--candidate-tex", str(candidate_tex),
            "--r113-manifest", str(r113_manifest),
            "--r114-manifest", str(r114_manifest),
            "--producer", str(producer),
            "--redteam", str(redteam),
            "--output-dir", str(output_dir),
            "--qa-dir", str(qa_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--candidate-tex", required=True, type=Path)
    parser.add_argument("--r113-manifest", required=True, type=Path)
    parser.add_argument("--r114-manifest", required=True, type=Path)
    parser.add_argument("--producer", required=True, type=Path)
    parser.add_argument("--redteam", required=True, type=Path)
    parser.add_argument("--renderer", required=True, type=Path)
    parser.add_argument("--figure-dir", required=True, type=Path)
    parser.add_argument("--qa-dir", required=True, type=Path)
    parser.add_argument("--claim-map", required=True, type=Path)
    parser.add_argument("--registry-delta", required=True, type=Path)
    parser.add_argument("--proposed-caption", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    checks: dict[str, bool] = {}
    hashes: dict[str, str] = {}
    for name, path in (
        ("candidate_tex", args.candidate_tex),
        ("r113_manifest", args.r113_manifest),
        ("r114_manifest", args.r114_manifest),
        ("producer", args.producer),
        ("redteam", args.redteam),
    ):
        actual = sha256(path) if path.is_file() else "MISSING"
        hashes[f"input:{name}"] = actual
        checks[f"input_hash:{name}"] = actual == EXPECTED[name]

    candidate_text = args.candidate_tex.read_text(encoding="utf-8")
    exact_tokens = (
        "10 & 0.761419 & 0.888498",
        "100 & 0.537185 & 0.451047",
        r"\(10^3\) & 0.253502 & 0.101308",
        r"\(10^4\) & 0.102100 & 0.0147107",
        "0.006399711753",
        "0.006393895852",
        "0.006372442154",
        r"Earth & \(2.54\times10^{-22}\) & \(2.09\times10^{-14}\)",
        r"Sun & \(2.78\times10^{-20}\) & \(6.36\times10^{-11}\)",
        r"Jupiter & \(2.79\times10^{-21}\) & \(6.05\times10^{-13}\)",
        r"Milky-Way mean within 15 kpc & \(1.85\times10^{-8}\) & \(5.74\times10^{-12}\)",
        r"cluster mean within 1 Mpc & \(1.23\times10^{-6}\) & \(1.51\times10^{-10}\)",
    )
    for token in exact_tokens:
        checks[f"candidate_exact:{token}"] = candidate_text.count(token) == 1

    values = [0.006399711753, 0.006393895852, 0.006372442154]
    checks["estimator_absolute_spread"] = close(max(values) - min(values), 0.000027269599)
    checks["estimator_relative_spread_percent"] = close(
        100.0 * (max(values) - min(values)) / min(values),
        0.4279301144,
        tolerance=2e-10,
    )

    pdf = args.figure_dir / f"{STEM}.pdf"
    png = args.figure_dir / f"{STEM}.png"
    checks["pdf_exists"] = pdf.is_file()
    checks["png_exists"] = png.is_file()
    if pdf.is_file():
        reader = PdfReader(str(pdf))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        checks["pdf_one_page"] = len(reader.pages) == 1
        for token in PDF_TOKENS:
            checks[f"pdf_text:{token}"] = token in text
        hashes[f"figure:{pdf.name}"] = sha256(pdf)
    if png.is_file():
        with Image.open(png) as image:
            dimensions = image.size
        checks["png_min_dimensions"] = dimensions[0] >= 3000 and dimensions[1] >= 900
        hashes[f"figure:{png.name}"] = sha256(png)
        for suffix in PREVIEWS:
            path = args.qa_dir / f"{STEM}_{suffix}.png"
            checks[f"preview_exists:{suffix}"] = path.is_file()
            if path.is_file():
                with Image.open(path) as preview:
                    checks[f"preview_dimensions:{suffix}"] = preview.size == dimensions
                hashes[f"preview:{path.name}"] = sha256(path)

    literal_guard = (
        "Fixed-metric scalar BVP / dimensional gate only; not physical body "
        "sensitivity, not coupled metric, not Cassini/WEP/full PPN prediction."
    )
    caption_text = args.proposed_caption.read_text(encoding="utf-8")
    checks["caption_literal_guard"] = literal_guard in caption_text
    claim_map = json.loads(args.claim_map.read_text(encoding="utf-8"))
    checks["claim_map_zero_insertions"] = claim_map.get("active_tex_insertions") == 0
    checks["claim_map_literal_guard"] = literal_guard in json.dumps(claim_map, ensure_ascii=False)
    registry_text = args.registry_delta.read_text(encoding="utf-8")
    checks["registry_zero_insertions"] = ",0," in registry_text
    checks["registry_proposal_only"] = "PROPOSAL_ONLY" in registry_text

    active_documents = (
        args.workspace_root / "LaTex/ECT_preprint.tex",
        args.workspace_root / "LaTex/companion/ECT_companion.tex",
        args.workspace_root / "LaTex/companion/ECT_companion_ru.tex",
        args.workspace_root / "LaTex/summary/ECT_summary.tex",
        args.workspace_root / "LaTex/summary/ru/ECT_summary_ru.tex",
    )
    basename = f"{STEM}.pdf"
    checks["zero_active_tex_insertions"] = all(
        path.read_text(encoding="utf-8").count(basename) == 0 for path in active_documents
    )

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("files", [])
    checks["manifest_schema"] = (
        manifest.get("schema") == "ECT_R114_finitebody_figure_manifest_v1"
    )
    checks["manifest_zero_insertions"] = manifest.get("active_tex_insertions") == 0
    checks["manifest_unique_paths"] = len({entry.get("path") for entry in entries}) == len(entries)
    manifest_records = []
    for entry in entries:
        relative = entry.get("path", "")
        path = args.workspace_root / relative
        actual = sha256(path) if path.is_file() else "MISSING"
        checks[f"manifest_file:{relative}"] = (
            actual == entry.get("sha256") and (path.stat().st_size if path.is_file() else -1) == entry.get("bytes")
        )
        manifest_records.append(f"{relative}\0{entry.get('sha256')}\n")
    aggregate = hashlib.sha256("".join(sorted(manifest_records)).encode("utf-8")).hexdigest()
    checks["manifest_aggregate"] = aggregate == manifest.get("aggregate_sha256")

    with tempfile.TemporaryDirectory(prefix="r114_finitebody_figure_replay_") as temp:
        replay_root = Path(temp)
        replay_figures = replay_root / "figures"
        replay_qa = replay_root / "qa"
        run_renderer(
            args.renderer,
            args.candidate_tex,
            args.r113_manifest,
            args.r114_manifest,
            args.producer,
            args.redteam,
            replay_figures,
            replay_qa,
        )
        for extension in ("pdf", "png"):
            frozen = args.figure_dir / f"{STEM}.{extension}"
            replay = replay_figures / f"{STEM}.{extension}"
            checks[f"byte_replay:{extension}"] = (
                frozen.is_file() and replay.is_file() and sha256(frozen) == sha256(replay)
            )
        for suffix in PREVIEWS:
            frozen = args.qa_dir / f"{STEM}_{suffix}.png"
            replay = replay_qa / f"{STEM}_{suffix}.png"
            checks[f"byte_replay:{suffix}"] = (
                frozen.is_file() and replay.is_file() and sha256(frozen) == sha256(replay)
            )

    failed = sorted(key for key, value in checks.items() if not value)
    report = {
        "schema": "R114_finitebody_scalar_gate_figure_verification_v1",
        "status": "PASS" if not failed else "FAIL",
        "scientific_scope": (
            "Fixed-metric scalar BVP and dimensional gate only; physical body "
            "sensitivity, coupled metric, Cassini, WEP and full PPN remain uncomputed."
        ),
        "checks": checks,
        "failed_checks": failed,
        "hashes": hashes,
        "all_checks_pass": not failed,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if not failed else 1)


if __name__ == "__main__":
    main()
