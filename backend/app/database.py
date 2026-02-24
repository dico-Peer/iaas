"""Database connection and session."""
import os
from contextlib import contextmanager
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://iaas:iaas@localhost:5432/iaas")


@contextmanager
def get_connection():
    """Get a database connection with dict cursor."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_default_org_id(conn) -> Optional[str]:
    """Get the first organization ID, or None if none exist."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM organizations LIMIT 1")
        row = cur.fetchone()
        return str(row["id"]) if row else None


def ensure_default_org(conn) -> str:
    """Ensure a default org exists; return its ID."""
    org_id = get_default_org_id(conn)
    if org_id:
        return org_id
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO organizations (name, slug, settings_json) VALUES (%s, %s, %s) RETURNING id",
            ("Default Organization", "default", "{}"),
        )
        row = cur.fetchone()
        return str(row["id"])
