#!/usr/bin/env python3
"""
test_state_transitions.py --- unit tests for state machine transitions

Contains:
    make_state(): builds a graph state dict for tests
    test_planner_to_executor_edge(): verifies the planner feeds the executor
"""

from apps.api.orchestration.state_machine import build_graph, executor_node, planner_node


def make_state(**overrides: object) -> dict:
    """Builds a graph state dict for tests.

    Args:
        overrides: Field overrides applied on the default state.

    Returns:
        state: Graph state dict with sensible defaults.
    """
    state = {"task": "t", "plan": [], "results": [], "critique": "", "iterations": 0}
    state.update(overrides)
    return state


def test_planner_to_executor_edge() -> None:
    """Verifies the planner feeds the executor."""
    after_plan = planner_node(make_state(task="do it"))
    after_exec = executor_node(after_plan)
    assert after_exec["results"]


def test_planner_update_only_touches_plan() -> None:
    """Verifies the planner update leaves other fields intact."""
    state = make_state(task="keep", results=["untouched"])
    after = planner_node(state)
    assert after["results"] == ["untouched"]


def test_executor_to_critic_edge() -> None:
    """Verifies the executor feeds the critic."""
    from apps.api.orchestration.state_machine import critic_node

    after_exec = executor_node(make_state(plan=["x"]))
    after_critic = critic_node(after_exec)
    assert after_critic["iterations"] == 1


def test_revise_edge_loops_to_planner() -> None:
    """Verifies a revise verdict routes back to planning."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="revise")) == "revise"
