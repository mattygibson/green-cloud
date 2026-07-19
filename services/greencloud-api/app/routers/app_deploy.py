"""Manual app deployment endpoint for triggering deploys without a webhook."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.db.models import Deployment, DeploymentStatus
from app.services.app_deployer import deploy_app

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["App Deploy"])


class AppDeployRequest(BaseModel):
    """Request to deploy an external app."""
    repo_url: str
    branch: str = "main"


class AppDeployResponse(BaseModel):
    deployment_id: int
    status: str
    message: str


@router.post("/deploy-app", response_model=AppDeployResponse, status_code=202)
async def trigger_app_deploy(
    request: AppDeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Manually trigger deployment of an external app.

    Clones the repo, reads greencloud.yml, builds images, and deploys.
    Use this for testing or to deploy apps without GitHub webhooks.
    """
    # Create deployment record
    deployment = Deployment(
        environment="prod",
        status=DeploymentStatus.PENDING,
        branch=request.branch,
        commit_sha="manual",
        repo_url=request.repo_url,
        trigger="manual",
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)

    logger.info(f"Manual app deploy triggered: {request.repo_url}")

    # Run deploy in background
    background_tasks.add_task(
        _run_manual_deploy,
        deployment.id,
        request.repo_url,
        SessionLocal,
    )

    return AppDeployResponse(
        deployment_id=deployment.id,
        status="pending",
        message=f"Deployment started for {request.repo_url}",
    )


async def _run_manual_deploy(
    deployment_id: int,
    repo_url: str,
    db_session_factory,
) -> None:
    """Run manual deployment in background."""
    db: Session = db_session_factory()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            return

        deployment.status = DeploymentStatus.BUILDING
        deployment.build_logs = f"Manual deployment started for {repo_url}...\n"
        db.commit()

        result = await deploy_app(
            repo_url=repo_url,
            commit_sha="manual",
        )

        deployment.build_logs += result.get("logs", "")

        if result["status"] == "deployed":
            deployment.status = DeploymentStatus.DEPLOYED
            deployment.build_logs += f"\nDeployed at {result.get('url', '')}\n"
        else:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = result.get("error", "Unknown error")

        db.commit()

    except Exception as e:
        logger.error(f"Manual deploy error: {e}", exc_info=True)
        if deployment:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            db.commit()
    finally:
        db.close()
