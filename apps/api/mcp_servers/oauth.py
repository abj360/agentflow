#!/usr/bin/env python3
"""
oauth.py --- OAuth 2.1 client flow for external MCP servers

Contains:
    OAuthClientConfig: connection and credential settings for one MCP server
    TokenSet: access/refresh token pair with expiry
    OAuthClient: runs the authorization-code flow and refreshes tokens
"""

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthClientConfig:
    """Declares connection and credential settings for one MCP server.

    Attributes:
        server_name: Identifier of the external MCP server.
        client_id: Registered OAuth client id.
        authorize_url: Authorization endpoint URL.
        token_url: Token endpoint URL.
        scopes: Requested OAuth scopes.
    """

    server_name: str
    client_id: str
    authorize_url: str
    token_url: str
    scopes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TokenSet:
    """Represents an access/refresh token pair with expiry.

    Attributes:
        access_token: Token presented to the MCP server.
        refresh_token: Token used to renew the access token, when issued.
        expires_at: Epoch seconds when the access token stops being valid.
    """

    access_token: str
    refresh_token: str | None
    expires_at: float

    def is_expired(self, skew_seconds: float = 30.0) -> bool:
        """Reports whether the access token has expired.

        Args:
            skew_seconds: Clock-skew tolerance before true expiry.

        Returns:
            expired: True when the token is past its expiry.
        """
        return time.time() >= self.expires_at - skew_seconds


class OAuthClient:
    """Runs the authorization-code flow and refreshes tokens.

    Attributes:
        config: OAuth client configuration for one MCP server.
        http: Async HTTP client used for token endpoint calls.
    """

    def __init__(self, config: OAuthClientConfig, http) -> None:
        """Initializes the client with config and an HTTP client.

        Args:
            config: OAuth client configuration for one MCP server.
            http: Async HTTP client used for token endpoint calls.
        """
        self.config = config
        self.http = http

    def build_authorize_url(self, state: str) -> str:
        """Builds the authorization URL for the user consent step.

        Args:
            state: CSRF state token echoed back by the provider.

        Returns:
            url: Fully-formed authorization URL.
        """
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "state": state,
            "scope": " ".join(self.config.scopes),
        }
        query = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{self.config.authorize_url}?{query}"

    async def exchange_code(self, code: str) -> TokenSet:
        """Exchanges an authorization code for a token set.

        Args:
            code: Authorization code from the consent redirect.

        Returns:
            tokens: Newly issued token set.
        """
        response = await self.http.post(
            self.config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.client_id,
            },
        )
        body = response.json()
        return TokenSet(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            expires_at=time.time() + body.get("expires_in", 3600),
        )

    async def refresh(self, tokens: TokenSet) -> TokenSet:
        """Refreshes an expiring token set.

        Args:
            tokens: The current token set with a refresh token.

        Returns:
            refreshed: Newly issued token set.
        """
        response = await self.http.post(
            self.config.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": tokens.refresh_token,
                "client_id": self.config.client_id,
            },
        )
        body = response.json()
        return TokenSet(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token", tokens.refresh_token),
            expires_at=time.time() + body.get("expires_in", 3600),
        )


def generate_code_verifier() -> str:
    """Generates a PKCE code verifier.

    Returns:
        verifier: Random URL-safe verifier string.
    """
    return secrets.token_urlsafe(64)


def code_challenge(verifier: str) -> str:
    """Derives the PKCE S256 code challenge from a verifier.

    Args:
        verifier: The PKCE code verifier.

    Returns:
        challenge: Base64url-encoded SHA-256 of the verifier.
    """
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
