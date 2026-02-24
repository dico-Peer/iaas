"""Add refresh_tokens table and default organization.

Revision ID: 002
Revises: 001
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # Insert default org for registration (if none exists)
    op.execute("""
        INSERT INTO organizations (id, name, slug, settings_json)
        SELECT gen_random_uuid(), 'Default Organization', 'default', '{}'
        WHERE NOT EXISTS (SELECT 1 FROM organizations LIMIT 1)
    """)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", "refresh_tokens")
    op.drop_table("refresh_tokens")
    # Note: we don't remove the default org as it may have users
