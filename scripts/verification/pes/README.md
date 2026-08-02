# P6 record-sector verification scripts

Curated, environment-stable checks for the conditional PES-R calculational
framework used in Appendices BI--BP.  They verify algebra and protocol
behaviour inside explicitly supplied kernels and toy models; the physical
record vertex/channel and global PES remain Open.

Contents:
- p6_s6r18_audit.py            -- kernel-exponent and dephasing-class audit
- p6_s6r19_checks.py           -- threshold residue, Z_b sum rule, P24 slope checks
- p6_s6r20_checks.py           -- dressed-response and counterterm-convention checks
- p6_s7_closure_demo.py        -- synthetic P26 cross-corner consistency check
- p6_m3_operational_guards.py  -- shared M3 guard audits (failure hierarchy inputs)
- p6_m3_p23_p24_protocol.py    -- M3-1 intrinsic/external threshold contrast protocol
- p6_m3_p7p18_zero_mode_detector.py -- M3-2 zero-mode detector (flatness transforms, odd projection)
- p6_m3_p11_p25_protocol.py    -- M3-3 Airy-width/fingerprint protocol checks

Environment: Python 3 with numpy only (standard library otherwise).
Each script is a curated copy of the corresponding frozen audit file;
private working logs, exploratory scratch files, and local virtual
environments are not part of this release archive. Conventions and
symbols follow Appendices BI--BP of the preprint (Weiss density
J_W = J_bare/(2*omega); pair normalisation sigma_dec = sigma_pair,
zeta_0^pair = 2).

The historical 16-sentinel freeze-status audit is preserved under
`provenance/pes/r190/nonautonomous_freeze_status_audit/`, not here: it requires
private ledger and honesty-log inputs and therefore is not an autonomous
public verifier.  Its frozen all-`MISSING` output is evidence of that missing
input boundary, not a failed scientific calculation.

## Independent R114 algebra guards

Three additional autonomous R114 checks are retained under `r114/` because
they test distinct standard open-system or response-algebra boundaries:

- `r114/m1/verify_m1_same_channel_fdt_v2.py` — finite-window, same-channel,
  matrix-completeness, causality and detailed-balance counterexamples;
- `r114/verify_m5_bridge_invariant.py` — response-coordinate and nonlinear
  bridge invariants/non-uniqueness; and
- `r114/verify_m6_spectral_lmi.py` — the correct pair of spectral LMIs and the
  noncommuting-matrix counterexample to an invalid absolute-value shortcut.

Run them directly from the repository root.  They are deterministic synthetic
algebra checks, contain no observational data, and do not derive a physical
ECT record channel, metric vertex, complete-positive reduced map or global
PES.  The former R114 figure-integration verifier is not included in this
active directory because it required private candidate/protocol inputs; its
absence is a declared public-input boundary, not a scientific PASS.

## Cross-runtime replay gate

After running all eight active verifiers, compare their eight result tables
and the active shape table with the tracked numerical-equivalence policy:

```bash
python3 scripts/verification/verify_runtime_equivalence.py \
  --policy scripts/verification/pes/PES_RUNTIME_EQUIVALENCE_POLICY_v1.json \
  --reference-root /path/to/frozen-reference-clone \
  --candidate-root /path/to/replay-clone
```

The policy requires the CSV row/column structure, categories, booleans,
status-like checks and all non-numeric text to remain exact.  Numeric tokens,
including numbers inside composite cells, use explicit absolute and relative
tolerances of `1e-12`.  A PASS is numerical equivalence, not byte identity and
not a scientific uncertainty statement.  These calculations remain
model-internal checks for supplied kernels and toy protocols: the physical
record vertex/channel and physical/global PES remain Open.
