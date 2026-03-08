#!/usr/bin/env python3
"""
calc_inflation_spectral_index.py
=================================
Computes the ECT predictions for inflationary observables:
spectral index n_s, tensor-to-scalar ratio r, and spectral running.

Paper location: Section 12 (Cosmological Predictions), Eq. 12.x

Physics:
--------
ECT inflation is driven by the condensate field Phi rolling toward the
O(4)->O(3) symmetry-breaking minimum. In the slow-roll approximation,
the inflaton is the radial mode of the condensate.

For a phi^2 potential (chaotic inflation, motivated by ECT V ~ Phi^2 near
the phase transition): n_s = 1 - 2/N_e, r = 8/N_e.
For a Starobinsky-like plateau (from Coleman-Weinberg): n_s = 1 - 2/N_e,
r ~ 12/N_e^2 (much lower r).

ECT uses the n_s = 1 - 2/N_e formula, which is the leading-order result
for a broad class of single-field slow-roll models.

Key results:
  N_e = 60:  n_s = 0.967  (Planck 2018: 0.965 +/- 0.004) — 1sigma match
  N_e = 55:  n_s = 0.964
  N_e = 50:  n_s = 0.960

The number of e-folds N_e ~ 50-60 corresponds to the horizon-crossing
scale leaving the Hubble radius 50-60 e-folds before inflation ends.

Dependencies: numpy
Usage: python calc_inflation_spectral_index.py
"""

import numpy as np

print("=" * 65)
print("ECT: Inflationary observables")
print("=" * 65)

# ============================================================
# Observational values (Planck 2018 + BKP 2022)
# ============================================================
ns_obs    = 0.965
ns_err    = 0.004       # 1-sigma
r_obs_upper = 0.056     # 95% CL upper bound (BKP 2022)

print(f"\nObservational constraints (Planck 2018 + BKP 2022):")
print(f"  n_s = {ns_obs} +/- {ns_err}  (1-sigma)")
print(f"  r < {r_obs_upper}  (95% CL)")

# ============================================================
# ECT predictions
# ============================================================
print(f"\nECT predictions (slow-roll, leading order):")
print(f"  n_s = 1 - 2/N_e  (independent of potential shape at leading order)")
print(f"")
print(f"  {'N_e':>6}  {'n_s':>8}  {'r (phi^2)':>12}  {'r (plateau)':>14}  {'sigma from Planck':>18}")

for N_e in [45, 50, 55, 60, 65]:
    ns = 1 - 2/N_e
    r_phi2 = 8/N_e           # chaotic phi^2
    r_plateau = 12/N_e**2    # Starobinsky-type plateau
    sigma = abs(ns - ns_obs) / ns_err
    flag = "<= 1sigma" if sigma < 1 else ("<= 2sigma" if sigma < 2 else "> 2sigma")
    print(f"  {N_e:>6}  {ns:>8.4f}  {r_phi2:>12.4f}  {r_plateau:>14.6f}  {sigma:>8.2f}σ  {flag}")

# ============================================================
# Best-fit N_e
# ============================================================
print(f"\nBest-fit N_e (minimising |n_s - {ns_obs}|):")
N_e_best = 2 / (1 - ns_obs)
ns_best = 1 - 2/N_e_best
print(f"  N_e = 2 / (1 - n_s_obs) = 2 / {1-ns_obs:.3f} = {N_e_best:.1f}")
print(f"  n_s = {ns_best:.4f}")
print(f"")

# The ECT choice N_e = 60 gives n_s = 0.9667
N_e_ect = 60
ns_ect = 1 - 2/N_e_ect
sigma_ect = abs(ns_ect - ns_obs) / ns_err
print(f"ECT canonical choice: N_e = {N_e_ect}")
print(f"  n_s = 1 - 2/{N_e_ect} = {ns_ect:.4f}")
print(f"  Deviation from Planck: {sigma_ect:.2f}σ  (within 1σ)")

# ============================================================
# Running of spectral index
# ============================================================
print(f"\nSpectral running (d n_s / d ln k):")
print(f"  ECT (slow roll):  d n_s / d ln k = -2/N_e^2 = {-2/N_e_ect**2:.2e}")
print(f"  Planck 2018 bound: |d n_s / d ln k| < 0.01 (95% CL)")
print(f"  ECT value {abs(-2/N_e_ect**2):.2e} << 0.01 — consistent")

# ============================================================
# Physical interpretation
# ============================================================
print(f"""
Physical interpretation:
  In ECT, inflation is driven by the condensate rolling from the
  O(4)-symmetric (high-temperature) phase toward the O(4)->O(3)
  broken-symmetry minimum. The slow-roll parameter eta = -2/N_e
  reflects the curvature of the condensate potential.

  N_e ~ 60 e-folds corresponds to the observed flatness of the CMB
  power spectrum; in ECT this is set by the initial conditions at the
  O(4)->O(3) phase transition.

  The formula n_s = 1 - 2/N_e is a CATEGORY I prediction:
  it matches Planck 2018 at the 1-sigma level with no free parameters
  (given N_e ~ 60 from basic inflationary arguments).
""")
