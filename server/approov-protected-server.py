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

APPROOV_ENABLED = True
_approov_enabled = getenv('APPROOV_ENABLED', 'True').lower()

if _approov_enabled == 'false':
    APPROOV_ENABLED = False

APPROOV_BASE64_SECRET = getenv('APPROOV_BASE64_SECRET')

def _getHeader(key, default_value = None):
    return request.headers.get(key, default_value)

def _isEmpty(token):
    return token is None or token == ""

def _logApproov(message):
    if APPROOV_ENABLED:
        log.error('APPROOV ENABLED | %s', message)
    else:
        log.info('APPROOV DISABLED | %s', message)

def _decodeApproovToken(approov_token, approov_base64_secret):
    try:
        # Decode the approov token, allowing only the HS256 algorithm and using
        # the approov base64 encoded SECRET
        approov_token_decoded = jwt.decode(approov_token, b64decode(approov_base64_secret), algorithms=['HS256'])

        return approov_token_decoded

    except jwt.InvalidSignatureError as e:
        _logApproov('JWT TOKEN INVALID SIGNATURE: %s' % e)
        return None
    except jwt.ExpiredSignatureError as e:
        _logApproov('JWT TOKEN EXPIRED: %s' % e)
        return None
    except jwt.InvalidTokenError as e:
        _logApproov('JWT TOKEN INVALID: %s' % e)
        return None

def _isValidPayloadInApproovToken(approov_token_decoded, custom_payload_claim):
    if _isEmpty(approov_token_decoded):
        return False

    # checking if the approov token contains a payload and verify it.
    if 'pay' in approov_token_decoded:

        # we need to hash and base64 encode the oauth2 token in order to verify
        # it matches the same one contained in the approov token payload.
        payload_claim_hash = sha256(custom_payload_claim.encode('utf-8')).digest()
        payload_claim_base64_hash = b64encode(payload_claim_hash).decode('utf-8')

        return approov_token_decoded['pay'] == payload_claim_base64_hash

    # The Approov failover running in the Google cloud doesn't return the custom
    # payload claim, thus we always need to have a pass when is not present.
    return True

def _abortApproovProtectedRequest(message):
    _logApproov(message)

    if APPROOV_ENABLED:
        abort(make_response(jsonify({}), 400))

def _checkApproovToken():
    approov_token = _getHeader('approov-token')

    if _isEmpty(approov_token):
        _abortApproovProtectedRequest('APPROOV TOKEN EMPTY')
        return ''

    approov_token_decoded = _decodeApproovToken(approov_token, APPROOV_BASE64_SECRET)

    if _isEmpty(approov_token_decoded):
        _abortApproovProtectedRequest('FAILED TO DECODE APPROOV TOKEN')

    return approov_token_decoded

def _checkApproovTokenWithCustomPayloadClaim(custom_payload_claim):

    approov_token_decoded = _checkApproovToken()

    # We will check that the OAUTH2 Token included by the mobile app in the
    # Approov Token payload is the same that was sent in the header of the request.
    #
    # On failure it means the request was tampered with, therefore is rejected.
    if not _isValidPayloadInApproovToken(approov_token_decoded, custom_payload_claim):
        _abortApproovProtectedRequest('APPROOV TOKEN WITH INVALID PAYLOAD')

    return approov_token_decoded

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

    # checkd if the Approov token is valid and aborts the request if not.
    _checkApproovToken()

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

    # check if the Approov token and the custom payload claim(the ouath2 token)
    # are valid and aborts the request if not.
    _checkApproovTokenWithCustomPayloadClaim(oauth2_token)

    # Now we can handle OAUTH2 as we usually would do in a Python Flask API.
    # Maybe like in https://auth0.com/docs/quickstart/webapp/python/

    form = choice([
        'Sphere',
        'Cone',
        'Cube',
        'Box',
    ])

    return jsonify(form=form)
