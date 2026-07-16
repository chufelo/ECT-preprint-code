# ECT publication repository — manuscripts, calculations, and figures

This directory is the publication layer of the shared ECT workspace. The workspace root is one level above; active research notes live in `../research/derivations/`, while this Git repository retains the canonical manuscripts and reproducibility materials.

All scripts in this repository reproduce the figures and numerical results
in the ECT preprint (*Euclidean Condensate Theory*, V. Blagovidov, 2025).

**Zenodo DOI:** [10.5281/zenodo.18917930](https://doi.org/10.5281/zenodo.18917930)

## Quick start

```bash
cd /Users/chufelo/Documents/Physics/VDT/ECT
source .workspace/runtime/venvs/latex-scripts/bin/activate
python3 .workspace/tools/codex_ect_preflight.py --root .
bash LaTex/scripts/compile_preprint.sh
```

The repository root is the preprint layer. Included section files are under `sections/`; reusable programs under `scripts/`; notebooks under `notebooks/`; datasets under `data/`; and current figures under `figures/`. Internal work remains available locally under `work/preprint/`: drafts are private, while proposals are publication candidates and enter Git only through explicit per-file review/force-add. This preserves reviewed renames of already-public proposal history without exposing new candidates through `git add -A`. The deferred book is likewise local-only and ignored under `/book/`; it must never be published by a broad staging command. The companion and summary have their own directories. Scripts can be run with Python 3.10+ and the scientific packages recorded in `data/environment.yml`.

The canonical preprint build defaults to four LaTeX passes and enforces zero
errors, undefined references/citations, and multiply-defined labels:

```bash
PREVIOUS_PAGES=803 bash scripts/compile_preprint.sh
```

`PREVIOUS_PAGES` should be taken from the last accepted build so the report
uses the required `X pages (was Y)` form. `LATEX_PASSES=3` is available only
for an explicit quick diagnostic; acceptance builds use the strengthened
default of four LaTeX runs plus BibTeX. The historical build sequence used
three LaTeX runs plus BibTeX; the extra LaTeX run is a stabilization guard,
not a claim about the old convention.

---

## Figure-generating scripts (`scripts/`)

| Script | Output figure(s) | Paper location |
|--------|------------------|----------------|
| `fig1_SPARC_rotation_curves.py` | `set1_milky_way.pdf`, `set2_sparc_sample.pdf` | Fig. 1–2 (Milky Way + SPARC sample) |
| `fig2_EFE_external_field.py` | `diag_chi2_comparison.pdf`, `diag_fixed_vs_free_*.pdf`, `diag_gdag_*.pdf` | Fig. 3–7 (EFE diagnostics) |
| `fig3_condensate_scales.py` | `fig_condensate_scales.png` | Condensate RG hierarchy |
| `fig4_level4_selfconsistency.py` | (self-consistency checks) | Level-4 consistency |
| `fig5_cosmological_timeline_v2.py` | `ect_vs_lcdm_comparative_timeline_bw.pdf` | ΛCDM vs ECT timeline |
| `fig6_dimensionality.py` | `fig_dimensionality_phi.png` | Force-law dimensionality d(r) |
| `fig_bh_shell.py` | `fig_bh_shell.pdf`, `fig_bh_information.pdf` | Black hole shell & information |
| `fig_condensate_evolution.py` | `ect_condensate_evolution_schematic_bw.pdf` | Condensate evolution schematic |
| `fig_condensate_evolution_time.py` | `ect_condensate_evolution_time_bw.pdf` | Condensate evolution (time axis) |
| `fig_ect_architecture.py` | `fig_ect_architecture.pdf` | ECT theory architecture |
| `fig_ect_derivation_map.py` | `fig_ect_derivation_map.png` | Derivation dependency map |
| `fig_equation_hierarchy.py` | `fig_equation_hierarchy.pdf` | Equation hierarchy diagram |
| `fig_gamma_crossover.py` | `fig_gamma_crossover.pdf` | Γ-crossover decoherence |
| `fig_liv_delay.py` | `fig_liv_delay.pdf` | Lorentz invariance violation delay |
| `fig_qubit_info_decoherence.py` | `fig_qubit_info_decoherence.pdf` | Qubit info & decoherence |
| `fig_cosmo_predictions.py` | `fig_cosmo_predictions.png` | Cosmological predictions summary |
| `fig_regime_diagram.py` | `fig_regime_diagram.png` | ECT regime diagram |
| `fig_cluster_merger_suite.py` | `fig_bullet_main.png`, `fig_cluster_suite_budget.png` | Bullet cluster + cluster budget |
| `gen_fig_comparison.py` | `fig_coupling_comparison.png` | Coupling constant comparison |
| `gen_fig_species.py` | `fig_species_beta5.png` | Species β₅ diagram |
| `ect_btfr_new.py` | `ect_btfr_new_bw.pdf` | Baryonic Tully-Fisher relation |
| `ect_rar_new.py` | `ect_rar_new_6panel_bw.pdf` | Radial acceleration relation (6-panel) |
| `ect_gdagger_analysis_new.py` | `fig_gdagger_analysis_new_bw.pdf` | g† analysis |
| `ect_hubble_jwst_background.py` | `ect_hubble_jwst_background_bw.pdf`, `ect_h0_scan_bw.pdf` | Hubble + JWST background |
| `ect_hubble_jwst_background_v6.py` | (extended version with anchor budget) | `ect_jwst_anchor_budget_bw.pdf` |
| `build_ect_figures.py` | `ect_jwst_anchor_budget_bw.pdf`, `ect_condensate_param_scan_bw.pdf` | Pack M multi-figure builder |
| `build_comparative_timeline.py` | `ect_vs_lcdm_comparative_timeline_bw.pdf` | Comparative timeline |
| `build_derived_parent_comparison.py` | `ect_derived_parent_comparison_bw.pdf` | Derived vs parent comparison |
| `build_full_condensate_evolution.py` | `ect_full_condensate_universe_evolution_bw.pdf` | Full condensate universe evolution |
| `build_param_scan_bw.py` | `ect_condensate_param_scan_bw.pdf` | Condensate parameter scan |
| `draw_derivation_logic.py` | Part I/II/III derivation logic diagrams | Uses Graphviz `.gv` source files |

## Calculation scripts (`scripts/`)

| Script | Paper section | What it computes |
|--------|---------------|------------------|
| `calc_fundamental_constants.py` | §5, Tab. 3 | Derives c*, G_N, ℏ from (v₀, λ, α) |
| `calc_universe_age.py` | §12 | Universe age integral: ΛCDM vs ECT |
| `calc_JWST_halo_abundance.py` | §12.1 | Press-Schechter halo abundance enhancement |
| `calc_inflation_spectral_index.py` | §12 | Inflation: n_s = 1 − 2/N_e, tensor-to-scalar ratio |
| `calc_hubble_tension.py` | §12 | ΔH₀ from G_eff(z) = G(1+z)^{2ε} |
| `calc_leptogenesis_eta_B.py` | §18 | Baryon asymmetry η_B from right-handed neutrino |
| `calc_fifth_force_bounds.py` | §9 | Fifth force: spin precession, Eötvös, neutron star M_max |

## SPARC fitting pipeline

| File | Purpose |
|------|---------|
| `ect_sparc_fit_phi_branch.py` | Core fitter: ECT ϕ-branch rotation curves (v3f) |
| `ect_sparc_plot_utils.py` | Plotting utilities for SPARC results |
| `MassModels_Lelli2016c.mrt` | SPARC mass models data (Lelli et al. 2016) |
| `ect_sparc_phi_all175.csv` | Pre-computed ECT fits for 175 SPARC galaxies |
| `sparc_environment.csv` | Galaxy environment classifications |

ECT closure formula: `g(R) = 0.5 * (gN + sqrt(gN² + 4·gN·g†))` — **do not modify**.

## Graphviz source files

| File | Generates |
|------|-----------|
| `fig_partI_derivation_logic.gv` | Part I derivation logic diagram |
| `fig_partII_derivation_logic.gv` | Part II derivation logic diagram |
| `fig_partIII_derivation_logic.gv` | Part III derivation logic diagram |

Compile with: `/opt/homebrew/bin/dot -Tpng input.gv -o output.png`

## Interactive notebooks (`notebooks/`)

| Notebook | Description |
|----------|-------------|
| `01_rotation_curves_interactive.ipynb` | Interactive SPARC rotation curve explorer |
| `02_cosmology_interactive.ipynb` | ECT cosmology: H(z), ages, growth factor |
| `03_fundamental_constants_interactive.ipynb` | Derive c*, G, ℏ from condensate parameters |
| `ECT_interactive_dashboard.ipynb` | Combined ECT dashboard |

## Figures

All 44 article figures are in `figures/`. Each corresponds to a generating
script listed above.

**Figures without identified generator scripts:**
- `fig_w_z_desi.png` — DESI dark energy EOS (w₀, wₐ)
- `fig_gdagger_hierarchy.png` — g† hierarchy diagram
- `github_qr.png` — QR code for this repository

## Physical conventions

- Natural units: c = ℏ = 1 unless stated otherwise
- G = 4.302×10⁻⁶ (km/s)² kpc / M☉ (rotation curve units)
- v₀ ≈ 2.4×10¹⁸ GeV, √λ ≈ 1.5×10⁴³ s⁻¹, α−1 ≈ 1

## Citation

If you use these scripts, please cite the ECT preprint:
> V. Blagovidov, "Euclidean Condensate Theory" (2025).
> Zenodo: [10.5281/zenodo.18917930](https://doi.org/10.5281/zenodo.18917930)
