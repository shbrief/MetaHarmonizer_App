"""Sentry init is a safe no-op unless configured."""

from __future__ import annotations

import app.core.settings as settings_mod
from app.core.sentry import init_sentry


def test_init_sentry_noop_without_dsn(monkeypatch):
    # Default settings have no DSN -> init returns False, no exception.
    monkeypatch.setattr(settings_mod.settings, "sentry_dsn", None, raising=False)
    assert init_sentry() is False
