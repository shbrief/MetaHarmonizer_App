"""Retention job tests (spec §6.8).

The directory-purge logic is tested in isolation with a temp dir (no DB needed);
a separate test exercises the revoked-session purge against the dev Postgres.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.db.session as db_session
from app.db.models import Session as SessionModel, User
from app.workers.retention import _purge_dir, _purge_revoked_sessions


def test_purge_dir_removes_only_aged_files(tmp_path):
    old = tmp_path / "old.csv"
    new = tmp_path / "new.csv"
    old.write_text("x")
    new.write_text("y")
    # Backdate "old" by 100 days.
    century = time.time() - 100 * 86400
    os.utime(old, (century, century))

    purged = _purge_dir(tmp_path, older_than_days=90, dry_run=False)
    assert purged == 1
    assert not old.exists()
    assert new.exists()


def test_purge_dir_noop_when_missing(tmp_path):
    assert _purge_dir(tmp_path / "nope", older_than_days=90, dry_run=False) == 0


def test_purge_dir_dry_run_keeps_files(tmp_path):
    f = tmp_path / "old.csv"
    f.write_text("x")
    century = time.time() - 100 * 86400
    os.utime(f, (century, century))
    assert _purge_dir(tmp_path, older_than_days=90, dry_run=True) == 1
    assert f.exists()  # dry-run didn't delete


@pytest.mark.asyncio
async def test_purge_revoked_sessions(database_url):
    engine = create_async_engine(database_url, poolclass=sa.pool.NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("dev Postgres not reachable")

    db_session.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    email = f"ret_{uuid.uuid4().hex[:8]}@example.com"
    async with db_session.SessionLocal() as s:
        user = User(email=email, role="curator")
        s.add(user)
        await s.flush()
        # One old revoked session, one recent revoked session.
        s.add(SessionModel(
            user_id=user.id, refresh_jti=uuid.uuid4().hex,
            revoked_at=sa.func.now() - sa.text("interval '100 days'"),
        ))
        s.add(SessionModel(
            user_id=user.id, refresh_jti=uuid.uuid4().hex,
            revoked_at=sa.func.now(),
        ))
        await s.commit()
        uid = user.id

    purged = await _purge_revoked_sessions(90, dry_run=False)
    assert purged >= 1  # the 100-day-old one is gone

    async with db_session.SessionLocal() as s:
        remaining = await s.scalar(
            sa.select(sa.func.count()).select_from(SessionModel).where(SessionModel.user_id == uid)
        )
        assert remaining == 1  # recent revoked session survives
        # cleanup
        await s.execute(sa.delete(SessionModel).where(SessionModel.user_id == uid))
        await s.execute(sa.delete(User).where(User.id == uid))
        await s.commit()

    await engine.dispose()
