# GreenCloud Template: React + Vite

A production-ready Dockerfile for React applications built with Vite, served by nginx.

## What's included

- `Dockerfile` — Multi-stage build (node build + nginx serve)
- `nginx.conf` — SPA-friendly nginx config with asset caching
- `docker-entrypoint.sh` — Runtime API URL injection (build once, deploy anywhere)
- `.dockerignore` — Excludes dev files from the image
- `greencloud.yml` — Pre-configured app config for GreenCloud

## How to use

1. Copy all files from this template into your project root
2. Make sure your `package.json` has a `build` script (Vite does this by default)
3. Use `import.meta.env.VITE_API_URL` in your code for API calls:

```typescript
const API_URL = import.meta.env.VITE_API_URL;

const response = await fetch(`${API_URL}/meals`);
```

4. Edit `greencloud.yml`:
   - Change `name` to your app name
   - Change `subdomain` to match
   - If you have a backend, add it as a second service

5. Test locally:

```bash
docker build -t my-app-ui .
docker run -p 3000:80 -e VITE_API_URL=http://localhost:8000 my-app-ui
# Visit http://localhost:3000
```

## How runtime config injection works

Vite bakes environment variables into the JS bundle at build time. This is a problem for Docker (you'd need to rebuild for each environment).

This template solves it:
1. At build time, `VITE_API_URL` is set to a placeholder string
2. At container startup, the entrypoint script replaces the placeholder with the real value from the environment
3. Result: one image, deployable to any environment

## Project structure assumptions

```
my-app/
├── src/              # React source code
├── index.html        # Vite entry point
├── package.json      # Dependencies and build script
├── package-lock.json # Lock file
├── vite.config.ts    # Vite configuration
├── Dockerfile        # (from this template)
├── nginx.conf        # (from this template)
├── docker-entrypoint.sh  # (from this template)
├── .dockerignore     # (from this template)
└── greencloud.yml    # (from this template)
```

## Customisation

- **Different build output:** If your build outputs to a directory other than `dist/`, update the COPY in the Dockerfile
- **Additional env vars:** Add more placeholder/sed pairs in `docker-entrypoint.sh`
- **API proxy in dev:** For local development without Docker, configure Vite's proxy in `vite.config.ts`
