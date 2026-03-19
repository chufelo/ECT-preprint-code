#!/usr/bin/env python3
"""
ECT derived-parent parameter scan — grayscale publication-quality version.
Readable in B&W: diverging grays, hatching for corridor, clear markers.
"""
import sys, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
exec(open(Path(__file__).parent / 'ect_hubble_jwst_background.py').read().split('def main():')[0])

OUTDIR = Path(__file__).parent.parent / 'figures'

plt.rcParams.update({
    'font.family': 'serif',
    'font.size':   10.5,
    'axes.linewidth': 0.8,
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'savefig.facecolor':'white',
})

# ── Compute scan ─────────────────────────────────────────────────────────────
omega0_vals = np.array([15., 20., 25., 30., 40., 50.])
phi0_vals   = np.array([-0.05, -0.08, -0.10, -0.12, -0.15])   # top→bottom = least negative → most negative

DH  = np.full((len(phi0_vals), len(omega0_vals)), np.nan)
Age = np.full_like(DH, np.nan)
tU10= np.full_like(DH, np.nan)
G10 = np.full_like(DH, np.nan)

print("Computing scan...")
for i, ph in enumerate(phi0_vals):
    for j, om in enumerate(omega0_vals):
        try:
            p = Params(closure_mode="derived_parent", omega0=float(om), phi0=float(ph),
                       npts=400, n_iter=4, zmax_solver=12)
            df_bg, _ = solve_background_selfconsistent(p, seed_mode="ref")
            full_df, summ, *_ = derived_quantities(df_bg, p)
            s = summ.iloc[0]
            DH[i,j]   = s['DeltaH0_over_H0']*100
            Age[i,j]  = s['age_ect_Gyr']
            tU10[i,j] = s.get('t_U_ect_z10', np.nan)
            j10 = abs(full_df["z"]-10).argmin()
            G10[i,j]  = np.exp(-p.beta*full_df["phi"].iloc[j10])
        except:
            pass
print("Scan done.")

# Working points
WP = [
    dict(label="B", name="balanced",        omega0=25, phi0=-0.10, mk="o", desc="B = balanced"),
    dict(label="H", name="Hubble-priority",  omega0=30, phi0=-0.10, mk="s", desc="H = Hubble-priority"),
    dict(label="A", name="age-priority",     omega0=25, phi0=-0.08, mk="^", desc="A = age-priority"),
]

good = (DH >= 1.5) & (DH <= 5.0) & (Age >= 12.5) & (tU10 >= 0.33)

# ── Figure layout ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(13, 11.0))
fig.subplots_adjust(hspace=0.42, wspace=0.38)

panels = [
    # (data, title, fmt, cmap, vmin, vmax, diverging_center)
    (DH,   r"$\Delta H_0/H_0$ [\%]",       "{:.1f}", None, -5,   6,    0.0),
    (Age,  r"$t_0$ (ECT) [Gyr]",            "{:.2f}", None, 11.5, 14.5, None),
    (tU10, r"$t_U(z=10)$ [Gyr]",            "{:.3f}", None, 0.25, 0.55, None),
    (G10,  r"$G_{\rm eff}(z=10)/G_N$",      "{:.2f}", None, 1.0,  3.0,  None),
]

