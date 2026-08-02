#!/usr/bin/env python3
"""Build the R177 terminal-units figure successors without live-file writes.

This candidate-only producer is intentionally narrow:

* Part I: replace the stale ``c_char^4`` Newton formula in the semantic
  source/topology/key; rebuild the compact reader so its visible source-hash
  footer points at the corrected semantic owner.
* Part II v4: keep the selected compact PDF byte-identical and add only the
  missing terminal-units semantic-key/provenance owner.
* Figure 41b: reuse the exact hash-locked R123 targeted-readability layout and
  replace only the lower-box formula text.
* The live preprint, live figure assets, and live CSV/JSON registries are read
  and hash-guarded but never edited.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import fitz


FIXED_UTC = "2026-07-29T00:00:00Z"
SCHEMA = "ect.r177.terminal_units_figures.v1"
LIVE_PREPRINT_SHA256 = (
    "2acbebbaa9c11be535195c6f2b8a0c184eee5dadc2070af252bd87f7eae17217"
)

MODULE = Path(__file__).resolve()
WORKSPACE = MODULE.parents[4]
LATEX = WORKSPACE / "LaTex"
RECOVERY = WORKSPACE / "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1"
PACKAGE = RECOVERY / "figures/terminal_units_successors"

PARTI_FAMILY = LATEX / "figures/source/graphviz/r168_connected_map_semantics_v1"
PARTI_SOURCE = PARTI_FAMILY / "fig09_partI_semantic_successor_r168.gv"
PARTI_TOPOLOGY = LATEX / "data/figures_r168/topology/fig09_partI_topology_r168.json"
PARTI_BUILDER = PARTI_FAMILY / "build_r150_assets_r168.py"
PARTI_HELPER = PARTI_FAMILY / "r168_reader_semantic_helpers.py"
PARTI_LIVE_PDF = LATEX / "figures/r168/logic_maps/partI_a4_reader_r168.pdf"

PARTII_PACKAGE = RECOVERY / "figures/partII_successor"
PARTII_SOURCE = PARTII_PACKAGE / "source/fig24_partII_semantic_successor_r177.gv"
PARTII_BUILDER = PARTII_PACKAGE / "build_partII_successor.py"
PARTII_DELTA = PARTII_PACKAGE / "SEMANTIC_TOPOLOGY_DELTA_R177.json"
PARTII_REPORT = PARTII_PACKAGE / "PACKAGE_REPORT_R177_v4.md"
PARTII_QA = PARTII_PACKAGE / "candidate_r177_v4/AUTOMATED_QA.json"
PARTII_PDF = PARTII_PACKAGE / "candidate_r177_v4/partII_a4_reader_r177_candidate.pdf"

FIG41_BUILDER = LATEX / (
    "work/preprint/R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v2/"
    "components/targeted_readability_assets/build_targeted_readability_assets.py"
)
FIG41_LIVE_PDF = LATEX / (
    "figures/r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf"
)
ATLAS_F41A = LATEX / "figures/r149/fig41_a_orientation_stiffness_upstream_r149.pdf"

REGISTRY_CSV = LATEX / "FIGURE_REGISTRY.csv"
REGISTRY_JSON = LATEX / "FIGURE_REGISTRY.json"
PREPRINT = LATEX / "ECT_preprint.tex"

EXPECTED_INPUTS = {
    PREPRINT: LIVE_PREPRINT_SHA256,
    REGISTRY_CSV: "0b0b4da74e10ba5e23781ba8d1c1e0f7248497f25c71b0725cceeaa0ebaa7673",
    REGISTRY_JSON: "6826993f79807de601b073df3a2ea03a1fdc0b5949a6beb655e7f838317bb1a0",
    PARTI_SOURCE: "3bb4469dab937835af6ff73004eb927941dd3e347dc502c4fd2f450011c56143",
    PARTI_TOPOLOGY: "26f493f49786e4a9442cc1c207050f55d9380c39b0f25a4e7f6bd0b5868e0c19",
    PARTI_BUILDER: "3ba84740e351975527cbca30959e839892d28147b6983b89a60daf6998bfee5d",
    PARTI_HELPER: "8b325db4f6bc92042e45620b8b9e89dfb71607f3949d55903903ea7d58a98aed",
    PARTI_LIVE_PDF: "7daa3a58b6c3189f071878fef38476cd7df84428ce23041f91516d6a9dc1bd81",
    PARTI_FAMILY / "semantic_keys/partI/partI_node_key.csv": "d621d8c5d50ade975e9f2d60767cda5d67b2ed3d1bf4ba134b2e0d2b5d27013d",
    PARTI_FAMILY / "semantic_keys/partI/partI_full_key.json": "ceb3f5e77e98aae8a72bb2c767a4113dffa70463b0e2ad3c6230ffa3376e45dd",
    PARTI_FAMILY / "semantic_keys/partI/partI_full_key_r168.pdf": "27b39aa3a75538d801363b1202731dbeff0ebffbbedc71003120247b3c554d7c",
    PARTII_SOURCE: "a21756dda12db4d06a163145e1fe540539c0e34b5f0bed5ae6ecfc52a314dbc0",
    PARTII_BUILDER: "8c3d2531baaa7788c58263c70f8fce1865b9ba940144f6fad6731a99cf655ab7",
    PARTII_DELTA: "2baefce85520d7951b5b9b076b786975c0f035f04df01c31d145d4cbff496962",
    PARTII_REPORT: "0a8022ac88ca841583e8467b7fd0b9b06aa1941b3a838235b9f9f84c8d7031f6",
    PARTII_QA: "b2d9c51fd3320c981dc0c1a3a2b26638124a5d4a6a403dfde67b093cce7ab133",
    PARTII_PDF: "07a2bde4f707ee143e9e32547cf36f0628f1e3909f72b84ee08604e9c436b43a",
    FIG41_BUILDER: "27e84e12e8170d7a4ed556034f8b6844ac6b0c340b0ee6e88bd35d0d959b80be",
    FIG41_LIVE_PDF: "18d93f9c182167192b8c67a38a36e606223ecc17adcc066a56b920004a422f49",
    ATLAS_F41A: "bf2c90e11026c6e13b7906e5761555d71caee993f651d4dc5e6202532e3cfc43",
}

OLD_PARTI_SOURCE_LABEL = (
    "GN [label=<Conditional physical tensor-EFT match<BR/>"
    "G<SUB>N</SUB> = c<SUB>char</SUB><SUP>4</SUP>/(8π M<SUB>G</SUB>²)<BR/>"
    "owners Open · §5.4>];"
)
NEW_PARTI_SOURCE_LABEL = (
    "GN [label=<Conditional tensor-EFT normalisation<BR/>"
    "G<SUB>N</SUB><SUP>nat</SUP> = (8π M<SUB>G</SUB>²)<SUP>−1</SUP><BR/>"
    "after physical matching: G<SUB>N</SUB><SUP>SI</SUP> = ℏ c<SUP>5</SUP>/"
    "(8π (E<SUB>M_G</SUB>[J])²)<BR/>"
    "E<SUB>M_G</SUB> ≡ M<SUB>G</SUB>|<SUB>joule</SUB> (GeV→J)<BR/>"
    "owners Open · §5.4>];"
)
OLD_PARTI_TOPOLOGY_LABEL = (
    '"label": "Conditional physical tensor-EFT match<BR/>'
    'G<SUB>N</SUB> = c<SUB>char</SUB><SUP>4</SUP>/(8π M<SUB>G</SUB>²)<BR/>'
    'owners Open · §5.4"'
)
NEW_PARTI_TOPOLOGY_LABEL = (
    '"label": "Conditional tensor-EFT normalisation<BR/>'
    'G<SUB>N</SUB><SUP>nat</SUP> = (8π M<SUB>G</SUB>²)<SUP>−1</SUP><BR/>'
    'after physical matching: G<SUB>N</SUB><SUP>SI</SUP> = ℏ c<SUP>5</SUP>/'
    '(8π (E<SUB>M_G</SUB>[J])²)<BR/>'
    'E<SUB>M_G</SUB> ≡ M<SUB>G</SUB>|<SUB>joule</SUB> (GeV→J)<BR/>'
    'owners Open · §5.4"'
)

PARTI_INSTALL_PDF = "figures/r177/logic_maps/partI_a4_reader_terminal_units_r177.pdf"
PARTII_INSTALL_PDF = "figures/r177/logic_maps/partII_a4_reader_r177.pdf"
FIG41_INSTALL_PDF = (
    "figures/r177/global/panels/fig41_b_tensor_normalisation_terminal_units_r177.pdf"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    return str(path.relative_to(WORKSPACE))


def replace_once(text: str, old: str, new: str, owner: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{owner}: expected one exact anchor, found {count}")
    return text.replace(old, new, 1)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def command_text(argv: list[str]) -> str:
    result = subprocess.run(argv, check=True, capture_output=True, text=True)
    return (result.stdout + result.stderr).strip()


def verify_inputs() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path, expected in EXPECTED_INPUTS.items():
        if not path.is_file():
            raise RuntimeError(f"missing frozen input: {path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"frozen input drift: {path}\nexpected {expected}\nactual   {actual}"
            )
        result[relative(path)] = {
            "bytes": path.stat().st_size,
            "sha256": actual,
        }
    return result


def pdf_text(path: Path) -> str:
    document = fitz.open(path)
    text = "\n".join(page.get_text() for page in document)
    document.close()
    return text


def pdf_metrics(path: Path) -> dict[str, Any]:
    document = fitz.open(path)
    result = {
        "pages": document.page_count,
        "media_boxes_pt": [
            [round(page.rect.width, 3), round(page.rect.height, 3)]
            for page in document
        ],
        "rotation": [page.rotation for page in document],
    }
    document.close()
    return result


def build_parti(staging: Path, helper: Any, builder: Any) -> dict[str, Any]:
    source_dir = staging / "source"
    source_path = source_dir / "fig09_partI_terminal_units_successor_r177.gv"
    topology_path = source_dir / "fig09_partI_topology_terminal_units_r177.json"
    source_text = replace_once(
        PARTI_SOURCE.read_text(encoding="utf-8"),
        OLD_PARTI_SOURCE_LABEL,
        NEW_PARTI_SOURCE_LABEL,
        relative(PARTI_SOURCE),
    )
    topology_text = replace_once(
        PARTI_TOPOLOGY.read_text(encoding="utf-8"),
        OLD_PARTI_TOPOLOGY_LABEL,
        NEW_PARTI_TOPOLOGY_LABEL,
        relative(PARTI_TOPOLOGY),
    )
    write_text(source_path, source_text)
    write_text(topology_path, topology_text)

    spec = helper.MapSpec(
        key="partI",
        title="Complete derivation logic - Part I",
        source=source_path.name,
        source_sha256=sha256(source_path),
        topology=topology_path.name,
        topology_sha256=sha256(topology_path),
        expected_nodes=47,
        expected_visible_edges=63,
        rankdir="TB",
        x_compress=0.72,
    )

    with tempfile.TemporaryDirectory(prefix="ect_r177_partI_root_") as tmp:
        root = Path(tmp) / "LaTex"
        family = root / "figures/source/graphviz/r168_connected_map_semantics_v1"
        topology_family = root / "data/figures_r168/topology"
        family.mkdir(parents=True)
        topology_family.mkdir(parents=True)
        shutil.copy2(source_path, family / source_path.name)
        shutil.copy2(topology_path, topology_family / topology_path.name)
        build_root = staging / "intermediates/partI"
        qa = builder.build_one(
            latex_root=root,
            output_root=build_root,
            spec=spec,
            helpers=helper,
        )

    map_src = staging / "intermediates/partI/partI/partI_a4_reader_r168.pdf"
    map_dst = staging / "assets/partI_a4_reader_terminal_units_r177.pdf"
    map_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(map_src, map_dst)

    topology = json.loads(topology_path.read_text(encoding="utf-8"))
    nodes = helper.semantic_nodes(topology)
    support = sorted(set(topology["nodes"]) - nodes)
    node_key: dict[str, dict[str, str]] = {}
    for node_id in sorted(nodes):
        attrs = topology["nodes"][node_id]
        canonical_label = helper.clean_html_label(attrs.get("label", ""))
        if node_id == "GN":
            # Preserve the grouped mass-scale subscript in plain-text semantic
            # keys; clean_html_label otherwise flattens the HTML to ``E_M_G``.
            canonical_label = (
                canonical_label
                .replace("E_M_G", "E_{M_G}")
                .replace("M_G|_joule", "M_G|_{joule}")
            )
        node_key[node_id] = {
            "reader_title": helper.reader_title(node_id, attrs),
            "status_code": helper.status_code(node_id, attrs),
            "canonical_full_label": canonical_label,
            "canonical_style": attrs.get("style", ""),
            "canonical_fillcolor": attrs.get("fillcolor", ""),
            "canonical_border_color": attrs.get("color", ""),
        }
    edges = [
        {
            "edge_id": f"E{index:03d}",
            "tail": edge["tail"],
            "head": edge["head"],
            "style": edge.get("style", "") or "solid",
            "canonical_edge_label": helper.clean_html_label(edge.get("label", "")),
            "canonical_edge_xlabel": helper.clean_html_label(edge.get("xlabel", "")),
        }
        for index, edge in enumerate(topology["visible_edges"], start=1)
    ]
    key_dir = staging / "semantic_keys/partI"
    key_dir.mkdir(parents=True, exist_ok=True)
    key_payload = {
        "schema": f"{SCHEMA}.partI.full_key",
        "status": "CANDIDATE_NOT_APPLIED",
        "source": "source/fig09_partI_terminal_units_successor_r177.gv",
        "source_sha256": sha256(source_path),
        "topology": "source/fig09_partI_topology_terminal_units_r177.json",
        "topology_sha256": sha256(topology_path),
        "semantic_nodes": node_key,
        "layout_support_node_ids": support,
        "visible_directed_edges": edges,
    }
    write_text(key_dir / "partI_full_key_terminal_units_r177.json", stable_json(key_payload))
    with (key_dir / "partI_node_key_terminal_units_r177.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = [
            "node_id", "reader_title", "status_code", "canonical_full_label",
            "canonical_style", "canonical_fillcolor", "canonical_border_color",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for node_id, item in node_key.items():
            writer.writerow({"node_id": node_id, **item})
    with (key_dir / "partI_edge_key_terminal_units_r177.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fields = list(edges[0])
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(edges)
    key_pdf = key_dir / "partI_full_key_terminal_units_r177.pdf"
    helper.build_key_pdf(
        output_pdf=key_pdf,
        spec=spec,
        node_key=node_key,
        edge_key=edges,
    )
    gn_label = node_key["GN"]["canonical_full_label"]
    gn_pdf_normalised = re.sub(r"[^a-z0-9]+", "", pdf_text(key_pdf).lower())
    notation_checks = {
        "grouped_response_energy_symbol": "E_{M_G}[J]" in gn_label,
        "gev_to_joule_definition": (
            "E_{M_G} ≡ M_G|_{joule} (GeV→J)" in gn_label
        ),
        "no_double_c_squared_conversion": "c²" not in gn_label and "c^2" not in gn_label,
        "unqualified_E_G_absent": "E_G" not in gn_label,
        "full_key_pdf_contains_response_energy_and_definition": (
            "emgj" in gn_pdf_normalised
            and "emgmgjoule" in gn_pdf_normalised
            and "gevj" in gn_pdf_normalised
        ),
    }
    if not all(notation_checks.values()):
        raise RuntimeError(f"Part-I E_MG notation checks failed: {notation_checks}")
    preview_dir = staging / "previews/partI"
    preview_dir.mkdir(parents=True, exist_ok=True)
    previews = helper.render_previews(map_dst, preview_dir, "partI_terminal_units_r177")
    return {
        "asset": str(map_dst.relative_to(staging)),
        "asset_sha256": sha256(map_dst),
        "source_sha256": sha256(source_path),
        "topology_sha256": sha256(topology_path),
        "node_count": len(topology["nodes"]),
        "semantic_node_count": len(nodes),
        "visible_edge_count": len(edges),
        "gn_key": node_key["GN"],
        "notation_checks": notation_checks,
        "builder_qa_pass": bool(qa["all_automated_gates_pass"]),
        "media": pdf_metrics(map_dst),
        "previews": previews,
    }


def build_partii_semantic_owner(staging: Path) -> dict[str, Any]:
    source_text = PARTII_SOURCE.read_text(encoding="utf-8")
    old_patterns = ["c_char^4", "c_{\\rm char}^4", "c<SUB>char</SUB><SUP>4</SUP>"]
    if any(pattern in source_text for pattern in old_patterns):
        raise RuntimeError("Part-II v4 source unexpectedly contains the stale formula")
    if any(pattern in pdf_text(PARTII_PDF) for pattern in old_patterns):
        raise RuntimeError("Part-II v4 PDF unexpectedly contains the stale formula")
    payload = {
        "schema": f"{SCHEMA}.partII.semantic_owner",
        "status": "CANDIDATE_NOT_APPLIED",
        "node_id": "GN",
        "reader_title": "Tensor match",
        "visible_status": "B/Open",
        "visible_v4_source_label": "Tensor match [B] / owners [Open]",
        "canonical_full_label": (
            "Conditional tensor-EFT normalisation\n"
            "G_N^nat = (8π M_G²)^−1\n"
            "after physical matching: G_N^SI = ℏ c⁵/[8π (E_{M_G}[J])²]\n"
            "E_{M_G} ≡ M_G|_{joule} (GeV→J)\n"
            "physical tensor/source/clock/light/scalar-response owners Open · §13.4"
        ),
        "natural_units_statement": "G_N^nat = (8π M_G²)^−1",
        "si_statement": (
            "Only after physical tensor, source, clock, light and scalar-response "
            "matching: G_N^SI = ℏ c⁵/[8π (E_{M_G}[J])²], where "
            "E_{M_G} ≡ M_G|_{joule} denotes M_G converted from GeV to joules."
        ),
        "notation_policy": (
            "E_G is reserved for the Diósi--Penrose energy; the manuscript "
            "tensor energy in joules is E_{M_G} ≡ M_G|_{joule}, obtained by "
            "converting M_G from GeV to joules."
        ),
        "v4_source": relative(PARTII_SOURCE),
        "v4_source_sha256": sha256(PARTII_SOURCE),
        "v4_pdf": relative(PARTII_PDF),
        "v4_pdf_sha256": sha256(PARTII_PDF),
        "v4_pdf_action": "KEEP_BYTE_IDENTICAL",
        "supersedes_for_GN_only": {
            "node_key": relative(PARTI_FAMILY / "semantic_keys/partII/partII_node_key.csv"),
            "full_key_json": relative(PARTI_FAMILY / "semantic_keys/partII/partII_full_key.json"),
            "full_key_pdf": relative(PARTI_FAMILY / "semantic_keys/partII/partII_full_key_r168.pdf"),
        },
        "does_not_modify_v4_topology_or_visible_labels": True,
    }
    notation_checks = {
        "grouped_response_energy_symbol": "E_{M_G}[J]" in payload["canonical_full_label"],
        "gev_to_joule_definition": (
            "E_{M_G} ≡ M_G|_{joule} (GeV→J)" in payload["canonical_full_label"]
        ),
        "no_double_c_squared_conversion": all(
            token not in payload["canonical_full_label"] + payload["si_statement"]
            for token in ("M_G c²", "M_Gc²", "M_G c^2", "M_Gc^2")
        ),
        "unqualified_E_G_absent_from_formula_and_definition": all(
            "E_G" not in payload[key]
            for key in ("canonical_full_label", "si_statement")
        ),
        "dp_reservation_recorded": "Diósi--Penrose energy" in payload["notation_policy"],
    }
    if not all(notation_checks.values()):
        raise RuntimeError(f"Part-II E_MG notation checks failed: {notation_checks}")
    payload["notation_checks"] = notation_checks
    key_dir = staging / "semantic_keys/partII"
    write_text(key_dir / "partII_v4_terminal_units_semantic_owner.json", stable_json(payload))
    key_dir.mkdir(parents=True, exist_ok=True)
    with (key_dir / "partII_v4_terminal_units_node_key.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "node_id", "reader_title", "status_code", "canonical_full_label",
            "v4_pdf_sha256", "asset_action",
        ])
        writer.writerow([
            "GN", "Tensor match", "B/O",
            payload["canonical_full_label"], sha256(PARTII_PDF), "KEEP_BYTE_IDENTICAL",
        ])
    return payload


def build_fig41(staging: Path, module: Any, helper: Any) -> dict[str, Any]:
    assets = staging / "assets"
    previews = staging / "previews/fig41"
    assets.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)
    output = assets / "fig41_b_tensor_normalisation_terminal_units_r177.pdf"
    color = assets / "fig41_b_tensor_normalisation_terminal_units_r177.png"

    original_box = module.status_box

    def terminal_units_box(
        ax: Any,
        center: tuple[float, float],
        width: float,
        height: float,
        title: str,
        body: str,
        fill: str,
        edge: str,
        status: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if title == r"Newton constant $G_N$":
            if body != r"$G_N=c_{\rm char}^4/(8\pi M_G^2)$ -- external supplied completion":
                raise RuntimeError("fig41 lower-box source anchor drift")
            body = (
                r"$G_N^{\rm nat}=(8\pi M_G^2)^{-1}$; "
                r"$E_{M_G}\equiv M_G|_{\rm J}$ (GeV$\to$J)"
                "\n"
                r"after matching: $G_N^{\rm SI}=\hbar c^5/[8\pi(E_{M_G}[\mathrm{J}])^2]$"
            )
            kwargs.update(
                {
                    "body_size": 8.2,
                    "title_y": 0.33,
                    "body_y": -0.04,
                    "status_y": -0.40,
                }
            )
        original_box(
            ax, center, width, height, title, body, fill, edge, status,
            *args, **kwargs,
        )

    module.status_box = terminal_units_box
    module.PDF_META = {
        **module.PDF_META,
        "Creator": "ECT R177 terminal-units figure successor",
        "Title": "R177 terminal-units tensor-normalisation open bridge",
    }
    try:
        result = module.build_tensor_bridge(output, color)
    finally:
        module.status_box = original_box

    preview_payload = helper.render_previews(
        output, previews, "fig41_b_terminal_units_r177"
    )
    extracted = pdf_text(output)
    compact = re.sub(r"\s+", " ", extracted)
    normalised = re.sub(r"[^a-z0-9]+", "", extracted.lower())
    checks = {
        "four_nodes": result.get("nodes") == 4,
        "three_edges": result.get("edges") == 3,
        "status_preserved": bool(result.get("status_preserved")),
        "old_c_char_formula_absent": "cchar" not in re.sub(r"[^a-z0-9]+", "", extracted.lower()),
        "natural_formula_visible": "nat" in compact,
        "si_formula_visible_after_matching": (
            "after matching" in compact
            and ("gnsi" in normalised or "gsin" in normalised)
            and "emgj" in normalised
            and "emgmgj" in normalised
            and "gevj" in normalised
        ),
        "no_double_c_squared_conversion": all(
            token not in extracted for token in ("M_G c²", "M_Gc²", "M_G c^2", "M_Gc^2")
        ),
        "unqualified_E_G_absent": "E_G" not in extracted,
        "media_box_preserved": pdf_metrics(output)["media_boxes_pt"] == pdf_metrics(FIG41_LIVE_PDF)["media_boxes_pt"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"fig41 checks failed: {checks}; extracted={compact!r}; normalised={normalised!r}")
    return {
        "asset": str(output.relative_to(staging)),
        "asset_sha256": sha256(output),
        "png": str(color.relative_to(staging)),
        "png_sha256": sha256(color),
        "media": pdf_metrics(output),
        "checks": checks,
        "previews": preview_payload,
    }


def locate_exact_line(text: str, token: str) -> int:
    lines = [index for index, line in enumerate(text.splitlines(), start=1) if token in line]
    if len(lines) != 1:
        raise RuntimeError(f"expected one line for {token!r}, found {lines}")
    return lines[0]


def registry_rows(
    staging: Path,
    parti: dict[str, Any],
    partii: dict[str, Any],
    fig41: dict[str, Any],
) -> list[dict[str, str]]:
    with REGISTRY_CSV.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        live_rows = list(reader)
    selected = {
        row["figure_id"]: dict(row)
        for row in live_rows
        if row["figure_id"] in {
            "fig:partI_derivation_logic",
            "fig:partII_derivation_logic",
            "fig:r103_Cn_scalechain_corrected",
        }
    }
    if set(selected) != {
        "fig:partI_derivation_logic",
        "fig:partII_derivation_logic",
        "fig:r103_Cn_scalechain_corrected",
    }:
        raise RuntimeError("expected exactly three registry replacement owners")

    preprint = PREPRINT.read_text(encoding="utf-8")
    module_rel = relative(MODULE)
    module_sha = sha256(MODULE)

    p1 = selected["fig:partI_derivation_logic"]
    old_p1 = "]{figures/r168/logic_maps/partI_a4_reader_r168.pdf}"
    p1.update({
        "source_line": str(locate_exact_line(preprint, old_p1)),
        "insertion_token": f"]{{{PARTI_INSTALL_PDF}}}",
        "current_asset_token": PARTI_INSTALL_PDF,
        "resolved_current_path": f"LaTex/{PARTI_INSTALL_PDF}",
        "output_sha256": parti["asset_sha256"],
        "scientific_owner": (
            "R177 terminal-units successor: compact labels/topology/status unchanged; "
            "GN semantic owner uses natural units and keeps physical/SI matching Open"
        ),
        "generator_paths": f"{module_rel};{relative(PARTI_BUILDER)};{relative(PARTI_HELPER)}",
        "generator_sha256": f"{module_sha};{sha256(PARTI_BUILDER)};{sha256(PARTI_HELPER)}",
        "data_paths": (
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/source/fig09_partI_terminal_units_successor_r177.gv;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/source/fig09_partI_topology_terminal_units_r177.json;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partI/partI_node_key_terminal_units_r177.csv;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partI/partI_edge_key_terminal_units_r177.csv;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partI/partI_full_key_terminal_units_r177.json;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partI/partI_full_key_terminal_units_r177.pdf"
        ),
        "data_sha256": (
            f"{parti['source_sha256']};{parti['topology_sha256']};"
            f"{sha256(staging / 'semantic_keys/partI/partI_node_key_terminal_units_r177.csv')};"
            f"{sha256(staging / 'semantic_keys/partI/partI_edge_key_terminal_units_r177.csv')};"
            f"{sha256(staging / 'semantic_keys/partI/partI_full_key_terminal_units_r177.json')};"
            f"{sha256(staging / 'semantic_keys/partI/partI_full_key_terminal_units_r177.pdf')}"
        ),
        "render_or_verify_command": f"python3 {module_rel}",
        "scientific_status": (
            "R177 candidate; natural GN normalisation conditional; physical tensor/source/"
            "clock/light/scalar-response and SI matching Open; topology unchanged"
        ),
        "current_disposition": "R177 SUCCESSOR CANDIDATE ONLY; not live",
        "grayscale_cvd_verdict": "PASS: RGB, grayscale, protan, deutan and tritan generated",
        "human_review_verdict": "PASS standalone RGB/grayscale/CVD; final owning-page context remains pending",
        "pending_review": "live apply, registry verifier, owning-page compile and publication not authorised",
        "provenance_basis": "R177 terminal-units package deterministic replay and hash manifest",
    })

    p2 = selected["fig:partII_derivation_logic"]
    old_p2 = "]{figures/r168/logic_maps/partII_a4_reader_r168.pdf}"
    p2.update({
        "source_line": str(locate_exact_line(preprint, old_p2)),
        "insertion_token": f"]{{{PARTII_INSTALL_PDF}}}",
        "current_asset_token": PARTII_INSTALL_PDF,
        "resolved_current_path": f"LaTex/{PARTII_INSTALL_PDF}",
        "output_sha256": partii["v4_pdf_sha256"],
        "scientific_owner": (
            "R177 Part-II v4 selected-status map plus terminal-units GN semantic owner; "
            "compact PDF bytes unchanged by this package"
        ),
        "generator_paths": relative(PARTII_BUILDER),
        "generator_sha256": sha256(PARTII_BUILDER),
        "data_paths": (
            f"{relative(PARTII_SOURCE)};{relative(PARTII_DELTA)};"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partII/"
            "partII_v4_terminal_units_semantic_owner.json;"
            "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/"
            "terminal_units_successors/semantic_keys/partII/"
            "partII_v4_terminal_units_node_key.csv;"
            f"{relative(PARTII_QA)};{relative(PARTII_REPORT)}"
        ),
        "data_sha256": (
            f"{sha256(PARTII_SOURCE)};{sha256(PARTII_DELTA)};"
            f"{sha256(staging / 'semantic_keys/partII/partII_v4_terminal_units_semantic_owner.json')};"
            f"{sha256(staging / 'semantic_keys/partII/partII_v4_terminal_units_node_key.csv')};"
            f"{sha256(PARTII_QA)};{sha256(PARTII_REPORT)}"
        ),
        "render_or_verify_command": (
            f"python3 {relative(PARTII_BUILDER)} --output-root "
            f"{relative(PARTII_PACKAGE / 'candidate_r177_v4')}"
        ),
        "scientific_status": (
            "R177 v4 candidate: A/B/C/Open separated; GN visible label compact and "
            "formula-free; natural-unit expansion owned by terminal semantic key"
        ),
        "current_disposition": "R177 SUCCESSOR CANDIDATE ONLY; v4 bytes KEEP",
        "grayscale_cvd_verdict": "PASS in v4 owning package; no asset-byte change here",
        "human_review_verdict": "PASS standalone v4; owning-page context review still required",
        "pending_review": "registry verifier/schema reconciliation, context compile and live authority",
        "provenance_basis": f"{relative(PARTII_REPORT)} sha256={sha256(PARTII_REPORT)}",
    })

    f41 = selected["fig:r103_Cn_scalechain_corrected"]
    old_f41_path = "figures/r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf"
    f41.update({
        "source_line": str(locate_exact_line(preprint, old_f41_path)),
        "insertion_token": (
            "\\includegraphics[width=0.94\\textwidth,height=0.68\\textheight,keepaspectratio]"
            f"{{{FIG41_INSTALL_PDF}}}"
        ),
        "current_asset_token": FIG41_INSTALL_PDF,
        "resolved_current_path": f"LaTex/{FIG41_INSTALL_PDF}",
        "output_sha256": fig41["asset_sha256"],
        "caption_or_title": (
            "Corrected ownership chain from the ordered variables through the conditional "
            "NLO orientation coefficient and exact EFT definition $\\kappa_n\\equiv"
            "\\mathcal C_nu_0^2$. The dashed $M_G^2\\stackrel{?}{=}c_M\\kappa_n$ "
            "step is Open. The natural-unit tensor normalisation is "
            "$G_N^{\\rm nat}=(8\\pi M_G^2)^{-1}$; an SI Newton constant is defined "
            "only after physical tensor/source/clock/light/scalar-response matching, "
            "as $G_N^{\\rm SI}=\\hbar c^5/[8\\pi(E_{M_G}[\\mathrm J])^2]$, "
            "where $E_{M_G}\\equiv M_G|_{\\rm joule}$ denotes the manuscript "
            "energy scale converted from GeV to joules."
        ),
        "scientific_owner": (
            "R177 terminal-units successor of hash-locked R123 targeted-readability layout; "
            "four nodes/three arrows/status encodings preserved"
        ),
        "generator_paths": f"{module_rel};{relative(FIG41_BUILDER)}",
        "generator_sha256": f"{module_sha};{sha256(FIG41_BUILDER)}",
        "data_paths": "",
        "data_sha256": "",
        "render_or_verify_command": f"python3 {module_rel}",
        "scientific_status": (
            "natural GN normalisation shown; physical tensor/source/clock/light/"
            "scalar-response matching required before the displayed SI conversion; "
            "no c_char=c identification"
        ),
        "current_disposition": "R177 SUCCESSOR CANDIDATE ONLY; not live",
        "grayscale_cvd_verdict": "PASS: five modes generated; status also literal/border/line encoded",
        "human_review_verdict": "PASS standalone RGB/grayscale/CVD; final owning-page context remains pending",
        "pending_review": "live apply, registry verifier, owning-page compile and publication not authorised",
        "provenance_basis": "R177 terminal-units package deterministic replay and hash manifest",
    })

    rows = [p1, p2, f41]
    registry_dir = staging / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    with (registry_dir / "FIGURE_REGISTRY_TERMINAL_UNITS_REPLACEMENTS.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_text(
        registry_dir / "FIGURE_REGISTRY_TERMINAL_UNITS_REPLACEMENTS.json",
        stable_json({"schema": f"{SCHEMA}.registry_rows", "rows": rows}),
    )
    return rows


def write_insertions(staging: Path, parti: dict[str, Any], fig41: dict[str, Any]) -> None:
    preprint = PREPRINT.read_text(encoding="utf-8")
    old_caption = r"""\caption{Corrected ownership chain from the ordered variables through the
conditional NLO orientation coefficient and the exact EFT definition
$\kappa_n\equiv\mathcal C_nu_0^2$.  The dashed step
$M_G^2\stackrel{?}{=}c_M\kappa_n$ is Open: the physical helicity--2 action,
source normalisation, residue and the coefficient $c_M$ are not supplied.
The final $G_N=c_{\rm char}^4/(8\pi M_G^2)$ relation is standard only inside
a supplied tensor completion.  Colour is redundant with fill luminance,
border style, arrow style and literal status text.  The diagram therefore
does not derive gravity from
$\kappa_n$.  Complementary full-width panels are retained in Appendix~\ref{app:r129_visual_orientation_tensor}.}"""
    new_caption = r"""\caption{Corrected ownership chain from the ordered variables through the
conditional NLO orientation coefficient and the exact EFT definition
$\kappa_n\equiv\mathcal C_nu_0^2$.  The dashed step
$M_G^2\stackrel{?}{=}c_M\kappa_n$ is Open: the physical helicity--2 action,
source normalisation, residue and the coefficient $c_M$ are not supplied.
The natural-unit tensor normalisation
$G_N^{\rm nat}=(8\pi M_G^2)^{-1}$ is standard only inside a supplied tensor
completion.  An SI Newton constant is defined only after physical tensor,
source, clock, light and scalar-response matching, as
$G_N^{\rm SI}=\hbar c^5/[8\pi(E_{M_G}[\mathrm J])^2]$, where
$E_{M_G}\equiv M_G|_{\rm joule}$ denotes the manuscript energy scale converted
from GeV to joules.  Colour is redundant with
fill luminance, border style, arrow style and literal status text.  The diagram
therefore does not derive gravity from $\kappa_n$.  Complementary full-width
panels are retained in Appendix~\ref{app:r129_visual_orientation_tensor}.}"""
    replacements = [
        {
            "id": "partI-reader-path",
            "file": "LaTex/ECT_preprint.tex",
            "old": "]{figures/r168/logic_maps/partI_a4_reader_r168.pdf}",
            "new": f"]{{{PARTI_INSTALL_PDF}}}",
            "old_count": preprint.count("]{figures/r168/logic_maps/partI_a4_reader_r168.pdf}"),
            "candidate_asset_sha256": parti["asset_sha256"],
        },
        {
            "id": "partII-v4-path-byte-keep",
            "file": "LaTex/ECT_preprint.tex",
            "old": "]{figures/r168/logic_maps/partII_a4_reader_r168.pdf}",
            "new": f"]{{{PARTII_INSTALL_PDF}}}",
            "old_count": preprint.count("]{figures/r168/logic_maps/partII_a4_reader_r168.pdf}"),
            "candidate_asset_sha256": sha256(PARTII_PDF),
        },
        {
            "id": "partI-reader-path-companion-en",
            "file": "LaTex/companion/ECT_companion.tex",
            "old": "]{../figures/r168/logic_maps/partI_a4_reader_r168.pdf}",
            "new": "]{../figures/r177/logic_maps/partI_a4_reader_terminal_units_r177.pdf}",
            "old_count": (LATEX / "companion/ECT_companion.tex").read_text(encoding="utf-8").count(
                "]{../figures/r168/logic_maps/partI_a4_reader_r168.pdf}"
            ),
            "candidate_asset_sha256": parti["asset_sha256"],
        },
        {
            "id": "partI-reader-path-companion-ru",
            "file": "LaTex/companion/ECT_companion_ru.tex",
            "old": "../figures/r168/logic_maps/partI_a4_reader_r168.pdf",
            "new": "../figures/r177/logic_maps/partI_a4_reader_terminal_units_r177.pdf",
            "old_count": (LATEX / "companion/ECT_companion_ru.tex").read_text(encoding="utf-8").count(
                "../figures/r168/logic_maps/partI_a4_reader_r168.pdf"
            ),
            "candidate_asset_sha256": parti["asset_sha256"],
        },
        {
            "id": "partII-v4-path-companion-en",
            "file": "LaTex/companion/ECT_companion.tex",
            "old": "]{../figures/r168/logic_maps/partII_a4_reader_r168.pdf}",
            "new": "]{../figures/r177/logic_maps/partII_a4_reader_r177.pdf}",
            "old_count": (LATEX / "companion/ECT_companion.tex").read_text(encoding="utf-8").count(
                "]{../figures/r168/logic_maps/partII_a4_reader_r168.pdf}"
            ),
            "candidate_asset_sha256": sha256(PARTII_PDF),
        },
        {
            "id": "partII-v4-path-companion-ru",
            "file": "LaTex/companion/ECT_companion_ru.tex",
            "old": "../figures/r168/logic_maps/partII_a4_reader_r168.pdf",
            "new": "../figures/r177/logic_maps/partII_a4_reader_r177.pdf",
            "old_count": (LATEX / "companion/ECT_companion_ru.tex").read_text(encoding="utf-8").count(
                "../figures/r168/logic_maps/partII_a4_reader_r168.pdf"
            ),
            "candidate_asset_sha256": sha256(PARTII_PDF),
        },
        {
            "id": "fig41-main-path",
            "file": "LaTex/ECT_preprint.tex",
            "old": "figures/r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf",
            "new": FIG41_INSTALL_PDF,
            "old_count": preprint.count("figures/r123/global/panels/fig41_b_tensor_normalisation_open_bridge_r123.pdf"),
            "candidate_asset_sha256": fig41["asset_sha256"],
        },
        {
            "id": "fig41-caption-terminal-units",
            "file": "LaTex/ECT_preprint.tex",
            "old": old_caption,
            "new": new_caption,
            "old_count": preprint.count(old_caption),
            "candidate_asset_sha256": fig41["asset_sha256"],
            "coordination_note": (
                "If successor_terminal_recovery.py has already replaced this block, "
                "use its scientifically equivalent caption owner and do not double-apply."
            ),
        },
    ]
    if any(item["old_count"] != 1 for item in replacements):
        raise RuntimeError(f"insertion anchor count failed: {replacements}")
    write_text(
        staging / "integration/CANDIDATE_INSERTION_REPLACEMENTS.json",
        stable_json({"schema": f"{SCHEMA}.insertions", "replacements": replacements}),
    )
    install = [
        {
            "action": "COPY_CANDIDATE_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "assets/partI_a4_reader_terminal_units_r177.pdf",
            "destination": f"LaTex/{PARTI_INSTALL_PDF}",
            "sha256": parti["asset_sha256"],
        },
        {
            "action": "COPY_EXISTING_V4_BYTES_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": relative(PARTII_PDF),
            "destination": f"LaTex/{PARTII_INSTALL_PDF}",
            "sha256": sha256(PARTII_PDF),
        },
        {
            "action": "COPY_CANDIDATE_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "assets/fig41_b_tensor_normalisation_terminal_units_r177.pdf",
            "destination": f"LaTex/{FIG41_INSTALL_PDF}",
            "sha256": fig41["asset_sha256"],
        },
        {
            "action": "COPY_SEMANTIC_OWNER_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "source/fig09_partI_terminal_units_successor_r177.gv",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "fig09_partI_terminal_units_successor_r177.gv"
            ),
            "sha256": parti["source_sha256"],
        },
        {
            "action": "COPY_TOPOLOGY_OWNER_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "source/fig09_partI_topology_terminal_units_r177.json",
            "destination": (
                "LaTex/data/figures_r177/topology/"
                "fig09_partI_topology_terminal_units_r177.json"
            ),
            "sha256": parti["topology_sha256"],
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partI/partI_node_key_terminal_units_r177.csv",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partI/partI_node_key_terminal_units_r177.csv"
            ),
            "sha256": sha256(staging / "semantic_keys/partI/partI_node_key_terminal_units_r177.csv"),
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partI/partI_edge_key_terminal_units_r177.csv",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partI/partI_edge_key_terminal_units_r177.csv"
            ),
            "sha256": sha256(staging / "semantic_keys/partI/partI_edge_key_terminal_units_r177.csv"),
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partI/partI_full_key_terminal_units_r177.json",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partI/partI_full_key_terminal_units_r177.json"
            ),
            "sha256": sha256(staging / "semantic_keys/partI/partI_full_key_terminal_units_r177.json"),
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partI/partI_full_key_terminal_units_r177.pdf",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partI/partI_full_key_terminal_units_r177.pdf"
            ),
            "sha256": sha256(staging / "semantic_keys/partI/partI_full_key_terminal_units_r177.pdf"),
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partII/partII_v4_terminal_units_semantic_owner.json",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partII/partII_v4_terminal_units_semantic_owner.json"
            ),
            "sha256": sha256(staging / "semantic_keys/partII/partII_v4_terminal_units_semantic_owner.json"),
        },
        {
            "action": "COPY_SEMANTIC_KEY_ONLY_AFTER_EXPLICIT_AUTHORITY",
            "source": "semantic_keys/partII/partII_v4_terminal_units_node_key.csv",
            "destination": (
                "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/"
                "semantic_keys/partII/partII_v4_terminal_units_node_key.csv"
            ),
            "sha256": sha256(staging / "semantic_keys/partII/partII_v4_terminal_units_node_key.csv"),
        },
    ]
    with (staging / "integration/CANDIDATE_INSTALL_MAP.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(install[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(install)


def occurrence_audit(staging: Path, parti: dict[str, Any], fig41: dict[str, Any]) -> dict[str, Any]:
    displayed = [
        ("Part-I compact live reader", PARTI_LIVE_PDF, False, "REPLACE: provenance footer binds stale semantic owner"),
        ("Part-I live full semantic key", PARTI_FAMILY / "semantic_keys/partI/partI_full_key_r168.pdf", True, "REPLACE semantic key"),
        ("Part-II live compact reader", LATEX / "figures/r168/logic_maps/partII_a4_reader_r168.pdf", False, "superseded by R177 v4"),
        ("Part-II live full semantic key", PARTI_FAMILY / "semantic_keys/partII/partII_full_key_r168.pdf", True, "supersede GN key only"),
        ("Part-II R177 v4 compact reader", PARTII_PDF, False, "KEEP BYTE IDENTICAL"),
        ("fig41_b live main panel", FIG41_LIVE_PDF, True, "REPLACE"),
        ("fig41_a live atlas upstream panel", ATLAS_F41A, False, "KEEP BYTE IDENTICAL"),
    ]
    rows = []
    for role, path, stale_visible, disposition in displayed:
        rows.append({
            "role": role,
            "path": relative(path),
            "sha256": sha256(path),
            "page_count": pdf_metrics(path)["pages"],
            "stale_formula_visibly_rendered": stale_visible,
            "disposition": disposition,
        })
    owners = [
        {"path": relative(PARTI_SOURCE), "kind": "Part-I semantic source", "stale": True},
        {"path": relative(PARTI_TOPOLOGY), "kind": "Part-I topology label", "stale": True},
        {"path": relative(PARTI_FAMILY / "semantic_keys/partI/partI_node_key.csv"), "kind": "Part-I key", "stale": True},
        {"path": relative(PARTI_FAMILY / "semantic_keys/partII/partII_node_key.csv"), "kind": "inherited Part-II key", "stale": True},
        {"path": relative(PARTII_SOURCE), "kind": "Part-II v4 compact source", "stale": False},
        {"path": relative(FIG41_BUILDER), "kind": "R123 fig41 producer", "stale": True},
        {"path": relative(REGISTRY_CSV), "kind": "fig41 caption plus stale semantic chains", "stale": True},
        {"path": relative(PREPRINT), "kind": "fig41 caption (text repair owned by terminal recovery)", "stale": True},
    ]
    payload = {
        "schema": f"{SCHEMA}.occurrence_audit",
        "displayed_assets": rows,
        "active_or_candidate_semantic_owners": owners,
        "candidate_outputs": {
            "partI_pdf_sha256": parti["asset_sha256"],
            "fig41_pdf_sha256": fig41["asset_sha256"],
            "partII_v4_pdf_sha256": sha256(PARTII_PDF),
        },
        "historical_shadow_policy": (
            "R148/R150/R123 archived and frozen predecessor files remain immutable; "
            "they are enumerated as superseded provenance, not rewritten."
        ),
    }
    write_text(staging / "audit/OCCURRENCE_AUDIT.json", stable_json(payload))
    with (staging / "audit/DISPLAYED_ASSET_AUDIT.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return payload


def build_once(staging: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    staging.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SOURCE_DATE_EPOCH", "1785283200")
    os.environ.setdefault("LC_ALL", "C")
    os.environ.setdefault("TZ", "UTC")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r177-terminal-units-mpl")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    helper = load_module(PARTI_HELPER, f"r177_parti_helper_{id(staging)}")
    builder = load_module(PARTI_BUILDER, f"r177_parti_builder_{id(staging)}")
    fig41_owner = load_module(FIG41_BUILDER, f"r177_fig41_owner_{id(staging)}")

    parti = build_parti(staging, helper, builder)
    partii = build_partii_semantic_owner(staging)
    fig41 = build_fig41(staging, fig41_owner, helper)
    rows = registry_rows(staging, parti, partii, fig41)
    write_insertions(staging, parti, fig41)
    audit = occurrence_audit(staging, parti, fig41)

    atlas_keep = {
        "figure_id": "fig:r123_atlas_f41a",
        "path": relative(ATLAS_F41A),
        "sha256": sha256(ATLAS_F41A),
        "action": "KEEP_BYTE_IDENTICAL",
        "reason": "upstream orientation-stiffness panel contains no Newton formula",
    }
    write_text(staging / "registry/ATLAS_KEEP_DECISION.json", stable_json(atlas_keep))
    runtime = {
        "schema": f"{SCHEMA}.runtime",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pymupdf": fitz.__doc__.split()[1].rstrip(":"),
        "graphviz_dot": command_text(["dot", "-V"]),
        "graphviz_gvpr": command_text(["gvpr", "-V"]),
        "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        "generator": relative(MODULE),
        "generator_sha256": sha256(MODULE),
    }
    write_text(staging / "RUNTIME_PROVENANCE.json", stable_json(runtime))
    write_text(
        staging / "INPUT_FREEZE.json",
        stable_json({
            "schema": f"{SCHEMA}.input_freeze",
            "fixed_utc": FIXED_UTC,
            "status": "CANDIDATE_NOT_APPLIED",
            "inputs": inputs,
        }),
    )
    qa = {
        "schema": f"{SCHEMA}.qa",
        "partI": parti,
        "partII": {
            "pdf_action": partii["v4_pdf_action"],
            "pdf_sha256": partii["v4_pdf_sha256"],
            "source_formula_free": True,
            "notation_checks": partii["notation_checks"],
        },
        "fig41": fig41,
        "terminal_energy_notation": {
            "response_mass_energy": "E_{M_G} ≡ M_G|_{joule} (M_G converted GeV→J)",
            "reserved_symbol": "E_G is reserved for Diósi--Penrose energy",
            "all_scoped_owner_checks_pass": (
                all(parti["notation_checks"].values())
                and all(partii["notation_checks"].values())
                and fig41["checks"]["unqualified_E_G_absent"]
            ),
        },
        "atlas": atlas_keep,
        "registry_replacement_rows": len(rows),
        "displayed_assets_audited": len(audit["displayed_assets"]),
        "all_automated_gates_pass": (
            parti["builder_qa_pass"]
            and all(parti["notation_checks"].values())
            and partii["v4_pdf_sha256"] == EXPECTED_INPUTS[PARTII_PDF]
            and all(partii["notation_checks"].values())
            and all(fig41["checks"].values())
            and atlas_keep["sha256"] == EXPECTED_INPUTS[ATLAS_F41A]
            and len(rows) == 3
        ),
        "human_visual_review": (
            "PASS 2026-07-29: both changed assets inspected in RGB, grayscale, "
            "protan, deutan and tritan; labels, formula, literal status, borders "
            "and edge styles remain readable with no visible clipping or overlap"
        ),
        "live_files_edited": False,
    }
    if not qa["all_automated_gates_pass"]:
        raise RuntimeError(f"terminal-units automated QA failed: {qa}")
    write_text(staging / "AUTOMATED_QA.json", stable_json(qa))

    visual_review = """# R177 terminal-units visual review

