#!/usr/bin/env python3
"""
CHANNEL 2 (Tier A): JWST early-galaxy excess WITH ECT-native time budget.

Updated 2026-04-19: uses shared ect_background module to propagate
t(z, eps) through the stellar-assembly time budget, in addition to
the Press-Schechter growth enhancement.

Physics: the JWST excess factor at z_JWST is the PRODUCT of two
eps-dependent pieces:

  R(eps) = R_PS(eps) * R_time(eps)

(1) R_PS = Press-Schechter tail ratio (original model):
    R_PS(eps) = exp[ nu^2 / 2 * (1 - 1/f) ],  f = (1+z)^(2*eps)
    This grows with eps (G_eff enhancement -> earlier growth ->
    lower nu in ECT -> more tail halos).

(2) R_time = stellar-assembly time-budget factor:
    The stellar mass observed at z_obs is built up during the
    interval between formation (z_form ~ 20) and observation
    (z_obs = 10).  If mean stellar assembly proceeds at a rate
    that is approximately linear in available time, the visible
    stellar mass scales as:
        Delta_t(z_form -> z_obs, eps) / Delta_t(z_form -> z_obs, eps=0)
    For eps > 0 in the ECT-native background, this ratio is < 1
    (time budget SHRINKS), partially counteracting (1).

The two effects compete: PS enhancement pushes eps upward,
time budget compression pulls the extracted eps upward even more
(since a larger eps is needed to reach the same observed R).

This second factor is the crucial correction missed by the earlier
proxy that held t(z) fixed at LambdaCDM values.

Solve R(eps) = R_obs for eps.
"""
import numpy as np
from scipy.optimize import brentq
import json, os

from ect_background import t_at_z

# ---- Observational inputs ----
z_JWST          = 10.0
z_form          = 20.0   # Typical formation redshift for JWST galaxies
nu_central      = 5.0
nu_low, nu_high = 4.0, 6.0
R_central       = 10.0
R_low, R_high   = 3.0, 100.0

# ---- Model ----
def R_PS(eps, nu, z):
    """Press-Schechter tail ratio ECT/LCDM at z."""
    f = (1.0 + z)**(2.0*eps)
    return np.exp(0.5 * nu**2 * (1.0 - 1.0/f))

def R_time(eps, z_form=z_form, z_obs=z_JWST):
    """Stellar-assembly time-budget factor ECT/LCDM.

    Ratio of Delta t(z_form -> z_obs) in ECT vs LCDM.
    For eps > 0 the interval SHRINKS, so R_time < 1.
    """
    dt_ECT  = t_at_z(z_obs, eps) - t_at_z(z_form, eps)
    dt_LCDM = t_at_z(z_obs, 0.0) - t_at_z(z_form, 0.0)
    return dt_ECT / dt_LCDM

def R_total(eps, nu, z=z_JWST):
    """Full JWST excess factor including time budget."""
    return R_PS(eps, nu, z) * R_time(eps, z_form, z)

def eps_from_R_total(R_target, nu, z=z_JWST):
    try:
        return brentq(lambda e: R_total(e, nu, z) - R_target,
                      1e-4, 0.30)
    except Exception:
        return np.nan

if __name__ == "__main__":
    print("="*72)
    print("CHANNEL 2 (Tier A): JWST with ECT-native time budget")
    print("="*72)
    print(f"z_form = {z_form}, z_JWST = {z_JWST}")
    print(f"nu = {nu_central} (range {nu_low}-{nu_high})")
    print(f"R_obs = {R_central}x (range {R_low}-{R_high}x)")
    print()

    # Show decomposition
    print(f"{'eps':>7}  {'R_PS':>8}  {'R_time':>8}  {'R_total':>8}  "
          f"{'Delta_t':>9}")
    for e in [0.0, 0.010, 0.020, 0.030, 0.040, 0.050, 0.060]:
        rps   = R_PS(e, nu_central, z_JWST)
        rtime = R_time(e)
        rtot  = rps * rtime
        dt    = (t_at_z(z_JWST, e) - t_at_z(z_form, e)) * 1000
        print(f"{e:>7.4f}  {rps:>8.3f}  {rtime:>8.4f}  {rtot:>8.3f}  "
              f"{dt:>7.2f} Myr")
    print()

    # Solve for central eps under different assumption sets:
    eps_central_OLD = brentq(lambda e: R_PS(e, nu_central, z_JWST) - R_central,
                              1e-4, 0.30)
    eps_central_NEW = eps_from_R_total(R_central, nu_central)

    print(f"OLD (PS only) eps for R={R_central}, nu={nu_central}: "
          f"{eps_central_OLD:.4f}")
    print(f"NEW (PS+time) eps for R={R_central}, nu={nu_central}: "
          f"{eps_central_NEW:.4f}")
    print(f"Shift: {eps_central_NEW - eps_central_OLD:+.4f}")
    print()

    # Scan over nu for 1-sigma: keep R=R_central, vary nu in [nu_low, nu_high]
    eps_1s_lo = eps_from_R_total(R_central, nu_high)   # larger nu -> smaller eps
    eps_1s_hi = eps_from_R_total(R_central, nu_low)

    # 2-sigma: vary R too
    candidates = []
    for nu in [nu_low, nu_central, nu_high]:
        for R in [R_low, R_central, R_high]:
            e = eps_from_R_total(R, nu)
            if np.isfinite(e):
                candidates.append(e)
    eps_2s_lo = float(np.min(candidates))
    eps_2s_hi = float(np.max(candidates))

    print(f"NEW (ECT-native, with time budget):")
    print(f"  eps_central = {eps_central_NEW:.4f}")
    print(f"  1-sigma (nu only) [{eps_1s_lo:.4f}, {eps_1s_hi:.4f}]")
    print(f"  2-sigma (nu+R)    [{eps_2s_lo:.4f}, {eps_2s_hi:.4f}]")
    print()
    print(f"  t_0(eps_central) = {t_at_z(0.0, eps_central_NEW):.3f} Gyr")
    print(f"  t(z=10, eps_central) = "
          f"{t_at_z(z_JWST, eps_central_NEW)*1000:.2f} Myr")

    result = {
        'channel':     'JWST (Tier A, with ECT-native time budget)',
        'tier':        'Tier A',
        'eps_central': float(eps_central_NEW),
        'eps_lo_1s':   float(eps_1s_lo),
        'eps_hi_1s':   float(eps_1s_hi),
        'eps_lo_2s':   float(eps_2s_lo),
        'eps_hi_2s':   float(eps_2s_hi),
        't0_at_eps_central_Gyr':  float(t_at_z(0.0, eps_central_NEW)),
        't_zJWST_eps_central_Myr': float(t_at_z(z_JWST, eps_central_NEW)*1000),
        'eps_central_OLD_PS_only': float(eps_central_OLD),
        'shift_vs_PS_only':        float(eps_central_NEW - eps_central_OLD),
        'caveat':      'ECT-native background via ect_background; includes '
                       'PS enhancement + stellar-assembly time-budget.',
        'notes':       f'R={R_central}x (range {R_low}-{R_high}x), '
                       f'nu={nu_central} ({nu_low}-{nu_high}), '
                       f'z_form={z_form} -> z_obs={z_JWST}',
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch2.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved {out}")
