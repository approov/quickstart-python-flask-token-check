# Approov Quicksart - Python Flask Token Check

Example code to perform an Approov token check using Python Flask.

The Python Flask API server is very simple and is defined in the file `/server/hello_server_protected.py`.

Hello server example have:

* Unprotected Server
* Approov Protected Server - Token Check
* Approov Protected Server - Token Binding Check
* Approov Protected Server - Token Message Signature
* Approov Protected Server - Token Binding & Message Signature Check
* Approov Protected Server - Token Binding & Custom Header Check

## Testing Approov with Curl 

To use Approov with the Python Flask API server we need a small amount of configuration.

### 1.Setup the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli).

Next, enable your Approov `admin` role with:

```bash
eval `approov role admin`
```

For the Windows powershell:

```bash
set APPROOV_ROLE=admin:___YOUR_APPROOV_ACCOUNT_NAME_HERE___
```

### 2. Setup Env File

From `/server` execute the following:
It will create .env file inside /donfig folder


```bash
mkdir -p config && cp -n .env.example config/.env
```

```bash
mkdir .dev -Force | Out-Null; if ((Test-Path .env.example) -and -not (Test-Path .dev/.env)) { Copy-Item .env.example .dev/.env }
```

### 3. Generete Approov secret
Now, get your Approov Secret with the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli):

```bash
approov secret -get base64
```

