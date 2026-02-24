"""Add user_invitations table and last_login to users.

Revision ID: 003
Revises: 002
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login", sa.DateTime()))
    op.create_table(
        "user_invitations",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_user_invitations_token", "user_invitations", ["token"])
    op.create_index("ix_user_invitations_user_id", "user_invitations", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_invitations_user_id", "user_invitations")
    op.drop_index("ix_user_invitations_token", "user_invitations")
    op.drop_table("user_invitations")
    op.drop_column("users", "last_login")
