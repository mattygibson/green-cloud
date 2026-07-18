from fastapi import APIRouter

from app.services.registry import check_registry_health

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check GreenCloud API health and dependencies."""
    registry_healthy = await check_registry_health()

    return {
        "status": "healthy" if registry_healthy else "degraded",
        "service": "greencloud-api",
        "dependencies": {
            "registry": "connected" if registry_healthy else "disconnected",
        },
    }
