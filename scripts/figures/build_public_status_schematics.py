#!/usr/bin/env python3
"""Render publication-neutral successors of six status schematics.

The scientific nodes, formulae, arrows, status classes and layout are reused
from the frozen R149/R181 presentation owners.  This public successor changes
only lifecycle language in visible titles and PDF metadata: internal round or
candidate identifiers are not appropriate in a reader-facing publication.

Run from a standalone repository clone:

    SOURCE_DATE_EPOCH=1785628800 \
      python3 scripts/figures/build_public_status_schematics.py

The output paths are the paths already used by the English preprint and
companion.  A deterministic JSON manifest records the exact source producers
and resulting binaries.  No manuscript source is edited by this script.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any


SOURCE_DATE_EPOCH = "1785628800"
FIXED_UTC = dt.datetime(2026, 8, 2, 0, 0, 0, tzinfo=dt.timezone.utc)
os.environ.setdefault("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)
os.environ.setdefault("TZ", "UTC")
os.environ.setdefault("LC_ALL", "C")
os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r190-public-figures-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/ect-r190-public-figures-xdg")


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
R181_SOURCE = (
    ROOT
    / "provenance/figures/r190/research_derivations/"
    "R181_HYPOTHESIS_PRESERVATION_v1/figures/build_r181_figures.py"
)
R149_SOURCE = (
    ROOT
    / "provenance/figures/r190/work_preprint/"
    "R149_READER_LAYOUT_CANDIDATE_v1/borderline_figure_typography/"
    "review_main_b/build_successors_b.py"
)

TITLE_MAP = {
    "ECT programme architecture — R181 hypothesis-preservation candidate":
        "ECT programme architecture",
    "Dimensionally separated scale inventory — R181 status successor":
        "Dimensionally separated scale inventory",
    "Dimensionally separated scale inventory — R181":
        "Dimensionally separated scale inventory",
    "Equation hierarchy — R181 companion status map":
        "Equation hierarchy — companion status map",
    "Equation hierarchy — R181 separated-owner candidate":
        "Equation hierarchy — separated physical owners",
    "Orientation stiffness — R181 parametric-owner audit":
        "Orientation stiffness — conditional owner map",
    "47C necessary-screen summary":
        "Record-channel necessary-screen summary",
}

OUTPUTS = (
    "figures/r177/global/fig_ect_architecture_r177.pdf",
    "figures/r153/line_semantics/fig_condensate_scales_line_semantics_r153.pdf",
    "figures/r153/line_semantics/fig_condensate_scales_line_semantics_r153.png",
    "figures/r177/global/fig_equation_hierarchy_r177.pdf",
    "figures/r149/r149_equation_hierarchy.pdf",
    "figures/r149/fig41_a_orientation_stiffness_upstream_r149.pdf",
    "figures/r149/r149_mediator_channels_summary_47C.pdf",
)

PDF_REQUIRED = {
    "figures/r177/global/fig_ect_architecture_r177.pdf": (
        "ECT programme architecture",
        "P4 adopted ordered-gradient postulate",
        "photon/tensor/common-cone universality Open",
    ),
    "figures/r153/line_semantics/fig_condensate_scales_line_semantics_r153.pdf": (
        "Dimensionally separated scale inventory",
        "No interpolation or RG flow is implied",
        "Level C/conditional benchmark",
    ),
    "figures/r177/global/fig_equation_hierarchy_r177.pdf": (
        "Equation hierarchy",
        "P4 adopted ordered-gradient postulate",
        "common-cone universality Open",
    ),
    "figures/r149/r149_equation_hierarchy.pdf": (
        "Equation hierarchy",
        "P4 adopted ordered-gradient postulate",
        "common-cone universality Open",
    ),
    "figures/r149/fig41_a_orientation_stiffness_upstream_r149.pdf": (
        "Orientation stiffness",
        "PARAMETRIC ONLY",
        "MISSING VERTEX",
    ),
    "figures/r149/r149_mediator_channels_summary_47C.pdf": (
        "Record-channel necessary-screen summary",
        "0 identified physical PES channels",
        "NOT IDENTIFIABLE",
    ),
}

FORBIDDEN_VISIBLE_TOKENS = ("R181", "47C")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_module(
    name: str,
    path: Path,
    *,
    workspace_override: Path | None = None,
) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(path)
    if workspace_override is not None:
        # The preserved R181 source was written for the larger private
        # workspace and locates that workspace through a neighbouring
        # ``LaTex/ECT_preprint.tex`` path.  A public clone has the preprint at
        # its root.  Replace only that location-discovery statement in memory;
        # the preserved source file and every scientific/layout instruction
        # remain byte-unchanged.
        source = path.read_text(encoding="utf-8")
        old = '''WORKSPACE = next(
    parent for parent in SCRIPT.parents
    if (parent / "LaTex/ECT_preprint.tex").is_file()
)'''
        if source.count(old) != 1:
            raise RuntimeError(
                f"unexpected R181 workspace-discovery anchor in {path}"
            )
        module = ModuleType(name)
        module.__file__ = str(path)
        module.__package__ = ""
        module.__dict__["_PUBLIC_WORKSPACE"] = workspace_override
        adapted = source.replace(old, "WORKSPACE = _PUBLIC_WORKSPACE", 1)
        exec(compile(adapted, str(path), "exec"), module.__dict__)
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load producer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def neutral(value: Any) -> Any:
    return TITLE_MAP.get(value, value)


def install_text_filter() -> tuple[Any, Any]:
    import matplotlib.axes
    import matplotlib.figure

    original_axes_text = matplotlib.axes.Axes.text
    original_figure_text = matplotlib.figure.Figure.text

    def axes_text(self: Any, x: Any, y: Any, s: Any, *args: Any, **kwargs: Any) -> Any:
        return original_axes_text(self, x, y, neutral(s), *args, **kwargs)

    def figure_text(self: Any, x: Any, y: Any, s: Any, *args: Any, **kwargs: Any) -> Any:
        return original_figure_text(self, x, y, neutral(s), *args, **kwargs)

    matplotlib.axes.Axes.text = axes_text
    matplotlib.figure.Figure.text = figure_text
    return original_axes_text, original_figure_text


def restore_text_filter(originals: tuple[Any, Any]) -> None:
    import matplotlib.axes
    import matplotlib.figure

    matplotlib.axes.Axes.text, matplotlib.figure.Figure.text = originals


def render(output_root: Path) -> None:
    r181 = load_module(
        "ect_r190_r181_source",
        R181_SOURCE,
        workspace_override=ROOT,
    )
    r149 = load_module("ect_r190_r149_source", R149_SOURCE)

    def save_pdf(fig: Any, path: Path, title: str, subject: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            path,
            format="pdf",
            metadata={
                "Title": neutral(title),
                "Author": "ECT reproducibility workflow",
                "Subject": subject,
                "Creator": SCRIPT.name,
                "CreationDate": FIXED_UTC,
                "ModDate": FIXED_UTC,
            },
        )

    def save_png(fig: Any, path: Path, dpi: int = 180) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            path,
            format="png",
            dpi=dpi,
            metadata={"Software": "ECT public figure generator"},
        )

    r181.save_pdf = save_pdf
    r181.save_png = save_png
    r149.ASSETS = output_root / "figures/r149"
    r149.LATEX = ROOT
    original_r149_sha = r149.sha

    def r149_sha(path: Path) -> str:
        if path.is_file():
            return original_r149_sha(path)
        marker = "work/preprint/"
        value = path.as_posix()
        if marker in value:
            mapped = (
                ROOT
                / "provenance/figures/r190/work_preprint"
                / value.split(marker, 1)[1]
            )
            if mapped.is_file():
                return sha256(mapped)
        raise FileNotFoundError(path)

    r149.sha = r149_sha
    r149.PDF_META = {
        "Title": "Record-channel necessary-screen summary",
        "Author": "ECT reproducibility workflow",
        "Subject": "Status-preserving reader-facing necessary-screen schematic",
        "Keywords": "ECT PES record channel status schematic",
        "Creator": SCRIPT.name,
        "CreationDate": FIXED_UTC,
        "ModDate": FIXED_UTC,
    }

    originals = install_text_filter()
    try:
        r181.render_architecture(
            output_root / "figures/r177/global/fig_ect_architecture_r177.pdf"
        )
        r181.render_scales(
            output_root
            / "figures/r153/line_semantics/"
            "fig_condensate_scales_line_semantics_r153.pdf",
            output_root
            / "figures/r153/line_semantics/"
            "fig_condensate_scales_line_semantics_r153.png",
        )
        r181.render_hierarchy(
            output_root / "figures/r177/global/fig_equation_hierarchy_r177.pdf",
            companion=False,
        )
        r181.render_hierarchy(
            output_root / "figures/r149/r149_equation_hierarchy.pdf",
            companion=True,
        )
        r181.render_orientation(
            output_root
            / "figures/r149/fig41_a_orientation_stiffness_upstream_r149.pdf"
        )
        try:
            r149.render_mediator()
        except ValueError as exc:
            # The frozen R149 producer constructs a provenance return record
            # with Path.relative_to(its original repository root) after it has
            # already saved the figure.  An isolated output-root is therefore
            # outside that historical reporting root.  The public successor
            # owns and verifies its own return manifest below.
            mediator_output = (
                output_root
                / "figures/r149/r149_mediator_channels_summary_47C.pdf"
            )
            if not mediator_output.is_file() or "subpath" not in str(exc):
                raise
    finally:
        restore_text_filter(originals)


def inspect_outputs(output_root: Path) -> list[dict[str, Any]]:
    r181 = load_module(
        "ect_r190_r181_inspector",
        R181_SOURCE,
        workspace_override=ROOT,
    )
    records: list[dict[str, Any]] = []
    for relative in OUTPUTS:
        path = output_root / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"missing or empty output: {relative}")
        record: dict[str, Any] = {
            "path": relative,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "role": "current English publication asset",
        }
        if path.suffix.lower() == ".pdf":
            with r181.fitz.open(path) as document:
                if document.page_count != 1:
                    raise RuntimeError(f"{relative}: expected one PDF page")
                text = "\n".join(page.get_text() for page in document)
            missing = [token for token in PDF_REQUIRED[relative] if token not in text]
            forbidden = [token for token in FORBIDDEN_VISIBLE_TOKENS if token in text]
            if missing or forbidden:
                raise RuntimeError(
                    f"{relative}: missing={missing!r}; forbidden={forbidden!r}"
                )
            record["page_count"] = 1
            record["required_tokens"] = list(PDF_REQUIRED[relative])
            record["forbidden_visible_tokens"] = list(FORBIDDEN_VISIBLE_TOKENS)
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT,
        help="Repository-shaped output root; defaults to this repository.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help=(
            "Manifest output path. Defaults below output-root at "
            "data/verification/R190_PUBLIC_STATUS_SCHEMATICS_v1.json."
        ),
    )
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    manifest_path = (
        args.manifest.resolve()
        if args.manifest
        else output_root
        / "data/verification/R190_PUBLIC_STATUS_SCHEMATICS_v1.json"
    )

    if os.environ.get("SOURCE_DATE_EPOCH") != SOURCE_DATE_EPOCH:
        raise RuntimeError(
            f"SOURCE_DATE_EPOCH must equal {SOURCE_DATE_EPOCH}"
        )

    render(output_root)
    records = inspect_outputs(output_root)
    manifest = {
        "schema_version": 1,
        "owner_id": "R190_PUBLIC_STATUS_SCHEMATICS_v1",
        "status": "PASS_PRESENTATION_ONLY",
        "scope": (
            "Lifecycle-neutral titles and metadata only; scientific nodes, "
            "formulae, edges, status classes and layout are inherited."
        ),
        "generator": {
            "path": "scripts/figures/build_public_status_schematics.py",
            "sha256": sha256(SCRIPT),
            "command": (
                "SOURCE_DATE_EPOCH=1785628800 "
                "python3 scripts/figures/build_public_status_schematics.py"
            ),
        },
        "source_producers": [
            {
                "path": str(R181_SOURCE.relative_to(ROOT)),
                "sha256": sha256(R181_SOURCE),
                "role": (
                    "preserved status/layout source; imported through a "
                    "location-only in-memory adapter"
                ),
            },
            {
                "path": str(R149_SOURCE.relative_to(ROOT)),
                "sha256": sha256(R149_SOURCE),
                "role": "frozen record-channel layout source; not edited",
            },
        ],
        "outputs": records,
        "scientific_status_firewall": {
            "presentation_change_only": True,
            "status_upgrade": False,
            "PES_R": "Level B calculational organisation",
            "physical_global_PES": "Open",
            "tensor_fixed_map": "Level A conditional negative result",
            "physical_spin_2_completion": "Open",
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(stable_json(manifest), encoding="utf-8")
    print(stable_json(manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
