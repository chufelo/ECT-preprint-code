#!/bin/bash
set -euo pipefail

DOC_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DOC_ROOT/.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
if [[ -d "$WORKSPACE_ROOT/.workspace" ]]; then
  DEFAULT_BUILD_DIR="$WORKSPACE_ROOT/.workspace/build/summary/current"
else
  DEFAULT_BUILD_DIR="$REPO_ROOT/.build/summary/current"
fi
BUILD_DIR="${BUILD_DIR:-$DEFAULT_BUILD_DIR}"
mkdir -p "$BUILD_DIR"
BUILD_DIR="$(cd "$BUILD_DIR" && pwd)"
cd "$DOC_ROOT"

PDFLATEX="${PDFLATEX:-/Library/TeX/texbin/pdflatex}"
BIBTEX="${BIBTEX:-/Library/TeX/texbin/bibtex}"
LATEX_PASSES="${LATEX_PASSES:-3}"
PREVIOUS_PAGES="${PREVIOUS_PAGES:-}"

if [[ -n "${SOURCE_DATE_EPOCH:-}" ]]; then
  if ! [[ "$SOURCE_DATE_EPOCH" =~ ^[0-9]+$ ]]; then
    printf 'SOURCE_DATE_EPOCH must be a non-negative integer (received %s)\n' "$SOURCE_DATE_EPOCH" >&2
    exit 2
  fi
  export SOURCE_DATE_EPOCH FORCE_SOURCE_DATE=1 TZ=UTC
fi

if ! [[ "$LATEX_PASSES" =~ ^[0-9]+$ ]] || (( LATEX_PASSES < 3 )); then
  printf 'LATEX_PASSES must be an integer >= 3 (received %s)\n' "$LATEX_PASSES" >&2
  exit 2
fi

run_pass() {
  local pass="$1"
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error \
    -output-directory="$BUILD_DIR" ECT_summary.tex \
    >"$BUILD_DIR/pass_${pass}.stdout.log" 2>&1
}

run_pass 1
(cd "$BUILD_DIR" && BIBINPUTS="$REPO_ROOT:" "$BIBTEX" ECT_summary) \
  >"$BUILD_DIR/bibtex.stdout.log" 2>&1
for ((pass = 2; pass <= LATEX_PASSES; pass++)); do
  run_pass "$pass"
done

LOG="$BUILD_DIR/ECT_summary.log"
PDF="$BUILD_DIR/ECT_summary.pdf"
if [[ "$PDF" == "$REPO_ROOT"/* ]]; then
  PDF_REPORT="${PDF#"$REPO_ROOT"/}"
else
  PDF_REPORT="<external-build>/$(basename "$PDF")"
fi
ERRORS="$(grep -c '^!' "$LOG" || true)"
UNDEFINED_REFERENCES="$(grep -c 'Reference.*undefined' "$LOG" || true)"
UNDEFINED_CITATIONS="$(grep -c 'Citation.*undefined' "$LOG" || true)"
MULTIPLY_DEFINED="$(grep -Eci 'multiply[- ]defined' "$LOG" || true)"
RERUN_REQUIRED="$(grep -Eci 'Rerun (LaTeX|to get)|Label\(s\) may have changed' "$LOG" || true)"
OVERFULL_BOXES="$(grep -Ec '^Overfull \\[hv]box' "$LOG" || true)"
UNDERFULL_BOXES="$(grep -Ec '^Underfull \\[hv]box' "$LOG" || true)"

if command -v pdfinfo >/dev/null 2>&1; then
  PAGES="$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2; exit}')"
else
  PAGES="$(tr '\n' ' ' <"$LOG" | sed -nE 's/.*Output written.*\(([0-9]+) pages.*/\1/p')"
fi

printf 'PDF: %s\n' "$PDF_REPORT"
printf 'LaTeX passes (plus BibTeX): %s\n' "$LATEX_PASSES"
printf 'SOURCE_DATE_EPOCH: %s\n' "${SOURCE_DATE_EPOCH:-UNSET_NONDETERMINISTIC_METADATA}"
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

if [[ -z "$PAGES" ]] || (( ERRORS != 0 || UNDEFINED_REFERENCES != 0 || UNDEFINED_CITATIONS != 0 || MULTIPLY_DEFINED != 0 || RERUN_REQUIRED != 0 )); then
  printf 'English summary validation gate: FAIL\n' >&2
  exit 2
fi
printf 'English summary validation gate: PASS\n'

# Russian downstream is deliberately opt-in.
if [[ "${BUILD_RU:-0}" != "1" ]]; then
  printf 'Russian summary: DEFERRED (set BUILD_RU=1 to opt in)\n'
  exit 0
fi

XELATEX="${XELATEX:-/Library/TeX/texbin/xelatex}"
RU_ROOT="$DOC_ROOT/ru"
RU_BUILD="${RU_BUILD_DIR:-$WORKSPACE_ROOT/.workspace/build/summary/ru-current}"
mkdir -p "$RU_BUILD"
cd "$RU_ROOT"
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_1.stdout.log" 2>&1
(cd "$RU_BUILD" && BIBINPUTS="$REPO_ROOT:" "$BIBTEX" ECT_summary_ru) >"$RU_BUILD/bibtex.stdout.log" 2>&1
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_2.stdout.log" 2>&1
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_3.stdout.log" 2>&1
printf 'Russian summary build completed at %s\n' "$RU_BUILD/ECT_summary_ru.pdf"
