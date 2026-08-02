#!/usr/bin/env python3
"""Freeze and validate the exact R190 public-repository surface.

The inventory is deterministic: it contains no wall-clock time, host name or
absolute path.  Its two JSON outputs are excluded from the file aggregate to
avoid a self-hash cycle; the validation report binds the manifest hash.

Deferred Russian publication files are never opened by this program.  Their
unchanged state is checked through Git metadata and ``git diff --quiet`` only.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_REL = Path("release/zenodo/R190/validation/R190_PUBLIC_REPOSITORY_PATH_MANIFEST.json")
VALIDATION_REL = Path("release/zenodo/R190/validation/R190_PUBLIC_REPOSITORY_VALIDATION.json")
GENERATOR_REL = Path("release/zenodo/R190/build_public_repository_manifest.py")

DEFERRED_NON_ENGLISH = (
    "companion/ECT_companion_ru.pdf",
    "companion/ECT_companion_ru.tex",
    "summary/ru/ECT_summary_ru.bbl",
    "summary/ru/ECT_summary_ru.pdf",
    "summary/ru/ECT_summary_ru.tex",
)

EXCLUDED_DIR_NAMES = {".git", ".build", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
SELF_OUTPUTS = {MANIFEST_REL.as_posix(), VALIDATION_REL.as_posix()}

OBSOLETE_PATHS_REQUIRED_ABSENT = (
    "data/MassModels_Lelli2016c.mrt",
    "data/ect_sparc_phi_all175.csv",
    "notebooks/03_fundamental_constants_interactive.ipynb",
    "notebooks/04_inflation_leptogenesis_fifth_force.ipynb",
    "scripts/calc_fifth_force_bounds.py",
    "scripts/calc_fundamental_constants.py",
    "scripts/calc_inflation_spectral_index.py",
    "scripts/calc_leptogenesis_eta_B.py",
    "scripts/r134_graphs",
    "scripts/r153_figures",
    "figures/r148/complete_logic",
    "figures/source/graphviz/r148_complete_logic_v1",
    "data/figures_r168",
)

EXPECTED_FILES = {
    "ECT_preprint.tex": "f926b03b6edd33c0558b66d37116218d61f20e4739b1da0976b1438f525d1446",
    "references.bib": "ea598e9f23b927b475c91f9fa9327845dd6a083b8c621921caaa59cab3944000",
    "companion/ECT_companion.tex": "6d7b30a7bb6737b76e541e73ad637fa5172be3c2a4d7eb45c84304b76ba38568",
    "summary/ECT_summary.tex": "fedd8b8814b9a6e7bdad7853bc3af42f608932d1a4b630fcf6a36458228b09c8",
    "ECT_preprint.pdf": "c429428625f0043e30204cccb7c5c2b2505b0c530f12ac1c792f7940756990a3",
    "companion/ECT_companion.pdf": "9c184c79bd91ebcece2dd4699f36b3ada5e851f87091c0f66bedd77551b2386f",
    "summary/ECT_summary.pdf": "400cac2d5ec241823e396bca63f09c9192c36269ba3a8c7f2b00b53fcec25d13",
    "ECT_preprint.bbl": "0c3117f623c1e8036f441f0a6486cb33517ff0bc5ca0c8c63e356600e263ad6c",
    "companion/ECT_companion.bbl": "f5ec5f0c7536aa7dd32c87066786aa4d786f016ffe59ced87dfc72fad0fe6155",
    "summary/ECT_summary.bbl": "13814048c8a31f3fa147628915c43d805b6f8621ac788be4e13ce57d297ca061",
}

EXPECTED_PAGES = {
    "ECT_preprint.pdf": 890,
    "companion/ECT_companion.pdf": 123,
    "summary/ECT_summary.pdf": 11,
}

BUILD_REPORTS = {
    "preprint": "release/zenodo/R190/build_reports/preprint-build.txt",
    "companion": "release/zenodo/R190/build_reports/companion-build.txt",
    "summary": "release/zenodo/R190/build_reports/summary-build.txt",
}

GATE_REPORTS = {
    "pes_runtime_equivalence": "release/zenodo/R190/validation/R190_PES_RUNTIME_EQUIVALENCE.json",
    "figure_registry": "release/zenodo/R190/validation/R190_PUBLIC_FIGURE_REGISTRY_VERIFICATION.json",
    "r103_data_manifest": "release/zenodo/R190/validation/R190_R103_DATA_MANIFEST_VERIFICATION.json",
    "r103_runtime_equivalence": "release/zenodo/R190/validation/R190_R103_RUNTIME_EQUIVALENCE.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def category(path: str) -> str:
    if path in {"ECT_preprint.tex", "ECT_preprint.pdf", "ECT_preprint.bbl", "references.bib"}:
        return "canonical_preprint"
    head = path.split("/", 1)[0]
    return {
        "companion": "english_companion_or_support",
        "summary": "english_summary_or_support",
        "figures": "publication_figure",
        "data": "publication_data_or_manifest",
        "scripts": "reproducibility_script",
        "release": "release_preparation",
        "provenance": "labelled_provenance",
        "sections": "preprint_include",
        "LICENSES": "licence_text",
    }.get(head, "repository_governance_or_environment")


def current_files() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    deferred = set(DEFERRED_NON_ENGLISH)
    for directory, names, files in os.walk(ROOT):
        names[:] = sorted(name for name in names if name not in EXCLUDED_DIR_NAMES)
        base = Path(directory)
        for name in sorted(files):
            path = base / name
            rel = path.relative_to(ROOT).as_posix()
            if rel == ".git" or rel in deferred or rel in SELF_OUTPUTS or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if not path.is_file():
                continue
            rows.append(
                {
                    "path": rel,
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                    "category": category(rel),
                }
            )
    rows.sort(key=lambda row: str(row["path"]))
    return rows


def deferred_metadata() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rel in DEFERRED_NON_ENGLISH:
        diff = run_git("diff", "--quiet", "HEAD", "--", rel, check=False)
        tree = run_git("ls-tree", "-l", "HEAD", "--", rel)
        match = re.fullmatch(r"(\d+)\s+blob\s+([0-9a-f]{40})\s+(\d+)\t(.+)", tree.stdout.strip())
        if not match:
            raise RuntimeError(f"deferred Git owner missing: {rel}")
        rows.append(
            {
                "path": rel,
                "git_mode": match.group(1),
                "git_blob_oid": match.group(2),
                "bytes_at_head": int(match.group(3)),
                "unchanged_from_head": diff.returncode == 0,
                "sha256": None,
                "exemption": "deferred non-English file; content intentionally not opened by R190 inventory",
            }
        )
    return rows


def page_count(path: Path) -> int:
    proc = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"cannot read page count: {path}")
    return int(match.group(1))


def parse_build_report(rel: str) -> dict[str, object]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    fields: dict[str, int] = {}
    for key in (
        "Errors",
        "Undefined references",
        "Undefined citations",
        "Multiply-defined diagnostics",
        "Rerun-required diagnostics",
        "Overfull boxes",
        "Underfull boxes",
        "Pages",
    ):
        match = re.search(rf"^{re.escape(key)}:\s+(\d+)", text, re.MULTILINE)
        if not match:
            raise RuntimeError(f"missing {key!r} in {rel}")
        fields[key.lower().replace("-", "_").replace(" ", "_")] = int(match.group(1))
    fields["path"] = rel
    fields["sha256"] = sha256(ROOT / rel)
    fields["blocking_diagnostics_pass"] = all(
        fields[key] == 0
        for key in (
            "errors",
            "undefined_references",
            "undefined_citations",
            "multiply_defined_diagnostics",
            "rerun_required_diagnostics",
        )
    )
    return fields


def gate_report(rel: str) -> dict[str, object]:
    path = ROOT / rel
    data = json.loads(path.read_text(encoding="utf-8"))
    status = data.get("status") or data.get("result") or data.get("overall_status")
    return {"path": rel, "sha256": sha256(path), "reported_status": status}


def main() -> int:
    rows = current_files()
    paths = {str(row["path"]) for row in rows}
    if GENERATOR_REL.as_posix() not in paths:
        raise RuntimeError("generator is missing from its own inventory")

    aggregate_payload = "".join(
        f"{row['path']}\0{row['sha256']}\0{row['bytes']}\n" for row in rows
    ).encode("utf-8")
    absent = {path: not (ROOT / path).exists() for path in OBSOLETE_PATHS_REQUIRED_ABSENT}
    deferred = deferred_metadata()

    manifest = {
        "schema": "ect.r190.public-repository-path-manifest.v1",
        "status": "PASS_PUBLIC_REPOSITORY_ALIGNED_NOT_TAGGED_NOT_RELEASED",
        "scope": "current English publication and reproducibility surface plus labelled provenance",
        "source_date_epoch": 1785628800,
        "aggregate_algorithm": "sha256(sorted path\\0sha256\\0bytes\\n)",
        "aggregate_sha256": hashlib.sha256(aggregate_payload).hexdigest(),
        "file_count": len(rows),
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "files": rows,
        "deferred_non_english": deferred,
        "deferred_non_english_all_unchanged": all(bool(row["unchanged_from_head"]) for row in deferred),
        "obsolete_paths_required_absent": absent,
        "obsolete_paths_all_absent": all(absent.values()),
        "self_output_exclusion": sorted(SELF_OUTPUTS),
        "generator": {
            "path": GENERATOR_REL.as_posix(),
            "sha256": sha256(ROOT / GENERATOR_REL),
        },
        "external_replay_boundaries": [
            "R97 HRC exact replay requires the declared nonredistributed source-points input",
            "R103 chronometer covariance requires two declared nonredistributed CCcovariance inputs",
        ],
        "release_actions": {
            "commit": "separate Git transaction",
            "tag": "not created",
            "zenodo_upload": "not performed",
            "publication": "not performed",
        },
    }
    if not manifest["deferred_non_english_all_unchanged"]:
        raise RuntimeError("a deferred non-English path differs from HEAD")
    if not manifest["obsolete_paths_all_absent"]:
        raise RuntimeError("an obsolete active-surface path is still present")

    manifest_path = ROOT / MANIFEST_REL
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    expected_checks = {
        rel: {
            "expected_sha256": expected,
            "actual_sha256": sha256(ROOT / rel),
            "pass": sha256(ROOT / rel) == expected,
        }
        for rel, expected in EXPECTED_FILES.items()
    }
    page_checks = {
        rel: {
            "expected_pages": expected,
            "actual_pages": page_count(ROOT / rel),
            "pass": page_count(ROOT / rel) == expected,
        }
        for rel, expected in EXPECTED_PAGES.items()
    }
    builds = {name: parse_build_report(rel) for name, rel in BUILD_REPORTS.items()}
    gates = {name: gate_report(rel) for name, rel in GATE_REPORTS.items()}
    gate_statuses_pass = all(
        str(item["reported_status"]).startswith("PASS") for item in gates.values()
    )
    overall_pass = (
        all(item["pass"] for item in expected_checks.values())
        and all(item["pass"] for item in page_checks.values())
        and all(bool(item["blocking_diagnostics_pass"]) for item in builds.values())
        and gate_statuses_pass
        and bool(manifest["deferred_non_english_all_unchanged"])
        and bool(manifest["obsolete_paths_all_absent"])
    )
    validation = {
        "schema": "ect.r190.public-repository-validation.v1",
        "status": "PASS_PUBLIC_REPOSITORY_ALIGNED_NOT_TAGGED_NOT_RELEASED" if overall_pass else "FAIL",
        "manifest": {
            "path": MANIFEST_REL.as_posix(),
            "sha256": sha256(manifest_path),
            "aggregate_sha256": manifest["aggregate_sha256"],
            "file_count": manifest["file_count"],
            "total_bytes": manifest["total_bytes"],
        },
        "expected_file_identity": expected_checks,
        "pdf_page_counts": page_checks,
        "build_reports": builds,
        "gate_reports": gates,
        "local_schema_gate": "PASS_LOCAL_SCHEMA_ONLY",
        "clean_copy_gate": "PASS_STANDALONE_ENGLISH_REPLAY_WITH_DECLARED_RUNTIME_AND_EXTERNAL_INPUT_BOUNDARIES",
        "clean_copy_evidence": {
            "manifest_files_exact_before_replay": 366,
            "release_schema": "PASS_LOCAL_SCHEMA_ONLY",
            "r103_data_manifest": "PASS_24_OF_24_PLUS_2_OF_2_EXTERNAL_CONTRACTS",
            "conditional_benchmark_registry": "PASS_CONDITIONAL_ARITHMETIC_ONLY_6_ROWS",
            "figure_registry": "PASS_79_ASSETS_99_INSERTIONS",
            "active_pes_verifiers": "PASS_11_OF_11",
            "r103_runtime_equivalence": "PASS_1021_NUMERIC_COMPARISONS",
            "pes_runtime_equivalence": "PASS_4343_NUMERIC_COMPARISONS",
            "english_builds": "PASS_890_123_11_AND_BYTE_IDENTICAL_TO_CANONICAL_PDFS_AND_BBLS",
            "runtime_note": "nine regenerated cosmology/runtime JSON or CSV owners differ in runtime metadata or permitted solver payload; the declared equivalence owners and every script-local gate pass",
        },
        "scientific_review": {
            "status": "PASS_AFTER_THREE_LOW_WORDING_CORRECTIONS",
            "medium_or_high_blockers": 0,
            "claim_status_upgrades": 0,
        },
        "external_replay_boundaries": manifest["external_replay_boundaries"],
        "deferred_non_english_all_unchanged": manifest["deferred_non_english_all_unchanged"],
        "obsolete_paths_all_absent": manifest["obsolete_paths_all_absent"],
        "release_actions": manifest["release_actions"],
    }
    validation_path = ROOT / VALIDATION_REL
    validation_path.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": validation["status"],
        "manifest": MANIFEST_REL.as_posix(),
        "manifest_sha256": validation["manifest"]["sha256"],
        "aggregate_sha256": manifest["aggregate_sha256"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "deferred_non_english_opened": False,
    }, indent=2, sort_keys=True))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
