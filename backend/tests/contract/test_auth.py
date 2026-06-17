"""Auth slice-1 tests: register (domain gate, bootstrap admin), login, /me.

Runs against the dev Postgres on an isolated app instance; skips if Postgres
is unreachable. Uses a unique domain per run so the bootstrap-admin assertion
is deterministic regardless of existing rows.
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
async def client(database_url, monkeypatch):
    engine = create_async_engine(database_url, poolclass=sa.pool.NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(sa.text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("dev Postgres not reachable")

    db_session.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    # Reset the Redis singleton so the lockout code binds to this test's loop.
    import app.core.redis as redis_mod

    redis_mod._client = None

    # Allow a unique throwaway domain for this test run.
    domain = f"t{uuid.uuid4().hex[:8]}.example.com"
    monkeypatch.setattr(settings_mod.settings, "allowed_email_domains", domain, raising=False)
    monkeypatch.setattr(settings_mod.settings, "hibp_check", False, raising=False)

    from fastapi import FastAPI
    from app.core.middleware import install_observability
    from app.routers import auth

    app = FastAPI()
    install_observability(app)
    app.include_router(auth.router)

    created: list[str] = []

    async def _make_client():
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

    yield _make_client, domain, db_session.SessionLocal

    # cleanup created users
    async with db_session.SessionLocal() as s:
        await s.execute(sa.delete(User).where(User.email.like(f"%@{domain}")))
        await s.commit()
    await engine.dispose()
    redis_mod._client = None


async def test_register_login_me_flow(client):
    make_client, domain, _ = client
    email = f"alice@{domain}"
    async with await make_client() as c:
        # register
        r = await c.post("/api/v1/auth/register", json={"email": email, "password": "s3cret-pass"})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["user"]["email"] == email
        assert body["user"]["role"] == "admin"  # first user in a fresh domain bootstraps admin
        token = body["access_token"]

        # me with the token
        r = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == email

        # login
        r = await c.post("/api/v1/auth/login", json={"email": email, "password": "s3cret-pass"})
        assert r.status_code == 200
        assert r.json()["access_token"]


async def test_second_user_is_curator(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        await c.post("/api/v1/auth/register", json={"email": f"admin@{domain}", "password": "pw-123456"})
        r = await c.post("/api/v1/auth/register", json={"email": f"bob@{domain}", "password": "pw-123456"})
        assert r.json()["user"]["role"] == "curator"


async def test_wrong_domain_rejected(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        r = await c.post("/api/v1/auth/register", json={"email": "x@gmail.com", "password": "pw-123456"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "REGISTRATION_CLOSED"


async def test_duplicate_email_conflict(client):
    make_client, domain, _ = client
    email = f"dup@{domain}"
    async with await make_client() as c:
        await c.post("/api/v1/auth/register", json={"email": email, "password": "pw-123456"})
        r = await c.post("/api/v1/auth/register", json={"email": email, "password": "pw-123456"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


async def test_bad_password_rejected(client):
    make_client, domain, _ = client
    email = f"carol@{domain}"
    async with await make_client() as c:
        await c.post("/api/v1/auth/register", json={"email": email, "password": "right-pass"})
        r = await c.post("/api/v1/auth/login", json={"email": email, "password": "wrong-pass"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "AUTH_FAILED"


async def test_me_requires_token(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        r = await c.get("/api/v1/auth/me")
    assert r.status_code == 401


# ── Slice 2: refresh / logout / sessions ─────────────────────────────────────
async def test_register_sets_refresh_cookie(client):
    from app.core.security import REFRESH_COOKIE

    make_client, domain, _ = client
    async with await make_client() as c:
        r = await c.post(
            "/api/v1/auth/register",
            json={"email": f"cook@{domain}", "password": "pw-123456"},
        )
        assert r.status_code == 201
        assert REFRESH_COOKIE in c.cookies


async def test_refresh_rotates_and_returns_access(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        await c.post(
            "/api/v1/auth/register",
            json={"email": f"refr@{domain}", "password": "pw-123456"},
        )
        r = await c.post("/api/v1/auth/refresh")
        assert r.status_code == 200, r.text
        assert r.json()["access_token"]


async def test_logout_revokes_refresh(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        await c.post(
            "/api/v1/auth/register",
            json={"email": f"out@{domain}", "password": "pw-123456"},
        )
        r = await c.post("/api/v1/auth/logout")
        assert r.status_code == 204
        # Cookie is cleared, and even a stale refresh token is now rejected.
        r = await c.post("/api/v1/auth/refresh")
        assert r.status_code == 401


async def test_sessions_list_and_revoke(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        reg = await c.post(
            "/api/v1/auth/register",
            json={"email": f"sess@{domain}", "password": "pw-123456"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # A second login creates a second session for the same user.
        async with await make_client() as c2:
            await c2.post(
                "/api/v1/auth/login",
                json={"email": f"sess@{domain}", "password": "pw-123456"},
            )

        r = await c.get("/api/v1/auth/sessions", headers=headers)
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 2
        assert any(s["current"] for s in rows)

        # Revoke a non-current session.
        other = next(s for s in rows if not s["current"])
        r = await c.delete(f"/api/v1/auth/sessions/{other['id']}", headers=headers)
        assert r.status_code == 204

        r = await c.get("/api/v1/auth/sessions", headers=headers)
        assert all(s["id"] != other["id"] for s in r.json())


async def test_refresh_without_cookie_rejected(client):
    make_client, domain, _ = client
    async with await make_client() as c:
        r = await c.post("/api/v1/auth/refresh")
    assert r.status_code == 401
