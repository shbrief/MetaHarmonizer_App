"""
Reusable column mixins.

- TimestampMixin     : created_at / updated_at (server-side UTC, auto-updated).
- OptimisticVersionMixin : version column for optimistic concurrency (spec §6.2).
                       Every UPDATE bumps version; a stale UPDATE affects 0 rows
                       and the service layer turns that into HTTP 409.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OptimisticVersionMixin:
    """Adds a ``version`` column for optimistic concurrency.

    The repository layer performs ``UPDATE ... SET version = version + 1
    WHERE id = :id AND version = :expected`` and treats a 0-row result as a
    409 Conflict. Kept explicit (per spec §6.2) rather than SQLAlchemy's
    implicit ``version_id_col`` so the conflict is easy to surface in the API.
    """

    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
