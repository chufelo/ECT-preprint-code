# Euclidean Condensate Theory publication repository

This repository is the English publication and reproducibility layer of
Euclidean Condensate Theory (ECT).

The governing document order is:

1. `ECT_preprint.tex` — canonical technical manuscript and claim owner;
2. `companion/ECT_companion.tex` — narrative companion, downstream of the
   preprint; and
3. `summary/ECT_summary.tex` — compact English summary, downstream of both.

If a downstream statement is ambiguous, the preprint controls. A downstream
document must never present a stronger status than its upstream owner.

Pre-existing non-English companion/summary files are deferred historical
artifacts, not part of the current English claim or release surface.  They are
kept byte-unchanged here and are not represented as synchronized with this
English document chain.

## Scientific status

ECT uses four status classes throughout the manuscript chain:

- **Level A:** derived inside the explicitly stated model and assumptions;
- **Level B:** structural or conditional result with declared open matching
  inputs;
- **Level C:** phenomenological fit, imported benchmark, application-level
  estimate, or candidate mechanism; and
- **Open:** not derived, not identified, or missing a required action, state,
  vertex, measure, likelihood, or observable map.

Four evidential steps must also remain distinct:

1. internal algebra or numerical normalisation;
2. reproduction of an external source model;
3. consistency with experimental or observational data; and
4. ECT-specific discrimination or prediction.

A result at steps 1–3 is not automatically evidence for ECT. In particular,
the repository does not claim that PES proves quantum mechanics or the Born
rule, that one scalar bath is universal, that compact phase winding is the
universal source of every discrete spectrum, or that a benchmark fit derives
its physical owner.

## Build the English document chain

Create the declared environment, then run these commands from the repository
root:

```bash
conda env create -f environment-r190.yml
conda activate ect-preprint-r190

bash scripts/compile_preprint.sh
bash companion/scripts/compile_companion.sh
bash summary/compile_summary.sh
```

The historical R97 HRC products use the separate
`environment-hrc-r97.yml` exact-replay environment. This separation is
intentional: the current utility environment is appropriate for the document
and registry toolchain, whereas the pinned Python 3.12 numerical stack is the
owner of byte-identical HRC replay. See `REPRODUCIBILITY.md` and
`scripts/hrc/README.md` before regenerating committed scientific products.

The build scripts use `.workspace/build/` when this repository is nested in
the full ECT workspace and `.build/` in a standalone clone. `PDFLATEX` and
`BIBTEX` may be set explicitly when the TeX executables are not installed at
the scripts' platform defaults.

Each accepted build must report a readable PDF, page count, zero LaTeX errors,
zero undefined references, zero undefined citations, zero multiply-defined
labels, and zero rerun-required diagnostics. Overfull and underfull boxes are
recorded even when they are non-fatal. Compilation alone does not validate a
scientific claim.

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the complete owner,
build, freeze, tag-attestation, and payload-staging protocol.

## Public reproducibility layout

- `scripts/` — publication calculations and verification tools, each governed
  by its own status and input contract;
- `data/` — public inputs and generated products whose provenance and
  redistribution boundary must be declared;
- `figures/` and `figures/source/` — publication figures and their sources;
- `provenance/` — immutable, hash-bound historical owners required to replay
  or audit current assets; these files are evidence, not active claim upgrades;
- `FIGURE_REGISTRY.csv` and `FIGURE_REGISTRY.json` — figure-to-owner registry;
- `release/zenodo/R190/` — successor, offline-only release preparation.

An executable file is not a scientific owner merely because it runs. Any path
not explicitly included by an owner manifest or release allowlist is excluded
by default.

Verify the complete English figure insertion and provenance registry from a
standalone clone with:

```bash
python3 scripts/figures/verify_public_figure_registry.py \
  --strict-provenance \
  --json-output .build/figure-registry-verification.json
```

This gate reads only the governing English chain, resolves the logical
`LaTex/...` owner paths stored in the registry against the standalone
repository root, and rejects missing, shadowed, stale-hash, absolute, or
traversing provenance paths. A declared missing or non-redistributed owner is
reported as such; it is never promoted to reproduced source.

