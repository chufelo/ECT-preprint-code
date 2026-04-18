#!/usr/bin/env python3
"""Phase 1 integration of §15.5.2.

Inserts §15.5.2 snippet between §15.5.1 block (ending in its END marker) and
the existing old §15.5 (which starts with the rebuild-annotation comment).
Also updates the annotation comment to reflect §15.5.2 is now integrated.

Safety: asserts on anchor existence and uniqueness; fails-fast on mismatch.
"""
import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/02_s15_5_2_LATEX_SNIPPET.tex"

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

print(f"MD5 pre  = {md5(PREPRINT)}")
text = PREPRINT.read_text()
snippet = SNIPPET.read_text()

# --- Anchor A: insert §15.5.2 snippet by replacing §15.5.1 END-marker comment.
# Old §15.5.1 END block contains: "END §15.5.1 (rebuilt). §15.5.2--15.5.6 will be inserted here"
# We replace it with: (new snippet) + (new END marker referring to §15.5.3--15.5.6)
anchor_A_old = (
    "% ==================================================================\n"
    "% END §15.5.1 (rebuilt). §15.5.2--15.5.6 will be inserted here in\n"
    "% subsequent steps. DO NOT REMOVE existing §15.5 below.\n"
    "% ==================================================================\n"
)
# The snippet itself ends with its own parallel END marker; strip that duplicate
# so we don't have two consecutive END markers. The snippet's final marker is:
snippet_end = (
    "% ==================================================================\n"
    "% END \u00a715.5.2 (rebuilt). \u00a715.5.3--15.5.6 will be inserted here in\n"
    "% subsequent steps. DO NOT REMOVE existing \u00a715.5 below.\n"
    "% ==================================================================\n"
)
# Actually the snippet written above uses ASCII "§" as "\\S" in LaTeX comments?
# Let's check by reading the file verbatim. The snippet file was written as plain
# Python string with "§" UTF-8 characters. Let's just handle whatever is in the file.

# We'll just use the whole snippet file as-is (its END marker stays), and replace
# the §15.5.1 END-marker with an "ABOVE §15.5.1" marker so we avoid duplicates.
anchor_A_new_prefix = (
    "% ==================================================================\n"
    "% END §15.5.1 (rebuilt). §15.5.2 follows below.\n"
    "% ==================================================================\n"
    "\n"
)

assert anchor_A_old in text, "Anchor A (§15.5.1 end marker) not found"
assert text.count(anchor_A_old) == 1, f"Anchor A not unique (count={text.count(anchor_A_old)})"
print("Anchor A: found, unique.")

text2 = text.replace(anchor_A_old, anchor_A_new_prefix + snippet.rstrip() + "\n\n", 1)

# --- Anchor B: update annotation comment in old §15.5.
anchor_B_old = "%       Current status: \\S15.5.1 (rebuilt) integrated,\n%       \\S15.5.2--15.5.6 pending.\n"
anchor_B_new = "%       Current status: \\S15.5.1 and \\S15.5.2 (rebuilt) integrated,\n%       \\S15.5.3--15.5.6 pending.\n"
assert anchor_B_old in text2, "Anchor B (annotation) not found"
assert text2.count(anchor_B_old) == 1, "Anchor B not unique"
print("Anchor B: found, unique.")
text3 = text2.replace(anchor_B_old, anchor_B_new, 1)

# --- Post-invariants
assert text3.count("\\label{subsec:eps_retained_rebuilt}") == 1
assert text3.count("\\label{tab:eps_retained_probes_rebuilt}") == 1
assert text3.count("\\label{eq:eps_hubble_retained}") == 1
assert text3.count("\\label{eq:eps_jwst_retained}") == 1
assert text3.count("\\label{eq:eps_cc_retained}") == 1
assert text3.count("\\label{eq:eps_fsigma8_retained}") == 1
assert text3.count("\\label{eq:eps_isw_retained}") == 1
# Old §15.5 labels must remain intact (untouched):
assert text3.count("\\label{sec:mp_hubble}") == 1
assert text3.count("\\label{eq:epsilon_eff_def}") == 1
assert text3.count("\\label{fig:h0_scan}") == 1
# New §15.5.1 labels still intact:
assert text3.count("\\label{sec:cosmo_constraints_rebuilt}") == 1
assert text3.count("\\label{subsec:eps_def_rebuilt}") == 1

PREPRINT.write_text(text3)
print(f"MD5 post = {md5(PREPRINT)}")
print(f"Size: {len(text)} -> {len(text3)} bytes (delta {len(text3)-len(text):+d})")
print(f"Lines: {text.count(chr(10))} -> {text3.count(chr(10))} (delta {text3.count(chr(10))-text.count(chr(10)):+d})")
print("OK: §15.5.2 integrated; annotation updated.")
