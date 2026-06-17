"""
Database layer — SQLAlchemy 2.x (async) over PostgreSQL.

- base.py     — DeclarativeBase + naming conventions
- session.py  — async engine + session factory + FastAPI dependency
- models/     — ORM models, one module per aggregate
                (users, studies, mappings, audit_events, versions, sessions,
                 api_tokens, job_runs, federation_*)

Alembic migrations live in backend/alembic/. Replaces the prototype's
SQLite layer in app/database.py during Sprint 2.
"""
