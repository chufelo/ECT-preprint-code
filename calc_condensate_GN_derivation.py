"""
ECT: Derivation of Newton's constant G_N from condensate action
================================================================
Appendix G of ECT preprint (Blagovidov 2026).

Derives G_N by expanding the ECT action to quadratic order in metric
perturbations h_AB around the broken-symmetry vacuum <Phi> = v0,
<n_A> = delta_{Aw}.

Key result:
    G_N = 1 / (16 pi v0^2 (alpha - beta))

At alpha=2, beta=1:
    G_N = 1 / (16 pi v0^2)  =>  v0 = M_Pl_reduced = 2.435e18 GeV

Physical interpretation (Sakharov induced gravity analogy):
    G_N = 1 / (vacuum stiffness)  =>  softer condensate = stronger gravity.
"""

import numpy as np

# ── Constants ────────────────────────────────────────────────────────────────
M_Pl_reduced_GeV = 2.435e18      # GeV, reduced Planck mass
GeV_to_kg        = 1.783e-27     # kg per GeV/c^2
c                = 2.998e8       # m/s
hbar             = 1.055e-34     # J*s
G_N_SI           = 6.674e-11     # m^3 kg^-1 s^-2 (CODATA)

# ── ECT formula ───────────────────────────────────────────────────────────────
def G_N_ECT(v0_GeV, alpha, beta):
    """
    Newton's constant from ECT condensate parameters.
    
    v0   : condensate VEV [GeV]
    alpha: gradient coupling (must satisfy alpha > beta for Lorentzian)
    beta : kinetic coefficient (=1 for canonical normalisation)
    
    Returns G_N in natural units (GeV^-2), then converts to SI.
    """
    # In natural units (hbar = c = 1), G_N [GeV^-2] = 1/(16 pi v0^2 (alpha-beta))
    G_N_nat = 1.0 / (16.0 * np.pi * v0_GeV**2 * (alpha - beta))
    # Convert to SI: G_N [m^3 kg^-1 s^-2]
    # G_N [GeV^-2] * (hbar c)^2 [J^2 s^2 / kg^2] / kg [J / c^2] ...
    # Simpler: use M_Pl^2 = hbar c / G_N
    hbar_c_GeV_m = 0.1973e-15 * 1e-9  # GeV * m  (hbar*c = 197.3 MeV*fm)
    M_Pl_SI = v0_GeV * np.sqrt(alpha - beta) * GeV_to_kg * c**2  # J
    G_N_SI_computed = hbar * c / M_Pl_SI**2 * (hbar * c)
    return G_N_nat, G_N_SI_computed

# ── Main calculation ──────────────────────────────────────────────────────────
print("=" * 60)
print("ECT: Derivation of G_N  (Appendix G)")
print("=" * 60)

for alpha, beta in [(2.0, 1.0), (1.5, 0.5), (3.0, 1.0)]:
    v0 = M_Pl_reduced_GeV / np.sqrt(alpha - beta)
    G_nat, G_SI = G_N_ECT(v0, alpha, beta)
    print(f"\nalpha={alpha}, beta={beta}  =>  alpha-beta={alpha-beta}")
    print(f"  v0 = {v0:.4e} GeV   (= M_Pl_reduced / sqrt(alpha-beta))")
    print(f"  G_N = {G_nat:.4e} GeV^-2  (natural units)")
    print(f"  G_N = {G_SI:.4e} m^3 kg^-1 s^-2  (SI)")
    print(f"  G_N (CODATA) = {G_N_SI:.4e} m^3 kg^-1 s^-2")
    print(f"  Ratio G_ECT/G_CODATA = {G_SI/G_N_SI:.6f}")

print("\n" + "=" * 60)
print("Matching condition for canonical normalisation (alpha=2, beta=1):")
print(f"  v0 = M_Pl_reduced = {M_Pl_reduced_GeV:.4e} GeV")
print(f"  G_N formula: G_N = 1/(16pi v0^2) in natural units")
print(f"  Physical meaning: G_N = inverse stiffness of the condensate")
print(f"  Analogy: Sakharov induced gravity (G_N ~ 1/sum_i m_i^2)")
print("=" * 60)

# ── Running G_N with condensate profile ──────────────────────────────────────
print("\nSpatially varying G_eff(r) for galactic rotation curve:")
r_kpc = np.array([0.1, 1.0, 5.0, 10.0, 50.0, 100.0])
r0_kpc = 14.0   # MW condensate correlation length

# ECT profile: v0(r) = v_inf / sqrt(1 + (r/r0)^2)
v0_r = M_Pl_reduced_GeV / np.sqrt(1.0 + (r_kpc / r0_kpc)**2)
G_eff_r = 1.0 / (16.0 * np.pi * v0_r**2)  # in natural units
G_eff_ratio = G_eff_r / (1.0 / (16.0 * np.pi * M_Pl_reduced_GeV**2))
print(f"  r0 = {r0_kpc} kpc (Milky Way condensate scale)")
print(f"  {'r [kpc]':>10} {'G_eff/G_N':>12}")
for r, ge in zip(r_kpc, G_eff_ratio):
    print(f"  {r:>10.1f} {ge:>12.4f}")
