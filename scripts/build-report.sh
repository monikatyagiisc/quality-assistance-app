#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/reports/quality-assistance-report"
OUTPUT_DIR="${REPO_ROOT}/tmp/reports"
REPORTS_DIR="${REPO_ROOT}/reports"
REPORT_NAME="quality-assistant-app"

for tool in pdflatex bibtex makeindex; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "${tool}" >&2
    printf 'On Ubuntu, install the TeX tools with:\n' >&2
    printf '  sudo apt-get update && sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-science texlive-bibtex-extra texlive-pictures texlive-fonts-recommended\n' >&2
    exit 1
  fi
done

if [[ ! -f "${SOURCE_DIR}/main.tex" ]]; then
  printf 'Report source not found: %s/main.tex\n' "${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

for extension in aux bbl blg brf ilg loa lof log lot nlo nls out toc pdf; do
  rm -f -- "${OUTPUT_DIR}/${REPORT_NAME}.${extension}"
done
rm -f -- "${OUTPUT_DIR}/appendix.aux"

cd "${SOURCE_DIR}"

compile_report() {
  pdflatex \
    -interaction=nonstopmode \
    -halt-on-error \
    -file-line-error \
    -output-directory="${OUTPUT_DIR}" \
    -jobname="${REPORT_NAME}" \
    main.tex
}

compile_report
(cd "${OUTPUT_DIR}" && BIBINPUTS="${SOURCE_DIR}:${BIBINPUTS:-}" bibtex "${REPORT_NAME}")
(cd "${OUTPUT_DIR}" && makeindex "${REPORT_NAME}.nlo" -s nomencl.ist -o "${REPORT_NAME}.nls")
compile_report
compile_report
compile_report

PDF_PATH="${OUTPUT_DIR}/${REPORT_NAME}.pdf"
if [[ ! -s "${PDF_PATH}" ]]; then
  printf 'PDF build did not produce the expected file: %s\n' "${PDF_PATH}" >&2
  exit 1
fi

REPORTS_PDF_PATH="${REPORTS_DIR}/${REPORT_NAME}.pdf"
cp -- "${PDF_PATH}" "${REPORTS_PDF_PATH}"

printf '\nReport generated successfully:\n%s\n%s\n' "${PDF_PATH}" "${REPORTS_PDF_PATH}"
