"""Energy and power monitoring endpoints."""

from fastapi import APIRouter

from app.services.calculator import emissions_calculator
from app.services.power_monitor import power_monitor

router = APIRouter(prefix="/energy", tags=["energy"])


@router.get("/power")
async def get_power():
    """Get current power readings for all nodes."""
    pi = power_monitor.get_pi_power()
    minipc = power_monitor.get_minipc_power()
    total = pi.watts + minipc.watts
    return {
        "total_watts": round(total, 2),
        "nodes": [
            {
                "node": pi.node,
                "watts": pi.watts,
                "cpu_percent": pi.cpu_percent,
                "source": pi.source,
            },
            {
                "node": minipc.node,
                "watts": minipc.watts,
                "cpu_percent": minipc.cpu_percent,
                "source": minipc.source,
            },
        ],
    }


@router.get("/emissions")
async def get_emissions():
    """Get cumulative emissions data."""
    summary = emissions_calculator.get_summary()
    return {
        "total_gco2": round(summary.total_gco2, 2),
        "today_gco2": round(summary.today_gco2, 2),
        "total_kwh": round(summary.total_kwh, 4),
        "today_kwh": round(summary.today_kwh, 4),
        "measurement_count": summary.measurement_count,
    }


@router.post("/deployment-emissions")
async def calculate_deployment_emissions(
    duration_seconds: float, avg_power_watts: float = 8.0, avg_intensity: float = 200.0
):
    """Calculate emissions for a specific deployment."""
    emissions = emissions_calculator.calculate_deployment_emissions(
        duration_seconds, avg_power_watts, avg_intensity
    )
    return {
        "duration_seconds": duration_seconds,
        "avg_power_watts": avg_power_watts,
        "avg_intensity_gco2_kwh": avg_intensity,
        "emissions_gco2": round(emissions, 4),
    }
