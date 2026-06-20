"""Shared auth helper for contract tests.

Since email verification landed, ``POST /auth/register`` returns a message
instead of tokens, and non-bootstrap users must verify before they can log in.
Most contract tests only need *an authenticated user*, so this helper registers,
force-verifies the account directly in the DB (skipping the email round-trip),
logs in, and returns the login body — i.e. the ``{"access_token", "user"}``
shape the tests already expect.
"""

from __future__ import annotations

import sqlalchemy as sa

import app.db.session as db_session
from app.db.models import User


async def register_and_login(c, email, password="pw-123456", **extra) -> dict:
    """Register ``email``, mark it verified, log in, and return the login JSON."""
    await c.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, **extra},
    )
    async with db_session.SessionLocal() as s:
        await s.execute(
            sa.update(User).where(User.email == email).values(email_verified=True)
        )
        await s.commit()
    r = await c.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return r.json()
