"""System stats collection endpoints."""

import os
import subprocess

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Get system resource usage stats."""
    stats = {
        "cpu_percent": _get_cpu_percent(),
        "memory": _get_memory_info(),
        "disk": _get_disk_info(),
        "containers": _get_container_count(),
    }
    return stats


def _get_cpu_percent() -> float | None:
    """Get CPU usage percentage."""
    try:
        # Works on Linux (Pi target)
        with open("/proc/stat", "r") as f:
            line = f.readline()
            parts = line.split()
            idle = int(parts[4])
            total = sum(int(p) for p in parts[1:])
            return round((1 - idle / total) * 100, 1)
    except (FileNotFoundError, IndexError):
        return None


def _get_memory_info() -> dict | None:
    """Get memory usage info."""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            info = {}
            for line in lines:
                parts = line.split()
                if parts[0] in ("MemTotal:", "MemAvailable:"):
                    info[parts[0].rstrip(":")] = int(parts[1]) * 1024
            if info:
                total = info.get("MemTotal", 0)
                available = info.get("MemAvailable", 0)
                used = total - available
                return {
                    "total_bytes": total,
                    "used_bytes": used,
                    "available_bytes": available,
                    "percent": round(used / total * 100, 1) if total else 0,
                }
    except FileNotFoundError:
        pass
    return None


def _get_disk_info() -> dict | None:
    """Get disk usage for the root filesystem."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent": round(used / total * 100, 1) if total else 0,
        }
    except (OSError, AttributeError):
        return None


def _get_container_count() -> dict:
    """Get running container count."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True, text=True, timeout=5,
        )
        running = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        return {"running": running}
    except Exception:
        return {"running": -1}
