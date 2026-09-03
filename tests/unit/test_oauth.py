#!/usr/bin/env python3
"""
test_oauth.py --- unit tests for the OAuth 2.1 client flow

Contains:
    test_authorize_url_contains_client_id(): verifies the consent URL parameters
    test_is_expired_past_expiry(): verifies an expired token reports expired
"""

from urllib.parse import parse_qs, urlparse

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
    tokens = TokenSet(access_token="t", refresh_token=None, expires_at=9_999_999_999.0)
    assert tokens.is_expired() is False


def test_authorize_url_scopes_joined() -> None:
    """Verifies scopes are space-joined in the consent URL."""
    url = build_client().build_authorize_url(state="s")
    query = parse_qs(urlparse(url).query)
    assert query["scope"] == ["tools:call tools:read"]


def test_authorize_url_starts_with_endpoint() -> None:
    """Verifies the consent URL targets the configured endpoint."""
    url = build_client().build_authorize_url(state="s")
    assert url.startswith("https://idp.example/authorize?")


def test_code_challenge_deterministic() -> None:
    """Verifies the PKCE challenge is stable per verifier."""
    from apps.api.mcp_servers.oauth import code_challenge

    assert code_challenge("v") == code_challenge("v")


def test_code_verifier_urlsafe() -> None:
    """Verifies the PKCE verifier contains only URL-safe characters."""
    from apps.api.mcp_servers.oauth import generate_code_verifier

    verifier = generate_code_verifier()
    assert " " not in verifier and "+" not in verifier


def test_code_challenge_differs_per_verifier() -> None:
    """Verifies different verifiers yield different challenges."""
    from apps.api.mcp_servers.oauth import code_challenge

    assert code_challenge("a") != code_challenge("b")


def test_is_expired_within_skew_window() -> None:
    """Verifies the skew window treats near-expiry tokens as expired."""
    import time

    tokens = TokenSet(access_token="t", refresh_token=None, expires_at=time.time() + 10)
    assert tokens.is_expired(skew_seconds=30) is True


def test_token_cache_round_trip() -> None:
    """Verifies tokens cache and read back per server."""
    from apps.api.mcp_servers.oauth import TokenCache

    cache = TokenCache()
    tokens = TokenSet(access_token="a", refresh_token="r", expires_at=1.0)
    cache.put("srv", tokens)
    assert cache.get("srv") == tokens


def test_token_cache_discard() -> None:
    """Verifies discarding drops the cached tokens."""
    from apps.api.mcp_servers.oauth import TokenCache

    cache = TokenCache()
    cache.put("srv", TokenSet(access_token="a", refresh_token=None, expires_at=1.0))
    cache.discard("srv")
    assert cache.get("srv") is None


async def test_exchange_code_returns_tokens() -> None:
    """Verifies code exchange maps the provider payload to a TokenSet."""

    class FakeResponse:
        """Mimics an HTTP response carrying a token payload."""

        def json(self) -> dict:
            """Returns the canned token payload."""
            return {"access_token": "at-1", "refresh_token": "rt-1", "expires_in": 3600}

    class FakeHttp:
        """Mimics the async HTTP client for token calls."""

        async def post(self, url: str, data: dict) -> FakeResponse:
            """Returns the canned token response."""
            return FakeResponse()

    tokens = await build_client(FakeHttp()).exchange_code("code-1")
    assert tokens.access_token == "at-1"
    assert tokens.refresh_token == "rt-1"


async def test_refresh_keeps_old_refresh_token_when_omitted() -> None:
    """Verifies refresh preserves the refresh token when not re-issued."""

    class FakeResponse:
        """Mimics an HTTP response carrying a token payload."""

        def json(self) -> dict:
            """Returns a payload without a new refresh token."""
            return {"access_token": "at-2", "expires_in": 3600}

    class FakeHttp:
        """Mimics the async HTTP client for token calls."""

        async def post(self, url: str, data: dict) -> FakeResponse:
            """Returns the canned token response."""
            return FakeResponse()

    old = TokenSet(access_token="at-1", refresh_token="rt-1", expires_at=0.0)
    tokens = await build_client(FakeHttp()).refresh(old)
    assert tokens.access_token == "at-2"
    assert tokens.refresh_token == "rt-1"


