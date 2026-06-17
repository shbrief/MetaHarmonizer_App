"""add job_failures dead-letter table (spec §6.3)

Records jobs that exhausted their retries so an admin can re-queue or discard
them (Sprint 4 surfaces the UI). Completes the Sprint 2 persistence schema.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_failures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_run_id",
            sa.Integer(),
            sa.ForeignKey("job_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("study_id", sa.String(length=64), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("error_code", sa.String(length=40), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload", JSONB(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_job_failures_study_id", "job_failures", ["study_id"])


def downgrade() -> None:
    op.drop_index("ix_job_failures_study_id", table_name="job_failures")
    op.drop_table("job_failures")
