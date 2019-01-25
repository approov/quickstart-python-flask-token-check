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
#CUSTOM_PAYLOAD_CLAIM_SHA256_HASH_BASE64_ENCODED = 'invalid-oauth2-base64-encoded-hash=='
CUSTOM_PAYLOAD_CLAIM_SHA256_HASH_BASE64_ENCODED = 'f3U2fniBJVE04Tdecj0d6orV9qT9t52TjfHxdUqDBgY='

def _generateSha256HashBase64Encoded(value):
    value_hash = sha256(value.encode('utf-8')).digest()
    return b64encode(value_hash).decode('utf-8')

def generateToken(approov_base64_secret, token_expire_in_minutes, custom_payload_claim):
    """Generates a token with a 5 minutes lifetime. Optionally we can set also a custom payload claim."""

    approov_base64_secret = approov_base64_secret.strip()

    if not approov_base64_secret:
        raise ValueError('Approov base64 encoded secret is missing.')

    if token_expire_in_minutes:
        token_expire_in_minutes = 5

    payload = {
        'exp': time() + (60 * token_expire_in_minutes), # required - the timestamp for when the token expires.
        'iss': 'failover', # optional - only included in tokens from the failover; the value is always “failover”.
    }

    if custom_payload_claim:
        payload['pay'] = _generateSha256HashBase64Encoded(custom_payload_claim)

    return encode(payload, b64decode(approov_base64_secret), algorithm='HS256').decode()

def main():

    arguments = docopt(__doc__, version='GENERATE APPROOV TOKEN CLI - 1.0')

    custom_payload_claim = None
    token_expire_in_minutes = int(arguments['--expire'])
    approov_base64_secret = getenv("APPROOV_BASE64_SECRET")

    if arguments['--claim']:
        custom_payload_claim = arguments['--claim']

    if not custom_payload_claim and arguments['--claim-example'] is True:
        custom_payload_claim = CUSTOM_PAYLOAD_CLAIM_SHA256_HASH_BASE64_ENCODED

    if not arguments['--secret'] == None:
        approov_base64_secret = arguments['--secret']

    if not approov_base64_secret:
        raise ValueError('--secret was provided as an empty string in the CLI.')

    token = generateToken(approov_base64_secret, token_expire_in_minutes, custom_payload_claim)

    print('Token:\n', token)

    return token

if __name__ == '__main__':
    try:
        main()
        exit(0)
    except Exception as error:
        print(error)
        exit(1)
