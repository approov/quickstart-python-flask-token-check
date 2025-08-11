#!/usr/bin/env bash
set -euo pipefail

# Generate EC P-256 private key (PEM)
openssl ecparam -genkey -name prime256v1 -noout -out private_key.pem

# Export private key as DER (client will sign with this)
openssl ec -in private_key.pem -outform DER -out private_key.der

# Export public key as DER
openssl ec -in private_key.pem -pubout -outform DER -out public_key.der

# Base64 encode public key (ipk claim)
PUB_B64=$(base64 < public_key.der | tr -d '\n')
echo -n "$PUB_B64" > public_key.b64

echo "Keys generated."
echo "Public key (base64) saved to public_key.b64"
echo "Private key PEM: private_key.pem"
echo "Private key DER: private_key.der"
echo "Public key DER: public_key.der"
