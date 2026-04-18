# ECT Project — Structure and Active Files

**Last updated:** April 18, 2026 | **Single source of truth** — update on every structural change.

**Current active work:** §15.5 rebuild, Phase 1 (parallel creation). §15.5.1 + §15.5.2 + §15.5.3 integrated (PDF pp. 246–250). Next: drafting §15.5.4 (excluded probes: methodology-limited / outside ε-sector / non-independent).

---

## 1. High-level overview

```
/Users/chufelo/Documents/Physics/VDT/ECT/
│
├── LaTex/                      ← MAIN WORKSPACE
│   ├── ECT_preprint.tex        ← 🟢 Main preprint (~583 pp) — §15.5 rebuild pending
│   ├── ECT_preprint.pdf
│   ├── references.bib          ← 🟢
│   ├── ECT_pop.tex / .pdf      ← 🟢
│   ├── ECT_pop_ru.tex          ← 🟡 Russian in progress
│   ├── PROJECT_STRUCTURE.md    ← 🟢 THIS FILE
│   ├── save_version.sh
│   ├── proposals/              ← 🟢 Drafts before preprint edits
│   │   ├── drafts_for_integration/
│   │   │   ├── 01_s15_5_1_structural_definition.md ← 🟢 v3 FINAL
│   │   │   ├── 01_s15_5_1_LATEX_SNIPPET.tex        ← 🟢 ready-to-paste
│   │   │   └── 01_INSERTION_GUIDE.md               ← 🟢 user's insertion steps
│   │   └── PROPOSAL_s15_5_rebuild_v3.md (+ corrections §8) ← 🟢 authoritative
│   ├── companion/              ← 🟢
│   ├── figures/                ← 🟢 grayscale only
│   ├── scripts/                ← 🟢 Python apparatus
│   │   └── epsilon_convergence/  ← 🟢 ε-ANALYSIS
│   ├── backup/                 ← 🟡 Versioned backups
│   └── drafts/, versions/, misc/, restored/, arcive/ ← 🟡⚫
└── github_repo/                ← 🟢 GitHub clone (branch: master)
```

---

## 2. Status legend

| Icon | Meaning |
|:----:|---------|
| 🟢 | **ACTIVE** |
| 🟡 | **STAGING / BACKUP** |
| ⚫ | **ARCHIVE / REMOVED / SUPERSEDED** |

---

## 3. Core workflow rules

### 3.1 — Backup, commit, structure-update
1. Backup before editing `ECT_preprint.tex`/`ECT_companion.tex` → `backup/ECT_preprint_BACKUP_vN_<desc>.tex`
2. New references → `references.bib` immediately
3. After confirmed edit → git commit + push
4. Structure changes → update THIS FILE immediately
5. Major restructuring → draft in `proposals/` first, get approval, then implement
6. Page count rule — after every compilation, report "X pages (was Y)"
7. Edit permission — NEVER edit preprint without explicit "integrate"/"insert"/"внедряй" approval
8. PHENOM-RULE — unsanctioned phenomenological numbers: flag, don't propagate

### 3.2 — Figure rules
- 🎨 **All figures/plots MUST be grayscale**. Use linestyles (solid/dashed/dotted/dash-dot) and markers (circle/square/triangle/diamond).
- Filenames: `fig_<topic>.{pdf,png}`. Scripts: `scripts/fig_<topic>.py`.

### 3.3 — Appendix insertion order rule
- New appendices inserted in **order of first reference**. Rename existing letters if needed. Apply independently to companion.

### 3.4 — Language discipline
- Never "derived" unless rigorously proven in current paper
- Never "ECT predicts X" when only "ECT admits a route toward X" is justified
- "Effective" framing preferred for data-inferred quantities
- "Level A / B / Open" — strict usage
- **Cosmological ε** — see §6.3 language rules v5

### 3.5 — Principle of no information loss (3 axes)

**Axis A — migration disposition:** verbatim / reframe / demote-to-appendix / retire
**Axis B — info-loss level:** content / structural (labels, refs, fig/tab/app) / argument-flow
**Axis C — Can this statement survive unchanged?** yes / rephrase / relocate / remove

No silent drops. Every existing item gets A × B × C assignment in Step 2.0 inventory.

