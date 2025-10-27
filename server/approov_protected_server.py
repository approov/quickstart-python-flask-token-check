from __future__ import annotations
from flask import abort, current_app, Flask, make_response, request

from typing import Optional, Tuple, List, Iterable
from functools import wraps
import base64
import hashlib
import jwt
import os


# ---- Configuration ----


from dotenv import load_dotenv
load_dotenv()

DEFAULTS = {
    # initial Approov enabled/disabled state here:
    "APPROOV_ENABLED": True,  # Set to False to disable Approov by default
    "APPROOV_BASE64_SECRET": os.getenv("APPROOV_BASE64_SECRET"),
    "APPROOV_TOKEN_HEADER": os.getenv(
        "APPROOV_TOKEN_HEADER", "Approov-Token"
    ),
}


def init_approov(app) -> None:
    """
    Call once in your app factory or main module.
    Any missing keys get sensible defaults so the quickstart "just works".
 
    Parameters:
        app (flask.app.Flask):
            The Flask app to configure.
    """
    for k, v in DEFAULTS.items():
        print(k, v)
        app.config.setdefault(k, v)
    if not app.config.get("APPROOV_ENABLED", False):
        app.logger.warning("[approov] protection explicitly disabled")
        return  # Approov is disabled, we don't need the secret
    if not app.config.get("APPROOV_BASE64_SECRET"):
        raise Exception("[approov] 'APPROOV_BASE64_SECRET' must be set")


# ---- Helpers ----

def _get_approov_token_from_request(req) -> Optional[str]:
    """
    Extracts the Approov token from the Flask request.

    Parameters:
        req (flask.Request):
            The Flask Request object.

    Returns:
        Optional[str]: An Approov token, if it exists. Otherwise None.
    """
    target_header = current_app.config.get("APPROOV_TOKEN_HEADER")
    return req.headers.get(target_header, None)


