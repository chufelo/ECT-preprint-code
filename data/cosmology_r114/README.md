# R114 two-slope finite-body publication owner

Status: **DETERMINISTIC CURRENT PUBLIC OWNER AT THE REPOSITORY COMMIT**  
Owner ID: `ECT-COSMO-R114-FINITEBODY-ESTIMATORS-v1`  
Date: 2026-07-20

## Scientific scope

This bundle owns three distinct scalar-BVP statistics for the declared
dimensionless row `(m,n,r,eta,m_out R)=(1,3,0.99,3333,1)` and the regular
`r -> 1` asymptotic limit at fixed `eta`.  It does not identify any statistic
with the physical sensitivity of a gravitating body, does not include metric
backreaction and is not a Cassini, WEP or full PPN calculation.

## Reproduction

From the repository root, run:

```text
python3 scripts/cosmology/compute_r114_twoslope_finitebody_estimators.py
python3 scripts/verification/r114/verify_r114_twoslope_finitebody_estimators.py
```

The producer and independent sparse-finite-difference verifier were replayed
twice.  Their four scientific payload files were byte-identical between runs.
Runtime versions are isolated in
`R114_TWOSLOPE_FINITEBODY_RUNTIME_v1.json` and are excluded from the
scientific manifest.

## Exact manuscript mapping

| Manuscript value | Machine-readable owner | Exact field / selection | Display rule |
|---:|---|---|---|
| `0.006399711753` | `R114_TWOSLOPE_FINITEBODY_REDTEAM_v1.json` | `stated_x5_x9_proxy_r0p99_eta3333` | 12 decimal places; finite-window mean on `5 <= x <= 9` |
| `0.006393895852` | same | `asymptotic_proxy_r0p99_eta3333` | 12 decimal places; independent asymptotic coefficient at `r=0.99`, `eta=3333` |
| `0.006372442154` | same | `vacuum_endpoint_asymptotic_proxy_r1_eta3333` | 12 decimal places; regular `r -> 1` asymptotic limit at fixed `eta` |

The values are not repeated measurements and must not be averaged.  Their
definitions are non-interchangeable.  The independent method finds that the
finite-window statistic exceeds the asymptotic `r=0.99` coefficient by about
`0.09096%`; this is an estimator-definition difference, not an uncertainty
band.

## File roles

- `R114_R105_ACTION_STATE_INPUT_SNAPSHOT_v1.csv`: model input;
- `R114_TWOSLOPE_FINITEBODY_TARGETS_v1.json`: producer scientific output;
- `R114_TWOSLOPE_FINITEBODY_GRID_v1.csv`: producer BVP grid/output table;
- `R114_EARLYG_CASSINI_CHARGE_TARGETS_v1.csv`: conditional design targets,
  not a PPN pass;
- `R114_TWOSLOPE_FINITEBODY_REDTEAM_v1.json`: independent decisive values and
  status guards;
- `R114_TWOSLOPE_FINITEBODY_RUNTIME_v1.json`: volatile runtime sidecar,
  deliberately excluded from the scientific manifest.

The bundle supersedes the same scientific calculation stored only inside the
R106 research handoff.  That predecessor remains preserved as provenance.
