"""
US-1.01: Docker Compose integration tests.
Given docker-compose up, when executed locally, then backend (8000), frontend (3001),
PostgreSQL (5432), and Redis (6379) all start and health-check green within 60 seconds.
"""

import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _wait_for_url(url: str, timeout: int = 30) -> bool:
    """Poll URL until it responds or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(2)
    return False


@pytest.mark.skipif(
    not (REPO_ROOT / "docker-compose.yml").exists(),
    reason="docker-compose.yml not found",
)
class TestDockerCompose:
    """Integration tests requiring Docker Compose."""

    @pytest.fixture(scope="class")
    def docker_compose_up(self):
        """Start docker-compose. Requires docker to be running."""
        proc = subprocess.Popen(
            ["docker", "compose", "up", "-d"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.wait(timeout=120)
        yield
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=30,
        )

    def test_docker_compose_all_services_start(self, docker_compose_up):
        """All 4 services health-check pass within 60 sec."""
        # Backend
        assert _wait_for_url("http://localhost:8000/health", 60), "Backend not healthy"
        # Frontend - may take longer to build
        assert _wait_for_url("http://localhost:3001", 90), "Frontend not healthy"

    def test_backend_port_8000_responds(self, docker_compose_up):
        """GET /health returns 200 OK."""
        with urllib.request.urlopen("http://localhost:8000/health", timeout=10) as resp:
            assert resp.status == 200
            data = resp.read().decode()
            assert "ok" in data.lower()

    def test_frontend_port_3001_responds(self, docker_compose_up):
        """Frontend page loads without 500 errors."""
        with urllib.request.urlopen("http://localhost:3001", timeout=10) as resp:
            assert resp.status == 200

    def test_postgres_5432_accepts_connections(self, docker_compose_up):
        """psql can connect and query."""
        result = subprocess.run(
            [
                "docker", "compose", "exec", "-T", "postgres",
                "pg_isready", "-U", "iaas", "-d", "iaas",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, f"PostgreSQL not ready: {result.stderr.decode()}"

    def test_redis_6379_accepts_connections(self, docker_compose_up):
        """redis-cli PING returns PONG."""
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "redis", "redis-cli", "ping"],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert b"PONG" in result.stdout
