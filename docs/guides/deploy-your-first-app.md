# Deploy Your First App on GreenCloud

This guide walks you through deploying your own app on GreenCloud — from zero to a live URL. No cloud account needed, no subscription, no credit card.

**What you'll end up with:** Your app running at `https://<your-app>.green-cloud.uk`, with automatic HTTPS, health monitoring, and resource limits.

**Time required:** ~15 minutes (assuming your app already works locally).

---

## Prerequisites

Before you start, make sure you have:

- [ ] Your app code in a GitHub repository
- [ ] An API key from the GreenCloud admin (ask Matt)
- [ ] Docker installed locally (for testing your Dockerfile)
- [ ] Basic familiarity with the terminal

Your app can be any web application — a Python API, a React frontend, a Node.js server, a static site — as long as it can run in a Docker container and listen on a port.

---

## Step 1: Add a Health Check Endpoint

GreenCloud monitors your app's health. Your backend needs a `/health` endpoint that returns HTTP 200 when everything is working.

**FastAPI example:**

```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "my-app-api"}
```

**Express.js example:**

```javascript
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'my-app-api' });
});
```

**Why:** GreenCloud uses this to know if your app is running correctly. If the health check fails, the platform can restart your container automatically.

---

## Step 2: Create a Dockerfile

Your app needs a `Dockerfile` so GreenCloud can build and run it as a container. We provide templates for common stacks (see `/templates/` in the green-cloud repo), or you can write your own.

### Key requirements for your Dockerfile:

1. **Multi-stage build** — keep the final image small
2. **Non-root user** — security best practice
3. **HEALTHCHECK instruction** — so Docker knows when the app is ready
4. **EXPOSE the port** — document which port your app listens on

### Example: Python FastAPI Backend

```dockerfile
# Stage 1: Install dependencies
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /build
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Example: React + Vite Frontend

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV VITE_API_URL=__VITE_API_URL_PLACEHOLDER__
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine AS runtime
COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
```

> **Frontend API URL:** Notice the `__VITE_API_URL_PLACEHOLDER__` — this gets replaced at container startup with the real API URL. This means you build once and configure at runtime.

---

## Step 3: Add a `.dockerignore`

Keep your Docker image clean and small by excluding files that shouldn't be in the container:

```
# Dependencies (rebuilt in Docker)
node_modules/
venv/
__pycache__/

# Build output (rebuilt in Docker)
dist/

# Environment files (injected at runtime)
.env
.env.*

# Git and IDE
.git
.gitignore
.vscode/
.idea/
```

---

## Step 4: Create `greencloud.yml`

Add a `greencloud.yml` file to the root of your repository. This tells GreenCloud how to deploy your app:

```yaml
# GreenCloud App Configuration
name: my-app
description: A short description of what your app does

services:
  api:
    context: ./backend        # Path to the Dockerfile directory
    port: 8000                # Port your app listens on
    health_check: /health     # Health check endpoint path
    environment:
      - PYTHONUNBUFFERED=1    # Any env vars your app needs
    resources:
      memory: 128MB           # Max memory (128MB-512MB)
      cpu: 0.25               # CPU cores (0.1-1.0)

  ui:
    context: ./frontend
    port: 80
    health_check: /
    environment:
      - VITE_API_URL=/api
    resources:
      memory: 64MB
      cpu: 0.1

routing:
  subdomain: my-app           # Your app will be at: https://my-app.green-cloud.uk
  rules:
    - path_prefix: /api       # Requests to /api/* go to the api service
      service: api
    - path_prefix: /          # Everything else goes to the ui service
      service: ui
```

### Configuration Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique app name (lowercase, hyphens only) |
| `description` | No | Human-readable description |
| `services.<name>.context` | Yes | Path to directory containing Dockerfile |
| `services.<name>.port` | Yes | Port the container listens on |
| `services.<name>.health_check` | Yes | HTTP path that returns 200 when healthy |
| `services.<name>.environment` | No | Environment variables for the container |
| `services.<name>.resources.memory` | No | Memory limit (default: 256MB, max: 512MB) |
| `services.<name>.resources.cpu` | No | CPU limit (default: 0.5, max: 1.0) |
| `routing.subdomain` | Yes | Subdomain for your app |
| `routing.rules` | Yes | Path-based routing rules |

### Resource Limits

GreenCloud runs on a Raspberry Pi with 8GB RAM shared across all apps. Be reasonable:

| App Type | Recommended Memory | Recommended CPU |
|----------|-------------------|-----------------|
| Static site (nginx) | 32-64MB | 0.1 |
| React/Vue frontend | 64MB | 0.1 |
| Python API (no DB) | 128MB | 0.25 |
| Python API (with DB) | 256MB | 0.5 |
| Node.js API | 256MB | 0.5 |

---

## Step 5: Test Locally with Docker

Before deploying, make sure your containers build and run correctly:

