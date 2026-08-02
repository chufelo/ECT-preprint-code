#!/usr/bin/env python3
"""Create an offline R190 pre-tag manifest or attest an existing local tag.

This tool never creates a commit or tag and never performs network access.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_ID = "R190"
PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = PACKAGE_DIR.parents[2]
CONTRACT_REL = "release/zenodo/R190/RELEASE_INPUT_CONTRACT.json"
VALIDATION_REL = (
    "release/zenodo/R190/validation/R190_RELEASE_VALIDATION_STATUS.json"
)
VALIDATOR_REL = "release/zenodo/R190/validate_release.py"
ALLOWED_ROLES = {
    "source-data",
    "extracted-data",
    "model-input",
    "generator",
    "verifier",
    "scientific-output",
    "figure-input",
    "interpretation",
}
PRIVATE_PATH_RE = re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\\\Users\\\\)")


class FreezeError(RuntimeError):
    """Fail-closed release-freeze error."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def write_canonical_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FreezeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FreezeError(f"JSON root must be an object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise FreezeError(f"unsafe repository path: {raw!r}")
    parsed = PurePosixPath(raw)
    if parsed.is_absolute() or raw.startswith("./") or ".." in parsed.parts:
        raise FreezeError(f"unsafe repository path: {raw!r}")
    normalised = parsed.as_posix()
    if normalised in {"", "."} or normalised != raw:
        raise FreezeError(f"non-canonical repository path: {raw!r}")
    return normalised


def resolve_under_root(root: Path, relative: str) -> Path:
    safe = safe_relative_path(relative)
    candidate = (root / PurePosixPath(safe)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise FreezeError(f"path escapes repository root: {relative}") from exc
    return candidate


def run_local(command: list[str], *, cwd: Path | None = None) -> bytes:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise FreezeError(
            f"local command failed: {' '.join(command)}"
            + (f" ({detail})" if detail else "")
        ) from exc
    return completed.stdout


def pdf_page_count(path: Path) -> int:
    errors: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        pages = len(PdfReader(str(path)).pages)
        if pages > 0:
            return pages
    except Exception as exc:  # pragma: no cover - runtime fallback
        errors.append(f"pypdf: {exc}")

    try:
        import fitz  # type: ignore

        with fitz.open(path) as document:
            pages = document.page_count
        if pages > 0:
            return pages
    except Exception as exc:  # pragma: no cover - runtime fallback
        errors.append(f"PyMuPDF: {exc}")

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        try:
            output = run_local([pdfinfo, str(path)]).decode(
                "utf-8", errors="replace"
            )
            match = re.search(r"^Pages:\s+(\d+)\s*$", output, re.MULTILINE)
            if match and int(match.group(1)) > 0:
                return int(match.group(1))
        except FreezeError as exc:  # pragma: no cover - runtime fallback
            errors.append(f"pdfinfo: {exc}")

    raise FreezeError(
        f"cannot determine a positive PDF page count for {path}; "
        + "; ".join(errors)
    )


def require_validation_pass(root: Path) -> None:
    validation = load_json(resolve_under_root(root, VALIDATION_REL))
    checks = validation.get("checks")
    if validation.get("overall_status") != "PASS":
        raise FreezeError(
            f"{VALIDATION_REL} is not accepting: overall_status must be PASS"
        )
    if not isinstance(checks, dict) or not checks:
        raise FreezeError(f"{VALIDATION_REL} has no check inventory")
    failing = sorted(key for key, value in checks.items() if value != "PASS")
    if failing:
        raise FreezeError(
            f"{VALIDATION_REL} contains non-PASS checks: {', '.join(failing)}"
        )


def require_pretag_gate(root: Path) -> None:
    validator = resolve_under_root(root, VALIDATOR_REL)
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(validator),
            "--repo-root",
            str(root),
            "--require-pretag-ready",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).strip()
        raise FreezeError(f"pre-tag readiness gate failed: {detail}")
    if "PASS_PRETAG_INPUTS_REVIEWED_NOT_FROZEN" not in completed.stdout:
        raise FreezeError("pre-tag readiness gate returned an unexpected verdict")


