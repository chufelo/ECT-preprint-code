# ch5_sne.py — REMOVED

This file previously contained a Type Ia supernova "channel" that was
methodologically invalid:

- It generated `mu_sn` values from the ΛCDM baseline theory itself,
  rather than using real Pantheon+ observational data.
- Fitting ECT to data derived from ΛCDM guarantees ε ≈ 0 by
  construction and is NOT a genuine observational test.

Removed following ChatGPT review (2026-04-17).

To implement a real SN Ia channel in the future, one needs:
- Actual Pantheon+ observed distance moduli
- Proper host-galaxy calibration treatment
- SH0ES systematics handling
- Full covariance matrix

Until then, SN Ia is NOT part of the ε-constraint apparatus.
