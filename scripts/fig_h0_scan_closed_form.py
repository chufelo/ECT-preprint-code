"""
Regenerate fig:h0_scan using the exact present-epoch closed-form
benchmark relation instead of the q_0 -> 0 leading-order limit.

Closed-form:
  dH/H = sqrt((1 + mu^2 phi^2 / 6) / (e^(beta*phi)*(1+beta*q_0) - (kappa/6)*q_0^2)) - 1

q_0 from slow-roll balance (self-consistent iteration):
  q_0 = (beta/kappa)*exp(beta*phi)*(2 + dlnE/dN) - (mu^2/(3*kappa))*phi/E^2

Fixed: mu = 1.5, kappa = 15 (same as paper)
Varied: beta, phi_0 (same (beta, phi_0) plane as old figure)
Output: ect_h0_scan_bw.pdf (grayscale, same filename/location)
"""
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle

# Fixed parameters
mu_fix = 1.5
kappa_fix = 15.0
Om_m = 0.315
Om_r = 9.2e-5
Om_V = 1.0 - Om_m - Om_r
dlnE_dN_approx = -3.0 * Om_m / 2.0  # ~ -0.472

# Scan grid
beta_grid = np.linspace(0.3, 1.2, 81)
phi_grid = np.linspace(-0.20, -0.02, 81)

BB, PP = np.meshgrid(beta_grid, phi_grid)

def q0_iterate(beta, mu, kappa, phi0, n_iter=15):
    """Self-consistent q_0 from slow-roll balance."""
    q0 = (beta/kappa)*math.exp(beta*phi0)*(2 + dlnE_dN_approx) - (mu**2/(3*kappa))*phi0
    for _ in range(n_iter):
        num = 1.0 + (mu**2/6.0)*phi0**2
        den = math.exp(beta*phi0)*(1 + beta*q0) - (kappa/6)*q0**2
        if den <= 0:
            return q0, float('nan')
        E2 = num / den
        q0 = (beta/kappa)*math.exp(beta*phi0)*(2 + dlnE_dN_approx) - (mu**2/(3*kappa))*phi0/E2
    return q0, E2

def dH_closed_form(beta, mu, kappa, phi0):
    q0, E2 = q0_iterate(beta, mu, kappa, phi0)
    if E2 != E2 or E2 <= 0:  # NaN or negative
        return float('nan')
    return math.sqrt(E2) - 1.0

def dH_q0_zero_limit(beta, mu, phi0):
    """Old paper formula (q_0 -> 0 limit)."""
    return mu**2 * phi0**2 / 12 - beta * phi0 / 2

# Compute both surfaces
ZZ_closed = np.zeros_like(BB)
ZZ_limit = np.zeros_like(BB)
for i in range(BB.shape[0]):
    for j in range(BB.shape[1]):
        b = BB[i, j]
        p = PP[i, j]
        try:
            ZZ_closed[i, j] = dH_closed_form(b, mu_fix, kappa_fix, p) * 100  # %
        except Exception:
            ZZ_closed[i, j] = np.nan
        ZZ_limit[i, j] = dH_q0_zero_limit(b, mu_fix, p) * 100

# Benchmark point
beta_bench = 0.8
phi0_bench = -0.12
dH_bench_closed = dH_closed_form(beta_bench, mu_fix, kappa_fix, phi0_bench) * 100
dH_bench_limit = dH_q0_zero_limit(beta_bench, mu_fix, phi0_bench) * 100
print(f"Benchmark (β=0.8, φ_0=-0.12):")
print(f"  Closed-form ΔH/H = {dH_bench_closed:.3f}%")
print(f"  q0→0 limit ΔH/H  = {dH_bench_limit:.3f}%")

# Plot
fig, ax = plt.subplots(1, 1, figsize=(6.5, 5.0))

# Grayscale contour
levels_closed = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
cs_closed = ax.contourf(BB, PP, ZZ_closed, levels=levels_closed,
                        cmap='Greys', alpha=0.7, extend='both')
# Line contours with labels
cs_lines = ax.contour(BB, PP, ZZ_closed, levels=levels_closed,
                       colors='black', linewidths=0.8, linestyles='solid')
ax.clabel(cs_lines, inline=True, fontsize=9, fmt=r'%.0f%%')

# Overlay q0→0 limit for comparison (dashed)
cs_limit = ax.contour(BB, PP, ZZ_limit, levels=levels_closed,
                       colors='black', linewidths=0.8, linestyles='dashed', alpha=0.6)

# Benchmark point marker
ax.plot(beta_bench, phi0_bench, 'k*', markersize=18, markeredgecolor='white',
        markeredgewidth=1.5, label=f'Benchmark (β=0.8, φ₀=-0.12)')
ax.annotate(f'{dH_bench_closed:.1f}% (closed-form)\n{dH_bench_limit:.1f}% (q₀→0 limit)',
            xy=(beta_bench, phi0_bench), xytext=(1.05, -0.06),
            fontsize=9, ha='left',
            arrowprops=dict(arrowstyle='->', color='black', lw=0.8))

ax.set_xlabel(r'$\beta$', fontsize=13)
ax.set_ylabel(r'$\phi_0$', fontsize=13)
ax.set_title(r'Late-time Hubble shift $\Delta H_0/H_0$ [%]' + '\n' +
             r'$(\mu=1.5,\ \kappa=15)$', fontsize=11)

# Colorbar
cb = fig.colorbar(cs_closed, ax=ax, shrink=0.9, label=r'$\Delta H_0/H_0$ [%] (closed-form)')

# Legend for line styles
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='black', linestyle='solid', label='Closed-form (with self-consistent q₀)'),
    Line2D([0], [0], color='black', linestyle='dashed', alpha=0.6, label='q₀→0 leading-order limit'),
    Line2D([0], [0], marker='*', color='white', markerfacecolor='black',
           markersize=14, markeredgecolor='black', linestyle='', label='Benchmark point')
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8, framealpha=0.9)

ax.grid(True, alpha=0.3, linestyle=':')

plt.tight_layout()

out_pdf = '/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/ect_h0_scan_bw.pdf'
plt.savefig(out_pdf, dpi=200, bbox_inches='tight')
print(f"Saved: {out_pdf}")
plt.close()
