# §15.5 Opening — Introductory part of the cosmological ε-section

**Status:** v1 draft for user + GPT review | **Target:** Phase 2 Step 1 (previously missing) | **Date:** 2026-04-18

**Purpose.** The current rebuilt §15.5 block jumps straight from the subsection-level header into §15.5.1 without any introductory framing for the chapter as a whole. This drops the most important piece of the narrative: *why* ECT proposes a single parameter ε, *why* the multi-probe test is a strong test of the framework, and *what* the reader should expect from the six subsections that follow.

This opening fills that gap. It is inserted between `\label{sec:cosmo_constraints_rebuilt}` and the start of §15.5.1.

**Design principles:**
- **Set the paradigm early.** In standard phenomenological cosmology each tension has its own parameter (EDE fractions, MOND accelerations, f(R) parameters). ECT proposes ONE parameter ε for a family of independent phenomena. That is the substantive claim of this whole section.
- **State the structural expectation explicitly.** If five independent observational channels — each with its own physics, kernel, and systematics — converge on a common narrow ε-range, this is not a fit; it is an indirect consistency check that a single mechanism underlies them.
- **Be honest about the diagnostic-vs-first-principles distinction** from the very first paragraph, so no reader can misread the subsection as a first-principles claim.
- **Flag the constancy-vs-ε(z) question** early — the retained 1σ-band of width ≈ 0.007 is compatible with a true constant ε, but also with a slow-varying ε(z) averaged over the kernel of each probe. This is one of the open questions.
- **Roadmap**: short, concrete, pointing to each of §15.5.1–§15.5.6 with one sentence each.

---

## Final draft text (~500 words)

### Introductory part of §15.5 (before §15.5.1)

**[Opening paragraph — the paradigm.]** The previous part of Chapter 15 examined the separate cosmological sectors — flatness, horizon and monopole problems, age and lookback integrals, structure-formation phenomenology — within the ordered-branch $\phi$-closure of ECT. The present section addresses a different kind of question. In the standard phenomenological treatment of late-time cosmological anomalies, each tension typically receives its own parameterisation: a pre-recombination component for the Hubble discrepancy, a modified gravity law for the late-time growth sector, an abundance enhancement factor for the high-$z$ galaxy counts. ECT offers a structurally different path. A single effective deformation parameter, $\varepsilon$, arising from the three-stage condensate closure, controls simultaneously the late-time gravitational response function $G_{\rm eff}(z)$ seen by every cosmological channel. The section therefore asks whether a single value of $\varepsilon$ — or more precisely, a single narrow range — is compatible with a set of observationally distinct channels probing that response.

**[Second paragraph — why this matters.]** If five channels of qualitatively different physics (a CMB-era distance-ratio proxy, a high-$z$ structure-formation anomaly, direct late-time Hubble-rate measurements, late-time growth likelihoods, and late-time potential-evolution signals) independently admit the same narrow $\varepsilon$-interval, then that interval is not a fit of a parameter to one phenomenon: it is the intersection of five largely independent empirical constraints on one common quantity. A non-trivial intersection is a genuine indirect consistency check of the framework. If the five channels had disagreed — for example, if any one of them had required a negative $\varepsilon$ that the others excluded — then the single-parameter description would have failed in a clean, falsifiable way. Conversely, a narrow joint band with five channels of different kernels and systematics is the strongest non-derivational evidence available at this methodological level that a single underlying mechanism is at work.

**[Third paragraph — diagnostic framing.]** Throughout \S15.5 $\varepsilon$ is treated as an effective diagnostic parameter rather than as a first-principles constant of ECT. The retained-five-probe joint band reported in \S15.5.3 is an empirical result under the stated methodology, not a measurement of a fundamental theoretical quantity and not a global statistical combination of independent likelihoods. A first-principles closure-level derivation of the full epoch-dependent function $\varepsilon(z)$ predicted by three-stage condensate closure, together with its mapping to the effective uniform-$\varepsilon$ layer used here, remains open. In this diagnostic layer the retained band is compatible with $\varepsilon$ being a true constant; it is equally compatible with a slow-varying $\varepsilon(z)$ averaged over the kernel of each probe. Distinguishing these two possibilities belongs to the closure-level extension.

**[Fourth paragraph — roadmap.]** The section is organised as follows. \S15.5.1 fixes the structural meaning of $\varepsilon$ within ECT and states the effective uniform-$\varepsilon$ ansatz. \S15.5.2 specifies the retained five probes, what each of them actually constrains, and introduces the two-sided vs one-sided-upper-bound distinction. \S15.5.3 reports the joint effective allowed band and fixes the working benchmark. \S15.5.4 discusses the channels not retained, in three structurally distinct categories, together with the reasons for their exclusion. \S15.5.5 places the result in the context of alternative proposals for the same observational pattern. \S15.5.6 states what the analysis establishes and what it does not, lists the first-principles open problem OP-Hubble-derive, and outlines the direction of future work. The quantitative pipelines supporting the probe-by-probe constraints are collected in Appendices A1–A5, and the methodological and benchmark-achievability apparatus in Appendix A6.

---

## What this opening accomplishes

1. **Establishes the paradigm shift** — from "per-phenomenon compensation parameters" to "one parameter, tested across channels". This was missing before.
2. **Explains why the multi-probe test is a strong test** of the framework (intersection of five independent constraints = indirect consistency check).
3. **Flags the constancy vs ε(z) question** early, as required by user directive (pt 6).
4. **States the honesty framing** before any subsection numerics appear, so all quantitative content is read in the correct mode.
5. **Gives a roadmap** pointing the reader at all six subsections + the six appendices that will follow.

## What this opening deliberately does NOT contain

- Numerics (no 0.029, 0.036, 0.032 — that belongs to §15.5.3 where the joint band is actually defined)
- Any legacy number (no 3%, 2.85%, 69 km/s/Mpc, ε = 0.010 per binding user directive)
- Citations (this is structural framing, not a literature review)
- Figures (opening is text-only; figures belong to the subsections and appendices)

## Integration point

Insert **between** the existing lines:
```
\label{sec:cosmo_constraints_rebuilt}
```
and the start of §15.5.1:
```
\subsubsection*{\normalfont\textbf{15.5.1 \quad Structural definition ...}}
```

## Questions to user / GPT

1. **Fourth paragraph roadmap** mentions "Appendices A1–A5 and A6" — this pre-announces the appendix structure that will be created in Phase 2 Steps 3–8. OK to pre-announce, or remove the appendix sentence until those appendices actually exist?
2. **"A non-trivial intersection is a genuine indirect consistency check"** — the phrase carries the user's pt 7 emphasis. Strong enough, or needs reinforcement?
3. **Length** — ~500 words / ~2 PDF pages. Appropriate, or too long/too short for an opening?
4. **Tone** — set slightly above subsection-level in register (philosophical framing before technical material). OK, or shift?
5. **OP-Hubble-derive mention in paragraph 3** — already prefigures §15.5.6's OP-Hubble-derive entry. Keep here, or defer?
