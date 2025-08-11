# Postman Curl Requests Examples

The cURL requests examples are extracted from the Postman collection, and they will test the Approov integration in the API server for requests with valid and invalid Approov tokens.

## Approov Token Protected

### Valid Requests

#### Approov Token with Valid Signature and Expire Time

The Approov token was signed with a secret only known by the Approov Cloud service and the GoLang server.

Request:

```txt
curl -iX GET http://localhost:8002/ \
  --header 'Approov-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjQ3MDg2ODMyMDUuODkxOTEyfQ.c8I4KNndbThAQ7zlgX4_QDtcxCrD9cff1elaCJe9p9U'
```

Response:

```txt
HTTP/1.1 200 OK
Content-Type: application/json
Date: Mon, 07 Sep 2020 11:47:29 GMT
Content-Length: 28

{"message": "Hello, World!"}
```

### Invalid Requests

#### Approov Token with an Invalid Signature

The Approov token was signed with a secret not known by the GoLang server, therefore the request must be rejected. This means that the mobile app failed the integrity check with the Approov cloud service or that an attacker is trying to spoof the Approov token.

Request:

```txt
curl -iX GET http://localhost:8002/ \
  --header 'Approov-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjQ3MDg2ODMyMDUuODkxOTEyfQ._ZdLOZmK4KXSIpVlhOpHBgboSHHTWer-X6oLqFIDQWI'
```

Response:

```txt
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Date: Mon, 07 Sep 2020 11:54:34 GMT
Content-Length: 3

{}
```


## Approov Token Binding Protected

### Valid Requests

#### Approov Token with Valid Signature, Expire Time, and Token Binding

The Approov token was signed with a secret only known by the Approov Cloud service and the GoLang server. The value in the key `pay` of the token claims matches the Base64 encoded hash of the `Authorization` header, therefore the token binding is valid.

Request:

```text
curl -iX GET 'http://localhost:8002/' \
  --header 'Approov-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjQ3MTgwMTgyMjQuNzgwMzY4LCJwYXkiOiJWUUZGUEpaNjgyYU90eFJNanowa3RDSG15V2VFRWVTTXZYaDF1RDhKM3ZrPSJ9.N-KwuLeUt9s6TDibhX32AIkhobCYVh5-brVESqUxdBk' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
```

Response:

```text
HTTP/1.1 200 OK
Content-Type: application/json
Date: Tue, 08 Sep 2020 10:28:36 GMT
Content-Length: 28

{"message": "Hello, World!"}
```

### Invalid Requests

#### Approov Token with an Invalid Token Binding

The Approov token was signed with a secret only known by the Approov Cloud service and the GoLang server, but the token binding in the key `pay` of the token claims doesn't match the Base64 encoded hash of the `Authorization` header, therefore the request must be rejected.

Request:

```text
curl -iX GET 'http://localhost:8002/' \
  --header 'Approov-Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjQ3MDg2ODM0NTcuNDg1Mzk1LCJwYXkiOiI1NjZ2UVdhV0dCZ3MrS0U4eXNqVFRQUXRncHVlK1hMTXF4OGVZb2JDckkwPSJ9.v9CxDagzviU6VcilyT7pC793FDzm_bjqG2sQqmmU5GE' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
```

Response:

```text
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Date: Tue, 08 Sep 2020 10:46:26 GMT
Content-Length: 3

{}
```


## Approov Message Signature Protected

### Valid Requests

#### Approov Token (with ipk) and Valid HTTP Message Signature


Request:

```bash
curl -i http://localhost:8002/token \
  -H "Approov-Token: $(cat token.txt)" \
  -H 'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
  -H "Signature: install=:$(cat signature.b64):"
```

Response:

```text
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.2
Date: Fri, 08 Aug 2025 12:51:38 GMT
Content-Type: application/json
Content-Length: 309
Connection: close

{
  "message": "\u2705 Token + Signature Verified",
  "payload": {
    "aud": "",
    "did": "ExampleApproovTokenDID==",
    "exp": 1754660970,
    "ip": "1.2.3.4",
    "ipk": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEoDm125ZgzYIybpkhSnNuDfAMwB6FSTMCzefElwfBlLo7A51uIDxoUFkKTYS3ZN8FgyKieOyuGSdReg0ZN4Wy6A=="
  }
}
```

#### Approov Token with Valid Signature and Expire Time

Request:

```bash
curl -i http://localhost:8002/token \
  -H "Approov-Token: $(cat token.txt)"
```

Response:

```text
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.2
Date: Fri, 08 Aug 2025 13:04:17 GMT
Content-Type: application/json
Content-Length: 112
Connection: close

{
  "has_ipk": false,
  "message": "\u2705 Token Verified (and signature if ipk present)",
  "path": "/token"
}
```


### Invalid Requests



Request:

```bash
curl -i http://localhost:8002/token \
  -H "Approov-Token: $(cat token.txt)" \
  -H 'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
  -H "Signature: install=:$(cat signature.b64):"
```

Response:




Request:

```bash
curl -i http://localhost:8002/token \
  -H "Approov-Token: $(cat token.txt)"
```

Response: