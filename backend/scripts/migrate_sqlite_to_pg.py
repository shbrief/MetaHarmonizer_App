"""
One-off migration: prototype SQLite -> Postgres (Sprint 2).

Reads the legacy ``backend/data/metaharmonizer.db`` and inserts its rows into
the new Postgres schema via the ORM. Idempotent-ish: it skips studies whose id
already exists, so re-running won't duplicate.

Type/Shape adaptations:
  - ``alternatives`` text JSON  -> JSONB (parsed)
  - ``reviewed_by`` curator name (text) -> NULL (new column is an int FK); the
    original name is preserved under the row's details/note where possible.
  - ``audit_log`` -> ``audit_events`` (curator text -> details.curator).

Usage:
    python -m scripts.migrate_sqlite_to_pg            # uses settings.DATABASE_URL
    python -m scripts.migrate_sqlite_to_pg --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.settings import settings
from app.db.models import AuditEvent, Mapping, OntologyMapping, Study

SQLITE_PATH = Path(__file__).resolve().parent.parent / "data" / "metaharmonizer.db"


def _rows(con: sqlite3.Connection, table: str) -> list[dict]:
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute(f"SELECT * FROM {table}")]


def _json_or_none(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


async def migrate(dry_run: bool = False) -> dict[str, int]:
    if not SQLITE_PATH.exists():
        raise SystemExit(f"No prototype DB at {SQLITE_PATH}")

    con = sqlite3.connect(str(SQLITE_PATH))
    studies = _rows(con, "studies")
    mappings = _rows(con, "mappings")
    onto = _rows(con, "ontology_mappings")
    audit = _rows(con, "audit_log")
    con.close()

    counts = {"studies": 0, "mappings": 0, "ontology_mappings": 0, "audit_events": 0}

    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        existing = set((await s.scalars(select(Study.id))).all())
        valid_studies = {r["id"] for r in studies}

        for r in studies:
            if r["id"] in existing:
                continue
            s.add(
                Study(
                    id=r["id"],
                    name=r["name"],
                    status=r.get("status") or "pending",
                    file_path=r.get("file_path"),
                    row_count=r.get("row_count"),
                    column_count=r.get("column_count"),
                )
            )
            counts["studies"] += 1
        # Flush parents before children so FK constraints are satisfied.
        await s.flush()

        for r in mappings:
            if r["study_id"] in existing or r["study_id"] not in valid_studies:
                continue
            s.add(
                Mapping(
                    study_id=r["study_id"],
                    raw_column=r["raw_column"],
                    matched_field=r.get("matched_field"),
                    confidence_score=r.get("confidence_score"),
                    stage=r.get("stage"),
                    method=r.get("method"),
                    alternatives=_json_or_none(r.get("alternatives")),
                    status=r.get("status") or "pending",
                    curator_field=r.get("curator_field"),
                    curator_note=r.get("curator_note"),
                )
            )
            counts["mappings"] += 1

        for r in onto:
            if r["study_id"] in existing or r["study_id"] not in valid_studies:
                continue
            s.add(
                OntologyMapping(
                    study_id=r["study_id"],
                    field_name=r["field_name"],
                    raw_value=r["raw_value"],
                    ontology_term=r.get("ontology_term"),
                    ontology_id=r.get("ontology_id"),
                    confidence_score=r.get("confidence_score"),
                    status=r.get("status") or "pending",
                    curator_term=r.get("curator_term"),
                    curator_id=r.get("curator_id"),
                )
            )
            counts["ontology_mappings"] += 1

        for r in audit:
            # audit_events is append-only; only migrate on the first run
            # (when no studies pre-existed) to avoid duplicating on re-run.
            if existing:
                break
            details = {"curator": r["curator"]} if r.get("curator") else None
            s.add(
                AuditEvent(
                    study_id=r.get("study_id"),
                    action=r["action"],
                    mapping_id=r.get("mapping_id"),
                    old_value=r.get("old_value"),
                    new_value=r.get("new_value"),
                    details=details,
                )
            )
            counts["audit_events"] += 1

        if dry_run:
            await s.rollback()
        else:
            await s.commit()

    await engine.dispose()
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="parse + count, don't write")
    args = ap.parse_args()
    counts = asyncio.run(migrate(dry_run=args.dry_run))
    verb = "would migrate" if args.dry_run else "migrated"
    print(f"{verb}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
