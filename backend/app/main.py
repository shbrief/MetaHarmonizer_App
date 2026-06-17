"""
MetaHarmonizer Dashboard — FastAPI Application

Main entry point. Configures logging, the unified error envelope + request-id
middleware, then registers all routers.
"""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.core.middleware import install_observability
from app.core.limits import install_limits
from app.core.metrics import MetricsMiddleware
from app.core.sentry import init_sentry
from app.core.settings import settings
from app.database import init_db
from app.routers import admin, audit, auth, export, harmonize, health, mappings, ontology, quality, tokens

configure_logging(settings.log_level)
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database and pre-warm the ML engine on startup."""
    init_db()

    # Pre-warm the selected engine in a background thread so the server
    # starts accepting requests immediately.  The engine loads the
    # SentenceTransformer model (~90 MB) and dictionaries once;
    # subsequent /harmonize uploads reuse the cached engine.
    def _warm():
        from app.engine_adapter import get_engine
        get_engine().pre_warm()

    t = threading.Thread(target=_warm, daemon=True)
    t.start()

    yield


app = FastAPI(
    title="MetaHarmonizer Dashboard API",
    description="Automated metadata harmonization for cBioPortal — curator review dashboard backend.",
    version="0.1.0",
    lifespan=lifespan,
)

# Request-id + unified error envelope (spec §6.1).
install_observability(app)

# Prometheus golden-signal instrumentation (exposed at admin-scoped /metrics).
app.add_middleware(MetricsMiddleware)

# Rate-limit + idempotency (spec §6.4); fail-open if Redis is unavailable.
install_limits(app)

# CORS — origins from settings (no wildcards in production).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tokens.router)
app.include_router(audit.router)
app.include_router(harmonize.router)
app.include_router(mappings.router)
app.include_router(quality.router)
app.include_router(export.router)
app.include_router(ontology.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "MetaHarmonizer Dashboard API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/health/engine", tags=["health"])
async def health_engine():
    """Report which engine adapter is active and whether it is ready."""
    from app.engine_adapter import get_engine

    return get_engine().health().model_dump()
