"""
arq worker (Sprint 4, ``JOB_MODE=queue``).

Run with::

    cd backend
    arq app.workers.arq_worker.WorkerSettings

Each worker process pre-warms the engine once on startup and then processes one
job at a time; scale concurrency by running more worker processes/containers.
Retries (3 attempts, backoff) and the hard timeout are enforced by arq here, so
a stuck job is killed and a transient failure is retried.
"""

from __future__ import annotations

import logging

from arq.connections import RedisSettings

from app.core.settings import settings
from app.workers.tasks import run_harmonize

logger = logging.getLogger("app.worker")


async def harmonize_job(ctx, **kwargs) -> None:
    """arq entry point — delegates to the shared task implementation."""
    await run_harmonize(**kwargs)


async def _startup(ctx) -> None:
    # Load the engine + dictionaries once so the first job isn't cold.
    try:
        from app.engine_adapter import get_engine

        get_engine().pre_warm()
    except Exception:  # noqa: BLE001
        logger.warning("engine pre-warm skipped", exc_info=True)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [harmonize_job]
    on_startup = _startup
    max_jobs = 4                         # concurrent jobs per worker process
    job_timeout = settings.job_hard_timeout_sec
    max_tries = settings.job_max_attempts
    retry_jobs = True
