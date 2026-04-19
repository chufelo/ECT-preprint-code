#!/usr/bin/env python3
"""
CHANNEL 11 (Tier B ROUGH): σ_8 from galaxy cluster counts — LINEARIZED.

METHODOLOGICAL STATUS: rough linearized proxy, order-of-magnitude.

Observational anchor
--------------------
Galaxy cluster number counts constrain σ_8·(Ω_m/0.3)^α (α~0.2-0.3).
Representative values (all ΛCDM-interpreted):
  Planck SZ counts (2016): σ_8 (Ω_m/0.3)^0.27 = 0.782 ± 0.010
  DES Y3 clusters (2022):  S_8 = 0.776 ± 0.017
  SPT-SZ (2019):           S_8 ≈ 0.76  ± 0.03
Tension with Planck CMB (ΛCDM) S_8 = 0.832 ± 0.013 at ~2–3σ level.

Direction: cluster counts see LESS structure than CMB-ΛCDM predicts.
Same direction as weak lensing (Channel 9), independent systematics.

Physical linearization
----------------------
Similar to Channel 9 (S_8 weak lensing), but probe different masses
and survey geometry.  Same underlying modified gravity relation:
    σ_8_ECT(0) / σ_8_ΛCDM(0) ≈ 1 + κ_σ · ε

Using average cluster-derived σ_8 ≈ 0.78 vs Planck CMB 0.811:
    δσ_8/σ_8 ≈ -0.039
    ε ≈ -0.02 (κ_σ ≈ 2)
    1σ range: [-0.06, +0.00]

⚠️ LIMITATIONS:
  1. Linearized; neglects halo mass function modifications at high mass
  2. Does not include mass-calibration systematics (hydrostatic bias,
     Y-M relation)
  3. Uses average of multiple surveys (DES, Planck SZ, SPT) informally;
     formal combined analysis would give tighter but less transparent bound
  4. Rough estimate only
"""
import json
import os

sigma8_CMB         = 0.811
sigma8_CMB_sig     = 0.006
sigma8_clusters    = 0.780     # rough average of DES, Planck SZ, SPT
sigma8_clusters_sig = 0.020    # conservative

kappa_sigma_central = 2.0
kappa_sigma_low     = 1.5
kappa_sigma_high    = 3.0

if __name__ == "__main__":
    print("="*66)
    print("CHANNEL 11 (Tier B ROUGH): σ_8 from cluster counts")
    print("="*66)
    print(f"σ_8 from CMB:       {sigma8_CMB} ± {sigma8_CMB_sig}")
    print(f"σ_8 from clusters:  {sigma8_clusters} ± {sigma8_clusters_sig}")
    print()

    delta = sigma8_clusters/sigma8_CMB - 1.0
    delta_sig = abs(delta) * ((sigma8_clusters_sig/sigma8_clusters)**2 +
                               (sigma8_CMB_sig/sigma8_CMB)**2)**0.5
    print(f"Fractional gap: {delta:+.4f} ± {delta_sig:.4f}")

    eps_central = delta / kappa_sigma_central
    eps_stat_sig = delta_sig / kappa_sigma_central

    eps_from_lo_k = delta / kappa_sigma_low
    eps_from_hi_k = delta / kappa_sigma_high

    eps_lo_1s = min(eps_from_lo_k, eps_central - eps_stat_sig)
    eps_hi_1s = max(eps_from_hi_k, eps_central + eps_stat_sig)
    eps_lo_2s = eps_lo_1s - eps_stat_sig
    eps_hi_2s = eps_hi_1s + eps_stat_sig

    print(f"Central ε = {eps_central:+.4f}")
    print(f"1σ range: [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]")
    print(f"2σ range: [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]")
    print()
    print("INTERPRETATION: Cluster counts similarly to weak lensing prefer")
    print("lower σ_8 than CMB-ΛCDM predicts.  In ECT, ε > 0 increases σ_8")
    print("(worsens tension); therefore cluster counts prefer ε ≲ 0.")
    print("Same direction as S_8 weak lensing and BAO; different systematics.")

    result = {
        'channel':     'σ_8 cluster counts (Tier B rough)',
        'tier':        'Tier B',
        'eps_central': float(eps_central),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'caveat':      'ROUGH linearized; no halo-mass bias; informal survey avg',
        'notes':       'DES Y3 / Planck SZ / SPT-SZ informal average; ~2σ tension with CMB'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch11.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
