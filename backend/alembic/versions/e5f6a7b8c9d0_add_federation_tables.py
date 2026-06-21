"""add federation-lite tables (G1)

Provenance for the signed cross-instance mapping exchange:
- ``federation_imports``  : one received bundle, pending local approval (Q10).
- ``federation_mappings`` : the curator-confirmed mappings it carried, with a
  per-source unique ``dedup_key`` so re-imports don't double-count.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "federation_imports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_instance", sa.String(length=120), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column(
            "signature_valid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("mapping_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("imported_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("payload_sha256", name="federation_imports_payload_sha256_key"),
        sa.CheckConstraint(
            "status in ('pending','approved','rejected')",
            name="fed_import_status_valid",
        ),
    )
    op.create_table(
        "federation_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "import_id",
            sa.Integer(),
            sa.ForeignKey("federation_imports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_instance", sa.String(length=120), nullable=False),
        sa.Column("record_type", sa.String(length=20), nullable=False),
        sa.Column("raw_key", sa.Text(), nullable=False),
        sa.Column("accepted_target", sa.Text(), nullable=False),
        sa.Column("ontology_id", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("dedup_key", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_instance", "dedup_key", name="federation_mapping_source_dedup"
        ),
        sa.CheckConstraint(
            "record_type in ('schema_mapping','ontology_mapping')",
            name="fed_mapping_type_valid",
        ),
    )
    op.create_index(
        "ix_federation_mappings_import_id", "federation_mappings", ["import_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_federation_mappings_import_id", table_name="federation_mappings")
    op.drop_table("federation_mappings")
    op.drop_table("federation_imports")
