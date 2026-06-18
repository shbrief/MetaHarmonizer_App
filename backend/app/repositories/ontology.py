"""Value-level ontology mapping data access (Postgres)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OntologyMapping


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _to_dict(o: OntologyMapping) -> dict:
    return {
        "id": o.id,
        "study_id": o.study_id,
        "field_name": o.field_name,
        "raw_value": o.raw_value,
        "ontology_term": o.ontology_term,
        "ontology_id": o.ontology_id,
        "confidence_score": o.confidence_score,
        "status": o.status,
        "curator_term": o.curator_term,
        "curator_id": o.curator_id,
        "reviewed_at": _iso(o.reviewed_at),
        "reviewed_by": "curator" if o.reviewed_at else None,
    }


async def insert_ontology_mappings(
    db: AsyncSession, study_id: str, onto_list: list[dict]
) -> None:
    for o in onto_list:
        db.add(
            OntologyMapping(
                study_id=study_id,
                field_name=o["field_name"],
                raw_value=o["raw_value"],
                ontology_term=o.get("ontology_term"),
                ontology_id=o.get("ontology_id"),
                confidence_score=o.get("confidence_score"),
                status=o.get("status", "pending"),
            )
        )
    await db.flush()


async def get_ontology_mappings(db: AsyncSession, study_id: str) -> list[dict]:
    stmt = (
        select(OntologyMapping)
        .where(OntologyMapping.study_id == study_id)
        .order_by(OntologyMapping.field_name)
    )
    return [_to_dict(o) for o in await db.scalars(stmt)]


async def update_ontology_mapping(
    db: AsyncSession,
    mapping_id: int,
    status: str,
    curator_term: str | None = None,
    curator_id: str | None = None,
    reviewed_by: str = "curator",
) -> dict | None:
    """Curator override for an ontology value mapping. When the curator assigns
    a term it's a confirmed human decision, so confidence is set to 1.0 (an
    unmatched value's engine score of 0 would otherwise show as "0%" after
    approval and look broken)."""
    o = await db.get(OntologyMapping, mapping_id)
    if not o:
        return None
    o.status = status
    o.reviewed_at = datetime.now(timezone.utc)
    if curator_term:
        o.curator_term = curator_term
        o.curator_id = curator_id
        o.confidence_score = 1.0
    await db.flush()
    return _to_dict(o)
