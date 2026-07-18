# GreenCloud - Project Blueprint

## Vision

Build a carbon-aware self-hosted Platform-as-a-Service (PaaS) using Raspberry Pi compute nodes and an on-demand Mini PC build server. The platform should provide an AWS-like deployment experience while minimizing energy usage.

## Architecture

```
Git → CI → Wake Mini PC → Build Docker Image → Local Registry → Raspberry Pi pulls image → Traefik → Website
```

## Hardware

- Raspberry Pi 5 (8GB), NVMe HAT and 500GB SSD
- Official Raspberry Pi PSU
- Mini PC (Lenovo Tiny / Dell OptiPlex Micro / HP EliteDesk Mini, i5 8th Gen+, 16GB RAM)
- 8-port Gigabit switch
- Ethernet cables
- Optional: smart plug and USB power meter

## Software Components

### GreenCloud API
- FastAPI
- Deployment management
- Node management
- Authentication
- Health checks

### Node Agent
- Runs on Pi
- Pull images
- Start/stop containers
- Report CPU/RAM/Power

### Control Plane
- CI/CD
- Docker builds
- Container registry
- Wake-on-LAN

### Observability
- Prometheus
- Grafana
- Loki
- Energy dashboard

### Carbon Engine
- Carbon-aware scheduling
- Grid intensity integration
- Power reporting

## Roadmap

1. **Infrastructure:** Install OS, Docker, SSH, networking.
2. **First Deployment:** Deploy FastAPI + PostgreSQL behind Traefik.
3. **GreenCloud API:** Create deployment API and node registry.
4. **Deployment Agent:** Manage containers and health checks.
5. **CI/CD:** Automated builds and deployments.
6. **Sustainability:** Energy metrics and carbon-aware deployments.
7. **Polish:** CLI, UI, RBAC, blue/green deployments, scaling.

## Future AWS-style Services

| AWS | GreenCloud |
|-----|------------|
| EC2 | Pi Nodes |
| ECS | Deployment Engine |
| RDS | Managed PostgreSQL |
| CloudWatch | Grafana/Prometheus |
| IAM | User Manager |
| ECR | Local Registry |

## Documentation Structure

```
/docs/architecture
/docs/adr
/docs/api
/docs/runbooks
/docs/sustainability
```
