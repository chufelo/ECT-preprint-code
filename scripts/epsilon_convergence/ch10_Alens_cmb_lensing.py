#!/usr/bin/env python3
"""
CHANNEL 10 (Tier B ROUGH): CMB lensing amplitude A_lens — LINEARIZED.

METHODOLOGICAL STATUS: rough linearized proxy.

Observational anchor
--------------------
CMB lensing smoothing amplitude A_lens (consistency check):
  Planck 2018 TT+lowE:        A_lens = 1.18 ± 0.065  (historical ~2.8σ excess)
  Planck 2020 PR4 + ACT DR4:  A_lens = 1.02 ± 0.029  (consistent with ΛCDM)

We use the more recent combined value: A_lens = 1.02 ± 0.03.

Physical linearization
----------------------
A_lens probes the amplitude of gravitational lensing of the CMB.
In ECT with enhanced G_eff(z) at matter era, lensing potential integral
gets a multiplicative enhancement:
    A_lens ≈ 1 + κ_A · ε,    κ_A ≈ 2–4

(κ_A comes from integrated lensing weight function, peaked at z ≈ 1–5;
integrated enhancement depends on full growth modification.)

For A_lens = 1.02 ± 0.03:
    κ_A · ε = 0.02 ± 0.03
    ε = 0.007 ± 0.010  (κ_A ≈ 3)
    1σ range: [-0.003, 0.017]

⚠️ LIMITATIONS:
  1. Assumes linear response (breaks down for |ε| > 0.05)
  2. κ_A uncertain (bracket 2–4)
  3. Uses combined CMB-only result; separate analyses (Planck only) 
     have historically higher A_lens with different systematic treatment
  4. Does NOT probe ε_early directly, more weighted to intermediate z
"""
import json
import os

A_lens_obs   = 1.020
A_lens_sigma = 0.030

kappa_A_central = 3.0
kappa_A_low     = 2.0
kappa_A_high    = 4.0

if __name__ == "__main__":
    print("="*66)
    print("CHANNEL 10 (Tier B ROUGH): A_lens CMB lensing (Planck+ACT)")
    print("="*66)
    print(f"A_lens observed: {A_lens_obs} ± {A_lens_sigma}")
    print()

    delta_A = A_lens_obs - 1.0
    eps_central = delta_A / kappa_A_central
    eps_stat_sig = A_lens_sigma / kappa_A_central

    # Bracketing κ
    eps_from_low_k  = delta_A / kappa_A_low
    eps_from_high_k = delta_A / kappa_A_high

    eps_lo_1s = min(eps_from_high_k, eps_central - eps_stat_sig)
    eps_hi_1s = max(eps_from_low_k,  eps_central + eps_stat_sig)
    eps_lo_2s = eps_lo_1s - eps_stat_sig
    eps_hi_2s = eps_hi_1s + eps_stat_sig

    print(f"Central ε = {eps_central:+.4f}")
    print(f"1σ range (stat + κ sys): [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]")
    print(f"2σ range: [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]")
    print()
    print("INTERPRETATION: A_lens consistent with ΛCDM (ε = 0) and with small")
    print("positive ε including preprint benchmark ε ≈ 0.01.  Broad, weak bound.")

    result = {
        'channel':     'A_lens CMB lensing (Tier B rough)',
        'tier':        'Tier B',
        'eps_central': float(eps_central),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'caveat':      'ROUGH linearized A_lens = 1 + κ_A·ε; κ_A bracketed 2-4',
        'notes':       'Planck PR4 + ACT DR4; consistent with benchmark ε ≈ 0.01'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch10.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
