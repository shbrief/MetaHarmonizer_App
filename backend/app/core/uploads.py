"""
Upload boundary checks (spec §6.4).

Pure validation helpers — no FastAPI/Starlette coupling — so they're trivially
unit-testable and reusable. Raise ``AppError`` subclasses that the error
envelope maps to the right HTTP status:

  - file too large  -> 413 PayloadTooLarge
  - too many columns / rows -> 422 ValidationError
"""

from __future__ import annotations

from app.core.errors import AppError, ValidationError


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


def check_table_shape(*, n_rows: int, n_cols: int, max_rows: int, max_cols: int) -> None:
    if n_cols > max_cols:
        raise ValidationError(
            f"Study has {n_cols} columns; the limit is {max_cols}.",
            details={"columns": n_cols, "limit": max_cols},
        )
    if n_rows > max_rows:
        raise ValidationError(
            f"Study has {n_rows} rows; the limit is {max_rows}.",
            details={"rows": n_rows, "limit": max_rows},
        )
