"""Health checking for deployed containers."""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Health check URLs per environment
HEALTH_URLS = {
    "prod": [
        "http://prod-api:8000/health",
    ],
    "dev": [
        "http://dev-api:8000/health",
    ],
}


async def check_stack_health(environment: str) -> bool:
    """
    Check all services in a stack are healthy.

    Polls health endpoints with retries until timeout.
    """
    urls = HEALTH_URLS.get(environment, [])
    if not urls:
        logger.warning(f"No health URLs configured for {environment}")
        return True

    timeout = settings.health_check_timeout
    interval = settings.health_check_interval
    elapsed = 0

    while elapsed < timeout:
        all_healthy = True
        for url in urls:
            healthy = await _check_url(url)
            if not healthy:
                all_healthy = False
                break

        if all_healthy:
            logger.info(f"All services healthy for {environment}")
            return True

        await asyncio.sleep(interval)
        elapsed += interval
        logger.info(
            f"Health check retry ({elapsed}s/{timeout}s) for {environment}"
        )

    logger.error(
        f"Health check timed out after {timeout}s for {environment}"
    )
    return False


async def _check_url(url: str) -> bool:
    """Check a single health URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=3.0)
            return response.status_code == 200
    except Exception:
        return False
