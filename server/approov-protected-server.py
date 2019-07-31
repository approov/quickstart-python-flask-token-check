# System packages
import logging
from random import choice
from base64 import b64decode, b64encode
from os import getenv
from hashlib import sha256

# Third part packages
import jwt
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, abort, make_response, jsonify

api = Flask(__name__)
api.config["JSON_SORT_KEYS"] = False

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

BAD_REQUEST_RESPONSE = {"status": "Bad Request"}

load_dotenv(find_dotenv(), override=True)

HTTP_PORT = int(getenv('HTTP_PORT', 5000))
APPROOV_BASE64_SECRET = getenv('APPROOV_BASE64_SECRET')

APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = True
_approov_enabled = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN', 'True').lower()
if _approov_enabled == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = False

APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM = True
_abort_on_invalid_claim = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM', 'True').lower()
if _abort_on_invalid_claim == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM = False

APPROOV_LOGGING_ENABLED = True
_approov_logging_enabled = getenv('APPROOV_LOGGING_ENABLED', 'True').lower()
if _approov_logging_enabled == 'false':
    APPROOV_LOGGING_ENABLED = False

def _getHeader(key, default_value = None):
    return request.headers.get(key, default_value)

def _isEmpty(value):
    return value is None or value == ""

def _getAuthorizationToken():
    authorization_token = _getHeader("Authorization")

    if _isEmpty(authorization_token):
        log.error('AUTHORIZATION TOKEN EMPTY')
        abort(make_response(jsonify(BAD_REQUEST_REPONSE), 400))

    return authorization_token

def _buildHelloResponse():
    return jsonify({
        "text": "Hello, World!",
        "status": "Hello, World! (healthy)"
    })

def _buildShapeResponse(status):
    shape = choice([
        "Circle",
        "Triangle",
        "Square",
        "Rectangle",
    ])

    return jsonify({
        "shape": shape,
        "status": shape + ' (' + status + ')'
    })

def _buildFormResponse(status):
    form = choice([
        'Sphere',
        'Cone',
        'Cube',
        'Box',
    ])

    return jsonify({
        "form": form,
        "status": form + ' (' + status + ')'
    })

def _logApproov(message):
    if APPROOV_LOGGING_ENABLED is True:
        log.info(message)

def _decodeApproovToken(approov_token):
    try:
        # Decode the approov token, allowing only the HS256 algorithm and using
        # the approov base64 encoded SECRET
        approov_token_decoded = jwt.decode(approov_token, b64decode(APPROOV_BASE64_SECRET), algorithms=['HS256'])

        return approov_token_decoded

    except jwt.InvalidSignatureError as e:
        _logApproov('APPROOV JWT TOKEN INVALID SIGNATURE: %s' % e)
        return None
    except jwt.ExpiredSignatureError as e:
        _logApproov('APPROOV JWT TOKEN EXPIRED: %s' % e)
        return None
    except jwt.InvalidTokenError as e:
        _logApproov('APPROOV JWT TOKEN INVALID: %s' % e)
        return None

def _getApproovToken():
    approov_token = _getHeader('approov-token')

    if _isEmpty(approov_token):
        _logApproov('APPROOV TOKEN HEADER IS EMPTY')
        return None

    approov_token_decoded = _decodeApproovToken(approov_token)

    if _isEmpty(approov_token_decoded):
        return None

    return approov_token_decoded

def _handleApproovProtectedRequest(approov_token_decoded):

    message = 'REQUEST WITH VALID APPROOV TOKEN'

    if not approov_token_decoded:
        message = 'REQUEST WITH INVALID APPROOV TOKEN'

    if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True and not approov_token_decoded:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

    _logApproov('ACCEPTED ' + message)

def _checkApproovCustomPayloadClaim(approov_token_decoded, claim_value):
    if _isEmpty(approov_token_decoded):
        return False

    # checking if the approov token contains a payload and verify it.
    if 'pay' in approov_token_decoded:

        # we need to hash and base64 encode the oauth2 token in order to verify
        # it matches the same one contained in the approov token payload.
        payload_claim_hash = sha256(claim_value.encode('utf-8')).digest()
        payload_claim_base64_hash = b64encode(payload_claim_hash).decode('utf-8')

        return approov_token_decoded['pay'] == payload_claim_base64_hash

    # The Approov failover running in the Google cloud doesn't return the custom
    # payload claim, thus we always need to have a pass when is not present.
    return True

def _handleApproovCustomPayloadClaim(approov_token_decoded, claim_value):

    message = 'REQUEST WITH VALID CUSTOM PAYLOAD CLAIM IN THE APPROOV TOKEN'

    valid_claim = _checkApproovCustomPayloadClaim(approov_token_decoded, claim_value)

    if not valid_claim:
        message = 'REQUEST WITH INVALID CUSTOM PAYLOAD CLAIM IN THE APPROOV TOKEN'

    if not valid_claim and APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM is True:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

    _logApproov('ACCEPTED ' + message)

@api.route("/")
def homePage():
    file = open('server/index.html', 'r')
    content = file.read()
    file.close()

    return content

@api.route("/v1/hello")
def hello():
    return _buildHelloResponse()

@api.route("/v1/shapes")
def shapes():
    return _buildShapeResponse('unprotected')

@api.route("/v1/forms")
def forms():
    # How to handle and validate the authorization token is out of scope for this tutorial.
    authorization_token = _getAuthorizationToken()

    return _buildFormResponse('unprotected')

@api.route("/v2/hello")
def helloV2():
    return _buildHelloResponse()


### APPROOV PROTECTED ENDPOINTS ###

@api.route("/v2/shapes")
def shapesV2():

    # Will get the Approov JWT token from the header, decode it and on success
    # will return it, otherwise None is returned.
    approov_token_decoded = _getApproovToken()

    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
    # when the decoded approov token is empty.
    _handleApproovProtectedRequest(approov_token_decoded)

    return _buildShapeResponse('protected')

@api.route("/v2/forms")
def formsV2():

    # Will get the Approov JWT token from the header, decode it and on success
    # will return it, otherwise None is returned.
    approov_token_decoded = _getApproovToken()

    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
    # when the decoded approov token is empty.
    _handleApproovProtectedRequest(approov_token_decoded)

    # How to handle and validate the authorization token is out of scope for this tutorial, but
    # you should only validate it after you have performed all the Approov checks.
    authorization_token = _getAuthorizationToken()

    # Checks if the custom payload claim in the Approov token is valid and aborts
    # the request if APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM is set to True.
    _handleApproovCustomPayloadClaim(approov_token_decoded, authorization_token)

    # Now you are free to handle and validate your Authorization token as you usually do.

    return _buildFormResponse('protected')
