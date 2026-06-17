"""Persistence contract tests against the dev Postgres.

Covers:
  - audit_events is append-only (UPDATE/DELETE raise) — G4 / spec §4.3
  - optimistic locking returns a conflict on a stale version — spec §6.2

Skipped automatically if the dev Postgres is not reachable.
"""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.errors import ConflictError, NotFoundError
from app.db.locking import versioned_update
from app.db.models import AuditEvent, Study

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def session(database_url):
    engine = create_async_engine(database_url, poolclass=sa.pool.NullPool)
    # Skip the whole module's DB tests if Postgres isn't up.
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("dev Postgres not reachable (run scripts/dev_services.ps1 start)")

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_audit_events_append_only(session):
    # INSERT allowed
    evt = AuditEvent(action="unit_test_insert")
    session.add(evt)
    await session.commit()
    evt_id = evt.id  # capture as plain int before any failed txn expires the ORM state

    # UPDATE blocked by the trigger
    with pytest.raises(DBAPIError):
        await session.execute(
            sa.text("UPDATE audit_events SET action='x' WHERE id=:i"), {"i": evt_id}
        )
    await session.rollback()

    # DELETE blocked by the trigger
    with pytest.raises(DBAPIError):
        await session.execute(
            sa.text("DELETE FROM audit_events WHERE id=:i"), {"i": evt_id}
        )
    await session.rollback()

    # The row is still there (immutable)
    still = await session.scalar(
        sa.select(AuditEvent.action).where(AuditEvent.id == evt_id)
    )
    assert still == "unit_test_insert"


async def test_optimistic_locking_conflict_and_success(session):
    study_id = f"test_{uuid.uuid4().hex[:8]}"
    session.add(Study(id=study_id, name="lock test", status="pending"))
    await session.commit()

    # Stale version -> ConflictError with current/your versions in details
    with pytest.raises(ConflictError) as ei:
        await versioned_update(
            session, Study, id_=study_id, expected_version=999,
            values={"status": "harmonized"},
        )
    assert ei.value.details["current_version"] == 1
    assert ei.value.details["your_version"] == 999

    # Correct version -> succeeds and bumps version
    updated = await versioned_update(
        session, Study, id_=study_id, expected_version=1,
        values={"status": "harmonized"},
    )
    assert updated.version == 2
    assert updated.status == "harmonized"

    # Missing id -> NotFoundError
    with pytest.raises(NotFoundError):
        await versioned_update(
            session, Study, id_="does_not_exist", expected_version=1,
            values={"status": "x"},
        )

    # cleanup
    await session.execute(sa.delete(Study).where(Study.id == study_id))
    await session.commit()
