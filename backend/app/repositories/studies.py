"""Study data access (Postgres; replaces the legacy SQLite ``database`` module).

Returns plain ``dict`` rows shaped exactly like the old SQLite layer so the
service/router contract is unchanged — notably ``upload_date`` (mapped from
``created_at``) and the ``exported`` purge guard.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Study

# A study with no explicit "completed" mark is treated as scratch work and is
# deleted once it's older than this, lazily on the owner's next list/overview.
IDLE_STUDY_DAYS = 7


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _to_dict(s: Study) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "upload_date": _iso(s.created_at),
        "status": s.status,
        "file_path": s.file_path,
        "row_count": s.row_count,
        "column_count": s.column_count,
        "owner_id": s.owner_id,
        "exported": s.exported,
    }


async def create_study(
    db: AsyncSession,
    *,
    study_id: str,
    name: str,
    file_path: str,
    row_count: int,
    column_count: int,
    owner_id: int | None = None,
) -> dict:
    study = Study(
        id=study_id,
        name=name,
        status="pending",
        file_path=file_path,
        row_count=row_count,
        column_count=column_count,
        owner_id=owner_id,
    )
    db.add(study)
    await db.flush()
    await db.refresh(study)
    return _to_dict(study)


async def get_study(db: AsyncSession, study_id: str) -> dict | None:
    s = await db.get(Study, study_id)
    return _to_dict(s) if s else None


async def list_studies(db: AsyncSession, owner_id: int | None = None) -> list[dict]:
    """List studies. When ``owner_id`` is given, return only that user's studies
    (per-user visibility); pass ``None`` for the global view.

    Lazily enforces the idle-expiry policy first: a user's studies older than
    ``IDLE_STUDY_DAYS`` are deleted unless they were marked ``completed`` (an
    explicit "keep this" signal). Cleanup runs on the owner's own list/overview
    load, so no scheduler is required for it to take effect."""
    if owner_id is not None:
        await purge_idle_studies(db, owner_id)
    stmt = select(Study).order_by(Study.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Study.owner_id == owner_id)
    return [_to_dict(s) for s in await db.scalars(stmt)]


async def mark_exported(db: AsyncSession, study_id: str) -> None:
    """Flag a study as exported. Purely informational now (studies persist until
    the user deletes them or they idle-expire); kept so exports are recorded."""
    await db.execute(update(Study).where(Study.id == study_id).values(exported=True))


async def update_status(db: AsyncSession, study_id: str, status: str) -> None:
    await db.execute(update(Study).where(Study.id == study_id).values(status=status))


async def mark_completed(db: AsyncSession, study_id: str) -> dict | None:
    """Mark a study ``completed`` — a "keep this" signal that also exempts it
    from idle-expiry. The study stays fully viewable and exportable."""
    s = await db.get(Study, study_id)
    if not s:
        return None
    s.status = "completed"
    await db.flush()
    return _to_dict(s)


async def delete_study(db: AsyncSession, study_id: str) -> bool:
    """Delete one study (mappings/ontology rows follow via ON DELETE CASCADE).
    Returns True if a row was removed. Ownership is enforced by the caller."""
    res = await db.execute(delete(Study).where(Study.id == study_id))
    return (res.rowcount or 0) > 0


async def purge_idle_studies(db: AsyncSession, owner_id: int) -> int:
    """Delete a user's studies older than ``IDLE_STUDY_DAYS`` that were never
    marked ``completed``. Returns the number removed."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=IDLE_STUDY_DAYS)
    res = await db.execute(
        delete(Study).where(
            Study.owner_id == owner_id,
            Study.status != "completed",
            Study.created_at < cutoff,
        )
    )
    return res.rowcount or 0
