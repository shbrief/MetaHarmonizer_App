"""Schema-version data access (U9).

A schema version is a named, immutable snapshot of the curated-fields CSV. New
studies are stamped with the current version for reproducibility; existing
studies stay pinned to whatever they were harmonized against.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SchemaVersion


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _to_dict(s: SchemaVersion) -> dict:
    return {
        "id": s.id,
        "label": s.label,
        "is_current": s.is_current,
        "source_path": s.source_path,
        "created_at": _iso(s.created_at),
    }


async def list_versions(db: AsyncSession) -> list[dict]:
    rows = (
        await db.execute(select(SchemaVersion).order_by(SchemaVersion.created_at.desc()))
    ).scalars().all()
    return [_to_dict(s) for s in rows]


async def get_current(db: AsyncSession) -> SchemaVersion | None:
    return (
        await db.execute(select(SchemaVersion).where(SchemaVersion.is_current.is_(True)))
    ).scalar_one_or_none()


async def get_by_label(db: AsyncSession, label: str) -> SchemaVersion | None:
    return (
        await db.execute(select(SchemaVersion).where(SchemaVersion.label == label))
    ).scalar_one_or_none()


async def create_version(
    db: AsyncSession, *, label: str, source_path: str, make_current: bool = False
) -> SchemaVersion:
    version = SchemaVersion(label=label, source_path=source_path, is_current=False)
    db.add(version)
    await db.flush()
    if make_current:
        await _set_current(db, version.id)
    return version


async def _set_current(db: AsyncSession, version_id: int) -> None:
    await db.execute(update(SchemaVersion).values(is_current=False))
    await db.execute(
        update(SchemaVersion).where(SchemaVersion.id == version_id).values(is_current=True)
    )


async def promote(db: AsyncSession, version_id: int) -> SchemaVersion | None:
    version = await db.get(SchemaVersion, version_id)
    if not version:
        return None
    await _set_current(db, version_id)
    return version


async def ensure_seed_version(db: AsyncSession, *, source_path: str) -> SchemaVersion:
    """Create the bootstrap ``v1`` version on first run; return the current one."""
    current = await get_current(db)
    if current:
        return current
    existing = await get_by_label(db, "v1")
    if existing:
        await _set_current(db, existing.id)
        await db.commit()
        return existing
    version = await create_version(db, label="v1", source_path=source_path, make_current=True)
    await db.commit()
    return version
