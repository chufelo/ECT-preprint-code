#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P6 M3 primary protocol demo (GPT Round 22): P23/P24 edge-plus-line + detuning-transition falsifier.
Environment-compatible: numpy only, relative paths, no pandas.

Purpose:
  1. Turn the P23/P24 qualitative discriminator into an executable protocol skeleton.
  2. Demonstrate the expected g2_crit(Delta) ~ Delta law for a soft-edge intrinsic channel.
  3. Demonstrate the external-vs-intrinsic contrast: external golden-rule widths vs intrinsic bound line.
  4. Export compact CSV diagnostics for Claude/ledger review.

This is not a lab-specific design. It is a normalized toy model with the R19 bosonic mirror KK kernel.
"""
import csv
import math
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
RR = []

# -------------------------
# Shared numerical utilities
# -------------------------
def trapz(y, x):
    return float(np.trapezoid(y, x))

def append(section, case, value, check, note):
    RR.append({"section": section, "case": case, "value": value, "check": check, "note": note})

# -------------------------
# Intrinsic soft-edge model
# -------------------------
# Units: E_edge = 1. g2 denotes the physical squared coupling amplitude.
E = 1.0
wc_edge = 2.2
A_edge = 12.0
w_grid = np.linspace(E + 1e-6, E + 80.0 * wc_edge, 260000)


def J_edge_unit(w):
    """Soft edge without g2: J(w) = A (w-E) exp[-(w-E)/wc] theta(w-E)."""
    w = np.asarray(w)
    y = np.maximum(w - E, 0.0)
    return A_edge * y * np.exp(-y / wc_edge)


def sigma_prime_unit(omega, eps=2.5e-5):
    """R19 bosonic-mirror dispersion, per unit g2."""
    x = w_grid
    J = J_edge_unit(x)
    den = x * x - omega * omega
    if omega > E:
        mask = np.abs(x - omega) > eps
    else:
        mask = np.ones_like(x, dtype=bool)
    return (2.0 / math.pi) * trapz(x[mask] * J[mask] / den[mask], x[mask])


def sigma_imag_unit(omega):
    """Imaginary self-energy proxy per unit g2; zero below edge."""
    if omega <= E:
        return 0.0
    return math.pi * float(J_edge_unit(np.array([omega]))[0])

# Threshold critical coupling: D(E-) = E^2 - Omega0^2 + g2 Sigma'(E) = 0.
SigE = sigma_prime_unit(E)
Deltas = np.array([0.004, 0.007, 0.010, 0.015, 0.020, 0.030, 0.045, 0.060])
gcrit = []
for Delta in Deltas:
    Om0 = E + Delta
    g2c = (Om0 * Om0 - E * E) / SigE
    gcrit.append(g2c)
gcrit = np.array(gcrit)
coef = np.polyfit(np.log(Deltas), np.log(gcrit), 1)
lin_slope = np.polyfit(Deltas, gcrit, 1)[0]
append("T1", "P24 log slope", f"{coef[0]:.6f}", "~1", "g2_crit(Delta) from D(E-)=0 with bosonic mirror KK")
append("T1", "P24 linear slope", f"{lin_slope:.6f}", ">0", "slope depends on kernel normalization; exponent is the invariant prediction")
assert abs(coef[0] - 1.0) < 0.04

# Bound-state solver below edge.
def D_below(omega, Om0, g2):
    return omega * omega - Om0 * Om0 + g2 * sigma_prime_unit(omega)


def find_bound(Om0, g2, n=220):
    xs = np.linspace(1e-5, E - 1e-5, n)
    vals = np.array([D_below(float(x), Om0, g2) for x in xs])
    # Find the root closest to the edge. The threshold transition creates this edge-adjacent pole.
    roots = []
    for i in range(len(xs) - 1):
        if vals[i] == 0.0 or vals[i] * vals[i + 1] < 0:
            lo, hi = xs[i], xs[i + 1]
            flo, fhi = vals[i], vals[i + 1]
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                fm = D_below(mid, Om0, g2)
                if flo * fm <= 0:
                    hi, fhi = mid, fm
                else:
                    lo, flo = mid, fm
            roots.append(0.5 * (lo + hi))
    if not roots:
        return None
    return max(roots)

Delta0 = 0.020
Om0 = E + Delta0
g2c0 = (Om0 * Om0 - E * E) / SigE
for mult in (0.55, 1.25, 2.0):
    g2 = mult * g2c0
    wb = find_bound(Om0, g2)
    if wb is None:
        append("T2", f"Delta={Delta0:.3f} g2/gcrit={mult:.2f}", "no subedge pole", "below threshold", "expected narrow/above-edge resonance branch")
    else:
        gap = E - wb
        gamma_b = 2.0 * sigma_imag_unit(wb) * g2
        append("T2", f"Delta={Delta0:.3f} g2/gcrit={mult:.2f}", f"omega_b={wb:.6f}; gap={gap:.6f}; Gamma_b={gamma_b:.3e}", "Gamma_b=0", "intrinsic protected line below edge")
        assert gamma_b == 0.0

# Above-edge continuum shoulder turns on linearly before resolution convolution.
for off in (-0.030, -0.010, 0.010, 0.030):
    w = E + off
    gamma = 2.0 * g2c0 * sigma_imag_unit(w)
    append("T3", f"shoulder offset {off:+.3f}", f"{gamma:.8f}", "0 below; >0 above", "ideal intrinsic continuum threshold")
assert sigma_imag_unit(E - 0.01) == 0.0 and sigma_imag_unit(E + 0.01) > 0

# Finite-resolution visibility condition.
g2_demo = 2.0 * g2c0
wb_demo = find_bound(Om0, g2_demo)
gap_demo = E - wb_demo
resolutions = [0.002, 0.006, 0.012, 0.025]
for res in resolutions:
    visible = gap_demo > 3.0 * res
    append("T4", f"resolution sigma={res:.3f}", str(visible), "gap > 3 sigma", f"gap={gap_demo:.6f}; finite-resolution guard")

# -------------------------
# External C12 contrast demo
# -------------------------
# External occupied ohmic monitor with known form factors. This is intentionally not the intrinsic edge pole problem.
C_ext, wc_ext, T_ext = 0.37, 3.4, 0.72

def J_ext(w):
    return C_ext * np.maximum(w, 0.0) * np.exp(-w / wc_ext)

def nB(w):
    return 1.0 / (np.exp(w / T_ext) - 1.0)

Oms = 0.42 + 0.19 * np.arange(1, 11)
forms = {
    "coordinate": np.ones_like(Oms),
    "velocity": Oms,
    "inverse_odd": 1.0 / Oms,
}
expected = {"coordinate": 0.0, "velocity": 2.0, "inverse_odd": -2.0}
for name, F in forms.items():
    Gam = 2.0 * math.pi * J_ext(Oms) * F * F * (1.0 + nB(Oms))
    # Remove occupation and kernel, then fit |F|^2 power.
    rec_F2 = Gam / (2.0 * math.pi * J_ext(Oms) * (1.0 + nB(Oms)))
    slope = np.polyfit(np.log(Oms), np.log(rec_F2), 1)[0]
    append("T5", f"external C12 exponent {name}", f"{slope:.6f}", f"{expected[name]:+.1f}", "golden-rule hierarchy after dividing J_W and occupation")
    assert abs(slope - expected[name]) < 2e-12

# External kernel -> dephasing/shift over-closure mini-check, inherited from S7/P26 but now part of M3 readout logic.
wg = np.logspace(-6, 2.3, 50000)
def Phi_ext(Cv, wcv, t):
    J = Cv * wg * np.exp(-wg / wcv)
    S = J / np.tanh(wg / (2.0 * T_ext))
    return trapz(S * (1.0 - np.cos(wg * t)) / (wg * wg), wg)

# Reconstruct C,wc from the coordinate external widths.
Gam_coord = 2.0 * math.pi * J_ext(Oms) * (1.0 + nB(Oms))
Jrec = Gam_coord / (2.0 * math.pi * (1.0 + nB(Oms)))
fit = np.polyfit(Oms, np.log(Jrec / Oms), 1)
C_rec, wc_rec = math.exp(fit[1]), -1.0 / fit[0]
worst = 0.0
for t in (0.5, 5.0, 50.0):
    r = Phi_ext(C_rec, wc_rec, t) / Phi_ext(C_ext, wc_ext, t)
    worst = max(worst, abs(r - 1.0))
append("T6", "external P26 closure from width corner", f"C={C_rec:.6f}; wc={wc_rec:.6f}; worstPhi={worst:.2e}", "machine/noiseless", "not independent of P23/P24; included as M3 sanity check")
assert worst < 1e-10

# Matrix-channel red flag: external and intrinsic data cannot be merged if cross-spectral Cauchy-Schwarz fails.
for r in (0.63, 1.20):
    ok = r * r <= 1.0 + 1e-15
    append("G4", f"cross-channel r={r:.2f}", str(ok), "True for admissible", "if false, scalar one-channel M3 interpretation is invalid")

with open(OUT / "p6_m3_p23_p24_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["section", "case", "value", "check", "note"])
    w.writeheader()
    for row in RR:
        w.writerow(row)

print("P6 M3 P23/P24 protocol demo complete.")
for row in RR:
    print(f"{row['section']:>2} | {row['case']:<42} | {row['value']:<48} | {row['check']}")
print("WROTE p6_m3_p23_p24_results.csv")
