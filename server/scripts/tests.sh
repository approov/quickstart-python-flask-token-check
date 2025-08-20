#!/usr/bin/env bash
# scripts/tests.sh — run all endpoint checks (works in venv & Docker)

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEV="${DEV_DIR:-$REPO_ROOT/config}"

# Optional env (HTTP_PORT, CUSTOM_BINDING_HEADER, etc.)
if [[ -f "$DEV/.env" ]]; then
  # shellcheck disable=SC1090
  source "$DEV/.env"
fi

# BASE_URL: CLI > BASE_URL env > HTTP_PORT from .env > default
BASE_URL_INPUT="${1:-${BASE_URL:-}}"
if [[ -z "${BASE_URL_INPUT}" && -n "${HTTP_PORT:-}" ]]; then
  BASE_URL_INPUT="http://localhost:${HTTP_PORT}"
fi
BASE_URL="${BASE_URL_INPUT:-http://localhost:8002}"
[[ "$BASE_URL" =~ ^[0-9]+$ ]] && BASE_URL="http://localhost:${BASE_URL}"

LOG_DIR="$DEV/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +'%Y%m%d-%H%M%S')"
LOG_FILE="$LOG_DIR/test-$STAMP.log"
: > "$LOG_FILE"

# Colors
green=$'\033[32m'; red=$'\033[31m'; yellow=$'\033[33m'; reset=$'\033[0m'

# Artifacts
TOK_CHECK_FILE="$DEV/token_check.txt"
TOK_BIND_FILE="$DEV/approov_token.txt"
AUTH_FILE="$DEV/authorization.txt"
TOK_MSG_FILE="$DEV/token.txt"
SIG_MSG_FILE="$DEV/signature.b64"
TOK_BM_FILE="$DEV/token_bm.txt"
SIG_BM_FILE="$DEV/signature_bm.b64"
TOK_CUSTOM="$DEV/token_custom.txt"
HEADER_FILE="$DEV/header.txt"

# Custom header name
CUSTOM_BINDING_HEADER="${CUSTOM_BINDING_HEADER:-X-Header-Id}"
[[ -z "$CUSTOM_BINDING_HEADER" ]] && CUSTOM_BINDING_HEADER="X-Header-Id"

passes=0; fails=0; skips=0
now_iso() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

log_header () {
  {
    echo "===================================================================="
    echo "Approov tests — $(now_iso)"
    echo "Base URL: $BASE_URL"
    echo "Config dir: $DEV"
    echo "Log file: $LOG_FILE"
    echo "===================================================================="
    echo
    echo "# Files in \$DEV:"
    ls -l "$DEV" || true
    echo
  } >>"$LOG_FILE"
}

log_section () {
  {
    echo
    echo "--------------------------------------------------------------------"
    echo "$1"
    echo "--------------------------------------------------------------------"
    echo "Time: $(now_iso)"
    echo
  } >>"$LOG_FILE"
}

need () {
  local file="$1" label="$2" path="$3"
  if [[ ! -f "$file" ]]; then
    printf "%s %s (%s) — SKIPPED (missing %s)\n" "${yellow}•${reset}" "$label" "$path" "$file"
    ((skips+=1))
    return 1
  fi
  return 0
}

print_error_snippet () {
  local body_file="$1" ct="$2"
  [[ ! -s "$body_file" ]] && return 0
  local char_limit=800
  if [[ "$ct" == application/json* || "$ct" == */json* ]]; then
    if command -v python3 >/dev/null 2>&1; then
      python3 - "$body_file" <<'PY' 2>/dev/null || cat "$body_file"
import sys, json
p = sys.argv[1]
with open(p, 'rb') as f:
    try:
        obj = json.load(f)
    except Exception:
        sys.exit(1)
print(json.dumps(obj, indent=2, ensure_ascii=False))
PY
      return 0
    fi
    cat "$body_file"
  else
    awk -v lim="$char_limit" '{
      out = out $0 ORS
      if (length(out) > lim) { print substr(out, 1, lim) "\n..."; exit }
    } END { if (NR>0 && length(out)<=lim) printf "%s", out }' "$body_file"
  fi
}

