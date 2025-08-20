#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREP="$ROOT_DIR/scripts/prep.sh"
TESTS="$ROOT_DIR/scripts/tests.sh"

# Anchor DEV to repo root
DEV="${DEV_DIR:-$ROOT_DIR/config}"

if [[ -f "$DEV/.env" ]]; then source "$DEV/.env"; fi
BASE_URL_INPUT="${1:-${BASE_URL:-}}"
if [[ -z "${BASE_URL_INPUT}" && -n "${HTTP_PORT:-}" ]]; then
  BASE_URL_INPUT="http://localhost:${HTTP_PORT}"
fi
BASE_URL="${BASE_URL_INPUT:-http://localhost:8002}"
if [[ "$BASE_URL" =~ ^[0-9]+$ ]]; then BASE_URL="http://localhost:${BASE_URL}"; fi

chmod +x "$PREP" "$TESTS" 2>/dev/null || true

echo "==> Running prep…"
SHOW_PAYLOADS="${SHOW_PAYLOADS:-0}" SKIP_TESTS=1 "$PREP" "$BASE_URL"

echo
echo "==> Running tests against $BASE_URL ..."
( cd "$ROOT_DIR" && "$TESTS" "$BASE_URL" )