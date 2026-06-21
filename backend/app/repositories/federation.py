"""Federation-lite data access (G1).

Builds the export bundle from this instance's curator-confirmed mappings and
ingests a peer's bundle into the staging tables (pending local approval, Q10).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    FederationImport,
    FederationMapping,
    Mapping,
    OntologyMapping,
)
from app.services import federation as fed_sig


def _dedup_key(record_type: str, raw_key: str, target: str, ontology_id: str | None) -> str:
    """Stable content identity for a mapping (per-source dedup)."""
    basis = f"{record_type}|{raw_key.strip().lower()}|{target.strip().lower()}|{(ontology_id or '').strip().lower()}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
async def build_export_records(db: AsyncSession) -> list[dict[str, Any]]:
    """Collect this instance's curator-confirmed mappings as portable records.

    Schema mappings: accepted column → field. Ontology mappings: accepted
    value → ontology term/id. Deduped by content so the bundle is a clean
    knowledge set, not a per-study dump.
    """
    records: dict[str, dict[str, Any]] = {}

    schema_stmt = select(Mapping).where(Mapping.status == "accepted")
    for m in await db.scalars(schema_stmt):
        target = m.curator_field or m.matched_field
        if not target:
            continue
        key = _dedup_key("schema_mapping", m.raw_column, target, None)
        records.setdefault(
            key,
            {
                "record_type": "schema_mapping",
                "raw_key": m.raw_column,
                "accepted_target": target,
                "ontology_id": None,
                "confidence_score": m.confidence_score,
                "dedup_key": key,
            },
        )

    onto_stmt = select(OntologyMapping).where(OntologyMapping.status == "accepted")
    for o in await db.scalars(onto_stmt):
        term = o.curator_term or o.ontology_term
        if not term:
            continue
        raw_key = f"{o.field_name}={o.raw_value}"
        key = _dedup_key("ontology_mapping", raw_key, term, o.ontology_id)
        records.setdefault(
            key,
            {
                "record_type": "ontology_mapping",
                "raw_key": raw_key,
                "accepted_target": term,
                "ontology_id": o.ontology_id,
                "confidence_score": o.confidence_score,
                "dedup_key": key,
            },
        )

    return list(records.values())


async def build_export_bundle(db: AsyncSession) -> dict[str, Any]:
    """Build the signed export envelope: payload + signature + source id."""
    from app.core.settings import settings

    records = await build_export_records(db)
    payload = {
        "bundle_version": fed_sig.BUNDLE_VERSION,
        "source_instance": settings.federation_instance_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mappings": records,
    }
    signature = fed_sig.sign_payload(payload)
    return {
        "payload": payload,
        "signature": signature,
        "source_instance": settings.federation_instance_id,
        "public_key": fed_sig.public_key_hex(),
    }


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
async def record_import(
    db: AsyncSession,
    *,
    payload: dict[str, Any],
    signature: str,
    signature_valid: bool,
    imported_by: int | None,
) -> dict[str, Any]:
    """Persist a received bundle (pending approval) with deduped staged rows.

    Returns a summary dict. Raises ``ValueError`` if this exact bundle
    (payload hash) was already imported.
    """
    source = str(payload.get("source_instance") or "unknown")
    sha = fed_sig.payload_sha256(payload)

    existing = await db.scalar(
        select(FederationImport).where(FederationImport.payload_sha256 == sha)
    )
    if existing is not None:
        raise ValueError("This bundle has already been imported.")

    imp = FederationImport(
        source_instance=source,
        payload_sha256=sha,
        signature=signature,
        signature_valid=signature_valid,
        status="pending",
        imported_by=imported_by,
        mapping_count=0,
    )
    db.add(imp)
    await db.flush()

    # Stage mappings, skipping any already seen from this source (dedup).
    seen_keys = set(
        await db.scalars(
            select(FederationMapping.dedup_key).where(
                FederationMapping.source_instance == source
            )
        )
    )
    added = 0
    for rec in payload.get("mappings", []):
        dedup_key = str(rec.get("dedup_key") or "")
        if not dedup_key or dedup_key in seen_keys:
            continue
        record_type = rec.get("record_type")
        if record_type not in ("schema_mapping", "ontology_mapping"):
            continue
        seen_keys.add(dedup_key)
        db.add(
            FederationMapping(
                import_id=imp.id,
                source_instance=source,
                record_type=record_type,
                raw_key=str(rec.get("raw_key") or ""),
                accepted_target=str(rec.get("accepted_target") or ""),
                ontology_id=rec.get("ontology_id"),
                confidence_score=rec.get("confidence_score"),
                dedup_key=dedup_key,
            )
        )
        added += 1

    imp.mapping_count = added
    await db.flush()
    return {
        "id": imp.id,
        "source_instance": source,
        "signature_valid": signature_valid,
        "status": imp.status,
        "mapping_count": added,
        "payload_sha256": sha,
    }


def _import_to_dict(imp: FederationImport) -> dict[str, Any]:
    return {
        "id": imp.id,
        "source_instance": imp.source_instance,
        "signature_valid": imp.signature_valid,
        "status": imp.status,
        "mapping_count": imp.mapping_count,
        "imported_by": imp.imported_by,
        "reviewed_by": imp.reviewed_by,
        "reviewed_at": imp.reviewed_at.isoformat() if imp.reviewed_at else None,
        "created_at": imp.created_at.isoformat() if imp.created_at else None,
    }


async def list_imports(
    db: AsyncSession, status: str | None = None
) -> list[dict[str, Any]]:
    stmt = select(FederationImport).order_by(FederationImport.created_at.desc())
    if status:
        stmt = stmt.where(FederationImport.status == status)
    return [_import_to_dict(i) for i in await db.scalars(stmt)]


async def get_import(db: AsyncSession, import_id: int) -> dict[str, Any] | None:
    imp = await db.get(FederationImport, import_id)
    if imp is None:
        return None
    out = _import_to_dict(imp)
    rows = await db.scalars(
        select(FederationMapping).where(FederationMapping.import_id == import_id)
    )
    out["mappings"] = [
        {
            "record_type": r.record_type,
            "raw_key": r.raw_key,
            "accepted_target": r.accepted_target,
            "ontology_id": r.ontology_id,
            "confidence_score": r.confidence_score,
        }
        for r in rows
    ]
    return out


async def set_import_status(
    db: AsyncSession, import_id: int, status: str, reviewed_by: int | None
) -> dict[str, Any] | None:
    imp = await db.get(FederationImport, import_id)
    if imp is None:
        return None
    imp.status = status
    imp.reviewed_by = reviewed_by
    imp.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    return _import_to_dict(imp)


async def count_pending(db: AsyncSession) -> int:
    return int(
        await db.scalar(
            select(func.count())
            .select_from(FederationImport)
            .where(FederationImport.status == "pending")
        )
        or 0
    )
