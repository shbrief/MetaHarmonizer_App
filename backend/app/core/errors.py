"""
Domain exceptions that map cleanly to HTTP responses.

Kept framework-agnostic (no FastAPI import) so services/repositories can raise
them without depending on the web layer. The error-envelope middleware (added
later this sprint) translates these to the unified JSON shape (spec §6.1).
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected, mapped application errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConflictError(AppError):
    """Optimistic-locking conflict — the row changed under the caller (spec §6.2)."""

    code = "MAPPING_CONFLICT"
    status_code = 409


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 422
