"""Health check endpoint."""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Carbon Engine health check."""
    return {
        "status": "healthy",
        "service": "carbon-engine",
        "zone": settings.electricity_maps_zone,
        "api_key_configured": bool(settings.electricity_maps_api_key),
    }
