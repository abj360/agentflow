#!/usr/bin/env python3
"""
graph_events.py --- builds the structural trace events the canvas renders from

Contains:
    ORCHESTRATOR_ID: id of the fixed central node every root task hangs off
    node_created(): builds the frame announcing a newly planned task node
    edge_created(): builds the frame announcing a new dependency edge
    node_status_changed(): builds the frame announcing a task status transition
    events_for_plan(): renders a validated task list as ordered structural events
"""

from collections.abc import Sequence

from apps.api.orchestration.graph_validator import validate_task_graph
from apps.api.orchestration.task_planner import PlannedTask, TaskStatus

ORCHESTRATOR_ID = "orchestrator"


def node_created(task: PlannedTask) -> dict[str, object]:
    """Builds the frame announcing a newly planned task node.

    Args:
        task: The task the planner has just added to the run.

    Returns:
        frame: Structural event the console turns into a canvas node.
    """
    return {"kind": "node_created", "task": task.to_wire()}


def edge_created(source: str, target: str) -> dict[str, object]:
    """Builds the frame announcing a new dependency edge.

    Args:
        source: Id of the task that must finish first.
        target: Id of the task that waits on the source.

    Returns:
        frame: Structural event the console turns into a canvas edge.
    """
    return {"kind": "edge_created", "from": source, "to": target}


def node_status_changed(task_id: str, status: TaskStatus) -> dict[str, object]:
    """Builds the frame announcing a task status transition.

    Args:
        task_id: Id of the task whose status moved.
        status: Lifecycle state the task has moved into.

    Returns:
        frame: Structural event the console applies to an existing node.
    """
    return {"kind": "node_status_changed", "id": task_id, "status": status}


def events_for_plan(tasks: Sequence[PlannedTask]) -> list[dict[str, object]]:
    """Renders a validated task list as the structural events the canvas needs.

    Args:
        tasks: Planned tasks to announce, newest plan first.

    Returns:
        frames: Node frames followed by the edge frames that reference them.
    """
    if not tasks:
        return []
    validate_task_graph(tasks)
    frames = [node_created(task) for task in tasks]
    for task in tasks:
        if not task.depends_on:
            frames.append(edge_created(ORCHESTRATOR_ID, task.id))
        frames.extend(
            edge_created(dependency, task.id) for dependency in task.depends_on
        )
    return frames
