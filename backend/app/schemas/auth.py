"""API schemas for auth (Sprint 3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    role: str
    is_active: bool
    email_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ip: str | None = None
    user_agent: str | None = None
    created_at: datetime
    last_seen: datetime | None = None
    current: bool = False
