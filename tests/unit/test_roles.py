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


def test_critic_stores_rubric() -> None:
    """Verifies the critic keeps the rubric it was built with."""
    critic = Critic(rubric=("accuracy", "coverage"))
    assert critic.rubric == ("accuracy", "coverage")


async def test_critic_revises_empty_results() -> None:
    """Verifies empty results trigger a revision request."""
    update = await Critic().run({"results": []})
    assert update["critique"] == "revise"


def test_critic_default_rubric_empty() -> None:
    """Verifies the critic starts with an empty rubric by default."""
    assert Critic().rubric == ()


def test_registry_resolves_default_roles() -> None:
    """Verifies all four default roles resolve from the registry."""
    from apps.api.orchestration.roles import RoleRegistry

    registry = RoleRegistry()
    for name in ("planner", "executor", "synthesizer", "critic"):
        assert registry.resolve(name) is not None


def test_registry_unknown_role_raises() -> None:
    """Verifies resolving an unknown role raises a KeyError."""
    from apps.api.orchestration.roles import RoleRegistry

    try:
        RoleRegistry().resolve("oracle")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


async def test_planner_with_llm_uses_completion_lines() -> None:
    """Verifies LLM-backed planning splits completions into steps."""

    class FakeLLM:
        """Returns a fixed multi-line completion."""

        async def complete(self, prompt: str, **kwargs: object) -> str:
            """Returns two canned plan lines."""
            return "step one\nstep two"

    update = await Planner(llm=FakeLLM()).run({"task": "t"})
    assert update["plan"] == ["step one", "step two"]
