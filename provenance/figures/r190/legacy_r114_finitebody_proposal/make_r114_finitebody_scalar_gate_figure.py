#!/usr/bin/env python3
"""Render the proposal-only R114 finite-body scalar-gate figure.

The renderer consumes only the exact, hash-frozen manuscript candidate tables
and the locally frozen R113/R114 owner manifests.  It does not identify the
fixed-metric scalar proxies with physical body sensitivities or a PPN metric.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"
PURPLE = "#CC79A7"
VERMILION = "#D55E00"
BLACK = "#222222"
GRAY = "#666666"
LIGHT_GRAY = "#E8E8E8"

EXPECTED = {
    "candidate_tex": "549992e9d48fc2fa716325d249b96f53cf4092f10dab66030dc3cf5f72e1367a",
    "r113_manifest": "5b11dae4993190ab1c0ae0f5e2783638dc7f445c757208c953904d5e19adf806",
    "r114_manifest": "b4fa7b018aab10793e2285c34e0efd6eab00b551e2e27c25f27f84c4a00cf7b7",
    "r114_aggregate": "5ae7eab0008bbcc8ddf7ac1ff0da4b007e3a0b6b30243dbb6792ffd40b2c5747",
    "producer": "b63770e7ef354d8296214fce409b1c40edd0d629e0ee16843ddc9eae59c61a5b",
    "redteam": "d5e00cefa6c68b625d33f935c031a374f1cc51094a5a4ebc014e6b040e889da7",
}

CVD_MATRICES = {
    "protanopia": np.array(
        [[0.152286, 1.052583, -0.204868],
         [0.114503, 0.786281, 0.099216],
         [-0.003882, -0.048116, 1.051998]]
    ),
    "deuteranopia": np.array(
        [[0.367322, 0.860646, -0.227968],
         [0.280085, 0.672501, 0.047413],
         [-0.011820, 0.042940, 0.968881]]
    ),
    "tritanopia": np.array(
        [[1.255528, -0.076749, -0.178779],
         [-0.078411, 0.930809, 0.147602],
         [0.004733, 0.691367, 0.303900]]
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_hash(path: Path, expected: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"input hash mismatch for {path}: {actual} != {expected}")


def configure() -> None:
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.6,
            "axes.titlesize": 10.0,
            "axes.labelsize": 8.8,
            "axes.edgecolor": BLACK,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "grid.color": "#D9D9D9",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.75,
            "xtick.color": BLACK,
            "ytick.color": BLACK,
            "text.color": BLACK,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def pdf_metadata() -> dict[str, object]:
    return {
        "Title": "R114 finite-body scalar gates",
        "Author": "ECT project",
        "Subject": (
            "Fixed-metric scalar BVP and dimensional gate only; not physical "
            "body sensitivity, coupled metric, Cassini, WEP, or full PPN prediction."
        ),
        "Keywords": "ECT; finite-body; fixed-metric scalar BVP; proposal-only",
        "Creator": "make_r114_finitebody_scalar_gate_figure.py",
        "Producer": "Matplotlib",
        "CreationDate": None,
        "ModDate": None,
    }


def extract_longtable(text: str, label: str) -> str:
    token = rf"\label{{{label}}}"
    index = text.find(token)
    if index < 0 or text.find(token, index + 1) >= 0:
        raise RuntimeError(f"label must occur exactly once: {label}")
    start = text.rfind(r"\begin{longtable}", 0, index)
    end = text.find(r"\end{longtable}", index)
    if start < 0 or end < 0:
        raise RuntimeError(f"could not isolate longtable for {label}")
    return text[start:end + len(r"\end{longtable}")]


def tex_number(token: str) -> float:
    cleaned = token.strip().replace(r"\(", "").replace(r"\)", "")
    cleaned = cleaned.replace("{", "").replace("}", "")
    match = re.fullmatch(r"([0-9.]+)\\times10\^([+-]?[0-9]+)", cleaned)
    if match:
        return float(match.group(1)) * 10.0 ** int(match.group(2))
    return float(cleaned)


def parse_proxy_table(text: str) -> list[dict[str, float]]:
    block = extract_longtable(text, "tab:ect_twoslope_finite_body_proxy")
    rows = []
    mapping = {"10": 10.0, "100": 100.0, r"\(10^3\)": 1.0e3, r"\(10^4\)": 1.0e4}
    for raw, density in mapping.items():
        match = re.search(
            rf"^{re.escape(raw)}\s*&\s*([0-9.]+)\s*&\s*([0-9.]+)\\\\$",
            block,
            flags=re.MULTILINE,
        )
        if not match:
            raise RuntimeError(f"missing finite-body proxy row {raw}")
        rows.append(
            {
                "density_contrast": density,
                "surface_flux_ratio": float(match.group(1)),
                "far_tail_ratio": float(match.group(2)),
            }
        )
    return rows


def parse_estimator_registry(text: str) -> list[dict[str, object]]:
    specs = [
        (
            "finite-window mean",
            r"Finite-window mean of \$xe\^x\[u\(x\)-1\]\$ on \$5\\le x\\le9\$,\s*\$r=0\.99\$\s*&\s*([0-9.]+)\\\\",
        ),
        (
            "FD/Green asymptotic",
            r"Green-identity / finite-difference asymptotic coefficient,\s*\$r=0\.99\$\s*&\s*([0-9.]+)\\\\",
        ),
        (
            r"regular $r\to1$ limit",
            r"Asymptotic coefficient in the regular \$r\\to1\$ limit at fixed \$\\eta\$\s*&\s*([0-9.]+)\\\\",
        ),
    ]
    rows = []
    for label, pattern in specs:
        match = re.search(pattern, text, flags=re.DOTALL)
        if not match:
            raise RuntimeError(f"missing estimator registry row: {label}")
        rows.append({"label": label, "ratio": float(match.group(1))})
    return rows


def parse_object_table(text: str) -> list[dict[str, object]]:
    block = extract_longtable(text, "tab:ect_twoslope_finite_body_objects")
    objects = [
        ("Earth", "Earth"),
        ("Sun", "Sun"),
        ("Jupiter", "Jupiter"),
        ("Milky-Way mean within 15 kpc", "Milky Way"),
        ("cluster mean within 1 Mpc", "cluster"),
    ]
    rows = []
    for source_name, display_name in objects:
        match = re.search(
            rf"^{re.escape(source_name)}\s*&\s*(.*?)\s*&\s*(.*?)\s*&\s*(.*?)\\\\$",
            block,
            flags=re.MULTILINE,
        )
        if not match:
            raise RuntimeError(f"missing finite-body object row: {source_name}")
        rows.append(
            {
                "object": display_name,
                "m_out_R": tex_number(match.group(1)),
                "Xi_body": tex_number(match.group(2)),
            }
        )
    return rows


def verify_owner_chain(
    r113_manifest_path: Path,
    r114_manifest_path: Path,
    producer: Path,
    redteam: Path,
) -> dict[str, object]:
    assert_hash(r113_manifest_path, EXPECTED["r113_manifest"])
    assert_hash(r114_manifest_path, EXPECTED["r114_manifest"])
    assert_hash(producer, EXPECTED["producer"])
    assert_hash(redteam, EXPECTED["redteam"])
    r114 = json.loads(r114_manifest_path.read_text(encoding="utf-8"))
    if r114.get("aggregate_sha256") != EXPECTED["r114_aggregate"]:
        raise RuntimeError("R114 scientific aggregate mismatch")
    by_path = {entry["path"]: entry["sha256"] for entry in r114.get("files", [])}
    expected_entries = {
        "scripts/cosmology/compute_r114_twoslope_finitebody_estimators.py": EXPECTED["producer"],
        "scripts/verification/r114/verify_r114_twoslope_finitebody_estimators.py": EXPECTED["redteam"],
    }
    for path, expected in expected_entries.items():
        if by_path.get(path) != expected:
            raise RuntimeError(f"R114 owner manifest entry mismatch: {path}")
    return {
        "r113_manifest_sha256": EXPECTED["r113_manifest"],
        "r114_manifest_sha256": EXPECTED["r114_manifest"],
        "r114_aggregate_sha256": EXPECTED["r114_aggregate"],
        "producer_sha256": EXPECTED["producer"],
        "redteam_sha256": EXPECTED["redteam"],
    }


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    return np.where(
        rgb <= 0.0031308,
        12.92 * rgb,
        1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055,
    )


def make_accessibility_previews(png_path: Path, qa_dir: Path) -> list[Path]:
    qa_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(png_path).convert("RGB")
    outputs = []
    colour = qa_dir / f"{png_path.stem}_colour.png"
    image.save(colour, optimize=False)
    outputs.append(colour)
    grayscale = qa_dir / f"{png_path.stem}_grayscale.png"
    image.convert("L").convert("RGB").save(grayscale, optimize=False)
    outputs.append(grayscale)
    array = np.asarray(image, dtype=float) / 255.0
    linear = srgb_to_linear(array)
    for name, matrix in CVD_MATRICES.items():
        transformed = np.einsum("...j,ij->...i", linear, matrix)
        encoded = np.clip(linear_to_srgb(transformed), 0.0, 1.0)
        path = qa_dir / f"{png_path.stem}_{name}.png"
        Image.fromarray(np.uint8(np.rint(encoded * 255.0))).save(path, optimize=False)
        outputs.append(path)
    return outputs


def render(
    proxy_rows: list[dict[str, float]],
    estimators: list[dict[str, object]],
    object_rows: list[dict[str, object]],
    stem: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.6, 4.85), constrained_layout=False)
    fig.subplots_adjust(left=0.055, right=0.985, top=0.82, bottom=0.25, wspace=0.36)

    ax = axes[0]
    density = np.array([row["density_contrast"] for row in proxy_rows])
    flux = np.array([row["surface_flux_ratio"] for row in proxy_rows])
    tail = np.array([row["far_tail_ratio"] for row in proxy_rows])
    ax.plot(
        density, flux, color=BLUE, ls="-", lw=1.8, marker="o", ms=5.8,
        markeredgecolor=BLACK, markeredgewidth=0.45,
        label="surface flux / linear source",
    )
    ax.plot(
        density, tail, color=ORANGE, ls="--", lw=1.8, marker="D", ms=5.2,
        markerfacecolor="white", markeredgecolor=BLACK, markeredgewidth=0.8,
        label=r"far tail $A_{\rm far}/A_{\rm lin}$",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 1.15)
    ax.set(
        xlabel=r"density contrast $\rho_{\rm in}/\rho_{\rm out}$",
        ylabel="dimensionless suppression ratio",
        title=r"A  Fixed-metric BVP, $m_{\rm out}R=1$",
    )
    ax.legend(loc="lower left", fontsize=7.3)
    ax.text(
        0.97, 0.96, "four supplied rows\nsegments guide the eye",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.0,
        bbox={"boxstyle": "round,pad=0.22", "facecolor": "white", "edgecolor": GRAY, "linewidth": 0.55},
    )

    ax = axes[1]
    values = np.array([float(row["ratio"]) for row in estimators])
    labels = [str(row["label"]) for row in estimators]
    y = np.arange(len(values))[::-1]
    colours = [BLUE, GREEN, PURPLE]
    markers = ["o", "^", "D"]
    linestyles = ["-", "-.", ":"]
    x_min = min(values) - 0.000008
    for yi, value, colour, marker, linestyle in zip(y, values, colours, markers, linestyles):
        ax.hlines(yi, x_min, value, color=colour, lw=1.5, ls=linestyle)
        ax.plot(value, yi, color=colour, marker=marker, ms=6.0,
                markeredgecolor=BLACK, markeredgewidth=0.55)
        ax.text(value + 0.0000011, yi, f"{value:.12f}", va="center", fontsize=7.2)
    ax.set_yticks(y, labels)
    ax.set_xlim(x_min, max(values) + 0.000012)
    ax.ticklabel_format(axis="x", style="plain", useOffset=False)
    ax.set(
        xlabel="declared nonlinear/linear ratio",
        title="B  Three tail estimators (not averaged)",
    )
    ax.grid(axis="y", visible=False)
    absolute_spread = float(max(values) - min(values))
    relative_spread = absolute_spread / float(min(values))
    ax.text(
        0.03, 0.68,
        rf"full range $={absolute_spread:.8f}$" "\n"
        rf"$={100.0 * relative_spread:.3f}\%$ of regular-limit value",
        transform=ax.transAxes, ha="left", va="center", fontsize=7.1,
        bbox={"boxstyle": "round,pad=0.22", "facecolor": "white", "edgecolor": GRAY, "linewidth": 0.55},
    )

    ax = axes[2]
    object_names = [str(row["object"]) for row in object_rows]
    xi = np.array([float(row["Xi_body"]) for row in object_rows])
    x = np.arange(len(xi))
    colours = [BLUE, BLUE, BLUE, GREEN, PURPLE]
    markers = ["o", "s", "D", "^", "v"]
    for index, (value, colour, marker) in enumerate(zip(xi, colours, markers)):
        ax.vlines(index, 1.0e-15, value, color=colour, lw=1.5, ls="-")
        ax.plot(index, value, color=colour, marker=marker, ms=6.2,
                markeredgecolor=BLACK, markeredgewidth=0.55)
        ax.annotate(
            f"{value:.2e}", (index, value), xytext=(0, 6),
            textcoords="offset points", ha="center", va="bottom", fontsize=6.8,
        )
    ax.axhline(1.0, color=VERMILION, lw=1.7, ls="--", label=r"threshold $\Xi_{\rm body}=1$")
    ax.set_yscale("log")
    ax.set_ylim(8.0e-15, 3.0)
    ax.set_xticks(x, object_names, rotation=27, ha="right")
    ax.set(
        ylabel=r"dimensional gate $\Xi_{\rm body}$",
        title=r"C  Named-object gate: all $\Xi_{\rm body}\ll1$",
    )
    ax.legend(loc="upper left", fontsize=7.3)

    fig.suptitle(
        "R114 finite-body scalar gates: suppression proxies and dimensional obstruction",
        fontsize=12.0,
        y=0.965,
    )
    fig.text(
        0.5, 0.055,
        "Fixed-metric scalar BVP / dimensional gate only; not physical body sensitivity, "
        "not coupled metric, not Cassini/WEP/full PPN prediction.",
        ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=BLACK,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": LIGHT_GRAY, "edgecolor": BLACK, "linewidth": 0.7},
    )
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), metadata=pdf_metadata())
    fig.savefig(
        stem.with_suffix(".png"), dpi=240,
        metadata={
            "Software": "ECT deterministic R114 finite-body renderer",
            "Title": "R114 finite-body scalar gates",
            "Description": (
                "Fixed-metric scalar BVP / dimensional gate only; not physical body "
                "sensitivity, not coupled metric, not Cassini/WEP/full PPN prediction."
            ),
        },
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-tex", required=True, type=Path)
    parser.add_argument("--r113-manifest", required=True, type=Path)
    parser.add_argument("--r114-manifest", required=True, type=Path)
    parser.add_argument("--producer", required=True, type=Path)
    parser.add_argument("--redteam", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--qa-dir", required=True, type=Path)
    parser.add_argument("--runtime-sidecar", type=Path)
    args = parser.parse_args()
    configure()

    assert_hash(args.candidate_tex, EXPECTED["candidate_tex"])
    owner_chain = verify_owner_chain(
        args.r113_manifest, args.r114_manifest, args.producer, args.redteam
    )
    text = args.candidate_tex.read_text(encoding="utf-8")
    proxy_rows = parse_proxy_table(text)
    estimators = parse_estimator_registry(text)
    object_rows = parse_object_table(text)
    stem = args.output_dir / "r114_finitebody_scalar_gates"
    render(proxy_rows, estimators, object_rows, stem)
    make_accessibility_previews(stem.with_suffix(".png"), args.qa_dir)

    if args.runtime_sidecar:
        args.runtime_sidecar.parent.mkdir(parents=True, exist_ok=True)
        args.runtime_sidecar.write_text(
            json.dumps(
                {
                    "schema": "R114_finitebody_figure_runtime_v1",
                    "candidate_tex_sha256": EXPECTED["candidate_tex"],
                    "owner_chain": owner_chain,
                    "python": platform.python_version(),
                    "numpy": np.__version__,
                    "matplotlib": matplotlib.__version__,
                    "pillow": Image.__version__ if hasattr(Image, "__version__") else "unknown",
                },
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
