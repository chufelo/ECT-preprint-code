#!/usr/bin/env python3
"""
Grayscale summary figure for the preprint §15.5.3.

Reads result_ch*.json and produces fig_epsilon_constraints_bw.pdf:
  - Horizontal bar chart of 5 retained probes
  - 1σ and 2σ intervals shaded at distinct gray levels
  - Joint 1σ band shown as horizontal stripe across all probes
  - All elements grayscale (no colour) per preprint convention

Probes shown in redshift order (high-z first):
  1. Hubble + r_s    (z ~ 1100)
  2. JWST            (z = 10)
  3. Cosmic Chron    (z ~ 0.7)
  4. f σ_8 RSD       (z ~ 0.56)
  5. ISW             (z ~ 0.4)
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR   = os.path.join(SCRIPT_DIR, 'epsilon_convergence')
OUT_DIR    = os.path.join(SCRIPT_DIR, '..', 'figures')

def load(name):
    with open(os.path.join(JSON_DIR, name)) as f:
        return json.load(f)

# Retained 5 probes
PROBES = [
    ('Hubble + $r_s$',               'result_ch1.json', 1100,   'Tier A'),
    ('JWST early-galaxy excess',     'result_ch2.json', 10,     'Tier A'),
    ('Cosmic chronometers ($H(z)$)', 'result_ch4.json', 0.7,    'Tier B'),
    ('$f\\sigma_8$ from RSD',        'result_ch8.json', 0.56,   'Tier B'),
    ('ISW amplitude',                'result_ch3.json', 0.40,   'Tier B'),
]

results = []
for label, fname, zd, tier in PROBES:
    r = load(fname)
    # Apply eps >= 0 physical prior
    lo_1s = max(r['eps_lo_1s'], 0.0)
    lo_2s = max(r['eps_lo_2s'], 0.0)
    hi_1s = r['eps_hi_1s']
    hi_2s = r['eps_hi_2s']
    best  = max(r['eps_central'], 0.0)
    raw_neg = r['eps_central'] < 0
    results.append({
        'label': label, 'z': zd, 'tier': tier,
        'lo_1s': lo_1s, 'hi_1s': hi_1s,
        'lo_2s': lo_2s, 'hi_2s': hi_2s,
        'best': best, 'raw_neg': raw_neg,
    })

# Joint band (intersection of all 1σ intervals in physical region)
joint_lo_1s = max(r['lo_1s'] for r in results)
joint_hi_1s = min(r['hi_1s'] for r in results)
joint_lo_2s = max(r['lo_2s'] for r in results)
joint_hi_2s = min(r['hi_2s'] for r in results)

fig, ax = plt.subplots(figsize=(7.8, 4.2))

# Vertical joint 1sigma band
ax.axvspan(joint_lo_1s, joint_hi_1s, color='0.35', alpha=0.35,
           zorder=1, label=f'Joint $1\\sigma$ $[{joint_lo_1s:.4f},\\,{joint_hi_1s:.4f}]$')
# Vertical joint 2sigma band (lighter)
ax.axvspan(joint_lo_2s, joint_hi_2s, color='0.75', alpha=0.25,
           zorder=0, label=f'Joint $2\\sigma$ $[{joint_lo_2s:.4f},\\,{joint_hi_2s:.4f}]$')

# Bar for each probe
y_positions = np.arange(len(results))[::-1]
for y, r in zip(y_positions, results):
    # 2-sigma bar (lighter)
    if r['hi_2s'] > r['lo_2s']:
        ax.barh(y, r['hi_2s']-r['lo_2s'], left=r['lo_2s'],
                height=0.52, color='0.85', edgecolor='black',
                linewidth=0.5, zorder=2)
    # 1-sigma bar (darker)
    if r['hi_1s'] > r['lo_1s']:
        ax.barh(y, r['hi_1s']-r['lo_1s'], left=r['lo_1s'],
                height=0.52, color='0.55', edgecolor='black',
                linewidth=0.8, zorder=3)
    # Best-fit marker
    marker = 'o' if r['tier'] == 'Tier A' else 's'
    ax.plot([r['best']], [y], marker, color='white',
            markeredgecolor='black', markersize=8,
            markeredgewidth=1.2, zorder=4)

# Lambda CDM line (eps = 0)
ax.axvline(0.0, color='black', linewidth=0.8, linestyle=':', alpha=0.6, zorder=2)

# Y-axis: probe labels
ax.set_yticks(y_positions)
ax.set_yticklabels([r['label'] for r in results], fontsize=10)

# Z-annotation on right side
for y, r in zip(y_positions, results):
    z_label = f"$z\\approx{r['z']}$" if r['z'] >= 10 else f"$z\\approx{r['z']:.2f}$"
    ax.text(0.23, y, z_label, ha='right', va='center',
            fontsize=8.5, color='0.35', transform=ax.get_yaxis_transform())

ax.set_xlim(-0.005, 0.22)
ax.set_xlabel(r'$\varepsilon$ (physical region: $\varepsilon \geq 0$)', fontsize=11)
ax.grid(axis='x', alpha=0.3, linestyle=':')
ax.set_axisbelow(True)

# Legend
legend_elements = [
    Patch(facecolor='0.35', alpha=0.5,
          label=f'Joint $1\\sigma$ band $[{joint_lo_1s:.4f},\\,{joint_hi_1s:.4f}]$'),
    Patch(facecolor='0.75', alpha=0.4,
          label=f'Joint $2\\sigma$ band $[{joint_lo_2s:.4f},\\,{joint_hi_2s:.4f}]$'),
    Patch(facecolor='0.55', edgecolor='black', label='Per-probe $1\\sigma$'),
    Patch(facecolor='0.85', edgecolor='black', label='Per-probe $2\\sigma$'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=8,
          framealpha=0.95, edgecolor='0.4')

plt.tight_layout()

os.makedirs(OUT_DIR, exist_ok=True)
out_pdf = os.path.join(OUT_DIR, 'fig_epsilon_constraints_bw.pdf')
plt.savefig(out_pdf, dpi=300, bbox_inches='tight')
print(f"Saved {out_pdf}")
