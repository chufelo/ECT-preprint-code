"""
Regenerate fig:h0_scan using exact present-epoch closed-form benchmark.

Annotation for benchmark star: placed compactly ABOVE-LEFT of the star,
no pointer line — keeps it clear of legend.
"""
import numpy as np
import math
import matplotlib.pyplot as plt

# Fixed
mu_fix = 1.5
kappa_fix = 15.0
Om_m = 0.315
Om_r = 9.2e-5
Om_V = 1.0 - Om_m - Om_r
dlnE_dN_approx = -3.0 * Om_m / 2.0

beta_grid = np.linspace(0.3, 1.2, 81)
phi_grid = np.linspace(-0.20, -0.02, 81)
BB, PP = np.meshgrid(beta_grid, phi_grid)

def q0_iterate(beta, mu, kappa, phi0, n_iter=15):
    q0 = (beta/kappa)*math.exp(beta*phi0)*(2 + dlnE_dN_approx) - (mu**2/(3*kappa))*phi0
    for _ in range(n_iter):
        num = 1.0 + (mu**2/6.0)*phi0**2
        den = math.exp(beta*phi0)*(1 + beta*q0) - (kappa/6)*q0**2
        if den <= 0: return q0, float('nan')
        E2 = num / den
        q0 = (beta/kappa)*math.exp(beta*phi0)*(2 + dlnE_dN_approx) - (mu**2/(3*kappa))*phi0/E2
    return q0, E2

def dH_closed_form(beta, mu, kappa, phi0):
    q0, E2 = q0_iterate(beta, mu, kappa, phi0)
    if E2 != E2 or E2 <= 0: return float('nan')
    return math.sqrt(E2) - 1.0

def dH_q0_zero_limit(beta, mu, phi0):
    return mu**2 * phi0**2 / 12 - beta * phi0 / 2

ZZ_closed = np.zeros_like(BB)
ZZ_limit = np.zeros_like(BB)
for i in range(BB.shape[0]):
    for j in range(BB.shape[1]):
        b = BB[i, j]; p = PP[i, j]
        try:
            ZZ_closed[i, j] = dH_closed_form(b, mu_fix, kappa_fix, p) * 100
        except Exception:
            ZZ_closed[i, j] = np.nan
        ZZ_limit[i, j] = dH_q0_zero_limit(b, mu_fix, p) * 100

beta_bench = 0.8
phi0_bench = -0.12
dH_bench_closed = dH_closed_form(beta_bench, mu_fix, kappa_fix, phi0_bench) * 100
dH_bench_limit = dH_q0_zero_limit(beta_bench, mu_fix, phi0_bench) * 100
print(f"Benchmark: closed-form {dH_bench_closed:.3f}%, limit {dH_bench_limit:.3f}%")

fig, ax = plt.subplots(1, 1, figsize=(6.5, 5.0))

levels_closed = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
cs_closed = ax.contourf(BB, PP, ZZ_closed, levels=levels_closed,
                        cmap='Greys', alpha=0.7, extend='both')
cs_lines = ax.contour(BB, PP, ZZ_closed, levels=levels_closed,
                       colors='black', linewidths=0.8, linestyles='solid')
ax.clabel(cs_lines, inline=True, fontsize=9, fmt=r'%.0f%%')

cs_limit = ax.contour(BB, PP, ZZ_limit, levels=levels_closed,
                       colors='black', linewidths=0.8, linestyles='dashed', alpha=0.6)

# Benchmark point — annotation COMPACTLY to upper-left, no pointer line
ax.plot(beta_bench, phi0_bench, 'k*', markersize=18, markeredgecolor='white',
        markeredgewidth=1.5)
# Place text above-left of the star, close enough that visual association is obvious
ax.annotate(f'{dH_bench_closed:.1f}% (closed-form)\n{dH_bench_limit:.1f}% ($q_0{{\\to}}0$ limit)',
            xy=(beta_bench, phi0_bench),
            xytext=(beta_bench - 0.02, phi0_bench + 0.018),
            fontsize=8.5, ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='black', linewidth=0.5, alpha=0.9))

ax.set_xlabel(r'$\beta$', fontsize=13)
ax.set_ylabel(r'$\phi_0$', fontsize=13)
ax.set_title(r'Late-time Hubble shift $\Delta H_0/H_0$ [%]' + '\n' +
             r'$(\mu=1.5,\ \kappa=15)$', fontsize=11)

cb = fig.colorbar(cs_closed, ax=ax, shrink=0.9, label=r'$\Delta H_0/H_0$ [%] (closed-form)')

from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='black', linestyle='solid', label='Closed-form (with self-consistent $q_0$)'),
    Line2D([0], [0], color='black', linestyle='dashed', alpha=0.6, label='$q_0{\\to}0$ leading-order limit'),
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
