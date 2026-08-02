# Third-party notices and redistribution boundary

This file records the principal third-party boundaries of the English ECT
publication and reproducibility repository. It is an inventory aid, not a
substitute for the controlling source terms. Terms and upstream availability
can change; verify them at release time.

## Observational and comparison inputs

### SPARC galaxy data

The manuscripts cite and analyse products associated with the SPARC database
described by Lelli, McGaugh, and Schombert (2016) and distributed by the SPARC
project.  The raw catalogue path
`data/MassModels_Lelli2016c.mrt` is a declared external-only logical input in
`EXTERNAL_INPUTS.json` and is not redistributed.  The former
`data/sparc_environment.csv` path is retired and absent from the current
repository.  SPARC-origin or SPARC-derived material that is actually shipped
is confined to the status-labelled `data/hrc_r97/` package and to HRC-generated
tables or figures whose local manifests identify the upstream input.

The ECT licences do not relicense the underlying SPARC catalogue. Raw or
repackaged SPARC products are excluded from the two Zenodo manuscript uploads
and from any source archive unless a path-level review affirmatively records
redistribution permission, required attribution, provenance, and the exact
files approved. Readers should obtain original inputs from the upstream
source and comply with its current terms and citation requirements.

Author-generated derived tables and plots are covered only to the extent that
Valeriy Blagovidov owns the added expression; rights in source data remain
with their owners.

### Cosmology and other external values

`data/cosmology_r103/` includes external chronometer/covariance inputs and
locally generated conditional products. Its README and source-import
manifests, rather than the repository-wide MIT or CC notice, govern the exact
provenance and redistribution decision for each file.

Values attributed to Planck, SH0ES, DESI, LIGO/Virgo/KAGRA, JWST studies,
MICROSCOPE, particle-data compilations, or other cited sources remain
third-party inputs. A comparison, transcription, fit, or reproduction does
not make those measurements ECT-owned and does not establish an ECT-specific
prediction.

## Fonts

The two DejaVu Sans binaries retained inside the frozen R153 figure-provenance
owner keep their upstream font licence.  The controlling notice is included
at `LICENSES/DejaVu-Fonts.txt`.  The superseded R134/R153 working-script trees
and their unused STIX font are not part of the public current-file allowlist.

Any release that includes the font binaries must include and verify the
corresponding notices. The manuscript-only Zenodo PDF payloads do not upload
the font files as separate assets.

## Software dependencies

TeX distributions, BibTeX, Graphviz, Python, NumPy, SciPy, Matplotlib, SymPy,
Pillow, PyMuPDF, pypdf, PyYAML, and other third-party software retain their own
licences. They are dependencies, not recipients of the ECT MIT grant. The
environment file records requested versions but does not redistribute those
packages.

## Quotations, equations, bibliography, and names

Brief quotations and source-attributed equations or values remain subject to
the rights and citation requirements of their sources. Bibliographic entries
are provenance metadata and are not represented as original ECT prose. Names,
marks, institutional labels, and dataset titles remain with their respective
owners.

## Fail-closed archive policy

Before creating any repository archive, inventory every included file as one
of:

- author-owned manuscript/figure material (`CC-BY-4.0`);
- author-owned code (MIT);
- third-party material with an identified licence and satisfied notice;
- external-only input that must be obtained upstream; or
- `MISSING` / unreviewed and therefore excluded.

Do not infer redistribution permission from public web access, Git tracking,
scientific citation, or successful local execution.

## Excluded from the two Zenodo manuscript uploads

The preprint and companion concept records each accept one allowlisted PDF.
The following are excluded:

- the English summary PDF;
- source archives;
- raw or repackaged external datasets;
- font binaries as separate uploads;
- private research notes, backups, work candidates, caches, or chat exports;
- deferred book material; and
- non-English publication sources or artifacts.

The exact machine-readable boundary is
`release/zenodo/R190/ZENODO_UPLOAD_ALLOWLIST.json`.
