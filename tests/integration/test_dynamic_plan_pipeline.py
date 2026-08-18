#!/usr/bin/env python3
"""
test_dynamic_plan_pipeline.py --- end-to-end tests from a planned task to a canvas frame

Contains:
    test_a_plan_becomes_a_graph_and_a_frame(): verifies plan, wiring, and frames agree
    test_every_edge_frame_names_an_announced_node(): verifies frames are self-consistent
    test_a_run_completes_over_the_dynamic_graph(): verifies the loop still finishes
"""

import pytest

from apps.api.orchestration.graph_events import (
    ORCHESTRATOR_ID,
    events_for_plan,
)
from apps.api.orchestration.loop import run_session
from apps.api.orchestration.state_machine import build_graph
from apps.api.orchestration.task_planner import TaskPlanner

PLAN_TEXT = "gather the sources\ndraft the summary\ncheck the citations"


def test_a_plan_becomes_a_graph_and_a_frame() -> None:
    """Verifies one plan produces matching graph nodes and canvas frames."""
    planned = TaskPlanner().plan(PLAN_TEXT)
    graph = build_graph(planned)
    frames = events_for_plan(planned)
    announced = {
        frame["task"]["id"] for frame in frames if frame["kind"] == "node_created"
    }
    assert announced == {task.id for task in planned}
    assert announced <= set(graph.nodes)


def test_every_edge_frame_names_an_announced_node() -> None:
    """Verifies no edge frame points at a node the canvas was never told about."""
    planned = TaskPlanner().plan(PLAN_TEXT)
    frames = events_for_plan(planned)
    announced = {
        frame["task"]["id"] for frame in frames if frame["kind"] == "node_created"
    }
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
