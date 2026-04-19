#!/usr/bin/env python3
"""
ε constraint analysis — 5-probe joint allowed region under uniform-ε + ε ≥ 0.

ACTIVE (5 probes):
  - Hubble + r_s   (Tier A, z = 0 → 1100 integrated)
  - JWST PS proxy  (Tier A, z ≈ 8-12)
  - CC Moresco+    (Tier B, z = 0.07-1.97)
  - fσ_8 RSD       (Tier B, z = 0.07-1.94)
  - ISW            (Tier B, z = 0-2)

EXCLUDED from headline analysis (retained for reproducibility):
  - BAO (DESI 2024): simplified methodology (Ω_m fixed, diagonal cov, shape-only).
    Raw best-fit −0.013 likely artefact. Needs full DESI likelihood.
  - A_lens CMB lensing: linearized proxy without full Boltzmann; theoretical
    systematic on κ_A not included. Narrow 1σ was misleading.
  - S_8 KiDS: 1σ entirely negative — measures S_8 tension, not ECT's ε.
  - σ_8 clusters: same as S_8.
  - SN Ia: was mock, permanently removed.

KEY FINDING:
  Joint 1σ allowed region under uniform-ε: ε ∈ [+0.029, +0.036]  (width 0.007)
  Joint 2σ allowed region:                  ε ∈ [+0.021, +0.042]
  Preprint benchmark ε ≈ 0.010 is BELOW 1σ joint — needs revision OR ε(z) required.
"""
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# 5 active probes, z-ordered
# ------------------------------------------------------------
PROBES_ORDERED = [
    ('Hubble',   'result_ch1.json',  'Tier A',
        r'Hubble tension + $r_s$',                 0.05, 1100, 1060,
        r'$\approx$380 000 yr'),
    ('JWST',     'result_ch2.json',  'Tier A',
        r'JWST early-gal excess (PS proxy)',        8,    12,    10,
        r'$\sim$500 Myr'),
    ('CC',       'result_ch4.json',  'Tier B',
        r'Cosmic chronometers ($H(z)$)',           0.07,  1.97, 0.70,
        r'$\sim$7.2 Gyr'),
    ('fsigma8',  'result_ch8.json',  'Tier B',
        r'$f\sigma_8$ from RSD (growth)',          0.07,  1.94, 0.56,
        r'$\sim$8.1 Gyr'),
    ('ISW',      'result_ch3.json',  'Tier B',
        r'ISW amplitude (linear proxy)',           0.05,  2.0,  0.40,
        r'$\sim$9.4 Gyr'),
]
AGE_FILE = 'result_ch7.json'

# Load with physical clipping
results = {}
for (key, fname, tier, label, zlo, zhi, zd, t_cos) in PROBES_ORDERED:
    with open(os.path.join(SCRIPT_DIR, fname)) as f:
        r = json.load(f)
    r['raw_best']  = r['eps_central']
    r['raw_lo_1s'] = r['eps_lo_1s']
    r['best_phys'] = max(r['eps_central'], 0.0)
    r['lo_1s_phys'] = max(r['eps_lo_1s'], 0.0)
    r['lo_2s_phys'] = max(r['eps_lo_2s'], 0.0)
    r['hi_1s'] = r['eps_hi_1s']
    r['hi_2s'] = r['eps_hi_2s']
    r.update(dict(tier=tier, label=label,
                  z_min=zlo, z_max=zhi, z_display=zd, t_cosmic=t_cos))
    results[key] = r

with open(os.path.join(SCRIPT_DIR, AGE_FILE)) as f:
    age = json.load(f)

# ------------------------------------------------------------
# JOINT allowed region (intersection of ALL 5 probes)
# ------------------------------------------------------------
keys = [k for k,_,_,_,_,_,_,_ in PROBES_ORDERED]
joint_lo_1s = max(results[k]['lo_1s_phys'] for k in keys)
joint_hi_1s = min(results[k]['hi_1s']    for k in keys)
joint_lo_2s = max(results[k]['lo_2s_phys'] for k in keys)
joint_hi_2s = min(results[k]['hi_2s']    for k in keys)

