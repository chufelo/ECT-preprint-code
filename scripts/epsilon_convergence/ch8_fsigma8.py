#!/usr/bin/env python3
"""
CHANNEL 8 (Tier B consistency): fσ_8 growth rate from redshift-space distortions.

METHODOLOGICAL CAVEATS:

1. **ΛCDM-background proxy**: Ω_m = 0.315, Ω_Λ = 0.685 fixed at
   Planck values.  CAVEAT as elsewhere — not ECT-native.

2. **Nuisance parameter σ_8(0)**: the z=0 matter power amplitude is
   profiled out. This means we test only the SHAPE of fσ_8(z) vs
   redshift, not its absolute normalization.  (Absolute normalization
   is tied to CMB A_s via growth history, which is ε-dependent —
   treating it as free is more conservative.)

3. **Growth equation integrated numerically**: modified Poisson source
   μ_G(a) = a^{-2ε} = (1+z)^{2ε} applied in the ECT-background
   Friedmann equation.  Matter-era scaling Ω_m(a) ∝ a^{-(3+2ε)}/E².

4. **Data compilation**: representative selection of published fσ_8
   measurements (BOSS DR12, 6dFGS, eBOSS, VIPERS).  NOT the full
   compilation with all cross-correlations.

Physics
-------
Growth equation in ε-deformed background:
    d²D/dN² + [2 + d(ln E)/dN] dD/dN = (3/2) Ω_m(a) μ_G(a) D
    N ≡ ln a,    μ_G(a) = a^{-2ε},    Ω_m(a) = Ω_m · a^{-(3+2ε)}/E²(a,ε)

Then fσ_8(z) = f(z) · σ_8(z),  where
    f(z) = d ln D/d ln a |_{a = 1/(1+z)}
    σ_8(z) = σ_8(0) · D(z)/D(0)

Fit: minimize χ² over (ε, σ_8_today), fixed H_0 and Ω_m.

Data
----
Standard compilation of RSD-derived fσ_8(z) from published surveys.
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
import json
import os

# Use shared background module
from ect_background import E_ECT, t_0, OMEGA_M, OMEGA_L

Omega_m = OMEGA_M
Omega_L = OMEGA_L

# ---- Data: (z, fσ_8_obs, σ_fσ_8) — representative compilation ----
RSD_DATA = np.array([
    [0.067, 0.423, 0.055],   # 6dFGS        Beutler+ 2012
    [0.17,  0.510, 0.060],   # 2dF GRASS    Percival+ 2004
    [0.32,  0.384, 0.095],   # BOSS LOWZ    Sanchez+ 2014
    [0.38,  0.497, 0.045],   # BOSS DR12    Alam+ 2017
    [0.51,  0.458, 0.038],   # BOSS DR12    Alam+ 2017
    [0.57,  0.453, 0.022],   # BOSS CMASS   Gil-Marin+ 2017
    [0.61,  0.436, 0.034],   # BOSS DR12    Alam+ 2017
    [0.72,  0.454, 0.139],   # VIPERS       de la Torre+ 2017
    [0.85,  0.315, 0.095],   # SDSS MGS     Howlett+ 2015
    [0.978, 0.379, 0.176],   # eBOSS        de Mattia+ 2020
    [1.23,  0.385, 0.099],   # eBOSS QSO    Hou+ 2021
    [1.48,  0.462, 0.045],   # eBOSS QSO    Neveux+ 2020
    [1.52,  0.420, 0.076],   # eBOSS QSO    Zhao+ 2019
    [1.944, 0.364, 0.106],   # eBOSS QSO    Hou+ 2021
])

z_data    = RSD_DATA[:, 0]
fs8_data  = RSD_DATA[:, 1]
fs8_sig   = RSD_DATA[:, 2]

# ============================================================
# ECT background
# ============================================================
def E_of_a(a, eps):
    return np.sqrt(Omega_m * a**(-3 - 2*eps) + Omega_L * a**(-2*eps))

def dlnE_dN(a, eps):
    """d(ln E)/d(ln a) analytically."""
    E2 = Omega_m * a**(-3 - 2*eps) + Omega_L * a**(-2*eps)
    # d(E²)/d(ln a) = Ω_m * (-(3+2ε)) * a^{-(3+2ε)} + Ω_Λ * (-2ε) * a^{-2ε}
    dE2 = Omega_m * (-(3 + 2*eps)) * a**(-3 - 2*eps) + Omega_L * (-2*eps) * a**(-2*eps)
    return 0.5 * dE2 / E2

def Omega_m_a(a, eps):
    E2 = Omega_m * a**(-3 - 2*eps) + Omega_L * a**(-2*eps)
    return Omega_m * a**(-3 - 2*eps) / E2

# ============================================================
# Growth equation integration
# ============================================================
def growth_rhs(N, y, eps):
    """y = [D, dD/dN].  Returns [dD/dN, d²D/dN²]."""
    D, Dp = y
    a = np.exp(N)
    mu_G = a**(-2*eps)
    dlnE = dlnE_dN(a, eps)
    Om_a = Omega_m_a(a, eps)
    Dpp = -(2.0 + dlnE) * Dp + 1.5 * Om_a * mu_G * D
    return [Dp, Dpp]

def integrate_growth(eps, N_start=np.log(1e-3), N_end=0.0):
    """Integrate from deep matter era to today.  Returns (N_arr, D_arr, Dp_arr)."""
    # Matter-era initial conditions: D ∝ a, so D = a_init, dD/dN = a_init
    D0  = np.exp(N_start)
    Dp0 = np.exp(N_start)
    N_eval = np.linspace(N_start, N_end, 500)
    sol = solve_ivp(
        lambda N, y: growth_rhs(N, y, eps),
        (N_start, N_end),
        [D0, Dp0],
        t_eval=N_eval,
        method='RK45',
        rtol=1e-8, atol=1e-10
    )
    return sol.t, sol.y[0], sol.y[1]

def fsigma8_model(z_arr, eps, sigma_8_today):
    """Compute fσ_8(z) given ε and σ_8(today)."""
    N_arr, D_arr, Dp_arr = integrate_growth(eps)
    # f = dlnD/dlnN at each a
    f_arr = Dp_arr / D_arr
    a_arr = np.exp(N_arr)
    z_arr_grid = 1/a_arr - 1
    # Normalise: D_today = D_arr at N=0
    D_today = D_arr[-1]
    # σ_8(z) = σ_8(today) * D(z) / D(today)
    s8_arr = sigma_8_today * D_arr / D_today
    fs8_arr = f_arr * s8_arr
    # Interpolate at requested z
    order = np.argsort(z_arr_grid)
    return np.interp(z_arr, z_arr_grid[order], fs8_arr[order])

def chi2(eps, sigma_8_today):
    model = fsigma8_model(z_data, eps, sigma_8_today)
    return float(np.sum(((fs8_data - model) / fs8_sig) ** 2))

def chi2_profile(eps):
    """Profile out σ_8(0): find best-fit σ_8 at given ε."""
    res = minimize_scalar(lambda s8: chi2(eps, s8),
                          bounds=(0.5, 1.1), method='bounded')
    return res.fun, res.x

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    print("="*72)
    print("CHANNEL 8 (Tier B): fσ_8 from RSD — growth rate probe")
    print("="*72)
    print("CAVEAT: ΛCDM-background proxy; σ_8(0) profiled as nuisance;")
    print("growth ODE integrated with modified Poisson source μ_G=a^{-2ε}")
    print()
    print(f"N data points: {len(z_data)}")
    print(f"Redshift range: [{z_data.min():.2f}, {z_data.max():.2f}]")
    print()

    # Grid scan (extended range to avoid lower-bound boundary artefact)
    eps_grid = np.linspace(-0.12, 0.15, 136)
    chi2_grid = np.zeros_like(eps_grid)
    s8_grid   = np.zeros_like(eps_grid)
    for i, e in enumerate(eps_grid):
        chi2_grid[i], s8_grid[i] = chi2_profile(e)

    i_best    = int(np.argmin(chi2_grid))
    eps_best  = eps_grid[i_best]
    chi2_best = chi2_grid[i_best]
    s8_best   = s8_grid[i_best]

    print(f"Best-fit ε    = {eps_best:+.4f}")
    print(f"σ_8(0) profiled  = {s8_best:.3f}")
    print(f"χ²_min / dof  = {chi2_best:.2f} / {len(z_data)-2}")
    print()

    # 1σ, 2σ from Δχ²
    dchi2 = chi2_grid - chi2_best
    def find_range(dchi2, eps_grid, threshold):
        below = dchi2 <= threshold
        if not np.any(below):
            return float('nan'), float('nan')
        return float(eps_grid[below].min()), float(eps_grid[below].max())
    eps_lo_1s, eps_hi_1s = find_range(dchi2, eps_grid, 1.0)
    eps_lo_2s, eps_hi_2s = find_range(dchi2, eps_grid, 4.0)

    print(f"1σ range (Δχ²≤1):  [{eps_lo_1s:+.4f}, {eps_hi_1s:+.4f}]")
    print(f"2σ range (Δχ²≤4):  [{eps_lo_2s:+.4f}, {eps_hi_2s:+.4f}]")
    print()

    # Sample table
    print(f"{'ε':>8}  {'χ²':>8}  {'σ_8(0)':>8}  {'Δχ²':>8}")
    for e_t in [-0.05, -0.03, -0.01, 0.0, 0.01, 0.02, 0.03, 0.05, 0.08]:
        c, s8 = chi2_profile(e_t)
        print(f"{e_t:>+8.4f}  {c:>8.2f}  {s8:>8.3f}  {c-chi2_best:>+8.2f}")

    result = {
        'channel':     'fσ_8 RSD (Tier B)',
        'tier':        'Tier B',
        'eps_central': float(eps_best),
        'eps_lo_1s':   float(eps_lo_1s),
        'eps_hi_1s':   float(eps_hi_1s),
        'eps_lo_2s':   float(eps_lo_2s),
        'eps_hi_2s':   float(eps_hi_2s),
        'sigma8_best': float(s8_best),
        'chi2_min':    float(chi2_best),
        'dof':         int(len(z_data) - 2),
        't0_at_eps_central_Gyr': float(t_0(eps_best)),
        'caveat':      'ECT-native background via ect_background; '
                       'σ_8(0) profiled; approximate compilation',
        'notes':       'Growth ODE integrated; μ_G=a^{-2ε}; 14 RSD points'
    }
    out = os.path.join(os.path.dirname(__file__), 'result_ch8.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out}")
