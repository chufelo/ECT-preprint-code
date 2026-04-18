# No-loss inventory — Old §15.5 (`sec:mp_hubble`, lines 20468–20781, ~13.7 KB)

**Purpose:** Per PROJECT_STRUCTURE.md §3.5 (no-loss) and user directive (2026-04-18): *"ничего из текущего содержимого статьи по этой теме не было потеряно"*. Every element of the old §15.5 block is catalogued and assigned a migration disposition. Phase 1 keeps old §15.5 physically intact; this inventory is the prescription for Phase 3 switchover.

**Schema:** Axis A = verbatim / reframe / demote-to-appendix / retire. Axis B = content / structural / argument-flow. Axis C = yes (survive unchanged) / rephrase / relocate / remove.

---

## Migration table

| # | Element | Loc. in old §15.5 | Axis A | Axis B | Axis C | Target location in new §15.5 / apparatus | Notes |
|:-:|---------|:-----------------:|:------:|:------:|:------:|------------------------------------------|-------|
| 1 | Status note (Level B; $\Delta H_0/H_0\approx 3\%$ closure-dependent) | opening paragraph | reframe | argument-flow | rephrase | **§15.5.3** Benchmark A retention (as the legacy 3% number) | Level B rating already expressed in §15.5.1 (methodological status paragraph). The **3%** number reclassified as Benchmark A low-drift illustrative point. |
| 2 | Bridge from age apparatus | `\paragraph{Bridge from the age apparatus.}` | reframe | argument-flow | rephrase | **§15.5.3** opening bridge | Cross-ref to `\S\ref{sec:universe_age}` preserved in §15.5.3. |
| 3 | Observational landscape (Planck + SH0ES + CCHP/Freedman numerics) | `\paragraph{Observational landscape.}` | reframe | content | rephrase | **§15.5.2 Probe 1 paragraph (partial)** | Planck2018 and Riess2022 numerics reframed and migrated into §15.5.2 Probe 1 context. Freedman2024 / CCHP mention retired from §15.5.2 per GPT round 6 (kept in inventory; available for later use in §15.5.5 / outlook or as footnote). |
| 4 | Structural mechanism ($G_{\rm eff}=G_N e^{-\beta\phi_b}$ derivation) | `\paragraph{Structural mechanism.}` | demote-to-appendix | content | relocate | **Appendix X2 (methodology)** | Short motivational form is in §15.5.1 via `\ref{par:planck_scale}`; full $e^{-\beta\phi}$ detail to appendix. |
| 5 | Sign theorem (formal $G_{\rm eff}>G_N \Rightarrow \delta H_0>0$ with QED) | `\paragraph{Sign theorem for the Hubble-shift route.}` | demote-to-appendix | content | relocate | **Appendix X2** | Formal proof preserved as a lemma in X2. |
| 6 | "Not a $\Lambda$CDM deformation by fiat" methodological statement | `\paragraph{Not a \Lambda CDM deformation by fiat.}` | reframe | argument-flow | rephrase | **§15.5.6** (one sentence) | Already partly covered by §15.5.1's "not a first-principles prediction" language. Distilled to one sentence in outlook. |
| 7 | Correlated-sign prediction (Hubble ↔ age, distance, JWST formation time) | `\paragraph{Correlated-sign prediction.}` | reframe | argument-flow | rephrase | **§15.5.6** (parsimony paragraph) | Naturally integrates into the "one mechanism compatible with multiple observations" framing of §15.5.5/§15.5.6. |
| 8 | Structural $w_0$–$H_0$ correlation | `\paragraph{Structural w_0--H_0 correlation.}` | demote-to-appendix + reframe | content | relocate | **Appendix X2** (full statement) + **§15.5.6** (one sentence) | Quantitative claim in appendix; qualitative correlation noted in outlook. |
| 9 | BBN localisation of the Hubble mechanism | `\paragraph{BBN localisation...}` | reframe | content + structural | rephrase | **§15.5.3** (BBN constraint on benchmark extrapolation) + **§15.5.4** (epoch-of-validity note) + **Appendix X2** (full argument) | Cross-ref to `\S\ref{sec:mp_flrw}` preserved. |
| 10 | **Minimal benchmark closure** subsubsection with 4 eqs | `\subsubsection*{...}` + `eq:late_cosmo_action`, `eq:ect_late_friedmann`, `eq:ect_h0_shift_exact`, `eq:ect_h0_shift` | demote-to-appendix | content + structural | relocate | **Appendix X2** (full benchmark apparatus) | **All four equation labels preserved** in X2. Any external `\eqref{}` resolves to X2. |
| 11a | `eq:epsilon_eff_def` ($\mu(a)$, $\varepsilon_{\rm eff}$ definitions) | line within "Robust definition..." | **scheduled retire-after-redirect** | structural | **remove (at Phase 3)** | — | Superseded by `eq:mu_def_rebuilt` in §15.5.1, **but may only be retired after a full audit and redirection of all external references in Phase 3**. Until then the label remains live. ★ critical label. |
| 11b | `eq:epsilon_eff_benchmark` (benchmark rewriting $\mu=\exp[-\beta\Delta\phi]$, $\varepsilon_{\rm eff}=\beta q/2$) | within same paragraph | demote-to-appendix | content | relocate | **Appendix X2** | Label preserved. |
| 11c | Statement: *"$\varepsilon=0.01$ ... is a late-time benchmark slope ... not an independently derived first-principles constant"* | same paragraph | reframe | argument-flow | rephrase | **§15.5.3 Benchmark A** retention paragraph | The specific ε = 0.01 becomes the **Benchmark A legacy illustrative point** (retained outside 1σ joint region). |
| 12 | H1 vs H2 paragraph (late-time closure-level vs full CMB-to-local pipeline) | `\paragraph{H1 vs H2...}` | reframe | argument-flow | rephrase | **§15.5.6** (scope statement) | Important methodological scope marker. Preserved as distinct sentence: *"The present analysis implements the H1 closure-level route; a full H2 CMB-to-local pipeline is open."* |
| 13 | **Benchmark numerical illustration** subsubsection + `fig:h0_scan` | `\subsubsection*{...}` + figure | reframe + demote-to-appendix | content + structural | relocate | **§15.5.3** Benchmark A quotes 3% / 69 km/s/Mpc numbers; **Appendix X2** holds full derivation + `fig:h0_scan` | Figure label `fig:h0_scan` preserved in Appendix X2. |
| 14a | "Three layers" itemize (structural / benchmark / deformed family) | `\subsubsection*{Robustness...}` | reframe | argument-flow | rephrase | **§15.5.6** (methodological layers paragraph) | Distills into one sentence listing the three layers. |
| 14b | Robustness check numerics (2.90% vs 2.85% for mild deformation) | same subsubsection | reframe | content | rephrase | **§15.5.3 Benchmark A** (robustness note) or **Appendix X2** | Supports Benchmark A stability; Appendix X2 is natural home. |

