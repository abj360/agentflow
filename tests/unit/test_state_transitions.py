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
