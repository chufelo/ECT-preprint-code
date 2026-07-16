#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
if [[ -d "$WORKSPACE_ROOT/.workspace" ]]; then
  BUILD_DIR="$WORKSPACE_ROOT/.workspace/build/preprint"
else
  BUILD_DIR="$REPO_ROOT/.build/preprint"
fi
mkdir -p "$BUILD_DIR"
cd "$REPO_ROOT"

PDFLATEX="${PDFLATEX:-/Library/TeX/texbin/pdflatex}"
BIBTEX="${BIBTEX:-/Library/TeX/texbin/bibtex}"
LATEX_PASSES="${LATEX_PASSES:-${PASSES:-4}}"
PREVIOUS_PAGES="${PREVIOUS_PAGES:-}"

if ! [[ "$LATEX_PASSES" =~ ^[0-9]+$ ]] || (( LATEX_PASSES < 3 )); then
  printf 'LATEX_PASSES must be an integer >= 3 (received %s)\n' "$LATEX_PASSES" >&2
  exit 2
fi

run_pass() {
  local pass="$1"
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error \
    -output-directory="$BUILD_DIR" ECT_preprint.tex \
    >"$BUILD_DIR/pass_${pass}.stdout.log" 2>&1
}

run_pass 1
(cd "$BUILD_DIR" && BIBINPUTS="$REPO_ROOT:" "$BIBTEX" ECT_preprint) \
  >"$BUILD_DIR/bibtex.stdout.log" 2>&1
for ((pass = 2; pass <= LATEX_PASSES; pass++)); do
  run_pass "$pass"
done

LOG="$BUILD_DIR/ECT_preprint.log"
ERRORS="$(grep -c '^!' "$LOG" || true)"
UNDEFINED_REFERENCES="$(grep -c 'Reference.*undefined' "$LOG" || true)"
UNDEFINED_CITATIONS="$(grep -c 'Citation.*undefined' "$LOG" || true)"
MULTIPLY_DEFINED="$(grep -Eci 'multiply[- ]defined' "$LOG" || true)"
RERUN_REQUIRED="$(grep -Eci 'Rerun (LaTeX|to get)|Label\(s\) may have changed' "$LOG" || true)"
OVERFULL_BOXES="$(grep -Ec '^Overfull \\[hv]box' "$LOG" || true)"
UNDERFULL_BOXES="$(grep -Ec '^Underfull \\[hv]box' "$LOG" || true)"
PDF="$BUILD_DIR/ECT_preprint.pdf"
if command -v pdfinfo >/dev/null 2>&1; then
  PAGES="$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2; exit}')"
elif command -v gs >/dev/null 2>&1; then
  PAGES="$(gs -q -dNOSAFER -dNODISPLAY -c "($PDF) (r) file runpdfbegin pdfpagecount = quit")"
else
  PAGES="$(tr '\n' ' ' <"$LOG" | sed -nE 's/.*Output written.*\(([0-9]+) pages.*/\1/p')"
fi

printf 'PDF: %s\n' "$PDF"
printf 'LaTeX passes (plus BibTeX): %s\n' "$LATEX_PASSES"
printf 'Errors: %s\n' "$ERRORS"
printf 'Undefined references: %s\n' "$UNDEFINED_REFERENCES"
printf 'Undefined citations: %s\n' "$UNDEFINED_CITATIONS"
printf 'Multiply-defined diagnostics: %s\n' "$MULTIPLY_DEFINED"
printf 'Rerun-required diagnostics: %s\n' "$RERUN_REQUIRED"
printf 'Overfull boxes: %s\n' "$OVERFULL_BOXES"
printf 'Underfull boxes: %s\n' "$UNDERFULL_BOXES"
if [[ -n "$PREVIOUS_PAGES" ]]; then
  printf 'Pages: %s (was %s)\n' "$PAGES" "$PREVIOUS_PAGES"
else
  printf 'Pages: %s\n' "$PAGES"
fi

if [[ -z "$PAGES" ]]; then
  printf 'Page-count gate: FAIL (could not read PDF page count)\n' >&2
  exit 2
fi

if (( ERRORS != 0 || UNDEFINED_REFERENCES != 0 || UNDEFINED_CITATIONS != 0 || MULTIPLY_DEFINED != 0 || RERUN_REQUIRED != 0 )); then
  printf 'Validation gate: FAIL\n' >&2
  exit 2
fi
printf 'Validation gate: PASS\n'
