"""append-only audit_events (block UPDATE/DELETE)

Enforces G4 immutability at the database level: a trigger raises on any
UPDATE or DELETE against audit_events, so even an admin (or a bug) cannot
alter the decision log. INSERT and SELECT remain allowed.

Revision ID: a1b2c3d4e5f6
Revises: 8f124a68339b
Create Date: 2026-06-17
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8f124a68339b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_events_block_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is append-only: % is not allowed', TG_OP
                USING ERRCODE = 'restrict_violation';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_no_update_delete
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_block_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update_delete ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS audit_events_block_mutation();")
