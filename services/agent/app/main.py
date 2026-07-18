import logging

from fastapi import FastAPI

from app.routers import deploy, dev, health, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="GreenCloud Agent",
    description="Node agent for container deployment and management",
    version="0.1.0",
    docs_url="/docs",
)

app.include_router(health.router)
app.include_router(deploy.router, prefix="/agent")
app.include_router(dev.router, prefix="/agent/dev")
app.include_router(stats.router, prefix="/agent")
