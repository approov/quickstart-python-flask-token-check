#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./prep_request.sh [METHOD] [PATH]
#   defaults: METHOD=GET, PATH=/token
METHOD="${1:-GET}"
PATH_ONLY="${2:-/token}"

# Files we need
ENV_FILE=".env"
PUB_B64_FILE="public_key.b64"
PRIV_PEM_FILE="private_key.pem"

# Outputs
TOKEN_FILE="token.txt"
MESSAGE_FILE="message.txt"
SIG_DER_FILE="sig.der"
SIG_B64_FILE="signature.b64"

# 0) sanity checks
[[ -f "$PUB_B64_FILE" ]] || { echo "Missing $PUB_B64_FILE"; exit 1; }
[[ -f "$PRIV_PEM_FILE" ]] || { echo "Missing $PRIV_PEM_FILE"; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE"; exit 1; }
command -v openssl >/dev/null || { echo "openssl not found in PATH"; exit 1; }
command -v python >/dev/null || { echo "python not found in PATH"; exit 1; }

# 1) load APPROOV_BASE64_SECRET
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${APPROOV_BASE64_SECRET:?APPROOV_BASE64_SECRET missing in .env}"

# 2) mint a local JWT with ipk claim (reads public_key.b64)
python - << 'PY' "$APPROOV_BASE64_SECRET" "$PUB_B64_FILE" > token.txt
import jwt, base64, sys, time, json
secret_b64 = sys.argv[1]
pubfile = sys.argv[2]
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

# 3) build the message your Flask server reconstructs
printf '@method: %s\n@target-uri: %s' "$METHOD" "$PATH_ONLY" > "$MESSAGE_FILE"

# 4) sign the message with your EC private key (DER ECDSA)
openssl dgst -sha256 -sign "$PRIV_PEM_FILE" -out "$SIG_DER_FILE" "$MESSAGE_FILE"
base64 < "$SIG_DER_FILE" | tr -d '\n' > "$SIG_B64_FILE"

echo
echo "Generated files:"
echo "  - $TOKEN_FILE        (Approov-style JWT with ipk)"
echo "  - $MESSAGE_FILE      (@method/@target-uri)"
echo "  - $SIG_B64_FILE      (base64 DER ECDSA signature)"
echo
echo " Now run Step 5 (your curl). Example:"
echo "curl -i http://localhost:8002$PATH_ONLY \\"
echo "  -H \"Approov-Token: \$(cat $TOKEN_FILE)\" \\"
echo "  -H 'Signature-Input: install=(\"@method\" \"@target-uri\");alg=\"ecdsa-p256-sha256\"' \\"
echo "  -H \"Signature: install=:\$(cat $SIG_B64_FILE):\""
echo
