# Docker Registry Architecture

## Overview

GreenCloud uses a self-hosted Docker registry (`registry:2`) to store all container images. This eliminates external dependencies for deployments and keeps all image data within the local network for carbon accounting purposes.

## Why Self-Hosted

- **No external dependency** — deployments don't rely on Docker Hub availability or rate limits
- **Full control** — images stay on the local network, never leave your infrastructure
- **Carbon accounting** — all storage energy is measurable (it's on your Pi)
- **Speed** — pulling from a local registry over gigabit ethernet is near-instant
- **Privacy** — your application code never leaves your network

## Image Naming Convention

```
<registry-host>:<port>/greencloud/<service>:<tag>
```

Examples:
- `localhost:5000/greencloud/api:prod`
- `localhost:5000/greencloud/api:dev`
- `localhost:5000/greencloud/ui:prod`
- `localhost:5000/greencloud/ui:a1b2c3d` (git SHA for rollback)

## Tag Strategy

| Tag | Purpose | When Created |
|-----|---------|--------------|
| `prod` | Current production deployment | On push to `main`/`prod` branch |
| `dev` | Current dev deployment | On push to `dev` branch |
| `latest` | Most recent build (any branch) | Every build |
| `<git-sha>` | Specific commit (7 chars) | Every build (for rollback) |

## Storage

- Registry data stored in a Docker volume: `registry-data`
- On the Pi, this maps to the NVMe SSD (fast I/O)
- Each image layer is stored once (content-addressed) — shared layers save space
- Estimated storage: ~200MB per service version (API + UI combined)

## Cleanup Policy

- Keep last 5 tagged versions per service
- Run garbage collection weekly to reclaim unused layers:
  ```bash
  ./scripts/registry-cleanup.sh
  ```
- Before cleanup, ensure no running containers reference old images

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
┌─────────────────┐                 ┌─────────────────────┐
│ docker buildx   │ ──── push ────> │ registry:2 (:5000)  │
│ (ARM64 images)  │                 │   └─ volume: data   │
└─────────────────┘                 │                     │
                                    │ greencloud-agent    │
                                    │   └─ docker pull    │
                                    │       from registry │
                                    └─────────────────────┘
```
