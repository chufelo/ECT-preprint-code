#!/usr/bin/env python3
"""Build the active R153 successors whose line semantics required correction.

This script changes only the visual treatment of already frozen numerical
payloads:

* independent categorical values and sparse diagnostic nodes are markers;
* an exact analytic relation is drawn on a dense grid with frozen nodes on top;
* finite-window counterexample bins are not joined into a fictitious curve.

No smoothing, regression, spline, new physical model, or new numerical value
is introduced.

The scale-inventory and post-ordering figures formerly produced by this
historical script now have later publication owners (R181 and R154,
respectively).  Their predecessor renderers are still initialised because
they establish the frozen Matplotlib style inherited by the active R153
figures, but their superseded canvases are closed without writing: replaying
R153 must not overwrite a later accepted successor or create unregistered
output.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import os
from pathlib import Path
import sys
import types

os.environ.setdefault("SOURCE_DATE_EPOCH", "1784937600")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r153-line-semantics-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/ect-r153-line-semantics-xdg")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np


SCRIPT = Path(__file__).resolve()
LATEX = SCRIPT.parents[2]
ROOT = LATEX.parent
OUT = LATEX / "figures/r153/line_semantics"
FIXED = dt.datetime(2026, 7, 25, tzinfo=dt.timezone.utc)

REMAINING_OWNER = (
    LATEX
    / "provenance/figures/r190/work_preprint/"
    "R149_READER_LAYOUT_CANDIDATE_v1/"
    "remaining_figure_typography/scripts/build_r149_remaining_typography.py"
)
MAIN_B_OWNER = (
    LATEX
    / "provenance/figures/r190/work_preprint/"
    "R149_READER_LAYOUT_CANDIDATE_v1/"
    "borderline_figure_typography/review_main_b/build_successors_b.py"
)
SECOND_HALF_OWNER = (
    LATEX
    / "provenance/figures/r190/work_preprint/"
    "R149_READER_LAYOUT_CANDIDATE_v1/"
    "second_half_typography_successors/build_successors.py"
)
COSMOLOGY_OWNER = LATEX / "scripts/cosmology/make_r103_corrected_cosmology_figures.py"
COSMOLOGY_DATA = LATEX / "data/cosmology_r103"

META = {
    "Title": "ECT R153 line-semantics successor",
    "Author": "ECT reproducibility workflow",
    "Subject": "Presentation correction only; frozen numerical payload",
    "Creator": SCRIPT.name,
    "CreationDate": FIXED,
    "ModDate": FIXED,
}

SCALE_OWNER = (
    LATEX
    / "provenance/figures/r190/work_preprint/"
    "R123_VISUAL_READABILITY_AND_RESTORATION_CANDIDATE_v2/"
    "components/targeted_readability_assets/build_targeted_readability_assets.py"
)
EVOLUTION_OWNER = (
    LATEX
    / "provenance/figures/r190/work_preprint/"
    "R149_READER_LAYOUT_CANDIDATE_v1/"
    "figure_typography_successors/scripts/build_r149_evolution_typography_successors.py"
)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write(fig: plt.Figure, stem: str, *, png: bool = True) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", metadata=META)
    if png:
        fig.savefig(
            OUT / f"{stem}.png",
            dpi=260,
            bbox_inches="tight",
            metadata={"Software": SCRIPT.name},
        )
    plt.close(fig)


def remove_sparse_connectors(fig: plt.Figure, count: int) -> int:
    changed = 0
    for ax in fig.findobj(match=Axes):
        changed_here = 0
        for line in ax.lines:
            if len(np.atleast_1d(line.get_xdata())) != count:
                continue
            marker = line.get_marker()
            if marker in (None, "None", "", " "):
                continue
            if line.get_linestyle() not in (None, "None", "", " "):
                line.set_linestyle("None")
                line.set_linewidth(0.0)
                changed += 1
                changed_here += 1
        if changed_here and ax.get_legend() is not None:
            ax.legend(frameon=False, loc="best")
    return changed


def initialise_superseded_style_owners() -> None:
    """Replay style initialisation without writing superseded figure assets."""

    scale = load(SCALE_OWNER, "r153_scale_owner")

    def discard_scale(fig, _out, _preview, _title):
        plt.close(fig)

    scale.save = discard_scale
    scale.build_scales(Path("unused.pdf"), Path("unused.png"))

    evolution = load(EVOLUTION_OWNER, "r153_evolution_owner")
    evolution.verify_inputs()
    dense = evolution.load_csv(evolution.INPUTS["dense"][0])
    observables = evolution.load_csv(evolution.INPUTS["observables"][0])

    def discard_evolution(fig, stem):
        if stem != "r149_conditional_post_ordering_evolution_typography":
            raise RuntimeError(stem)
        plt.close(fig)

    evolution.save = discard_evolution
    evolution.conditional_post_ordering(dense, observables)


def build_timescale_and_chronology() -> None:
    module = load(REMAINING_OWNER, "r153_remaining_owner")
    original_save = module.save

    def capture(fig, stem, _title, _subject):
        if stem == "fig11_a_timescale_mismatch_typography_r149":
            ax = fig.axes[0]
            curve = next(
                line
                for line in ax.lines
                if len(np.atleast_1d(line.get_xdata())) == 3
                and "tau" in line.get_label()
            )
            h = np.asarray(curve.get_xdata(), dtype=float)
            tau = np.asarray(curve.get_ydata(), dtype=float)
            constant = float(np.median(h * tau))
            dense_h = np.linspace(float(h.min()), float(h.max()), 401)
            colour = curve.get_color()
            label = curve.get_label()
            curve.set_linestyle("None")
            curve.set_label("computed reference nodes")
            ax.plot(
                dense_h,
                constant / dense_h,
                color=colour,
                linestyle="-.",
                linewidth=2.0,
                label=label + " (exact analytic curve)",
            )
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc="center left")
            write(fig, "one_real_pole_exact_curve_r153", png=False)
        elif stem == "r123_conditional_chronology_typography_r149":
            changed = remove_sparse_connectors(fig, 9)
            if changed != 1:
                raise RuntimeError(f"expected one nine-node residual connector, changed {changed}")
            write(fig, "conditional_chronology_nodes_r153", png=False)
        else:
            original_save(fig, stem, _title, _subject)

    module.save = capture
    module.timescale()
    module.chronology()


def build_restricted_proxies() -> None:
    # The frozen owner imports PyMuPDF for unrelated crop helpers.  This
    # successor calls only its Matplotlib renderer, so permit that isolated
    # function to replay in a plotting environment without PyMuPDF.
    if importlib.util.find_spec("fitz") is None:
        fitz_stub = types.ModuleType("fitz")
        fitz_stub.VersionBind = "not-used-by-render_restricted"
        sys.modules["fitz"] = fitz_stub
    module = load(MAIN_B_OWNER, "r153_main_b_owner")

    def capture(fig, path, tight=False):
        if Path(path).name != "r149_restricted_perturbation_proxies.pdf":
            raise RuntimeError(path)
        changed = remove_sparse_connectors(fig, 4)
        if changed != 5:
            raise RuntimeError(f"expected five four-node proxy connectors, changed {changed}")
        write(fig, "restricted_perturbation_nodes_r153", png=False)

    module.save_mpl = capture
    module.render_restricted()


def build_acoustic_scan() -> None:
    module = load(COSMOLOGY_OWNER, "r153_cosmology_owner")
    scan = module.load(COSMOLOGY_DATA / "R103_TWO_SLOPE_CALIBRATED_SCAN_v1.json")

    def capture(fig, _path):
        changed = 0
        for ax in fig.axes:
            for line in ax.lines:
                if len(np.atleast_1d(line.get_xdata())) != 3:
                    continue
                if line.get_linestyle() in (None, "None", "", " "):
                    continue
                line.set_linestyle("None")
                line.set_linewidth(0.0)
                changed += 1
        if changed != 6:
            raise RuntimeError(f"expected six three-node guide segments, changed {changed}")
        for ax in fig.axes:
            for legend in list(ax.findobj(match=matplotlib.legend.Legend)):
                title = legend.get_title()
                if title.get_text() == "line/colour":
                    title.set_text(r"$\kappa_s$ colour")
                for handle, label in zip(legend.get_lines(), [text.get_text() for text in legend.get_texts()]):
                    if r"\kappa_s" in label:
                        handle.set_linestyle("None")
                        handle.set_marker("s")
                        handle.set_markersize(5.5)
        # The source owner used a wide two-column canvas.  At manuscript
        # text width that layout reduced the lower text decile below the
        # release readability floor.  Keep the same nine frozen values but
        # place the two diagnostics on a portrait reader canvas.  This is a
        # presentation-only relayout: axes, values, reference lines, marker
        # encodings and labels are unchanged.
        if len(fig.axes) != 2:
            raise RuntimeError(f"expected two acoustic/PPN panels, got {len(fig.axes)}")
        fig.set_size_inches(7.2, 8.7, forward=True)
        positions = (
            [0.14, 0.57, 0.82, 0.36],
            [0.14, 0.09, 0.82, 0.36],
        )
        for ax, pos in zip(fig.axes, positions):
            ax.set_position(pos)
            # Keep even mathtext subscripts above the 7 pt effective
            # manuscript floor after the height-constrained TeX insertion.
            ax.tick_params(axis="both", which="major", labelsize=11.5)
            ax.tick_params(axis="both", which="minor", labelsize=11.5)
            ax.xaxis.label.set_size(12.5)
            ax.yaxis.label.set_size(12.5)
            ax.title.set_size(15.0)
            for legend in ax.findobj(match=matplotlib.legend.Legend):
                plt.setp(legend.get_texts(), fontsize=11.5)
                legend.get_title().set_fontsize(12.0)
        write(fig, "acoustic_ppn_nodes_r153", png=False)

    module.finish = capture
    module.tradeoff_figure(scan, Path("unused"))


def build_m1_counterexamples() -> None:
    module = load(SECOND_HALF_OWNER, "r153_second_half_owner")

    def capture(fig, stem, _title):
        if stem != "fig47_b_counterexamples_r149":
            raise RuntimeError(stem)
        changed = 0
        for ax in fig.axes:
            for line in ax.lines:
                if line.get_label() == "input temperature":
                    continue
                if len(np.atleast_1d(line.get_xdata())) > 1:
                    line.set_linestyle("None")
                    line.set_linewidth(0.0)
                    changed += 1
        if changed != 3:
            raise RuntimeError(f"expected three finite-window connectors, changed {changed}")
        for ax in fig.axes:
            if ax.get_legend() is not None:
                ax.legend(loc="lower left", ncol=2, fontsize=9.0)
        write(fig, "m1_counterexample_bins_r153", png=False)

    module.save = capture
    module.m1()


def main() -> None:
    initialise_superseded_style_owners()
    build_timescale_and_chronology()
    build_acoustic_scan()
    build_restricted_proxies()
    build_m1_counterexamples()
    print(f"Wrote R153 line-semantics successors to {OUT}")


if __name__ == "__main__":
    main()
