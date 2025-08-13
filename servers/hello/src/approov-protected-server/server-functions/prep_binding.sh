#!/usr/bin/env bash
set -euo pipefail

# prep_binding.sh
# Generate an Approov-Token (with 'pay') + matching Authorization header for token-binding tests.
# Usage:
#   ./prep_binding.sh [URL] [EXP_MINUTES] [AUTH_BEARER] [--curl]
# Defaults:
URL="${1:-http://localhost:8002/}"
EXP_MIN="${2:-5}"
AUTH_BEARER_INPUT="${3:-}"
DO_CURL="${4:-}"

ENV_FILE=".env"
TOKEN_FILE="approov_token.txt"
AUTH_FILE="authorization.txt"

command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

# 1) Load secret from .env
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE (needs APPROOV_BASE64_SECRET=...)"; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${APPROOV_BASE64_SECRET:?APPROOV_BASE64_SECRET missing in .env}"

# 2) Pick/generate a bearer for the Authorization header
if [[ -n "$AUTH_BEARER_INPUT" ]]; then
  BEARER="$AUTH_BEARER_INPUT"
else
  # Generate a random URL-safe token as the bearer value (dev-only)
  BEARER="$(python3 - <<'PY'
import os, base64
print(base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip('='))
PY
)"
fi
AUTH_HDR="Bearer ${BEARER}"

# 3) Compute pay = base64(sha256(Authorization))  — no newline issues (pass as argv)
PAY="$(python3 - <<'PY' "$AUTH_HDR"
import sys, hashlib, base64
auth = sys.argv[1]
digest = hashlib.sha256(auth.encode('utf-8')).digest()
print(base64.b64encode(digest).decode('utf-8'))
PY
)"

# 4) Mint Approov-Token with 'pay' (HS256)
python3 - <<'PY' "$APPROOV_BASE64_SECRET" "$EXP_MIN" "$PAY" > "$TOKEN_FILE"
import sys, time, base64, jwt
secret_b64, exp_min, pay = sys.argv[1], int(sys.argv[2]), sys.argv[3]
secret = base64.b64decode(secret_b64)
payload = {"exp": int(time.time()) + 60*exp_min, "pay": pay}
print(jwt.encode(payload, secret, algorithm="HS256"))
PY

# 5) Save Authorization header (no trailing newline)
printf '%s' "$AUTH_HDR" > "$AUTH_FILE"

TOKEN="$(cat "$TOKEN_FILE")"

echo
echo "Prepared token-binding request:"
echo "  URL:            $URL"
echo "  Authorization:  $(cat "$AUTH_FILE")  (saved to $AUTH_FILE)"
echo "  Approov-Token:  (saved to $TOKEN_FILE)"
echo
echo "curl example (using the saved files):"
echo "curl -iX GET \"$URL\" \\"
echo "  -H \"Approov-Token: \$(cat $TOKEN_FILE)\" \\"
echo "  -H \"Authorization: \$(cat $AUTH_FILE)\""

if [[ "$DO_CURL" == "--curl" ]]; then
  echo
  echo "Running curl..."
  curl -iX GET "$URL" \
    -H "Approov-Token: $(cat "$TOKEN_FILE")" \
    -H "Authorization: $(cat "$AUTH_FILE")"
fi
