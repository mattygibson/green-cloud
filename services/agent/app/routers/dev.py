"""Dev environment toggle endpoints."""

import logging
import subprocess

from fastapi import APIRouter

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_compose(action: str, file: str) -> tuple[bool, str]:
    """Run a docker compose command."""
    cmd = ["docker", "compose", "-f", file, action]
    if action == "up":
        cmd.extend(["-d"])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


@router.post("/start")
async def start_dev():
    """Start the dev environment stack."""
    logger.info("Starting dev environment")
    compose_file = f"{settings.compose_project_dir}/docker-compose.dev.yml"
    success, output = _run_compose("up", compose_file)

    if success:
        return {"status": "started", "message": "Dev environment is starting"}
    return {"status": "error", "message": output}


@router.post("/stop")
async def stop_dev():
    """Stop the dev environment stack (preserves volumes)."""
    logger.info("Stopping dev environment")
    compose_file = f"{settings.compose_project_dir}/docker-compose.dev.yml"
    success, output = _run_compose("down", compose_file)

    if success:
        return {"status": "stopped", "message": "Dev environment stopped"}
    return {"status": "error", "message": output}


@router.get("/status")
async def dev_status():
    """Check if the dev environment is running."""
    cmd = [
        "docker", "compose",
        "-f", f"{settings.compose_project_dir}/docker-compose.dev.yml",
        "ps", "--format", "json",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "running", "containers": result.stdout.strip()}
        return {"status": "stopped"}
    except Exception:
        return {"status": "unknown"}
