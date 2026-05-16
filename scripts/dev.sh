#!/usr/bin/env bash
# Start agent, backend, and frontend for local development.
# Uses local PostgreSQL if already running; otherwise falls back to Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PIDS=()
LOG_DIR="$ROOT/.logs"
STARTED_DOCKER=false

# ANSI colors (disabled when not a TTY)
if [[ -t 1 ]]; then
  NC='\033[0m'
  COLOR_AGENT='\033[1;35m'    # magenta
  COLOR_BACKEND='\033[1;32m'  # green
  COLOR_FRONTEND='\033[1;33m' # yellow
  COLOR_POSTGRES='\033[1;34m' # blue
  COLOR_SYSTEM='\033[1;36m'   # cyan
else
  NC='' COLOR_AGENT='' COLOR_BACKEND='' COLOR_FRONTEND='' COLOR_POSTGRES='' COLOR_SYSTEM=''
fi

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-quality_assistance}"
PGDATABASE="${PGDATABASE:-quality_assistance}"

cleanup() {
  echo ""
  echo "Stopping app services..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  if [[ "$STARTED_DOCKER" == true ]]; then
    echo "Stopping Docker PostgreSQL..."
    docker compose stop postgres 2>/dev/null || true
  fi
  echo "Done."
}
trap cleanup EXIT INT TERM

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

ensure_env() {
  local example target
  example="$1"
  target="$2"
  if [[ ! -f "$target" && -f "$example" ]]; then
    cp "$example" "$target"
    log_line "system" "$COLOR_SYSTEM" "Created $target from example."
  fi
}

log_line() {
  local label="$1"
  local color="$2"
  shift 2
  printf '%b[%s]%b %s\n' "$color" "$label" "$NC" "$*"
}

prefix_stream() {
  local label="$1"
  local color="$2"
  while IFS= read -r line || [[ -n "$line" ]]; do
    log_line "$label" "$color" "$line"
  done
}

