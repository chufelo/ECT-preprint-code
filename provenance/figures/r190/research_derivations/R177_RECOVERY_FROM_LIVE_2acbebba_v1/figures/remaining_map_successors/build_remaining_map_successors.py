#!/usr/bin/env python3
"""Build four preservation-first R177 map successors.

This producer is candidate-only.  It reads three frozen compact Graphviz maps
and the frozen R149 architecture owner, guards their hashes, preserves every
old semantic node, and applies a small explicit semantic delta.  Unsupported
arrows are retained only as dashed/dotted Open dependencies.  New nodes expose
owners that the older maps compressed away (P3/P4 separation, action-valued
normalisations, vector/axial/mediator separation, and the incomplete YM gap
bridge).

The live TeX tree is never written by this script.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

os.environ.setdefault("SOURCE_DATE_EPOCH", "1785283200")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ect-r177-remaining-maps-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/ect-r177-remaining-maps-xdg")

import fitz
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import PIL
from PIL import Image


SCHEMA = "ect.r177.remaining_complete_map_successors.v1"
FIXED_UTC = "2026-07-29T00:00:00Z"
FIXED_DATE = dt.datetime(2026, 7, 29, tzinfo=dt.timezone.utc)
SOURCE_DATE_EPOCH = "1785283200"

SCRIPT = Path(__file__).resolve()
PACKAGE = SCRIPT.parent
WORKSPACE = next(
    parent for parent in SCRIPT.parents
    if (parent / "LaTex/ECT_preprint.tex").is_file()
)
LATEX = WORKSPACE / "LaTex"

UPSTREAM_ARCH = LATEX / (
    "work/preprint/R149_READER_LAYOUT_CANDIDATE_v1/"
    "remaining_figure_typography/scripts/build_r149_remaining_typography.py"
)
UPSTREAMS = {
    "architecture": (
        UPSTREAM_ARCH,
        "13dbcc2c9d950c339f048217df41f43447ac5591cb2040c2d9b4f05c0d2f89dc",
    ),
    "partIII": (
        LATEX / (
            "figures/source/graphviz/r150_curved_compact_v1/"
            "maps_curved_compact/partIII/partIII_curved_compact_r150.gv"
        ),
        "dfa73c035ee1e53935da435b7aab0dbb8b2f2c2ce46309f94715556f9d92b5ab",
    ),
    "partIV": (
        LATEX / (
            "figures/source/graphviz/r150_curved_compact_v1/"
            "maps_curved_compact/partIV/partIV_curved_compact_r150.gv"
        ),
        "556de0fb88d9037039bc50342d26b453fb1e1c09b476312baf6ee6c823d726ed",
    ),
    "whole": (
        LATEX / (
            "figures/source/graphviz/r168_connected_map_semantics_v1/"
            "generated/r153_profile/whole/whole_curved_compact_r168.gv"
        ),
        "0902001ec6d9fc2c5ea9f3099f36bb21a3ea69c3ff38705f38f5645a3abf5e30",
    ),
}

MASTER_CORRECTED = LATEX / (
    "work/preprint/R177_MASTER_CORRECTION_2acbebba_v1/rehearsal/"
    "LaTex/ECT_preprint.tex"
)
MASTER_SHA256 = "d2bcb1609486133b7b85f1c108e64fc623864f0825ae795ff88cac43acbe910b"

A4 = fitz.paper_rect("a4")
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#D55E00"
AMBER = "#A66E00"
BLACK = "#222222"
GREY = "#666666"
LIGHT = "#E8E8E8"
PALE_BLUE = "#DCECF7"
PALE_GREEN = "#DDF2E9"
PALE_AMBER = "#FBE9C9"
PALE_RED = "#F5DDD7"
WHITE = "#FFFFFF"

CVD = {
    "protan": np.array(
        [[0.152286, 1.052583, -0.204868],
         [0.114503, 0.786281, 0.099216],
         [-0.003882, -0.048116, 1.051998]], dtype=np.float32
    ),
    "deutan": np.array(
        [[0.367322, 0.860646, -0.227968],
         [0.280085, 0.672501, 0.047413],
         [-0.011820, 0.042940, 0.968881]], dtype=np.float32
    ),
    "tritan": np.array(
        [[1.255528, -0.076749, -0.178779],
         [-0.078411, 0.930809, 0.147602],
         [0.004733, 0.691367, 0.303900]], dtype=np.float32
    ),
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


def run(argv: list[str], *, stdout_path: Path | None = None) -> str:
    env = os.environ.copy()
    env.update({
        "LC_ALL": "C",
        "TZ": "UTC",
        "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
        "FORCE_SOURCE_DATE": "1",
    })
    if stdout_path is None:
        completed = subprocess.run(
            argv, check=True, capture_output=True, text=True, env=env
        )
        return (completed.stdout + completed.stderr).strip()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("wb") as handle:
        subprocess.run(argv, check=True, stdout=handle, env=env)
    return ""


def verify_inputs() -> dict[str, Any]:
    owners: dict[str, Any] = {}
    for key, (path, expected) in UPSTREAMS.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"frozen upstream drift for {key}: {path}\n"
                f"expected {expected}\nactual   {actual}"
            )
        owners[key] = {"path": str(path.relative_to(WORKSPACE)), "sha256": actual}
    for key, path, expected in (
        ("corrected_master_status_owner", MASTER_CORRECTED, MASTER_SHA256),
    ):
        if not path.is_file():
            raise RuntimeError(f"missing semantic owner: {path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"semantic owner drift for {key}: {actual}")
        owners[key] = {"path": str(path.relative_to(WORKSPACE)), "sha256": actual}
    return owners


PARTIII_LABELS = {
    "inputs": "Part I inputs\n[B/O]",
    "phase": "BR1 phase\n[B/O]",
    "S0EFT": "iota_0 dimless\n[A/O]",
    "T1MODEL": "T1 owners Open\n[B/O]",
    "T1MIN": "T1 minimum\n[A/B]",
    "S0BAL": "iota_bal dimless\n[B/O]",
    "MBAL": "carrier owners\n[MISSING]",
    "S0": "Sigma x I action\n[B/O]",
    "S0_match": "S0=hbar calib.\n[B/O]",
    "RP": "Gaussian OS-II\n[A/B]",
    "exchange": "Exchange topology\n[A/O]",
    "lorentz_cliff": "Lorentz/Clifford\n[A/O]",
    "decoh": "Record Phi_ab\n[B/O]",
    "crooks": "Crooks + F/R\n[O]",
    "pes": "PES-R organisation\n[B/O]",
    "amp_prob": "Amplitude algebra\n[A/B]",
    "born": "Admitted measure\n[B/O]",
    "entangle": "Correlations\n[A/O]",
    "analogue": "Source-model\nmechanisms [C];\nECT map Open [O]",
    "bell_toy": "CHSH MD toy\n[C/O]",
    "bell_full": "Bell correlators\n[O]",
    "born_full": "Full Born rule\n[O]",
    "measurement": "Outcome/update\n[O]",
    "S0_calc": "Action-owner audit\n[O]",
    "two_level_ontology": "Outcome ontology\n[O]",
    "gie": "Gravity vertex\n[MISSING]",
    "charge_quant": "Winding; charge Open\n[A/O]",
}

PARTIII_NODE_ATTRS = {
    "analogue": {
        "color": f'"{AMBER}"',
        "fillcolor": f'"{PALE_AMBER}"',
        "style": '"rounded,filled,dashed"',
    },
}

PARTIII_NEW_NODES = {
    "SIGTH": {
        "label": "Sigma_theta [hbar]\n[B/O]",
        "fill": PALE_GREEN,
        "border": "#007A59",
        "style": "rounded,filled,dashed",
    },
    "SIGVART": {
        "label": "Sigma_vartheta [hbar]\n[B/O]",
        "fill": PALE_GREEN,
        "border": "#007A59",
        "style": "rounded,filled,dashed",
    },
}

PARTIII_EDGE_STYLES = {
    ("S0", "HJ"): "dashed",
    ("S0", "pes"): "dashed",
    ("S0", "wave_kin"): "dashed",
    ("phase", "exchange"): "dashed",
    ("exchange", "entangle"): "dashed",
    ("exchange", "lorentz_cliff"): "dashed",
    ("unitarity", "decoh"): "dashed",
    ("unitarity", "entangle"): "dashed",
    ("phase", "analogue"): "dashed",
    ("unified_vac", "analogue"): "dashed",
    ("decoh", "analogue"): "dashed",
    ("decoh", "bh_shell"): "dashed",
    ("decoh", "no_info_loss"): "dashed",
}

PARTIV_LABELS = {
    "forward_inputs": "Structural inputs\n[P/O]",
    "obs_algebra": "Rep. condition\n[A/B]",
    "obs_condensate": "Singlet counterex.\n[A]",
    "P7": "P7 input\n[P]",
    "min_eft": "Leading colour EFT\n[B/O]",
    "anomaly_restatement": "Matter anomaly tests\n[B/O]",
    "no_gluon_mass": "No Proca term\n[A/B]",
    "no_higgs_colour": "No colour Higgs\n[B/O]",
    "no_oscillator": "Unmapped osc. !=\ncolour gap [B/O]",
    "y_alpha": "Wilson coeffs independent\n[A/O]",
    "lambda_col": "Standard b0=11\n[A/B]",
    "triviality": "Constant matching\n[A/B]",
    "three_scale": "Scale inputs separate\n[B/O]",
    "anomaly_su33": "A(8)=0; A(6)=7\n[A]",
    "anomaly_mixed": "Mixed anomalies\n[A/B]",
    "witten_ga": "Witten supplied test\n[A/B]",
    "thooft_match": "t Hooft owner\n[O]",
    "sm_candidate": "SM-like test\n[B/O]",
    "strong_cp": "theta_gauge:\nallowed, not forced\n[B/O]",
    "coverage": "Coverage ledger\n[B/O]",
    "three_way": "HKLoc incomplete\n[B/O]",
    "proton": "Proton patterns\n[C/O]",
    "bridging": "Physical gap bridge\n[N/I]",
    "openlist": "Action/matter/gap Open\n[O]",
}

PARTIV_NODE_ATTRS = {
    "proton": {
        "color": f'"{AMBER}"',
        "fillcolor": f'"{PALE_AMBER}"',
        "style": '"rounded,filled,dashed"',
    },
}

PARTIV_NEW_NODES = {
    "health": {
        "label": "Z>0 and Z-Y/2>0\n[A/B]",
        "fill": PALE_BLUE,
        "border": BLUE,
        "style": "rounded,filled",
    },
}

PARTIV_EDGE_STYLES = {
    ("P7", "min_eft"): "dashed",
    ("P7", "anomaly_restatement"): "dashed",
    ("obs_algebra", "P7"): "dashed",
    ("obs_condensate", "P7"): "dashed",
    ("min_eft", "no_oscillator"): "dashed",
    ("min_eft", "y_alpha"): "dashed",
    ("y_alpha", "coverage"): "dashed",
    ("y_alpha", "triviality"): "dashed",
    ("three_way", "openlist"): "dashed",
    ("no_oscillator", "three_way"): "dashed",
    ("anomaly_restatement", "proton"): "dashed",
    ("proton", "openlist"): "dashed",
    ("coverage", "bridging"): "dashed",
}

WHOLE_LABELS = {
    "P3": "P3 scalar\n[P]",
    "P4": "P4 datum\n[P]",
    "PC": "P7 colour\n[P/O]",
    "SSB": "O(3)\nP4 Open\n[A/O]",
    "LOR": "Scalar EFT\nsignature\n[A/B/O]",
    "COLOUR": "SU(3)\nstructure\n[B/O]",
    "S0EFT": "dimless iota_0\n[A/O]",
    "T1MODEL": "T1 owners\nOpen [B/O]",
    "T1MIN": "T1 min\n[A/B]",
    "S0BAL": "dimless iota_bal\n[B/O]",
    "MBAL": "carrier owners\n[MISSING]",
    "S0": "Sigma x I\naction [B/O]",
    "S0HBAR": "S0=hbar\ncalib. [B/O]",
    "TOPO": "Exchange\ntopology [A/O]",
    "BORN": "Admitted\nmeasure [B/O]",
    "PES_DYN": "PES-R\nadmissibility [B/O]",
    "PES_PERSIST": "PES-R\nretention [B/O]",
    "FIFTH": "Vector\nd=3 [B/O]",
    "CPT": "Energy/CPT\n[B/O]",
    "FERMIONS": "Weighted\nCAR [A/O]",
    "ANOM": "Anomaly\ntests [A/B/O]",
    "OPEN": "Open\nowners [O]",
}

WHOLE_NEW_NODES = {
    "P3RAD": {
        "label": "P3 radial\n[A/P3]",
        "fill": PALE_BLUE,
        "border": BLUE,
        "style": "rounded,filled",
    },
    "P4POLE": {
        "label": "P4 pole\n[O]",
        "fill": PALE_AMBER,
        "border": AMBER,
        "style": "rounded,filled,dashed",
    },
    "SIGTH": {
        "label": "Sigma_th [hbar]\n[B/O]",
        "fill": PALE_GREEN,
        "border": "#007A59",
        "style": "rounded,filled,dashed",
    },
    "SIGVART": {
        "label": "Sigma_vth [hbar]\n[B/O]",
        "fill": PALE_GREEN,
        "border": "#007A59",
        "style": "rounded,filled,dashed",
    },
    "AXIAL": {
        "label": "Axial\nspin [O]",
        "fill": PALE_AMBER,
        "border": AMBER,
        "style": "rounded,filled,dashed",
    },
    "MEDIATOR": {
        "label": "Mediator\nforce/WEP [O]",
        "fill": PALE_AMBER,
        "border": AMBER,
        "style": "rounded,filled,dashed",
    },
    "YM": {
        "label": "YM local\nHKLoc [A/B/O]",
        "fill": PALE_GREEN,
        "border": "#007A59",
        "style": "rounded,filled,dashed",
    },
}

WHOLE_EDGE_STYLES = {
    ("PHI", "PC"): "dashed",
    ("SSB", "LOR"): "dashed",
    ("LOR", "MBRANCH"): "dashed",
    ("LOR", "QBRANCH"): "dashed",
    ("LOR", "CC"): "dashed",
    ("TOPO", "FERMIONS"): "dashed",
    ("CPT", "ANOM"): "dashed",
    ("EW", "CPT"): "dashed",
    ("EW", "ANOM"): "dashed",
    ("FERMIONS", "CPT"): "dashed",
    ("FERMIONS", "FLAVOUR"): "dashed",
    ("FERMIONS", "UNIFICATION"): "dashed",
}


EXPANDED_SEMANTICS: dict[str, dict[str, str]] = {
    "partIII": {
        "S0EFT": (
            "The fixed-core reduced coefficient iota_0 is dimensionless in the "
            "printed natural-unit normalisation. It is not an action and cannot equal hbar."
        ),
        "T1MODEL": (
            "The supplied T1 truncation provides conditional mathematics only; its "
            "carrier, profile, stability, quotient and physical action owner remain Open."
        ),
        "T1MIN": "The T1 length minimum is Level-A mathematics only inside the supplied truncation.",
        "S0BAL": "The balanced reduced iota coefficient is dimensionless, not an action unit.",
        "SIGTH": (
            "Sigma_theta is an independent action-valued normalisation with dimension [hbar]. "
            "The phase physical action is S_theta^phys = Sigma_theta I_theta."
        ),
        "SIGVART": (
            "Sigma_vartheta is a separate independent action-valued normalisation with "
            "dimension [hbar]. The modulus physical action is "
            "S_vartheta^phys = Sigma_vartheta I_n^(vartheta)."
        ),
        "S0": (
            "Only products Sigma_theta times a dimensionless phase functional or "
            "Sigma_vartheta times a dimensionless modulus functional can be compared "
            "with an operational action scale."
        ),
        "S0_match": "S0 = hbar is a Level-B/Open calibration, not a loop derivation.",
        "RP": "The exact result is scoped to the supplied free-Gaussian OS-II package.",
        "born": "A probability measure is admitted under declared hypotheses; it is not derived by decoherence or PES-R.",
        "pes": "PES-R is a Level-B/Open calculational organisation, not a Born-rule or outcome theorem.",
        "analogue": (
            "External analogue/source-model mechanisms test those named source models. "
            "Structural similarity is not evidence for ECT, and generic mismatch is not an ECT falsifier. "
            "An ECT-specific comparison requires a named ECT action, state/preparation, operator, "
            "observable map, uncertainty model and discriminator."
        ),
    },
    "partIV": {
        "obs_condensate": (
            "A nontrivial irreducible representation has no invariant vector, but a "
            "reducible representation containing a trivial singlet supplies a counterexample "
            "to the old universal condensate no-go. A fundamental 3 VEV has SU(2) stabiliser "
            "only under that stated representation."
        ),
        "P7": "P7 is a reverse-engineered structural postulate/input, not a forward derivation.",
        "min_eft": (
            "The displayed colour action is one declared leading truncation after a supplied "
            "bundle, connection, field content and power counting. It is not a complete or minimal physical basis."
        ),
        "health": (
            "For the declared constant-background quadratic ansatz, necessary transverse "
            "health conditions are Z>0 and Z-Y/2>0. They are not sufficient for a generic background."
        ),
        "y_alpha": (
            "Wilson coefficients in different sectors are independent. A Y-to-alpha_ECT "
            "identification requires a common action and explicit matching and remains Open."
        ),
        "lambda_col": (
            "b0=11 running and dimensional transmutation are standard supplied pure-SU(3) "
            "mathematics, not an ECT prediction."
        ),
        "anomaly_su33": (
            "In the declared convention A(8)=0 and A(6)=7, so an adjoint plus one sextet is anomalous."
        ),
        "no_oscillator": (
            "An oscillator tower is not universally excluded from a gauge-invariant physical spectrum. "
            "Only an internal tower for which no gauge-invariant operator/state/spectral map has been "
            "supplied cannot be identified with the established QCD/glueball gap."
        ),
        "strong_cp": (
            "The gauge topological term g_s^2 theta_gauge F^a_{mu nu} Ftilde^{a mu nu}/(32 pi^2) "
            "is allowed by the truncation but is not forced. The physical bar-theta also contains "
            "the quark-mass phase arg det M_q, with the relative sign fixed by convention."
        ),
        "three_way": (
            "HKLoc/polymer material is an incomplete attempted entry criterion. Local heat-kernel "
            "lemmas do not establish the physical four-dimensional mass gap."
        ),
        "proton": (
            "Colour triality supplies only a colour-singlet constraint. It does not derive a global "
            "U(1)_B, a conserved baryon current, the absence or presence of a baryon-violating vertex, "
            "or a proton-decay selection rule. All three proton-stability patterns remain Level C/Open."
        ),
        "openlist": "P7 does not derive the colour connection, physical action, matter content, confinement or mass gap.",
    },
    "whole": {
        "P3RAD": "m_Phi,rad^2=2 mu^2 is a Level-A result inside the homogeneous P3 potential only.",
        "P4POLE": (
            "A P4 pole requires a stationary P4 action/state and constrained Hessian. "
            "m_P4,pole = m_Phi,rad is not an identity and any matching remains Open."
        ),
        "LOR": (
            "The scalar kinetic EFT K=beta delta-alpha nn is supplied separately from the P4 datum. "
            "Its signature criterion is beta(beta-alpha)<0; alpha>beta is only the beta>0 branch."
        ),
        "SIGTH": "Sigma_theta is an independent action-valued phase normalisation [hbar].",
        "SIGVART": "Sigma_vartheta is an independent action-valued modulus normalisation [hbar].",
        "MBAL": "The carrier/action identification needed to turn a reduced modulus functional into a physical sector remains missing.",
        "S0": "Physical actions are products of the appropriate Sigma with a dimensionless reduced functional.",
        "S0HBAR": "S0=hbar is calibration-only (Level B/Open), not a loop derivation.",
        "FIFTH": (
            "The dimension-three vector current a_mu^(V) j^mu needs a dimension-one coefficient "
            "and a separately defined relative energy/CPT observable."
        ),
        "AXIAL": "Spin/precession requires an independent axial or Pauli operator; no vector-to-axial derivation exists.",
        "MEDIATOR": (
            "Force/WEP phenomenology requires an independent dynamical mediator/profile, source/body "
            "charges, propagator, range and screening; no vector-to-force derivation exists."
        ),
        "YM": (
            "The b0=11 running algebra and local heat-kernel identities are retained, while "
            "HKLoc/polymer closure and the physical ECT Yang-Mills mass gap remain Open."
        ),
        "COLOUR": "P7 supplies at most a structural SU(3) programme; action, matter and physical gap owners remain Open.",
        "FERMIONS": "Weighted-CAR normalisation is a conditional lemma; the physical fermion carrier and spin link remain Open.",
    },
}


EXPANDED_EDGE_SEMANTICS: dict[str, list[dict[str, str]]] = {
    "partIII": [
        {"edge": "S0EFT -> S0", "meaning": "dashed Open owner map; requires Sigma_theta"},
        {"edge": "SIGTH -> S0", "meaning": "phase physical-action product"},
        {"edge": "S0BAL -> S0", "meaning": "dashed Open physical matching"},
        {"edge": "SIGVART -> S0", "meaning": "modulus physical-action product"},
        {"edge": "SIGTH <-> SIGVART", "meaning": "dotted Open compatibility, never an identity"},
        {"edge": "phase -> analogue", "meaning": "dashed: external source-model similarity; ECT map Open"},
        {"edge": "unified_vac -> analogue", "meaning": "dashed: common-vacuum source-model route, not ECT evidence"},
        {"edge": "decoh -> analogue", "meaning": "dashed: analogy route requires named ECT operator/observable discriminator"},
    ],
    "partIV": [
        {"edge": "P7 -> min_eft", "meaning": "dashed: supplied connection/action assumptions required"},
        {"edge": "min_eft -> health", "meaning": "exact algebra inside the declared quadratic ansatz"},
        {"edge": "min_eft -> no_oscillator", "meaning": "dashed scoped diagnostic: absent physical spectral map, not a universal no-oscillator theorem"},
        {"edge": "no_oscillator -> three_way", "meaning": "dashed: an unmapped internal tower does not establish the colour gap"},
        {"edge": "min_eft -> y_alpha", "meaning": "dashed non-transfer diagnostic, not coefficient inheritance"},
        {"edge": "three_way -> openlist", "meaning": "HKLoc remains incomplete; physical gap Open"},
        {"edge": "anomaly_restatement -> proton", "meaning": "dashed: triality/singlet constraint does not derive baryon protection"},
        {"edge": "proton -> openlist", "meaning": "dashed: three proton-stability patterns remain Level C/Open"},
    ],
    "whole": [
        {"edge": "P3 -> P3RAD", "meaning": "P3-only radial result"},
        {"edge": "P4 -> P4POLE", "meaning": "dashed Open P4 owner requirement; no P3RAD edge"},
        {"edge": "SIGTH <-> SIGVART", "meaning": "dotted Open Sigma_theta/Sigma_vartheta compatibility"},
        {"edge": "FIFTH -> CPT", "meaning": "dashed vector-energy/CPT observable route only"},
        {"edge": "QBRANCH -> AXIAL", "meaning": "independent axial completion"},
        {"edge": "MBRANCH -> MEDIATOR", "meaning": "independent mediator completion"},
        {"edge": "COLOUR -> YM", "meaning": "supplied YM/local-mathematics route; physical gap Open"},
    ],
}


FORBIDDEN_DISPLAY_TOKENS = {
    "partIII": [
        "Balanced action unit", "Fixed-core candidate", "Action-unit slot",
        "Analogue lab",
    ],
    "partIV": [
        "Condensate no-go", "Minimal colour EFT", "P7 anomaly map", "Triviality result",
        "Oscillator != gap", "Theta allowed, not forced", "Proton stability",
    ],
    "whole": ["Balanced action unit", "Fixed-core candidate", "Fifth-force route"],
}


def replace_node_label(text: str, node: str, new_label: str) -> str:
    pattern = re.compile(
        rf"(?ms)^(\s*{re.escape(node)}\s*\[)(.*?)(\];)$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"node {node}: expected one definition, found {len(matches)}")
    attrs = matches[0].group(2)
    updated, count = re.subn(r'label=".*?"', f'label="{new_label}"', attrs, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"node {node}: label not found")
    return text[:matches[0].start()] + matches[0].group(1) + updated + matches[0].group(3) + text[matches[0].end():]


def set_node_attributes(text: str, node: str, updates: dict[str, str]) -> str:
    pattern = re.compile(rf"(?ms)^(\s*{re.escape(node)}\s*\[)(.*?)(\];)$")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"node {node}: expected one definition, found {len(matches)}")
    attrs = matches[0].group(2)
    for attribute, value in updates.items():
        attribute_pattern = re.compile(
            rf"(?m)^(\s*{re.escape(attribute)}=)(?:\"[^\"]*\"|[^,\n]+)"
        )
        if attribute_pattern.search(attrs):
            attrs, count = attribute_pattern.subn(rf"\g<1>{value}", attrs, count=1)
            if count != 1:
                raise RuntimeError(f"node {node}: failed to update {attribute}")
        else:
            attrs = f"{attribute}={value},\n" + attrs
    return (
        text[:matches[0].start()] + matches[0].group(1) + attrs
        + matches[0].group(3) + text[matches[0].end():]
    )


def edge_pattern(tail: str, head: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?ms)^(\s*{re.escape(tail)}\s*->\s*{re.escape(head)}\s*\[)(.*?)(\];)$"
    )


def set_edge_style(text: str, tail: str, head: str, style: str) -> str:
    pattern = edge_pattern(tail, head)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"edge {tail}->{head}: expected one, found {len(matches)}")
    attrs = matches[0].group(2)
    if re.search(r"(?m)^\s*style=", attrs):
        attrs, count = re.subn(r"(?m)^(\s*style=)[^,\n]+", rf"\g<1>{style}", attrs, count=1)
    else:
        attrs = f"style={style},\n" + attrs
        count = 1
    if count != 1:
        raise RuntimeError(f"edge {tail}->{head}: style update failed")
    return text[:matches[0].start()] + matches[0].group(1) + attrs + matches[0].group(3) + text[matches[0].end():]


def replace_edge_direction(text: str, old: tuple[str, str], new: tuple[str, str]) -> str:
    pattern = edge_pattern(*old)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"edge {old}: expected one, found {len(matches)}")
    prefix = re.sub(
        rf"{re.escape(old[0])}\s*->\s*{re.escape(old[1])}",
        f"{new[0]} -> {new[1]}", matches[0].group(1), count=1,
    )
    return text[:matches[0].start()] + prefix + matches[0].group(2) + matches[0].group(3) + text[matches[0].end():]


def node_definition(node: str, spec: dict[str, str]) -> str:
    return (
        f'\t{node}\t[color="{spec["border"]}",\n'
        f'\t\tfillcolor="{spec["fill"]}",\n'
        '\t\tfixedsize=false,\n'
        '\t\tfontcolor="#262626",\n'
        '\t\tfontname="Arial Narrow",\n'
        '\t\tfontsize=17.5,\n'
        '\t\theight=0.84,\n'
        f'\t\tlabel="{spec["label"]}",\n'
        '\t\tmargin="0.04,0.03",\n'
        '\t\tpenwidth=1.35,\n'
        '\t\tshape=box,\n'
        f'\t\tstyle="{spec["style"]}",\n'
        '\t\twidth=1.06];\n'
    )


def edge_definition(tail: str, head: str, style: str = "dashed", *,
                    both: bool = False, constraint: bool = True) -> str:
    extra = ",\n\t\tdir=both" if both else ""
    if not constraint:
        extra += ",\n\t\tconstraint=false"
    return (
        f"\t{tail} -> {head}\t[arrowsize=0.72,\n"
        '\t\tcolor="#222222",\n'
        '\t\tpenwidth=0.92,\n'
        f"\t\tstyle={style}{extra}];\n"
    )


def insert_before_first_edge(text: str, marker: str, payload: str) -> str:
    count = text.count(marker)
    if count != 1:
        raise RuntimeError(f"edge insertion marker {marker!r}: found {count}")
    return text.replace(marker, payload + marker, 1)


def build_graph_source(key: str, output: Path) -> dict[str, Any]:
    source = UPSTREAMS[key][0]
    text = source.read_text(encoding="utf-8")
    if key == "partIII":
        labels, nodes, styles = PARTIII_LABELS, PARTIII_NEW_NODES, PARTIII_EDGE_STYLES
        for node, label in labels.items():
            text = replace_node_label(text, node, label)
        for node, updates in PARTIII_NODE_ATTRS.items():
            text = set_node_attributes(text, node, updates)
        for edge, style in styles.items():
            text = set_edge_style(text, *edge, style)
        additions = "".join(node_definition(node, spec) for node, spec in nodes.items())
        additions += "\t{ rank=same; MBAL; SIGTH; SIGVART; }\n"
        additions += edge_definition("S0BAL", "S0")
        additions += edge_definition("SIGTH", "S0")
        additions += edge_definition("SIGVART", "S0")
        additions += edge_definition("SIGTH", "SIGVART", "dotted", both=True, constraint=False)
        text = insert_before_first_edge(text, "\n\tinputs -> phase", "\n" + additions)
    elif key == "partIV":
        labels, nodes, styles = PARTIV_LABELS, PARTIV_NEW_NODES, PARTIV_EDGE_STYLES
        for node, label in labels.items():
            text = replace_node_label(text, node, label)
        for node, updates in PARTIV_NODE_ATTRS.items():
            text = set_node_attributes(text, node, updates)
        for edge, style in styles.items():
            text = set_edge_style(text, *edge, style)
        additions = "".join(node_definition(node, spec) for node, spec in nodes.items())
        additions += "\t{ rank=same; y_alpha; lambda_col; health; }\n"
        additions += edge_definition("min_eft", "health", "solid")
        additions += edge_definition("health", "coverage", "dashed")
        text = insert_before_first_edge(text, "\n\tforward_inputs -> methodology", "\n" + additions)
    elif key == "whole":
        labels, nodes, styles = WHOLE_LABELS, WHOLE_NEW_NODES, WHOLE_EDGE_STYLES
        for node, label in labels.items():
            text = replace_node_label(text, node, label)
        for edge, style in styles.items():
            text = set_edge_style(text, *edge, style)
        for old, new in (
            ("nodesep=0.22", "nodesep=0.08"),
            ("ranksep=0.31", "ranksep=0.22"),
            ("ratio=1.25", "ratio=compress"),
        ):
            if text.count(old) != 1:
                raise RuntimeError(f"whole-map layout anchor {old!r} is not unique")
            text = text.replace(old, new, 1)
        additions = "".join(node_definition(node, spec) for node, spec in nodes.items())
        additions += edge_definition("P3", "P3RAD", "solid")
        additions += edge_definition("P3RAD", "OPEN", "dashed", constraint=False)
        additions += edge_definition("P4", "P4POLE", "dashed")
        additions += edge_definition("P4POLE", "OPEN", "dashed", constraint=False)
        additions += edge_definition("QBRANCH", "SIGTH", "dashed")
        additions += edge_definition("SIGTH", "S0", "dashed")
        additions += edge_definition("SIGVART", "S0", "dashed")
        additions += edge_definition("SIGTH", "SIGVART", "dotted", both=True, constraint=False)
        additions += edge_definition("QBRANCH", "AXIAL", "dashed")
        additions += edge_definition("MBRANCH", "MEDIATOR", "dashed")
        additions += edge_definition("AXIAL", "OPEN", "dashed", constraint=False)
        additions += edge_definition("MEDIATOR", "OPEN", "dashed", constraint=False)
        additions += edge_definition("COLOUR", "YM", "dashed")
        additions += edge_definition("YM", "OPEN", "dashed", constraint=False)
        text = insert_before_first_edge(text, "\n\tPHI -> P2", "\n" + additions)
    else:
        raise ValueError(key)
    write_text(output, text)
    return {
        "path": str(output),
        "sha256": sha256(output),
        "bytes": output.stat().st_size,
    }


def graph_counts(layout: dict[str, Any]) -> tuple[int, int]:
    nodes = graph_node_labels(layout)
    edges = [edge for edge in layout.get("edges", []) if "invis" not in str(edge.get("style", ""))]
    return len(nodes), len(edges)


def graph_node_labels(layout: dict[str, Any]) -> dict[str, str]:
    return {
        str(item["name"]): str(item.get("label", ""))
        for item in layout.get("objects", [])
        if "name" in item
        and re.search(r"\[[^\]]+\]", str(item.get("label", "")))
    }


def graph_edges(layout: dict[str, Any]) -> list[dict[str, Any]]:
    names = {
        int(item["_gvid"]): str(item.get("name", ""))
        for item in layout.get("objects", []) if "_gvid" in item
    }
    rows: list[dict[str, Any]] = []
    for edge in layout.get("edges", []):
        if "invis" in str(edge.get("style", "")):
            continue
        rows.append({
            "tail": names[int(edge["tail"])],
            "head": names[int(edge["head"])],
            "style": str(edge.get("style", "solid")),
            "dir": str(edge.get("dir", "forward")),
        })
    return sorted(rows, key=lambda row: (row["tail"], row["head"], row["style"], row["dir"]))


def node_overlaps(layout: dict[str, Any]) -> list[list[str]]:
    boxes: list[tuple[str, float, float, float, float]] = []
    for item in layout.get("objects", []):
        if not all(field in item for field in ("name", "pos", "width", "height")):
            continue
        x, y = (float(value) for value in str(item["pos"]).split(",")[:2])
        half_width = float(item["width"]) * 36.0
        half_height = float(item["height"]) * 36.0
        boxes.append((str(item["name"]), x-half_width, y-half_height, x+half_width, y+half_height))
    overlaps: list[list[str]] = []
    for index, left in enumerate(boxes):
        for right in boxes[index+1:]:
            if (
                min(left[3], right[3]) - max(left[1], right[1]) > 0.5
                and min(left[4], right[4]) - max(left[2], right[2]) > 0.5
            ):
                overlaps.append([left[0], right[0]])
    return overlaps


def compose_a4(raw_pdf: Path, output: Path, title: str, source_hash: str,
               node_count: int, edge_count: int) -> dict[str, Any]:
    raw = fitz.open(raw_pdf)
    if raw.page_count != 1:
        raise RuntimeError(f"expected one raw graph page: {raw_pdf}")
    raw_rect = raw[0].rect
    graph_area = fitz.Rect(8, 34, A4.width - 8, A4.height - 47)
    scale = min(graph_area.width/raw_rect.width, graph_area.height/raw_rect.height)
    width, height = raw_rect.width*scale, raw_rect.height*scale
    placement = fitz.Rect(
        graph_area.x0 + (graph_area.width-width)/2,
        graph_area.y0 + (graph_area.height-height)/2,
        graph_area.x0 + (graph_area.width+width)/2,
        graph_area.y0 + (graph_area.height+height)/2,
    )
    document = fitz.open()
    page = document.new_page(width=A4.width, height=A4.height)
    if page.insert_textbox(
        fitz.Rect(18, 9, A4.width-18, 31), title,
        fontname="helv", fontsize=10.8, color=(0.12, 0.12, 0.12),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError(f"title overflow: {title}")
    page.show_pdf_page(placement, raw, 0, keep_proportion=True)
    legend = (
        "P postulate/input | A exact in stated model | B conditional | C fit/toy | "
        "O Open | MISSING/N-I owner absent. Solid: exact declared step; dashed: "
        "conditional/Open dependency; dotted two-way: unproved compatibility."
    )
    if page.insert_textbox(
        fitz.Rect(18, A4.height-51, A4.width-18, A4.height-23), legend,
        fontname="helv", fontsize=7.8, color=(0.16, 0.16, 0.16),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError("legend overflow")
    footer = (
        f"{node_count} semantic nodes / {edge_count} visible directed edges | "
        f"R177 owner {source_hash[:16]} | full semantic key accompanies this map"
    )
    if page.insert_textbox(
        fitz.Rect(18, A4.height-20, A4.width-18, A4.height-7), footer,
        fontname="helv", fontsize=6.9, color=(0.34, 0.34, 0.34),
        align=fitz.TEXT_ALIGN_CENTER,
    ) < 0:
        raise RuntimeError("footer overflow")
    document.set_metadata({
        "title": title,
        "author": "ECT reproducibility workflow",
        "subject": "R177 preservation-first complete derivation map successor",
        "keywords": "ECT R177 complete Graphviz status map",
        "creator": SCRIPT.name,
        "producer": "PyMuPDF",
        "creationDate": "D:20260729000000Z",
        "modDate": "D:20260729000000Z",
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output, garbage=4, deflate=True, no_new_id=True)
    document.close()
    raw.close()
    return {
        "raw_media_box_pt": [round(raw_rect.width, 3), round(raw_rect.height, 3)],
        "placement_rect_pt": [round(value, 3) for value in placement],
        "scale_from_graphviz": scale,
        "effective_node_font_pt": 17.5 * scale,
    }


def preview_modes(pdf: Path, output_dir: Path, stem: str) -> dict[str, str]:
    document = fitz.open(pdf)
    pixmap = document[0].get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False)
    rgb = output_dir / f"{stem}_rgb.png"
    rgb.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(rgb)
    document.close()
    image = Image.open(rgb).convert("RGB")
    grey = output_dir / f"{stem}_grayscale.png"
    image.convert("L").save(grey)
    array = np.asarray(image, dtype=np.float32) / 255.0
    result = {"rgb": str(rgb), "grayscale": str(grey)}
    for name, matrix in CVD.items():
        simulated = np.clip(array @ matrix.T, 0.0, 1.0)
        path = output_dir / f"{stem}_{name}.png"
        Image.fromarray((simulated*255).astype(np.uint8), "RGB").save(path)
        result[name] = str(path)
    return result


def pdf_text(path: Path) -> str:
    document = fitz.open(path)
    result = "\n".join(page.get_text() for page in document)
    document.close()
    return result


def pdf_metrics(path: Path) -> dict[str, Any]:
    document = fitz.open(path)
    fonts = sorted({font[3] for page in document for font in page.get_fonts(full=True)})
    result = {
        "pages": document.page_count,
        "media_boxes_pt": [[round(page.rect.width, 3), round(page.rect.height, 3)] for page in document],
        "rotations": [page.rotation for page in document],
        "font_names": fonts,
        "searchable_text_chars": len(pdf_text(path)),
    }
    document.close()
    return result


def build_logic_map(key: str, root: Path) -> dict[str, Any]:
    source_dir = root / "source"
    source_path = source_dir / f"{key}_complete_map_successor_r177.gv"
    build_graph_source(key, source_path)
    raw_pdf = root / "intermediate" / f"{key}_r177_raw.pdf"
    layout_path = root / "intermediate" / f"{key}_r177.layout.json"
    raw_pdf.parent.mkdir(parents=True, exist_ok=True)
    run(["dot", "-Tpdf", str(source_path), "-o", str(raw_pdf)])
    run(["dot", "-Tjson", str(source_path)], stdout_path=layout_path)
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    node_count, edge_count = graph_counts(layout)
    output_name = f"{key}_a4_reader_r177.pdf"
    output_pdf = root / "assets" / output_name
    titles = {
        "partIII": "Complete R177 derivation logic of Part III - quantum sector and PES-R",
        "partIV": "Complete R177 derivation logic of Part IV - conditional colour programme",
        "whole": "Complete R177 status-sensitive programme map of ECT",
    }
    placement = compose_a4(
        raw_pdf, output_pdf, titles[key], sha256(source_path), node_count, edge_count
    )
    previews = preview_modes(output_pdf, root / "previews", key)
    labels = graph_node_labels(layout)
    edges = graph_edges(layout)
    with (root / "semantic_keys" / f"{key}_node_key_r177.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["node_id", "display_label"], lineterminator="\n")
        writer.writeheader()
        for node, label in sorted(labels.items()):
            writer.writerow({"node_id": node, "display_label": label})
    with (root / "semantic_keys" / f"{key}_edge_key_r177.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=["tail", "head", "style", "dir"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(edges)
    full_key = {
        "schema": f"{SCHEMA}.semantic_key",
        "map": key,
        "scientific_status": "candidate semantic successor; no live authority",
        "nodes": labels,
        "edges": edges,
        "expanded_semantics": EXPANDED_SEMANTICS[key],
        "expanded_edge_semantics": EXPANDED_EDGE_SEMANTICS[key],
        "binding_owner_rules": {
            "action": (
                "Reduced iota/I objects are dimensionless; Sigma_theta and "
                "Sigma_vartheta are independent action-valued normalisations; "
                "only products may be matched to operational S0; S0=hbar is calibration."
            ),
            "p3_p4": (
                "P3 radial mass is confined to P3; a P4 pole requires its own "
                "stationary action and constrained Hessian; no identity is drawn."
            ),
            "partiv": (
                "P7 does not derive a colour connection, action, matter content or "
                "physical mass gap; HKLoc/polymer remains an incomplete entry criterion."
            ),
            "vaf": (
                "Vector energy/CPT, axial spin and dynamical mediator force/WEP "
                "operators are independent and have no derivation arrows between them."
            ),
        },
    }
    write_text(root / "semantic_keys" / f"{key}_full_key_r177.json", stable_json(full_key))
    required = {
        "partIII": [
            "dimless", "Sigma_theta", "Sigma_vartheta", "S0=hbar calib.",
            "Admitted measure", "Crooks + F/R", "Source-model", "ECT map Open",
        ],
        "partIV": [
            "Singlet counterex.", "Z>0 and Z-Y/2>0", "A(8)=0; A(6)=7",
            "Unmapped osc.", "theta_gauge:", "allowed, not forced", "HKLoc incomplete",
            "Physical gap bridge", "Proton patterns",
        ],
        "whole": ["P3 radial", "P4", "Sigma_th", "Sigma_vth", "Vector", "d=3", "Axial", "Mediator", "HKLoc"],
    }[key]
    searchable = pdf_text(output_pdf)
    missing_required = [token for token in required if token.lower() not in searchable.lower()]
    forbidden_hits = [
        token for token in FORBIDDEN_DISPLAY_TOKENS[key]
        if token.lower() in searchable.lower()
    ]
    statuses_missing = [node for node, label in labels.items() if not re.search(r"\[[^\]]+\]", label)]
    old_labels = graph_node_labels(json.loads(run_dot_json(UPSTREAMS[key][0])))
    qa = {
        "schema": f"{SCHEMA}.automated_qa",
        "map": key,
        "source_sha256": sha256(source_path),
        "asset_sha256": sha256(output_pdf),
        "node_count": node_count,
        "edge_count": edge_count,
        "old_node_count": len(old_labels),
        "old_nodes_preserved": set(old_labels).issubset(labels),
        "added_nodes": sorted(set(labels) - set(old_labels)),
        "node_overlaps": node_overlaps(layout),
        "statuses_missing": statuses_missing,
        "missing_required_tokens": missing_required,
        "forbidden_display_token_hits": forbidden_hits,
        "all_visible_edges_near_black_by_graph_default": '#222222' in source_path.read_text(encoding="utf-8"),
        "pdf": pdf_metrics(output_pdf),
        "placement": placement,
        "verdict": "PASS",
    }
    if qa["node_overlaps"] or statuses_missing or missing_required or forbidden_hits:
        qa["verdict"] = "FAIL"
        raise RuntimeError(stable_json(qa))
    write_text(root / "qa" / f"{key}_AUTOMATED_QA.json", stable_json(qa))
    return {
        "key": key,
        "source": source_path,
        "asset": output_pdf,
        "layout": layout_path,
        "previews": previews,
        "qa": qa,
    }


def run_dot_json(source: Path) -> str:
    env = os.environ.copy()
    env.update({"LC_ALL": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH})
    completed = subprocess.run(
        ["dot", "-Tjson", str(source)], check=True, capture_output=True, text=True, env=env
    )
    return completed.stdout


ARCH_NODES = {
    "phi": (6.0, 11.9, 5.4, 0.75, "Phi medium on M4 - P1-P6 and DP\npostulates / supplied starting layer", PALE_BLUE, BLUE, "-"),
    "p3": (2.1, 10.45, 3.55, 1.05, "P3 homogeneous scalar action\nradial mass m_Phi,rad^2 = 2 mu^2\n[A inside P3 only]", PALE_BLUE, BLUE, "-"),
    "p4": (6.0, 10.45, 3.55, 1.05, "P4 directional datum / chart\nO(4) vector stabiliser O(3)\n[Input; stationary P4 action Open]", PALE_GREEN, GREEN, "--"),
    "eft": (9.9, 10.45, 4.0, 1.25, "Separately supplied scalar kinetic EFT\nK = beta delta - alpha n n\n[B/Input; coefficients not from P4]", PALE_GREEN, GREEN, "--"),
    "p4pole": (3.2, 8.75, 4.3, 1.10, "P4 pole / particle needs stationary action\nstate plus constrained Hessian [Open]\nno P3-radial identity", PALE_AMBER, AMBER, "--"),
    "sig": (8.0, 8.75, 5.2, 1.15, "Signature: beta(beta-alpha) < 0 [A in supplied EFT]\nalpha > beta only on branch beta > 0\nphysical clock/photon/tensor cones Open", PALE_BLUE, BLUE, "-"),
    "macro": (3.0, 6.9, 4.8, 1.25, "Macroscopic / tensor programme (Part II)\nphysical metric, tensor source, G_N map Open\nconditional cosmology and HRC diagnostics", WHITE, GREY, "--"),
    "quant": (9.0, 6.9, 4.8, 1.25, "Coherent / quantum programme (Part III)\nfree-Gaussian OS-II conditional; measure admitted\nSigma x I action matching and outcomes Open", WHITE, GREY, "--"),
    "colour": (2.3, 4.75, 4.5, 1.35, "Part IV / P7 structural colour programme\nconnection, action, matter and mass gap Open\nb0=11/local lemmas do not close HKLoc", PALE_GREEN, GREEN, "--"),
    "vector": (6.35, 4.75, 3.1, 1.35, "d=3 vector current\nenergy/CPT coefficient\n[B/Open]", PALE_GREEN, GREEN, "--"),
    "axial": (9.7, 5.25, 3.3, 0.85, "Independent axial/Pauli operator\nspin / precession [Open]", PALE_AMBER, AMBER, "--"),
    "mediator": (9.8, 4.05, 3.6, 0.95, "Independent mediator\nprofile/propagator\nforce / WEP [Open]", PALE_AMBER, AMBER, "--"),
    "outputs": (6.0, 2.55, 8.7, 1.15, "Conditional outputs, external comparators and falsifiers\nvalid algebra / benchmarks retained at A/B/C with explicit assumptions\nphysical cross-sector owners and universal ECT conclusions remain Open", PALE_AMBER, AMBER, "--"),
}

ARCH_EDGES = [
    ("phi", "p3", "-"), ("phi", "p4", "--"), ("phi", "eft", "--"),
    ("p4", "p4pole", "--"), ("p4", "sig", "--"), ("eft", "sig", "-"),
    ("sig", "macro", "--"), ("sig", "quant", "--"),
    ("macro", "colour", "--"), ("macro", "vector", "--"),
    ("quant", "vector", "--"), ("macro", "outputs", "--"),
    ("quant", "outputs", "--"), ("colour", "outputs", "--"),
    ("vector", "outputs", "--"), ("axial", "outputs", "--"),
    ("mediator", "outputs", "--"),
]


def build_architecture(root: Path) -> dict[str, Any]:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9.2,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.facecolor": "white",
    })
    fig, ax = plt.subplots(figsize=(7.9, 9.2))
    ax.set_xlim(0, 12); ax.set_ylim(0.7, 13.25); ax.axis("off")
    ax.text(6, 13.05, "ECT programme architecture - R177 corrected owner graph",
            ha="center", va="top", weight="bold", fontsize=12.0)
    ax.text(6, 12.66, "No P3 radial -> P4 pole identity; no P4 datum -> EFT coefficient derivation.",
            ha="center", va="top", color=GREY, fontsize=8.7)
    patches: dict[str, FancyBboxPatch] = {}
    texts: dict[str, Any] = {}
    for key, (x, y, w, h, label, fill, edge, linestyle) in ARCH_NODES.items():
        patch = FancyBboxPatch(
            (x-w/2, y-h/2), w, h,
            boxstyle="round,pad=0.07,rounding_size=0.10",
            facecolor=fill, edgecolor=edge, linestyle=linestyle,
            linewidth=1.35, zorder=3,
        )
        ax.add_patch(patch); patches[key] = patch
        texts[key] = ax.text(x, y, label, ha="center", va="center", fontsize=6.80,
                             linespacing=1.02, color=BLACK, zorder=4)

    def boundary_point(src: str, dst: str, at_source: bool) -> tuple[float, float]:
        sx, sy, sw, sh, *_ = ARCH_NODES[src]
        dx, dy, dw, dh, *_ = ARCH_NODES[dst]
        vx, vy = dx-sx, dy-sy
        if vx == 0 and vy == 0:
            return sx, sy
        scale = min(sw/(2*abs(vx)) if vx else math.inf,
                    sh/(2*abs(vy)) if vy else math.inf)
        if at_source:
            return sx + vx*scale, sy + vy*scale
        scale_d = min(dw/(2*abs(vx)) if vx else math.inf,
                      dh/(2*abs(vy)) if vy else math.inf)
        return dx - vx*scale_d, dy - vy*scale_d

    for src, dst, linestyle in ARCH_EDGES:
        start = boundary_point(src, dst, True)
        end = boundary_point(src, dst, False)
        ax.add_patch(FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=10.5,
            linewidth=1.05, linestyle=linestyle, color=BLACK, zorder=2,
            connectionstyle="arc3,rad=0.0",
        ))
    # Missing common-action/backreaction connector is explicit and is not a
    # derived arrow between the two programmes.
    ax.add_patch(FancyArrowPatch(
        (5.40, 6.12), (6.60, 6.12), arrowstyle="<|-|>", mutation_scale=9,
        linewidth=1.0, linestyle="--", color=GREY, zorder=2,
    ))
    ax.text(6, 5.91, "common-action / backreaction vertex MISSING",
            ha="center", fontsize=7.8, color=GREY, style="italic",
            bbox=dict(boxstyle="round,pad=.08", fc=WHITE, ec="none", alpha=.94))
    ax.text(6, 1.30,
            "Solid near-black arrow: exact step inside the stated supplied model.  Dashed: conditional/Open dependency.",
            ha="center", fontsize=7.8, color=BLACK)
    ax.text(6, 1.00,
            "Colour is redundant with literal status, fill luminance and border/arrow style.",
            ha="center", fontsize=7.8, color=GREY)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inverse = ax.transData.inverted()
    overflows: list[str] = []
    for key, artist in texts.items():
        x, y, w, h, *_ = ARCH_NODES[key]
        bbox = inverse.transform_bbox(artist.get_window_extent(renderer=renderer))
        if bbox.x0 < x-w/2 or bbox.x1 > x+w/2 or bbox.y0 < y-h/2 or bbox.y1 > y+h/2:
            overflows.append(key)
    if overflows:
        raise RuntimeError(f"architecture text overflow: {overflows}")
    output = root / "assets" / "fig_ect_architecture_r177.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output, bbox_inches="tight",
        metadata={
            "Title": "ECT programme architecture - R177 corrected owner graph",
            "Author": "ECT reproducibility workflow",
            "Subject": "Preservation-first successor of the R149 architecture map",
            "Creator": SCRIPT.name,
            "CreationDate": FIXED_DATE,
            "ModDate": FIXED_DATE,
        },
    )
    plt.close(fig)
    previews = preview_modes(output, root / "previews", "architecture")
    node_rows = {key: values[4] for key, values in ARCH_NODES.items()}
    edge_rows = [
        {"tail": tail, "head": head, "style": "solid" if style == "-" else "dashed", "dir": "forward"}
        for tail, head, style in ARCH_EDGES
    ]
    full_key = {
        "schema": f"{SCHEMA}.semantic_key",
        "map": "architecture",
        "nodes": node_rows,
        "edges": edge_rows,
        "missing_connector": {
            "between": ["macro", "quant"],
            "status": "MISSING",
            "meaning": "common-action/backreaction vertex not derived",
        },
        "scientific_status": "candidate semantic successor; no live authority",
    }
    write_text(root / "semantic_keys" / "architecture_full_key_r177.json", stable_json(full_key))
    required = [
        "P3 homogeneous scalar action", "P4 directional datum", "Separately supplied scalar kinetic EFT",
        "beta(beta-alpha) < 0", "stationary P4 action Open", "axial/Pauli", "profile/propagator",
        "HKLoc", "backreaction vertex MISSING",
    ]
    searchable = pdf_text(output)
    missing = [token for token in required if token.lower() not in searchable.lower()]
    qa = {
        "schema": f"{SCHEMA}.automated_qa",
        "map": "architecture",
        "node_count": len(ARCH_NODES),
        "edge_count": len(ARCH_EDGES),
        "text_overflows": overflows,
        "missing_required_tokens": missing,
        "pdf": pdf_metrics(output),
        "asset_sha256": sha256(output),
        "verdict": "PASS" if not missing else "FAIL",
    }
    if missing:
        raise RuntimeError(stable_json(qa))
    write_text(root / "qa" / "architecture_AUTOMATED_QA.json", stable_json(qa))
    return {"key": "architecture", "asset": output, "previews": previews, "qa": qa}


def contact_sheet(paths: list[Path], output: Path, title: str) -> None:
    images = [Image.open(path).convert("RGB") for path in paths]
    thumb_w = 900
    resized: list[Image.Image] = []
    for image in images:
        height = int(image.height * thumb_w / image.width)
        resized.append(image.resize((thumb_w, height), Image.Resampling.LANCZOS))
    margin, header, gap = 40, 90, 30
    width = thumb_w * 2 + margin * 2 + gap
    row_heights = [max(resized[i].height, resized[i+1].height) for i in (0, 2)]
    height = header + margin + sum(row_heights) + gap + margin
    canvas = Image.new("RGB", (width, height), "white")
    # Keep the contact sheet deterministic and dependency-light: no rendered
    # title font is needed; the filename supplies the mode.
    y = header + margin
    for row, start in enumerate((0, 2)):
        for col in (0, 1):
            image = resized[start+col]
            x = margin + col*(thumb_w+gap)
            canvas.paste(image, (x, y))
        y += row_heights[row] + gap
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def reproducible_files(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and "intermediate" not in path.parts:
            result[str(path.relative_to(root))] = sha256(path)
    return result


def build_all(root: Path) -> dict[str, Any]:
    (root / "semantic_keys").mkdir(parents=True, exist_ok=True)
    (root / "qa").mkdir(parents=True, exist_ok=True)
    results = [build_architecture(root)]
    for key in ("partIII", "partIV", "whole"):
        results.append(build_logic_map(key, root))
    rgb = [Path(item["previews"]["rgb"]) for item in results]
    grey = [Path(item["previews"]["grayscale"]) for item in results]
    contact_sheet(rgb, root / "previews" / "CONTACT_SHEET_RGB.png", "RGB")
    contact_sheet(grey, root / "previews" / "CONTACT_SHEET_GRAYSCALE.png", "grayscale")
    return {
        "schema": f"{SCHEMA}.build",
        "results": [
            {
                "key": item["key"],
                "asset": str(item["asset"].relative_to(root)),
                "asset_sha256": sha256(item["asset"]),
                "qa": item["qa"],
            }
            for item in results
        ],
    }


def install_outputs(source: Path, destination: Path) -> None:
    for directory in ("assets", "source", "semantic_keys", "qa", "previews"):
        target = destination / directory
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source / directory, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-replay", action="store_true")
    args = parser.parse_args()
    inputs = verify_inputs()
    with tempfile.TemporaryDirectory(prefix="ect_r177_remaining_maps_a_") as tmp_a:
        run_a = Path(tmp_a)
        build_report = build_all(run_a)
        hashes_a = reproducible_files(run_a)
        replay: dict[str, Any] = {"skipped": args.skip_replay}
        if not args.skip_replay:
            with tempfile.TemporaryDirectory(prefix="ect_r177_remaining_maps_b_") as tmp_b:
                run_b = Path(tmp_b)
                build_all(run_b)
                hashes_b = reproducible_files(run_b)
            replay = {
                "skipped": False,
                "file_set_equal": sorted(hashes_a) == sorted(hashes_b),
                "byte_identical": hashes_a == hashes_b,
                "file_count": len(hashes_a),
                "mismatches": sorted(
                    path for path in set(hashes_a) | set(hashes_b)
                    if hashes_a.get(path) != hashes_b.get(path)
                ),
            }
            if not replay["file_set_equal"] or not replay["byte_identical"]:
                raise RuntimeError(stable_json(replay))
        install_outputs(run_a, PACKAGE)
    runtime = {
        "schema": f"{SCHEMA}.runtime",
        "fixed_utc": FIXED_UTC,
        "python": sys.version.split()[0],
        "graphviz": run(["dot", "-V"]),
        "pymupdf": fitz.__doc__.split()[1].rstrip(":"),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "pillow": PIL.__version__,
        "generator": str(SCRIPT.relative_to(WORKSPACE)),
        "generator_sha256": sha256(SCRIPT),
    }
    write_text(PACKAGE / "BUILD_REPORT.json", stable_json(build_report))
    write_text(PACKAGE / "REPLAY_CHECK.json", stable_json(replay))
    write_text(PACKAGE / "RUNTIME_PROVENANCE.json", stable_json(runtime))
    payload = {}
    for path in sorted(PACKAGE.rglob("*")):
        if (
            path.is_file()
            and path.name not in {"PACKAGE_MANIFEST.json"}
            and "__pycache__" not in path.parts
        ):
            payload[str(path.relative_to(PACKAGE))] = {
                "sha256": sha256(path), "bytes": path.stat().st_size,
            }
    manifest = {
        "schema": f"{SCHEMA}.manifest",
        "owner_id": "R177_REMAINING_COMPLETE_MAP_SUCCESSORS_v1",
        "status": "LOCALLY FROZEN CANDIDATE; not live, not apply-authorised",
        "input_owners": inputs,
        "payload": payload,
    }
    write_text(PACKAGE / "PACKAGE_MANIFEST.json", stable_json(manifest))
    print(stable_json({
        "verdict": "PASS", "replay": replay,
        "assets": {
            path.name: sha256(path) for path in sorted((PACKAGE / "assets").glob("*.pdf"))
        },
    }))


if __name__ == "__main__":
    main()
