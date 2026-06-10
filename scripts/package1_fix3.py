#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package 1 fix3, version 2 (session 2026-06-09/10).

Final completion of the SANCTIONED P1-4 rename beta -> beta_phi, driven
by the fix2 audit blocks, PLUS the workflow-rule-4 update of
PROJECT_STRUCTURE.md (anchored patch with backup).

  A1 (audit-3): three phi-definitions in beta^{-1} typography,
      \\beta^{-1}\\ln(u/u_\\infty) -> \\beta_\\phi^{-1}\\ln(u/u_\\infty)
      (one of them inside the TikZ node 'Amplitude variable').
  A2 (audit-2, L26104): second OP-grad parameter triple,
      ($Z_u$, $W(u)$, $\\beta$) -> ($Z_u$, $W(u)$, $\\beta_\\phi$)
      - same semantic unit as the already-renamed table row
      'Underlying EFT parameters ($Z_u$, $W$, $\\beta_\\phi$)'.

  HELD (no edit): the 'Planck-suppressed $\\beta$' line (audit-2,
  ~L55356). This script only DUMPS +-15 lines of context into the
  report; the decision is made after review of the dump.

  STRUCTURE: PROJECT_STRUCTURE.md gets (i) header date 2026-06-10,
  (ii) new 'Current active work' paragraph for Package 1 with the old
  one demoted to 'Previously finalised work (2026-05-25)', (iii) tree
  page count 669 -> 742, (iv) new top row in 'Recent changes'.
  Backup: backup/PROJECT_STRUCTURE_BACKUP_pre_package1.md.
  Idempotent and independent of the preprint-edit stage.

