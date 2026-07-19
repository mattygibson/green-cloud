# ---------------------------------------------------------
# GreenCloud Template: Python FastAPI
# A production-ready Dockerfile for FastAPI applications.
#
# Usage:
#   1. Copy this file into your project root (next to requirements.txt)
#   2. Adjust the COPY commands if your project structure differs
#   3. Build: docker build -t my-api .
#   4. Run:   docker run -p 8000:8000 my-api
# ---------------------------------------------------------

# Stage 1: Install dependencies with uv (fast Python package installer)
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency file first (maximises Docker layer caching)
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Runtime (minimal image)
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy your application source code
# Adjust these COPY commands to match your project structure:
COPY main.py .
COPY app/ ./app/

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check — update the URL path if your health endpoint differs
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
