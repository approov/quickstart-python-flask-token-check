# APPROOV INTEGRATION EXAMPLE

An Approov token integration example for a Python 3 Flask API as described in the article: [Approov Integration in a Python Flask API](https://approov.io/blog//approov-integration-in-a-python-flask-api).

## HOW TO USE

For your convenience we host ourselves the backend for this Approov integration walk-through, and the specific url for it can be found on the article, that we invite you to read in order to better understand the purpose and scope for this walk-through.

If you prefer to have control of the backend please follow the [deployment](./docs/DEPLOYMENT.md) guide to deploy the backend to your own online server or just run it in localhost by following the [Approov Shapes API Server](./docs/approov-shapes-api-server.md) walk-through.

The concrete implementation of the Approov Shapes API Server is in the [approov-protected-server.py](./approov-protected-server.py) file, that is a simple Python Flask server with some endpoints protected by Approov and other endpoints without any Approov protection.

Now let's continue reading this README for a **quick start** introduction in how to integrate Approov on a current project by using as an example the code for the Approov Shapes API Server.


## APPROOV VALIDATION PROCESS

Before we dive into the code we need to understand the Approov validation
process on the back-end side.

### The Approov Token

API calls protected by Approov will typically include a header holding an Approov
JWT token. This token must be checked to ensure it has not expired and that it is
properly signed with the secret shared between the back-end and the Approov cloud
service.

We will use a Python package to help us in the validation of the Approov JWT
token.

> **NOTE**
>
> Just to be sure that we are on the same page, a JWT token have 3 parts, that
> are separated by dots and represented as a string in the format of
> `header.payload.signature`. Read more about JWT tokens [here](https://jwt.io/introduction/).

### The Approov Token Binding

When an Approov token contains the key `pay`, its value is a base64 encoded sha256 hash of
some unique identifier in the request, that we may want to bind with the Approov token, in order
to enhance the security on that request, like an Authorization token.

Dummy example for the JWT token middle part, the payload:

```
{
    "exp": 123456789, # required - the timestamp for when the token expires.
    "pay":"f3U2fniBJVE04Tdecj0d6orV9qT9t52TjfHxdUqDBgY=" # optional - a sha256 hash of the token binding value, encoded with base64.
}
```

The token binding in an Approov token is the one in the `pay` key:

```
"pay":"f3U2fniBJVE04Tdecj0d6orV9qT9t52TjfHxdUqDBgY="
```

**ALERT**:

Please bear in mind that the token binding is not meant to pass application data
to the API server.


## SYSTEM CLOCK

In order to correctly check for the expiration times of the Approov tokens is
very important that the Python Flask server is synchronizing automatically the
system clock over the network with an authoritative time source. In Linux this
is usual done with a NTP server.


## REQUIREMENTS

We will use Python 3 with a Flask API server to run our code.

Docker is required for the ones wanting to use the docker environment provided
by the [stack](./stack) bash script, that is a wrapper around docker commands.

Postman is the tool we recommend to be used when simulating the queries against
the API, but feel free to use any other tool of your preference.


## THE DOCKER STACK

We recommend the use of the included Docker stack to play with this Approov
integration.

For details in how to use it you need to follow the setup instructions in the
[Approov Shapes API Server](./docs/approov-shapes-api-server.md#development-environment)
walk-through, but feel free to use your local environment to play with this
Approov integration.


## THE POSTMAN COLLECTION

As you go through your Approov Integration you may want to test it and if you are using Postman then you can import this [Postman collection](https://raw.githubusercontent.com/approov/postman-collections/master/quickstarts/shapes-api/shapes-api.postman_collection.json) to see how it's done for the Approov Shapes API Server [example](./docs/approov-shapes-api-server.md), and use it as an inspiration or starting point for your own collection.

The Approov tokens used in the headers of this Postman collection where generated with this [Python script](./bin/generate-token.py), that used the dummy secret set on the `.env.example` file to sign all the Approov tokens.

If you are using the Aproov secret retrieved with the [Approov CLI]((https://approov.io/docs/latest/approov-cli-tool-reference/)) tool then you need to use it to generate some valid and invalid tokens. Some examples of using it can be found in the Approov [docs](https://approov.io/docs/latest/approov-usage-documentation/#generating-example-tokens).


## INSTALL DEPENDENCIES

If not already using the packages `pyjwt` and `python-dotenv` in your Python
Flask API project, please add them:

```bash
pip3 install pyjwt python-dotenv
```

## ORIGINAL SERVER

Let's use the [original-server.py](./original-server.py) as an example
for a current server where we want to add Approov to protect some or all the
endpoints and after we add only the necessary code to integrate Approov,
the end result can be seen in the [approov-protected-server.py](./approov-protected-server.py).


## HOW TO INTEGRATE

We will learn how to go from the [original-server.py](./original-server.py)
to the [approov-protected-server.py](./approov-protected-server.py) and
how to configure the server.

In order to be able to check the Approov token the `PyJWT` library needs
to know the secret used by the Approov cloud service to sign it. A secure way to
do this is by passing it as an environment variable, as it can be seen
[here](./approov-protected-server.py#L24).

Next we need to define two core methods to be used during the Approov token check
process. We also define some other methods to help with the Approov integration
and this are probably the ones you may want to customize for your use case.

The token binding is optional in the Aproov Token, but when present needs to be a
base64 encoded string from a hash of some value you want to bind with the
Approov token. A good example is to bind the user authentication token with
the Approov token, but your needs and requirements may be different.

Let's breakdown the implementation of the [approov-protected-server.py](./approov-protected-server.py) to make it easier to adapt to your current project.


### Import Dependencies

We need to [require the dependencies](./approov-protected-server.py#L4-L9)
we installed before, plus some more system dependencies:

```python
# file: server/approov-protected-server.py

# System packages
from base64 import b64decode, b64encode
from os import getenv
from hashlib import sha256

# Third part packages
import jwt
```

### Setup Environment

If you don't have already an `.env` file, then you need to create one in the
root of your project by using this [.env.example](./.env.example) as your
starting point.

The `.env` file must contain this four variables:

```env
# Feel free to play with different secrets. For development only you can create them with:
# openssl rand -base64 64 | tr -d '\n'; echo
APPROOV_BASE64_SECRET=h+CX0tOzdAAR9l15bWAqvq7w9olk66daIH+Xk+IAHhVVHszjDzeGobzNnqyRze3lw/WVyWrc2gZfh3XXfBOmww==
APPROOV_LOGGING_ENABLED=true
APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN=true
APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING=true
```

Now we can read them from our code, like is done [here](./approov-protected-server.py#L24-L39):

```python
# file: server/approov-protected-server.py

APPROOV_BASE64_SECRET = getenv('APPROOV_BASE64_SECRET')

APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = True
_approov_enabled = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN', 'True').lower()
if _approov_enabled == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = False

APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = True
_abort_on_invalid_token_binding = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING', 'True').lower()
if _abort_on_invalid_token_binding == 'false':
    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = False

APPROOV_LOGGING_ENABLED = True
_approov_logging_enabled = getenv('APPROOV_LOGGING_ENABLED', 'True').lower()
if _approov_logging_enabled == 'false':
    APPROOV_LOGGING_ENABLED = False
```


### Methods

Let's start by adding [this method](./approov-protected-server.py#L85-L87)
to enable logging for Approov specific occurrences:

```python
# file: approov-protected-server.py

def _logApproov(message):
    if APPROOV_LOGGING_ENABLED is True:
        log.info(message)
```

Now we need to add [this method](./approov-protected-server.py#L89-L105) to
decode the Approv token:

```python
# file: approov-protected-server.py

def _decodeApproovToken(approov_token):
    try:
        # Decode the approov token, allowing only the HS256 algorithm and using
        # the approov base64 encoded SECRET
        approov_token_decoded = decode(approov_token, b64decode(APPROOV_BASE64_SECRET), algorithms=['HS256'])

        return approov_token_decoded

    except jwt.InvalidSignatureError as e:
        _logApproov('APPROOV JWT TOKEN INVALID SIGNATURE: %s' % e)
        return None
    except jwt.ExpiredSignatureError as e:
        _logApproov('APPROOV JWT TOKEN EXPIRED: %s' % e)
        return None
    except jwt.InvalidTokenError as e:
        _logApproov('APPROOV JWT TOKEN INVALID: %s' % e)
        return None
```

Now we need to add [this method](./approov-protected-server.py#L107-L128)
to get the Approov token and validate it in each endpoint we want to protect:

```python
# file: approov-protected-server.py

def _getApproovToken():

    message = 'REQUEST WITH APPROOV TOKEN HEADER EMPTY OR MISSING'

    approov_token = _getHeader('approov-token')

    if _isEmpty(approov_token):

        if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True:
            _logApproov('REJECTED ' + message)
            abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

        _logApproov(message)

        return None

    approov_token_decoded = _decodeApproovToken(approov_token)

    if _isEmpty(approov_token_decoded):
        return None

    return approov_token_decoded
```

We also need to add [this method](./approov-protected-server.py#L130-L141)
to handle requests with an invalid Approov token:

```python
# file: approov-protected-server.py

def _handleApproovProtectedRequest(approov_token_decoded):

    message = 'REQUEST WITH VALID APPROOV TOKEN'

    if not approov_token_decoded:
        message = 'REQUEST WITH INVALID APPROOV TOKEN'

    if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True and not approov_token_decoded:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))

    _logApproov('ACCEPTED ' + message)
```

Then we need [this method](./approov-protected-server.py#L143-L159) to check
the token binding in the Approov token:

```python
# file: approov-protected-server.py

def _checkApproovTokenBinding(approov_token_decoded, token_binding_header):
    if _isEmpty(approov_token_decoded):
        return False

    # checking if the approov token contains a payload and verify it.
    if 'pay' in approov_token_decoded:

        # We need to hash and base64 encode the token binding header, because that's how it was included in the Approov
        # token on the mobile app.
        token_binding_header_hash = sha256(token_binding_header.encode('utf-8')).digest()
        token_binding_header_encoded = b64encode(token_binding_header_hash).decode('utf-8')

        return approov_token_decoded['pay'] == token_binding_header_encoded

    return False
```

Finally we need [this method](./approov-protected-server.py#L161-L174) to
handle the validation of the token binding in the Approov token:

```python
# file: approov-protected-server.py

def _handlesApproovTokenBindingVerification(approov_token_decoded, token_binding_header):

    if not 'pay' in approov_token_decoded:
        message = 'REQUEST WITH APPROOV TOKEN MISSING THE CLAIM TO VERIFY THE TOKEN BINDING'

        if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is True:
            _logApproov('REJECTED ' + message)
            abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))
        else:
            _logApproov('ACCEPTED ' + message)
            return

    message = 'REQUEST WITH VALID TOKEN BINDING IN THE APPROOV TOKEN'

    valid_token_binding = _checkApproovTokenBinding(approov_token_decoded, token_binding_header)

    if not valid_token_binding:
        message = 'REQUEST WITH INVALID TOKEN BINDING IN THE APPROOV TOKEN'

    if not valid_token_binding and APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is True:
        _logApproov('REJECTED ' + message)
        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))

    _logApproov('ACCEPTED ' + message)
```

#### Endpoints

To protect specific endpoints in a current server we only need to add the Approov
token check for each endpoint we want to protect, as we have done in the
[shapes](./approov-protected-server.py#L209-L215) endpoint:

```python
# file: approov-protected-server.py

# Will get the Approov JWT token from the header, decode it and on success
# will return it, otherwise None is returned.
approov_token_decoded = _getApproovToken()

# If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
# when the decoded approov token is empty.
_handleApproovProtectedRequest(approov_token_decoded)
```

or if using the token binding in the Approov token, as we have done in
the [forms](./approov-protected-server.py#L222-L236) endpoint:

```python
# file: approov-protected-server.py

# Will get the Approov JWT token from the header, decode it and on success
# will return it, otherwise None is returned.
approov_token_decoded = _getApproovToken()

# If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
# when the decoded approov token is empty.
_handleApproovProtectedRequest(approov_token_decoded)

# How to handle and validate the authorization token is out of scope for this tutorial, but
# you should only validate it after you have decoded the Approov token.
authorization_token = _getAuthorizationToken()

# Checks if the Approov token binding is valid and aborts the request when the environment variable
# APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is set to True.
_handlesApproovTokenBindingVerification(approov_token_decoded, authorization_token)
```

Did you notice that we only retrieve the `Authorization` token after we have successful decoded the `Approov-Token`? This is because if the Approov token is not a valid one, we don't want to waste time in other tasks.

#### The Code Difference

If we compare the [original-server.py](./original-server.py) with the
[approov-protected-server.py](./approov-protected-server.py) we will see
this file difference:

```python
--- /home/sublime/workspace/quickstart-python-flask_shapes-api/servers/shapes-api/original-server.py
+++ /home/sublime/workspace/quickstart-python-flask_shapes-api/servers/shapes-api/approov-protected-server.py
@@ -1,8 +1,12 @@
 # System packages
 import logging
 from random import choice
+from base64 import b64decode, b64encode
+from os import getenv
+from hashlib import sha256

 # Third part packages
+import jwt
 from dotenv import load_dotenv, find_dotenv
 from flask import Flask, request, abort, make_response, jsonify

@@ -12,6 +16,28 @@
 logging.basicConfig(level=logging.DEBUG)
 log = logging.getLogger(__name__)

+BAD_REQUEST_RESPONSE = {}
+
+load_dotenv(find_dotenv(), override=True)
+
+HTTP_PORT = int(getenv('HTTP_PORT', 8002))
+APPROOV_BASE64_SECRET = getenv('APPROOV_BASE64_SECRET')
+
+APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = True
+_approov_enabled = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN', 'True').lower()
+if _approov_enabled == 'false':
+    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN = False
+
+APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = True
+_abort_on_invalid_token_binding = getenv('APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING', 'True').lower()
+if _abort_on_invalid_token_binding == 'false':
+    APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING = False
+
+APPROOV_LOGGING_ENABLED = True
+_approov_logging_enabled = getenv('APPROOV_LOGGING_ENABLED', 'True').lower()
+if _approov_logging_enabled == 'false':
+    APPROOV_LOGGING_ENABLED = False
+
 def _getHeader(key, default_value = None):
     return request.headers.get(key, default_value)

@@ -23,7 +49,7 @@

     if _isEmpty(authorization_token):
         log.error('AUTHORIZATION TOKEN EMPTY OR MISSING')
-        abort(make_response(jsonify(BAD_REQUEST_REPONSE), 400))
+        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))

     return authorization_token

@@ -56,6 +82,104 @@
         "form": form,
     })

+def _logApproov(message):
+    if APPROOV_LOGGING_ENABLED is True:
+        log.info(message)
+
+def _decodeApproovToken(approov_token):
+    try:
+        # Decode the approov token, allowing only the HS256 algorithm and using
+        # the approov base64 encoded SECRET
+        approov_token_decoded = jwt.decode(approov_token, b64decode(APPROOV_BASE64_SECRET), algorithms=['HS256'])
+
+        return approov_token_decoded
+
+    except jwt.InvalidSignatureError as e:
+        _logApproov('APPROOV JWT TOKEN INVALID SIGNATURE: %s' % e)
+        return None
+    except jwt.ExpiredSignatureError as e:
+        _logApproov('APPROOV JWT TOKEN EXPIRED: %s' % e)
+        return None
+    except jwt.InvalidTokenError as e:
+        _logApproov('APPROOV JWT TOKEN INVALID: %s' % e)
+        return None
+
+def _getApproovToken():
+
+    message = 'REQUEST WITH APPROOV TOKEN HEADER EMPTY OR MISSING'
+
+    approov_token = _getHeader('approov-token')
+
+    if _isEmpty(approov_token):
+
+        if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True:
+            _logApproov('REJECTED ' + message)
+            abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 400))
+
+        _logApproov(message)
+
+        return None
+
+    approov_token_decoded = _decodeApproovToken(approov_token)
+
+    if _isEmpty(approov_token_decoded):
+        return None
+
+    return approov_token_decoded
+
+def _handleApproovProtectedRequest(approov_token_decoded):
+
+    message = 'REQUEST WITH VALID APPROOV TOKEN'
+
+    if not approov_token_decoded:
+        message = 'REQUEST WITH INVALID APPROOV TOKEN'
+
+    if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is True and not approov_token_decoded:
+        _logApproov('REJECTED ' + message)
+        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))
+
+    _logApproov('ACCEPTED ' + message)
+
+def _checkApproovTokenBinding(approov_token_decoded, token_binding_header):
+    if _isEmpty(approov_token_decoded):
+        return False
+
+    if 'pay' in approov_token_decoded:
+
+        # We need to hash and base64 encode the token binding header, because that's how it was included in the Approov
+        # token on the mobile app.
+        token_binding_header_hash = sha256(token_binding_header.encode('utf-8')).digest()
+        token_binding_header_encoded = b64encode(token_binding_header_hash).decode('utf-8')
+
+        return approov_token_decoded['pay'] == token_binding_header_encoded
+
+    return False
+
+def _handlesApproovTokenBindingVerification(approov_token_decoded, token_binding_header):
+
+    if not 'pay' in approov_token_decoded:
+        message = 'REQUEST WITH APPROOV TOKEN MISSING THE CLAIM TO VERIFY THE TOKEN BINDING'
+
+        if APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is True:
+            _logApproov('REJECTED ' + message)
+            abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))
+        else:
+            _logApproov('ACCEPTED ' + message)
+            return
+
+    message = 'REQUEST WITH VALID TOKEN BINDING IN THE APPROOV TOKEN'
+
+    valid_token_binding = _checkApproovTokenBinding(approov_token_decoded, token_binding_header)
+
+    if not valid_token_binding:
+        message = 'REQUEST WITH INVALID TOKEN BINDING IN THE APPROOV TOKEN'
+
+    if not valid_token_binding and APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is True:
+        _logApproov('REJECTED ' + message)
+        abort(make_response(jsonify(BAD_REQUEST_RESPONSE), 401))
+
+    _logApproov('ACCEPTED ' + message)
+
 @api.route("/")
 def homePage():
     file = open('server/index.html', 'r')
@@ -74,8 +198,50 @@

 @api.route("/v1/forms")
 def forms():
-
     # How to handle and validate the authorization token is out of scope for this tutorial.
     authorization_token = _getAuthorizationToken()

     return _buildFormResponse()
+
+@api.route("/v2/hello")
+def helloV2():
+    return _buildHelloResponse()
+
+
+### APPROOV PROTECTED ENDPOINTS ###
+
+@api.route("/v2/shapes")
+def shapesV2():
+
+    # Will get the Approov JWT token from the header, decode it and on success
+    # will return it, otherwise None is returned.
+    approov_token_decoded = _getApproovToken()
+
+    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
+    # when the decoded approov token is empty.
+    _handleApproovProtectedRequest(approov_token_decoded)
+
+    return _buildShapeResponse()
+
+@api.route("/v2/forms")
+def formsV2():
+
+    # Will get the Approov JWT token from the header, decode it and on success
+    # will return it, otherwise None is returned.
+    approov_token_decoded = _getApproovToken()
+
+    # If APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN is set to True it will abort the request
+    # when the decoded approov token is empty.
+    _handleApproovProtectedRequest(approov_token_decoded)
+
+    # How to handle and validate the authorization token is out of scope for this tutorial, but
+    # you should only validate it after you have decoded the Approov token.
+    authorization_token = _getAuthorizationToken()
+
+    # Checks if the Approov token binding is valid and aborts the request when the environment variable
+    # APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING is set to True.
+    _handlesApproovTokenBindingVerification(approov_token_decoded, authorization_token)
+
+    # Now you are free to handle and validate your Authorization token as you usually do.
+
+    return _buildFormResponse()
```

As we can see the Approov integration in a current server is simple, easy and is done with just a few lines of code.

If you have not done it already, now is time to follow the
[Approov Shapes API Server](./docs/approov-shapes-api-server.md) walk-through
to see and have a feel for how all this works.


## PRODUCTION

In order to protect the communication between your mobile app and the API server
is important to only communicate hover a secure communication channel, aka HTTPS, and to use certificate pinning.

We do not use HTTPS and certificate pinning in this Approov integration example
because we want to be able to run the [Approov Shapes API Server](./docs/approov-shapes-api-server.md) in localhost.

Please bear in mind that HTTPS on its own is not enough, certificate pinning
must be also used to pin the connection between the mobile app and the API
server in order to prevent Man in the Middle Attacks and Approov provides out of the box [Dynamic Certificate Pinning](https://approov.io/product/dynamic-cert-pinning) to allow your mobile app to pin the connection to your API server without for you to have to write a single line of code, while giving you the ability to update the pins remotely with the [Approov CLI Tool](https://approov.io/docs/latest/approov-cli-tool-reference/#api-command). Yes you will not need to release a new mobile app to revoke/rotate certificates.
