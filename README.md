# ECT Preprint — Code & Notebooks

> **Paper:** *Euclidean Condensate Theory (ECT): Emergence of Spacetime, Quantum Mechanics,
> and Gravity from Spontaneous O(4) Symmetry Breaking*
> **Author:** Valeriy Blagovidov | vblagovidov@gmail.com
> **Preprint:** [10.5281/zenodo.18917930](https://doi.org/10.5281/zenodo.18917930)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18917930.svg)](https://doi.org/10.5281/zenodo.18917930)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/chufelo/ECT-preprint-code/master?filepath=ECT_interactive_dashboard.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ▶ Interactive Mode

Click the Binder badge to launch a **live Jupyter environment** — no installation needed.
Three interactive notebooks:

| Notebook | Topic | Key slider |
|---|---|---|
| `01_rotation_curves_interactive.ipynb` | SPARC rotation curves (φ-first IR) | r₀ per galaxy |
| `02_cosmology_interactive.ipynb` | Hubble tension, JWST, primordial perturbations | ε, H₀, N_e |
| `03_fundamental_constants_interactive.ipynb` | G_N, ℏ, c from condensate parameters | α, v₀ |

---

## What is ECT?

**Euclidean Condensate Theory (ECT)** derives Lorentzian spacetime, quantum mechanics,
and gravitational dynamics from **spontaneous O(4)→O(3) symmetry breaking** of a real
scalar condensate field Φ on a 4D Euclidean manifold — with no time coordinate assumed.

### Core mechanism

The Euclidean action
$$\mathcal{L}_E = \tfrac{1}{2}(\partial\Phi)^2 - \tfrac{\alpha}{2}(n^A\partial_A\Phi)^2 + V(n^2)$$
admits a gradient condensate ⟨∂_AΦ⟩ = v₀ δ_{Aw} that breaks O(4)→O(3).
Perturbations around this background see the effective metric diag(−(α−1), 1, 1, 1),
which is **Lorentzian when α > 1**. Effective speed: c* = 1/√(α−1).

### Three condensate parameters → three fundamental constants

| Condensate | ECT relation | Constant | Status |
|---|---|---|---|
| α > 1 | c* = 1/√(α−1) | Speed of light *c* | Level B (parameter matching) |
| v₀ = M̄_Pl | G_N = c*²(α−1)/(16πv₀²) | Newton's G_N | Level B |
| v₀, λ | ℏ_eff = v₀² m_φ/2 | Planck's ℏ | Level B (self-consistency) |

> **Honest note:** these are parameter-matching relations, not zero-parameter predictions.
> ECT reduces the number of independent inputs but does not eliminate free parameters.
> GW170817 confirms c_em = c_gw to |δc/c| < 10⁻¹⁵, consistent with α=2.

### Three condensate scales — one field

| Scale | Value | Physical sector |
|---|---|---|
| v₀ ~ M̄_Pl | ≈ 2.43×10¹⁸ GeV | Gravity, ℏ, c |
| v₂ ~ v_EW | ≈ 246 GeV | W, Z, Higgs |
| v_gal ~ 1/r₀ | ~ kpc⁻¹ | Flat rotation curves |

The RG running connecting these three scales is an **open problem**.

---

## Figures

### Fig. 1 — SPARC Rotation Curves

ECT φ-first closure fits SPARC galaxies with **one free parameter r₀** per galaxy.
ECT dimensional prediction: **r₀ ∝ M★^(1/3)** (Level A — zero-parameter exponent).

![SPARC ECT fit](SPARC_ECT_fit.png)

**Sample fit results** (full 175-galaxy results: `ect_sparc_results_v3.csv`):

| Galaxy | r₀ [kpc] | χ²/N (ECT, 1 param) | log M★/M☉ |
|---|---|---|---|
| DDO 154 | 0.10 | 3.55 | 7.47 |
| NGC 2403 | 2.3 | 1.40 | 9.65 |
| NGC 3198 | 6.7 | **1.38** | 10.54 |
| NGC 6503 | 7.8 | 12.75 | 10.28 |
| UGC 2885 | 17.7 | 8.08 | 11.28 |

Milky Way: r₀ = 5.7 kpc, χ²/N = 2.84 (ECT, 1 param) vs 3.51 (ΛCDM/NFW, 3 params).

### Fig. 2 — External Field Effect (EFE)

Condensate φ-field sourced by a neighbouring mass modifies the local effective G_eff,
producing an external field effect analogous to (but mechanistically distinct from) MOND.

![EFE](ECT_EFE_rotation_curves.png)

### Fig. 3 — Condensate Scales

Three-scale structure of the single condensate field: Planck, electroweak, galactic.

![Scales](ECT_condensate_scales.png)

### Fig. 4 — Level-4 Self-Consistency

Internal consistency check: condensate stability, ghost-freedom, LIV bound, causality,
baryogenesis, 2nd law.

![Level4](ECT_level4_selfconsistency.png)

### Fig. 5 — Cosmological Timeline: ECT vs ΛCDM

![Timeline](ECT_vs_LCDM_timeline.png)

---

## Key observational results

### Galactic dynamics
- **RAR:** Radial Acceleration Relation reproduced with g† ≈ c²H₀/(2π) (6–13% deviation from McGaugh+2016)
- **BTFR:** Baryonic Tully-Fisher slope 1/4 reproduced algebraically (Level A)
- **Milky Way:** χ²/N = 2.84 vs ΛCDM/NFW 3.51 (1 vs 3 parameters)

### Cosmology
- **Hubble tension:** G_eff(z) = G_N(1+z)^{2ε}, ε ≈ 0.01 (phenomenological) shifts H₀ by ~3 km/s/Mpc
- **JWST:** Alleviates but does not resolve the high-redshift massive halo abundance
- **CMB quadrupole:** δC₂/C₂ ~ e^{−2π} ≈ 0.19 (observed ~0.13; qualitative)
- **LIV:** Δt_gw ~ 10⁻⁵² s from GW170817 (unobservable, consistent)
- **Inflation:** n_s = 0.967 (N_e = 60) matches Planck 2018 within 1σ — *note: this is a slow-roll formula, not a first-principles ECT derivation*

### Fundamental constants
- **Baryogenesis:** leptogenesis via right-handed neutrino M_R ~ 10⁹ GeV gives η_B ~ 9×10⁻¹⁰ vs observed 6×10⁻¹⁰ (factor 1.5×; nearly resolved)
- **5th force:** predicted spin precession ω₅ ~ 10⁻¹⁰ rad/s; Eötvös η ~ 10⁻¹⁵ (MICROSCOPE-2 sensitivity)
- **Neutron star max mass:** M_max = 2.17 M☉ (PSR J0740+6620: 2.14 M☉)

---

## Claim levels

All claims in the paper are classified:

| Level | Meaning |
|---|---|
| **A** | Strictly derived from postulates P1–P7 |
| **B** | Derived under stated additional assumptions |
| **C** | Conjecture / research programme |

---

## Cosmological problems — current ECT status

| Problem | ΛCDM/Inflation | ECT | Level |
|---|---|---|---|
| Horizon | Inflation (Level B) | Coherent branch selection from O(4) postulate | **A** |
| Flatness | Inflation suppresses Ω_K (Level B) | k=0 from P1 + macrocoherence | **A** |
| Relic monopoles | Inflation dilutes (Level B) | O(4)→O(3) does not topologically require monopoles | **A** |
| Primordial spectrum | Quantitative (inflation leads) | Candidate variables identified; scale-free hint | **C** |

---

## Scripts

### Main figure scripts
| Script | Figure | Description |
|---|---|---|
| `fig1_SPARC_rotation_curves.py` | Fig. 1 | 5 SPARC galaxies + Milky Way |
| `fig2_EFE_external_field.py` | Fig. 2 | External field effect |
| `fig3_condensate_scales.py` | Fig. 3 | Three-scale condensate |
| `fig4_level4_selfconsistency.py` | Fig. 4 | Self-consistency radar |
| `fig5_cosmological_timeline.py` | Fig. 5 | ECT vs ΛCDM timeline |

### Analysis scripts
| Script | Purpose |
|---|---|
| `ect_sparc_fit_phi_branch.py` | Full φ-branch SPARC fit (175 galaxies) |
| `ect_hubble_jwst_background.py` | Hubble tension + JWST + linear growth |
| `ect_btfr_new.py` | BTFR slope derivation |
| `ect_rar_new.py` | RAR from condensate |
| `ect_gdagger_analysis_new.py` | g† scale analysis |
| `calc_leptogenesis_eta_B.py` | Baryogenesis via leptogenesis |
| `calc_fifth_force_bounds.py` | 5th force experimental bounds |
| `calc_fundamental_constants.py` | G_N, ℏ, c matching |
| `calc_hubble_tension.py` | Hubble tension estimate |
| `calc_inflation_spectral_index.py` | Slow-roll n_s comparison |
| `draw_derivation_logic.py` | Derivation logic diagram |

### Data files
| File | Contents |
|---|---|
| `ect_sparc_results_v3.csv` | φ-branch fit results for 175 SPARC galaxies |
| `ect_sparc_phi_all175.csv` | Full SPARC φ-profile data |
| `sparc_environment.csv` | Galaxy environment data |

---

## Installation

```bash
git clone https://github.com/chufelo/ECT-preprint-code
cd ECT-preprint-code
conda env create -f environment.yml
conda activate ect
```

Or use the Binder badge above for zero-install interactive mode.

---

## Citation

```bibtex
@software{blagovidov2026ect,
  author  = {Blagovidov, Valeriy},
  title   = {{Euclidean Condensate Theory (ECT): Emergence of Spacetime,
              Quantum Mechanics, and Gravity from Spontaneous O(4) Symmetry Breaking}},
  year    = {2026},
  doi     = {10.5281/zenodo.18917930},
  url     = {https://doi.org/10.5281/zenodo.18917930}
}
```
