#!/usr/bin/env python3

# Standard Library
import base64
import time
import os

# Third-Party
import jwt

# Constants
TOKEN_LIFETIME_IN_SECONDS = 2 * 60 # 2 minutes

def generate_token(payload, b64_token_secret):
    payload["exp"] = int(time.time()) + TOKEN_LIFETIME_IN_SECONDS

    token = jwt.encode(payload, base64.b64decode(b64_token_secret), algorithm='HS256')

    return token

def main():
  """Generates a token with a custom issuer claim and a 5 minute
  lifetime"""

  # to base64 encode the custom payload claim hash: http://tomeko.net/online_tools/hex_to_base64.php
  #'pay':'invalid-oauth2-base64-encoded-hash=='
  my_token = {
    'iss':'custom',
    'pay':'f3U2fniBJVE04Tdecj0d6orV9qT9t52TjfHxdUqDBgY='
  }

  # base64 encoded string for this secret: approov-base64-encoded-secret
  default_base64_secret = "YXBwcm9vdi1iYXNlNjQtZW5jb2RlZC1zZWNyZXQ="
  b64_token_secret = os.environ.get("APPROOV_BASE64_SECRET", default_base64_secret)

  token = generate_token(my_token, b64_token_secret)
  print("Token:", token)

  return

if __name__ == "__main__":
  main()


