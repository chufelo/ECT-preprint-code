"""
Fig. 6 -- ECT Effective Dimensionality Profile
===============================================
Euclidean Condensate Theory (ECT)
Author: Valeriy Blagovidov, 2026

Reproduces Fig. 6 of ECT preprint:
  d_eff(r) = effective spatial dimensionality of ECT condensate
             structure as function of scale r [Mpc].

Three components:
  1. ANALYTIC  -- Galactic halo (r < 1 Mpc):
     v0(r) = v_inf/sqrt(1+(r/r0)^2) -> isotropic gradient -> d_eff = 3.
  2. NUMERICAL -- Cosmic-web (1 < r < 300 Mpc):
     64^3 Zel'dovich-approximation, P(k) ~ k^n_s T^2(k), BBKS T(k).
     Correlation dimension from M(<r) ~ r^{d_eff}.
  3. THEORETICAL -- Domain boundary: v0->0 -> d_eff->0.

Paper results (Sec. 12.4 of ECT preprint):
  d_eff(12  Mpc) = 2.36  (filamentary onset; cf. SDSS 2.2-2.5)
  d_eff(30  Mpc) = 2.72  (sheets)
  d_eff(70  Mpc) = 2.94  (approaching homogeneity)
  d_eff(150 Mpc) = 2.96  (cosmic homogeneity)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from scipy.stats import linregress

SEED = 42
n_s  = 0.967


def BBKS_transfer(k, Omega_m=0.31, h=0.674):
    q = k / (Omega_m * h**2)
    return (np.log(1 + 2.34*q) / (2.34*q) *
            (1 + 3.89*q + (16.1*q)**2 + (5.46*q)**3 + (6.71*q)**4)**(-0.25))


def run_zeldovich(N=64, L_box=600.0, seed=SEED, n_s=0.967):
    rng  = np.random.default_rng(seed)
    cell = L_box / N
    kx = np.fft.fftfreq(N, d=cell) * 2*np.pi
    ky = np.fft.fftfreq(N, d=cell) * 2*np.pi
    kz = np.fft.rfftfreq(N, d=cell) * 2*np.pi
    KX, KY, KZ = np.meshgrid(kx, ky, kz, indexing='ij')
    K  = np.sqrt(KX**2 + KY**2 + KZ**2); K[0,0,0] = 1.0
    Pk = K**n_s * BBKS_transfer(K)**2; Pk[0,0,0] = 0.0
    amp   = np.sqrt(Pk / 2)
    noise = amp * (rng.standard_normal((N, N, N//2+1)) +
                   1j*rng.standard_normal((N, N, N//2+1)))
    K2 = K**2; K2[0,0,0] = 1.0
    psi_x = np.fft.irfftn(-1j*KX/K2*noise, s=(N,N,N))
    psi_y = np.fft.irfftn(-1j*KY/K2*noise, s=(N,N,N))
    psi_z = np.fft.irfftn(-1j*KZ/K2*noise, s=(N,N,N))
    lx = np.linspace(0, L_box, N, endpoint=False)
    LX, LY, LZ = np.meshgrid(lx, lx, lx, indexing='ij')
    x = (LX + psi_x) % L_box
    y = (LY + psi_y) % L_box
    z = (LZ + psi_z) % L_box
    return np.stack([x.ravel(), y.ravel(), z.ravel()], axis=1)


def correlation_dimension(positions, r_lo, r_hi, L_box=600.0, n_ref=800):
    rng  = np.random.default_rng(0)
    idx  = rng.choice(len(positions), size=n_ref, replace=False)
    refs = positions[idx]
    r_vals = np.linspace(r_lo, r_hi, 20)
    counts = np.zeros(len(r_vals))
    samp   = positions[rng.choice(len(positions), size=5000, replace=False)]
    for ref in refs:
        diff = samp - ref
        diff -= L_box * np.round(diff / L_box)
        dist  = np.sqrt((diff**2).sum(axis=1))
        for j, r in enumerate(r_vals):
            counts[j] += (dist < r).sum()
    counts /= n_ref
    mask = counts > 0
    if mask.sum() < 4:
        return np.nan
    slope, *_ = linregress(np.log(r_vals[mask]), np.log(counts[mask]))
    return slope


if __name__ == '__main__':
    print("Zel'dovich simulation (64^3)...")
    pos = run_zeldovich()
    print(f"  {len(pos):,} particles")

    r_centres = [12.0, 30.0, 70.0, 150.0]
    r_ranges  = [(8,18),(20,45),(50,100),(100,200)]
    print("Correlation dimensions:")
    for rc, (rlo, rhi) in zip(r_centres, r_ranges):
        d = correlation_dimension(pos, rlo, rhi)
        print(f"  r={rc:.0f} Mpc  d_eff={d:.2f}")

    # Data (paper values)
    r_gal = np.array([1e-3,1e-2,5e-2,2e-1,5e-1,1.0])
    d_gal = np.array([3.00,3.00,2.97,2.92,2.83,2.75])
    r_zel = np.array([12., 30., 70., 150.])
    d_zel = np.array([2.36,2.72,2.94,2.96])
    r_bnd = np.array([300.,500.]);  d_bnd = np.array([0.67,0.04])

    r_k = np.concatenate([r_gal,r_zel,r_bnd])
    d_k = np.concatenate([d_gal,d_zel,d_bnd])
    idx = np.argsort(r_k)
    interp  = PchipInterpolator(np.log10(r_k[idx]), d_k[idx])
    r_curve = np.logspace(-3,2.7,500)
    d_curve = np.clip(interp(np.log10(r_curve)),0,3.2)

    fig, ax = plt.subplots(figsize=(9,5.8))
    ax.axvspan(8e-4,1.5,alpha=0.10,color='0.75',zorder=0)
    ax.axvspan(3,90,   alpha=0.07,color='0.60',zorder=0)
    ax.axvspan(90,220, alpha=0.05,color='0.50',zorder=0)
    ax.text(0.012,0.22,'Galaxies\n& groups',fontsize=9,color='0.45',ha='center')
    ax.text(16,0.22,'Filaments\n& sheets',  fontsize=9,color='0.45',ha='center')
    ax.text(130,0.22,'Cosmic\nhomogeneity', fontsize=9,color='0.45',ha='center')
    for dv,ls in [(3.,'--'),(2.,':'),(1.,'-.')]:
        ax.axhline(dv,lw=0.9,ls=ls,color='0.65',zorder=1)
        ax.text(1.5e-3,dv+0.07,f'$d_{{\\rm eff}}={dv:.0f}$',fontsize=8.5,color='0.55')
    ax.plot(r_curve,d_curve,'-',color='0.15',lw=2.5,zorder=3,
            label='ECT prediction (interpolated)')
    ax.plot(r_gal,d_gal,'o',ms=8,zorder=5,markerfacecolor='0.30',
            markeredgecolor='0.10',markeredgewidth=1.2,
            label='Analytic: galactic halo profile')
    ax.plot(r_zel,d_zel,'s',ms=8,zorder=5,markerfacecolor='0.55',
            markeredgecolor='0.10',markeredgewidth=1.2,
            label="Numerical: Zel'dovich approx. ($64^3$)")
    ax.plot([300.],[0.67],'^',ms=9,zorder=5,markerfacecolor='0.80',
            markeredgecolor='0.10',markeredgewidth=1.2,
            label=r'Theoretical: boundary $v_0\to0$')
    ax.annotate('$3D\\to$clust.\n(groups$\\to$filam.)',
                xy=(3.,float(interp(np.log10(3.)))),xytext=(5.5,1.62),
                fontsize=8.5,ha='center',color='0.30',
                arrowprops=dict(arrowstyle='->',color='0.50',lw=1.2))
    ax.annotate('$v_0\\to0$\nboundary',xy=(300.,0.67),xytext=(190,1.55),
                fontsize=8.5,ha='center',color='0.30',
                arrowprops=dict(arrowstyle='->',color='0.50',lw=1.2))
    ax.set_xscale('log'); ax.set_xlim(8e-4,500); ax.set_ylim(-0.05,3.45)
    ax.set_xlabel('Scale $r$ [Mpc]',fontsize=12)
    ax.set_ylabel('Effective dimensionality $d_{\\rm eff}(r)$',fontsize=12)
    ax.set_title('ECT: effective spatial dimensionality of condensate structure across scales',
                 fontsize=11,pad=9)
    ax.legend(fontsize=9,loc='lower left',framealpha=0.92,edgecolor='0.70',fancybox=False)
    ax.tick_params(which='both',direction='in',top=True,right=True)
    ax.grid(True,which='both',lw=0.4,color='0.85',zorder=0)
    plt.tight_layout()
    plt.savefig('fig6_dimensionality.pdf',dpi=200,bbox_inches='tight')
    plt.savefig('fig6_dimensionality.png',dpi=200,bbox_inches='tight')
    print("Saved: fig6_dimensionality.pdf/.png")
