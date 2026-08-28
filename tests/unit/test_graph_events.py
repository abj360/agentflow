#!/usr/bin/env python3
"""
test_graph_events.py --- unit tests for the structural trace event builders

Contains:
    test_node_created_carries_the_wire_task(): verifies the node frame wraps to_wire()
    test_edge_created_names_both_ends(): verifies the edge frame carries source and target
    test_node_status_changed_carries_the_new_status(): verifies status frames
    test_events_for_plan_emits_nodes_before_edges(): verifies frame ordering
    test_events_for_plan_on_empty_plan_emits_nothing(): verifies the empty case
    test_wire_task_carries_cost_counters(): verifies tokens/retries/tool calls ship
    test_fresh_task_reports_no_cost_yet(): verifies a planned task starts at zero
    test_batcher_holds_events_until_the_frame_is_full(): verifies buffering
    test_batcher_returns_a_whole_frame_once_full(): verifies the automatic flush
    test_structural_frame_names_its_run(): verifies the frame carries the run id
    test_flushing_an_empty_batcher_sends_nothing(): verifies the empty flush
    test_traced_events_match_the_untraced_ones(): verifies tracing is transparent
"""

from apps.api.orchestration.graph_events import (
    ORCHESTRATOR_ID,
    StructuralEventBatcher,
    edge_created,
    events_for_plan,
    node_created,
    node_status_changed,
    structural_frame,
    traced_events_for_plan,
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


def test_fresh_task_reports_no_cost_yet() -> None:
    """Verifies a freshly planned task reports no timing and no spend."""
    wire = node_created(PlannedTask(id="task-1", title="draft"))["task"]
    assert wire["startedAt"] is None
    assert (wire["tokens"], wire["retries"], wire["toolCallCount"]) == (0, 0, 0)


def test_wire_task_carries_cost_counters() -> None:
    """Verifies the canvas receives the per-task cost counters it renders."""
    task = PlannedTask(id="task-1", title="fetch", tokens=120, retries=1, tool_call_count=3)
    wire = node_created(task)["task"]
    assert (wire["tokens"], wire["retries"], wire["toolCallCount"]) == (120, 1, 3)


def test_batcher_holds_events_until_the_frame_is_full() -> None:
    """Verifies a partly filled batcher writes no frame at all."""
    batcher = StructuralEventBatcher(max_batch=3)
    assert batcher.add(node_status_changed("task-1", "running")) is None
    assert batcher.add(node_status_changed("task-2", "running")) is None


def test_batcher_returns_a_whole_frame_once_full() -> None:
    """Verifies the batcher hands back every buffered event in one go."""
    batcher = StructuralEventBatcher(max_batch=2)
    batcher.add(node_status_changed("task-1", "running"))
    batch = batcher.add(node_status_changed("task-2", "running"))
    assert batch is not None
    assert len(batch) == 2


def test_structural_frame_names_its_run() -> None:
    """Verifies a batched frame says which run it belongs to."""
    frame = structural_frame("run-7", [node_status_changed("task-1", "done")])
    assert frame["kind"] == "graph_delta"
    assert frame["runId"] == "run-7"


def test_flushing_an_empty_batcher_sends_nothing() -> None:
    """Verifies flushing an idle batcher never writes an empty frame."""
    assert StructuralEventBatcher().flush() == []


def test_traced_events_match_the_untraced_ones() -> None:
    """Verifies tracing a plan changes nothing about the frames it emits."""
    planned = TaskPlanner().plan("first\nsecond")
    assert traced_events_for_plan("run-7", planned) == events_for_plan(planned)


def test_a_batcher_reports_what_it_is_holding() -> None:
    """Verifies the batcher can be asked how much is still unsent."""
    batcher = StructuralEventBatcher(max_batch=4)
    assert batcher.pending() == 0
    batcher.add(node_status_changed("task-1", "running"))
    assert batcher.pending() == 1
    batcher.flush()
    assert batcher.pending() == 0


def test_tracing_an_empty_plan_emits_no_spans() -> None:
    """Verifies an empty plan is traced as nothing rather than as one span."""
    assert traced_events_for_plan("run-7", ()) == []


def test_every_traced_frame_keeps_its_kind() -> None:
    """Verifies tracing never rewrites the frames it passes through."""
    frames = traced_events_for_plan("run-7", TaskPlanner().plan("a\nb"))
    assert {str(frame["kind"]) for frame in frames} == {
        "node_created",
        "edge_created",
    }
