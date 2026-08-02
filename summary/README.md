# ECT summary

`ECT_summary.tex` is the compact third English publication layer, downstream
of both the canonical preprint and the narrative companion. It introduces ECT
for a new reader, but it must not omit a qualification in a way that
strengthens an upstream claim. The governing order is preprint → companion →
summary.

The repository-level `references.bib` is its only authoritative bibliography.
Build the complete English chain from the root of a standalone clone:

```bash
bash scripts/compile_preprint.sh
bash companion/scripts/compile_companion.sh
bash summary/compile_summary.sh
```

Level A means a derivation only inside its explicitly stated model and
assumptions; Level B is structural or conditional; Level C is fitted,
benchmarked or application-level; Open identifies a missing owner or input.
Clean typesetting, successful execution and agreement with an external model
do not by themselves strengthen those statuses.
