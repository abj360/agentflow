#!/usr/bin/env python3
"""
graph_events.py --- builds the structural trace events the canvas renders from

Contains:
    ORCHESTRATOR_ID: id of the fixed central node every root task hangs off
    node_created(): builds the frame announcing a newly planned task node
    edge_created(): builds the frame announcing a new dependency edge
    node_status_changed(): builds the frame announcing a task status transition
    MAX_EVENTS_PER_FRAME: structural events one WebSocket frame may carry
    events_for_plan(): renders a validated task list as ordered structural events
    traced_events_for_plan(): emits a plan's structural events under OTel spans
    structural_frame(): wraps a batch of structural events in one frame
    StructuralEventBatcher: coalesces structural events into whole frames
    StructuralEventBatcher.pending(): how many events are waiting to be sent
"""

from collections.abc import Sequence

from apps.api.observability.tracing import set_span_attribute, structural_span
from apps.api.orchestration.graph_validator import validate_task_graph
from apps.api.orchestration.task_planner import PlannedTask, TaskStatus

ORCHESTRATOR_ID = "orchestrator"
MAX_EVENTS_PER_FRAME = 32


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
        frames.extend(edge_created(dependency, task.id) for dependency in task.depends_on)
    return frames


def structural_frame(run_id: str, events: Sequence[dict[str, object]]) -> dict[str, object]:
    """Wraps a batch of structural events in the single frame the console reads.

    Args:
        run_id: Run the batched events belong to.
        events: Structural events to deliver together.

    Returns:
        frame: One graph_delta frame carrying every event in the batch.
    """
    return {"kind": "graph_delta", "runId": run_id, "events": list(events)}


class StructuralEventBatcher:
    """Coalesces structural events so one plan costs one WebSocket frame.

    A run that plans twelve tasks used to write twelve frames, and the console
    re-laid the canvas out on each one. Batching keeps that to a single layout,
    which is the difference between one relaxation pass and twelve.

    Attributes:
        max_batch: Events that accumulate before the batcher flushes on its own.
    """

    def __init__(self, max_batch: int = MAX_EVENTS_PER_FRAME) -> None:
        """Initializes the batcher with an empty buffer.

        Args:
            max_batch: Events that accumulate before an automatic flush.
        """
        self.max_batch = max_batch
        self._buffered: list[dict[str, object]] = []

    def add(self, event: dict[str, object]) -> list[dict[str, object]] | None:
        """Buffers one structural event, returning a full batch when it fills.

        Args:
            event: Structural event to deliver to the console.

        Returns:
            batch: The events to send now, or None while the buffer has room.
        """
        self._buffered.append(event)
        if len(self._buffered) < self.max_batch:
            return None
        return self.flush()

    def pending(self) -> int:
        """Returns how many events are waiting for a frame to carry them.

        Returns:
            pending: Events buffered since the last flush.
        """
        return len(self._buffered)

    def flush(self) -> list[dict[str, object]]:
        """Returns and clears whatever the batcher is still holding.

        Returns:
            batch: The buffered events, which may be empty.
        """
        batch = self._buffered
        self._buffered = []
        return batch


def traced_events_for_plan(run_id: str, tasks: Sequence[PlannedTask]) -> list[dict[str, object]]:
    """Renders a plan's structural events, one OTel span per emitted event.

    Args:
        run_id: Run whose canvas the events are being emitted to.
        tasks: Planned tasks to announce.

    Returns:
        frames: The same frames events_for_plan builds, each one traced.
    """
    frames = events_for_plan(tasks)
    for frame in frames:
        kind = str(frame["kind"])
        with structural_span(kind, run_id):
            set_span_attribute("graph.event_kind", kind)
    return frames
