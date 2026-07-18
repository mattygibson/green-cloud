# GreenCloud Test Plan

## Overview

This test plan covers the current state of GreenCloud (Tasks 1-5). It validates all services, endpoints, and integration points work correctly.

## Prerequisites

- Docker Desktop installed and running
- `uv` installed (for lockfile generation)
- Repository cloned locally
- No other services using ports: 80, 5000, 8000, 8001, 8080

## 1. Infrastructure Stack

### 1.1 Docker Registry

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 1 | Registry starts | `docker compose -f infra/docker-compose.infra.yml up -d` | Container `greencloud-registry` running |
| 2 | Registry healthy | `docker ps` | Status shows `(healthy)` |
| 3 | Registry responds | `curl http://localhost:5000/v2/` | Returns `{}` |
| 4 | Push image | `docker tag infra-prod-api:latest localhost:5000/greencloud/api:test && docker push localhost:5000/greencloud/api:test` | Push succeeds |
| 5 | List repositories | `curl http://localhost:5000/v2/_catalog` | Returns `{"repositories":["greencloud/api"]}` |
| 6 | List tags | `curl http://localhost:5000/v2/greencloud/api/tags/list` | Returns JSON with `"test"` tag |
| 7 | Data persists | Restart registry container, repeat test 5 | Same result |

### 1.2 GreenCloud API

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 8 | API starts | `docker compose -f infra/docker-compose.infra.yml up -d` | Container `greencloud-api` running |
| 9 | API healthy | `docker ps` | Status shows `(healthy)` |
| 10 | Health endpoint | `curl http://localhost:8000/health` | `{"status":"healthy","service":"greencloud-api","dependencies":{"registry":"connected"}}` |
| 11 | Swagger docs | Open `http://localhost:8000/docs` | Swagger UI loads |
| 12 | List deployments (empty) | `curl http://localhost:8000/deployments` | Returns `[]` |
| 13 | Manual trigger | `curl -X POST http://localhost:8000/deployments/trigger -H "Content-Type: application/json" -d '{"environment":"dev","branch":"dev","commit_sha":"abc1234"}'` | Returns 202 with deployment object |
| 14 | Get deployment | `curl http://localhost:8000/deployments/1` | Returns deployment with status |
| 15 | Get logs | `curl http://localhost:8000/deployments/1/logs` | Returns logs object |
| 16 | Webhook rejects no signature | `curl -X POST http://localhost:8000/webhooks/github -H "Content-Type: application/json" -d '{}'` | Returns 401 |

### 1.3 GreenCloud Agent

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 17 | Agent starts | `docker compose -f infra/docker-compose.infra.yml up -d` | Container `greencloud-agent` running |
| 18 | Agent healthy | `docker ps` | Status shows `(healthy)` |
| 19 | Health endpoint | `curl http://localhost:8001/health` | `{"status":"healthy","service":"greencloud-agent"}` |
| 20 | Swagger docs | Open `http://localhost:8001/docs` | Swagger UI loads |
| 21 | System stats | `curl http://localhost:8001/agent/stats` | Returns JSON with cpu/memory/disk/containers |
| 22 | Dev status | `curl http://localhost:8001/agent/dev/status` | Returns `{"status":"stopped"}` or `{"status":"running"}` |

## 2. Production App Stack

### 2.1 Full Stack Startup

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 23 | Prod stack starts | `docker compose -f infra/docker-compose.prod.yml up -d --build` | All containers start |
| 24 | Database healthy | `docker ps` (check `prod-db`) | Status shows `(healthy)` |
| 25 | API healthy | `docker ps` (check `prod-api`) | Status shows `(healthy)` |
| 26 | UI healthy | `docker ps` (check `prod-ui`) | Status shows `(healthy)` |
| 27 | Traefik running | `docker ps` (check `greencloud-traefik`) | Status shows `Up` |

### 2.2 Traefik Routing

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 28 | UI accessible | Open `http://app.localhost` | GreenCloud React UI loads |
| 29 | Health via Traefik | `curl http://app.localhost/health` | Returns `{"status":"healthy","database":"connected","environment":"production"}` |
| 30 | API items endpoint | `curl http://app.localhost/api/v1/items` | Returns JSON array (may have seed item) |
| 31 | Create item | `curl -X POST http://app.localhost/api/v1/items -H "Content-Type: application/json" -d '{"name":"Test","description":"A test item"}'` | Returns 201 with created item |
| 32 | Get item | `curl http://app.localhost/api/v1/items/1` | Returns the item |
| 33 | Delete item | `curl -X DELETE http://app.localhost/api/v1/items/1` | Returns 204 |
| 34 | Traefik dashboard | Open `http://localhost:8080` | Traefik dashboard loads |
| 35 | Routers registered | `curl http://localhost:8080/api/http/routers` | Shows prod-api, prod-health, prod-ui routers |

### 2.3 Database

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 36 | Seed data loaded | `curl http://app.localhost/api/v1/items` | Contains "GreenCloud" seed item |
| 37 | Data persists | Restart prod stack, check items again | Same items present |
| 38 | CRUD works | Create, read, delete an item via API | All operations succeed |

## 3. Dev Stack (Isolation)

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 39 | Dev starts separately | `docker compose -f infra/docker-compose.dev.yml up -d --build` | Dev containers start alongside prod |
| 40 | Dev API on different port | `curl http://localhost:8001/health` (if port 8001 configured) | Dev API responds |
| 41 | Dev DB isolated | Create item in dev, verify it doesn't appear in prod | Separate databases |
| 42 | Dev stop | `docker compose -f infra/docker-compose.dev.yml down` | Dev stops, prod unaffected |
| 43 | Prod still running | `curl http://app.localhost/health` after dev stop | Still returns healthy |

## 4. Integration Tests

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 44 | Registry ↔ API | GreenCloud API health check reports registry connected | `"registry": "connected"` |
| 45 | Full rebuild | `make clean && make infra-up && make prod-up` | Everything comes up clean |
| 46 | Makefile commands | Run `make prod-up`, `make prod-down`, `make dev-up`, `make dev-down` | All work correctly |

## 5. Edge Cases

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 47 | Port conflict | Start stack with port 80 already in use | Clear error message |
| 48 | Registry down | Stop registry, check API health | Reports `"registry": "disconnected"` |
| 49 | Invalid item | `POST /api/v1/items` with empty body | Returns 422 validation error |
| 50 | Non-existent item | `GET /api/v1/items/9999` | Returns 404 |

## Running the Full Test Suite

```bash
# 1. Clean slate
make clean

# 2. Start infrastructure
make infra-up

# 3. Wait for healthy (30 seconds)
sleep 30

# 4. Start prod
make prod-up

# 5. Wait for healthy (30 seconds)
sleep 30

# 6. Run through tests 1-50 above

# 7. Cleanup
make clean
```

## Status

- [ ] All tests passing
- [ ] Documented any failures and fixes
