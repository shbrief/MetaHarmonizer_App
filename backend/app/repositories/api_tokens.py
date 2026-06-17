"""API-token data access (Sprint 3, slice 4).

Tokens are personal access credentials for programmatic/CLI use. Only the
SHA-256 hash is stored; the plaintext is shown to the user exactly once at
creation. ``scope`` is ``read`` or ``write``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiToken


async def create_token(
    db: AsyncSession, *, user_id: int, token_hash: str, scope: str
) -> ApiToken:
    token = ApiToken(user_id=user_id, token_hash=token_hash, scope=scope)
    db.add(token)
    await db.flush()
    return token


async def get_active_by_hash(db: AsyncSession, token_hash: str) -> ApiToken | None:
    stmt = select(ApiToken).where(
        ApiToken.token_hash == token_hash, ApiToken.revoked_at.is_(None)
    )
    return await db.scalar(stmt)


async def list_for_user(db: AsyncSession, user_id: int) -> list[ApiToken]:
    stmt = (
        select(ApiToken)
        .where(ApiToken.user_id == user_id, ApiToken.revoked_at.is_(None))
        .order_by(ApiToken.created_at.desc())
    )
    return list(await db.scalars(stmt))


async def revoke(db: AsyncSession, *, user_id: int, token_id: int) -> bool:
    stmt = (
        update(ApiToken)
        .where(
            ApiToken.id == token_id,
            ApiToken.user_id == user_id,
            ApiToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    result = await db.execute(stmt)
    return result.rowcount > 0
