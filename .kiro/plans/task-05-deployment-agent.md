# Task 5: Deployment Agent and Stack Orchestration

## Objective

Build the node agent that pulls new images from the registry and restarts the appropriate Docker Compose stack (dev or prod). This is the component that runs on the Pi and manages the actual containers.

## Prerequisites

- Task 4 complete (GreenCloud API can build and push images)
- Registry contains images to deploy

## Implementation Steps

### 5.1 Create the agent service

Location: `services/agent/`

```
services/agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app (lightweight API)
│   ├── config.py            # Agent settings
│   ├── routers/
│   │   ├── deploy.py        # Deployment trigger endpoints
│   │   ├── health.py        # Agent health
│   │   └── stats.py         # System stats reporting
│   ├── services/
│   │   ├── deployer.py      # Docker Compose orchestration
│   │   ├── health_checker.py # Container health validation
│   │   ├── rollback.py      # Rollback logic
│   │   └── stats_collector.py # CPU/RAM/Power metrics
│   └── models/
│       └── deployment.py    # Deployment request/response models
├── tests/
│   ├── test_deployer.py
│   ├── test_health_checker.py
│   └── conftest.py
├── Dockerfile
└── requirements.txt
```

### 5.2 Implement deployment trigger endpoint

Endpoint: `POST /agent/deploy`

Request body:
```json
{
  "environment": "prod",
  "images": {
    "api": "localhost:5000/greencloud/api:prod",
    "ui": "localhost:5000/greencloud/ui:prod"
  },
  "deployment_id": "uuid",
  "rollback_to": "previous-tag"  // optional
}
```

Logic:
1. Pull new images from registry
2. Store current image digests (for rollback)
3. Run `docker compose -f <env-compose> pull`
4. Run `docker compose -f <env-compose> up -d`
5. Wait for health checks to pass (configurable timeout)
6. If healthy → report success to GreenCloud API
7. If unhealthy → trigger rollback

### 5.3 Implement health checking

Service: `app/services/health_checker.py`

- Poll each container's health status via Docker API
- Configurable checks:
  - Container is running
  - Health check passing (Docker HEALTHCHECK)
  - HTTP endpoint responding (for API and UI)
  - Database accepting connections (for PostgreSQL)
- Timeout: 60 seconds total, check every 5 seconds
- Return detailed status per container

### 5.4 Implement rollback

Service: `app/services/rollback.py`

- On health check failure:
  1. Log the failure reason
  2. Pull the previous image (stored before deployment)
  3. Run `docker compose up -d` with previous images
  4. Verify rollback health
  5. Report failure + rollback status to GreenCloud API
- Keep last 3 image tags for each service (rollback history)

### 5.5 Implement dev environment toggle

Endpoints:
```
POST /agent/dev/start   # Start dev Docker Compose stack
POST /agent/dev/stop    # Stop and remove dev containers (keep volumes)
GET  /agent/dev/status  # Is dev running?
```

Logic:
- Start: `docker compose -f docker-compose.dev.yml up -d`
- Stop: `docker compose -f docker-compose.dev.yml down` (preserves volumes)
- Status: check if containers exist and are running

### 5.6 Implement system stats collection

Service: `app/services/stats_collector.py`

Collect and expose:
- CPU usage (per container and system total)
- Memory usage (per container and system total)
- Disk usage (volumes, registry storage)
- Container count and status
- Uptime

Expose via:
- `GET /agent/stats` — JSON snapshot
- Prometheus metrics endpoint (`GET /agent/metrics`) for scraping

### 5.7 Create Dockerfile for agent

- Python 3.12 slim
- Mount Docker socket (`/var/run/docker.sock`) for container management
- Mount Compose files directory
- Run as non-root user (add to docker group)

### 5.8 Add agent to infrastructure Compose

In `infra/docker-compose.infra.yml`:
```yaml
agent:
  build: ../services/agent
  container_name: greencloud-agent
  restart: unless-stopped
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ../infra:/infra:ro  # Access to compose files
  environment:
    GREENCLOUD_API_URL: http://greencloud-api:8000
    REGISTRY_HOST: localhost:5000
    COMPOSE_PROJECT_DIR: /infra
  networks:
    - infra-net
  ports:
    - "8001:8000"
```

### 5.9 Wire GreenCloud API to Agent

Update `services/greencloud-api/app/services/builder.py`:
- After successful build + push → call agent's deploy endpoint
- Pass deployment ID, environment, and image references
- Poll agent for deployment status updates
- Update deployment record based on agent response

## Test Requirements

- Unit test: deployer correctly generates docker compose commands
- Unit test: health checker reports correct status for healthy/unhealthy containers
- Unit test: rollback triggers when health check fails
- Integration test: push new image to registry → trigger deploy → containers restart with new image
- Integration test: push broken image → deploy → health check fails → rollback succeeds
- Dev toggle: start/stop dev environment without affecting prod

## Demo

End-to-end: `git push` → GreenCloud API builds → pushes to registry → calls agent → agent pulls and restarts stack → health checks pass → deployment marked successful. Dev environment can be toggled on/off independently.

## Dependencies

- Task 4 (GreenCloud API triggers deployments)
- Task 3 (registry holds images)
- Task 2 (Compose stacks to manage)

## Estimated Effort

- 8-10 hours
