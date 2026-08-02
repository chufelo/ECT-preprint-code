# R113 cosmology calculation owners

These files are the deterministic publication owners for three calculations
used by the R109/R113 cosmology addendum.  Their repository commit fixes the
exact public identities; none of the bundles changes the declared scientific
status merely by being tracked.

## Owner-specific early-response envelope

- Script: `scripts/cosmology/compute_r113_early_response_growth_collapse_envelope.py`
- Outputs: `R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v3.{json,csv}`
- Manuscript coordinate: `zeta_ER`.
- Status: Level A inside the explicitly supplied response envelope for background/equality/growth algebra; Level C top-hat and Press--Schechter sensitivity. This is neither the withdrawn universal ECT epsilon nor the named two-slope orbit.

The script independently uses DOP853 and Radau for the linear-growth ratio and reproduces every displayed eight-decimal R109 table entry. The maximum cross-solver growth difference is `8.33e-13`; the maximum difference from the rounded manuscript table is `4.95e-9`.  Version 3 freezes scientific outputs to 13 significant digits and excludes runtime-version strings and sub-publication last-bit residuals from the scientific JSON hash.  Those quantities remain execution provenance and are printed during replay.

The earlier output files `R113_EPSILONG_GROWTH_COLLAPSE_ENVELOPE_v1.*` are
preserved as superseded R113 data provenance.  They encode the same numerical
payload but use a symbol token that collides with unrelated BBN and PES
tolerances.  Their predecessor generator is intentionally absent from the
active public script surface; the current v3 generator above is the only
advertised publication owner.

`R113_EARLY_RESPONSE_GROWTH_COLLAPSE_ENVELOPE_v2.*` is also preserved.  Its
scientific rows agree with v3, but its JSON included runtime strings and a
last-bit solver diagnostic in the frozen payload; it is therefore superseded
for immutable publication provenance.

## One-real-pole merger-scale no-go

- Script: `scripts/cosmology/verify_r113_one_pole_cluster_no_go.py`
- Output: `R113_ONE_POLE_CLUSTER_NO_GO_v2.json`
- Status: conditional arithmetic no-go only for `tau_pole=2 pi/H0` plus ballistic `ell=v tau`.

This calculation does not equate a KMS period to a retarded pole and does not exclude multipole, dispersive, anisotropic or separately owned merger kernels.

Version 2 separates runtime provenance from the deterministic scientific
payload.  The v1 file is retained and has the same scientific values.

## Director source-normalisation guard

- Script: `scripts/verification/r113/verify_r113_director_source_normalisation.py`
- Output: `R113_DIRECTOR_SOURCE_NORMALISATION_v2.json`
- Status: exact Level-A rank-one metric algebra; physical density/source vertex `PARAMETRIC ONLY`.

The same exact metric gives a tilt-dependent action for a fixed background worldline and no tilt action for a source co-moving with the director. Therefore the metric alone does not select a universal physical matter current, record vertex or screening charge.

Version 2 separates runtime provenance from the exact rational scientific
payload.  The v1 file is retained and has the same scientific identities.

## Freeze

`MANIFEST_SHA256_v3.json` records the current script and deterministic-output
hashes. `MANIFEST_SHA256_v1.json` and `MANIFEST_SHA256_v2.json` are retained
as historical provenance; v2 is explicitly superseded because two of its
whole-file hashes were runtime-dependent. Regeneration with a materially
different scientific payload requires a newly named version.
