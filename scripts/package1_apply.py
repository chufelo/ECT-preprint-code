#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package 1 (P1-1..P1-8) anchor-based application script for ECT_preprint.tex
Session 2026-06-09. Incorporates GPT clarifications 1-8.
v2: GV step idempotent.
v3: B7 per-site verification (94 lines / 95 occurrences resolved).
v4: (a) Sanity 'preserved' patterns now checked as BEFORE/AFTER INVARIANTS
    (baseline captured from the original file) instead of hard-coded
    absolute counts - eliminates the grep-c/lines-vs-occurrences error
    class entirely (v3 died on beta^2/c_* == 1 while the file legitimately
    contains 9 untouched kinetic det-K instances).
    (b) CRITICAL completion of the beta_phi semantic pass: the v3 context
    dump revealed bare coupling-beta PREFIXES in the background Friedmann/
    scalar equations that no previous pattern covered:
    \\beta e^{\\beta\\phi} (x5), \\beta^2 e^{\\beta\\phi} (x1),
    (1+\\beta q) (non-(k)), (so that $f' = \\beta...), and the definition
    \\frac{1}{\\beta}\\ln(u/u_\\infty). These are now renamed (B6a-B6e).
    Completeness of the x5/x1 counts is guaranteed: each such prefix
    contains e^{\\beta\\phi} and therefore necessarily appeared in the
    full 95-site dump.
    (c) New zero-checks for residual bare prefixes; non-fatal post-audit
    of mixed beta/beta_phi neighbourhoods written to the report.
Design: ALL edits applied in memory; file written ONLY if every HARD
assert passes. Backups created before any write. Full report written to
scripts/package1_apply_report.txt.
"""
import hashlib, shutil, subprocess, sys, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # .../LaTex
TEX  = BASE / "ECT_preprint.tex"
GV   = BASE / "scripts" / "fig_partI_derivation_logic.gv"
FIGD = BASE / "figures"
BAK  = BASE / "backup"
REP  = BASE / "scripts" / "package1_apply_report.txt"
EXPECTED_MD5 = "4c5c4f8bbda1bf73beautiful"  # placeholder replaced below
EXPECTED_MD5 = "4c5c4f8bbda1bf73023b72bb1f005144"
DOT = "/opt/homebrew/bin/dot"
PDFLATEX = "/Library/TeX/texbin/pdflatex"
BIBTEX = "/Library/TeX/texbin/bibtex"

log_lines = []
def log(s):
    print(s)
    log_lines.append(s)

def fail(msg):
    log("FATAL: " + msg)
    REP.write_text("\n".join(log_lines), encoding="utf-8")
    sys.exit(1)

# ---------------------------------------------------------------- md5 gate
data = TEX.read_bytes()
md5 = hashlib.md5(data).hexdigest()
log(f"[gate] md5(ECT_preprint.tex) = {md5}")
if md5 != EXPECTED_MD5:
    fail(f"md5 mismatch: expected {EXPECTED_MD5}. File changed since audit; re-verify anchors. NOTHING modified.")
content = data.decode("utf-8")
gv_text = GV.read_text(encoding="utf-8")

# idempotency / stale-copy asserts
if "eq:Ktheta_1D" in content: fail("eq:Ktheta_1D already present -> script already applied. NOTHING modified.")
for pat in ["v_0^2", "hbar_{\\rm eff}", "unit ratio"]:
    if pat in content: fail(f"unexpected stale-copy pattern present: {pat!r}")
log("[gate] stale-copy patterns absent - OK.")

# ---- v4: baseline invariants for patterns that the edits must NOT touch
PRESERVED = [r"\beta^2/c_*", r"\beta\bar\Psi", r"\beta\,\bar\Psi", r"\alpha-\beta"]
orig_inv = {p: content.count(p) for p in PRESERVED}
for p in PRESERVED:
    log(f"[invariant] baseline count({p!r}) = {orig_inv[p]}")

warnings = []
def rep1(cid, old, new):
    n = content.count(old)
    if n != 1: fail(f"{cid}: anchor count={n} (expected 1): {old[:90]!r}")
    log(f"[{cid}] 1 replacement")
    return content.replace(old, new)

def repN(cid, old, new, expect):
    n = content.count(old)
    if n != expect: fail(f"{cid}: count={n}, expected {expect}: {old[:60]!r}")
    log(f"[{cid}] {n} replacements (global)")
    return content.replace(old, new)

def rep_all_logged(cid, old, new, min_expected=1):
    global warnings
    n = content.count(old)
    log(f"[{cid}] occurrences={n}")
    if n < min_expected:
        warnings.append(f"{cid}: pattern not found (n={n}) - manual check advised: {old[:60]!r}")
        return content
    log(f"[{cid}] {n} replacements (semantically unambiguous pattern)")
    return content.replace(old, new)

def soft1(cid, old, new):
    global warnings
    n = content.count(old)
    if n != 1:
        warnings.append(f"{cid}: SKIPPED (count={n}): {old[:80]!r}")
        log(f"[{cid}] SOFT skipped (count={n})")
        return content
    log(f"[{cid}] 1 replacement (soft)")
    return content.replace(old, new)

def ins_after(cid, anchor, insert, soft=False):
    global warnings
    n = content.count(anchor)
    if n != 1:
        if soft:
            warnings.append(f"{cid}: SKIPPED insert (anchor count={n})")
            log(f"[{cid}] SOFT insert skipped (count={n})")
            return content
        fail(f"{cid}: insert anchor count={n}: {anchor[:90]!r}")
    log(f"[{cid}] insert after anchor")
    return content.replace(anchor, anchor + insert)

def ins_before(cid, anchor, insert):
    n = content.count(anchor)
    if n != 1: fail(f"{cid}: insert anchor count={n}: {anchor[:90]!r}")
    log(f"[{cid}] insert before anchor")
    return content.replace(anchor, insert + anchor)

# ================= GROUP 0: time-convention customs (GPT-4 classified pass)
content = rep1("W1-wick-4872",
 r"The formal analytic continuation $w_E\to \pm ic_*t$ relates",
 "The formal analytic continuation $w_E\\to \\pm i\\,t$ (with $t=w$ the\n"
 "ordered-branch time coordinate; physical SI units enter only through\n"
 "the matching $c_*=c$) relates")

content = rep1("W2-wick-27844",
 r"$w_E\to \pm ic_*t$ provides",
 r"$w_E\to \pm i\,t$ provides")

content = rep1("W3-16534",
 r"writing $w=c_*t$, the principal hyperbolic operator is:",
 r"writing $t=w$, the principal hyperbolic operator is:")

content = rep1("T1-2482",
 r"$t=w/c_*$, with $c_*^2=\beta/(\alpha-\beta)$.",
 "$t=w$: the ordered direction itself serves as the emergent time\n"
 "coordinate of the Lorentzian branch, and the dimensionless cone slope\n"
 "in these coordinates is $c_*$, with $c_*^2=\\beta/(\\alpha-\\beta)$.\n"
 "(The rescaled coordinate $w/c_*$, in which the cone slope is unity, is\n"
 "not used for the field equations in this paper; physical SI units of\n"
 "time enter only through the matching step Ph1, $c_*=c$.)")

content = rep1("T3-429-symbols",
 r"$t$ & Lorentzian time; $t=w/c_*$ (real parametrisation) & s \\",
 r"$t$ & Lorentzian time; $t=w$ (ordered-branch parametrisation; cone slope $c_*$) & s \\")

content = rep1("N1-2193-norm",
 r"$\tilde\varphi = (\sqrt{\alpha-\beta}/c_*)\,\varphi$ gives",
 r"$\tilde\varphi = \sqrt{\alpha-\beta}\,\varphi$ gives")

content = repN("T-global", "t=w/c_*", "t=w", 33)

# ================= GROUP 1: P1-1 S0 chain (reduced-loop closure)
INS_S1 = (
"\\emph{One-dimensional reduction and the transverse three-volume\n"
"weight.}\n"
"For a closed coherent loop the four-dimensional phase action reduces\n"
"to an effective one-dimensional functional only after integrating the\n"
"transverse profile of the coherent tube over its transverse\n"
"three-volume.\n"
"We encode this reduction in the effective one-dimensional stiffness\n"
"\\begin{equation}\n"
"  K_\\theta^{1\\mathrm D}\n"
"  \\;\\equiv\\;\n"
"  K_\\theta\\,\\mathcal A_\\perp ,\n"
"  \\qquad\n"
"  \\mathcal A_\\perp = c_\\perp\\,\\xi_{\\rm core}^{3},\n"
"  \\qquad\n"
"  [K_\\theta^{1\\mathrm D}]=\\text{GeV}^{-1},\n"
"  \\label{eq:Ktheta_1D}\n"
"\\end{equation}\n"
"where $\\xi_{\\rm core}\\sim m_\\varphi^{-1}$ is the radial-core scale and\n"
"$c_\\perp=\\mathcal O(1)$ is a profile-dependent geometric coefficient of\n"
"the transverse three-volume weight that is \\emph{not} fixed at the\n"
"present EFT level (Appendix~\\ref{app:Sloop_calc}).\n"
"This step is a dimensionally consistent reduced-loop closure, not a\n"
"first-principles derivation of the transverse profile~(Level~B).\n\n")
content = ins_before("S1-insert-1Dreduction", r"\emph{Sharp lower bound on loop action", INS_S1)

content = soft1("S2a-intro",
 "The reduced 1D action along the loop is",
 "The reduced 1D action along the loop, built on the reduced\none-dimensional stiffness~\\eqref{eq:Ktheta_1D}, is")
content = rep1("S2b-Sloopdef", r"\frac{K_\theta}{2}\oint", r"\frac{K_\theta^{1\mathrm D}}{2}\oint")
content = rep1("S3-loopbound", r"\frac{2\pi^2 K_\theta\,n^2}{L},", r"\frac{2\pi^2 K_\theta^{1\mathrm D}\,n^2}{L},")
content = rep1("S4a", r"\frac{2\pi^2 K_\theta}{L_{\rm core}}", r"\frac{2\pi^2 K_\theta^{1\mathrm D}}{L_{\rm core}}")
content = rep1("S4b", r"= \pi\,K_\theta\,m_\varphi.", r"= \pi\,c_\perp\,\frac{K_\theta}{m_\varphi^{2}}.")
NEW_S5 = r"= \frac{c_\perp\,K_\theta}{2\,m_\varphi^{2}}.}"
content = rep1("S5-boxed", r"= \frac{K_\theta\,m_\varphi}{2}.}", NEW_S5)

idx = content.find(NEW_S5)
if idx < 0: fail("S6: NEW_S5 not found after S5")
j = content.find("\\end{equation}", idx)
if j < 0: fail("S6: end{equation} after boxed S0 not found")
j += len("\\end{equation}")
INS_S6 = (
"\n\n\\emph{Dimensionless form and parameter compression.}\n"
"In the simplest quartic realisation\n"
"(in the convention $V(\\Phi)=-\\tfrac{\\mu^2}{2}\\Phi^2\n"
"+\\tfrac{\\lambda}{4}\\Phi^4$ of~P3, so that $K_\\theta\\sim\\phi_0^2$ and\n"
"$m_\\varphi^2=2\\lambda\\,\\phi_0^2$)\n"
"the elementary-loop scale becomes\n"
"\\begin{equation}\n"
"  S_0^{\\rm EFT}\\;\\sim\\;\\frac{c_\\perp}{4\\lambda},\n"
"  \\label{eq:S0_lambda}\n"
"\\end{equation}\n"
"independent of $\\phi_0$: the candidate action quantum is controlled by\n"
"the dimensionless self-coupling alone, in structural analogy with the\n"
"inverse-coupling scaling of instanton actions.\n"
"Consequently the identification $S_0^{\\rm EFT}=\\hbar$ fixes the\n"
"dimensionless combination $c_\\perp/\\lambda$ at order unity rather than\n"
"a dimensionful scale.\n"
"This is a promising parameter-compression route~(Level~B closure with\n"
"profile-dependent $c_\\perp$), not a completed first-principles\n"
"determination of~$\\lambda$.")
content = content[:j] + INS_S6 + content[j:]
log("[S6] inserted eq:S0_lambda paragraph")

content = rep1("S7-4814", r"$K_\theta\,m_\varphi/2\approx\hbar$.", r"$c_\perp K_\theta/(2m_\varphi^{2})\approx\hbar$.")
content = repN("S8-displays", "  S_0^{\\rm EFT} = \\frac{K_\\theta\\,m_\\varphi}{2},",
                              "  S_0^{\\rm EFT} = \\frac{c_\\perp\\,K_\\theta}{2\\,m_\\varphi^{2}},", 2)
content = rep1("S9a", r"fixes $m_\varphi$, or", "fixes the dimensionless combination")
content = rep1("S9b", "    equivalently~$\\lambda$.", "    $c_\\perp/\\lambda$~(Eq.~\\eqref{eq:S0_lambda}).")
content = rep1("S10", r"by fixing $m_\varphi = 2\hbar/K_\theta$.",
 "by fixing the dimensionless combination $c_\\perp K_\\theta/m_\\varphi^{2}$,\n"
 "i.e.\\ in the quartic realisation $\\lambda\\simeq c_\\perp/4$~(Level~B;\n"
 "$c_\\perp$ profile-dependent and open).")
content = rep1("S11a", r"$S_0^{\rm EFT}=K_\theta\,m_\varphi/2$", r"$S_0^{\rm EFT}=c_\perp K_\theta/(2m_\varphi^{2})$")
content = soft1("S11b", "& B & Characteristic elementary-loop action scale",
                        "& B & Reduced-loop closure; transverse coefficient $c_\\perp$ open")
content = rep1("S12-9117", "  S_0^{\\rm EFT} = \\frac{K_\\theta\\,m_\\varphi}{2}.",
                           "  S_0^{\\rm EFT} = \\frac{c_\\perp\\,K_\\theta}{2\\,m_\\varphi^{2}}.")
content = rep1("S13-14936", "  S_0 = \\frac{K_\\theta\\,m_\\varphi}{2}\\,.",
                            "  S_0 = \\frac{c_\\perp\\,K_\\theta}{2\\,m_\\varphi^{2}}\\,.")
content = rep1("S14a-27730", "  \\frac{K_\\theta^{\\rm eff}\\,m_\\varphi}{2},",
                             "  \\frac{c_\\perp\\,K_\\theta^{\\rm eff}}{2\\,m_\\varphi^{2}},")
content = rep1("S14b", "coherent branch and $m_\\varphi$ is the inverse core-length scale",
                       "coherent branch, $m_\\varphi$ is the inverse core-length scale")
content = ins_after("S14c", "entering the elementary-loop closure.",
 "\nHere $c_\\perp=\\mathcal O(1)$ is the profile-dependent coefficient of\n"
 "the transverse three-volume reduction of the coherent tube\n"
 "(Section~\\ref{sec:hbar_status}, Eq.~\\eqref{eq:Ktheta_1D}).", soft=True)

INS_S15 = ("\nFor closed-loop functionals the relevant stiffness is the reduced\n"
"one-dimensional coefficient\n"
"$K_\\theta^{1\\mathrm D}=K_\\theta\\,\\mathcal A_\\perp$ with\n"
"$[\\mathcal A_\\perp]=\\text{GeV}^{-3}$ (transverse three-volume weight),\n"
"so that $[K_\\theta^{1\\mathrm D}]=\\text{GeV}^{-1}$ and the reduced loop\n"
"action $S_{\\rm loop}=\\tfrac12 K_\\theta^{1\\mathrm D}\\oint d\\ell\\,(\\partial_\\ell\\theta)^2$\n"
"is dimensionless, as required for an action scale.")
m = re.search(re.escape(r"$[K_\theta]=\text{GeV}^2$") + r"[^\n]*\n", content)
if m:
    content = content[:m.end()] + INS_S15 + "\n" + content[m.end():]
    log("[S15] dim_phase note inserted")
else:
    warnings.append("S15: dim_phase anchor not found - SKIPPED")

content = rep1("S16a-Sloopcalc", r"$S_0^{\rm EFT}=K_\theta m_\varphi/2$ by evaluating that bound at",
                                 r"$S_0^{\rm EFT}=c_\perp K_\theta/(2m_\varphi^2)$ by evaluating that bound at")
OLD_S16B = (
"(ii)~integration of $f(\\rho)$ over the transverse cross-section;\n"
"(iii)~introduction of an effective line tension $\\mathcal{T}$\n"
"     such that $S_{\\rm eff}^{\\rm 1D}[\\mathcal{C}]=\\mathcal{T}\\cdot|\\mathcal{C}|$;\n"
"(iv)~evaluation at the characteristic core-sized loop under the $n=1$\n"
"     winding constraint.\n"
"Each of these steps requires the nonlinear broken-phase potential\n"
"(beyond the quadratic EFT) and the choice of a vortex profile,\n"
"which are not determined at the ECT basics level.")
NEW_S16B = (
"(ii)~integration of $f(\\rho)$ over the transverse three-volume of the\n"
"     tube, encoded in the reduced one-dimensional stiffness\n"
"     $K_\\theta^{1\\mathrm D}=K_\\theta\\,\\mathcal A_\\perp$ with\n"
"     $\\mathcal A_\\perp=c_\\perp\\,\\xi_{\\rm core}^3$~\\eqref{eq:Ktheta_1D};\n"
"(iii)~introduction of an effective line tension $\\mathcal{T}$\n"
"     such that $S_{\\rm eff}^{\\rm 1D}[\\mathcal{C}]=\\mathcal{T}\\cdot|\\mathcal{C}|$;\n"
"(iv)~evaluation at the characteristic core-sized loop under the $n=1$\n"
"     winding constraint.\n"
"Steps~(i)--(ii) are performed schematically by the transverse\n"
"three-volume reduction~\\eqref{eq:Ktheta_1D}; what remains open is the\n"
"explicit profile coefficient $c_\\perp$, which requires the nonlinear\n"
"broken-phase potential (beyond the quadratic EFT) and the choice of a\n"
"vortex profile, not determined at the ECT basics level.")
content = rep1("S16b", OLD_S16B, NEW_S16B)

OLD_S17 = "not a strict derivation: $\\ell_{\\rm Pl}$ depends on~$\\hbar$,\nwhich is not yet derived at this stage."
INS_S17 = ("\nWithin the corrected reduced-loop closure of\n"
"Section~\\ref{sec:hbar_status}, the identification\n"
"$S_0^{\\rm EFT}=\\hbar$ corresponds to $\\lambda\\sim\\mathcal O(1)$\n"
"(Eq.~\\eqref{eq:S0_lambda}), and hence to\n"
"$m_\\sigma=\\sqrt{2\\lambda}\\,\\phi_0\\sim\\bar M_{\\rm Pl}$ and\n"
"$\\xi_{\\rm cond}\\sim\\ell_{\\rm Pl}$.\n"
"The Planck-length matching is therefore internally consistent with the\n"
"third calibration relation rather than independent of it; this remains\n"
"a promising consistency route conditional on the profile coefficient\n"
"$c_\\perp=\\mathcal O(1)$~(Level~B), not a derivation.")
content = ins_after("S17-sigma-scales", OLD_S17, INS_S17, soft=True)

# ================= GROUP 2: P1-4 beta_phi rename (semantic pass) + P1-3
content = rep1("B1", r"\beta\dot\phi^2", r"\beta_\phi\dot\phi^2")
content = rep1("B2", r"+\beta e^{\beta \phi}q", r"+\beta_\phi e^{\beta_\phi \phi}q")
content = rep1("B3", r"\frac{\beta e^{\beta \phi}}{\kappa}", r"\frac{\beta_\phi e^{\beta_\phi \phi}}{\kappa}")
content = rep1("B4", r"(1+\beta q^{(k)})", r"(1+\beta_\phi q^{(k)})")
content = rep1("B5", r"Z_u\beta^2 u_\infty^2", r"Z_u\beta_\phi^2 u_\infty^2")
content = rep1("B6", r"Z_u \beta^2 u_\infty^2", r"Z_u \beta_\phi^2 u_\infty^2")

# ---- v4: bare coupling-beta PREFIXES revealed by the v3 context dump ----
# Completeness of expects 1 and 5: each pattern contains e^{\beta\phi},
# hence every instance necessarily appeared among the 95 dumped sites.
content = repN("B6a-prefix-sq", r"\beta^2 e^{\beta\phi}", r"\beta_\phi^2 e^{\beta\phi}", 1)
content = repN("B6b-prefix",    r"\beta e^{\beta\phi}",   r"\beta_\phi e^{\beta\phi}",   5)
content = rep_all_logged("B6c-1plusbq", r"(1+\beta q)", r"(1+\beta_\phi q)")
content = rep1("B6d-fprime", r"(so that $f' = \beta", r"(so that $f' = \beta_\phi")
content = rep_all_logged("B6e-phidef",
 r"\frac{1}{\beta}\ln(u/u_\infty)", r"\frac{1}{\beta_\phi}\ln(u/u_\infty)")

# ---- B7-global: per-site verified replacement of '\beta\phi' ----
PAT = r"\beta\phi"
positions = [mm.start() for mm in re.finditer(re.escape(PAT), content)]
nlines = sum(1 for L in content.split("\n") if PAT in L)
log(f"[B7-verify] occurrences={len(positions)}, lines-containing={nlines}")
bad = []
for p in positions:
    pre6 = content[max(0, p-6):p]
    if re.search(r"e\^\{-?2?$", pre6) is None:
        bad.append(content[max(0, p-60):p+40].replace("\n", "\\n"))
if bad:
    log("[B7-verify] BAD contexts:")
    for c in bad: log("   " + c)
    fail(f"B7-verify: {len(bad)} occurrence(s) of '\\beta\\phi' NOT inside e^{{...}}. NOTHING modified.")
n_b7 = content.count(PAT)
content = content.replace(PAT, r"\beta_\phi\phi")
log(f"[B7-global] {n_b7} replacements (all sites verified inside e^{{...}})")

# ---- B8-global: '\beta \phi' (spaced variant) ----
pos8 = [mm.start() for mm in re.finditer(re.escape(r"\beta \phi"), content)]
log(f"[B8-verify] occurrences={len(pos8)}; contexts:")
for p in pos8:
    log("   | ..." + content[max(0, p-40):p+28].replace("\n", "\\n") + "...")
content = repN("B8-global", r"\beta \phi", r"\beta_\phi \phi", 4)

content = rep1("B9-Gdot", r"{G_{\rm eff}} = -\dot\phi.", r"{G_{\rm eff}} = -\beta_\phi\,\dot\phi.")
content = rep1("B10-bound", r"requiring $|\dot\phi|\lesssim 10^{-12}$\,yr$^{-1}$",
                            r"requiring $|\beta_\phi\dot\phi|\lesssim 10^{-12}$\,yr$^{-1}$")
content = ins_after("B11-defnote", r"G_{\rm eff}(X)=G_N\,e^{-\beta_\phi\phi(X)}.",
 "\n\\end{equation}\n"
 "(Here and below $\\beta_\\phi$ denotes the dimensionless\n"
 "amplitude--curvature coupling of the ordered-branch closure,\n"
 "notationally distinct from the kinetic coefficient $\\beta$ of the\n"
 "quadratic tensor $K^{AB}$ and from the fifth-force coupling\n"
 "$\\beta_5$.)", soft=True)
if any(w.startswith("B11") for w in warnings):
    pass
else:
    k = content.find(r"G_{\rm eff}(X)=G_N\,e^{-\beta_\phi\phi(X)}.")
    tail = content[k:]
    tail = tail.replace("$\\beta_5$.)\n\\end{equation}", "$\\beta_5$.)", 1)
    content = content[:k] + tail
content = rep1("B12-symbolrow",
 r"$\beta_5$ & Dimensionless fifth-coupling ratio defined by $\mu_5=\beta_5 m_f$ & dimensionless \\",
 "$\\beta_5$ & Dimensionless fifth-coupling ratio defined by $\\mu_5=\\beta_5 m_f$ & dimensionless \\\\\n"
 "$\\beta_\\phi$ & Dimensionless amplitude--curvature coupling of the $\\phi$-first closure, $F(\\phi)=e^{\\beta_\\phi\\phi}$ (distinct from the kinetic $\\beta$) & dimensionless \\\\")

# ================= GROUP 3: P1-6 demotion of 1.6 GeV ansatz
INS_D1 = (
"\n\n\\paragraph{Primary-stiffness objection and demotion of the GeV-scale\n"
"ansatz.}\n"
"A Derrick-type scaling argument sharpens the status of\n"
"Eq.~\\eqref{eq:topological_mass_ansatz}.\n"
"In three spatial dimensions the two-derivative orientation term alone\n"
"does not stabilise $\\pi_3$ configurations against collapse; any\n"
"stabilisation, if it occurs, must involve contributions beyond the\n"
"two-derivative term, and the higher-derivative (NLO) operators of the\n"
"same class that generates the orientation stiffness $\\kappa_n$ may\n"
"provide the required stabilising terms.\n"
"For textures of the \\emph{primary} vacuum manifold, whose stiffness is\n"
"tied to the high condensate scale ($\\kappa_n\\sim\\phi_0^2$), the natural\n"
"mass scale of any so-stabilised configuration is then parametrically\n"
"tied to the high condensate scale rather than to the GeV range, up to\n"
"profile- and operator-dependent numerical factors (Level~B scaling\n"
"argument; no explicit profile solution is available).\n"
"The GeV-scale law~\\eqref{eq:topological_mass_ansatz} is therefore not\n"
"supported by the primary $\\pi_3(S^3)$ sector.\n"
"It is hereby demoted to a \\emph{legacy phenomenological benchmark}: if\n"
"retained at all, it must be reassigned to a secondary\n"
"(electroweak- or colour-linked) topological sector, whose existence\n"
"and scale are themselves open~(OP-top-mass; cf.\\\n"
"Appendix~\\ref{app:second_transition}).\n"
"Its falsification constrains only this legacy benchmark, not the\n"
"Level~A sector classification.")
content = ins_after("D1-insert", "only the specific dynamical ansatz used to estimate its masses.", INS_D1)

content = rep1("D2-D7row",
 r"but the mass law is not derived from topology alone & \ref{sec:predicted_states} \\",
 r"but the mass law is not derived from topology alone; demoted to a legacy benchmark, not supported by the primary-sector stiffness scale; secondary-sector reassignment open (OP-top-mass) & \ref{sec:predicted_states} \\")

content = rep1("D3-F6row",
 r"F6 & Topological mass ansatz $m_n \sim n\times1.6\,$GeV &",
 r"F6 & Topological mass ansatz $m_n \sim n\times1.6\,$GeV (legacy benchmark; primary-stiffness objection, \S\ref{sec:predicted_states}) &")

content = ins_after("D4-F6bullet",
 "the topological sector, not the topological sector as such.",
 "\n    Following the primary-stiffness objection of\n"
 "    Section~\\ref{sec:predicted_states}, this realisation is a demoted\n"
 "    legacy benchmark reassigned at most to a secondary sector\n"
 "    (OP-top-mass).")

content = rep1("D5-14887",
 r"$m_n\sim n\times 1.6\,$GeV/$c^2$~(D7) is directly falsifiable",
 "$m_n\\sim n\\times 1.6\\,$GeV/$c^2$~(D7) --- demoted to a legacy benchmark\n"
 "by the primary-stiffness objection\n"
 "(Section~\\ref{sec:predicted_states}) --- is directly falsifiable")

# ================= GROUP 4: P1-7 eta_B unification
content = rep1("H1-11312",
 "illustrative benchmark for the resonant leptogenesis estimate",
 "illustrative \\emph{imported} benchmark (not an ECT-derived\nprediction) for the resonant leptogenesis estimate")
content = rep1("H2-26052", r"$\sim6\times10^{-10}$ & Benchmark only \\",
                           r"$\sim6\times10^{-10}$ & Imported benchmark only \\")
content = rep1("H3-45201",
 r"$\eta_B$ (baryon asymmetry) & Benchmark leptogenesis &",
 r"$\eta_B$ (baryon asymmetry) & Imported benchmark (leptogenesis) &")
OLD_H4 = ("The cosmological sector further yields a leptogenesis estimate\n"
"$\\eta_B\\sim 9\\times10^{-10}$ (within a factor of~$1.5$ of the\n"
"observed $6\\times10^{-10}$) and compatibility with the\n"
"DESI~2024 dark-energy constraint $w_0 = -0.827$.")
NEW_H4 = ("The cosmological sector is further compatible with an \\emph{imported}\n"
"resonant-leptogenesis benchmark $\\eta_B\\sim 9\\times10^{-10}$ (not an\n"
"ECT-derived prediction; within a factor of~$1.5$ of the observed\n"
"$6\\times10^{-10}$) and with the dataset- and\n"
"parametrisation-dependent DESI~DR1/DR2 indications of evolving dark\n"
"energy~\\cite{DESIDR2_2025,Lodha2025}.")
content = rep1("H4-conclusion", OLD_H4, NEW_H4)

# ================= GROUP 5: P1-8 DESI refresh
OLD_DE1 = ("\\paragraph{Cosmological dark-energy compatibility.}\n"
"The DESI~2024 measurement $w_0 = -0.827$ is compatible with the\n"
"ECT late-time amplitude-sector closure if the ratio of kinetic to\n"
"condensate energy density satisfies\n"
"$\\rho_{\\rm kin}/\\rho_{\\rm cond} \\approx 0.26$.\n"
"This provides a concrete target for the full cosmological\n"
"$\\phi_{\\rm bg}(t)$ programme.")
NEW_DE1 = ("\\paragraph{Cosmological dark-energy compatibility.}\n"
"DESI DR1/DR2 analyses provide dataset- and parametrisation-dependent\n"
"indications of evolving dark energy in combined\n"
"fits~\\cite{DESI2024,DESIDR2_2025}, with significance depending on the\n"
"supernova combination and on the assumed dark-energy\n"
"parametrisation~\\cite{Lodha2025}; these indications are suggestive but\n"
"not definitive and are not used here as a fixed numerical calibration\n"
"anchor.\n"
"The legacy DR1 anchor $w_0=-0.827$ is compatible with the ECT\n"
"late-time amplitude-sector closure if the ratio of kinetic to\n"
"condensate energy density satisfies\n"
"$\\rho_{\\rm kin}/\\rho_{\\rm cond} \\approx 0.26$ (DR1-anchored legacy\n"
"benchmark).\n"
"This remains a concrete target for the full cosmological\n"
"$\\phi_{\\rm bg}(t)$ programme.")
content = rep1("DE1-paragraph", OLD_DE1, NEW_DE1)

content = rep1("DE2-tablerow",
 r"$w_0$ (DESI 2024) & $-0.83$ & $-0.827$ & Closure consistency \\",
 r"$w_0$ (DESI) & $\approx-0.83$ (thawing) & DR1: $-0.827$; DR2: dataset-dependent & Legacy DR1-anchored consistency \\")
content = rep1("DE3-25461", "(calibrated,\nnot derived from first principles)",
                            "(DR1-anchored legacy calibration,\nnot derived from first principles)")
content = rep1("DE4-25512", r"DESI-calibrated benchmark $(f_0,\kappa)\approx(0.26,4.3)$",
                            r"DR1-calibrated legacy benchmark $(f_0,\kappa)\approx(0.26,4.3)$")

# ================= FINAL SANITY
zero_checks = [
 "t=w/c_*", "ic_*t", "w=c_*t",
 r"K_\theta\,m_\varphi", r"K_\theta m_\varphi", r"K_\theta^{\rm eff}\,m_\varphi",
 r"e^{\beta\phi", r"e^{-\beta\phi", r"e^{2\beta\phi", r"\beta \phi", r"\beta\phi",
 r"\beta e^{", r"\beta^2 e^{", r"(1+\beta q)",
 r"2\hbar/K_\theta",
]
for pat in zero_checks:
    n = content.count(pat)
    if n != 0: fail(f"sanity-zero: count({pat!r})={n}, expected 0")
log("[sanity] all zero-checks OK")
for p in PRESERVED:
    n = content.count(p)
    if n != orig_inv[p]:
        fail(f"sanity-invariant: count({p!r})={n}, baseline was {orig_inv[p]} - edits leaked into preserved pattern")
    log(f"[sanity] invariant OK: {p!r} = {n} (unchanged)")
log(f"[sanity] beta_phi total occurrences now: {content.count(chr(92)+'beta_'+chr(92)+'phi')}")

# ---- non-fatal audit: mixed beta/beta_phi neighbourhoods (manual review)
lines = content.split("\n")
has_b  = [("\\beta" in L) and ("\\beta_\\phi" not in L) and ("\\beta_5" not in L) for L in lines]
has_bp = ["\\beta_\\phi" in L for L in lines]
sus = []
for i in range(len(lines)):
    if has_b[i] and any(has_bp[max(0, i-2):i+3]):
        sus.append((i+1, lines[i].strip()[:110]))
log(f"[audit] mixed beta/beta_phi neighbourhoods: {len(sus)} (non-fatal, for manual review)")
for ln, txt in sus[:40]:
    log(f"   L{ln}: {txt}")

# ================= .gv fix (IDEMPOTENT)
OLD_G = ("  gauge -> SU3 [style=dashed, color=gray50];\n"
         "  gauge -> threegen [style=dashed, color=gray50];")
NEW_G = ("  gauge -> SU3 [style=dashed, color=black];\n"
         "  gauge -> threegen [style=dashed, color=black];")
if gv_text.count(OLD_G) == 1:
    gv_new = gv_text.replace(OLD_G, NEW_G); gv_changed = True
    log("[GV] grey->black on 2 edges")
elif gv_text.count(NEW_G) == 1:
    gv_new = gv_text; gv_changed = False
    log("[GV] edges already black (pre-applied in-session) - source unchanged; figure will be regenerated")
else:
    fail("GV anchor mismatch (neither gray50 nor black pair found exactly once)")

# ================= WRITE (backups first)
BAK.mkdir(exist_ok=True)
shutil.copy2(TEX, BAK / "ECT_preprint_BACKUP_v202_pre_package1.tex")
log("[backup] backup/ECT_preprint_BACKUP_v202_pre_package1.tex created")
gv_bak = Path(str(GV) + ".bak_pre_package1")
if gv_changed and not gv_bak.exists():
    shutil.copy2(GV, gv_bak)
    log("[backup] gv backup created")
else:
    log("[backup] gv backup pre-existing or gv unchanged - skip")
TEX.write_text(content, encoding="utf-8")
log(f"[write] ECT_preprint.tex written ({len(content)} chars)")
if gv_changed:
    GV.write_text(gv_new, encoding="utf-8")
    log("[write] .gv written")
if warnings:
    log("WARNINGS (soft skips):")
    for w in warnings: log("  - " + w)

# ================= dot regeneration (always)
try:
    for fmt, out in [("pdf", FIGD / "fig_partI_derivation_logic.pdf"),
                     ("png", FIGD / "fig_partI_derivation_logic.png")]:
        r = subprocess.run([DOT, f"-T{fmt}", str(GV), "-o", str(out)],
                           capture_output=True, text=True, timeout=120)
        log(f"[dot -T{fmt}] rc={r.returncode} {r.stderr.strip()[:200]}")
except Exception as e:
    log(f"[dot] SKIPPED: {e}")

# ================= 4-pass compile
def run(cmd):
    r = subprocess.run(cmd, cwd=str(BASE), capture_output=True, text=True, timeout=1800)
    return r.returncode
try:
    rcs = [run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]),
           run([BIBTEX, "ECT_preprint"]),
           run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"]),
           run([PDFLATEX, "-interaction=nonstopmode", "ECT_preprint.tex"])]
    log(f"[compile] rcs={rcs}")
    logtxt = (BASE / "ECT_preprint.log").read_text(encoding="utf-8", errors="ignore")
    nerr = sum(1 for L in logtxt.splitlines() if L.startswith("!"))
    nundef_ref = len(re.findall(r"Reference `[^']*' .* undefined", logtxt))
    nundef_cit = len(re.findall(r"Citation `[^']*' .* undefined", logtxt))
    mpages = re.search(r"Output written on ECT_preprint\.pdf \((\d+) pages", logtxt)
    log(f"[compile] hard errors (^!): {nerr}; undefined refs: {nundef_ref}; undefined citations: {nundef_cit}")
    log(f"[compile] PAGES: {mpages.group(1) if mpages else 'NOT FOUND'} (was 740)")
except Exception as e:
    log(f"[compile] FAILED/SKIPPED: {e}")

REP.write_text("\n".join(log_lines), encoding="utf-8")
print("\nDONE. Full report: scripts/package1_apply_report.txt")
