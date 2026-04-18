#!/usr/bin/env python3
"""Phase 1 integration of §15.5.6 (final subsection of §15.5 rebuild)."""
import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/06_s15_5_6_LATEX_SNIPPET.tex"

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

print(f"MD5 pre  = {md5(PREPRINT)}")
text = PREPRINT.read_text()
snippet = SNIPPET.read_text()

# Anchor A: replace §15.5.5 END marker with §15.5.6 content + new END
anchor_A_old = (
    "% ==================================================================\n"
    "% END §15.5.5 (rebuilt). §15.5.6 will be inserted here in a\n"
    "% subsequent step. DO NOT REMOVE existing §15.5 below.\n"
    "% ==================================================================\n"
)
assert anchor_A_old in text, "Anchor A not found"
assert text.count(anchor_A_old) == 1, "Anchor A not unique"
print("Anchor A: found, unique.")

anchor_A_new = (
    "% ==================================================================\n"
    "% END §15.5.5 (rebuilt). §15.5.6 follows below.\n"
    "% ==================================================================\n"
    "\n"
    + snippet.rstrip() + "\n\n"
)
text2 = text.replace(anchor_A_old, anchor_A_new, 1)

# Anchor B: update status line to reflect Phase 1 complete
anchor_B_old = (
    "%       Current status: \\S15.5.1--\\S15.5.5 (rebuilt) integrated,\n"
    "%       \\S15.5.6 pending.\n"
)
anchor_B_new = (
    "%       Current status: \\S15.5.1--\\S15.5.6 (rebuilt) integrated.\n"
    "%       Phase 1 of the rebuild complete; Phase 3 switchover pending.\n"
)
assert anchor_B_old in text2, "Anchor B not found"
assert text2.count(anchor_B_old) == 1, "Anchor B not unique"
print("Anchor B: found, unique.")
text3 = text2.replace(anchor_B_old, anchor_B_new, 1)

# Invariants: new labels resolve, old preserved
assert text3.count("\\label{subsec:eps_outlook_rebuilt}") == 1
assert text3.count("\\label{op:hubble_derive}") == 1
# Sanity: all 6 rebuilt subsection labels present exactly once
for lab in [
    "subsec:eps_def_rebuilt",
    "subsec:eps_retained_rebuilt",
    "subsec:eps_joint_band_rebuilt",
    "subsec:eps_excluded_rebuilt",
    "subsec:eps_comparison_rebuilt",
    "subsec:eps_outlook_rebuilt",
]:
    assert text3.count(f"\\label{{{lab}}}") == 1, f"label {lab} count != 1"

# Legacy-number + GPT-r13 guard on new §15.5.6 block
new_block_start = text3.find("subsec:eps_outlook_rebuilt")
new_block_end = text3.find("END §15.5.6 (rebuilt)")
assert new_block_start != -1 and new_block_end != -1
new_block = text3[new_block_start:new_block_end]
forbidden_tokens = [
    # User directive: no legacy numbers
    "0.010", "0.012", "$0.01$", "3\\%", "2.85", "2.90", "69 km", "69~km",
    # GPT r13 explicitly removed:
    "without fine-tuning",
    "This closes the rebuilt",
    # Over-claims flagged in previous rounds:
    "derived structurally",
    "independent observations",
]
for tok in forbidden_tokens:
    assert tok not in new_block, f"FORBIDDEN token in §15.5.6: {tok!r}"
print("All guards OK.")

PREPRINT.write_text(text3)
print(f"MD5 post = {md5(PREPRINT)}")
print(f"Size: {len(text)} -> {len(text3)} (delta {len(text3)-len(text):+d})")
print(f"Lines: {text.count(chr(10))} -> {text3.count(chr(10))} (delta {text3.count(chr(10))-text.count(chr(10)):+d})")
print("OK: §15.5.6 integrated. §15.5 rebuild Phase 1 COMPLETE.")
