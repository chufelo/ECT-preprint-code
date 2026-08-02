# Reproducibility and release protocol

This document defines the public, standalone-clone-safe workflow for the
English ECT publication chain and the successor release package in
`release/zenodo/R190/`.

The current package status is
`DRAFT_NOT_TAGGED_NOT_RELEASED`. `R190` is an internal
preparation identifier, not a public version. This protocol makes no network
write and does not grant permission to commit, tag, push, upload, or publish.

## 1. Status and evidence discipline

Reproduction has four different meanings which must not be collapsed:

1. internal algebra or numerical normalisation;
2. reproduction of an external source model;
3. consistency with experimental or observational data; and
4. ECT-specific discrimination or prediction.

Scientific claims retain their Level A / Level B / Level C / Open labels. A
deterministic calculation, clean build, metadata check, or tag attestation
does not upgrade that hierarchy.

The release gates use these outcomes:

- `PASS_LOCAL_SCHEMA_ONLY` — draft metadata and policies are internally
  consistent; artifacts, Git ownership and publication are not established;
- `PASS_LOCAL_FROZEN_CANDIDATE` — exact local artifacts have a canonical
  pre-tag manifest; Git ownership and publication are not established; and
- `PASS_TAG_ATTESTED_NOT_RELEASED` — the manifest and every frozen artifact
  are owned by a named local tag and commit; no push, upload, DOI assignment,
  or publication is established.

There is intentionally no local `RELEASED` result.

## 2. Environment

Create the declared utility environment from the repository root:

```bash
conda env create -f environment-r190.yml
conda activate ect-preprint-r190
```

The YAML is an executable environment specification, not a cross-platform
lockfile. The optional runtime sidecar produced during a freeze records exact
tool and platform versions, but is excluded from the scientific aggregate
digest. Historical frozen products retain their own environment records and
must not be silently overwritten by a newer runtime.

The frozen R97 HRC products have a separate exact-replay environment:

```bash
conda env create -f environment-hrc-r97.yml
conda activate ect-hrc-r97-frozen
```

Use that environment when byte identity of the committed HRC CSV/JSON and
figure set is the acceptance criterion. The general R190 environment may be
used for an independent numerical check, but last-bit differences under newer
NumPy/SciPy/Matplotlib versions must be evaluated under an explicit tolerance
policy and must never overwrite the frozen R97 owners. The historical R103
two-slope scan is governed by the same principle: its recorded legacy runtime
can reproduce the frozen bytes, while a modern-runtime replay is a numerical
equivalence check rather than a byte-identity proof.

English document builds additionally require pdfTeX, BibTeX, the fonts used by
the sources, and one supported PDF page counter (`pypdf`, PyMuPDF, or
`pdfinfo`). Graphviz is required only for Graphviz-owned figures.

The build scripts accept explicit executable overrides, for example:

```bash
PDFLATEX="$(command -v pdflatex)" \
BIBTEX="$(command -v bibtex)" \
bash scripts/compile_preprint.sh
```

## 3. Standalone path policy

Every public command is run from the repository root. Public scripts resolve
the root relative to their own location and use repository-relative owner
paths. They must reject absolute owner paths and `..` traversal.

When the repository is nested in the full ECT workspace, document builds use
the sibling `.workspace/build/` tree. In a standalone clone they use
`.build/`. Release tools accept `--repo-root` and never require
`research/derivations/`, `work/preprint/`, a private chat export, or an
absolute path from the author's computer.

## 4. Rebuild the governing English chain

Run in governing order:

```bash
PREVIOUS_PAGES=890 bash scripts/compile_preprint.sh \
  | tee release/zenodo/R190/build_reports/preprint-build.txt

PREVIOUS_PAGES=123 bash companion/scripts/compile_companion.sh \
  | tee release/zenodo/R190/build_reports/companion-build.txt

PREVIOUS_PAGES=11 bash summary/compile_summary.sh \
  | tee release/zenodo/R190/build_reports/summary-build.txt
```

