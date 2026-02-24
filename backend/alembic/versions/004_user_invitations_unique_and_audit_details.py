"""Add UniqueConstraint on user_invitations.token and details_json to audit_logs.

Revision ID: 004
Revises: 003
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_user_invitations_token", "user_invitations")
    op.create_unique_constraint("uq_user_invitations_token", "user_invitations", ["token"])
    op.add_column("audit_logs", sa.Column("details_json", sa.JSON()))


def downgrade() -> None:
    op.drop_column("audit_logs", "details_json")
    op.drop_constraint("uq_user_invitations_token", "user_invitations", type_="unique")
    op.create_index("ix_user_invitations_token", "user_invitations", ["token"])
