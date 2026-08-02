#!/usr/bin/env python3
"""Build the preservation-first R177 equation-hierarchy successor."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


SCHEMA = "ect.r177.equation-hierarchy-successor.v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(path: Path) -> dict[str, object]:
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "mathtext.fontset": "cm",
    })
    fig, ax = plt.subplots(figsize=(7.2, 9.4))
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 9.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    nodes: dict[str, tuple[float, float, float, float]] = {}

    def box(
        key: str,
        x: float,
        y: float,
        width: float,
        height: float,
        lines: tuple[str, ...],
        status: str,
        fill: str,
        edge: str,
        font_size: float = 10.2,
    ) -> None:
        nodes[key] = (x, y, width, height)
        ax.add_patch(FancyBboxPatch(
            (x - width / 2.0, y - height / 2.0),
            width,
            height,
            boxstyle="round,pad=0.10",
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.7,
            zorder=3,
        ))
        ax.text(
            x,
            y + 0.08,
            "\n".join(lines),
            ha="center",
            va="center",
            fontsize=font_size,
            zorder=4,
            linespacing=1.18,
        )
        ax.text(
            x,
            y - height / 2.0 + 0.10,
            status,
            ha="center",
            va="bottom",
            fontsize=7.8,
            color="0.30",
            fontstyle="italic",
            zorder=4,
        )

    def arrow(
        source: str,
        target: str,
        label: str,
        source_x_shift: float = 0.0,
        target_x_shift: float = 0.0,
        label_position: tuple[float, float] | None = None,
    ) -> None:
        x0, y0, _w0, h0 = nodes[source]
        x1, y1, _w1, h1 = nodes[target]
        start = (x0 + source_x_shift, y0 - h0 / 2.0)
        end = (x1 + target_x_shift, y1 + h1 / 2.0)
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops={
                "arrowstyle": "-|>",
                "color": "0.30",
                "lw": 1.6,
                "mutation_scale": 15,
                "linestyle": (0, (4, 2.5)),
            },
            zorder=2,
        )
        label_x, label_y = label_position or (
            (start[0] + end[0]) / 2.0 + 0.08,
            (start[1] + end[1]) / 2.0,
        )
        ax.text(
            label_x,
            label_y,
            label,
            fontsize=7.6,
            color="0.28",
            ha="left",
            va="center",
            fontstyle="italic",
            zorder=5,
        )

    box(
        "P3",
        1.85,
        8.35,
        3.15,
        1.22,
        (
            r"P3 homogeneous scalar owner",
            r"$m_{\Phi,\rm rad}^2=V''(\phi_0)=2\mu^2$",
            r"$\xi_{\rm P3}=m_{\Phi,\rm rad}^{-1}$",
        ),
        "A-math inside supplied P3;\nnot a P4 pole",
        "#D9EAF7",
        "#0072B2",
        9.1,
    )
    box(
        "P4",
        5.35,
        8.35,
        3.15,
        1.22,
        (
            r"P4 non-zero-gradient datum",
            r"$\langle\partial_A\Phi\rangle=u_0\delta_{Aw}$",
            r"stabiliser $O(3)$; no spectrum supplied",
        ),
        "conditional kinematics;\naction/Hessian/pole Open",
        "#DDF3EA",
        "#009E73",
        9.1,
    )

    box(
        "L1",
        3.6,
        6.25,
        5.9,
        1.25,
        (
            r"P4 datum + separately supplied scalar EFT",
            r"$K^{AB}\partial_A\partial_B\chi+M_{\rm eff}^2\chi=0$",
            r"$K^{AB}=\beta\delta^{AB}-\alpha n^An^B$",
            r"Lorentzian iff $\beta(\beta-\alpha)<0$",
        ),
        "Level 1: EFT coefficients and physical P4 pole/cutoff not supplied by P4",
        "#E7E7E7",
        "#444444",
        9.6,
    )
    arrow(
        "P3", "L1", "P3--P4 equality: Open matching", 0.55, -0.55,
        label_position=(0.72, 7.10),
    )
    arrow(
        "P4", "L1", "P4 datum/stabiliser only", -0.55, 0.55,
        label_position=(4.42, 7.10),
    )

    box(
        "L2",
        3.6,
        4.15,
        5.9,
        1.05,
        (
            r"$\partial_t^2\varphi-c_*^2\nabla^2\varphi+M^2\varphi=0$",
            "conditional scalar Klein--Gordon form",
        ),
        "Level 2: coordinate, clock, common cone and physical-state map Open",
        "#F3E7C9",
        "#D89000",
        10.1,
    )
    arrow("L1", "L2", "conditional coordinate / clock / cone map")

    box(
        "L3",
        3.6,
        2.05,
        5.9,
        1.15,
        (
            r"$i\hbar\,\partial_t\psi="
            r"-[\hbar^2/(2m)]\nabla^2\psi+V\psi$",
            "conditional Schrödinger-type envelope",
        ),
        "Level 3: hbar calibration + state/operator/measure/detector owners required",
        "#F6E1D8",
        "#CC5500",
        9.9,
    )
    arrow("L2", "L3", "state + positive-frequency + NR assumptions")

    ax.text(
        3.6,
        0.58,
        "Dashed arrows are conditional dependencies, never status upgrades.\n"
        "P3 radial curvature, P4 datum, scalar-EFT coefficients and quantum calibration have distinct owners.",
        ha="center",
        va="center",
        fontsize=8.7,
        color="0.25",
        fontweight="bold",
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        bbox_inches="tight",
        metadata={
            "Title": "R177 preservation-first equation hierarchy",
            "Author": "ECT R177 reproducibility builder",
            "Subject": "P3, P4, scalar-EFT and quantum-calibration owners separated",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    plt.close(fig)
    return {
        "nodes": 5,
        "edges": 4,
        "scientific_owner_split": [
            "P3 homogeneous radial curvature",
            "P4 datum and stabiliser kinematics",
            "separately supplied scalar EFT",
            "conditional clock/cone map",
            "hbar/state/operator/measure/detector calibration",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    asset = output / "assets/fig_equation_hierarchy_r177.pdf"
    semantics = render(asset)
    with tempfile.TemporaryDirectory(prefix="r177-equation-hierarchy-replay-") as temp:
        replay = Path(temp) / asset.name
        render(replay)
        replay_equal = asset.read_bytes() == replay.read_bytes()
    if not replay_equal:
        raise RuntimeError("equation-hierarchy replay was not byte-identical")

    report = {
        "schema": SCHEMA,
        "status": "CANDIDATE_ONLY_NOT_LIVE_APPLY",
        "asset": str(asset.relative_to(output)),
        "asset_sha256": sha256(asset),
        "asset_bytes": asset.stat().st_size,
        "replay_byte_identical": replay_equal,
        "semantics": semantics,
        "predecessor": {
            "path": "LaTex/figures/r149/r149_equation_hierarchy.pdf",
            "disposition": "SUPERSEDED_PRESERVED",
            "reason": "predecessor silently assigned the scalar EFT and radial mass to P4",
        },
    }
    (output / "BUILD_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest: dict[str, dict[str, int | str]] = {}
    for item in sorted(
        path for path in output.rglob("*")
        if path.is_file() and path.name != "PACKAGE_MANIFEST.json"
    ):
        manifest[str(item.relative_to(output))] = {
            "bytes": item.stat().st_size,
            "sha256": sha256(item),
        }
    (output / "PACKAGE_MANIFEST.json").write_text(
        json.dumps(
            {"schema": SCHEMA + ".manifest", "payload": manifest},
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