The numeric values above are the accepted R189 comparison baseline, not a
promise about a later revision. Every report must state `X pages (was Y)` and
record:

- LaTeX errors;
- undefined references;
- undefined citations;
- multiply-defined labels;
- rerun-required diagnostics;
- overfull boxes; and
- underfull boxes.

Acceptance requires zero for the first five diagnostic classes and a readable,
non-empty PDF. Box diagnostics are retained for review. Review the rendered
first pages, diagrams, status labels, bibliography pages, and every region
changed since the accepted predecessor.

The default commands build only the English chain. Deferred or non-English
publication paths are outside this release.

## 5. Re-run scientific owners

Compilation proves TeX integrity, not theory. Re-run every public verifier
whose source, input, output, table, or figure changed. Use the nearest owning
README and manifest to determine the command, assumptions, tolerances, and
expected output.

At minimum, the release review must cover the active public surfaces named in
the manuscript reproducibility tables:

- the six-row conditional conclusion registry under
  scripts/verification/verify_conditional_benchmark_registry.py;

- HRC release verification under `scripts/hrc/`;
- conditional cosmology checks under `scripts/cosmology/` and
  `scripts/verification/r103/`, `r113/`, and `r114/`;
- PES-R verifiers under `scripts/verification/pes/`; and
- the registered-figure verifier under `scripts/figures/` and the label,
  reference and citation diagnostics emitted by each document build.

For HRC, activate `environment-hrc-r97.yml` before the four commands listed in
`scripts/hrc/README.md`. Record both the runtime and the clean-copy comparison;
running those generators in `environment-r190.yml` is not a substitute for the
frozen byte-identity gate.

The strict standalone figure-registry gate is:

```bash
python3 scripts/figures/verify_public_figure_registry.py \
  --strict-provenance \
  --json-output .build/figure-registry-verification.json
```

The six lifecycle-neutral status schematics are reproduced before this gate:

```bash
SOURCE_DATE_EPOCH=1785628800 \
  python3 scripts/figures/build_public_status_schematics.py
```

That producer inherits the frozen scientific nodes, arrows, formulae, status
classes and layout; it changes only reader-facing lifecycle titles and PDF
metadata.  Its deterministic manifest is
data/verification/R190_PUBLIC_STATUS_SCHEMATICS_v1.json.

It checks the English preprint, companion and summary in that governing order,
all active figure insertions, exact output hashes, CSV/JSON registry identity,
and every publicly declared generator and data-owner hash. Logical
`LaTex/...` paths in the registry are resolved relative to the root of this
standalone repository. The verifier rejects absolute or traversing owner paths
and does not inspect deferred or non-English documents.

Do not substitute a broad “all scripts ran” statement for owner-by-owner
results. Imported benchmarks, matching-only checks, parametric calculations,
synthetic tests, and quarantined historical producers must retain those
classifications. Any unlisted script or notebook is excluded by default.

The standalone arithmetic owner for the six conclusion benchmarks is:

```bash
SOURCE_DATE_EPOCH=1785628800 \
  python3 scripts/verification/verify_conditional_benchmark_registry.py
```

Its accepted status is PASS_CONDITIONAL_ARITHMETIC_ONLY.  It is explicitly
not a data test, not an ECT prediction and not a physical-owner closure.

For cross-runtime replays, use
`scripts/verification/verify_runtime_equivalence.py` with the tracked R103 or
PES policy and separate reference/replay roots. These policies require exact
structure, status text and non-numeric content; only numeric values use their
declared tolerances. A tolerance-policy PASS is not byte identity and is not
a scientific uncertainty estimate.

For repeated calculations, require:

- exact input paths and SHA-256 hashes;
- parameters, seeds, conventions and thresholds;
- deterministic JSON or CSV outputs where applicable;
- two clean replays after removing only generated outputs; and
- byte-identical scientific outputs, or an explicit tolerance policy if bytes
  cannot be the identity criterion.

Runtime timestamps, host names, absolute paths and package diagnostics belong
in a sidecar and must not alter the scientific digest.

