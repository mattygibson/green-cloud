from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class DeploymentStatus:
    PENDING = "pending"
    BUILDING = "building"
    BUILT = "built"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    BUILD_FAILED = "build_failed"
    CANCELLED = "cancelled"


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    environment = Column(String(20), nullable=False)  # "prod" or "dev"
    status = Column(String(20), nullable=False, default=DeploymentStatus.PENDING)
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(40), nullable=False)
    repo_url = Column(String(500), nullable=False)
    trigger = Column(String(20), nullable=False, default="webhook")  # "webhook" or "manual"
    build_logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
