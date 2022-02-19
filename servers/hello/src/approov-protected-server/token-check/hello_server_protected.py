from flask import Flask, jsonify, request, abort, g, make_response

# @link https://github.com/jpadilla/pyjwt/
import jwt
import base64
import hashlib

# @link https://github.com/theskumar/python-dotenv
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)
from os import getenv

import logging
log = logging.getLogger(__name__)

api = Flask(__name__)

# Token secret value obtained with the Approov CLI tool:
#  - approov secret -get
approov_base64_secret = getenv('APPROOV_BASE64_SECRET')

if approov_base64_secret == None:
    raise ValueError("Missing the value for environment variable: APPROOV_BASE64_SECRET")

APPROOV_SECRET = base64.b64decode(approov_base64_secret)

@api.before_request
def _verifyApproovToken():
    approov_token = request.headers.get("Approov-Token")

    # If we didn't find a token, then reject the request.
    if approov_token is None or approov_token == "":
        # You may want to add some logging here.
        log.error('Approov Token Check: The Approov Token is empty...')
        return abort(make_response({}, 401))

    try:
        # Decode the Approov token explicitly with the HS256 algorithm to
        # avoid the algorithm None attack.
        g.approov_token_claims = jwt.decode(approov_token, APPROOV_SECRET, algorithms=['HS256'])

        # When doesn't occur an exception we have a valid Aproov Token

    except jwt.ExpiredSignatureError as e:
        # You may want to add some logging here.
        log.error(e)
        return abort(make_response({}, 401))

    except jwt.InvalidTokenError as e:
        # You may want to add some logging here.
        log.error(e)
        return abort(make_response({}, 401))

    except:
        log.error('Approov Token check failed with unknown error...')
        return abort(make_response({}, 401))

@api.route("/")
def hello():
    return jsonify({"message": "Hello World"})
