# R103 ECT cosmology verification

These are the active publication-side cosmology checks.

`verify_r103_ect_age_nonidentifiability.py` verifies the scalar-background
inverse-reconstruction identities and a conditional family of inequivalent
backgrounds.  Its terminal conclusion is that the current ECT action/state do
not identify one unique `H(a)`, one ordering event, or one universal cosmic
age from P1--P6.  Named completion estimates are a separate conditional layer.

`verify_r103_conditional_ect_age_matching.py` independently replays the
dimensionless age of the named two-slope action/state, its regular-branch and
finite-start checks, and two alternative supplied `H0` unit calibrations.  Its
output is a conditional completion result, not a unique P1--P6 age prediction.

`compute_r103_two_slope_conditional_observables.py` integrates one explicitly
supplied globally regular action and reports direct $H(z)$, clocks and
distances plus clearly labelled conditional growth and sound-horizon layers.
`scan_r103_two_slope_calibrated_family.py` shoots a nine-point family to common
present conditions and exposes the early-time/Planck-drift/unscreened-PPN
trade-off. `verify_r103_cluster_local_hrc_synthetic.py` reproduces only the
hand-set finite-box amplitude proxy and local-map peak-preservation theorem.
`verify_r103_twoslope_finite_body_correction_v2.py` applies the same named two-slope action
to a two-method scalar-only body proxy and tests whether the cosmological
parameter slice reaches its surface-localisation regime.  The physical
small-body estimate has tiny `Xi_body` and therefore no mass screening; the
formal homogeneous equilibrium roots are not reached.

`compute_r103_restricted_isw_lensing_proxy.py` evaluates only the declared
same-metric, zero-slip, sub-horizon Weyl-amplitude and conformal-derivative
carriers.  `compute_r103_restricted_large_flow_proxy.py` derives the associated
linear $aHfD$ velocity carrier.  Neither output is a physical projected
lensing/ISW spectrum or a survey bulk-flow likelihood.

`compute_r103_two_slope_chronometer_covariance.py` replays the declared
15-point BC03 subset calculation.  Its two repackaged upstream inputs are not
redistributed.  Their identities and preparation instructions are in
`EXTERNAL_INPUTS.json`; the script requires `ECT_EXTERNAL_INPUT_ROOT` and
fails closed if an input is missing, undeclared or hash-mismatched.

`prepare_r103_cccovariance_external_inputs.py` verifies a user-supplied
checkout of the frozen upstream commit and creates the exact hash-gated files
under a separate external-input root.  It does not download or redistribute
the inputs.

Run from the publication root:

```bash
python3 scripts/cosmology/verify_r103_ect_age_nonidentifiability.py \
  --output data/cosmology_r103/R103_ECT_AGE_NONIDENTIFIABILITY_v1.json
python3 scripts/cosmology/verify_r103_conditional_ect_age_matching.py
python3 scripts/cosmology/compute_r103_two_slope_conditional_observables.py
python3 scripts/cosmology/scan_r103_two_slope_calibrated_family.py
python3 scripts/cosmology/compute_r103_restricted_isw_lensing_proxy.py
python3 scripts/cosmology/compute_r103_restricted_large_flow_proxy.py \
  --input data/cosmology_r103/R103_RESTRICTED_ISW_LENSING_PROXY_v1.json \
  --output data/cosmology_r103/R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json
python3 scripts/cosmology/verify_r103_cluster_local_hrc_synthetic.py
python3 scripts/cosmology/verify_r103_twoslope_finite_body_correction_v2.py
ECT_EXTERNAL_INPUT_ROOT=/path/to/external-input-root \
  python3 scripts/cosmology/compute_r103_two_slope_chronometer_covariance.py
python3 scripts/cosmology/make_r103_corrected_cosmology_figures.py \
  --data-dir data/cosmology_r103 --output-dir figures/r103
python3 scripts/figures/make_r103_restored_visuals.py \
  --hwg-csv data/cosmology_r103/R103_TWO_SLOPE_HWG_FROZEN_v1.csv \
  --output-dir figures/r103
python3 scripts/figures/make_r114_closure_figures.py \
  --data-dir data/cosmology_r113 \
  --output-dir figures/r114 \
  --qa-dir .build/figure-qa/r114
```

The first R103 renderer owns the four data-driven conditional cosmology
panels.  The second owns the three status-safe construction diagrams.  The
R114 renderer replays the two bounded closure figures and writes colour,
grayscale and colour-vision-deficiency previews below the requested QA
directory.  These commands are independent generators; none upgrades the
status of the supplied models or their inputs.

Source-hash-gated scripts require regeneration after a manuscript change.  A manuscript change
requires regeneration and a reviewed hash update.

Accepted R103 replay environment: Python 3.13.5,
NumPy 2.3, SciPy 1.17.1 and SymPy 1.14.  Other environments are acceptable
only after reproducing the scientific payload; absence of SciPy or SymPy must
be reported as a dependency error, not as a failed physical gate.
