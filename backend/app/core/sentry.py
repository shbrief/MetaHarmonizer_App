"""
Sentry initialisation — opt-in, no-op by default.

Calling ``init_sentry()`` does nothing unless ``SENTRY_DSN`` is set, so local
dev and CI stay quiet. The ``sentry-sdk`` package is an optional dependency:
if it isn't installed, init is skipped with a debug log rather than failing.
Release is tagged with the git short SHA when available.
"""

from __future__ import annotations

import logging
import os
import subprocess

from app.core.settings import settings

logger = logging.getLogger("app.sentry")


def _git_short_sha() -> str | None:
    sha = os.getenv("GIT_SHA")
    if sha:
        return sha[:12]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def init_sentry() -> bool:
    """Initialise Sentry if configured. Returns True when actually enabled."""
    if not settings.sentry_dsn:
        logger.debug("Sentry disabled (SENTRY_DSN unset).")
        return False
    try:
        import sentry_sdk  # type: ignore
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry-sdk is not installed; skipping.")
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        release=_git_short_sha(),
        traces_sample_rate=0.0,  # errors only by default; tracing opt-in later
        send_default_pii=False,
    )
    logger.info("Sentry initialised.")
    return True
