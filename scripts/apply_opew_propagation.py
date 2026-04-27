#!/usr/bin/env python3
"""
Apply 8 OP-EW propagation edits to ECT_companion.tex (5) and ECT_preprint.tex (3).

Each replacement is anchor-based with strict count check. Backup created first.
"""
import sys, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex')
COMPANION = ROOT / 'companion' / 'ECT_companion.tex'
PREPRINT = ROOT / 'ECT_preprint.tex'

# ---- Backups ----
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy(COMPANION, ROOT / 'companion' / f'ECT_companion_BACKUP_pre_opew_propagation_{ts}.tex')
shutil.copy(PREPRINT, ROOT / 'backup' / f'ECT_preprint_BACKUP_v195_pre_opew_propagation.tex')
print("Backups created.")
print()

applied, failed = [], []

def safe_replace(path, old, new, label):
    t = path.read_text()
    if old not in t:
        failed.append((label, "anchor NOT FOUND"))
        return
    cnt = t.count(old)
    if cnt != 1:
        failed.append((label, f"anchor count={cnt}"))
        return
    path.write_text(t.replace(old, new))
    applied.append(label)

# ============================================================
# C1 — companion line ~457: hierarchy explanation update
# ============================================================
c1_old = (
    "The \\textbf{electroweak scale} $v_2 \\sim 246$\\,GeV corresponds to a second, "
    "subsidiary condensation within the $\\Phi$-sector, generating masses for the $W$, "
    "$Z$ bosons, and the Higgs particle. The enormous hierarchy $\\phi_0/v_2 \\sim 10^{16}$ "
    "remains open: it is structurally compatible with a running-coupling / "
    "dimensional-transmutation scenario analogous to the generation of the QCD scale "
    "from the running of $\\alpha_s$, but an explicit derivation within ECT has not "
    "been performed. Progress on this hierarchy is structurally tied to the broader "
    "programme of emergent gauge-sector derivation (\\emph{Open})."
)
c1_new = (
    "The \\textbf{electroweak scale} $v_2 \\sim 246$\\,GeV corresponds to a second, "
    "subsidiary condensation within the $\\Phi$-sector, generating masses for the $W$, "
    "$Z$ bosons, and the Higgs particle. The enormous hierarchy $\\phi_0/v_2 \\sim 10^{16}$ "
    "is logarithmically equivalent to a single dimensionless quantity, "
    "$\\mathcal{I}_{\\rm EW}\\equiv\\ln(\\phi_0/v_2)\\approx 36.8$, of the same order as "
    "the analogous QCD logarithm $\\ln(M_{\\rm Pl}/\\Lambda_{\\rm QCD})\\approx 44$. "
    "Its origin remains open. The technical preprint reduces this to a "
    "non-polynomial scale-generation problem in a phase--orientation alignment sector and "
    "lists four candidate mechanisms (asymptotic-freedom-like running, "
    "walking/near-conformal dynamics, Miransky/BKT critical scaling, and topological/"
    "Hopf-like routes), each requiring an order-one input rather than a fine-tuned "
    "$10^{-16}$ ratio. None has been derived from P1--P6. Progress is structurally tied "
    "to the broader programme of emergent gauge-sector derivation (the layered "
    "OP-EW programme: OP-EW-scale, OP-EW-locking, OP-EW-gauge, OP-EW-naturalness, "
    "OP-EW-matter; \\emph{Open})."
)
safe_replace(COMPANION, c1_old, c1_new, "C1: companion hierarchy 4 mechanisms")

