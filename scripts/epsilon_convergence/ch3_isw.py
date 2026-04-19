#!/usr/bin/env python3
"""
CHANNEL 3 (Tier B consistency): ISW amplitude — LINEAR PROXY.

Phase 2A note (2026-04-19, GPT r18 framing):
In the present retained-pipeline recalc, the ISW channel is kept
numerically unchanged at the linear proxy level.  A fully
self-consistent recalibration of the ISW kernel on the common ECT
background (ect_background.py) remains pending -- it would require
re-integrating the late-time ISW weight function W_ISW(z) under the
new H(z,eps), t(z,eps) and Phi_dot(z,eps) trajectories, which is
beyond the scope of this recalc round.

At the current linear-proxy level:
    A_ISW(eps) = 1 + kappa_ISW * eps,  kappa_ISW ~ 6
This calibration was obtained under LCDM-background Limber weights
and is inherited as-is for Phase 2A.

Methodological caveats:

1. LINEAR PROXY: real |eps| > 0.05 requires non-linear re-computation.
2. Not a strong measurement: A_ISW = 0.96 +/- 0.30 (30% uncertainty).
   Central best-fit eps = -0.007 is consistent with 0 within errors.
3. LCDM-background proxy for Limber weight; ECT-native kernel OPEN.
4. eps < 0 is allowed by the linear model but not by ECT physics;
   unclipped ranges reported; physical floor eps >= 0 applied in
   combine.py before joint-band intersection.

Observational anchor: Krolewski+ 2024 (unWISE x Planck).
"""
import json, os

# Use shared background module (even though ISW doesn't numerically
# depend on it at linear proxy level -- for bookkeeping consistency).
from ect_background import t_0  # noqa: F401 (used in metadata)

A_ISW_obs   = 0.96
A_ISW_sigma = 0.30
kappa_ISW   = 6.0

def A_ISW(eps):    return 1.0 + kappa_ISW * eps
def eps_from_A(A): return (A - 1.0) / kappa_ISW

if __name__ == "__main__":
    eps_best  = eps_from_A(A_ISW_obs)
    eps_lo_1s = eps_from_A(A_ISW_obs - A_ISW_sigma)
    eps_hi_1s = eps_from_A(A_ISW_obs + A_ISW_sigma)
    eps_lo_2s = eps_from_A(A_ISW_obs - 2*A_ISW_sigma)
    eps_hi_2s = eps_from_A(A_ISW_obs + 2*A_ISW_sigma)

    print("="*66)
    print("CHANNEL 3 (Tier B consistency): ISW amplitude -- LINEAR PROXY")
    print("="*66)
    print("Note: kernel NOT recalibrated on ECT-native background in this "
          "recalc round.")
    print("Consistency check only, NOT a measurement.")
    print()
    print(f"A_ISW_obs = {A_ISW_obs} +/- {A_ISW_sigma}")
    print(f"eps_best    = {eps_best:+.4f}")
    print(f"1sigma range  = [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]  (unclipped)")
    print(f"2sigma range  = [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]  (unclipped)")
    print()
    print(f"t_0(eps=0) = {t_0(0.0):.3f} Gyr (from ect_background)")
    print("Upper 1sigma bound eps < 0.043 does not exclude high-z band.")

    result = {
        'channel':     'ISW (Tier B consistency)',
        'tier':        'Tier B',
        'eps_central': float(eps_best),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'kappa_ISW':   float(kappa_ISW),
        'caveat':      'Linear proxy with kappa_ISW~6 calibrated under '
                       'LCDM-background Limber weights; ECT-native '
                       'recalibration OPEN.',
        'notes':       'Phase 2A: NOT recalibrated on common '
                       'ect_background; numerically unchanged at '
                       'linear-proxy level. Unclipped.',
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch3.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved {out}")
