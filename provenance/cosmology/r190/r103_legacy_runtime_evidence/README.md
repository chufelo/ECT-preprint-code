# R103 legacy runtime evidence

These files are excluded from the active R103 scientific data manifest.

- The conditional-age and conditional-observable stdout captures were made in
  an older runtime and contain stale last-bit/runtime metadata.
- The restricted ISW stdout capture is byte-identical to its then-current JSON
  owner, but is a redundant console transcript rather than a scientific input.
- The rebuild report records an intermediate R190 metadata refresh, before the
  final English-document release build.

Current scientific JSON/CSV owners remain under `data/cosmology_r103/`.
Runtime and build evidence for the current package belongs in the R190 release
build reports and is excluded from scientific digests.
