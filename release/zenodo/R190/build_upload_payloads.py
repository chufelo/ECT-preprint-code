#!/usr/bin/env python3
"""Stage the two R190 manuscript PDFs from an attested local Git commit.

The tool is offline. It refuses to overwrite a non-empty output directory and
does not create commits, tags, remote releases, Zenodo drafts, or uploads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_ID = "R190"
PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = PACKAGE_DIR.parents[2]
ALLOWLIST_REL = "release/zenodo/R190/ZENODO_UPLOAD_ALLOWLIST.json"
METADATA_RELS = (
    "release/zenodo/R190/PREPRINT_ZENODO_METADATA.json",
    "release/zenodo/R190/COMPANION_ZENODO_METADATA.json",
)


class PayloadError(RuntimeError):
    """Fail-closed payload staging error."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PayloadError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PayloadError(f"JSON root must be an object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(raw: Any) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise PayloadError(f"unsafe repository path: {raw!r}")
    value = PurePosixPath(raw)
    if value.is_absolute() or ".." in value.parts or value.as_posix() != raw:
        raise PayloadError(f"unsafe repository path: {raw!r}")
    return raw


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PayloadError(f"path is outside repository root: {path}") from exc


def git_bytes(root: Path, commit: str, relative: str) -> bytes:
    safe = safe_path(relative)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{safe}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise PayloadError(
            f"cannot read tagged object {safe}: {detail or exc}"
        ) from exc
    return result.stdout


def resolve_commit(root: Path, revision: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", f"{revision}^{{commit}}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PayloadError(f"cannot resolve Git revision {revision!r}: {exc}") from exc
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise PayloadError(f"Git returned a non-full commit: {value!r}")
    return value


def prepare_output(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise PayloadError(f"output exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise PayloadError(f"output directory is not empty: {path}")
    else:
        path.mkdir(parents=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--pretag-manifest", required=True)
    parser.add_argument("--tag-attestation", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        root = Path(args.repo_root).resolve()
        manifest_path = Path(args.pretag_manifest).resolve()
        attestation_path = Path(args.tag_attestation).resolve()
        manifest = load_json(manifest_path)
        attestation = load_json(attestation_path)
        allowlist = load_json(root / ALLOWLIST_REL)

        if manifest.get("owner_id") != PACKAGE_ID:
            raise PayloadError("pre-tag manifest has the wrong owner_id")
        if manifest.get("status") != "LOCALLY FROZEN CANDIDATE":
            raise PayloadError("pre-tag manifest does not have frozen-candidate status")
        manifest_bytes = manifest_path.read_bytes()
        if attestation.get("owner_id") != PACKAGE_ID:
            raise PayloadError("tag attestation has the wrong owner_id")
        if attestation.get("status") != "TRACKED OWNER":
            raise PayloadError("tag attestation does not establish a tracked owner")
        if attestation.get("release_status") != "TAG_ATTESTED_NOT_RELEASED":
            raise PayloadError("tag attestation has the wrong release boundary")
        if attestation.get("network_access") != "NONE":
            raise PayloadError("tag attestation must state network_access=NONE")
        if attestation.get("pretag_manifest_sha256") != sha256_bytes(manifest_bytes):
            raise PayloadError("tag attestation does not bind this pre-tag manifest")
        if attestation.get("scientific_payload_sha256") != manifest.get(
            "scientific_payload_sha256"
        ):
            raise PayloadError("tag attestation scientific digest mismatch")

        commit = attestation.get("git_commit")
        tag = attestation.get("git_tag")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise PayloadError("tag attestation has no full Git commit")
        if not isinstance(tag, str) or not tag or tag.startswith("-") or ".." in tag:
            raise PayloadError("tag attestation has an unsafe Git tag")
        if resolve_commit(root, commit) != commit:
            raise PayloadError("attested commit does not resolve to itself")
        if resolve_commit(root, f"refs/tags/{tag}") != commit:
            raise PayloadError("attested tag does not resolve to attested commit")

        manifest_rel = relative_to_root(root, manifest_path)
        if attestation.get("pretag_manifest_path") != manifest_rel:
            raise PayloadError("tag attestation manifest path mismatch")
        if git_bytes(root, commit, manifest_rel) != manifest_bytes:
            raise PayloadError("tagged pre-tag manifest differs from local manifest")

        for relative in METADATA_RELS:
            metadata = load_json(root / relative)
            if metadata.get("new_version_record_id") is not None:
                raise PayloadError(f"{relative} invents a new record ID")
            if metadata.get("new_version_doi") is not None:
                raise PayloadError(f"{relative} invents a new version DOI")

        records = manifest.get("artifact_records")
        if not isinstance(records, list) or not records:
            raise PayloadError("pre-tag manifest has no artifact records")
        by_path: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict):
                raise PayloadError("pre-tag manifest contains a non-object record")
            path = safe_path(record.get("path"))
            if path in by_path:
                raise PayloadError(f"duplicate manifest path: {path}")
            by_path[path] = record

        allow_records = allowlist.get("records")
        if not isinstance(allow_records, dict) or set(allow_records) != {
            "preprint",
            "companion",
        }:
            raise PayloadError("allowlist must contain exactly two manuscript records")

        planned: list[tuple[str, str, dict[str, Any]]] = []
        for name in ("preprint", "companion"):
            record = allow_records[name]
            if not isinstance(record, dict):
                raise PayloadError(f"{name} allowlist record must be an object")
            uploads = record.get("allowed_uploads")
            if record.get("maximum_file_count") != 1 or not isinstance(uploads, list) or len(
                uploads
            ) != 1:
                raise PayloadError(f"{name} allowlist must contain exactly one upload")
            upload = uploads[0]
            source_path = safe_path(upload.get("manifest_path"))
            basename = upload.get("basename")
            if not isinstance(basename, str) or PurePosixPath(basename).name != basename:
                raise PayloadError(f"unsafe basename for {name}")
            if upload.get("media_type") != "application/pdf" or upload.get(
                "sha256"
            ) is not None:
                raise PayloadError(f"invalid draft allowlist fields for {name}")
            if source_path not in by_path:
                raise PayloadError(f"allowlisted PDF absent from manifest: {source_path}")
            target = f"{name}/{basename}"
            planned.append((source_path, target, by_path[source_path]))

        if {item[0] for item in planned} != {
            "ECT_preprint.pdf",
            "companion/ECT_companion.pdf",
        }:
            raise PayloadError("payload paths differ from the fixed two-PDF policy")

        output = Path(args.output).resolve()
        prepare_output(output)
        checksum_lines: list[str] = []
        for source_path, target_path, record in planned:
            data = git_bytes(root, commit, source_path)
            digest = sha256_bytes(data)
            if len(data) != record.get("bytes") or digest != record.get("sha256"):
                raise PayloadError(f"tagged PDF differs from manifest: {source_path}")
            destination = output / PurePosixPath(target_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            checksum_lines.append(f"{digest}  {target_path}")
        (output / "PAYLOAD_SHA256SUMS").write_text(
            "\n".join(sorted(checksum_lines)) + "\n", encoding="utf-8"
        )
    except (PayloadError, OSError, UnicodeError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2

    print("PAYLOADS_STAGED_FROM_TAG_ATTESTED_COMMIT")
    print("file_count=2")
    print("network_access=NONE")
    print("upload_performed=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
