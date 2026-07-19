# Domain and Cloudflare Tunnel Setup

Step-by-step record of how green-cloud.uk was set up with Cloudflare Tunnel.

## What We Have

- Domain: `green-cloud.uk` (bought directly from Cloudflare)
- Cloudflare manages DNS automatically (no nameserver change needed)
- Tunnel name: `greencloud`
- All traffic flows: Internet → Cloudflare → Tunnel → Traefik → services

## Public URLs

| URL | Service |
|-----|--------|
| `https://green-cloud.uk` | Landing page (links to all services) |
| `https://app.green-cloud.uk` | Production app (React UI + FastAPI) |
| `https://grafana.green-cloud.uk` | Grafana dashboards |
| `https://carbon.green-cloud.uk` | Carbon Engine API |
| `https://api.green-cloud.uk` | GreenCloud management API |

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

### 4. Added public hostnames

In the tunnel config → Public Hostname tab, added entries one at a time:

| Subdomain | Domain | Service |
|-----------|--------|--------|
| *(empty)* | `green-cloud.uk` | `http://greencloud-traefik:80` |
| `app` | `green-cloud.uk` | `http://greencloud-traefik:80` |
| `grafana` | `green-cloud.uk` | `http://greencloud-traefik:80` |
| `carbon` | `green-cloud.uk` | `http://greencloud-traefik:80` |
| `api` | `green-cloud.uk` | `http://greencloud-traefik:80` |

All point to Traefik — it routes internally by hostname.

### 5. Updated `.env`

In `infra/.env`:
```
DOMAIN=green-cloud.uk
CLOUDFLARE_TUNNEL_TOKEN=ey...
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-password
```

### 6. Started everything with tunnel

```bash
docker compose -f infra/docker-compose.infra.yml down
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d
docker compose -f infra/docker-compose.prod.yml up -d
```

### 7. Verified

- `docker logs greencloud-tunnel` — check for "Connection registered"
- Cloudflare dashboard: tunnel shows HEALTHY
- Visited `https://app.green-cloud.uk` from phone

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

### DNS not resolving (new subdomain)

- Add the hostname in Cloudflare tunnel config (Public Hostname tab)
- Cloudflare creates the CNAME automatically
- Wait 1-2 minutes for propagation

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
