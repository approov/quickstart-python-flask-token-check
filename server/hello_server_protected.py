#!/usr/bin/env python3

from flask import Flask, jsonify, request, abort, make_response
import logging, base64, hashlib, re, os, sys, jwt
from pathlib import Path

# Message Signature (ECDSA P-256)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature

from dotenv import load_dotenv

# ----------------- load .env -----------------
CONFIG_DIR = os.getenv("DEV_DIR", "config")
ENV_PATH = Path(__file__).resolve().parent / CONFIG_DIR / ".env"
load_dotenv(ENV_PATH, override=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("approov_tests")

api = Flask(__name__)
api.config["JSON_SORT_KEYS"] = False

# ----------------- ON/OFF switch (code-only) -----------------
# Set this to True to enforce all checks, False to bypass them.
CHECKS_ENABLED = True

# Port comes from env (HTTP_PORT), but can be overridden by CLI arg (digits only)
SERVER_HOSTNAME = os.getenv("SERVER_HOSTNAME")
HTTP_PORT = int(os.getenv("HTTP_PORT"))
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    HTTP_PORT = int(sys.argv[1])

# Header name for custom binding; keep in sync with prep/tests (default X-Header-Id)
CUSTOM_BINDING_HEADER = os.getenv("CUSTOM_BINDING_HEADER", "X-Header-Id")

def _b64_loose_decode(s: str) -> bytes:
    """Tolerant base64/base64url decode (strip ws, fix padding)."""
    s = re.sub(r"\s+", "", (s or "").strip())
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * ((4 - (len(s) % 4)) % 4)
    return base64.b64decode(s)

APPROOV_B64_SECRET = os.getenv("APPROOV_BASE64_SECRET")
if not APPROOV_B64_SECRET:
    raise ValueError(f"Missing APPROOV_BASE64_SECRET in {CONFIG_DIR}/.env")
APPROOV_SECRET = _b64_loose_decode(APPROOV_B64_SECRET)

# -------- logging helpers --------
def _pass(test: str, extra: str = ""):
    msg = f"{test}: PASSED"
    if extra:
        msg += f" — {extra}"
    log.info(msg)

def _fail(test: str, reason: str, status: int = 401):
    log.error(f"{test}: FAILED — {reason}")
    abort(make_response(jsonify({"error": reason, "test": test}), status))

def _hash_b64(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("utf-8")

def _claims_subset(claims):
    try:
        return sorted(list(claims.keys()))
    except Exception:
        return []

# -------- low-level checks (names unchanged) --------
def verifyApproovToken(test_name: str):
    token = request.headers.get("Approov-Token") or request.headers.get("approov-token")
    if not token:
        _fail(test_name, "Missing Approov-Token", 401)
    try:
        claims = jwt.decode(token, APPROOV_SECRET, algorithms=["HS256"])
        _pass("Token check")
        return claims
    except jwt.ExpiredSignatureError:
        _fail("Token check", "Approov token expired", 401)
    except jwt.InvalidTokenError as e:
        _fail("Token check", f"Approov token invalid ({e})", 401)

def verifyApproovTokenBinding(claims: dict, test_name: str):
    """Single-header binding: pay must equal b64(sha256(Authorization))."""
    auth = request.headers.get("Authorization")
    if not auth:
        _fail(test_name, "Authorization header required for token binding", 400)
    if "pay" not in claims:
        _fail(test_name, "Approov token missing 'pay' claim for token binding", 401)

    pay_from_auth = _hash_b64(auth)
    if claims["pay"] != pay_from_auth:
        _fail(test_name, "Token binding mismatch", 401)

    _pass("Token binding")
    return {"authorization": auth, "computed_pay": pay_from_auth, "token_pay": claims["pay"]}

def verifyApproovTokenBindingCustom(claims: dict, test_name: str):
    """
    Two-header binding (concat): require Authorization + CUSTOM_BINDING_HEADER.
    pay must equal b64(sha256(Authorization + customHeaderValue))
    """
    auth = request.headers.get("Authorization")
    custom = request.headers.get(CUSTOM_BINDING_HEADER)
    if not auth or not custom:
        _fail(test_name, f"Both 'Authorization' and '{CUSTOM_BINDING_HEADER}' headers are required", 400)
    if "pay" not in claims:
        _fail(test_name, "Approov token missing 'pay' claim for token binding", 401)

    expected = _hash_b64(auth + custom)  # exact concatenation, no spaces
    if claims["pay"] != expected:
        _fail(test_name, "Token binding mismatch (Authorization + custom header)", 401)

    _pass("Token binding (two headers, concat)")
    return {
        "custom_header_name": CUSTOM_BINDING_HEADER,
        "authorization": auth,
        CUSTOM_BINDING_HEADER: custom,
        "computed_pay_from_concat": expected,
        "token_pay": claims["pay"],
        "matched": "authorization+custom",
    }

def _b64url_to_bytes(s: str) -> bytes:
    pad = "=" * ((4 - (len(s or "") % 4)) % 4)
    return base64.urlsafe_b64decode((s or "") + pad)

def verifyMessageSignature(claims: dict, test_name: str):
    ipk_b64url = claims.get("ipk")
    if not ipk_b64url:
        _fail(test_name, "Approov token missing 'ipk' claim required for message signature", 401)

    sig_header = request.headers.get("Signature")
    sig_input  = request.headers.get("Signature-Input")
    if not sig_header or not sig_input:
        _fail(test_name, "Missing Signature/Signature-Input headers", 401)

    parts = sig_header.split(":")
    if len(parts) < 3 or not parts[1]:
        _fail(test_name, "Bad Signature header format", 401)

    signature = base64.b64decode(parts[1])
    pubkey_der = _b64url_to_bytes(ipk_b64url)
    pubkey = load_der_public_key(pubkey_der)

    canonical = f"@method: {request.method.upper()}\n@target-uri: {request.path}".encode("utf-8")
    try:
        pubkey.verify(signature, canonical, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        _fail(test_name, "Invalid message signature", 401)

    _pass("Message signature")
    return {"has_ipk": True}

# -------- mode dispatcher --------
def run_mode(mode: str):
    if mode == "unprotected":
        _pass("Unprotected")
        return jsonify({"mode": mode, "status": "ok"}), 200

    # If checks are OFF, return OK immediately for protected modes
    if not CHECKS_ENABLED:
        _pass(f"{mode}", "checks disabled")
        return jsonify({"mode": mode, "status": "ok", "checks": "disabled"}), 200

    if mode == "token_check":
        claims = verifyApproovToken("Token test")
        return jsonify({"mode": mode, "status": "ok", "claims_subset": _claims_subset(claims)}), 200

    if mode == "token_binding":
        claims = verifyApproovToken("Token test")
        verifyApproovTokenBinding(claims, "Token binding test")
        return jsonify({"mode": mode, "status": "ok"}), 200

    if mode == "message_signature":
        claims = verifyApproovToken("Token test")
        verifyMessageSignature(claims, "Message signature test")
        return jsonify({"mode": mode, "status": "ok"}), 200

    if mode == "token_binding_message_signature":
        claims = verifyApproovToken("Token test")
        verifyApproovTokenBinding(claims, "Token binding test")
        verifyMessageSignature(claims, "Message signature test")
        return jsonify({"mode": mode, "status": "ok"}), 200

    if mode == "token_binding_custom":
        claims = verifyApproovToken("Token test")
        echo = verifyApproovTokenBindingCustom(claims, "Token binding custom test")
        return jsonify({"mode": mode, "status": "ok", **echo}), 200

    _fail("Routing", f"Unknown mode: {mode}", 404)

# -------- endpoints --------
@api.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def unprotected_server():
    return run_mode("unprotected")

@api.route("/token_check", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def token_check():
    return run_mode("token_check")

@api.route("/token_binding", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def token_binding():
    return run_mode("token_binding")

@api.route("/message_signature", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def message_signature():
    return run_mode("message_signature")

@api.route("/token_binding_message_signature", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def token_binding_message_signature():
    return run_mode("token_binding_message_signature")

@api.route("/token_binding_custom", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def token_binding_custom():
    return run_mode("token_binding_custom")

# -------- state endpoint --------
@api.route("/token_state", methods=["GET"])
def token_state():
    msg = "Token check is enabled" if CHECKS_ENABLED else "Token check is disabled"
    return make_response(msg, 200, {"Content-Type": "text/plain; charset=utf-8"})

if __name__ == "__main__":
    api.run(host=SERVER_HOSTNAME, port=HTTP_PORT, debug=False)
