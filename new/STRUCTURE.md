# Quickstart Structure

In general, we seek to achieve the following:

1. A quickstart which runs out-of-the-box.
1. The ability for a developer to make it "real" by:
    * Modifying the server to use their real Approov secret (`approov secret -get base64`).
    * Generating real example tokens (`approov token -genExample example.com`).
1. Making it clear that Approov is easy to enable *and* disable.
1. A single idiomatic function which a developer can use as a starting point for their real integration.

## Code Structure

As far as the language allows, a minimal set of files (ideally one) should define:

- Requirements / Imports
- Configuration
    - Defaults which work with the test script(s) out-of-the-box
    - Ability for the user to override the defaults
        - Overriding defaults should not break test script(s)
- Helper Functions
    - Constructing the Token Binding input
        - For the absence of doubt, this is a string
    - Generating the Token Binding hash (to compare to `pay`)
        - For the absence of doubt: this is a base64-encoded SHA256 hash of the above string
- An `approov` function with the following parameters:
    - An HTTP request object.
    - A boolean flag to enable or disable token checking.
    - A list of strings, each representing a Header whose value should be included in the Token Binding input.
        - The order of this list is important.
    - A boolean flag to enable or disable Message Signing.
- Optionally, any idiomatic language features which are build on top of this function. Examples may include:
    - Python decorators.
    - Golang middlewares.
- HTTP Server definition with the following endpoints:
    - `/unprotected` - `approov(false, [], false)`
    - `/token-check` - `approov(true, [], false)`
    - `/token-binding-1` - `approov(true, ['authorization'], false)`
    - `/token-binding-2` - `approov(true, ['authorization', 'content-digest'], false)`
    - `/msg-sig` - `approov(true, [], true)`
    - `/msg-sig-token-binding` - `approov(true, ['authorization'], true)`
    - `/approov-state` - returns 200 if APPROOV_ENABLED, otherwise 501
- A `main` function which runs the server.

## Code Style

The following should be true of our code:

- It is as idiomatic as possible.
- It is as agnostic as possible. For example:
    - We should return errors rather HTTP responses.
    - We should use libraries which will easily integrate with the majority of customer codebases (e.g. Django's `current_app.logger` or Go's `log.Logger`)
- All functions, parameters, and returns should be documented in the preferred style of the language.
