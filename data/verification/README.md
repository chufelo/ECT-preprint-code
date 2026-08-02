# Conditional benchmark registry verification

`R190_CONDITIONAL_BENCHMARK_RESULTS_v1.json` is a deterministic, standalone
public arithmetic owner for exactly six conditional benchmark rows:

- Hubble soft-scalar orientation;
- geometric seesaw scale and inverse fits;
- unit Weinberg point and required coefficient;
- heavy-radial negative control;
- dimension-six proton NDA; and
- D-P hard homogeneous spheres at `d/R = 1`.

Regenerate it from the repository root with:

```sh
SOURCE_DATE_EPOCH=1785628800 python3 scripts/verification/verify_conditional_benchmark_registry.py
```

The verifier has no internal-package, manuscript, external-data, or network
dependency. Its inputs, conventions, no-seed declaration, tolerances and
printed-rounding policy are frozen inside the source and copied into the JSON
payload. It fails closed if arithmetic, independent D-P quadrature, edge
cases, finite-precision checks, displayed rounding, or the status firewall
changes.

Every row is conditional/external arithmetic and **not a data test**. None is
an ECT prediction; every physical ECT owner remains Open or Not Identifiable.
The result is reproducible computational arithmetic, not experimental closure.
