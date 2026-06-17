"""Shared pytest fixtures.

Database tests use the local dev Postgres (scripts/dev_services.ps1 start).
They are skipped automatically if DATABASE_URL is not reachable, so the unit
tests (settings) still run anywhere.
"""

from __future__ import annotations

import os

import pytest

# Ensure a valid JWT secret for any settings import during tests.
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!!")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://mh:mh_dev_password@127.0.0.1:5433/metaharmonizer",
)


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ["DATABASE_URL"]
