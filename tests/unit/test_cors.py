#!/usr/bin/env python3
"""
test_cors.py --- unit tests for browser access from the console origin

Contains:
    test_preflight_is_allowed(): verifies the console origin passes preflight
    test_response_carries_allow_origin(): verifies a GET echoes the origin back
    test_unknown_origin_is_not_allowed(): verifies other origins are refused
    test_allowed_origins_parsing(): verifies the comma-separated setting splits
"""

from fastapi.testclient import TestClient

from apps.api.config import Settings
from apps.api.main import create_app

CONSOLE_ORIGIN = "http://localhost:3000"


def build_client() -> TestClient:
    """Builds a test client over the real application.

    Returns:
        client: Test client bound to the configured app.
    """
    return TestClient(create_app())


def test_preflight_is_allowed() -> None:
    """Verifies the console origin clears the CORS preflight.

    The console runs on :3000 and the API on :8000, so every fetch it makes
    is cross-origin and the browser blocks it without this.
    """
    response = build_client().options(
        "/approvals/pending",
        headers={
            "Origin": CONSOLE_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == CONSOLE_ORIGIN


def test_response_carries_allow_origin() -> None:
    """Verifies a real request echoes the allowed origin back."""
    response = build_client().get("/health", headers={"Origin": CONSOLE_ORIGIN})
    assert response.headers["access-control-allow-origin"] == CONSOLE_ORIGIN


def test_unknown_origin_is_not_allowed() -> None:
    """Verifies an unlisted origin is not granted access."""
    response = build_client().get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origins_parsing() -> None:
    """Verifies the comma-separated origin setting splits and trims."""
    settings = Settings(cors_allow_origins="http://a.test , http://b.test ,")
    assert settings.allowed_origins() == ["http://a.test", "http://b.test"]
