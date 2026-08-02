#!/usr/bin/env python3
"""Compare frozen calculation outputs across declared numerical runtimes.

The comparison is deliberately stricter than a scientific uncertainty test:
JSON structure, booleans, nulls and text are exact, apart from explicitly
ignored JSON value paths.  CSV structure and the non-numeric skeleton of every
cell are exact.  Only numeric values use the policy's absolute and relative
tolerances.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?"
    r"(?![A-Za-z0-9_])"
)
MAX_REPORTED_MISMATCHES = 100


class PolicyError(ValueError):
    """Raised when a policy or an input contract is invalid."""


@dataclass
class Metrics:
    numeric_comparisons: int = 0
    exact_comparisons: int = 0
    ignored_json_values: int = 0
    max_abs_difference: float = 0.0
    max_abs_location: str | None = None
    max_relative_difference: float = 0.0
    max_relative_location: str | None = None
    max_tolerance_fraction: float = 0.0
    max_tolerance_fraction_location: str | None = None
    total_mismatches: int = 0
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    def mismatch(self, location: str, reason: str, reference: Any, candidate: Any) -> None:
        self.total_mismatches += 1
        if len(self.mismatches) < MAX_REPORTED_MISMATCHES:
            self.mismatches.append(
                {
                    "location": location,
                    "reason": reason,
                    "reference": reference,
                    "candidate": candidate,
                }
            )

    def numeric(self, location: str, reference: float, candidate: float, abs_tol: float, rel_tol: float) -> None:
        self.numeric_comparisons += 1
        if not (math.isfinite(reference) and math.isfinite(candidate)):
            if reference != candidate:
                self.mismatch(location, "non-finite numeric values differ", reference, candidate)
            return

        difference = abs(reference - candidate)
        scale = max(abs(reference), abs(candidate))
        relative = difference / scale if scale else 0.0
        limit = abs_tol + rel_tol * scale
        tolerance_fraction = difference / limit if limit else (0.0 if difference == 0.0 else math.inf)

        if difference > self.max_abs_difference:
            self.max_abs_difference = difference
            self.max_abs_location = location
        if relative > self.max_relative_difference:
            self.max_relative_difference = relative
            self.max_relative_location = location
        if tolerance_fraction > self.max_tolerance_fraction:
            self.max_tolerance_fraction = tolerance_fraction
            self.max_tolerance_fraction_location = location
        if difference > limit:
            self.mismatch(
                location,
                f"numeric difference exceeds abs_tol + rel_tol*scale ({difference:.17g} > {limit:.17g})",
                reference,
                candidate,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--reference-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument(
        "--reference-label",
        default="REFERENCE_ROOT",
        help="portable label written to the report instead of the host path",
    )
    parser.add_argument(
        "--candidate-label",
        default="CANDIDATE_ROOT",
        help="portable label written to the report instead of the host path",
    )
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise PolicyError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid JSON in {path}: {exc}") from exc


def validate_tolerance(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyError(f"{name} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise PolicyError(f"{name} must be a finite non-negative number")
    return result


def safe_relative_path(raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise PolicyError("each file path must be a non-empty string")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise PolicyError(f"file path must remain below each comparison root: {raw}")
    return path


def json_pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def json_location(base: str, token: str | int) -> str:
    return f"{base}/{json_pointer_escape(str(token))}"


def compare_json(
    reference: Any,
    candidate: Any,
    location: str,
    ignored_paths: set[str],
    abs_tol: float,
    rel_tol: float,
    metrics: Metrics,
) -> None:
    if location in ignored_paths:
        if type(reference) is not type(candidate):
            metrics.mismatch(location, "ignored JSON values have different types", type(reference).__name__, type(candidate).__name__)
        else:
            metrics.ignored_json_values += 1
        return

    if isinstance(reference, bool) or reference is None or isinstance(reference, str):
        metrics.exact_comparisons += 1
        if type(reference) is not type(candidate) or reference != candidate:
            metrics.mismatch(location, "exact JSON scalar differs", reference, candidate)
        return

    if isinstance(reference, (int, float)) and not isinstance(reference, bool):
        if not isinstance(candidate, (int, float)) or isinstance(candidate, bool):
            metrics.mismatch(location, "JSON numeric/non-numeric type mismatch", type(reference).__name__, type(candidate).__name__)
            return
        metrics.numeric(location, float(reference), float(candidate), abs_tol, rel_tol)
        return

    if isinstance(reference, dict):
        if not isinstance(candidate, dict):
            metrics.mismatch(location, "JSON object/non-object type mismatch", "object", type(candidate).__name__)
            return
        ref_keys = set(reference)
        cand_keys = set(candidate)
        if ref_keys != cand_keys:
            metrics.mismatch(
                location,
                "JSON object keys differ",
                {"missing_from_candidate": sorted(ref_keys - cand_keys)},
                {"extra_in_candidate": sorted(cand_keys - ref_keys)},
            )
        for key in sorted(ref_keys & cand_keys):
            compare_json(
                reference[key],
                candidate[key],
                json_location(location, key),
                ignored_paths,
                abs_tol,
                rel_tol,
                metrics,
            )
        return

    if isinstance(reference, list):
        if not isinstance(candidate, list):
            metrics.mismatch(location, "JSON array/non-array type mismatch", "array", type(candidate).__name__)
            return
        if len(reference) != len(candidate):
            metrics.mismatch(location, "JSON array lengths differ", len(reference), len(candidate))
        for index, (ref_value, cand_value) in enumerate(zip(reference, candidate)):
            compare_json(
                ref_value,
                cand_value,
                json_location(location, index),
                ignored_paths,
                abs_tol,
                rel_tol,
                metrics,
            )
        return

    metrics.mismatch(location, "unsupported JSON value type", type(reference).__name__, type(candidate).__name__)


def numeric_tokens_and_skeleton(value: str) -> tuple[str, list[float]]:
    tokens: list[float] = []

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        try:
            number = float(token)
        except ValueError:
            return token
        tokens.append(number)
        return "<NUMBER>"

    return NUMBER_RE.sub(replace, value), tokens


def compare_csv_cell(
    reference: str,
    candidate: str,
    location: str,
    abs_tol: float,
    rel_tol: float,
    metrics: Metrics,
) -> None:
    ref_skeleton, ref_numbers = numeric_tokens_and_skeleton(reference)
    cand_skeleton, cand_numbers = numeric_tokens_and_skeleton(candidate)
    metrics.exact_comparisons += 1
    if ref_skeleton != cand_skeleton:
        metrics.mismatch(location, "CSV non-numeric text skeleton differs", ref_skeleton, cand_skeleton)
        return
    if len(ref_numbers) != len(cand_numbers):
        metrics.mismatch(location, "CSV numeric-token counts differ", len(ref_numbers), len(cand_numbers))
        return
    for index, (ref_number, cand_number) in enumerate(zip(ref_numbers, cand_numbers)):
        metrics.numeric(f"{location}#number[{index}]", ref_number, cand_number, abs_tol, rel_tol)


def read_csv(path: Path) -> list[list[str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.reader(handle))
    except FileNotFoundError as exc:
        raise PolicyError(f"missing file: {path}") from exc
    except csv.Error as exc:
        raise PolicyError(f"invalid CSV in {path}: {exc}") from exc


def compare_csv(reference_path: Path, candidate_path: Path, display_path: str, abs_tol: float, rel_tol: float, metrics: Metrics) -> None:
    reference = read_csv(reference_path)
    candidate = read_csv(candidate_path)
    if len(reference) != len(candidate):
        metrics.mismatch(display_path, "CSV row counts differ", len(reference), len(candidate))
    for row_index, (ref_row, cand_row) in enumerate(zip(reference, candidate), start=1):
        if len(ref_row) != len(cand_row):
            metrics.mismatch(f"{display_path}:row[{row_index}]", "CSV column counts differ", len(ref_row), len(cand_row))
        for column_index, (ref_cell, cand_cell) in enumerate(zip(ref_row, cand_row), start=1):
            compare_csv_cell(
                ref_cell,
                cand_cell,
                f"{display_path}:row[{row_index}]/column[{column_index}]",
                abs_tol,
                rel_tol,
                metrics,
            )


def validate_ignored_paths(data: Any, ignored_paths: set[str], file_path: str, which: str) -> None:
    for pointer in sorted(ignored_paths):
        if not pointer.startswith("/"):
            raise PolicyError(f"ignored JSON path must be an RFC 6901-style absolute pointer: {pointer}")
        current = data
        for raw_token in pointer[1:].split("/"):
            token = raw_token.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict) and token in current:
                current = current[token]
            elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                current = current[int(token)]
            else:
                raise PolicyError(f"ignored path {pointer} is absent in {which} {file_path}")


def validate_root_label(value: str, option: str) -> str:
    if not value or "\n" in value or "\r" in value:
        raise PolicyError(f"{option} must be a non-empty single-line label")
    return value


def compare_from_policy(
    policy: dict[str, Any],
    reference_root: Path,
    candidate_root: Path,
    reference_label: str,
    candidate_label: str,
) -> dict[str, Any]:
    if policy.get("schema_version") != 1:
        raise PolicyError("policy schema_version must be 1")
    policy_id = policy.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id:
        raise PolicyError("policy_id must be a non-empty string")
    files = policy.get("files")
    if not isinstance(files, list) or not files:
        raise PolicyError("policy files must be a non-empty array")

    defaults = policy.get("default_tolerance", {})
    if not isinstance(defaults, dict):
        raise PolicyError("default_tolerance must be an object")
    default_abs = validate_tolerance(defaults.get("absolute"), "default_tolerance.absolute")
    default_rel = validate_tolerance(defaults.get("relative"), "default_tolerance.relative")

    reference_root = reference_root.resolve()
    candidate_root = candidate_root.resolve()
    metrics = Metrics()
    file_summaries: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for file_index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise PolicyError(f"files[{file_index}] must be an object")
        relative = safe_relative_path(entry.get("path"))
        display_path = relative.as_posix()
        if display_path in seen_paths:
            raise PolicyError(f"duplicate policy file path: {display_path}")
        seen_paths.add(display_path)
        file_format = entry.get("format")
        if file_format not in {"json", "csv"}:
            raise PolicyError(f"unsupported format for {display_path}: {file_format!r}")
        abs_tol = validate_tolerance(entry.get("absolute_tolerance", default_abs), f"{display_path}.absolute_tolerance")
        rel_tol = validate_tolerance(entry.get("relative_tolerance", default_rel), f"{display_path}.relative_tolerance")
        ignored_raw = entry.get("ignore_json_paths", [])
        if not isinstance(ignored_raw, list) or any(not isinstance(item, str) for item in ignored_raw):
            raise PolicyError(f"ignore_json_paths for {display_path} must be an array of strings")
        ignored_paths = set(ignored_raw)
        if file_format != "json" and ignored_paths:
            raise PolicyError(f"ignore_json_paths is only valid for JSON files: {display_path}")

        mismatch_before = metrics.total_mismatches
        numeric_before = metrics.numeric_comparisons
        reference_path = reference_root / relative
        candidate_path = candidate_root / relative
        if file_format == "json":
            reference = load_json(reference_path)
            candidate = load_json(candidate_path)
            validate_ignored_paths(reference, ignored_paths, display_path, "reference")
            validate_ignored_paths(candidate, ignored_paths, display_path, "candidate")
            compare_json(reference, candidate, "", ignored_paths, abs_tol, rel_tol, metrics)
        else:
            compare_csv(reference_path, candidate_path, display_path, abs_tol, rel_tol, metrics)
        file_summaries.append(
            {
                "path": display_path,
                "format": file_format,
                "absolute_tolerance": abs_tol,
                "relative_tolerance": rel_tol,
                "ignored_json_paths": sorted(ignored_paths),
                "numeric_comparisons": metrics.numeric_comparisons - numeric_before,
                "mismatches": metrics.total_mismatches - mismatch_before,
                "status": "PASS" if metrics.total_mismatches == mismatch_before else "FAIL",
            }
        )

    return {
        "schema_version": 1,
        "policy_id": policy_id,
        "comparison_semantics": policy.get("comparison_semantics"),
        "scientific_status_guard": policy.get("scientific_status_guard"),
        "reference_root": validate_root_label(reference_label, "--reference-label"),
        "candidate_root": validate_root_label(candidate_label, "--candidate-label"),
        "status": "PASS" if metrics.total_mismatches == 0 else "FAIL",
        "files": file_summaries,
        "totals": {
            "files": len(file_summaries),
            "numeric_comparisons": metrics.numeric_comparisons,
            "exact_comparisons": metrics.exact_comparisons,
            "ignored_json_values": metrics.ignored_json_values,
            "mismatches_total": metrics.total_mismatches,
            "mismatches_reported": len(metrics.mismatches),
            "mismatch_report_limit": MAX_REPORTED_MISMATCHES,
            "max_absolute_difference": metrics.max_abs_difference,
            "max_absolute_difference_location": metrics.max_abs_location,
            "max_relative_difference": metrics.max_relative_difference,
            "max_relative_difference_location": metrics.max_relative_location,
            "max_tolerance_fraction": metrics.max_tolerance_fraction,
            "max_tolerance_fraction_location": metrics.max_tolerance_fraction_location,
        },
        "mismatches": metrics.mismatches,
    }


def emit(summary: dict[str, Any], output: Path | None) -> None:
    encoded = json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    sys.stdout.write(encoded)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        policy = load_json(args.policy)
        if not isinstance(policy, dict):
            raise PolicyError("policy root must be a JSON object")
        summary = compare_from_policy(
            policy,
            args.reference_root,
            args.candidate_root,
            args.reference_label,
            args.candidate_label,
        )
        emit(summary, args.json_output)
        return 0 if summary["status"] == "PASS" else 1
    except (PolicyError, OSError) as exc:
        summary = {
            "schema_version": 1,
            "policy": str(args.policy),
            "reference_root": args.reference_label,
            "candidate_root": args.candidate_label,
            "status": "ERROR",
            "error": str(exc),
        }
        emit(summary, args.json_output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
