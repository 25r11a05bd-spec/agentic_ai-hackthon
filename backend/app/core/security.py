from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx
from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings

try:
    import jwt
except ImportError:  # pragma: no cover
    jwt = None


Role = Literal["admin", "operator", "viewer"]


@dataclass(slots=True)
class AuthenticatedUser:
    user_id: str
    role: Role
    email: str | None = None


async def _decode_clerk_token(token: str) -> dict:
    settings = get_settings()
    if jwt is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PyJWT is not installed; Clerk token verification is unavailable.",
        )
    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clerk JWKS URL is not configured.",
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        jwks = (await client.get(settings.clerk_jwks_url)).json()

    header = jwt.get_unverified_header(token)
    key_id = header.get("kid")
    matching_key = next((item for item in jwks["keys"] if item["kid"] == key_id), None)
    if not matching_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signing key.")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_key)
    return jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_aud": False})


async def get_current_user(
    authorization: str | None = Header(default=None),
    x_demo_role: str | None = Header(default=None),
    x_demo_user: str | None = Header(default=None),
) -> AuthenticatedUser:
    settings = get_settings()

    if settings.auth_dev_mode:
        return AuthenticatedUser(
            user_id=x_demo_user or "dev-admin",
            role=(x_demo_role or "admin"),  # type: ignore[arg-type]
            email="dev@local",
        )

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    token = authorization.split(" ", 1)[1]
    payload = await _decode_clerk_token(token)
    public_metadata = payload.get("public_metadata", {})
    role = public_metadata.get("role", "viewer")
    return AuthenticatedUser(
        user_id=payload.get("sub", "unknown"),
        role=role,  # type: ignore[arg-type]
        email=payload.get("email"),
    )


def require_role(*allowed: Role):
    async def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role `{user.role}` cannot access this resource.",
            )
        return user

    dependency.allowed_roles = allowed  # type: ignore[attr-defined]
    return dependency