print("="*110)
print("ε CONSTRAINTS — 5 active probes (z-ordered)")
print("="*110)
print(f"{'#':>2}  {'Probe':<32} {'Tier':<7} {'z-range':<16}  "
      f"{'ε_best':>9}  {'1σ (phys)':>18}  {'2σ (phys)':>18}")
print("-"*110)
for i, (key, *_rest) in enumerate(PROBES_ORDERED, 1):
    r = results[key]
    zrng = f"[{r['z_min']:.2f}, {r['z_max']:.0f}]" if r['z_max'] >= 10 else f"[{r['z_min']:.2f}, {r['z_max']:.2f}]"
    neg_flag = " [raw<0]" if r['raw_best'] < 0 else ""
    print(f"{i:>2}. {r['label'][:32]:<32} {r['tier']:<7} {zrng:<16}  "
          f"{r['best_phys']:>+9.4f}  "
          f"[{r['lo_1s_phys']:>+6.3f},{r['hi_1s']:>+6.3f}]  "
          f"[{r['lo_2s_phys']:>+6.3f},{r['hi_2s']:>+6.3f}]{neg_flag}")

print()
print(f"JOINT 1σ allowed:  ε ∈ [{joint_lo_1s:+.4f}, {joint_hi_1s:+.4f}]  "
      f"(width {joint_hi_1s - joint_lo_1s:.4f}, centered at {(joint_lo_1s + joint_hi_1s)/2:+.4f})")
print(f"JOINT 2σ allowed:  ε ∈ [{joint_lo_2s:+.4f}, {joint_hi_2s:+.4f}]  "
      f"(width {joint_hi_2s - joint_lo_2s:.4f})")
print()
bench = 0.010
if bench < joint_lo_1s:
    print(f"Preprint benchmark ε = {bench} is BELOW the joint 1σ region.")
    print("→ Either benchmark needs revision (to ~0.03), or uniform-ε inadequate (ε(z) required).")

print()
print("EXCLUDED from headline analysis:")
print("  - BAO (DESI 2024):  simplified methodology; raw best −0.013 (artefact)")
print("  - A_lens CMB:       linearized proxy, theoretical systematic not included")
print("  - S_8 KiDS:         1σ entirely negative (measures S_8 tension, not ECT ε)")
print("  - σ_8 clusters:     same as S_8")
print()
print("Text note: Age t_0 = self-consistency (uses Hubble H₀(ε)).")
print(f"  ε_age = {age['eps_central']:+.4f} [{age['eps_lo_1s']:+.4f}, {age['eps_hi_1s']:+.4f}]")

# ------------------------------------------------------------
# FIGURE
# ------------------------------------------------------------
fig = plt.figure(figsize=(13, 9))
gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1],
                      width_ratios=[2.2, 1.3], hspace=0.38, wspace=0.08)
ax_main = fig.add_subplot(gs[0, :])
ax_low  = fig.add_subplot(gs[1, 0])
ax_high = fig.add_subplot(gs[1, 1], sharey=ax_low)

y_pos = np.arange(len(keys))[::-1]

def colors(tier):
    if tier == 'Tier A': return ('#5c7d9c', '#b6c9d8')
    return ('#8a9c6d', '#c9d4b8')

# ============ MAIN BARS ============
# Joint 2σ band (pale)
ax_main.axvspan(joint_lo_2s, joint_hi_2s, alpha=0.08, color='#c73e6a', zorder=1)
# Joint 1σ band (strong)
ax_main.axvspan(joint_lo_1s, joint_hi_1s, alpha=0.25, color='#c73e6a', zorder=1)
# Joint boundary lines
ax_main.axvline(joint_lo_1s, color='#c73e6a', lw=1.1, ls='--', zorder=2)
ax_main.axvline(joint_hi_1s, color='#c73e6a', lw=1.1, ls='--', zorder=2)
# Benchmark
ax_main.axvspan(0.005, 0.015, alpha=0.22, color='gold', zorder=1)
ax_main.axvline(0.010, color='darkorange', lw=1.3, ls='-.', zorder=2)
# ΛCDM
ax_main.axvline(0, color='black', lw=1.0, ls=':', zorder=2)