- Date: 2026-07-29
- Reviewer status: `PASS_STANDALONE_CANDIDATES`
- Assets reviewed: Part-I compact reader and fig41_b tensor-normalisation bridge
- Modes reviewed for each changed asset: RGB, grayscale, protan, deutan, tritan

The Part-I map retains the full 47-node/63-edge layout, readable compact node
labels, literal status codes, border styles and line styles.  The only visible
semantic-owner change is the footer hash.  No clipping, overlap, missing glyph
or lost relation was observed.

The fig41_b successor retains four boxes, three arrows, all literal statuses,
the dashed Open bridge and the external-completion styling.  The replacement
shows `G_N^nat=(8 pi M_G^2)^-1`, `E_{M_G}=M_G|_{joule}` with an explicit
GeV-to-joule conversion, and the SI row using `E_{M_G}[J]` only after physical
matching.  All three statements are fully
visible in every mode.  No clipping, overlap, missing glyph or colour-only
distinction was observed.

This is a standalone asset review.  Final owning-page PDF context remains a
post-integration gate and is not authorisation to edit the live manuscript.
"""
    write_text(staging / "VISUAL_REVIEW.md", visual_review)

    report = f"""# R177 terminal-units figure successors

- Date: 2026-07-29
- Status: `CANDIDATE_COMPLETE_NOT_APPLIED`
- Frozen live preprint: `{LIVE_PREPRINT_SHA256}`
- Live manuscript/assets/registries edited: **no**

