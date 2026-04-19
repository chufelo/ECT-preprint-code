# Appendix A1 — Hubble + r_s: extraction of ε under uniform-ε deformation

**Status:** v1 draft for user + GPT review | **Target:** Phase 2A Step 2 | **Date:** 2026-04-19

**Purpose.** First per-probe methodology appendix. Establishes the template that A2–A5 will follow. For the Hubble channel, derives the retained 1σ and 2σ ε-intervals under the effective uniform-ε deformation of the ΛCDM background, with explicit physics, observational inputs, extraction pipeline, uncertainty budget, and a grayscale χ²(ε) figure.

**Structural role (PROPOSAL v3 E.8).** Extraction layer — NOT a physical derivation of ε. The existing computational machinery in `app:late_cosmo_algorithm` / `app:late_cosmo_background` supplies forward evolution H(z, ε) given a chosen ε; this new appendix is the INVERSE step: from observations → allowed ε-interval.

**Unified per-probe structure** (template for A2–A6):
1. Physics of the probe
2. Observational inputs and their uncertainty
3. ECT-side model via uniform-ε deformation
4. Extraction procedure: what χ² is minimised, over what parameters
5. Derivation of 1σ and 2σ intervals from Δχ² = 1, 4
6. Grayscale figure: χ²(ε) with shaded 1σ and 2σ bands
7. Methodological limitations

**Numerics source.** `scripts/epsilon_convergence/ch1_hubble.py` + `result_ch1.json`:
- ε_central = 0.03231
- 1σ = [0.02671, 0.03755]
- 2σ = [0.02069, 0.04250]

**No legacy numbers.** In particular, the old "3% compensation" or "ε = 0.010 benchmark" narrative does NOT enter. The appendix is written entirely in the new extraction logic.

**Placement rule.** Inserted into the appendix section of the preprint at a point that respects the first-reference-wins ordering (PROPOSAL v3 §3.3). First reference to A1 occurs in §15.5.2 Probe 1 paragraph (Hubble + r_s), which is the earliest of all six retained-probe appendix citations. Therefore A1 becomes the first of the six new appendices in the preprint body.

---

## Prose draft (full — ~900 words)

### Appendix A1. Extraction of the effective uniform-ε interval from the Hubble + r_s channel

The purpose of this appendix is to set out, in one place and at the level of detail appropriate for reproducibility, how the effective one-dimensional ε-interval quoted for the Hubble + r_s channel in §15.5.2 is obtained. The appendix follows the unified per-probe template also used in Appendices A2–A6. The forward-modelling machinery — the late-time ordered-branch background, the ε-deformed expansion, and the auxiliary numerical algorithms — is collected in Appendix `app:late_cosmo_background` and Appendix `app:late_cosmo_algorithm`. The task of the present appendix is the INVERSE step: given observational inputs and the uniform-ε ansatz, to extract the one-dimensional ε-interval that this single channel admits.

**A1.1 Physics of the probe.**
Two independent determinations of the present-day Hubble rate are compared. The local distance-ladder determination H₀^SH0ES uses Cepheid-calibrated Type Ia supernovae and is insensitive to sound-horizon physics. The CMB-based determination H₀^Planck is obtained from the acoustic-scale angle θ_s = r_s/D_A(z*), measured to high precision by the Planck mission. A shift in the inferred late-time expansion rate can arise if the late-time gravitational response function changes from the ΛCDM form. In the effective uniform-ε layer adopted in §15.5.1, this response is parametrised by

$$G_{\rm eff}(z)/G_N = (1+z)^{2\varepsilon}.$$

Under this parametrisation, both the low-redshift distance integral (entering H₀^Planck through D_A(z*)) and the high-redshift sound-horizon integral (entering r_s) are modified. The channel therefore tests ε through the joint constraint imposed by a fixed, precisely-measured θ_s and an independently determined local H₀.

**A1.2 Observational inputs.**
The two anchoring values are H₀^Planck = 67.4 ± 0.5 km s⁻¹ Mpc⁻¹ from Planck 2018 in ΛCDM and H₀^SH0ES = 73.04 ± 1.04 km s⁻¹ Mpc⁻¹ from the SH0ES distance-ladder analysis. The target shift to be accommodated is therefore ΔH₀^obs = 5.64 km s⁻¹ Mpc⁻¹ with a combined uncertainty σ = (σ_P² + σ_SH²)^{1/2} ≈ 1.15 km s⁻¹ Mpc⁻¹. The acoustic-scale measurement θ_s = r_s/D_A(z*) is taken as fixed; the ε-scan is carried out at fixed θ_s, such that the ε-deformation modifies r_s and D_A(z*) in correlated ways.

**A1.3 ECT-side model.**
Under the uniform-ε ansatz, the Friedmann equation is deformed to

$$E^2_{\rm ECT}(z, \varepsilon) = \Omega_r(1+z)^4 + \Omega_m(1+z)^{3+2\varepsilon} + \Omega_\Lambda(1+z)^{2\varepsilon}$$

