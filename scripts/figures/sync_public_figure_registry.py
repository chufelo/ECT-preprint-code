#!/usr/bin/env python3
"""Synchronise the public figure registries after a governed figure rebuild.

This tool is intentionally narrow.  It reads the deterministic
R190_PUBLIC_STATUS_SCHEMATICS_v1 manifest, updates only the registered assets
listed there, refreshes source-line and insertion-token locations for the
fixed English publication chain, and refreezes the public figure-owner
manifest.  It never edits a manuscript or a figure binary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
CSV_PATH = ROOT / "FIGURE_REGISTRY.csv"
JSON_PATH = ROOT / "FIGURE_REGISTRY.json"
SCHEMATIC_MANIFEST = (
    ROOT / "data/verification/R190_PUBLIC_STATUS_SCHEMATICS_v1.json"
)
OWNER_MANIFEST = (
    ROOT / "data/figures_r190/R190_PUBLIC_FIGURE_OWNER_MANIFEST_v1.json"
)
VERIFIER = ROOT / "scripts/figures/verify_public_figure_registry.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def logical(path: str) -> str:
    return path if path.startswith("LaTex/") else f"LaTex/{path}"


def manifest_record(path: str, role: str) -> dict[str, Any]:
    physical = ROOT / path.removeprefix("LaTex/")
    if not physical.is_file():
        raise FileNotFoundError(physical)
    public_path = path.removeprefix("LaTex/")
    return {
        "bytes": physical.stat().st_size,
        "original_workspace_path": path,
        "public_repository_path": public_path,
        "registry_path": path,
        "role": role,
        "sha256": sha256(physical),
    }


def aggregate_records(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        f"{record['registry_path']}\0{record['sha256']}\0{record['role']}\n"
        for record in records
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="record completed standalone and owning-page visual review",
    )
    args = parser.parse_args()

    verifier = load_module("ect_public_figure_verifier", VERIFIER)
    schematic = json.loads(SCHEMATIC_MANIFEST.read_text(encoding="utf-8"))
    if schematic.get("status") != "PASS_PRESENTATION_ONLY":
        raise RuntimeError("schematic manifest is not PASS_PRESENTATION_ONLY")
    output_map = {
        logical(record["path"]): record
        for record in schematic.get("outputs", [])
    }
    if len(output_map) != 7:
        raise RuntimeError(f"expected 7 governed outputs, found {len(output_map)}")

    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise RuntimeError("empty CSV header")

    occurrences, document_hashes = verifier.scan_documents(ROOT, [ROOT])
    if any(item.get("error") or not item.get("resolved") for item in occurrences):
        raise RuntimeError("English figure insertion scan contains unresolved entries")

    generator_path = "LaTex/scripts/figures/build_public_status_schematics.py"
    generator_hash = sha256(ROOT / generator_path.removeprefix("LaTex/"))
    data_path = "LaTex/data/verification/R190_PUBLIC_STATUS_SCHEMATICS_v1.json"
    data_hash = sha256(SCHEMATIC_MANIFEST)
    changed = 0
    for row in rows:
        asset = row["resolved_current_path"]
        matches = [item for item in occurrences if item.get("resolved") == asset]
        row["source_line"] = ";".join(str(item["line"]) for item in matches)
        row["insertion_token"] = ";".join(item["include"] for item in matches)
        if asset not in output_map:
            continue
        record = output_map[asset]
        row["output_sha256"] = record["sha256"]
        row["generator_paths"] = generator_path
        row["generator_sha256"] = generator_hash
        row["data_paths"] = data_path
        row["data_sha256"] = data_hash
        row["scientific_owner"] = (
            "R190 publication-neutral presentation successor; scientific "
            "payload inherited from the frozen R149/R181 owners"
        )
        row["render_or_verify_command"] = (
            "SOURCE_DATE_EPOCH=1785628800 python3 "
            "scripts/figures/build_public_status_schematics.py; "
            "python3 scripts/figures/verify_public_figure_registry.py "
            "--root . --registry FIGURE_REGISTRY.csv "
            "--json-registry FIGURE_REGISTRY.json --strict-palette "
            "--strict-provenance"
        )
        row["current_disposition"] = (
            "CURRENT ENGLISH PUBLICATION ASSET; lifecycle-neutral visible "
            "title; exact hash registered; scientific ceiling unchanged"
        )
        row["provenance_basis"] = (
            "R190_PUBLIC_STATUS_SCHEMATICS_v1; frozen R149/R181 scientific "
            "and layout sources retained; lifecycle title/metadata only"
        )
        if args.reviewed:
            row["grayscale_cvd_verdict"] = (
                "PASS R190: status remains redundant with literal text, "
                "luminance, border and line style; title-only successor"
            )
            row["human_review_verdict"] = (
                "PASS R190: standalone full-resolution and compiled "
                "owning-page review"
            )
            row["pending_review"] = "PASS"
        else:
            row["human_review_verdict"] = (
                "PENDING R190: standalone and compiled owning-page review"
            )
            row["pending_review"] = "PENDING R190 visual review"
        changed += 1
    if changed != 7:
        raise RuntimeError(f"expected 7 registry updates, found {changed}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    owner = json.loads(OWNER_MANIFEST.read_text(encoding="utf-8"))
    records_by_path = {
        record["public_repository_path"]: record
        for record in owner["records"]
    }
    roles = {
        generator_path: "figure_generator",
        data_path: "figure_data",
    }
    for logical_path in output_map:
        roles[logical_path] = "figure_asset"
    for logical_path, role in roles.items():
        record = manifest_record(logical_path, role)
        records_by_path[record["public_repository_path"]] = record
    records = sorted(records_by_path.values(), key=lambda item: item["registry_path"])
    owner["candidate_document_hashes"] = document_hashes
    owner["records"] = records
    owner["record_count"] = len(records)
    owner["aggregate_sha256"] = aggregate_records(records)
    OWNER_MANIFEST.write_text(stable_json(owner), encoding="utf-8")

    registry_json = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    registry_json["candidate_document_hashes"] = document_hashes
    registry_json["english_insertions"] = len(occurrences)
    registry_json["figure_owner_manifest"] = (
        "LaTex/data/figures_r190/R190_PUBLIC_FIGURE_OWNER_MANIFEST_v1.json"
    )
    registry_json["figure_owner_manifest_sha256"] = sha256(OWNER_MANIFEST)
    registry_json["row_count"] = len(rows)
    registry_json["rows"] = rows
    registry_json["source_lines_synchronized"] = True
    registry_json["unique_resolved_assets"] = len(
        {item["resolved"] for item in occurrences}
    )
    JSON_PATH.write_text(stable_json(registry_json), encoding="utf-8")

    result = {
        "status": "PASS",
        "reviewed": args.reviewed,
        "registry_rows": len(rows),
        "governed_rows_updated": changed,
        "english_insertions": len(occurrences),
        "document_hashes": document_hashes,
        "csv_sha256": sha256(CSV_PATH),
        "json_sha256": sha256(JSON_PATH),
        "owner_manifest_sha256": sha256(OWNER_MANIFEST),
        "owner_manifest_records": len(records),
    }
    print(stable_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
