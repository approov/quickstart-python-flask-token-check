# APPROOV SHAPES API SERVER

The Approov Shapes API Server contains endpoints with and without the Approov
protection. The protected endpoints differ in the sense that they can use or not
the optional token binding feature for the Approov token.

We will demonstrate how to call each API endpoint with screen-shots from Postman
and from the shell terminal. Postman is used here as an easy way to demonstrate
how you can play with the Approov integration in the API server, but to see a
real demo of how Approov would work in production you need to request a demo
[here](https://info.approov.io/demo).

When presenting the screen-shots we will present them as 2 distinct views. The
Postman view will tell how we performed the request and what response we got
back and the shell view show us the log entries that lets us see the result of
checking the Approov token and how the requested was handled.


## REQUIREMENTS

* Docker or Python 3 on your machine.
* Postman - to simulate calls to the the API server.

## SETUP

### Postman

To make the API request against the Shapes API server running on your machine you will need to use Postman and import [this collection](https://raw.githubusercontent.com/approov/postman-collections/master/quickstarts/shapes-api/shapes-api.postman_collection.json) that contains all the API endpoints prepared with all scenarios we want to demonstrate.

### Clone the Repo

To run the Shapes API server on localhost you will need to have the repos for this demo on your machine.

Clone from Github with:

```bash
git clone https://github.com/approov/quickstart-python-flask-token-check.git
cd quickstart-python-flask-token-check/servers/shapes-api
```

### The Environment File

Lets' copy the `.env.example` to `.env` with the command:

```bash
cp .env.example .env
```

No modifications are necessary to the newly created `.env` in order to start running the demo.

### Docker Stack

In order to have an agnostic development environment through this tutorial we
recommend the use of Docker, that can be installed by following [the official
instructions](https://docs.docker.com/install/) for your platform, but feel free
to use your own setup, provided it satisfies the [requirements](#requirements).

A symlink `./stack` to the bash script `./bin/stack.bash` is provided in the root of the demo, at `/servers/shapes-api`, to make easy to use the docker stack to run this demo.

Show the usage help by running from `/servers/shapes-api`:

```bash
./stack --help
```

#### Building the docker image

From your machine terminal run:

```bash
./stack build
```
> **NOTE:** The docker image will contain the Python Flask Approov Shapes API Server with the dependencies already installed.


#### Getting a shell terminal inside the docker container

Unless you choose to not follow this demo with the provided docker stack you need to get a shell inside the docker container in order to run all the subsequent shell commands that you will be instructed to execute during the demo.

From your machine terminal execute:

```bash
./stack shell
```

## RUNNING THE APPROOV SHAPES API SERVER

We will run this demo first with Approov enabled and a second time with Approov
disabled. When Approov is enabled any API endpoint protected by an Approov token
will have the request denied with a `400` or `401` response. When Approov is
disabled the check still takes place but no requests are denied, only the reason
for the failure is logged, if debug is enabled.

### The logs

When a request is issued from Postman you can see the logs being printed to your
shell terminal and you can search for `INFO:approov-protected-server:` to see
all log entries about requests protected by Approov and compare the logged
messages with the results returned to Postman for failures or success in
the validation of requests protected by Approov.

An example for an accepted request:

```bash
INFO:approov-protected-server:ACCEPTED REQUEST WITH VALID APPROOV TOKEN
INFO:approov-protected-server:ACCEPTED REQUEST WITH VALID TOKEN BINDING IN THE APPROOV TOKEN
172.17.0.1 - - [25/Jan/2019 16:25:45] "GET /v2/forms HTTP/1.1" 200 -
INFO:werkzeug:172.17.0.1 - - [25/Jan/2019 16:25:45] "GET /v2/forms HTTP/1.1" 200 -
```

Example for a rejected request:

```bash
INFO:approov-protected-server:ACCEPTED REQUEST WITH VALID APPROOV TOKEN
INFO:approov-protected-server:REJECTED REQUEST WITH INVALID TOKEN BINDING IN THE APPROOV TOKEN
172.17.0.1 - - [25/Jan/2019 16:25:51] "GET /v2/forms HTTP/1.1" 400 -
INFO:werkzeug:172.17.0.1 - - [25/Jan/2019 16:25:51] "GET /v2/forms HTTP/1.1" 400 -
```

### Starting the Python Flask Server

To start the server we want to issue the command:

```bash
flask run -h 0.0.0.0 -p 8002
```
> **NOTE**:
>
> The use of `-h 0.0.0.0` is only necessary when using the docker stack in order
> to expose the server outside of the container network, once by default it runs
> on `127.0.0.1`, that is only accessible from inside the container network.
>
> So in your computer you are free to just use `flask run -p 8002` instead of
> `flask run -h 0.0.0.0 -p 8002`.

### Endpoint Not Protected by Approov

The endpoint doesn't benefit from Approov protection and the goal here is to
show that both Approov protected and unprotected endpoints can coexist in the
same API server.

#### /v2/hello

**Postman View:**

![postman hello endpoint](./assets/img/postman-hello.png)
> As we can see we have not set any headers.

**Shell view:**

![shell terminal hello endpoint](./assets/img/shell-hello.png)
> As expected the logs don't have entries with Approov errors.


**Request Overview:**

Looking into the Postman view, we can see that the request was sent without the
`Approov-Token` header and we got a `200` response that matches the one in the
logs output from the shell view.


### Endpoints Protected by an Approov Token

The endpoints here will require an `Approov-Token` header and depending on the boolean
value for the environment variable `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` we will
have 2 distinct behaviors. When being set to `true` we refuse to fulfill the
request and when set to `false` we will let the request pass through. For both
behaviors we log the result of checking the Approov token, but only if the environment
variable `APPROOV_LOGGING_ENABLED` is set to `true`.

The default behavior is to have `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to
`true`, but you may feel more comfortable to have it set to `false` during
the initial deployment, until you are confident that you are only refusing bad
requests to your API server.

#### /v2/shapes - missing the Approov token header

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `true`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

##### Postman view:

![Postman - shapes endpoint without an Approov token](./assets/img/postman-shapes-missing-approov-token.png)
> As we can see we have not set any headers.

##### Shell view:

![Shell - shapes endpoint without an Approov token](./assets/img/shell-shapes-missing-approov-token.png)
> As expected status code in the logs matches the one in the Postman response.

##### Request Overview:

Looking to the Postman view we can see that we forgot to add the `Approov-Token`
header, thus a `400` response is returned.

In the shell view we can see in the logs entries that Approov is enabled and the Approov token is empty and this is the reason why the `400` response was
returned to Postman.

**Let's see the same request with Approov disabled**

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `false`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - shapes endpoint without an Approov token and approov disabled](./assets/img/postman-shapes-missing-approov-token-and-approov-disabled.png)
> Did you notice that now we have a successfully response back?

**Shell view:**

![Shell - shapes endpoint without an Approov token and approov disabled](./assets/img/shell-shapes-missing-approov-token-and-approov-disabled.png)
> Can you see where are the new log entries?

**Request Overview:**

We continue to not provide the `Approov-Token` header but this time we have a
`200` response with the value for the shape, because once Approov is disabled the
request is not denied.

Looking into the shell view we can see that the logs continue to tell us that
the JWT token is empty, but now we can see a log entry for the `/v2/shapes`
endpoint response with the status code `200`, meaning that the request was
fulfilled and a successful response sent back.


#### /v2/shapes - Malformed Approov token header

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `true`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - shapes endpoint with an invalid Approov token](./assets/img/postman-shapes-malformed-approov-token.png)
> Did you notice the `Approov-Token` with an invalid JWT token?

**Shell view:**

![Shell - shapes endpoint with an invalid Approov token](./assets/img/shell-shapes-malformed-approov-token.png)
> Can you spot what is the reason for the `401` response?

**Request Overview:**

In Postman we issue the request with a malformed `Approov-Token` header, that is
a normal string, not a JWT token, thus we get back a `401` response.

Looking to shell view we can see that the logs is also telling us that the
request was denied with a `401` and that the reason is an invalid JWT token,
that doesn't contain enough segments.


**Let's see the same request with Approov disabled**

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `false`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - shapes endpoint with an invalid Approov token and approov disabled](./assets/img/postman-shapes-malformed-approov-token-and-approov-disabled.png)


**Shell view:**

![Shell - shapes endpoint with an invalid Approov token and approov disabled](./assets/img/shell-shapes-malformed-approov-token-and-approov-disabled.png)


**Request Overview:**

In Postman, instead of sending a valid JWT token, we continue to send the
`Approov-Token` header as a normal string, but this time we got a `200` response
back because Approov is disabled, thus not blocking the request.

In the shell view we continue to see the same reason for the Approov token
validation failure and we can confirm the `200` response as Postman shows.


#### /v2/shapes - Valid Approov token header

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `true`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

> **NOTE**:
>
> For your convenience the Postman collection includes a token that only expires
> in a very distant future for this call "Approov Token with valid signature and
> expire time". For the call "Expired Approov Token with valid signature" an
> expired token is also included.


**Postman view with token correctly signed and not expired token:**

![Postman - shapes endpoint with a valid Approov token](./assets/img/postman-shapes-valid-approov-token.png)

**Postman view with token correctly signed but this time is expired:**

![Postman - shapes endpoint with a expired Approov token](./assets/img/postman-shapes-expired-approov-token.png)


**Shell view:**

![Shell - shapes endpoint with a valid and with a expired Approov token](./assets/img/shell-shapes-valid-and-expired-approov-token.png)


**Request Overview:**

In Postman we performed 2 requests with correctly signed Approov tokens, where the first one was successful while the second request failed with a `401` response. This was because the token in the second request as already expired as we can see by the log messages in the shell view. A token expires when the timestamp contained in the payload claim `exp` is in the past.

**Let's see the same request with Approov disabled**

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN` set to `false`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```
**Postman view with token valid for 1 minute:**

![Postman - shapes endpoint with a valid Approov token and Approov disabled](./assets/img/postman-shapes-valid-approov-token-and-approov-disabled.png)

**Postman view with same token but this time is expired:**

![Postman - shapes endpoint with a expired Approov token and Approov disabled](./assets/img/postman-shapes-expired-approov-token-and-approov-disabled.png)

**Shell view:**

![Shell - shapes endpoints with a valid and with an expired Approov token and Approov disabled](./assets/img/shell-shapes-approov-disabled-with-valid-and-expired-approov-token.png)
> Can you spot where is the difference between this shell view and the previous
> one?

**Request Overview:**

We repeated the same two requests, but this time we got both of them with `200` responses.

If we look into the shell view we can see that the first request have
a valid token and in the second request the token is not valid because is
expired, but once Approov is disabled the request is accepted.

### Endpoints Protected with the Approov Token Binding

The token binding is optional in any Approov token and you can read more about them [here](./../README.md#approov-validation-process).

The requests where the Approov token binding is checked will be rejected on failure, but
only if the environment variable `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING`
is set to `true`. To bear in mind that before this check is done the request
have already been through the same flow we have described for the `/v2/shapes` endpoint.


#### /v2/forms - Invalid Approov Token Binding

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING` set to `true`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - forms endpoint with an invalid Approov token binding](./assets/img/postman-forms-invalid-approov-token-binding.png)

**Shell view:**

![Shell - forms endpoint with an invalid Approov token binding](./assets/img/shell-forms-invalid-approov-token-binding.png)

**Request Overview:**

In Postman we added an Approov token with a token binding not matching the
`Authorization` token, thus the API server rejects the request with a `401` response.

While we can see in the shell view that the request is accepted for the Approov
token itself, afterwards we see the request being rejected, and this is due to
an invalid token binding in the Approov token, thus returning a `401` response.

> **IMPORTANT**:
>
> When decoding the Approov token we only check if the signature and expiration
> time are valid, nothing else within the token is checked.
>
> The token binding check works on the decoded Approov token to validate if the
> value from the key `pay` matches the one for the token binding header, that in
> our case is the `Authorization` header.


**Let's see the same request with Approov disabled**

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING` set to `false`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - forms endpoint with an invalid Approov token binding](./assets/img/postman-forms-invalid-approov-token-binding-with-approov-disabled.png)

**Shell view:**

![Shell - forms endpoint with an invalid Approov token binding](./assets/img/shell-forms-invalid-approov-token-binding-with-approov-disabled.png)

**Request Overview:**

We still have the invalid token binding in the Approov token, but once we have
disabled Approov we now have a `200` response.

In the shell view we can confirm that the log entry still reflects that the
token binding is invalid, but this time a `200` response is logged instead of
the previously `401` one, and this is because Approov is now disabled.


#### /v2/forms - Valid Approov Token Binding

Make sure that the `.env` file contains `APPROOV_ABORT_REQUEST_ON_INVALID_TOKEN_BINDING` set to `true`.

Cancel current server session with `ctrl+c` and start it again with:

```bash
flask run -h 0.0.0.0 -p 8002
```

**Postman view:**

![Postman - forms endpoint with valid Approov Token Binding](./assets/img/postman-forms-valid-approov-token-binding.png)

**Shell view:**

![Shell - forms endpoint with valid Approov Token Binding](./assets/img/shell-forms-valid-approov-token-binding.png)

**Request Overview:**

In the Postman view the `Approov-Token` contains a valid token binding, the
`Authorization` token value, thus when we perform the request, the API server
doesn't reject it, and a `200` response is sent back.

The shell view confirms us that the token binding is valid and we can also see
the log entry confirming the `200` response.
