from flask import Flask, jsonify

api = Flask(__name__)

@api.route("/")
def hello():
    return jsonify({"message": "Hello, World!"})
