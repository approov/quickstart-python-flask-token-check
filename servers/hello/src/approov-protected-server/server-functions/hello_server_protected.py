#!/usr/bin/env python3
# unified_server.py

from flask import Flask, jsonify, request, abort, make_response, g
import logging, base64, hashlib, jwt
from os import getenv
from dotenv import load_dotenv, find_dotenv

# Message Signature (ECDSA P-256)
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature

# ---------- setup ----------
load_dotenv(find_dotenv(), override=True)
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("approov_unified")
api = Flask(__name__)
api.config["JSON_SORT_KEYS"] = False

# Approov shared secret (base64)
approov_b64_secret = getenv("APPROOV_BASE64_SECRET")
if not approov_b64_secret:
    raise ValueError("Missing APPROOV_BASE64_SECRET in .env")
APPROOV_SECRET = base64.b64decode(approov_b64_secret)

def error(status: int, msg: str):
    abort(make_response(jsonify({"error": msg}), status))

def b64url_to_bytes(s: str) -> bytes:
    """Decode base64url (no +/ and maybe no =) into bytes."""
    pad = '=' * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode(s + pad)

# ---------- checks (as functions) ----------

def check_approov_token(token: str):
    """Verify Approov-Token (HS256). On success, store claims in g.approov_claims."""
    if not token:
        error(401, "Missing Approov-Token")
    try:
        claims = jwt.decode(token, APPROOV_SECRET, algorithms=["HS256"])
        g.approov_claims = claims
        log.info("Approov token verified")
        return claims
    except jwt.ExpiredSignatureError:
        error(401, "Approov token expired")
    except jwt.InvalidTokenError as e:
        log.error(f"Approov token invalid: {e}")
        error(401, "Approov token invalid")

def check_token_binding(claims: dict, authorization: str):
    """Verify token binding when Authorization header and/or 'pay' claim are present."""
    if not claims:
        error(400, "Approov token required for token binding check")
    if not authorization:
        error(400, "Authorization header required for token binding check")
    if "pay" not in claims:
        error(401, "Approov token missing 'pay' claim for token binding")
    # Compare pay == b64(sha256(Authorization))
    auth_hash = hashlib.sha256(authorization.encode("utf-8")).digest()
    auth_b64 = base64.b64encode(auth_hash).decode("utf-8")
    if claims["pay"] != auth_b64:
        error(401, "Token binding mismatch")
    log.info("Token binding verified")

def check_message_signature(claims: dict, sig_header: str, sig_input: str, method: str, path: str):
    """Verify HTTP Message Signature when ipk is present or signature headers are sent."""
    if not claims:
        error(400, "Approov token required for message signature check")
    ipk_b64url = claims.get("ipk")
    if not ipk_b64url:
        error(401, "Approov token missing 'ipk' claim required for message signature")
    if not sig_header or not sig_input:
        error(401, "Missing Signature/Signature-Input headers")

    try:
        # Expect a label like:  install=:BASE64SIG:
        parts = sig_header.split(":")
        if len(parts) < 3 or not parts[1]:
            raise ValueError("Bad Signature header format")
        sig_b64 = parts[1]
        signature = base64.b64decode(sig_b64)

        # Public key from ipk (DER, base64url)
        pubkey_der = b64url_to_bytes(ipk_b64url)
        pubkey = load_der_public_key(pubkey_der)

        # Canonical message must match client
        message = f"@method: {method.upper()}\n@target-uri: {path}".encode("utf-8")
        log.debug(f"MSG-SIG verifying:\n{message.decode()}")

        pubkey.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        g.signature_ok = True
        log.info("Message signature verified")
    except (InvalidSignature, ValueError, Exception) as e:
        log.error(f"Message signature verification failed: {e}")
        error(401, "Invalid message signature")

# ---------- single dynamic endpoint ----------
@api.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@api.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def unified(path):
    """
    Dynamic behavior based on headers you send:
      - No special headers → unprotected
      - Approov-Token only → token check
      - Approov-Token + Authorization/pay → token binding
      - Approov-Token + ipk + Signature headers → message signature
    Priority: token → message signature (if ipk/signature present) → token binding → unprotected.
    """
    token = request.headers.get("Approov-Token")
    authorization = request.headers.get("Authorization")
    sig_header = request.headers.get("Signature")
    sig_input = request.headers.get("Signature-Input")

    # If someone sends binding/signature headers without a token, fail fast with 400.
    if (authorization or sig_header or sig_input) and not token:
        error(400, "Approov-Token is required when sending Authorization or Signature headers")

    # 1) Token present ⇒ verify token
    if token:
        claims = check_approov_token(token)

        # 1a) If ipk present OR signature headers provided ⇒ message signature path
        if claims.get("ipk") or (sig_header and sig_input):
            check_message_signature(claims, sig_header, sig_input, request.method, request.path)
            return jsonify({
                "mode": "message_signature",
                "path": f"/{path}",
                "has_ipk": True,
                "status": "ok"
            }), 200

        # 1b) Else if Authorization present OR token has 'pay' ⇒ token binding path
        if authorization or ("pay" in claims):
            check_token_binding(claims, authorization)
            return jsonify({
                "mode": "token_binding",
                "path": f"/{path}",
                "has_pay": "pay" in claims,
                "status": "ok"
            }), 200

        # 1c) Token only
        return jsonify({
            "mode": "token_only",
            "path": f"/{path}",
            "status": "ok"
        }), 200

    # 2) No token & no binding/signature headers ⇒ unprotected
    return jsonify({
        "mode": "unprotected",
        "path": f"/{path}",
        "status": "ok"
    }), 200


if __name__ == "__main__":
    api.run(host="0.0.0.0", port=int(getenv("HTTP_PORT", "8002")), debug=True)
