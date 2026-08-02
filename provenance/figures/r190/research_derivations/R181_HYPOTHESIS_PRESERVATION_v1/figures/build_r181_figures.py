#!/usr/bin/env python3
"""Build the English-only R181 hypothesis-preservation figure successors.

This producer is candidate-only.  It writes only to the R181 research figure
owner and to the R181 candidate's ``LaTex/figures`` subtree.  Live publication
assets and live TeX are read-only, hash-guarded inputs.

Eight logical figures / nine binaries are produced at the exact relative paths
already used by the R181 English candidate.  The three large dependency maps
retain their frozen R177 topologies and receive narrowly targeted status-label
successors.  The remaining five figures are deterministic vector redraws from
explicit R181 semantics.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any


FIXED_UTC = dt.datetime(2026, 7, 31, 0, 0, 0, tzinfo=dt.timezone.utc)
SOURCE_DATE_EPOCH = "1785456000"
SCHEMA = "ect.r181.hypothesis-preservation-figures.v1"
OWNER_ID = "R181_HYPOTHESIS_PRESERVATION_FIGURES_V1"

os.environ.setdefault("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)
os.environ.setdefault("TZ", "UTC")
os.environ.setdefault("LC_ALL", "C")
os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r181-figures-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/ect-r181-figures-xdg")

import fitz  # type: ignore
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
import numpy as np
from PIL import Image


SCRIPT = Path(__file__).resolve()
PACKAGE = SCRIPT.parent
WORKSPACE = next(
    parent for parent in SCRIPT.parents
    if (parent / "LaTex/ECT_preprint.tex").is_file()
)
R181_ROOT = PACKAGE.parent
DEFAULT_CANDIDATE_ROOT = (
    R181_ROOT
    / "candidate/R181_HYPOTHESIS_PRESERVATION_CASCADE_V1/LaTex/figures"
)


# Calm Okabe--Ito-derived palette.  Status remains literal and is also encoded
# by border, hatch, luminance, and arrow style.
BLACK = "#222222"
GREY = "#666666"
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#D55E00"
AMBER = "#A66E00"
PALE_BLUE = "#DCECF7"
PALE_GREEN = "#DDF2E9"
PALE_AMBER = "#FBE9C9"
PALE_RED = "#F5DDD7"
LIGHT_GREY = "#E8E8E8"
WHITE = "#FFFFFF"

STATUS_STYLE = {
    "A": dict(face=PALE_BLUE, edge=BLUE, linestyle="-", hatch=None),
    "B": dict(face=PALE_GREEN, edge=GREEN, linestyle="--", hatch="/"),
    "OPEN": dict(face=PALE_AMBER, edge=AMBER, linestyle="--", hatch="."),
    "MISSING": dict(face=PALE_RED, edge=ORANGE, linestyle="-.", hatch="x"),
    "EXTERNAL": dict(face=LIGHT_GREY, edge=BLACK, linestyle="-", hatch=None),
}

CVD = {
    "protanopia": np.array(
        [[0.152286, 1.052583, -0.204868],
         [0.114503, 0.786281, 0.099216],
         [-0.003882, -0.048116, 1.051998]], dtype=np.float32
    ),
    "deuteranopia": np.array(
        [[0.367322, 0.860646, -0.227968],
         [0.280085, 0.672501, 0.047413],
         [-0.011820, 0.042940, 0.968881]], dtype=np.float32
    ),
    "tritanopia": np.array(
        [[1.255528, -0.076749, -0.178779],
         [-0.078411, 0.930809, 0.147602],
         [0.004733, 0.691367, 0.303900]], dtype=np.float32
    ),
}


# Every input is English-only.  Predecessor binaries are guards/provenance, not
# raster sources for the new figures.
INPUTS: dict[str, dict[str, str]] = {
    "live_preprint_semantic_owner": {
        "path": "LaTex/ECT_preprint.tex",
        "sha256": "83542174966195c47d8171bb9055851f88121322425986f24559a0acf42d7f97",
        "role": "live English semantic owner; read only",
    },
    "candidate_preprint_semantic_anchor": {
        "path": "research/derivations/R181_HYPOTHESIS_PRESERVATION_v1/candidate/R181_HYPOTHESIS_PRESERVATION_CASCADE_V1/LaTex/ECT_preprint.tex",
        "sha256": "b27de5b2243cf1c1d7fe914ac041244cb6f96bfc2d012a89aabf569361ec697e",
        "role": "final R181 English candidate text anchor; read only; not the live owner",
    },
    "r181_hypothesis_audit": {
        "path": "research/derivations/R181_HYPOTHESIS_PRESERVATION_v1/R181_HYPOTHESIS_VS_PHENOMENOLOGY_AUDIT_v1.md",
        "sha256": "d754065535115b876f88c1ba9885ba56ae35b74d122e8326ab9fafc788a020fa",
        "role": "final R181 English status audit; read only",
    },
    "r181_dependency_ledger": {
        "path": "research/derivations/R181_HYPOTHESIS_PRESERVATION_v1/R181_SEMANTIC_DEPENDENCY_LEDGER_v1.csv",
        "sha256": "99ebb87149735b9b47799f6a4c8ca5c6451ed1a8b575d8a709b02166b8f892e2",
        "role": "R181 candidate semantic crosswalk; read only",
    },
    "partI_graphviz_owner": {
        "path": "LaTex/figures/source/graphviz/r177_terminal_units_successors_v1/fig09_partI_terminal_units_successor_r177.gv",
        "sha256": "8eb6901d7b7aad7d850fee41b97fb35968964da1460f687b0133359d9827024e",
        "role": "frozen R177 Part-I topology/source owner; read only",
    },
    "partI_reader_layout_owner": {
        "path": "LaTex/figures/source/graphviz/r168_connected_map_semantics_v1/semantic_keys/partI/partI_a4_reader_r168_fixed.gv",
        "sha256": "b69742ebb88f32b34a7f2e4bd5508258656d2f589a038e095ff6c7a35f9785ea",
        "role": "frozen 47-node A4-reader layout seed downstream of the Part-I semantic owner; read only",
    },
    "partIII_graphviz_owner": {
        "path": "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/remaining_map_successors/source/partIII_complete_map_successor_r177.gv",
        "sha256": "5f858a3aa7b78e56865677ec70dcd2e4fe310f6a0c57b997242ec3b5b29e8008",
        "role": "frozen R177 Part-III topology/source owner; read only",
    },
    "whole_graphviz_owner": {
        "path": "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/remaining_map_successors/source/whole_complete_map_successor_r177.gv",
        "sha256": "d711b919f01cd982016cc2e4feb0b6f7656109025532410126ed3a16a103ee56",
        "role": "frozen R177 whole-map topology/source owner; read only",
    },
    "r177_map_generator_reference": {
        "path": "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/remaining_map_successors/build_remaining_map_successors.py",
        "sha256": "bd65f4bc2ac6c3cf6fea4991f58a7e7c045d689bc4178d4523d1f001f354531c",
        "role": "read-only deterministic layout/QA reference",
    },
    "r177_hierarchy_generator_reference": {
        "path": "research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/equation_hierarchy_successor/build_equation_hierarchy_successor.py",
        "sha256": "5ed484d76aadb15a80415a1ce200889407666718895e5f0a8a1519612280139e",
        "role": "read-only hierarchy layout reference",
    },
    "scale_generator_reference": {
        "path": "LaTex/scripts/fig3_condensate_scales.py",
        "sha256": "70e8fa9bc79fd455a549c6523b72299a18dbd33dc36937a1e994f23b0165b76b",
        "role": "read-only scale plot reference",
    },
    "r149_typography_generator_reference": {
        "path": "LaTex/work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/second_half_typography_successors/build_successors.py",
        "sha256": "cd1cea5272c8c5d98eddb0f683fa009a0ae6d0e8eb7da53b3c6151c8e099c881",
        "role": "read-only companion/orientation layout reference",
    },
    "predecessor_architecture": {
        "path": "LaTex/figures/r177/global/fig_ect_architecture_r177.pdf",
        "sha256": "fff4c5368fc652fe5c44ef1f49da6b803b768ff7fd6935a08fd11d7544fdd653",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_scales_pdf": {
        "path": "LaTex/figures/r153/line_semantics/fig_condensate_scales_line_semantics_r153.pdf",
        "sha256": "70982d201862d6d0ee3c661f3fab1decc89da322d068cd77afb5cd9217b13383",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_scales_png": {
        "path": "LaTex/figures/r153/line_semantics/fig_condensate_scales_line_semantics_r153.png",
        "sha256": "a4ab3fc1447f90ca76285a104e45de60f1f36feb9a72b4b4aa7ab65db042288e",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_partI": {
        "path": "LaTex/figures/r179/logic_maps/partI_status_dependency_v15.pdf",
        "sha256": "39deee130ae99ce4ca9e701c43c4a8ace6ced421cdccd7aa326064c08e5fafeb",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_hierarchy_main": {
        "path": "LaTex/figures/r177/global/fig_equation_hierarchy_r177.pdf",
        "sha256": "e9b1ea98e1ff7b5794a5b521ddc4600479d763cec74a39733afa1bfc3b1c3762",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_hierarchy_companion": {
        "path": "LaTex/figures/r149/r149_equation_hierarchy.pdf",
        "sha256": "2bedf33cc5bd11c45759bf8e4f9264c70f13a622f9dd88999a60958d6ac5bfad",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_partIII": {
        "path": "LaTex/figures/r179/logic_maps/partIII_status_dependency_v15.pdf",
        "sha256": "c95c978b2a271d305f039e6b270076ea3dbef8bb493319899c56373b4c6dc7f8",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_whole": {
        "path": "LaTex/figures/r179/logic_maps/whole_status_dependency_v15.pdf",
        "sha256": "20b42d82bfbe03c7baeedf9cfcf1669d8f27bac9b7895d3d6f443d48dd40feac",
        "role": "predecessor binary guard; preserved",
    },
    "predecessor_orientation": {
        "path": "LaTex/figures/r149/fig41_a_orientation_stiffness_upstream_r149.pdf",
        "sha256": "bf2c90e11026c6e13b7906e5761555d71caee993f651d4dc5e6202532e3cfc43",
        "role": "predecessor binary guard; preserved",
    },
}


FIGURES: dict[str, dict[str, Any]] = {
    "architecture": {
        "figure_id": "fig:ect_architecture",
        "outputs": ["r177/global/fig_ect_architecture_r177.pdf"],
        "status": "P/Level B inputs; Level A conditional formula/algebra; Level B coefficient and speed calibrations; Open physical owners",
        "required_tokens": [
            "P4 adopted", "Level B input", "O(4)", "O(3)",
            "P7 adopted", "physical QCD connection/action/matter/mass gap Open", "S0 = hbar",
            "c_hat^2 = beta/(alpha-beta)", "Level A conditional formula",
            "c_hat = 1: Level B coefficient benchmark",
            "c_char = c: Level B calibration", "linked when N_Phi=1 and c_u=c",
            "phi0 = zeta_phi", "M_n,heavy", "MISSING VERTEX",
        ],
        "forbidden_tokens": [
            "c_hat = 1 unit-slope benchmark [A", "generic M_heavy",
        ],
    },
    "scales": {
        "figure_id": "fig:three_condensate_scales",
        "outputs": [
            "r153/line_semantics/fig_condensate_scales_line_semantics_r153.pdf",
            "r153/line_semantics/fig_condensate_scales_line_semantics_r153.png",
        ],
        "status": "Level B scale matching; external/benchmark points; Open mechanism",
        "required_tokens": [
            "phi0 = zeta_phi", "Level B matching", "zeta_phi = 1 display benchmark",
            "gravitational explanation Open", "Conditional HRC matching",
        ],
    },
    "partI": {
        "figure_id": "fig:partI_derivation_logic",
        "outputs": ["r179/logic_maps/partI_status_dependency_v15.pdf"],
        "status": "R177 topology retained; R181 P4/coefficient/calibration/S0/orientation statuses corrected",
        "required_tokens": [
            "P4 adopted gradient", "O(4)->O(3) stabiliser",
            "c_hat^2=beta/(alpha-beta)", "c_hat=1 [B benchmark]",
            "c_char=c [B calibration]", "linked if N_Phi=1,c_u=c",
            "cone universality Open", "M_n,heavy", "VERTEX MISSING", "S0=hbar",
        ],
        "forbidden_tokens": ["c_hat=1 [A]", "M_heavy"],
    },
    "hierarchy_main": {
        "figure_id": "fig:equation_hierarchy",
        "outputs": ["r177/global/fig_equation_hierarchy_r177.pdf"],
        "status": "Distinct P3, P4, Level-A scalar formula, Level-B coefficient/speed benchmarks and quantum calibration owners",
        "required_tokens": [
            "P4 adopted", "A-math conditional",
            "c_hat^2 = beta/(alpha-beta): Level A conditional formula",
            "c_hat = 1: Level B coefficient benchmark",
            "c_char = c: Level B calibration", "N_Phi=1 and c_u=c: linked algebraically",
            "S0 = hbar", "owner and universality Open",
        ],
        "forbidden_tokens": ["c_hat = 1: unit-slope benchmark [A"],
    },
    "hierarchy_companion": {
        "figure_id": "fig:pop_equation_hierarchy",
        "outputs": ["r149/r149_equation_hierarchy.pdf"],
        "status": "Companion-readable hierarchy with the same status ceiling as the preprint",
        "required_tokens": [
            "P4 adopted", "O(4) -> O(3)",
            "c_hat^2 = beta/(alpha-beta): Level A conditional formula",
            "c_hat = 1: Level B coefficient benchmark",
            "c_char = c: Level B calibration", "N_Phi=1 and c_u=c: linked algebraically",
            "S0 = hbar", "universality Open",
        ],
        "forbidden_tokens": ["c_hat = 1: unit-slope benchmark [A"],
    },
    "partIII": {
        "figure_id": "fig:qs_consistency",
        "outputs": ["r179/logic_maps/partIII_status_dependency_v15.pdf"],
        "status": "R177 topology retained; action calibration and owner status corrected",
        "required_tokens": [
            "Action-unit slot S0", "S0=hbar", "B calibration",
            "owner + universality Open", "dimensionless; not action",
        ],
    },
    "whole": {
        "figure_id": "fig:ect_derivation_map",
        "outputs": ["r179/logic_maps/whole_status_dependency_v15.pdf"],
        "status": "R177 topology retained; R181 P4/P7/SU3/S0/cone statuses corrected",
        "required_tokens": [
            "P4 adopted gradient", "P7 colour postulate", "SU(3) stabiliser",
            "physical QCD Open", "S0=hbar", "B calibration",
            "cone universality Open",
        ],
    },
    "orientation": {
        "figure_id": "fig:r123_atlas_f41a",
        "outputs": ["r149/fig41_a_orientation_stiffness_upstream_r149.pdf"],
        "status": "Level B EFT identity and owner-specific orientation-sector template; microscopic vertex Open/MISSING",
        "required_tokens": [
            "M_n,heavy", "PARAMETRIC ONLY", "MISSING VERTEX",
            "[C_n] = E^-2", "[kappa_n] = E^2", "tensor bridge Open",
        ],
        "forbidden_tokens": ["M_heavy"],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def guard_inputs() -> dict[str, dict[str, str]]:
    frozen: dict[str, dict[str, str]] = {}
    for key, record in INPUTS.items():
        path = WORKSPACE / record["path"]
        if not path.is_file():
            raise RuntimeError(f"missing frozen input {key}: {path}")
        actual = sha256(path)
        if actual != record["sha256"]:
            raise RuntimeError(
                f"frozen input drift for {key}: {record['path']}\n"
                f"expected {record['sha256']}\nactual   {actual}"
            )
        frozen[key] = dict(record)
    return frozen


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source anchor, found {count}")
    return source.replace(old, new, 1)


def regex_once(source: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, source, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected one regex anchor, found {count}")
    return updated


def configure_matplotlib() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "mathtext.fontset": "dejavusans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.8,
        "savefig.facecolor": WHITE,
        "figure.facecolor": WHITE,
    })


def pdf_metadata(title: str, subject: str) -> dict[str, Any]:
    return {
        "Title": title,
        "Author": "ECT R181 candidate reproducibility owner",
        "Subject": subject,
        "Creator": SCRIPT.name,
        "CreationDate": FIXED_UTC,
        "ModDate": FIXED_UTC,
    }


def save_pdf(fig: Any, path: Path, title: str, subject: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf", metadata=pdf_metadata(title, subject))


def save_png(fig: Any, path: Path, dpi: int = 180) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        format="png",
        dpi=dpi,
        metadata={"Software": "ECT R181 deterministic candidate generator"},
    )


def draw_status_box(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    status: str,
    *,
    fontsize: float = 8.0,
    linewidth: float = 1.45,
    zorder: int = 3,
) -> FancyBboxPatch:
    style = STATUS_STYLE[status]
    patch = FancyBboxPatch(
        (x - width / 2.0, y - height / 2.0),
        width,
        height,
        boxstyle="round,pad=0.06,rounding_size=0.09",
        facecolor=style["face"],
        edgecolor=style["edge"],
        linestyle=style["linestyle"],
        hatch=style["hatch"],
        linewidth=linewidth,
        zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(
        x, y, text, ha="center", va="center", fontsize=fontsize,
        color=BLACK, linespacing=1.08, zorder=zorder + 1,
    )
    return patch


def box_boundary(
    source: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    sx, sy, sw, sh = source
    tx, ty, tw, th = target
    vx, vy = tx - sx, ty - sy
    src_scale = min(
        sw / (2.0 * abs(vx)) if vx else math.inf,
        sh / (2.0 * abs(vy)) if vy else math.inf,
    )
    dst_scale = min(
        tw / (2.0 * abs(vx)) if vx else math.inf,
        th / (2.0 * abs(vy)) if vy else math.inf,
    )
    return (
        (sx + vx * src_scale, sy + vy * src_scale),
        (tx - vx * dst_scale, ty - vy * dst_scale),
    )


def draw_arrow(
    ax: Any,
    source: tuple[float, float, float, float],
    target: tuple[float, float, float, float],
    *,
    conditional: bool,
    label: str | None = None,
    label_xy: tuple[float, float] | None = None,
    rad: float = 0.0,
) -> None:
    start, end = box_boundary(source, target)
    linestyle = "--" if conditional else "-"
    ax.add_patch(FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=10.5,
        linewidth=1.05,
        linestyle=linestyle,
        color=BLACK,
        connectionstyle=f"arc3,rad={rad}",
        zorder=2,
    ))
    if label:
        lx, ly = label_xy or ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
        ax.text(
            lx, ly, label, fontsize=6.6, color=GREY, ha="center", va="center",
            style="italic", bbox=dict(boxstyle="round,pad=.06", fc=WHITE, ec="none", alpha=.9),
            zorder=5,
        )


def render_architecture(output: Path) -> None:
    configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.9, 9.2))
    ax.set_xlim(0.0, 12.0)
    ax.set_ylim(0.35, 13.45)
    ax.axis("off")
    ax.text(
        6.0, 13.20, "ECT programme architecture — R181 hypothesis-preservation candidate",
        ha="center", va="top", fontsize=11.5, weight="bold", color=BLACK,
    )
    ax.text(
        6.0, 12.83,
        "Postulates, conditional algebra, calibrations and Open physical owners remain distinct.",
        ha="center", va="top", fontsize=7.7, color=GREY,
    )

    nodes: dict[str, tuple[float, float, float, float, str, str]] = {
        "start": (6.0, 11.95, 5.7, 0.72,
                  "P1–P6 supplied starting layer\npostulates are inputs, not microscopic derivations", "EXTERNAL"),
        "p3": (1.95, 10.52, 3.4, 1.08,
               "P3 homogeneous scalar owner\nradial curvature: Level A inside supplied P3\nnot a P4 pole", "A"),
        "p4": (5.95, 10.52, 3.7, 1.12,
               "P4 adopted ordered-gradient postulate\n[P / Level B input]\nstationary action and formation Open", "B"),
        "eft": (10.0, 10.52, 3.7, 1.12,
                "Separately supplied scalar EFT [Level B]\ncoefficients are not derived from P4\nphysical state map Open", "B"),
        "stab": (3.55, 8.78, 4.6, 1.12,
                 "Conditional group geometry\nnonzero vector: O(4) stabiliser O(3) [Level A]\nphysical SSB / dynamical selection Open", "A"),
        "speed": (8.35, 8.78, 5.0, 1.42,
                  "Scalar coefficient / speed owner\n"
                  "c_hat^2 = beta/(alpha-beta): Level A conditional formula\n"
                  "c_hat = 1: Level B coefficient benchmark\n"
                  "c_char = c: Level B calibration; linked when N_Phi=1 and c_u=c\n"
                  "photon/tensor/common-cone universality Open", "B"),
        "phi0": (2.45, 6.82, 4.35, 1.15,
                 "Independent scale match\nphi0 = zeta_phi Mbar_Pl [Level B matching]\nzeta_phi and gravitational explanation Open", "B"),
        "orient": (7.05, 6.82, 4.65, 1.20,
                   "Orientation-stiffness route\nM_n,heavy template: PARAMETRIC ONLY\n"
                   "orientation coupling/operator owner: MISSING VERTEX", "MISSING"),
        "quant": (10.35, 5.12, 3.1, 1.22,
                  "Quantum calibration\nS0 = hbar [Level B]\nmicroscopic owner and universality Open", "B"),
        "p7": (2.35, 4.63, 4.5, 1.42,
               "P7 adopted rank-three (h, Omega) postulate [P / Level B]\nSU(3) stabiliser algebra: Level A conditional\nphysical QCD connection/action/matter/mass gap Open", "B"),
        "macro": (6.55, 4.62, 3.6, 1.36,
                  "Macroscopic/tensor programme\nphysical tensor Hessian, source vertex, pole residue\nand common cone remain Open", "OPEN"),
        "out": (6.0, 2.30, 8.9, 1.22,
                "Conditional outputs, external comparators and falsifiers\nA/B/C results retain their declared assumptions\nuniversal or cross-sector ECT closure remains Open", "OPEN"),
    }
    boxes: dict[str, tuple[float, float, float, float]] = {}
    for key, (x, y, w, h, label, status) in nodes.items():
        draw_status_box(ax, x, y, w, h, label, status, fontsize=6.55)
        boxes[key] = (x, y, w, h)

    for src, dst, conditional, label, rad in (
        ("start", "p3", False, None, 0.0),
        ("start", "p4", True, None, 0.0),
        ("start", "eft", True, None, 0.0),
        ("p4", "stab", False, "conditional stabiliser", 0.0),
        ("p4", "speed", True, "separate EFT owner", 0.0),
        ("eft", "speed", False, None, 0.0),
        ("p3", "phi0", True, "independent B match", 0.0),
        ("p4", "orient", True, "additional operator required", 0.0),
        ("eft", "quant", True, "state + action calibration", 0.12),
        ("stab", "p7", True, "new structural postulate", 0.0),
        ("phi0", "macro", True, "tensor bridge Open", 0.0),
        ("orient", "macro", True, "vertex/pole map missing", 0.0),
        ("speed", "macro", True, "common-cone owner Open", 0.0),
        ("speed", "quant", True, None, 0.0),
        ("p7", "out", True, None, 0.0),
        ("macro", "out", True, None, 0.0),
        ("quant", "out", True, None, 0.0),
    ):
        # Relationship semantics are already literal in the adjacent nodes;
        # suppress midpoint labels here so arrows never obscure scientific text.
        draw_arrow(ax, boxes[src], boxes[dst], conditional=conditional, label=None, rad=rad)

    ax.text(
        6.0, 1.12,
        "Solid near-black arrow: exact conditional algebra inside supplied assumptions.  "
        "Dashed: conditional/Open dependency.",
        ha="center", fontsize=7.2, color=BLACK,
    )
    ax.text(
        6.0, 0.76,
        "Status is literal and redundant with fill luminance, hatch, border and arrow style.",
        ha="center", fontsize=7.2, color=GREY,
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.99, bottom=0.02)
    save_pdf(
        fig, output,
        "ECT programme architecture — R181 hypothesis-preservation candidate",
        "P4, P7, scalar-speed, action-scale, scale-matching and orientation-owner statuses",
    )
    plt.close(fig)


def render_scales(pdf_output: Path, png_output: Path) -> None:
    configure_matplotlib()
    # Frozen display inputs.  The phi0 point is explicitly the zeta_phi=1
    # benchmark of a Level-B matching ansatz, not a microscopic prediction.
    phi0_benchmark_gev = 2.435e18
    v2_external_gev = 246.22
    g_newton = 6.67430e-11
    m_sun = 1.98847e30
    kpc = 3.0856775814913673e19
    a_m0 = 1.0824013602e-10

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.1, 9.4))
    fig.suptitle(
        "Dimensionally separated scale inventory — R181 status successor",
        fontsize=11.2, weight="bold", y=0.985,
    )

    x = np.array([0.0, 1.0])
    energies = np.array([phi0_benchmark_gev, v2_external_gev])
    ax1.scatter(
        [x[0]], [energies[0]], s=85, marker="o", facecolor=PALE_BLUE,
        edgecolor=BLUE, linewidth=1.6, zorder=4,
    )
    ax1.scatter(
        [x[1]], [energies[1]], s=78, marker="s", facecolor=WHITE,
        edgecolor=BLACK, linewidth=1.5, zorder=4,
    )
    ax1.set_yscale("log")
    ax1.set_xlim(-0.45, 1.45)
    ax1.set_ylim(1e1, 1e20)
    ax1.set_xticks(x, [r"$\phi_0$", r"$v_2$"])
    ax1.set_ylabel("energy / matching scale [GeV]")
    ax1.set_title("(a) Energy-dimension inventory", loc="left", fontweight="bold")
    ax1.grid(True, alpha=0.28, linewidth=0.6)
    ax1.annotate(
        "phi0 = zeta_phi Mbar_Pl\nLevel B matching\nzeta_phi = 1 display benchmark",
        (x[0], energies[0]), xytext=(25, -10), textcoords="offset points",
        ha="left", va="top", fontsize=8.2,
        bbox=dict(boxstyle="round,pad=.32", fc=PALE_GREEN, ec=GREEN, hatch="/"),
        arrowprops=dict(arrowstyle="->", color=BLACK, lw=1.0),
    )
    ax1.annotate(
        "v2 = 246.22 GeV\nexternal matched scale\nECT origin Open",
        (x[1], energies[1]), xytext=(-24, 22), textcoords="offset points",
        ha="right", va="bottom", fontsize=8.2,
        bbox=dict(boxstyle="round,pad=.32", fc=LIGHT_GREY, ec=BLACK),
        arrowprops=dict(arrowstyle="->", color=BLACK, lw=1.0),
    )
    ax1.text(
        0.50, 0.48,
        "The two points share one energy axis only.\n"
        "No interpolation or RG flow is implied.\n"
        "Hierarchy mechanism and gravitational explanation Open.",
        transform=ax1.transAxes, ha="center", va="center", fontsize=8.1,
        bbox=dict(boxstyle="round,pad=.34", fc=PALE_AMBER, ec=AMBER, hatch=".", linestyle="--"),
    )

    masses_solar = np.logspace(7, 12, 300)
    r_kpc = np.sqrt(g_newton * masses_solar * m_sun / a_m0) / kpc
    ax2.plot(
        masses_solar, r_kpc, color=BLUE, lw=2.0, linestyle="-",
        label="conditional HRC matching identity",
    )
    m_ref = 1.0e10
    r_ref = math.sqrt(g_newton * m_ref * m_sun / a_m0) / kpc
    ax2.scatter(
        [m_ref], [r_ref], s=78, marker="D", facecolor=WHITE,
        edgecolor=ORANGE, linewidth=1.6, zorder=4,
        label="declared reference mass",
    )
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"baryonic mass $M_{\rm bar}$ [$M_\odot$]")
    ax2.set_ylabel(r"conditional matching length $L_{\rm gal}=r_*$ [kpc]")
    ax2.set_title("(b) Conditional HRC matching benchmark", loc="left", fontweight="bold")
    ax2.grid(True, alpha=0.28, linewidth=0.6)
    ax2.text(
        0.04, 0.96,
        r"$r_*=\sqrt{G_N M_{\rm bar}/a_{M0}}$" + "\n"
        + r"$a_{M0}=1.0824\times10^{-10}$ m s$^{-2}$ (matched)" + "\n"
        + "Level C/conditional benchmark; not a first-principles bridge",
        transform=ax2.transAxes, ha="left", va="top", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=.32", fc=PALE_AMBER, ec=AMBER, hatch=".", linestyle="--"),
    )
    ax2.annotate(
        rf"$M_{{\rm bar}}=10^{{10}}M_\odot$" + "\n" + rf"$r_*={r_ref:.1f}$ kpc",
        (m_ref, r_ref), xytext=(24, -25), textcoords="offset points",
        ha="left", va="top", fontsize=8.0,
        arrowprops=dict(arrowstyle="->", color=BLACK, lw=1.0),
    )
    ax2.text(
        0.03, 0.06, "No common GeV axis\nNo RG link claimed",
        transform=ax2.transAxes, ha="left", va="bottom", fontsize=8.2, color=GREY,
        bbox=dict(boxstyle="round,pad=.15", fc=WHITE, ec="none", alpha=.9),
    )
    ax2.legend(loc="lower right", frameon=True, framealpha=1.0, fontsize=8.1)

    fig.subplots_adjust(left=0.12, right=0.97, top=0.94, bottom=0.08, hspace=0.25)
    save_pdf(
        fig, pdf_output,
        "Dimensionally separated scale inventory — R181",
        "Level-B phi0 matching, external electroweak scale and conditional HRC benchmark",
    )
    save_png(fig, png_output, dpi=180)
    plt.close(fig)


def render_hierarchy(output: Path, *, companion: bool) -> None:
    configure_matplotlib()
    figsize = (6.7, 8.2) if companion else (7.2, 9.4)
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0.0, 7.2)
    ax.set_ylim(0.0, 9.4)
    ax.axis("off")
    title = (
        "Equation hierarchy — R181 companion status map"
        if companion else
        "Equation hierarchy — R181 separated-owner candidate"
    )
    ax.text(3.6, 9.18, title, ha="center", va="top", fontsize=10.7, weight="bold")

    boxes = {
        "p3": (1.78, 8.12, 3.0, 1.22),
        "p4": (5.42, 8.12, 3.0, 1.22),
        "eft": (3.60, 6.18, 5.9, 1.30),
        "speed": (3.60, 4.10, 5.9, 1.55),
        "quant": (3.60, 2.02, 5.9, 1.22),
    }
    fs = 8.7 if companion else 8.8
    draw_status_box(
        ax, *boxes["p3"],
        "P3 homogeneous scalar owner\nradial curvature: A-math inside supplied P3\nnot a P4 pole",
        "A", fontsize=fs,
    )
    draw_status_box(
        ax, *boxes["p4"],
        "P4 adopted ordered-gradient postulate\n[P / Level B input]\nO(4) -> O(3) stabiliser: A-math conditional",
        "B", fontsize=fs,
    )
    draw_status_box(
        ax, *boxes["eft"],
        "Separately supplied scalar EFT [Level B]\n"
        r"$K^{AB}=\beta\delta^{AB}-\alpha n^An^B$, Lorentzian iff $\beta(\beta-\alpha)<0$" "\n"
        "P4 does not derive EFT coefficients, pole or cutoff",
        "B", fontsize=8.55,
    )
    draw_status_box(
        ax, *boxes["speed"],
        "Scalar coefficient and characteristic calibration\n"
        "c_hat^2 = beta/(alpha-beta): Level A conditional formula\n"
        "c_hat = 1: Level B coefficient benchmark\n"
        "c_char = c: Level B calibration\n"
        "N_Phi=1 and c_u=c: linked algebraically; common-cone universality Open",
        "OPEN", fontsize=7.55,
    )
    draw_status_box(
        ax, *boxes["quant"],
        "Conditional Schrodinger-type envelope\n"
        "S0 = hbar: Level B calibration\n"
        "microscopic owner and universality Open; state/operator/measure owners required",
        "OPEN", fontsize=8.35,
    )

    draw_arrow(ax, boxes["p3"], boxes["eft"], conditional=True, label="P3–P4 matching Open", label_xy=(2.05, 7.12))
    draw_arrow(ax, boxes["p4"], boxes["eft"], conditional=True, label="adopted datum only", label_xy=(5.10, 7.12))
    draw_arrow(ax, boxes["eft"], boxes["speed"], conditional=True, label="coordinate / unit-conversion calibration")
    draw_arrow(ax, boxes["speed"], boxes["quant"], conditional=True, label="state + positive-frequency + NR assumptions")
    ax.text(
        3.6, 0.68,
        "Dashed arrows are conditional dependencies, not status upgrades.\n"
        "Physical P4 formation, common cones, and action-scale universality remain Open.",
        ha="center", va="center", fontsize=8.0, color=GREY, weight="bold",
    )
    fig.subplots_adjust(left=0.03, right=0.97, top=0.99, bottom=0.02)
    save_pdf(
        fig, output, title,
        "P3/P4, scalar-speed and quantum action-scale owners separated",
    )
    plt.close(fig)


def render_orientation(output: Path) -> None:
    configure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 6.1))
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 8.0)
    ax.axis("off")
    ax.text(
        5.0, 7.68, "Orientation stiffness — R181 parametric-owner audit",
        ha="center", va="top", fontsize=11.3, weight="bold",
    )
    ax.text(
        5.0, 7.31,
        "The EFT identity is retained; the microscopic heavy-field route is not promoted to a derivation.",
        ha="center", va="top", fontsize=7.7, color=GREY,
    )
    boxes = {
        "p4": (5.0, 6.32, 7.8, 0.86),
        "eft": (5.0, 5.02, 7.8, 0.92),
        "template": (3.15, 3.52, 4.25, 1.08),
        "missing": (7.65, 3.52, 3.65, 1.35),
        "tensor": (5.0, 1.72, 7.8, 1.02),
    }
    draw_status_box(
        ax, *boxes["p4"],
        "P4 adopted ordered-gradient datum [P / Level B input]; physical formation Open",
        "B", fontsize=8.6,
    )
    draw_status_box(
        ax, *boxes["eft"],
        r"$\kappa_n=\mathcal{C}_n u_0^2$ — Level B EFT identity" "\n"
        "dimension audit: [C_n] = E^-2, [u0] = E^2, [kappa_n] = E^2",
        "B", fontsize=8.6,
    )
    draw_status_box(
        ax, *boxes["template"],
        r"$\mathcal{C}_n=\hat a_n/(16\pi^2M_{n,\rm heavy}^2)$" "\n"
        "orientation scale M_n,heavy\nPARAMETRIC ONLY [Level B conditional]",
        "OPEN", fontsize=8.0,
    )
    draw_status_box(
        ax, *boxes["missing"],
        "MISSING VERTEX\norientation field H_n + coupling/operator\n"
        "quadratic Hessian + BC\nregulator/subtraction + finite match",
        "MISSING", fontsize=7.8,
    )
    draw_status_box(
        ax, *boxes["tensor"],
        "M_G^2 ?= c_M kappa_n — tensor bridge Open\n"
        "representation, gauge reduction, positive pole residue and matter/source vertex missing",
        "OPEN", fontsize=8.25,
    )
    draw_arrow(ax, boxes["p4"], boxes["eft"], conditional=True, label="supplied EFT owner")
    draw_arrow(ax, boxes["eft"], boxes["template"], conditional=True, label="possible matching route", rad=0.0)
    draw_arrow(ax, boxes["missing"], boxes["template"], conditional=True, label="required input", rad=0.0)
    draw_arrow(ax, boxes["template"], boxes["tensor"], conditional=True, label="not an identification", rad=0.0)
    ax.text(
        5.0, 0.62,
        "Counterexamples/guards: pure P(X) supplies no independent orientation stiffness.\n"
        "M_n,heavy cannot be set to the P3 radial mass or M_Y,heavy by notation.",
        ha="center", va="center", fontsize=7.3, color=GREY, weight="bold",
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.99, bottom=0.02)
    save_pdf(
        fig, output,
        "Orientation stiffness — R181 parametric-owner audit",
        "Orientation-sector M_n,heavy template with missing microscopic vertex and Open tensor bridge",
    )
    plt.close(fig)


def transform_partI(source: str) -> str:
    replacements = (
        (
            'label="P4: ordered\nbranch\n[P]"',
            'label="P4 adopted\ngradient input\n[P/B]"',
            "partI P4 input",
        ),
        (
            'label="Clock / EM\n[O]"',
            'label="c_char=c\nB calibration\ncones Open"',
            "partI physical speed calibration",
        ),
        (
            'label="Ordered\nO(4)->O(3)\n[A]"',
            'label="O(4)->O(3)\nstabiliser\n[A conditional]"',
            "partI stabiliser",
        ),
        (
            'label="Scalar\ncone slope\n[A/O]"',
            'label="c_hat^2=beta/(alpha-beta)\n[A conditional]\nc_hat=1 [B benchmark]\n'
            'c_char=c [B calibration]\nlinked if N_Phi=1,c_u=c\ncones Open", '
            'width=1.72, height=1.12, fontsize=8.2',
            "partI c-hat and c-char",
        ),
        (
            'label="Orientation\nstiffness\n[O]"',
            'label="M_n,heavy template\nPARAMETRIC ONLY\nVERTEX MISSING", '
            'width=1.60, height=0.92, fontsize=9.0',
            "partI orientation owner",
        ),
        (
            'label="Empirical\nS0 match\n[B/O]"',
            'label="S0=hbar\nB calibration\nowner Open"',
            "partI S0 calibration",
        ),
        (
            'label="Action-unit\nslot\n[B/O]"',
            'label="S0 action slot\n[B]\nowner Open"',
            "partI S0 slot",
        ),
        (
            'label="SU(3)c\ncompletion\n[O]"',
            'label="SU(3)c route\nphysical QCD\nOpen"',
            "partI colour scope",
        ),
    )
    for old, new, label in replacements:
        # This compact Graphviz seed stores line breaks as literal ``\\n``
        # escapes on one source line.
        source = replace_once(
            source, old.replace("\n", "\\n"), new.replace("\n", "\\n"), label
        )
    return source


def transform_partIII(source: str) -> str:
    replacements = (
        (
            'label="iota_0 dimless\n[A/O]",',
            'label="iota_0 dimensionless; not action\n[A/Open owner]",',
            "partIII dimensionless coefficient",
        ),
        (
            'label="Sigma x I action\n[B/O]",',
            'label="Action-unit slot S0\n[B; microscopic owner Open]",',
            "partIII S0 slot",
        ),
        (
            'label="S0=hbar calib.\n[B/O]",',
            'label="S0=hbar: B calibration\nowner + universality Open",',
            "partIII S0 calibration",
        ),
    )
    for old, new, label in replacements:
        source = replace_once(source, old, new, label)
    return source


def transform_whole(source: str) -> str:
    replacements = (
        (
            'label="P4 datum\n[P]",',
            'label="P4 adopted gradient\npostulate [P/B]",',
            "whole P4",
        ),
        (
            'label="P7 colour\n[P/O]",',
            'label="P7 colour postulate\n[P/Level B]",',
            "whole P7",
        ),
        (
            'label="O(3)\nP4 Open\n[A/O]",',
            'label="O(3) stabiliser [A conditional]\nphysical SSB Open",',
            "whole stabiliser",
        ),
        (
            'label="SU(3)\nstructure\n[B/O]",',
            'label="SU(3) stabiliser\n[A conditional]\nphysical QCD Open",',
            "whole SU3",
        ),
        (
            'label="dimless iota_0\n[A/O]",',
            'label="iota_0 dimensionless\nnot action [A/O]",',
            "whole dimensionless coefficient",
        ),
        (
            'label="Sigma x I\naction [B/O]",',
            'label="Action-unit slot S0\n[B; owner Open]",',
            "whole S0 slot",
        ),
        (
            'label="S0=hbar\ncalib. [B/O]",',
            'label="S0=hbar\nB calibration\nowner/universality Open",',
            "whole S0 calibration",
        ),
        (
            'label="Sector\ncones\\n[B/O]",',
            'label="scalar c_char=c [B]\ncone universality Open",',
            "whole cone scope",
        ),
    )
    for old, new, label in replacements:
        source = replace_once(source, old, new, label)
    return source


def run_command(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
        "TZ": "UTC",
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return subprocess.run(
        argv, cwd=cwd, env=env, check=True, capture_output=True, text=True,
    )


def graph_counts(source_path: Path) -> tuple[int, int]:
    completed = run_command(["dot", "-Tjson", str(source_path)])
    payload = json.loads(completed.stdout)
    nodes = len([
        item for item in payload.get("objects", [])
        if "name" in item and "invis" not in str(item.get("style", ""))
    ])
    edges = len([
        edge for edge in payload.get("edges", [])
        if "invis" not in str(edge.get("style", ""))
    ])
    return nodes, edges


def compose_a4(
    raw_pdf: Path,
    output: Path,
    *,
    title: str,
    subtitle: str,
    source_hash: str,
    node_count: int,
    edge_count: int,
) -> None:
    a4 = fitz.paper_rect("a4")
    raw = fitz.open(raw_pdf)
    if raw.page_count != 1:
        raise RuntimeError(f"expected one raw Graphviz page: {raw_pdf}")
    raw_rect = raw[0].rect
    graph_area = fitz.Rect(8, 59, a4.width - 8, a4.height - 64)
    scale = min(graph_area.width / raw_rect.width, graph_area.height / raw_rect.height)
    width, height = raw_rect.width * scale, raw_rect.height * scale
    placement = fitz.Rect(
        graph_area.x0 + (graph_area.width - width) / 2.0,
        graph_area.y0 + (graph_area.height - height) / 2.0,
        graph_area.x0 + (graph_area.width + width) / 2.0,
        graph_area.y0 + (graph_area.height + height) / 2.0,
    )
    document = fitz.open()
    page = document.new_page(width=a4.width, height=a4.height)
    if page.insert_textbox(
        fitz.Rect(18, 8, a4.width - 18, 30),
        title,
        fontname="helv",
        fontsize=10.8,
        color=(0.12, 0.12, 0.12),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError(f"map title overflow: {title}")
    if page.insert_textbox(
        fitz.Rect(20, 28, a4.width - 20, 56),
        subtitle,
        fontname="helv",
        fontsize=6.5,
        color=(0.30, 0.30, 0.30),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError(f"map subtitle overflow: {subtitle}")
    page.show_pdf_page(placement, raw, 0, keep_proportion=True)
    legend = (
        "P postulate/input | A exact in stated model | B conditional/calibration | "
        "C fit/toy | O Open | MISSING owner absent. Solid: exact declared step; "
        "dashed/dotted: conditional or Open dependency. Literal node status controls."
    )
    if page.insert_textbox(
        fitz.Rect(18, a4.height - 61, a4.width - 18, a4.height - 30),
        legend,
        fontname="helv",
        fontsize=7.6,
        color=(0.16, 0.16, 0.16),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError("map legend overflow")
    footer = (
        f"{node_count} semantic nodes / {edge_count} visible directed edges | "
        f"R181 successor of frozen source {source_hash[:16]} | candidate only"
    )
    if page.insert_textbox(
        fitz.Rect(18, a4.height - 26, a4.width - 18, a4.height - 9),
        footer,
        fontname="helv",
        fontsize=6.8,
        color=(0.34, 0.34, 0.34),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError("map footer overflow")
    document.set_metadata({
        "title": title,
        "author": "ECT R181 candidate reproducibility owner",
        "subject": "R181 hypothesis-preservation status/dependency-map successor",
        "keywords": "ECT R181 candidate status dependency map",
        "creator": SCRIPT.name,
        "producer": "PyMuPDF",
        "creationDate": "D:20260731000000Z",
        "modDate": "D:20260731000000Z",
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output, garbage=4, deflate=True, no_new_id=True)
    document.close()
    raw.close()


def render_graph_map(
    input_key: str,
    output: Path,
    *,
    title: str,
    subtitle: str,
    transform: Any,
) -> dict[str, int]:
    source_path = WORKSPACE / INPUTS[input_key]["path"]
    transformed = transform(source_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="r181-graphviz-") as temporary:
        temp = Path(temporary)
        gv = temp / "map.gv"
        raw_pdf = temp / "map.pdf"
        write_text(gv, transformed)
        nodes, edges = graph_counts(gv)
        run_command(["dot", "-Tpdf", str(gv), "-o", str(raw_pdf)])
        compose_a4(
            raw_pdf,
            output,
            title=title,
            subtitle=subtitle,
            source_hash=INPUTS[input_key]["sha256"],
            node_count=nodes,
            edge_count=edges,
        )
    return {"nodes": nodes, "visible_edges": edges}


def render_previews(pdf: Path, preview_root: Path, logical_name: str) -> dict[str, str]:
    document = fitz.open(pdf)
    if document.page_count != 1:
        raise RuntimeError(f"preview expects one-page PDF: {pdf}")
    pixmap = document[0].get_pixmap(matrix=fitz.Matrix(1.55, 1.55), alpha=False)
    rgb_path = preview_root / f"{logical_name}_rgb.png"
    rgb_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(rgb_path)
    document.close()
    base = Image.open(rgb_path).convert("RGB")
    outputs: dict[str, str] = {"rgb": str(rgb_path.relative_to(preview_root.parent))}
    grayscale = preview_root / f"{logical_name}_grayscale.png"
    base.convert("L").save(grayscale, compress_level=9)
    outputs["grayscale"] = str(grayscale.relative_to(preview_root.parent))
    array = np.asarray(base, dtype=np.float32) / 255.0
    for mode, matrix in CVD.items():
        simulated = np.clip(array @ matrix.T, 0.0, 1.0)
        path = preview_root / f"{logical_name}_{mode}.png"
        Image.fromarray((simulated * 255.0).round().astype(np.uint8), "RGB").save(
            path, compress_level=9
        )
        outputs[mode] = str(path.relative_to(preview_root.parent))
    base.close()
    return outputs


def normalize_text(text: str) -> str:
    return " ".join(text.replace("−", "-").replace("–", "-").split()).lower()


def inspect_pdf(
    path: Path,
    required_tokens: list[str],
    forbidden_tokens: list[str] | None = None,
) -> dict[str, Any]:
    document = fitz.open(path)
    if document.page_count != 1:
        raise RuntimeError(f"expected one-page PDF: {path}")
    page = document[0]
    text = page.get_text("text")
    searchable = normalize_text(text)
    missing = [token for token in required_tokens if normalize_text(token) not in searchable]
    present_forbidden = [
        token for token in (forbidden_tokens or [])
        if normalize_text(token) in searchable
    ]
    info = {
        "page_count": document.page_count,
        "media_box_pt": [round(page.rect.width, 3), round(page.rect.height, 3)],
        "embedded_font_records": len(page.get_fonts(full=True)),
        "searchable_text_chars": len(text),
        "missing_required_tokens": missing,
        "present_forbidden_tokens": present_forbidden,
    }
    document.close()
    return info


def inspect_png(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        return {
            "dimensions_px": [image.width, image.height],
            "mode": image.mode,
            "metadata_keys": sorted(str(key) for key in image.info),
        }


def output_record(candidate_root: Path, relative_path: str) -> dict[str, Any]:
    path = candidate_root / relative_path
    record: dict[str, Any] = {
        "path": f"LaTex/figures/{relative_path}",
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "mime": "application/pdf" if path.suffix.lower() == ".pdf" else "image/png",
    }
    if path.suffix.lower() == ".pdf":
        record["pdf"] = inspect_pdf(path, [])
    else:
        record["png"] = inspect_png(path)
    return record


def build(candidate_root: Path, metadata_root: Path, *, write_runtime: bool) -> dict[str, Any]:
    frozen_inputs = guard_inputs()
    candidate_root.mkdir(parents=True, exist_ok=True)
    metadata_root.mkdir(parents=True, exist_ok=True)

    paths = {
        relative: candidate_root / relative
        for figure in FIGURES.values() for relative in figure["outputs"]
    }
    render_architecture(paths["r177/global/fig_ect_architecture_r177.pdf"])
    render_scales(
        paths["r153/line_semantics/fig_condensate_scales_line_semantics_r153.pdf"],
        paths["r153/line_semantics/fig_condensate_scales_line_semantics_r153.png"],
    )
    map_counts = {
        "partI": render_graph_map(
            "partI_reader_layout_owner",
            paths["r179/logic_maps/partI_status_dependency_v15.pdf"],
            title="Selected Part I status and dependency map (R181 candidate)",
            subtitle=(
                "R181 focus: P4 adopted P/B; O(4)->O(3) stabiliser A conditional; "
                "c_hat^2=beta/(alpha-beta) A conditional; c_hat=1 B coefficient benchmark; "
                "c_char=c B calibration, linked when N_Phi=1 and c_u=c; "
                "cone universality Open; M_n,heavy route PARAMETRIC ONLY / VERTEX MISSING."
            ),
            transform=transform_partI,
        ),
        "partIII": render_graph_map(
            "partIII_graphviz_owner",
            paths["r179/logic_maps/partIII_status_dependency_v15.pdf"],
            title="Selected Part III status and dependency map (R181 candidate)",
            subtitle=(
                "R181 focus: dimensionless iota_0 is not an action; S0 is an action-unit slot; "
                "S0=hbar is a Level-B calibration with owner and universality Open."
            ),
            transform=transform_partIII,
        ),
        "whole": render_graph_map(
            "whole_graphviz_owner",
            paths["r179/logic_maps/whole_status_dependency_v15.pdf"],
            title="Selected ECT status and dependency map (R181 candidate)",
            subtitle=(
                "R181 focus: P4 and P7 are adopted Level-B inputs; their stabiliser algebra is conditional; "
                "physical QCD, S0 ownership and cross-sector cone universality remain Open."
            ),
            transform=transform_whole,
        ),
    }
    render_hierarchy(paths["r177/global/fig_equation_hierarchy_r177.pdf"], companion=False)
    render_hierarchy(paths["r149/r149_equation_hierarchy.pdf"], companion=True)
    render_orientation(paths["r149/fig41_a_orientation_stiffness_upstream_r149.pdf"])

    previews: dict[str, dict[str, str]] = {}
    preview_root = metadata_root / "previews"
    for logical_name, figure in FIGURES.items():
        pdf_relative = next(path for path in figure["outputs"] if path.endswith(".pdf"))
        previews[logical_name] = render_previews(
            candidate_root / pdf_relative, preview_root, logical_name
        )

    figure_records: list[dict[str, Any]] = []
    failures: list[str] = []
    for logical_name, figure in FIGURES.items():
        outputs = [output_record(candidate_root, rel) for rel in figure["outputs"]]
        pdf_rel = next(rel for rel in figure["outputs"] if rel.endswith(".pdf"))
        forbidden_tokens = figure.get("forbidden_tokens", [])
        semantic_qa = inspect_pdf(
            candidate_root / pdf_rel,
            figure["required_tokens"],
            forbidden_tokens,
        )
        if semantic_qa["missing_required_tokens"]:
            failures.append(
                f"{logical_name}: missing embedded tokens "
                + ", ".join(semantic_qa["missing_required_tokens"])
            )
        if semantic_qa["present_forbidden_tokens"]:
            failures.append(
                f"{logical_name}: forbidden embedded tokens "
                + ", ".join(semantic_qa["present_forbidden_tokens"])
            )
        figure_records.append({
            "logical_name": logical_name,
            "figure_id": figure["figure_id"],
            "scientific_status": figure["status"],
            "required_tokens": figure["required_tokens"],
            "forbidden_tokens": forbidden_tokens,
            "semantic_qa": semantic_qa,
            "outputs": outputs,
            "preview_modes": previews[logical_name],
        })

    preview_records: dict[str, dict[str, Any]] = {}
    for path in sorted(preview_root.glob("*.png")):
        preview_records[str(path.relative_to(metadata_root))] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "png": inspect_png(path),
        }

    manifest = {
        "schema": SCHEMA,
        "owner_id": OWNER_ID,
        "status": "LOCALLY_FROZEN_CANDIDATE_ONLY_NOT_LIVE_NOT_AUTHORISED",
        "scope": "English-only; 8 logical figures / 9 binaries",
        "live_manuscript_edited": False,
        "live_figure_tree_edited": False,
        "generator": {
            "path": str(SCRIPT.relative_to(WORKSPACE)),
            "sha256": sha256(SCRIPT),
            "render_argv": (
                "PYTHONHASHSEED=0 SOURCE_DATE_EPOCH=1785456000 "
                "python3 research/derivations/R181_HYPOTHESIS_PRESERVATION_v1/"
                "figures/build_r181_figures.py"
            ),
        },
        "inputs": frozen_inputs,
        "figures": figure_records,
        "previews": preview_records,
        "graph_topology_counts": map_counts,
        "semantic_contract": {
            "dimensionless_coefficient_formula": {
                "statement": "c_hat^2 = beta/(alpha-beta)",
                "status": "Level A conditional inside the supplied scalar principal EFT",
            },
            "unit_slope_coefficient_benchmark": {
                "statement": "c_hat = 1 (equivalently alpha = 2 beta)",
                "status": "Level B coefficient benchmark",
            },
            "scalar_clock_calibration": {
                "statement": "c_char = c",
                "status": "Level B calibration",
                "conditional_link": "algebraically equivalent to c_hat = 1 only when N_Phi = 1 and c_u = c",
            },
            "orientation_heavy_scale": {
                "symbol": "M_n,heavy",
                "status": "PARAMETRIC ONLY / MISSING VERTEX",
            },
            "yukawa_heavy_scale": {
                "symbol": "M_Y,heavy",
                "status": "distinct optional Yukawa completion; no equality to M_n,heavy is supplied",
            },
            "cross_sector_cone_universality": "Open",
        },
        "scientific_payload_policy": {
            "serialization": "UTF-8/LF/sorted JSON; fixed PDF dates; fixed locale/hash seed",
            "determinism_gate": "two isolated renders must be byte-identical",
            "semantic_negative_gate": "deprecated status/owner tokens must be absent from searchable PDF text",
            "manifest_excludes": [
                "R181_FIGURE_MANIFEST.json",
                "R181_RUNTIME_PROVENANCE.json",
                "R181_REPLAY_CHECK.json",
            ],
        },
        "open_microscopic_inputs": [
            "stationary P4 action/state/stability and dynamical O(4)->O(3) formation/selection",
            "P7 physical gauge connection, action, matter map, state and QCD scale/mass-gap owner",
            "microscopic action-valued owner of S0 and proof of universality",
            "physical clock/unit-conversion map and photon/tensor/common-cone matching",
            "microscopic derivation of zeta_phi and gravitational explanation of phi0 matching",
            "orientation field H_n, owner-specific scale M_n,heavy, coupling/operator vertex, Hessian, boundary conditions, regulator, subtraction and finite coefficient",
            "distinct Yukawa scale M_Y,heavy if that completion is invoked; no cross-sector heavy-scale equality is supplied",
            "constrained tensor representation/gauge reduction, positive pole residue and matter/source vertex",
        ],
    }
    write_text(metadata_root / "R181_FIGURE_MANIFEST.json", stable_json(manifest))

    build_report = {
        "schema": f"{SCHEMA}.build_report",
        "owner_id": OWNER_ID,
        "verdict": "PASS" if not failures else "FAIL",
        "logical_figure_count": len(FIGURES),
        "binary_count": sum(len(figure["outputs"]) for figure in FIGURES.values()),
        "preview_count": len(preview_records),
        "semantic_text_failures": failures,
        "map_topology_counts": map_counts,
        "artifact_axes": {
            "scientific_payload_deterministic": "PENDING REPLAY",
            "decisive_render_reproduced": "PENDING REPLAY",
            "scientific_dependency_closure": "OPEN; microscopic inputs listed in manifest",
            "local_owner_frozen": "PENDING REPLAY",
            "repository_tracked_public_provenance": "NO",
            "manuscript_use_authorised": "NO",
        },
    }
    write_text(metadata_root / "R181_FIGURE_BUILD_REPORT.json", stable_json(build_report))

    if write_runtime:
        dot_version = run_command(["dot", "-V"]).stderr.strip()
        runtime = {
            "schema": f"{SCHEMA}.runtime",
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "python": sys.version,
            "platform": platform.platform(),
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
            "pillow": Image.__version__,
            "pymupdf": fitz.VersionBind,
            "graphviz": dot_version,
            "source_date_epoch": SOURCE_DATE_EPOCH,
            "locale": "C",
            "hash_seed": "0",
            "note": "Volatile runtime sidecar; excluded from scientific manifest digest.",
        }
        write_text(metadata_root / "R181_RUNTIME_PROVENANCE.json", stable_json(runtime))

    if failures:
        raise RuntimeError("; ".join(failures))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-root",
        type=Path,
        default=DEFAULT_CANDIDATE_ROOT,
        help="Target LaTex/figures directory for the R181 candidate only.",
    )
    parser.add_argument(
        "--metadata-root",
        type=Path,
        default=PACKAGE,
        help="R181-owned directory for manifest, report and previews.",
    )
    parser.add_argument(
        "--no-runtime",
        action="store_true",
        help="Do not write the volatile runtime sidecar (used by isolated replay).",
    )
    args = parser.parse_args()
    manifest = build(
        args.candidate_root.resolve(),
        args.metadata_root.resolve(),
        write_runtime=not args.no_runtime,
    )
    summary = {
        "owner_id": manifest["owner_id"],
        "status": manifest["status"],
        "logical_figures": len(manifest["figures"]),
        "binaries": sum(len(row["outputs"]) for row in manifest["figures"]),
        "manifest": str((args.metadata_root.resolve() / "R181_FIGURE_MANIFEST.json")),
    }
    print(stable_json(summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
