#!/usr/bin/env python3
"""
test_roles.py --- unit tests for the four agent role interfaces

Contains:
    test_planner_returns_plan(): verifies the planner emits plan steps
    test_executor_runs_each_step(): verifies the executor covers every step
"""

from apps.api.orchestration.roles import Critic, Executor, Planner, Synthesizer


async def test_planner_returns_plan() -> None:
    """Verifies the planner emits plan steps."""
    update = await Planner().run({"task": "t"})
    assert update["plan"]


async def test_executor_runs_each_step() -> None:
    """Verifies the executor covers every step."""
    update = await Executor().run({"plan": ["a", "b"]})
    assert len(update["results"]) == 2


async def test_critic_accepts_by_default() -> None:
    """Verifies the default critic verdict is accept."""
    update = await Critic().run({"results": ["r"]})
    assert update["critique"] == "accept"


async def test_synthesizer_joins_results() -> None:
    """Verifies the synthesizer merges results into one output."""
    update = await Synthesizer().run({"results": ["x", "y"]})
    assert "x" in update["output"] and "y" in update["output"]


def test_llm_client_is_protocol() -> None:
    """Verifies the LLM client interface stays structural."""
    from apps.api.orchestration.roles import LLMClient

    assert hasattr(LLMClient, "complete")


async def test_planner_without_llm_falls_back() -> None:
    """Verifies the planner works without an LLM client attached."""
    update = await Planner(llm=None).run({"task": "fallback"})
    assert update["plan"] == ["fallback"]


async def test_executor_without_gateway_uses_stub() -> None:
    """Verifies the executor runs with no gateway configured."""
    update = await Executor(tool_gateway=None).run({"plan": ["step"]})
    assert update["results"] == ["done: step"]