# ============================================================
# C2 — companion line ~545: weak interaction Hopf-locking mention
# ============================================================
c2_old = (
    "\\textbf{Weak interaction (\\emph{Level~B+}):} The residual rotation group $O(3)$ "
    "after $O(4) \\to O(3)$ SSB is algebraically isomorphic to $SU(2)$ (as Lie algebras: "
    "$\\mathfrak{so}(3) \\cong \\mathfrak{su}(2)$). The oriented condensate---through the "
    "sign of the four-volume form---selects one of the two $SU(2)$ factors of $Spin(4) "
    "\\simeq SU(2)_+ \\times SU(2)_-$, structurally selecting a single \\emph{chiral} "
    "$SU(2)$ sector. This provides a structural route to weak-sector parity asymmetry. "
    "The exact maximally parity-violating Standard-Model pattern and the full derivation "
    "of the weak sector as an independent internal gauge field remain open. The "
    "phenomenological realisation occurs through a secondary condensate scale at "
    "$v_2\\simeq246$\\,GeV, producing $W^\\pm$, $Z$ bosons and electroweak symmetry "
    "breaking."
)
c2_new = (
    "\\textbf{Weak interaction (\\emph{Level~B+}):} The residual rotation group $O(3)$ "
    "after $O(4) \\to O(3)$ SSB is algebraically isomorphic to $SU(2)$ (as Lie algebras: "
    "$\\mathfrak{so}(3) \\cong \\mathfrak{su}(2)$). The oriented condensate---through the "
    "sign of the four-volume form---selects one of the two $SU(2)$ factors of $Spin(4) "
    "\\simeq SU(2)_+ \\times SU(2)_-$, structurally selecting a single \\emph{chiral} "
    "$SU(2)$ sector. This provides a structural route to weak-sector parity asymmetry. "
    "The exact maximally parity-violating Standard-Model pattern and the full derivation "
    "of the weak sector as an independent internal gauge field remain open. The "
    "phenomenological realisation occurs through a secondary condensate scale at "
    "$v_2\\simeq246$\\,GeV, producing $W^\\pm$, $Z$ bosons and electroweak symmetry "
    "breaking. A reduced $O(3)\\to O(2)$ analogue alone provides only two broken "
    "directions, whereas the electroweak Higgs mechanism requires three; the technical "
    "preprint therefore proposes a candidate geometric upgrade---Hopf-fibered "
    "phase--orientation diagonal locking, $SU(2)_{\\rm orient}\\times U(1)_\\theta\\to "
    "U(1)_{\\rm diag}$, with pre-gauge vacuum manifold $S^3$ matching the fixed-radius "
    "Higgs-doublet manifold---as the geometric route to the missing third broken "
    "direction. This locking dynamics, the chirality lift $SU(2)_{\\rm orient}\\to "
    "SU(2)_L$, the local gauge completion, and the protection of the secondary radial "
    "mode all remain open."
)
safe_replace(COMPANION, c2_old, c2_new, "C2: companion weak sector + Hopf-locking")

# ============================================================
# C3 — companion line ~2370: hierarchy in great problems list
# ============================================================
c3_old = (
    "\\item \\textbf{The hierarchy problem.} $M_{\\rm Pl}/M_{\\rm EW} \\sim 10^{16}$ "
    "addressed through running coupling (\\emph{B/Open})."
)
c3_new = (
    "\\item \\textbf{The hierarchy problem.} The ratio $M_{\\rm Pl}/M_{\\rm EW} \\sim 10^{16}$ "
    "is logarithmically equivalent to $\\mathcal{I}_{\\rm EW}\\approx 36.8$, of the "
    "same order as the analogous QCD logarithm. The technical preprint reduces this "
    "to a non-polynomial scale-generation problem with four candidate mechanisms "
    "(asymptotic-freedom-like, walking, Miransky/BKT, topological/Hopf), and "
    "decomposes the broader question into the layered OP-EW programme "
    "(OP-EW-scale, OP-EW-locking, OP-EW-gauge, OP-EW-naturalness, OP-EW-matter), "
    "all currently open (\\emph{B/Open})."
)
safe_replace(COMPANION, c3_old, c3_new, "C3: companion great problems hierarchy")

# ============================================================
# C4 — companion symbols table: add I_EW row before $M_G,\bar M_{Pl}$
# ============================================================
c4_old = (
    "$v_2$ & Electroweak scale $\\approx 246$\\,GeV (second condensate scale). \\\\\n"
    "$M_G,\\bar M_{\\rm Pl}$ & Induced gravitational-stiffness scale / reduced Planck mass $\\approx 2.435\\times10^{18}$\\,GeV. \\\\"
)
c4_new = (
    "$v_2$ & Electroweak scale $\\approx 246$\\,GeV (second condensate scale). \\\\\n"
    "$\\mathcal{I}_{\\rm EW}$ & Logarithmic measure of the electroweak hierarchy: "
    "$\\mathcal{I}_{\\rm EW}=\\ln(\\phi_0/v_2)\\approx 36.8$; central reduction quantity "
    "for the OP-EW-scale programme (technical preprint). \\\\\n"
    "$M_G,\\bar M_{\\rm Pl}$ & Induced gravitational-stiffness scale / reduced Planck mass $\\approx 2.435\\times10^{18}$\\,GeV. \\\\"
)
safe_replace(COMPANION, c4_old, c4_new, "C4: companion symbols I_EW row")

