"""Slice-3 tests: RBAC role enforcement, admin user management, AUTH_MODE=none."""

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
    monkeypatch.setattr(settings_mod.settings, "hibp_check", False, raising=False)

    from fastapi import FastAPI
    from app.core.middleware import install_observability
    from app.routers import admin, auth

    def build_app() -> FastAPI:
        app = FastAPI()
        install_observability(app)
        app.include_router(auth.router)
        app.include_router(admin.router)
        return app

    def make_client(app) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    yield build_app, make_client, domain

    async with db_session.SessionLocal() as s:
        await s.execute(sa.delete(User).where(User.email.like(f"%@{domain}")))
        await s.commit()
    await engine.dispose()
    redis_mod._client = None


async def _register(c, email, pw="pw-123456"):
    r = await c.post("/api/v1/auth/register", json={"email": email, "password": pw})
    return r.json()


async def test_admin_can_list_users(env):
    build_app, make_client, domain = env
    app = build_app()
    async with make_client(app) as c:
        admin = await _register(c, f"admin@{domain}")  # first user -> admin
        assert admin["user"]["role"] == "admin"
        r = await c.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
        )
        assert r.status_code == 200
        assert any(u["email"] == f"admin@{domain}" for u in r.json())


async def test_curator_forbidden(env):
    build_app, make_client, domain = env
    app = build_app()
    async with make_client(app) as c:
        await _register(c, f"admin@{domain}")  # first -> admin
        curator = await _register(c, f"cur@{domain}")  # second -> curator
        assert curator["user"]["role"] == "curator"
        r = await c.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {curator['access_token']}"},
        )
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"


async def test_admin_can_change_role(env):
    build_app, make_client, domain = env
    app = build_app()
    async with make_client(app) as c:
        admin = await _register(c, f"admin@{domain}")
        curator = await _register(c, f"cur@{domain}")
        headers = {"Authorization": f"Bearer {admin['access_token']}"}
        uid = curator["user"]["id"]
        r = await c.patch(f"/api/v1/admin/users/{uid}/role", json={"role": "admin"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"


async def test_admin_cannot_self_demote(env):
    build_app, make_client, domain = env
    app = build_app()
    async with make_client(app) as c:
        admin = await _register(c, f"admin@{domain}")
        headers = {"Authorization": f"Bearer {admin['access_token']}"}
        uid = admin["user"]["id"]
        r = await c.patch(f"/api/v1/admin/users/{uid}/role", json={"role": "curator"}, headers=headers)
        assert r.status_code == 403


async def test_disable_account_revokes_sessions(env):
    build_app, make_client, domain = env
    app = build_app()
    async with make_client(app) as c:
        admin = await _register(c, f"admin@{domain}")
        # Victim logs in on their own client (gets a refresh session).
        async with make_client(app) as c2:
            victim = await _register(c2, f"vic@{domain}")
            headers = {"Authorization": f"Bearer {admin['access_token']}"}
            uid = victim["user"]["id"]
            r = await c.patch(
                f"/api/v1/admin/users/{uid}/active", json={"is_active": False}, headers=headers
            )
            assert r.status_code == 200
            # Victim's refresh now fails (sessions revoked + account disabled).
            r = await c2.post("/api/v1/auth/refresh")
            assert r.status_code == 401


async def test_auth_mode_none_grants_admin(env, monkeypatch):
    build_app, make_client, domain = env
    monkeypatch.setattr(settings_mod.settings, "auth_mode", "none", raising=False)
    app = build_app()
    async with make_client(app) as c:
        # No token at all, but AUTH_MODE=none yields a synthetic admin.
        r = await c.get("/api/v1/admin/users")
        assert r.status_code == 200
