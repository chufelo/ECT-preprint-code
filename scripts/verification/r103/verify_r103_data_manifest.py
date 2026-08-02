#!/usr/bin/env python3
"""Verify the public R103 data registry without rewriting any artifact.

The manifest separates committed, author-generated files from declared
external inputs.  External inputs must not appear in the public data tree;
their logical paths and hashes are owned by EXTERNAL_INPUTS.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPOSITORY_ROOT / "data/cosmology_r103"
MANIFEST = DATA_DIR / "MANIFEST_SHA256.json"
EXTERNAL_CONTRACT = REPOSITORY_ROOT / "EXTERNAL_INPUTS.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(EXTERNAL_CONTRACT.read_text(encoding="utf-8"))
    contract_by_path = {
        str(item["logical_repository_path"]): item
        for item in contract.get("inputs", [])
    }
    errors: list[dict[str, object]] = []

    declared_files = set(manifest.get("files", {}))
    actual_files = {
        path.relative_to(DATA_DIR).as_posix()
        for path in DATA_DIR.rglob("*")
        if path.is_file() and path != MANIFEST
    }
    if declared_files != actual_files:
        errors.append(
            {
                "type": "file-set-mismatch",
                "missing": sorted(declared_files - actual_files),
                "unregistered": sorted(actual_files - declared_files),
            }
        )

    verified_files = 0
    for relative, record in sorted(manifest.get("files", {}).items()):
        path = DATA_DIR / relative
        if not path.is_file():
            continue
        actual_hash = sha256(path)
        actual_bytes = path.stat().st_size
        if actual_hash != record.get("sha256") or actual_bytes != record.get("bytes"):
            errors.append(
                {
                    "type": "file-identity-mismatch",
                    "path": relative,
                    "expected_sha256": record.get("sha256"),
                    "actual_sha256": actual_hash,
                    "expected_bytes": record.get("bytes"),
                    "actual_bytes": actual_bytes,
                }
            )
        else:
            verified_files += 1

    verified_external = 0
    for name, record in sorted(manifest.get("external_inputs", {}).items()):
        logical = str(record.get("logical_repository_path", ""))
        public_path = REPOSITORY_ROOT / logical
        if public_path.exists():
            errors.append(
                {
                    "type": "external-input-was-redistributed",
                    "path": logical,
                }
            )
        owner = contract_by_path.get(logical)
        if owner is None:
            errors.append(
                {
                    "type": "external-input-missing-from-contract",
                    "path": logical,
                }
            )
            continue
        if (
            record.get("expected_sha256") != owner.get("expected_sha256")
            or record.get("redistributed") is not False
        ):
            errors.append(
                {
                    "type": "external-input-contract-mismatch",
                    "path": logical,
                    "manifest_hash": record.get("expected_sha256"),
                    "contract_hash": owner.get("expected_sha256"),
                }
            )
        else:
            verified_external += 1

    report = {
        "schema": "ect.r103.public-data-manifest-verification.v1",
        "status": "PASS" if not errors else "FAIL",
        "verified_committed_files": verified_files,
        "verified_declared_external_inputs": verified_external,
        "errors": errors,
        "scientific_status": (
            "manifest identity gate only; conditional R103 calculations retain "
            "their declared Level A/B/C/Open ceilings"
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
