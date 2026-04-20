# UDG stress-test scripts

Diagnostic scripts for the dark-matter-deficient ultra-diffuse galaxy
(UDG) stress test of the current ECT Level-B galactic closure.

These scripts accompany Appendix `app:udg_stress_test` of the ECT
preprint (`ECT_preprint.tex`).  All numerical content of that appendix
can be reproduced by running the three scripts in this directory.

## Scope

DIAGNOSTIC ONLY.  The scripts compute the inverse-problem quantity

    Xi_req(R) = r (r - 1) g_N(R) / g_dagger_0 ,

with `r = M_dyn / M_bar = sigma_obs^2 / sigma_N^2`, evaluated at the
Wolf half-mass radius, under the current practical galactic closure
(Eq. `eq:ect_rotation_closure_main` of the preprint).  A result
`Xi_req << 1` for a given object means that the current closure is
strained on that object, not that ECT explains it.  **No rescue
mechanism is derived here.**

## Files

- `01_xi_req_stress_test.py` --- six-object stress-test table
  (DF4, FCC 224, DF2, NGC 5846-UDG1, Dragonfly 44; AGC 114905 noted
  as disc-rotator out of scope).

- `02_jeans_check.py` --- isotropic Plummer Jeans forward model for
  DF4 vs the Wolf-proxy.  Shows the two methods agree to a factor
  1.30 at Xi = 0; the `Xi_req << 1` classification is robust under
  the Jeans upgrade.

- `03_nuisance_and_sanity.py` --- distance covariance, M/L
  sensitivity, small-N Monte-Carlo for the 7-GC DF4 dispersion, the
  MOND-EFE benchmark for all four spherical UDGs, and the UFD and GC
  side diagnostics.

## Dependencies

Python 3, `numpy`, `scipy`.

## Running

    python3 01_xi_req_stress_test.py
    python3 02_jeans_check.py
    python3 03_nuisance_and_sanity.py

## Linked preprint

Appendix `app:udg_stress_test` and the ND-13 entry of Table
`tab:future_discriminants` in the ECT preprint (see top-level
`ECT_preprint.tex`).  The integration proposal and the internal
consolidated derivation notes (`ECT_UDG_integration_proposal.pdf`,
`ECT_UDG_derivation.pdf`) document the methodology but are not
semi-official supplements to the preprint.
