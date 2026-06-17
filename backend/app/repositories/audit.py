"""
Audit repository — read access to the append-only audit log (U11).

Cursor pagination orders by (id DESC) — id is monotonic, so the cursor is just
the last seen id. Filters by study/action/actor are optional and composable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent


async def list_audit_events(
    db: AsyncSession,
    *,
    study_id: str | None = None,
    action: str | None = None,
    actor_id: int | None = None,
    before_id: int | None = None,
    limit: int = 50,
) -> list[AuditEvent]:
    """Return up to ``limit + 1`` events newest-first (the extra row signals a
    next page to the pagination helper)."""
    stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit + 1)

    if study_id is not None:
        stmt = stmt.where(AuditEvent.study_id == study_id)
    if action is not None:
        stmt = stmt.where(AuditEvent.action == action)
    if actor_id is not None:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)
    if before_id is not None:
        stmt = stmt.where(AuditEvent.id < before_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())
