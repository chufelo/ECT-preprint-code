#!/usr/bin/env python3
"""Strictly verify the public ECT figure registry from a standalone clone.

This is the repository-local successor of the ECT workspace
``ect-figure-governance`` registry verifier.  It preserves the fixed
English-only scope and v2 checks while resolving the registry's stable logical
``LaTex/...`` paths against either:

* this public repository root (the prefix is stripped); or
* a full ECT workspace root (the prefix is retained).

No non-English document is opened.  Absolute and traversing provenance owner
paths are rejected.  A ``NOT IDENTIFIED...`` marker is a declared gap, not a
successful reproduction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath


DOCUMENTS = (
    "LaTex/ECT_preprint.tex",
    "LaTex/companion/ECT_companion.tex",
    "LaTex/summary/ECT_summary.tex",
)
INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
INCLUDEPDF_RE = re.compile(r"\\includepdf\s*\[.*?\]\{([^}]+)\}", re.DOTALL)
ATLAS_RE = re.compile(r"\\RAtlas(?:FirstSingle|Single|WideSingle|PanelUnit)\{([^}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\{((?:\{[^}]*\})+)\}")
BRACED_RE = re.compile(r"\{([^}]*)\}")
EXTENSIONS = ("", ".pdf", ".png", ".jpg", ".jpeg", ".svg")
SAFE_PALETTE_WORDS = (
    "okabe",
    "grayscale",
    "grey",
    "gray",
    "black",
    "monochrome",
    "luminance",
    "redundan",
    "status",
    "navigation",
)
DECLARED_GAP_PREFIXES = (
    "NOT IDENTIFIED",
    "NOT APPLICABLE",
    "NONE IDENTIFIED",
)
REQUIRED_V2 = {
    "figure_id",
    "source_line",
    "insertion_token",
    "current_asset_token",
    "resolved_current_path",
    "output_sha256",
    "generator_paths",
    "generator_sha256",
    "data_paths",
    "data_sha256",
    "scientific_status",
    "palette_profile",
    "redundant_channels",
}


def sha256(path: Path) -> str:
    """Return a lowercase SHA-256 digest for one regular file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip_comments(text: str) -> str:
    """Mask unescaped TeX comments without changing line positions."""

    output: list[str] = []
    for line in text.splitlines(keepends=True):
        cut = None
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        if cut is None:
            output.append(line)
        else:
            newline = "\n" if line.endswith("\n") else ""
            visible = len(line.rstrip("\n"))
            output.append(line[:cut] + " " * max(0, visible - cut) + newline)
    return "".join(output)


def normalise_public_path(logical: str) -> PurePosixPath | None:
    """Map a safe logical owner path to a standalone-repository path."""

    logical = logical.strip()
    if not logical:
        return None
    path = PurePosixPath(logical)
    if path.is_absolute() or ".." in path.parts:
        return None
    parts = path.parts[1:] if path.parts and path.parts[0] == "LaTex" else path.parts
    if not parts:
        return None
    return PurePosixPath(*parts)


def logical_join(base: PurePosixPath, token: str) -> PurePosixPath:
    return PurePosixPath(os.path.normpath((base / token).as_posix()))


def physical_candidates(logical: str, roots: list[Path]) -> list[Path]:
    """Return existing public-repo and full-workspace candidates."""

    relative = normalise_public_path(logical)
    if relative is None:
        return []
    candidates: list[Path] = []
    for root in roots:
        for candidate in (root / relative, root / logical):
            if candidate.is_file() and candidate not in candidates:
                candidates.append(candidate)
    return candidates


def physical(logical: str, roots: list[Path]) -> Path | None:
    candidates = physical_candidates(logical, roots)
    return candidates[0] if candidates else None


