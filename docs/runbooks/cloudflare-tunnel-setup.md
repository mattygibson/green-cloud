# Cloudflare Tunnel Setup

This runbook walks you through exposing GreenCloud to the internet via Cloudflare Tunnel. The result: your app is publicly accessible at `app.yourdomain.com` with HTTPS, without opening any ports on your router.

## Prerequisites

- A domain name (any registrar works)
- A Cloudflare account (free tier is fine)
- GreenCloud running locally with `make infra-up && make prod-up`

## Step 1: Add your domain to Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **Add a site** and enter your domain
3. Select the **Free** plan
4. Cloudflare will show you two nameservers (e.g., `ada.ns.cloudflare.com`)
5. Go to your domain registrar and change the nameservers to Cloudflare's
6. Wait for DNS propagation (usually 5-30 minutes, can take up to 24h)
7. Cloudflare will confirm the domain is active

## Step 2: Create a Cloudflare Tunnel

1. In Cloudflare Dashboard, go to **Zero Trust** (left sidebar)
2. Navigate to **Networks > Tunnels**
3. Click **Create a tunnel**
4. Choose **Cloudflared** as the connector
5. Name the tunnel: `greencloud`
6. Click **Save tunnel**
7. On the "Install and run a connector" page, select **Docker**
8. Copy the **tunnel token** (long string starting with `ey...`)

## Step 3: Configure the tunnel token

Add the token to your local `.env` file:

```bash
# infra/.env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiYWJjMTIzLi4uIiwidCI6Ii4uLiIsInMiOiIuLi4ifQ==
```

Also set your domain:

```bash
DOMAIN=yourdomain.com
```

## Step 4: Configure public hostnames in Cloudflare

Back in the Cloudflare tunnel configuration page, add **two** public hostnames using the wildcard approach:

| Hostname | Service | Description |
|----------|---------|-------------|
| `*.green-cloud.uk` | `http://greencloud-traefik:80` | All app subdomains (wildcard) |
| `green-cloud.uk` | `http://greencloud-traefik:80` | Root domain (landing page) |

**Why wildcard?** All traffic goes to Traefik, which routes to the correct container based on the `Host` header (via Docker labels). This means:

- Deploying a new app requires **zero** changes to tunnel config
- Removing an app requires **zero** changes to tunnel config
- Any container with Traefik labels like `Host(\`my-app.green-cloud.uk\`)` is automatically publicly accessible

You never need to touch the Cloudflare dashboard again after this initial setup.

## Step 5: Start the tunnel

The tunnel uses a Docker Compose **profile** so it doesn't start by default:

```bash
# Start everything including the tunnel
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d

# Or start just the tunnel if infra is already running
docker compose -f infra/docker-compose.infra.yml --profile tunnel up -d cloudflared
```

## Step 6: Verify

1. Check the tunnel is connected:
   ```bash
   docker logs greencloud-tunnel
   # Should show: "Connection registered" and "Registered tunnel connection"
   ```

2. Check in Cloudflare Dashboard: **Zero Trust > Tunnels** should show status **HEALTHY**

3. Visit `https://app.yourdomain.com` from your phone or a different network

## Local Development (no tunnel)

For local development, the tunnel is not needed. Everything works with `*.localhost`:

- `http://app.localhost` — production app
- `http://grafana.localhost` — Grafana
- `http://traefik.localhost` — Traefik dashboard
- `http://carbon.localhost` — Carbon Engine
- `http://api.localhost` — GreenCloud API

Browsers resolve `*.localhost` automatically. No `/etc/hosts` changes needed.

## Troubleshooting

### Tunnel shows "Connection failed"

- Check the token is correct in `.env`
- Ensure Docker has internet access
- Check `docker logs greencloud-tunnel` for specific errors

### 502 Bad Gateway

- Traefik isn't running or isn't healthy: `docker ps | grep traefik`
- The target service isn't running: check the specific service logs
- Network issue: ensure cloudflared and traefik are on the same Docker network

### DNS not resolving

- Nameservers haven't propagated yet (wait 24h max)
- Check Cloudflare DNS tab — CNAME records should point to your tunnel
- Use `nslookup app.yourdomain.com` to debug

### Dev subdomain not working

- Dev stack might not be running: `make dev-up`
- Dev services need to be on a network Traefik can reach

## Security Notes

- **No ports open on your router** — all traffic flows through Cloudflare's network
- **HTTPS is handled by Cloudflare** — traffic between Cloudflare and your tunnel is encrypted
- **Cloudflare Access** (free) can add SSO/email-based auth for internal services like Grafana
- **Traefik dashboard** is exposed locally only by default. If exposed via tunnel, protect with Cloudflare Access
- **Grafana** has its own authentication (admin/password)

## Architecture

```
[Internet] --> [Cloudflare Edge (HTTPS)] --> [Tunnel] --> [cloudflared container]
    --> [Traefik :80] --> routes by hostname (via Docker labels):
        *.green-cloud.uk --> matched by container labels:
          app.green-cloud.uk         --> prod-ui / prod-api
          meal-planner.green-cloud.uk --> meal-planner-ui / meal-planner-api
          grafana.green-cloud.uk     --> grafana
          carbon.green-cloud.uk      --> carbon-engine
          api.green-cloud.uk         --> greencloud-api
          <new-app>.green-cloud.uk   --> automatically routed (no config change)
```

## How New Apps Get Routed Automatically

1. You deploy a container with Traefik labels: `Host(\`my-app.green-cloud.uk\`)`
2. Traefik auto-discovers the container via Docker socket
3. Cloudflare tunnel wildcard (`*.green-cloud.uk`) already forwards all subdomains
4. Traffic flows: Internet → Cloudflare → Tunnel → Traefik → your container
5. **No manual steps required**