def test_token_cache_isolated_per_server() -> None:
    """Verifies servers' cached tokens don't leak across names."""
    from apps.api.mcp_servers.oauth import TokenCache

    cache = TokenCache()
    cache.put("srv-a", TokenSet(access_token="a", refresh_token=None, expires_at=1.0))
    assert cache.get("srv-b") is None


async def test_exchange_code_error_payload_raises() -> None:
    """Verifies an error payload from the provider raises OAuthError."""
    from apps.api.mcp_servers.oauth import OAuthError

    class FakeResponse:
        """Mimics an HTTP response carrying an error payload."""

        def json(self) -> dict:
            """Returns a canned OAuth error payload."""
            return {"error": "invalid_grant", "error_description": "code expired"}

    class FakeHttp:
        """Mimics the async HTTP client for token calls."""

        async def post(self, url: str, data: dict) -> FakeResponse:
            """Returns the canned error response."""
            return FakeResponse()

    try:
        await build_client(FakeHttp()).exchange_code("bad-code")
    except OAuthError as exc:
        assert exc.error == "invalid_grant"
        return
    raise AssertionError("expected OAuthError")


def test_oauth_error_message_includes_code() -> None:
    """Verifies the OAuthError message carries the provider's code."""
    from apps.api.mcp_servers.oauth import OAuthError

    err = OAuthError("access_denied", "user declined")
    assert "access_denied" in str(err)


def test_oauth_error_without_description() -> None:
    """Verifies the OAuthError renders cleanly without a description."""
    from apps.api.mcp_servers.oauth import OAuthError

    assert str(OAuthError("server_error")) == "server_error"


def test_build_client_without_http() -> None:
    """Verifies a client can be built before wiring the HTTP client."""
    client = build_client()
    assert client.config.server_name == "github-mcp"


def test_token_cache_starts_empty() -> None:
    """Verifies a fresh token cache has no entries."""
    from apps.api.mcp_servers.oauth import TokenCache

    assert TokenCache().tokens == {}


def test_authorize_url_uses_response_type_code() -> None:
    """Verifies the consent URL requests an authorization code."""
    url = build_client().build_authorize_url(state="s")
    assert "response_type=code" in url


def test_scopes_param_sorted() -> None:
    """Verifies scopes render sorted for stable URLs."""
    from apps.api.mcp_servers.oauth import scopes_param

    assert scopes_param(("b", "a")) == "a b"


def test_scopes_param_empty() -> None:
    """Verifies an empty scope tuple renders as an empty string."""
    from apps.api.mcp_servers.oauth import scopes_param

    assert scopes_param(()) == ""


def test_authorize_url_scopes_sorted_after_refactor() -> None:
    """Verifies the consent URL keeps working after the scopes refactor."""
    url = build_client().build_authorize_url(state="s")
    query = parse_qs(urlparse(url).query)
    assert query["scope"] == ["tools:call tools:read"]
    assert " " not in urlparse(url).query  # the space must arrive encoded


def test_config_is_frozen() -> None:
    """Verifies the client config is immutable."""
    from dataclasses import FrozenInstanceError

    import pytest

    with pytest.raises(FrozenInstanceError):
        CONFIG.client_id = "other"


def test_token_set_is_frozen() -> None:
    """Verifies token sets are immutable value objects."""
    from dataclasses import FrozenInstanceError

    import pytest

    tokens = TokenSet(access_token="t", refresh_token=None, expires_at=0.0)
    with pytest.raises(FrozenInstanceError):
        tokens.access_token = "x"
