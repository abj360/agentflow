#!/usr/bin/env python3
"""
test_dynamic_plan_pipeline.py --- end-to-end tests from a planned task to a canvas frame

Contains:
    test_a_plan_becomes_a_graph_and_a_frame(): verifies plan, wiring, and frames agree
    test_every_edge_frame_names_an_announced_node(): verifies frames are self-consistent
    test_a_run_completes_over_the_dynamic_graph(): verifies the loop still finishes
    test_a_single_step_plan_still_reaches_the_canvas(): verifies the degenerate plan
    test_batching_a_plan_costs_one_frame(): verifies the whole plan ships together
"""

import pytest

from apps.api.orchestration.graph_events import (
    ORCHESTRATOR_ID,
    StructuralEventBatcher,
    events_for_plan,
    structural_frame,
)
from apps.api.orchestration.graph_validator import GraphValidationError
from apps.api.orchestration.loop import run_session
from apps.api.orchestration.state_machine import build_graph
from apps.api.orchestration.task_planner import PlannedTask, TaskPlanner

PLAN_TEXT = "gather the sources\ndraft the summary\ncheck the citations"


def test_a_plan_becomes_a_graph_and_a_frame() -> None:
    """Verifies one plan produces matching graph nodes and canvas frames."""
    planned = TaskPlanner().plan(PLAN_TEXT)
    graph = build_graph(planned)
    frames = events_for_plan(planned)
    announced = {frame["task"]["id"] for frame in frames if frame["kind"] == "node_created"}
    assert announced == {task.id for task in planned}
    assert announced <= set(graph.nodes)


def test_every_edge_frame_names_an_announced_node() -> None:
    """Verifies no edge frame points at a node the canvas was never told about."""
    planned = TaskPlanner().plan(PLAN_TEXT)
    frames = events_for_plan(planned)
    announced = {frame["task"]["id"] for frame in frames if frame["kind"] == "node_created"}
    announced.add(ORCHESTRATOR_ID)
    for frame in frames:
        if frame["kind"] == "edge_created":
            assert frame["from"] in announced
            assert frame["to"] in announced


@pytest.mark.asyncio
async def test_a_run_completes_over_the_dynamic_graph() -> None:
    """Verifies a session still runs to completion on a planner-built topology."""
    result = await run_session("it-canvas-1", PLAN_TEXT)
    assert result["status"] in {"completed", "revision-bounded"}


def test_a_single_step_plan_still_reaches_the_canvas() -> None:
    """Verifies a one-objective plan produces a node and an orchestrator edge."""
    frames = events_for_plan(TaskPlanner().plan("just do it"))
    assert [frame["kind"] for frame in frames] == [
        "node_created",
        "edge_created",
    ]
    assert frames[1]["from"] == ORCHESTRATOR_ID


def test_batching_a_plan_costs_one_frame() -> None:
    """Verifies a whole plan reaches the console as a single graph_delta frame."""
    frames = events_for_plan(TaskPlanner().plan(PLAN_TEXT))
    batcher = StructuralEventBatcher(max_batch=len(frames))
    batches = [batcher.add(frame) for frame in frames]
    assert batches[:-1] == [None] * (len(frames) - 1)
    assert len(structural_frame("run-1", batches[-1] or [])["events"]) == len(frames)


@pytest.mark.asyncio
async def test_a_run_reports_every_task_it_starts() -> None:
    """Verifies the status sink sees every planned task move through running."""
    seen: list[tuple[str, str]] = []
    await run_session(
        "it-canvas-2", PLAN_TEXT, on_status=lambda task_id, status: seen.append((task_id, status))
    )
    started = {task_id for task_id, status in seen if status == "running"}
    assert started == {task.id for task in TaskPlanner().plan(PLAN_TEXT)}


@pytest.mark.asyncio
async def test_a_completed_run_bounds_no_branch() -> None:
    """Verifies a run that finishes cleanly reports no exhausted branches."""
    result = await run_session("it-canvas-3", PLAN_TEXT)
    assert result["bounded_branches"] == []


def test_a_batched_plan_reaches_the_canvas_in_one_frame() -> None:
    """Verifies a whole plan is announced in a single graph_delta frame."""
    frames = events_for_plan(TaskPlanner().plan(PLAN_TEXT))
    frame = structural_frame("run-9", frames)
    assert frame["kind"] == "graph_delta"
    assert len(frame["events"]) == len(frames), (
        "the whole plan has to travel to the console inside a single frame"
    )


def test_a_cyclic_plan_never_produces_a_frame() -> None:
    """Verifies validation runs before anything is rendered as a frame."""
    tasks = [
        PlannedTask(id="task-1", title="a", depends_on=("task-2",)),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
    ]
    with pytest.raises(GraphValidationError):
        events_for_plan(tasks)


@pytest.mark.asyncio
async def test_a_run_streams_its_graph_and_then_its_statuses() -> None:
    """Verifies one run produces a plan, a wired graph, and a status for every task."""
    seen: list[tuple[str, str]] = []
    result = await run_session(
        "it-canvas-4",
        PLAN_TEXT,
        on_status=lambda task_id, status: seen.append((task_id, status)),
    )
    planned = TaskPlanner().plan(PLAN_TEXT)
    frames = events_for_plan(planned)

    announced = {
        frame["task"]["id"] for frame in frames if frame["kind"] == "node_created"
    }
    started = {task_id for task_id, status in seen if status == "running"}
    finished = {task_id for task_id, status in seen if status == "done"}

    assert announced == started == finished
    assert result["status"] in {"completed", "revision-bounded"}


def test_a_fanned_out_plan_reaches_the_canvas_as_parallel_roots() -> None:
    """Verifies independent objectives arrive as roots off the orchestrator."""
    from apps.api.orchestration.state_machine import plan_for

    frames = events_for_plan(plan_for(PLAN_TEXT))
    sources = {
        frame["from"] for frame in frames if frame["kind"] == "edge_created"
    }
    assert sources == {ORCHESTRATOR_ID}


def test_every_announced_node_carries_the_counters_the_canvas_reads() -> None:
    """Verifies no node frame reaches the console missing a field it renders."""
    for frame in events_for_plan(TaskPlanner().plan(PLAN_TEXT)):
        if frame["kind"] != "node_created":
            continue
        assert set(frame["task"]) == {
            "id",
            "title",
            "assignee",
            "status",
            "dependsOn",
            "startedAt",
            "finishedAt",
            "tokens",
            "retries",
            "toolCallCount",
        }
