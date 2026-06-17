"""
Harmonize job task (Sprint 4).

The single source of truth for *running* a harmonization, shared by both the
arq worker (``queue`` mode) and the inline executor (``inline`` mode). It:

- drives the job_runs lifecycle (queued -> running -> succeeded/failed/cancelled),
- publishes stage-by-stage progress on the Redis bus (so every connected user
  sees live updates regardless of which process runs the work),
- checks the cancel flag at each stage boundary,
- runs the CPU-heavy engine pipeline in a worker thread so the API event loop
  stays responsive for other concurrent users.
"""

from __future__ import annotations

import logging

import anyio
import pandas as pd

from app import database as db
from app.core.jobs import (
    JobCancelled,
    clear_cancel,
    is_cancelled,
    notify_user,
    publish_progress,
)
from app.db.session import SessionLocal
from app.engine_adapter import get_engine
from app.repositories import jobs as jobs_repo

logger = logging.getLogger("app.jobs")

# Stage weights for a smooth progress bar (parse, schema, ontology, finalize).
_STAGES = [
    ("parse", "Reading file", 10),
    ("schema", "Mapping columns to schema", 55),
    ("ontology", "Resolving ontology terms", 90),
    ("done", "Finalizing", 100),
]


async def _emit(study_id: str, *, stage: str, message: str, pct: int, state: str = "running") -> None:
    await publish_progress(
        study_id,
        {"type": "progress", "stage": stage, "message": message, "pct": pct, "state": state},
    )


async def _checkpoint(study_id: str) -> None:
    """Raise if a cancel was requested — called at every stage boundary."""
    if await is_cancelled(study_id):
        raise JobCancelled()


def _run_pipeline(study_id: str, file_path: str, suffix: str, curated_path: str) -> dict:
    """Synchronous, CPU-heavy engine work — executed in a worker thread."""
    sep = "\t" if suffix in (".tsv", ".txt") else ","
    raw_df = pd.read_csv(file_path, sep=sep, low_memory=False)
    curated_df = pd.read_csv(curated_path, low_memory=False)

    engine = get_engine()
    schema_results = engine.harmonize_schema(raw_df, curated_df, csv_path=file_path)
    db.insert_mappings(study_id, schema_results)

    onto_results = engine.map_values(raw_df, schema_results)
    if onto_results:
        db.insert_ontology_mappings(study_id, onto_results)

    return {
        "columns": len(schema_results),
        "rows": int(len(raw_df)),
        "ontology_values": len(onto_results) if onto_results else 0,
    }


async def run_harmonize(
    *,
    job_id: int,
    study_id: str,
    file_path: str,
    suffix: str,
    curated_path: str,
    owner_id: int | None = None,
) -> None:
    """Execute one harmonize job end-to-end. Never raises — terminal state is
    recorded in job_runs and broadcast on the bus."""
    async with SessionLocal() as session:
        job = await jobs_repo.get_job(session, job_id)
        if job is None:
            logger.warning("run_harmonize: job %s not found", job_id)
            return
        await jobs_repo.mark_running(session, job)
        await session.commit()

    try:
        await _checkpoint(study_id)
        await _emit(study_id, stage="parse", message="Reading file", pct=10)

        db.update_study_status(study_id, "processing")
        await _emit(study_id, stage="schema", message="Mapping columns to schema", pct=30)

        # Heavy engine work off the event loop; re-check cancel before & after.
        await _checkpoint(study_id)
        result = await anyio.to_thread.run_sync(
            _run_pipeline, study_id, file_path, suffix, curated_path
        )
        await _checkpoint(study_id)

        await _emit(study_id, stage="ontology", message="Resolving ontology terms", pct=90)
        db.update_study_status(study_id, "review")

        async with SessionLocal() as session:
            job = await jobs_repo.get_job(session, job_id)
            if job:
                await jobs_repo.mark_succeeded(session, job)
                await session.commit()

        await clear_cancel(study_id)
        await publish_progress(
            study_id,
            {
                "type": "complete",
                "stage": "done",
                "state": "succeeded",
                "pct": 100,
                "message": f"Harmonization complete — {result['columns']} columns.",
                "result": result,
            },
        )
        if owner_id:
            await notify_user(
                owner_id,
                {"type": "job_complete", "study_id": study_id, "result": result},
            )

    except JobCancelled:
        db.update_study_status(study_id, "cancelled")
        async with SessionLocal() as session:
            job = await jobs_repo.get_job(session, job_id)
            if job:
                await jobs_repo.mark_cancelled(session, job)
                await session.commit()
        await clear_cancel(study_id)
        await publish_progress(
            study_id,
            {"type": "cancelled", "stage": "done", "state": "cancelled", "pct": 0,
             "message": "Harmonization cancelled."},
        )

    except Exception as exc:  # noqa: BLE001 — terminal failure is recorded, not raised
        logger.exception("harmonize job %s failed", job_id)
        db.update_study_status(study_id, "failed")
        async with SessionLocal() as session:
            job = await jobs_repo.get_job(session, job_id)
            if job:
                exhausted = job.attempt >= _max_attempts()
                await jobs_repo.mark_failed(
                    session,
                    job,
                    error_code="ENGINE_ERROR",
                    error_message=str(exc),
                    dead_letter=exhausted,
                )
                await session.commit()
        await publish_progress(
            study_id,
            {"type": "failed", "stage": "done", "state": "failed", "pct": 0,
             "message": "Harmonization failed. Please try again."},
        )


def _max_attempts() -> int:
    from app.core.settings import settings

    return settings.job_max_attempts
