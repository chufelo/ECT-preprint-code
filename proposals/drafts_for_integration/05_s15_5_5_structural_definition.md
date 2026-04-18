# §15.5.5 — Comparison with other approaches

**Status:** v2 for review (GPT round 12 applied) | **Target:** Step 2.1 subsection 5 of 6 | **Date:** 2026-04-18

**Design log:**
- PROPOSAL v3 Key Change 6 rules **enforced**: short categorical, ≤2 refs per category max, no literature survey.
- Four categories: ΛCDM, EDE, Modified gravity, Phenomenological G_eff(z).
- **GPT round 12 corrections** (5 edits):
  1. Opening rephrased: listing of probed observational pattern (Hubble / JWST / late-time consistency channels), not "observational tensions".
  2. ΛCDM paragraph: softened, late-time consistency probes noted as part of standard ΛCDM fitting framework; removed overgeneralising "each observational anomaly addressed through separate" claim.
  3. EDE: "not designed to simultaneously..." → "not primarily constructed as... model-dependent".
  4. Modified gravity: removed imprecise "galactic-scale motivation" blanket claim (wrong for f(R)); heterogeneous-class framing; added ECT-distinguishing sentence.
  5a. `DESI2024` removed (observational BAO paper, wrong reference class); replaced with `Uzan2011` (proper methodology review — Living Reviews in Relativity 14, 2).
  5b. Key rhetorical point rephrased: removed "derived structurally" / "independent observations" overclaims; use "condensate-closure-motivated drift, treated here at the effective level" / "compatible with multiple observational channels".

**References added to `references.bib`** (per §3.1 rule 2: new sources immediately):
- `Poulin2019` — Poulin, Smith, Karwal, Kamionkowski, PRL 122, 221301 (2019) — EDE flagship paper (added earlier)
- `Sotiriou2010` — Sotiriou & Faraoni, RMP 82, 451 (2010) — standard f(R) review (added earlier)
- `Uzan2011` — Uzan, LRR 14, 2 (2011) — varying constants/gravitation/cosmology review (added 2026-04-18 for GPT r12)

**References re-used from existing bib**:
- `Planck2018` — ΛCDM anchor
- `Milgrom1983` — MOND foundational

**Category → refs count:**
- ΛCDM: 1 (Planck2018)
- EDE: 1 (Poulin2019)
- Modified gravity: 2 (Milgrom1983, Sotiriou2010) — at GPT-LOCKED maximum
- Phenomenological G_eff(z): 1 (Uzan2011)

**`DESI2024` no longer cited in §15.5.5** — it stays in `references.bib` (used elsewhere in preprint).

---

## Final draft text (~560 words)

### §15.5.5  Comparison with other approaches

The retained five-probe effective band of §15.5.3 can be briefly placed in the context of alternative proposals addressing the same observational pattern discussed in §§15.5.2–15.5.4, namely the Hubble discrepancy, the JWST high-redshift abundance anomaly, and the associated late-time consistency channels.

**ΛCDM.** The base ΛCDM model does not accommodate the Hubble discrepancy or the JWST early-galaxy excess within its minimal parameter space. In practice, these tensions are typically discussed either in terms of residual systematics or by extending the baseline model in different directions, while the late-time consistency probes retained in §15.5.2 are already part of the standard ΛCDM fitting framework [Planck2018].

**Early Dark Energy.** Early-dark-energy proposals primarily target the Hubble discrepancy through a pre-recombination modification of the expansion history, typically by introducing one or more additional components or effective functions [Poulin2019]. In their basic form they are not primarily constructed as a simultaneous explanation of the high-redshift structure-formation anomalies discussed here; whether they help with the JWST sector is model-dependent and not part of their minimal motivation.

**Modified gravity.** Modified-gravity approaches form a heterogeneous class. MOND-type scenarios and TeVeS are historically tied most directly to galactic phenomenology, while scalar-tensor and f(R)-type models are often motivated by late-time background and growth modifications [Milgrom1983, Sotiriou2010]. What distinguishes the present ECT use of the ε-sector is not simply that gravity is modified, but that a single effective deformation is confronted here with both high-redshift and late-time cosmological channels within one common diagnostic layer.

**Phenomenological G_eff(z) deformations.** The ε-deformation used in the present analysis is related to a broader class of phenomenological varying-coupling or effective-response parameterizations considered in cosmology [Uzan2011]. What distinguishes the ECT use of this class is that the present effective deformation is motivated by ECT's three-stage condensate-closure picture and then constrained empirically here, rather than introduced as an otherwise free late-time fitting function.

**Key rhetorical point.** The observation that one and the same effective deformation parameter admits a narrow retained-five-probe effective band across observationally distinct channels serves as an indirect consistency check for the framework. One mechanism — condensate-closure-motivated drift, treated here at the effective level — remains compatible with multiple observational channels within a single narrow band. This parsimony does not constitute a proof of ECT, but it does strengthen the plausibility of its cosmological strategy relative to approaches that require separate parameters or separate mechanisms for different anomalies.

**Honest caveats.** Three qualifications are stated explicitly. First, the retained five-probe set is a restricted subset of the broader cosmological dataset; BAO, A_lens, and the S_8-sector probes contribute uncertainties and tensions not captured in the joint effective band (§15.5.4). Second, the comparison above is with schematic representatives of alternative proposals, not with their full modern pipelines. Third, the ECT treatment of the ε-sector in §15.5 is effective, not first-principles; the closure-derived ε(z) remains open and is logged as such in §15.5.6.

**Bridge.** The implications of the retained five-probe effective band for the broader ECT programme, and the list of open problems associated with the ε-sector, are discussed in §15.5.6.

---

## Integration readiness

Per GPT round 12 vердикт: *"После этих 5 правок я считаю §15.5.5 готовым к внедрению."* — draft готов к integration.
