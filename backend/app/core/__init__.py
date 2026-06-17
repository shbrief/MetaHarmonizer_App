"""
Core cross-cutting concerns (no business logic, no engine imports).

Houses what every layer depends on:
- settings.py   — Pydantic BaseSettings, the single env-var loader (spec §6.5)
- security.py   — password hashing (argon2id), JWT encode/decode, CSRF helpers
- logging.py    — structured JSON logging + request_id context
- errors.py     — unified error envelope + exception handlers (spec §6.1)
- pagination.py — cursor pagination helper (spec §6.1)

Added incrementally during Sprint 2 (operational contracts) and Sprint 3 (auth).
"""
