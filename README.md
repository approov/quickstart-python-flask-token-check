# Approov QuickStart - Python Flask Token Check

[Approov](https://approov.io) is an API security solution used to verify that requests received by your backend services originate from trusted versions of your mobile apps.

This repo implements the Approov server-side request verification code with the Python Flask framework in a simple Approov API server, which performs the verification check before allowing valid traffic to be processed by the API endpoint.

The Python Flask API server is very simple and is defined in the file `/server/approov_protected_server.py`.

Server example have:

* Unprotected Server
* Approov Protected Server - Token Check
* Approov Protected Server - Token Binding Check
* Approov Protected Server - Token Binding & Custom Header Check
* Approov Protected Server - Token Message Signature
* Approov Protected Server - Token Binding & Message Signature Check

## Approov Integration Quickstart

The quickstart was tested with the following Operating Systems:

* Ubuntu 20.04
* MacOS Big Sur
* Windows 10 WSL2 - Ubuntu 20.04


### 1.Setup the Approov CLI
First, setup the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli).

Next, enable your Approov `admin` role with:

```bash
approov whoami
```

For the Windows powershell:

```bash
set APPROOV_ROLE=admin:___YOUR_APPROOV_ACCOUNT_NAME_HERE___
```


### 2.Ensure `example.com` is registered

```bash
approov api -add api.example.com
```


### 3. Generate Approov secret
Now, get your Approov Secret with the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli):

```bash
approov secret -get base64
```

Next, add the [Approov secret](https://approov.io/docs/latest/approov-usage-documentation/#account-secret-key-export) to your project `server/.env` file:

```bash
cp -n .env.example .env
```


### 5.  Install the dependencies and run the server
Run the server with Approov enabled by default:

```bash
cd server/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python approov_protected_server.py
```

#### Run with Approov disabled

Disable Approov by setting the `APPROOV_ENABLED` variable to `False` inside the `server/approov_protected_server.py` file or by running the endpoint below:

```bash
curl -X POST http://localhost:8080/approov-disable
```


```text
APPROOV_ENABLED = os.getenv('APPROOV_ENABLED', 'False') == 'False'
```

To enable Approov again, just set the `APPROOV_ENABLED` variable to `True` inside the `server/approov_protected_server.py` file or by running the endpoint below:

```bash
curl -X POST http://localhost:8080/approov-enable
```

### 6. Test the server automatically

Now, you can run automated tests from the `/server` folder with:

```bash
ch.       c
./tests.sh
```

Log file with all tests results can be found in `server/.config/logs/`.


### 7. Test the server manually
You can also test the server manually with the following commands:

#### 0 - Unprotected
`curl http://localhost:8080/unprotected`

### 1 - Protected

##### 1.1 - Valid Token
```bash
approov token -genExample example.com > .config/approov_token_1_valid
curl -H "approov-token: $(cat .config/approov_token_1_valid)" http://localhost:8080/token-check
```

##### 1.2 - Invalid Token
```bash
approov token -genExample example.com -type invalid > .config/approov_token_1_invalid
curl -H "approov-token: $(cat .config/approov_token_1_invalid)" http://localhost:8080/token-check
```

#### 2 - Token Binding ["Authorization"]

##### 2.1 - Valid Token
```bash
export HASH_INPUT="ExampleAuthToken=="
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > .config/approov_token_2_valid
curl -H "Authorization: ExampleAuthToken==" -H "approov-token: $(cat .config/approov_token_2_valid)" http://localhost:8080/token-binding-1
```

##### 2.2 - Missing Header
`curl -H "approov-token: $(cat .config/approov_token_2_valid)" http://localhost:8080/token-binding-1`

##### 2.3 - Incorrect Header
`curl -H "Authorization: BadAuthToken==" -H "approov-token: $(cat .config/approov_token_2_valid)" http://localhost:8080/token-binding-1`

##### 2.4 - Invalid Token
```bash
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com -type invalid > .config/approov_token_2_invalid
curl -H "Authorization: ExampleAuthToken==" -H "approov-token: $(cat .config/approov_token_2_invalid)" http://localhost:8080/token-binding-1
```

#### 3 - Token Binding ["Authorization", "Message-Digest"]

##### 3.1 - Valid Token
```bash
export HASH_INPUT="ExampleAuthToken==ContentDigest=="
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > .config/approov_token_3_valid
curl -H "Authorization: ExampleAuthToken==" -H "Content-Digest: ContentDigest==" -H "approov-token: $(cat .config/approov_token_3_valid)" http://localhost:8080/token-binding-3
```

##### 3.2 - Missing Header
```bash
curl -H "approov-token: $(cat .config/approov_token_3_valid)" http://localhost:8080/token-binding-3
```

###### 3.3 - Incorrect Header
```bash
curl -H "Authorization: BadAuthToken==" -H "Content-Digest: BadContentDigest==" -H "approov-token: $(cat .config/approov_token_3_valid)" http://localhost:8080/token-binding-3
```

##### 3.4 - Invalid Token 
```bash
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com -type invalid > .config/approov_token_3_invalid
curl -H "Authorization: ExampleAuthToken==" -H "Content-Digest: ContentDigest==" -H "approov-token: $(cat .config/approov_token_3_invalid)" http://localhost:8080/token-binding-3
```


## More Information

* [Approov Docs Flask API](docs/APPROOV_TOKEN_CHECK_QUICKSTART.md)


## Issues

If you find any issue while following our instructions then just report it [here](https://github.com/approov/quickstart-python-flask-token-check/issues), with the steps to reproduce it, and we will sort it out and/or guide you to the correct path.


## Useful Links

If you wish to explore the Approov solution in more depth, then why not try one of the following links as a jumping off point:

* [Approov Free Trial](https://approov.io/signup)(no credit card needed)
* [Approov Get Started](https://approov.io/product/demo)
* [Approov QuickStarts](https://approov.io/docs/latest/approov-integration-examples/)
* [Approov Docs](https://approov.io/docs)
* [Approov Blog](https://approov.io/blog/)
* [Approov Resources](https://approov.io/resource/)
* [Approov Customer Stories](https://approov.io/customer)
* [Approov Support](https://approov.io/contact)
* [About Us](https://approov.io/company)
* [Contact Us](https://approov.io/contact)
