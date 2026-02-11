#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
from functools import wraps
from typing import Any, Iterable, Optional, Tuple, TypeGuard

import jwt
from flask import Flask, Request, Response, current_app, g, jsonify, request

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional helper dependency
    def load_dotenv() -> bool:
        return False

APPROOV_HEADER = "Approov-Token"
AUTH_HEADER = "Authorization"
SESSION_ID_HEADER = "SessionId"
PLACEHOLDER_SECRET = "approov_base64url_secret_here"
APPROOV_ENABLED_KEY = "APPROOV_ENABLED"
TOKEN_BINDING_ENABLED_KEY = "TOKEN_BINDING_ENABLED"
APPROOV_TOKEN_HEADER_KEY = "APPROOV_TOKEN_HEADER"
APPROOV_SECRET_KEY = "APPROOV_SECRET"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _has_text(value: Optional[str]) -> TypeGuard[str]:
    return value is not None and value.strip() != ""


def _decode_base64url(secret: str) -> bytes:
    padding = "=" * (-len(secret) % 4)
    return base64.urlsafe_b64decode(secret + padding)


def _normalize_base64url(value: str) -> str:
    return value.strip().replace("+", "-").replace("/", "_").rstrip("=")


def load_approov_secret() -> bytes:
    logger = logging.getLogger("approov")
    raw_secret = os.getenv("APPROOV_BASE64URL_SECRET")
    if not _has_text(raw_secret):
        logger.error("Required secret is not set")
        raise RuntimeError("Required secret is not set")

    normalized_secret = raw_secret.strip()
    if normalized_secret == PLACEHOLDER_SECRET:
        logger.error("Required secret is not set")
        raise RuntimeError("Required secret is not set")

    try:
        decoded = _decode_base64url(normalized_secret)
    except (binascii.Error, ValueError):
        logger.error("Required secret is invalid")
        raise RuntimeError("Required secret is invalid")

    if len(decoded) < 32:
        logger.error("Required secret is invalid")
        raise RuntimeError("Required secret is invalid")

    return decoded


def init_approov(app: Flask) -> None:
    app.config[APPROOV_ENABLED_KEY] = True
    app.config[TOKEN_BINDING_ENABLED_KEY] = True
    app.config[APPROOV_TOKEN_HEADER_KEY] = APPROOV_HEADER
    app.config[APPROOV_SECRET_KEY] = load_approov_secret()


def _get_approov_token_from_request(req: Request) -> Optional[str]:
    target_header = current_app.config.get(APPROOV_TOKEN_HEADER_KEY, APPROOV_HEADER)
    return req.headers.get(target_header)


def _build_token_binding_string(
    req: Request, bound_headers: list[str]
) -> Tuple[Optional[str], Optional[str]]:
    if not bound_headers:
        return "[approov] binding headers not specified", None

    values: list[str] = []
    for header in bound_headers:
        value = req.headers.get(header)
        if not _has_text(value):
            return f"[approov] bound header '{header}' does not exist", None
        values.append(value.strip())

    return None, "".join(values)


