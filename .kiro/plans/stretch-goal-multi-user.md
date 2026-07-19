# Stretch Goal: Multi-User App Publishing Platform

## Vision

After the core GreenCloud tasks are complete, open the platform so friends and other learners can deploy their own small apps. Provide a free, subscription-free environment where people can learn real CI/CD without needing AWS, Vercel, or any paid service.

**Tagline:** "Your own Heroku, running on a Raspberry Pi in someone's house."

## Who It's For

- Friends wanting to learn basic CI/CD and deployment
- Junior developers building portfolio projects
- Anyone who wants to publish a small web app without a subscription
- Students learning Docker, containers, and deployment pipelines

## What Users Get

- A subdomain: `<their-app>.greencloud.yourdomain.com`
- Push-to-deploy: push code to a branch → app goes live
- Free HTTPS (via Cloudflare Tunnel)
- Basic logs and health monitoring
- No credit card, no subscription, no vendor lock-in

## What Users Need to Provide

- Their code in a Git repo (GitHub)
- A `Dockerfile` in their repo (we provide templates)
- A `greencloud.yml` config file (port, health check path, environment variables)

## Technical Design

### App Configuration (`greencloud.yml`)

Users add this to their repo root:

```yaml
name: my-app
port: 8080
health_check: /health
environment:
  - NODE_ENV=production
resources:
  memory: 256MB
  cpu: 0.5
```

### Deployment Flow

```
User pushes code → GitHub webhook → GreenCloud API receives it
→ Build image (tagged per user/app) → Push to registry
→ Agent deploys as a new container → Traefik auto-routes subdomain
→ App is live at <app-name>.greencloud.yourdomain.com
```

### Routing (Traefik)

Each user app gets a Traefik router automatically via Docker labels:

```
traefik.http.routers.<app-name>.rule=Host(`<app-name>.greencloud.yourdomain.com`)
```

No manual configuration needed — Traefik discovers new containers via Docker labels.

### Resource Limits

Since everything runs on a single Pi (8GB RAM):

| Resource | Per App | Max Apps |
|----------|---------|----------|
| Memory | 256MB default (configurable 128-512MB) | ~10-15 small apps |
| CPU | 0.5 cores default | Shared across all |
| Storage | 1GB per app | Limited by NVMe size |

### User Management (Invite-Only — No Public Access)

**This platform is private.** Only people you explicitly invite can deploy apps. There is no public signup, no registration page, and no way for anyone on the internet to use the platform without your approval.

**How access works:**

1. A friend asks you to join
2. You register them: `greencloud users add --name "John" --github "johndoe"`
3. They receive a unique API key (generated, not chosen)
4. They configure their GitHub webhook with that key
5. Only webhooks signed with a registered key are processed — all others get 401 Rejected

**Security layers:**

- **API key validation:** Every webhook is verified against the registered keys database
- **GitHub username whitelist:** Only pushes from registered GitHub usernames are accepted
- **App ownership:** Each key is scoped to specific app names — users can only deploy their own apps
- **Audit log:** All deploy attempts logged (who, when, what repo, success/failure)
- **Instant revocation:** Delete a key → that user can never deploy again
- **Rate limiting:** Max 5 deploys per hour per user (prevents abuse)

**Admin controls:**

```
greencloud users add --name "John" --github "johndoe"    # Invite a friend
greencloud users list                                      # See all users
greencloud users revoke --github "johndoe"                # Remove access
greencloud users activity                                  # See who deployed what
```

### Multi-User GreenCloud API Extensions

New endpoints:

```
POST   /users                     # Admin: register new user
GET    /users                     # Admin: list users
POST   /apps                      # User: register a new app
GET    /apps                      # User: list their apps
DELETE /apps/{app-name}           # User: remove their app
GET    /apps/{app-name}/logs      # User: view app logs
GET    /apps/{app-name}/status    # User: check app health
```

### Dockerfile Templates

Provide ready-made templates for common stacks so users don't need to write their own:

- `templates/node-express/` — Node.js Express app
- `templates/python-flask/` — Python Flask app
- `templates/python-fastapi/` — Python FastAPI app
- `templates/static-site/` — HTML/CSS/JS served by nginx
- `templates/react-vite/` — React app built with Vite

Each template includes:
- `Dockerfile` (multi-stage, optimised)
- `greencloud.yml` (pre-configured)
- `README.md` (how to use it)
- Example app code

### User Guide ("Deploy Your First App")

A step-by-step guide for complete beginners:

1. Get your API key from the admin (you)
2. Create a new repo on GitHub with your app code
3. Copy the right Dockerfile template into your repo
4. Add a `greencloud.yml` with your app name
5. Set up the GitHub webhook (one-time, we provide a script)
6. Push to `main` — your app deploys automatically
7. Visit `https://<your-app>.greencloud.yourdomain.com`

### Safety and Isolation

- Each app runs in its own container (process isolation)
- Resource limits prevent one app from starving others
- Network isolation: apps can't talk to each other or to infrastructure containers
- No shell access — users only interact via their code and the API
- Admin can kill any app instantly if it misbehaves

## Implementation Tasks

1. **User registration system** — API keys, user→app mapping
2. **App registry** — store app configs, track deployments per user
3. **Dynamic Traefik routing** — auto-generate routes from app registry
4. **Resource limits in Docker** — enforce memory/CPU caps per container
5. **Dockerfile templates** — create 4-5 common stack templates
6. **User-facing guide** — "Deploy Your First App in 5 Minutes"
7. **Admin dashboard** — see all running apps, resource usage, kill switch
8. **Webhook per-user** — route webhooks to the correct app build

## What This Teaches Users

By using GreenCloud, friends learn:

- How CI/CD pipelines actually work (not just clicking buttons)
- What Docker does and why it matters
- How web apps get from code to a live URL
- DNS, routing, and reverse proxies (at a high level)
- Health checks and why they matter
- Environment variables and configuration
- The deployment lifecycle: build → push → deploy → verify

## Success Criteria

- A friend with zero DevOps experience can deploy a "Hello World" app in under 10 minutes
- The guide is clear enough that you don't need to help them (async-friendly)
- At least 5 small apps running simultaneously without performance issues
- No recurring costs for users (everything runs on your hardware)

## Estimated Effort

- 20-30 hours additional development on top of Tasks 1-10
- Best tackled after Task 10 (CLI, RBAC) is complete since it builds on that foundation

## Dependencies

- All 10 core tasks complete
- Domain with Cloudflare Tunnel working (Task 6)
- Hardware deployed and stable (Task 9)
- RBAC system in place (Task 10)
