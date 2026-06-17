"""
Upload safety guard (spec §6.4).

A single byte-size guard against a runaway upload filling the disk / OOMing the
box — this is server safety, not a study-scale ceiling. There are deliberately
no row/column count limits: those numbers are scale expectations, not gates.
"""

from __future__ import annotations

from app.core.errors import AppError


class PayloadTooLargeError(AppError):
    code = "PAYLOAD_TOO_LARGE"
    status_code = 413


def check_upload_size(num_bytes: int, max_mb: int) -> None:
    limit = max_mb * 1024 * 1024
    if num_bytes > limit:
        raise PayloadTooLargeError(
            f"Upload exceeds the {max_mb} MB limit.",
            details={"size_bytes": num_bytes, "limit_bytes": limit},
        )
