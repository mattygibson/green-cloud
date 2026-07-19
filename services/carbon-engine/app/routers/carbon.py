"""Carbon intensity endpoints."""

from fastapi import APIRouter

from app.services.electricity_maps import electricity_maps_client
from app.services.scheduler import (
    CarbonStatus,
    SchedulerDecision,
    get_carbon_status,
    get_thresholds,
    should_proceed,
)

router = APIRouter(prefix="/carbon", tags=["carbon"])


@router.get("/current")
async def get_current_intensity():
    """Get current carbon intensity for configured zone."""
    data = await electricity_maps_client.get_current_intensity()
    status = get_carbon_status(data.carbon_intensity)
    return {
        "zone": data.zone,
        "carbon_intensity_gco2_kwh": data.carbon_intensity,
        "fossil_fuel_percentage": data.fossil_fuel_percentage,
        "status": status.value,
        "timestamp": data.timestamp,
        "is_cached": data.is_cached,
    }


@router.get("/history")
async def get_intensity_history():
    """Get 24h carbon intensity history."""
    history = await electricity_maps_client.get_history()
    return {"zone": "GB", "history": history}


@router.get("/forecast")
async def get_intensity_forecast():
    """Get carbon intensity forecast."""
    forecast = await electricity_maps_client.get_forecast()
    return {"zone": "GB", "forecast": forecast}


@router.get("/status")
async def get_status():
    """Get overall carbon status (green/amber/red)."""
    data = await electricity_maps_client.get_current_intensity()
    status = get_carbon_status(data.carbon_intensity)
    thresholds = get_thresholds()
    return {
        "status": status.value,
        "carbon_intensity_gco2_kwh": data.carbon_intensity,
        "thresholds": thresholds,
        "description": {
            CarbonStatus.LOW: "Grid is clean — all workloads proceed",
            CarbonStatus.MEDIUM: "Moderate intensity — non-critical workloads deferred",
            CarbonStatus.HIGH: "High intensity — only production deploys proceed",
        }[status],
    }


@router.get("/should-proceed")
async def check_should_proceed(is_production: bool = False):
    """Check if a workload should proceed based on carbon intensity."""
    data = await electricity_maps_client.get_current_intensity()
    decision = should_proceed(data.carbon_intensity, is_production)
    return {
        "decision": decision.value,
        "carbon_intensity_gco2_kwh": data.carbon_intensity,
        "is_production": is_production,
        "status": get_carbon_status(data.carbon_intensity).value,
    }
