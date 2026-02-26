"""Add help_text, options_json, scale_config to questions; probing_depth 1-10.

Revision ID: 005
Revises: 004
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("interview_questions", sa.Column("help_text", sa.Text()))
    op.add_column("interview_questions", sa.Column("options_json", sa.JSON()))
    op.add_column("interview_questions", sa.Column("scale_config", sa.JSON()))
    op.execute("UPDATE interview_questions SET probing_depth = 1 WHERE probing_depth < 1")
    op.drop_constraint("ck_questions_probing", "interview_questions", type_="check")
    op.create_check_constraint(
        "ck_questions_probing",
        "interview_questions",
        "probing_depth BETWEEN 1 AND 10",
    )


def downgrade() -> None:
    op.drop_constraint("ck_questions_probing", "interview_questions", type_="check")
    op.create_check_constraint(
        "ck_questions_probing",
        "interview_questions",
        "probing_depth BETWEEN 0 AND 5",
    )
    op.drop_column("interview_questions", "scale_config")
    op.drop_column("interview_questions", "options_json")
    op.drop_column("interview_questions", "help_text")
