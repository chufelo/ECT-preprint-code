#!/usr/bin/env python3
"""Render the proposal-only R114 M1-v2 same-channel FDT protocol figure.

The plotted numerical payload is the preserved v1 synthetic baseline, whose
decisive calculations are independently replayed by the v2 verifier.  The
v2 protocol, erratum and verifier own the interpretation.  The
figure contains standard equilibrium/non-equilibrium source-model examples;
it contains no experimental data and no ECT-specific signal or prediction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


BLUE = "#0072B2"
ORANGE = "#E69F00"
VERMILION = "#D55E00"
BLACK = "#222222"
GRAY = "#666666"
LIGHT_GRAY = "#E8E8E8"

EXPECTED_PROTOCOL_SHA256 = (
    "571272ff6ce376eac5f7e18d694002163d4f26773b47faccdb51cc1f3cc174f0"
)
EXPECTED_ERRATUM_SHA256 = (
    "1a3e5055b41b147ae06883aa2b19eba5a81b166e86d4e20a991984ca30f69b41"
)
EXPECTED_PROTOCOL_VERIFIER_SHA256 = (
    "ad0d638dffe6dc7e20b58e16737268999d66548f3342302cbfa4f96f0dd2c9da"
)
EXPECTED_BASELINE_VERIFIER_SHA256 = (
    "73ecd7c3912613e3023205cfb62a4eaf8cce7334e23b6f4d534274e59b9983ce"
)

CVD_MATRICES = {
    "protanopia": np.array(
        [
            [0.152286, 1.052583, -0.204868],
            [0.114503, 0.786281, 0.099216],
            [-0.003882, -0.048116, 1.051998],
        ]
    ),
    "deuteranopia": np.array(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ]
    ),
    "tritanopia": np.array(
        [
            [1.255528, -0.076749, -0.178779],
            [-0.078411, 0.930809, 0.147602],
            [0.004733, 0.691367, 0.303900],
        ]
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
            "font.size": 9.0,
            "axes.titlesize": 10.2,
            "axes.labelsize": 9.2,
            "axes.edgecolor": BLACK,
            "axes.linewidth": 0.8,
            "axes.grid": True,
            "grid.color": "#D9D9D9",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.75,
            "xtick.color": BLACK,
            "ytick.color": BLACK,
            "text.color": BLACK,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def payload_from_verifiers(protocol_verifier: Path, baseline_verifier: Path) -> dict:
    protocol_completed = subprocess.run(
        [sys.executable, str(protocol_verifier)],
        check=True,
        capture_output=True,
        text=True,
    )
    protocol_payload = json.loads(protocol_completed.stdout)
    if protocol_payload.get("status") != "PASS":
        raise RuntimeError("M1-v2 protocol verifier did not report PASS")
    if (
        protocol_payload.get("finite_window_forward_convolution_gate", {}).get(
            "conclusion"
        )
        != "a common finite window/bin is necessary but does not preserve "
        "pointwise FDT; forward-convolve the model"
    ):
        raise RuntimeError("M1-v2 finite-window guard is missing or stale")

    completed = subprocess.run(
        [sys.executable, str(baseline_verifier)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    if payload.get("status") != "PASS":
        raise RuntimeError("preserved M1 synthetic baseline did not report PASS")
    return payload


def rows_xy(rows: list[dict], y_key: str) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray([float(row["omega"]) for row in rows], dtype=float),
        np.asarray([float(row[y_key]) for row in rows], dtype=float),
    )


def pdf_metadata() -> dict[str, object]:
    return {
        "Title": "M1 same-channel FDT protocol",
        "Author": "ECT project",
        "Subject": (
            "Standard synthetic KMS benchmark and ordinary non-KMS counterexamples; "
            "not experimental data and not ECT signals."
        ),
        "Keywords": "PES; FDT; KMS; synthetic benchmark; conditional protocol",
        "Creator": "make_r114_pes_m1_fdt_figure_v2.py",
        "Producer": "Matplotlib",
        "CreationDate": None,
        "ModDate": None,
    }


def render(payload: dict, stem: Path) -> None:
    thermal = payload["thermal_oscillator_benchmark"]
    two_bath = payload["non_equilibrium_two_bath_counterexample"]
    occupation = payload["nonthermal_occupation_bump_counterexample"]
    filters = payload["filter_guard"]

    omega_kms, teff_kms = rows_xy(thermal["rows"], "T_eff_FDT")
    omega_two, teff_two = rows_xy(two_bath["rows"], "T_eff")
    omega_occ, teff_occ = rows_xy(occupation["rows"], "T_eff")
    omega_filter, teff_filter = rows_xy(filters["rows"], "T_eff_mismatched_filters")
    input_temperature = float(thermal["input_temperature"])

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.45))
    fig.subplots_adjust(left=0.075, right=0.975, bottom=0.30, top=0.80, wspace=0.24)

    ax = axes[0]
    ax.axhline(
        input_temperature,
        color=BLACK,
        lw=1.0,
        ls="--",
        label="input temperature",
    )
    ax.plot(
        omega_kms,
        teff_kms,
        color=BLUE,
        lw=1.8,
        ls="-",
        marker="o",
        ms=5.8,
        markeredgecolor=BLACK,
        markeredgewidth=0.45,
        label="recovered temperature",
    )
    ax.set(
        xlabel=r"angular frequency $\omega$ [synthetic units]",
        ylabel=r"$T_{\rm eff}$ [synthetic energy units]",
        title="Single KMS channel: flat recovered temperature",
        ylim=(4.2, 5.2),
    )
    ax.annotate(
        r"$T_{\rm eff}=4.7$ (FDT and detailed balance)",
        xy=(omega_kms[-1], teff_kms[-1]),
        xytext=(-8, 18),
        textcoords="offset points",
        ha="right",
        color=BLUE,
        fontsize=8.0,
        arrowprops={"arrowstyle": "-", "color": BLUE, "lw": 0.8},
    )
    ax.text(
        0.03,
        0.06,
        "standard KMS source model\nconditional Level A algebra",
        transform=ax.transAxes,
        fontsize=7.7,
        va="bottom",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": GRAY,
            "linewidth": 0.6,
        },
    )

    ax = axes[1]
    ax.plot(
        omega_two,
        teff_two,
        color=ORANGE,
        lw=1.7,
        ls="--",
        marker="D",
        ms=5.0,
        markeredgecolor=BLACK,
        markeredgewidth=0.45,
    )
    ax.plot(
        omega_occ,
        teff_occ,
        color=VERMILION,
        lw=1.7,
        ls="-.",
        marker="x",
        ms=6.4,
        mew=1.35,
    )
    ax.plot(
        omega_filter,
        teff_filter,
        color=GRAY,
        lw=1.7,
        ls=":",
        marker="s",
        ms=5.0,
        markerfacecolor="white",
        markeredgecolor=BLACK,
        markeredgewidth=0.75,
    )
    ax.axhline(input_temperature, color=BLACK, lw=0.8, ls="--")
    ax.set(
        xlabel=r"angular frequency $\omega$ [synthetic units]",
        ylabel=r"apparent $T_{\rm eff}$ [synthetic energy units]",
        title="Ordinary non-KMS or protocol counterexamples",
        ylim=(3.7, 15.7),
    )
    ax.annotate(
        "two thermal baths",
        xy=(omega_two[-1], teff_two[-1]),
        xytext=(-8, 6),
        textcoords="offset points",
        ha="right",
        color="#9A6500",
        fontsize=7.8,
    )
    peak_index = int(np.argmax(teff_occ))
    ax.annotate(
        "nonthermal occupation bump",
        xy=(omega_occ[peak_index], teff_occ[peak_index]),
        xytext=(15, 7),
        textcoords="offset points",
        ha="left",
        color=VERMILION,
        fontsize=7.8,
    )
    ax.annotate(
        "mismatched response/noise filters",
        xy=(omega_filter[-1], teff_filter[-1]),
        xytext=(-8, 7),
        textcoords="offset points",
        ha="right",
        color=BLACK,
        fontsize=7.8,
    )
    ax.text(
        0.03,
        0.96,
        "finite-window/bin data:\nforward model required",
        transform=ax.transAxes,
        fontsize=7.4,
        va="top",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": LIGHT_GRAY,
            "edgecolor": GRAY,
            "linewidth": 0.6,
            "hatch": "///",
        },
    )

    fig.suptitle(
        "M1 same-channel FDT protocol: diagnostic power and scope",
        fontsize=12.0,
        y=0.95,
    )
    fig.text(
        0.5,
        0.125,
        "Standard synthetic source models only — not experimental data or ECT signals.\n"
        "Common windows are necessary, not sufficient: forward-convolve the actual leakage kernel.\n"
        r"Freeze $S_0$/gain, matrix-complete channels, generator, preparation, causality/KK/contact terms; "
        "one-channel pass is not global KMS.",
        ha="center",
        va="center",
        fontsize=7.7,
        color=BLACK,
        bbox={
            "boxstyle": "round,pad=0.30",
            "facecolor": "white",
            "edgecolor": BLACK,
            "linewidth": 0.75,
        },
    )

    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), metadata=pdf_metadata())
    fig.savefig(
        stem.with_suffix(".png"),
        dpi=240,
        metadata={
            "Software": "ECT deterministic R114 M1-v2 renderer",
            "Title": "M1 same-channel FDT protocol",
            "Description": (
                "Standard synthetic source models only; not experimental data or ECT signals."
            ),
        },
    )
    plt.close(fig)


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    return np.where(
        rgb <= 0.0031308,
        12.92 * rgb,
        1.055 * np.power(np.clip(rgb, 0, None), 1.0 / 2.4) - 0.055,
    )


def make_accessibility_previews(png_path: Path, qa_dir: Path) -> list[Path]:
    qa_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(png_path).convert("RGB")
    outputs: list[Path] = []
    colour = qa_dir / f"{png_path.stem}_colour.png"
    source.save(colour, optimize=False)
    outputs.append(colour)
    grayscale = qa_dir / f"{png_path.stem}_grayscale.png"
    source.convert("L").convert("RGB").save(grayscale, optimize=False)
    outputs.append(grayscale)
    arr = np.asarray(source, dtype=float) / 255.0
    linear = srgb_to_linear(arr)
    for name, matrix in CVD_MATRICES.items():
        transformed = np.einsum("...j,ij->...i", linear, matrix)
        encoded = np.clip(linear_to_srgb(transformed), 0.0, 1.0)
        output = qa_dir / f"{png_path.stem}_{name}.png"
        Image.fromarray(np.uint8(np.rint(encoded * 255.0))).save(output, optimize=False)
        outputs.append(output)
    return outputs


def write_runtime_sidecar(
    path: Path,
    protocol: Path,
    erratum: Path,
    protocol_verifier: Path,
    baseline_verifier: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = {
        "schema": "R114_PES_M1_figure_runtime_v2",
        "python": platform.python_version(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "pillow": Image.__version__,
        "protocol_sha256": sha256(protocol),
        "erratum_sha256": sha256(erratum),
        "protocol_verifier_sha256": sha256(protocol_verifier),
        "baseline_verifier_sha256": sha256(baseline_verifier),
        "note": "Runtime metadata is excluded from the scientific manifest.",
    }
    path.write_text(
        json.dumps(sidecar, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol-note", required=True, type=Path)
    parser.add_argument("--erratum-note", required=True, type=Path)
    parser.add_argument("--protocol-verifier", required=True, type=Path)
    parser.add_argument("--baseline-verifier", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--qa-dir", required=True, type=Path)
    parser.add_argument("--runtime-sidecar", type=Path)
    args = parser.parse_args()

    configure()
    assert_hash(args.protocol_note, EXPECTED_PROTOCOL_SHA256)
    assert_hash(args.erratum_note, EXPECTED_ERRATUM_SHA256)
    assert_hash(args.protocol_verifier, EXPECTED_PROTOCOL_VERIFIER_SHA256)
    assert_hash(args.baseline_verifier, EXPECTED_BASELINE_VERIFIER_SHA256)
    payload = payload_from_verifiers(args.protocol_verifier, args.baseline_verifier)
    stem = args.output_dir / "r114_pes_m1_same_channel_fdt_protocol"
    render(payload, stem)
    make_accessibility_previews(stem.with_suffix(".png"), args.qa_dir)
    if args.runtime_sidecar:
        write_runtime_sidecar(
            args.runtime_sidecar,
            args.protocol_note,
            args.erratum_note,
            args.protocol_verifier,
            args.baseline_verifier,
        )


if __name__ == "__main__":
    main()