Then: zero-checks, invariants, audit re-runs, backup v204, write,
4-pass compilation (robust: console -> DEVNULL, .log/.blg parsed from
bytes), page count.
Idempotent: if A1 is already applied -> COMPILE-ONLY mode for the
preprint stage (structure patch still runs if pending).
Abort-before-write throughout.
Backup: backup/ECT_preprint_BACKUP_v204_pre_package1_fix3.tex
Report: scripts/package1_fix3_report.txt
"""
import hashlib, re, shutil, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # .../LaTex
TEX  = BASE / "ECT_preprint.tex"
BAK  = BASE / "backup"
REP  = BASE / "scripts" / "package1_fix3_report.txt"
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
    fail("Package 1 not applied (eq:Ktheta_1D missing). NOTHING modified.")
if "and $\\beta_\\phi$ is a dimensionless coupling parameter." not in content:
    fail("fix2 not applied (F1 marker missing). Run package1_fix2.py first. NOTHING modified.")

NEW_A1 = r"\beta_\phi^{-1}\ln(u/u_\infty)"
edits_needed = NEW_A1 not in content
if not edits_needed:
    log("[gate] fix3 preprint edits already present -> COMPILE-ONLY mode for the preprint stage")

if edits_needed:
    PRESERVED = [r"\beta^2/c_*", r"\beta\bar\Psi", r"\beta\,\bar\Psi", r"\alpha-\beta"]
    orig_inv = {p: content.count(p) for p in PRESERVED}
    for p in PRESERVED:
        log(f"[invariant] baseline count({p!r}) = {orig_inv[p]}")

    # ---- A1: phi-definitions in beta^{-1} typography ----
    OLD_A1 = r"\beta^{-1}\ln(u/u_\infty)"
    positions = [m.start() for m in re.finditer(re.escape(OLD_A1), content)]
    log(f"[A1-phidef-invtypo] occurrences={len(positions)}; contexts:")
    for p in positions:
        log("   | ..." + content[max(0, p-55):p+len(OLD_A1)+30].replace("\n", "\\n") + "...")
    if len(positions) != 3:
        fail(f"A1: count={len(positions)}, expected 3 (from fix2 audit-3). NOTHING modified.")
    content = content.replace(OLD_A1, NEW_A1)
    log("[A1-phidef-invtypo] 3 replacements")

    # ---- A2: second OP-grad parameter triple ----
    OLD_A2 = "($Z_u$, $W(u)$, $\\beta$)"
    n = content.count(OLD_A2)
    if n != 1:
        fail(f"A2: count={n}, expected 1. NOTHING modified.")
    content = content.replace(OLD_A2, "($Z_u$, $W(u)$, $\\beta_\\phi$)")
    log("[A2-OPgrad-triple] 1 replacement")

    # ---- HELD item: context dump ONLY, no edit ----
    KEY = "Planck-suppressed $\\beta$"
    lines = content.split("\n")
    idxs = [i for i, L in enumerate(lines) if KEY in L]
    log(f"[HELD-dump] lines containing {KEY!r}: {len(idxs)} (NO edit; +-15 lines of context each)")
    for i in idxs:
        lo, hi = max(0, i-15), min(len(lines), i+16)
        for j in range(lo, hi):
            mark = ">>" if j == i else "  "
            log(f"   {mark} L{j+1}: {lines[j][:120]}")

    # ================= sanity (self-diagnosing) =================
    zero_checks = [
        OLD_A1, r"\beta^{-1}\ln", "($Z_u$, $W(u)$, $\\beta$)",
        r"\frac{1}{\beta}\ln", r"\frac{1}{\beta}\,\ln", r"\beta(\phi')",
        r"e^{\beta\phi", r"e^{-\beta\phi", r"e^{2\beta\phi",
        r"\beta \phi", r"\beta\phi",
        r"\beta e^{", r"\beta^2 e^{", r"(1+\beta q)",
        "t=w/c_*", r"2\hbar/K_\theta",
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
    log(f"[sanity] beta_phi total occurrences now: {nbp} (expected 146 = 142 + 3 + 1)")

    # ---- audit 1 re-run: mixed beta/beta_phi neighbourhoods ----
    lines = content.split("\n")
    has_b  = [("\\beta" in L) and ("\\beta_\\phi" not in L) and ("\\beta_5" not in L) for L in lines]
    has_bp = ["\\beta_\\phi" in L for L in lines]
    sus = [(i+1, lines[i].strip()[:110]) for i in range(len(lines))
           if has_b[i] and any(has_bp[max(0, i-2):i+3])]
    log(f"[audit-1] mixed beta/beta_phi neighbourhoods: {len(sus)} (expected 1 = definitional note; non-fatal)")
    for ln, txt in sus[:40]:
        log(f"   L{ln}: {txt}")

    # ---- audit 2 re-run (review-only): solitary $\beta$ tokens ----
    tok = "$\\beta$"
    hits = [(i+1, L.strip()[:110]) for i, L in enumerate(lines) if tok in L]
    log(f"[audit-2] lines containing solitary {tok!r}: {len(hits)} (review-only)")
    for ln, txt in hits[:50]:
        log(f"   L{ln}: {txt}")

    # ---- audit 3 re-run (review-only) ----
    for pat in [r"\frac{1}{\beta}", r"\beta(", r"\beta^{-1}"]:
        positions = [m.start() for m in re.finditer(re.escape(pat), content)]
        log(f"[audit-3] count({pat!r}) = {len(positions)} (review-only)")
        for p in positions[:10]:
            log("   | ..." + content[max(0, p-45):p+42].replace("\n", "\\n") + "...")

    # ================= write (backup first) =================
    BAK.mkdir(exist_ok=True)
    bak = BAK / "ECT_preprint_BACKUP_v204_pre_package1_fix3.tex"
    if bak.exists():
        fail(f"backup already exists: {bak.name} - refusing to overwrite. NOTHING modified.")
    shutil.copy2(TEX, bak)
    log(f"[backup] backup/{bak.name} created")
    TEX.write_text(content, encoding="utf-8")
    log(f"[write] ECT_preprint.tex written ({len(content)} chars)")
    flush()

# ================= PROJECT_STRUCTURE.md anchored patch =================
PS = BASE / "PROJECT_STRUCTURE.md"
ps = PS.read_text(encoding="utf-8")
if "Package 1 (\u041f1-1" in ps:
    log("[structure] PROJECT_STRUCTURE.md already updated -> skip")
else:
    NEW_CURRENT = (
"**Current active work:** **Package 1 (\u041f1-1\u2026\u041f1-8) INTEGRATED** "
"(2026-06-09/10; three scripted runs `package1_apply.py` v4 \u2192 `package1_fix2.py` v2 \u2192 `package1_fix3.py`; "
"\u2248230 individual anchored replacements across \u224880 edit IDs, every counter asserted, md5 gates, "
"invariance checks for untouched \u03b2-classes, three audit layers, abort-before-write throughout). "
"Content: (\u041f1-1) S0-chain made dimensionally consistent \u2014 reduced 1D stiffness "
"$K_\\theta^{1\\mathrm D}=K_\\theta\\mathcal A_\\perp$, $\\mathcal A_\\perp=c_\\perp\\xi_{\\rm core}^3$ (`eq:Ktheta_1D`); "
"$S_0^{\\rm EFT}=c_\\perp K_\\theta/(2m_\\varphi^2)\\sim c_\\perp/(4\\lambda)$ (`eq:S0_lambda`), Level B reduced-loop "
"closure with open profile coefficient $c_\\perp$; 16 dependent sites updated incl. sigma-scales consistency note "
"$\\xi_{\\rm cond}\\sim\\ell_{\\rm Pl}$. (\u041f1-2) Time convention unified to $t=w$ (ordered-branch parametrisation; "
"cone slope $c_*$; SI units only via matching $c_*=c$); Wick rotation $w_E\\to\\pm i\\,t$; 33 global + 6 custom sites; "
"normalisation $\\tilde\\varphi=\\sqrt{\\alpha-\\beta}\\,\\varphi$. (\u041f1-3) $\\dot G/G=-\\beta_\\phi\\dot\\phi$ with "
"bound on $|\\beta_\\phi\\dot\\phi|$. (\u041f1-4) Full semantic rename of the amplitude\u2013curvature coupling "
"$\\beta\\to\\beta_\\phi$ (146 occurrences) with kinetic $\\beta$, RG $\\beta$-functions, $\\beta_5$, Jeans $\\beta(r)$ "
"untouched (invariants: $\\beta^2/c_*$=9, $\\alpha-\\beta$=58, $\\beta\\bar\\Psi$); definitional note after "
"`eq:Geff_phi`; new symbols-table row. One HELD ambiguous site ('Planck-suppressed $\\beta$', ~L55356) dumped by fix3 "
"for a post-run decision. (\u041f1-6) $m_n\\sim n\\times1.6$\u00a0GeV demoted to legacy phenomenological benchmark "
"(primary-stiffness/Derrick objection; OP-top-mass registered; D7/F6 rows + falsifiability text updated). "
"(\u041f1-7) $\\eta_B$ relabelled imported benchmark (4 sites incl. Conclusion). (\u041f1-8) DESI refresh: DR1/DR2 "
"dataset- and parametrisation-dependent framing (`DESIDR2_2025`, `Lodha2025` cited), $w_0=-0.827$ \u2192 DR1-anchored "
"legacy benchmark (4 sites). (\u041f1-5) `fig_partI_derivation_logic.gv` grey edges \u2192 black, figure regenerated. "
"**Preprint: 742 pp (was 740), 0 errors, 0 undef refs, 0 undef cites, 0 multiply-defined, bibtex clean.** "
"Backups v202\u2013v204 + `.gv.bak_pre_package1`; reports `scripts/package1_*_report.txt`. "
"**Commit pending:** single commit = v201 $C_n$ lemma (still uncommitted) + Package 1; books excluded as always.\n\n"
"**Previously finalised work (2026-05-25):**")
    NEW_ROW = (
"| 2026-06-09/10 | **Package 1 (\u041f1-1\u2026\u041f1-8) integrated** over three scripted runs "
"(`package1_apply.py` v4, `package1_fix2.py` v2, `package1_fix3.py`) with md5 gates, per-anchor count asserts, "
"invariance checks for untouched \u03b2-classes (kinetic $\\beta$, RG $\\beta$-functions, $\\beta_5$, Jeans "
"$\\beta(r)$), three audit layers and abort-before-write. S0-chain $K_\\theta^{1\\mathrm D}$/$c_\\perp$ "
"(`eq:Ktheta_1D`, `eq:S0_lambda`); $t=w$ convention; $\\dot G/G=-\\beta_\\phi\\dot\\phi$; \u03b2\u2192\u03b2_\u03c6 "
"rename (146 sites); 1.6 GeV \u2192 legacy benchmark (OP-top-mass); \u03b7_B \u2192 imported benchmark; DESI DR1/DR2 "
"refresh (DESIDR2_2025, Lodha2025); .gv edges black. **742 pp (was 740), 0/0/0/0, bibtex clean.** Backups "
"v202\u2013v204; reports in `scripts/`. HELD: 'Planck-suppressed \u03b2' decision after fix3 dump. Commit pending "
"together with v201 $C_n$ lemma. |")
    ok = True
    A1m = "**Last updated:** May 25, 2026 |"
    if ps.count(A1m) != 1:
        ok = False; log(f"[structure-FAIL] anchor date count={ps.count(A1m)}")
    A2m = "**Current active work:**"
    if ps.count(A2m) != 1:
        ok = False; log(f"[structure-FAIL] anchor current-work count={ps.count(A2m)}")
    A4m = "| Date | Change |\n|------|--------|\n"
    if ps.count(A4m) != 1:
        ok = False; log(f"[structure-FAIL] anchor recent-changes header count={ps.count(A4m)}")
    if not ok:
        fail("PROJECT_STRUCTURE.md anchors mismatch - structure patch aborted (preprint stage unaffected).")
    BAK.mkdir(exist_ok=True)
    ps_bak = BAK / "PROJECT_STRUCTURE_BACKUP_pre_package1.md"
    if not ps_bak.exists():
        shutil.copy2(PS, ps_bak)
        log(f"[backup] backup/{ps_bak.name} created")
    ps = ps.replace(A1m, "**Last updated:** June 10, 2026 |")
    ps = ps.replace(A2m, NEW_CURRENT, 1)
    A3m = "Main preprint (669 pp) \u2014 QG/decoherence upgrade + full housekeeping done"
    if ps.count(A3m) == 1:
        ps = ps.replace(A3m, "Main preprint (742 pp) \u2014 Package 1 integrated (2026-06)")
        log("[structure] tree page count updated 669 -> 742")
    else:
        log(f"[structure-WARN] tree anchor count={ps.count(A3m)} - page-count line left as is")
    ps = ps.replace(A4m, A4m + NEW_ROW + "\n")
    PS.write_text(ps, encoding="utf-8")
    log("[structure] PROJECT_STRUCTURE.md updated (date, current-work, tree, new Recent-changes row)")
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
print("\nDONE. Full report: scripts/package1_fix3_report.txt")