def _build_token_binding_string(req, bound_headers: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Constructs a binding string from a list of target headers.

    Parameters:
        req (flask.Request):
            The Flask Request object.
        bound_headers (list[str]):
            An ordered list of headers to construct the binding string from.
            This should never be set to None when invoking this function.

    Returns:
        Optional[str]:
            An optional error reason. None if no error occurred.
        Optional[str]:
            The constructed binding string. None if an error occurred.
    """
    if not bound_headers:
        return "[approov] binding headers not specified", None

    values: List[str] = []
    for header in bound_headers:
        val = req.headers.get(header)
        if val is None:
            error = f"[approov] bound header '{header}' does not exist"
            return error, None
        values.append(val)

    # NOTE: The server and client must agree on the binding string format.
    #       We do not pad the input strings for this example.
    binding_string = "".join(values)

    return None, binding_string


def _sha256_b64_from_str(s: str) -> str:
    """
    Calculates a base64-encoded SHA256 hash from a given string.

    Parameters:
        s (str):
            The string to hash and encode.

    Returns:
        str: The base64-encoded SHA256 hash.
    """
    digest = hashlib.sha256(s.encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


# ---- Approov Quickstart Function ----

def approov(req, token_check: bool = True,
            bound_headers: Optional[list[str]] = None,
            message_signing: bool = False) -> Optional[str]:
    """
    Demonstrates Approov protection modes on a given request.
    Currently implemented modes are:
        * Token Verification
        * Token Binding (to one or multiple Header values)

    Parameters:
        req (flask.Request):
            The Flask request object.
        token_check (bool):
            If True, perform Approov token verification.
            This is a pre-requisite for Token Binding and Message Signing.
            Default is True.
        bound_headers (list[str] | None).
            If provided, enforce token binding against these headers.
            Default is None.
        message_signing (bool):
            If True, perform HTTP message signature verification.
            Default is False.

    Returns:
        Optional[str]: An error string, if applicable. Otherwise None.
    """

    # --- 0) Approov Protection Disabled
    if not token_check or not current_app.config.get("APPROOV_ENABLED"):
        current_app.logger.warning("[approov] endpoint protection is disabled")
        return None
    # --- 1) Approov Token Verification
    else:
        token = _get_approov_token_from_request(req)

        # Does the Approov token exist?
        if not token:
            return f"[approov] missing {current_app.config.get('APPROOV_TOKEN_HEADER')} header"

        try:
            claims = jwt.decode(
                token,
                base64.b64decode(current_app.config.get("APPROOV_BASE64_SECRET")),
                algorithms=["HS256"],
                options={
                    "verify_signature": True,   # Signature must be good
                    "verify_exp": True,         # Expiry must be valid
                },
            )
            # So far so good - the Approov token is valid!
            current_app.logger.debug("[approov] token signature and expiry are good")
            pass
        except jwt.ExpiredSignatureError:
            return "[approov] token expired"
        except jwt.InvalidSignatureError:
            return "[approov] token signature invalid"
        except jwt.InvalidTokenError as e:
            return f"[approov] token invalid: {str(e)}"

    # --- 2) Approov Token Binding
    if bound_headers:
        pay = claims.get("pay")
        if pay is None:
            return f"[approov] token does not have a 'pay' claim"

        error, binding_string = _build_token_binding_string(req, bound_headers)
        if error:
            return error

        computed = _sha256_b64_from_str(binding_string)

        if not (computed == pay):
            return f"[approov] token binding: hash mismatch (expected '{computed}', got '{pay}')"

        current_app.logger.debug(f"[approov] token binding verification successful for {bound_headers}")

    # --- 3) Approov Message Signing
    if message_signing:
        # TODO: Implement SFV/IPK signature verification.
        return "[approov] message signing not implemented"

    # We now export the Approov claims for any downstream functions.
    #   These are trivially accessible via g.approov_claims if hasattr(g, 'approov_claims') else '' anywhere
    #   within the Flask app scope.
    from flask import g
    g.approov_claims = claims

    # Verification completed successfully.
    current_app.logger.debug("[approov] token verification successful")
    return None

# ---- Approov Quickstart Decorator ----
def require_approov(
    *,
    bound_headers: Optional[Iterable[str]] = None,
    message_signing: bool = False,
    status_code: int = 401,
):
    """
    Drop-in decorator for protected endpoints.

    Example:
        @app.get("/endpoint")
        @require_approov(bound_headers=["Authorization"])
        def endpoint():
            ...

    Please see the approov function for parameter docs.
    """
    def _decorator(f):
        @wraps(f)
        def _wrapped(*args, **kwargs):
            err = approov(
                request,
                bound_headers=bound_headers,
                message_signing=message_signing,
            )
            if err is not None:
                current_app.logger.warning(f"[approov] request aborted: {err}")
                abort(make_response(("Unauthorized", status_code)))
            return f(*args, **kwargs)
        return _wrapped
    return _decorator


# ---- Flask Application ----

app = Flask(__name__)


# Approov Disabled
@app.route("/unprotected")
def unprotected():
    return "OK", 200


# Approov Token Checking
@app.route("/token-check")
@require_approov()
def token_check():
    from flask import g
    app.logger.debug(f"[approov] claims: {g.approov_claims if hasattr(g, 'approov_claims') else ''}")
    return "OK", 200


# Approov Token Binding to Authorization Header
#   (requires Approov Token Checking)
@app.route("/token-binding-1")
@require_approov(bound_headers=["Authorization"])
def token_binding_1():
    from flask import g
    app.logger.debug(f"[approov] claims: {g.approov_claims if hasattr(g, 'approov_claims') else ''}")
    return "OK", 200


# Approov Token Binding to Multiple Headers
#   (requires Approov Token Checking)
@app.route("/token-binding-2")
@require_approov(bound_headers=["Authorization", "Content-Digest"])
def token_binding_2():
    from flask import g
    app.logger.debug(f"[approov] claims: {g.approov_claims if hasattr(g, 'approov_claims') else ''}")
    return "OK", 200


# Approov Message Signing
#   (requires Approov Token Checking)
@app.route("/msg-sig")
@require_approov(message_signing=True)
def msg_sig():
    from flask import g
    app.logger.debug(f"[approov] claims: {g.approov_claims if hasattr(g, 'approov_claims') else ''}")
    return "OK", 200


# Approov Message Signing + Token Binding to Authorization Header
#   (requires Approov Token Checking)
@app.route("/msg-sig-token-binding")
@require_approov(bound_headers=["Authorization"], message_signing=True)
def msg_sig_token_binding():
    from flask import g
    app.logger.debug(f"[approov] claims: {g.approov_claims if hasattr(g, 'approov_claims') else ''}")
    return "OK", 200


@app.route("/approov-state")
def approov_state():
    if app.config.get("APPROOV_ENABLED"):
        return "OK", 200
    return "Not Implemented", 501

# ---- Approov Enable/Disable Endpoints ----

# Disable Approov protection
@app.route("/approov-disable", methods=["POST"])
def disable_approov():
    app.config["APPROOV_ENABLED"] = False
    app.logger.warning("[approov] protection explicitly disabled via API")
    return "Approov protection disabled", 200

# Enable Approov protection
@app.route("/approov-enable", methods=["POST"])
def enable_approov():
    app.config["APPROOV_ENABLED"] = True
    app.logger.info("[approov] protection enabled via API")
    return "Approov protection enabled", 200


# --- Main ---

if __name__ == "__main__":
    init_approov(app)
    app.run(host="0.0.0.0", port=8080, debug=True)
