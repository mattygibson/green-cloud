"""Registry interaction — check images, tags, etc."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def list_repositories() -> list[str]:
    """List all repositories in the local registry."""
    url = f"http://{settings.registry_host}/v2/_catalog"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json().get("repositories", [])
    except Exception as e:
        logger.error(f"Failed to list registry repositories: {e}")
    return []


async def list_tags(repository: str) -> list[str]:
    """List tags for a specific repository."""
    url = f"http://{settings.registry_host}/v2/{repository}/tags/list"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json().get("tags", [])
    except Exception as e:
        logger.error(f"Failed to list tags for {repository}: {e}")
    return []


async def check_registry_health() -> bool:
    """Check if the registry is reachable."""
    url = f"http://{settings.registry_host}/v2/"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=3.0)
            return response.status_code == 200
    except Exception:
        return False
