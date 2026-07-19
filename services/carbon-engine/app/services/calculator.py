"""Emissions calculator: energy x carbon intensity = CO2."""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmissionsSnapshot:
    """Emissions data at a point in time."""

    timestamp: float
    power_watts: float
    carbon_intensity: float  # gCO2eq/kWh
    emissions_rate_gco2_per_hour: float  # gCO2/hour at current rate


@dataclass
class EmissionsSummary:
    """Cumulative emissions summary."""

    total_gco2: float = 0.0
    today_gco2: float = 0.0
    total_kwh: float = 0.0
    today_kwh: float = 0.0
    measurement_count: int = 0
    first_measurement: float = 0.0
    last_measurement: float = 0.0


class EmissionsCalculator:
    """Calculates and accumulates carbon emissions."""

    def __init__(self) -> None:
        self._summary = EmissionsSummary()
        self._last_snapshot: EmissionsSnapshot | None = None
        self._data_file = Path(settings.data_dir) / "emissions.json"
        self._load()

    def _load(self) -> None:
        """Load persisted emissions data."""
        try:
            if self._data_file.exists():
                data = json.loads(self._data_file.read_text())
                self._summary = EmissionsSummary(**data)
                logger.info(f"Loaded emissions data: {self._summary.total_gco2:.1f} gCO2 total")
        except Exception as e:
            logger.warning(f"Could not load emissions data: {e}")

    def _save(self) -> None:
        """Persist emissions data to disk."""
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "total_gco2": self._summary.total_gco2,
                "today_gco2": self._summary.today_gco2,
                "total_kwh": self._summary.total_kwh,
                "today_kwh": self._summary.today_kwh,
                "measurement_count": self._summary.measurement_count,
                "first_measurement": self._summary.first_measurement,
                "last_measurement": self._summary.last_measurement,
            }
            self._data_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Could not save emissions data: {e}")

    def record(self, power_watts: float, carbon_intensity: float) -> EmissionsSnapshot:
        """Record a measurement and update cumulative totals.

        Args:
            power_watts: Current power draw in watts
            carbon_intensity: Current grid carbon intensity in gCO2eq/kWh

        Returns:
            Snapshot of current emissions rate
        """
        now = time.time()

        # Calculate emissions rate: watts * intensity / 1000 = gCO2/hour
        # (power_watts / 1000 = kW, kW * gCO2/kWh = gCO2/h)
        emissions_rate = (power_watts / 1000.0) * carbon_intensity

        snapshot = EmissionsSnapshot(
            timestamp=now,
            power_watts=power_watts,
            carbon_intensity=carbon_intensity,
            emissions_rate_gco2_per_hour=round(emissions_rate, 4),
        )

        # If we have a previous measurement, calculate energy used in interval
        if self._last_snapshot is not None:
            interval_hours = (now - self._last_snapshot.timestamp) / 3600.0
            # Use average of previous and current power for trapezoidal integration
            avg_power = (self._last_snapshot.power_watts + power_watts) / 2.0
            energy_kwh = (avg_power / 1000.0) * interval_hours
            avg_intensity = (self._last_snapshot.carbon_intensity + carbon_intensity) / 2.0
            interval_emissions = energy_kwh * avg_intensity

            self._summary.total_kwh += energy_kwh
            self._summary.today_kwh += energy_kwh
            self._summary.total_gco2 += interval_emissions
            self._summary.today_gco2 += interval_emissions

        if self._summary.first_measurement == 0.0:
            self._summary.first_measurement = now
        self._summary.last_measurement = now
        self._summary.measurement_count += 1

        self._last_snapshot = snapshot

        # Persist every 10 measurements
        if self._summary.measurement_count % 10 == 0:
            self._save()

        return snapshot

    def get_summary(self) -> EmissionsSummary:
        """Get current emissions summary."""
        return self._summary

    def reset_daily(self) -> None:
        """Reset daily counters (call at midnight)."""
        self._summary.today_gco2 = 0.0
        self._summary.today_kwh = 0.0
        self._save()

    def calculate_deployment_emissions(
        self, duration_seconds: float, avg_power_watts: float, avg_intensity: float
    ) -> float:
        """Calculate emissions for a specific deployment.

        Args:
            duration_seconds: How long the build/deploy took
            avg_power_watts: Average power during the operation
            avg_intensity: Average carbon intensity during the operation

        Returns:
            Emissions in gCO2
        """
        energy_kwh = (avg_power_watts / 1000.0) * (duration_seconds / 3600.0)
        return energy_kwh * avg_intensity


# Singleton
emissions_calculator = EmissionsCalculator()
