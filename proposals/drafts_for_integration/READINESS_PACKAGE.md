# Readiness Package — §15.5 Phase 2A appendix cycle

**Date:** 2026-04-19  
**Status:** All 6 appendices drafted on freeze-checkpoint numbers. All 6 grayscale figures generated. Ready for review before main-text integration.

---

## 1. Appendix package (A1–A6)

All appendices on freeze-checkpoint numbers. **No integration into `ECT_preprint.tex` yet.**

| # | File | Lines | Figure | Channel status |
|:-:|---|:-:|---|---|
| A1 | `A1_hubble_rs_FINAL.tex` | 333 | `fig_hubble_rs_extraction_bw.pdf` | stable |
| A2 | `A2_jwst_FINAL.tex` | 436 | `fig_jwst_extraction_bw.pdf` | materially revised; two robustness axes defended |
| A3 | `A3_cc_FINAL.tex` | 248 | `fig_cc_extraction_bw.pdf` | stable |
| A4 | `A4_fsigma8_FINAL.tex` | 321 | `fig_fsigma8_extraction_bw.pdf` | stable after grid-fix; negative raw explicitly explained |
| A5 | `A5_isw_FINAL.tex` | 261 | `fig_isw_extraction_bw.pdf` | provisional, proxy-level; κ_ISW not recalibrated |
| A6 | `A6_methodology_FINAL.tex` | 381 | (summary figure `fig_epsilon_constraints_bw.pdf`) | methodology + benchmark achievability + age-viability |
| **Total** | | **1980 lines** | 6 figures | |

---

## 2. Old / New / Final numbers table (frozen)

| Channel | Old 1σ (pre-recalc) | New 1σ (common module) | Final 1σ (this checkpoint) |
|---|---|---|---|
| Hubble + r_s (A1) | [0.0267, 0.0376] | [0.0267, 0.0376] | **[0.0267, 0.0376]** |
| JWST (A2) | [0.0287, 0.0710] | [0.0296, 0.0786] | **[0.0296, 0.0786]** (time budget included) |
| Cosmic Chron (A3) | [0, 0.087] | [0, 0.087] | **[0, 0.087]** |
| f σ_8 (A4) | [0, 0.036] preprint / [0, 0.058] artefact | [0, 0.0396] Brent | **[0, 0.0396]** |
| ISW (A5) | [0, 0.0433] | [0, 0.0433] | **[0, 0.0433]** (proxy unchanged) |
| **Joint 1σ** | **[0.029, 0.036]** | **[0.0296, 0.0376]** | **[0.0296, 0.0376]** |
| Joint 2σ | [0.021, 0.042] | [0.0207, 0.0425] | **[0.0207, 0.0425]** |

---

## 3. Cross-reference map

All inter-appendix references are unified under labels:

### Labels used by per-probe appendices (A1–A5)
- `\ref{app:eps_methodology}` → A6 (common background module, age-viability, benchmark achievability, excluded probes)
- `\ref{subsec:eps_def_rebuilt}` → §15.5.1 (uniform-ε definition, G_eff(z)=(1+z)^(2ε))
- `\ref{subsec:eps_retained_rebuilt}` → §15.5.2 (retained-probe table)
- `\ref{subsec:eps_joint_band_rebuilt}` → §15.5.3 (joint band)
- `\ref{subsec:eps_outlook_rebuilt}` → §15.5.6 (OP-Hubble-derive, closure program)
- `\ref{app:late_cosmo_background}` → existing background appendix
- `\ref{app:late_cosmo_algorithm}` → existing algorithm appendix

### Equations used across appendices
- `eq:eps_friedmann_A1` defined in A1.3, referenced in A3.3, A4.3, A5.1
- `eq:H0_inferred_eps` defined in A1.3, referenced in A6.4
- `eq:R_total_jwst`, `eq:R_PS`, `eq:R_time` defined in A2.3
- `eq:mu_G`, `eq:growth_ode_fsigma8` defined in A4.1
- `eq:A_ISW_model` defined in A5.3
- `eq:joint_band_A6` defined in A6.3

