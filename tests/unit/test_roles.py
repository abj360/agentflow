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
