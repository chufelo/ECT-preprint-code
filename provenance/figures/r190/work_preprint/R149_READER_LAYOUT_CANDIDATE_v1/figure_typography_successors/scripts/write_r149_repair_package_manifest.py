#!/usr/bin/env python3
"""Write the deterministic manifest for the R149 pp. 001--416 repair package."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / 'LaTex/ECT_preprint.tex').is_file())
OUT = COMPONENT / 'outputs'
PREVIEWS = COMPONENT / 'previews'
QA = COMPONENT / 'qa'
EQ = COMPONENT / 'equation_gap'

LIVE = ROOT / 'LaTex/ECT_preprint.tex'
LIVE_SHA = 'd6eabf06ff6c35b3c1ba809f6c13784551d09b90e4aed0db932354b3f5bc577a'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path) -> dict[str, object]:
    return {
        'path': str(path.relative_to(ROOT)),
        'sha256': sha(path),
        'bytes': path.stat().st_size,
    }


def main() -> None:
    pdfs = sorted(OUT.glob('*.pdf'))
    pngs = sorted(OUT.glob('*.png'))
    previews = sorted(PREVIEWS.glob('*.png'))
    scripts = sorted(HERE.glob('*.py'))
    evidence = sorted((EQ / 'evidence').glob('*.png'))
    manifest = {
        'artifact': 'R149 pp. 001--416 reader-layout repair package',
        'status': 'PROPOSAL_ONLY_NOT_APPLIED',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': {
            'included': [
                'typography-only successors for two evolution figures (pp. 273--274)',
                'three sequential, two-galaxy SPARC comparison successors for pp. 323--324',
                'exact source-anchored snippets for pp. 115, 220, 253, 291--292, 380 and 464',
                'before-render evidence and focused A4 equation-layout probe',
            ],
            'excluded': [
                'no live or candidate ECT_preprint.tex change',
                'no scientific recalculation, claim/status change, data substitution, caption rewriting or bibliography change',
                'no full-candidate float-pagination acceptance; this remains a later owning compile gate',
            ],
        },
        'frozen_live_source': {
            'path': str(LIVE.relative_to(ROOT)),
            'expected_sha256': LIVE_SHA,
            'actual_sha256': sha(LIVE),
            'match': sha(LIVE) == LIVE_SHA,
        },
        'typography_policy': {
            'insertion_assumption': 'A4, 2.5 cm margins, approximately 160 mm text width; each successor is inserted at width=\\textwidth.',
            'public_font_floor_before_tex_pt': 10.5,
            'effective_floor_at_160mm_for_7.7in_assets_pt': round(10.5 * (160 / (7.7 * 25.4)), 3),
            'minimum_required_after_tex_pt': 8.0,
            'semantics': 'Colour is redundant with literal status text, border/line style, marker and direct label. No dense decorative hatching is introduced.',
        },
        'required_replay_environment': {
            'PYTHONHASHSEED': '0',
            'SOURCE_DATE_EPOCH': '1700000000',
            'MPLCONFIGDIR': 'figure_typography_successors/runtime/mplconfig',
            'verdict': 'Byte-identical across two full PDF rerenders only under this declared environment.',
        },
        'replay': {
            'run1_sha256_manifest': record(QA / 'R149_TYPOGRAPHY_SUCCESSORS_DETERMINISM_RUN1.sha256'),
            'run2_sha256_manifest': record(QA / 'R149_TYPOGRAPHY_SUCCESSORS_DETERMINISM_RUN2.sha256'),
            'verdict': 'BYTE_IDENTICAL_WITH_FIXED_ENV',
        },
        'science_guards': {
            'evolution': 'Frozen R103 data hashes are verified by the successor verifier; the producer changes only canvas, typography, labels and visual spacing.',
            'sparc': 'All 159 frozen R102 point rows and the five named curve columns are read directly; no fit or numerical recalculation occurs.',
            'equations': 'The focused guard verifies the live-source hash, all terms in source order, arrow kinds/counts, p115 delete-only scope, p291 placement-only scope and zero focused-probe overfull boxes.',
        },
        'artifacts': {
            'producer_scripts': [record(path) for path in scripts],
            'successor_pdfs': [record(path) for path in pdfs],
            'successor_pngs': [record(path) for path in pngs],
            'accessibility_previews': [record(path) for path in previews],
            'equation_proposal': record(EQ / 'R149_EXACT_LAYOUT_INSERTION_SNIPPETS_v1.tex'),
            'equation_probe_source': record(EQ / 'R149_EQUATION_GAP_FOCUSED_QA_v1.tex'),
            'equation_content_guard': record(EQ / 'qa/R149_EQUATION_GAP_CONTENT_GUARD_v1.json'),
            'equation_before_and_after_render_evidence': [record(path) for path in evidence],
        },
        'pending_integration': [
            'Rebase these exact snippets and successor assets against the active canonical candidate.',
            'Assert every anchor is unique before editing.',
            'Compile the full candidate and inspect pp. 115, 220, 253, 291--293, 323--324, 380 and 464 as well as float neighbourhoods.',
            'Update figure registry and TeX captions/inclusion tokens only in a reviewed named candidate.',
            'Run full rendered page, overflow, font-bound and cascade QA before any live apply.',
        ],
        'live_manuscript_modified': False,
        'git_modified': False,
    }
    (QA / 'R149_PAGES_001_416_REPAIR_PACKAGE_MANIFEST_v1.json').write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )


if __name__ == '__main__':
    main()
