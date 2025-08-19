# Approov QuickStart - Python Flask Token Check

[Approov](https://approov.io) is an API security solution used to verify that requests received by your backend services originate from trusted versions of your mobile apps.

This repo implements the Approov server-side request verification code with the Python Flask framework in a simple Hello API server, which performs the verification check before allowing valid traffic to be processed by the API endpoint.


## The Quickstarts

The quickstart code for the Approov backend server is implemented in (/docs/APPROOV_TOKEN_MESSAGE_SIGNATURE.md) That has three features availibale:
* Approov token check 
* Approov token check with token binding 
* Approov token check with message signature


## Why?

You can learn more about Approov, the motives for adopting it, and more detail on how it works by following this [link](https://approov.io/product). In brief, Approov:

* Ensures that accesses to your API come from official versions of your apps; it blocks accesses from republished, modified, or tampered versions
* Protects the sensitive data behind your API; it prevents direct API abuse from bots or scripts scraping data and other malicious activity
* Secures the communication channel between your app and your API with [Approov Dynamic Certificate Pinning](https://approov.io/docs/latest/approov-usage-documentation/#approov-dynamic-pinning). This has all the benefits of traditional pinning but without the drawbacks
* Removes the need for an API key in the mobile app
* Provides DoS protection against targeted attacks that aim to exhaust the API server resources to prevent real users from reaching the service or to at least degrade the user experience.

## Testing Approov with Curl 

[Approov](https://approov.io) is an API security solution used to verify that requests received by your backend services originate from trusted versions of your mobile apps.

Go to `docs/APPROOV_TOKEN_MESSAGE_SIGNATURE.md` for detailed steps.

## Requirements

To complete this quickstart you will need both Python, Flask, and the Approov CLI tool installed.

* [Python 3](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Flask](https://flask.palletsprojects.com/en/2.0.x/installation/)
* [Approov CLI](https://approov.io/docs/latest/approov-installation/#approov-tool) - Learn how to use it [here](https://approov.io/docs/latest/approov-cli-tool-reference/)

## Approov Integration Quickstart

The quickstart was tested with the following Operating Systems:

* Ubuntu 20.04
* MacOS Big Sur
* Windows 10 WSL2 - Ubuntu 20.04

First, setup the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli).

Now, register the API domain for which Approov will issues tokens:

```bash
approov api -add api.example.com
```

> **NOTE:** By default a symmetric key (HS256) is used to sign the Approov token on a valid attestation of the mobile app for each API domain it's added with the Approov CLI, so that all APIs will share the same secret and the backend needs to take care to keep this secret secure.
>
> A more secure alternative is to use asymmetric keys (RS256 or others) that allows for a different keyset to be used on each API domain and for the Approov token to be verified with a public key that can only verify, but not sign, Approov tokens.
>
> To implement the asymmetric key you need to change from using the symmetric HS256 algorithm to an asymmetric algorithm, for example RS256, that requires you to first [add a new key](https://approov.io/docs/latest/approov-usage-documentation/#adding-a-new-key), and then specify it when [adding each API domain](https://approov.io/docs/latest/approov-usage-documentation/#keyset-key-api-addition). Please visit [Managing Key Sets](https://approov.io/docs/latest/approov-usage-documentation/#managing-key-sets) on the Approov documentation for more details.

Next, enable your Approov `admin` role with:

```bash
eval `approov role admin`
````

For the Windows powershell:

```bash
set APPROOV_ROLE=admin:___YOUR_APPROOV_ACCOUNT_NAME_HERE___
```

Now, get your Approov Secret with the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli):

```bash
approov secret -get base64
```

Next, add the [Approov secret](https://approov.io/docs/latest/approov-usage-documentation/#account-secret-key-export) to your project `.env` file:

```env
APPROOV_BASE64_SECRET=approov_base64_secret_here
```

Now, add to your `requirements.txt` file the [JWT dependency](https://github.com/jpadilla/pyjwt/):

```bash
PyJWT==1.7.1 # update the version to the latest one
```

Next, you need to install the dependencies:

```bash
pip3 install -r requirements.txt
```

 Add code from `/server/hello_server_protected.py` to your project



> **NOTE:** When the Approov token validation fails we return a `401` with an empty body, because we don't want to give clues to an attacker about the reason the request failed, and you can go even further by returning a `400`.

Using the `before_request` decorator approach will ensure that all endpoints in your API will be protected by Approov.

Not enough details in the bare bones quickstart? No worries, check the [detailed quickstarts](QUICKSTARTS.md) that contain a more comprehensive set of instructions, including how to test the Approov integration.


## Test your Approov Integration


Generate a valid token example from the Approov Cloud service(???):

```bash
approov token -setDataHashInToken 'Bearer authorizationtoken' -genExample your.api.domain.com
```

Then make the request with the generated token:

```text
curl -i --request GET '' \
  --header 'Authorization: Bearer authorizationtoken' \
  --header 'Approov-Token: APPROOV_TOKEN_EXAMPLE_HERE'
```

The request should be accepted. For example:

```text
HTTP/1.1 200 OK

...

{"message": ""}
```


### System Clock

In order to correctly check for the expiration times of the Approov tokens is very important that the backend server is synchronizing automatically the system clock over the network with an authoritative time source. In Linux this is usually done with a NTP server.

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


## Tree 

```bash
$ tree .
.
├── server
│   │── scripts
│   │    │── prep.sh
│   │    └── tests.sh
│   │
│   ├── .env.example
│   ├── docker_run.sh
│   ├── hello_server_protected.py
│   ├── run.sh
│   ├── requirements.txt
│   └── README.md
│  
│── docs/
│   └── APPROOV_MESSAGE_SIGNATURE_QUICKSTART.md
│
├── .gitignore
├── Dockerfile  
├── docker-compose.yml   
└── OVERVIEW.md
└── README.md
```