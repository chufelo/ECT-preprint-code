# R190 successor release package

Internal preparation identifier: `R190`.

Status: `DRAFT_NOT_TAGGED_NOT_RELEASED`.

`R190` is not a public version number. This candidate has no release date, no
new Zenodo record ID, and no version-specific DOI. It is a successor to the
historical R148 workspace package, which remains unchanged outside the
current public-tree allowlist. Predecessor public record facts needed here are
frozen in `KNOWN_RECORDS_SNAPSHOT.json`.

## Record owners

This package prepares possible new versions under two existing concept
records:

- technical preprint: `10.5281/zenodo.18917929`;
- narrative companion: `10.5281/zenodo.19430795`.

Concept DOIs identify evolving records, not exact revisions. The last
read-only predecessor observation is frozen in
`KNOWN_RECORDS_SNAPSHOT.json`. It must be refreshed and reviewed before an
external transaction; the snapshot does not claim perpetual currentness.

## Contents

- `PREPRINT_ZENODO_METADATA.json` and
  `COMPANION_ZENODO_METADATA.json` — draft metadata with null version, date,
  new record ID, and new version DOI;
- `KNOWN_RECORDS_SNAPSHOT.json` — dated, read-only predecessor facts;
- `ZENODO_UPLOAD_ALLOWLIST.json` — exactly one PDF per manuscript record;
- `RELEASE_INPUT_CONTRACT.json` — required sources, PDFs, BBLs, reports,
  predecessor evidence, and path exclusions;
- `validate_release.py` — offline schema, manifest, and tag-attestation gates;
- `freeze_release.py` — deterministic pre-tag manifest and post-tag local Git
  attestation;
- `build_upload_payloads.py` — offline staging from an attested commit;
- `build_public_repository_manifest.py` — deterministic exact-path/hash
  inventory and English standalone-replay validation owner;
- `RELEASE_NOTES.md` — status-separated draft notes; and
- `build_reports/` — accepted English build reports; and
- `validation/R190_PUBLIC_REPOSITORY_PATH_MANIFEST.json` plus
  `validation/R190_PUBLIC_REPOSITORY_VALIDATION.json` — the final local
  repository-surface and clean-copy evidence, without a release claim.

## Draft validation

From the repository root:

```bash
python3 release/zenodo/R190/validate_release.py
```

Expected candidate result:

```text
PASS_LOCAL_SCHEMA_ONLY
```

This result establishes only local schema and policy consistency.

The exact public-tree inventory is regenerated independently with:

```bash
python3 release/zenodo/R190/build_public_repository_manifest.py
```

Its PASS status establishes local English repository alignment only.  It does
not create a tag, contact Zenodo, assign a DOI, upload or publish anything.

## Two-phase freeze

Before Phase A, the chosen public version/date, all validation results, and all
status-bearing files must be reviewed and advanced together to
`RELEASE_CANDIDATE_NOT_RELEASED`; the draft package correctly fails that gate.

The pre-tag manifest binds the scientific artifact set but deliberately has
no commit or tag field:

```bash
python3 release/zenodo/R190/freeze_release.py pretag \
  --repo-root . \
  --output release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --runtime-sidecar .build/zenodo-r190-runtime.json
```

After an explicitly authorised commit and tag exist, a separate attestation
binds the manifest to that immutable local Git object:

```bash
python3 release/zenodo/R190/freeze_release.py attest-tag \
  --repo-root . \
  --pretag-manifest release/zenodo/R190/PRETAG_ARTIFACT_MANIFEST.json \
  --git-commit FULL_40_CHARACTER_COMMIT_SHA \
  --git-tag EXACT_TAG_NAME \
  --output .build/zenodo-r190-tag-attestation.json
```

This avoids the circular claim that a manifest embedded in a commit already
knows the hash of the commit that first contains it.

## Fixed payload policy

- preprint record: `ECT_preprint.pdf` only;
- companion record: `ECT_companion.pdf` only;
- maximum file count per record: one.

The summary, source archive, raw external data, private/work material,
backups, deferred book material, and non-English publication artifacts are
excluded.

## No external side effects

The R190 tools use local files and local Git only. They do not create a commit
or tag, alter a remote repository, call Zenodo, create a draft deposit,
upload, or publish. Every such action requires a separate explicit author
command.
