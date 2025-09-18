#!/usr/bin/env bash
# Simple helper to run both Django dev servers with environment variables from .env
# - Auth server: ./auth_server on port 8000
# - Backend server: ./backend_server on port 8001

set -euo pipefail
ENV_FILE=".env"

# Load .env if present (exports variables)
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment from $ENV_FILE"
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "Warning: $ENV_FILE not found. Continuing without loading env vars."
fi

# Ensure we run from repo root
cd "$(dirname "$0")" || exit 1

PIDS=()

start_server() {
  local dir="$1"
  local port="$2"
  echo "Starting $dir on port $port..."
  ( cd "$dir" && python manage.py runserver "$port" ) &
  PIDS+=("$!")
}

start_server "auth_server" 8000
start_server "backend_server" 8001

echo "Servers started (PIDs: ${PIDS[*]})"

echo "Press Ctrl-C to stop all servers"

_cleanup() {
  echo "Stopping servers..."
  if [ ${#PIDS[@]} -gt 0 ]; then
    kill "${PIDS[@]}" 2>/dev/null || true
    wait "${PIDS[@]}" 2>/dev/null || true
  fi
  exit 0
}

trap _cleanup INT TERM EXIT

# Wait for background processes
wait
