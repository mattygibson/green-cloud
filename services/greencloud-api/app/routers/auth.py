"""Auth management endpoints."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import (
    ROLE_ADMIN,
    create_api_key,
    delete_api_key,
    list_api_keys,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class CreateKeyRequest(BaseModel):
    name: str
    role: str = "viewer"


class CreateKeyResponse(BaseModel):
    name: str
    role: str
    key: str  # Only shown once at creation time


@router.post("/keys", response_model=CreateKeyResponse)
async def create_key(
    request: CreateKeyRequest,
    _: Annotated[dict, Depends(require_role(ROLE_ADMIN))],
):
    """Create a new API key (admin only). The key is only shown once."""
    key_value = secrets.token_urlsafe(32)
    create_api_key(request.name, request.role, key_value)
    return CreateKeyResponse(name=request.name, role=request.role, key=key_value)


@router.get("/keys")
async def list_keys(
    _: Annotated[dict, Depends(require_role(ROLE_ADMIN))],
):
    """List all API keys (admin only)."""
    return list_api_keys()


@router.delete("/keys/{name}")
async def revoke_key(
    name: str,
    _: Annotated[dict, Depends(require_role(ROLE_ADMIN))],
):
    """Revoke an API key by name (admin only)."""
    if not delete_api_key(name):
        raise HTTPException(status_code=404, detail=f"Key '{name}' not found")
    return {"message": f"Key '{name}' revoked"}


@router.get("/me")
async def get_me(
    key_info: Annotated[dict, Depends(require_role("viewer"))],
):
    """Get current key info and permissions."""
    return {
        "name": key_info["name"],
        "role": key_info["role"],
    }
