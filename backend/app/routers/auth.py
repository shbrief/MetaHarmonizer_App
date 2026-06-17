"""
Auth router (Sprint 3, slice 1) — register, login, and current-user.

Slice 1 scope (testable end-to-end):
  POST /api/v1/auth/register  — create an account (domain-gated), returns access token
  POST /api/v1/auth/login     — email/password -> access token
  GET  /api/v1/auth/me        — who am I (requires Bearer access token)

Policy:
  - Argon2id password hashing.
  - Domain-restricted signup: if ALLOWED_EMAIL_DOMAINS is set, only those
    domains may register; empty list -> registration is closed (admin-invite-only).
  - Bootstrap: the very first account created becomes ``admin``; everyone else
    is a ``curator``. (Full admin user-management lands in a later slice.)

Refresh cookies, sessions, RBAC enforcement, API tokens, lockout, and email
verification arrive in later slices.
"""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.settings import settings
from app.db.session import get_db
from app.repositories import users as users_repo
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AuthError(AppError):
    code = "AUTH_FAILED"
    status_code = 401


class RegistrationClosedError(AppError):
    code = "REGISTRATION_CLOSED"
    status_code = 403


class EmailTakenError(AppError):
    code = "EMAIL_TAKEN"
    status_code = 409


def _domain_allowed(email: str) -> bool:
    domains = settings.allowed_email_domain_list
    if not domains:
        return False  # empty -> registration closed (invite-only)
    return email.split("@")[-1].lower() in domains


def _token_response(user) -> TokenResponse:
    access = create_access_token(user_id=user.id, role=user.role, email=user.email)
    return TokenResponse(access_token=access, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if not _domain_allowed(body.email):
        raise RegistrationClosedError(
            "Registration is restricted to approved email domains."
        )
    if await users_repo.get_by_email(db, body.email):
        raise EmailTakenError("An account with this email already exists.")

    # Bootstrap: first user is admin, the rest are curators.
    role = "admin" if await users_repo.count_users(db) == 0 else "curator"

    user = await users_repo.create_user(
        db,
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        role=role,
    )
    await db.commit()
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await users_repo.get_by_email(db, body.email)
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise AuthError("Incorrect email or password.")
    if not user.is_active:
        raise AuthError("This account is disabled.")
    return _token_response(user)


async def current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Dependency: resolve the user from the Bearer access token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    token = auth[7:]
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise AuthError("Invalid or expired token.")
    if payload.get("type") != "access":
        raise AuthError("Wrong token type.")
    user = await users_repo.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthError("Account not found or disabled.")
    request.state.user_id = user.id
    return user


@router.get("/me", response_model=UserOut)
async def me(user=Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)
