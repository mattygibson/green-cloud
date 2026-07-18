# Task 2: Docker Compose Stacks for Full-Stack App

## Objective

Create two Docker Compose files (`docker-compose.prod.yml` and `docker-compose.dev.yml`) that define the full application stack (PostgreSQL + FastAPI + React) — runnable on your Windows PC via Docker Desktop now, portable to the Pi later.

## Prerequisites

- Task 1 complete (folder structure exists)
- Docker Desktop installed on Windows PC

## Implementation Steps

### 2.1 Create the FastAPI backend

Location: `services/app/api/`

- FastAPI application with:
  - `/health` — returns DB connection status
  - `/api/v1/items` — basic CRUD endpoint (proves DB works)
  - SQLAlchemy + Alembic for database management
  - Pydantic settings for config via environment variables
- `Dockerfile` with multi-stage build:
  - Stage 1: Install dependencies
  - Stage 2: Copy app, run with uvicorn
  - Target platforms: `linux/amd64` and `linux/arm64`
- `requirements.txt` or `pyproject.toml`

### 2.2 Create the React frontend

Location: `services/app/ui/`

- Vite + React + TypeScript app
- Single page that:
  - Calls the FastAPI `/health` endpoint
  - Displays "GreenCloud is running" with connection status
  - Shows environment indicator (DEV / PROD)
- `Dockerfile` with multi-stage build:
  - Stage 1: `node:20-alpine` — install deps, build
  - Stage 2: `nginx:alpine` — serve static files
  - nginx config to proxy `/api` requests to FastAPI

### 2.3 Create database initialisation

Location: `services/app/db/`

- `init.sql` — creates the initial schema
- Alembic migrations directory (in the API service)
- Separate volume mounts for dev and prod data

### 2.4 Create the prod Docker Compose file

Location: `infra/docker-compose.prod.yml`

```yaml
services:
  prod-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: greencloud_prod
      POSTGRES_USER: ${PROD_DB_USER}
      POSTGRES_PASSWORD: ${PROD_DB_PASSWORD}
    volumes:
      - prod-db-data:/var/lib/postgresql/data
    networks:
      - prod-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${PROD_DB_USER}"]
      interval: 5s
      timeout: 3s
      retries: 5

  prod-api:
    image: ${REGISTRY_HOST:-localhost:5000}/greencloud/api:prod
    build:
      context: ../services/app/api
      platforms:
        - linux/amd64
        - linux/arm64
    environment:
      DATABASE_URL: postgresql://${PROD_DB_USER}:${PROD_DB_PASSWORD}@prod-db:5432/greencloud_prod
      ENVIRONMENT: production
    depends_on:
      prod-db:
        condition: service_healthy
    networks:
      - prod-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prod-api.rule=Host(`app.${DOMAIN}`) && PathPrefix(`/api`)"

  prod-ui:
    image: ${REGISTRY_HOST:-localhost:5000}/greencloud/ui:prod
    build:
      context: ../services/app/ui
      platforms:
        - linux/amd64
        - linux/arm64
    networks:
      - prod-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prod-ui.rule=Host(`app.${DOMAIN}`)"

volumes:
  prod-db-data:

networks:
  prod-net:
    name: greencloud-prod
```

### 2.5 Create the dev Docker Compose file

Location: `infra/docker-compose.dev.yml`

Same structure as prod but with:
- Different container names (prefixed `dev-`)
- Different network (`greencloud-dev`)
- Different volume (`dev-db-data`)
- Hot-reload volume mounts for API and UI source code
- Different Traefik routing rules (`dev.app.${DOMAIN}`)
- `ENVIRONMENT: development` flag

### 2.6 Create environment files

- `infra/.env.prod` — prod database credentials, domain config
- `infra/.env.dev` — dev database credentials, domain config
- `infra/.env.example` — template with placeholder values (committed to git)

### 2.7 Create Traefik base configuration

Location: `infra/traefik/`

- `traefik.yml` — static config (entrypoints, providers, dashboard)
- Docker provider enabled (auto-discovers services via labels)
- Entrypoints: `web` (80), `websecure` (443)
- For local dev: use `*.localhost` domains (no DNS needed)

### 2.8 Local development convenience

- `Makefile` or shell scripts in `scripts/`:
  - `make prod-up` → `docker compose -f infra/docker-compose.prod.yml up -d`
  - `make dev-up` → `docker compose -f infra/docker-compose.dev.yml up -d`
  - `make dev-down` → stops dev stack
  - `make logs` → tails logs for both stacks

## Test Requirements

- `docker compose -f infra/docker-compose.prod.yml up --build` brings up all 3 services
- React UI at `app.localhost` shows data fetched from FastAPI
- FastAPI `/health` returns `{"status": "healthy", "database": "connected"}`
- Dev and prod stacks can run simultaneously without port conflicts
- Dev stack hot-reloads on file changes

## Demo

Full-stack app running locally with Traefik routing — accessible at `app.localhost` (prod) and `dev.app.localhost` (dev). Both environments run independently with their own databases.

## Dependencies

- Task 1 (folder structure)

## Estimated Effort

- 4-6 hours
