"""
Typed Pydantic DTOs for the engine contract.

Right now most adapter methods still return ``list[dict]`` so the
existing DB layer keeps working without changes. These models are the
target shape — use them in new code and convert over incrementally.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Stage = Literal["stage1", "stage2", "stage3", "stage4", "unmapped", "invalid"]
"""Pipeline stage that produced a mapping. Matches the upstream engine."""


class Alternative(BaseModel):
    """One candidate match for a column or value."""

    field: str
    score: float
    method: str = ""  # e.g. "std_exact", "bert", "fuzzy", "llm", "mock"


class MappingRow(BaseModel):
    """One row of the schema-mapping output (one per input column)."""

    raw_column: str
    matched_field: str | None
    confidence_score: float
    stage: Stage
    method: str
    alternatives: list[Alternative] = []
    status: Literal["accepted", "pending", "rejected"] = "pending"


class OntologyMappingRow(BaseModel):
    """One row of the value-level ontology output."""

    field_name: str
    raw_value: str
    ontology_term: str | None
    ontology_id: str | None
    confidence_score: float
    status: Literal["accepted", "pending", "rejected"] = "pending"


class LLMSuggestion(BaseModel):
    """One Stage-4 LLM suggestion for a single column."""

    field: str
    confidence: float
    reasoning: str = ""


class EngineHealth(BaseModel):
    """Adapter health snapshot. Exposed via ``GET /health/engine``."""

    ok: bool
    name: str
    version: str
    loaded_models: list[str] = []
    warnings: list[str] = []
