# GreenCloud Template: Python FastAPI

A production-ready Dockerfile for FastAPI applications.

## What's included

- `Dockerfile` — Multi-stage build with uv, non-root user, health check
- `.dockerignore` — Excludes dev files from the image
- `greencloud.yml` — Pre-configured app config for GreenCloud

## How to use

1. Copy these files into your project root
2. Make sure you have a `requirements.txt` with your dependencies
3. Add a `/health` endpoint to your FastAPI app:

```python
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "my-app"}
```

4. Edit `greencloud.yml`:
   - Change `name` to your app name (lowercase, hyphens only)
   - Change `subdomain` to match
   - Adjust resource limits if needed

5. Test locally:

```bash
docker build -t my-app .
docker run -p 8000:8000 my-app
curl http://localhost:8000/health
```

## Project structure assumptions

This template assumes your project looks like:

```
my-app/
├── main.py           # FastAPI app entry point (app = FastAPI())
├── app/              # Application modules
├── requirements.txt  # Python dependencies
├── Dockerfile        # (from this template)
├── .dockerignore     # (from this template)
└── greencloud.yml    # (from this template)
```

If your structure differs, adjust the `COPY` commands in the Dockerfile.

## Customisation

- **Different entry point:** Change `CMD ["uvicorn", "main:app", ...]` to match your module
- **Additional files:** Add more `COPY` commands for extra directories
- **Database:** If you need PostgreSQL, add `asyncpg` or `psycopg2-binary` to requirements.txt and update `greencloud.yml` resources to 256MB
