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

BAD_REQUEST_RESPONSE = {}

load_dotenv(find_dotenv(), override=True)

HTTP_PORT = int(getenv('HTTP_PORT', 8002))
APPROOV_BASE64_SECRET = getenv('APPROOV_BASE64_SECRET')

APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = True
_approov_enabled = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN', 'True').lower()
if _approov_enabled == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = False

APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = True
_abort_on_invalid_token_binding = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING', 'True').lower()
if _abort_on_invalid_token_binding == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = False

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
        log.error('AUTHORIZATION TOKEN EMPTY OR MISSING')
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

    return authorization_token

def _buildHelloResponse():
    return jsonify({
        "text": "Hello, World!",
    })

def _buildShapeResponse():
    shape = choice([
        "Circle",
        "Triangle",
        "Square",
        "Rectangle",
    ])

    return jsonify({
        "shape": shape,
    })

def _buildFormResponse():
    form = choice([
        'Sphere',
        'Cone',
        'Cube',
        'Box',
    ])

    return jsonify({
        "form": form,
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

    message = 'REQUEST WITH APPROOV TOKEN HEADER EMPTY OR MISSING'

    approov_token = _getHeader('approov-token')

    if _isEmpty(approov_token):

        if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True:
            _logApproov('REJECTED ' + message)
            abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

        _logApproov(message)

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
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))

    _logApproov('ACCEPTED ' + message)

def _checkApproovTokenBinding(approov_token_decoded, token_binding_header):
    if _isEmpty(approov_token_decoded):
        return False

    # checking if the approov token contains a payload and verify it.
    if 'pay' in approov_token_decoded:

        # We need to hash and base64 encode the token binding header, because that's how it was included in the Approov
        # token on the mobile app.
        token_binding_header_hash = sha256(token_binding_header.encode('utf-8')).digest()
        token_binding_header_encoded = b64encode(token_binding_header_hash).decode('utf-8')

        return approov_token_decoded['pay'] == token_binding_header_encoded

    # The Approov failover running in the Google cloud doesn't return the key
    # `pay`, thus we always need to have a pass when is not present.
    return True

def _handlesApproovTokenBindingVerification(approov_token_decoded, token_binding_header):

    message = 'REQUEST WITH VALID TOKEN BINDING IN THE APPROOV TOKEN'

    valid_token_binding = _checkApproovTokenBinding(approov_token_decoded, token_binding_header)

    if not valid_token_binding:
        message = 'REQUEST WITH INVALID TOKEN BINDING IN THE APPROOV TOKEN'

    if not valid_token_binding and APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is True:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))

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
    return _buildShapeResponse()

@api.route("/v1/forms")
def forms():
    # How to handle and validate the authorization token is out of scope for this tutorial.
    authorization_token = _getAuthorizationToken()

    return _buildFormResponse()

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

    return _buildShapeResponse()

@api.route("/v2/forms")
def formsV2():

    # Will get the Approov JWT token from the header, decode it and on success
    # will return it, otherwise None is returned.
    approov_token_decoded = _getApproovToken()

    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
    # when the decoded approov token is empty.
    _handleApproovProtectedRequest(approov_token_decoded)

    # How to handle and validate the authorization token is out of scope for this tutorial, but
    # you should only validate it after you have decoded the Approov token.
    authorization_token = _getAuthorizationToken()

    # Checks if the Approov token binding is valid and aborts the request when the environment variable
    # APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is set to True.
    _handlesApproovTokenBindingVerification(approov_token_decoded, authorization_token)

    # Now you are free to handle and validate your Authorization token as you usually do.

    return _buildFormResponse()
