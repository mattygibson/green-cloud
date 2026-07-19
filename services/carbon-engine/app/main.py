"""Carbon Engine — FastAPI application."""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Gauge, Counter
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routers import carbon, energy, health
from app.services.calculator import emissions_calculator
from app.services.electricity_maps import electricity_maps_client
from app.services.power_monitor import power_monitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GreenCloud Carbon Engine",
    description="Carbon-aware scheduling and emissions tracking",
    version="0.1.0",
    docs_url="/docs",
)

# CORS — allow the app frontend to call this service directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.green-cloud.uk",
        "http://app.localhost",
        "http://localhost",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Custom Prometheus metrics
carbon_intensity_gauge = Gauge(
    "greencloud_carbon_intensity_gco2_per_kwh",
    "Current grid carbon intensity",
    ["zone"],
)
power_watts_gauge = Gauge(
    "greencloud_power_watts",
    "Current power draw in watts",
    ["node"],
)
emissions_total_gauge = Gauge(
    "greencloud_emissions_gco2_total",
    "Total cumulative emissions in gCO2",
)
emissions_today_gauge = Gauge(
    "greencloud_emissions_gco2_today",
    "Emissions today in gCO2",
)
carbon_status_gauge = Gauge(
    "greencloud_carbon_status",
    "Carbon status (0=low, 1=medium, 2=high)",
)
builds_deferred_counter = Counter(
    "greencloud_builds_deferred_total",
    "Total builds deferred due to high carbon intensity",
)

# Register routers
app.include_router(health.router)
app.include_router(carbon.router)
app.include_router(energy.router)


async def metrics_collection_loop():
    """Background task to collect metrics every 60 seconds."""
    while True:
        try:
            # Get carbon intensity
            intensity_data = await electricity_maps_client.get_current_intensity()
            carbon_intensity_gauge.labels(zone=settings.electricity_maps_zone).set(
                intensity_data.carbon_intensity
            )

            # Get power readings
            pi_power = power_monitor.get_pi_power()
            minipc_power = power_monitor.get_minipc_power()
            power_watts_gauge.labels(node="pi5").set(pi_power.watts)
            power_watts_gauge.labels(node="minipc").set(minipc_power.watts)

            # Record emissions
            total_power = pi_power.watts + minipc_power.watts
            emissions_calculator.record(total_power, intensity_data.carbon_intensity)

            # Update summary metrics
            summary = emissions_calculator.get_summary()
            emissions_total_gauge.set(summary.total_gco2)
            emissions_today_gauge.set(summary.today_gco2)

            # Carbon status
            from app.services.scheduler import get_carbon_status, CarbonStatus
            status = get_carbon_status(intensity_data.carbon_intensity)
            status_value = {CarbonStatus.LOW: 0, CarbonStatus.MEDIUM: 1, CarbonStatus.HIGH: 2}
            carbon_status_gauge.set(status_value[status])

        except Exception as e:
            logger.error(f"Metrics collection error: {e}")

        await asyncio.sleep(60)


@app.on_event("startup")
async def startup():
    """Start background metrics collection."""
    asyncio.create_task(metrics_collection_loop())
    logger.info(
        f"Carbon Engine started — zone={settings.electricity_maps_zone}, "
        f"thresholds: low<{settings.carbon_threshold_low}, high>{settings.carbon_threshold_high}"
    )
