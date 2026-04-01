#!/usr/bin/env python3
"""
ECT Derivation Map — Graphviz branching graph.
Two-column branching but portrait proportions via size constraint.
All 6 postulates, proper HTML subscripts, greyscale.
"""
import subprocess, os, struct

dot_code = """
digraph ECT {
  rankdir=TB;
  fontname="Helvetica";
  node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled",
        fillcolor="#f0f0f0", color="#333333", penwidth=1.2, margin="0.14,0.07"];
  edge [fontname="Helvetica", fontsize=8, color="#555555", penwidth=1.0];
  splines=true;
  nodesep=0.4;
  ranksep=0.5;
  size="7.5,16";
  ratio=compress;

  /* ===== TIER 0: Phi-medium ===== */
  PHI [label=<Φ-medium<BR/><FONT POINT-SIZE="9">4D Euclidean manifold (ℳ⁴, δ<SUB>AB</SUB>)   ·   Scalar condensate field Φ</FONT>>,
       fillcolor="#c0c0c0", penwidth=2.2, fontsize=11];

  /* ===== TIER 1: Postulates ===== */
  subgraph cluster_postulates {
    label=<Foundational Postulates P1–P6>; labeljust=l;
    style=dashed; color="#888888"; fontsize=9; fontname="Helvetica";
    P1 [label=<P1: 4D Euclidean arena (ℳ⁴, δ<SUB>AB</SUB>)>, fillcolor="#d9d9d9"];
    P2 [label=<P2: O(4)-invariant action S<SUB>E</SUB>[Ψ]>, fillcolor="#d9d9d9"];
    P3 [label=<P3: Minimal scalar microdynamics>, fillcolor="#d9d9d9"];
    P4 [label=<P4: Ordered vacuum branch ⟨∂Φ⟩ ≠ 0>, fillcolor="#d9d9d9"];
    P5 [label=<P5: Medium character → gauge redundancy>, fillcolor="#d9d9d9"];
    P6 [label=<P6: Multiplicity of configurations>, fillcolor="#d9d9d9"];
    {rank=same; P1; P2}
    {rank=same; P3; P4}
    {rank=same; P5; P6}
  }
  PHI -> P1 [style=invis]; PHI -> P2 [style=invis];
  P1 -> P3 [style=invis]; P2 -> P4 [style=invis];
  P3 -> P5 [style=invis]; P4 -> P6 [style=invis];

  /* ===== TIER 2: SSB ===== */
  SSB [label=<O(4) → O(3) Spontaneous Symmetry Breaking<BR/><FONT POINT-SIZE="9">Preferred direction n<SUB>A</SUB> = δ<SUB>Aw</SUB>   ·   Ordered condensate background</FONT>>,
       fillcolor="#b5b5b5", penwidth=1.8, fontsize=10];
  P5 -> SSB; P6 -> SSB;

  /* ===== TIER 3: Emergent Lorentzian ===== */
  LOR [label=<Emergent Lorentzian Structure<BR/><FONT POINT-SIZE="9">Metric diag(−1,1,1,1)   ·   c<SUB>*</SUB> = 1/√(α−β)   ·   Causal cone   ·   Arrow of time</FONT>>,
       fillcolor="#c8c8c8", penwidth=1.5, fontsize=10];
  SSB -> LOR [xlabel=<  α &gt; β >];

  /* ===== TIER 4: Two branches ===== */
  MBRANCH [label=<Macroscopic / Tensor Branch (Part II)>,
           fillcolor="#d3d3d3", fontsize=10];
  QBRANCH [label=<Quantum / Coherent Branch (Part III)>,
           fillcolor="#d3d3d3", fontsize=10];
  LOR -> MBRANCH;
  LOR -> QBRANCH;
  {rank=same; MBRANCH; QBRANCH}

  /* ===== MACRO BRANCH (left) ===== */
  GR [label=<General Relativity<BR/><FONT POINT-SIZE="9">Fierz–Pauli → Einstein eqs.<BR/>G<SUB>N</SUB> = c<SUB>*</SUB>²(α−β) / (16πv₀²)   [A/B]</FONT>>];

  MBRANCH -> GR;

  COSMO [label=<Cosmology<BR/><FONT POINT-SIZE="9">Inflation n<SUB>s</SUB> ≈ 0.967   ·   Λ<SUB>eff</SUB><BR/>Hubble tension route   [B]</FONT>>];
  GAL [label=<Galactic Dynamics<BR/><FONT POINT-SIZE="9">φ-branch   ·   BTFR slope = 4   ·   RAR<BR/>g<SUB>†</SUB> ~ cH₀/(2π)   [B]</FONT>>];
  BH [label=<Black Holes &amp; Strong Field<BR/><FONT POINT-SIZE="9">Shell ρ<SUB>c</SUB> = ℓ<SUB>Pl</SUB>/√(3π)   ·   BH thermo<BR/>Information prog.   [B/Open]</FONT>>];
  FIFTH [label=<5th Force<BR/><FONT POINT-SIZE="9">β₅ ~ m<SUB>f</SUB>/M<SUB>Pl</SUB>   ·   M<SUB>max</SUB> ≈ 2.17 M<SUB>⊙</SUB>   [B]</FONT>>];
  CLUSTER [label=<Cluster Lensing<BR/><FONT POINT-SIZE="9">Bullet, A520, El Gordo<BR/>ν-closure rule   [B]</FONT>>];

  GR -> COSMO;
  GR -> GAL;
  GR -> BH;
  GAL -> FIFTH;
  GAL -> CLUSTER;

  /* ===== QUANTUM BRANCH (right) ===== */
  S0 [label=<Action Scale S₀<BR/><FONT POINT-SIZE="9">Winding sectors   ·   Phase quantisation   [A]</FONT>>];

  QBRANCH -> S0;

  SCHROD [label=<Schrödinger Equation<BR/><FONT POINT-SIZE="9">Canonical phase dynamics<BR/>Uncertainty principle   [A/B]</FONT>>];
  VACUUM [label=<Vacuum Response<BR/><FONT POINT-SIZE="9">Casimir (3/2)   ·   Unruh T<SUB>U</SUB><BR/>Particle production   [A/B]</FONT>>];
  DECOH [label=<Decoherence &amp; Arrow of Time<BR/><FONT POINT-SIZE="9">Influence functional   ·   Entropy<BR/>Crooks relation   [A/B]</FONT>>];
  BORN [label=<Born Rule<BR/><FONT POINT-SIZE="9">Gleason route (C1–C3)   [B/Open]</FONT>>];
  TOPO [label=<Exchange Topology &amp; Spinors<BR/><FONT POINT-SIZE="9">π₁(ℳ₂) = ℤ₂   ·   Dirac route<BR/>Entanglement   [A]</FONT>>];

  S0 -> SCHROD;
  S0 -> VACUUM;
  SCHROD -> DECOH;
  SCHROD -> BORN;
  LOR -> TOPO [style=dashed, xlabel=<d<SUB>sp</SUB>=3>];

  /* ===== GAUGE SECTOR (bridging both branches) ===== */
  GAUGE [label=<Gauge &amp; Matter Sector<BR/><FONT POINT-SIZE="9">U(1) → photon   ·   SU(2) → W<SUP>±</SUP>, Z   ·   Higgs (v₂ ≈ 246 GeV)<BR/>Fermions: O(3) spinor reps   ·   SU(3): open   ·   3 gen.: open   [A/B/Open]</FONT>>,
        fillcolor="#ddd"];
  S0 -> GAUGE [xlabel=<phase>];
  TOPO -> GAUGE [xlabel=<spinor>];
  FIFTH -> GAUGE [style=invis]; /* pull gauge down */

  /* ===== PREDICTIONS & FALSIFIERS ===== */
  PRED [label=<Quantitative Predictions<BR/><FONT POINT-SIZE="9">LIV: |δc/c| &lt; 10⁻¹⁵   ·   Casimir: 3/2 × QED   ·   g<SUB>†</SUB> ≈ 1.1×10⁻¹⁰ m/s²<BR/>BTFR slope = 4   ·   n<SUB>s</SUB> ≈ 0.967   ·   M<SUB>max</SUB> ≈ 2.17 M<SUB>⊙</SUB>   ·   Env.-dep. g<SUB>†</SUB></FONT>>,
       fillcolor="#d0d0d0", penwidth=1.5];
  FALS [label=<Cross-Sector Architectural Falsifiers<BR/><FONT POINT-SIZE="9">Single c<SUB>*</SUB>   ·   Single S₀   ·   Single UV threshold m<SUB>σ</SUB><BR/>No DM particles in lab   ·   Env.-dep. transition morphology</FONT>>,
       fillcolor="#d0d0d0", penwidth=1.5];

  GAUGE -> PRED;
  CLUSTER -> PRED [constraint=false];
  COSMO -> PRED [constraint=false];
  VACUUM -> PRED [constraint=false];
  PRED -> FALS;

  /* ===== OPEN PROBLEMS ===== */
  OPEN [label=<Major Open Fronts<BR/><FONT POINT-SIZE="9">S₀ = ℏ   ·   SU(3) colour   ·   Yukawa hierarchy   ·   α<SUB>fs</SUB> = 1/137<BR/>Full nonlinear GR   ·   Born rule unconditional   ·   Bell correlators<BR/>Page curve   ·   3 fermion generations</FONT>>,
        fillcolor="white", style="rounded,dashed,filled"];

  FALS -> OPEN [style=dashed];
  BORN -> OPEN [style=dashed, constraint=false];
  BH -> OPEN [style=dashed, constraint=false];

  /* Minimal ranking */
  {rank=same; GR; S0}
}
"""

dot_path = "/opt/homebrew/bin/dot"
out_dir = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures"
dot_file = os.path.join(out_dir, "fig_ect_derivation_map.dot")
pdf_file = os.path.join(out_dir, "fig_ect_derivation_map.pdf")
png_file = os.path.join(out_dir, "fig_ect_derivation_map.png")

with open(dot_file, "w") as f:
    f.write(dot_code)

subprocess.run([dot_path, "-Tpdf", dot_file, "-o", pdf_file], check=True)
subprocess.run([dot_path, "-Tpng", "-Gdpi=300", dot_file, "-o", png_file], check=True)

with open(png_file, 'rb') as f:
    f.read(16); w = struct.unpack('>I', f.read(4))[0]; h = struct.unpack('>I', f.read(4))[0]
print(f"Done: {w}x{h} px, ratio w/h={w/h:.2f}, approx {w/300:.1f}x{h/300:.1f} inches")
