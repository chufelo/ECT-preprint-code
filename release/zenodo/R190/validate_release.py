#!/usr/bin/env python3
"""Offline, fail-closed validation for the R190 successor release package."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_ID = "R190"
DRAFT_STATUS = "DRAFT_NOT_TAGGED_NOT_RELEASED"
REVIEWED_STATUS = "RELEASE_CANDIDATE_NOT_RELEASED"
PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = PACKAGE_DIR.parents[2]
JSON_PATHS = {
    "preprint": "release/zenodo/R190/PREPRINT_ZENODO_METADATA.json",
    "companion": "release/zenodo/R190/COMPANION_ZENODO_METADATA.json",
    "snapshot": "release/zenodo/R190/KNOWN_RECORDS_SNAPSHOT.json",
    "allowlist": "release/zenodo/R190/ZENODO_UPLOAD_ALLOWLIST.json",
    "contract": "release/zenodo/R190/RELEASE_INPUT_CONTRACT.json",
    "validation": (
        "release/zenodo/R190/validation/R190_RELEASE_VALIDATION_STATUS.json"
    ),
}
EXPECTED = {
    "preprint": {
        "concept_doi": "10.5281/zenodo.18917929",
        "previous_latest_record_id": 21560326,
        "previous_latest_version_doi": "10.5281/zenodo.21560326",
        "relation_doi": "10.5281/zenodo.19430795",
        "relation": "isSupplementedBy",
        "pdf_path": "ECT_preprint.pdf",
        "pdf_basename": "ECT_preprint.pdf",
    },
    "companion": {
        "concept_doi": "10.5281/zenodo.19430795",
        "previous_latest_record_id": 21560220,
        "previous_latest_version_doi": "10.5281/zenodo.21560220",
        "relation_doi": "10.5281/zenodo.18917929",
        "relation": "isSupplementTo",
        "pdf_path": "companion/ECT_companion.pdf",
        "pdf_basename": "ECT_companion.pdf",
    },
}
EXPECTED_R189_SOURCES = {
    "ECT_preprint.tex": "495f37d40ef9243a96cbcc0de86fc6df3f3960733971383823131449aa6f9e63",
    "companion/ECT_companion.tex": "4521925573be588e024247d55b883b44ad5adc579365e81c068a215e79c326a1",
    "references.bib": "ea598e9f23b927b475c91f9fa9327845dd6a083b8c621921caaa59cab3944000",
    "summary/ECT_summary.tex": "db111cf6f3655beee8ebfbf541ff416b98b5ba37588b37b0e2acc38729d59f95",
}
REQUIRED_OWNER_PATHS = {
    "ECT_preprint.tex",
    "references.bib",
    "companion/ECT_companion.tex",
    "summary/ECT_summary.tex",
    "ECT_preprint.pdf",
    "companion/ECT_companion.pdf",
    "summary/ECT_summary.pdf",
    "ECT_preprint.bbl",
    "companion/ECT_companion.bbl",
    "summary/ECT_summary.bbl",
    "release/zenodo/R190/build_reports/preprint-build.txt",
    "release/zenodo/R190/build_reports/companion-build.txt",
    "release/zenodo/R190/build_reports/summary-build.txt",
    "release/zenodo/R190/validation/R190_RELEASE_VALIDATION_STATUS.json",
}
FORBIDDEN_OVERCLAIMS = (
    "pes proves quantum mechanics",
    "pes derives the born rule",
    "pes derives s_0",
    "all record channels share one universal scalar bath",
    "compact phase winding is the universal origin",
    "decoherence alone selects one ontologically actual outcome",
    "1.0014 is an experimental sum rule",
)


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative_path(raw: Any, errors: list[str], label: str) -> str | None:
    if not isinstance(raw, str) or not raw or "\\" in raw:
        errors.append(f"{label}: unsafe path {raw!r}")
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("./") or ".." in path.parts:
        errors.append(f"{label}: unsafe path {raw!r}")
        return None
    if path.as_posix() != raw or raw in {"", "."}:
        errors.append(f"{label}: non-canonical path {raw!r}")
        return None
    return raw


def under_root(root: Path, relative: str) -> Path:
    path = (root / PurePosixPath(relative)).resolve()
    path.relative_to(root)
    return path


def load_json(root: Path, relative: str, errors: list[str]) -> dict[str, Any]:
    path = under_root(root, relative)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"{relative}: cannot read JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{relative}: JSON root must be an object")
        return {}
    return value


def validate_statuses(
    documents: dict[str, dict[str, Any]], *, release_ready: bool, errors: list[str]
) -> None:
    expected = REVIEWED_STATUS if release_ready else DRAFT_STATUS
    for name, document in documents.items():
        if document.get("package_id") != PACKAGE_ID:
            errors.append(f"{name}: package_id must be {PACKAGE_ID}")
        if document.get("release_status") != expected:
            errors.append(f"{name}: release_status must be {expected}")


def validate_metadata(
    name: str,
    document: dict[str, Any],
    *,
    release_ready: bool,
    errors: list[str],
) -> None:
    expected = EXPECTED[name]
    for key in ("concept_doi", "previous_latest_record_id", "previous_latest_version_doi"):
        if document.get(key) != expected[key]:
            errors.append(f"{name}: unexpected {key}")
    if document.get("new_version_record_id") is not None:
        errors.append(f"{name}: new_version_record_id must remain null pre-draft")
    if document.get("new_version_doi") is not None:
        errors.append(f"{name}: new_version_doi must remain null pre-draft")

    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{name}: metadata must be an object")
        return
    fixed = {
        "upload_type": "publication",
        "publication_type": "preprint",
        "access_right": "open",
        "license": "cc-by-4.0",
        "language": "eng",
    }
    for key, value in fixed.items():
        if metadata.get(key) != value:
            errors.append(f"{name}: metadata.{key} must be {value!r}")
    creators = metadata.get("creators")
    if creators != [
        {"name": "Blagovidov, Valeriy", "orcid": "0009-0008-6707-7068"}
    ]:
        errors.append(f"{name}: creator/ORCID does not match the owner")

    relations = metadata.get("related_identifiers")
    expected_relation = [
        {
            "identifier": expected["relation_doi"],
            "relation": expected["relation"],
            "resource_type": "publication-preprint",
        }
    ]
    if relations != expected_relation:
        errors.append(f"{name}: reciprocal relation is incorrect")

    version = metadata.get("version")
    publication_date = metadata.get("publication_date")
    if release_ready:
        if not isinstance(version, str) or not version.strip():
            errors.append(f"{name}: reviewed public version is required")
        elif version.strip().lower() in {"r190", "draft", "tbd", "pending"}:
            errors.append(f"{name}: internal/draft identifier is not a public version")
        if not isinstance(publication_date, str):
            errors.append(f"{name}: reviewed publication_date is required")
        else:
            try:
                dt.date.fromisoformat(publication_date)
            except ValueError:
                errors.append(f"{name}: publication_date must be YYYY-MM-DD")
    elif version is not None or publication_date is not None:
        errors.append(f"{name}: draft version and publication_date must both be null")

    title = metadata.get("title")
    description = metadata.get("description")
    keywords = metadata.get("keywords")
    if not isinstance(title, str) or len(title.strip()) < 20:
        errors.append(f"{name}: title is missing or implausibly short")
    if not isinstance(description, str) or len(description.strip()) < 200:
        errors.append(f"{name}: description is missing or implausibly short")
    if not isinstance(keywords, list) or len(keywords) < 5:
        errors.append(f"{name}: at least five keywords are required")
    prose = f"{title or ''}\n{description or ''}".lower()
    for forbidden in FORBIDDEN_OVERCLAIMS:
        if forbidden in prose:
            errors.append(f"{name}: forbidden overclaim found: {forbidden!r}")


def validate_snapshot(snapshot: dict[str, Any], errors: list[str]) -> None:
    observation = snapshot.get("observation")
    if not isinstance(observation, dict):
        errors.append("snapshot: observation must be an object")
    else:
        if observation.get("observed_on") != "2026-08-01":
            errors.append("snapshot: observed_on must preserve the verified date")
        if observation.get("network_write_performed") is not False:
            errors.append("snapshot: network_write_performed must be false")
        sources = observation.get("sources")
        if not isinstance(sources, list) or len(sources) != 2:
            errors.append("snapshot: exactly two read-only source URLs are required")

    records = snapshot.get("records")
    if not isinstance(records, dict):
        errors.append("snapshot: records must be an object")
        return
    for name, expected in EXPECTED.items():
        record = records.get(name)
        if not isinstance(record, dict):
            errors.append(f"snapshot: missing {name} record")
            continue
        checks = {
            "concept_doi": expected["concept_doi"],
            "latest_record_id": expected["previous_latest_record_id"],
            "latest_version_doi": expected["previous_latest_version_doi"],
            "latest_publication_date": "2026-07-25",
            "license": "cc-by-4.0",
        }
        for key, value in checks.items():
            if record.get(key) != value:
                errors.append(f"snapshot: {name}.{key} is incorrect")
    new_ids = snapshot.get("new_version_identifiers")
    if not isinstance(new_ids, dict):
        errors.append("snapshot: new_version_identifiers must be an object")
    else:
        for key in (
            "preprint_record_id",
            "preprint_version_doi",
            "companion_record_id",
            "companion_version_doi",
        ):
            if new_ids.get(key) is not None:
                errors.append(f"snapshot: {key} must remain null pre-draft")


def validate_allowlist(allowlist: dict[str, Any], errors: list[str]) -> None:
    if allowlist.get("policy") != "fail_closed":
        errors.append("allowlist: policy must be fail_closed")
    records = allowlist.get("records")
    if not isinstance(records, dict) or set(records) != {"preprint", "companion"}:
        errors.append("allowlist: records must be exactly preprint and companion")
        return
    for name, expected in EXPECTED.items():
        record = records.get(name)
        if not isinstance(record, dict):
            continue
        if record.get("concept_doi") != expected["concept_doi"]:
            errors.append(f"allowlist: {name} concept DOI is incorrect")
        if record.get("maximum_file_count") != 1:
            errors.append(f"allowlist: {name} maximum_file_count must be 1")
        uploads = record.get("allowed_uploads")
        if not isinstance(uploads, list) or len(uploads) != 1:
            errors.append(f"allowlist: {name} must contain exactly one upload")
            continue
        upload = uploads[0]
        if not isinstance(upload, dict):
            errors.append(f"allowlist: {name} upload must be an object")
            continue
        checks = {
            "manifest_path": expected["pdf_path"],
            "basename": expected["pdf_basename"],
            "media_type": "application/pdf",
            "sha256": None,
        }
        for key, value in checks.items():
            if upload.get(key) != value:
                errors.append(f"allowlist: {name}.{key} is incorrect")


def validate_contract(contract: dict[str, Any], errors: list[str]) -> set[str]:
    if contract.get("artifact_owner_root") != ".":
        errors.append("contract: artifact_owner_root must be '.'")
    policy = contract.get("finalisation_policy")
    if not isinstance(policy, dict):
        errors.append("contract: finalisation_policy must be an object")
    else:
        if policy.get("network_access") != "forbidden":
            errors.append("contract: network access must be forbidden")
        if policy.get("manifest_self_exclusion") is not True:
            errors.append("contract: manifest self-exclusion must be true")
        if policy.get("post_tag_attestation_required") is not True:
            errors.append("contract: post-tag attestation must be required")
        for key in ("commit", "tag"):
            if policy.get(key) is not None:
                errors.append(f"contract: draft {key} must be null")

    predecessor = contract.get("predecessor_evidence")
    if not isinstance(predecessor, dict):
        errors.append("contract: predecessor_evidence must be an object")
    else:
        source_baseline = predecessor.get("source_baseline")
        if not isinstance(source_baseline, dict):
            errors.append("contract: predecessor source_baseline is missing")
        else:
            for path, expected_hash in EXPECTED_R189_SOURCES.items():
                if source_baseline.get(path) != expected_hash:
                    errors.append(f"contract: incorrect R189 source baseline for {path}")
        evidence = predecessor.get("evidence_files")
        if not isinstance(evidence, list) or len(evidence) < 5:
            errors.append("contract: R189 gate/report evidence inventory is incomplete")
        else:
            for index, item in enumerate(evidence):
                if not isinstance(item, dict):
                    errors.append(f"contract: evidence_files[{index}] is not an object")
                    continue
                if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
                    errors.append(f"contract: evidence_files[{index}] has invalid SHA-256")
                if not isinstance(item.get("bytes"), int) or item.get("bytes") <= 0:
                    errors.append(f"contract: evidence_files[{index}] has invalid byte count")

    configured = contract.get("required_artifacts")
    if not isinstance(configured, list) or not configured:
        errors.append("contract: required_artifacts must be a non-empty list")
        return set()
    paths: set[str] = set()
    for index, item in enumerate(configured):
        if not isinstance(item, dict):
            errors.append(f"contract: required_artifacts[{index}] is not an object")
            continue
        path = safe_relative_path(item.get("path"), errors, f"contract[{index}]")
        if path is None:
            continue
        if path in paths:
            errors.append(f"contract: duplicate artifact path {path}")
        paths.add(path)
        if item.get("role") not in {
            "source-data",
            "extracted-data",
            "model-input",
            "generator",
            "verifier",
            "scientific-output",
            "figure-input",
            "interpretation",
        }:
            errors.append(f"contract: unsupported role for {path}")
    missing = sorted(REQUIRED_OWNER_PATHS - paths)
    if missing:
        errors.append("contract: required owner paths missing: " + ", ".join(missing))
    exclusions = contract.get("required_exclusions")
    if not isinstance(exclusions, list) or not exclusions:
        errors.append("contract: required_exclusions must be a non-empty list")
    return paths


def validate_citation(root: Path, errors: list[str]) -> None:
    path = root / "CITATION.cff"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"CITATION.cff: cannot read: {exc}")
        return
    try:
        import yaml  # type: ignore
    except ImportError:
        # Keep the draft gate usable with the Python standard library. The
        # declared R190 environment supplies PyYAML for a full parse; this
        # fallback checks the fixed top-level contract without pretending to
        # be a general YAML parser.
        if not re.search(r"^cff-version:\s*1\.2\.0\s*$", text, re.MULTILINE):
            errors.append("CITATION.cff: cff-version must be 1.2.0")
        if not re.search(r"^type:\s*software\s*$", text, re.MULTILINE):
            errors.append("CITATION.cff: type must be software")
        for key in ("version", "date-released", "license"):
            if re.search(rf"^{re.escape(key)}:\s*", text, re.MULTILINE):
                errors.append(f"CITATION.cff: draft must omit top-level {key}")
        if 'doi: "10.5281/zenodo.18917929"' not in text:
            errors.append(
                "CITATION.cff: preferred citation must use preprint concept DOI"
            )
        return
    try:
        value = yaml.safe_load(text)
    except Exception as exc:
        errors.append(f"CITATION.cff: cannot parse YAML: {exc}")
        return
    if not isinstance(value, dict):
        errors.append("CITATION.cff: root must be a mapping")
        return
    if value.get("cff-version") != "1.2.0":
        errors.append("CITATION.cff: cff-version must be 1.2.0")
    if value.get("type") != "software":
        errors.append("CITATION.cff: type must be software")
    for key in ("version", "date-released"):
        if key in value:
            errors.append(f"CITATION.cff: draft must omit {key}")
    if "license" in value:
        errors.append("CITATION.cff: omit one top-level licence for mixed scopes")
    preferred = value.get("preferred-citation")
    if not isinstance(preferred, dict) or preferred.get("doi") != EXPECTED["preprint"][
        "concept_doi"
    ]:
        errors.append("CITATION.cff: preferred citation must use preprint concept DOI")


def validate_licensing(root: Path, errors: list[str]) -> None:
    required_fragments = {
        "LICENSE.md": ("CC-BY-4.0", "MIT", "Third-party"),
        "LICENSES/MIT.txt": ("MIT License", "Permission is hereby granted"),
        "THIRD_PARTY_NOTICES.md": ("SPARC", "Fail-closed archive policy"),
    }
    for relative, fragments in required_fragments.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{relative}: cannot read: {exc}")
            continue
        for fragment in fragments:
            if fragment not in text:
                errors.append(f"{relative}: missing required scope marker {fragment!r}")


def validate_public_status_texts(
    root: Path, *, pretag_ready: bool, errors: list[str]
) -> None:
    required = REVIEWED_STATUS if pretag_ready else DRAFT_STATUS
    patterns = {
        "README.md": rf"candidate release package has status\s+`{required}`",
        "REPRODUCIBILITY.md": rf"current package status is\s+`{required}`",
        "release/zenodo/R190/README.md": rf"^Status:\s+`{required}`\.$",
        "release/zenodo/R190/RELEASE_NOTES.md": rf"^\*\*Status:\*\*\s+`{required}`",
    }
    for relative, pattern in patterns.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{relative}: cannot read status text: {exc}")
            continue
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"{relative}: must state {required}")


def validate_manifest(
    root: Path,
    path: Path,
    required_paths: set[str],
    errors: list[str],
) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"pre-tag manifest: cannot read: {exc}")
        return {}
    if not isinstance(manifest, dict):
        errors.append("pre-tag manifest: root must be an object")
        return {}
    fixed = {
        "owner_id": PACKAGE_ID,
        "owner_root": ".",
        "status": "LOCALLY FROZEN CANDIDATE",
        "release_status": "LOCALLY_FROZEN_NOT_TAGGED_NOT_RELEASED",
        "git_commit": None,
        "git_tag": None,
        "manifest_self_excluded": True,
        "runtime_sidecar_in_scientific_digest": False,
    }
    for key, expected in fixed.items():
        if manifest.get(key) != expected:
            errors.append(f"pre-tag manifest: {key} is incorrect")
    records = manifest.get("artifact_records")
    if not isinstance(records, list) or not records:
        errors.append("pre-tag manifest: artifact_records must be a non-empty list")
        return manifest
    paths: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"pre-tag manifest: record {index} is not an object")
            continue
        relative = safe_relative_path(
            record.get("path"), errors, f"pre-tag manifest record {index}"
        )
        if relative is None:
            continue
        paths.append(relative)
        try:
            artifact = under_root(root, relative)
        except ValueError:
            errors.append(f"pre-tag manifest: path escapes root: {relative}")
            continue
        if not artifact.is_file():
            errors.append(f"pre-tag manifest: current artifact missing: {relative}")
            continue
        if artifact.stat().st_size != record.get("bytes"):
            errors.append(f"pre-tag manifest: byte count mismatch: {relative}")
        if sha256_file(artifact) != record.get("sha256"):
            errors.append(f"pre-tag manifest: SHA-256 mismatch: {relative}")
        if relative.endswith(".pdf") and (
            not isinstance(record.get("pages"), int) or record.get("pages") <= 0
        ):
            errors.append(f"pre-tag manifest: PDF page count invalid: {relative}")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        errors.append("pre-tag manifest: records must be uniquely sorted by path")
    if set(paths) != required_paths:
        missing = sorted(required_paths - set(paths))
        extra = sorted(set(paths) - required_paths)
        if missing:
            errors.append("pre-tag manifest: required paths missing: " + ", ".join(missing))
        if extra:
            errors.append("pre-tag manifest: uncontracted paths present: " + ", ".join(extra))
    digest = sha256_bytes(canonical_json_bytes(records))
    if manifest.get("scientific_payload_sha256") != digest:
        errors.append("pre-tag manifest: aggregate scientific digest mismatch")
    return manifest


def git_bytes(root: Path, commit: str, relative: str, errors: list[str]) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{relative}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        errors.append(f"Git cannot read {commit}:{relative}: {detail or exc}")
        return None
    return result.stdout


def resolve_commit(root: Path, revision: str, errors: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", f"{revision}^{{commit}}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"Git cannot resolve {revision!r}: {exc}")
        return None
    value = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        errors.append(f"Git resolved a non-full commit for {revision!r}: {value!r}")
        return None
    return value


def validate_attestation(
    root: Path,
    attestation_path: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    try:
        attestation = json.loads(attestation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"tag attestation: cannot read: {exc}")
        return
    if not isinstance(attestation, dict):
        errors.append("tag attestation: root must be an object")
        return
    if attestation.get("owner_id") != PACKAGE_ID:
        errors.append("tag attestation: wrong owner_id")
    if attestation.get("status") != "TRACKED OWNER":
        errors.append("tag attestation: status must be TRACKED OWNER")
    if attestation.get("release_status") != "TAG_ATTESTED_NOT_RELEASED":
        errors.append("tag attestation: release status is incorrect")
    if attestation.get("network_access") != "NONE":
        errors.append("tag attestation: network_access must be NONE")
    commit = attestation.get("git_commit")
    tag = attestation.get("git_tag")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("tag attestation: invalid full git_commit")
        return
    if not isinstance(tag, str) or not tag or tag.startswith("-") or ".." in tag:
        errors.append("tag attestation: unsafe git_tag")
        return
    resolved_commit = resolve_commit(root, commit, errors)
    resolved_tag = resolve_commit(root, f"refs/tags/{tag}", errors)
    if resolved_commit != commit or resolved_tag != commit:
        errors.append("tag attestation: commit/tag resolution mismatch")

    try:
        manifest_rel = manifest_path.resolve().relative_to(root).as_posix()
    except ValueError:
        errors.append("tag attestation: pre-tag manifest must be inside repository root")
        return
    manifest_bytes = manifest_path.read_bytes()
    if attestation.get("pretag_manifest_path") != manifest_rel:
        errors.append("tag attestation: pretag_manifest_path is incorrect")
    if attestation.get("pretag_manifest_sha256") != sha256_bytes(manifest_bytes):
        errors.append("tag attestation: pre-tag manifest SHA-256 mismatch")
    if attestation.get("scientific_payload_sha256") != manifest.get(
        "scientific_payload_sha256"
    ):
        errors.append("tag attestation: scientific payload digest mismatch")
    committed_manifest = git_bytes(root, commit, manifest_rel, errors)
    if committed_manifest is not None and committed_manifest != manifest_bytes:
        errors.append("tag attestation: tagged manifest differs from local manifest")
    records = manifest.get("artifact_records", [])
    if attestation.get("artifact_count") != len(records):
        errors.append("tag attestation: artifact_count mismatch")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            continue
        data = git_bytes(root, commit, record["path"], errors)
        if data is None:
            continue
        if len(data) != record.get("bytes") or sha256_bytes(data) != record.get(
            "sha256"
        ):
            errors.append(f"tag attestation: tagged bytes differ: {record['path']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--pretag-manifest")
    parser.add_argument("--tag-attestation")
    parser.add_argument(
        "--require-pretag-ready",
        action="store_true",
        help="require reviewed version/date/status and all validation checks",
    )
    parser.add_argument(
        "--require-release-ready",
        action="store_true",
        help="require reviewed version/date plus tag-bound artifact evidence",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.repo_root).resolve()
    errors: list[str] = []
    if not root.is_dir():
        print(f"HOLD: repository root does not exist: {root}", file=sys.stderr)
        return 2

    documents = {
        name: load_json(root, relative, errors) for name, relative in JSON_PATHS.items()
    }
    pretag_ready = bool(
        args.require_pretag_ready
        or args.require_release_ready
        or args.pretag_manifest
        or args.tag_attestation
    )
    validate_statuses(documents, release_ready=pretag_ready, errors=errors)
    validate_metadata(
        "preprint",
        documents["preprint"],
        release_ready=pretag_ready,
        errors=errors,
    )
    validate_metadata(
        "companion",
        documents["companion"],
        release_ready=pretag_ready,
        errors=errors,
    )
    if pretag_ready:
        preprint_metadata = documents["preprint"].get("metadata", {})
        companion_metadata = documents["companion"].get("metadata", {})
        if preprint_metadata.get("version") != companion_metadata.get("version"):
            errors.append("metadata: preprint and companion public versions differ")
        if preprint_metadata.get("publication_date") != companion_metadata.get(
            "publication_date"
        ):
            errors.append("metadata: preprint and companion publication dates differ")
        policy = documents["contract"].get("finalisation_policy", {})
        if policy.get("public_version") != preprint_metadata.get("version"):
            errors.append("contract: public_version does not match metadata")
        if policy.get("publication_date") != preprint_metadata.get("publication_date"):
            errors.append("contract: publication_date does not match metadata")

    validate_snapshot(documents["snapshot"], errors)
    validate_allowlist(documents["allowlist"], errors)
    required_paths = validate_contract(documents["contract"], errors)
    validate_citation(root, errors)
    validate_licensing(root, errors)
    validate_public_status_texts(root, pretag_ready=pretag_ready, errors=errors)

    validation = documents["validation"]
    if pretag_ready:
        checks = validation.get("checks")
        if validation.get("overall_status") != "PASS":
            errors.append("validation status: overall_status must be PASS")
        if not isinstance(checks, dict) or not checks:
            errors.append("validation status: checks must be a non-empty object")
        elif any(value != "PASS" for value in checks.values()):
            errors.append("validation status: every check must be PASS")
    elif validation.get("overall_status") != "PENDING":
        errors.append("draft validation status: overall_status must be PENDING")

    manifest: dict[str, Any] = {}
    manifest_path: Path | None = None
    if args.pretag_manifest:
        manifest_path = Path(args.pretag_manifest).resolve()
        manifest = validate_manifest(root, manifest_path, required_paths, errors)
    elif args.require_release_ready:
        errors.append("release-ready validation requires --pretag-manifest")

    if args.tag_attestation:
        if manifest_path is None or not manifest:
            errors.append("tag attestation requires a valid --pretag-manifest")
        else:
            validate_attestation(
                root,
                Path(args.tag_attestation).resolve(),
                manifest_path,
                manifest,
                errors,
            )
    elif args.require_release_ready:
        errors.append("release-ready validation requires --tag-attestation")

    if errors:
        print("HOLD")
        for error in errors:
            print(f"- {error}")
        print("network_access=NONE")
        return 2

    if args.require_release_ready:
        verdict = "PASS_TAG_ATTESTED_NOT_RELEASED"
    elif args.tag_attestation:
        verdict = "PASS_TAG_ATTESTED_NOT_RELEASED"
    elif args.pretag_manifest:
        verdict = "PASS_LOCAL_FROZEN_CANDIDATE"
    elif args.require_pretag_ready:
        verdict = "PASS_PRETAG_INPUTS_REVIEWED_NOT_FROZEN"
    else:
        verdict = "PASS_LOCAL_SCHEMA_ONLY"
    print(verdict)
    print("network_access=NONE")
    print("external_action_authorised=NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
