#!/usr/bin/env python3
"""
test_config_env.py --- unit tests for environment-driven settings

Contains:
    test_shared_env_keys_are_ignored(): verifies non-API keys do not crash startup
    test_agentflow_keys_are_applied(): verifies prefixed keys reach the settings
    test_defaults_hold_without_env(): verifies defaults apply with no .env present
"""

from pathlib import Path

from apps.api.config import Settings

SHARED_ENV = """\
AGENTFLOW_DATABASE_URL=postgresql+asyncpg://agentflow:s3cret@postgres:5432/agentflow
AGENTFLOW_RATE_LIMIT_REQUESTS=7
POSTGRES_PASSWORD=s3cret
NEXT_PUBLIC_API_URL=http://localhost:8000
MCP_OAUTH_CLIENT_ID=
"""


def write_env(tmp_path: Path, body: str) -> Path:
    """Writes a .env file and returns its path.

    Args:
        tmp_path: Directory the env file is written into.
        body: Contents of the env file.

    Returns:
        env_path: Path to the written env file.
    """
    env_path = tmp_path / ".env"
    env_path.write_text(body)
    return env_path


def test_shared_env_keys_are_ignored(tmp_path: Path) -> None:
    """Verifies keys meant for other services do not fail validation.

    The .env file is shared with postgres, the console and the MCP client, so
    forbidding unknown keys made `cp .env.example .env` crash the API at import.
    """
    settings = Settings(_env_file=write_env(tmp_path, SHARED_ENV))
    assert settings.database_url.endswith("/agentflow")


def test_agentflow_keys_are_applied(tmp_path: Path) -> None:
    """Verifies AGENTFLOW_-prefixed keys actually reach the settings."""
    settings = Settings(_env_file=write_env(tmp_path, SHARED_ENV))
    assert "s3cret" in settings.database_url
    assert settings.rate_limit_requests == 7


def test_defaults_hold_without_env(tmp_path: Path) -> None:
    """Verifies tracing stays off and limits default with no env file."""
    settings = Settings(_env_file=write_env(tmp_path, ""))
    assert settings.otel_exporter_otlp_endpoint == ""
    assert settings.rate_limit_requests == 120
