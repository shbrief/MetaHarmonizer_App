"""
Cursor-based pagination (spec §6.1).

List endpoints return ``{ "items": [...], "next_cursor": "<opaque>" | null }``.
Cursors are opaque base64 of the last item's sort key — never page numbers — so
results stay stable under concurrent inserts. Default page size 50, hard cap 500.
"""

from __future__ import annotations

import base64
import json
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None


def clamp_limit(limit: int | None) -> int:
    if not limit or limit < 1:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)


def encode_cursor(value: object) -> str:
    """Opaque base64-url cursor from a JSON-serialisable sort key."""
    raw = json.dumps(value, default=str).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str | None) -> object | None:
    """Inverse of :func:`encode_cursor`; returns None for an empty/invalid cursor."""
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
        return json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return None


def build_page(rows: list[T], limit: int, cursor_of) -> Page[T]:
    """Slice an over-fetched result set into a Page.

    Caller fetches ``limit + 1`` rows; if the extra row exists there's a next
    page and ``cursor_of(last_returned_row)`` becomes the next cursor.
    """
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = encode_cursor(cursor_of(page_rows[-1])) if has_more and page_rows else None
    return Page(items=page_rows, next_cursor=next_cursor)
