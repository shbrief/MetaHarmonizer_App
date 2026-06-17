"""
Structured JSON logging + request-id context.

A ``contextvar`` holds the current request's id for the duration of the request,
so every log line emitted while handling it carries ``request_id`` automatically.
The error envelope (core/errors.py) returns the same id, so a user-visible error
is one grep away from its server-side logs (spec §6.1, §6.6).

No third-party logging dependency: stdlib ``logging`` + a JSON formatter.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar

# Set by the request-id middleware; empty outside a request.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class JsonFormatter(logging.Formatter):
    """One JSON object per log line, with request_id when available."""

    # Standard LogRecord attributes we don't want duplicated in "extra".
    _RESERVED = set(
        logging.makeLogRecord({}).__dict__.keys()
    ) | {"message", "asctime", "taskName"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid

        # Promote any structured "extra" fields (e.g. study_id, user_id).
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "info") -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Quiet noisy libraries; let our app logger speak.
    logging.getLogger("uvicorn.access").handlers.clear()
