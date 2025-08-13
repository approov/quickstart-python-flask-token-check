#!/usr/bin/env bash
set -euo pipefail

# prep_msgsig_all.sh
# 1) Generate EC P-256 keypair (if missing, or force with --regen-keys)
# 2) Mint Approov-style JWT with ipk claim (HS256)
# 3) Build canonical message (@method/@target-uri)
# 4) Sign message with EC private key → base64 DER signature
# 5) (optional) Run the curl

# ---- defaults / args ----
METHOD="GET"
PATH_ONLY="/"
DO_CURL=false
REGEN_KEYS=false
ENV_FILE=".env"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method) METHOD="${2:-GET}"; shift 2 ;;
    --path)   PATH_ONLY="${2:-/}"; shift 2 ;;
    --curl)   DO_CURL=true; shift ;;
    --regen-keys) REGEN_KEYS=true; shift ;;
    --env)    ENV_FILE="${2:-.env}"; shift 2 ;;
    *)  # allow positional METHOD PATH as a shortcut
        if [[ "$METHOD" == "GET" && "$1" != /* && "$1" != --* ]]; then
          METHOD="$1"; shift; continue
        fi
        if [[ "$PATH_ONLY" == "/" && "$1" == /* ]]; then
          PATH_ONLY="$1"; shift; continue
        fi
        echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Ensure path starts with '/'
[[ "$PATH_ONLY" == /* ]] || PATH_ONLY="/$PATH_ONLY"

# ---- filenames ----
PRIV_PEM_FILE="private_key.pem"
PRIV_DER_FILE="private_key.der"
PUB_DER_FILE="public_key.der"
PUB_B64_FILE="public_key.b64"

TOKEN_FILE="token.txt"
MESSAGE_FILE="message.txt"
SIG_DER_FILE="sig.der"
SIG_B64_FILE="signature.b64"

# ---- deps ----
command -v openssl >/dev/null || { echo "openssl not found"; exit 1; }
PYTHON="$(command -v python3 || command -v python || true)"
[[ -n "$PYTHON" ]] || { echo "python3/python not found"; exit 1; }

# ---- env / secret ----
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE (needs APPROOV_BASE64_SECRET=...)"; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${APPROOV_BASE64_SECRET:?APPROOV_BASE64_SECRET missing in $ENV_FILE}"

# ---- 1) keys (generate once, or refresh with --regen-keys) ----
if $REGEN_KEYS || [[ ! -f "$PRIV_PEM_FILE" || ! -f "$PUB_B64_FILE" ]]; then
  echo "Generating EC P-256 keypair..."
  openssl ecparam -genkey -name prime256v1 -noout -out "$PRIV_PEM_FILE"
  openssl ec -in "$PRIV_PEM_FILE" -outform DER -out "$PRIV_DER_FILE"
  openssl ec -in "$PRIV_PEM_FILE" -pubout -outform DER -out "$PUB_DER_FILE"
  base64 < "$PUB_DER_FILE" | tr -d '\n' > "$PUB_B64_FILE"
  echo "Keys generated:"
  echo "  Private PEM: $PRIV_PEM_FILE"
  echo "  Private DER: $PRIV_DER_FILE"
  echo "  Public  DER: $PUB_DER_FILE"
  echo "  Public  b64: $PUB_B64_FILE"
fi

# ---- 2) mint JWT with ipk ----
"$PYTHON" - << 'PY' "$APPROOV_BASE64_SECRET" "$PUB_B64_FILE" > "$TOKEN_FILE"
import jwt, base64, sys, time
secret_b64, pubfile = sys.argv[1], sys.argv[2]
with open(pubfile,"r") as f:
    ipk = f.read().strip()
secret = base64.b64decode(secret_b64)
payload = {
  "exp": int(time.time()) + 3600,
  "aud": "",
  "ip": "1.2.3.4",
  "did": "ExampleApproovTokenDID==",
  "ipk": ipk
}
print(jwt.encode(payload, secret, algorithm="HS256"))
PY

# ---- 3) canonical message ----
printf '@method: %s\n@target-uri: %s' "$METHOD" "$PATH_ONLY" > "$MESSAGE_FILE"

# ---- 4) sign the message (ECDSA P-256 / SHA-256) ----
openssl dgst -sha256 -sign "$PRIV_PEM_FILE" -out "$SIG_DER_FILE" "$MESSAGE_FILE"
base64 < "$SIG_DER_FILE" | tr -d '\n' > "$SIG_B64_FILE"

# ---- summary ----
echo
echo "Generated files:"
echo "  - $TOKEN_FILE      (Approov-style JWT with ipk)"
echo "  - $MESSAGE_FILE    (@method/@target-uri)"
echo "  - $SIG_B64_FILE    (base64 DER ECDSA signature)"
echo
echo "curl example:"
echo "curl -i http://localhost:8002$PATH_ONLY \\"
echo "  -H \"Approov-Token: \$(cat $TOKEN_FILE)\" \\"
echo "  -H 'Signature-Input: install=(\"@method\" \"@target-uri\");alg=\"ecdsa-p256-sha256\"' \\"
echo "  -H \"Signature: install=:\$(cat $SIG_B64_FILE):\""

# ---- 5) optional: run the curl ----
if $DO_CURL; then
  echo
  echo "Running curl..."
  curl -i "http://localhost:8002$PATH_ONLY" \
    -H "Approov-Token: $(cat "$TOKEN_FILE")" \
    -H 'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
    -H "Signature: install:=$(cat "$SIG_B64_FILE"):"
fi
