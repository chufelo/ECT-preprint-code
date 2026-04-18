# §15.5.4 — Excluded and stress-test probes

**Status:** v1 for review (user + GPT) | **Target:** Step 2.1 subsection 4 of 6 | **Date:** 2026-04-18

**Design log:**
- Three categories per PROPOSAL v3 §A.15.5.4 with *strict structural separation*: (i) methodology-limited, (ii) outside ε-sector (category error), (iii) non-independent / placeholder.
- Category (ii) strengthened with explicit "category error" language per PROPOSAL v3 Key Change 5.
- **Data source**: `scripts/epsilon_convergence/result_ch{6,9,10,11,7}.json` and `ch5_sne_REMOVED.md`. No re-ask.
- **No legacy Hubble compensation numbers** (3%, 2.85%, 2.90%, 69 km/s/Mpc) anywhere per user directive 2026-04-18.
- **No specific legacy ε values** (0.010, 0.012) per user directive. Raw best-fit numbers quoted **only where they are the defining feature of the exclusion** (e.g., S_8 raw 1σ entirely negative — this IS the structural argument). For Age t₀, we quote qualitative statement, not ε number.
- Bridge-style consistent with §15.5.2/§15.5.3.
- **No new figure** (§15.5.4 is text-only).
- **New labels planned**: `subsec:eps_excluded_rebuilt`.
- Methodological-requirement list in (i) is NOT a formal OP list per PROPOSAL v3 §E.8 — written as text notes, not OP-* entries.

---

## Final draft text (~820 words)

### §15.5.4 Excluded and stress-test probes

**[Opening bridge.]** Beyond the retained five-probe set of §15.5.2, several additional cosmological channels were considered in the present analysis but are not used in the joint effective band of §15.5.3. We group them into three categories whose underlying reasons for exclusion are structurally distinct.

**Category (i) — Excluded because methodology-limited.** These channels probe the same effective ε-sector as the retained probes and could in principle re-enter the joint band at a later stage, but the extraction pipelines currently implemented for them are insufficiently explicit to support a headline result. **The incompatibility is methodological, not structural**: upgrading the pipeline (a full likelihood or full Boltzmann implementation) would allow them to be included.

- **BAO (DESI 2024 DR1).** The present BAO channel is fit with a simplified shape-only treatment in which Ω_m is independently fixed, the covariance is treated as diagonal, and H₀ and r_d are profiled on a reduced grid. Under this simplified pipeline the raw 1σ interval is two-sided but straddles ε = 0 with negative central. This negative central is most naturally read as an artefact of the independent Ω_m fixing rather than as evidence against the ε-sector. A headline inclusion of BAO requires the full DESI likelihood with coupled (Ω_m, r_d, ε) fit, which is not implemented here. The channel is therefore retained in the project pipeline for reproducibility but is not part of the joint band.
- **A_lens CMB lensing.** The present CMB-lensing channel is evaluated through a linearised proxy A_lens ≈ 1 + κ_A·ε. The observational uncertainty used is Planck's, but the theoretical systematic on κ_A under such a linearisation is large (bracketed κ_A ∈ [2, 4] in the present proxy). The resulting narrow 1σ interval is therefore not credible at the headline level. Inclusion at headline level requires a full Boltzmann-code implementation (CAMB/CLASS) in which A_lens is predicted rather than linearised. The channel is retained in the project pipeline for reproducibility and not part of the joint band.

**Category (ii) — Excluded because outside the present ε-sector (category error).** This category is distinct in kind from (i). The channels listed here have raw 1σ intervals that lie **entirely in the region ε < 0**. Under the uniform-ε ansatz and the physical prior ε ≥ 0 of §15.5.1, ε > 0 *worsens* the observational tension they report rather than accommodating it. Including them as ε-band constraints would therefore be a category error: the tension they carry is a separate observational puzzle whose resolution, if any, lies outside the ε-sector as presently parameterised. **Unlike category (i), no amount of methodological improvement to the ε-fit would change this — the incompatibility is structural.**

- **S_8 weak lensing (KiDS-1000).** The raw 1σ interval obtained under a rough linearised estimate is entirely negative (1σ ~ [−0.065, −0.018], with 2σ reaching up to zero but not crossing it). This is the quantitative signature of the S_8 tension and is independent of the detailed proxy kernel choice within its bracketed range. The S_8 tension is a recognised observational puzzle in the broader cosmological literature; the present analysis does not claim to address it.
- **σ_8 cluster counts.** The same structural pattern recurs for σ_8 as inferred from cluster-count surveys (informal survey-averaged 1σ ~ [−0.031, −0.009], entirely negative). The exclusion rationale is identical to that of S_8.

In both cases the statement is not that these probes are incorrect, but that they measure physics outside the ε-sector as currently parameterised. No future methodological improvement on the ε-side refits would alter the sign of the raw constraint.

**Category (iii) — Non-independent or placeholder channels.** This category covers channels that cannot add independent information under the present methodology or that were previously included in mock form.

- **Age t₀.** Under a self-consistent treatment in which H₀(ε) is inherited from the Primary Hubble channel, the Age t₀ constraint carries no independent information: it is a downstream consistency check of the Hubble pipeline rather than an independent ε-probe. It is therefore noted only as a text-level consistency item and does not enter the joint band.
- **Type Ia supernovae (SN Ia).** An earlier placeholder SN Ia channel in the project pipeline was constructed from a ΛCDM-baseline template rather than from an actual observational dataset with SH0ES calibration and host-galaxy systematics. Fitting the ECT ansatz to a template derived from ΛCDM is guaranteed to return ε ≈ 0 by construction and is not a genuine observational test. The placeholder has been removed from the pipeline. A genuine SN Ia ε-probe requires actual Pantheon+ observed distance moduli with the full SH0ES calibration and host-systematics chain, and is not implemented at the present analysis level.

**Cross-category principle.** Categories (i) and (ii) are fundamentally different. Category (i) describes channels which *could* re-enter the joint band under an upgraded pipeline; category (ii) describes channels which *cannot* do so under any refinement of the ε-extraction alone, because their raw support lies outside the prior ε ≥ 0. Keeping these two categories distinct is essential to avoid presenting the S_8-sector tension as an ε-band constraint.

**Bridge.** A short comparison of the ECT-ε result reported above with alternative proposals for the same set of observational tensions is given in §15.5.5.
