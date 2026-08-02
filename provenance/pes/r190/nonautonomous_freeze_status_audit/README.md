# Non-autonomous historical P6 freeze-status audit

This directory preserves the old 16-sentinel ledger audit and the output it
produces in a public checkout.  The script searches for private PES ledger,
honesty-log, and verification-note inputs that are not redistributed here;
without them its correct outcome is `FREEZE_CANDIDATE_INCOMPLETE` with all
sentinels marked `MISSING`.

It is not part of the active public scientific verification surface.  The
autonomous numerical and algebraic P6/PES checks remain under
`scripts/verification/pes/`, and physical/global PES remains Open.
