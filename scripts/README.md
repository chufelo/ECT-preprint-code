# ECT Figure and Calculation Scripts

## Figure generation scripts

### `fig_condensate_evolution.py`
**Figure:** `figures/ect_condensate_evolution_schematic_bw.pdf`  
**Used in:** §15.2 (Cosmological evolution of the condensate amplitude)  
**Content:** 4-panel schematic of condensate background evolution vs redshift z:
- (a) φ_b(z): monotonically increasing from -3 (ordering) → -0.6 (stabilisation) → -0.10 (today)
- (b) u/u_∞ = exp(βφ): amplitude ratio approaching unity
- (c) G_eff/G_N = exp(-βφ): decreasing from ~11 to ~1.08
- (d) w_φ(z): frozen near -1 at high z, quintessence-like at late times

Key benchmark values: φ(z=10) ≈ -0.51, G_eff(z=10)/G_N ≈ 1.5 (matches derived-parent table).  
Shows Scenarios A (stable asymptote) and B (continued drift).  
**Status:** Schematic closure-level visualisation, not output of full background solver.  
**Last updated:** 2026-03-27 (critical fix: corrected late-time φ direction)

### `fig_condensate_evolution_time.py`
**Figure:** `figures/ect_condensate_evolution_time_bw.pdf`  
**Used in:** §15.2 (same section, complementary to z-based figure)  
**Content:** 2-panel condensate evolution over cosmic time (Gyr):
- (a) φ_b(t) (left axis) + u/u_∞ (right axis, grey)
- (b) G_eff/G_N(t): log-log scale with epoch markers (BBN, recombination, today)

Uses Planck 2018 background cosmology for t(z) mapping.  
Three-stage shading: ordering / stabilisation / late approach to screened state.  
**Status:** Schematic closure-level visualisation.  
**Last updated:** 2026-03-27 (critical fix: corrected late-time φ direction)

---

## Notes
- All figures are grayscale, 300 dpi, publication-ready
- Scripts require: numpy, matplotlib, scipy
- Output goes to `../figures/` relative to script location
- Schematic figures use smooth interpolating functions, not solutions of full ODE system
