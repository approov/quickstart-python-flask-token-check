import logging
from flask import Flask

api = Flask(__name__)

from flask import jsonify
from random import choice

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)

@api.route("/")
def endpoints():
    return jsonify(
        hello="http://localhost:5000/hello",
        shapes="http://localhost:5000/shapes"
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


    log.info("Shape=%s", shape)
    return jsonify(shape=shape)
