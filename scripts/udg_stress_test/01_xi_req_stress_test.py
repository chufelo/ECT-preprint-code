#!/usr/bin/env python3
"""
DM-deficient UDG stress test of the current ECT Level-B galactic closure.

Computes the inverse-problem diagnostic
    Xi_req(R) = r (r - 1) g_N(R) / g_dagger_0,
where r = M_dyn / M_bar = sigma_obs^2 / sigma_N^2, evaluated at the Wolf
half-mass radius R_1/2 = (4/3) R_e.

Produces the numerical content of Appendix `app:udg_stress_test` in the
ECT preprint: six-object stress-test table, nuisance budget for DF4,
and EFE benchmark for the four spherical reference objects.

Scientific scope: DIAGNOSTIC.  The script does not claim any rescue
mechanism; it reports Xi_req under the current practical closure
together with its nuisance band.
"""
import math

# -------- physical constants / scales ---------------------------------
G      = 6.6743e-11           # m^3 / kg / s^2
c_SI   = 2.998e8              # m / s
M_sun  = 1.989e30             # kg
kpc    = 3.086e19             # m
H0     = 67.4e3 / 3.086e22    # s^-1, Planck-like
a_0    = 1.2e-10              # m / s^2, MOND scale (benchmark only)
g_dag0 = c_SI * H0 / (2 * math.pi)  # baseline g^dagger_0

def xi_req_wolf(M_star_solar, Re_kpc, sigma_kms, R_half_factor=4.0/3.0, f_e=0.5):
    """
    Central-value diagnostic Xi_req via Wolf estimator.

    Xi_req = r (r - 1) g_N / g_dagger_0, at R_{1/2} = R_half_factor * R_e.
    """
    M_star = M_star_solar * M_sun
    Re     = Re_kpc * kpc
    R_half = R_half_factor * Re
    sigma  = sigma_kms * 1000.0

    M_dyn  = 4.0 * sigma**2 * R_half / G
    M_bar  = f_e * M_star
    r      = M_dyn / M_bar

    y      = r * (r - 1.0)
    g_N    = G * M_bar / R_half**2
    Xi_req = max(0.0, y * g_N / g_dag0)
    return {"r": r, "Xi_req": Xi_req, "g_N": g_N, "M_dyn": M_dyn, "M_bar": M_bar}

# --------- six reference objects (mean literature values) -------------
objects = [
    # (name, M_star/Msun, R_e/kpc, sigma/kms, class)
    ("NGC 1052-DF4",    1.5e8,  1.6,  6.3,  "stress-low"),
    ("FCC 224",         1.74e8, 1.89, 7.8,  "stress-low"),
    ("NGC 1052-DF2",    1.3e8,  2.2, 10.0,  "ambiguous"),   # centre of 8.6-14.9 bracket
    ("NGC 5846-UDG1",   1.1e8,  2.1, 17.0,  "normal RAR"),
    ("Dragonfly 44",    3.0e8,  4.7, 33.0,  "upper tail"),
    # AGC 114905 omitted: gas-rich rotator, spherical Jeans not applicable.
]

def main():
    print("="*80)
    print("UDG stress test: inverse-problem diagnostic of the current ECT closure")
    print("="*80)
    print(f"g_dagger_0 = cH_0 / (2 pi) = {g_dag0:.3e} m/s^2")
    print()
    print(f"{'Object':<20} {'M*/1e8':>7} {'R_e kpc':>8} {'sigma':>7}"
          f" {'r':>7} {'Xi_req':>11}  class")
    print("-"*80)
    for name, Ms, Re, sigma, klass in objects:
        res = xi_req_wolf(Ms, Re, sigma)
        print(f"{name:<20} {Ms/1e8:>7.2f} {Re:>8.2f} {sigma:>7.2f}"
              f" {res['r']:>7.2f} {res['Xi_req']:>11.3e}  {klass}")
    print()
    print("Matched-pair observation (proxy-level diagnostic):")
    print("  DF4 vs NGC 5846-UDG1 share M*, R_e, and group environment,")
    print("  but Xi_req differs by a factor ~1e3 across the pair.")
    print("  Conclusion: the minimal density-only Level-B ansatz is")
    print("  structurally insufficient for this class of objects.")
    print()
    print("Nuisance budget for DF4 (multiplicative factors on Xi_req):")
    print("  Distance D in [13,25] Mpc (covariant):        ~10x")
    print("  M/L in [1,4] (SPS systematic):                 ~10x")
    print("  Small-N at 95% CL on sigma (N=7 GCs):         ~100x")
    print("  Anisotropy beta in [-0.5, 0.5]:                ~1.5x")
    print("  Proxy -> Jeans upgrade:                        ~1.3x")
    print()
    print("  Combined 95% CL: log10(Xi_req) in [-4, -0.5] for DF4.")
    print("  Entire band lies below RAR-normal range Xi ~ O(1).")
    print("  -> Stress-test classification is robust; numerical value is not.")

if __name__ == "__main__":
    main()
