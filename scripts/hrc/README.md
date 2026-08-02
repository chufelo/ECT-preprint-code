# HRC publication calculations

Status: **current Level-C conditional publication calculation family**. The
scripts reproduce the HRC-0/HRC-3 algebraic diagnostics used by the English
publication package. This status does not promote them to an ECT derivation or
an ECT-specific prediction.

## Scientific scope

The current calculation registry contains only HRC-0 and HRC-3. It does not
implement the superseded galactic response law and does not provide a fallback
to it. HRC-0 is exact inside the stated ERP-Φ/inverse-DtN response model. HRC-3
is exact inside the supplied equal-three-channel rank-one model and is a
conditional proof of class. The identity internal-to-gravity bridge and
`a_M0 = c H0/(2π)` are declared matching inputs, not consequences of P1–P6.

The SPARC calculations are Level-C algebraic diagnostics. They use signed gas,
a 2 km/s uncertainty floor, bounded `a_M/a_M0` and disk mass-to-light nuisance
fits, and whole-galaxy held-out folds. They are not a finite-thickness disk PDE,
a covariance-complete or hierarchical likelihood, a modern Milky-Way posterior,
or a metric/lensing calculation.

## Entry points

- `make_r97_hrc_only_figures.py`: response functions, frozen held-out SPARC
  summaries, regime diagnostics, and the first three HRC figures.
- `make_r97_hrc_completion_figures.py`: 165-galaxy HRC-only scale and nuisance
  fits, BTFR/RAR diagnostics, representative curves, Milky-Way sensitivity,
  UDG stress tests, the five-seed common-`M/L` training-to-held-out transfer
  calculation, and the remaining six HRC figures. Every per-galaxy
  two-parameter fit receives an independent global optimisation audit; the
  common-`M/L` fold registry records all 50 HRC-only fits explicitly.
- `compute_r97_hrc_udg.py`: deterministic UDG interval inversion and residual
  checks.
- `verify_hrc_release.py`: independent release gate for repository-relative
  manifest paths and hashes, exact figure ownership, HRC-only source schemas,
  analytic HRC-0 inversion, an independent monotone HRC-3 inversion,
  signed-gas handling, frozen fit sentinels, common-`M/L` fold counts and
  manuscript-table values, and UDG inverse residuals.

## Frozen inputs and outputs

Author-generated CSV/JSON products live under `data/hrc_r97/`. Three SPARC-
origin inputs are deliberately not redistributed: the upstream mass-model
table and the two frozen R89-to-R97 projection tables. Their logical paths,
SHA-256 identities, citations, acquisition notes and redistribution status are
declared in [`EXTERNAL_INPUTS.json`](../../EXTERNAL_INPUTS.json). The projection
tables are source-model outputs, not independent observations and not evidence
that HRC follows from P1--P6.

Obtain the declared files under their upstream terms, reproduce the relative
layout below a separate directory, and set the external root for the run:

```bash
export ECT_EXTERNAL_INPUT_ROOT=/path/to/authorised-input-root
```

For example, the mass-model table must then be found at
`$ECT_EXTERNAL_INPUT_ROOT/data/MassModels_Lelli2016c.mrt`. Every entry point
fails closed when the environment variable, a declared file, or its exact hash
is missing. No script falls back to an in-repository copy.

For a byte-identical replay, create and activate the frozen HRC environment
from the repository root:

```bash
conda env create -f environment-hrc-r97.yml
conda activate ect-hrc-r97-frozen
```

It pins Python 3.12.6, NumPy 2.1.2, SciPy 1.14.1 and Matplotlib 3.9.3, the
recorded owners of the committed R97 numerical bytes. A run in the general
`environment-r190.yml` can provide an independent numerical-equivalence check,
but newer libraries may change last-bit values; such a run is not the exact
artifact gate and must not replace the frozen CSV/JSON or figures. Re-running
a script must not modify any manuscript source. Generated figures go only to
`figures/hrc/`.

The deterministic run order is:

1. `python3 scripts/hrc/compute_r97_hrc_udg.py`
2. `python3 scripts/hrc/make_r97_hrc_only_figures.py`
3. `python3 scripts/hrc/make_r97_hrc_completion_figures.py`
4. `python3 scripts/hrc/verify_hrc_release.py`

The final command is a static integrity gate and writes
`data/hrc_r97/R97_HRC_RELEASE_VERIFICATION.json`; a release is acceptable
only when its top-level `pass` field is `true` and a clean-copy rerun of the
three generators reproduces the frozen CSV/JSON products and owned figure
sets under the recorded Python/NumPy/SciPy/Matplotlib environment.

## Status and provenance rule

Superseded galactic scripts and products are preserved in a dated provenance
archive and Git history. They are not part of the current theory exposition,
the current calculation registry, or any active numerical conclusion. Any
historical comparison must be performed as an external model-comparison study,
not by restoring the old response as an ECT branch.