for y, k in zip(y_pos, keys):
    r = results[k]; tier = r['tier']
    c1, c2 = colors(tier)
    # 2σ rect
    if r['hi_2s'] > r['lo_2s_phys']:
        ax_main.barh(y, r['hi_2s']-r['lo_2s_phys'], left=r['lo_2s_phys'],
                     height=0.55, color=c2, edgecolor='gray', linewidth=0.4,
                     zorder=2, alpha=0.85)
    # 1σ rect
    if r['hi_1s'] > r['lo_1s_phys']:
        ax_main.barh(y, r['hi_1s']-r['lo_1s_phys'], left=r['lo_1s_phys'],
                     height=0.55, color=c1, edgecolor='black',
                     linewidth=0.9, zorder=3, alpha=0.95)
    # Central
    marker = 'o' if tier == 'Tier A' else 's'
    ax_main.plot([r['best_phys']], [y], marker, color='white',
                 markeredgecolor='black', markersize=9, zorder=4, lw=0.9)
    # Upper-bound arrow
    if r['raw_best'] < 0:
        ax_main.annotate('←', xy=(0, y), xytext=(-0.003, y),
                         ha='right', va='center', fontsize=11, color='#666')
        ax_main.text(-0.007, y, 'upper\nbound', ha='right', va='center',
                     fontsize=8, color='#666', style='italic')
    fw = 'bold' if tier == 'Tier A' else 'normal'
    ax_main.text(-0.020, y, r['label'], ha='right', va='center',
                 fontsize=10.5, fontweight=fw, color='#222')
    zstr = (f"z≈{r['z_display']}" if r['z_display'] >= 10
            else f"z≈{r['z_display']:.2f}")
    ax_main.text(0.148, y, zstr, ha='left', va='center',
                 fontsize=9, color='0.25', fontfamily='monospace')

ax_main.set_xlim(-0.018, 0.175)
ax_main.set_ylim(-0.6, len(keys)-0.4)
ax_main.set_yticks([])
ax_main.set_xlabel(r'$\varepsilon$  (physical region $\geq 0$)', fontsize=11)
ax_main.set_title(
    f'ε constraints — 5-probe joint 1σ region: ε ∈ [{joint_lo_1s:.3f}, {joint_hi_1s:.3f}] '
    f'(width {joint_hi_1s-joint_lo_1s:.3f})',
    fontsize=11.5, fontweight='bold')
ax_main.grid(axis='x', alpha=0.3, linestyle=':')

legend_main = [
    Patch(facecolor='#c73e6a', alpha=0.4,
          label=f'Joint 1σ region [{joint_lo_1s:.3f}, {joint_hi_1s:.3f}]'),
    Patch(facecolor='#c73e6a', alpha=0.15,
          label=f'Joint 2σ region [{joint_lo_2s:.3f}, {joint_hi_2s:.3f}]'),
    Patch(facecolor='steelblue', alpha=0.6, label='Tier A (Hubble, JWST) 1σ'),
    Patch(facecolor='olivedrab', alpha=0.6, label='Tier B (CC, fσ_8, ISW) 1σ'),
    Patch(facecolor='gold', alpha=0.4, label='Preprint benchmark ε ≈ 0.010'),
]
ax_main.legend(handles=legend_main, loc='lower right', fontsize=8.5, framealpha=0.95)