### 3.6 — Parallel creation strategy for major restructurings

- **Phase 1 — create in parallel.** New subsections (§15.5'), new appendices alongside existing. Old content NOT touched.
- **Phase 2 — validate.** Compile, cross-check new vs old, GPT review on both.
- **Phase 3 — switch.** Single session: remove old, update all cross-refs in one pass.
- **Phase 4 — cleanup.** Reports, audits, companion mirror.

### 3.7 — Post-integration task list (do NOT forget after §15.5 rebuild)
1. Recalculate universe age range under retained five-probe effective band
2. Redraw evolution diagrams under new band; consistency check with t_0 and JWST
3. Paper-wide ε benchmark audit — every remaining specific ε value outside §15.5

### 3.8 — Retained-probe table column schema (LOCKED)

For §15.5.2 retained-probe table, exactly these columns in this order:
1. Probe
2. Nature of constraint
3. What is actually fitted
4. Kernel / epoch sensitivity
5. Role in §15.5 (primary / consistency)

---

## 4. `proposals/` — drafts before preprint edits

### 4.1 Active drafts for integration (Step 2.1 output)

| File | Status |
|------|:------:|
| `drafts_for_integration/01_s15_5_1_structural_definition.md` | 🟢 v3 FINAL — approved by user+GPT |
| `drafts_for_integration/01_s15_5_1_LATEX_SNIPPET.tex` | 🟢 ready-to-paste |
| `drafts_for_integration/01_INSERTION_GUIDE.md` | 🟢 user's insertion steps (Step A through F) |

### 4.2 Authoritative §15.5 rebuild proposal

`PROPOSAL_s15_5_rebuild_v3.md` + corrections in §8 — authoritative overall plan.

### 4.3 Integration progress

| # | Subsection | Draft status | Integrated in preprint |
|:-:|-----------|:------------:|:-----------------------:|
| 15.5.1 | Structural definition | **🟢 v3 FINAL approved** | **✅ integrated 2026-04-18 (PDF p.246)** |
| 15.5.2 | Retained 5-probe analysis | **🟢 v2 FINAL approved (GPT round 5+6)** | **✅ integrated 2026-04-18 (PDF pp.247–249)** |
| 15.5.3 | Joint band + benchmark | **🟢 FINAL (GPT round 7 + user directive: no legacy numbers)** | **✅ integrated 2026-04-18 (PDF pp.249–250)** |
| 15.5.4 | Excluded probes | 🟡 next (methodology-limited / outside ε-sector / non-independent) | — |
| 15.5.4 | Excluded probes | 🟡 queued | — |
| 15.5.5 | Comparison with other approaches | 🟡 queued | — |
| 15.5.6 | Interpretation and outlook | 🟡 queued | — |

---

## 5. Key figures

Grayscale only; linestyles for distinction.

| File | Section | Content |
|------|---------|---------|
| `fig_epsilon_constraints.{pdf,png}` | §15.5' | **5-probe joint effective band [+0.029, +0.036]** |
| (other figures unchanged) | — | — |

---

## 6. `scripts/epsilon_convergence/` — ε-CONSTRAINT ANALYSIS

**Current result:** 5-probe joint effective band **ε ∈ [+0.029, +0.036]** (1σ); [+0.021, +0.042] (2σ).

### 6.1 Active / excluded
- **Active (5):** Hubble+r_s, JWST, CC, fσ_8, ISW
- **Excluded (i) methodology-limited:** BAO, A_lens
- **Excluded (ii) outside ε-sector (category error):** S_8, σ_8 clusters
- **Excluded (iii) non-independent/placeholder:** Age (text note), SN Ia (removed)

### 6.2 Benchmark system (FINAL)
- **Only one entity:** the retained-five-probe effective band [+0.029, +0.036]
- **No legacy values** (0.010, 0.012, or any past benchmark number)
- Midpoint ε ≈ 0.032 used only as contextual illustration phrase

### 6.3 Language rules v5 (FINAL)

**❌ NEVER:**
- "Probes converge" / "Direct ε(z) measurement" / "Uniform-ε fails"
- "ECT resolves/fully resolves/matches"
- ANY specific ε value other than band-internal — especially NOT 0.010, 0.012
- "ε_rep" as a symbol
- "Joint allowed band" without "effective"
- "Strictly ε ≥ 0" (use "requires in the effective parameterization ... physical prior")
- "Such a channel does not measure ECT's ε" — use "is not retained as a headline ε-probe"

**✅ DO:**
- "Retained five-probe uniform-ε analysis"
- "Compatibility with the retained band"
- "For illustration, midpoint of the retained band (ε ≈ 0.032)"
- "Retained probes form a consistency set, not five direct local measurements"
- "In the effective uniform-ε parameterization used here, the intended three-stage relaxation picture of ECT motivates and, within the present diagnostic layer, requires the prior ε ≥ 0"
- "Is not retained as a headline ε-probe in the present effective analysis"
- "One derived mechanism compatible with multiple independent observations — indirect consistency check"
- "This retained-five-probe effective band is an empirical result of the present analysis, not a first-principles ECT prediction"

---

## 7. External resources
- GitHub: `https://github.com/chufelo/ECT-preprint-code`
- Zenodo DOI: `https://doi.org/10.5281/zenodo.18917929`
- LaTeX: `/Library/TeX/texbin/pdflatex` | Graphviz: `/opt/homebrew/bin/dot`

---

## 8. Recent changes

| Date | Change |
|------|--------|
| 2026-04-18 | **§15.5.3 INTEGRATED** into `ECT_preprint.tex` via parallel-creation strategy (§3.6 Phase 1). New `\subsubsection*{15.5.3 Joint effective allowed band and working benchmark}` inserted after §15.5.2 block. **All 10 GPT round 7 corrections applied** (headline scope-of-applicability tightened with "within the present methodology"; "centred near the midpoint" removed; range-based scaling table replaces midpoint-based table; Benchmark B paragraph editorial metalanguage removed; Benchmark A opens with hard "legacy only" sentence; future-figure label dropped; `epsilon_diagram.html` removed from main text; narrow-width sentence softened; §15.5.4 bridge softened). **User directive 2026-04-18 applied (binding)**: no legacy Hubble compensation numbers (3%, 2.85%, 2.90%, 69 km/s/Mpc) and no legacy specific ε values (0.010, 0.012) appear in new §15.5 main text; these are deferred to Appendix X2 (methodology) only. Inventory items #1, #9, #11c, #13, #14b **reclassified** from "reframe → §15.5.3 main text" to "demote-to-appendix only". **Python guard script** verifies no forbidden legacy tokens present in new §15.5.3. **3 new labels** resolved cleanly (subsec:eps_joint_band_rebuilt, eq:eps_joint_band_rebuilt, tab:eps_scaling_benchmark_B); PDF pp. 249–250. **Page delta: 641 → 642 (+1).** Compile: 0 errors, 0 undef refs, 0 multiply-def. Backup: `ECT_preprint_BACKUP_v5_pre_s15_5_3.tex`. Script: `scripts/insert_s15_5_3.py`. **Cascade TODO logged (PROPOSAL v3 §E.11):** article-wide audit of residual `ε = 0.01` / `3%` / `69 km/s/Mpc` references in remaining old-apparatus content (e.g. §15.2, §15.4, §14.6, `sec:isw_diagnostic`, `sec:mp_jwst_cosmo` and other referrers of old §15.5) — to be performed in a later polishing pass once §15.5.4–15.5.6 are drafted and full Phase 3 switchover is imminent. |
| 2026-04-18 | **§15.5.2 GPT round 6 polish applied** (surgical, 8 edits): (1) CCHP/Freedman sentence removed from Probe 1 Hubble paragraph (not part of the adopted extraction pipeline); (2) "upper bounds = upper edges of raw intervals after imposing ε≥0, not separate positive-domain refits" methodological note added after two-sided/upper-bound distinction; (3) Probe 3/4/5 language unified to "we therefore report this channel as a one-sided upper bound:"; (4) Probe 5 "raw central" → "raw likelihood maximum lies near"; (5) Probe 2 "yields" → "is translated here into"; (6) Probe 2 "binding lower bound" softened to "will become the lower edge of the joint effective band discussed in §15.5.3"; (7) consistency-window paragraph closed with "structured consistency test of a common effective deformation layer, not a claim of strict statistical independence"; (8) table caption "analysis" → "analysis layer". Pages 641 stable. 0 errors, 0 undef refs, 0 multiply-def. Backup: `ECT_preprint_BACKUP_v4_pre_s15_5_2_gpt_r6.tex`. Script: `scripts/fix_s15_5_2_gpt_r6.py`. Snippet file `02_s15_5_2_LATEX_SNIPPET.tex` and inventory `02_s15_5_2_INVENTORY.md` synced. |
| 2026-04-18 | **§15.5.2 INTEGRATED** into `ECT_preprint.tex` via parallel-creation strategy (§3.6 Phase 1). New `\subsubsection*{15.5.2 Retained five-probe effective analysis}` + LOCKED 5-column retained-probe table + 5 per-probe paragraphs + non-independence paragraph, inserted after §15.5.1 block and before old §15.5 annotation. **GPT round 5 corrections applied**: Hubble "effective distance-ratio proxy" softening + explicit "H1-type extraction, not full H2/CMB pipeline" statement; JWST "representative enhancement target of order R~10" softening + explicit "proxy-level, not full structure-formation pipeline" statement; fσ_8 "raw likelihood maximum" wording; ISW explicit "linearised proxy ... rather than a full fit to C_ℓ^Tg estimator"; non-independence paragraph strengthened with shared-ingredient specifics; "working effective benchmark" removed from bridge (→ "joint effective band"); table Hubble/JWST rows hardened. **7 new labels resolved cleanly** (subsec:eps_retained_rebuilt, tab:eps_retained_probes_rebuilt, eq:eps_{hubble,jwst,cc,fsigma8,isw}_retained); PDF pp. 247–249. **Page delta: 639 → 641 (+2).** Compile: 0 errors, 0 undef refs, 0 multiply-defined. Numerics from `scripts/epsilon_convergence/result_ch{1,2,3,4,8}.json`. Backup: `ECT_preprint_BACKUP_v3_pre_s15_5_2.tex` (MD5 b019f1cb79bd47f3df43c8b193bcc4f0). Script: `scripts/insert_s15_5_2.py`. Companion no-loss inventory: `proposals/drafts_for_integration/02_s15_5_2_INVENTORY.md` (14 items of old §15.5 with Phase 3 disposition). |
| 2026-04-18 | **§15.5.1 v3 INTEGRATED** into `ECT_preprint.tex` via parallel-creation strategy (§3.6 Phase 1). New `\subsection*{...rebuilt version --- under construction}` + `\subsubsection*{15.5.1 Structural definition...}` inserted immediately before existing §15.5 (line 20357). Labels: `sec:cosmo_constraints_rebuilt`, `subsec:eps_def_rebuilt`. Old §15.5 fully intact with top-of-section "rebuilt in parallel" annotation. **Page delta: 638 → 639 (+1).** Compile clean: 0 errors, 0 undefined refs, 0 multiply-defined labels; +1 overfull vbox (8.7pt, cosmetic). Backup: `ECT_preprint_BACKUP_v1_pre_s15_5_rebuild.tex` (MD5 a571bc9b71e0f47f354f551679b77320). Script: `scripts/insert_s15_5_1.py`. **GPT round 4 follow-up fixes (same commit):** placeholder TODO resolved to `\ref{par:planck_scale}`; `v_0` → `u_0` (notation alignment with rest of preprint); "controlled by" → "tied to" (softer phrasing per GPT). |
| 2026-04-17 | Proposals v1→v3 + corrections; drafting phase began |
| 2026-04-17 | **§15.5.1 v3 FINAL** approved (GPT review round 4 passed): opening does-not-re-derive statement; physical prior softened to "motivates and, within the present diagnostic layer, requires the prior"; operational consequence as decision-of-analysis ("is not retained as a headline ε-probe"); cross-ref placeholder added for v_0^{-2}; "retained five-probe uniform-ε analysis" shortened phrasing |
| 2026-04-17 | Prepared `01_s15_5_1_LATEX_SNIPPET.tex` + `01_INSERTION_GUIDE.md` for user-side physical insertion |
| 2026-04-17 | Added Axis C to no-info-loss schema (§3.5); locked retained-probe table schema (§3.8) |

---

**End of structure file.**