def resolve_cli_file(root: Path, logical: str) -> Path:
    """Resolve a CLI path without accepting traversal outside the root."""

    value = Path(logical)
    if value.is_absolute():
        return value.resolve()
    candidates = [root / value]
    normalised = normalise_public_path(logical)
    if normalised is not None:
        candidates.append(root / normalised)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def resolve_token(document: str, token: str, text: str, roots: list[Path]) -> list[str]:
    """Resolve one active TeX inclusion to stable logical registry paths."""

    document_parent = PurePosixPath(document).parent
    bases = [document_parent]
    for match in GRAPHICSPATH_RE.finditer(text):
        bases.extend(
            logical_join(document_parent, raw)
            for raw in BRACED_RE.findall(match.group(1))
        )
    candidates: list[str] = []
    token_path = PurePosixPath(token)
    for base in bases:
        for extension in EXTENSIONS:
            logical = logical_join(base, token if token_path.suffix else token + extension)
            value = logical.as_posix()
            if normalise_public_path(value) is None:
                continue
            if physical(value, roots) and value not in candidates:
                candidates.append(value)
    return candidates


def scan_documents(root: Path, roots: list[Path]) -> tuple[list[dict], list[dict]]:
    """Enumerate active graphic inclusions in the fixed English chain."""

    del root  # root is represented by roots; retained for interface clarity.
    occurrences: list[dict] = []
    document_hashes: list[dict] = []
    for document in DOCUMENTS:
        path = physical(document, roots)
        if path is None:
            occurrences.append({"document": document, "error": "missing-document"})
            continue
        document_hashes.append({"document": document, "sha256": sha256(path)})
        text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))

        def add(token: str, include: str, line_offset: int) -> None:
            candidates = resolve_token(document, token, text, roots)
            occurrences.append(
                {
                    "document": document,
                    "line": text.count("\n", 0, line_offset) + 1,
                    "token": token,
                    "include": include,
                    "resolved": candidates[0] if candidates else None,
                    "all_existing_candidates": candidates,
                }
            )

        for match in INCLUDE_RE.finditer(text):
            if not match.group(1).startswith("#"):
                add(match.group(1), match.group(0), match.start())
        for match in INCLUDEPDF_RE.finditer(text):
            add(match.group(1), f"]{{{match.group(1)}}}", match.start(1))
        for match in ATLAS_RE.finditer(text):
            if not match.group(1).startswith("#"):
                add(match.group(1), match.group(0), match.start())
    return occurrences, document_hashes


def split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def declared_gap(logical: str, expected: str) -> bool:
    return any(
        logical.startswith(prefix) or expected.startswith(prefix)
        for prefix in DECLARED_GAP_PREFIXES
    )


