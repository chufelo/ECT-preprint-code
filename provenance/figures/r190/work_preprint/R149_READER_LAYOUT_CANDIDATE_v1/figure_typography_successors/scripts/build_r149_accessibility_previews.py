#!/usr/bin/env python3
"""Create deterministic grayscale and CVD previews for R149 successor PDFs.

The previews are review artefacts only.  They do not replace or modify the
publication PDFs and write exclusively below the R149 successor component.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
OUTPUTS = COMPONENT / "outputs"
PREVIEWS = COMPONENT / "previews"

MATRICES = {
    "DEUTERANOPIA": np.asarray([[0.367, 0.861, -0.228], [0.280, 0.673, 0.047], [-0.012, 0.043, 0.969]]),
    "PROTANOPIA": np.asarray([[0.152, 1.053, -0.205], [0.115, 0.786, 0.099], [-0.004, -0.048, 1.052]]),
    "TRITANOPIA": np.asarray([[1.256, -0.077, -0.179], [-0.079, 0.931, 0.148], [0.005, 0.691, 0.304]]),
}


def render_pdf(pdf: Path, png: Path) -> None:
    subprocess.run(
        ["gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pngalpha", "-r180", f"-sOutputFile={png}", str(pdf)],
        check=True,
    )


def transform(source: Path, target: Path, matrix: np.ndarray | None) -> None:
    with Image.open(source) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    if matrix is None:
        # Rec. 709 luminance, replicated into RGB for an ordinary grayscale preview.
        y = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        out = np.stack((y, y, y), axis=-1)
    else:
        out = np.clip(rgb @ matrix.T, 0.0, 1.0)
    Image.fromarray(np.rint(out * 255.0).astype(np.uint8), mode="RGB").save(target, format="PNG", compress_level=9, optimize=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=PREVIEWS)
    args = parser.parse_args()
    target = args.output_dir.resolve()
    target.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(OUTPUTS.glob("*.pdf")):
        base = target / pdf.stem
        color = base.with_suffix(".png")
        render_pdf(pdf, color)
        transform(color, target / f"{pdf.stem}_GRAYSAFE.png", None)
        for name, matrix in MATRICES.items():
            transform(color, target / f"{pdf.stem}_{name}.png", matrix)


if __name__ == "__main__":
    main()
