#!/usr/bin/env bash
# config/prep.sh — generate tokens & signatures your Flask server expects (quiet by default)

set -Eeuo pipefail

# Always resolve paths from the repo root (parent of this scripts/ folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEV="${DEV_DIR:-$REPO_ROOT/config}"   # <— now REPO_ROOT is defined before use
mkdir -p "$DEV" "$DEV/logs"

ENV_FILE="$DEV/.env"
AUTH_FILE="$DEV/authorization.txt"

TOK_CHECK="$DEV/token_check.txt"            # {exp}
TOK_BIND="$DEV/approov_token.txt"           # {exp, pay}  (pay = b64(sha256(Auth)))
TOK_MSG="$DEV/token.txt"                    # {exp, ipk}
TOK_BM="$DEV/token_bm.txt"                  # {exp, pay, ipk}  (pay = b64(sha256(Auth)))
TOK_CUSTOM="$DEV/token_custom.txt"          # {exp, pay}  (pay = b64(sha256(Auth + HeaderVal)))

HEADER_FILE="$DEV/header.txt"               # value for X-Header-Id

SIG_MSG="$DEV/signature.b64"
SIG_BM="$DEV/signature_bm.b64"
PRIV_PEM="$DEV/private_key.pem"
PUB_DER="$DEV/public_key.der"

# Set SHOW_PAYLOADS=1 to print decoded JWT payloads from the Python step
SHOW_PAYLOADS="${SHOW_PAYLOADS:-0}"

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE (APPROOV_BASE64_SECRET=...)"; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"
: "${APPROOV_BASE64_SECRET:?APPROOV_BASE64_SECRET missing in $ENV_FILE}"

command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }

# Ensure default header value exists for the custom-binding test
[[ -f "$HEADER_FILE" ]] || echo "dev-123" > "$HEADER_FILE"

python3 - "$APPROOV_BASE64_SECRET" "$AUTH_FILE" "$HEADER_FILE" "$PRIV_PEM" "$PUB_DER" \
         "$TOK_CHECK" "$TOK_BIND" "$TOK_MSG" "$TOK_BM" "$TOK_CUSTOM" "$SIG_MSG" "$SIG_BM" "$SHOW_PAYLOADS" <<'PY'
import sys, os, time, base64, hashlib, json, secrets
from pathlib import Path

# cryptography for ECDSA + key I/O
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

# PyJWT to mint HS256
import jwt

(SECRET_B64, AUTH_FILE, HEADER_FILE, PRIV_PEM, PUB_DER,
 TOK_CHECK, TOK_BIND, TOK_MSG, TOK_BM, TOK_CUSTOM, SIG_MSG, SIG_BM, SHOW_PAYLOADS) = sys.argv[1:]

show = str(SHOW_PAYLOADS) == "1"

DEV = Path("config"); DEV.mkdir(exist_ok=True)

# 1) Authorization header (no trailing newline)
auth_path = Path(AUTH_FILE)
if not auth_path.exists():
    auth_path.write_text("Bearer " + secrets.token_hex(16))
AUTH = auth_path.read_text().strip()

# 1b) X-Header-Id value
hdr_path = Path(HEADER_FILE)
HEADER_VAL = hdr_path.read_text().strip()

# 2) Ensure P-256 keypair; write public DER/SPKI
priv_path = Path(PRIV_PEM); pub_der_path = Path(PUB_DER)
if priv_path.exists():
    with open(priv_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
else:
    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    priv_path.write_bytes(pem)

public_key = private_key.public_key()
pub_der = public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
pub_der_path.write_bytes(pub_der)

# 3) Compute claims
PAY_SINGLE = base64.b64encode(hashlib.sha256(AUTH.encode("utf-8")).digest()).decode()
PAY_CONCAT = base64.b64encode(hashlib.sha256((AUTH+HEADER_VAL).encode("utf-8")).digest()).decode()
IPK = base64.urlsafe_b64encode(pub_der).decode().rstrip("=")

# 4) Mint HS256 JWTs with claims using the same secret as server
secret = base64.b64decode(SECRET_B64)
def mint(claims: dict) -> str:
    c = {"exp": int(time.time()) + 3600}
    c.update(claims)
    return jwt.encode(c, secret, algorithm="HS256")

Path(TOK_CHECK).write_text(mint({}))
Path(TOK_BIND).write_text(mint({"pay": PAY_SINGLE}))
Path(TOK_MSG).write_text(mint({"ipk": IPK}))
Path(TOK_BM).write_text(mint({"pay": PAY_SINGLE, "ipk": IPK}))
Path(TOK_CUSTOM).write_text(mint({"pay": PAY_CONCAT}))

# 5) Sign canonical strings expected by your server (no quotes)
def sign_to_b64(canonical: str) -> str:
    sig = private_key.sign(canonical.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode()

Path(SIG_MSG).write_text(sign_to_b64("@method: GET\n@target-uri: /message_signature"))
Path(SIG_BM).write_text(sign_to_b64("@method: GET\n@target-uri: /token_binding_message_signature"))

# 6) Optional payload printout (debug)
if show:
    def payload_of(jwt_str: str) -> dict:
        body = jwt_str.split(".")[1]
        body += "=" * (-len(body) % 4)
        return json.loads(base64.urlsafe_b64decode(body))
    print("\nDecoded payloads:")
    for name, path in [
        ("token_check.txt", TOK_CHECK),
        ("approov_token.txt (single-header pay)", TOK_BIND),
        ("token.txt (ipk)", TOK_MSG),
        ("token_bm.txt (single-header pay + ipk)", TOK_BM),
        ("token_custom.txt (concat pay)", TOK_CUSTOM),
    ]:
        tok = Path(path).read_text().strip()
        print(f"\n{name}:")
        print(json.dumps(payload_of(tok), indent=2))
PY

echo "Done."
echo "Artifacts written to $DEV:"
ls -l "$TOK_CHECK" "$TOK_BIND" "$TOK_MSG" "$TOK_BM" "$TOK_CUSTOM" "$HEADER_FILE" "$AUTH_FILE" "$PUB_DER" "$SIG_MSG" "$SIG_BM"