```bash
# Build and test the backend
cd backend
docker build -t my-app-api .
docker run -p 8000:8000 my-app-api
# Visit http://localhost:8000/health — should return {"status": "healthy"}

# Build and test the frontend
cd frontend
docker build -t my-app-ui .
docker run -p 3000:80 -e VITE_API_URL=http://localhost:8000 my-app-ui
# Visit http://localhost:3000 — should show your app
```

If both containers work independently, you're ready to deploy.

---

## Step 6: Set Up the GitHub Webhook

GreenCloud deploys your app automatically when you push to your `main` branch. To enable this:

1. Go to your GitHub repo > **Settings** > **Webhooks** > **Add webhook**
2. Configure:
   - **Payload URL:** `https://api.green-cloud.uk/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** Your GreenCloud API key (provided by admin)
   - **Events:** Select "Just the push event"
3. Click **Add webhook**

That's it. Every push to `main` will now trigger a build and deploy.

---

## Step 7: Push and Deploy

```bash
# Make sure all your files are committed
git add Dockerfile .dockerignore greencloud.yml
git commit -m "feat: add GreenCloud deployment config"
git push origin main
```

Within a few minutes, your app will be live at:

```
https://<your-app-name>.green-cloud.uk
```

---

## Verifying Your Deployment

After pushing, you can check deployment status:

```bash
# If you have the GreenCloud CLI installed
greencloud deploy list
greencloud deploy status <deploy-id>

# Or check directly
curl https://<your-app>.green-cloud.uk/health
```

---

## Troubleshooting

### "My build failed"

- Check your Dockerfile builds locally first: `docker build -t test .`
- Make sure all files referenced in COPY commands exist
- Check your `.dockerignore` isn't excluding required files

### "Health check is failing"

- Verify your `/health` endpoint returns HTTP 200
- Make sure the port in your Dockerfile matches the port in `greencloud.yml`
- **Use `127.0.0.1` instead of `localhost` in health checks** — Alpine containers resolve `localhost` to IPv6 (`::1`) which nginx doesn't listen on. Always use the explicit IPv4 address.
- Check container logs: `greencloud deploy logs <deploy-id>`

### "Container is healthy but I get 404 from Traefik"

- Check what host rule Traefik registered: `curl http://localhost:8080/api/http/routers | python -m json.tool`
- The `DOMAIN` environment variable must be set when you start the compose stack — if unset it defaults to `localhost`
- Set it explicitly before running: `set DOMAIN=green-cloud.uk` (Windows) or `export DOMAIN=green-cloud.uk` (Linux/Mac)
- After changing DOMAIN, recreate containers: `docker compose up -d --force-recreate`

### "Frontend can't reach the API"

- Your frontend should use `/api` as the API URL (not `localhost:8000`)
- GreenCloud's reverse proxy routes `/api/*` to your backend automatically
- Make sure your `routing.rules` in `greencloud.yml` are correct

### "App is slow or unresponsive"

- Check your resource limits — you might need more memory
- The Pi has limited resources; keep your app lightweight
- Avoid blocking operations in your API endpoints

---

## What Happens Behind the Scenes

When you push code, here's what GreenCloud does:

1. **GitHub sends a webhook** to the GreenCloud API
2. **Build server wakes up** (Mini PC via Wake-on-LAN)
3. **Pulls your code** and builds Docker images (ARM64 for the Pi)
4. **Pushes images** to the local registry
5. **Agent on the Pi** pulls the new images
6. **Restarts your containers** with the new version
7. **Traefik** auto-discovers the new containers and routes traffic
8. **Cloudflare Tunnel** makes it publicly accessible with HTTPS

Total time: typically 2-5 minutes from push to live.

---

## Example: Meal Planner App

For a complete working example, see the Meal Planner deployment:

- **App repo structure:** backend (FastAPI) + frontend (React/Vite)
- **Backend Dockerfile:** `/backend/Dockerfile`
- **Frontend Dockerfile:** `/frontend/Dockerfile`
- **App config:** `/greencloud.yml`
- **Live URL:** `https://meal-planner.green-cloud.uk`

This app was deployed following exactly the steps above — it serves as proof that the process works end-to-end.

---

## Quick Reference

| What | Where |
|------|-------|
| Your app URL | `https://<name>.green-cloud.uk` |
| Health check | `https://<name>.green-cloud.uk/health` |
| Webhook URL | `https://api.green-cloud.uk/webhooks/github` |
| Dockerfile templates | `/templates/` in green-cloud repo |
| Resource limits | 128-512MB RAM, 0.1-1.0 CPU |
| Deploy trigger | Push to `main` branch |

---

## Need Help?

- Check the [Dockerfile templates](../templates/) for your stack
- Look at the [Meal Planner example](https://github.com/mattygibson/Meal-Planner) for a working reference
- Ask Matt — this is a learning platform, questions are welcome