---

## External references to `sec:mp_hubble` and tracked labels

**External `\ref{sec:mp_hubble}` occurrences** (found via `grep`): 10 lines.
- Lines 17539, 17673, 17992 (Part I/II context — §§8–12)
- Lines 19787, 20278 (within §14–§15)
- Lines 20525, 20724 (within current §15 area)
- Lines 20911, 20996, 21230 (within §15.6+ — JWST, phenomenology)

**Plan:** All 10 external references stay valid through Phase 1 + Phase 2 (old §15.5 intact). At **Phase 3 switchover**, each is audited: the reference is either
- redirected to `\ref{sec:cosmo_constraints_rebuilt}` (if the referrer is discussing the ε-sector topic broadly), or
- redirected to a specific new subsection `\ref{subsec:eps_*_rebuilt}` (if the referrer cites a specific claim), or
- redirected to Appendix X2 (if the referrer cites a specific benchmark equation or the formal sign-theorem proof).

**Tracked equation/figure labels:**

| Old label | Phase 3 fate | Notes |
|-----------|--------------|-------|
| `sec:mp_hubble` | redirected per referrer | section-level rename |
| `eq:late_cosmo_action` | preserved in Appendix X2 | |
| `eq:ect_late_friedmann` | preserved in Appendix X2 | |
| `eq:ect_h0_shift_exact` | preserved in Appendix X2 | |
| `eq:ect_h0_shift` | preserved in Appendix X2 | leading-order limit |
| `eq:epsilon_eff_def` | **scheduled retire-after-redirect (Phase 3)** | ★ superseded by `eq:mu_def_rebuilt`. All external `\eqref{eq:epsilon_eff_def}` must be redirected to `eq:mu_def_rebuilt` before the label is removed. Until redirect audit complete, label remains live. |
| `eq:epsilon_eff_benchmark` | preserved in Appendix X2 | |
| `fig:h0_scan` | preserved in Appendix X2 | |

**Action at Phase 3:** run audit script to enumerate all `\ref{}`, `\eqref{}`, `\pageref{}` uses of each tracked label in the rest of the preprint and in the companion. Redirect per the table above. No silent drops.

---

## What §15.5.2 in this round contributes

§15.5.2 absorbs only **item #3** (Observational Landscape numerics, partial — Freedman2024 to be added).

All other items listed above are assigned homes in §15.5.3 / §15.5.4 / §15.5.6 / Appendix X2 (methodology). Their actual migration into those future subsections happens in the corresponding integration rounds (§15.5.3 next, §15.5.4 after, etc.).

This inventory is the binding contract: no item above will be dropped in later rounds without explicit entry in `PROJECT_STRUCTURE.md §8` recent-changes log.
