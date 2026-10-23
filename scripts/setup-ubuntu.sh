#!/usr/bin/env bash
# Prepare local development on Ubuntu.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "Error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "'$1' is required. Install it and rerun this script."
}

check_version() {
  local command_name="$1"
  local minimum_major="$2"
  local minimum_minor="$3"
  local version major minor
  version="$("$command_name" --version 2>&1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -n 1)"
  [[ -n "$version" ]] || fail "Could not determine $command_name version."
  major="${version%%.*}"
  minor="${version#*.}"
  minor="${minor%%.*}"
  if (( major < minimum_major || (major == minimum_major && minor < minimum_minor) )); then
    fail "$command_name $version found; version $minimum_major.$minimum_minor or newer is required."
  fi
}

if [[ ! -f /etc/os-release ]] || ! grep -qi '^ID=ubuntu' /etc/os-release; then
  fail "This script is for Ubuntu. Use scripts/dev.sh on other Linux distributions."
fi

if ! command -v uv >/dev/null 2>&1 && [[ -f "$HOME/.local/bin/env" ]]; then
  # shellcheck source=/dev/null
  source "$HOME/.local/bin/env"
fi

require_cmd node
require_cmd npm
require_cmd uv
require_cmd yarn

PYTHON_CMD="python3"
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_CMD="python3.11"
fi
require_cmd "$PYTHON_CMD"

python_version="$("$PYTHON_CMD" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -n 1)"
[[ -n "$python_version" ]] || fail "Could not determine Python version."
python_major="${python_version%%.*}"
python_minor="${python_version#*.}"
if (( python_major < 3 || (python_major == 3 && python_minor < 11) )); then
  fail "Python $python_version found; Python 3.11 or newer is required."
fi
check_version node 20 0

ensure_env() {
  local example="$1"
  local target="$2"
  if [[ ! -f "$target" ]]; then
    cp "$example" "$target"
    echo "Created $target from its example."
  fi
}

ensure_env "$ROOT/backend/.env.example" "$ROOT/backend/.env"
ensure_env "$ROOT/agent/.env.example" "$ROOT/agent/.env"
ensure_env "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"

"$PYTHON_CMD" - "$ROOT/backend/.env" <<'PY'
import base64
import re
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = path.read_text()
defaults = {
    "DB_PASSWORD": ("your_password", "quality_assistance"),
    "JWT_SECRET": ("change-me-in-production", secrets.token_hex(32)),
    "ENCRYPTION_KEY": (
        "change-me-generate-with-cryptography-fernet",
        base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    ),
}
for name, (placeholder, value) in defaults.items():
    pattern = re.compile(rf"(?m)^{re.escape(name)}=(.*)$")
    match = pattern.search(content)
    if match and match.group(1).strip().strip("\"'") == placeholder:
        content = pattern.sub(f"{name}={value}", content, count=1)
        print(f"Generated a development value for {name} in backend/.env.")
path.write_text(content)
PY

get_env_value() {
  local name="$1"
  local default="$2"
  local value
  value="$(grep -m1 -E "^${name}=" "$ROOT/backend/.env" | cut -d= -f2- || true)"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "${value:-$default}"
}

pg_host="$(get_env_value DB_HOST localhost)"
pg_port="$(get_env_value DB_PORT 5432)"

if ! (echo >/dev/tcp/"$pg_host"/"$pg_port") >/dev/null 2>&1; then
  if [[ "$pg_host" != "localhost" && "$pg_host" != "127.0.0.1" ]] || [[ "$pg_port" != "5432" ]]; then
    fail "PostgreSQL is not reachable at $pg_host:$pg_port. Start it and rerun setup."
  fi
  require_cmd docker
  echo "PostgreSQL is not reachable. Starting the project's PostgreSQL container..."
  docker compose up -d postgres
  for attempt in {1..30}; do
    if (echo >/dev/tcp/localhost/5432) >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  (echo >/dev/tcp/localhost/5432) >/dev/null 2>&1 \
    || fail "PostgreSQL did not become ready. Check Docker and port 5432."
fi

echo "Installing agent and backend Python dependencies..."
(cd "$ROOT/agent" && uv sync --system-certs --quiet)
(cd "$ROOT/backend" && uv sync --system-certs --quiet)

echo "Installing frontend dependencies..."
if [[ -n "${JFROG_NPM_TOKEN:-}" ]]; then
  "$ROOT/scripts/yarn-install-jfrog.sh"
else
  (
    cd "$ROOT/frontend"
    NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--use-openssl-ca" yarn install --frozen-lockfile
  )
fi

echo "Applying database migrations..."
(cd "$ROOT/backend" && uv run alembic upgrade head)

if grep -qE '^AGENT_BACKEND=gemini([[:space:]]|$)' "$ROOT/agent/.env" \
  && grep -qE '^GOOGLE_API_KEY=your-gemini-api-key([[:space:]]|$)' "$ROOT/agent/.env"; then
  echo "Warning: Add your Gemini API key to agent/.env before requesting AI assistance." >&2
fi

echo ""
echo "Setup complete. Configure agent/.env, then run: ./scripts/run-ubuntu.sh"
echo "Generated development secrets are stored in backend/.env; existing values were preserved."
