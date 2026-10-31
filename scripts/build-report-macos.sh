#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -d /Library/TeX/texbin ]]; then
  PATH="/Library/TeX/texbin:${PATH}"
  export PATH
fi

missing_tools=()
for tool in pdflatex bibtex makeindex; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    missing_tools+=("${tool}")
  fi
done

if ((${#missing_tools[@]} > 0)); then
  printf 'Missing required TeX commands: %s\n' "${missing_tools[*]}" >&2
  printf 'Install MacTeX from https://tug.org/mactex/, then reopen Terminal.\n' >&2
  printf 'The full MacTeX distribution includes the packages used by this report.\n' >&2
  exit 1
fi

exec "${SCRIPT_DIR}/build-report.sh"