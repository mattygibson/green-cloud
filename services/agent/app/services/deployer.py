"""Deployment orchestration — pull images and restart stacks."""

import logging
import subprocess

from app.config import settings

logger = logging.getLogger(__name__)


async def deploy_stack(
    environment: str, images: dict[str, str]
) -> tuple[bool, str]:
    """
    Deploy a stack by pulling new images and restarting.

    Args:
        environment: "prod" or "dev"
        images: dict of service_name → image reference

    Returns:
        (success, logs)
    """
    compose_file = _get_compose_file(environment)
    logs = ""

    # Step 1: Pull new images
    logger.info(f"Pulling images for {environment}")
    cmd = ["docker", "compose", "-f", compose_file, "pull"]
    success, output = _run_cmd(cmd)
    logs += f"=== Pull ===\n{output}\n"
    if not success:
        return False, logs

    # Step 2: Restart with new images
    logger.info(f"Restarting {environment} stack")
    cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
    success, output = _run_cmd(cmd)
    logs += f"=== Up ===\n{output}\n"

    return success, logs


def _get_compose_file(environment: str) -> str:
    """Get the compose file path for an environment."""
    if environment == "prod":
        return f"{settings.compose_project_dir}/docker-compose.prod.yml"
    return f"{settings.compose_project_dir}/docker-compose.dev.yml"


def _run_cmd(cmd: list[str]) -> tuple[bool, str]:
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out (300s)"
    except Exception as e:
        return False, f"Error: {str(e)}"
