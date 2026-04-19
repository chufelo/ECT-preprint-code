# PHASE 3 REDIRECT MAP — §15.5 rebuild finalisation
**Created:** 2026-04-19 | **Status:** authoritative for Phase 3A+3B execution

---

## Phase 3A — main-text switchover

### A.1 Labels to rename (drop `_rebuilt` suffix)

| Old label | New label | Definition line | # external refs |
|-----------|-----------|:---------------:|:---------------:|
| `sec:cosmo_constraints_rebuilt` | `sec:cosmo_constraints` | 20382 | 1 |
| `subsec:eps_def_rebuilt` | `subsec:eps_def` | 20499 | 20 |
| `subsec:eps_retained_rebuilt` | `subsec:eps_retained` | 20596 | 17 |
| `subsec:eps_joint_band_rebuilt` | `subsec:eps_joint_band` | 20828 | 11 |
| `subsec:eps_excluded_rebuilt` | `subsec:eps_excluded` | 20989 | 7 |
| `subsec:eps_comparison_rebuilt` | `subsec:eps_comparison` | 21140 | 2 |
| `subsec:eps_outlook_rebuilt` | `subsec:eps_outlook` | 21253 | 7 |
| `tab:eps_retained_probes_rebuilt` | `tab:eps_retained_probes` | 20658 | 2 |
| `eq:mu_def_rebuilt` | `eq:mu_def` | 20516 | 0 |
| `eq:uniform_eps_ansatz_rebuilt` | `eq:uniform_eps_ansatz` | 20533 | 0 |
| `eq:eps_nonneg_rebuilt` | `eq:eps_nonneg` | 20549 | 0 |
| `eq:eps_joint_band_rebuilt` | `eq:eps_joint_band` | 20849 | 2 |

**Note**: per-probe equations `eq:eps_{hubble,jwst,cc,fsigma8,isw}_retained` do NOT have `_rebuilt` suffix → keep as-is.

### A.2 Old blocks to delete

| Block | Lines | Label |
|-------|:-----:|-------|
| Old §15.5 main text | 21406–21832 | `sec:mp_hubble` |
| Old §15.6 main text | 21834–22218 | `sec:mp_jwst_cosmo` |

(exact line numbers will be re-measured at execution)

### A.3 Redirect map for `sec:mp_hubble` (27 refs)

| Location | Current ref | New ref | Notes |
|:--------:|-------------|---------|-------|
| 17544 | `\S\ref{sec:mp_hubble}` | `\S\ref{subsec:eps_joint_band}` | `tab:nlee_footprint` row — Hubble sector |
| 17678 | `\S\ref{sec:mp_hubble}` | `\S\ref{sec:cosmo_constraints}` | perturbative orientation context |
| 17997 | `\S\ref{sec:mp_hubble}` | `\S\ref{sec:cosmo_constraints}` | LLR/Cassini context |
| 19792 | `(\S\ref{sec:mp_hubble})` | `(\S\ref{subsec:eps_joint_band})` | Hubble-tension alleviation pointer |
| 20283 | `(\S\ref{sec:mp_hubble}) gives` | `(\S\ref{subsec:eps_joint_band}) gives` | universe-age context |
| 20836 | `\S\ref{sec:mp_hubble}` | `\S\ref{subsec:eps_joint_band}` | inside new §15.5.3 bridge |
| 21465 | `\S\ref{sec:mp_hubble}, H2 discussion` | `\S\ref{subsec:eps_outlook}` | DELETED-block-internal → wait |
| 21664 | `\S\ref{sec:mp_hubble}` | DELETED | inside sec:mp_hubble block — will be removed with block |
| 21851 | `\S\ref{sec:mp_hubble}` | DELETED | inside sec:mp_jwst_cosmo block — will be removed |
| 21936 | `\S\ref{sec:mp_hubble}` | DELETED | inside sec:mp_jwst_cosmo block — will be removed |
| 22170 | `(\S\ref{sec:mp_hubble})` | DELETED | inside sec:mp_jwst_cosmo block — will be removed |
| 22191 | `\S\ref{sec:mp_hubble}:` | DELETED | inside sec:mp_jwst_cosmo block — will be removed |
| 22386 | `& \S\ref{sec:mp_hubble}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22392 | `& \S\ref{sec:mp_hubble}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22398 | `& \S\ref{sec:mp_hubble}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22416 | `& \S\ref{sec:mp_hubble}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22638 | `sectors~(\S\ref{sec:mp_hubble})` | `sectors~(\S\ref{subsec:eps_joint_band})` | Part II conclusions |
| 23026 | `\S\S\ref{sec:mp_hubble}--\ref{sec:mp_jwst_cosmo}` | `\S\ref{sec:cosmo_constraints}` | Galactic context |
| 23048 | `(\S\ref{sec:mp_hubble})` | `(\S\ref{subsec:eps_joint_band})` | galactic cosmology |
| 25169 | `\S\ref{sec:mp_hubble}, eq.~\eqref{eq:gdag_bg_z_hubble}` | `\S\ref{sec:cosmo_constraints}, eq.~\eqref{eq:gdag_bg_z_hubble}` | mass-discrepancy context — keep eq ref |
| 25560 | `Sections~\ref{sec:mp_hubble}--\ref{sec:mp_dark}` | `Sections~\ref{sec:cosmo_constraints}--\ref{sec:mp_dark}` | Observational tests intro |
| 25575 | `\S\ref{sec:mp_hubble}` | `\S\ref{sec:cosmo_constraints}` | ordered-branch closure list |
| 25687 | `sense of~\S\ref{sec:mp_hubble}` | `sense of~\S\ref{subsec:eps_joint_band}` | benchmark framing |
| 26563 | row + `\S\ref{sec:mp_hubble}` | row rewritten (see Phase 3B) + `\S\ref{subsec:eps_joint_band}` | legacy 3%/2.8%/2% row |
| 26735 | `\ref{sec:mp_hubble}` | `\ref{subsec:eps_joint_band}` | D32 row |
| 48756 | `\S\ref{sec:mp_hubble}` | `\S\ref{sec:cosmo_constraints}` | inside app:nlee_jwst_growth |
| 50495 | `Section~\ref{sec:mp_hubble}` | `Section~\ref{sec:cosmo_constraints}` | inside app:isw_diagnostic |

