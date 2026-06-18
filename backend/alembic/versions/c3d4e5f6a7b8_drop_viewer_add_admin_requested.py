"""drop viewer role + add admin_requested

Roles collapse to ('curator','admin') — the viewer role was unused. Any
existing viewers become curators. Adds ``users.admin_requested`` so a curator
can request admin access at registration for an existing admin to approve.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the admin-request flag.
    op.add_column(
        "users",
        sa.Column(
            "admin_requested",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Collapse the role set: migrate any viewers to curators, then tighten the
    # CHECK constraint to the two remaining roles.
    op.execute("UPDATE users SET role = 'curator' WHERE role = 'viewer'")
    op.drop_constraint(op.f("ck_users_role_valid"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_role_valid"), "users", "role in ('curator','admin')"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_role_valid"), "users", type_="check")
    op.create_check_constraint(
        op.f("ck_users_role_valid"), "users", "role in ('viewer','curator','admin')"
    )
    op.drop_column("users", "admin_requested")
