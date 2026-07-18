# GitHub Webhook Setup

## Overview

The GreenCloud API receives push events from GitHub to trigger
automated builds and deployments.

## Setup Steps

### 1. Generate a webhook secret

Generate a random secret for signing webhooks:

```bash
openssl rand -hex 32
```

Save this value — you'll need it in both GitHub and your `.env` file.

### 2. Configure the webhook in GitHub

1. Go to https://github.com/mattygibson/green-cloud/settings/hooks
2. Click "Add webhook"
3. Configure:
   - **Payload URL:** `https://greencloud-api.yourdomain.com/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** paste the secret from step 1
   - **Events:** select "Just the push event"
4. Click "Add webhook"

### 3. Add secret to environment

Add to your `infra/.env` file:

```
GITHUB_WEBHOOK_SECRET=your-secret-here
```

### 4. Local testing with ngrok

For testing before Cloudflare Tunnel is set up:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Use the generated URL as your webhook payload URL
# e.g., https://abc123.ngrok.io/webhooks/github
```

### 5. Verify

Push a commit to the `main` or `dev` branch and check:

```bash
# Check deployment was created
curl http://localhost:8000/deployments

# Check specific deployment logs
curl http://localhost:8000/deployments/1/logs
```

## Branch Routing

| Branch | Environment | Action |
|--------|-------------|--------|
| `main` / `prod` / `master` | prod | Auto-build and deploy |
| `dev` | dev | Auto-build and deploy |
| Any other | — | Ignored (200 response) |

## Troubleshooting

- **401 Invalid signature:** Check the secret matches in both
  GitHub and your `.env`
- **Webhook not firing:** Check GitHub webhook delivery logs at
  Settings → Webhooks → Recent Deliveries
- **Build failing:** Check `GET /deployments/{id}/logs` for details
