#!/usr/bin/env python3
"""Phase 1 integration of §15.5.5 (final, post GPT round 12)."""
import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/05_s15_5_5_LATEX_SNIPPET.tex"

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

print(f"MD5 pre  = {md5(PREPRINT)}")
text = PREPRINT.read_text()
snippet = SNIPPET.read_text()

# Anchor A: replace §15.5.4 END marker with §15.5.5 content + new END
anchor_A_old = (
    "% ==================================================================\n"
    "% END §15.5.4 (rebuilt). §15.5.5--15.5.6 will be inserted here in\n"
    "% subsequent steps. DO NOT REMOVE existing §15.5 below.\n"
    "% ==================================================================\n"
)
assert anchor_A_old in text, "Anchor A not found"
assert text.count(anchor_A_old) == 1
print("Anchor A: found, unique.")

anchor_A_new = (
    "% ==================================================================\n"
    "% END §15.5.4 (rebuilt). §15.5.5 follows below.\n"
    "% ==================================================================\n"
    "\n"
    + snippet.rstrip() + "\n\n"
)
text2 = text.replace(anchor_A_old, anchor_A_new, 1)

# Anchor B: update status line
anchor_B_old = (
    "%       Current status: \\S15.5.1--\\S15.5.4 (rebuilt) integrated,\n"
    "%       \\S15.5.5--15.5.6 pending.\n"
)
anchor_B_new = (
    "%       Current status: \\S15.5.1--\\S15.5.5 (rebuilt) integrated,\n"
    "%       \\S15.5.6 pending.\n"
)
assert anchor_B_old in text2, "Anchor B not found"
assert text2.count(anchor_B_old) == 1
print("Anchor B: found, unique.")
text3 = text2.replace(anchor_B_old, anchor_B_new, 1)

# Invariants
assert text3.count("\\label{subsec:eps_comparison_rebuilt}") == 1

# Legacy-number + forbidden-token guard on new §15.5.5 block
new_block_start = text3.find("subsec:eps_comparison_rebuilt")
new_block_end = text3.find("END §15.5.5 (rebuilt)")
assert new_block_start != -1 and new_block_end != -1
new_block = text3[new_block_start:new_block_end]
for forbidden in [
    "0.010", "0.012", "$0.01$", "3\\%", "2.85", "2.90", "69 km",
    "epsilon_diagram.html", "fig_epsilon_constraints",
    "DESI2024",  # GPT r12 removed this cite from §15.5.5
    "derived structurally",  # GPT r12 removed overclaim
    "independent observations",  # GPT r12 removed overclaim
    "galactic-scale motivation",  # GPT r12 removed imprecise f(R) framing
    "not designed to simultaneously",  # GPT r12 softened EDE
]:
    assert forbidden not in new_block, f"FORBIDDEN token in §15.5.5: {forbidden!r}"
print("All guards OK.")

PREPRINT.write_text(text3)
print(f"MD5 post = {md5(PREPRINT)}")
print(f"Size: {len(text)} -> {len(text3)} (delta {len(text3)-len(text):+d})")
print(f"Lines: {text.count(chr(10))} -> {text3.count(chr(10))} (delta {text3.count(chr(10))-text.count(chr(10)):+d})")
print("OK: §15.5.5 integrated.")
