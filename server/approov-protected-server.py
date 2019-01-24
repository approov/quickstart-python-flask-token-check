# System packages
import logging
from base64 import b64decode, b64encode
from os import getenv
from hashlib import sha256
from random import choice

# Third part packages
import jwt
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, abort, make_response, jsonify

api = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

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

def _isEmpty(token):
    return token is None or token == ""

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
        abort(make_response(jsonify({}), 400))

    _logApproov('ACCETPED ' + message)

def _handleApproovCustomPayloadClaim(approov_token_decoded, claim_value):

    message = 'REQUEST WITH VALID CUSTOM PAYLOAD CLAIM IN THE APPROOV TOKEN'

    valid_claim = _checkApproovCustomPayloadClaim(approov_token_decoded, claim_value)

    if not valid_claim:
        message = 'REQUEST WITH INVALID CUSTOM PAYLOAD CLAIM IN THE APPROOV TOKEN'

    if APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM is True:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify({}), 400))

    _logApproov('ACCETPED ' + message)

@api.route("/")
def endpoints():
    return jsonify(
        hello="http://localhost:%i/hello" % HTTP_PORT,
        shapes="http://localhost:%i/shapes" % HTTP_PORT,
        forms="http://localhost:%i/forms" % HTTP_PORT
    )

@api.route("/hello")
def hello():
    return jsonify(hello="Hello World!")

@api.route("/shapes")
def shapes():

    # Will get the Approov JWT token from the header, decode it and on success
    # will return it, otherwise None is returned.
    approov_token_decoded = _getApproovToken()

    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
    # when the decoded approov token is empty.
    _handleApproovProtectedRequest(approov_token_decoded)

    shape = choice([
        "Circle",
        "Triangle",
        "Square",
        "Rectangle",
    ])

    return jsonify(shape=shape)

@api.route("/forms")
def forms():

    oauth2_token = _getHeader("oauth2-token")

    if _isEmpty(oauth2_token):
        log.error('OAUTH2 TOKEN EMPTY')
        abort(make_response(jsonify({}), 403))

    # Will get the Approov JWT token from the header, decode it and on success
    # will return it, otherwise None is returned.
    approov_token_decoded = _getApproovToken()

    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
    # when the decoded approov token is empty.
    _handleApproovProtectedRequest(approov_token_decoded)

    # check if the custom payload claim in the approov token is valid and aborts
    # the request if APPROOV_ABORT_REQUEST_ON_INVALID_CUSTOM_PAYLOAD_CLAIM is set to True.
    _handleApproovCustomPayloadClaim(approov_token_decoded, oauth2_token)

    # Now we can handle OAUTH2 as we usually would do in a Python Flask API.
    # Maybe like in https://auth0.com/docs/quickstart/webapp/python/

    form = choice([
        'Sphere',
        'Cone',
        'Cube',
        'Box',
    ])

    return jsonify(form=form)
