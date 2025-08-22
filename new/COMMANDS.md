# Ensure we're authenticated
`approov whoami`
(assume the correct role)

# Ensure `example.com` is registered
`approov api -add example.com`

# Run the server
```
cd server/
python3 -m venv venv
source venv/bin/activate
export APPROOV_SECRET_BASE64=$(approov secret -get base64 -plain)
pip install -r requirements.txt
python approov_protected_server.py
```

## Run with Approov disabled
```
export APPROOV_ENABLED=False
python approov_protected_server.py
```

# 0 - Unprotected
`curl http://localhost:8080/unprotected`

# 1 - Protected

## 1.1 - Valid Token
```
approov token -genExample example.com > .tokens/approov_token_1_valid
curl -H "approov-token: $(cat .tokens/approov_token_1_valid)" http://localhost:8080/token-check
```

## 1.2 - Invalid Token
```
approov token -genExample example.com -type invalid > .tokens/approov_token_1_invalid
curl -H "approov-token: $(cat .tokens/approov_token_1_invalid)" http://localhost:8080/token-check
```

# 2 - Token Binding ["Authorization"]

## 2.1 - Valid Token
```
export HASH_INPUT="ExampleAuthToken=="
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > .tokens/approov_token_2_valid
curl -H "Authorization: ExampleAuthToken==" -H "approov-token: $(cat .tokens/approov_token_2_valid)" http://localhost:8080/token-binding-1
```

## 2.2 - Missing Header
`curl -H "approov-token: $(cat .tokens/approov_token_2_valid)" http://localhost:8080/token-binding-1`

## 2.3 - Incorrect Header
`curl -H "Authorization: BadAuthToken==" -H "approov-token: $(cat .tokens/approov_token_2_valid)" http://localhost:8080/token-binding-1`

## 2.4 - Invalid Token
```
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com -type invalid > .tokens/approov_token_2_invalid
curl -H "Authorization: ExampleAuthToken==" -H "approov-token: $(cat .tokens/approov_token_2_invalid)" http://localhost:8080/token-binding-1
```

# 3 - Token Binding ["Authorization", "Message-Digest"]

## 3.1 - Valid Token
```
export HASH_INPUT="ExampleAuthToken==ContentDigest=="
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > .tokens/approov_token_3_valid
curl -H "Authorization: ExampleAuthToken==" -H "Content-Digest: ContentDigest==" -H "approov-token: $(cat .tokens/approov_token_3_valid)" http://localhost:8080/token-binding-2
```

## 3.2 ...

# 4 - Message Signing
...

# 5 - Message Signing + Token Binding ["Authorization"]
...