load_pg_config() {
  local env_file="$ROOT/backend/.env"
  local database_url=""

  if [[ -f "$env_file" ]]; then
    # shellcheck disable=SC1090
    set -a && source "$env_file" && set +a
  fi

  PGHOST="${DB_HOST:-${PGHOST:-localhost}}"
  PGPORT="${DB_PORT:-${PGPORT:-5432}}"
  PGUSER="${DB_USER:-${PGUSER:-quality_assistance}}"
  PGDATABASE="${DB_NAME:-${DBNAME:-${PGDATABASE:-quality_assistance}}}"

  if [[ -n "${DATABASE_URL:-}" ]]; then
    database_url="$DATABASE_URL"
    if [[ "$database_url" =~ //([^:]+):[^@]+@([^:/]+)(:([0-9]+))?/([^/?]+) ]]; then
      PGUSER="${BASH_REMATCH[1]}"
      PGHOST="${BASH_REMATCH[2]}"
      PGPORT="${BASH_REMATCH[4]:-5432}"
      PGDATABASE="${BASH_REMATCH[5]}"
    fi
  fi
}

postgres_port_open() {
  if command -v nc >/dev/null 2>&1; then
    nc -z "$PGHOST" "$PGPORT" 2>/dev/null
    return $?
  fi
  (echo >/dev/tcp/"$PGHOST"/"$PGPORT") 2>/dev/null
}

postgres_is_ready() {
  if command -v pg_isready >/dev/null 2>&1; then
    pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -q 2>/dev/null
    return $?
  fi
  postgres_port_open
}

wait_for_postgres() {
  local i
  for i in {1..30}; do
    if postgres_is_ready; then
      return 0
    fi
    sleep 1
  done
  return 1
}

ensure_postgres() {
  load_pg_config

  if postgres_is_ready; then
    log_line "postgres" "$COLOR_POSTGRES" "Already running at $PGHOST:$PGPORT (local instance, skipping Docker)."
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: PostgreSQL is not reachable at $PGHOST:$PGPORT and Docker is not installed." >&2
    echo "Start PostgreSQL locally or set DB_* variables in backend/.env" >&2
    exit 1
  fi

  log_line "postgres" "$COLOR_POSTGRES" "Not reachable at $PGHOST:$PGPORT. Starting Docker..."
  docker compose up -d postgres
  STARTED_DOCKER=true

  log_line "postgres" "$COLOR_POSTGRES" "Waiting for Docker PostgreSQL..."
  PGHOST="localhost"
  PGPORT="5432"
  PGUSER="quality_assistance"
  PGDATABASE="quality_assistance"

  if ! wait_for_postgres; then
    echo "Error: PostgreSQL did not become ready in time." >&2
    exit 1
  fi
}

# uv may be installed via the official installer
if ! command -v uv >/dev/null 2>&1 && [[ -f "$HOME/.local/bin/env" ]]; then
  # shellcheck source=/dev/null
  source "$HOME/.local/bin/env"
fi

require_cmd uv
require_cmd yarn

ensure_env "$ROOT/backend/.env.example" "$ROOT/backend/.env"
ensure_env "$ROOT/agent/.env.example" "$ROOT/agent/.env"
ensure_env "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"

if [[ ! -f "$ROOT/agent/.env" ]] || ! grep -qE '^GOOGLE_API_KEY=.+' "$ROOT/agent/.env" 2>/dev/null; then
  echo "Warning: Set GOOGLE_API_KEY in agent/.env before using the agent." >&2
fi

mkdir -p "$LOG_DIR"

ensure_postgres

log_line "system" "$COLOR_SYSTEM" "Installing Python dependencies..."
(cd "$ROOT/agent" && uv sync --quiet)
(cd "$ROOT/backend" && uv sync --quiet)

log_line "system" "$COLOR_SYSTEM" "Running database migrations..."
(cd "$ROOT/backend" && uv run alembic upgrade head)

log_line "system" "$COLOR_SYSTEM" "Installing frontend dependencies..."
(cd "$ROOT/frontend" && yarn install --frozen-lockfile --silent 2>/dev/null || yarn install --silent)

start_service() {
  local label="$1"
  local color="$2"
  local dir="$3"
  shift 3

  log_line "$label" "$color" "Starting..."

  (
    cd "$dir" || exit 1
    if command -v stdbuf >/dev/null 2>&1; then
      exec stdbuf -oL -eL "$@"
    else
      exec "$@"
    fi
  ) 2>&1 | tee -a "$LOG_DIR/$label.log" | prefix_stream "$label" "$color" &
  PIDS+=("$!")
}

: >"$LOG_DIR/agent.log"
: >"$LOG_DIR/backend.log"
: >"$LOG_DIR/frontend.log"

start_service "agent" "$COLOR_AGENT" "$ROOT/agent" uv run quality-assistance-agent
start_service "backend" "$COLOR_BACKEND" "$ROOT/backend" uv run quality-assistance-backend
start_service "frontend" "$COLOR_FRONTEND" "$ROOT/frontend" yarn dev

sleep 2

load_pg_config

echo ""
log_line "system" "$COLOR_SYSTEM" "All services started."
log_line "system" "$COLOR_SYSTEM" "  Frontend:  http://localhost:5173"
log_line "system" "$COLOR_SYSTEM" "  Backend:   http://localhost:8000  (docs: /docs)"
log_line "system" "$COLOR_SYSTEM" "  Agent:     http://localhost:8001  (docs: /docs)"
log_line "postgres" "$COLOR_POSTGRES" "  Database:  $PGHOST:$PGPORT ($PGDATABASE)"
echo ""
log_line "system" "$COLOR_SYSTEM" "Plain logs: $LOG_DIR/{agent,backend,frontend}.log"
log_line "system" "$COLOR_SYSTEM" "Press Ctrl+C to stop app services."
if [[ "$STARTED_DOCKER" == true ]]; then
  log_line "postgres" "$COLOR_POSTGRES" "Docker PostgreSQL started by this script will be stopped on exit."
fi
echo ""

wait "${PIDS[@]}"
