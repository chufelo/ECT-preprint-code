#!/usr/bin/env python3
"""Render the bounded R114 cosmology closure figures from frozen owners.

The figures are diagnostics of declared models.  They are not observational
posteriors, JWST predictions, cluster-lensing reconstructions or general
no-go results for arbitrary causal kernels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
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
    "early_csv": "8a6fd7818ee0fc0ed5683ec58fa3beeff778e7966590c5ba606442f71e631e35",
    "early_json": "a538c86d69989e6030a157465a779dd7fb950acdb7573c9680c043e92a222db0",
    "one_pole_json": "d0cbf68192cc26629b9ec92a561b0b999888b6fd5dc518c5648e6cbbbc86fff0",
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
            "font.size": 9.0,
            "axes.titlesize": 10.5,
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
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def pdf_metadata(title: str, subject: str) -> dict[str, object]:
    return {
        "Title": title,
        "Author": "ECT project",
        "Subject": subject,
        "Keywords": "ECT; conditional diagnostic; status-explicit",
        "Creator": "make_r114_closure_figures.py",
        "Producer": "Matplotlib",
        "CreationDate": None,
        "ModDate": None,
    }


def save_figure(fig: plt.Figure, stem: Path, title: str, subject: str) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        stem.with_suffix(".pdf"),
        bbox_inches="tight",
        metadata=pdf_metadata(title, subject),
    )
    fig.savefig(
        stem.with_suffix(".png"),
        dpi=240,
        bbox_inches="tight",
        metadata={
            "Software": "ECT deterministic R114 renderer",
            "Title": title,
            "Description": subject,
        },
    )
    plt.close(fig)


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055)


def make_accessibility_previews(png_path: Path, qa_dir: Path) -> list[Path]:
    qa_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(png_path).convert("RGB")
    image.save(qa_dir / f"{png_path.stem}_colour.png", optimize=False)
    image.convert("L").convert("RGB").save(
        qa_dir / f"{png_path.stem}_grayscale.png", optimize=False
    )
    arr = np.asarray(image, dtype=float) / 255.0
    linear = srgb_to_linear(arr)
    outputs = [
        qa_dir / f"{png_path.stem}_colour.png",
        qa_dir / f"{png_path.stem}_grayscale.png",
    ]
    for name, matrix in CVD_MATRICES.items():
        transformed = np.einsum("...j,ij->...i", linear, matrix)
        encoded = np.clip(linear_to_srgb(transformed), 0.0, 1.0)
        path = qa_dir / f"{png_path.stem}_{name}.png"
        Image.fromarray(np.uint8(np.rint(encoded * 255.0))).save(path, optimize=False)
        outputs.append(path)
    return outputs


def read_early_rows(csv_path: Path) -> list[dict[str, float]]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = [{key: float(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    rows.sort(key=lambda row: row["zeta_ER"])
    if len(rows) != 5 or any(rows[i]["zeta_ER"] >= rows[i + 1]["zeta_ER"] for i in range(4)):
        raise RuntimeError("early-response owner must contain five strictly ordered rows")
    return rows


def early_response_figure(rows: list[dict[str, float]], stem: Path) -> None:
    zeta = np.array([row["zeta_ER"] for row in rows])
    growth = np.array([row["D_over_D0_z10_zon1000"] for row in rows])
    equality = np.array([row["equality_ratio"] for row in rows])
    ps_fixed = np.array([row["cumulative_PS_ratio_nu5_fixed_barrier"] for row in rows])
    ps_tophat = np.array([row["cumulative_PS_ratio_nu5_tophat_barrier"] for row in rows])

    fig, axes = plt.subplots(1, 2, figsize=(10.7, 4.25), constrained_layout=True)
    ax = axes[0]
    ax.plot(zeta, growth, color=BLUE, lw=1.7, ls="-", marker="o", ms=5.5,
            markeredgecolor=BLACK, markeredgewidth=0.45, label=r"growth $D/D_0$")
    ax.plot(zeta, equality, color=ORANGE, lw=1.7, ls="--", marker="D", ms=5.2,
            markeredgecolor=BLACK, markeredgewidth=0.45, label="equality-coordinate ratio")
    ax.axhline(1.0, color=GRAY, lw=1.0, ls=":", label="control ratio = 1")
    ax.set_xscale("log")
    ax.set(
        xlabel=r"owner coordinate $\zeta_{\rm ER}$",
        ylabel="dimensionless ratio",
        title="Growth and equality response",
    )
    ax.legend(loc="upper left", fontsize=8)
    ax.annotate(f"{growth[-1]:.3f}", (zeta[-1], growth[-1]), xytext=(-30, 7),
                textcoords="offset points", color=BLUE, fontsize=8)
    ax.annotate(f"{equality[-1]:.3f}", (zeta[-1], equality[-1]), xytext=(-34, -14),
                textcoords="offset points", color=BLACK, fontsize=8)

    ax = axes[1]
    ax.plot(zeta, ps_fixed, color=GREEN, lw=1.7, ls="-.", marker="^", ms=6,
            markeredgecolor=BLACK, markeredgewidth=0.45,
            label=r"fixed barrier, $\nu=5$")
    ax.plot(zeta, ps_tophat, color=PURPLE, lw=1.7, ls=":", marker="D", ms=5.4,
            markerfacecolor="white", markeredgecolor=BLACK, markeredgewidth=0.75,
            label=r"top-hat barrier, $\nu=5$")
    ax.axhline(1.0, color=GRAY, lw=1.0, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(
        xlabel=r"owner coordinate $\zeta_{\rm ER}$",
        ylabel="cumulative Press--Schechter sensitivity ratio",
        title="Rare-tail sensitivity (Level C)",
    )
    ax.legend(loc="upper left", fontsize=8)
    ax.text(
        0.98,
        0.035,
        "five prescribed rows; connecting segments guide the eye\n"
        "not a posterior, JWST prediction, or cosmological likelihood",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.2,
        color=BLACK,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": GRAY, "linewidth": 0.6},
    )
    fig.suptitle("Owner-specific early-response envelope", fontsize=12)
    save_figure(
        fig,
        stem,
        "Owner-specific early-response envelope",
        "Level A algebra inside the supplied envelope and Level C rare-tail sensitivity; not a JWST prediction.",
    )


def extract_one_pole(data: dict) -> tuple[list[tuple[float, float]], list[float], list[tuple[float, float]]]:
    matching = []
    for key, value in data["tau_aM_Gyr"].items():
        matching.append((float(key.removeprefix("H0=")), 1000.0 * float(value)))
    matching.sort()
    required = sorted(float(value) for value in data["required_offset_times_Myr"].values())
    distances = []
    for key, value in data["ballistic_transport_at_H0_70_Mpc"].items():
        speed = float(key.removeprefix("v="))
        distances.append((speed, 1000.0 * float(value)))
    distances.sort()
    return matching, required, distances


def one_pole_figure(data: dict, stem: Path) -> None:
    matching, required, distances = extract_one_pole(data)
    h0 = np.array([row[0] for row in matching])
    tau_myr = np.array([row[1] for row in matching])
    required_min, required_max = min(required), max(required)
    speeds = np.array([row[0] for row in distances])
    distance_kpc = np.array([row[1] for row in distances])

    fig, axes = plt.subplots(1, 2, figsize=(10.7, 4.25), constrained_layout=True)
    ax = axes[0]
    ax.fill_between([h0.min() - 1, h0.max() + 1], required_min, required_max,
                    facecolor=LIGHT_GRAY, edgecolor=GRAY, hatch="///", linewidth=0.8,
                    label="70--100 kpc ballistic target")
    ax.plot(h0, tau_myr, color=VERMILION, ls="-.", marker="x", ms=7, mew=1.5,
            lw=1.8, label=r"conditional $\tau_{a_M}=2\pi/H_0$")
    ax.set_yscale("log")
    ax.set(
        xlabel=r"$H_0$ [km s$^{-1}$ Mpc$^{-1}$]",
        ylabel="time [Myr]",
        title="Conditional timescale mismatch",
    )
    ax.legend(loc="center left", fontsize=8)

    ax = axes[1]
    ax.fill_between([speeds.min() - 80, speeds.max() + 80], 70.0, 100.0,
                    facecolor=LIGHT_GRAY, edgecolor=GRAY, hatch="///", linewidth=0.8,
                    label="target offset")
    ax.plot(speeds, distance_kpc, color=VERMILION, ls="-.", marker="x", ms=7,
            mew=1.5, lw=1.8, label=r"$v\tau_{a_M}$ at $H_0=70$")
    ax.set_yscale("log")
    ax.set(
        xlabel=r"speed [km s$^{-1}$]",
        ylabel="distance [kpc]",
        title="Ballistic-distance mismatch",
    )
    ax.legend(loc="center left", fontsize=8)
    ax.text(
        0.98,
        0.045,
        r"mismatch $2.02\times10^3$--$3.85\times10^3$" "\n"
        "restricted to one real pole + ballistic transport",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.4,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": GRAY, "linewidth": 0.6},
    )
    fig.suptitle("One-real-pole cluster-scale test", fontsize=12)
    save_figure(
        fig,
        stem,
        "One-real-pole cluster-scale test",
        "Conditional no-go for tau_pole=2pi/H0 plus ballistic transport only; general causal kernels remain open.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--qa-dir", type=Path, required=True)
    args = parser.parse_args()
    configure()

    early_csv = args.data_dir / "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.csv"
    early_json = args.data_dir / "R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.json"
    one_pole_json = args.data_dir / "R113_ONE_POLE_CLUSTER_NO_GO_v2.json"
    assert_hash(early_csv, EXPECTED["early_csv"])
    assert_hash(early_json, EXPECTED["early_json"])
    assert_hash(one_pole_json, EXPECTED["one_pole_json"])
    early_meta = json.loads(early_json.read_text(encoding="utf-8"))
    if not early_meta.get("all_checks_pass"):
        raise RuntimeError("frozen early-response owner did not pass its own checks")
    one_pole = json.loads(one_pole_json.read_text(encoding="utf-8"))
    if not one_pole.get("all_checks_pass"):
        raise RuntimeError("frozen one-pole owner did not pass its own checks")

    outputs = [
        ("r114_early_response_growth_collapse_envelope", early_response_figure,
         read_early_rows(early_csv)),
        ("r114_one_real_pole_cluster_scale_no_go", one_pole_figure, one_pole),
    ]
    for name, renderer, payload in outputs:
        stem = args.output_dir / name
        renderer(payload, stem)
        make_accessibility_previews(stem.with_suffix(".png"), args.qa_dir)


if __name__ == "__main__":
    main()
