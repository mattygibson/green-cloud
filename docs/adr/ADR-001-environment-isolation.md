# ADR-001: Use Docker Compose for Environment Isolation on Single Pi

## Status

Accepted

## Context

GreenCloud runs dev and prod environments on a single Raspberry Pi 5. We need a way to isolate these environments so they don't interfere with each other, while keeping the solution simple enough for a single-node personal project.

Options considered:
- **Kubernetes (K3s)**: Full orchestration, but heavy overhead for a single Pi with 8GB RAM.
- **Docker Compose with separate files**: Lightweight, well-understood, easy to toggle environments on/off.
- **Podman pods**: Similar to Compose but less ecosystem support for tooling we're using (Traefik, etc.).

## Decision

Use separate Docker Compose files (`docker-compose.prod.yml` and `docker-compose.dev.yml`) with isolated Docker networks and volumes for each environment.

- Prod stack: `greencloud-prod` network, `prod-*` named volumes
- Dev stack: `greencloud-dev` network, `dev-*` named volumes
- Infrastructure (registry, Traefik, monitoring): `greencloud-infra` network, shared across environments

Dev environment is toggled manually via `docker compose up/down`.

## Consequences

**Positive:**
- Simple to understand and manage
- No orchestrator overhead (saves RAM on constrained Pi)
- Easy to start/stop dev without affecting prod
- Docker Compose is well-documented and widely supported

**Negative:**
- Limited to single-node without additional tooling
- No automatic failover or self-healing (manual intervention needed)
- Scaling to multiple Pis will require a different approach (agent-based, not Compose-native)

**Mitigations:**
- The GreenCloud Agent handles health checks and restarts, providing basic self-healing
- Architecture is designed so adding multi-node support later doesn't require rewriting existing services
