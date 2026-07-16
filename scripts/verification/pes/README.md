# P6 record-sector verification scripts

Curated, environment-stable verification scripts for the frozen P6/PES
spectral-record framework of the ECT preprint (Appendices BI--BP).

Contents:
- p6_s6r18_audit.py            -- kernel-exponent and dephasing-class audit
- p6_s6r19_checks.py           -- threshold residue, Z_b sum rule, P24 slope checks
- p6_s6r20_checks.py           -- dressed-response and counterterm-convention checks
- p6_s7_closure_demo.py        -- P26 over-closure loop demonstration (width -> kernel -> dephasing/shift)
- p6_m3_operational_guards.py  -- shared M3 guard audits (failure hierarchy inputs)
- p6_m3_p23_p24_protocol.py    -- M3-1 intrinsic/external threshold contrast protocol
- p6_m3_p7p18_zero_mode_detector.py -- M3-2 zero-mode detector (flatness transforms, odd projection)
- p6_m3_p11_p25_protocol.py    -- M3-3 Airy-width/fingerprint protocol checks
- p6_freeze_status_audit.py    -- freeze-status sentinel audit (16-point)

Environment: Python 3 with numpy only (standard library otherwise).
Each script is a curated copy of the corresponding frozen audit file;
private working logs, exploratory scratch files, and local virtual
environments are not part of this release archive. Conventions and
symbols follow Appendices BI--BP of the preprint (Weiss density
J_W = J_bare/(2*omega); pair normalisation sigma_dec = sigma_pair,
zeta_0^pair = 2).