Next, add the [Approov secret](https://approov.io/docs/latest/approov-usage-documentation/#account-secret-key-export) to your project `.dev/.env` file:

```env
APPROOV_BASE64_SECRET=approov_base64_secret_here
```

### 4.  Install the dependencies and run test

 To run tests you have two options availibale. To run it locally (venv) or by using Docker.

### Docker Stack

The docker stack provided via the `docker-compose.yml` file in this folder is used for development proposes of server.

If you decide to use the docker stack then you need to bear in mind that the , used to test the servers examples, will connect to port `8002`  with `docker-compose up` by default.

To be able run tests by using Docker should be installed.

####  Install Dependencies, Run Server, Run tests

First, you need to install the dependencies and start Docker container.

Now, you can run this example from the `/server` folder with:

```bash
chmod +x docker_run.sh
./docker_run.sh
```
This will start Docker container, approov-server and run prep.sh, tests.sh from `/scripts` folder. It prepare and craete all nedeed files and run tests. Log file with all results can be found in `server/config/log/`.

Expected response: 

```text
==> Starting approov-server on port 8002…
[+] Building 1.0s (13/13) FINISHED                                                                                                                                       0.0s
[+] Running 2/2
 ✔ approov-server            Built                                                                                                                                       0.0s 
 ✔ Container approov-server  Started                                                                                                                                    10.5s 
==> Ensuring server is running, waiting until ready, then prepping & testing…
→ starting hello_server_protected.py on 8002
==> Waiting for server to be ready…
✓ Server is up
==> Running prep…
Done.
Artifacts written to /home/python/workspace/server/config:
-rw-r--r-- 1 python python 176 Aug 18 14:02 /home/python/workspace/server/config/approov_token.txt
-rw-r--r-- 1 python python  39 Aug 18 13:50 /home/python/workspace/server/config/authorization.txt
-rw-r--r-- 1 python python   8 Aug 18 13:50 /home/python/workspace/server/config/header.txt
-rw-r--r-- 1 python python  91 Aug 18 14:02 /home/python/workspace/server/config/public_key.der
-rw-r--r-- 1 python python  96 Aug 18 14:02 /home/python/workspace/server/config/signature.b64
-rw-r--r-- 1 python python  96 Aug 18 14:02 /home/python/workspace/server/config/signature_bm.b64
-rw-r--r-- 1 python python 351 Aug 18 14:02 /home/python/workspace/server/config/token_bm.txt
-rw-r--r-- 1 python python 105 Aug 18 14:02 /home/python/workspace/server/config/token_check.txt
-rw-r--r-- 1 python python 176 Aug 18 14:02 /home/python/workspace/server/config/token_custom.txt
-rw-r--r-- 1 python python 280 Aug 18 14:02 /home/python/workspace/server/config/token.txt
==> Running tests…
Running tests against http://127.0.0.1:8002
(full log: /server/config/logs/test-********-******.log)

✔ Unprotected (/) — PASSED (HTTP 200)
✔ Token check (/token_check) — PASSED (HTTP 200)
✔ Token binding (/token_binding) — PASSED (HTTP 200)
✔ Message signature (/message_signature) — PASSED (HTTP 200)
✔ Token Binding + Message Signature (/token_binding_message_signature) — PASSED (HTTP 200)
✔ Token binding custom (/token_binding_custom) — PASSED (HTTP 200)

6 passed, 0 failed, 0 skipped  |  log: /config/logs/test-********-******.log
==> Done.
```


### Venv 

#### Install Dependencies 

First, you need to install the dependencies and start venv. From the `/server` folder execute:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

#### Run Server

Now, you can run this example from the `/server` folder with:

```bash
FLASK_APP=hello_server_protected.py flask run --port 8002
```

> **NOTE:** If using python from inside a docker container add the option `--host 0.0.0.0`

#### Run tests

Now, you can run this example from the `/server` folder with:


```bash
chmod +x run.sh
./run.sh
```
This will run prep.sh and tests.sh from /scripts folder. It prepare and craete all nedeed files and run tests. Log file with all results can be found in `server/config/log/`.

Expected response: 

```text
==> Running prep…
Done.
Artifacts written to ../server/config:
-rw-r--r--@ 1 user  staff  176 Aug 19 11:47 /server/config/approov_token.txt
-rw-r--r--@ 1 user  staff   39 Aug 18 14:50 /server/config/authorization.txt
-rw-r--r--@ 1 user  staff    8 Aug 18 14:50 /server/config/header.txt
-rw-r--r--@ 1 user  staff   91 Aug 19 11:47 /server/config/public_key.der
-rw-r--r--@ 1 user  staff   96 Aug 19 11:47 /server/config/signature.b64
-rw-r--r--@ 1 user  staff   96 Aug 19 11:47 /server/config/signature_bm.b64
-rw-r--r--@ 1 user  staff  280 Aug 19 11:47 /server/config/token.txt
-rw-r--r--@ 1 user  staff  351 Aug 19 11:47 /server/config/token_bm.txt
-rw-r--r--@ 1 user  staff  105 Aug 19 11:47 /server/config/token_check.txt
-rw-r--r--@ 1 user  staff  176 Aug 19 11:47 /server/config/token_custom.txt

==> Running tests against http://localhost:8002 ...
Running tests against http://localhost:8002
(full log: ../config/logs/test-********-******.log)

✔ Unprotected (/) — PASSED (HTTP 200)
✔ Token check (/token_check) — PASSED (HTTP 200)
✔ Token binding (/token_binding) — PASSED (HTTP 200)
✔ Message signature (/message_signature) — PASSED (HTTP 200)
✔ Token Binding + Message Signature (/token_binding_message_signature) — PASSED (HTTP 200)
✔ Token binding custom (/token_binding_custom) — PASSED (HTTP 200)

6 passed, 0 failed, 0 skipped  |  log: ../config/logs/test-********-******.log
```

## Enable Approov

Approov function features are enabled by defualt. To disable it in `/server/hello_server_protected.py` change CHECKS_ENABLED = False 

 ```python
# ----------------- ON/OFF switch (code-only) -----------------
# Set this to True to enforce all checks, False to bypass them.
CHECKS_ENABLED = True
```
To check if approov token check is enable run: 

```bash
curl -s http://localhost:8002/token_state
```

Response: 

```text
Token check is enabled
```

## Unprotected Server

The server only replies to the endpoint / 

## Approov Protected Server - Token Check

Take a look at the _verifyApproovToken() function to see the simple code for the checks.

## Approov Protected Server - Token Binding Check

Take a look at the _verifyApproovToken() and _verifyApproovTokenBinding() functions to see the simple code for the checks.

## Approov Protected Server - Token Message Signature

Take a look at the _verifyApproovToken() and _verifyMessageSignature functions to see the simple code for the checks.

## Approov Protected Server - Token Binding & Message Signature Check

Take a look at the _verifyApproovToken(),  _verifyApproovTokenBinding() and _verifyMessageSignature functions to see the simple code for the checks.

## Approov Protected Server - Token Binding & Custom Header Check

Take a look at the _verifyApproovToken(),  _verifyApproovTokenBinding(), verifyApproovTokenBindingCustom  _verifyMessageSignature functions to see the simple code for the checks.

Set CUSTOM_BINDING_HEADER in `/server/hello_server_protected.py` (defaults to X-Header-Id). The value sent in tests comes from server/config/header.txt.