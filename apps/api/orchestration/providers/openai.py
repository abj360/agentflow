#!/usr/bin/env python3
"""
openai.py --- reasoning through OpenAI's chat models

Contains:
    PREFERRED_MODELS: models tried in order when the account exposes them
    MAX_TOKENS: output ceiling one reasoning call may spend
    OpenAIProvider: reasons through OpenAI for prose answers and typed plans
    OpenAIProvider.verify(): confirms the credential and picks a live model
    OpenAIProvider.list_models(): lists the chat models the key can reach
    OpenAIProvider.complete(): returns the model's prose answer, streaming it if asked
    OpenAIProvider.parse(): returns the model's answer validated against a schema
"""

from __future__ import annotations

from typing import TypeVar

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from apps.api.orchestration.reasoning import ChatMessage, OnDelta, ReasoningFailed

PREFERRED_MODELS = ("gpt-5", "gpt-4.1", "gpt-4o")
MAX_TOKENS = 16000

Schema = TypeVar("Schema", bound=BaseModel)


class OpenAIProvider:
    """Reasons through OpenAI for both prose answers and typed plans.

    Attributes:
        model: Model every call from this provider is routed to, chosen on verify.
    """

    name = "openai"

    def __init__(self, api_key: str, model: str = "") -> None:
        """Initializes the provider, leaving the model to be resolved on verify.

        Args:
            api_key: OpenAI credential the orchestrator reasons through.
            model: Model to pin, or empty to pick the best the account exposes.
        """
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def verify(self) -> None:
        """Confirms the credential and pins the best model the account exposes.

        The model is resolved here rather than hard-coded because which models an
        OpenAI account can reach varies, and a guessed id fails at the worst time.

        Raises:
            ReasoningFailed: When the credential is rejected or exposes no model.
        """
        try:
            listed = await self._client.models.list()
            available = {item.id for item in listed.data}
        except Exception as error:  # provider errors vary; the caller wants one
            raise ReasoningFailed(f"openai rejected the credential: {error}") from error

        if self.model and self.model in available:
            return
        for candidate in PREFERRED_MODELS:
            if candidate in available:
                self.model = candidate
                return
        chat_models = sorted(name for name in available if name.startswith("gpt-"))
        if not chat_models:
            raise ReasoningFailed("this openai account exposes no chat model")
        self.model = chat_models[-1]

    async def list_models(self) -> list[str]:
        """Lists the chat models this credential can reach.

        The account's full model list includes embeddings, audio, and image
        models the team cannot reason through, so it is filtered down to the
        families that answer a chat completion.

        Returns:
            models: Chat model ids the reviewer may pin the team to.

        Raises:
            ReasoningFailed: When the credential cannot list models at all.
        """
        try:
            listed = await self._client.models.list()
        except Exception as error:  # provider errors vary; the caller wants one
            raise ReasoningFailed(f"openai would not list its models: {error}") from error
        chat = [item.id for item in listed.data if item.id.startswith(("gpt-", "o1", "o3", "o4"))]
        preferred = [name for name in PREFERRED_MODELS if name in chat]
        return preferred + sorted(name for name in chat if name not in preferred)

    async def complete(
        self,
        system: str,
        prompt: str,
        on_delta: OnDelta | None = None,
    ) -> str:
        """Returns the model's prose answer to one rendered prompt.

        A caller that passes on_delta is handed the answer as it is written, so
        a reviewer watching a node can read it being produced rather than
        waiting for the whole thing.

        Args:
            system: Standing instructions describing the role that is answering.
            prompt: The question or task put to the model.
            on_delta: Called with each text fragment as the model writes it.

        Returns:
            answer: The model's reply as plain text.
        """
        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system),
            ChatCompletionUserMessageParam(role="user", content=prompt),
        ]
        if on_delta is None:
            response = await self._client.chat.completions.create(
                model=self.model,
                max_completion_tokens=MAX_TOKENS,
                messages=messages,
            )
            return response.choices[0].message.content or ""

        chunks: list[str] = []
        stream = await self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=MAX_TOKENS,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            text = chunk.choices[0].delta.content if chunk.choices else None
            if text:
                chunks.append(text)
                on_delta(text)
        return "".join(chunks)

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

        Raises:
            ReasoningFailed: When the model returned nothing that fits the schema.
        """
        turns: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system)
        ]
        for turn in messages:
            turns.append(
                ChatCompletionUserMessageParam(role="user", content=turn["content"])
                if turn["role"] == "user"
                else ChatCompletionAssistantMessageParam(role="assistant", content=turn["content"])
            )
        response = await self._client.chat.completions.parse(
            model=self.model,
            max_completion_tokens=MAX_TOKENS,
            messages=turns,
            response_format=schema,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ReasoningFailed("openai returned nothing matching the schema")
        return parsed
