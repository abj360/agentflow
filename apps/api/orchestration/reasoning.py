#!/usr/bin/env python3
"""
reasoning.py --- the contract every model provider answers to

Contains:
    ChatMessage: one turn handed to a provider, in a shape both understand
    OnDelta: called with each fragment of an answer as the model writes it
    ReasoningFailed: raised when a provider cannot answer
    ReasoningClient: what the coordinator and its agents reason through
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Protocol, TypedDict, TypeVar

from pydantic import BaseModel

Schema = TypeVar("Schema", bound=BaseModel)


class ChatMessage(TypedDict):
    """Represents one turn handed to a provider.

    Attributes:
        role: Who spoke, either the reviewer or the assistant.
        content: What was said.
    """

    role: Literal["user", "assistant"]
    content: str


OnDelta = Callable[[str], None]


class ReasoningFailed(RuntimeError):
    """Raised when a provider cannot answer, including a rejected credential."""


class ReasoningClient(Protocol):
    """Defines what the coordinator and its agents reason through.

    Attributes:
        name: Short provider name the console shows.
        model: Model every call from this client is routed to.
    """

    name: str
    model: str

    async def verify(self) -> None:
        """Confirms the credential can actually reach the model."""
        ...

    async def list_models(self) -> list[str]:
        """Returns the models this credential can reason through.

        Returns:
            models: Model ids the caller may pin, best first.
        """
        ...

    async def complete(
        self,
        system: str,
        prompt: str,
        on_delta: OnDelta | None = None,
    ) -> str:
        """Returns the model's prose answer to one rendered prompt.

        Args:
            system: Standing instructions describing the role that is answering.
            prompt: The question or task put to the model.
            on_delta: Called with each fragment as the model writes it, so a
                caller can stream the answer instead of waiting for all of it.

        Returns:
            answer: The model's reply as plain text.
        """
        ...

    async def parse(
        self,
        system: str,
        messages: list[ChatMessage],
        schema: type[Schema],
    ) -> Schema:
        """Returns the model's answer validated against a schema.

        Args:
            system: Standing instructions describing the role that is answering.
            messages: The conversation so far, oldest turn first.
            schema: Shape the answer has to satisfy before it is returned.

        Returns:
            answer: The model's reply, parsed into the requested shape.
        """
        ...
