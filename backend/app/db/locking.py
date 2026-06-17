"""
Optimistic-locking helper (spec §6.2).

``versioned_update`` runs an UPDATE guarded by the caller's expected version and
bumps the version atomically. If no row matches (someone else changed it, or it
was deleted), it raises ``ConflictError`` → HTTP 409, carrying the current row's
version in ``details`` so the UI can show a "reload?" prompt.

    await versioned_update(
        db, Mapping, id_=mapping_id, expected_version=6,
        values={"status": "accepted", "curator_field": "SEX"},
    )
"""

from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def versioned_update(
    db: AsyncSession,
    model: type[ModelT],
    *,
    id_: Any,
    expected_version: int,
    values: dict[str, Any],
) -> ModelT:
    """Update one row only if its ``version`` matches ``expected_version``.

    Bumps ``version`` by 1 on success. Raises:
      - ``NotFoundError`` if the row id doesn't exist at all,
      - ``ConflictError`` if it exists but at a different version.
    """
    pk = model.__mapper__.primary_key[0]

    stmt = (
        update(model)
        .where(pk == id_, model.version == expected_version)
        .values(**values, version=model.version + 1)
        .returning(model)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if row is not None:
        await db.commit()
        return row

    # No row updated — distinguish "missing" from "stale version".
    current = await db.scalar(select(model).where(pk == id_))
    if current is None:
        raise NotFoundError(f"{model.__tablename__} {id_} not found")

    raise ConflictError(
        f"{model.__tablename__} was modified by another user.",
        details={"current_version": current.version, "your_version": expected_version},
    )
