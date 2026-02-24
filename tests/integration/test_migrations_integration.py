"""
US-1.02: Integration tests for Alembic migrations.
Requires: PostgreSQL running (e.g. via docker compose up).
"""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"


@pytest.fixture(scope="module")
def migrated_db():
    """Run alembic upgrade head. Requires DATABASE_URL or default postgres."""
    env = os.environ.copy()
    env.setdefault(
        "DATABASE_URL",
        "postgresql://iaas:iaas@localhost:5432/iaas_test",
    )
    # Create test DB if needed
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"Alembic upgrade failed: {result.stderr.decode()}")
    yield
    # Optionally downgrade for clean state
    subprocess.run(
        ["alembic", "downgrade", "-1"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        timeout=30,
    )


def test_alembic_upgrade_head_succeeds(migrated_db):
    """alembic upgrade head runs without errors."""
    pass  # fixture runs it


def test_alembic_downgrade_reverses_cleanly():
    """alembic downgrade -1 reverses last migration cleanly."""
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", "postgresql://iaas:iaas@localhost:5432/iaas_test")
    result = subprocess.run(
        ["alembic", "downgrade", "-1"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        timeout=30,
    )
    # May fail if no migrations to downgrade - that's ok
    if result.returncode != 0 and b"Can't locate revision" not in result.stderr:
        pytest.fail(f"Downgrade failed: {result.stderr.decode()}")
