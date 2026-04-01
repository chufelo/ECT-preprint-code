#!/usr/bin/env python3
"""
ECT Derivation Map — master logic graph for Part IV.
Greyscale, 300 dpi.
"""
import subprocess, os

dot_code = r"""
digraph ECT_derivation {
  rankdir=TB;
  fontname="Helvetica";
  node [fontname="Helvetica", fontsize=9, shape=box, style="rounded,filled",
        fillcolor="#f0f0f0", color="#333333", penwidth=1.2, margin="0.12,0.06"];
  edge [fontname="Helvetica", fontsize=7, color="#555555", penwidth=0.9];
  splines=true;
  nodesep=0.4;
  ranksep=0.5;

  /* ===== TIER 0: Foundation ===== */
  PHI [label="Φ-medium\n4D Euclidean manifold (M⁴, δ_AB)\nScalar condensate field Φ",
       shape=box, fillcolor="#c8c8c8", penwidth=2.2, fontsize=10];

  /* ===== TIER 1: Postulates ===== */
  subgraph cluster_postulates {
    label="Foundational Postulates"; labeljust=l;
    style=dashed; color="#888888"; fontsize=8;
    P12 [label="P1–P2\nEuclidean manifold\nO(4)-invariant action"];
    P34 [label="P3–P4\nNo external time\nGradient condensate"];
  }
  PHI -> P12; PHI -> P34;

  /* ===== TIER 2: SSB ===== */
  SSB [label="O(4) → O(3) Spontaneous Symmetry Breaking\nPreferred direction n_A = δ_{Aw}\nOrdered condensate background",
       fillcolor="#bbbbbb", penwidth=1.8, fontsize=9];
  P12 -> SSB; P34 -> SSB;

  /* ===== TIER 3: Emergent Lorentzian ===== */
  LOR [label="Emergent Lorentzian Structure\nMetric diag(−1,1,1,1)  |  c* = 1/√(α−1)\nCausal cone  |  Arrow of time",
       fillcolor="#d5d5d5", penwidth=1.5];
  SSB -> LOR [label="P5: α > β"];

  /* ===== TIER 3b: Two branches ===== */
  MBRANCH [label="Macroscopic / Tensor Branch\n(Part II)", fillcolor="#dcdcdc", fontsize=9];
  QBRANCH [label="Quantum / Coherent Branch\n(Part III)", fillcolor="#dcdcdc", fontsize=9];
  LOR -> MBRANCH; SSB -> QBRANCH [label="coherent branch"];

  /* ===== MACRO BRANCH ===== */
  GR [label="General Relativity\nFierz–Pauli → Einstein eqs.\nG_N = c*²(α−1)/(16πv₀²)  [A/B]"];
  COSMO [label="Cosmology\nInflation n_s ≈ 0.967\nDark energy w₀  |  Hubble tension\nΛ_eff from condensate  [B]"];
  GAL [label="Galactic Dynamics\nφ-branch closure  |  BTFR slope = 4\nRAR  |  Rotation curves\ng† ~ cH₀/(2π)  [B]"];
  BH [label="Black Holes & Strong Field\nCritical shell ρ_c = ℓ_Pl/√(3π)\nBH thermodynamics\nInformation reading  [B/Open]"];
  FIFTH [label="5th Force\nβ ~ m/M_Pl  |  CP, LIV violation\nM_max ≈ 2.17 M☉  [B]"];
  CLUSTER [label="Cluster Lensing\nBullet, A520, El Gordo\nν-closure rule  [B]"];

  MBRANCH -> GR;
  GR -> COSMO;
  GR -> GAL [label="weak field"];
  GR -> BH [label="strong field"];
  GAL -> CLUSTER [label="cluster scale"];
  LOR -> FIFTH [label="n_A coupling"];

  /* ===== QUANTUM BRANCH ===== */
  S0 [label="Structural Action Scale S₀\nWinding sectors  |  Phase quantisation  [A]"];
  SCHROD [label="Schrödinger Equation\nCanonical phase dynamics\nUncertainty principle  [A/B]"];
  DECOH [label="Decoherence & Arrow of Time\nInfluence functional\nEntropy growth  |  Crooks relation  [A/B]"];
  VACUUM [label="Vacuum Response\nCasimir (3/2 ratio)  |  Unruh T_U\nParticle production  [A/B]"];
  BORN [label="Born Rule\nGleason route (C1–C3)  [B/Open]"];
  TOPO [label="Exchange Topology & Spinors\nπ₁(M₂) = Z₂  |  Dirac route\nEntanglement  [A]"];

  QBRANCH -> S0;
  S0 -> SCHROD;
  S0 -> VACUUM;
  SCHROD -> DECOH [label="open system"];
  SCHROD -> BORN;
  LOR -> TOPO [label="d_spatial = 3"];

  /* ===== GAUGE SECTOR (bridge) ===== */
  GAUGE [label="Gauge & Matter Sector\nU(1) compact phase → photon\nSU(2) non-Abelian → W±, Z\nHiggs: radial mode, v₂ ≈ 246 GeV\nSU(3): open  [A/B/Open]"];
  FERM [label="Fermion Sector\nO(3) spinor representations\n3 generations: open  [B/Open]"];

  S0 -> GAUGE [label="phase symmetry"];
  TOPO -> FERM [label="spinor reps"];
  GAUGE -> FERM;

  /* ===== PREDICTIONS ===== */
  PRED [label="Quantitative Predictions\nLIV: |δc/c| < 10⁻¹⁵  |  Casimir: 3/2 × QED\ng† ≈ 1.1×10⁻¹⁰ m/s²  |  BTFR slope = 4\nn_s ≈ 0.967  |  M_max ≈ 2.17 M☉\nEnvironment-dependent g†  |  EFE",
       fillcolor="#e0e0e0", penwidth=1.5, fontsize=8];
  FALS [label="Cross-Sector Architectural Falsifiers\nSingle c* for all sectors  |  Single S₀\nSingle UV threshold m_σ  |  No DM particles\nEnvironment-dependent transition morphology",
       fillcolor="#e0e0e0", penwidth=1.5, fontsize=8];

  GAL -> PRED; COSMO -> PRED; VACUUM -> PRED; FIFTH -> PRED;
  GR -> FALS; S0 -> FALS; GAL -> FALS;

  /* ===== OPEN PROBLEMS ===== */
  OPEN [label="Major Open Fronts\nS₀ = ℏ  |  SU(3) colour  |  Yukawa hierarchy\nα_fs = 1/137  |  Full nonlinear GR\nBorn rule unconditional  |  Bell correlators\nPage curve  |  3 fermion generations",
        fillcolor="white", style="rounded,dashed,filled", fontsize=8];

  BORN -> OPEN [style=dashed]; GAUGE -> OPEN [style=dashed];
  BH -> OPEN [style=dashed]; FERM -> OPEN [style=dashed];

  /* Force ranking */
  {rank=same; MBRANCH; QBRANCH}
  {rank=same; GR; S0}
  {rank=same; COSMO; GAL; SCHROD; VACUUM}
  {rank=same; BH; CLUSTER; DECOH; BORN}
  {rank=same; GAUGE; FERM; TOPO}
  {rank=same; PRED; FALS}
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
print(f"PDF: {pdf_file}")
print(f"PNG: {png_file}")
