# Test Image — Deployment Sanity Check

## What

A minimal "Hello World" Docker image with zero dependencies. It's a single HTML page served by nginx — no database, no API, no configuration needed.

## Why

Use this image to quickly verify that:
- Docker is running and can build images
- The local registry accepts pushes and serves pulls
- The deployment pipeline builds and stores images correctly
- A container can be run from a registry image

If this image works, you know the infrastructure is healthy. If it doesn't, the problem is in Docker/registry/networking — not in your application code.

## How to Use

### Build and push to registry

```bash
docker build -t localhost:5000/greencloud/test:latest services/app/test/
docker push localhost:5000/greencloud/test:latest
```

### Run it

```bash
docker run -d --name sanity-check -p 9090:80 localhost:5000/greencloud/test:latest
```

Open http://localhost:9090 — you should see "Hello World, Images are working!"

### Clean up

```bash
docker rm -f sanity-check
```

### Via the deployment pipeline

Trigger a dev deployment to test the full pipeline:

```bash
curl -X POST http://localhost:8000/deployments/trigger \
  -H "Content-Type: application/json" \
  -d '{"environment":"dev","branch":"dev","commit_sha":"test123"}'
```

Then check `curl http://localhost:8000/deployments/1/logs` to verify the build pipeline runs end-to-end.

## When to Use

- After setting up Docker for the first time
- After changing Docker Desktop settings
- After modifying the registry or pipeline code
- When debugging "is it the app or the infrastructure?"
- As a smoke test before deploying real changes
