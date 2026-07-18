# Task 10: Polish — CLI, RBAC, Blue/Green Deployments

## Objective

Add developer experience polish and production-readiness features: a CLI tool for managing deployments from the terminal, basic authentication/authorization, and zero-downtime deployments via blue/green strategy.

## Prerequisites

- Task 9 complete (full system running on real hardware)
- All core features working end-to-end

## Implementation Steps

### 10.1 Create GreenCloud CLI

Location: `services/cli/`

```
services/cli/
├── greencloud/
│   ├── __init__.py
│   ├── cli.py               # Main CLI entry point (Click or Typer)
│   ├── commands/
│   │   ├── deploy.py        # Deployment commands
│   │   ├── dev.py           # Dev environment commands
│   │   ├── status.py        # Status and logs
│   │   ├── carbon.py        # Carbon metrics
│   │   └── config.py        # CLI configuration
│   ├── api_client.py        # HTTP client for GreenCloud API
│   └── output.py            # Rich terminal output formatting
├── tests/
│   ├── test_deploy.py
│   └── test_status.py
├── pyproject.toml
└── README.md
```

**Commands:**
```bash
# Deployment
greencloud deploy                    # Deploy current branch to its environment
greencloud deploy --env prod         # Deploy to prod explicitly
greencloud deploy --rollback         # Rollback to previous version
greencloud deployments               # List recent deployments
greencloud deployments <id> --logs   # Show build/deploy logs

# Dev environment
greencloud dev start                 # Start dev stack
greencloud dev stop                  # Stop dev stack
greencloud dev status                # Show dev stack status

# Status
greencloud status                    # Overview of all services
greencloud health                    # Health check all components
greencloud logs <service>            # Tail logs for a service

# Carbon
greencloud carbon                    # Current carbon intensity + status
greencloud carbon history            # Show emissions over time
greencloud carbon savings            # Show deferred builds and savings

# Configuration
greencloud config set api-url <url>  # Set API endpoint
greencloud config set api-key <key>  # Set authentication key
greencloud config show               # Show current config
```

**Implementation:**
- Use `typer` for CLI framework (modern, type-hints based)
- Use `rich` for terminal output (tables, progress bars, colors)
- Use `httpx` for API calls
- Config stored in `~/.greencloud/config.yml`
- Installable via `pip install -e .` or `pipx install .`

### 10.2 Implement RBAC (Role-Based Access Control)

**Authentication:**
- API key based (simple, no external auth provider needed)
- Keys stored hashed in GreenCloud API database
- Each key has: name, hashed value, created date, last used, permissions

**Roles:**
- `admin` — full access (manage deployments, configure system, view all)
- `deployer` — can trigger deployments and view status
- `viewer` — read-only access to status and metrics

**Implementation:**
- Add `Authorization: Bearer <api-key>` header to all API requests
- Middleware in GreenCloud API validates key and loads permissions
- CLI stores key in config file
- Webhook endpoint uses separate GitHub webhook secret (not API key)

**Endpoints to add:**
```
POST /auth/keys              # Create new API key (admin only)
GET  /auth/keys              # List keys (admin only)
DELETE /auth/keys/{id}       # Revoke key (admin only)
GET  /auth/me                # Current key info and permissions
```

### 10.3 Implement blue/green deployments

**Strategy:**
Instead of stopping old containers and starting new ones, run both versions simultaneously and switch traffic atomically.

**Implementation:**

1. **Deploy new version alongside old:**
   - New containers get a suffix: `prod-api-green` vs `prod-api-blue`
   - Both connected to the same network
   - New version gets a temporary Traefik route for smoke testing

2. **Health check new version:**
   - Run health checks against new containers
   - Optional: run smoke tests against temp route
   - If unhealthy → remove new containers, report failure

3. **Switch traffic:**
   - Update Traefik labels to point to new containers
   - Traefik picks up the change automatically (Docker provider watches labels)
   - Traffic now flows to new version

4. **Drain old version:**
   - Wait for in-flight requests to complete (configurable drain time)
   - Stop and remove old containers
   - Clean up old images

**Traefik label management:**
```python
# Using Docker SDK to update labels
import docker
client = docker.from_env()
container = client.containers.get("prod-api-green")
# Update labels to make it the active service
# Traefik auto-detects the change
```

**Rollback:**
- Keep old containers in "standby" for 5 minutes after switch
- If issues detected → switch labels back to old containers
- Instant rollback (no rebuild needed)

### 10.4 Scaling preparation

Document and partially implement support for multiple Pi nodes:

**Node registry:**
- Add `nodes` table to GreenCloud API database
- Endpoints: `GET /nodes`, `POST /nodes`, `DELETE /nodes/{id}`
- Each node has: hostname, IP, MAC address, status, capacity

**Load distribution:**
- Simple strategy: round-robin or least-loaded
- Each service instance can specify which node to run on
- Agent on each node reports capacity (CPU, memory available)

**Implementation (partial — full implementation is future work):**
- Node registration endpoint (agent registers itself on startup)
- Node health monitoring (GreenCloud API polls each agent)
- Deployment targeting (specify node or let system choose)
- Document: how to add a second Pi and join it to the cluster

### 10.5 Add CLI to CI/CD workflow

- Publish CLI as a Python package (internal or PyPI)
- Or: include CLI in the repo and install from path
- Add CLI commands to deployment scripts
- Document CLI usage in `docs/api/cli-reference.md`

### 10.6 Final documentation pass

Update all docs with learnings from implementation:
- `docs/architecture/final-architecture.md` — actual architecture as built
- `docs/runbooks/` — operational procedures refined from real experience
- `docs/api/openapi.json` — exported from FastAPI (auto-generated)
- `README.md` — final version with accurate quick-start guide
- `CONTRIBUTING.md` — how to develop on GreenCloud

## Test Requirements

- CLI commands work end-to-end (deploy, status, dev toggle, carbon check)
- API key auth: unauthenticated requests return 401
- API key auth: insufficient permissions return 403
- Blue/green: deploy new version → traffic switches → no downtime (verify with continuous curl)
- Blue/green: deploy broken version → health check fails → traffic stays on old version
- Rollback: `greencloud deploy --rollback` restores previous version

## Demo

Developer pushes code, watches it deploy via CLI (`greencloud status` shows progress), sees zero-downtime rollover in action (continuous requests never fail), and checks the carbon cost of the deployment — all from the terminal.

```bash
$ greencloud deploy --env prod
🚀 Deployment started (ID: abc123)
   Building images... ████████████ 100%
   Pushing to registry... done
   Deploying (blue/green)...
     ✓ New containers healthy
     ✓ Traffic switched
     ✓ Old containers drained
✅ Deployed successfully in 2m 34s
   Carbon cost: 0.8 gCO2eq

$ greencloud carbon
🌱 Grid Status: LOW (62 gCO2/kWh)
   Today's emissions: 12.4 gCO2
   Builds deferred: 0
   Carbon saved this week: 23.1 gCO2
```

## Dependencies

- Task 9 (full system on hardware)
- All previous tasks (features to polish)

## Estimated Effort

- 12-16 hours
