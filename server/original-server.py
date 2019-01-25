# System packages
import logging
from random import choice

# Third part packages
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request, abort, make_response, jsonify

api = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv(find_dotenv(), override=True)

HTTP_PORT = int(getenv('HTTP_PORT', 5000))

def _getHeader(key, default_value = None):
    return request.headers.get(key, default_value)

def _isEmpty(token):
    return token is None or token == ""

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

    # Now we can handle OAUTH2 as we usually would do in a Python Flask API.
    # Maybe like in https://auth0.com/docs/quickstart/webapp/python/

    form = choice([
        'Sphere',
        'Cone',
        'Cube',
        'Box',
    ])

    return jsonify(form=form)
