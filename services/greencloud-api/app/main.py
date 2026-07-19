import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.db.database import Base, engine
from app.routers import app_deploy, apps, auth, deployments, health, webhooks

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

# CORS — allow the dashboard frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.green-cloud.uk",
        "http://app.localhost",
        "http://localhost:3000",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(deployments.router)
app.include_router(auth.router)
app.include_router(apps.router)
app.include_router(app_deploy.router)
