"""API schemas for the audit query surface (U11)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    study_id: str | None = None
    actor_id: int | None = None
    action: str
    mapping_id: int | None = None
    old_value: str | None = None
    new_value: str | None = None
    details: dict | None = None
    created_at: datetime
