"""Carbon-aware scheduling logic."""

import logging
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class CarbonStatus(str, Enum):
    """Grid carbon intensity status."""

    LOW = "low"  # Green: all workloads proceed
    MEDIUM = "medium"  # Amber: defer non-critical
    HIGH = "high"  # Red: only critical (prod) proceeds


class SchedulerDecision(str, Enum):
    """Scheduling decision for a workload."""

    PROCEED = "proceed"
    DEFER = "defer"


def get_carbon_status(carbon_intensity: float) -> CarbonStatus:
    """Determine carbon status from intensity value.

    Args:
        carbon_intensity: Current grid carbon intensity in gCO2eq/kWh

    Returns:
        CarbonStatus (low/medium/high)
    """
    if carbon_intensity < settings.carbon_threshold_low:
        return CarbonStatus.LOW
    elif carbon_intensity < settings.carbon_threshold_high:
        return CarbonStatus.MEDIUM
    else:
        return CarbonStatus.HIGH


def should_proceed(carbon_intensity: float, is_production: bool) -> SchedulerDecision:
    """Decide whether a workload should proceed or be deferred.

    Args:
        carbon_intensity: Current grid carbon intensity
        is_production: Whether this is a production deployment

    Returns:
        SchedulerDecision (proceed or defer)
    """
    # Production deployments always proceed
    if is_production:
        return SchedulerDecision.PROCEED

    status = get_carbon_status(carbon_intensity)

    if status == CarbonStatus.LOW:
        return SchedulerDecision.PROCEED
    elif status == CarbonStatus.MEDIUM:
        # Medium: defer non-critical workloads
        logger.info(
            f"Deferring non-critical workload: intensity={carbon_intensity:.0f} gCO2/kWh"
        )
        return SchedulerDecision.DEFER
    else:
        # High: definitely defer
        logger.info(
            f"Deferring workload (high intensity): {carbon_intensity:.0f} gCO2/kWh"
        )
        return SchedulerDecision.DEFER


def get_thresholds() -> dict[str, int]:
    """Get current scheduling thresholds."""
    return {
        "low_below": settings.carbon_threshold_low,
        "high_above": settings.carbon_threshold_high,
    }
