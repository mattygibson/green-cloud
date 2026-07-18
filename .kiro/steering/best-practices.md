# Best Practices

This steering file defines engineering best practices for the GreenCloud project. Follow these when writing code, configuring infrastructure, or making design decisions.

## General Engineering

- Write the simplest thing that works first, then iterate
- Every service must be independently startable and testable
- Prefer explicit over implicit — no magic configuration, no hidden dependencies
- If something is hard to understand, add a comment explaining *why*, not *what*
- Keep functions short and single-purpose; if a function needs a comment explaining what it does, it should probably be split

## Docker Best Practices

- Pin base image versions (e.g., `python:3.12-slim`, not `python:latest`)
- Order Dockerfile instructions from least to most frequently changing (maximise layer caching)
- Copy dependency files first, install, then copy source code
- Use `.dockerignore` to keep images small (exclude `.git`, `node_modules`, `__pycache__`, tests)
- Set explicit `EXPOSE` ports for documentation
- Use `HEALTHCHECK` in every Dockerfile — don't rely on container "running" as healthy
- Run as non-root: create a dedicated user in the Dockerfile
- Multi-stage builds: separate build dependencies from runtime
- Keep images under 200MB where possible

## Docker Compose Best Practices

- Use `depends_on` with `condition: service_healthy` — never rely on start order alone
- Define resource limits (`mem_limit`, `cpus`) for Pi deployment where memory is constrained
- Use named networks with explicit names (don't rely on auto-generated names)
- Always define a `restart: unless-stopped` policy for production services
- Group related services in the same Compose file, not one service per file
- Use variable substitution (`${VAR:-default}`) for anything environment-specific

## Python / FastAPI Best Practices

- Use async def for endpoints that do I/O (database, HTTP calls, file access)
- Use dependency injection (FastAPI `Depends()`) for shared resources (DB sessions, settings, auth)
- Validate all inputs with Pydantic models — never trust raw request data
- Return appropriate HTTP status codes (201 for creation, 202 for async tasks, 404 for not found)
- Use structured logging (JSON format) with correlation IDs for request tracing
- Handle exceptions with custom exception handlers — don't let stack traces reach the client
- Use Alembic for all database schema changes — never modify the DB by hand
- Keep business logic out of route handlers — put it in a service layer

## React / Frontend Best Practices

- Components should be small and composable
- Keep API calls in dedicated hook files (`useDeployments.ts`, `useCarbon.ts`)
- Handle loading, error, and empty states for every data-fetching component
- Use environment variables for API URLs — never hardcode backend addresses
- Build once, configure at runtime (inject config via env vars or `/config.json` served by nginx)
- Lazy-load routes/pages that aren't immediately visible

## Security Best Practices

- Never commit secrets (tokens, passwords, keys) — use environment variables
- Validate and sanitize all external input (webhooks, API parameters, user data)
- Use parameterised queries (SQLAlchemy handles this) — never construct SQL from strings
- Set minimum permissions: containers get only the capabilities they need
- Docker socket access is a root-equivalent privilege — limit it to services that strictly need it (agent, Traefik)
- Rotate API keys periodically; log when keys are created and last used
- Webhook secrets: use constant-time comparison (hmac.compare_digest) to prevent timing attacks

## Infrastructure Best Practices

- Infrastructure as Code: everything reproducible from the repo (no manual configuration)
- If you configure something manually (router, Cloudflare), document it in a runbook
- Keep secrets out of Compose files — reference them via `.env` files or Docker secrets
- Monitor everything you depend on: if it can break, it needs a health check and an alert
- Design for failure: what happens if the Mini PC doesn't wake? If the registry is down? If Cloudflare is unreachable?
- Backups: database volumes should be backed up regularly (document schedule and restore procedure)

## Testing Best Practices

- Write tests alongside code, not after — test-driven where practical
- Test behaviour, not implementation: test what the endpoint returns, not how the service internally works
- Use fixtures for shared setup (pytest fixtures, test databases)
- Mock external services at the HTTP boundary (use `httpx` mocking or `respx`)
- Integration tests should use real databases (PostgreSQL in Docker) not SQLite
- Name tests descriptively: `test_webhook_rejects_invalid_signature` not `test_webhook_3`
- Tests must be runnable in isolation — no test should depend on another test's state

## Observability Best Practices

- Every service exposes `/health` (for orchestration) and `/metrics` (for Prometheus)
- Use labels/tags on metrics to distinguish environments (prod vs dev)
- Log structured JSON with: timestamp, level, service name, request ID, message
- Don't log sensitive data (tokens, passwords, full request bodies with user data)
- Set retention limits on Prometheus and Loki — Pi storage is finite (30 days default)
- Dashboard before alert: understand what normal looks like before defining what's abnormal

## Carbon / Sustainability Best Practices

- Measure before optimising — get accurate baselines before making efficiency claims
- Document your methodology assumptions and their limitations
- Use average (not marginal) carbon intensity — compatible with reporting frameworks
- Cache API responses (grid intensity doesn't change every second)
- Separate critical path (prod deploys) from deferrable workloads (dev builds, cleanup tasks)
- Report honestly: include what's out of scope (GitHub, network, manufacturing emissions)

## Performance on Constrained Hardware (Pi 5)

- Pi has 8GB RAM — account for all services running concurrently
- Budget RAM: PostgreSQL (~256MB), FastAPI (~128MB per instance), React/nginx (~32MB), Traefik (~64MB), monitoring stack (~512MB), registry (~128MB)
- Leave at least 1GB free for system overhead and spikes
- Use Alpine images to reduce disk usage
- Consider enabling swap (2GB) as a safety net, not a crutch
- Build on Mini PC, not on Pi — Pi's CPU is fast enough to run containers but slow for compilation
- NVMe storage is fast — use it for Docker storage and database volumes (not the SD card)
