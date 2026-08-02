"""Fail-closed resolver for non-redistributed HRC inputs.

The public repository records logical paths and SHA-256 identities, but does
not ship the SPARC-origin payloads listed in ``EXTERNAL_INPUTS.json``.  A user
who has obtained the inputs under the upstream terms supplies a separate
directory with the same relative layout through ``ECT_EXTERNAL_INPUT_ROOT``.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath


ENVIRONMENT_VARIABLE = "ECT_EXTERNAL_INPUT_ROOT"


class ExternalInputError(RuntimeError):
    """Raised when a declared external input is absent or has drifted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contract_entries(repository_root: Path) -> dict[str, dict[str, object]]:
    contract_path = repository_root / "EXTERNAL_INPUTS.json"
    if not contract_path.is_file():
        raise ExternalInputError(
            f"MISSING_EXTERNAL_INPUT_CONTRACT: {contract_path.name} is absent"
        )
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    if payload.get("environment_variable") != ENVIRONMENT_VARIABLE:
        raise ExternalInputError(
            "INVALID_EXTERNAL_INPUT_CONTRACT: environment-variable owner drift"
        )
    entries = {
        str(item["logical_repository_path"]): item
        for item in payload.get("inputs", [])
    }
    if len(entries) != len(payload.get("inputs", [])):
        raise ExternalInputError(
            "INVALID_EXTERNAL_INPUT_CONTRACT: duplicate logical paths"
        )
    return entries


def declared_external_input_hashes(repository_root: Path) -> dict[str, str]:
    """Return the public contract's logical-path-to-hash map."""

    return {
        logical_path: str(entry["expected_sha256"])
        for logical_path, entry in _contract_entries(repository_root).items()
    }


def resolve_external_input(
    repository_root: Path,
    logical_path: str,
    expected_sha256: str | None = None,
) -> Path:
    """Resolve and verify one declared external input.

    Resolution never falls back to an in-repository copy.  This both prevents
    accidental redistribution and makes an incomplete public checkout fail
    with an actionable message instead of silently using a different file.
    """

    logical = PurePosixPath(logical_path)
    if logical.is_absolute() or ".." in logical.parts or not logical.parts:
        raise ExternalInputError(f"UNSAFE_EXTERNAL_INPUT_PATH: {logical_path}")

    entries = _contract_entries(repository_root)
    entry = entries.get(logical_path)
    if entry is None:
        raise ExternalInputError(
            f"UNDECLARED_EXTERNAL_INPUT: {logical_path} is not in EXTERNAL_INPUTS.json"
        )

    configured = os.environ.get(ENVIRONMENT_VARIABLE)
    if not configured:
        raise ExternalInputError(
            "MISSING_EXTERNAL_INPUT_ROOT: set ECT_EXTERNAL_INPUT_ROOT to a "
            "directory containing the declared logical paths; see "
            "EXTERNAL_INPUTS.json"
        )
    external_root = Path(configured).expanduser().resolve()
    if not external_root.is_dir():
        raise ExternalInputError(
            f"INVALID_EXTERNAL_INPUT_ROOT: {ENVIRONMENT_VARIABLE} is not a directory"
        )

    candidate = (external_root / Path(*logical.parts)).resolve()
    if candidate != external_root and external_root not in candidate.parents:
        raise ExternalInputError(f"EXTERNAL_INPUT_ESCAPES_ROOT: {logical_path}")
    if not candidate.is_file():
        raise ExternalInputError(
            f"MISSING_EXTERNAL_INPUT: {logical_path}; place it below "
            f"{ENVIRONMENT_VARIABLE} with the declared relative path"
        )

    contract_hash = str(entry.get("expected_sha256", ""))
    if len(contract_hash) != 64:
        raise ExternalInputError(
            f"INVALID_EXTERNAL_INPUT_CONTRACT_HASH: {logical_path}"
        )
    if expected_sha256 is not None and contract_hash != expected_sha256:
        raise ExternalInputError(
            f"EXTERNAL_INPUT_OWNER_DRIFT: {logical_path}; script/contract hash mismatch"
        )
    actual = _sha256(candidate)
    if actual != contract_hash:
        raise ExternalInputError(
            f"EXTERNAL_INPUT_HASH_MISMATCH: {logical_path}: "
            f"{actual} != {contract_hash}"
        )
    return candidate
