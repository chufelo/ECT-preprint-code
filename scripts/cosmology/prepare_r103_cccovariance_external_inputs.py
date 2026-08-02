#!/usr/bin/env python3
"""Prepare the two hash-gated R103 CCcovariance external inputs.

The upstream files are not redistributed by this repository.  This helper
accepts a user-supplied checkout of the declared upstream commit, verifies the
upstream bytes, adds the frozen provenance header used by R103, and writes the
two logical paths below a separate external-input root.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


COMMIT = "881413330a7f1e1e5203607d6964db49b4c6c461"
FILES = (
    {
        "upstream": "data/HzTable_MM_BC03.dat",
        "upstream_sha256": (
            "32ce92caf251cb60a7a837c71f1856bea2b44fa5c1041f85410d11cb8164da98"
        ),
        "logical": (
            "data/cosmology_r103/"
            "OFFICIAL_CCcovariance_HzTable_MM_BC03_commit88141333.dat"
        ),
        "prepared_sha256": (
            "0fa5e906dc0a2d58d63fdba746bfe2fbb5610a1d54e896b450795f323997fb01"
        ),
        # Preserve the exact historical R103 comment-header whitespace.  It is
        # semantically inert because NumPy treats the line as a comment.
        "header_replacement": (
            b"# z\tHz\terrHz\tstat_contr\tmet_contr\treference\n",
            b"# z\tHz\terrHz\t\tstat_contr\tmet_contr\treference\n",
        ),
    },
    {
        "upstream": "data/data_MM20.dat",
        "upstream_sha256": (
            "577ac2f346e346fe7cf94daa7b7000c05d04ebc8a029cda31e0d8643b956a485"
        ),
        "logical": (
            "data/cosmology_r103/"
            "OFFICIAL_CCcovariance_data_MM20_commit88141333.dat"
        ),
        "prepared_sha256": (
            "8c88a10a0cf69620937da6c51c0c5a925377c1b514404e91ea9dae3263123c07"
        ),
        "header_replacement": None,
    },
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def prepare(source_root: Path, external_root: Path) -> None:
    for spec in FILES:
        upstream = source_root / str(spec["upstream"])
        if not upstream.is_file():
            raise SystemExit(f"missing upstream input: {upstream}")
        raw = upstream.read_bytes()
        actual_upstream = sha256_bytes(raw)
        if actual_upstream != spec["upstream_sha256"]:
            raise SystemExit(
                f"upstream hash mismatch for {spec['upstream']}: "
                f"{actual_upstream} != {spec['upstream_sha256']}"
            )

        replacement = spec["header_replacement"]
        if replacement is not None:
            old, new = replacement
            if not raw.startswith(old):
                raise SystemExit(
                    f"unexpected upstream header in {spec['upstream']}"
                )
            raw = new + raw[len(old) :]

        prefix = (
            f"# Exact snapshot of {spec['upstream']} from\n"
            "# https://gitlab.com/mmoresco/CCcovariance.git commit\n"
            f"# {COMMIT}\n"
            f"# Original SHA-256: {spec['upstream_sha256']}\n"
        ).encode("utf-8")
        prepared = prefix + raw
        actual_prepared = sha256_bytes(prepared)
        if actual_prepared != spec["prepared_sha256"]:
            raise SystemExit(
                f"prepared hash mismatch for {spec['logical']}: "
                f"{actual_prepared} != {spec['prepared_sha256']}"
            )

        destination = external_root / str(spec["logical"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(prepared)
        print(f"PASS {spec['logical']} {actual_prepared}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Checkout of CCcovariance at the declared commit",
    )
    parser.add_argument(
        "--external-input-root",
        type=Path,
        required=True,
        help="Separate root later supplied through ECT_EXTERNAL_INPUT_ROOT",
    )
    args = parser.parse_args()
    prepare(args.source_root.resolve(), args.external_input_root.resolve())


if __name__ == "__main__":
    main()
