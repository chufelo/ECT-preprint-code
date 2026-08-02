# Public calculation and verification scripts

Run public commands from the root of a standalone clone. The governing
document order is preprint → companion → summary, and no downstream
document may state a stronger result than the preprint.

```bash
bash scripts/compile_preprint.sh
bash companion/scripts/compile_companion.sh
bash summary/compile_summary.sh
```

The principal script families are:

- `cosmology/` and `verification/r103/`, `r113/`, `r114/` — conditional
  cosmology calculations with the action, background, response and input
  assumptions declared by their manifests;
- `hrc/` — supplied-response galactic diagnostics and release verification;
- `verification/pes/` — PES-R algebraic and protocol checks; physical/global
  PES remains Open;
- `verification/verify_conditional_benchmark_registry.py` — the standalone
  arithmetic owner for the six explicitly scoped conclusion benchmarks;
- `verification/verify_runtime_equivalence.py` — fail-closed comparison of
  frozen and replay outputs under a named tolerance policy;
- `figures/` and `r153_line_semantics/` — current publication-figure
  generation and rendering, including the lifecycle-neutral public status
  schematics; frozen predecessor producers needed by the active registry are
  retained under `../provenance/figures/r190/`, not advertised as current
  scripts; and
- `figures/verify_public_figure_registry.py` — strict English-chain insertion,
  provenance and hash verification.

Run the figure gate from the repository root:

```bash
python3 scripts/figures/verify_public_figure_registry.py \
  --strict-provenance \
  --json-output .build/figure-registry-verification.json
```

Data owners are under `data/`, publication assets under `figures/`, and exact
figure-to-owner relations in `FIGURE_REGISTRY.csv` and
`FIGURE_REGISTRY.json`. Some external inputs are deliberately not
redistributed; the owning input contract supplies their source and expected
hash. Successful execution establishes only the result declared by that
owner. It does not turn a calibration, imported benchmark, fit, candidate
mechanism or Open programme into a Level-A ECT prediction.

Two additional deterministic commands are part of the publication gate:

```bash
SOURCE_DATE_EPOCH=1785628800 \
  python3 scripts/verification/verify_conditional_benchmark_registry.py
SOURCE_DATE_EPOCH=1785628800 \
  python3 scripts/figures/build_public_status_schematics.py
```

Historical patch, migration and integration helpers are not public scientific
owners and are intentionally absent from this directory. See
[`../REPRODUCIBILITY.md`](../REPRODUCIBILITY.md) for the full gate sequence.
