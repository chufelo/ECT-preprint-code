#!/usr/bin/env python3
"""
CHANNEL 9 (Tier B ROUGH): S_8 weak lensing tension — LINEARIZED ESTIMATE.

METHODOLOGICAL STATUS: rough linearized proxy, ORDER-OF-MAGNITUDE only.

Observational anchor
--------------------
KiDS-1000 weak-lensing (Heymans+ 2021): S_8 = 0.759 ± 0.024
Planck 2018 ΛCDM prediction:          S_8 = 0.832 ± 0.013
where S_8 ≡ σ_8 · (Ω_m/0.3)^0.5

This is the "S_8 tension" (~3σ).  Low-z weak lensing prefers LOWER
structure amplitude than the CMB (ΛCDM-interpreted) predicts.

Physical linearization
----------------------
In ECT, G_eff(z) = (1+z)^(2ε) enhances linear growth during the
matter era.  For same initial power spectrum (fixed A_s from CMB),
σ_8(0) increases:
    σ_8_ECT(0) / σ_8_ΛCDM(0) ≈ 1 + κ_σ · ε,    κ_σ ≈ 1.5–3
(kappa depends on effective growth-era integration).

For ECT to match the KiDS observation instead of ΛCDM prediction:
    S_8_ECT / S_8_Planck = 0.759 / 0.832 = 0.912
    ⇒ κ_σ · ε ≈ -0.088
    ⇒ ε ≈ -0.04  (with κ_σ ≈ 2)

Rough 1σ range from uncertainty in κ_σ (1.5–3) and observational σ:
    ε ∈ [-0.065, -0.015]  (central -0.04)

⚠️ LIMITATIONS:
  1. κ_σ depends on nonlinear matter power spectrum modeling (not full)
  2. Assumes Planck CMB A_s is unchanged in ECT (in reality it might
     shift if background evolution differs)
  3. Does not include full KiDS covariance
  4. Rough estimate only — not to be combined in inverse-variance fit
"""
import json
import os

# --- Observational inputs ---
S8_KiDS     = 0.759
S8_KiDS_sig = 0.024
S8_Planck   = 0.832
S8_Planck_sig = 0.013

# --- Linearization coefficient (rough) ---
kappa_sigma_central = 2.0        # effective σ_8 enhancement per unit ε
kappa_sigma_low     = 1.5        # lower bracket
kappa_sigma_high    = 3.0        # upper bracket

if __name__ == "__main__":
    print("="*66)
    print("CHANNEL 9 (Tier B ROUGH): S_8 weak-lensing tension (KiDS-1000)")
    print("="*66)
    print(f"KiDS-1000:    S_8 = {S8_KiDS} ± {S8_KiDS_sig}")
    print(f"Planck ΛCDM:  S_8 = {S8_Planck} ± {S8_Planck_sig}")
    print()

    # Gap and its uncertainty
    delta = S8_KiDS/S8_Planck - 1.0        # -0.088
    delta_sig = delta * ((S8_KiDS_sig/S8_KiDS)**2 +
                          (S8_Planck_sig/S8_Planck)**2)**0.5
    print(f"Fractional gap: (S8_KiDS/S8_Planck - 1) = {delta:+.4f} ± {delta_sig:.4f}")

    # Central estimate
    eps_central = delta / kappa_sigma_central
    eps_stat_sig = abs(delta_sig / kappa_sigma_central)
    # Systematic from κ uncertainty (bracketing)
    eps_sys_lo = delta / kappa_sigma_low     # more negative
    eps_sys_hi = delta / kappa_sigma_high    # less negative

    # Combine stat + sys conservatively
    eps_lo_1s = min(eps_sys_lo, eps_central - eps_stat_sig)
    eps_hi_1s = max(eps_sys_hi, eps_central + eps_stat_sig)

    # 2σ: broader
    eps_lo_2s = eps_lo_1s - eps_stat_sig
    eps_hi_2s = eps_hi_1s + eps_stat_sig

    print(f"κ_σ (central, low, high): {kappa_sigma_central}, "
          f"{kappa_sigma_low}, {kappa_sigma_high}")
    print(f"Central ε = {eps_central:+.4f} (stat σ ≈ {eps_stat_sig:.4f})")
    print(f"1σ range (stat + κ sys): [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]")
    print(f"2σ range: [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]")
    print()
    print("INTERPRETATION: KiDS observation prefers LOWER σ_8 than Planck CMB-ΛCDM")
    print("predicts.  In ECT with uniform ε > 0, σ_8(0) would be HIGHER, worsening")
    print("the tension.  Therefore S_8 prefers ε ≲ 0 — opposite direction to Tier A.")
    print("Consistent with BAO, fσ_8 low-z probes.")

    result = {
        'channel':     'S_8 weak lensing (Tier B rough)',
        'tier':        'Tier B',
        'eps_central': float(eps_central),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'caveat':      'ROUGH linearized estimate; κ_σ bracketed 1.5-3; no full covariance',
        'notes':       'KiDS-1000 vs Planck ΛCDM prediction; ~3σ S_8 tension'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch9.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
