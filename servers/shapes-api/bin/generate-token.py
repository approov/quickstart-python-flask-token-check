#!/usr/bin/env python3

"""
GENERATE APPROOV TOKEN CLI

To be used only to generate Approov tokens for testing purposes during development.

Usage:
    generate-token.py
    generate-token.py [--expire EXPIRE] [--claim CLAIM] [--claim-example] [--secret SECRET]

Options:
    --expire EXPIRE  The Approov token expire time in minutes [default: 5].
    --claim CLAIM    The base64 encode sha256 hash of the custom payload claim for the Approov token.
    --claim-example  Same as --claim but using an hard-coded claim example.
    --secret SECRET  The base64 encoded secret to sign the Approov token for test purposes.
    -h --help        Show this screen.
    -v --version     Show version.

"""

# Standard Libraries
from os import getenv
from sys import exit
from time import time
from hashlib import sha256
from base64 import b64decode, b64encode

# Third-Party Libraries
from jwt import encode
from docopt import docopt

# to base64 encode the custom payload claim hash: http://tomeko.net/online_tools/hex_to_base64.php
REQUEST_CLAIM_RAW_VALUE_EXAMPLE = 'claim-value-to-be-sha256-hashed-and-base64-encoded'

def _generateSha256HashBase64Encoded(value):
    value_hash = sha256(value.encode('utf-8')).digest()
    return b64encode(value_hash).decode('utf-8')

def generateToken(approov_base64_secret, token_expire_in_minutes, request_claim_raw_value):
    """Generates a token with a 5 minutes lifetime. Optionally we can set also a custom payload claim."""

    approov_base64_secret = approov_base64_secret.strip()

    if not approov_base64_secret:
        raise ValueError('Approov base64 encoded secret is missing.')

    if not token_expire_in_minutes:
        token_expire_in_minutes = 5

    payload = {
        'exp': time() + (60 * token_expire_in_minutes), # required - the timestamp for when the token expires.
    }

    if request_claim_raw_value:
        payload['pay'] = _generateSha256HashBase64Encoded(request_claim_raw_value)

    return encode(payload, b64decode(approov_base64_secret), algorithm='HS256').decode()

def main():

    arguments = docopt(__doc__, version='GENERATE APPROOV TOKEN CLI - 1.0')

    request_claim_raw_value = None
    token_expire_in_minutes = int(arguments['--expire'])
    approov_base64_secret = getenv("APPROOV_BASE64_SECRET")

    if arguments['--claim']:
        request_claim_raw_value = arguments['--claim']

    if not request_claim_raw_value and arguments['--claim-example'] is True:
        request_claim_raw_value = REQUEST_CLAIM_RAW_VALUE_EXAMPLE

    if arguments['--secret']:
        approov_base64_secret = arguments['--secret']

    if not approov_base64_secret:
        raise ValueError('--secret was provided as an empty string in the CLI or in the .env file.')

    token = generateToken(approov_base64_secret, token_expire_in_minutes, request_claim_raw_value)

    print('Token:\n', token)

    return token

if __name__ == '__main__':
    try:
        main()
        exit(0)
    except Exception as error:
        print(error)
        exit(1)
