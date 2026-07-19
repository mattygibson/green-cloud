# GreenCloud — How-to Guide

A step-by-step guide to get GreenCloud running on your machine.

## What You'll Get

After following this guide, you'll have:
- A full-stack web application (React + FastAPI + PostgreSQL)
- A reverse proxy routing traffic via domain names (Traefik)
- A local Docker registry storing your images
- A deployment management API (GreenCloud API)
- A node agent for container orchestration
- Cloudflare Tunnel for public access (*.green-cloud.uk)
- Dynamic app discovery and hosted applications dashboard

All running locally on your machine via Docker.

## Environments

GreenCloud has two app environments:

| Environment | Purpose | When to use |
|-------------|---------|-------------|
| **Dev** | Testing, verification, trying things out | Day-to-day development and all testing |
| **Prod** | Finished, proven product only | Final deployment — don't use for testing |

**Rule: Always use the dev environment for testing. Prod is only for the finished product.**

## Prerequisites

You need:
- **Windows 10/11** (or Linux/Mac — adjust commands accordingly)
- **Docker Desktop** — [Download here](https://docs.docker.com/desktop/setup/install/windows-install/)
- **Git** — [Download here](https://git-scm.com/downloads)
- **uv** (Python package manager) — Install with:
  ```
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

## Step 1: Clone the Repository

```bash
git clone https://github.com/mattygibson/green-cloud.git
cd green-cloud
```

## Step 2: Start Docker Desktop

Open Docker Desktop and wait until it shows "Docker is running" (green icon in the system tray).

**Important:** In Docker Desktop Settings → General, enable:
- "Expose daemon on tcp://localhost:2375 without TLS"

Click Apply and wait for Docker to restart.

## Step 3: Start the Infrastructure

The infrastructure stack includes the Docker registry, GreenCloud API, and deployment agent:

```bash
docker compose -f infra/docker-compose.infra.yml up -d
```

Wait ~30 seconds for everything to become healthy, then verify:

```bash
# Check all containers are healthy
docker ps --format "table {{.Names}}\t{{.Status}}"

# Test the registry
curl http://localhost:5000/v2/
# Expected: {}

# Test the GreenCloud API
curl http://localhost:8000/health
# Expected: {"status":"healthy",...}

# Test the agent
curl http://localhost:8001/health
# Expected: {"status":"healthy",...}
```

## Step 4: Start the Dev App

The dev stack includes PostgreSQL, FastAPI backend, React frontend — use this for all testing:

```bash
docker compose -f infra/docker-compose.dev.yml up -d --build
```

First run will take a few minutes to build images. Subsequent starts are fast.

Wait ~30 seconds, then verify:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

All containers should show `(healthy)` or `Up`.

## Step 5: Access the Application

Open your browser:

| URL | What it shows |
|-----|---------------|
| http://localhost:3001 | Dev React UI |
| http://localhost:8001 | Dev API (also agent — see note) |
| http://localhost:5433 | Dev PostgreSQL (connect via pgAdmin) |
| http://localhost:8000/docs | GreenCloud API — Swagger docs |
| http://localhost:8001/docs | Agent API — Swagger docs |
| http://localhost:5000/v2/ | Docker Registry |

**pgAdmin connection (dev database):**
- Host: `localhost`
- Port: `5433`
- Database: `greencloud_dev`
- Username: `greencloud`
- Password: `changeme_dev`

## Step 6: Try the API

Create an item:

```bash
curl -X POST http://localhost:8001/api/v1/items \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Item", "description": "Hello from GreenCloud!"}'
```

List items:

```bash
curl http://localhost:8001/api/v1/items
```

## Step 7: Run the Sanity Check Image

To quickly verify Docker and the registry are working:

```bash
docker build -t localhost:5000/greencloud/test:latest services/app/test/
docker push localhost:5000/greencloud/test:latest
docker run -d --name sanity-check -p 9090:80 localhost:5000/greencloud/test:latest
```

Open http://localhost:9090 — you should see "Hello World, Images are working!"

Clean up: `docker rm -f sanity-check`

## Step 8: Test the Deployment Pipeline

Trigger a build through the GreenCloud API:

```bash
curl -X POST http://localhost:8000/deployments/trigger \
  -H "Content-Type: application/json" \
  -d '{"environment":"dev","branch":"dev","commit_sha":"test123"}'
```

Wait ~60 seconds, then check the result:

```bash
curl http://localhost:8000/deployments/1/logs
```

Status should be `built` with both API and UI images pushed to the registry.

## Step 9: Deploy to Production (when ready)

Only deploy to prod when the dev version is tested and verified:

```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

Prod URLs:
| URL | What it shows |
|-----|---------------|
| http://app.localhost | Production React UI |
| http://app.localhost/health | Production API health |
| http://app.localhost/api/v1/items | Production items endpoint |
| http://localhost:8080 | Traefik dashboard |

## Step 10: Enable Public Access (Cloudflare Tunnel)

To make services publicly accessible via `*.green-cloud.uk`:

1. Ensure `CLOUDFLARE_TUNNEL_TOKEN` is set in `infra/.env`
2. Start with the tunnel profile:

```bash
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d
docker compose -f infra/docker-compose.prod.yml up -d
```

The wildcard tunnel route (`*.green-cloud.uk → greencloud-traefik:80`) means any new app you deploy with a Traefik host rule is publicly accessible immediately — no manual DNS or tunnel changes needed.

See [Domain and Tunnel Setup](runbooks/domain-and-tunnel-setup.md) for full details.

## Deploying External Apps

GreenCloud can host third-party applications alongside the core platform. For example, the Meal-Planner app is deployed at [meal-planner.green-cloud.uk](https://meal-planner.green-cloud.uk).

### Quick steps

1. Use a Dockerfile template from the `templates/` directory (Python FastAPI or React Vite available)
2. Build and push the image to the local registry:
   ```bash
   docker build -t localhost:5000/greencloud/my-app:latest .
   docker push localhost:5000/greencloud/my-app:latest
   ```
3. Add your app's service to a Compose file with Traefik labels:
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.my-app.rule=Host(`my-app.green-cloud.uk`)"
   ```
4. Start the app — it's publicly accessible immediately via wildcard routing.

For the full walkthrough, see [Deploy Your First App](guides/deploy-your-first-app.md).

### App Discovery

The GreenCloud API exposes a `/api/v1/apps` endpoint that dynamically queries Docker for running user apps. The dashboard at [app.green-cloud.uk](https://app.green-cloud.uk) displays these in the "Hosted Applications" section automatically.

## Useful Commands

| Command | What it does |
|---------|--------------|
| `make infra-up` | Start infrastructure (registry, API, agent) |
| `make infra-down` | Stop infrastructure |
| `make dev-up` | Start dev app stack (use this for testing) |
| `make dev-down` | Stop dev app stack |
| `make prod-up` | Start production app stack (finished product only) |
| `make prod-down` | Stop production app stack |
| `make clean` | Stop everything and delete all volumes |
| `make logs-dev` | Follow dev logs |
| `make logs-prod` | Follow production logs |
| `make logs-infra` | Follow infrastructure logs |

## Stopping Everything

```bash
make clean
```

This stops all containers and removes volumes (database data will be lost).

To stop without losing data:

```bash
make dev-down
make infra-down
```

## Troubleshooting

### "Port already in use"

Another process is using a required port. Find it:

```bash
netstat -ano | findstr :80
```

Stop the conflicting process or change the port in the compose file.

### Traefik shows 404 (prod only)

If `http://app.localhost` returns 404:
1. Check Traefik dashboard at `http://localhost:8080` — are routers registered?
2. If no routers shown, the Docker provider isn't connecting. Verify Docker Desktop's TCP socket is enabled.

### Container keeps restarting

Check its logs:

```bash
docker logs <container-name>
```

### "Cannot connect to the Docker daemon"

Docker Desktop isn't running. Start it and wait for the green icon.

### New app not accessible publicly

If you deployed a new app and it's not reachable at `<app>.green-cloud.uk`:
1. Verify the container is running: `docker ps | grep <app>`
2. Check Traefik labels are correct (Host rule matches the subdomain)
3. Ensure the container is on the `greencloud-prod` network
4. Check Traefik dashboard for the router entry
5. No DNS changes needed — wildcard CNAME covers all subdomains

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Your Machine (Docker Desktop)                        │
│                                                      │
│  ┌─── Infrastructure Stack ──────────────────────┐  │
│  │ greencloud-registry (:5000)                    │  │
│  │ greencloud-api (:8000)                         │  │
│  │ greencloud-agent (:8001)                       │  │
│  │ greencloud-tunnel (Cloudflare)                 │  │
│  │ prometheus + grafana + loki                    │  │
│  │ carbon-engine                                  │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── Dev Stack (daily use) ─────────────────────┐  │
│  │ dev-db (PostgreSQL :5433)                      │  │
│  │ dev-api (FastAPI)                              │  │
│  │ dev-ui (React + nginx :3001)                   │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── Production Stack (finished product) ───────┐  │
│  │ greencloud-traefik (:80, :8080)                │  │
│  │ prod-db (PostgreSQL — not exposed)             │  │
│  │ prod-api (FastAPI)                             │  │
│  │ prod-ui (React + nginx)                        │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌─── User Apps ─────────────────────────────────┐  │
│  │ meal-planner (meal-planner.green-cloud.uk)     │  │
│  │ ... (any app deployed via PaaS)                │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## What's Next

The remaining work to reach full production readiness:

- **Hardware deployment** — Raspberry Pi 5 + Mini PC procurement and setup
- **Wake-on-LAN build pipeline** — Mini PC builds ARM64 images on demand (depends on hardware)
- **Blue/green zero-downtime deployments** — rolling updates without downtime
- **Multi-user management** — user registration, per-user API keys, app ownership
- **Cloudflare Access** — protect admin services (Grafana, Traefik dashboard) from public access
- **USB power meter** — real energy measurements for accurate carbon accounting

See the [project blueprint](plan/greencloud-project-blueprint.md) for the full roadmap.
