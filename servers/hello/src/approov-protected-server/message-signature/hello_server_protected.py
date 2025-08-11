from flask import Flask, jsonify, request, abort, make_response, g
import logging, base64, jwt
from os import getenv
from dotenv import load_dotenv, find_dotenv
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature

# ---------- setup ----------
load_dotenv(find_dotenv(), override=True)
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("approov_single_route")
api = Flask(__name__)

# Approov shared secret (base64)
approov_b64_secret = getenv("APPROOV_BASE64_SECRET")
if not approov_b64_secret:
    raise ValueError("Missing APPROOV_BASE64_SECRET in .env")
APPROOV_SECRET = base64.b64decode(approov_b64_secret)

def b64url_to_bytes(s: str) -> bytes:
    """Decode base64url (no +/ and maybe no =) into bytes."""
    pad = '=' * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode(s + pad)

# ---------- 1) Approov token check ----------
@api.before_request
def _verifyApproovToken():
    token = request.headers.get("Approov-Token")
    if not token:
        log.error("Missing Approov-Token")
        abort(make_response({"error": "Missing Approov-Token"}, 401))

    try:
        claims = jwt.decode(token, APPROOV_SECRET, algorithms=["HS256"])
        g.approov_claims = claims
        log.info("Approov token verified")
    except jwt.ExpiredSignatureError:
        log.error("Approov token expired")
        abort(make_response({"error": "Approov token expired"}, 401))
    except jwt.InvalidTokenError as e:
        log.error(f"Approov token invalid: {e}")
        abort(make_response({"error": "Approov token invalid"}, 401))

# ---------- 2) Message signature check (only if ipk present) ----------
@api.before_request
def _verifyMessageSignature():
    # Require the token check to have run first
    claims = getattr(g, "approov_claims", None)
    if not claims:
        return  # token gate already handled the aborts

    ipk_b64url = claims.get("ipk")
    if not ipk_b64url:
        return  # no ipk -> no message signature required

    sig_header = request.headers.get("Signature")           # e.g.  install=:BASE64SIG:
    sig_input  = request.headers.get("Signature-Input")     # not parsed here, just required
    if not sig_header or not sig_input:
        log.error("Missing Signature headers for ipk")
        abort(make_response({"error": "Missing Signature headers for ipk"}, 401))

    try:
        # Extract base64 signature between the colons: install=:...:
        parts = sig_header.split(":")
        if len(parts) < 3 or not parts[1]:
            raise ValueError("Bad Signature header format")
        sig_b64 = parts[1]
        signature = base64.b64decode(sig_b64)

        # Public key from ipk claim (DER, base64url)
        pubkey_der = b64url_to_bytes(ipk_b64url)
        pubkey = load_der_public_key(pubkey_der)

        # Canonical message MUST match what client signed
        method = request.method.upper()
        target_uri = request.path
        message = f"@method: {method}\n@target-uri: {target_uri}".encode("utf-8")
        log.debug(f"Verifying message:\n{message.decode()}")

        pubkey.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        g.signature_ok = True
        log.info("Message signature verified")
    except (InvalidSignature, ValueError, Exception) as e:
        log.error(f"Signature verification failed: {e}")
        abort(make_response({"error": "Invalid message signature"}, 401))

# ---------- one handler for everything ----------
@api.route("/", defaults={"path": ""}, methods=["GET","POST","PUT","DELETE","PATCH"])
@api.route("/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH"])
def any_path(path):
    resp = {
        "message": "Token Verified (and signature if ipk present)",
        "path": f"/{path}",
        "has_ipk": bool(getattr(g, "approov_claims", {}).get("ipk")),
    }
    return jsonify(resp), 200

if __name__ == "__main__":
    api.run(host="0.0.0.0", port=8002, debug=True)
