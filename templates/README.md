# GreenCloud Dockerfile Templates

Ready-made templates for deploying common app stacks on GreenCloud. Copy the template that matches your stack into your project and follow the instructions in its README.

## Available Templates

| Template | Stack | Use case |
|----------|-------|----------|
| [python-fastapi](./python-fastapi/) | Python 3.12 + FastAPI + uvicorn | Backend APIs, webhooks, data services |
| [react-vite](./react-vite/) | React 18+ + Vite + nginx | Single-page applications, dashboards |

## Coming Soon

- `node-express` — Node.js + Express backend
- `python-flask` — Python + Flask backend
- `static-site` — HTML/CSS/JS served by nginx

## How to Use

1. Pick the template that matches your app's stack
2. Copy all files from that template directory into your project root
3. Follow the template's README for customisation steps
4. Add a `greencloud.yml` to configure your deployment
5. Push to GitHub — GreenCloud does the rest

## Full Guide

See [Deploy Your First App on GreenCloud](../docs/guides/deploy-your-first-app.md) for the complete walkthrough.
