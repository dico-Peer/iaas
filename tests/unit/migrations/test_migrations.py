"""
US-1.02: PostgreSQL Database Schema & Migrations
Test Specification: Verify migrations create all required tables with correct schema.
"""

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"

# Required tables per acceptance criteria
REQUIRED_TABLES = [
    "organizations",
    "users",
    "interview_projects",
    "interview_questions",
    "agents",
    "agent_versions",
    "conversations",
    "messages",
    "voice_sessions",
    "analysis_runs",
    "themes",
    "theme_quotes",
    "distribution_links",
    "invitations",
    "audit_logs",
    "participants",
    "cost_tracking",
]


@pytest.fixture
def db_connection():
    """Create a test database connection. Requires PostgreSQL running."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            user=os.getenv("PGUSER", "iaas"),
            password=os.getenv("PGPASSWORD", "iaas"),
            dbname=os.getenv("PGDATABASE", "iaas_test"),
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


def test_migration_creates_all_required_tables(db_connection):
    """All 17+ tables exist after alembic upgrade head."""
    cur = db_connection.cursor()
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT LIKE 'alembic%'
    """)
    tables = {row[0] for row in cur.fetchall()}
    cur.close()

    for table in REQUIRED_TABLES:
        assert table in tables, f"Table '{table}' must exist"


def test_messages_table_schema(db_connection):
    """messages table: content=TEXT, sentiment_score=FLOAT CHECK(-1,1), sequence_number=INT."""
    cur = db_connection.cursor()
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'messages'
        AND column_name IN ('content', 'sentiment_score', 'sequence_number')
    """)
    cols = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()

    assert "content" in cols, "messages.content must exist"
    assert cols["content"] == "text", "messages.content must be TEXT"
    assert "sentiment_score" in cols, "messages.sentiment_score must exist"
    assert cols["sentiment_score"] in ("double precision", "real"), "sentiment_score must be FLOAT"
    assert "sequence_number" in cols, "messages.sequence_number must exist"
    assert cols["sequence_number"] in ("integer", "bigint"), "sequence_number must be INT"


def test_pgvector_extension_installed(db_connection):
    """pgvector extension is installed."""
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    cur.close()
    assert row is not None, "pgvector extension must be installed"


def test_alembic_migrations_directory_exists():
    """Alembic migrations directory exists in backend."""
    migrations_dir = BACKEND_ROOT / "alembic" / "versions"
    assert migrations_dir.is_dir(), "backend/alembic/versions must exist"


def test_alembic_config_exists():
    """alembic.ini exists in backend."""
    alembic_ini = BACKEND_ROOT / "alembic.ini"
    assert alembic_ini.exists(), "backend/alembic.ini must exist"


def test_initial_migration_file_exists():
    """Initial migration creates required tables."""
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    files = sorted(f for f in versions_dir.glob("*.py") if not f.name.startswith("__"))
    assert len(files) >= 1, "At least one migration file must exist"
    # Check that initial migration (001) contains key tables and pgvector
    migration_content = files[0].read_text()
    assert "organizations" in migration_content
    assert "users" in migration_content
    assert "messages" in migration_content
    assert "vector" in migration_content or "pgvector" in migration_content.lower()
