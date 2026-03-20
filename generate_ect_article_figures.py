#!/usr/bin/env python3
"""
Generate article figures for the ECT Hubble + JWST + age block.

This script uses the current numerical artefacts and the current solver
implementation to build the main visual layer requested for the paper:

1. Benchmark control figure (re-generated from the benchmark solver)
2. Derived-parent parameter scan with labeled working points
3. Benchmark vs derived-parent comparison figure
4. Conceptual evolution figure for the Universe and condensate
5. JWST anchor age/maturity budget figure

Expected inputs in the same directory (or specified via --data-dir):
- ect_hubble_jwst_background_v6.py
- derived_parent_scan_stage1.csv
- derived_parent_preferred_points.csv
- jwst_object_age_budget_stage2.csv
- jwst_maturity_budget_stage3.csv

Outputs are written to --outdir as both PDF and PNG.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


# ------------------------------ loading helpers -----------------------------

def load_solver_module(data_dir: Path):
    solver_path = data_dir / "ect_hubble_jwst_background_v6.py"
    if not solver_path.exists():
        raise FileNotFoundError(f"Missing solver module: {solver_path}")
    spec = importlib.util.spec_from_file_location("ect_v6", solver_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_csv(data_dir: Path, name: str) -> pd.DataFrame:
    path = data_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    return pd.read_csv(path)


# ------------------------------ common utilities ----------------------------

def save_fig(fig: plt.Figure, outbase: Path):
    fig.tight_layout()
    fig.savefig(outbase.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(outbase.with_suffix(".png"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def bw_style(module=None):
    if module is not None and hasattr(module, "apply_bw_style"):
        module.apply_bw_style()
    else:
        plt.rcParams.update({
            "font.size": 11,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "figure.figsize": (8, 5),
        })


# ------------------------------ figure 1 ------------------------------------

def build_benchmark_control_figure(module, outdir: Path):
    """Rebuild the benchmark control figure from the current solver."""
    p = module.Params(
        H_star=67.4,
        omega_m_star=0.315,
        omega_r_star=9.2e-5,
        omega_V_star=1.0 - 0.315 - 9.2e-5,
        beta=0.8,
        mu=1.5,
        kappa=15.0,
        k1=0.0,
        k2=0.0,
        lambda3=0.0,
        lambda4=0.0,
        omega0=15.0,
        A2=None,
        A3=0.0,
        A4=0.0,
        phi0=-0.12,
        closure_mode="benchmark",
        zmax_solver=15.0,
        zplot=15.0,
        z_match=10.0,
        npts=2500,
        n_iter=4,
    )
    df, _ = module.solve_background_selfconsistent(p, seed_mode="ref")
    full, summary, *_ = module.derived_quantities(df, p)
    module.make_figure(full, summary, outdir / "ect_hubble_jwst_background_bw", p)


# ------------------------------ figure 2 ------------------------------------

def build_param_scan_figure(scan_df: pd.DataFrame, pref_df: pd.DataFrame, outdir: Path):
    pivots = {
        "DeltaH0_pct": scan_df.pivot(index="phi0", columns="omega0", values="DeltaH0_pct"),
        "t0_Gyr": scan_df.pivot(index="phi0", columns="omega0", values="t0_Gyr"),
        "tU10_Gyr": scan_df.pivot(index="phi0", columns="omega0", values="tU10_Gyr"),
        "Geff10_over_GN": scan_df.pivot(index="phi0", columns="omega0", values="Geff10_over_GN"),
    }
    labels = {
        "DeltaH0_pct": r"$\Delta H_0/H_0$ [\%]",
        "t0_Gyr": r"$t_0$ [Gyr]",
        "tU10_Gyr": r"$t_U(z=10)$ [Gyr]",
        "Geff10_over_GN": r"$G_{\rm eff}(10)/G_N$",
    }
    point_labels = {
        "balanced": "B",
        "hubble_priority": "H",
        "age_priority": "A",
    }

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.2))
    for ax, key in zip(axes.ravel(), pivots.keys()):
        piv = pivots[key]
        x = piv.columns.to_numpy(dtype=float)
        y = piv.index.to_numpy(dtype=float)
        X, Y = np.meshgrid(x, y)
        pcm = ax.pcolormesh(X, Y, piv.to_numpy(), shading="nearest")
        cbar = fig.colorbar(pcm, ax=ax)
        cbar.set_label(labels[key])
        ax.set_xlabel(r"$\omega_0$")
        ax.set_ylabel(r"$\phi_0$")
        ax.set_title(labels[key])

        # Draw the first useful corridor as dashed rectangle.
        rect = FancyBboxPatch((25 - 2.5, -0.10 - 0.02), 15.0, 0.04,
                              boxstyle="round,pad=0.02", fill=False,
                              linestyle="--", linewidth=1.5)
        ax.add_patch(rect)

        for _, row in pref_df.iterrows():
            role = str(row["role"])
            lab = point_labels.get(role, role[:1].upper())
            ax.plot(row["omega0"], row["phi0"], marker="o", ms=6)
            ax.text(row["omega0"] + 0.6, row["phi0"] + 0.0015, lab, fontsize=10, weight="bold")

    save_fig(fig, outdir / "ect_condensate_param_scan_bw")


# ------------------------------ figure 3 ------------------------------------

def compute_run(module, *, closure_mode: str, omega0: float, phi0: float,
                beta: float = 0.8, mu: float = 1.5, A2: float | None = None,
                A3: float = 0.0, A4: float = 0.0) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p = module.Params(
        H_star=67.4,
        omega_m_star=0.315,
        omega_r_star=9.2e-5,
        omega_V_star=1.0 - 0.315 - 9.2e-5,
        beta=beta,
        mu=mu,
        kappa=15.0,
        k1=0.0,
        k2=0.0,
        lambda3=0.0,
        lambda4=0.0,
        omega0=omega0,
        A2=A2,
        A3=A3,
        A4=A4,
        phi0=phi0,
        closure_mode=closure_mode,
        zmax_solver=15.0,
        zplot=15.0,
        z_match=10.0,
        npts=2500,
        n_iter=4,
    )
    df, _ = module.solve_background_selfconsistent(p, seed_mode="ref")
    full, summary, *_ = module.derived_quantities(df, p)
    growth = module.solve_linear_growth(full, p)
    return full, summary, growth


def build_derived_parent_comparison(module, outdir: Path):
    bench_full, bench_summary, bench_growth = compute_run(module, closure_mode="benchmark", omega0=15.0, phi0=-0.12)
    bal_full, bal_summary, bal_growth = compute_run(module, closure_mode="derived_parent", omega0=25.0, phi0=-0.10)
    hub_full, hub_summary, hub_growth = compute_run(module, closure_mode="derived_parent", omega0=30.0, phi0=-0.10)

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.2))

    # (a) expansion history
    ax = axes[0, 0]
    for full, label, ls in [
        (bench_full, "benchmark", "-"),
        (bal_full, "derived balanced", "--"),
        (hub_full, "derived H-priority", ":"),
    ]:
        ax.plot(full["z"], full["E"], ls=ls, label=label)
    ax.plot(bench_full["z"], bench_full["E_ref"], color="0.3", linestyle="-.", label="reference")
    ax.set_xlim(0, 15)
    ax.set_xlabel("z")
    ax.set_ylabel(r"$E(z)=H/H_*$")
    ax.set_title("(a) Expansion history")
    ax.legend(fontsize=8)

    # (b) effective gravity
    ax = axes[0, 1]
    for full, label, ls in [
        (bench_full, "benchmark", "-"),
        (bal_full, "derived balanced", "--"),
        (hub_full, "derived H-priority", ":"),
    ]:
        geff = np.exp(-0.8 * full["phi"].to_numpy())
        ax.plot(full["z"], geff, ls=ls, label=label)
    ax.axhline(1.0, color="0.3", linestyle="-.")
    ax.set_xlim(0, 15)
    ax.set_xlabel("z")
    ax.set_ylabel(r"$G_{\rm eff}/G_N$")
    ax.set_title("(b) Effective gravity")

    # (c) linear growth
    ax = axes[1, 0]
    for growth, label, ls in [
        (bench_growth, "benchmark", "-"),
        (bal_growth, "derived balanced", "--"),
        (hub_growth, "derived H-priority", ":"),
    ]:
        ax.plot(growth["z"], growth["D_ratio"], ls=ls, label=label)
    ax.axhline(1.0, color="0.3", linestyle="-.")
    ax.set_xlim(0, 15)
    ax.set_xlabel("z")
    ax.set_ylabel(r"$D(z)/D_{\rm ref}(z)$")
    ax.set_title("(c) Solved linear growth")

    # (d) local maturity channels
    ax = axes[1, 1]
    for full, label, ls in [
        (bal_full, "collapse factor (balanced)", "--"),
        (hub_full, "collapse factor (H-priority)", ":"),
    ]:
        phi = full["phi"].to_numpy()
        beta = 0.8
        geff = np.exp(-beta * phi)
        collapse = np.sqrt(geff)
        bh = geff
        ax.plot(full["z"], collapse, ls=ls, label=label)
        ax.plot(full["z"], bh, ls=ls, label=label.replace("collapse", "BH-like"), alpha=0.7)
    ax.axhline(1.0, color="0.3", linestyle="-.")
    ax.set_xlim(0, 15)
    ax.set_xlabel("z")
    ax.set_ylabel("relative acceleration")
    ax.set_title("(d) Local maturity channels")
    ax.legend(fontsize=7)

    save_fig(fig, outdir / "ect_derived_parent_comparison_bw")


# ------------------------------ figure 4 ------------------------------------

def build_conceptual_evolution(outdir: Path):
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Timeline arrows
    ax.annotate("", xy=(0.95, 0.75), xytext=(0.08, 0.75), arrowprops=dict(arrowstyle="->", lw=1.8))
    ax.annotate("", xy=(0.95, 0.28), xytext=(0.08, 0.28), arrowprops=dict(arrowstyle="->", lw=1.8))

    # Epoch separators
    for x in [0.28, 0.58, 0.80]:
        ax.plot([x, x], [0.08, 0.92], linestyle="--", linewidth=1.0, color="0.5")

    # Labels
    ax.text(0.02, 0.80, "Condensate", fontsize=12, weight="bold")
    ax.text(0.02, 0.33, "Universe", fontsize=12, weight="bold")

    ax.text(0.14, 0.86, "pre-Lorentzian /\nordering regime", ha="center")
    ax.text(0.43, 0.86, "early derived-parent\ncosmology", ha="center")
    ax.text(0.69, 0.86, "structure formation /\naccelerated local maturity", ha="center")
    ax.text(0.89, 0.86, "late screened\nbranch", ha="center")

    # Condensate curve
    xs = np.linspace(0.10, 0.92, 400)
    ys = 0.78 - 0.16*np.exp(-((xs-0.2)/0.11)**2) + 0.02*np.sin(7*xs)
    ys += 0.12*(1/(1+np.exp(-(xs-0.72)/0.07)) - 0.5)
    ax.plot(xs, ys, lw=2.0)
    ax.text(0.39, 0.60, r"$\phi<0$, $u/u_\infty=e^{\beta\phi}<1$", ha="center")
    ax.text(0.86, 0.68, r"$\phi\to 0$ screened branch", ha="center")

    # Universe line with annotations
    ax.text(0.18, 0.20, "emergence of\nLorentzian branch", ha="center")
    ax.text(0.45, 0.20, r"$G_{\rm eff}>G_N$", ha="center")
    ax.text(0.67, 0.18, "linear growth alone\nnot sufficient", ha="center")
    ax.text(0.67, 0.08, "BH-assisted / local maturity\nchannels strengthened", ha="center")
    ax.text(0.88, 0.18, "benchmark truncation\nvalid near screened branch", ha="center")

    save_fig(fig, outdir / "ect_universe_condensate_evolution_bw")


# ------------------------------ figure 5 ------------------------------------

def build_jwst_anchor_budget(maturity_df: pd.DataFrame, outdir: Path):
    # Use Hubble-priority point as main visual working point.
    df = maturity_df[maturity_df["point"] == "hubble_priority"].copy()
    order = ["JADES-GS-z14-0", "GN-z11", "mini-quenched z=7.3", "RUBIES-EGS-QG-1"]
    df["object"] = pd.Categorical(df["object"], categories=order, ordered=True)
    df = df.sort_values("object")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))

    # Panel 1: ages at observation
    ax = axes[0]
    x = np.arange(len(df))
    w = 0.36
    ax.bar(x - w/2, df["tU_ref_Gyr"], width=w, label=r"$t_U^{\rm ref}$")
    ax.bar(x + w/2, df["tU_ect_Gyr"], width=w, label=r"$t_U^{\rm ECT}$")
    ax.set_xticks(x)
    ax.set_xticklabels(df["object"], rotation=20, ha="right")
    ax.set_ylabel("Gyr")
    ax.set_title("(a) Age of the Universe at observation")
    ax.legend(fontsize=8)

    # Panel 2: required vs achieved maturity factors
    ax = axes[1]
    ax.bar(x - 0.25, df["required_speedup_tU"], width=0.22, label=r"$\mathcal{R}_{\rm req}$")
    ax.bar(x, df["maturity_ff"], width=0.22, label=r"$\mathcal{R}_{\rm gal}$")
    ax.bar(x + 0.25, df["maturity_bh"], width=0.22, label=r"$\mathcal{R}_{\rm BH}$")
    ax.set_xticks(x)
    ax.set_xticklabels(df["object"], rotation=20, ha="right")
    ax.set_ylabel("factor")
    ax.set_title("(b) Required vs achieved maturity factors")
    ax.legend(fontsize=8)

    save_fig(fig, outdir / "ect_jwst_anchor_budget_bw")


# ------------------------------ main ----------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=".", help="Directory containing CSVs and ect_hubble_jwst_background_v6.py")
    ap.add_argument("--outdir", default="figures", help="Where to save generated figures")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    module = load_solver_module(data_dir)
    bw_style(module)

    scan_df = load_csv(data_dir, "derived_parent_scan_stage1.csv")
    pref_df = load_csv(data_dir, "derived_parent_preferred_points.csv")
    maturity_df = load_csv(data_dir, "jwst_maturity_budget_stage3.csv")

    build_benchmark_control_figure(module, outdir)
    build_param_scan_figure(scan_df, pref_df, outdir)
    build_derived_parent_comparison(module, outdir)
    build_conceptual_evolution(outdir)
    build_jwst_anchor_budget(maturity_df, outdir)

    print("Saved figures:")
    for stem in [
        "ect_hubble_jwst_background_bw",
        "ect_condensate_param_scan_bw",
        "ect_derived_parent_comparison_bw",
        "ect_universe_condensate_evolution_bw",
        "ect_jwst_anchor_budget_bw",
    ]:
        print(f"  - {stem}.pdf")
        print(f"  - {stem}.png")


if __name__ == "__main__":
    main()
