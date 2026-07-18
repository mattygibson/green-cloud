# Task 4: CI/CD Pipeline — GitHub Webhook Receiver and Build Orchestration

## Objective

Build the GreenCloud API component that receives GitHub webhooks, triggers builds on the Mini PC (simulated locally for now), and pushes images to the local registry. This is the brain of the deployment pipeline.

## Prerequisites

- Task 3 complete (registry running)
- GitHub repo set up with webhook capability

## Implementation Steps

### 4.1 Create the GreenCloud API service

Location: `services/greencloud-api/`

FastAPI application structure:
```
services/greencloud-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via pydantic-settings
│   ├── models/
│   │   ├── deployment.py    # Deployment state models
│   │   └── webhook.py       # GitHub webhook payload models
│   ├── routers/
│   │   ├── webhooks.py      # POST /webhooks/github
│   │   ├── deployments.py   # Deployment management endpoints
│   │   └── health.py        # GET /health
│   ├── services/
│   │   ├── builder.py       # Build orchestration logic
│   │   ├── registry.py      # Registry interaction
│   │   └── wol.py           # Wake-on-LAN client
│   └── db/
│       ├── database.py      # SQLAlchemy setup
│       └── models.py        # DB models (deployment history)
├── tests/
│   ├── test_webhooks.py
│   ├── test_builder.py
│   └── conftest.py
├── Dockerfile
├── requirements.txt
└── alembic/
```

### 4.2 Implement webhook receiver

Endpoint: `POST /webhooks/github`

Logic:
1. Validate GitHub webhook signature (HMAC-SHA256 with secret)
2. Parse push event payload — extract branch, commit SHA, repo URL
3. Determine target environment:
   - `main` or `prod` branch → prod deployment
   - `dev` branch → dev deployment
   - Other branches → ignore
4. Create deployment record in DB (status: `pending`)
5. Trigger build pipeline (async task)
6. Return 202 Accepted with deployment ID

### 4.3 Implement build pipeline

Service: `app/services/builder.py`

Pipeline steps:
1. Wake build server (send Wake-on-LAN magic packet) — stub for now
2. Wait for build server to be reachable (health check poll)
3. Clone/pull the repository at the specified commit SHA
4. Run `docker buildx build --platform linux/arm64` for each service
5. Tag images: `<registry>/greencloud/<service>:<env>` and `<registry>/greencloud/<service>:<sha>`
6. Push to local registry
7. Update deployment record (status: `built`)
8. Notify agent to deploy (next task)

For local simulation:
- Skip WoL step
- Build directly on the local machine
- Use `linux/amd64` platform when running on Windows

### 4.4 Implement Wake-on-LAN client

Service: `app/services/wol.py`

- Send UDP magic packet (6 x 0xFF + 16 x target MAC address) to broadcast address
- Configurable MAC address and broadcast IP via settings
- Health check: attempt SSH or HTTP ping to build server
- Timeout: wait up to 60 seconds for wake

### 4.5 Implement deployment management endpoints

```
POST   /webhooks/github          # Receives GitHub push events
POST   /deployments/trigger      # Manual deployment trigger (for dev)
GET    /deployments              # List recent deployments
GET    /deployments/{id}         # Get specific deployment status
GET    /deployments/{id}/logs    # Get build logs
DELETE /deployments/{id}         # Cancel a pending deployment
```

### 4.6 Add deployment state machine

States:
```
pending → building → built → deploying → deployed → failed
                                                  ↗
pending → building → build_failed ──────────────/
```

Store in SQLite (lightweight, no extra service needed for the API itself).

### 4.7 Create Dockerfile for GreenCloud API

- Multi-stage build
- Python 3.12 slim base
- Install deps, copy app
- Run with uvicorn
- Health check endpoint

### 4.8 Add to infrastructure Compose

Add `greencloud-api` service to `infra/docker-compose.infra.yml`:
- Depends on registry
- Environment variables for GitHub webhook secret, registry host, build server MAC
- Persistent volume for SQLite database
- Exposed on port 8000 (behind Traefik later)

### 4.9 Set up GitHub webhook

Document the process:
1. Go to repo Settings → Webhooks → Add webhook
2. Payload URL: `https://greencloud-api.yourdomain.com/webhooks/github` (or ngrok for testing)
3. Content type: `application/json`
4. Secret: generate and store in `.env`
5. Events: Just the push event

For local testing: use `ngrok http 8000` to expose the API temporarily.

## Test Requirements

- Unit tests for webhook signature validation (valid and invalid)
- Unit tests for branch-to-environment mapping
- Integration test: send simulated webhook payload → verify deployment record created
- Integration test: trigger build → verify image appears in registry with correct tags
- Build logs are captured and retrievable via API

## Demo

Push to the `prod` branch on GitHub → webhook fires → GreenCloud API receives it → image builds → image appears in local registry with `prod` tag. The deployment status is trackable via `GET /deployments/{id}`.

## Dependencies

- Task 3 (local registry)

## Estimated Effort

- 8-10 hours
