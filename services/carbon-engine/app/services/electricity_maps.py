"""Electricity Maps API client with caching."""

import logging
import time
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CarbonIntensityData:
    """Carbon intensity measurement."""

    zone: str
    carbon_intensity: float  # gCO2eq/kWh
    fossil_fuel_percentage: float = 0.0
    timestamp: str = ""
    is_cached: bool = False


@dataclass
class CachedResponse:
    """Cached API response with TTL."""

    data: dict | list | None = None
    fetched_at: float = 0.0

    def is_valid(self, ttl_seconds: int) -> bool:
        return self.data is not None and (time.time() - self.fetched_at) < ttl_seconds


class ElectricityMapsClient:
    """Client for the Electricity Maps API."""

    def __init__(self) -> None:
        self._cache_current: CachedResponse = CachedResponse()
        self._cache_history: CachedResponse = CachedResponse()
        self._cache_forecast: CachedResponse = CachedResponse()
        self._last_known_intensity: float | None = None

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if settings.electricity_maps_api_key:
            headers["auth-token"] = settings.electricity_maps_api_key
        return headers

    async def get_current_intensity(self) -> CarbonIntensityData:
        """Get current carbon intensity for configured zone."""
        if self._cache_current.is_valid(settings.electricity_maps_cache_ttl_seconds):
            data = self._cache_current.data
            return CarbonIntensityData(
                zone=settings.electricity_maps_zone,
                carbon_intensity=data.get("carbonIntensity", 0),
                fossil_fuel_percentage=data.get("fossilFuelPercentage", 0),
                timestamp=data.get("datetime", ""),
                is_cached=True,
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.electricity_maps_base_url}/carbon-intensity/latest",
                    params={"zone": settings.electricity_maps_zone},
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()

            self._cache_current = CachedResponse(data=data, fetched_at=time.time())
            intensity = data.get("carbonIntensity", 0)
            self._last_known_intensity = intensity

            return CarbonIntensityData(
                zone=settings.electricity_maps_zone,
                carbon_intensity=intensity,
                fossil_fuel_percentage=data.get("fossilFuelPercentage", 0),
                timestamp=data.get("datetime", ""),
            )
        except Exception as e:
            logger.warning(f"Electricity Maps API error: {e}")
            # Fallback to last known value
            return CarbonIntensityData(
                zone=settings.electricity_maps_zone,
                carbon_intensity=self._last_known_intensity or 200.0,
                is_cached=True,
            )

    async def get_history(self) -> list[dict]:
        """Get 24h carbon intensity history."""
        if self._cache_history.is_valid(settings.electricity_maps_cache_ttl_seconds):
            return self._cache_history.data

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.electricity_maps_base_url}/carbon-intensity/history",
                    params={"zone": settings.electricity_maps_zone},
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()

            history = data.get("history", data) if isinstance(data, dict) else data
            self._cache_history = CachedResponse(data=history, fetched_at=time.time())
            return history
        except Exception as e:
            logger.warning(f"Electricity Maps history error: {e}")
            return self._cache_history.data or []

    async def get_forecast(self) -> list[dict]:
        """Get carbon intensity forecast (if available)."""
        if self._cache_forecast.is_valid(settings.electricity_maps_cache_ttl_seconds):
            return self._cache_forecast.data

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.electricity_maps_base_url}/carbon-intensity/forecast",
                    params={"zone": settings.electricity_maps_zone},
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()

            forecast = data.get("forecast", data) if isinstance(data, dict) else data
            self._cache_forecast = CachedResponse(data=forecast, fetched_at=time.time())
            return forecast
        except Exception as e:
            logger.warning(f"Electricity Maps forecast error: {e}")
            return self._cache_forecast.data or []


# Singleton instance
electricity_maps_client = ElectricityMapsClient()
