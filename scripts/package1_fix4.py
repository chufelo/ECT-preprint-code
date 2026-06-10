#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package 1 fix4 (session 2026-06-10). FINAL micro-pass of the sanctioned
P1-4 rename + environment probe.

  C1 (resolved HELD, formula site L55353 - found ONLY via the fix3
      context dump, invisible to all token/neighbour audits):
      \\omega_{BD} = K(\\bar\\phi)/(\\beta^2 M_Pl^2)  ->  \\beta_\\phi^2.
      Dimensional analysis: \\bar\\phi ~ 0.03-0.08 is the dimensionless
      amplitude variable, hence [K]=M^2 and the beta in the formula is
      dimensionless => the amplitude-curvature coupling beta_phi
      (f = Mbar_Pl^2 e^{beta_phi phi}, f' = beta_phi f =>
      omega_BD = K f/f'^2 ~ K/(beta_phi^2 M_Pl^2) at phi << 1).
  C2 (resolved HELD, prose site L55356):
      'for Planck-suppressed $\\beta$,' -> '$\\beta_\\phi$,'.
  FLAGGED, NOT edited (needs separate sanction - physics prose, not a
  rename): 'K ~ 1' in the same sentence is dimensionally sloppy
  ([K]=M^2; cleaner: K/Mbar_Pl^2 ~ 1). Registered for a future pass.

  CLASS-CLOSURE AUDITS (review-only): full dumps of \\beta^2 and of
  beta-adjacent-to-Planck-mass patterns, to certify that no further
  coupling-beta sites of this shape remain.

  ENV PROBE (non-fatal): python/numpy/scipy/matplotlib/sympy versions,
  dot -V, pdflatex, git, github_repo HEAD + dirty count.

  PROJECT_STRUCTURE.md: HELD wording updated to 'resolved' (soft
  anchored patches).

Idempotent: if C1 already applied -> env+compile-only mode.
Abort-before-write. Backup:
backup/ECT_preprint_BACKUP_v205_pre_package1_fix4.tex
Report: scripts/package1_fix4_report.txt
"""
import hashlib, re, shutil, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # .../LaTex
TEX  = BASE / "ECT_preprint.tex"
BAK  = BASE / "backup"
REP  = BASE / "scripts" / "package1_fix4_report.txt"
PDFLATEX = "/Library/TeX/texbin/pdflatex"
BIBTEX   = "/Library/TeX/texbin/bibtex"
DOT      = "/opt/homebrew/bin/dot"
REPO     = BASE.parent / "github_repo"

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

if r"\beta_\phi^{-1}\ln(u/u_\infty)" not in content:
    fail("fix3 not applied (A1 marker missing). Run package1_fix3.py first. NOTHING modified.")

NEW_C1 = r"{K(\bar\phi)}{\beta_\phi^2 M_{\rm Pl}^2}"
edits_needed = NEW_C1 not in content
if not edits_needed:
    log("[gate] fix4 edits already present -> ENV+COMPILE-ONLY mode")

if edits_needed:
    PRESERVED = [r"\beta^2/c_*", r"\beta\bar\Psi", r"\beta\,\bar\Psi", r"\alpha-\beta"]
    orig_inv = {p: content.count(p) for p in PRESERVED}
    for p in PRESERVED:
        log(f"[invariant] baseline count({p!r}) = {orig_inv[p]}")

    # ---- C1: omega_BD formula (resolved HELD, formula site) ----
    OLD_C1 = r"{K(\bar\phi)}{\beta^2 M_{\rm Pl}^2}"
    n = content.count(OLD_C1)
    if n != 1:
        fail(f"C1: count={n}, expected 1. NOTHING modified.")
    content = content.replace(OLD_C1, NEW_C1)
    log("[C1-omegaBD-formula] 1 replacement")

    # ---- C2: prose site (resolved HELD) ----
    OLD_C2 = "for Planck-suppressed $\\beta$,"
    n = content.count(OLD_C2)
    if n != 1:
        fail(f"C2: count={n}, expected 1. NOTHING modified.")
    content = content.replace(OLD_C2, "for Planck-suppressed $\\beta_\\phi$,")
    log("[C2-prose] 1 replacement")

    # ---- class-closure audits (review-only) ----
    pat = r"\beta^2"
    positions = [m.start() for m in re.finditer(re.escape(pat), content)]
    log(f"[class-audit] count({pat!r}) = {len(positions)} (review-only; expected: 9 kinetic det-K + renamed-beta_phi sites do not match this pattern)")
    for p in positions[:25]:
        log("   | ..." + content[max(0, p-50):p+45].replace("\n", "\\n") + "...")
    for pat in [r"\beta M_", r"\beta\,M_", r"\beta \bar M", r"\beta\bar M", r"\beta\,\bar M"]:
        positions = [m.start() for m in re.finditer(re.escape(pat), content)]
        log(f"[class-audit] count({pat!r}) = {len(positions)} (review-only)")
        for p in positions[:5]:
            log("   | ..." + content[max(0, p-50):p+45].replace("\n", "\\n") + "...")

    # ================= sanity (self-diagnosing) =================
    zero_checks = [
        r"{K(\bar\phi)}{\beta^2", r"\beta^2 M_{\rm Pl}",
        "for Planck-suppressed $\\beta$,",
        r"\beta^{-1}\ln", r"\frac{1}{\beta}\ln", r"\beta(\phi')",
        r"e^{\beta\phi", r"e^{-\beta\phi", r"e^{2\beta\phi",
        r"\beta \phi", r"\beta\phi",
        r"\beta e^{", r"\beta^2 e^{", r"(1+\beta q)",
        "t=w/c_*",
    ]
    for pat in zero_checks:
        nz = content.count(pat)
        if nz != 0:
            log(f"[sanity-FAIL] count({pat!r})={nz}; contexts:")
            for m in list(re.finditer(re.escape(pat), content))[:10]:
                p = m.start()
                log("   | ..." + content[max(0, p-55):p+75].replace("\n", "\\n") + "...")
            fail(f"sanity-zero: count({pat!r})={nz}, expected 0")
    log("[sanity] all zero-checks OK")
    for p in PRESERVED:
        nz = content.count(p)
        if nz != orig_inv[p]:
            fail(f"sanity-invariant: count({p!r})={nz}, baseline {orig_inv[p]} - edits leaked")
        log(f"[sanity] invariant OK: {p!r} = {nz} (unchanged)")
    nbp = content.count(chr(92) + 'beta_' + chr(92) + 'phi')
    log(f"[sanity] beta_phi total occurrences now: {nbp} (expected 148 = 146 + 2)")

    # ---- audit 1 re-run ----
    lines = content.split("\n")
    has_b  = [("\\beta" in L) and ("\\beta_\\phi" not in L) and ("\\beta_5" not in L) for L in lines]
    has_bp = ["\\beta_\\phi" in L for L in lines]
    sus = [(i+1, lines[i].strip()[:110]) for i in range(len(lines))
           if has_b[i] and any(has_bp[max(0, i-2):i+3])]
    log(f"[audit-1] mixed beta/beta_phi neighbourhoods: {len(sus)} (expected 1 = definitional note; non-fatal)")
    for ln, txt in sus[:40]:
        log(f"   L{ln}: {txt}")

    # ---- audit 2 re-run (review-only) ----
    tok = "$\\beta$"
    hits = [(i+1, L.strip()[:110]) for i, L in enumerate(lines) if tok in L]
    log(f"[audit-2] lines containing solitary {tok!r}: {len(hits)} (expected 16; review-only)")
    for ln, txt in hits[:50]:
        log(f"   L{ln}: {txt}")

    # ================= write (backup first) =================
    BAK.mkdir(exist_ok=True)
    bak = BAK / "ECT_preprint_BACKUP_v205_pre_package1_fix4.tex"
    if bak.exists():
        fail(f"backup already exists: {bak.name} - refusing to overwrite. NOTHING modified.")
    shutil.copy2(TEX, bak)
    log(f"[backup] backup/{bak.name} created")
    TEX.write_text(content, encoding="utf-8")
    log(f"[write] ECT_preprint.tex written ({len(content)} chars)")
    flush()

# ================= PROJECT_STRUCTURE.md HELD-status patch (soft) =====
PS = BASE / "PROJECT_STRUCTURE.md"
try:
    ps = PS.read_text(encoding="utf-8")
    changed = False
    PS1_OLD = "dumped by fix3 for a post-run decision."
    PS1_NEW = ("dumped by fix3 and resolved by fix4: identified as $\\beta_\\phi$ by dimensional analysis "
               "($\\bar\\phi$ dimensionless, $[K]=M^2$ \u21d2 dimensionless coupling); both sites (formula "
               "$\\omega_{\\rm BD}=K/(\\beta_\\phi^2 M_{\\rm Pl}^2)$ + prose) renamed. Flagged for a future "
               "sanctioned micro-pass: '$K\\approx1$' in `app:cluster_slip` is dimensionally sloppy "
               "(cleaner: $K/\\bar M_{\\rm Pl}^2\\approx1$).")
    if ps.count(PS1_OLD) == 1:
        ps = ps.replace(PS1_OLD, PS1_NEW)
        changed = True
    else:
        log(f"[structure-WARN] PS1 anchor count={ps.count(PS1_OLD)} - skipped")
    PS2_OLD = "decision after fix3 dump."
    PS2_NEW = "resolved by fix4 (\u03b2_\u03c6; formula + prose sites)."
    if ps.count(PS2_OLD) == 1:
        ps = ps.replace(PS2_OLD, PS2_NEW)
        changed = True
    else:
        log(f"[structure-WARN] PS2 anchor count={ps.count(PS2_OLD)} - skipped")
    if changed:
        PS.write_text(ps, encoding="utf-8")
        log("[structure] PROJECT_STRUCTURE.md HELD-status updated to resolved")
    else:
        log("[structure] no changes applied (anchors absent or already updated)")
except Exception as e:
    log(f"[structure] FAILED (non-fatal): {e}")
flush()

# ================= ENVIRONMENT PROBE (non-fatal) =====================
def probe(cmd, label, prefer_stderr=False, timeout=90):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        out = (r.stderr if prefer_stderr else r.stdout) or b""
        if not out.strip():
            out = (r.stdout or b"") + (r.stderr or b"")
        line = out.decode("utf-8", "ignore").strip().splitlines()
        log(f"[env] {label}: rc={r.returncode}  {line[0][:110] if line else '(no output)'}")
    except Exception as e:
        log(f"[env] {label}: FAILED  {e}")

log(f"[env] sys.executable = {sys.executable}")
probe([sys.executable, "--version"], "python")
probe([sys.executable, "-c", "import numpy as n; print('numpy', n.__version__)"], "numpy")
probe([sys.executable, "-c", "import scipy as s; print('scipy', s.__version__)"], "scipy")
probe([sys.executable, "-c", "import matplotlib as m; print('matplotlib', m.__version__)"], "matplotlib")
probe([sys.executable, "-c", "import sympy as y; print('sympy', y.__version__)"], "sympy")
probe([DOT, "-V"], "graphviz dot", prefer_stderr=True)
probe([PDFLATEX, "--version"], "pdflatex")
probe(["git", "--version"], "git")
probe(["git", "-C", str(REPO), "log", "--oneline", "-1"], "github_repo HEAD")
try:
    r = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"],
                       capture_output=True, timeout=90)
    nn = len([l for l in r.stdout.decode("utf-8", "ignore").splitlines() if l.strip()])
    log(f"[env] github_repo dirty/untracked entries: {nn}")
except Exception as e:
    log(f"[env] github_repo status: FAILED  {e}")
flush()

# ================= 4-pass compilation (both modes) ===================
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

logtxt = (BASE / "ECT_preprint.log").read_bytes().decode("utf-8", errors="ignore")
err_lines = [L for L in logtxt.splitlines() if L.startswith("!")]
nundef_ref = logtxt.count("Warning: Reference")
nundef_cit = logtxt.count("Warning: Citation")
nmult = logtxt.count("multiply defined") + logtxt.count("multiply-defined")
mpages = re.search(r"Output written on ECT_preprint\.pdf \((\d+) pages", logtxt)
log(f"[compile] hard errors (^!): {len(err_lines)}")
for L in err_lines[:10]:
    log("   ! " + L[:110])
log(f"[compile] undefined references: {nundef_ref}; undefined citations: {nundef_cit}; multiply-defined: {nmult}")
log(f"[compile] PAGES: {mpages.group(1) if mpages else 'NOT FOUND'} (was 742)")

blg = BASE / "ECT_preprint.blg"
if blg.exists():
    blgtxt = blg.read_bytes().decode("utf-8", errors="ignore")
    blg_err = [L for L in blgtxt.splitlines() if "rror" in L]
    log(f"[bibtex] .blg error-lines: {len(blg_err)}")
    for L in blg_err[:5]:
        log("   " + L[:110])

flush()
print("\nDONE. Full report: scripts/package1_fix4_report.txt")
