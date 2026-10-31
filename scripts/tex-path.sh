#!/usr/bin/env bash
# Prepend common TeX Live / TinyTeX / MacTeX locations to PATH.

prepend_dir() {
  local dir="$1"
  if [[ -d "${dir}" && ":${PATH}:" != *":${dir}:"* ]]; then
    PATH="${dir}:${PATH}"
  fi
}

prepend_dir "/Library/TeX/texbin"
prepend_dir "${HOME}/bin"

for dir in \
  "${HOME}/Library/TinyTeX/bin/"* \
  "${HOME}/.TinyTeX/bin/"*
do
  prepend_dir "${dir}"
done

if [[ -d /usr/local/texlive ]]; then
  for dir in /usr/local/texlive/*/bin/*; do
    prepend_dir "${dir}"
  done
fi

export PATH
