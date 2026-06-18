"""Study data access (Postgres; replaces the legacy SQLite ``database`` module).

Returns plain ``dict`` rows shaped exactly like the old SQLite layer so the
service/router contract is unchanged — notably ``upload_date`` (mapped from
``created_at``) and the ``exported`` purge guard.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Study


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
    (per-user visibility); pass ``None`` for the admin/global view."""
    stmt = select(Study).order_by(Study.created_at.desc())
    if owner_id is not None:
        stmt = stmt.where(Study.owner_id == owner_id)
    return [_to_dict(s) for s in await db.scalars(stmt)]


async def mark_exported(db: AsyncSession, study_id: str) -> None:
    """Flag a study as exported so it survives the logout purge."""
    await db.execute(update(Study).where(Study.id == study_id).values(exported=True))


async def update_status(db: AsyncSession, study_id: str, status: str) -> None:
    await db.execute(update(Study).where(Study.id == study_id).values(status=status))


async def purge_user_studies(db: AsyncSession, owner_id: int | None) -> int:
    """Delete a user's not-yet-exported studies (mappings/ontology rows follow
    via ON DELETE CASCADE). Returns the number of studies removed. Used on
    logout so in-progress work isn't preserved unless it was exported."""
    if owner_id is None:
        return 0
    ids = list(
        await db.scalars(
            select(Study.id).where(
                Study.owner_id == owner_id, Study.exported.is_(False)
            )
        )
    )
    if ids:
        await db.execute(delete(Study).where(Study.id.in_(ids)))
    return len(ids)
