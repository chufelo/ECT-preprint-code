# R177 Part-II selected-status map, candidate v4

- Date: 2026-07-29
- Status: `CANDIDATE_COMPLETE_NOT_APPLIED`
- Scope: scientific successor of the R168 Part-II map; v4 closes the semantic-source hash embedded in the v3 delta
- Frozen live preprint: SHA-256 `2acbebbaa9c11be535195c6f2b8a0c184eee5dadc2070af252bd87f7eae17217`
- Live manuscript/repository edited: no
- Commit, push or publication: none

## Strongest scientific content

The map preserves the selected Part-II programme and makes six status
boundaries explicit:

1. \(F\) is supplied by the scalar--tensor closure; it is not derived by the
   logarithmic change of amplitude coordinate.
2. \(w_\phi^{\rm bare}\ge-1\) is Level A only inside the supplied
   positive-kinetic stress and under its displayed positivity conditions.
   Observable \(w_{\rm eff}\) is not bounded by that identity and remains Open
   for ECT.
3. The old false arrow from the bare ratio to a physical late source is kept
   as a dashed, tee-terminated, literal `BLOCKED` non-implication.
4. A GR-reference density conversion is separated from the Open
   scalar--tensor late-source owner.
5. The JWST result is a finite nine-node calculation, not a continuous-family
   theorem or abundance solution.
6. The figure is labelled a selected status/dependency map, not the complete
   derivation logic of Part II.

No topic or failed route is silently discarded.  The map is navigation; the
equations and claim ledger remain the scientific owners.

## Hash-bound owners

| Role | Path | SHA-256 |
|---|---|---|
| R168 semantic baseline | `LaTex/figures/source/graphviz/r168_connected_map_semantics_v1/fig24_partII_semantic_successor_r168.gv` | `f1ebf339255d9d1e8c824a53339fe683d89edb919f4a52846c961923b1dfa9d5` |
| R168 topology baseline | `LaTex/data/figures_r168/topology/fig24_partII_topology_r168.json` | `a45704fb23b985d6494215ec5f4fb13590feeebcfa4da8e2f19f99cff70c4a0b` |
| R168 publication asset | `LaTex/figures/r168/logic_maps/partII_a4_reader_r168.pdf` | `ac471afef621d1d912ca4d1c3917f631a256fb4875339d92af9f5997c10596ca` |
| R177 semantic source | `source/fig24_partII_semantic_successor_r177.gv` | `a21756dda12db4d06a163145e1fe540539c0e34b5f0bed5ae6ecfc52a314dbc0` |
| R177 semantic/topology delta | `SEMANTIC_TOPOLOGY_DELTA_R177.json` | `2baefce85520d7951b5b9b076b786975c0f035f04df01c31d145d4cbff496962` |
| Deterministic generator | `build_partII_successor.py` | `8c3d2531baaa7788c58263c70f8fce1865b9ba940144f6fad6731a99cf655ab7` |
| v4 PDF | `candidate_r177_v4/partII_a4_reader_r177_candidate.pdf` | `07a2bde4f707ee143e9e32547cf36f0628f1e3909f72b84ee08604e9c436b43a` |

The semantic delta now embeds the actual source hash `a21756dd...`; the
builder independently guards the delta hash `2baefce8...`.  Candidates v1,
v2 and v3 remain preserved provenance.  V3 produced the same PDF but is
superseded because its delta embedded the older semantic-source hash.

## Reproduction and gates

Command:

```text
python3 research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/partII_successor/build_partII_successor.py \
  --output-root research/derivations/R177_RECOVERY_FROM_LIVE_2acbebba_v1/figures/partII_successor/candidate_r177_v4
```

Results:

- frozen base/source/delta/font guards: PASS;
- semantic nodes: 35/35;
- visible relations: 59/59;
- topology-plus-delta pair multiset: PASS;
- literal status and redundant non-colour channels: PASS;
- blocked non-implication: PASS;
- node overlaps: 0;
- edge-through-third-node crossings: 0;
- one searchable ISO-A4 page: PASS;
- effective node font: 8.479 pt (gate 7.5 pt);
- independent renders: 2;
- byte-identical replay across all 14 build files: PASS;
- final PDF SHA-256 in both renders:
  `07a2bde4f707ee143e9e32547cf36f0628f1e3909f72b84ee08604e9c436b43a`.

Machine evidence:

- `candidate_r177_v4/AUTOMATED_QA.json`, SHA-256 `b2d9c51fd3320c981dc0c1a3a2b26638124a5d4a6a403dfde67b093cce7ab133`;
- `candidate_r177_v4/REPLAY_CHECK.json`, SHA-256 `08177e15d69a7522cdd66924ec1296fba48efd749f8df2d7222a39c6302b62b6`;
- `candidate_r177_v4/manifest.json`, SHA-256 `61e5b8814e79a51c421f3925e0885b8893b351820da37f1de56ce4f5c00850d5`;
- `candidate_r177_v4/SHA256SUMS`, SHA-256 `d0295a1e9f8be2b84bfb4dd04a3c962181551b8bb339c683773ae778441d2a03`.

RGB, grayscale, protan, deutan and tritan views were inspected.  The result is
recorded in `VISUAL_REVIEW_R177_v4.md`.

## Integration boundary

The preservation-first successor assembler may copy this PDF into its local
candidate tree and update exactly the preprint, English companion and Russian
companion candidate paths.  It does not authorise a live edit.

The general figure-registry verifier remains incompatible with the present
registry schema.  This is a release-infrastructure blocker, not a defect in
the deterministic v4 PDF; it must be resolved by a separately governed
registry/verifier change before release readiness can be claimed.
