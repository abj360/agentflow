#!/usr/bin/env python3
"""
llm.py --- picks and holds the model provider the orchestrator reasons through

Contains:
    PROVIDERS: the provider names a caller may choose between
    ProviderStatus: what the console is told about the configured provider
    UnknownProvider: raised when a caller names a provider that does not exist
    configure(): verifies a credential and makes that provider the live one
    choose_model(): repins the live client to another model from the same key
    get_llm(): returns the live client, or None when nothing is configured
    is_configured(): whether the orchestrator currently has a model to reason with
    provider_status(): what the console shows about the configured provider
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Literal, get_args

from pydantic import BaseModel

from apps.api.orchestration.providers import ClaudeProvider, OpenAIProvider
from apps.api.orchestration.reasoning import ReasoningClient, ReasoningFailed

ProviderName = Literal["claude", "openai"]
PROVIDERS: tuple[str, ...] = get_args(ProviderName)

_BUILDERS: dict[str, Callable[..., ReasoningClient]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}

_live: ReasoningClient | None = None
_key: str = ""
_models: list[str] = []


class UnknownProvider(ValueError):
    """Raised when a caller names a provider the orchestrator does not have."""


class ProviderStatus(BaseModel):
    """Represents what the console is told about the configured provider.

    Attributes:
        configured: Whether the orchestrator can reason at all right now.
        provider: Provider currently in use, empty when none is.
        model: Model currently in use, empty when none is.
        providers: Every provider a caller may choose between.
        models: Models this credential can reach, so the reviewer picks one
            rather than being handed whatever the provider defaults to.
    """

    configured: bool
    provider: str = ""
    model: str = ""
    providers: list[str] = []
    models: list[str] = []


async def configure(provider: str, api_key: str, model: str = "") -> ProviderStatus:
    """Verifies a credential and makes that provider the one the team reasons through.

    The key is verified before it is kept, so a reviewer who mistypes one is told
    immediately rather than at the first goal they set. It is held in this process
    only: never written to disk, never returned to a caller.

    Args:
        provider: Which provider the credential belongs to.
        api_key: The credential to reason through.
        model: Model to pin, or empty to take the provider's default.

    Returns:
        status: The provider and model now in use, and the models on offer.

    Raises:
        UnknownProvider: When the named provider does not exist.
        ReasoningFailed: When the credential is rejected or reaches no model.
    """
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise UnknownProvider(f"unknown provider: {provider}")

    client = builder(api_key, model)
    await client.verify()

    global _live, _key, _models
    _live = client
    _key = api_key
    # Listing is a courtesy, not a gate: a key that can reason but cannot list
    # models should still leave the reviewer with a working orchestrator.
    try:
        _models = await client.list_models()
    except ReasoningFailed:
        _models = [client.model]
    return provider_status()


async def choose_model(model: str) -> ProviderStatus:
    """Repins the live client to another model reachable with the same key.

    Args:
        model: Model the reviewer wants the team to reason through.

    Returns:
        status: The provider and model now in use.

    Raises:
        UnknownProvider: When nothing is configured, or the model is not on offer.
        ReasoningFailed: When the model turns out to be unreachable after all.
    """
    client = get_llm()
    if client is None or not _key:
        raise UnknownProvider("no provider is configured to change the model of")
    if _models and model not in _models:
        raise UnknownProvider(f"{client.name} does not offer model: {model}")
    return await configure(client.name, _key, model)


def get_llm() -> ReasoningClient | None:
    """Returns the live client, or None when nothing has been configured.

    A credential in the environment is honoured on first use, so a deployment can
    set one without anyone opening the console.

    Returns:
        client: The live client, or None so callers can degrade rather than crash.
    """
    global _live
    if _live is None and os.environ.get("ANTHROPIC_API_KEY"):
        _live = ClaudeProvider(api_key=os.environ["ANTHROPIC_API_KEY"])
    if _live is None and os.environ.get("OPENAI_API_KEY"):
        _live = OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"])
    return _live


def is_configured() -> bool:
    """Reports whether the orchestrator currently has a model to reason with.

    Returns:
        configured: True when a provider is available to the process.
    """
    return get_llm() is not None


def provider_status() -> ProviderStatus:
    """Returns what the console shows about the configured provider.

    Returns:
        status: The provider and model in use, and the choices on offer.
    """
    client = get_llm()
    if client is None:
        return ProviderStatus(configured=False, providers=list(PROVIDERS))
    return ProviderStatus(
        configured=True,
        provider=client.name,
        model=client.model,
        providers=list(PROVIDERS),
        models=list(_models) or [client.model],
    )
