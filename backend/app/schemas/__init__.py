"""
API schemas — Pydantic v2 request/response DTOs for the HTTP surface.

Distinct from app/engine_adapter/types.py (those are the engine-boundary DTOs).
These shape what the REST API accepts and returns: pagination envelopes,
error envelope, auth payloads, study/mapping/audit response models.

Grouped by domain (auth.py, studies.py, mappings.py, audit.py, ...).
"""
