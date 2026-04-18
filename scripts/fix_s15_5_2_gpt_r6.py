#!/usr/bin/env python3
"""GPT round 6 corrections applied directly to §15.5.2 in preprint + snippet file.

8 edits:
1. Remove CCHP/Freedman sentence from Probe 1
2. Add 'one-sided = upper edges after prior, not refits' note after Two-sided distinction
3. Unify Probe 3,4,5 language: 'we therefore report this channel as a one-sided upper bound:'
4. Probe 5: 'raw central' -> 'raw likelihood maximum lies near...'
5. Probe 2: 'yields' -> 'is translated here into'
6. Probe 2 end: soften 'binding lower bound' -> 'will become the lower edge...'
7. Consistency-window final sentence added
8. Table caption: 'analysis' -> 'analysis layer'
"""
import hashlib
from pathlib import Path

def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()

def apply_edits(path, edits):
    text = path.read_text()
    for i, (old, new) in enumerate(edits, 1):
        assert old in text, f"Edit {i}: anchor not found"
        assert text.count(old) == 1, f"Edit {i}: anchor not unique (count={text.count(old)})"
        text = text.replace(old, new, 1)
    path.write_text(text)
    return md5(path)

# --- 8 edits as (old, new) pairs ---
EDITS = [
    # 1. Remove CCHP/Freedman sentence from Probe 1
    (
        "define an observed tension of $\\sim 5\\sigma$.\n"
        "Recent CCHP/JWST determinations fall near\n"
        "$H_0 \\sim 70~\\mathrm{km\\,s^{-1}\\,Mpc^{-1}}$~\\cite{Freedman2024},\n"
        "intermediate between the two.\n"
        "The effective distance-ratio proxy",
        "define an observed tension of $\\sim 5\\sigma$.\n"
        "The effective distance-ratio proxy",
    ),
    # 2. Add methodological note after Two-sided vs upper-bound distinction paragraph
    (
        "reported here as one-sided upper bounds under the physical prior\n"
        "$\\varepsilon\\geq 0$ introduced in \\S\\ref{subsec:eps_def_rebuilt}.\n"
        "\n"
        "\\paragraph{Probe 1",
        "reported here as one-sided upper bounds under the physical prior\n"
        "$\\varepsilon\\geq 0$ introduced in \\S\\ref{subsec:eps_def_rebuilt}.\n"
        "In the one-sided cases quoted below, the reported $1\\sigma$ and\n"
        "$2\\sigma$ bounds are the upper edges of the corresponding raw\n"
        "intervals after imposing the physical prior $\\varepsilon \\geq 0$;\n"
        "they are not separate positive-domain refits.\n"
        "\n"
        "\\paragraph{Probe 1",
    ),
    # 5. Probe 2: 'yields' -> 'is translated here into'
    (
        "without full growth-ODE integration or halo-to-stellar-mass\n"
        "mapping, yields a two-sided effective interval centred at",
        "without full growth-ODE integration or halo-to-stellar-mass\n"
        "mapping, is translated here into a two-sided effective interval centred at",
    ),
    # 6. Probe 2 end softening
    (
        "halo-to-stellar-mass systematics propagated end-to-end. The lower edge\n"
        "$\\varepsilon=0.029$ is the binding lower bound of the joint effective\n"
        "band reported in \\S15.5.3.",
        "halo-to-stellar-mass systematics propagated end-to-end. In the present\n"
        "five-probe comparison, the lower edge $\\varepsilon = 0.029$ will\n"
        "become the lower edge of the joint effective band discussed in\n"
        "\\S15.5.3.",
    ),
    # 3a. Probe 3: language unification
    (
        "The raw\n"
        "best-fit $\\varepsilon = 0.006$ is compatible with $\\varepsilon=0$;\n"
        "under the physical prior the probe enters as a one-sided upper bound",
        "The raw\n"
        "best-fit $\\varepsilon = 0.006$ is compatible with $\\varepsilon=0$;\n"
        "under the physical prior we therefore report this channel as a one-sided upper bound:",
    ),
    # 3b. Probe 4: language unification
    (
        "without a physically meaningful lower branch in the present ECT\n"
        "interpretation; under the physical prior this channel is therefore\n"
        "reported as a one-sided upper bound",
        "without a physically meaningful lower branch in the present ECT\n"
        "interpretation; under the physical prior we therefore report this\n"
        "channel as a one-sided upper bound:",
    ),
    # 3c + 4. Probe 5: language unification + raw likelihood maximum
    (
        "under $\\Lambda$CDM-background Limber weights. The raw central\n"
        "$\\varepsilon\\approx -0.007$ is compatible with $\\varepsilon=0$\n"
        "within a large $\\sigma$; under the physical prior the probe enters as\n"
        "a one-sided upper bound",
        "under $\\Lambda$CDM-background Limber weights. The raw likelihood\n"
        "maximum lies near $\\varepsilon \\approx -0.007$ and remains compatible\n"
        "with $\\varepsilon = 0$ within a broad uncertainty; under the physical\n"
        "prior we therefore report this channel as a one-sided upper bound:",
    ),
    # 7. Consistency-window final sentence
    (
        "partially overlap in their dependence on late-time growth or potential\n"
        "evolution.\n"
        "\n"
        "\\paragraph{Bridge.}",
        "partially overlap in their dependence on late-time growth or potential\n"
        "evolution. The retained five-probe comparison should thus be read as a\n"
        "structured consistency test of a common effective deformation layer,\n"
        "not as a claim of strict statistical independence.\n"
        "\n"
        "\\paragraph{Bridge.}",
    ),
    # 8. Table caption: add 'layer'
    (
        "Retained five-probe set for the present effective\n"
        "uniform-$\\varepsilon$ analysis. ``Primary''",
        "Retained five-probe set for the present effective\n"
        "uniform-$\\varepsilon$ analysis layer. ``Primary''",
    ),
]

for p in [
    Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/ECT_preprint.tex"),
    Path("/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/proposals/drafts_for_integration/02_s15_5_2_LATEX_SNIPPET.tex"),
]:
    print(f"--- {p.name} (pre md5={md5(p)[:8]}) ---")
    post = apply_edits(p, EDITS)
    print(f"    post md5={post[:8]} ... 8 edits OK")
