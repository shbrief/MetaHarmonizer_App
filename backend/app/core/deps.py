"""
Auth dependencies shared across routers.

``current_user`` resolves the Bearer access token to a ``User``. ``require_role``
builds a dependency that additionally enforces a minimum role. When
``AUTH_MODE=none`` (local dev / CI without auth) a synthetic admin user is
returned so protected routes stay reachable.
"""

from __future__ import annotations

import jwt
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_token
from app.core.settings import settings
from app.db.models import User
from app.db.session import get_db
from app.repositories import users as users_repo

# Role hierarchy: higher number = more privilege.
ROLE_RANK = {"viewer": 1, "curator": 2, "admin": 3}


class AuthError(AppError):
    code = "AUTH_FAILED"
    status_code = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


def _dev_admin() -> User:
    """Synthetic user used only when AUTH_MODE=none."""
    return User(
        id=0,
        email="dev@localhost",
        name="Dev (auth disabled)",
        role="admin",
        is_active=True,
        email_verified=True,
    )


async def current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    if settings.auth_mode == "none":
        user = _dev_admin()
        request.state.user_id = user.id
        return user

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    token = auth[7:]
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise AuthError("Invalid or expired token.")
    if payload.get("type") != "access":
        raise AuthError("Wrong token type.")

    user = await users_repo.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("Account not found or disabled.")
    request.state.user_id = user.id
    return user


def require_role(minimum: str):
    """Return a dependency that requires at least ``minimum`` role."""
    threshold = ROLE_RANK[minimum]

    async def _checker(user: User = Depends(current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < threshold:
            raise ForbiddenError(f"Requires '{minimum}' role or higher.")
        return user

    return _checker
