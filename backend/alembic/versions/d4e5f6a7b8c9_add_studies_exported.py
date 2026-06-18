"""add studies.exported flag

Curation domain data (studies/mappings/ontology_mappings/audit) now lives in
Postgres instead of the prototype SQLite. The only column the ORM was missing
versus the legacy SQLite schema is ``studies.exported`` — a guard that exempts
an exported study from the session-only logout purge.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "studies",
        sa.Column(
            "exported",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("studies", "exported")
