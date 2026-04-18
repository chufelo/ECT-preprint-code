#!/usr/bin/env python3
"""Phase 2 Step 1: insert §15.5 Opening (intro) before §15.5.1."""
import hashlib
from pathlib import Path

LATEX = Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex")
PREPRINT = LATEX / "ECT_preprint.tex"
SNIPPET = LATEX / "proposals/drafts_for_integration/00_s15_5_opening_SNIPPET.tex"

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

print(f"MD5 pre  = {md5(PREPRINT)}")
text = PREPRINT.read_text()
snippet = SNIPPET.read_text()

# Anchor: insert snippet BETWEEN \label{sec:cosmo_constraints_rebuilt}
# (line 20377) and the start of §15.5.1 (line 20380: \subsubsection*).
# Use a multi-line anchor bridging the label and the first subsubsection
# that is guaranteed unique.

anchor_old = """\\label{sec:cosmo_constraints_rebuilt}

\\subsubsection*{\\normalfont\\textbf{15.5.1 \\quad Structural definition of the effective deformation parameter}}
\\label{subsec:eps_def_rebuilt}"""

assert anchor_old in text, "Anchor not found — check whitespace/escaping"
assert text.count(anchor_old) == 1, "Anchor not unique"
print("Anchor: found, unique.")

anchor_new = (
    "\\label{sec:cosmo_constraints_rebuilt}\n\n"
    + snippet.rstrip() + "\n\n"
    + "\\subsubsection*{\\normalfont\\textbf{15.5.1 \\quad Structural definition of the effective deformation parameter}}\n"
    + "\\label{subsec:eps_def_rebuilt}"
)
text2 = text.replace(anchor_old, anchor_new, 1)

# Invariants check — opening now contains the paragraph markers
assert "The previous part of Chapter~15" in text2
assert "not independent enough to serve" in text2

# Guard: forbidden tokens in the opening block
opening_start = text2.find("The previous part of Chapter~15")
opening_end = text2.find("not independent enough to serve")
assert opening_start != -1 and opening_end != -1
opening_block = text2[opening_start:opening_end]
for forbidden in [
    # Legacy numbers (binding user directive)
    "0.010", "0.012", "3\\%", "2.85", "2.90", "69 km", "69~km",
    # Specific band endpoints should not appear in opening (they are §15.5.3)
    "0.029", "0.036", "0.021", "0.042", "0.032",
    # GPT r14 explicitly removed:
    "arising from the three-stage condensate closure",
    "five largely independent empirical constraints",
]:
    assert forbidden not in opening_block, f"FORBIDDEN token in opening: {forbidden!r}"
print("All guards OK.")

PREPRINT.write_text(text2)
print(f"MD5 post = {md5(PREPRINT)}")
print(f"Size: {len(text)} -> {len(text2)} (delta {len(text2)-len(text):+d})")
print(f"Lines: {text.count(chr(10))} -> {text2.count(chr(10))} (delta {text2.count(chr(10))-text.count(chr(10)):+d})")
print("OK: §15.5 Opening integrated.")