## Principal calculation surfaces

| Programme | Public entry points | Status boundary |
|---|---|---|
| HRC galactic diagnostics | `scripts/hrc/`, `data/hrc_r97/`, `figures/hrc/` | supplied algebraic response and application diagnostics; no derived universal metric |
| Conditional cosmology | `scripts/cosmology/`, `data/cosmology_r103/`, `data/cosmology_r113/`, `data/cosmology_r114/` | conditional on the stated action, background, response and data inputs |
| PES-R and record channels | `scripts/verification/pes/` and the owning manuscript tables | Level-B calculational organisation; physical/global PES remains Open |
| Figure governance | `scripts/figures/`, `scripts/r153_line_semantics/`, `figures/source/`, and `provenance/figures/r190/` | current generators plus frozen provenance/readability owners; no claim-status upgrade |

The public calculation inventory also includes the standalone six-row
conditional benchmark owner in
`scripts/verification/verify_conditional_benchmark_registry.py` and the
cross-runtime gate in `scripts/verification/verify_runtime_equivalence.py`.
The former is arithmetic only, not a data test or ECT prediction.  The latter
proves numerical equivalence under an explicit policy, not byte identity or a
scientific uncertainty.

Historical, imported, matching-only, parametric, or quarantined calculations
retain those labels. Their successful execution cannot convert them into ECT
predictions.

## Citation

For the technical preprint, use the permanent Zenodo concept DOI:

- <https://doi.org/10.5281/zenodo.18917929>

For the narrative companion, use:

- <https://doi.org/10.5281/zenodo.19430795>

A concept DOI resolves to the latest published record. To identify an exact
revision, cite the version-specific DOI recorded for that revision and verify
the corresponding Git tag plus frozen artifact manifest. The repository does
not infer a version-specific DOI from a concept DOI, Git commit, filename, or
internal preparation identifier. See [`CITATION.cff`](CITATION.cff).

## Licensing and third-party boundaries

- author-owned manuscript text and original publication figures:
  `CC-BY-4.0`, except where a more specific notice applies;
- author-owned project code: MIT, except where a more specific notice applies;
- external datasets, fonts, software, quotations, and other third-party
  material: their own terms.

See [`LICENSE.md`](LICENSE.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Inclusion in a working tree
does not by itself establish permission to redistribute an item in a GitHub or
Zenodo release.

## Release boundary

`R190` is an internal preparation identifier, not a public version number.
The candidate release package has status
`DRAFT_NOT_TAGGED_NOT_RELEASED`. It contains no R190 release
date, public version, version-specific DOI, or Zenodo record ID.

All tools under `release/zenodo/R190/` are local and offline. They can validate
metadata, freeze an exact artifact set, attest an existing local Git tag, and
stage allowlisted files. They do not create a tag, push a repository, contact
Zenodo, create a draft deposit, upload, or publish.

The two manuscript records accept one PDF each. The summary PDF remains a
repository artifact unless separately authorised. Source archives, raw
third-party datasets, private research material, backups, work candidates,
chat exports, deferred book material, and non-English publication artifacts
are excluded from those two uploads.

Release state must be established by evidence in this order:

1. reviewed source and owner gates;
2. clean English builds and frozen PDF/BBL/build-report hashes;
3. a scoped Git commit containing the pre-tag manifest;
4. a local tag resolving to that exact commit;
5. a separate tag attestation; and
6. explicit, separately authorised external transactions.

No local PASS is upload or publication permission.

## Repository-host metadata (maintainer action only)

The following conservative metadata is suitable for the repository host but
is not changed by any release tool:

- description: `English ECT preprint, companion, summary, and status-disciplined reproducibility sources.`
- website: `https://doi.org/10.5281/zenodo.18917929`
- topics: `theoretical-physics`, `mathematical-physics`,
  `reproducible-research`, `latex`

Repository-host settings, releases, and topics require an explicit maintainer
action outside this package.