for ax, (data, title, fmt, _, vmin, vmax, div_cen) in zip(axes.ravel(), panels):

    # ── Choose grayscale colormap ─────────────────────────────────────────
    if div_cen is not None:
        # Diverging: white at center (ΔH=0), dark at extremes
        # Dark gray → white → light gray  (negative=dark, positive=light doesn't work)
        # Use: dark = high values (positive shift = good), light = negative
        # Actually: use a custom diverging where white=div_cen
        from matplotlib.colors import TwoSlopeNorm
        norm = TwoSlopeNorm(vmin=vmin, vcenter=div_cen, vmax=vmax)
        cmap_name = 'RdGy_r'   # in grayscale: diverging through white at center
        # For true B&W: manually map to [0.15, 1.0, 0.55] (dark-white-midgray)
        cmap = plt.cm.RdGy_r
    else:
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        if title.startswith(r"$G_"):
            cmap = plt.cm.Oranges_r   # dark=high G_eff
        elif "t_0" in title:
            cmap = plt.cm.Blues       # dark=old universe
        else:
            cmap = plt.cm.YlOrBr_r   # dark=more time

    # Convert everything to grayscale via luminance-preserving conversion
    # Apply grayscale manually: render colour then desaturate
    # Strategy: use 'gray' or 'Greys' with appropriate direction

    # Simple approach: map to Greys with suitable direction
    if div_cen is not None:
        # ΔH panel: dark=large positive (good Hubble shift), white=zero, mid-gray=negative
        # Use custom: darker for larger |ΔH|, but different hatch for neg vs pos
        cmap = plt.cm.Greys
        norm2 = plt.Normalize(vmin=0, vmax=max(abs(vmin), abs(vmax)))
        img_data_abs = np.abs(data - div_cen)
        im = ax.imshow(img_data_abs, aspect='auto', origin='upper',
                       cmap=cmap, norm=norm2,
                       extent=[-0.5, len(omega0_vals)-0.5,
                                len(phi0_vals)-0.5, -0.5])
        cbar = plt.colorbar(im, ax=ax, shrink=0.88)
        cbar.set_label(r"$|\Delta H_0/H_0|$ [\%]; sign shown in corner", fontsize=8.5)
    elif "t_0" in title:
        # t₀: lighter = younger (lower), darker = older
        cmap = plt.cm.Greys_r
        im = ax.imshow(data, aspect='auto', origin='upper',
                       cmap=cmap, vmin=vmin, vmax=vmax,
                       extent=[-0.5, len(omega0_vals)-0.5,
                                len(phi0_vals)-0.5, -0.5])
        cbar = plt.colorbar(im, ax=ax, shrink=0.88)
        cbar.set_label(title, fontsize=9.5)
    elif "t_U" in title:
        # tU(z=10): lighter = less time (worse for JWST), darker = more time
        cmap = plt.cm.Greys
        im = ax.imshow(data, aspect='auto', origin='upper',
                       cmap=cmap, vmin=vmin, vmax=vmax,
                       extent=[-0.5, len(omega0_vals)-0.5,
                                len(phi0_vals)-0.5, -0.5])
        cbar = plt.colorbar(im, ax=ax, shrink=0.88)
        cbar.set_label(title, fontsize=9.5)
    else:
        # G_eff: lighter = closer to G_N (screened), darker = stronger G_eff
        cmap = plt.cm.Greys
        im = ax.imshow(data, aspect='auto', origin='upper',
                       cmap=cmap, vmin=vmin, vmax=vmax,
                       extent=[-0.5, len(omega0_vals)-0.5,
                                len(phi0_vals)-0.5, -0.5])
        cbar = plt.colorbar(im, ax=ax, shrink=0.88)
        cbar.set_label(title, fontsize=9.5)

    ax.set_xticks(np.arange(len(omega0_vals)))
    ax.set_xticklabels([f"{v:.0f}" for v in omega0_vals], fontsize=9.5)
    ax.set_yticks(np.arange(len(phi0_vals)))
    ax.set_yticklabels([f"{v:.2f}" for v in phi0_vals], fontsize=9.5)
    ax.set_xlabel(r"$\omega_0$", fontsize=11)
    ax.set_ylabel(r"$\phi_0$", fontsize=11)
    ax.set_title(title, fontweight="bold", fontsize=11, pad=6)

    # ── Cell annotations ─────────────────────────────────────────────────
    for ii in range(len(phi0_vals)):
        for jj in range(len(omega0_vals)):
            if np.isnan(data[ii, jj]):
                continue
            v = data[ii, jj]
            # Determine background brightness to pick text color
            if div_cen is not None:
                norm_v = abs(v - div_cen) / max(abs(vmin), abs(vmax))
            else:
                norm_v = (v - vmin) / (vmax - vmin + 1e-9)
            # For Greys_r: norm_v=0 → white, norm_v=1 → black
            # text should be black on light, white on dark
            if cmap == plt.cm.Greys_r:
                text_dark = norm_v > 0.55
            else:
                text_dark = norm_v < 0.50
            col = 'white' if text_dark else 'black'
            ax.text(jj, ii, fmt.format(v), ha='center', va='center',
                    fontsize=9, color=col, fontweight='bold')

    # ── Corridor boxes ────────────────────────────────────────────────────
    for ii in range(len(phi0_vals)):
        for jj in range(len(omega0_vals)):
            if good[ii, jj]:
                ax.add_patch(Rectangle((jj-0.5, ii-0.5), 1, 1,
                    fill=False, edgecolor='black', lw=2.2, zorder=5))

    # ── Working-point markers ─────────────────────────────────────────────
    for wp in WP:
        ji = np.where(omega0_vals == wp['omega0'])[0]
        pi = np.where(phi0_vals   == wp['phi0'])[0]
        if len(ji) and len(pi):
            ax.plot(ji[0], pi[0], wp['mk'],
                    ms=13, mfc='white', mec='black', mew=2.2, zorder=10)
            ax.text(ji[0]+0.32, pi[0]-0.36, wp['label'],
                    fontsize=9.5, color='black', fontweight='bold', zorder=11,
                    bbox=dict(fc='white', ec='none', pad=0.5))

    # ── Sign indicator for ΔH panel ───────────────────────────────────────
    if div_cen is not None:
        # Overlay a "+" or "–" sign inside cells to distinguish sign
        for ii in range(len(phi0_vals)):
            for jj in range(len(omega0_vals)):
                if np.isnan(DH[ii, jj]):
                    continue
                sign = '+' if DH[ii, jj] >= 0 else '−'
                ax.text(jj-0.44, ii+0.44, sign,
                        fontsize=9, color='black', fontweight='bold',
                        ha='left', va='bottom', zorder=12)

# ── Shared legend ─────────────────────────────────────────────────────────────
from matplotlib.lines import Line2D
legend_els = [
    mpatches.Patch(facecolor='white', edgecolor='black', lw=2.2,
                   label='Hubble-compatible corridor'),
    Line2D([0],[0], marker='o', color='black', ls='none', ms=10,
           mfc='white', mew=2, label='B = balanced'),
    Line2D([0],[0], marker='s', color='black', ls='none', ms=10,
           mfc='white', mew=2, label='H = Hubble-priority'),
    Line2D([0],[0], marker='^', color='black', ls='none', ms=10,
           mfc='white', mew=2, label='A = age-priority'),
]
fig.legend(handles=legend_els, loc='lower center', ncol=4,
           fontsize=10, bbox_to_anchor=(0.5, 0.01),
           framealpha=1.0, edgecolor='black', fancybox=False)

fig.suptitle(
    r"ECT derived-parent parameter scan: $\beta=0.8$, $\mu=1.5$, "
    r"$A_2=\mu^2/(6\beta^2)$, $A_3=A_4=0$",
    fontsize=12.5, fontweight='bold', y=0.995)

out = OUTDIR / 'ect_condensate_param_scan_bw'
fig.savefig(out.with_suffix('.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(out.with_suffix('.png'), dpi=220, bbox_inches='tight')
plt.close()
print(f"Saved: {out}.pdf/png")