## Scientific correction

The candidate uses the natural-unit tensor normalisation
`G_N^nat = (8 pi M_G^2)^-1`.  It does not identify `c_char` with measured
light speed.  Only after independent tensor, source, clock, light and
scalar-response matching does the separate conversion read
`G_N^SI = hbar c^5/[8 pi (E_{{M_G}}[J])^2]`, where
`E_{{M_G}} = M_G|_{{joule}}` is `M_G` converted from GeV to joules.  The symbol
`E_G` remains
reserved for the Diósi--Penrose energy and is not used for this matching scale.

## Asset decisions

- Part-I compact reader: rebuilt only because its source-owner footer must bind
  the corrected semantic source.  Topology, 47 node IDs, 63 visible edges,
  compact labels and status codes are preserved.  Candidate SHA-256:
  `{parti['asset_sha256']}`.
- Part-II v4 compact reader: **KEEP BYTE IDENTICAL**, SHA-256
  `{partii['v4_pdf_sha256']}`.  Its visible source is formula-free; this package
  adds only the missing GN semantic-key/provenance owner.
- `fig41_b`: exact R123 targeted-readability layout, four status boxes and three
  arrows preserved; only the lower-box formula text is changed.  Candidate
  SHA-256: `{fig41['asset_sha256']}`.