# ============ LOLLIPOP with 2σ ============
def draw_lollipop_panel(ax, z_min, z_max, log_x, show_y):
    # Joint bands (horizontal)
    ax.axhspan(joint_lo_2s, joint_hi_2s, color='#c73e6a', alpha=0.08)
    ax.axhspan(joint_lo_1s, joint_hi_1s, color='#c73e6a', alpha=0.22)
    ax.axhline(joint_lo_1s, color='#c73e6a', lw=0.9, ls='--', alpha=0.8)
    ax.axhline(joint_hi_1s, color='#c73e6a', lw=0.9, ls='--', alpha=0.8)

    # Benchmark
    ax.axhline(0.010, color='darkorange', lw=1, ls='-.', alpha=0.7)
    # Zero line
    ax.axhline(0, color='black', lw=0.7)

    # Joint label
    if show_y:
        ax.text(z_min + (z_max - z_min)*0.03 if not log_x else z_min*1.15,
                (joint_lo_1s + joint_hi_1s)/2,
                'joint 1σ', fontsize=8.5, color='#8c2a4a',
                style='italic', fontweight='bold', va='center')
        ax.text(z_min + (z_max - z_min)*0.03 if not log_x else z_min*1.15,
                0.0108, 'ε=0.010', fontsize=8, color='#b06000',
                style='italic', va='bottom')

    for k in keys:
        r = results[k]; tier = r['tier']
        zd = r['z_display']
        if zd < z_min or zd > z_max: continue
        c1, c2 = colors(tier)

        if tier == 'Tier A':
            # 2σ outer band
            hw2 = 0.11 if log_x else 0.11*(z_max-z_min)/3
            x0 = zd*(1-hw2) if log_x else zd - hw2
            x1 = zd*(1+hw2) if log_x else zd + hw2
            ax.fill_between([x0, x1], [r['lo_2s_phys']]*2, [r['hi_2s']]*2,
                            color=c2, alpha=0.75, edgecolor=c1, linewidth=0.5)
            # 1σ inner band
            hw1 = 0.085 if log_x else 0.085*(z_max-z_min)/3
            x0i = zd*(1-hw1) if log_x else zd - hw1
            x1i = zd*(1+hw1) if log_x else zd + hw1
            ax.fill_between([x0i, x1i], [r['lo_1s_phys']]*2, [r['hi_1s']]*2,
                            color=c1, alpha=0.55, edgecolor=c1, linewidth=1.5)
            # best marker
            ax.plot([zd], [r['best_phys']], 'o', color='white',
                    markeredgecolor=c1, markersize=7, markeredgewidth=1.5, zorder=5)
        else:
            # 2σ outer light stem
            hi2 = min(r['hi_2s'], 0.10)
            ax.plot([zd, zd], [0, hi2], color=c2, lw=6,
                    solid_capstyle='butt', zorder=3, alpha=0.85)
            # 2σ cap or off-scale arrow
            if r['hi_2s'] > 0.10:
                ax.annotate('', xy=(zd, 0.102), xytext=(zd, 0.098),
                            arrowprops=dict(arrowstyle='->', color=c2, lw=1.3))
            else:
                if log_x:
                    ax.plot([zd*0.92, zd*1.08], [r['hi_2s']]*2, color=c2, lw=2)
                else:
                    ax.plot([zd-0.05, zd+0.05], [r['hi_2s']]*2, color=c2, lw=2)
            # 1σ inner dark stem
            ax.plot([zd, zd], [0, r['hi_1s']], color=c1, lw=3.5,
                    solid_capstyle='butt', zorder=4)
            if log_x:
                ax.plot([zd*0.93, zd*1.07], [r['hi_1s']]*2, color=c1, lw=2, zorder=4)
            else:
                ax.plot([zd-0.04, zd+0.04], [r['hi_1s']]*2, color=c1, lw=2, zorder=4)
            # Base
            if log_x:
                ax.plot([zd*0.93, zd*1.07], [0, 0], color=c1, lw=1.5, zorder=4)
            else:
                ax.plot([zd-0.05, zd+0.05], [0, 0], color=c1, lw=1.5, zorder=4)
            # best if positive
            if r['best_phys'] > 0:
                ax.plot([zd], [r['best_phys']], 'o', color='white',
                        markeredgecolor=c1, markersize=5, markeredgewidth=1.2, zorder=5)
        # Label
        lbl_map = {'Hubble': 'Hubble', 'JWST': 'JWST',
                   'CC': 'CC', 'fsigma8': r'$f\sigma_8$', 'ISW': 'ISW'}
        label_y = r['hi_1s'] + 0.006 if tier == 'Tier A' else min(r['hi_2s'] + 0.003, 0.105)
        ax.annotate(lbl_map.get(k, k), (zd, label_y),
                    fontsize=9.5, fontweight='bold' if tier=='Tier A' else 'normal',
                    ha='center', color='#222')

    ax.set_xlim(z_min, z_max)
    ax.set_ylim(-0.003, 0.11)
    if log_x:
        ax.set_xscale('log')
        ax.set_xticks([3, 10, 30, 100, 300, 1000])
        ax.set_xticklabels(['3', '10', '30', '100', '300', '1000'])
    ax.set_xlabel('redshift z' + (' (log)' if log_x else ''), fontsize=10)
    if show_y:
        ax.set_ylabel(r'$\varepsilon$  (physical, $\geq 0$)', fontsize=10)
    ax.grid(alpha=0.3, linestyle=':')

