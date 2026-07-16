#!/bin/bash
set -euo pipefail

DOC_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$DOC_ROOT/.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
BUILD_DIR="$WORKSPACE_ROOT/.workspace/build/companion"
mkdir -p "$BUILD_DIR"
cd "$DOC_ROOT"

PDFLATEX="${PDFLATEX:-/Library/TeX/texbin/pdflatex}"
for pass in 1 2 3; do
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error \
    -output-directory="$BUILD_DIR" ECT_companion.tex \
    >"$BUILD_DIR/pass_${pass}.stdout.log" 2>&1
done

LOG="$BUILD_DIR/ECT_companion.log"
printf 'PDF: %s\n' "$BUILD_DIR/ECT_companion.pdf"
printf 'Errors: %s\n' "$(grep -c '^!' "$LOG" || true)"
printf 'Undefined references: %s\n' "$(grep -c 'Reference.*undefined' "$LOG" || true)"
printf 'Undefined citations: %s\n' "$(grep -c 'Citation.*undefined' "$LOG" || true)"
grep -oE 'Output written.*\([0-9]+ pages' "$LOG" | tail -1 || true

XELATEX="${XELATEX:-/Library/TeX/texbin/xelatex}"
RU_BUILD="$BUILD_DIR/ru"
mkdir -p "$RU_BUILD"
for pass in 1 2; do
  "$XELATEX" -interaction=nonstopmode -halt-on-error \
    -output-directory="$RU_BUILD" ECT_companion_ru.tex \
    >"$RU_BUILD/pass_${pass}.stdout.log" 2>&1
done
RU_LOG="$RU_BUILD/ECT_companion_ru.log"
printf 'RU PDF: %s\n' "$RU_BUILD/ECT_companion_ru.pdf"
printf 'RU errors: %s\n' "$(grep -c '^!' "$RU_LOG" || true)"
printf 'RU undefined references: %s\n' "$(grep -c 'Reference.*undefined' "$RU_LOG" || true)"
