
## 1. Install the dependencies

First, you need to install the dependencies. From the `/servers/hello/src/approov-protected-server/server-functions` folder execute:

```text
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## 2. Run Server
Now, you can run this example from the `/servers/hello/src/approov-protected-server/server-functions` folder with:

```text
FLASK_APP=hello_server_protected.py flask run --port 8002
```
> **NOTE:** If using python from inside a docker container add the option `--host 0.0.0.0`


## 3. Setup Env File

From `/servers/hello/src/approov-protected-server/server-functions` execute the following:

```bash
cp .env.example .env
```

## 4. Generete Approov secret
Now, get your Approov Secret with the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli):

```bash
approov secret -get base64
```

Next, add the [Approov secret](https://approov.io/docs/latest/approov-usage-documentation/#account-secret-key-export) to your project `.env` file:

```env
APPROOV_BASE64_SECRET=approov_base64_secret_here
```

## 5. Unprotected server 

You can test that it with:

```bash
curl -iX GET 'http://localhost:8002'
```

The response will be:

```text
HTTP/1.1 200 OK
Server: Werkzeug/3.0.3 Python/3.9.6
Date: Wed, 13 Aug 2025 13:00:51 GMT
Content-Type: application/json
Content-Length: 48
Connection: close

{"mode":"unprotected","path":"/","status":"ok"}
```

## 6. Approov protected server

### 7. Token check 
```bash
approov token --genExample approov.io > token.txt
```

```bash
curl -i http://localhost:8002/ \
  -H "Approov-Token: $(cat token.txt)"  
```

Response:
HTTP/1.1 200 OK
Server: Werkzeug/3.0.3 Python/3.9.6
Date: Wed, 13 Aug 2025 13:05:44 GMT
Content-Type: application/json
Content-Length: 52
Connection: close

{"mode":"token_only","path":"/","status":"ok"}

### 8. Token binding check 
```bash
chmod +x prep_binding.sh
./prep_binding.sh
```
```bash
curl -iX GET "http://localhost:8002/" \
  -H "Approov-Token: $(cat approov_token.txt)" \
  -H "Authorization: $(cat authorization.txt)"
```

HTTP/1.1 200 OK
Server: Werkzeug/3.0.3 Python/3.9.6
Date: Wed, 13 Aug 2025 13:23:06 GMT
Content-Type: application/json
Content-Length: 65
Connection: close

{"has_pay":true,"mode":"token_binding","path":"/","status":"ok"}


### 9. Message signature

```bash
chmod +x prep_msgsig_all.sh
./prep_msgsig_all.sh
```

```bash
curl -i http://localhost:8002/ \ 
  -H "Approov-Token: $(cat token.txt)" \
  -H 'Signature-Input: install=("@method" "@target-uri");alg="ecdsa-p256-sha256"' \
  -H "Signature: install=:$(cat signature.b64):"
```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.3 Python/3.9.6
Date: Wed, 13 Aug 2025 14:03:43 GMT
Content-Type: application/json
Content-Length: 69
Connection: close

{"has_ipk":true,"mode":"message_signature","path":"/","status":"ok"}