run_test () {
  # Usage: run_test "Name" "/path" [METHOD] [headers...]
  local name="$1"; local path="$2"
  shift 2
  local method="GET"
  if (( $# >= 1 )); then
    case "$1" in
      GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) method="$1"; shift ;;
    esac
  fi

  local -a hdrs=()
  while (( $# > 0 )); do
    hdrs+=("$1")
    shift
  done

  log_section "$name ($method $BASE_URL$path)"
  {
    echo "Request:"
    echo "  $method $BASE_URL$path"
    if ((${#hdrs[@]})); then
      echo "  Headers:"
      for h in "${hdrs[@]}"; do echo "    $h"; done
    fi
    echo
    echo "Response:"
  } >>"$LOG_FILE"

  local tmpdir hdr_file body_file
  tmpdir="$(mktemp -d 2>/dev/null || mktemp -d -t tests)"
  hdr_file="$tmpdir/headers.txt"
  body_file="$tmpdir/body.txt"
  : > "$hdr_file"; : > "$body_file"

  local -a curl_args=()
  if ((${#hdrs[@]})); then
    for h in "${hdrs[@]}"; do curl_args+=(-H "$h"); done
  fi

  local code
  if ((${#curl_args[@]})); then
    code="$(
      curl -sS -m 15 --connect-timeout 5 \
        -X "$method" "$BASE_URL$path" \
        "${curl_args[@]}" \
        --dump-header "$hdr_file" \
        -o "$body_file" \
        -w "%{http_code}" \
      || echo "000"
    )"
  else
    code="$(
      curl -sS -m 15 --connect-timeout 5 \
        -X "$method" "$BASE_URL$path" \
        --dump-header "$hdr_file" \
        -o "$body_file" \
        -w "%{http_code}" \
      || echo "000"
    )"
  fi

  {
    echo "# --- Response headers ---"
    cat "$hdr_file"
    echo
    echo "# --- Response body ---"
    cat "$body_file"
    echo
    echo "# --- End of response ---"
  } >>"$LOG_FILE"

  local ct
  ct="$(awk 'BEGIN{IGNORECASE=1} /^Content-Type:/ {sub(/\r$/,"",$0); sub(/^Content-Type:[[:space:]]*/,"",$0); print; exit}' "$hdr_file" || true)"

  if [[ "$code" == "200" ]]; then
    printf "${green}✔ %s (%s) — PASSED (HTTP %s)${reset}\n" "$name" "$path" "$code"
    ((passes+=1))
  elif [[ "$code" == "000" ]]; then
    printf "${red}✘ %s (%s) — FAILED (no connection)${reset}\n" "$name" "$path"
    ((fails+=1))
  else
    printf "${red}✘ %s (%s) — FAILED (HTTP %s)${reset}\n" "$name" "$path" "$code"
    print_error_snippet "$body_file" "$ct" | sed 's/^/  /'
    echo
    ((fails+=1))
  fi

  rm -rf "$tmpdir"
}

echo "Running tests against $BASE_URL"
echo "(full log: $LOG_FILE)"
echo
log_header

# 1) Unprotected
run_test "Unprotected" "/"

# 2) Token check
if need "$TOK_CHECK_FILE" "Token check" "/token_check"; then
  run_test "Token check" "/token_check" GET \
    "Approov-Token: $(<"$TOK_CHECK_FILE")"
fi

# 3) Token binding
if need "$TOK_BIND_FILE" "Token binding" "/token_binding" && \
   need "$AUTH_FILE" "Token binding" "/token_binding"; then
  run_test "Token binding" "/token_binding" GET \
    "Approov-Token: $(<"$TOK_BIND_FILE")" \
    "Authorization: $(<"$AUTH_FILE")"
fi

# 4) Message signature
if need "$TOK_MSG_FILE" "Message signature" "/message_signature" && \
   need "$SIG_MSG_FILE" "Message signature" "/message_signature"; then
  run_test "Message signature" "/message_signature" GET \
    "Approov-Token: $(<"$TOK_MSG_FILE")" \
    'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
    "Signature: install=:$(<"$SIG_MSG_FILE"):"
fi

# 5) Binding + MsgSig
if need "$TOK_BM_FILE" "Binding + MsgSig" "/token_binding_message_signature" && \
   need "$AUTH_FILE"  "Binding + MsgSig" "/token_binding_message_signature" && \
   need "$SIG_BM_FILE" "Binding + MsgSig" "/token_binding_message_signature"; then
  run_test "Token Binding + Message Signature" "/token_binding_message_signature" GET \
    "Approov-Token: $(<"$TOK_BM_FILE")" \
    "Authorization: $(<"$AUTH_FILE")" \
    'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
    "Signature: install=:$(<"$SIG_BM_FILE"):"
fi

# 6) Token binding custom (Authorization + custom header; pay=hash(Auth+Header))
if need "$TOK_CUSTOM" "Token binding custom" "/token_binding_custom" && \
   need "$AUTH_FILE" "Token binding custom" "/token_binding_custom" && \
   need "$HEADER_FILE" "Token binding custom" "/token_binding_custom"; then
  run_test "Token binding custom" "/token_binding_custom" GET \
    "Approov-Token: $(<"$TOK_CUSTOM")" \
    "Authorization: $(<"$AUTH_FILE")" \
    "$CUSTOM_BINDING_HEADER: $(<"$HEADER_FILE")"
fi

echo
printf "${green}%s passed${reset}, ${red}%s failed${reset}, ${yellow}%s skipped${reset}  |  log: %s\n" "$passes" "$fails" "$skips" "$LOG_FILE"