def _sha256_b64url_from_str(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _binding_matches(pay_claim: str, computed_hash: str) -> bool:
    return hmac.compare_digest(
        _normalize_base64url(pay_claim), _normalize_base64url(computed_hash)
    )


def _summarize_error(error: str) -> str:
    if "missing Approov-Token header" in error:
        return "missing_approov_token"
    if "bound header" in error and "does not exist" in error:
        return "missing_binding_header"
    if "hash mismatch" in error or "does not have a 'pay' claim" in error:
        return "binding_mismatch"
    return "token_verification_failed"


def _required_headers_for_request(bound_headers: list[str]) -> list[str]:
    approov_header = str(current_app.config.get(APPROOV_TOKEN_HEADER_KEY, APPROOV_HEADER))
    if (not current_app.config[TOKEN_BINDING_ENABLED_KEY]) or (not bound_headers):
        return [approov_header]
    return [approov_header, *bound_headers]


def _unauthorized_response(error: str) -> tuple[Response, int]:
    g.approov_summary = f"approov_failed:{_summarize_error(error)}"
    g.approov_error = error
    return jsonify({"message": "Unauthorized"}), 401


def approov(
    req: Request,
    token_check: bool = True,
    bound_headers: Optional[list[str]] = None,
) -> Optional[str]:
    if not token_check or not current_app.config[APPROOV_ENABLED_KEY]:
        current_app.logger.warning("[approov] endpoint protection is disabled")
        g.approov_claims = {}
        return None

    token = _get_approov_token_from_request(req)
    if not _has_text(token):
        return (
            f"[approov] missing {current_app.config.get(APPROOV_TOKEN_HEADER_KEY, APPROOV_HEADER)} header"
        )

    try:
        claims = jwt.decode(
            token.strip(),
            current_app.config[APPROOV_SECRET_KEY],
            algorithms=["HS256"],
            options={
                "require": ["exp"],
                "verify_signature": True,
                "verify_exp": True,
            },
        )
    except jwt.ExpiredSignatureError:
        return "[approov] token expired"
    except jwt.InvalidSignatureError:
        return "[approov] token signature invalid"
    except jwt.InvalidTokenError as error:
        return f"[approov] token invalid: {error}"

    if bound_headers:
        pay_claim = claims.get("pay")
        if pay_claim is None or (isinstance(pay_claim, str) and not _has_text(pay_claim)):
            return "[approov] token does not have a 'pay' claim"
        if not isinstance(pay_claim, str):
            return "[approov] token does not have a valid 'pay' claim"

        binding_error, binding_string = _build_token_binding_string(req, bound_headers)
        if binding_error is not None or binding_string is None:
            return binding_error

        computed = _sha256_b64url_from_str(binding_string)
        if not _binding_matches(pay_claim, computed):
            return (
                "[approov] token binding: hash mismatch "
                f"(expected '{computed}', got '{pay_claim}')"
            )

        current_app.logger.debug(
            "[approov] token binding verification successful for %s", bound_headers
        )

    g.approov_claims = claims
    current_app.logger.debug("[approov] token verification successful")
    return None


def require_approov(
    *,
    bound_headers: Optional[Iterable[str]] = None,
):
    configured_bound_headers = list(bound_headers or [])

    def _decorator(function):
        @wraps(function)
        def _wrapped(*args: Any, **kwargs: Any):
            g.approov_error = None
            g.required_headers = _required_headers_for_request(configured_bound_headers)

            if not current_app.config[APPROOV_ENABLED_KEY]:
                g.approov_summary = "approov_disabled"
                g.approov_claims = {}
                return function(*args, **kwargs)

            active_bound_headers = (
                configured_bound_headers
                if current_app.config[TOKEN_BINDING_ENABLED_KEY]
                else []
            )
            error = approov(
                request,
                token_check=True,
                bound_headers=active_bound_headers,
            )
            if error is not None:
                return _unauthorized_response(error)
            g.approov_summary = "approov_ok"
            return function(*args, **kwargs)

        return _wrapped

    return _decorator


def state_payload() -> dict[str, Any]:
    return {
        "approovEnabled": bool(current_app.config[APPROOV_ENABLED_KEY]),
        "tokenBindingEnabled": bool(current_app.config[TOKEN_BINDING_ENABLED_KEY]),
    }


def info_payload(details: str) -> dict[str, Any]:
    body = state_payload()
    body["details"] = details
    return body


def _request_server_port() -> int:
    server_port = request.environ.get("SERVER_PORT")
    if isinstance(server_port, str):
        normalized_server_port = server_port.strip()
        if normalized_server_port:
            try:
                return int(normalized_server_port)
            except ValueError:
                pass
    configured = os.getenv("HTTP_PORT", "8080")
    try:
        return int(configured)
    except ValueError:
        return 8080


def _log_http_request_completed(response: Response) -> None:
    if response.status_code not in (200, 401):
        return

    required_headers = getattr(g, "required_headers", [])
    summary = getattr(g, "approov_summary", "request_completed")
    if response.status_code == 401 and summary == "approov_ok":
        summary = "approov_failed:downstream_unauthorized"

    payload = {
        "summary": summary,
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "ip": request.remote_addr or "",
        "port": _request_server_port(),
        "approovEnabled": bool(current_app.config[APPROOV_ENABLED_KEY]),
        "tokenBindingEnabled": bool(current_app.config[TOKEN_BINDING_ENABLED_KEY]),
        "required_headers": required_headers,
    }

    error = getattr(g, "approov_error", None)
    if error:
        payload["error"] = error

    message = "http.request.completed " + json.dumps(payload, separators=(",", ":"))

    if response.status_code == 401:
        current_app.logger.warning(message)
    else:
        current_app.logger.info(message)


def create_app() -> Flask:
    load_dotenv()
    configure_logging()
    app = Flask(__name__)
    init_approov(app)

    @app.after_request
    def emit_request_log(response: Response):
        _log_http_request_completed(response)
        return response

    @app.get("/")
    def home():
        return jsonify(info_payload("Approov demo API is running on port 8080.")), 200

    @app.get("/approov-state")
    def approov_state():
        return jsonify(state_payload()), 200

    @app.post("/approov/enable")
    def enable_approov_endpoint():
        app.config[APPROOV_ENABLED_KEY] = True
        app.config[TOKEN_BINDING_ENABLED_KEY] = True
        return jsonify(state_payload()), 200

    @app.post("/approov/disable")
    def disable_approov_endpoint():
        app.config[APPROOV_ENABLED_KEY] = False
        app.config[TOKEN_BINDING_ENABLED_KEY] = False
        return jsonify(state_payload()), 200

    @app.post("/token-binding/enable")
    def enable_token_binding_endpoint():
        app.config[TOKEN_BINDING_ENABLED_KEY] = True
        return jsonify(state_payload()), 200

    @app.post("/token-binding/disable")
    def disable_token_binding_endpoint():
        app.config[TOKEN_BINDING_ENABLED_KEY] = False
        return jsonify(state_payload()), 200

    @app.get("/unprotected")
    def unprotected():
        return jsonify(
            info_payload(
                "Unprotected endpoint '/unprotected'; no Approov checks performed."
            )
        ), 200

    @app.get("/token-check")
    @require_approov()
    def token_check():
        return jsonify(
            info_payload("Protected endpoint '/token-check'; Approov token verified.")
        ), 200

    @app.get("/token-binding")
    @require_approov(bound_headers=[AUTH_HEADER])
    def token_binding():
        response = info_payload(
            "Protected endpoint '/token-binding'; Approov token binding enforced."
        )
        response["authorizationHeaderPresent"] = _has_text(request.headers.get(AUTH_HEADER))
        return jsonify(response), 200

    @app.get("/token-double-binding")
    @require_approov(bound_headers=[AUTH_HEADER, SESSION_ID_HEADER])
    def token_double_binding():
        response = info_payload(
            "Protected endpoint '/token-double-binding'; dual token binding enforced."
        )
        response["authorizationHeaderPresent"] = _has_text(request.headers.get(AUTH_HEADER))
        response["sessionIdHeaderPresent"] = _has_text(request.headers.get(SESSION_ID_HEADER))
        return jsonify(response), 200

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("SERVER_HOSTNAME", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", "8080"))
    app.run(host=host, port=port, debug=False)
