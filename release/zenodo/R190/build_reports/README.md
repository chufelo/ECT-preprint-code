# Build-report staging

This directory contains the accepted deterministic English build reports for
the current public-repository alignment.  They are evidence for the document
build gate, but they do not turn the still-draft Zenodo package into a tagged
or released version.

The accepted command outputs are:

- `preprint-build.txt`;
- `companion-build.txt`; and
- `summary-build.txt`.

Each report must use repository-relative or neutral build paths and record
pages as `X pages (was Y)`, errors, undefined references, undefined citations,
multiply-defined labels, rerun-required diagnostics, overfull boxes, and
underfull boxes. Do not record private absolute host paths.

The reports become release-manifest inputs only after a public version and
date are chosen, the release package is advanced through review, and
`freeze_release.py pretag` hashes them. This README is not a substitute for
the reports, and no tag, upload or publication is represented here.
