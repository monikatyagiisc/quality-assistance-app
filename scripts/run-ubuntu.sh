#!/usr/bin/env bash
# Start the local development services on Ubuntu.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f /etc/os-release ]] || ! grep -qi '^ID=ubuntu' /etc/os-release; then
  echo "Error: This script is for Ubuntu. Use scripts/dev.sh on other Linux distributions." >&2
  exit 1
fi

if [[ ! -f "$ROOT/agent/.env" || ! -f "$ROOT/backend/.env" || ! -f "$ROOT/frontend/.env" ]]; then
  echo "Error: App environment files are missing. Run ./scripts/setup-ubuntu.sh first." >&2
  exit 1
fi

export UV_SYSTEM_CERTS=true
export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--use-openssl-ca"

if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then
  export BROWSER="${BROWSER:-xdg-open}"
else
  echo "No graphical browser launcher detected; open http://localhost:5173 when the app starts."
fi

exec "$ROOT/scripts/dev.sh"
