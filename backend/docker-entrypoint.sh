#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting backend API..."
exec uvicorn quality_assistance_backend.main:app \
  --host "${BACKEND_HOST:-0.0.0.0}" \
  --port "${BACKEND_PORT:-8000}"
