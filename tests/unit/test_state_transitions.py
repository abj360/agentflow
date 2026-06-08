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
    state = {
        "task": "t",
        "plan": [],
        "results": [],
        "critique": "",
        "iterations": 0,
    }
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


def test_executor_update_preserves_plan() -> None:
    """Verifies the executor leaves the plan in place."""
    after = executor_node(make_state(plan=["stay"]))
    assert after["plan"] == ["stay"]


def test_accept_edge_ends_run() -> None:
    """Verifies an accept verdict routes to the end."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="accept")) == "accept"


def test_critic_update_only_touches_verdict_fields() -> None:
    """Verifies the critic leaves plan and results intact."""
    from apps.api.orchestration.state_machine import critic_node

    after = critic_node(make_state(plan=["p"], results=["r"]))
    assert after["plan"] == ["p"] and after["results"] == ["r"]


def test_validate_graph_flags_missing_critic() -> None:
    """Verifies validation reports a missing critic node."""

    class PlannerOnlyGraph:
        """Graph stand-in with only a planner node."""

        nodes = {"planner": object()}

    from apps.api.orchestration.state_machine import validate_graph

    assert validate_graph(PlannerOnlyGraph()) != []


def test_full_cycle_two_iterations() -> None:
    """Verifies plan/exec/critic chains over two simulated cycles."""
    from apps.api.orchestration.state_machine import critic_node

    state = make_state(task="cycle")
    for _ in range(2):
        state = planner_node(state)
        state = executor_node(state)
        state = critic_node(state)
    assert state["iterations"] == 2


def test_validate_graph_detects_sound_graph() -> None:
    """Verifies the production graph passes its own validation."""
    from apps.api.orchestration.state_machine import validate_graph

    assert validate_graph(build_graph()) == []
