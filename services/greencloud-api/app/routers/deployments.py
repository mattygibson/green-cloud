"""Deployment management endpoints."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.db.models import Deployment, DeploymentStatus
from app.models.deployment import DeploymentResponse, DeploymentTrigger
from app.services.builder import run_build_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentResponse])
async def list_deployments(
    limit: int = 20,
    environment: str | None = None,
    db: Session = Depends(get_db),
):
    """List recent deployments, optionally filtered by environment."""
    query = db.query(Deployment).order_by(Deployment.created_at.desc())
    if environment:
        query = query.filter(Deployment.environment == environment)
    return query.limit(limit).all()


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """Get a specific deployment by ID."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(deployment_id: int, db: Session = Depends(get_db)):
    """Get build logs for a specific deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return {
        "deployment_id": deployment.id,
        "status": deployment.status,
        "logs": deployment.build_logs or "No logs available.",
    }


@router.post("/trigger", status_code=202, response_model=DeploymentResponse)
async def trigger_deployment(
    trigger: DeploymentTrigger,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger a deployment (useful for dev environment)."""
    deployment = Deployment(
        environment=trigger.environment,
        status=DeploymentStatus.PENDING,
        branch=trigger.branch,
        commit_sha=trigger.commit_sha,
        repo_url="manual",
        trigger="manual",
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    logger.info(f"Manual deployment {deployment.id} triggered for {trigger.environment}")

    # Trigger build pipeline in background
    background_tasks.add_task(run_build_pipeline, deployment.id, SessionLocal)

    return deployment


@router.delete("/{deployment_id}", status_code=204)
async def cancel_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """Cancel a pending or building deployment."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.status not in (DeploymentStatus.PENDING, DeploymentStatus.BUILDING):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel deployment in '{deployment.status}' state",
        )

    deployment.status = DeploymentStatus.CANCELLED
    db.commit()
    logger.info(f"Deployment {deployment_id} cancelled")
