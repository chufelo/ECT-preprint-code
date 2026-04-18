#!/usr/bin/env python3
"""Phase 1 insertion: new §15.5.1 block before old §15.5, + rebuild annotation on old §15.5.

Hard safety:
- asserts on anchor existence and uniqueness before any write
- verifies post-write invariants
- prints checksums before and after
"""

import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/01_s15_5_1_LATEX_SNIPPET.tex"


def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


print(f"MD5 pre-edit  = {md5(PREPRINT)}")
print(f"PREPRINT size = {PREPRINT.stat().st_size} bytes")

text = PREPRINT.read_text()
snippet = SNIPPET.read_text()
snippet_core = snippet.rstrip() + "\n\n"

# --- Anchor C: insertion of new block before old §15.5 header delimiter ---
anchor_C_old = (
    "is not independently identifiable at the current closure level.\n"
    "\n"
    "% ============================================================\n"
    "\\subsection{Hubble tension: structural mechanism, benchmark closure, and robustness}\n"
    "\\label{sec:mp_hubble}\n"
)
assert anchor_C_old in text, "Anchor C not found"
assert text.count(anchor_C_old) == 1, f"Anchor C not unique (count={text.count(anchor_C_old)})"
print("Anchor C: found, unique.")

anchor_C_new = (
    "is not independently identifiable at the current closure level.\n"
    "\n"
    + snippet_core +
    "% ============================================================\n"
    "\\subsection{Hubble tension: structural mechanism, benchmark closure, and robustness}\n"
    "\\label{sec:mp_hubble}\n"
)

text2 = text.replace(anchor_C_old, anchor_C_new, 1)
assert text2 != text, "Replacement C produced no change"
assert text2.count(anchor_C_new) == 1, "Anchor C replacement not unique post-insertion"

# --- Anchor D: add rebuild-annotation block at top of old §15.5 body ---
anchor_D_old = (
    "\\subsection{Hubble tension: structural mechanism, benchmark closure, and robustness}\n"
    "\\label{sec:mp_hubble}\n"
    "% ============================================================\n"
    "\n"
)
assert anchor_D_old in text2, "Anchor D not found after C insertion"
assert text2.count(anchor_D_old) == 1, f"Anchor D not unique (count={text2.count(anchor_D_old)})"
print("Anchor D: found, unique.")

annotation = (
    "% ==================================================================\n"
    "% NOTE: This section is being rebuilt in parallel.\n"
    "%       See \\ref{sec:cosmo_constraints_rebuilt} above for the new\n"
    "%       version under construction.\n"
    "%       Current status: \\S15.5.1 (rebuilt) integrated,\n"
    "%       \\S15.5.2--15.5.6 pending.\n"
    "%       Full migration inventory pending Step 2.0.\n"
    "%       DO NOT REMOVE this section until the rebuild is complete.\n"
    "%       Per-item migration annotations will be added during\n"
    "%       Step 2.0 inventory.\n"
    "% ==================================================================\n"
    "\n"
)

anchor_D_new = (
    "\\subsection{Hubble tension: structural mechanism, benchmark closure, and robustness}\n"
    "\\label{sec:mp_hubble}\n"
    "% ============================================================\n"
    "\n"
    + annotation
)

text3 = text2.replace(anchor_D_old, anchor_D_new, 1)
assert text3 != text2, "Replacement D produced no change"

# --- Post-write invariants ---
assert text3.count("\\label{sec:cosmo_constraints_rebuilt}") == 1, "new label count != 1"
assert text3.count("\\label{subsec:eps_def_rebuilt}") == 1, "new sub-label count != 1"
assert text3.count("\\label{sec:mp_hubble}") == 1, "old label count != 1 (must remain intact)"
assert text3.count(
    "\\subsection{Hubble tension: structural mechanism, benchmark closure, and robustness}"
) == 1, "old §15.5 subsection header count != 1"

PREPRINT.write_text(text3)

print(f"MD5 post-edit = {md5(PREPRINT)}")
print(f"PREPRINT size = {PREPRINT.stat().st_size} bytes")
old_lines = text.count("\n")
new_lines = text3.count("\n")
print(f"Line delta    = {new_lines - old_lines} (old {old_lines} -> new {new_lines})")

print("OK: S15.5.1 block inserted, old S15.5 annotated with rebuild notice.")
