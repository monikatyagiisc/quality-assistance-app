#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=tex-path.sh
source "${SCRIPT_DIR}/tex-path.sh"

TINYTEX_HOME="${HOME}/Library/TinyTeX"

# Packages required by IIScthesisPSnPDF.cls and reports/quality-assistance-report/main.tex
REPORT_TEX_PACKAGES=(
  algorithmicx
  algorithms
  amscls
  amsfonts
  amsmath
  babel
  babel-english
  bigfoot
  booktabs
  cancel
  caption
  cleveref
  datetime
  diagbox
  epstopdf-pkg
  etoolbox
  fancyhdr
  float
  fmtcount
  footmisc
  graphics
  hyperref
  iftex
  jknapltx
  makeindex
  mdwtools
  multirow
  natbib
  nomencl
  notoccite
  pdfpages
  pgf
  setspace
  subfigure
  titlesec
  tocbibind
  tools
  url
  varwidth
  wrapfig
  xcolor
  collection-fontsrecommended
  collection-latexextra
  collection-latexrecommended
  collection-pictures
)

pdflatex_available() {
  command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1
}

tex_tools_available() {
  pdflatex_available && command -v makeindex >/dev/null 2>&1
}

install_tinytex() {
  printf 'pdflatex was not found. Installing TinyTeX (a compact TeX Live) for this user...\n' >&2
  if [[ -d "${TINYTEX_HOME}" ]] && [[ -z "$(ls -A "${TINYTEX_HOME}" 2>/dev/null || true)" ]]; then
    rmdir -- "${TINYTEX_HOME}"
  fi
  # The installer may ask for sudo to edit PATH. Ignore that; this script sets PATH itself.
  curl -fsSL "https://yihui.org/tinytex/install-bin-unix.sh" | sh || true
  # shellcheck source=tex-path.sh
  source "${SCRIPT_DIR}/tex-path.sh"
}

install_report_packages() {
  local tlmgr
  tlmgr="$(command -v tlmgr || true)"
  if [[ -z "${tlmgr}" ]]; then
    printf 'tlmgr was not found after TeX install.\n' >&2
    return 1
  fi
  printf 'Ensuring report LaTeX packages are installed...\n' >&2
  "${tlmgr}" update --self --repository https://mirror.ctan.org/systems/texlive/tlnet || true
  "${tlmgr}" install "${REPORT_TEX_PACKAGES[@]}" || true
  # shellcheck source=tex-path.sh
  source "${SCRIPT_DIR}/tex-path.sh"
}

if ! pdflatex_available; then
  if ! command -v curl >/dev/null 2>&1; then
    printf 'curl is required to install TinyTeX.\n' >&2
    exit 1
  fi
  install_tinytex
  if ! pdflatex_available; then
    printf 'TinyTeX installed, but pdflatex/bibtex are still not on PATH.\n' >&2
    printf 'Add this to your shell profile if needed:\n' >&2
    printf '  export PATH="%s/bin/universal-darwin:$PATH"\n' "${TINYTEX_HOME}" >&2
    exit 1
  fi
fi

install_report_packages

if ! tex_tools_available; then
  printf 'pdflatex, bibtex, and makeindex are required. After TinyTeX, run:\n' >&2
  printf '  tlmgr install makeindex\n' >&2
  exit 1
fi

printf 'Using pdflatex: %s\n' "$(command -v pdflatex)"
exec "${SCRIPT_DIR}/build-report.sh"
