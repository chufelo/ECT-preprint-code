#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package 1 fix6 (session 2026-06-10). Re-application of the verified
fix5 edit set (fix5 aborted BEFORE write on an over-strict zero-check,
so the file is unchanged) with three corrections driven by the fix5
dumps:

  P  - the missing period after 'fixed independently by $\\alpha>\\beta$'
       is followed by a BLANK line + \\paragraph (the fix5 regex
       required an immediate capital letter). Now anchored exactly.
  D  - GPT's quoted DESI sentence does not exist verbatim; the real
       text (L25505) is '\\emph{strengthened}: $w_0w_a$CDM is preferred
       over...'. fix6 dumps +-15 lines, guards against table rows, and
       inserts a separate hedging sentence AFTER the sentence end:
       'This strengthening refers to the DESI Collaboration
       CPL-combined analyses; the interpretation remains dataset- and
       parametrisation-dependent~\\cite{Lodha2025}.' All original
       numbers/citations preserved.
  U^A - the second c_*^{-1}\\partial_t site is the pmatrix definition
       U^A := (c_*^{-1}\\partial_t Phi, \\partial_i Phi). Two readings:
       (a) leftover of the old w=c_*t convention -> should be
       \\partial_t Phi; (b) orthonormal-frame/SI component under
       ds^2 = -c_*^2 dt^2 + dx^2 (e_0 = c_*^{-1} d_t) -> CORRECT under
       t=w. Cannot be decided blindly: the site is HELD (dump +-20
       lines, WARN); any OTHER residual c_*^{-1}\\partial_t is fatal.

