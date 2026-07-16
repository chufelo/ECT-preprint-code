#!/bin/bash
set -euo pipefail

DOC_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$DOC_ROOT/.." && pwd)"
WORKSPACE_ROOT="$(cd "$REPO_ROOT/.." && pwd)"
BUILD_DIR="$WORKSPACE_ROOT/.workspace/build/summary/current"
mkdir -p "$BUILD_DIR"
cd "$DOC_ROOT"

PDFLATEX="${PDFLATEX:-/Library/TeX/texbin/pdflatex}"
BIBTEX="${BIBTEX:-/Library/TeX/texbin/bibtex}"
"$PDFLATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" ECT_summary.tex >"$BUILD_DIR/pass_1.stdout.log" 2>&1
(cd "$BUILD_DIR" && BIBINPUTS="$REPO_ROOT:" "$BIBTEX" ECT_summary) >"$BUILD_DIR/bibtex.stdout.log" 2>&1
"$PDFLATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" ECT_summary.tex >"$BUILD_DIR/pass_2.stdout.log" 2>&1
"$PDFLATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" ECT_summary.tex >"$BUILD_DIR/pass_3.stdout.log" 2>&1

LOG="$BUILD_DIR/ECT_summary.log"
printf 'PDF: %s\n' "$BUILD_DIR/ECT_summary.pdf"
printf 'Errors: %s\n' "$(grep -c '^!' "$LOG" || true)"
printf 'Undefined references: %s\n' "$(grep -c 'Reference.*undefined' "$LOG" || true)"
printf 'Undefined citations: %s\n' "$(grep -c 'Citation.*undefined' "$LOG" || true)"
grep -oE 'Output written.*\([0-9]+ pages' "$LOG" | tail -1 || true

XELATEX="${XELATEX:-/Library/TeX/texbin/xelatex}"
RU_ROOT="$DOC_ROOT/ru"
RU_BUILD="$WORKSPACE_ROOT/.workspace/build/summary/ru-current"
mkdir -p "$RU_BUILD"
cd "$RU_ROOT"
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_1.stdout.log" 2>&1
(cd "$RU_BUILD" && BIBINPUTS="$REPO_ROOT:" "$BIBTEX" ECT_summary_ru) >"$RU_BUILD/bibtex.stdout.log" 2>&1
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_2.stdout.log" 2>&1
"$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$RU_BUILD" ECT_summary_ru.tex >"$RU_BUILD/pass_3.stdout.log" 2>&1
RU_LOG="$RU_BUILD/ECT_summary_ru.log"
printf 'RU PDF: %s\n' "$RU_BUILD/ECT_summary_ru.pdf"
printf 'RU errors: %s\n' "$(grep -c '^!' "$RU_LOG" || true)"
printf 'RU undefined references: %s\n' "$(grep -c 'Reference.*undefined' "$RU_LOG" || true)"
printf 'RU undefined citations: %s\n' "$(grep -c 'Citation.*undefined' "$RU_LOG" || true)"
