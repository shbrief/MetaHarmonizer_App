"""Sprint-3 finalization: RBAC is enforced on the curation write routes.

Proves the acceptance-matrix rows: an authenticated curator passes the write
guard (reaching the handler, which 404s on missing data) while an
unauthenticated caller is rejected (401).
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.core.settings as settings_mod
import app.db.session as db_session
from app.db.models import User

from _authflow import register_and_login

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def env(database_url, monkeypatch):
    engine = create_async_engine(database_url, poolclass=sa.pool.NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("dev Postgres not reachable")

    db_session.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    import app.core.redis as redis_mod

    redis_mod._client = None

    domain = f"t{uuid.uuid4().hex[:8]}.example.com"
    monkeypatch.setattr(settings_mod.settings, "allowed_email_domains", domain, raising=False)
    # Avoid network calls to HIBP during tests.
    monkeypatch.setattr(settings_mod.settings, "hibp_check", False, raising=False)

    from fastapi import FastAPI
    from app.core.middleware import install_observability
    from app.routers import admin, auth, mappings

    app = FastAPI()
    install_observability(app)
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(mappings.router)

    def make_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    yield make_client, domain

    async with db_session.SessionLocal() as s:
        await s.execute(sa.delete(User).where(User.email.like(f"%@{domain}")))
        await s.commit()
    await engine.dispose()
    redis_mod._client = None


async def _register(c, email):
    return await register_and_login(c, email)


async def test_curator_allowed_unauth_denied_on_write(env):
    make_client, domain = env
    async with make_client() as c:
        await _register(c, f"admin@{domain}")  # first -> admin
        curator = await _register(c, f"cur@{domain}")  # second -> curator
        curator_h = {"Authorization": f"Bearer {curator['access_token']}"}

        # Curator passes the write guard (handler then 404s on the missing mapping).
        r = await c.post("/api/v1/mappings/999999/accept", headers=curator_h)
        assert r.status_code == 404

        # Unauthenticated is rejected.
        r = await c.post("/api/v1/mappings/999999/accept")
        assert r.status_code == 401
