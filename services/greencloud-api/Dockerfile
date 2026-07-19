# Stage 1: Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Install Docker CLI (needed for buildx commands) and git (needed for repo cloning)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    curl -fsSL https://get.docker.com | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create data and workspace directories
RUN mkdir -p /app/data /app/workspaces

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
