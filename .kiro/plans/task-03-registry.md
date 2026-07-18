# Task 3: Local Docker Registry

## Objective

Add a self-hosted Docker registry container to the infrastructure stack so built images are stored locally rather than pushed to Docker Hub. This is the foundation for the CI/CD pipeline — builds push here, deployments pull from here.

## Prerequisites

- Task 2 complete (app images exist to push/pull)
- Docker Desktop running

## Implementation Steps

### 3.1 Add registry service to infrastructure Compose

Location: `infra/docker-compose.infra.yml`

```yaml
services:
  registry:
    image: registry:2
    container_name: greencloud-registry
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - registry-data:/var/lib/registry
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
    networks:
      - infra-net
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5000/v2/"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  registry-data:

networks:
  infra-net:
    name: greencloud-infra
```

### 3.2 Configure registry for local network access

- For local dev on Windows: `localhost:5000` works out of the box
- For Pi deployment: registry needs to be accessible on the local network
- Add Docker daemon config to allow insecure registry for local network:
  - Document the required `/etc/docker/daemon.json` change:
    ```json
    { "insecure-registries": ["192.168.x.x:5000"] }
    ```
- Alternatively, plan for TLS with self-signed cert (document as future enhancement)

### 3.3 Create registry management scripts

Location: `scripts/`

- `registry-list.sh` — list all repositories and tags
  ```bash
  curl -s http://localhost:5000/v2/_catalog | jq
  ```
- `registry-tags.sh <repo>` — list tags for a specific image
  ```bash
  curl -s http://localhost:5000/v2/$1/tags/list | jq
  ```
- `registry-cleanup.sh` — garbage collect unused layers
  ```bash
  docker exec greencloud-registry registry garbage-collect /etc/docker/registry/config.yml
  ```

### 3.4 Update app Compose files to use local registry

Update `docker-compose.prod.yml` and `docker-compose.dev.yml`:
- Image references: `localhost:5000/greencloud/api:prod`, `localhost:5000/greencloud/ui:prod`
- Use `${REGISTRY_HOST:-localhost:5000}` variable for portability between local dev and Pi

### 3.5 Create a build-and-push script

Location: `scripts/build-and-push.sh`

```bash
#!/bin/bash
# Build images for the target platform and push to local registry
REGISTRY=${REGISTRY_HOST:-localhost:5000}
PLATFORM=${TARGET_PLATFORM:-linux/arm64}
TAG=${1:-latest}

docker buildx build --platform $PLATFORM \
  -t $REGISTRY/greencloud/api:$TAG \
  --push \
  ../services/app/api/

docker buildx build --platform $PLATFORM \
  -t $REGISTRY/greencloud/ui:$TAG \
  --push \
  ../services/app/ui/
```

### 3.6 Document registry architecture

Add to `docs/architecture/registry.md`:
- Why self-hosted (no external dependency, full control, carbon accounting)
- Image naming convention: `<registry>/greencloud/<service>:<environment>`
- Tag strategy: `prod`, `dev`, `latest`, git SHA for rollback
- Storage estimates and cleanup policy

## Test Requirements

- `docker compose -f infra/docker-compose.infra.yml up -d` starts the registry
- `curl http://localhost:5000/v2/` returns `{}`
- Build an image, push to `localhost:5000/greencloud/api:test`, pull it back, run it
- Registry data persists across container restarts (volume mount)
- `docker-compose.prod.yml` pulls from local registry successfully

## Demo

Images are stored and served from your own registry. Running `docker pull localhost:5000/greencloud/api:latest` retrieves the image you built. The prod Compose stack starts by pulling from the registry rather than building locally.

## Dependencies

- Task 2 (app images to push/pull)

## Estimated Effort

- 2-3 hours
