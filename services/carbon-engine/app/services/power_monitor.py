"""Power monitoring via CPU-based estimation."""

import logging
import platform
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PowerReading:
    """Power measurement for a node."""

    node: str
    watts: float
    cpu_percent: float
    source: str  # "estimated" or "measured"


def _read_cpu_percent() -> float:
    """Read CPU usage from /proc/stat (Linux) or return estimate."""
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:])
        # This gives instantaneous snapshot; for delta-based calculation
        # we'd need to sample twice. Using a simple heuristic instead.
        busy = total - idle
        return (busy / total) * 100 if total > 0 else 0.0
    except (FileNotFoundError, IndexError, ValueError):
        # Not on Linux or /proc not available
        return 25.0  # Default estimate


def _estimate_watts(cpu_percent: float, idle_watts: float, max_watts: float) -> float:
    """Estimate power draw from CPU usage using linear interpolation."""
    fraction = min(max(cpu_percent / 100.0, 0.0), 1.0)
    return idle_watts + (max_watts - idle_watts) * fraction


class PowerMonitor:
    """Monitors power consumption of GreenCloud nodes."""

    def __init__(self) -> None:
        self._last_pi_reading: PowerReading | None = None
        self._last_minipc_reading: PowerReading | None = None

    def get_pi_power(self) -> PowerReading:
        """Get estimated power draw for the Pi 5."""
        cpu = _read_cpu_percent()
        watts = _estimate_watts(cpu, settings.pi_idle_watts, settings.pi_max_watts)
        reading = PowerReading(
            node="pi5", watts=round(watts, 2), cpu_percent=round(cpu, 1), source="estimated"
        )
        self._last_pi_reading = reading
        return reading

    def get_minipc_power(self) -> PowerReading:
        """Get estimated power for Mini PC (0 if sleeping)."""
        # TODO: Implement Wake-on-LAN status check or smart plug query
        # For now, assume Mini PC is off unless actively building
        reading = PowerReading(
            node="minipc", watts=0.0, cpu_percent=0.0, source="estimated"
        )
        self._last_minipc_reading = reading
        return reading

    def get_total_power(self) -> float:
        """Get total power draw across all nodes in watts."""
        pi = self.get_pi_power()
        minipc = self.get_minipc_power()
        return pi.watts + minipc.watts


# Singleton
power_monitor = PowerMonitor()
