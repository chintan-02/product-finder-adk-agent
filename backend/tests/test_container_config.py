"""Static container-contract tests that do not require a Docker daemon."""

from __future__ import annotations

import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).parents[1]
DOCKERFILE = (BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")
DOCKERIGNORE = (BACKEND_ROOT / ".dockerignore").read_text(encoding="utf-8")
REQUIREMENTS = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")


class ContainerConfigurationTests(unittest.TestCase):
    def test_uses_supported_python_runtime(self) -> None:
        self.assertIn("FROM python:3.12-slim", DOCKERFILE)

    def test_listens_on_cloud_run_host_and_port(self) -> None:
        self.assertIn("--host 0.0.0.0", DOCKERFILE)
        self.assertIn("${PORT:-8080}", DOCKERFILE)

    def test_runs_as_non_root_user(self) -> None:
        self.assertIn("USER appuser", DOCKERFILE)

    def test_only_runtime_application_is_copied(self) -> None:
        self.assertIn("COPY --chown=appuser:appgroup app ./app", DOCKERFILE)
        self.assertNotIn("COPY . .", DOCKERFILE)

    def test_secrets_are_excluded_from_build_context(self) -> None:
        ignored_patterns = set(DOCKERIGNORE.splitlines())
        self.assertIn(".env", ignored_patterns)
        self.assertIn(".env.*", ignored_patterns)
        self.assertIn("tests", ignored_patterns)

    def test_web_server_dependencies_are_explicit(self) -> None:
        self.assertIn("fastapi", REQUIREMENTS)
        self.assertIn("uvicorn", REQUIREMENTS)


if __name__ == "__main__":
    unittest.main()
