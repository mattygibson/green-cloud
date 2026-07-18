# Task 1: Project Scaffolding and Documentation

## Objective

Set up the repo structure, developer docs, and architecture decision records so everything built after this has a home. This is pure planning work — no hardware required.

## Implementation Steps

### 1.1 Create the project folder structure

```
green-cloud/
├── .github/
│   └── workflows/          # GitHub Actions (later)
├── .kiro/
│   ├── plans/              # This planning folder
│   └── steering/           # Project conventions
├── docs/
│   ├── architecture/       # System design docs
│   ├── adr/                # Architecture Decision Records
│   ├── api/                # API reference (OpenAPI specs)
│   ├── runbooks/           # Operational procedures
│   └── sustainability/     # Carbon methodology
├── services/
│   ├── greencloud-api/     # Main API (FastAPI) — deployment management
│   ├── agent/              # Node agent — runs on Pi
│   ├── carbon-engine/      # Carbon-aware scheduling service
│   └── app/                # The sample full-stack app
│       ├── api/            # FastAPI backend
│       ├── ui/             # React frontend
│       └── db/             # Database migrations/init scripts
├── infra/
│   ├── docker-compose.infra.yml    # Registry, Traefik, monitoring
│   ├── docker-compose.prod.yml     # Prod app stack
│   ├── docker-compose.dev.yml      # Dev app stack
│   ├── traefik/                    # Traefik config files
│   └── cloudflare/                 # Tunnel config
├── scripts/
│   ├── wake-on-lan.py      # WoL utility
│   └── setup-pi.sh         # Pi initial setup script
├── .gitignore
├── README.md
└── greencloud-project-blueprints.md  # Original blueprint (existing)
```

### 1.2 Write Architecture Decision Records

Create the following ADRs in `docs/adr/`:

**ADR-001-environment-isolation.md**
- Title: Use Docker Compose for environment isolation on single Pi
- Context: Need dev and prod on one machine, want simple toggle for dev
- Decision: Separate Docker Compose files with isolated networks and volumes
- Consequences: Simple to manage, no orchestrator overhead, limited to single-node scaling without additional tooling

**ADR-002-public-ingress.md**
- Title: Use Cloudflare Tunnel for public ingress
- Context: Need public access without exposing home network, no networking expertise
- Decision: Cloudflare Tunnel (cloudflared daemon) with outbound-only connections
- Consequences: Free HTTPS, no open ports, dependent on Cloudflare availability, custom domain required

**ADR-003-carbon-data-source.md**
- Title: Use Electricity Maps average intensity API for carbon awareness
- Context: Want to measure and minimise carbon emissions from the platform
- Decision: Electricity Maps API using average (not marginal) carbon intensity
- Consequences: Compatible with GHG Protocol Scope 2 reporting, requires API key, limited to zones covered by Electricity Maps

**ADR-004-build-strategy.md**
- Title: Cross-compile ARM64 images on Mini PC with Wake-on-LAN
- Context: Pi is too slow for Docker builds; need ARM64 images for deployment
- Decision: Mini PC builds via `docker buildx` with QEMU, wakes on demand, sleeps when idle
- Consequences: Saves energy vs always-on build server, adds latency for cold starts (~30s wake time)

### 1.3 Write the README.md

Contents:
- Project vision (from blueprint)
- Architecture diagram (mermaid)
- Hardware requirements (procurement table)
- Quick start guide (placeholder for now)
- Link to docs/ folder
- Status badges (placeholder)

### 1.4 Create hardware procurement checklist

File: `docs/runbooks/hardware-procurement.md`

Include:
- Item list with exact specs, links to purchase, and estimated costs
- Setup priority order (what to buy first)
- Compatibility notes (e.g., which NVMe HATs work with Pi 5)
- Optional items clearly marked

### 1.5 Create .gitignore

Cover:
- Python: `__pycache__/`, `*.pyc`, `.venv/`, `.env`
- Node: `node_modules/`, `dist/`, `.next/`
- Docker: `.docker/`
- IDE: `.vscode/`, `.idea/`
- OS: `.DS_Store`, `Thumbs.db`
- Secrets: `*.pem`, `*.key`, `.env.local`, `.env.*.local`

### 1.6 Initialise git and push to GitHub

- `git init` (already done based on .git folder existing)
- Create GitHub repo `green-cloud`
- Push initial structure
- Set up branch protection on `main` (optional at this stage)

## Test Requirements

- All markdown files render correctly in GitHub preview
- Folder structure is consistent with the plan
- ADRs follow a consistent template (Title, Status, Context, Decision, Consequences)
- No broken links between docs

## Demo

A well-structured repo on GitHub with complete documentation that someone could read to understand the entire project vision, architecture, and hardware needs — without any running code yet.

## Dependencies

- None (this is the starting task)

## Estimated Effort

- 2-3 hours