### A.4 Redirect map for `sec:mp_jwst_cosmo` (15 refs)

| Location | Current ref | New ref | Notes |
|:--------:|-------------|---------|-------|
| 17556 | `\S\ref{sec:mp_jwst_cosmo}` | `\S\ref{subsec:eps_joint_band}` | tab:nlee_footprint |
| 19793 | `(\S\ref{sec:mp_jwst_cosmo})` | `(\S\ref{subsec:eps_joint_band})` | JWST enhancement pointer |
| 20322 | `\S\ref{sec:mp_jwst_cosmo}` | `\S\ref{subsec:eps_joint_band}` | age/JWST context in new §15.5 |
| 21490 | `(\S\ref{sec:mp_jwst_cosmo})` | DELETED | inside sec:mp_hubble block |
| 21626 | `(\S\ref{sec:isw_diagnostic}, \S\ref{sec:mp_jwst_cosmo})` | DELETED | inside sec:mp_hubble block |
| 21785 | `(\S\ref{sec:mp_jwst_cosmo}).` | DELETED | inside sec:mp_hubble block |
| 22428 | `& \S\ref{sec:mp_jwst_cosmo}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22434 | `& \S\ref{sec:mp_jwst_cosmo}` | `& \S\ref{subsec:eps_joint_band}` | Part II falsification table |
| 22642 | `(\S\ref{sec:mp_jwst_cosmo})` | `(\S\ref{subsec:eps_joint_band})` | Part II conclusions |
| 23026 | part of `\S\S\ref{sec:mp_hubble}--\ref{sec:mp_jwst_cosmo}` | already covered in A.3 | — |
| 23056 | `(\S\ref{sec:mp_jwst_cosmo})` | `(\S\ref{subsec:eps_joint_band})` | galactic cosmology |
| 23060 | `\S\ref{sec:jwst}, \S\ref{sec:mp_jwst_cosmo}` | `\S\ref{sec:jwst}, \S\ref{subsec:eps_joint_band}` | JWST tension discussion |
| 25576 | `\S\ref{sec:mp_jwst_cosmo}` | `\S\ref{sec:cosmo_constraints}` | cosmo JWST framework |
| 26564 | row + `\S\ref{sec:mp_jwst_cosmo}` | row rewritten (Phase 3B) + `\S\ref{subsec:eps_joint_band}` | legacy row |
| 26736 | `\ref{sec:mp_jwst_cosmo}` | `\ref{subsec:eps_joint_band}` | D33 row |

### A.5 Preserve (do NOT delete)

- `app:late_cosmo_background` (infrastructure, 19 refs including from new A1–A6)
- `app:late_cosmo_algorithm` (infrastructure, 7 refs including from new A1–A6)
- `app:isw_diagnostic` (legacy appendix — Phase 3C only, content audit required)
- `app:nlee_jwst_growth` (legacy appendix — Phase 3C only, content audit required)

---

## Phase 3B — summary/table cleanup

### B.1 Line 26563 (Level-4 checklist row, "Late-time background closure")

**Current text**:
> "late-time benchmark response encoded by $\mu(a)$... present-epoch closed-form gives benchmark H1 shift $\approx 3\%$ (numerical solver: $\approx 2.8\%$), derived-parent closure gives $\approx 2\%$; full early+late $H_0$ closure (H2) remains open"

**New text** (retained-band headline, legacy relegated):
> "late-time diagnostic-layer response under uniform-$\varepsilon$ ansatz yields retained five-probe band $\varepsilon \in [0.0296,\,0.0376]$ at $1\sigma$ ([0.0207, 0.0425] at $2\sigma$) from closed-form benchmark extraction; full early+late $H_0$ closure (H2) and closure-level $\varepsilon(z)$ derivation (OP-Hubble-derive) remain open"

**Cross-refs**: `\S\ref{sec:mp_flrw}, \S\ref{sec:universe_age}, \S\ref{sec:mp_hubble}` → `\S\ref{sec:mp_flrw}, \S\ref{sec:universe_age}, \S\ref{subsec:eps_joint_band}`

### B.2 Line 26564 (Level-4 checklist row, "JWST correlated background")

**Current text**:
> "Correlated age/distance/growth logic established; derived-parent corridor and maturity budgets give partial alleviation only, not a full morphology-level solution"

**New text**:
> "Correlated age/distance/growth logic established; retained-band analysis (\S\ref{subsec:eps_joint_band}) gives JWST extraction $\varepsilon\approx 0.0296$ lower edge, compatible with retained band; full morphology-level solution remains open"

**Cross-refs**: `\S\ref{sec:mp_jwst_cosmo}, \S\ref{sec:mp_tests}` → `\S\ref{subsec:eps_joint_band}, \S\ref{sec:mp_tests}`

### B.3 Line 26735 (D32 row)

**Current**: "Correlated with age, distance, JWST through same $\phi_b(z)$; benchmark few-per-cent H1 shift (exact value pending re-audit)"

**New**: "Correlated with age, distance, JWST through same $\phi_b(z)$; retained-band headline extraction $\varepsilon \in [0.0296,\,0.0376]$ at $1\sigma$"

**Ref**: `\ref{sec:mp_hubble}` → `\ref{subsec:eps_joint_band}`

### B.4 Line 26736 (D33 row)

**Current**: "Mixed effect: distance/time/growth all shift; BH-assisted channel more promising; partial alleviation only"

**New**: "Mixed effect: distance/time/growth all shift; JWST channel contributes retained-band lower edge $\varepsilon\approx 0.0296$; partial alleviation only"

**Ref**: `\ref{sec:mp_jwst_cosmo}` → `\ref{subsec:eps_joint_band}`

### B.5 Part II falsification table rows (~line 22361–22440)

Rows like "Upward Hubble-shift mechanism", "w₀–H₀ correlation", "BBN-localised drift", "Benchmark Hubble shift", "JWST: galaxy-assembly channel", "JWST: BH-assisted channel" — **keep content**, just redirect `\S\ref{sec:mp_hubble}` → `\S\ref{subsec:eps_joint_band}` and `\S\ref{sec:mp_jwst_cosmo}` → `\S\ref{subsec:eps_joint_band}`. These are structural-mechanism rows, valid independently of the ε extraction.

### B.6 Opening-title cleanup

**Current** (line 20376):
```
\subsection*{\normalfont\textbf{Cosmological constraints on the effective drift parameter}%
  \\[0.3ex]\normalfont\small\itshape (rebuilt version --- under construction)}
```

**New**:
```
\subsection{Cosmological constraints on the effective drift parameter}
```

Also remove guard comment block and annotation.

---

## Phase 3C — DEFERRED (separate mini-pass later)

`app:isw_diagnostic` (2 refs) and `app:nlee_jwst_growth` (2 refs) content audit to check for unique content not in A2/A5. If none unique — retire. If unique — retain as legacy methodological notes.

---

## Post-switchover global audit (grep tokens)

After Phase 3A+3B executes, run repo-wide grep for:
- `sec:mp_hubble` (should be 0)
- `sec:mp_jwst_cosmo` (should be 0)
- `0.010` (only in legacy comments or specific contexts)
- `2.85`, `2.90`, `69 km`, `few-per-cent` (survey hits)
- `_rebuilt` in labels (should be 0)
- `under construction`, `rebuild`, `parallel creation` (cleanup)