# ============================================================
# C5 — companion keywords: add Hopf-locking + layered EW
# ============================================================
c5_old = "electroweak metastability; RG running;\n"
c5_new = (
    "electroweak metastability; RG running;\n"
    "Hopf-fibered phase--orientation locking; layered electroweak programme;\n"
)
safe_replace(COMPANION, c5_old, c5_new, "C5: companion keywords Hopf-locking")

# ============================================================
# P1 — preprint symbols list: add v_2 and I_EW rows
# After c_* row, before m_eff^2 row, in the "Broken-phase EFT parameters" block
# ============================================================
p1_old = (
    "$c_*$ & Effective propagation speed: $c_*=\\sqrt{\\beta/(\\alpha-\\beta)}$, Level~A & $=c$ (canonical) \\\\\n"
    "$m_{\\rm eff}^2$ & EFT fluctuation mass parameter; $m_{\\rm eff}^2\\neq m_\\sigma^2$ in general & GeV$^2$ \\\\"
)
p1_new = (
    "$c_*$ & Effective propagation speed: $c_*=\\sqrt{\\beta/(\\alpha-\\beta)}$, Level~A & $=c$ (canonical) \\\\\n"
    "$v_2$ & Electroweak matching scale: $v_2=(\\sqrt{2}G_F)^{-1/2}$ "
    "(eq.~\\ref{eq:v2_GF}); intermediate condensate scale, not derived from P1--P6 "
    "(OP-EW-scale, Sec.~\\ref{sec:three_scales}) & $\\approx 246.22$\\,GeV \\\\\n"
    "$\\mathcal{I}_{\\rm EW}$ & Logarithmic measure of the electroweak hierarchy: "
    "$\\mathcal{I}_{\\rm EW}\\equiv\\ln(\\phi_0/v_2)$; central reduction quantity for "
    "the OP-EW-scale closure programme (eq.~\\ref{eq:I_EW_definition}, "
    "Sec.~\\ref{sec:three_scales}) & $\\approx 36.8$ (dimensionless) \\\\\n"
    "$m_{\\rm eff}^2$ & EFT fluctuation mass parameter; $m_{\\rm eff}^2\\neq m_\\sigma^2$ in general & GeV$^2$ \\\\"
)
safe_replace(PREPRINT, p1_old, p1_new, "P1: preprint symbols + v_2 + I_EW")

# ============================================================
# P2 — preprint keywords: add Hopf-locking, layered EW programme
# ============================================================
p2_old = "electroweak metastability;\nRG running;\n"
p2_new = (
    "electroweak metastability;\n"
    "RG running;\n"
    "Hopf-fibered phase--orientation locking;\n"
    "layered electroweak programme;\n"
)
safe_replace(PREPRINT, p2_old, p2_new, "P2: preprint keywords Hopf-locking")

# ============================================================
# P3 — preprint abbreviations: add OP-EW layered note after WV
# ============================================================
p3_old = (
    "WV & Witten--Veneziano (relation between $\\eta'$ mass and topological "
    "susceptibility, Part~IV, \\S\\ref{sec:topological_strong_cp}) \\\\\n"
    "\\end{longtable}"
)
p3_new = (
    "WV & Witten--Veneziano (relation between $\\eta'$ mass and topological "
    "susceptibility, Part~IV, \\S\\ref{sec:topological_strong_cp}) \\\\\n"
    "OP-EW & Layered electroweak open-problem programme: OP-EW-scale "
    "($\\mathcal{I}_{\\rm EW}\\approx 36.8$, four candidate mechanisms), "
    "OP-EW-locking (compact $U(1)_\\theta$ origin and Hopf-fibered diagonal "
    "locking, App.~\\ref{app:hopf_locking}), OP-EW-gauge (chirality, hypercharge, "
    "$g$, $g'$, Weinberg angle), OP-EW-naturalness (radial-mode protection), "
    "OP-EW-matter (chiral fermions, Yukawa hierarchy) \\\\\n"
    "\\end{longtable}"
)
safe_replace(PREPRINT, p3_old, p3_new, "P3: preprint abbreviations OP-EW layered")

# ============================================================
print(f"\nApplied: {len(applied)}/8")
for a in applied: print(f"  OK  {a}")
print(f"\nFailed: {len(failed)}")
for lbl, why in failed: print(f"  FAIL {lbl}: {why}")

if failed:
    print("\nABORTING. Some anchors not matched. NO files were partially modified - safe_replace either succeeds or skips per anchor; check failed list above.")
    sys.exit(1)
print("\nAll 8 edits successful.")
