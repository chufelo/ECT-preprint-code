#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package 1 fix2, version 2 (session 2026-06-09).

(1) Completion of the SANCTIONED P1-4 rename beta -> beta_phi.
    v1 used exact anchors for the \\ln\\frac variants (3 sites) and was
    correctly aborted by the broad zero-check: the file contains FIVE
    further \\frac{1}{\\beta}\\ln sites with other argument typographies
    (invisible to the v4 +-2-line audit). Total on disk: 8.
    v2 replaces the entire class generically:
      every occurrence of \\frac{1}{\\beta}\\ln (and the \\, variant) is
      context-dumped, signature-verified (the argument must contain
      u_\\infty within the following 90 chars - the unique fingerprint
      of the phi-definition phi = (1/beta_phi) ln(u/u_inf)), and only
      then renamed. Hard expectation: primary pattern count == 8.
    Plus the unchanged F1 (prose definition), F3 (EFT-parameter table
    row), F4 (beta(phi')^2 term of the N-variable scalar equation).

(2) Proper 4-pass compilation (bug #3 fix kept from v1):
    pdflatex/bibtex console -> DEVNULL; .log/.blg parsed from bytes
    with errors='ignore'.

(3) Zero-checks now SELF-DIAGNOSE: on failure they dump up to 10
    contexts of the offending pattern before aborting.

Idempotent: if the fix2 edits are already present, skips straight to
compile-only mode (safe to re-run just to recompile).
Abort-before-write: the file is written only if every hard assert
passes. Backup created before the write:
backup/ECT_preprint_BACKUP_v203_pre_package1_fix2.tex
Report: scripts/package1_fix2_report.txt
"""
import hashlib, re, shutil, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # .../LaTex
TEX  = BASE / "ECT_preprint.tex"
BAK  = BASE / "backup"
REP  = BASE / "scripts" / "package1_fix2_report.txt"
PDFLATEX = "/Library/TeX/texbin/pdflatex"
BIBTEX   = "/Library/TeX/texbin/bibtex"

log_lines = []
def log(s):
    print(s)
    log_lines.append(s)

def flush():
    REP.write_text("\n".join(log_lines), encoding="utf-8")

def fail(msg):
    log("FATAL: " + msg)
    flush()
    sys.exit(1)

data = TEX.read_bytes()
log(f"[gate] md5(ECT_preprint.tex) = {hashlib.md5(data).hexdigest()}  size={len(data)} bytes")
content = data.decode("utf-8")

if "eq:Ktheta_1D" not in content:
    fail("Package 1 (v4) not applied: eq:Ktheta_1D missing. Run package1_apply.py first. NOTHING modified.")

ALREADY = "and $\\beta_\\phi$ is a dimensionless coupling parameter."
edits_needed = ALREADY not in content
if not edits_needed:
    log("[gate] fix2 edits already present -> COMPILE-ONLY mode")

def rep1(cid, old, new):
    global content
    n = content.count(old)
    if n != 1:
        fail(f"{cid}: anchor count={n} (expected 1): {old[:90]!r}")
    content = content.replace(old, new)
    log(f"[{cid}] 1 replacement")

def rep_all_ctx(cid, old, new, min_expected=1):
    global content
    positions = [m.start() for m in re.finditer(re.escape(old), content)]
    log(f"[{cid}] occurrences={len(positions)}; contexts:")
    for p in positions:
        log("   | ..." + content[max(0, p-55):p+len(old)+28].replace("\n", "\\n") + "...")
    if len(positions) < min_expected:
        fail(f"{cid}: found {len(positions)}, expected >= {min_expected}: {old[:70]!r}")
    content = content.replace(old, new)
    log(f"[{cid}] {len(positions)} replacements")

if edits_needed:
    PRESERVED = [r"\beta^2/c_*", r"\beta\bar\Psi", r"\beta\,\bar\Psi", r"\alpha-\beta"]
    orig_inv = {p: content.count(p) for p in PRESERVED}
    for p in PRESERVED:
        log(f"[invariant] baseline count({p!r}) = {orig_inv[p]}")

    # ---- F1: prose definition of the coupling ----
    rep1("F1-prose-coupling",
         "and $\\beta$ is a dimensionless coupling parameter.",
         "and $\\beta_\\phi$ is a dimensionless coupling parameter.")

    # ---- F2-generic: the ENTIRE class of (1/beta) ln phi-definitions ----
    PRIMARY  = r"\frac{1}{\beta}\ln"
    THINSP   = r"\frac{1}{\beta}\,\ln"
    sites = []
    for g in (PRIMARY, THINSP):
        for m in re.finditer(re.escape(g), content):
            sites.append((g, m.start()))
    n_primary = sum(1 for g, _ in sites if g == PRIMARY)
    n_thin    = sum(1 for g, _ in sites if g == THINSP)
    log(f"[F2-generic] primary occurrences={n_primary}, thin-space occurrences={n_thin}; contexts:")
    bad = []
    for g, p in sorted(sites, key=lambda t: t[1]):
        ctx = content[max(0, p-55):p+95].replace("\n", "\\n")
        sig = "u_\\infty" in content[p:p+95]
        log(("   OK  | ..." if sig else "   BAD | ...") + ctx + "...")
        if not sig:
            bad.append(ctx)
    if bad:
        fail(f"F2-generic: {len(bad)} site(s) lack the u_infty signature - manual review required. NOTHING modified.")
    if n_primary != 8:
        fail(f"F2-generic: primary count={n_primary}, expected 8 (3 dumped by v1 + 5 caught by the zero-check). NOTHING modified.")
    content = content.replace(PRIMARY, r"\frac{1}{\beta_\phi}\ln")
    content = content.replace(THINSP,  r"\frac{1}{\beta_\phi}\,\ln")
    log(f"[F2-generic] {n_primary + n_thin} replacements (signature-verified)")

    # ---- F3: EFT-parameter table row ----
    rep1("F3-EFT-param-row",
         "($Z_u$, $W$, $\\beta$)",
         "($Z_u$, $W$, $\\beta_\\phi$)")

    # ---- F4: N-variable scalar equation, beta(phi')^2 term ----
    rep_all_ctx("F4-scalar-eq-Nvar",
         r"\beta(\phi')^2",
         r"\beta_\phi(\phi')^2")

    # ================= sanity (self-diagnosing) =================
    zero_checks = [
        r"\frac{1}{\beta}\ln", r"\frac{1}{\beta}\,\ln", r"\beta(\phi')",
        r"e^{\beta\phi", r"e^{-\beta\phi", r"e^{2\beta\phi",
        r"\beta \phi", r"\beta\phi",
        r"\beta e^{", r"\beta^2 e^{", r"(1+\beta q)",
        "t=w/c_*", r"2\hbar/K_\theta",
    ]
    for pat in zero_checks:
        n = content.count(pat)
        if n != 0:
            log(f"[sanity-FAIL] count({pat!r})={n}; contexts:")
            for m in list(re.finditer(re.escape(pat), content))[:10]:
                p = m.start()
                log("   | ..." + content[max(0, p-55):p+75].replace("\n", "\\n") + "...")
            fail(f"sanity-zero: count({pat!r})={n}, expected 0")
    log("[sanity] all zero-checks OK")
    for p in PRESERVED:
        n = content.count(p)
        if n != orig_inv[p]:
            fail(f"sanity-invariant: count({p!r})={n}, baseline {orig_inv[p]} - edits leaked")
        log(f"[sanity] invariant OK: {p!r} = {n} (unchanged)")
    log(f"[sanity] beta_phi total occurrences now: {content.count(chr(92)+'beta_'+chr(92)+'phi')}")

    # ---- audit 1: mixed beta/beta_phi neighbourhoods (expect exactly 1:
    #      the deliberate definitional note near eq:Geff_phi) ----
    lines = content.split("\n")
    has_b  = [("\\beta" in L) and ("\\beta_\\phi" not in L) and ("\\beta_5" not in L) for L in lines]
    has_bp = ["\\beta_\\phi" in L for L in lines]
    sus = [(i+1, lines[i].strip()[:110]) for i in range(len(lines))
           if has_b[i] and any(has_bp[max(0, i-2):i+3])]
    log(f"[audit-1] mixed beta/beta_phi neighbourhoods: {len(sus)} (expected 1 = definitional note; non-fatal)")
    for ln, txt in sus[:40]:
        log(f"   L{ln}: {txt}")

    # ---- audit 2 (review-only): solitary math-mode $\beta$ tokens ----
    tok = "$\\beta$"
    hits = [(i+1, L.strip()[:110]) for i, L in enumerate(lines) if tok in L]
    log(f"[audit-2] lines containing solitary {tok!r}: {len(hits)} (review-only; kinetic-beta mentions are legitimate)")
    for ln, txt in hits[:50]:
        log(f"   L{ln}: {txt}")

    # ---- audit 3 (review-only): remaining suspicious beta forms ----
    for pat in [r"\frac{1}{\beta}", r"\beta(", r"\beta^{-1}\ln"]:
        positions = [m.start() for m in re.finditer(re.escape(pat), content)]
        log(f"[audit-3] count({pat!r}) = {len(positions)} (review-only)")
        for p in positions[:10]:
            log("   | ..." + content[max(0, p-45):p+42].replace("\n", "\\n") + "...")

    # ================= write (backup first) =================
    BAK.mkdir(exist_ok=True)
    bak = BAK / "ECT_preprint_BACKUP_v203_pre_package1_fix2.tex"
    if bak.exists():
        fail(f"backup already exists: {bak.name} - refusing to overwrite. NOTHING modified.")
    shutil.copy2(TEX, bak)
    log(f"[backup] backup/{bak.name} created")
    TEX.write_text(content, encoding="utf-8")
    log(f"[write] ECT_preprint.tex written ({len(content)} chars)")
    flush()

# ================= 4-pass compilation (both modes) =================
def run(cmd):
    r = subprocess.run(cmd, cwd=str(BASE),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=2400)
    return r.returncode

log("[compile] pdflatex -> bibtex -> pdflatex -> pdflatex (console suppressed; parsing .log/.blg)")
try:
    rcs = []
    rcs.append(run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]))
    rcs.append(run([BIBTEX, "ECT_preprint"]))
    rcs.append(run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]))
    rcs.append(run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]))
    log(f"[compile] return codes: {rcs}")
except Exception as e:
    log(f"[compile] EXECUTION FAILED: {e}")
    flush()
    sys.exit(1)

logf = BASE / "ECT_preprint.log"
logtxt = logf.read_bytes().decode("utf-8", errors="ignore")
err_lines = [L for L in logtxt.splitlines() if L.startswith("!")]
nundef_ref = logtxt.count("Warning: Reference")
nundef_cit = logtxt.count("Warning: Citation")
nmult = logtxt.count("multiply defined") + logtxt.count("multiply-defined")
mpages = re.search(r"Output written on ECT_preprint\.pdf \((\d+) pages", logtxt)
log(f"[compile] hard errors (^!): {len(err_lines)}")
for L in err_lines[:10]:
    log("   ! " + L[:110])
log(f"[compile] undefined references: {nundef_ref}; undefined citations: {nundef_cit}; multiply-defined: {nmult}")
log(f"[compile] PAGES: {mpages.group(1) if mpages else 'NOT FOUND'} (was 740)")

blg = BASE / "ECT_preprint.blg"
if blg.exists():
    blgtxt = blg.read_bytes().decode("utf-8", errors="ignore")
    blg_err = [L for L in blgtxt.splitlines() if "rror" in L]
    log(f"[bibtex] .blg error-lines: {len(blg_err)}")
    for L in blg_err[:5]:
        log("   " + L[:110])

flush()
print("\nDONE. Full report: scripts/package1_fix2_report.txt")
