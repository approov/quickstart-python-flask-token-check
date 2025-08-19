#!/usr/bin/env bash
# server/run_docker.sh — build, start, wait, prep, test (all inside Docker)
set -euo pipefail

PORT="${1:-${HTTP_PORT:-8002}}"
SERVICE="approov-server"

echo "==> Starting ${SERVICE} on port ${PORT}…"
HTTP_PORT="$PORT" docker compose up -d --build "${SERVICE}" --remove-orphans

# Fixed paths (no /app) — everything under /home/python/workspace
DEV_DIR_IN_CTN="/home/python/workspace/server/config"
APP_DIR_IN_CTN="/home/python/workspace/server"

# Ensure the expected dirs exist in the container
docker compose exec -T "${SERVICE}" bash -lc "
  set -e
  test -d '${APP_DIR_IN_CTN}' || { echo '✗ Missing ${APP_DIR_IN_CTN} inside container' >&2; exit 1; }
  test -d '${DEV_DIR_IN_CTN}' || { echo '✗ Missing ${DEV_DIR_IN_CTN} inside container' >&2; exit 1; }
"

echo "==> Ensuring server is running, waiting until ready, then prepping & testing…"
docker compose exec -T "${SERVICE}" bash -lc "
  set -e

  cd '${APP_DIR_IN_CTN}'

  # Make scripts executable & normalize line endings
  shopt -s nullglob
  for f in scripts/*.sh; do
    sed -i 's/\r$//' \"\$f\" || true
    chmod +x \"\$f\"
  done

  # Use your server filename (fallbacks if needed)
  SERVER_FILE=hello_server_protected.py
  if [[ ! -f \"\$SERVER_FILE\" ]]; then
    for cand in hello_server.py server.py app.py; do
      if [[ -f \"\$cand\" ]]; then SERVER_FILE=\"\$cand\"; break; fi
    done
  fi
  [[ -f \"\$SERVER_FILE\" ]] || { echo '✗ Could not find server file in ${APP_DIR_IN_CTN}' >&2; exit 1; }

  # Start server if not already running
  if ! pgrep -f \"python.*\$SERVER_FILE\" >/dev/null 2>&1; then
    echo '→ starting' \"\$SERVER_FILE\" 'on ${PORT}'
    nohup python3 \"\$SERVER_FILE\" ${PORT} >/tmp/server.log 2>&1 &
    disown || true
  fi

  # Wait for readiness
  echo '==> Waiting for server to be ready…'
  for i in \$(seq 1 30); do
    if curl -fsS -m 2 'http://127.0.0.1:${PORT}/' >/dev/null; then
      echo '✓ Server is up'
      break
    fi
    sleep 1
  done

  # Final sanity check
  curl -fsS 'http://127.0.0.1:${PORT}/' >/dev/null || {
    echo '✗ Server did not become ready, dumping /tmp/server.log:' >&2
    test -f /tmp/server.log && { echo '--- /tmp/server.log ---'; tail -n +1 /tmp/server.log; echo '------------------------'; }
    exit 1
  }

  # Run prep (creates tokens/signatures in config)
  echo '==> Running prep…'
  export DEV_DIR='${DEV_DIR_IN_CTN}'
  bash ./scripts/prep.sh '${PORT}'

  # Run tests (all 6)
  echo '==> Running tests…'
  bash ./scripts/tests.sh 'http://127.0.0.1:${PORT}'
"

echo "==> Done."