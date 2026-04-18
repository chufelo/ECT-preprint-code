#!/usr/bin/env python3
"""Phase 1 integration of §15.5.3 (final, post GPT round 7 + user directive)."""
import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/03_s15_5_3_LATEX_SNIPPET.tex"

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

print(f"MD5 pre  = {md5(PREPRINT)}")
text = PREPRINT.read_text()
snippet = SNIPPET.read_text()

# Anchor A: replace §15.5.2 END marker with §15.5.3 content + new END marker
anchor_A_old = (
    "% ==================================================================\n"
    "% END §15.5.2 (rebuilt). §15.5.3--15.5.6 will be inserted here in\n"
    "% subsequent steps. DO NOT REMOVE existing §15.5 below.\n"
    "% ==================================================================\n"
)
assert anchor_A_old in text, "Anchor A not found"
assert text.count(anchor_A_old) == 1, "Anchor A not unique"
print("Anchor A: found, unique.")

anchor_A_new = (
    "% ==================================================================\n"
    "% END §15.5.2 (rebuilt). §15.5.3 follows below.\n"
    "% ==================================================================\n"
    "\n"
    + snippet.rstrip() + "\n\n"
)
text2 = text.replace(anchor_A_old, anchor_A_new, 1)

# Anchor B: update status line in old §15.5 annotation
anchor_B_old = (
    "%       Current status: \\S15.5.1 and \\S15.5.2 (rebuilt) integrated,\n"
    "%       \\S15.5.3--15.5.6 pending.\n"
)
anchor_B_new = (
    "%       Current status: \\S15.5.1--\\S15.5.3 (rebuilt) integrated,\n"
    "%       \\S15.5.4--15.5.6 pending.\n"
)
assert anchor_B_old in text2, "Anchor B not found"
assert text2.count(anchor_B_old) == 1, "Anchor B not unique"
print("Anchor B: found, unique.")
text3 = text2.replace(anchor_B_old, anchor_B_new, 1)

# Post-invariants
assert text3.count("\\label{subsec:eps_joint_band_rebuilt}") == 1
assert text3.count("\\label{eq:eps_joint_band_rebuilt}") == 1
assert text3.count("\\label{tab:eps_scaling_benchmark_B}") == 1
# Guard: no legacy numbers sneaking into new block
new_block_start = text3.find("subsec:eps_joint_band_rebuilt")
new_block_end = text3.find("END §15.5.3 (rebuilt)")
assert new_block_start != -1 and new_block_end != -1
new_block = text3[new_block_start:new_block_end]
for forbidden in ["0.010", "0.012", "$0.01$", "3\\%", "2.85", "2.90", "2.8\\%", "69~\\text",
                  "69\\,\\mathrm", "69 km", "69~km", "epsilon_diagram.html",
                  "fig_epsilon_constraints", "few-per-cent"]:
    assert forbidden not in new_block, f"FORBIDDEN token found in new §15.5.3: {forbidden!r}"
print("All legacy-number guards OK: none present in §15.5.3.")

PREPRINT.write_text(text3)
print(f"MD5 post = {md5(PREPRINT)}")
print(f"Size: {len(text)} -> {len(text3)} bytes (delta {len(text3)-len(text):+d})")
print(f"Lines: {text.count(chr(10))} -> {text3.count(chr(10))} (delta {text3.count(chr(10))-text.count(chr(10)):+d})")
print("OK: §15.5.3 integrated; annotation updated.")
