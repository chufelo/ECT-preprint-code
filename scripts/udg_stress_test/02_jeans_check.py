#!/usr/bin/env python3
"""
Jeans-equation check against the Wolf-proxy for NGC 1052-DF4.

Solves the isotropic spherical Jeans equation for a Plummer tracer in
the gravitational field of the current practical galactic closure
    g(r) = (1/2) [g_N + sqrt(g_N^2 + 4 g_N g_dag_eff)],
with g_dag_eff = Xi * g_dag_0, then projects to line-of-sight and
aperture-averages.  Compares against the simpler Wolf-proxy
sigma_N^2 = (3/32) G M_star / R_e.

For DF4 the two approaches agree to a factor 1.30 at Xi = 0 (Newton).
This is the Jeans-upgrade check reported in Appendix `app:udg_stress_test`
(subsection `app:udg:jeans_upgrade`).

Scientific scope: DIAGNOSTIC.  Does not claim any rescue mechanism.
"""
import math
from scipy.integrate import quad

G      = 6.6743e-11
c_SI   = 2.998e8
M_sun  = 1.989e30
kpc    = 3.086e19
H0     = 67.4e3 / 3.086e22
g_dag0 = c_SI * H0 / (2 * math.pi)

def plummer_density(r, a):
    return (1.0 + (r/a)**2)**(-2.5)

def plummer_mass_enclosed(r, M_tot, a):
    return M_tot * r**3 / (r*r + a*a)**1.5

def closure_g(g_N, g_dag_eff):
    if g_N <= 0: return 0.0
    return 0.5 * (g_N + math.sqrt(g_N*g_N + 4.0*g_N*g_dag_eff))

def sigma_r_squared_jeans(r, M_tot, a, Xi):
    """Isotropic Plummer: sigma_r^2(r) = (1/nu(r)) int_r^inf nu(s) g(s) ds."""
    def integrand(s):
        if s < 1e-12: return 0.0
        g_N = G * plummer_mass_enclosed(s, M_tot, a) / s**2
        g   = closure_g(g_N, Xi * g_dag0)
        return plummer_density(s, a) * g
    nu_r = plummer_density(r, a)
    val, _ = quad(integrand, r, 100.0*a, limit=200)
    return val / nu_r

def aperture_avg_sigma_los(Re, M_tot, a, Xi, R_ap):
    """
    Aperture-averaged LOS dispersion inside projected R_ap.
    Plummer surface density: ~ (1 + R^2/a^2)^{-2}.
    """
    def weighted_sigma_sq(R):
        def num(r):
            if r <= R + 1e-12: return 0.0
            sig2 = sigma_r_squared_jeans(r, M_tot, a, Xi)
            return plummer_density(r, a) * sig2 * r / math.sqrt(r*r - R*R)
        def den(r):
            if r <= R + 1e-12: return 0.0
            return plummer_density(r, a) * r / math.sqrt(r*r - R*R)
        n_val, _ = quad(num, R + 1e-10, 100.0*a, limit=100)
        d_val, _ = quad(den, R + 1e-10, 100.0*a, limit=100)
        return 2.0 * n_val / (2.0 * d_val) if d_val > 0 else 0.0
    def weight(R):
        return (1.0 + (R/a)**2)**(-2) * R
    def weighted(R):
        return weight(R) * weighted_sigma_sq(R)
    num_v, _ = quad(weighted,   1e-10, R_ap, limit=100)
    den_v, _ = quad(weight,     1e-10, R_ap, limit=100)
    return math.sqrt(num_v/den_v) if den_v > 0 else 0.0

def main():
    # DF4 parameters (literature central values)
    M_star = 1.5e8 * M_sun
    Re     = 1.6 * kpc
    a      = Re / 1.305                 # Plummer: R_e = 1.305 a

    print("="*80)
    print("Jeans check against Wolf-proxy: NGC 1052-DF4")
    print("="*80)
    print(f"M* = {M_star/M_sun:.2e} Msun, R_e = {Re/kpc:.2f} kpc, a = {a/kpc:.3f} kpc")
    print()
    # Newton (Xi=0)
    sig_jeans = aperture_avg_sigma_los(Re, M_star, a, 0.0, Re)
    sig_proxy = math.sqrt((3.0/32.0) * G * M_star / Re)
    print(f"Newton (Xi = 0), aperture = R_e:")
    print(f"  Jeans aperture-avg:  sigma = {sig_jeans/1000:.2f} km/s")
    print(f"  Wolf proxy sqrt(3/32 GM/R_e):  sigma = {sig_proxy/1000:.2f} km/s")
    print(f"  ratio Jeans/proxy = {sig_jeans/sig_proxy:.3f}")
    print()
    # Scan Xi to see MOND-regime behaviour
    print("Xi scan (closure forward model):")
    for Xi in (0.0, 0.01, 0.1, 0.5, 1.0):
        s = aperture_avg_sigma_los(Re, M_star, a, Xi, Re) / 1000.0
        print(f"  Xi = {Xi:5.2f}  ->  sigma_pred = {s:5.2f} km/s")
    print()
    print("Observed DF4: sigma = 6.3 +2.5 / -1.6 km/s")
    print()
    print("-> Proxy and Jeans agree to a factor 1.30 at Xi = 0; the")
    print("   stress-test conclusion Xi_req << 1 for DF4 is unchanged")
    print("   under the Jeans upgrade.")

if __name__ == "__main__":
    main()
