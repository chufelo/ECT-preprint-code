# R103 cosmology data registry

This directory contains frozen outputs of the publication-side R103 cosmology verifiers. `MANIFEST_SHA256.json` records every scientific file hash. The two-slope background, age, distance, imported-recombination, restricted growth, Weyl/ISW-carrier and peculiar-flow products are conditional on their declared action/state and limiting assumptions. The cluster product is a synthetic replay of the exact local peak-preservation no-go.

`R103_RESTRICTED_ISW_LENSING_PROXY_v1.json` is not a projected ISW or lensing spectrum. `R103_RESTRICTED_LARGE_FLOW_PROXY_v1.json` is not a survey bulk-flow or Great-Attractor prediction. The two-slope finite-body product establishes no mass screening in the named near-GR slice; the full PPN metric remains Open.

The active chronometer calibration uses the official 15-point Moresco BC03
subset and the suggested covariance prescription from the frozen
`CCcovariance` commit `881413330a7f1e1e5203607d6964db49b4c6c461`.
`R103_OFFICIAL_CCCOVARIANCE_SUBSET_RESULT_v1.json` is a Level-C one-scale
calibration of the named two-slope orbit.  It is not the later full 32-point
likelihood, a BC03/MaStro-combined result, an ECT derivation of `H0`, ECT
discrimination, or a resolution of the Hubble tension.  The age uncertainty
in that file propagates only the fitted `H0` covariance; action/state,
metric/lapse, redshift-map and formation-front uncertainties remain open.

The two repackaged `CCcovariance` inputs are deliberately not redistributed in
this repository.  Their logical paths, upstream owner, frozen upstream commit,
preparation rule and expected SHA-256 identities are declared in
[`EXTERNAL_INPUTS.json`](../../EXTERNAL_INPUTS.json).  After obtaining an
authorised checkout of the upstream commit, prepare the exact files below a
separate input root and run, from the repository root:

```bash
python3 scripts/cosmology/prepare_r103_cccovariance_external_inputs.py \
  --source-root /path/to/CCcovariance-checkout \
  --external-input-root /path/to/external-input-root
ECT_EXTERNAL_INPUT_ROOT=/path/to/external-input-root \
  python3 scripts/cosmology/compute_r103_two_slope_chronometer_covariance.py
```

Without that environment variable, with an undeclared file, or with a hash
mismatch, the calculation fails closed.  The omission concerns redistribution
only; the frozen derived output remains a Level-C conditional calibration, not
an ECT prediction.

## Cross-runtime replay of the calibrated scan

The calibrated scan JSON and CSV can differ in their last floating-point
digits between supported Python/NumPy/SciPy stacks even when the calculation,
checks and interpretation are unchanged.  The tracked
[`R103_RUNTIME_EQUIVALENCE_POLICY_v1.json`](R103_RUNTIME_EQUIVALENCE_POLICY_v1.json)
therefore defines a separate numerical-equivalence gate:

```bash
python3 scripts/verification/verify_runtime_equivalence.py \
  --policy data/cosmology_r103/R103_RUNTIME_EQUIVALENCE_POLICY_v1.json \
  --reference-root /path/to/frozen-reference-clone \
  --candidate-root /path/to/replay-clone
```

The policy compares both calibrated-scan files, requires identical JSON/CSV
structure, booleans, statuses and text, and ignores only the values of
`runtime.python`, `runtime.numpy` and `runtime.scipy` in the JSON.  Numerical
values use `absolute = 1e-10` and `relative = 1e-8`; all other differences
fail.  A PASS means numerical replay equivalence under this declared policy.
It is not byte identity, a fitted uncertainty, a scientific error bar, a
unique ECT prediction or evidence for selecting the still-Open physical
completion.
