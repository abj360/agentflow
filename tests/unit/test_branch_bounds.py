#!/usr/bin/env python3
"""
test_branch_bounds.py --- unit tests for the per-branch revision bound

Contains:
    test_fresh_branch_has_spent_nothing(): verifies an unseen branch starts at zero
    test_recording_a_revision_only_charges_one_branch(): verifies budgets stay separate
    test_branch_under_its_bound_still_revises(): verifies routing while budget remains
    test_branch_at_its_bound_stops_revising(): verifies the bound ends that branch
    test_a_fresh_branch_has_its_whole_budget(): verifies the starting budget
    test_a_spent_branch_reports_no_budget_left(): verifies an exhausted branch
"""

from apps.api.orchestration.state_machine import (
    MAX_REVISIONS,
    bounded_branches,
    branch_budget_remaining,
    branch_revision_count,
    record_branch_revision,
    route_after_critic,
)
from apps.api.orchestration.task_planner import PlannedTask, branch_roots


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
        "critique": "revise",
        "iterations": 0,
    }
    state.update(overrides)
    return state


def test_fresh_branch_has_spent_nothing() -> None:
    """Verifies a branch nobody has revised yet reports a zero count."""
    assert branch_revision_count(make_state(), "task-1") == 0


def test_recording_a_revision_only_charges_one_branch() -> None:
    """Verifies revising one branch leaves the other branch's budget intact."""
    counters = record_branch_revision(make_state(), "task-1")
    assert counters == {"task-1": 1}
    assert branch_revision_count(make_state(branch_revisions=counters), "task-2") == 0


def test_branch_under_its_bound_still_revises() -> None:
    """Verifies a branch with budget left is sent back to the orchestrator."""
    state = make_state(active_branch="task-1", branch_revisions={"task-1": 1})
    assert route_after_critic(state) == "revise"


def test_branch_at_its_bound_stops_revising() -> None:
    """Verifies a branch that has spent its budget ends instead of looping."""
    state = make_state(active_branch="task-1", branch_revisions={"task-1": MAX_REVISIONS})
    assert route_after_critic(state) == "bounded"


def test_branch_roots_group_a_chain_under_its_first_task() -> None:
    """Verifies every task in a chain is budgeted against the chain's root."""
    tasks = [
        PlannedTask(id="task-1", title="a"),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
        PlannedTask(id="task-3", title="c", depends_on=("task-2",)),
    ]
    assert branch_roots(tasks) == {
        "task-1": "task-1",
        "task-2": "task-1",
        "task-3": "task-1",
    }


def test_branch_roots_keep_independent_branches_apart() -> None:
    """Verifies two independent chains are budgeted separately."""
    tasks = [
        PlannedTask(id="task-1", title="a"),
        PlannedTask(id="task-2", title="b"),
        PlannedTask(id="task-3", title="c", depends_on=("task-2",)),
    ]
    roots = branch_roots(tasks)
    assert roots["task-1"] != roots["task-3"]


def test_a_fresh_branch_has_its_whole_budget() -> None:
    """Verifies an untouched branch may still spend every revision."""
    assert branch_budget_remaining(make_state(), "task-1") == MAX_REVISIONS


def test_a_spent_branch_reports_no_budget_left() -> None:
    """Verifies a branch at its bound reports nothing left to spend."""
    state = make_state(branch_revisions={"task-1": MAX_REVISIONS})
    assert branch_budget_remaining(state, "task-1") == 0
    assert bounded_branches(state) == ("task-1",)
