"""
Shared async Redis client.

One connection pool per process, created lazily from ``settings.redis_url``.
Used by the idempotency and rate-limit middleware (and later the WS ticket /
queue layers). ``get_redis()`` returns the singleton; ``None`` is never returned
— callers that must tolerate Redis being down should catch connection errors.
"""

from __future__ import annotations

import redis.asyncio as redis

from app.core.settings import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
