"""
Dynamic app discovery endpoint.

Queries Docker for running containers that have Traefik routing labels,
filtering out infrastructure services to return only user-deployed apps.
"""

import logging
from typing import Optional

import docker
from docker.errors import DockerException
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Apps"])

# Infrastructure containers that should NOT appear as "user apps"
INFRA_CONTAINERS = {
    "greencloud-api",
    "greencloud-agent",
    "greencloud-carbon",
    "greencloud-registry",
    "greencloud-traefik",
    "greencloud-tunnel",
    "greencloud-prometheus",
    "greencloud-node-exporter",
    "greencloud-loki",
    "greencloud-promtail",
    "greencloud-grafana",
    "greencloud-landing",
    "prod-api",
    "prod-ui",
    "prod-db",
    "dev-api",
    "dev-ui",
    "dev-db",
}


class AppInfo(BaseModel):
    name: str
    url: str
    health_url: str
    status: str
    container_name: str


class AppsResponse(BaseModel):
    apps: list[AppInfo]
    count: int


def _extract_host_from_labels(labels: dict) -> Optional[str]:
    """Extract the hostname from Traefik router labels."""
    for key, value in labels.items():
        if "routers." in key and ".rule" in key:
            # Parse Host(`example.com`) from the rule
            if "Host(`" in value:
                start = value.index("Host(`") + 6
                end = value.index("`)", start)
                return value[start:end]
    return None


def _extract_health_path_from_labels(labels: dict) -> Optional[str]:
    """Extract health check path from container labels if a health router exists."""
    for key, value in labels.items():
        if "health" in key.lower() and ".rule" in key:
            if "Path(`" in value:
                start = value.index("Path(`") + 6
                end = value.index("`)", start)
                return value[start:end]
    return None


@router.get("/apps", response_model=AppsResponse)
async def list_apps():
    """List all running user applications discovered via Docker."""
    apps: list[AppInfo] = []
    seen_hosts: set[str] = set()

    try:
        client = docker.from_env()
        containers = client.containers.list(filters={"status": "running"})

        for container in containers:
            name = container.name or ""

            # Skip infrastructure containers
            if name in INFRA_CONTAINERS:
                continue

            labels = container.labels or {}

            # Only include containers with Traefik routing enabled
            if labels.get("traefik.enable") != "true":
                continue

            # Extract the hostname
            host = _extract_host_from_labels(labels)
            if not host or host in seen_hosts:
                continue

            seen_hosts.add(host)

            # Determine health status from container health
            health_status = "unknown"
            try:
                container.reload()
                health = container.attrs.get("State", {}).get("Health", {})
                if health:
                    health_status = health.get("Status", "unknown")
                else:
                    # No health check defined but container is running
                    health_status = "running"
            except Exception:
                health_status = "unknown"

            # Build the app URL
            url = f"https://{host}"

            # Check for health path
            health_path = _extract_health_path_from_labels(labels)
            health_url = f"{url}{health_path}" if health_path else f"{url}/health"

            # Derive a friendly app name from the hostname
            app_name = host.split(".")[0].replace("-", " ").title()

            apps.append(
                AppInfo(
                    name=app_name,
                    url=url,
                    health_url=health_url,
                    status=health_status,
                    container_name=name,
                )
            )

    except DockerException as e:
        logger.error(f"Failed to connect to Docker: {e}")

    return AppsResponse(apps=apps, count=len(apps))
