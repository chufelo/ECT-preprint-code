#!/usr/bin/env python3
"""
INSPIRE-HEP -> references.bib helper for the ECT project.

Fetches BibTeX from INSPIRE-HEP and appends it to references.bib, deduplicating
by BibTeX key. Pure standard library (urllib) -- runs with any python3, no pip
install required.

Usage:
    python3 inspire_to_bib.py arxiv:2401.12345
    python3 inspire_to_bib.py --doi 10.1103/PhysRevD.108.123456
    python3 inspire_to_bib.py "Weinberg cosmological constant problem"
    python3 inspire_to_bib.py arxiv:2401.12345 --dry-run
    python3 inspire_to_bib.py arxiv:2401.12345 --bib /path/to/references.bib

Rule (1): run this the moment a new source is cited, so references.bib stays the
single source of truth. Never paste raw \\bibitem; references.bib only.
"""
import argparse, os, re, ssl, sys, urllib.parse, urllib.request

DEFAULT_BIB = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/references.bib"
API = "https://inspirehep.net/api/literature"
CA_CANDIDATES = (
    "/opt/homebrew/etc/ca-certificates/cert.pem",
    "/opt/homebrew/etc/openssl@3/cert.pem",
    "/etc/ssl/cert.pem",
)


def ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    for p in CA_CANDIDATES:
        if os.path.exists(p):
            return ssl.create_default_context(cafile=p)
    return ssl.create_default_context()


def fetch_bibtex(query, size=1):
    url = API + "?" + urllib.parse.urlencode({"q": query, "size": size})
    req = urllib.request.Request(url, headers={
        "Accept": "application/x-bibtex",
        "User-Agent": "ECT-inspire-to-bib/1.0",
    })
    with urllib.request.urlopen(req, timeout=30, context=ssl_ctx()) as r:
        return r.read().decode("utf-8", "replace").strip()


def bib_keys(text):
    return set(re.findall(r"@\w+\{\s*([^,\s]+)\s*,", text))


def main():
    p = argparse.ArgumentParser(description="Append INSPIRE BibTeX to references.bib")
    p.add_argument("query", help="arxiv:ID, free text, or use --doi")
    p.add_argument("--doi", help="treat the query as a DOI")
    p.add_argument("--bib", default=DEFAULT_BIB)
    p.add_argument("--size", type=int, default=1, help="max records to fetch")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    q = ("doi:" + a.doi) if a.doi else a.query
    try:
        bibtex = fetch_bibtex(q, a.size)
    except Exception as e:
        sys.exit("INSPIRE fetch failed: %s" % e)
    if not bibtex or "@" not in bibtex:
        sys.exit("No BibTeX returned for query: %s" % q)

    new_keys = bib_keys(bibtex)
    existing = ""
    if os.path.exists(a.bib):
        with open(a.bib, encoding="utf-8") as f:
            existing = f.read()
    have = bib_keys(existing)

    dup = new_keys & have
    fresh = new_keys - have
    print("Fetched keys: %s" % ", ".join(sorted(new_keys)))
    if dup:
        print("Already present (skipped): %s" % ", ".join(sorted(dup)))
    if not fresh:
        print("Nothing new to add.")
        return
    print("New keys: %s" % ", ".join(sorted(fresh)))

    if a.dry_run:
        print("--- BibTeX (dry run, not written) ---")
        print(bibtex)
        return

    entries = re.split(r"(?=@\w+\{)", bibtex)
    to_add = [e for e in entries if bib_keys(e) & fresh]
    block = "\n".join(s.strip() for s in to_add if s.strip())
    with open(a.bib, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n" + block + "\n")
    n = len(to_add)
    print("Appended %d entr%s to %s" % (n, "y" if n == 1 else "ies", a.bib))


if __name__ == "__main__":
    main()
