#!/usr/bin/env python3
"""
P6/PES freeze status audit (GPT Round 25).

Purpose:
  - environment-compatible: stdlib only, no pandas, no absolute paths required;
  - checks that the current ledger/honesty/verification files contain the sentinel
    statements needed for a P6/PES ledger freeze;
  - emits a compact CSV that Claude/Valera can diff or archive.

Usage:
  python p6_freeze_status_audit.py
  python p6_freeze_status_audit.py --root path/to/derivations/pes
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class Check:
    block: str
    item: str
    requirement: str
    status_if_found: str
    status_if_missing: str
    patterns: tuple[str, ...]
    file_hint: str = "ledger"


def newest_matching(root: Path, patterns: Iterable[str]) -> Optional[Path]:
    candidates: list[Path] = []
    for pat in patterns:
        candidates.extend(root.glob(pat))
    if not candidates:
        return None
    # Prefer larger ledger revisions and newest uploads; stable enough for archive use.
    return max(candidates, key=lambda p: (p.stat().st_mtime, len(p.name), p.name))


def read_text(path: Optional[Path]) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def has_all(text: str, patterns: tuple[str, ...]) -> bool:
    return all(re.search(p, text, flags=re.IGNORECASE | re.MULTILINE) for p in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="directory containing ledger/verification files")
    parser.add_argument("--out", default="p6_freeze_status_summary.csv", help="CSV output file")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ledger = newest_matching(root, ["PES_LAWS_LEDGER_v6*.md", "*PES*LEDGER*.md"])
    honesty = newest_matching(root, ["P6_HONESTY_LOG*.md"])
    verifs = sorted(root.glob("P6_VERIFICATION_v*.md"), key=lambda p: p.name)
    latest_verif = verifs[-1] if verifs else None

    ledger_text = read_text(ledger)
    honesty_text = read_text(honesty)
    latest_verif_text = read_text(latest_verif)
    all_text = "\n".join([ledger_text, honesty_text, latest_verif_text])

    checks = [
        Check("S6", "C8 canonical normalization", "canonical C8 temp/spat kernels and reduced=4x dictionary present", "CLOSED", "MISSING", (r"canonical J_temp", r"historical-reduced\s*=\s*4x", r"J_S/J_T\s*=\s*w\^2/c\^2")),
        Check("S6", "C13' threshold protection", "conditional 5-case threshold-protection theorem present", "ADOPTED_CONDITIONAL", "MISSING", (r"P6-C13'", r"5-case", r"Gamma\(omega_b\)\s*=\s*0")),
        Check("S6", "bosonic KK mirror", "R19 bosonic mirror/sum-rule correction present", "CERTIFIED", "MISSING", (r"Z \+ int 2w rho_cont\s*=\s*1", r"0\.99999", r"1\.00000")),
        Check("S6", "zeta0 pair convention", "absolute record-normalization convention closed as zeta0 pair=2", "CLOSED", "MISSING", (r"zeta_0", r"zeta_0\^pair\s*=\s*2", r"sigma_pair\s*=\s*2 sigma_face")),
        Check("S7", "one-kernel triangle", "fixed channel: dephasing/widths/shifts are projections of one positive kernel", "ADOPTED", "MISSING", (r"P6-S7", r"dephasing/widths/shifts", r"ONE positive spectral kernel")),
        Check("S7", "matrix-kernel guard", "J_ab positivity and Cauchy-Schwarz detector present", "BINDING_GUARD", "MISSING", (r"P6-G4", r"Matrix-kernel", r"J_ab")),
        Check("S7", "P26 over-closure", "width corner reconstructs kernel and predicts other corners", "FALSIFIER_READY", "MISSING", (r"P6-P26", r"width corner", r"ratios 1\.000000")),
        Check("M3", "M3-1 P23/P24", "two-protocol edge-plus-line/detuning protocol adopted", "ADOPTED", "MISSING", (r"M3-1", r"Two-protocol contrast", r"P23/P24")),
        Check("M3", "M3-2 P7'/P18", "zero-mode detector protocol adopted", "ADOPTED", "MISSING", (r"P6-M3-2", r"Zero-mode detector", r"Q_core")),
        Check("M3", "M3-3 P11/P25", "Airy/fingerprint composite protocol adopted", "ADOPTED", "MISSING", (r"P6-M3-3", r"Composite protocol", r"Airy-squared")),
        Check("Correction", "P11 kappa_b correction", "stiffness convention correction and C9 scaling present", "CORRECTED_LOGGED", "MISSING", (r"P6-P11-corr", r"kappa_b.*sigma_dec.*-1/3", r"L_z\^coh")),
        Check("Correction", "G8 kappa/flexibility guard", "same-symbol stiffness/flexibility guard present", "BINDING_GUARD", "MISSING", (r"P6-G8", r"D_b\s*=\s*1/kappa_b")),
        Check("Milestone", "M3 queue complete", "all three M3 protocols adopted with operational guards", "QUEUE_COMPLETE", "MISSING", (r"M3 QUEUE COMPLETE", r"structural phase \+ falsification protocols", r"FULLY ASSEMBLED")),
        Check("Open", "preprint transfer pending", "freeze still requires Valera preprint-transfer decision", "PENDING_DECISION", "MISSING", (r"preprint-transfer decision", r"final consolidation/freeze")),
        Check("Open", "deep opens separated", "OP-GUT1/OP-Planck/S0 not collapsed into P6 closure", "SEPARATED", "MISSING", (r"OP-GUT1", r"OP-Planck", r"S_0")),
        Check("Honesty", "P11 honesty log", "transcription error logged in honesty file", "LOGGED", "MISSING", (r"TRANSCRIPTION error", r"ell = \(2 kappa_b sigma\)"), file_hint="honesty"),
    ]

    rows = []
    passed = 0
    for ch in checks:
        source_text = honesty_text if ch.file_hint == "honesty" else all_text
        ok = has_all(source_text, ch.patterns)
        passed += int(ok)
        rows.append({
            "block": ch.block,
            "item": ch.item,
            "requirement": ch.requirement,
            "status": ch.status_if_found if ok else ch.status_if_missing,
            "found": "yes" if ok else "no",
            "patterns": " ; ".join(ch.patterns),
        })

    summary_status = "FREEZE_CANDIDATE_PASS" if passed == len(checks) else "FREEZE_CANDIDATE_INCOMPLETE"
    rows.append({
        "block": "Summary",
        "item": "sentinel checks",
        "requirement": f"{passed}/{len(checks)} required sentinels found",
        "status": summary_status,
        "found": "yes" if passed == len(checks) else "no",
        "patterns": f"ledger={ledger.name if ledger else 'MISSING'}; honesty={honesty.name if honesty else 'MISSING'}; latest_verif={latest_verif.name if latest_verif else 'MISSING'}",
    })

    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["block", "item", "requirement", "status", "found", "patterns"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"ledger={ledger}")
    print(f"honesty={honesty}")
    print(f"latest_verification={latest_verif}")
    print(f"sentinels={passed}/{len(checks)}")
    print(f"status={summary_status}")
    print(f"wrote={out}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