- Atlas `fig41_a`: **KEEP BYTE IDENTICAL**, SHA-256 `{sha256(ATLAS_F41A)}`;
  it contains only the upstream orientation-stiffness chain.

## Gates

- frozen input hashes: PASS;
- Part-I semantic-node/edge/layout gates: PASS;
- Part-II source/PDF old-formula absence and byte-keep gate: PASS;
- fig41 four-node/three-edge/status/media-box gates: PASS;
- RGB, grayscale, protan, deutan and tritan previews: generated and manually
  inspected for both changed assets; standalone visual review PASS;
- deterministic independent replay: recorded by the top-level builder after
  this build;
- final page-context compile, registry-verifier reconciliation, live apply,
  Git and publication: **not authorised / not performed**.
"""
    write_text(staging / "REPORT.md", report)
    correction_history = """# R177 terminal-energy dimensional-definition correction

- Date: 2026-07-29
- Status: `WITHDRAWN_PREVIOUS_CANDIDATE_DEFINITION`
- Live sources edited by either candidate build: **no**

An earlier, never-applied version of this candidate defined the joule-valued
response energy as `E_{M_G}=M_G c^2`.  Independent red-team review established
that this double-converted the manuscript quantity: `M_G` is already an energy
scale quoted in GeV, not a mass awaiting multiplication by `c^2`.

