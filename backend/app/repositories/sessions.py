"""Session (refresh-token) data access (Sprint 3, slice 2).

A row in ``sessions`` is the server-side record of a refresh token. Revocation
is done here — deleting/blanking a session immediately invalidates its refresh
token regardless of the JWT's own expiry.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session


async def create_session(
    db: AsyncSession,
    *,
    user_id: int,
    refresh_jti: str,
    ip: str | None,
    user_agent: str | None,
) -> Session:
    session = Session(
        user_id=user_id,
        refresh_jti=refresh_jti,
        ip=ip,
        user_agent=user_agent,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return session


async def get_active_by_jti(db: AsyncSession, jti: str) -> Session | None:
    stmt = select(Session).where(Session.refresh_jti == jti, Session.revoked_at.is_(None))
    return await db.scalar(stmt)


async def list_for_user(db: AsyncSession, user_id: int) -> list[Session]:
    stmt = (
        select(Session)
        .where(Session.user_id == user_id, Session.revoked_at.is_(None))
        .order_by(Session.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def touch(db: AsyncSession, session: Session) -> None:
    session.last_seen = datetime.now(timezone.utc)
    await db.flush()


async def revoke(db: AsyncSession, *, user_id: int, session_id: int) -> bool:
    """Revoke one session owned by ``user_id``. Returns True if a row changed."""
    stmt = (
        update(Session)
        .where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    return result.rowcount > 0


async def revoke_by_jti(db: AsyncSession, jti: str) -> None:
    stmt = (
        update(Session)
        .where(Session.refresh_jti == jti, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)


async def revoke_all_for_user(db: AsyncSession, user_id: int) -> int:
    """Force-logout: revoke every live session for a user. Returns count."""
    stmt = (
        update(Session)
        .where(Session.user_id == user_id, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    return result.rowcount
