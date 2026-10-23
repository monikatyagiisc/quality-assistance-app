#!/usr/bin/env bash
# Install frontend dependencies through the organization's JFrog npm repository.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND="$ROOT/frontend"
LOCK_FILE="$FRONTEND/yarn.lock"
REGISTRY="https://jfrog.alight.com/artifactory/api/npm/yarnpkg-npm-remote-virual/"

if [[ -z "${JFROG_NPM_TOKEN:-}" ]]; then
  echo "Error: Set JFROG_NPM_TOKEN to your JFrog access token and rerun this script." >&2
  echo "The token is used temporarily and is not saved in the repository." >&2
  exit 1
fi

for command_name in node yarn python3; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Error: '$command_name' is required but was not found on PATH." >&2
    exit 1
  fi
done

if [[ ! -f "$FRONTEND/package.json" || ! -f "$LOCK_FILE" ]]; then
  echo "Error: frontend/package.json or frontend/yarn.lock is missing." >&2
  exit 1
fi

TEMP_DIR="$(mktemp -d)"
LOCK_BACKUP="$TEMP_DIR/yarn.lock"
NPM_CONFIG="$TEMP_DIR/npmrc"
cp -p "$LOCK_FILE" "$LOCK_BACKUP"
chmod 600 "$LOCK_BACKUP"

cleanup() {
  local exit_code=$?
  cp -p "$LOCK_BACKUP" "$LOCK_FILE"
  rm -rf -- "$TEMP_DIR"
  exit "$exit_code"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

umask 077
JFROG_NPM_REGISTRY="$REGISTRY" python3 - "$NPM_CONFIG" <<'PY'
import os
import sys
from pathlib import Path

token = os.environ["JFROG_NPM_TOKEN"]
if "\n" in token or "\r" in token:
    raise SystemExit("Error: JFROG_NPM_TOKEN must not contain newline characters.")

registry = os.environ["JFROG_NPM_REGISTRY"]
auth_path = registry.removeprefix("https:").rstrip("/") + "/:_authToken"
Path(sys.argv[1]).write_text(
    f"registry={registry}\nalways-auth=true\n{auth_path}={token}\n"
)
PY

echo "Routing locked package downloads through the configured JFrog registry..."
python3 - "$LOCK_FILE" "$REGISTRY" <<'PY'
import sys
from pathlib import Path

lockfile = Path(sys.argv[1])
registry = sys.argv[2]
content = lockfile.read_text()
replacements = 0
for source in ("https://registry.yarnpkg.com/", "https://registry.npmjs.org/"):
    count = content.count(source)
    content = content.replace(source, registry)
    replacements += count

if replacements == 0:
    raise SystemExit("Error: No public npm registry URLs found in yarn.lock to redirect.")

lockfile.write_text(content)
print(f"Redirected {replacements} locked package URLs for this install.")
PY

export NPM_CONFIG_USERCONFIG="$NPM_CONFIG"
export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--use-openssl-ca"

echo "Installing frontend dependencies with the frozen lockfile..."
cd "$FRONTEND"
yarn install --frozen-lockfile --non-interactive --registry "$REGISTRY"