with ΛCDM-best-fit values Ω_m = 0.315, Ω_r = 9.2×10⁻⁵, Ω_Λ = 1 − Ω_m − Ω_r adopted as the background proxy. The low-redshift distance integral is I(ε) = ∫₀^{z*} dz/E_{\rm ECT}(z, ε) and the sound horizon is r_s(ε) = ∫_{z_drag}^∞ c_s(z)/[H₀^P · E_{\rm ECT}(z, ε)] dz, with the baryon-photon sound speed c_s(z) = c/√(3(1+R(z))), R(z) = (3Ω_b/4Ω_r)(1+z)^{-1}. The inferred H₀ under ε-deformation, at fixed θ_s, becomes

$$H_0^{\rm inferred}(\varepsilon) = H_0^P \cdot \frac{I(\varepsilon)}{I(0)} \cdot \frac{r_s(0)}{r_s(\varepsilon)}.$$

For ε > 0, r_s decreases by a larger fractional amount than I, so the ratio exceeds unity and H₀^inferred is pushed upward — the Hubble-tension direction.

**A1.4 Extraction procedure.**
The ε-dependent prediction for the Hubble-tension shift is ΔH₀^pred(ε) = H₀^inferred(ε) − H₀^P. The single-parameter chi-squared is

$$\chi^2(\varepsilon) = \left[\frac{\Delta H_0^{\rm pred}(\varepsilon) - \Delta H_0^{\rm obs}}{\sigma}\right]^2.$$

The best-fit value ε_* and the 1σ and 2σ intervals are obtained from Δχ² = 0, 1, and 4 respectively, solved by root-finding on ΔH₀^pred(ε) − ΔH₀^obs = 0, ±σ, ±2σ.

**A1.5 Derivation of 1σ and 2σ intervals.**
Direct numerical evaluation of the integrals with the parameters of A1.3 yields

$$\varepsilon_* = 0.0323, \qquad [\varepsilon_{\rm lo}^{1\sigma}, \varepsilon_{\rm hi}^{1\sigma}] = [0.0267,\ 0.0376], \qquad [\varepsilon_{\rm lo}^{2\sigma}, \varepsilon_{\rm hi}^{2\sigma}] = [0.0207,\ 0.0425].$$

The 1σ width Δε ≈ 0.0109 inherits roughly linearly from the combined uncertainty σ of the input tension. This is the numerical content of the Hubble + r_s row of Table `tab:eps_retained_probes_rebuilt` in §15.5.2.

**A1.6 Figure.**
Figure `fig:hubble_rs_extraction` shows the χ²(ε) curve together with the 1σ and 2σ shaded intervals. The Δχ² = 1 and Δχ² = 4 horizontal reference lines are drawn for clarity. All elements are rendered in grayscale per the preprint convention; interval shading uses distinct gray levels rather than colour.

**A1.7 Methodological limitations.**
Three limitations are stated explicitly and inherit to every other probe of this family. First, the background is a ΛCDM-best-fit proxy, not an ECT-native solution; the deformation is applied on top. A fully self-consistent ECT-native extraction would use the derived ordered-branch background of Appendix `app:late_cosmo_background`. Second, the sound-horizon integral is computed with a simplified baryon–photon c_s(z), a z_drag = 1059.94 anchor, and neutrino effects absorbed into Ω_r; at the level of the absolute r_s this gives a few-per-cent discrepancy with the Planck 2018 value, but the ratio r_s(ε)/r_s(0) that actually enters the extraction is more robust. Third, the uniform-ε ansatz treats ε as epoch-independent. A first-principles ε(z) from three-stage condensate closure (OP-Hubble-derive, §15.5.6) would reshape the width of the retained interval and in general would not map one-to-one onto a constant ε — this is why the retained interval is reported here as the projection of the true ε(z) history onto the uniform-ε diagnostic layer, not as a measurement of a fundamental constant.

---

## Questions to user / GPT

1. **Level of numerical detail.** The main text of the appendix quotes ε_*, 1σ, 2σ directly. Should I also include a short numerical table (ε, H₀^inferred, ΔH₀, r_s ratio) as is done in `ch1_hubble.py` output? This would add ~5 rows of numbers but make the derivation reproducible-by-hand.

2. **c_s form.** Full appendix correctness would require tighter c_s(z) with full neutrino handling, not the simplified form used here. I've noted this as limitation (A1.7); is that sufficient, or should it be elevated to an explicit caveat paragraph in A1.4?

3. **Figure numbering.** I've used label `fig:hubble_rs_extraction`. Other retained-probe figures will be `fig:jwst_extraction`, `fig:cc_extraction`, `fig:fsigma8_extraction`, `fig:isw_extraction`. Consistent with preprint conventions?

4. **Length.** ~900 words / ~3 PDF pages. Is this the right scale for each of A1–A5, or should they be longer (more extended derivations) / shorter (just the skeleton)?

5. **Unified per-probe template.** A1.1–A1.7 will be exactly replicated in A2–A5. Does the structure look right before I commit to it?
