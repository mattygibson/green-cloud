"""GitHub webhook receiver."""

import asyncio
import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import SessionLocal, get_db
from app.db.models import Deployment, DeploymentStatus
from app.models.deployment import DeploymentResponse
from app.models.webhook import GitHubPushEvent
from app.services.app_deployer import deploy_app
from app.services.builder import determine_environment, run_build_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    received = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@router.post("/webhooks/github", status_code=202, response_model=DeploymentResponse)
async def receive_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """
    Receive and process GitHub push webhooks.

    Validates the webhook signature, determines the target environment,
    creates a deployment record, and triggers the build pipeline.
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify webhook signature
    if not _verify_signature(body, x_hub_signature_256 or "", settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Only process push events
    if x_github_event != "push":
        raise HTTPException(status_code=200, detail=f"Ignoring event: {x_github_event}")

    # Parse payload
    payload = await request.json()
    event = GitHubPushEvent(**payload)

    # Determine target environment from branch
    environment = determine_environment(event.branch)
    if environment is None:
        raise HTTPException(
            status_code=200,
            detail=f"Ignoring push to branch: {event.branch}",
        )

    # Check if this is an external app (not the green-cloud repo itself)
    is_external_app = "green-cloud" not in event.repo_name.lower()

    if is_external_app:
        # External app deployment — use the app deployer
        logger.info(
            f"External app push detected: {event.repo_name} "
            f"(branch: {event.branch}, SHA: {event.commit_sha[:7]})"
        )

        # Only deploy on push to main/prod/master
        if event.branch not in ("main", "prod", "master"):
            raise HTTPException(
                status_code=200,
                detail=f"Ignoring external app push to non-prod branch: {event.branch}",
            )

        # Create deployment record
        deployment = Deployment(
            environment="prod",
            status=DeploymentStatus.PENDING,
            branch=event.branch,
            commit_sha=event.commit_sha,
            repo_url=event.repo_url,
            trigger="webhook",
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)

        # Run external app deploy in background
        background_tasks.add_task(
            _run_external_deploy,
            deployment.id,
            event.repo_url,
            event.repo_name,
            event.commit_sha,
            SessionLocal,
        )

        return deployment

    # Internal green-cloud repo deployment — use the existing build pipeline

    # Create deployment record
    deployment = Deployment(
        environment=environment,
        status=DeploymentStatus.PENDING,
        branch=event.branch,
        commit_sha=event.commit_sha,
        repo_url=event.repo_url,
        trigger="webhook",
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    logger.info(
        f"Deployment {deployment.id} created: "
        f"{event.branch} → {environment} (SHA: {event.commit_sha[:7]})"
    )

    # Trigger build pipeline in background
    background_tasks.add_task(run_build_pipeline, deployment.id, SessionLocal)

    return deployment


async def _run_external_deploy(
    deployment_id: int,
    repo_url: str,
    repo_name: str,
    commit_sha: str,
    db_session_factory,
) -> None:
    """
    Run the external app deployment pipeline in the background.
    Updates the deployment record with status and logs.
    """
    from sqlalchemy.orm import Session

    db: Session = db_session_factory()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            logger.error(f"Deployment {deployment_id} not found")
            return

        # Update status to building
        deployment.status = DeploymentStatus.BUILDING
        deployment.build_logs = f"Starting deployment for {repo_name}...\n"
        db.commit()

        # Run the app deployer
        result = await deploy_app(
            repo_url=repo_url,
            app_name_hint=repo_name.split("/")[-1].lower(),
            commit_sha=commit_sha,
        )

        # Update deployment record with results
        deployment.build_logs += result.get("logs", "")

        if result["status"] == "deployed":
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.build_logs += f"\nDeployed successfully at {result.get('url', '')}\n"
            logger.info(f"Deployment {deployment_id}: {repo_name} deployed successfully")
        else:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = result.get("error", "Unknown error")
            deployment.build_logs += f"\nDeployment failed: {result.get('error', '')}\n"
            logger.error(f"Deployment {deployment_id}: {repo_name} failed: {result.get('error')}")

        db.commit()

    except Exception as e:
        logger.error(f"External deploy error: {e}", exc_info=True)
        if deployment:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            db.commit()
    finally:
        db.close()
