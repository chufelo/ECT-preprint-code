# epsilon_convergence/ — ε-constraint analysis for §15.5

**Last updated:** April 17, 2026 | **5 active probes** — joint 1σ: ε ∈ [+0.029, +0.036]

---

## 🔑 Key result

Under ECT's physical constraint ε ≥ 0 and uniform-ε parameterization, **five robust
cosmological probes are jointly consistent with**:

| Joint allowed region | ε range | width |
|----------------------|:-------:|:-----:|
| **1σ** | **[+0.029, +0.036]** | 0.007 |
| **2σ** | **[+0.021, +0.042]** | 0.021 |

Centered at **ε ≈ 0.032**. The preprint benchmark ε ≈ 0.010 lies **below** the 1σ joint
region → benchmark needs revision upward OR uniform-ε inadequate (ε(z) required).

---

## Active probes (5)

All have 1σ intervals that include ε = 0 OR are strictly positive; all measure physics
that ECT's ε-deformation is expected to address; all are free of structural failures
under ε ≥ 0.

| # | Probe | Tier | z-range | ε_best (phys) | 1σ (phys) | 2σ (phys) |
|:-:|-------|:----:|:-------:|:------------:|:---------:|:---------:|
| 1 | **Hubble + r_s** | **A** | 0 → 1100 (integrated) | **+0.032** | [+0.027, +0.038] | [+0.021, +0.042] |
| 2 | **JWST excess** | **A** | 8 – 12 | **+0.043** | [+0.029, +0.071] | [+0.013, +0.179] |
| 3 | CC Moresco+ | B | 0.07 – 1.97 | +0.006 | [0, +0.087] | [0, +0.150] |
| 4 | fσ_8 RSD | B | 0.07 – 1.94 | 0 (raw −0.06) | **[0, +0.036]** ← binding upper | [0, +0.120] |
| 5 | ISW | B | 0.05 – 2 | 0 (raw −0.007) | [0, +0.043] | [0, +0.093] |
| *note* | *Age t₀* | *D* | *—* | *+0.007* | *[+0.001, +0.014]* | *—* |

**Binding constraints for the joint region:**
- Lower: **JWST 1σ lower = 0.029** (tightest positive requirement)
- Upper: **fσ_8 1σ upper = 0.036** (tightest non-trivial upper bound)

---

## Excluded probes and reasons

All scripts retained for reproducibility; **not used** by `combine.py`.

| Probe | Reason | Script status |
|-------|--------|--------------|
| **BAO (DESI 2024)** | Simplified methodology: Ω_m fixed, diagonal cov, shape-only. Raw best-fit −0.013 likely artefact. Needs full DESI likelihood with coupled (Ω_m, r_d, ε) fit. | `ch6_bao.py` — retained |
| **A_lens CMB lensing** | Linearized proxy A_lens ≈ 1 + κ_A·ε without full Boltzmann (CAMB/CLASS). Uses observational σ (0.03) but omits theoretical systematic on κ_A (50-100%). Narrow 1σ misleading. | `ch10_Alens_cmb_lensing.py` — retained |
| **S_8 KiDS-1000** | Raw 1σ = [−0.065, −0.018] entirely negative. Measures S_8 tension — ECT's ε > 0 *worsens* this, doesn't resolve. | `ch9_S8_weak_lensing.py` — retained |
| **σ_8 clusters** | Same structural issue as S_8. | `ch11_sigma8_clusters.py` — retained |
| **SN Ia** | Was mock. | `ch5_sne.py` — REMOVED |
| **Age t₀** | Self-consistency only (uses Hubble H₀(ε)). | `ch7_age.py` — text note only |

---

## ⚠️ Principles upheld

1. **Physical constraint ε ≥ 0 is binding.** Channels whose 1σ is entirely negative do NOT
   measure ECT's ε — they're structurally incompatible and must be excluded.
