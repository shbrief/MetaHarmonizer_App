"""Slice-4 tests: personal API tokens (create once, authenticate, scope, revoke)."""

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
    monkeypatch.setattr(settings_mod.settings, "hibp_check", False, raising=False)

    from fastapi import FastAPI
    from app.core.middleware import install_observability
    from app.routers import auth, tokens

    app = FastAPI()
    install_observability(app)
    app.include_router(auth.router)
    app.include_router(tokens.router)

    def make_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    yield make_client, domain

    async with db_session.SessionLocal() as s:
        await s.execute(sa.delete(User).where(User.email.like(f"%@{domain}")))
        await s.commit()
    await engine.dispose()
    redis_mod._client = None


async def _register(c, email, pw="pw-123456"):
    return await register_and_login(c, email, pw)


async def test_create_list_and_use_token(env):
    make_client, domain = env
    async with make_client() as c:
        reg = await _register(c, f"tok@{domain}")
        jwt_headers = {"Authorization": f"Bearer {reg['access_token']}"}

        # Create a write token (plaintext returned once).
        r = await c.post("/api/v1/tokens", json={"scope": "write"}, headers=jwt_headers)
        assert r.status_code == 201
        created = r.json()
        assert created["token"].startswith("mh_")
        assert created["scope"] == "write"
        plaintext = created["token"]

        # It authenticates /me just like a JWT.
        r = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {plaintext}"})
        # /me lives in the auth router which this app also mounts.
        assert r.status_code == 200
        assert r.json()["email"] == f"tok@{domain}"

        # Listing shows the token but never the plaintext.
        r = await c.get("/api/v1/tokens", headers=jwt_headers)
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 1
        assert "token" not in rows[0]


async def test_revoked_token_rejected(env):
    make_client, domain = env
    async with make_client() as c:
        reg = await _register(c, f"rev@{domain}")
        jwt_headers = {"Authorization": f"Bearer {reg['access_token']}"}
        created = (await c.post("/api/v1/tokens", json={"scope": "read"}, headers=jwt_headers)).json()
        tid, plaintext = created["id"], created["token"]

        # Works before revocation.
        r = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {plaintext}"})
        assert r.status_code == 200

        # Revoke, then it must fail.
        r = await c.delete(f"/api/v1/tokens/{tid}", headers=jwt_headers)
        assert r.status_code == 204
        r = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {plaintext}"})
        assert r.status_code == 401


async def test_bad_token_rejected(env):
    make_client, domain = env
    async with make_client() as c:
        r = await c.get("/api/v1/auth/me", headers={"Authorization": "Bearer mh_not-a-real-token"})
    assert r.status_code == 401
