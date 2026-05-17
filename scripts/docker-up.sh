#!/usr/bin/env bash
# Build and start the full stack with Docker Compose.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is required. Install Docker Desktop and try again." >&2
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  if [[ -f "$ROOT/.env.docker.example" ]]; then
    cp "$ROOT/.env.docker.example" "$ROOT/.env"
    echo "Created .env from .env.docker.example — set GOOGLE_API_KEY before continuing."
  else
    echo "Error: Missing .env file. Create one with GOOGLE_API_KEY (see .env.docker.example)." >&2
    exit 1
  fi
fi

# shellcheck disable=SC1091
set -a && source "$ROOT/.env" && set +a

if [[ -z "${GOOGLE_API_KEY:-}" || "${GOOGLE_API_KEY}" == "your-gemini-api-key" ]]; then
  echo "Error: Set a valid GOOGLE_API_KEY in $ROOT/.env" >&2
  exit 1
fi

echo "Building and starting services..."
docker compose up --build -d

echo ""
echo "Waiting for services to become healthy..."
deadline=$((SECONDS + 180))
while [[ $SECONDS -lt $deadline ]]; do
  if docker compose ps --status running 2>/dev/null | grep -q frontend \
    && curl -sf http://localhost:8000/health >/dev/null \
    && curl -sf http://localhost:8001/health >/dev/null \
    && curl -sf http://localhost:5173/ >/dev/null; then
    echo ""
    echo "All services are up."
    echo "  Frontend:  http://localhost:5173"
    echo "  Backend:   http://localhost:8000  (docs: /docs)"
    echo "  Agent:     http://localhost:8001  (docs: /docs)"
    echo "  Postgres:  localhost:5432"
    echo ""
    echo "Logs:  docker compose logs -f"
    echo "Stop:  docker compose down"
    exit 0
  fi
  sleep 3
done

echo "Error: Services did not become healthy within 3 minutes." >&2
docker compose ps
exit 1