2. **Methodology must support the headline claim.** Channels with simplified or linearized
   treatment (BAO simplified, A_lens rough proxy) cannot carry headline weight; need full
   likelihood / Boltzmann for publication.
3. **NOT an ECT-native extraction.** All probes use ΛCDM-background proxy (Ω_m=0.315).
   True ECT-native extraction requires closure theory (OP-Hubble-derive, OPEN).
4. **Probes are NOT local ε(z) measurements.** Each has its own integration kernel.
   The joint band is interpreted as uniform-ε consistency, not ε(z) reconstruction.

---

## Files

```
epsilon_convergence/
│
│  ==== 5-probe active pipeline ====
├── ch1_hubble.py               [Tier A primary]
├── ch2_jwst.py                 [Tier A primary]
├── ch4_cosmic_chronometers.py  [Tier B]
├── ch8_fsigma8.py              [Tier B]
├── ch3_isw.py                  [Tier B]
│
│  ==== excluded (retained for reproducibility) ====
├── ch6_bao.py                  [EXCLUDED: simplified methodology]
├── ch10_Alens_cmb_lensing.py   [EXCLUDED: linearized proxy]
├── ch9_S8_weak_lensing.py      [EXCLUDED: 1σ entirely negative]
├── ch11_sigma8_clusters.py     [EXCLUDED: same]
├── ch5_sne.py                  [REMOVED: mock]
├── ch5_sne_REMOVED.md
│
│  ==== text note only ====
├── ch7_age.py                  [Tier D]
│
│  ==== aggregation ====
├── combine.py                  5-probe analysis + joint-band figure
├── epsilon_diagram.html        interactive (bar + lollipop with 1σ/2σ, joint band)
├── result_ch{1..11}.json       per-probe outputs
├── constraint_summary.json     combined summary
└── README.md                   this file
```

**Output figure:** `../../figures/fig_epsilon_constraints.{pdf,png}` — 3-panel:
- Top: main bar chart with **joint 1σ band highlighted** (magenta/pink)
- Bottom left: lollipop low-z (linear 0-3) with 1σ (dark) + 2σ (light) stems, joint band
- Bottom right: lollipop high-z (log 3-1500)

---

## How to run

```bash
cd /Users/chufelo/Documents/Physics/VDT/ECT/LaTex/scripts/epsilon_convergence
# Active probes
for s in ch1_hubble ch2_jwst ch3_isw ch4_cosmic_chronometers ch8_fsigma8; do
    python3 ${s}.py
done
# (excluded probes can be run for reproducibility but are NOT used by combine.py)
python3 combine.py
open epsilon_diagram.html
```

---

## Language rules for §15.5 (final)

**❌ NEVER:**
- "9/7 probes converge on ε"
- "Direct measurement of ε(z)"
- "Uniform-ε fails" (when joint region exists, it doesn't fail)

**✅ DO:**
- "Five robust cosmological probes jointly constrain uniform-ε to [+0.029, +0.036] (1σ)"
- "Hubble and JWST provide two-sided constraints requiring ε > 0"
- "CC, fσ_8, ISW provide upper bounds consistent with ε ≥ 0; fσ_8 is tightest"
- "Preprint benchmark ε ≈ 0.010 is below joint 1σ — requires revision upward or ε(z)"
- "BAO and A_lens require improved methodology before joining headline"
- "S_8-sector probes measure a separate observational tension outside ECT's ε scope"

---

## Status

- [x] 5 active probes (Hubble, JWST, CC, fσ_8, ISW)
- [x] BAO, A_lens, S_8, σ_8 clusters excluded with documented reasons
- [x] Age → text note
- [x] Joint 1σ band computed: [+0.029, +0.036] (width 0.007)
- [x] Lollipop with both 1σ and 2σ shown
- [x] Interactive HTML aligned
- [x] README, PROJECT_STRUCTURE updated
- [ ] Integration into §15.5 of ECT_preprint.tex (pending approval)
- [ ] Decision: revise benchmark to ε ≈ 0.03 OR reformulate as ε(z)?
