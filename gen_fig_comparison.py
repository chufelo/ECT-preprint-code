#!/usr/bin/env python3
"""Coupling comparison - markers, GRAYSCALE"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'serif', 'font.size': 10, 'axes.linewidth': 0.8})

fig, ax = plt.subplots(figsize=(7.5, 4.5))

interactions = ['Strong\n' + r'$\alpha_s$', 'EM\n' + r'$\alpha$',
                'Gravity\n' + r'$G_N m^2/\hbar c$', 'ECT fifth\n' + r'$\beta_5 = m_f/u_0$']

vals_e = [0, -2.14, -44.8, -22.3]
vals_p = [0, -2.14, -38.2, -18.4]
x = np.arange(len(interactions))

ax.scatter(x-0.12, vals_e, s=120, marker='o', color='0.2', edgecolors='black', linewidths=0.8, zorder=5, label='electron scale')
ax.scatter(x+0.12, vals_p, s=120, marker='s', color='0.6', edgecolors='black', linewidths=0.8, zorder=5, label='proton scale')

for i in range(len(interactions)):
    ax.plot([x[i]-0.12, x[i]+0.12], [vals_e[i], vals_p[i]], '-', color='0.7', lw=1.0, zorder=2)

for i, (ve, vp) in enumerate(zip(vals_e, vals_p)):
    if ve < -5:
        ax.text(x[i]-0.12, ve-2.5, f'$10^{{{int(round(ve))}}}$', ha='center', fontsize=7, color='0.3')
    else:
        ax.text(x[i]-0.12, ve+2, r'$\sim\!1$', ha='center', fontsize=7, color='0.3')
    if vp < -5 and abs(vp-ve) > 3:
        ax.text(x[i]+0.12, vp-2.5, f'$10^{{{int(round(vp))}}}$', ha='center', fontsize=7, color='0.5')

ax.set_xticks(x); ax.set_xticklabels(interactions, fontsize=9)
ax.set_ylabel(r'$\log_{10}$(characteristic dimensionless suppression)', fontsize=9)
ax.set_ylim(-52, 8); ax.axhline(0, color='black', lw=0.5)
ax.legend(fontsize=8, loc='lower right', framealpha=0.9, edgecolor='0.7')

ax.annotate(r'$\beta_5 > \alpha_G$ at particle scale,' + '\nbut these are different\nkinds of couplings',
            xy=(2.5, -31), fontsize=8, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='0.6', lw=0.8))

ax.set_title('Schematic comparison of characteristic dimensionless\ninteraction suppressions (not identical force laws)', fontsize=10, style='italic')
plt.tight_layout()
plt.savefig('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_coupling_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("SAVED fig_coupling_comparison.png")
