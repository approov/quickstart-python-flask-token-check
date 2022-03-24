# Approov Token Binding Integration Example

This Approov integration example is from where the code example for the [Approov token binding check quickstart](/docs/APPROOV_TOKEN_BINDING_QUICKSTART.md) is extracted, and you can use it as a playground to better understand how simple and easy it is to implement [Approov](https://approov.io) in a Python Flask API server.

## TOC - Table of Contents

* [Why?](#why)
* [How it Works?](#how-it-works)
* [Requirements](#requirements)
* [Setup Env File](#setup-env-file)
* [Try the Approov Integration Example](#try-the-approov-integration-example)


## Why?

To lock down your API server to your mobile app. Please read the brief summary in the [README](/README.md#why) at the root of this repo or visit our [website](https://approov.io/product.html) for more details.

[TOC](#toc---table-of-contents)


## How it works?

The Python Flask API server is very simple and is defined in the file [src/approov-protected-server/token-binding-check/hello_server_protected.py](/servers/hello/src/approov-protected-server/token-binding-check/hello_server_protected.py). Take a look at the `_verifyApproovToken()` and `_verifyApproovTokenBinding()` functions to see the simple code for the checks.

For more background on Approov, see the overview in the [README](/README.md#how-it-works) at the root of this repo.

[TOC](#toc---table-of-contents)


## Requirements

To run this example you will need to have installed:

* [Python 3](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Flask](https://flask.palletsprojects.com/en/2.0.x/installation/)

[TOC](#toc---table-of-contents)


## Setup Env File

From `/servers/hello/src/approov-protected-server/token-binding-check` execute the following:

```bash
cp .env.example .env
```

Edit each file and add the [dummy secret](/README.md#the-dummy-secret) to it in order to be able to test the Approov integration with the provided [Postman collection](https://github.com/approov/postman-collections/blob/master/quickstarts/hello-world/hello-world.postman_curl_requests_examples.md).

[TOC](#toc---table-of-contents)


## Try the Approov Integration Example

First, you need to install the dependencies. From the `/servers/hello/src/approov-protected-server/token-binding-check` folder execute:

```text
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Now, you can run this example from the `/servers/hello/src/approov-protected-server/token-binding-check` folder with:

```text
FLASK_APP=hello_server_protected.py flask run --port 8002
```
> **NOTE:** If using python from inside a docker container add the option `--host 0.0.0.0`

Next, you can test that it works with:

```bash
curl -iX GET 'http://localhost:8002'
```

The response will be a `401` unauthorized request:

```text
HTTP/1.0 401 UNAUTHORIZED
Content-Type: application/json
Content-Length: 3
Server: Werkzeug/2.0.3 Python/3.10.3
Date: Thu, 24 Mar 2022 12:34:04 GMT

{}
```

The reason you got a `401` is because no Approoov token isn't provided in the headers of the request.

Finally, you can test that the Approov integration example works as expected with this [Postman collection](/README.md#testing-with-postman) or with some cURL requests [examples](/README.md#testing-with-curl).

[TOC](#toc---table-of-contents)
