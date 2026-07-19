# Docker Registry Architecture

## Overview

GreenCloud uses a self-hosted Docker registry (`registry:2`) to store all container images. This includes both GreenCloud's own service images and third-party/user application images deployed through the PaaS. This eliminates external dependencies for deployments and keeps all image data within the local network for carbon accounting purposes.

## Why Self-Hosted

- **No external dependency** — deployments don't rely on Docker Hub availability or rate limits
- **Full control** — images stay on the local network, never leave your infrastructure
- **Carbon accounting** — all storage energy is measurable (it's on your Pi)
- **Speed** — pulling from a local registry over gigabit ethernet is near-instant
- **Privacy** — your application code never leaves your network
- **Multi-tenant** — user apps and platform images share the same registry with namespace isolation

## Image Naming Convention

```
<registry-host>:<port>/greencloud/<service>:<tag>
```

### Platform service images

- `localhost:5000/greencloud/api:prod`
- `localhost:5000/greencloud/api:dev`
- `localhost:5000/greencloud/ui:prod`
- `localhost:5000/greencloud/ui:a1b2c3d` (git SHA for rollback)
- `localhost:5000/greencloud/carbon-engine:latest`

### Third-party / user app images

User-deployed applications follow the same namespace convention:

- `localhost:5000/greencloud/meal-planner-api:latest`
- `localhost:5000/greencloud/meal-planner-ui:latest`
- `localhost:5000/greencloud/<app-name>:latest`

All images live under the `greencloud/` namespace. User apps are distinguished by their service name rather than a separate namespace, keeping the registry structure flat and simple.

**Future consideration:** When multi-user management is implemented, the naming convention may evolve to include user namespaces (e.g., `localhost:5000/greencloud/<username>/<app>:<tag>`).

## Tag Strategy

| Tag | Purpose | When Created |
|-----|---------|--------------|
| `prod` | Current production deployment | On push to `main`/`prod` branch |
| `dev` | Current dev deployment | On push to `dev` branch |
| `latest` | Most recent build (any branch) | Every build |
| `<git-sha>` | Specific commit (7 chars) | Every build (for rollback) |

For third-party apps that don't have a CI/CD pipeline, `latest` is the primary tag used.

## Storage

- Registry data stored in a Docker volume: `registry-data`
- On the Pi, this maps to the NVMe SSD (fast I/O)
- Each image layer is stored once (content-addressed) — shared layers save space
- Estimated storage: ~200MB per service version (API + UI combined)
- Third-party app images add to storage proportionally

## Cleanup Policy

- Keep last 5 tagged versions per service
- Run garbage collection weekly to reclaim unused layers:
  ```bash
  ./scripts/registry-cleanup.sh
  ```
- Before cleanup, ensure no running containers reference old images
- Third-party app images follow the same retention policy

## Network Access

### Local Development (Windows PC)

Registry is accessible at `localhost:5000` — no special configuration needed.

### Production (Pi + Mini PC)

The Mini PC needs to push images to the registry on the Pi. Configure Docker on the Mini PC to allow the insecure registry:

```json
// /etc/docker/daemon.json on Mini PC
{
  "insecure-registries": ["192.168.1.100:5000"]
}
```

**Future enhancement:** Add TLS with a self-signed certificate for encrypted transport between Mini PC and Pi.

## Architecture Diagram

```
Mini PC (builder)                    Raspberry Pi 5
┌─────────────────┐                 ┌─────────────────────────────────┐
│ docker buildx   │ ──── push ────> │ registry:2 (:5000)              │
│ (ARM64 images)  │                 │   ├─ greencloud/api:prod        │
└─────────────────┘                 │   ├─ greencloud/ui:prod         │
                                    │   ├─ greencloud/carbon-engine   │
Developer workstation               │   ├─ greencloud/meal-planner-*  │
┌─────────────────┐                 │   └─ greencloud/<user-app>      │
│ docker build    │ ──── push ────> │                                 │
│ (user apps)     │                 │ greencloud-agent                │
└─────────────────┘                 │   └─ docker pull from registry  │
                                    └─────────────────────────────────┘
```

## Pushing a Third-Party App

To deploy an external application to GreenCloud:

```bash
# Build the image (use templates/ for Dockerfile if needed)
docker build -t localhost:5000/greencloud/my-app:latest .

# Push to the local registry
docker push localhost:5000/greencloud/my-app:latest

# Verify it's in the catalog
curl http://localhost:5000/v2/_catalog
# {"repositories":["greencloud/api","greencloud/my-app","greencloud/ui"]}
```

The image is now available for deployment. Add it to a Compose file with Traefik labels to make it accessible.
