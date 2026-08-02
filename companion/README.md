# ECT narrative companion

`ECT_companion.tex` is the second English publication layer. It is downstream
of the canonical technical preprint `../ECT_preprint.tex`: when wording or
status differs, the preprint controls, and the companion must not strengthen
the claim.

Its local figures are under `figures/`, its build helper under `scripts/`, and
shared publication figures are resolved explicitly from `../figures/`.

Build from the root of a standalone clone, after the preprint:

```bash
bash scripts/compile_preprint.sh
bash companion/scripts/compile_companion.sh
```

Level A, Level B, Level C and Open have the meanings defined in the repository
[`README.md`](../README.md). A clean build or a reproduced benchmark does not
upgrade a scientific status. The English summary is the next downstream layer
and is built only after this companion.
