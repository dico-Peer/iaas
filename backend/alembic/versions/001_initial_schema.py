"""Initial schema - organizations, users, projects, agents, conversations, etc.

Revision ID: 001
Revises:
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "organizations",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("sso_enabled", sa.Boolean(), server_default="false"),
        sa.Column("sso_provider", sa.String(50)),
        sa.Column("sso_config", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('system_admin', 'org_admin', 'designer', 'analyst', 'viewer')")
    op.create_check_constraint("ck_users_status", "users", "status IN ('active', 'invited', 'inactive', 'suspended')")

    op.create_table(
        "interview_projects",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("research_objectives", sa.Text()),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("settings_json", sa.JSON(), nullable=False, server_default='{"max_duration_minutes": 60, "require_consent": true}'),
        sa.Column("modality_type", sa.String(50), server_default="text"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime()),
    )
    op.create_check_constraint("ck_projects_status", "interview_projects", "status IN ('draft', 'active', 'paused', 'completed', 'archived')")
    op.create_check_constraint("ck_projects_modality", "interview_projects", "modality_type IN ('text', 'voice', 'hybrid')")

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("probing_depth", sa.Integer(), server_default="1"),
        sa.Column("branching_rules", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "order_index", name="uq_questions_project_order"),
    )
    op.create_check_constraint("ck_questions_type", "interview_questions", "question_type IN ('open', 'multiple_choice', 'scale', 'ranking', 'branching_gate')")
    op.create_check_constraint("ck_questions_probing", "interview_questions", "probing_depth BETWEEN 0 AND 5")

    op.create_table(
        "distribution_links",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime()),
        sa.UniqueConstraint("token", name="uq_distribution_links_token"),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", sa.UUID(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_version"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.UUID(), sa.ForeignKey("agents.id"), nullable=False),
        sa.Column("distribution_link_id", sa.UUID(), sa.ForeignKey("distribution_links.id")),
        sa.Column("participant_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(50), nullable=False, server_default="invited"),
        sa.Column("session_token", sa.String(255), nullable=False),
        sa.Column("consent_given", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("session_token", name="uq_conversations_session_token"),
    )
    op.create_check_constraint("ck_conversations_status", "conversations", "status IN ('invited', 'in_progress', 'paused', 'completed', 'abandoned')")

    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_type", sa.String(50), nullable=False),
        sa.Column("agent_id", sa.UUID(), sa.ForeignKey("agents.id")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(50), server_default="text"),
        sa.Column("sentiment_score", sa.Float()),
        sa.Column("sequence_number", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_messages_sender", "messages", "sender_type IN ('agent', 'participant', 'system')")
    op.create_check_constraint("ck_messages_sentiment", "messages", "sentiment_score IS NULL OR (sentiment_score BETWEEN -1 AND 1)")

    op.create_table(
        "voice_sessions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime()),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_check_constraint("ck_analysis_status", "analysis_runs", "status IN ('pending', 'processing', 'complete', 'failed')")

    op.create_table(
        "themes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analysis_run_id", sa.UUID(), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("theme_name", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "theme_quotes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("theme_id", sa.UUID(), sa.ForeignKey("themes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.UUID(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("quote_text", sa.Text(), nullable=False),
        sa.Column("tagged_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "invitations",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_id", sa.UUID(), sa.ForeignKey("distribution_links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_invitations_status", "invitations", "status IN ('sent', 'opened', 'started', 'completed', 'bounced', 'opted_out')")

    op.create_table(
        "participants",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "email", name="uq_participants_project_email"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.UUID()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "cost_tracking",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("interview_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cost_type", sa.String(50)),
        sa.Column("cost_amount", sa.Numeric(10, 4)),
        sa.Column("cost_currency", sa.String(3), server_default="EUR"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_check_constraint("ck_cost_type", "cost_tracking", "cost_type IN ('llm', 'voice_stt', 'voice_tts', 'storage', 'infrastructure')")


def downgrade() -> None:
    op.drop_table("cost_tracking")
    op.drop_table("audit_logs")
    op.drop_table("participants")
    op.drop_table("invitations")
    op.drop_table("theme_quotes")
    op.drop_table("themes")
    op.drop_table("analysis_runs")
    op.drop_table("voice_sessions")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("agent_versions")
    op.drop_table("agents")
    op.drop_table("distribution_links")
    op.drop_table("interview_questions")
    op.drop_table("interview_projects")
    op.drop_table("users")
    op.drop_table("organizations")
    op.execute("DROP EXTENSION IF EXISTS vector")
