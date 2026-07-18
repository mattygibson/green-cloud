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