def verify_path_hash_pairs(
    roots: list[Path],
    paths_value: str,
    hashes_value: str,
    row_line: int,
    field: str,
    errors: list[dict],
) -> list[dict]:
    """Verify every semicolon-paired public provenance path and digest."""

    paths = split_semicolon(paths_value)
    hashes = split_semicolon(hashes_value)
    records: list[dict] = []
    if not paths:
        return records
    if len(paths) != len(hashes):
        errors.append(
            {
                "type": "provenance-path-hash-count-mismatch",
                "line": row_line,
                "field": field,
                "path_count": len(paths),
                "hash_count": len(hashes),
            }
        )
        return records
    for logical, expected in zip(paths, hashes):
        if declared_gap(logical, expected):
            records.append({"path": logical, "declared_gap": True})
            continue
        if normalise_public_path(logical) is None:
            errors.append(
                {
                    "type": "unsafe-provenance-path",
                    "line": row_line,
                    "field": field,
                    "path": logical,
                }
            )
            continue
        candidates = physical_candidates(logical, roots)
        if not candidates:
            errors.append(
                {
                    "type": "missing-provenance-file",
                    "line": row_line,
                    "field": field,
                    "path": logical,
                }
            )
            continue
        if len(candidates) > 1:
            unique_hashes = {sha256(candidate) for candidate in candidates}
            if len(unique_hashes) > 1:
                errors.append(
                    {
                        "type": "shadowed-provenance-file",
                        "line": row_line,
                        "field": field,
                        "path": logical,
                        "candidate_count": len(candidates),
                    }
                )
                continue
        path = candidates[0]
        actual = sha256(path)
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(
                {
                    "type": "invalid-provenance-sha256",
                    "line": row_line,
                    "field": field,
                    "path": logical,
                    "value": expected,
                }
            )
        elif actual != expected:
            errors.append(
                {
                    "type": "provenance-hash-mismatch",
                    "line": row_line,
                    "field": field,
                    "path": logical,
                    "expected": expected,
                    "actual": actual,
                }
            )
        records.append({"path": logical, "sha256": actual})
    return records


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Verify the public v2 ECT figure registry from a standalone clone."
    )
    result.add_argument(
        "--root",
        help="public repository root; defaults to the root owning this script",
    )
    result.add_argument(
        "--asset-root",
        action="append",
        default=[],
        help="optional read-only fallback root; not needed by a complete public clone",
    )
    result.add_argument("--registry", default="FIGURE_REGISTRY.csv")
    result.add_argument(
        "--json-registry",
        help="defaults to the CSV sibling with a .json suffix",
    )
    result.add_argument("--json-output")
    result.add_argument("--strict-palette", action="store_true")
    result.add_argument(
        "--strict-provenance",
        action="store_true",
        help="verify every non-declared generator and data-owner digest",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    default_root = Path(__file__).resolve().parents[2]
    root = Path(args.root).expanduser().resolve() if args.root else default_root
    roots = [root]
    for item in args.asset_root:
        candidate = Path(item).expanduser().resolve()
        if candidate not in roots:
            roots.append(candidate)

    registry_path = resolve_cli_file(root, args.registry)
    json_path = (
        resolve_cli_file(root, args.json_registry)
        if args.json_registry
        else registry_path.with_suffix(".json")
    )
    errors: list[dict] = []
    warnings: list[dict] = []
    declared_gaps: list[dict] = []

    try:
        with registry_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            registry_rows = list(reader)
    except (OSError, csv.Error) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, indent=2), file=sys.stderr)
        return 3

    if not REQUIRED_V2.issubset(fields):
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "error": "unsupported registry schema; public verifier requires v2",
                    "missing_fields": sorted(REQUIRED_V2 - fields),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 3

    try:
        json_data = json.loads(json_path.read_text(encoding="utf-8"))
        json_rows = json_data.get("rows") if isinstance(json_data, dict) else json_data
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(
            {
                "type": "json-registry-read-error",
                "path": json_path.name,
                "error": str(exc),
            }
        )
        json_rows = None
    if json_rows is not None and registry_rows != json_rows:
        errors.append(
            {
                "type": "csv-json-row-sync-mismatch",
                "csv_rows": len(registry_rows),
                "json_rows": len(json_rows),
            }
        )

    occurrences, document_hashes = scan_documents(root, roots)
    for item in occurrences:
        if item.get("error"):
            errors.append({"type": item["error"], **item})
        elif not item["resolved"]:
            errors.append({"type": "unresolved-english-insertion", **item})
        elif len(item["all_existing_candidates"]) != 1:
            errors.append({"type": "shadowed-english-insertion", **item})

    registry_assets: dict[str, tuple[int, dict]] = {}
    registry_ids: dict[str, int] = {}
    row_analysis: list[dict] = []
    for line, row in enumerate(registry_rows, start=2):
        asset = row["resolved_current_path"].strip()
        figure_id = row["figure_id"].strip()
        if not figure_id:
            errors.append({"type": "missing-figure-id", "line": line, "asset": asset})
        elif figure_id in registry_ids:
            errors.append(
                {
                    "type": "duplicate-figure-id",
                    "figure_id": figure_id,
                    "lines": [registry_ids[figure_id], line],
                }
            )
        else:
            registry_ids[figure_id] = line
        if normalise_public_path(asset) is None:
            errors.append({"type": "unsafe-registered-asset", "line": line, "asset": asset})
        if asset in registry_assets:
            errors.append(
                {
                    "type": "duplicate-registry-asset",
                    "asset": asset,
                    "lines": [registry_assets[asset][0], line],
                }
            )
        registry_assets[asset] = (line, row)

        matches = [item for item in occurrences if item.get("resolved") == asset]
        candidates = physical_candidates(asset, roots)
        if not candidates:
            errors.append({"type": "missing-registered-asset", "line": line, "asset": asset})
            actual_hash = None
        else:
            actual_hash = sha256(candidates[0])
            if len(candidates) > 1 and len({sha256(path) for path in candidates}) > 1:
                errors.append(
                    {
                        "type": "shadowed-registered-asset",
                        "line": line,
                        "asset": asset,
                        "candidate_count": len(candidates),
                    }
                )

        expected_hash = row["output_sha256"].strip()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            errors.append(
                {
                    "type": "invalid-output-sha256",
                    "line": line,
                    "asset": asset,
                    "value": expected_hash,
                }
            )
        elif actual_hash and expected_hash != actual_hash:
            errors.append(
                {
                    "type": "output-hash-mismatch",
                    "line": line,
                    "asset": asset,
                    "expected": expected_hash,
                    "actual": actual_hash,
                }
            )

        expected_lines = ";".join(str(item["line"]) for item in matches)
        expected_tokens = ";".join(item["include"] for item in matches)
        if row["source_line"] != expected_lines:
            errors.append(
                {
                    "type": "source-line-mismatch",
                    "line": line,
                    "asset": asset,
                    "expected": expected_lines,
                    "actual": row["source_line"],
                }
            )
        if row["insertion_token"] != expected_tokens:
            errors.append(
                {
                    "type": "insertion-token-mismatch",
                    "line": line,
                    "asset": asset,
                    "expected": expected_tokens,
                    "actual": row["insertion_token"],
                }
            )
        if not row["scientific_status"].strip():
            errors.append({"type": "missing-scientific-status", "line": line, "asset": asset})
        if not row["redundant_channels"].strip():
            errors.append({"type": "missing-redundant-channel", "line": line, "asset": asset})
        palette = row["palette_profile"].lower()
        if not any(word in palette for word in SAFE_PALETTE_WORDS):
            target = errors if args.strict_palette else warnings
            target.append(
                {
                    "type": "palette-safety-not-declared",
                    "line": line,
                    "asset": asset,
                }
            )

        if args.strict_provenance:
            generators = verify_path_hash_pairs(
                roots,
                row["generator_paths"],
                row["generator_sha256"],
                line,
                "generator",
                errors,
            )
            data_files = verify_path_hash_pairs(
                roots,
                row["data_paths"],
                row["data_sha256"],
                line,
                "data",
                errors,
            )
        else:
            generators = [{"status": "NOT_CHECKED_WITHOUT_STRICT_PROVENANCE"}]
            data_files = [{"status": "NOT_CHECKED_WITHOUT_STRICT_PROVENANCE"}]

        for record in (*generators, *data_files):
            if record.get("declared_gap"):
                declared_gaps.append(
                    {"line": line, "asset": asset, "path": record["path"]}
                )
        if not matches:
            errors.append({"type": "orphan-registry-asset", "line": line, "asset": asset})

        row_analysis.append(
            {
                "line": line,
                "figure_id": figure_id,
                "asset": asset,
                "matched_insertions": len(matches),
                "sha256": actual_hash,
                "generator_records": generators,
                "data_records": data_files,
            }
        )

    for occurrence in occurrences:
        if occurrence.get("resolved") and occurrence["resolved"] not in registry_assets:
            errors.append({"type": "unregistered-english-insertion", **occurrence})

    status = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    result = {
        "status": status,
        "schema": "v2",
        "verifier": "scripts/figures/verify_public_figure_registry.py",
        "verifier_sha256": sha256(Path(__file__).resolve()),
        "registry": Path(args.registry).as_posix(),
        "registry_sha256": sha256(registry_path),
        "json_registry": (
            Path(args.json_registry).as_posix()
            if args.json_registry
            else Path(args.registry).with_suffix(".json").as_posix()
        ),
        "json_registry_sha256": sha256(json_path) if json_path.is_file() else None,
        "registry_rows": len(registry_rows),
        "fixed_english_documents": list(DOCUMENTS),
        "document_hashes": document_hashes,
        "english_insertions": len(
            [item for item in occurrences if not item.get("error")]
        ),
        "unique_resolved_english_assets": len(
            {item.get("resolved") for item in occurrences if item.get("resolved")}
        ),
        "strict_provenance": args.strict_provenance,
        "provenance_replay": (
            "DECLARED_GAPS_PRESENT"
            if declared_gaps
            else ("FULLY_CHECKED" if args.strict_provenance else "NOT_CHECKED")
        ),
        "errors": errors,
        "warnings": warnings,
        "declared_gaps": declared_gaps,
        "rows": row_analysis,
        "non_english_documents_opened": False,
        "scientific_status_inferred_from_colour": False,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        output = Path(args.json_output).expanduser()
        if not output.is_absolute():
            output = root / output
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 2 if errors else (1 if warnings else 0)


if __name__ == "__main__":
    raise SystemExit(main())