draw_lollipop_panel(ax_low,  0,    3,    False, True)
draw_lollipop_panel(ax_high, 3,    1500, True,  False)
plt.setp(ax_high.get_yticklabels(), visible=False)
ax_low.set_title('low-z (linear)  —  darker stem = 1σ, lighter = 2σ', fontsize=9.5, style='italic')
ax_high.set_title('high-z (log)',  fontsize=10, style='italic')

plt.tight_layout()
plt.subplots_adjust(top=0.95)

out_pdf = os.path.join(SCRIPT_DIR, '..', '..', 'figures', 'fig_epsilon_constraints.pdf')
out_png = os.path.join(SCRIPT_DIR, '..', '..', 'figures', 'fig_epsilon_constraints.png')
plt.savefig(out_pdf, dpi=300, bbox_inches='tight')
plt.savefig(out_png, dpi=150, bbox_inches='tight')
print(f"\nFigure saved: {out_pdf}")
print(f"          and {out_png}")

# Summary JSON
summary = {
    'analysis': '5-probe joint ε-constraint under uniform-ε + ε ≥ 0',
    'joint_1s':  [joint_lo_1s, joint_hi_1s],
    'joint_2s':  [joint_lo_2s, joint_hi_2s],
    'joint_width_1s': joint_hi_1s - joint_lo_1s,
    'joint_center':   (joint_lo_1s + joint_hi_1s) / 2,
    'benchmark_status':
        f'ε=0.010 is {"BELOW" if 0.010 < joint_lo_1s else "within"} joint 1σ region; '
        'needs revision OR ε(z) required.',
    'probes': [
        dict(key=k, tier=results[k]['tier'],
             z_range=[results[k]['z_min'], results[k]['z_max']],
             z_display=results[k]['z_display'],
             raw_best=results[k]['raw_best'],
             best_physical=results[k]['best_phys'],
             range_1s_physical=[results[k]['lo_1s_phys'], results[k]['hi_1s']],
             range_2s_physical=[results[k]['lo_2s_phys'], results[k]['hi_2s']])
        for k in keys
    ],
    'excluded': {
        'BAO':           'simplified methodology (Ω_m fixed, diagonal cov); raw −0.013 artefact',
        'A_lens':        'linearized proxy without Boltzmann; theoretical systematic omitted',
        'S_8 KiDS':      'raw 1σ entirely negative → measures S_8 tension, not ECT ε',
        'σ_8 clusters':  'same as S_8',
        'SN Ia':         'was mock',
    },
    'text_note_age': {
        'eps_best': age['eps_central'],
        'range_1s': [age['eps_lo_1s'], age['eps_hi_1s']],
    },
}
out_json = os.path.join(SCRIPT_DIR, 'constraint_summary.json')
with open(out_json, 'w') as f:
    json.dump(summary, f, indent=2)
print(f"Summary saved: {out_json}")
