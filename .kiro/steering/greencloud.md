# GreenCloud - Project Conventions

## Overview

GreenCloud is a carbon-aware self-hosted PaaS running on a Raspberry Pi 5 with a Mini PC build server. This document defines the conventions and standards for all code and configuration in this project.

## Language and Frameworks

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend services | Python + FastAPI | Python 3.12+, FastAPI 0.100+ |
| Frontend | React + TypeScript + Vite | React 18+, Node 20+ |
| Database | PostgreSQL | 16+ |
| Containers | Docker + Docker Compose | Compose v2 |
| Reverse proxy | Traefik | v3.0 |
| Monitoring | Prometheus + Grafana + Loki | Latest |
| CLI | Python + Typer + Rich | Python 3.12+ |

## Project Structure

```
green-cloud/
├── .kiro/              # Kiro plans and steering
├── docs/               # All documentation
├── services/           # All application code
│   ├── greencloud-api/ # Deployment management API
│   ├── agent/          # Node agent (runs on Pi)
│   ├── carbon-engine/  # Carbon-aware scheduling
│   └── app/            # The deployed full-stack app
│       ├── api/        # FastAPI backend
│       ├── ui/         # React frontend
│       └── db/         # Migrations and init scripts
├── infra/              # Docker Compose files, Traefik, Cloudflare config
└── scripts/            # Utility scripts
```

## Code Conventions

### Python (FastAPI services)

- Use `pyproject.toml` for dependency management
- Type hints on all function signatures
- Pydantic models for all request/response schemas
- Async endpoints where I/O is involved
- Settings via `pydantic-settings` (environment variables)
- Tests with `pytest` and `pytest-asyncio`
- Code formatting: `ruff format`
- Linting: `ruff check`
- Import sorting: handled by ruff

### TypeScript/React (Frontend)

- Vite as build tool
- Functional components with hooks
- TypeScript strict mode enabled
- ESLint + Prettier for formatting
- Component naming: PascalCase
- File naming: kebab-case for files, PascalCase for components

### Docker

- Multi-stage builds for all services
- Target both `linux/amd64` and `linux/arm64`
- Use Alpine base images where possible
- Non-root user in production containers
- HEALTHCHECK defined in every Dockerfile
- `.dockerignore` in every service directory

### Docker Compose

- Separate files per concern: `docker-compose.infra.yml`, `docker-compose.prod.yml`, `docker-compose.dev.yml`
- Environment variables via `.env` files (never committed — use `.env.example`)
- Named volumes for persistence
- Named networks for isolation
- Health checks with `depends_on: condition: service_healthy`

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Docker images | `<registry>/greencloud/<service>:<tag>` | `localhost:5000/greencloud/api:prod` |
| Container names | `greencloud-<service>` or `<env>-<service>` | `greencloud-api`, `prod-db` |
| Networks | `greencloud-<purpose>` | `greencloud-prod`, `greencloud-infra` |
| Volumes | `<env>-<service>-data` | `prod-db-data` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `CARBON_ZONE` |
| API endpoints | lowercase, hyphens, plural nouns | `/api/v1/deployments`, `/carbon/emissions` |
| Python packages | lowercase, underscores | `greencloud_api`, `carbon_engine` |
| Branch names | `<type>/<short-description>` | `feature/carbon-scheduler`, `fix/webhook-validation` |

## Git Workflow

- `main` / `prod` branch: triggers production deployment
- `dev` branch: triggers dev deployment (when dev stack is running)
- Feature branches: `feature/<name>`, merged via PR to `dev` or `main`
- Commit messages: conventional commits format
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation
  - `infra:` infrastructure changes
  - `refactor:` code refactoring
  - `test:` adding tests

## Environment Configuration

- All configuration via environment variables
- Never hardcode secrets, IPs, or domain names
- Use `.env.example` as template (committed)
- Use `.env.prod` and `.env.dev` for actual values (gitignored)
- Required variables documented in each service's README

## API Design

- RESTful endpoints
- JSON request/response bodies
- Consistent error format:
  ```json
  {"detail": "Human-readable message", "code": "MACHINE_CODE"}
  ```
- Versioned API paths: `/api/v1/...`
- Health check at `/health` for every service
- Metrics at `/metrics` (Prometheus format) for every service
- OpenAPI docs auto-generated at `/docs`

## Testing

- Unit tests for business logic (no external dependencies)
- Integration tests for API endpoints (use test database)
- Mock external services (Electricity Maps, Docker API) in tests
- Minimum coverage target: 80% for core services
- Tests run before deployment (CI pipeline)

## Documentation

- ADRs for architectural decisions (numbered, never deleted)
- Runbooks for operational procedures
- API docs auto-generated from code (FastAPI OpenAPI)
- Sustainability methodology documented separately
- Keep docs updated as implementation evolves

## Security

- API key authentication for all management endpoints
- GitHub webhook signature validation (HMAC-SHA256)
- No ports opened on home network (Cloudflare Tunnel only)
- Docker socket access limited to agent and Traefik
- Secrets never logged or exposed in API responses
- HTTPS terminated at Cloudflare edge

## Carbon Awareness

- Use average (not marginal) carbon intensity
- Data source: Electricity Maps API
- Scope: Pi and Mini PC energy consumption only
- GitHub hosting energy is out of scope
- Network transit energy is out of scope
- Document all methodology assumptions in `/docs/sustainability/`
