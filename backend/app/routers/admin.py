"""
Admin router (Sprint 3, slice 3) — user management, RBAC-protected.

Every endpoint here requires the ``admin`` role via ``require_role("admin")``,
which demonstrates the role-based access control built in ``app.core.deps``.
When ``AUTH_MODE=none`` the dependency yields a synthetic admin, so these
routes remain reachable for local development.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import ForbiddenError, require_role
from app.core.errors import NotFoundError
from app.db.models import User
from app.db.session import get_db
from app.repositories import sessions as sessions_repo
from app.repositories import users as users_repo
from app.schemas.auth import ActiveUpdate, RoleUpdate, UserOut

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[UserOut]:
    rows = await users_repo.list_users(db)
    return [UserOut.model_validate(u) for u in rows]


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def set_role(
    user_id: int,
    body: RoleUpdate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await users_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")
    if user.id == admin.id and body.role != "admin":
        # Guard against an admin accidentally demoting themselves and locking
        # everyone out; promotion of others is fine.
        raise ForbiddenError("You cannot remove your own admin role.")
    user.role = body.role
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/users/{user_id}/approve-admin", response_model=UserOut)
async def approve_admin_request(
    user_id: int,
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Approve a pending admin-access request: promote the user to admin."""
    user = await users_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")
    user.role = "admin"
    user.admin_requested = False
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/users/{user_id}/reject-admin", response_model=UserOut)
async def reject_admin_request(
    user_id: int,
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Reject a pending admin-access request: clear the flag, keep curator role."""
    user = await users_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")
    user.admin_requested = False
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}/active", response_model=UserOut)
async def set_active(
    user_id: int,
    body: ActiveUpdate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await users_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")
    if user.id == admin.id and not body.is_active:
        raise ForbiddenError("You cannot disable your own account.")
    user.is_active = body.is_active
    if not body.is_active:
        # Disabling an account also ends all of its sessions.
        await sessions_repo.revoke_all_for_user(db, user_id)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/users/{user_id}/logout", status_code=204)
async def force_logout(
    user_id: int,
    _admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Revoke every active session for a user (force sign-out everywhere)."""
    user = await users_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("User not found.")
    await sessions_repo.revoke_all_for_user(db, user_id)
    await db.commit()
