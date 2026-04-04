#!/usr/bin/env python3
"""Species hierarchy of beta5 - GRAYSCALE"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'serif', 'font.size': 10, 'axes.linewidth': 0.8})

u0 = 2.44e18

leptons = {'$e$': 0.000511, r'$\mu$': 0.1057, r'$\tau$': 1.777}
hadrons = {'$p/n$': 0.938}
heavy_q = {'$b$': 4.18, '$t$': 173.0}

groups = [('Leptons', leptons, '0.3'), ('Hadrons', hadrons, '0.55'), ('Heavy quarks', heavy_q, '0.75')]

fig, ax = plt.subplots(figsize=(7.5, 4.2))
y = 0
yticks, ylabels, group_spans = [], [], []

for gname, particles, shade in groups:
    y_start = y
    for name, mass in particles.items():
        beta5 = mass / u0
        lb = np.log10(beta5)
        ax.barh(y, lb, color=shade, edgecolor='black', height=0.6, zorder=3)
        ax.text(lb + 0.3, y, f'$\\sim 10^{{{int(np.round(np.log10(beta5)))}}}$', va='center', ha='left', fontsize=9)
        yticks.append(y); ylabels.append(name); y += 1
    group_spans.append((gname, y_start, y - 1, shade)); y += 0.4

ax.set_yticks(yticks); ax.set_yticklabels(ylabels, fontsize=11)
ax.set_xlabel(r'$\log_{10}\,\beta_5$,    $\beta_5 = m_f\, /\, u_0$' + '\n(larger $\\beta_5$ = stronger microscopic preferred-direction coupling)', fontsize=9)
ax.set_xlim(-24, -13)

for gname, ys, ye, shade in group_spans:
    ax.annotate(gname, xy=(-13.5, (ys+ye)/2), fontsize=8, ha='left', va='center', style='italic', color='0.3',
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=shade, lw=0.8))

ax.axvline(x=np.log10(0.000511/u0), color='0.8', ls=':', lw=0.8, zorder=1)
ax.text(np.log10(0.000511/u0)-0.15, y-0.3, 'electron\nbaseline', fontsize=7, ha='right', va='top', color='0.6')
ax.set_title(r'Species hierarchy of the ECT preferred-direction coupling  $\beta_5 \sim m_f/u_0$', fontsize=10, style='italic')
ax.invert_xaxis(); ax.set_ylim(-0.5, y-0.2)
plt.tight_layout()
plt.savefig('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures/fig_species_beta5.png', dpi=300, bbox_inches='tight')
plt.close()
print("SAVED fig_species_beta5.png")
