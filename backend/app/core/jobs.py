"""
Job progress bus + cancellation + WS tickets — all Redis-backed (Sprint 4).

Everything here is shared state in Redis (never in-process memory) so the
system works correctly when **many users run jobs at once** and when the API
and workers are scaled to multiple processes/instances:

- Progress is broadcast on a pub/sub channel per study; any API instance holding
  a WebSocket for that study relays it, regardless of which worker produced it.
- The latest snapshot is cached so a browser that connects mid-job (or
  reconnects) immediately sees current state without waiting for the next tick.
- Cancellation is a Redis flag the worker polls at each stage boundary.
- WS auth tickets are one-time nonces with a short TTL.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from app.core.redis import get_redis
from app.core.settings import settings


# ── channel / key helpers ─────────────────────────────────────────────────────
def job_channel(study_id: str) -> str:
    return f"ws:jobs:{study_id}"


def _snapshot_key(study_id: str) -> str:
    return f"job:snapshot:{study_id}"


def _cancel_key(study_id: str) -> str:
    return f"job:cancel:{study_id}"


def user_channel(user_id: int) -> str:
    return f"ws:notify:{user_id}"


# ── progress publish / snapshot ───────────────────────────────────────────────
async def publish_progress(study_id: str, payload: dict[str, Any]) -> None:
    """Broadcast a progress event and cache it as the latest snapshot (1h TTL)."""
    payload = {"study_id": study_id, **payload}
    body = json.dumps(payload)
    try:
        r = get_redis()
        await r.publish(job_channel(study_id), body)
        await r.set(_snapshot_key(study_id), body, ex=3600)
    except Exception:
        # Progress is best-effort: a Redis blip must never fail the job itself.
        pass


async def get_snapshot(study_id: str) -> dict[str, Any] | None:
    try:
        raw = await get_redis().get(_snapshot_key(study_id))
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def notify_user(user_id: int, payload: dict[str, Any]) -> None:
    try:
        await get_redis().publish(user_channel(user_id), json.dumps(payload))
    except Exception:
        pass


# ── cancellation ──────────────────────────────────────────────────────────────
async def request_cancel(study_id: str) -> None:
    try:
        await get_redis().set(_cancel_key(study_id), "1", ex=3600)
    except Exception:
        pass


async def is_cancelled(study_id: str) -> bool:
    try:
        return bool(await get_redis().get(_cancel_key(study_id)))
    except Exception:
        return False


async def clear_cancel(study_id: str) -> None:
    try:
        await get_redis().delete(_cancel_key(study_id))
    except Exception:
        pass


# ── WS auth tickets (one-time, short-lived) ───────────────────────────────────
async def mint_ws_ticket(user_id: int) -> str:
    ticket = secrets.token_urlsafe(32)
    await get_redis().set(f"ws:ticket:{ticket}", str(user_id), ex=settings.ws_ticket_ttl_sec)
    return ticket


async def redeem_ws_ticket(ticket: str) -> int | None:
    """Validate + consume a ticket. Returns the user id, or None if invalid."""
    try:
        r = get_redis()
        key = f"ws:ticket:{ticket}"
        uid = await r.get(key)
        if uid is None:
            return None
        await r.delete(key)  # one-time use
        return int(uid)
    except Exception:
        return None


class JobCancelled(Exception):
    """Raised inside the task when a cancel flag is observed at a stage boundary."""
