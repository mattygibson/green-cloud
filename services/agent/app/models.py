from pydantic import BaseModel


class DeployRequest(BaseModel):
    environment: str  # "prod" or "dev"
    deployment_id: str
    images: dict[str, str]  # service_name → image reference
    rollback_to: str | None = None


class DeployResponse(BaseModel):
    deployment_id: str
    status: str
    message: str
