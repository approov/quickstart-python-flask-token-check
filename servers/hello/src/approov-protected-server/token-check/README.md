# Approov Token Integration Example

This Approov integration example is from where the code example for the [Approov token check quickstart](/docs/APPROOV_TOKEN_QUICKSTART.md) is extracted, and you can use it as a playground to better understand how simple and easy it is to implement [Approov](https://approov.io) in a Python Flask API server.

## TOC - Table of Contents

* [Why?](#why)
* [How it Works?](#how-it-works)
* [Requirements](#requirements)
* [Setup Env File](#setup-env-file)
* [Try the Approov Integration Example](#try-the-approov-integration-example)


## Why?

To lock down your API server to your mobile app. Please read the brief summary in the [Approov Overview](/OVERVIEW.md#why) at the root of this repo or visit our [website](https://approov.io/product) for more details.

[TOC](#toc---table-of-contents)


## How it works?

The Python Flask API server is very simple and is defined in the file [src/approov-protected-server/token-check/hello_server_protected.py](/servers/hello/src/approov-protected-server/token-check/hello_server_protected.py). Take a look at the `_verifyApproovToken()` function to see the simple code for the check.

For more background on Approov, see the [Approov Overview](/OVERVIEW.md#how-it-works) at the root of this repo.

[TOC](#toc---table-of-contents)


## Requirements

To run this example you will need to have installed:

* [Python 3](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Flask](https://flask.palletsprojects.com/en/2.0.x/installation/)

[TOC](#toc---table-of-contents)


## Setup Env File

From `/servers/hello/src/approov-protected-server/token-check` execute the following:

```bash
cp .env.example .env
```

Edit each file and add the [dummy secret](/TESTING.md#the-dummy-secret) to it in order to be able to test the Approov integration with the provided [Postman collection](https://github.com/approov/postman-collections/blob/master/quickstarts/hello-world/hello-world.postman_curl_requests_examples.md).

[TOC](#toc---table-of-contents)


## Try the Approov Integration Example

First, you need to install the dependencies. From the `/servers/hello/src/approov-protected-server/token-check` folder execute:

```text
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Now, you can run this example from the `/servers/hello/src/approov-protected-server/token-check` folder with:

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

Finally, you can test that the Approov integration example works as expected with this [Postman collection](/TESTING.md#testing-with-postman) or with some cURL requests [examples](/TESTING.md#testing-with-curl).

[TOC](#toc---table-of-contents)


## Issues

If you find any issue while following our instructions then just report it [here](https://github.com/approov/quickstart-python-flask-token-check/issues), with the steps to reproduce it, and we will sort it out and/or guide you to the correct path.

[TOC](#toc---table-of-contents)


## Useful Links

If you wish to explore the Approov solution in more depth, then why not try one of the following links as a jumping off point:

* [Approov Free Trial](https://approov.io/signup)(no credit card needed)
* [Approov Get Started](https://approov.io/product/demo)
* [Approov QuickStarts](https://approov.io/docs/latest/approov-integration-examples/)
* [Approov Docs](https://approov.io/docs)
* [Approov Blog](https://approov.io/blog/)
* [Approov Resources](https://approov.io/resource/)
* [Approov Customer Stories](https://approov.io/customer)
* [Approov Support](https://approov.zendesk.com/hc/en-gb/requests/new)
* [About Us](https://approov.io/company)
* [Contact Us](https://approov.io/contact)

[TOC](#toc---table-of-contents)
