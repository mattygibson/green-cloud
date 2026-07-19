import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.db.database import Base, engine
from app.routers import deployments, health, webhooks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="GreenCloud API",
    description="Deployment management and CI/CD orchestration for GreenCloud PaaS",
    version="0.1.0",
    docs_url="/docs",
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(deployments.router)
