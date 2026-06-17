"""
Prometheus metrics (spec §6.6) — the four golden signals + auth failures.

A lightweight middleware records request latency/traffic/errors. The counters
are exposed at an admin-scoped ``GET /metrics`` (see app.routers.health). Other
modules bump ``AUTH_FAILURES`` / ``WS_CONNECTIONS`` / ``QUEUE_DEPTH`` directly.
"""

from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ── Golden signals ────────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)
REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "HTTP responses with status >= 500.",
    ["method", "path"],
)

# ── Auxiliary signals ─────────────────────────────────────────────────────────
AUTH_FAILURES = Counter("auth_failures_total", "Failed authentication attempts.")
WS_CONNECTIONS = Gauge("ws_connections", "Open WebSocket connections.")
QUEUE_DEPTH = Gauge("job_queue_depth", "Pending jobs in the queue.")


def _route_template(request: Request) -> str:
    """Use the matched route path (``/studies/{study_id}``) so cardinality stays
    bounded instead of exploding per-id."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        path = _route_template(request)
        method = request.method
        REQUEST_LATENCY.labels(method, path).observe(time.perf_counter() - start)
        REQUEST_COUNT.labels(method, path, str(response.status_code)).inc()
        if response.status_code >= 500:
            REQUEST_ERRORS.labels(method, path).inc()
        return response


def render_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
