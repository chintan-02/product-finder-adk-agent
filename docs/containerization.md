# Backend containerization

## Why the backend is containerized separately

The assignment requires the backend on Cloud Run. The React frontend is a
static build and does not need to be bundled into the Python service. Keeping
them separate produces a smaller backend image and lets the browser call the
Cloud Run URL directly, as required by the PDF.

## Container design

- Python 3.12 slim base image
- Dependencies installed before application code for reusable build caching
- Only runtime application files copied into the image
- `.env`, tests, caches, virtual environments, and Git metadata excluded
- Dedicated non-root `appuser`
- Unbuffered Python logs for Cloud Logging
- Uvicorn bound to `0.0.0.0`
- Port read from Cloud Run's injected `PORT`, with local default `8080`
- `exec` used so Uvicorn receives Cloud Run termination signals directly

## Build on Apple Silicon for Cloud Run

Run these commands from the repository root on the MacBook:

```bash
docker build \
  --platform linux/amd64 \
  --file backend/Dockerfile \
  --tag product-finder-api:local \
  backend
```

Cloud Run requires a Linux image with an `amd64` entry. The explicit platform
prevents an Apple Silicon Mac from producing an ARM-only image.

## Run locally

Create `backend/.env` from the example and set the real API key locally. Never
commit it.

```bash
docker run --rm \
  --name product-finder-api \
  --publish 8080:8080 \
  --env-file backend/.env \
  --env PORT=8080 \
  product-finder-api:local
```

The container does not require the key for its health endpoint:

```bash
curl --fail http://localhost:8080/health
```

Expected response:

```json
{"status":"healthy","service":"product_finder"}
```

Then test the live agent endpoint:

```bash
curl --fail \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{"message":"What clothing items are available under $50?"}' \
  http://localhost:8080/api/v1/chat
```

Expected product names are `UBC Hoodie` and `T-Shirt`. The exact conversational
message may vary, but `products`, `count`, and `applied_filters` must be correct.

## Inspect the runtime identity

This confirms that the container is not running as root:

```bash
docker run --rm --entrypoint id product-finder-api:local
```

The returned user must be `appuser`, not UID `0`.

## Stop a detached container

The documented command runs in the foreground and stops with `Ctrl+C`. If it
is started with `--detach`, stop it using:

```bash
docker stop product-finder-api
```
