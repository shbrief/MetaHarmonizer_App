"""Sprint-3 finalization: RBAC is enforced on the curation write routes.

Proves the acceptance-matrix rows: a viewer is denied writes (403) while a
curator passes the guard (reaching the handler, which 404s on missing data).
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
    r = await c.post("/api/v1/auth/register", json={"email": email, "password": "pw-123456"})
    return r.json()


async def test_viewer_denied_curator_allowed_on_write(env):
    make_client, domain = env
    async with make_client() as c:
        admin = await _register(c, f"admin@{domain}")  # first -> admin
        curator = await _register(c, f"cur@{domain}")  # second -> curator
        admin_h = {"Authorization": f"Bearer {admin['access_token']}"}

        # Demote a third user to viewer via the admin API.
        viewer = await _register(c, f"vw@{domain}")
        vid = viewer["user"]["id"]
        await c.patch(f"/api/v1/admin/users/{vid}/role", json={"role": "viewer"}, headers=admin_h)
        # Re-login the viewer so the new role is in their token.
        vlogin = await c.post("/api/v1/auth/login", json={"email": f"vw@{domain}", "password": "pw-123456"})
        viewer_h = {"Authorization": f"Bearer {vlogin.json()['access_token']}"}
        curator_h = {"Authorization": f"Bearer {curator['access_token']}"}

        # Viewer is forbidden from writing.
        r = await c.post("/api/v1/mappings/999999/accept", headers=viewer_h)
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"

        # Curator passes the guard (handler then 404s on the missing mapping).
        r = await c.post("/api/v1/mappings/999999/accept", headers=curator_h)
        assert r.status_code == 404

        # Unauthenticated is rejected too.
        r = await c.post("/api/v1/mappings/999999/accept")
        assert r.status_code == 401
