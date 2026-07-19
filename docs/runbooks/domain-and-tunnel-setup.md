# Domain and Cloudflare Tunnel Setup

Step-by-step record of how green-cloud.uk was set up with Cloudflare Tunnel.

## What We Have

- Domain: `green-cloud.uk` (bought directly from Cloudflare)
- Cloudflare manages DNS automatically (no nameserver change needed)
- Tunnel name: `greencloud`
- **Wildcard routing:** `*.green-cloud.uk` routes all subdomains through the tunnel
- All traffic flows: Internet → Cloudflare → Tunnel → Traefik → services

## Public URLs

| URL | Service |
|-----|--------|
| `https://green-cloud.uk` | Landing page (links to all services) |
| `https://app.green-cloud.uk` | Production dashboard (React UI + FastAPI + app discovery) |
| `https://meal-planner.green-cloud.uk` | Meal Planner (third-party app — PaaS proof) |
| `https://grafana.green-cloud.uk` | Grafana dashboards |
| `https://carbon.green-cloud.uk` | Carbon Engine API |
| `https://api.green-cloud.uk` | GreenCloud management API |
| `https://<any-app>.green-cloud.uk` | Any deployed user app (wildcard routing) |

## Setup Steps (what we did)

### 1. Bought the domain

- Went to Cloudflare Dashboard → Registrar → Register Domain
- Bought `green-cloud.uk`
- DNS is automatically managed by Cloudflare (no external registrar steps needed)

### 2. Created the tunnel

1. Cloudflare Dashboard → Zero Trust → Networks → Tunnels
2. "Create a tunnel" → Cloudflared connector
3. Named it: `greencloud`
4. Saved the tunnel

### 3. Got the tunnel token

1. In the tunnel config, selected Docker as environment
2. Copied the token from the command shown (the `ey...` string after `--token`)
3. Added it to `infra/.env`:
   ```
   CLOUDFLARE_TUNNEL_TOKEN=ey...the-actual-token...
   ```

### 4. Configured wildcard routing

Instead of adding individual public hostnames per subdomain, we use a single **wildcard route** that forwards all subdomains to Traefik. Traefik then routes internally based on the Host header.

In the tunnel config → Public Hostname tab:

| Subdomain | Domain | Service |
|-----------|--------|--------|
| `*` | `green-cloud.uk` | `http://greencloud-traefik:80` |
| *(empty)* | `green-cloud.uk` | `http://greencloud-traefik:80` |

The wildcard entry (`*`) catches all subdomains (`app.`, `grafana.`, `meal-planner.`, `anything.`) and sends them to Traefik. The empty subdomain entry handles the apex domain (`green-cloud.uk` itself).

**Why wildcard:** New apps deployed to GreenCloud become publicly accessible immediately — no need to add a new public hostname in Cloudflare for each app. Just add a Traefik Host rule label to the container and it works.

### 5. Added wildcard DNS CNAME record

In Cloudflare DNS settings, add a wildcard CNAME:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| CNAME | `*` | `<tunnel-id>.cfargotunnel.com` | Proxied |
| CNAME | `@` | `<tunnel-id>.cfargotunnel.com` | Proxied |

Cloudflare creates CNAME records automatically for individually configured hostnames, but for wildcard routing you need the wildcard CNAME record (`*`) to exist so DNS resolution works for arbitrary subdomains.

### 6. Updated `.env`

In `infra/.env`:
```
DOMAIN=green-cloud.uk
CLOUDFLARE_TUNNEL_TOKEN=ey...
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-password
```

### 7. Started everything with tunnel

```bash
docker compose -f infra/docker-compose.infra.yml down
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d
docker compose -f infra/docker-compose.prod.yml up -d
```

### 8. Verified

- `docker logs greencloud-tunnel` — check for "Connection registered"
- Cloudflare dashboard: tunnel shows HEALTHY
- Visited `https://app.green-cloud.uk` from phone
- Visited `https://meal-planner.green-cloud.uk` from phone — confirms wildcard working

## Adding a New App (no Cloudflare changes needed)

With wildcard routing, deploying a new app is straightforward:

1. Build and push the image to the local registry
2. Add the service to a Compose file with Traefik labels:
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.my-app.rule=Host(`my-app.green-cloud.uk`)"
   ```
3. Ensure the service is on the `greencloud-prod` network
4. Start the container — it's publicly accessible at `https://my-app.green-cloud.uk`

No DNS changes, no Cloudflare tunnel hostname additions required.

## How to Restart After Reboot

```bash
cd C:\Users\M\Dev\Apps\green-cloud
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d
docker compose -f infra/docker-compose.prod.yml up -d
```

## How to Stop

```bash
docker compose -f infra/docker-compose.prod.yml down
docker compose -f infra/docker-compose.infra.yml --profile tunnel down
```

## Troubleshooting

### Grafana password not working

The password is set on first startup and stored in the Grafana volume. If you change it in `.env` it won't take effect until you reset the volume:

```bash
docker compose -f infra/docker-compose.infra.yml down
docker volume rm infra_grafana-data
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d
```

### Tunnel not connecting

- Check token is correct: `docker logs greencloud-tunnel`
- Ensure Docker has internet access
- Check Cloudflare dashboard for tunnel status

### 502 Bad Gateway on a subdomain

- The target service isn't running
- Check: `docker ps` to see what's up
- Restart the specific service: `docker compose -f infra/docker-compose.infra.yml up -d <service>`

### New subdomain not resolving

With wildcard routing, you should NOT need to add individual hostnames. If a new subdomain doesn't resolve:
1. Verify the wildcard CNAME record (`*`) exists in Cloudflare DNS
2. Verify the wildcard public hostname (`*`) exists in the tunnel config
3. Check that Traefik has a matching router (inspect Traefik dashboard at `http://localhost:8080`)
4. Ensure the container has the correct `traefik.http.routers.<name>.rule=Host(...)` label
5. Ensure the container is on the `greencloud-prod` network

### App accessible locally but not publicly

- Confirm the tunnel is running: `docker ps | grep tunnel`
- Check tunnel logs: `docker logs greencloud-tunnel`
- Verify the Cloudflare dashboard shows the tunnel as HEALTHY
- Confirm Traefik can reach the service (check Traefik dashboard for errors)

## Local Development (no tunnel)

When developing locally, you don't need the tunnel. Everything works with `*.localhost`:

```bash
# Start without tunnel profile
docker compose -f infra/docker-compose.infra.yml up -d
docker compose -f infra/docker-compose.prod.yml up -d
```

Access via:
- `http://app.localhost`
- `http://grafana.localhost`
- `http://carbon.localhost`
- `http://traefik.localhost`
