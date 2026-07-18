# Task 6: Traefik + Cloudflare Tunnel Integration

## Objective

Configure Traefik as the reverse proxy with automatic service discovery, and wire Cloudflare Tunnel to expose prod (and optionally dev) to the internet — safely, with no open ports on your home network.

## Prerequisites

- Task 5 complete (all services running and healthy)
- A domain name (can be purchased cheaply, e.g., `.dev` or `.cloud`)
- Cloudflare account (free tier)

## Implementation Steps

### 6.1 Configure Traefik static configuration

Location: `infra/traefik/traefik.yml`

```yaml
api:
  dashboard: true
  insecure: false  # Dashboard behind auth in prod

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false  # Only route services with traefik.enable=true
    network: greencloud-infra
  file:
    directory: /etc/traefik/dynamic
    watch: true

log:
  level: INFO

metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addServicesLabels: true

entryPoints:
  metrics:
    address: ":8082"
```

### 6.2 Configure Traefik dynamic routing

Location: `infra/traefik/dynamic/`

**routing.yml:**
```yaml
http:
  routers:
    # Prod app
    prod-ui:
      rule: "Host(`app.yourdomain.com`)"
      service: prod-ui
      entryPoints:
        - web
    prod-api:
      rule: "Host(`app.yourdomain.com`) && PathPrefix(`/api`)"
      service: prod-api
      entryPoints:
        - web

    # Dev app (optional, can be disabled)
    dev-ui:
      rule: "Host(`dev.app.yourdomain.com`)"
      service: dev-ui
      entryPoints:
        - web
    dev-api:
      rule: "Host(`dev.app.yourdomain.com`) && PathPrefix(`/api`)"
      service: dev-api
      entryPoints:
        - web

    # Internal services
    grafana:
      rule: "Host(`grafana.yourdomain.com`)"
      service: grafana
      entryPoints:
        - web
      middlewares:
        - auth

  middlewares:
    auth:
      basicAuth:
        users:
          - "admin:$apr1$..." # htpasswd generated
```

Note: Most routing is handled via Docker labels on the containers (see Task 2). The file-based config above is for services that need extra middleware or custom rules.

### 6.3 Add Traefik to infrastructure Compose

In `infra/docker-compose.infra.yml`:
```yaml
traefik:
  image: traefik:v3.0
  container_name: greencloud-traefik
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
    - "8082:8082"  # Metrics
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
    - ./traefik/dynamic:/etc/traefik/dynamic:ro
  networks:
    - infra-net
    - greencloud-prod
    - greencloud-dev
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.dashboard.rule=Host(`traefik.yourdomain.com`)"
    - "traefik.http.routers.dashboard.service=api@internal"
    - "traefik.http.routers.dashboard.middlewares=auth"
```

### 6.4 Set up Cloudflare Tunnel

**Steps to configure in Cloudflare dashboard:**
1. Add your domain to Cloudflare (change nameservers)
2. Go to Zero Trust → Networks → Tunnels → Create Tunnel
3. Name: `greencloud`
4. Note the tunnel token

**Tunnel config on the Pi/local machine:**

Location: `infra/cloudflare/config.yml`
```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: app.yourdomain.com
    service: http://traefik:80
  - hostname: dev.app.yourdomain.com
    service: http://traefik:80
  - hostname: grafana.yourdomain.com
    service: http://traefik:80
  - hostname: traefik.yourdomain.com
    service: http://traefik:80
  - service: http_status:404  # Catch-all
```

### 6.5 Add cloudflared to infrastructure Compose

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  container_name: greencloud-tunnel
  restart: unless-stopped
  command: tunnel run
  environment:
    TUNNEL_TOKEN: ${CLOUDFLARE_TUNNEL_TOKEN}
  networks:
    - infra-net
  depends_on:
    - traefik
```

### 6.6 DNS configuration

In Cloudflare DNS dashboard, create CNAME records:
- `app.yourdomain.com` → `<TUNNEL_UUID>.cfargotunnel.com`
- `dev.app.yourdomain.com` → `<TUNNEL_UUID>.cfargotunnel.com`
- `grafana.yourdomain.com` → `<TUNNEL_UUID>.cfargotunnel.com`

(Cloudflare can auto-create these when you configure the tunnel via dashboard)

### 6.7 Security considerations

- Traefik dashboard: behind basic auth middleware
- Grafana: has its own auth (configured in Task 7)
- Dev environment: consider adding IP allowlist or basic auth
- Cloudflare Access (free tier): can add SSO/email-based auth for internal services
- Document: which services are public vs. internal-only

### 6.8 Local development setup

For development without Cloudflare:
- Use `*.localhost` domains (resolved by browsers automatically)
- Add entries to `/etc/hosts` (or Windows `hosts` file) if needed:
  ```
  127.0.0.1 app.localhost dev.app.localhost grafana.localhost
  ```
- Traefik works identically in local mode

### 6.9 Document the setup

Create `docs/runbooks/cloudflare-tunnel-setup.md`:
- Step-by-step Cloudflare account setup
- Tunnel creation walkthrough (with screenshots placeholders)
- DNS record configuration
- Troubleshooting: tunnel not connecting, 502 errors, DNS propagation

## Test Requirements

- All services accessible via their domain names through Traefik
- Cloudflare Tunnel connects and serves traffic from external network
- `app.yourdomain.com` loads the prod React app from an external device (phone, different network)
- Dev subdomain only accessible when dev stack is running
- Traefik dashboard accessible with auth
- Traefik metrics endpoint returns Prometheus-format data

## Demo

Your full-stack app is publicly accessible via a real domain with HTTPS, served from your local machine. No ports are open on your router. Visiting `app.yourdomain.com` from any device shows your application.

## Dependencies

- Task 5 (all services running)
- Domain name purchased
- Cloudflare account created

## Estimated Effort

- 4-6 hours (including Cloudflare setup)
