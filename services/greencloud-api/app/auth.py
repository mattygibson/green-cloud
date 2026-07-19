"""API key authentication middleware."""

import hashlib
import hmac
import json
import logging
import time
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)

# Roles
ROLE_ADMIN = "admin"
ROLE_DEPLOYER = "deployer"
ROLE_VIEWER = "viewer"

# Role hierarchy: admin > deployer > viewer
ROLE_HIERARCHY = {ROLE_ADMIN: 3, ROLE_DEPLOYER: 2, ROLE_VIEWER: 1}

# Keys storage (file-based for simplicity)
KEYS_FILE = Path("/app/data/api_keys.json")


def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def _load_keys() -> list[dict]:
    """Load API keys from storage."""
    if not KEYS_FILE.exists():
        return []
    try:
        return json.loads(KEYS_FILE.read_text())
    except Exception:
        return []


def _save_keys(keys: list[dict]) -> None:
    """Save API keys to storage."""
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text(json.dumps(keys, indent=2))


def create_api_key(name: str, role: str, key_value: str) -> dict:
    """Create a new API key."""
    if role not in ROLE_HIERARCHY:
        raise ValueError(f"Invalid role: {role}. Must be one of: {list(ROLE_HIERARCHY.keys())}")

    keys = _load_keys()
    new_key = {
        "name": name,
        "key_hash": _hash_key(key_value),
        "role": role,
        "created_at": time.time(),
        "last_used": None,
    }
    keys.append(new_key)
    _save_keys(keys)
    return new_key


def list_api_keys() -> list[dict]:
    """List all API keys (without hashes)."""
    keys = _load_keys()
    return [
        {
            "name": k["name"],
            "role": k["role"],
            "created_at": k["created_at"],
            "last_used": k.get("last_used"),
        }
        for k in keys
    ]


def delete_api_key(name: str) -> bool:
    """Delete an API key by name."""
    keys = _load_keys()
    new_keys = [k for k in keys if k["name"] != name]
    if len(new_keys) == len(keys):
        return False
    _save_keys(new_keys)
    return True


def validate_key(key_value: str) -> dict | None:
    """Validate an API key and return its info."""
    key_hash = _hash_key(key_value)
    keys = _load_keys()
    for k in keys:
        if hmac.compare_digest(k["key_hash"], key_hash):
            # Update last_used
            k["last_used"] = time.time()
            _save_keys(keys)
            return k
    return None


def has_role(required_role: str, actual_role: str) -> bool:
    """Check if actual_role meets or exceeds required_role."""
    return ROLE_HIERARCHY.get(actual_role, 0) >= ROLE_HIERARCHY.get(required_role, 99)


async def get_current_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)] = None,
) -> dict | None:
    """Extract and validate API key from request. Returns None if no auth configured."""
    # If no keys exist yet, allow unauthenticated access (first-run setup)
    keys = _load_keys()
    if not keys:
        return {"name": "setup", "role": ROLE_ADMIN}

    if credentials is None:
        raise HTTPException(status_code=401, detail="API key required")

    key_info = validate_key(credentials.credentials)
    if key_info is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return key_info


def require_role(role: str):
    """Dependency that requires a minimum role."""

    async def _check(
        key_info: Annotated[dict | None, Depends(get_current_key)],
    ) -> dict:
        if key_info is None:
            raise HTTPException(status_code=401, detail="API key required")
        if not has_role(role, key_info["role"]):
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {role}. Your role: {key_info['role']}",
            )
        return key_info

    return _check
