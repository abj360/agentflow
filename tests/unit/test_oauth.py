#!/usr/bin/env python3
"""
test_oauth.py --- unit tests for the OAuth 2.1 client flow

Contains:
    test_authorize_url_contains_client_id(): verifies the consent URL parameters
    test_is_expired_past_expiry(): verifies an expired token reports expired
"""

from apps.api.mcp_servers.oauth import OAuthClient, OAuthClientConfig, TokenSet

CONFIG = OAuthClientConfig(
    server_name="github-mcp",
    client_id="client-123",
    authorize_url="https://idp.example/authorize",
    token_url="https://idp.example/token",
    scopes=("tools:read", "tools:call"),
)


def build_client(http: object = None) -> OAuthClient:
    """Builds an OAuth client for tests.

    Args:
        http: Fake async HTTP client, or None.

    Returns:
        client: Configured OAuth client.
    """
    return OAuthClient(CONFIG, http)


def test_authorize_url_contains_client_id() -> None:
    """Verifies the consent URL parameters."""
    url = build_client().build_authorize_url(state="abc")
    assert "client_id=client-123" in url
    assert "state=abc" in url


def test_is_expired_past_expiry() -> None:
    """Verifies an expired token reports expired."""
    tokens = TokenSet(access_token="t", refresh_token=None, expires_at=0.0)
    assert tokens.is_expired() is True


def test_is_expired_future_token() -> None:
    """Verifies a token with time left is not expired."""
    tokens = TokenSet(access_token="t", refresh_token=None,
                      expires_at=9_999_999_999.0)
    assert tokens.is_expired() is False
