#!/usr/bin/env python3
"""
test_graph_events.py --- unit tests for the structural trace event builders

Contains:
    test_node_created_carries_the_wire_task(): verifies the node frame wraps to_wire()
    test_edge_created_names_both_ends(): verifies the edge frame carries source and target
    test_node_status_changed_carries_the_new_status(): verifies status frames
    test_events_for_plan_emits_nodes_before_edges(): verifies frame ordering
    test_events_for_plan_on_empty_plan_emits_nothing(): verifies the empty case
"""

from apps.api.orchestration.graph_events import (
    ORCHESTRATOR_ID,
    edge_created,
    events_for_plan,
    node_created,
    node_status_changed,
)
from apps.api.orchestration.task_planner import PlannedTask, TaskPlanner


def test_node_created_carries_the_wire_task() -> None:
    """Verifies the node frame wraps the task's wire shape."""
    frame = node_created(PlannedTask(id="task-1", title="research"))
    assert frame["kind"] == "node_created"
    assert frame["task"]["dependsOn"] == []


def test_edge_created_names_both_ends() -> None:
    """Verifies the edge frame carries both ends of the dependency."""
    frame = edge_created("task-1", "task-2")
    assert (frame["from"], frame["to"]) == ("task-1", "task-2")


def test_node_status_changed_carries_the_new_status() -> None:
    """Verifies the status frame names the task and its new state."""
    frame = node_status_changed("task-1", "running")
    assert frame["id"] == "task-1"
    assert frame["status"] == "running"


def test_events_for_plan_emits_nodes_before_edges() -> None:
    """Verifies every node frame lands before the edges referencing it."""
    planned = TaskPlanner().plan("first\nsecond")
    kinds = [frame["kind"] for frame in events_for_plan(planned)]
    assert kinds == ["node_created", "node_created", "edge_created", "edge_created"]


def test_events_for_plan_hangs_roots_off_the_orchestrator() -> None:
    """Verifies a task with no dependencies is linked to the orchestrator."""
    planned = TaskPlanner().plan("only step")
    edges = [frame for frame in events_for_plan(planned) if frame["kind"] == "edge_created"]
    assert edges[0]["from"] == ORCHESTRATOR_ID


def test_events_for_plan_on_empty_plan_emits_nothing() -> None:
    """Verifies a plan with no tasks produces no structural frames."""
    assert events_for_plan(()) == []
