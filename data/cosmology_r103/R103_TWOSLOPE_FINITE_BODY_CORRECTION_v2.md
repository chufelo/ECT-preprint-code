# R103 two-slope finite-body scalar correction

- **Date:** 2026-07-18
- **Status:** corrected interpretation of an exact model-internal reduction
  and two-method numerical proxy; **NO MASS SCREENING** in the named near-GR
  slice; displayed unscreened `gamma_PPN` gate passes; complete finite-body
  PPN remains Open; proposal-only.
- **Supersedes:** Sections 4--5 and the terminal verdict of
  `R103_TWOSLOPE_FINITE_BODY_AUDIT_v1.md`.
- **Scope:** the same supplied two-slope Jordan scalar action used for the
  conditional R103 background. This is not a microscopic P1--P6 derivation,
  a coupled scalar--metric solution, a full PPN result or an observational
  fit.
- **Frozen live preprint:** `LaTex/ECT_preprint.tex`, SHA-256
  `8a979e4a8be327c22010481f31a38fd7080cc5924dd24ad0fa9bbc8fbdade8e8`.
- **Live manuscript/Git edited:** no.

## 1. Results that remain valid

For

\[
 F=f_*e^{a\sigma},\qquad K=\kappa F,\qquad
 V=V_-e^{a\sigma}+V_+e^{3a\sigma},\qquad
 D=\kappa+\frac32a^2,
\]

the redefinition (y=e^{a\sigma}=F/f_*) gives, in the declared static,
pressureless, fixed-flat scalar proxy,

\[
 \nabla^2y={a^2\over f_*D}
 \left(V_+y^3-V_-y-\frac\rho2\right).
\]

The positive zero-density root

\[
 y_{\rm vac}=\sqrt{V_-/V_+}>0
\]

removes the old one-exponential (F_{\rm vac}\to0) obstruction inside this
supplied completion.

At the artificial benchmark (m_{\rm out}R=1), density contrasts
(10,10^2,10^3,10^4) give far-amplitude/linear-amplitude ratios

\[
 0.888498,\quad0.451047,\quad0.101308,\quad0.0147107.
\]

Collocation and an independent sparse-Newton solve agree within
(2.13\times10^{-4}); the flux/volume identity closes below
(5.4\times10^{-6}). Thus the equation has a mathematical
surface-localisation regime when a body is already large in the interior
Compton scale. This is synthetic/model-internal evidence, not a physical
screening or PPN result.

## 2. Error in the previous interpretation

The earlier audit observed very large homogeneous equilibrium values of
(F_{\rm in}/F_{\rm out}) for crude physical-body densities and treated
those values as if the bodies attained them. That converse is false.
All listed bodies have (m_{\rm in}R\ll1), so there is insufficient radial
extent for relaxation to the homogeneous interior stationary point.
The large equilibrium roots are therefore counterfactual diagnostics, not
realised field values.

For a uniform small body, linearisation about the exterior solution gives

\[
 \Xi_{\rm body}={V_+-V_-\over3V_+-V_-}(s-1)(m_{\rm out}R)^2,
\]

\[
 \delta u(R)={\Xi_{\rm body}\over3(1+m_{\rm out}R)},\qquad
 \delta u(0)=\delta u(R)+{\Xi_{\rm body}\over6}.
\]

| object proxy | (m_{\rm out}R) | counterfactual (m_{\rm in}R) | (\Xi_{\rm body}) | leading (\delta u(0)) |
|---|---:|---:|---:|---:|
| Earth | (2.5423\times10^{-22}) | (2.6202\times10^{-12}) | (2.09\times10^{-14}) | (1.05\times10^{-14}) |
| Sun | (2.7762\times10^{-20}) | (1.8152\times10^{-10}) | (6.36\times10^{-11}) | (3.18\times10^{-11}) |
| Jupiter | (2.7898\times10^{-21}) | (1.7880\times10^{-11}) | (6.05\times10^{-13}) | (3.03\times10^{-13}) |
| Milky-Way spherical mean | (1.8470\times10^{-8}) | (7.1100\times10^{-7}) | (5.74\times10^{-12}) | (2.87\times10^{-12}) |
| cluster (200\rho_{\rm crit}), 1 Mpc | (1.2313\times10^{-6}) | (8.6085\times10^{-6}) | (1.51\times10^{-10}) | (7.57\times10^{-11}) |

Hence (u\simeq1) throughout these proxies. The large equilibrium
(F)-ratios are not reached, and they cannot be used to declare a local or
cosmological failure.

## 3. Correct terminal verdict

The named near-GR slice supplies **NO MASS SCREENING** for these bodies.
It passes the project's commonly used absolute-deviation proxy gate:

\[
 \gamma_{\rm PPN}={\kappa+a^2\over\kappa+2a^2},\qquad
 |\gamma_{\rm PPN}-1|=9.9998\times10^{-6}<2.3\times10^{-5}.
\]

The primary Cassini result is
(\gamma-1)=(2.1\pm2.3)\times10^{-5}. The model value
(\gamma-1)=-0.99998\times10^{-5} lies 1.35 standard deviations from that
central value: it is inside the two-sigma interval but outside the literal
one-sigma interval. Thus `PASS` here means only the declared project
screening proxy, not a Cassini likelihood fit. It is not a complete
local-gravity pass. The coupled finite-body metric, (\beta_{\rm PPN}),
preferred-frame parameters, composition dependence/WEP, time variation,
environmental charge and lensing remain Open.

Conversely, stronger scan points that fail their unscreened PPN gate cannot
borrow this absent mass-screening mechanism as a rescue. They require a
different derived response, derivative screening, a suppressed matter
vertex, or another metric completion.

## 4. Corrected status ledger

| Claim | Result | Status |
|---|---|---|
| two-slope (y=e^{a\sigma}) reduction | exact | Level A inside supplied scalar proxy |
| positive zero-density root | exact | Level A inside supplied action |
| artificial (m_{\rm out}R=1) profiles | two-method PASS | synthetic/model-internal |
| surface localisation when (m_{\rm in}R\gg1) | reproduced | conditional mathematical trend |
| named slice reaches this regime in listed bodies | no; (\Xi_{\rm body}\ll1) and (u\simeq1) | NO MASS SCREENING, not model failure |
| huge equilibrium (F)-contrast is realised | no | counterfactual root only; old inference WITHDRAWN |
| unscreened first-order (\gamma) gate | (|\gamma-1|=9.9998\times10^{-6}) | conditional PASS inside stated limit |
| coupled body metric, (\beta), preferred-frame, WEP, variation, lensing | not computed | Open |
| microscopic P1--P6 ownership | not derived | Open |

## 5. Reproducibility

The corrected owner script is `verify_r103_twoslope_finite_body.py`; it
emits the small-source values into
`results/R103_TWOSLOPE_FINITE_BODY_RESULTS_v1.json`. The filename is retained
for compatibility, while this note records that its interpretation
supersedes the original audit. The CSV contains only the artificial
(m_{\rm out}R=1) profile campaign.

No synthetic result has been promoted to empirical evidence, and no live
publication file was modified.
