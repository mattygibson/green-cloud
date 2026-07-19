"""Build orchestration — triggers Docker builds and pushes to registry."""

import asyncio
import logging
import subprocess

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Deployment, DeploymentStatus
from app.services.wol import check_build_server_health, wake_build_server

logger = logging.getLogger(__name__)


def _determine_environment(branch: str) -> str | None:
    """Map a git branch to a deployment environment."""
    if branch in ("main", "prod", "master"):
        return "prod"
    elif branch == "dev":
        return "dev"
    return None


def _run_build(
    registry: str,
    platform: str,
    service_path: str,
    tag: str,
    sha_tag: str,
) -> tuple[bool, str]:
    """
    Run docker buildx build for a service.
    Returns (success, logs).
    """
    image_name = f"{registry}/greencloud/{service_path.split('/')[-1]}:{tag}"
    image_sha = f"{registry}/greencloud/{service_path.split('/')[-1]}:{sha_tag}"

    cmd = [
        "docker", "buildx", "build",
        "--platform", platform,
        "-t", image_name,
        "-t", image_sha,
        "--push",
        service_path,
    ]

    logger.info(f"Building: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )
        logs = result.stdout + result.stderr
        if result.returncode != 0:
            logger.error(f"Build failed: {logs}")
            return False, logs
        logger.info(f"Build succeeded: {image_name}")
        return True, logs
    except subprocess.TimeoutExpired:
        return False, "Build timed out after 600 seconds"
    except Exception as e:
        return False, f"Build error: {str(e)}"


async def run_build_pipeline(deployment_id: int, db_session_factory) -> None:
    """
    Execute the full build pipeline for a deployment.

    This runs asynchronously after the webhook returns 202.
    """
    db: Session = db_session_factory()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            logger.error(f"Deployment {deployment_id} not found")
            return

        # Update status to building
        deployment.status = DeploymentStatus.BUILDING
        deployment.build_logs = "Starting build pipeline...\n"
        db.commit()

        # Step 1: Wake build server (stub for local dev)
        deployment.build_logs += "Waking build server...\n"
        db.commit()
        await wake_build_server()

        # Step 2: Check build server health
        deployment.build_logs += "Checking build server health...\n"
        db.commit()
        healthy = await check_build_server_health()
        if not healthy:
            deployment.status = DeploymentStatus.BUILD_FAILED
            deployment.error_message = "Build server unreachable"
            deployment.build_logs += "ERROR: Build server unreachable\n"
            db.commit()
            return

        # Step 3: Build API service
        deployment.build_logs += f"Building API (platform: {settings.build_platform})...\n"
        db.commit()

        success, logs = await asyncio.to_thread(
            _run_build,
            settings.build_registry_host,
            settings.build_platform,
            "/workspace/services/app/api",
            deployment.environment,
            deployment.commit_sha[:7],
        )
        deployment.build_logs += logs + "\n"
        if not success:
            deployment.status = DeploymentStatus.BUILD_FAILED
            deployment.error_message = "API build failed"
            db.commit()
            return

        # Step 4: Build UI service
        deployment.build_logs += f"Building UI (platform: {settings.build_platform})...\n"
        db.commit()

        success, logs = await asyncio.to_thread(
            _run_build,
            settings.build_registry_host,
            settings.build_platform,
            "/workspace/services/app/ui",
            deployment.environment,
            deployment.commit_sha[:7],
        )
        deployment.build_logs += logs + "\n"
        if not success:
            deployment.status = DeploymentStatus.BUILD_FAILED
            deployment.error_message = "UI build failed"
            db.commit()
            return

        # Step 5: Mark as built
        deployment.status = DeploymentStatus.BUILT
        deployment.build_logs += "Build complete. Ready for deployment.\n"
        db.commit()

        logger.info(f"Deployment {deployment_id} built successfully")

    except Exception as e:
        logger.error(f"Build pipeline error: {e}")
        if deployment:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            db.commit()
    finally:
        db.close()


def determine_environment(branch: str) -> str | None:
    """Public wrapper for branch → environment mapping."""
    return _determine_environment(branch)
