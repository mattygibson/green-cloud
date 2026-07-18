"""Deployment trigger and management endpoints."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models import DeployRequest, DeployResponse
from app.services.deployer import deploy_stack
from app.services.health_checker import check_stack_health

logger = logging.getLogger(__name__)
router = APIRouter()

# Track current deployments
_current_deployments: dict[str, dict] = {}


@router.post("/deploy", response_model=DeployResponse, status_code=202)
async def trigger_deploy(
    request: DeployRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger a deployment for the specified environment.

    Pulls new images and restarts the Docker Compose stack.
    """
    logger.info(
        f"Deploy triggered: env={request.environment}, "
        f"deployment_id={request.deployment_id}"
    )

    # Store deployment state
    _current_deployments[request.deployment_id] = {
        "environment": request.environment,
        "status": "deploying",
        "images": request.images,
    }

    # Run deployment in background
    background_tasks.add_task(
        _run_deployment,
        request.deployment_id,
        request.environment,
        request.images,
    )

    return DeployResponse(
        deployment_id=request.deployment_id,
        status="deploying",
        message=f"Deployment started for {request.environment}",
    )


@router.get("/deploy/{deployment_id}")
async def get_deploy_status(deployment_id: str):
    """Get the status of a deployment."""
    if deployment_id not in _current_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return _current_deployments[deployment_id]


async def _run_deployment(
    deployment_id: str,
    environment: str,
    images: dict[str, str],
) -> None:
    """Execute deployment: pull images, restart stack, verify health."""
    try:
        # Step 1: Deploy (pull + restart)
        logger.info(f"[{deployment_id}] Pulling and restarting {environment} stack")
        success, logs = await deploy_stack(environment, images)

        if not success:
            _current_deployments[deployment_id]["status"] = "failed"
            _current_deployments[deployment_id]["error"] = logs
            logger.error(f"[{deployment_id}] Deploy failed: {logs}")
            return

        # Step 2: Health check
        logger.info(f"[{deployment_id}] Running health checks")
        healthy = await check_stack_health(environment)

        if healthy:
            _current_deployments[deployment_id]["status"] = "deployed"
            logger.info(f"[{deployment_id}] Deployment successful")
        else:
            _current_deployments[deployment_id]["status"] = "unhealthy"
            logger.warning(f"[{deployment_id}] Health checks failed")
            # TODO: trigger rollback

    except Exception as e:
        _current_deployments[deployment_id]["status"] = "failed"
        _current_deployments[deployment_id]["error"] = str(e)
        logger.error(f"[{deployment_id}] Deployment error: {e}")