## 6. Figure provenance and third-party inputs

Every included publication figure must have an entry in
`FIGURE_REGISTRY.csv` and `FIGURE_REGISTRY.json` with its output, source owner
or external origin, generation command, inputs, document uses, scientific
status, and readability classification. A frozen binary without a public
generator must be labelled as such; it is not reproducible source.

Before a repository tag or archive is created, audit every external input
against [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Presence in the
working tree does not establish redistribution permission. Raw SPARC products
and any other unapproved external payload are excluded from both manuscript
uploads and from a source archive.

A registry entry may explicitly declare that an external input is not
redistributed. Such a declaration preserves the provenance boundary but does
not count as a successful replay. Full reproduction then requires the input
contract, expected hash and acquisition instructions named by the owning
programme.

## 7. Validate the draft release package

The default validator is offline and schema-only:

```bash
python3 release/zenodo/R190/validate_release.py
```

Expected result for the checked-in draft:

```text
PASS_LOCAL_SCHEMA_ONLY
```

This checks the two concept DOI owners, the read-only predecessor-record
snapshot, reciprocal relations, creator, language, licence, null future
identifiers, null draft version/date, upload allowlist, licensing boundary,
safe relative paths, and citation metadata. It does not inspect Zenodo live
state and does not claim the snapshot is current forever.

`KNOWN_RECORDS_SNAPSHOT.json` records where and when the predecessor facts were
observed. Refreshing it is a separate read-only research step. Never replace
the recorded observation date with the current date without performing that
verification.

## 8. Prepare canonical build artifacts

After builds and scientific gates pass, install the accepted English outputs
at their canonical repository paths and prove byte identity against the build
outputs. The exact build locations depend on whether this is a full workspace
or standalone clone; resolve them explicitly and never embed a private
absolute path in a report.

The pre-tag manifest requires:

- four source owners: preprint, companion, summary, and bibliography;
- three canonical PDFs;
- three canonical BBL files;
- three build reports; and
- the public R190 scientific/integrity validation report named by
  `RELEASE_INPUT_CONTRACT.json` once that report has been accepted and copied
  into the public package.

The draft contract records the accepted R189 source/PDF/BBL baseline as
predecessor evidence. Those hashes are not silently reused as R190 final
hashes: `freeze_release.py` records the actual bytes present at freeze time.

## 9. Phase A — create the pre-tag artifact manifest

Before freezing, choose and review the intended public version and publication
date, replace `DRAFT_NOT_TAGGED_NOT_RELEASED` with
`RELEASE_CANDIDATE_NOT_RELEASED` in all status-bearing R190 public documents
and JSON files, enter the same values in both metadata files and the input
contract, and replace every validation `PENDING` only with an evidence-backed
`PASS`. Then require:

```bash
python3 release/zenodo/R190/validate_release.py --require-pretag-ready
```

Expected result is `PASS_PRETAG_INPUTS_REVIEWED_NOT_FROZEN`. From that reviewed
repository root, freeze the artifact set:

```bash
python3 release/zenodo/R190/freeze_release.py pretag \
  --repo-root . \
  --output release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --runtime-sidecar .build/zenodo-r190-runtime.json
```

The command:

- reads the exact artifact allowlist from `RELEASE_INPUT_CONTRACT.json`;
- rejects missing, absolute, traversing, duplicate, or unlisted owner paths;
- records SHA-256, byte count, role, and PDF page count;
- sorts records by repository-relative path;
- computes the aggregate digest from the canonical record list;
- excludes the manifest itself and the runtime sidecar from that digest; and
- writes canonical UTF-8 JSON with sorted keys, LF line endings, and a final
  newline.

The resulting status is `LOCALLY FROZEN CANDIDATE`. It contains no commit,
tag, release date, public version, or new DOI. Run it twice to different
temporary outputs and compare the files byte-for-byte before accepting it.

Validate against the current worktree:

```bash
python3 release/zenodo/R190/validate_release.py \
  --pretag-manifest release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json
```

Expected result:

```text
PASS_LOCAL_FROZEN_CANDIDATE
```

## 10. Review, commit and tag — separately authorised operations

Before a commit, inspect the exact scoped diff and confirm that it excludes
private material, caches, backups, work candidates, unapproved third-party
payloads, deferred book paths, and non-English publication artifacts. The
pre-tag manifest itself must be in the reviewed commit.

Creating the commit and tag are external state changes relative to this
candidate workflow. They require explicit authorisation and are not performed
by any R190 Python tool.

## 11. Phase B — attest the existing tag

After an authorised tag exists locally, generate a separate post-tag
attestation:

```bash
python3 release/zenodo/R190/freeze_release.py attest-tag \
  --repo-root . \
  --pretag-manifest release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --git-commit FULL_40_CHARACTER_COMMIT_SHA \
  --git-tag EXACT_TAG_NAME \
  --output .build/zenodo-r190-tag-attestation.json
```

This second phase resolves the tag to a commit and reads every frozen artifact
directly from that commit with local Git. It verifies that the committed
pre-tag manifest is byte-identical to the reviewed manifest and that every
artifact hash and byte count matches. The attestation is separate because a
file cannot truthfully contain the hash of the commit that first contains that
same file.

Final local validation is:

```bash
python3 release/zenodo/R190/validate_release.py \
  --pretag-manifest release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --tag-attestation .build/zenodo-r190-tag-attestation.json \
  --require-release-ready
```

Expected result after the metadata version and publication date have been
reviewed and deliberately filled, and after the exact tag exists:

```text
PASS_TAG_ATTESTED_NOT_RELEASED
```

Future Zenodo record IDs and version-specific DOIs must still be `null` at
this pre-draft stage. They may be recorded only after Zenodo actually assigns
them.

## 12. Stage the exact two PDF payloads

After tag attestation, stage bytes from the attested commit rather than from a
possibly dirty worktree:

```bash
python3 release/zenodo/R190/build_upload_payloads.py \
  --repo-root . \
  --pretag-manifest release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --tag-attestation .build/zenodo-r190-tag-attestation.json \
  --output .build/zenodo-r190-payloads
```

Expected contents:

```text
.build/zenodo-r190-payloads/
├── companion/ECT_companion.pdf
├── preprint/ECT_preprint.pdf
└── PAYLOAD_SHA256SUMS
```

The tool refuses extra files, a summary upload, source archives, raw external
data, private/work material, future identifiers invented before assignment,
or bytes that do not match the tag-bound manifest. It performs no network
operation.

## 13. External release boundary

The following steps are outside these tools and each requires explicit
authorisation:

1. push the reviewed commit and tag;
2. create a new draft under each existing Zenodo concept record;
3. enter and inspect the deliberately chosen public version and publication
   date;
4. upload exactly the allowlisted PDF to each draft;
5. record the Zenodo-assigned record IDs and version-specific DOIs;
6. verify reciprocal relations, licence, preview, filenames, sizes and hashes;
   and
7. publish only after a final author command.

The technical preprint concept DOI is
`10.5281/zenodo.18917929`; the companion concept DOI is
`10.5281/zenodo.19430795`. These permanent identifiers do not identify an
exact revision. No tool in this repository calls the Zenodo API or performs a
network write.

## 14. Required release report

The final handoff must state separately:

- what was derived or established;
- what was merely reproduced, imported, fitted, or benchmarked;
- what remains Open;
- every file created or modified;
- all checks and their exact outcomes;
- source, PDF, BBL, report, manifest, commit and tag hashes;
- pages as `X pages (was Y)`;
- errors, undefined references, undefined citations, multiply-defined labels,
  overfull boxes and underfull boxes;
- unresolved licence or provenance uncertainty; and
- whether any commit, push, upload, DOI assignment, or publication occurred.

Do not rewrite the historical R148 workspace package.  It is predecessor
provenance, not part of the current public-tree allowlist; the public facts
needed for succession are frozen in
`release/zenodo/R190/KNOWN_RECORDS_SNAPSHOT.json`.
