"""Pytest configuration - add backend to path, set test DB."""
import os
import sys
from pathlib import Path

# Use test DB for pytest if not set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://iaas:iaas@localhost:5432/iaas",
    )

backend = Path(__file__).resolve().parent / "backend"
if str(backend) not in sys.path:
    sys.path.insert(0, str(backend))
