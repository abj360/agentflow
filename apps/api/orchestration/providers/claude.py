#!/usr/bin/env python3
"""
claude.py --- reasoning through Anthropic's Claude models

Contains:
    DEFAULT_MODEL: Claude model the orchestrator reasons with
    MAX_TOKENS: output ceiling one reasoning call may spend
    THINKING: thinking configuration every reasoning call runs under
    OUTPUT: how hard the model works before it answers
    ClaudeProvider: reasons through Claude for prose answers and typed plans
    ClaudeProvider.verify(): confirms the credential can reach the model
    ClaudeProvider.list_models(): lists the Claude models the key can reach
    ClaudeProvider.complete(): returns Claude's prose answer, streaming it if asked
    ClaudeProvider.parse(): returns Claude's answer validated against a schema
"""

from __future__ import annotations

from typing import TypeVar

from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, OutputConfigParam, ThinkingConfigParam
from pydantic import BaseModel

from apps.api.orchestration.reasoning import ChatMessage, OnDelta, ReasoningFailed

DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 16000

# Adaptive thinking lets Claude decide how long to reason about a goal; high
# effort is what makes a plan worth executing rather than a list of guesses.
THINKING: ThinkingConfigParam = {"type": "adaptive"}
OUTPUT: OutputConfigParam = {"effort": "high"}

Schema = TypeVar("Schema", bound=BaseModel)


class ClaudeProvider:
    """Reasons through Claude for both prose answers and typed plans.

    Attributes:
        model: Claude model every call from this provider is routed to.
    """

    name = "claude"

    def __init__(self, api_key: str, model: str = "") -> None:
        """Initializes the provider against one Claude model.

        Args:
            api_key: Anthropic credential the orchestrator reasons through.
            model: Claude model to pin, or empty to use the default one.
        """
        self.model = model or DEFAULT_MODEL
        self._client = AsyncAnthropic(api_key=api_key)

    async def verify(self) -> None:
        """Confirms the credential can actually reach the model.

        Raises:
            ReasoningFailed: When the credential is rejected or unreachable.
        """
        try:
            await self._client.models.retrieve(self.model)
        except Exception as error:  # provider errors vary; the caller wants one
            raise ReasoningFailed(f"claude rejected the credential: {error}") from error

    async def list_models(self) -> list[str]:
        """Lists the Claude models this credential can reach, newest first.

        Returns:
            models: Model ids the reviewer may pin the team to.

        Raises:
            ReasoningFailed: When the credential cannot list models at all.
        """
        try:
            listed = await self._client.models.list(limit=50)
        except Exception as error:  # provider errors vary; the caller wants one
            raise ReasoningFailed(f"claude would not list its models: {error}") from error
        return [item.id for item in listed.data]

    async def complete(
        self,
        system: str,
        prompt: str,
        on_delta: OnDelta | None = None,
    ) -> str:
        """Returns Claude's prose answer to one rendered prompt.

        A caller that passes on_delta is handed the answer as it is written, so
        a reviewer watching a node can read it being produced rather than
        waiting for the whole thing. Streaming also keeps a long answer from
        hitting the request timeout.

        Args:
            system: Standing instructions describing the role that is answering.
            prompt: The question or task put to the model.
            on_delta: Called with each text fragment as the model writes it.

        Returns:
            answer: The model's reply with its text blocks joined.
        """
        if on_delta is None:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                thinking=THINKING,
                output_config=OUTPUT,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if block.type == "text")

        chunks: list[str] = []
        async with self._client.messages.stream(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            thinking=THINKING,
            output_config=OUTPUT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                chunks.append(text)
                on_delta(text)
        return "".join(chunks)

    async def parse(
        self,
        system: str,
        messages: list[ChatMessage],
        schema: type[Schema],
    ) -> Schema:
        """Returns Claude's answer validated against a schema.

        Args:
            system: Standing instructions describing the role that is answering.
            messages: The conversation so far, oldest turn first.
            schema: Shape the answer has to satisfy before it is returned.

        Returns:
            answer: The model's reply, parsed into the requested shape.

        Raises:
            ReasoningFailed: When the model returned nothing that fits the schema.
        """
        turns: list[MessageParam] = [
            {"role": turn["role"], "content": turn["content"]} for turn in messages
        ]
        response = await self._client.messages.parse(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            thinking=THINKING,
            output_config=OUTPUT,
            messages=turns,
            output_format=schema,
        )
        parsed = response.parsed_output
        if parsed is None:
            raise ReasoningFailed("claude returned nothing matching the schema")
        return parsed
