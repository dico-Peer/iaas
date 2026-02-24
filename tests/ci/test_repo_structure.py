"""
US-1.01: Monorepo Setup & CI/CD Pipeline
Test Specification: Verify repository structure contains required directories and files.

Given the repository root, when inspected, then it contains:
- /backend (FastAPI)
- /frontend (Next.js 14)
- /shared (shared types)
- /tests
- /infrastructure (Terraform)
- docker-compose.yml
- Makefile
- .github/workflows/ci.yml
"""

import os
from pathlib import Path

# Repository root is 2 levels up from tests/ci/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_repo_contains_backend_directory():
    """Backend directory exists for FastAPI application."""
    assert (REPO_ROOT / "backend").is_dir(), "backend/ directory must exist"


def test_repo_contains_frontend_directory():
    """Frontend directory exists for Next.js application."""
    assert (REPO_ROOT / "frontend").is_dir(), "frontend/ directory must exist"


def test_repo_contains_shared_directory():
    """Shared directory exists for shared types."""
    assert (REPO_ROOT / "shared").is_dir(), "shared/ directory must exist"


def test_repo_contains_tests_directory():
    """Tests directory exists."""
    assert (REPO_ROOT / "tests").is_dir(), "tests/ directory must exist"


def test_repo_contains_infrastructure_directory():
    """Infrastructure directory exists for Terraform."""
    assert (REPO_ROOT / "infrastructure").is_dir(), "infrastructure/ directory must exist"


def test_repo_contains_docker_compose():
    """docker-compose.yml exists at repository root."""
    assert (REPO_ROOT / "docker-compose.yml").exists(), "docker-compose.yml must exist"


def test_repo_contains_makefile():
    """Makefile exists at repository root."""
    assert (REPO_ROOT / "Makefile").exists(), "Makefile must exist"


def test_repo_contains_ci_workflow():
    """GitHub Actions CI workflow exists."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), ".github/workflows/ci.yml must exist"


def test_makefile_has_test_target():
    """Makefile contains 'test' target."""
    makefile = REPO_ROOT / "Makefile"
    content = makefile.read_text()
    assert "test:" in content or "test " in content, "Makefile must have 'test' target"


def test_makefile_has_lint_target():
    """Makefile contains 'lint' target."""
    makefile = REPO_ROOT / "Makefile"
    content = makefile.read_text()
    assert "lint:" in content or "lint " in content, "Makefile must have 'lint' target"


def test_makefile_has_type_check_target():
    """Makefile contains 'type-check' target."""
    makefile = REPO_ROOT / "Makefile"
    content = makefile.read_text()
    assert "type-check" in content, "Makefile must have 'type-check' target"
