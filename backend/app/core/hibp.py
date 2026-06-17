"""
Have-I-Been-Pwned breached-password check (k-anonymity, spec §6.7).

Sends only the first 5 chars of the SHA-1 hash to the range API, so the full
password (or hash) never leaves the process. Fails open: if the network call
errors or times out, registration proceeds (availability over strictness).
"""

from __future__ import annotations

import hashlib

import httpx

_API = "https://api.pwnedpasswords.com/range/"


async def password_breach_count(password: str, *, timeout: float = 2.5) -> int:
    """Return how many times this password appears in known breaches (0 if safe
    or if the lookup could not be completed)."""
    digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = digest[:5], digest[5:]
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{_API}{prefix}", headers={"Add-Padding": "true"}
            )
        if resp.status_code != 200:
            return 0
        for line in resp.text.splitlines():
            tail, _, count = line.partition(":")
            if tail.strip() == suffix:
                return int(count or 0)
        return 0
    except Exception:
        return 0  # fail-open
