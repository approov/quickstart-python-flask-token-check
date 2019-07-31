# System packages
import logging
from random import choice

# Third part packages
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, abort, make_response, jsonify

api = Flask(__name__)
api.config["JSON_SORT_KEYS"] = False

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

BAD_REQUEST_RESPONSE = {"status": "Bad Request"}

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
