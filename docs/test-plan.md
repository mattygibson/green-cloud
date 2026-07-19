# GreenCloud Test Plan

## Overview

This test plan covers the current state of GreenCloud (Tasks 1-5). It validates all services, endpoints, and integration points work correctly.

**All testing uses the dev environment. Prod is only for the finished product.**

## Prerequisites

- Docker Desktop installed and running
- `uv` installed (for lockfile generation)
- Repository cloned locally
- No other services using ports: 5000, 5433, 8000, 8001, 3001, 9090

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

## 2. Dev App Stack (use for all testing)

### 2.1 Full Stack Startup

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 23 | Dev stack starts | `docker compose -f infra/docker-compose.dev.yml up -d --build` | All containers start |
| 24 | Database healthy | `docker ps` (check `dev-db`) | Status shows `(healthy)` |
| 25 | API healthy | `docker ps` (check `dev-api`) | Status shows `(healthy)` |
| 26 | UI healthy | `docker ps` (check `dev-ui`) | Status shows `(healthy)` |

### 2.2 Dev Endpoints

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 27 | UI accessible | Open `http://localhost:3001` | GreenCloud React UI loads |
| 28 | API items endpoint | `curl http://localhost:8001/api/v1/items` | Returns JSON array (may have seed item) |
| 29 | Create item | `curl -X POST http://localhost:8001/api/v1/items -H "Content-Type: application/json" -d '{"name":"Test","description":"A test item"}'` | Returns 201 with created item |
| 30 | Get item | `curl http://localhost:8001/api/v1/items/1` | Returns the item |
| 31 | Delete item | `curl -X DELETE http://localhost:8001/api/v1/items/1` | Returns 204 |

### 2.3 Database (pgAdmin access)

| # | Test | Command | Expected Result |
|---|------|---------|-----------------|
| 32 | pgAdmin connects | Connect to localhost:5433, user: greencloud, pass: changeme_dev | Connection succeeds |
| 33 | Seed data loaded | Check items table | Contains "GreenCloud" seed item |
| 34 | Data persists | Restart dev stack, check items again | Same items present |
| 35 | CRUD works | Create, read, delete an item via API | All operations succeed |

## 3. Environment Isolation

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 36 | Dev and prod isolated | Start both, create item in dev | Item does NOT appear in prod |
| 37 | Dev stop doesn't affect prod | `docker compose -f infra/docker-compose.dev.yml down` | Prod (if running) still works |
| 38 | Prod stop doesn't affect dev | `docker compose -f infra/docker-compose.prod.yml down` | Dev still works |

## 4. Deployment Pipeline

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 39 | Trigger dev deployment | `curl -X POST http://localhost:8000/deployments/trigger -H "Content-Type: application/json" -d '{"environment":"dev","branch":"dev","commit_sha":"test123"}'` | Returns 202 |
| 40 | Build completes | Wait 60s, check `curl http://localhost:8000/deployments/1/logs` | Status: `built` |
| 41 | Images in registry | `curl http://localhost:5000/v2/_catalog` | Shows `greencloud/api` and `greencloud/ui` |
| 42 | Sanity check image | Build + push + run test image at localhost:9090 | Shows "Hello World, Images are working!" |

## 5. Integration Tests

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 43 | Registry ↔ API | GreenCloud API health check reports registry connected | `"registry": "connected"` |
| 44 | Full rebuild | `make clean && make infra-up && make dev-up` | Everything comes up clean |
| 45 | Makefile commands | Run `make dev-up`, `make dev-down` | All work correctly |

## 6. Edge Cases

| # | Test | Steps | Expected Result |
|---|------|-------|-----------------|
| 46 | Port conflict | Start stack with port already in use | Clear error message |
| 47 | Registry down | Stop registry, check API health | Reports `"registry": "disconnected"` |
| 48 | Invalid item | `POST /api/v1/items` with empty body | Returns 422 validation error |
| 49 | Non-existent item | `GET /api/v1/items/9999` | Returns 404 |
| 50 | Webhook rejects no signature | `POST /webhooks/github` with no signature | Returns 401 |

## Running the Full Test Suite

```bash
# 1. Clean slate
make clean

# 2. Start infrastructure
make infra-up

# 3. Wait for healthy (30 seconds)
sleep 30

# 4. Start dev (use dev for all testing)
make dev-up

# 5. Wait for healthy (30 seconds)
sleep 30

# 6. Run through tests 1-50 above

# 7. Cleanup
make clean
```

## Status

- [ ] All tests passing
- [ ] Documented any failures and fixes
