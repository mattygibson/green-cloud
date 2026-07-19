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
   - **Payload URL:** `https://api.green-cloud.uk/webhooks/github`
   - **Content type:** `application/json`
   - **Secret:** paste the secret from step 1
   - **Events:** select "Just the push event"
4. Click "Add webhook"

### 3. Add secret to environment

Add to your `infra/.env` file:

```
GITHUB_WEBHOOK_SECRET=your-secret-here
```

### 4. Verify

Push a commit to the `main` or `dev` branch and check:

```bash
# Check deployment was created
curl https://api.green-cloud.uk/deployments

# Or locally:
curl http://localhost:8000/deployments

# Check specific deployment logs
curl https://api.green-cloud.uk/deployments/1/logs
```

You can also check GitHub's delivery logs at Settings → Webhooks → Recent Deliveries to confirm the payload was sent and received successfully.

## Branch Routing

| Branch | Environment | Action |
|--------|-------------|--------|
| `main` / `prod` / `master` | prod | Auto-build and deploy |
| `dev` | dev | Auto-build and deploy |
| Any other | — | Ignored (200 response) |

## Authentication

The webhook endpoint validates the `X-Hub-Signature-256` header using HMAC-SHA256. Requests without a valid signature are rejected with 401.

The GreenCloud API uses API key authentication (RBAC) for all other management endpoints. The webhook endpoint uses its own secret-based validation.

## Troubleshooting

- **401 Invalid signature:** Check the secret matches in both
  GitHub and your `.env`
- **Webhook not firing:** Check GitHub webhook delivery logs at
  Settings → Webhooks → Recent Deliveries
- **Build failing:** Check `GET /deployments/{id}/logs` for details
- **502 from Cloudflare:** The GreenCloud API container isn't running — check `docker ps`
