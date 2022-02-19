# Approov Integrations Examples

[Approov](https://approov.io) is an API security solution used to verify that requests received by your backend services originate from trusted versions of your mobile apps, and here you can find the Hello servers examples that are the base for the Approov [quickstarts](/docs) for the Python Flask framework.

For more information about how Approov works and why you should use it you can read the [README](/README.md) at the root of this repo.

If you are looking for the Approov quickstarts to integrate Approov in your Python Flask API server then you can find them [here](/docs).


## Hello Server Examples

To learn more about each Hello server example you need to read the README for each one at:

* [Unprotected Server](./src/unprotected-server)
* [Approov Protected Server - Token Check](./src/approov-protected-server/token-check)
* [Approov Protected Server - Token Binding Check](./src/approov-protected-server/token-binding-check)


## Docker Stack

The docker stack provided via the `docker-compose.yml` file in this folder is used for development proposes and if you are familiar with docker then feel free to also use it to follow along the examples.

If you decide to use the docker stack then you need to bear in mind that the Postman collections, used to test the servers examples, will connect to port `8002` therefore you cannot start all docker compose services at once, for example with `docker-compose up`, instead you need to run one at a time as exemplified below.

For the unprotected server:

```bash
sudo docker-compose up unprotected-server
```

To run the Approov protected servers you need to provide a `.env` file with the Approov Base64 secret, therefore you need to copy the file `.env.example` to `.env` and add [the dummy secret](/README.md#the-dummy-secret) used only for test proposes on this examples.

For the Approov Token Check:

```bash
sudo docker-compose up approov-token-check
```

For the Approov Token Binding Check:

```bash
sudo docker-compose up approov-token-check
```

If you find any issue while running the examples then just open an issue on this repo with the steps to reproduce it and we will help you to solve them.
