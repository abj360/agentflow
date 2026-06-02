#!/usr/bin/env python3
"""
test_state_machine.py --- unit tests for the orchestration state machine

Contains:
    test_graph_has_three_nodes(): verifies planner/executor/critic nodes exist
    test_planner_seeds_plan_with_task(): verifies the planner puts the task in the plan
"""

from apps.api.orchestration.state_machine import build_graph, planner_node


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


def test_graph_has_three_nodes() -> None:
    """Verifies planner/executor/critic nodes exist."""
    graph = build_graph()
    assert {"planner", "executor", "critic"} <= set(graph.nodes)


def test_planner_seeds_plan_with_task() -> None:
    """Verifies the planner puts the task in the plan."""
    assert planner_node(make_state(task="ship it"))["plan"] == ["ship it"]


def test_route_after_critic_accepts_on_verdict() -> None:
    """Verifies an accept verdict ends the run."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="accept")) == "accept"


def test_route_after_critic_revises_on_reject() -> None:
    """Verifies a non-accept verdict loops back to the planner."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="revise")) == "revise"


def test_critic_increments_iterations() -> None:
    """Verifies each critic pass bumps the iteration counter."""
    from apps.api.orchestration.state_machine import critic_node

    assert critic_node(make_state())["iterations"] == 1


def test_critic_revises_when_no_results() -> None:
    """Verifies empty executor output triggers a revision request."""
    from apps.api.orchestration.state_machine import critic_node

    assert critic_node(make_state())["critique"] == "revise"
