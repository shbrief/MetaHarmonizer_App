"""
Security primitives: password hashing (Argon2id) and JWT access tokens.

- Passwords are hashed with Argon2id (argon2-cffi defaults are OWASP-sane).
- Access tokens are short-lived signed JWTs (HS256) carrying the user id, role,
  and email. Refresh tokens (Sprint 3 slice 2) live in an httpOnly cookie and
  are tracked server-side in the sessions table.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.settings import settings

_ph = PasswordHasher()

JWT_ALG = "HS256"

# Cookie name for the refresh token (httpOnly, not readable by JS).
REFRESH_COOKIE = "mh_refresh"


# ── Passwords ────────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    return _ph.check_needs_rehash(hashed)


# ── Access tokens ────────────────────────────────────────────────────────────
def create_access_token(*, user_id: int, role: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "email": email,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_ttl_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    """Decode + verify a JWT. Raises ``jwt.PyJWTError`` on any problem."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALG])


# ── Refresh tokens ───────────────────────────────────────────────────────────
def new_jti() -> str:
    """A unique, unguessable identifier for a refresh token / session."""
    return secrets.token_urlsafe(32)


def create_refresh_token(*, user_id: int, jti: str) -> str:
    """Long-lived signed JWT bound to a server-side session via ``jti``.

    The session row (sessions table) is the source of truth for revocation:
    a refresh token is only honoured while its ``jti`` maps to a live session.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_ttl_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALG)


# ── API tokens (Sprint 3 slice 4) ────────────────────────────────────────────
def generate_api_token() -> tuple[str, str]:
    """Return ``(plaintext, sha256_hash)``. Only the hash is stored; the
    plaintext is shown to the user exactly once."""
    plain = "mh_" + secrets.token_urlsafe(32)
    return plain, hash_api_token(plain)


def hash_api_token(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()
