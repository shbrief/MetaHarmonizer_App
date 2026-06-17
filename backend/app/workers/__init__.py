"""
Background workers — `arq` tasks run in a separate worker process.

- settings.py   — arq WorkerSettings (Redis, concurrency=1 job/process)
- jobs.py       — harmonize_columns / harmonize_values task wrappers
- lifecycle.py  — job_runs state machine, retry/timeout/cancel (spec §6.3)

This is the ONLY place outside engine_adapter/ that runs the engine
(workers import the adapter, not the wheel). Added in Sprint 4.
"""
