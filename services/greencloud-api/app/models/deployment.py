from datetime import datetime

from pydantic import BaseModel


class DeploymentCreate(BaseModel):
    environment: str
    branch: str
    commit_sha: str
    repo_url: str
    trigger: str = "manual"


class DeploymentResponse(BaseModel):
    id: int
    environment: str
    status: str
    branch: str
    commit_sha: str
    repo_url: str
    trigger: str
    build_logs: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeploymentTrigger(BaseModel):
    """Manual deployment trigger request."""
    environment: str = "dev"
    branch: str = "dev"
    commit_sha: str = "HEAD"