def validate_build_report(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required_zero = (
        "Errors: 0",
        "Undefined references: 0",
        "Undefined citations: 0",
        "Multiply-defined diagnostics: 0",
        "Rerun-required diagnostics: 0",
    )
    missing = [marker for marker in required_zero if marker not in text]
    if missing:
        raise FreezeError(
            f"build report {path.name} lacks accepting diagnostics: "
            + ", ".join(missing)
        )
    if "Validation gate: PASS" not in text and "validation gate: PASS" not in text:
        raise FreezeError(f"build report {path.name} lacks a PASS gate")
    if not re.search(r"^Pages:\s+\d+\s+\(was\s+\d+\)\s*$", text, re.MULTILINE):
        raise FreezeError(f"build report {path.name} lacks 'X pages (was Y)'")
    if PRIVATE_PATH_RE.search(text):
        raise FreezeError(f"build report {path.name} contains a private absolute path")


def artifact_records(root: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    configured = contract.get("required_artifacts")
    if not isinstance(configured, list) or not configured:
        raise FreezeError("contract required_artifacts must be a non-empty list")

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in configured:
        if not isinstance(item, dict):
            raise FreezeError("each required_artifacts entry must be an object")
        relative = safe_relative_path(item.get("path"))
        role = item.get("role")
        if role not in ALLOWED_ROLES:
            raise FreezeError(f"unsupported role for {relative}: {role!r}")
        if relative in seen:
            raise FreezeError(f"duplicate required artifact: {relative}")
        seen.add(relative)
        path = resolve_under_root(root, relative)
        if not path.is_file():
            raise FreezeError(f"required artifact is missing or not a file: {relative}")
        if relative.startswith("release/zenodo/R190/build_reports/") and relative.endswith(
            "-build.txt"
        ):
            validate_build_report(path)
        record: dict[str, Any] = {
            "bytes": path.stat().st_size,
            "path": relative,
            "role": role,
            "sha256": sha256_file(path),
        }
        if relative.lower().endswith(".pdf"):
            record["pages"] = pdf_page_count(path)
        records.append(record)
    return sorted(records, key=lambda value: value["path"])


def tool_version(command: str, args: list[str]) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    try:
        output = run_local([executable, *args]).decode("utf-8", errors="replace")
    except FreezeError:
        return None
    return output.strip().splitlines()[0] if output.strip() else None


def create_runtime_sidecar(root: Path) -> dict[str, Any]:
    return {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "package_id": PACKAGE_ID,
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "repository_root": str(root),
        "role": "runtime-sidecar",
        "scientific_digest_member": False,
        "tool_versions": {
            "bibtex": tool_version("bibtex", ["--version"]),
            "dot": tool_version("dot", ["-V"]),
            "git": tool_version("git", ["--version"]),
            "pdflatex": tool_version("pdflatex", ["--version"]),
        },
    }


def command_pretag(args: argparse.Namespace) -> None:
    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        raise FreezeError(f"repository root does not exist: {root}")
    contract_path = resolve_under_root(root, CONTRACT_REL)
    contract = load_json(contract_path)
    if contract.get("package_id") != PACKAGE_ID:
        raise FreezeError("release input contract has the wrong package_id")
    if contract.get("release_status") != "RELEASE_CANDIDATE_NOT_RELEASED":
        raise FreezeError("contract is not in reviewed pre-tag status")
    if contract.get("finalisation_policy", {}).get("network_access") != "forbidden":
        raise FreezeError("contract must forbid network access")

    require_validation_pass(root)
    require_pretag_gate(root)
    records = artifact_records(root, contract)
    digest = sha256_bytes(canonical_json_bytes(records))
    predecessor = contract.get("predecessor_evidence")
    if not isinstance(predecessor, dict):
        raise FreezeError("contract predecessor_evidence must be an object")

    manifest = {
        "aggregate_algorithm": "sha256(canonical artifact_records JSON)",
        "artifact_records": records,
        "git_commit": None,
        "git_tag": None,
        "manifest_self_excluded": True,
        "owner_id": PACKAGE_ID,
        "owner_root": ".",
        "predecessor_evidence_sha256": sha256_bytes(
            canonical_json_bytes(predecessor)
        ),
        "release_status": "LOCALLY_FROZEN_NOT_TAGGED_NOT_RELEASED",
        "runtime_sidecar_in_scientific_digest": False,
        "schema_version": "2.0",
        "scientific_payload_sha256": digest,
        "status": "LOCALLY FROZEN CANDIDATE",
    }

    output = Path(args.output).resolve()
    if output == contract_path:
        raise FreezeError("output cannot overwrite the release input contract")
    if args.runtime_sidecar and Path(args.runtime_sidecar).resolve() == output:
        raise FreezeError("manifest and runtime sidecar outputs must differ")
    write_canonical_json(output, manifest)
    if args.runtime_sidecar:
        write_canonical_json(
            Path(args.runtime_sidecar).resolve(), create_runtime_sidecar(root)
        )
    print("LOCALLY_FROZEN_CANDIDATE")
    print(f"artifacts={len(records)}")
    print(f"scientific_payload_sha256={digest}")
    print("network_access=NONE")


def git_object(root: Path, revision: str, relative: str) -> bytes:
    safe = safe_relative_path(relative)
    return run_local(["git", "-C", str(root), "show", f"{revision}:{safe}"])


def full_commit(root: Path, revision: str) -> str:
    value = run_local(
        ["git", "-C", str(root), "rev-parse", "--verify", f"{revision}^{{commit}}"]
    ).decode("ascii", errors="strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise FreezeError(f"Git did not resolve a full SHA-1 commit: {value!r}")
    return value


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise FreezeError(f"path must be inside repository root: {path}") from exc


def command_attest_tag(args: argparse.Namespace) -> None:
    root = Path(args.repo_root).resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", args.git_commit):
        raise FreezeError("--git-commit must be a full lowercase 40-character SHA")
    if not args.git_tag or args.git_tag.startswith("-") or ".." in args.git_tag:
        raise FreezeError("unsafe or empty --git-tag")

    commit = full_commit(root, args.git_commit)
    if commit != args.git_commit:
        raise FreezeError("--git-commit does not resolve to itself")
    tag_commit = full_commit(root, f"refs/tags/{args.git_tag}")
    if tag_commit != commit:
        raise FreezeError(
            f"tag {args.git_tag!r} resolves to {tag_commit}, not {commit}"
        )

    manifest_path = Path(args.pretag_manifest).resolve()
    manifest_rel = relative_to_root(root, manifest_path)
    manifest_bytes = manifest_path.read_bytes()
    committed_manifest = git_object(root, commit, manifest_rel)
    if committed_manifest != manifest_bytes:
        raise FreezeError("local pre-tag manifest differs from the tagged bytes")
    manifest = load_json(manifest_path)
    if manifest.get("status") != "LOCALLY FROZEN CANDIDATE":
        raise FreezeError("pre-tag manifest has an unexpected status")
    records = manifest.get("artifact_records")
    if not isinstance(records, list) or not records:
        raise FreezeError("pre-tag manifest has no artifact records")
    digest = sha256_bytes(canonical_json_bytes(records))
    if manifest.get("scientific_payload_sha256") != digest:
        raise FreezeError("pre-tag manifest aggregate digest is invalid")

    for record in records:
        if not isinstance(record, dict):
            raise FreezeError("invalid artifact record in pre-tag manifest")
        relative = safe_relative_path(record.get("path"))
        data = git_object(root, commit, relative)
        if len(data) != record.get("bytes") or sha256_bytes(data) != record.get(
            "sha256"
        ):
            raise FreezeError(f"tagged artifact differs from manifest: {relative}")

    attestation = {
        "artifact_count": len(records),
        "git_commit": commit,
        "git_tag": args.git_tag,
        "network_access": "NONE",
        "owner_id": PACKAGE_ID,
        "pretag_manifest_path": manifest_rel,
        "pretag_manifest_sha256": sha256_bytes(manifest_bytes),
        "release_status": "TAG_ATTESTED_NOT_RELEASED",
        "schema_version": "1.0",
        "scientific_payload_sha256": digest,
        "status": "TRACKED OWNER",
    }
    write_canonical_json(Path(args.output).resolve(), attestation)
    print("TAG_ATTESTED_NOT_RELEASED")
    print(f"git_commit={commit}")
    print(f"git_tag={args.git_tag}")
    print(f"scientific_payload_sha256={digest}")
    print("network_access=NONE")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    pretag = subparsers.add_parser(
        "pretag", help="freeze the reviewed local artifact set before tagging"
    )
    pretag.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    pretag.add_argument("--output", required=True)
    pretag.add_argument("--runtime-sidecar")
    pretag.set_defaults(function=command_pretag)

    attest = subparsers.add_parser(
        "attest-tag", help="bind an existing pre-tag manifest to a local Git tag"
    )
    attest.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    attest.add_argument("--pretag-manifest", required=True)
    attest.add_argument("--git-commit", required=True)
    attest.add_argument("--git-tag", required=True)
    attest.add_argument("--output", required=True)
    attest.set_defaults(function=command_attest_tag)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.function(args)
    except (FreezeError, OSError, UnicodeError) as exc:
        print(f"HOLD: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