### Figures
- `fig:hubble_rs_extraction` — A1.6
- `fig:jwst_extraction` — A2.7
- `fig:cc_extraction` — A3.6
- `fig:fsigma8_extraction` — A4.6
- `fig:isw_extraction` — A5.6
- (summary `fig_epsilon_constraints_bw.pdf` for §15.5.3 when integrated)

---

## 4. What needs updating in §15.5.2 and §15.5.3 after appendix-freeze

When integration is approved, these main-text updates follow:

### §15.5.2 (retained probes table)
- Numerical update: row 2 (JWST) 1σ interval `[0.029, 0.071]` → `[0.0296, 0.0786]`
- Row 4 (fσ_8): upper bound `0.036` → `0.0396` (or keep `0.036` with Brent-precision footnote)
- Add `\ref{app:eps_extraction_hubble}` through `\ref{app:eps_extraction_isw}` cross-refs in the table's rightmost column

### §15.5.3 (joint band)
- Numerical update: band `[0.029, 0.036]` → `[0.0296, 0.0376]`
- Insert figure `\ref{fig:epsilon_constraints}` (using `fig_epsilon_constraints_bw.pdf`)
- Add short paragraph: "Channel-by-channel extractions in
  Appendix~\ref{app:eps_extraction_hubble} through
  Appendix~\ref{app:eps_extraction_isw}; methodology in
  Appendix~\ref{app:eps_methodology}."

### §15.5.6 (outlook)
- Add viability-note reference to A6.4 (age-viability ambiguity)
- No new OP-age-consistency (per GPT r19+r20+r21 consensus)

### Cascade (after §15.5 integration)
- Abstract: no change expected (uniform-ε values differ at 3rd sig fig)
- Introduction: no change expected
- Part II Conclusions: numerical update if band is quoted
- Observational Tests: no change expected (this is §15.5 itself)

---

## 5. Unified appendix-order plan

Proposed ordering in preprint appendices:
1. Existing appendices (background, algorithm, etc.)
2. A1 `app:eps_extraction_hubble`
3. A2 `app:eps_extraction_jwst`
4. A3 `app:eps_extraction_cc`
5. A4 `app:eps_extraction_fsigma8`
6. A5 `app:eps_extraction_isw`
7. A6 `app:eps_methodology`

A6 comes last because it is referenced by all of A1–A5 and collects methodology + benchmark + age-viability.

---

## 6. Summary for user + GPT review

**All GPT r17–r21 required items present in the drafts:**

- r17: common background module (A6.1), all 5 channels re-expressed (A6.2)
- r18: no "ECT-native" overclaim — "re-expressed against common module" (A6.1, A6.2, A6.3 explicit)
- r19: JWST robustness check (A2.4), Brent refinement for fσ_8 (A4.4), age-viability ambiguity (A6.4), ISW provisional (A5.3, A5.7(iv))
- r20: physics + observable + ECT model + extraction procedure + origin of 1σ/2σ all explicit in each appendix (A1.1–A1.5, A2.1–A2.6, A3.1–A3.5, A4.1–A4.5, A5.1–A5.5)
- r21 (1): A2 two robustness axes (p-scaling + z_form, A2.4)
- r21 (2): A2 main physical finding paragraph (time budget makes JWST more, not less, consistent with Hubble; A2.3)
- r21 (3): A4 explicit explanation of negative raw best-fit + physical prior clipping + one-sided bound (A4.5, A4.7(i))
- r21 (4): A5 maximum-honesty framing (proxy-level only, κ_ISW not recalibrated, not same epistemic level as A1–A4; A5.3, A5.7)
- r21 (5): A6 as binding glue (A6.1–A6.7)
- r21 (6): excluded probes NOT silently dismissed (A6.6 explicit audit)

**Still deferred beyond this checkpoint:**
- Closure-level ECT background replacing ΛCDM proxy (OP-Hubble-derive)
- ISW kernel recalibration on common background (deferred to Phase 3)
- Full BAO/S_8/A_lens pipeline reconsideration
- Main-text integration (gated on review)

---

*End of Readiness Package.*