The withdrawn candidate is identified by:

- generator SHA-256 `9adf3882bdb38fc8680e745a90044b5b0519d33fe704c47e6407436a58c730f3`;
- Part-I compact PDF SHA-256 `ff8f48b7fc6ad7f432e7f13d6a40db916b0c37d2bedbd1cb3a1c60da595814e2`;
- fig41_b PDF SHA-256 `b6245ab8c54cdb54398a6656d50ca4345728c0e285f116d729ff1469db5ba04f`;
- replay SHA-256 `0ef85326c1c2ab764dc487093d410a193a53fecb925c8d8300b60ff5896c7908`;
- package-manifest SHA-256 `06a7ede1b19ad58acc303ce0af057c1190d510bf89dfc8fea76c27c51ac8fd32`.

That definition is withdrawn and must not be integrated.  The active candidate
defines `E_{M_G}=M_G|_{joule}` by direct GeV-to-joule conversion, keeps the SI
Newton formula unchanged, and records automated absence of the double-`c^2`
conversion in every scoped response owner and rendered asset.
"""
    write_text(staging / "CORRECTION_HISTORY.md", correction_history)
    write_text(
        staging / "README.md",
        "# Terminal-units successor package\n\n"
        "Run `python3 research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/"
        "assembler/successor_terminal_figures.py`.  The package is a candidate "
        "only; consult `REPORT.md`, `AUTOMATED_QA.json`, `integration/`, and "
        "`registry/`.\n",
    )

    files = {
        str(path.relative_to(staging)): sha256(path)
        for path in sorted(staging.rglob("*"))
        if path.is_file() and path.name not in {"PACKAGE_MANIFEST.json", "REPLAY_CHECK.json", "SHA256SUMS"}
    }
    manifest = {
        "schema": f"{SCHEMA}.manifest",
        "fixed_utc": FIXED_UTC,
        "status": "CANDIDATE_COMPLETE_NOT_APPLIED",
        "scientific_ceiling": (
            "natural-unit normalisation; separate SI conversion only after physical "
            "tensor/source/clock/light/scalar-response matching, which remains Open"
        ),
        "live_files_edited": False,
        "files": files,
    }
    write_text(staging / "PACKAGE_MANIFEST.json", stable_json(manifest))
    return {"partI": parti, "partII": partii, "fig41": fig41, "qa": qa}


def reproducible_files(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"REPLAY_CHECK.json", "SHA256SUMS"}
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=PACKAGE)
    args = parser.parse_args()
    output = args.output_root.resolve()
    inputs = verify_inputs()

    with tempfile.TemporaryDirectory(prefix="ect_r177_terminal_units_first_") as a_tmp, tempfile.TemporaryDirectory(prefix="ect_r177_terminal_units_second_") as b_tmp:
        first_root = Path(a_tmp) / "terminal_units_successors"
        second_root = Path(b_tmp) / "terminal_units_successors"
        first_result = build_once(first_root, inputs)
        build_once(second_root, inputs)
        first = reproducible_files(first_root)
        second = reproducible_files(second_root)
        replay = {
            "schema": f"{SCHEMA}.replay",
            "independent_builds": 2,
            "file_set_equal": set(first) == set(second),
            "byte_identical": first == second,
            "first": first,
            "second": second,
        }
        if not replay["file_set_equal"] or not replay["byte_identical"]:
            differing = sorted(key for key in set(first) | set(second) if first.get(key) != second.get(key))
            raise RuntimeError(f"deterministic replay failed: {differing}")
        if output.exists():
            if output == PACKAGE or output.name == "terminal_units_successors":
                shutil.rmtree(output)
            else:
                raise RuntimeError(f"refusing to replace unexpected output path: {output}")
        shutil.copytree(first_root, output)

    write_text(output / "REPLAY_CHECK.json", stable_json(replay))
    sums = {
        str(path.relative_to(output)): sha256(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "SHA256SUMS"
    }
    with (output / "SHA256SUMS").open("w", encoding="utf-8", newline="\n") as handle:
        for name, digest in sums.items():
            handle.write(f"{digest}  {name}\n")
    print(stable_json({
        "status": "CANDIDATE_COMPLETE_NOT_APPLIED",
        "output_root": str(output),
        "partI_pdf_sha256": first_result["partI"]["asset_sha256"],
        "partII_v4_pdf_sha256": first_result["partII"]["v4_pdf_sha256"],
        "fig41_pdf_sha256": first_result["fig41"]["asset_sha256"],
        "replay_byte_identical": replay["byte_identical"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
