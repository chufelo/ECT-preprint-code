# §15.5.2 — Retained five-probe effective analysis

**Status:** v1 for review (user + GPT) | **Target:** Step 2.1 subsection 2 of 6 | **Date:** 2026-04-18

**Design log:**
- All four GPT-obligatory corrections applied upstream (two-sided vs upper-bound distinction; hardened table rows; non-independence paragraph; single-sentence retention criterion).
- Numerics taken directly from `scripts/epsilon_convergence/result_ch{1,2,3,4,8}.json` and `scripts/epsilon_convergence/README.md`. Not re-asked from user.
- Figure `fig_epsilon_constraints` **NOT cited here**: reference deferred to §15.5.3 per GPT rule (cite only if regenerated under the final retained five-probe set).
- No-loss inventory of old §15.5 — see `02_s15_5_2_INVENTORY.md` (parallel file).

---

## Final draft text (~640 words)

### §15.5.2  Retained five-probe effective analysis

**[Opening bridge.]** With the effective meaning of $\varepsilon$ fixed in §15.5.1, we now specify which cosmological probes are retained for the present uniform-$\varepsilon$ analysis, what each of them actually constrains, and how their resulting effective intervals are to be interpreted.

**Retention criterion.** A probe is retained in §15.5 only if it constrains the present effective $\varepsilon$-sector rather than a distinct physical sector, and if its extraction pipeline is sufficiently explicit that an effective interval can be stated without importing an uncontrolled external likelihood. Five probes satisfy this criterion under the uniform-$\varepsilon$ ansatz and the $\Lambda$CDM-background proxy $(\Omega_m = 0.315, \Omega_\Lambda = 0.685)$; all other probes considered in the present analysis are discussed in §15.5.4.

**[Table retained_probes — see LaTeX snippet.]**

**Two-sided vs upper-bound distinction.** Within the retained five-probe set, Hubble+$r_s$ and the JWST early-galaxy excess provide two-sided effective extraction intervals, whereas cosmic chronometers, $f\sigma_8$ from RSD, and the ISW amplitude are retained as late-time consistency channels whose raw likelihoods are compatible with $\varepsilon = 0$ and are therefore reported here as one-sided upper bounds under the physical prior $\varepsilon \geq 0$ introduced in §15.5.1.

**Probe 1 — Hubble + $r_s$ (two-sided effective extraction).**
The SH0ES distance-ladder determination $H_0 = 73.04 \pm 1.04~\mathrm{km\,s^{-1}\,Mpc^{-1}}$ and the Planck 2018 base-$\Lambda$CDM value $H_0 = 67.4 \pm 0.5~\mathrm{km\,s^{-1}\,Mpc^{-1}}$ define an observed tension of $\sim 5\sigma$. Recent CCHP/JWST determinations fall near $H_0 \sim 70~\mathrm{km\,s^{-1}\,Mpc^{-1}}$ [Freedman2024], intermediate between the two. The effective distance-ratio requirement imposed by the uniform-$\varepsilon$ ansatz on the CMB-scale-to-local-distance integral, evaluated on the $\Lambda$CDM-background proxy with a simplified $r_s$ treatment, yields a two-sided extraction centred at $\varepsilon = 0.032$ with $1\sigma$ interval $[0.027,\,0.038]$ and $2\sigma$ interval $[0.021,\,0.043]$.

**Probe 2 — JWST early-galaxy excess (two-sided effective extraction, binding below).**
Reported high-$z$ stellar-mass abundances at $z \approx 8$–$12$ show an enhancement factor $R \approx 10\times$ (range $3$–$100\times$, $\nu \approx 5$) over $\Lambda$CDM expectations. A Press–Schechter proxy that ties $G_{\rm eff}(z)$ to the halo mass function via the growth factor, on the same $\Lambda$CDM-background proxy and without full growth-ODE integration or halo-to-stellar-mass mapping, yields a two-sided extraction centred at $\varepsilon = 0.042$ with $1\sigma$ interval $[0.029,\,0.071]$ and $2\sigma$ interval $[0.013,\,0.179]$. The lower edge $\varepsilon = 0.029$ is the binding lower bound of the joint effective band quoted in §15.5.3.

**Probe 3 — Cosmic chronometers (one-sided consistency bound under $\varepsilon \geq 0$).**
The Moresco-compilation $H(z)$ points at $z = 0.07$–$1.97$ are fit against the effective expansion $H^{\rm ECT}(z) = H_0 \sqrt{\Omega_m (1+z)^{3+2\varepsilon} + \Omega_\Lambda (1+z)^{2\varepsilon}}$ with $\Omega_m = 0.315$ fixed and $(\varepsilon, H_0)$ varied. The raw best-fit $\varepsilon = 0.006$ is compatible with $\varepsilon = 0$; under the physical prior the probe enters as a one-sided upper bound with $1\sigma$ upper at $\varepsilon = 0.087$ and $2\sigma$ upper at $\varepsilon = 0.150$. The constraint is weak; its role is late-time consistency, not extraction.

**Probe 4 — $f\sigma_8$ from RSD (one-sided consistency bound; binding above).**
Fourteen RSD measurements at $z = 0.07$–$1.94$ are fit by integrating the linear-growth ODE for the density contrast $\delta(a)$ with a modified Poisson source driven by $G_{\rm eff}(a)$, profiling $\sigma_8(0)$ freely. A strong $\sigma_8$–$\varepsilon$ degeneracy leaves the raw central at $\varepsilon \approx -0.06$ without a physical lower bound; under the physical prior this channel is reported as a one-sided upper bound with $1\sigma$ upper at $\varepsilon = 0.036$ and $2\sigma$ upper at $\varepsilon = 0.120$. The $1\sigma$ upper is the binding upper bound of the joint effective band quoted in §15.5.3.

**Probe 5 — ISW amplitude (one-sided consistency bound under $\varepsilon \geq 0$).**
A linearized proxy $A_{\rm ISW} \approx 1 + \kappa_A\,\varepsilon$ is compared to Planck+CMB-cross-correlation data on the ISW window $z \lesssim 2$ under $\Lambda$CDM-background Limber weights. The raw central $\varepsilon \approx -0.007$ is compatible with $\varepsilon = 0$ within a large $\sigma$; under the physical prior the probe enters as a one-sided upper bound with $1\sigma$ upper at $\varepsilon = 0.043$ and $2\sigma$ upper at $\varepsilon = 0.093$. Role: consistency, not extraction.

**Effective consistency window, not a global joint likelihood.** The retained five-probe set should not be read as a full statistically independent joint likelihood. It is an effective multi-probe comparison performed within a common diagnostic uniform-$\varepsilon$ layer, with partially shared background and growth ingredients across some channels. The resulting band in §15.5.3 is therefore an effective consistency window under the present methodology, not a first-principles ECT prediction and not a final global MCMC determination.

**Bridge.** The combined $1\sigma$ / $2\sigma$ intervals of these five effective channels, and the resulting joint-band definition of the working effective benchmark, are taken up in §15.5.3.
