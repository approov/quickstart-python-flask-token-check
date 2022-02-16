# DEPLOYMENT

Guide to deploy the Python Flask backend into a production demo server.

For now this will be a small set of manual steps, but later we may want to automate this via the CI pipeline, by building the docker image and push it to the docker hub.

## CLONE

```
git clone https://github.com/approov/python-flask_approov-shapes-api-server.git && cd python-flask_approov-shapes-api-server
```

## ENVIRONMENT

Copy the `.env.example`:

```
cp .env.example .env
```

### The Appoov secret

The `v2/*` endpoints are protected by the Approov Token, thus we need to set the Approov secret for `python-flask-shapes.approov.io`.

Get the Approov secret with:

```
approov secret /path/to/administration.tok -get base64
```

Add it to the `.env` file:

```
APPROOV_BASE64_SECRET=approov-base64-encoded-secret-here
```

## HOW TO RUN

### Build the Docker Container

```
sudo docker-compose build
```

### Bring the API up

```
sudo docker-compose up -d
```

### Bring the API down

```
sudo docker-compose down
```

### Check the Logs

```
sudo docker-compose logs --follow --tail 20
```
