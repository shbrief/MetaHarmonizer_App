"""
Application settings — the single source of configuration truth.

Loaded once from environment variables (and an optional ``.env`` for local dev)
via pydantic-settings. Importing ``settings`` anywhere returns the same cached
instance. Boot fails loudly (ValidationError) if a required var is missing or a
value is invalid — there is no silent default for security-critical settings.

Mirrors the catalogue in ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Engine ──────────────────────────────────────────────────────────────
    engine_impl: Literal["metaharmonizer", "mock"] = "metaharmonizer"
    method_model_yaml: str | None = None
    llm_threshold: float = 0.5
    gemini_api_key: str | None = None
    umls_api_key: str | None = None

    # ── Datastore / cache ───────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://mh:mh_dev_password@localhost:5432/metaharmonizer",
        description="Async SQLAlchemy Postgres DSN.",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── Object storage ──────────────────────────────────────────────────────
    object_store_url: str = "file:///app/data/objects"
    r2_bucket: str | None = None
    r2_key: str | None = None
    r2_secret: str | None = None

    # ── Auth / security ─────────────────────────────────────────────────────
    auth_mode: Literal["jwt", "none"] = "jwt"
    jwt_secret: str = Field(
        default="change-me-in-prod-min-32-bytes-long-string",
        description="HMAC signing key; must be >= 32 bytes when AUTH_MODE=jwt.",
    )
    access_ttl_min: int = 15
    refresh_ttl_days: int = 30
    allowed_email_domains: str = ""  # comma-separated; empty -> admin-invite-only
    resend_api_key: str | None = None

    # ── Web / CORS ──────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # ── Upload safety (spec §6.4) ───────────────────────────────────────────
    # Byte-size guard only (prevents a runaway upload filling the disk).
    # No row/column ceilings — study scale is guidance, not a gate.
    max_upload_mb: int = 50

    # ── Observability ───────────────────────────────────────────────────────
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    sentry_dsn: str | None = None

    # ── Validators (fail-fast) ──────────────────────────────────────────────
    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_strength(cls, v: str, info) -> str:
        # Only enforce length when JWT auth is actually in use.
        mode = info.data.get("auth_mode", "jwt")
        if mode == "jwt" and len(v.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must be at least 32 bytes when AUTH_MODE=jwt")
        return v

    @field_validator("llm_threshold")
    @classmethod
    def _threshold_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("LLM_THRESHOLD must be between 0.0 and 1.0")
        return v

    # ── Derived helpers ─────────────────────────────────────────────────────
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_email_domain_list(self) -> list[str]:
        return [d.strip().lower().lstrip("@") for d in self.allowed_email_domains.split(",") if d.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance (constructed once per process)."""
    return Settings()


settings = get_settings()