Everything else is byte-identical in intent to fix5 (T/B/K groups,
invariants, audits, backup, PROJECT_STRUCTURE patch, dot regeneration,
scipy/matplotlib probe - now meaningful after the user's pip
reinstall - and 4-pass compilation).
Idempotent: \\widehat K marker present -> dot+env+compile-only.
Backup: backup/ECT_preprint_BACKUP_v206_pre_package1_fix6.tex
Report: scripts/package1_fix6_report.txt
"""
import hashlib, re, shutil, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # .../LaTex
TEX  = BASE / "ECT_preprint.tex"
BAK  = BASE / "backup"
REP  = BASE / "scripts" / "package1_fix6_report.txt"
GV   = BASE / "scripts" / "fig_partI_derivation_logic.gv"
FIGD = BASE / "figures"
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
    fail("fix3 not applied. NOTHING modified.")

MARK_DONE = r"\widehat K(\bar\phi)"
edits_needed = MARK_DONE not in content
if not edits_needed:
    log("[gate] fix6 edits already present -> DOT+ENV+COMPILE-ONLY mode")
elif r"{K(\bar\phi)}{\beta_\phi^2 M_{\rm Pl}^2}" not in content:
    fail("fix4 not applied. NOTHING modified.")

def rep1(cid, old, new):
    global content
    n = content.count(old)
    if n != 1:
        fail(f"{cid}: anchor count={n} (expected 1): {old[:90]!r}")
    content = content.replace(old, new)
    log(f"[{cid}] 1 replacement")

def rep_all_ctx(cid, old, new, min_expected=1, note=""):
    global content
    positions = [m.start() for m in re.finditer(re.escape(old), content)]
    log(f"[{cid}] occurrences={len(positions)}{note}; contexts:")
    for p in positions:
        log("   | ..." + content[max(0, p-55):p+len(old)+28].replace("\n", "\\n") + "...")
    if len(positions) < min_expected:
        fail(f"{cid}: found {len(positions)}, expected >= {min_expected}: {old[:70]!r}")
    content = content.replace(old, new)
    log(f"[{cid}] {len(positions)} replacements")
    return len(positions)

def resubn(cid, pattern, newtext, expect):
    global content
    rx = re.compile(pattern)
    matches = list(rx.finditer(content))
    log(f"[{cid}] regex matches={len(matches)} (expected {expect}); contexts:")
    for m in matches:
        p = m.start()
        log("   | ..." + content[max(0, p-50):m.end()+55].replace("\n", "\\n") + "...")
    if len(matches) != expect:
        fail(f"{cid}: matches={len(matches)}, expected {expect}. NOTHING modified.")
    content, n = rx.subn(lambda m: newtext, content)
    log(f"[{cid}] {n} replacements")

def zero_regex(cid, pattern):
    rx = re.compile(pattern)
    matches = list(rx.finditer(content))
    if matches:
        log(f"[sanity-FAIL] {cid}: {len(matches)} residual match(es):")
        for m in matches[:10]:
            p = m.start()
            log("   | ..." + content[max(0, p-55):m.end()+60].replace("\n", "\\n") + "...")
        fail(f"sanity-zero-regex {cid}: {len(matches)} matches, expected 0")
    log(f"[sanity] zero-regex OK: {cid}")

nB = 0
if edits_needed:
    PRESERVED = [r"\beta^2/c_*", r"\beta\bar\Psi", r"\beta\,\bar\Psi", r"\alpha-\beta"]
    orig_inv = {p: content.count(p) for p in PRESERVED}
    for p in PRESERVED:
        log(f"[invariant] baseline count({p!r}) = {orig_inv[p]}")
    base_bp = content.count(chr(92) + 'beta_' + chr(92) + 'phi')
    log(f"[invariant] baseline beta_phi = {base_bp} (expected 148)")

    # ===================== GROUP T: time convention =====================
    RE_WID  = r"w\s*=\s*c_\*(?:\s|\\,)*t\b"
    RE_WICK = r"w_E\s*\\to\s*\\pm\s*i\s*c_\*\s*t"
    resubn("RT1-param-realtime",
           r"parametrised in real time by\s*\$w\s*=\s*c_\*\s*t\$",
           "parametrised by the ordered-branch time coordinate $t=w$", 2)
    resubn("RT2-sr-interval",
           r"Introducing the emergent time coordinate\s*\$w\s*=\s*c_\*\\,t\$~\\eqref\{eq:sr_cone\},",
           "Introducing the ordered-branch time coordinate $t=w$ (cone slope $c_*$; cf.~\\eqref{eq:sr_cone}),", 1)
    n3 = content.count("in units $c_*=1$, and")
    if n3 == 1:
        content = content.replace("in units $c_*=1$, and", "in matched units $c_*=1$, and")
        log("[RT3-matched-units] 1 replacement")
    else:
        log(f"[RT3-matched-units] SOFT skipped (count={n3})")
    resubn("RT4-dpartial",
           r"\$\\partial_w\s*=\s*c_\*\^\{-1\}\\partial_t\$\s*,\s*so",
           "$\\partial_w=\\partial_t$; the factor $1/c_*^2$ in the Lorentzian kinetic form below is supplied by the ordered-branch kinetic tensor rather than by a rescaling of the time coordinate, so", 1)
    resubn("RT5-wick-spaced", RE_WICK, "w_E \\to \\pm i\\,t", 3)

    # ===================== GROUP B: benchmark beta -> beta_phi ==========
    nB += rep_all_ctx("B1-beta08-inline", "$\\beta=0.8$", "$\\beta_\\phi=0.8$",
                      min_expected=3, note=" (expected ~4)")
    rep1("B2-beta08-display", "\\beta=0.8,\\qquad", "\\beta_\\phi=0.8,\\qquad"); nB += 1
    nB += rep_all_ctx("B3-A2-inline", "(6\\beta^2)", "(6\\beta_\\phi^2)")
    nB += rep_all_ctx("B4-A2-display", "{6\\beta^2}", "{6\\beta_\\phi^2}")
    nB += rep_all_ctx("B5-betaq", "|\\beta q|", "|\\beta_\\phi q|")
    rep1("B6-config-tuple", "$(\\beta,\\,\\mu,\\,\\kappa,\\,\\phi_0",
         "$(\\beta_\\phi,\\,\\mu,\\,\\kappa,\\,\\phi_0"); nB += 1
    rep1("B7-solver-list", "\\beta,\\qquad K_0,\\qquad m_\\phi,\\qquad V_0,",
         "\\beta_\\phi,\\qquad K_0,\\qquad m_\\phi,\\qquad V_0,"); nB += 1
    rep1("B8-window", "\\beta\\sim 0.7\\text{--}1.0",
         "\\beta_\\phi\\sim 0.7\\text{--}1.0"); nB += 1

    # ===================== GROUP K: dimensionally clean omega_BD ========
    rep1("K1-omegaBD",
         "\\omega_{\\rm BD} = \\frac{K(\\bar\\phi)}{\\beta_\\phi^2 M_{\\rm Pl}^2}\\,.",
         "\\omega_{\\rm BD} = \\frac{\\widehat K(\\bar\\phi)}{\\beta_\\phi^2}\\,, \\qquad \\widehat K(\\bar\\phi)\\equiv \\frac{K(\\bar\\phi)}{M_{\\rm Pl}^2}.")
    resubn("K2-Khat-prose",
           r"\\ll1\$, so\s*\$K\\approx1\$ and \$\\omega",
           "\\ll1$, the chosen normalisation gives $\\widehat K(\\bar\\phi)\\approx1$, so $\\omega", 1)

    # ===================== GROUP P: missing period ======================
    rep1("P-period",
         "independently by $\\alpha>\\beta$\n\n\\paragraph{Parameter-counting closure",
         "independently by $\\alpha>\\beta$.\n\n\\paragraph{Parameter-counting closure")

    # ===================== GROUP D: DESI DR2 scoping (real anchor) ======
    d_anchor = "\\emph{strengthened}: $w_0w_a$CDM is preferred over"
    nd = content.count(d_anchor)
    if nd != 1:
        log(f"[D-scoping] SOFT skipped (anchor count={nd}); lines with 'strengthened':")
        for i, L in enumerate(content.split("\n")):
            if "strengthened" in L:
                log(f"   L{i+1}: {L.strip()[:120]}")
    else:
        ia = content.find(d_anchor)
        ls = content.rfind("\n", 0, ia) + 1
        le = content.find("\n", ia)
        Lall = content.split("\n")
        ln = content.count("\n", 0, ia)
        lo, hi = max(0, ln-15), min(len(Lall), ln+16)
        log("[D-context] +-15 lines around the anchor:")
        for j in range(lo, hi):
            mark = ">>" if j == ln else "  "
            log(f"   {mark} L{j+1}: {Lall[j][:120]}")
        if "&" in content[ls:le]:
            log("[D-scoping] SOFT skipped (anchor sits inside a table row)")
        else:
            m = re.search(r"\.(?=\s+[A-Z])", content[ia:ia+700])
            if not m:
                m = re.search(r"\.(?=\s*\n)", content[ia:ia+700])
            if m:
                pos = ia + m.start() + 1
                hedge = (" This strengthening refers to the DESI Collaboration"
                         " CPL-combined analyses; the interpretation remains"
                         " dataset- and parametrisation-dependent~\\cite{Lodha2025}.")
                content = content[:pos] + hedge + content[pos:]
                log("[D-hedge] sentence inserted after the strengthened-claim sentence:")
                log("   | ..." + content[ia:pos+len(hedge)+2].replace("\n", "\\n") + "...")
            else:
                log("[D-hedge] SOFT skipped (no sentence end within 700 chars)")

    # ===================== sanity =======================================
    zero_regex("w-identification", RE_WID)
    zero_regex("wick-i-cstar-t", r"(?<![A-Za-z])i\s*c_\*(?:\s|\\,)*t\b")
    # --- conditional check for c_*^{-1}\partial_t: HELD pmatrix site ---
    rx = re.compile(r"c_\*\^\{-1\}\\partial_t")
    held, bad = [], []
    for m in rx.finditer(content):
        pre = content[max(0, m.start()-90):m.start()]
        (held if ("\\begin{pmatrix}" in pre or "U^A" in pre) else bad).append(m)
    if bad:
        log(f"[sanity-FAIL] stray c_*^-1 partial_t: {len(bad)}")
        for m in bad[:5]:
            p = m.start()
            log("   | ..." + content[max(0, p-60):m.end()+60].replace("\n", "\\n") + "...")
        fail("stray c_*^{-1}\\partial_t outside the HELD pmatrix site")
    log(f"[sanity] c_*^-1 partial_t: {len(held)} HELD pmatrix site(s), 0 stray (decision pending review)")
    Lall = content.split("\n")
    for m in held:
        ln = content.count("\n", 0, m.start())
        lo, hi = max(0, ln-20), min(len(Lall), ln+21)
        log("[HELD-UA-dump] +-20 lines:")
        for j in range(lo, hi):
            mark = ">>" if j == ln else "  "
            log(f"   {mark} L{j+1}: {Lall[j][:120]}")
    zero_regex("beta=0.8", r"\\beta\s*=\s*0\.8")
    zero_regex("beta~0.7", r"\\beta\s*\\sim\s*0\.7")
    for pat in ["6\\beta^2", "|\\beta q|", "$(\\beta,\\,",
                "\\beta,\\qquad K_0",
                "e^{\\beta\\phi", "e^{-\\beta\\phi", "e^{2\\beta\\phi",
                "\\beta \\phi", "\\beta\\phi", "\\beta e^{", "(1+\\beta q)",
                "t=w/c_*", "\\frac{1}{\\beta}\\ln", "\\beta^{-1}\\ln"]:
        nz = content.count(pat)
        if nz != 0:
            log(f"[sanity-FAIL] count({pat!r})={nz}; contexts:")
            for m in list(re.finditer(re.escape(pat), content))[:10]:
                p = m.start()
                log("   | ..." + content[max(0, p-55):p+75].replace("\n", "\\n") + "...")
            fail(f"sanity-zero: count({pat!r})={nz}, expected 0")
    log("[sanity] all literal zero-checks OK")
    nk = content.count("$K\\approx1$")
    if nk:
        log(f"[sanity-WARN] residual '$K\\approx1$' count={nk} (review-only)")
    for p in PRESERVED:
        nz = content.count(p)
        if nz != orig_inv[p]:
            fail(f"sanity-invariant: count({p!r})={nz}, baseline {orig_inv[p]} - edits leaked")
        log(f"[sanity] invariant OK: {p!r} = {nz} (unchanged)")
    nbp = content.count(chr(92) + 'beta_' + chr(92) + 'phi')
    exp_bp = base_bp + nB
    log(f"[sanity] beta_phi total now: {nbp} (expected {exp_bp} = {base_bp} + {nB})")
    if nbp != exp_bp:
        fail(f"beta_phi count mismatch: {nbp} != {exp_bp}")

    lines = content.split("\n")
    has_b  = [("\\beta" in L) and ("\\beta_\\phi" not in L) and ("\\beta_5" not in L) for L in lines]
    has_bp = ["\\beta_\\phi" in L for L in lines]
    sus = [(i+1, lines[i].strip()[:110]) for i in range(len(lines))
           if has_b[i] and any(has_bp[max(0, i-2):i+3])]
    log(f"[audit-1] mixed beta/beta_phi neighbourhoods: {len(sus)} (expected 1; non-fatal)")
    for ln, txt in sus[:40]:
        log(f"   L{ln}: {txt}")
    tok = "$\\beta$"
    hits = [(i+1, L.strip()[:110]) for i, L in enumerate(lines) if tok in L]
    log(f"[audit-2] lines containing solitary {tok!r}: {len(hits)} (expected 16; review-only)")
    for ln, txt in hits[:50]:
        log(f"   L{ln}: {txt}")

    # ================= write (backup first) =============================
    BAK.mkdir(exist_ok=True)
    bak = BAK / "ECT_preprint_BACKUP_v206_pre_package1_fix6.tex"
    if bak.exists():
        fail(f"backup already exists: {bak.name}. NOTHING modified.")
    shutil.copy2(TEX, bak)
    log(f"[backup] backup/{bak.name} created")
    TEX.write_text(content, encoding="utf-8")
    log(f"[write] ECT_preprint.tex written ({len(content)} chars)")
    flush()

    # ---- PROJECT_STRUCTURE.md status patch (soft) ----
    try:
        PS = BASE / "PROJECT_STRUCTURE.md"
        ps = PS.read_text(encoding="utf-8")
        a = "resolved by fix4 (\u03b2_\u03c6; formula + prose sites)."
        add = (" fix5/6 (GPT post-review): 7 spaced time-convention residuals "
               "(w=c_* t parametrisations \u00d72, w=c_*\\,t interval, Wick i c_* t \u00d73, "
               "\u2202_w=c_*^{-1}\u2202_t derivation route), 11 late-time benchmark "
               "\u03b2\u2192\u03b2_\u03c6 sites, dimensionally clean \u03c9_BD=K\u0302/\u03b2_\u03c6\u00b2 "
               "with K\u0302\u2261K/M_Pl\u00b2, period after \u03b1>\u03b2, DESI DR2 'strengthened' "
               "claim scoped to CPL-combined analyses (+cite Lodha2025), skyrmion node "
               "'(legacy; secondary-sector route open)' (self-edited .gv). "
               "HELD pending review: U^A pmatrix component c_*^{-1}\u2202_t\u03a6 "
               "(orthonormal-frame vs legacy-convention reading; dump in fix6 report).")
        if a in ps and "fix5/6 (GPT post-review)" not in ps:
            ps = ps.replace(a, a + add, 1)
            PS.write_text(ps, encoding="utf-8")
            log("[structure] PROJECT_STRUCTURE.md fix5/6 note appended")
        else:
            log("[structure] skipped (anchor absent or already patched)")
    except Exception as e:
        log(f"[structure] FAILED (non-fatal): {e}")
    flush()

# ================= dot regeneration (both modes) =====================
try:
    gv_text = GV.read_text(encoding="utf-8")
    log("[gv] '(legacy' present" if "(legacy" in gv_text else "[gv-WARN] '(legacy' NOT found")
    for fmt, out in [("pdf", FIGD / "fig_partI_derivation_logic.pdf"),
                     ("png", FIGD / "fig_partI_derivation_logic.png")]:
        r = subprocess.run([DOT, f"-T{fmt}", str(GV), "-o", str(out)],
                           capture_output=True, timeout=120)
        err = (r.stderr or b"").decode("utf-8", "ignore").strip().splitlines()
        log(f"[dot -T{fmt}] rc={r.returncode} {err[0][:90] if err else ''}")
except Exception as e:
    log(f"[dot] FAILED: {e}")
flush()

# ================= env probe (post pip reinstall) ====================
for mod in ["numpy", "scipy", "matplotlib"]:
    try:
        r = subprocess.run([sys.executable, "-c", f"import {mod} as m; print('{mod}', m.__version__)"],
                           capture_output=True, timeout=120)
        if r.returncode == 0:
            log(f"[env] {mod}: OK  {(r.stdout or b'').decode('utf-8','ignore').strip()}")
        else:
            tb = (r.stderr or b"").decode("utf-8", "ignore").strip().splitlines()
            log(f"[env] {mod}: FAILED rc={r.returncode}; traceback tail:")
            for L in tb[-12:]:
                log("   " + L[:120])
    except Exception as e:
        log(f"[env] {mod}: PROBE FAILED {e}")
flush()

# ================= 4-pass compilation ================================
def run(cmd):
    r = subprocess.run(cmd, cwd=str(BASE),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=2400)
    return r.returncode

log("[compile] pdflatex -> bibtex -> pdflatex -> pdflatex")
try:
    rcs = [run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]),
           run([BIBTEX, "ECT_preprint"]),
           run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]),
           run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"])]
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
print("\nDONE. Full report: scripts/package1_fix6_report.txt")
