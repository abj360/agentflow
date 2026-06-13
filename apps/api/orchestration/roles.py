#!/usr/bin/env python3
"""
roles.py --- Planner/Executor/Synthesizer/Critic role interfaces

Contains:
    AgentRole: protocol every orchestration role implements
    Planner: breaks the task into an ordered plan
    Executor: runs plan steps through governed tools
    Synthesizer: merges step outputs into the final answer
    Critic: reviews plans and outputs, requesting revisions
"""

from typing import Protocol


class AgentRole(Protocol):
    """Defines the contract every orchestration role implements."""

    async def run(self, state: dict) -> dict:
        """Executes the role against the current orchestration state.

        Args:
            state: Current shared orchestration state.

        Returns:
            update: Partial state update produced by this role.
        """
        ...


class Planner:
    """Breaks the task into an ordered plan.

    Attributes:
        llm: Completion client used to draft plans.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        """Initializes the planner with an optional LLM client.

        Args:
            llm: Completion client used to draft plans.
        """
        self.llm = llm

    async def run(self, state: dict) -> dict:
        """Produces a plan from the task in the current state.

        Args:
            state: Current shared orchestration state.

        Returns:
            update: State update carrying the plan steps.
        """
        return {"plan": [state["task"]]}


class Executor:
    """Runs plan steps through governed tools.

    Attributes:
        tool_gateway: Governed entrypoint for MCP tool calls.
    """

    def __init__(self, tool_gateway: object | None = None) -> None:
        """Initializes the executor with an optional tool gateway.

        Args:
            tool_gateway: Governed entrypoint for MCP tool calls.
        """
        self.tool_gateway = tool_gateway

    async def run(self, state: dict) -> dict:
        """Executes every plan step and collects the outputs.

        Args:
            state: Current shared orchestration state.

        Returns:
            update: State update carrying one result per plan step.
        """
        return {"results": [f"done: {step}" for step in state["plan"]]}


class Synthesizer:
    """Merges step outputs into the final answer."""

    async def run(self, state: dict) -> dict:
        """Merges the collected step outputs into one answer.

        Args:
            state: Current shared orchestration state.

        Returns:
            update: State update carrying the synthesized output.
        """
        return {"output": "\n".join(state["results"])}


class Critic:
    """Reviews plans and outputs, requesting revisions.

    Attributes:
        rubric: Ordered checks the critic scores outputs against.
    """

    def __init__(self, rubric: tuple[str, ...] = ()) -> None:
        """Initializes the critic with a scoring rubric.

        Args:
            rubric: Ordered checks the critic scores outputs against.
        """
        self.rubric = rubric

    async def run(self, state: dict) -> dict:
        """Reviews the current results and returns a verdict.

        Args:
            state: Current shared orchestration state.

        Returns:
            update: State update carrying the critique verdict.
        """
        if not state["results"]:
            return {"critique": "revise"}
        return {"critique": "accept"}


class LLMClient(Protocol):
    """Defines the completion interface roles use to call a model."""

    async def complete(self, prompt: str, **kwargs: object) -> str:
        """Returns the model completion for a prompt.

        Args:
            prompt: The rendered prompt text.
            kwargs: Provider-specific completion options.

        Returns:
            completion: The model's response text.
        """
        ...
