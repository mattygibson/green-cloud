from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Agent health check."""
    return {
        "status": "healthy",
        "service": "greencloud-agent",
    }
